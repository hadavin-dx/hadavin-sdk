from __future__ import annotations
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
import pytest
from support import FakeClock
from test_mirror_gate import _pass, _tries
from test_sonar_p2_choke_points import _mid_send
from lead_desk.constants import MIRROR_RETRY_WAIT_SECONDS


def _lock_always(rig: Any, monkeypatch: pytest.MonkeyPatch, exc: Exception | None = None) -> None:
    @contextmanager
    def w(conn: Any) -> Iterator[None]:
        raise exc or sqlite3.OperationalError("database is locked")
        yield  # pragma: no cover
    monkeypatch.setattr(rig.desk, "_write", w)


def test_f1_locked_throughout_keeps_row_sending_and_stage_and_copy_not_stuck(env: Any, monkeypatch: Any) -> None:
    rig, lid, token = _mid_send(env, monkeypatch, "f1")
    real = rig.desk._write
    _lock_always(rig, monkeypatch)
    rig.desk._record_send_result(lid, "sent", token)  # swallowed
    monkeypatch.setattr(rig.desk, "_write", real)
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == "sending"
    assert _tries(rig, lid)[2] == "new"
    assert lid in rig.desk._mirror_not_before
    # the wait is time-bounded: it drops once its time has passed, so the copy is not stuck
    import time
    assert rig.desk._mirror_not_before.waiting(time.monotonic() + 10_000) == []
    assert lid not in rig.desk._mirror_not_before
    # a retry with the same token afterwards records and moves the stage and frees the slot
    rig.desk._mirror_not_before.set(lid, time.monotonic() + 400, 0)
    rig.desk._record_send_result(lid, "sent", token)
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == "sent"
    assert _tries(rig, lid)[2] == "contacted" and lid not in rig.desk._mirror_not_before


def test_f2_commit_fails_once_then_succeeds_moves_and_frees(env: Any, monkeypatch: Any) -> None:
    rig, lid, token = _mid_send(env, monkeypatch, "f2")
    real = rig.desk._write
    n = [0]

    @contextmanager
    def w(conn: Any) -> Iterator[None]:
        n[0] += 1
        with real(conn):
            yield
            if n[0] == 1:
                raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(rig.desk, "_write", w)
    rig.desk._record_send_result(lid, "sent", token)
    assert n[0] == 2
    assert _tries(rig, lid)[2] == "contacted" and lid not in rig.desk._mirror_not_before
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == "sent"


def test_f3_non_busy_error_propagates_and_changes_nothing(env: Any, monkeypatch: Any) -> None:
    rig, lid, token = _mid_send(env, monkeypatch, "f3")
    _lock_always(rig, monkeypatch, sqlite3.IntegrityError("boom"))
    with pytest.raises(sqlite3.IntegrityError):
        rig.desk._record_send_result(lid, "sent", token)
    assert lid in rig.desk._mirror_not_before


def test_f4_gate_busy_is_swallowed_and_nothing_freed(env: Any, monkeypatch: Any) -> None:
    from lead_desk.desk import _GateBusy
    rig, lid, token = _mid_send(env, monkeypatch, "f4")
    _lock_always(rig, monkeypatch, _GateBusy("database is locked (write gate wait ran out)"))
    rig.desk._record_send_result(lid, "sent", token)
    assert lid in rig.desk._mirror_not_before and _tries(rig, lid)[2] == "new"


@pytest.mark.parametrize("state", ["unknown", "pending", "failed"])
def test_f5_other_results_never_move(env: Any, monkeypatch: Any, state: str) -> None:
    rig, lid, token = _mid_send(env, monkeypatch, "f5" + state)
    rig.desk._record_send_result(lid, state, token, "x")  # type: ignore[arg-type]
    assert _tries(rig, lid)[2] == "new" and lid in rig.desk._mirror_not_before
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == state


def test_f6_same_token_twice_second_is_noop(env: Any, monkeypatch: Any) -> None:
    rig, lid, token = _mid_send(env, monkeypatch, "f6")
    import time
    rig.desk._record_send_result(lid, "sent", token)
    rig.desk._mirror_not_before.set(lid, time.monotonic() + 400, 3)
    rig.desk._record_send_result(lid, "sent", token)  # 0 rows: must not free
    assert lid in rig.desk._mirror_not_before


def test_f7_no_leadflow_sent_does_not_crash(env: Any, monkeypatch: Any) -> None:
    from support import lead
    rig = env.rig()
    lid = str(rig.desk.handle("form", "f7", lead()).body["lead_id"])
    rig.desk.run_followup(lid)
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == "sent"


def test_f8_sent_result_when_the_stage_is_already_further_keeps_the_wait(env: Any, monkeypatch: Any) -> None:
    from test_mirror_gate import _sql
    import time
    rig, lid, token = _mid_send(env, monkeypatch, "f8")
    _sql(rig, "UPDATE lead_state SET step='qualified', step_rank=(SELECT MAX(step_rank) FROM lead_state) + 5 WHERE lead_id=?", lid)
    rig.desk._mirror_not_before.set(lid, time.monotonic() + 400, 9)
    rig.desk._record_send_result(lid, "sent", token)
    assert rig.query("SELECT state FROM followups WHERE lead_id=?", (lid,))[0][0] == "sent"
    assert _tries(rig, lid)[2] == "qualified"
    assert lid in rig.desk._mirror_not_before

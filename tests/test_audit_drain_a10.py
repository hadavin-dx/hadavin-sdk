"""A10 (tickets/A-audit-drain.md): bounded flush retries with backoff, the configured per-tick LIMIT, quarantine by age (never delete, never skip silently), operator release. Fake sleep, memory database."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.audit import chain as audit
from hadavin_sdk.backends.table import ChainSettings
from tests.test_audit_drain import (
    _allow_all,
    _append_fails_for,
    _event,
    _ids,
    _outbox,
    _park,
    _park_in_memory,
    _refuse,
)


def _log(**kw):
    sleeps: list[float] = []
    return audit.ChainAudit(audit._Db.memory(), sleep=sleeps.append, **kw), sleeps


def _psql(state):
    """A driver-named error with a SQLSTATE (recognised by class name, no psycopg import needed)."""
    cls = type("DataError", (Exception,), {"__module__": "psycopg.errors", "sqlstate": state})
    return cls("refused")


# --- (a) one classifier -------------------------------------------------------------------------------------


def test_a_one_classifier_serves_flush_pass_and_select():
    src = audit.ChainAudit.__dict__
    import inspect

    for name in ("_flush_pending", "_drain_item", "_drain_with_backoff"):
        assert "_is_permanent" in inspect.getsource(src[name])
    assert audit._is_permanent(_psql("23505")) and not audit._is_permanent(_psql("57014"))


# --- (b) bounded retries with backoff ------------------------------------------------------------------------


def test_b_flush_retries_a_transient_failure_with_doubling_backoff_then_keeps_the_event(
    monkeypatch,
):
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    tried = _append_fails_for(monkeypatch, log, OSError("down"), a)
    assert log._flush_pending() == 0
    assert len(tried) == defaults.AUDIT_FLUSH_ATTEMPTS  # bounded
    assert log._pending == [a] and log._unwritable == []  # kept, visible, never dropped
    assert sleeps == [defaults.AUDIT_FLUSH_BACKOFF_S * 2**i for i in range(len(sleeps))]
    assert len(sleeps) == defaults.AUDIT_FLUSH_ATTEMPTS - 1  # no sleep after the last try


def test_b_backoff_is_capped(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_FLUSH_ATTEMPTS", 8)
    monkeypatch.setattr(defaults, "AUDIT_FLUSH_BACKOFF_S", 0.2)
    monkeypatch.setattr(defaults, "AUDIT_FLUSH_BACKOFF_MAX_S", 0.5)
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    _append_fails_for(monkeypatch, log, OSError("down"), a)
    log._flush_pending()
    assert sleeps == [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5]
    assert log._pending == [a]


def test_b_a_transient_failure_that_clears_is_written(monkeypatch):
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    real, calls = log._append, []

    def flaky(event):
        calls.append(1)
        if len(calls) < 3:
            raise OSError("blip")
        return real(event)

    monkeypatch.setattr(log, "_append", flaky)
    assert log._flush_pending() == 1 and _ids(log) == [a.event_id] and len(sleeps) == 2


def test_b_a_permanent_failure_is_not_retried_or_slept(monkeypatch):
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    tried = _append_fails_for(monkeypatch, log, _psql("23505"), a)
    log._flush_pending()
    assert len(tried) == 1 and sleeps == [] and log._unwritable == [a]


# --- (c) config key ---------------------------------------------------------------------------------------------


def test_c_drain_batch_key_is_bounded_and_defaults_to_the_constant():
    assert ChainSettings(kind="chain").drain_batch is None
    assert ChainSettings(kind="chain", drain_batch=1).drain_batch == 1
    assert (
        ChainSettings(kind="chain", drain_batch=defaults.AUDIT_DRAIN_BATCH_MAX).drain_batch
        == defaults.AUDIT_DRAIN_BATCH_MAX
    )
    for bad in (0, -1, defaults.AUDIT_DRAIN_BATCH_MAX + 1):
        with pytest.raises(ValidationError):
            ChainSettings(kind="chain", drain_batch=bad)
    assert _log()[0].drain_batch == defaults.AUDIT_DRAIN_BATCH
    assert _log(drain_batch=7)[0].drain_batch == 7


def test_c_the_configured_limit_is_the_rows_per_tick():
    log, _ = _log(drain_batch=2)
    for i in range(5):
        _park(log, _event(i, event_id=f"evt-{i}"))
    assert log.reconcile() == 2
    assert log.reconcile() == 2
    assert log.reconcile() == 1
    assert len(_ids(log)) == 5


def test_c_build_passes_the_key(monkeypatch):
    seen = {}
    monkeypatch.setattr(audit, "_Db", audit._Db)
    from hadavin_sdk.store.memory import MemoryStore

    class D:
        store, anchor, signer = MemoryStore(), None, None

    s = ChainSettings(kind="chain", drain_batch=9)
    seen["v"] = audit.build(s, D()).drain_batch
    assert seen["v"] == 9


# --- (d) quarantine after N ticks -----------------------------------------------------------------------------------


def _poison_log(n_good=2):
    log, _ = _log()
    bad = _event(0, event_id="evt-bad")
    _park(log, bad)
    for i in range(n_good):
        _park(log, _event(i + 1, event_id=f"evt-g{i}"))
    _refuse(log, bad)
    return log, bad


def _ids_in_outbox(log):
    return [r[0] for r in log._db.run("SELECT event_id FROM audit_outbox ORDER BY event_id")]


def test_d_a_young_row_stays_and_an_old_one_is_quarantined_and_the_drain_continues():
    log, _bad = _poison_log()
    with pytest.raises(RuntimeError, match="1 rows not writable"):
        log.reconcile()
    assert _ids_in_outbox(log) == ["evt-bad"]  # younger than AUDIT_QUARANTINE_AFTER_S: in place
    assert _ids(log) == ["evt-g0", "evt-g1"]  # the drain went past it
    log._clock = lambda: (
        datetime.now(UTC) + timedelta(seconds=defaults.AUDIT_QUARANTINE_AFTER_S + 1)
    )
    with pytest.raises(RuntimeError, match="1 rows not writable"):
        log.reconcile()
    assert _ids_in_outbox(log) == ["poison:evt-bad"]  # visible quarantined state


def test_d_quarantine_is_logged_and_counted_on_the_following_ticks(caplog, monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_QUARANTINE_AFTER_S", 0)
    log, _ = _poison_log(0)
    caplog.set_level("WARNING")
    with pytest.raises(RuntimeError):
        log.reconcile()
    assert "quarantined_now=1" in caplog.text
    with pytest.raises(RuntimeError, match="1 poison rows quarantined earlier"):
        log.reconcile()


def test_d_the_write_path_pre_drain_does_not_quarantine(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_QUARANTINE_AFTER_S", 0)
    log, _ = _poison_log(0)
    log._outbox_dirty = True
    for _ in range(3):
        log._drain_pass(retry_refused=False)
    assert _ids_in_outbox(log) == ["evt-bad"]


@pytest.mark.parametrize("state", ["42501", "57014", "40001"])
def test_d_42501_and_transient_errors_are_never_quarantined(state, monkeypatch):
    log, _ = _log()
    _park(log, _event(0, event_id="evt-x"))
    _append_fails_for(monkeypatch, log, _psql(state), _event(0, event_id="evt-x"))
    log._clock = lambda: datetime.now(UTC) + timedelta(days=30)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            log.reconcile()
    assert _ids_in_outbox(log) == ["evt-x"]


def test_d_a_quarantined_row_is_readable_never_lost_and_the_operator_can_release_it():
    log, bad = _poison_log()
    log._clock = lambda: (
        datetime.now(UTC) + timedelta(seconds=defaults.AUDIT_QUARANTINE_AFTER_S + 1)
    )
    with pytest.raises(RuntimeError):
        log.reconcile()
    rows = log._db.run(
        "SELECT event_id, body FROM audit_outbox WHERE event_id LIKE ?",
        (defaults.AUDIT_QUARANTINE_PREFIX + "%",),
    )
    assert [r[0] for r in rows] == ["poison:evt-bad"]
    assert rows[0][1] == bad.model_dump_json()  # body intact
    assert _outbox(log) == [("evt-bad", bad.model_dump_json())]
    # operator release (ticket A7): re-insert under the original id, delete the poison row, fix the cause
    _allow_all(log)
    log._db.run(
        "INSERT INTO audit_outbox (event_id, body) SELECT substr(event_id, 8), body FROM audit_outbox "
        "WHERE event_id = 'poison:evt-bad'"
    )
    log._db.run("DELETE FROM audit_outbox WHERE event_id = 'poison:evt-bad'")
    assert log.reconcile() == 1
    assert "evt-bad" in _ids(log) and log._db.run("SELECT COUNT(*) FROM audit_outbox")[0][0] == 0

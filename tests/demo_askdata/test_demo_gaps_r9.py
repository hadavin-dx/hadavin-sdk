"""Round 9: a failed freeze leaves nothing, a partly lost run does not brick the gate, the meter survives readers on
Windows, settle trusts only what was stored, the ledger matches the meter after Ctrl-C, roles.sql revokes the
large-object creators."""

from __future__ import annotations

import json
import os
import threading
from decimal import Decimal

import pytest
from askdata import evalset
from askdata.evalset import Lock, LockError, write_lock
from askdata.fixtures import Step
from askdata.meter import Meter, MeterError
from askdata.sealed import SealedGate, report_state

from .conftest import DEMO
from .kit import COUNT_ORDERS, Kit
from .test_demo_gaps_r3 import KEY, Wrap, gate_for
from .test_demo_gaps_r7 import RUN1

Q = "How many orders are there"


def _files(root, keep=("a.jsonl",)):
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.name not in keep
    )


# ============================================================ M1: a freeze that fails at ANY fsync leaves nothing
def test_a_freeze_that_fails_at_any_fsync_leaves_no_file_and_the_retry_works(tmp_path, monkeypatch):
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "a.jsonl").write_text("x\n", encoding="utf-8")
    anchors = [tmp_path / "audit" / "sealed-anchor.json", ev / "anchor.json"]
    real = os.fsync
    failed_steps = 0
    for step in range(1, 40):
        counter = {"n": 0}

        def failing(fd, _step=step, _counter=counter):
            _counter["n"] += 1
            if _counter["n"] == _step:
                raise OSError("disk full")
            return real(fd)

        monkeypatch.setattr(os, "fsync", failing)
        gate = SealedGate(ev, tmp_path / "audit" / "chain.jsonl", tmp_path / "runs", None, anchors)
        try:
            gate.create(["a.jsonl"])
        except (OSError, LockError):
            failed_steps += 1
            assert _files(tmp_path) == [], f"fsync #{step} failed and left files behind"
            continue
        break
    monkeypatch.setattr(os, "fsync", real)
    assert failed_steps >= 3  # the chain append, the lock and the anchors each fsync
    assert gate.load().test_runs == 0  # the last, unfailed attempt is a normal freeze
    fresh = tmp_path / "again"
    (fresh / "ev").mkdir(parents=True)
    (fresh / "ev" / "a.jsonl").write_text("x\n", encoding="utf-8")


def test_a_chain_append_that_fails_restores_an_existing_chain_byte_for_byte(tmp_path, monkeypatch):
    g = gate_for(tmp_path, KEY)
    before = g.chain.path.read_bytes()

    def boom(_fd):
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", boom)
    with pytest.raises(OSError, match="disk full"):
        g.chain.append("smoke_pass", {"key": "k"})
    monkeypatch.undo()
    assert g.chain.path.read_bytes() == before


# ============================================================ m6: the chain reader gives a typed error
def test_a_chain_that_is_not_utf8_is_a_lock_error_not_a_traceback(tmp_path):
    g = gate_for(tmp_path, KEY)
    with open(g.chain.path, "ab") as f:
        f.write(b"\xff\xfe\n")
    with pytest.raises(LockError, match="damaged"):
        g.chain.entries()


# ============================================================ m7: a failed temp write leaves no temp file
def test_a_failed_lock_write_leaves_no_temp_file(tmp_path, monkeypatch):
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "a.jsonl").write_text("x\n", encoding="utf-8")

    def boom(_fd):
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", boom)
    with pytest.raises(OSError, match="disk full"):
        write_lock(ev, Lock(files={}))
    monkeypatch.undo()
    assert [p.name for p in ev.iterdir()] == ["a.jsonl"]
    assert evalset  # the module under test


# ============================================================ M2: report-lost on a partly lost run
def _three_file_run(g, rid):
    g.begin(g.load(), rid)
    folder = g.runs_dir / rid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "report.json").write_text(json.dumps({"aborted": False}), encoding="utf-8")
    (folder / "report.md").write_text("# report\n", encoding="utf-8")
    (folder / "results.jsonl").write_text('{"x": 1}\n', encoding="utf-8")
    g.record_report(rid)
    g.finish(rid, "complete")
    return folder


def test_report_lost_after_only_report_md_vanished_does_not_brick_the_gate(tmp_path):
    g = gate_for(tmp_path, KEY)
    folder = _three_file_run(g, RUN1)
    (folder / "report.md").unlink()
    g.mark_report_lost(RUN1, "report.md was removed by the antivirus scan")
    assert g.load().test_runs == 1  # no "files appeared" error: the two survivors still match
    assert report_state(g.chain.entries(), g.runs_dir, RUN1) == "lost"
    g.record_smoke("k")  # later commands work too


def test_a_survivor_of_a_lost_run_that_was_changed_or_a_new_file_is_still_refused(tmp_path):
    g = gate_for(tmp_path, KEY)
    folder = _three_file_run(g, RUN1)
    (folder / "report.md").unlink()
    g.mark_report_lost(RUN1, "report.md was removed by the antivirus scan")
    (folder / "report.json").write_text(json.dumps({"aborted": False, "x": 1}), encoding="utf-8")
    with pytest.raises(LockError, match=r"report\.json .*do not match"):
        g.load()
    (folder / "report.json").write_text(json.dumps({"aborted": False}), encoding="utf-8")
    assert g.load().test_runs == 1  # restored: fine again
    (folder / "report.md").write_text(
        "# something else\n", encoding="utf-8"
    )  # a forged re-creation
    with pytest.raises(LockError, match=r"report\.md .*do not match"):
        g.load()


# ============================================================ M3 / m8 / m9: the meter
def _meter(tmp_path, name="m"):
    path = tmp_path / name / "m.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    Meter.create(path, total_cap="100.00", reserve="1.00", demo_cap="90.00")
    return path


def test_writers_and_readers_together_lose_and_double_bill_nothing(tmp_path):
    path = _meter(tmp_path)
    errors: list[BaseException] = []
    done = threading.Event()

    def writer(i):
        try:
            m = Meter(path, lock_wait_s=120)
            for _ in range(10):
                rid = m.reserve(Decimal("0.20"), live=False)
                m.settle(Decimal("0.20"), Decimal("0.01") * (i + 1), rid)
        except BaseException as err:  # noqa: BLE001
            errors.append(err)

    def reader():
        m = Meter(path, lock_wait_s=120)
        while not done.is_set():
            try:
                m.snapshot()
                m.check(Decimal("0.01"), live=False)
                m.open_reservations()
            except BaseException as err:  # noqa: BLE001
                errors.append(err)
                return

    writers = [threading.Thread(target=writer, args=(i,)) for i in range(12)]
    readers = [threading.Thread(target=reader) for _ in range(4)]
    for t in [*readers, *writers]:
        t.start()
    for t in writers:
        t.join()
    done.set()
    for t in readers:
        t.join()
    assert errors == []
    snap = Meter(path).snapshot()
    assert snap["askdata_spent"] == sum(Decimal("0.01") * (i + 1) * 10 for i in range(12))
    assert snap["open"] == 0


def test_every_reader_of_the_meter_takes_its_lock(tmp_path):
    """While another holder has the meter lock, a reader waits and then gives up (it does not read around it)."""
    path = _meter(tmp_path)
    holder = Meter(path)
    with holder._locked():
        impatient = Meter(path, lock_wait_s=0.05)
        for call in (
            impatient.snapshot,
            impatient.open_reservations,
            lambda: impatient.check(Decimal("0.01"), live=False),
            impatient.remaining,
            impatient.stale_open,
        ):
            with pytest.raises(MeterError, match="lock busy"):
                call()


def test_the_meter_retries_a_permission_error_on_read_and_replace(tmp_path, monkeypatch):
    path = _meter(tmp_path)
    m = Meter(path)
    real_replace, real_read = os.replace, type(path).read_text
    calls = {"replace": 0, "read": 0}

    def flaky_replace(src, dst, *a, **k):
        calls["replace"] += 1
        if calls["replace"] <= 2:
            raise PermissionError("held open")
        return real_replace(src, dst, *a, **k)

    def flaky_read(self, *a, **k):
        if self == path:
            calls["read"] += 1
            if calls["read"] <= 2:
                raise PermissionError("being replaced")
        return real_read(self, *a, **k)

    monkeypatch.setattr(os, "replace", flaky_replace)
    monkeypatch.setattr(type(path), "read_text", flaky_read)
    monkeypatch.setattr(evalset.time, "sleep", lambda _s: None)
    rid = m.reserve(Decimal("0.5"), live=False)
    m.settle(Decimal("0.5"), Decimal("0.1"), rid)
    assert (
        m.snapshot()["askdata_spent"] == Decimal("0.1")
        and calls["replace"] >= 3
        and calls["read"] >= 3
    )


def test_settle_releases_the_stored_reservation_not_the_callers_number(tmp_path):
    m = Meter(_meter(tmp_path))
    rid = m.reserve(Decimal("0.50"), live=False)
    m.settle(Decimal("0.01"), Decimal("0.10"), rid)  # a wrong `reserved` from the caller
    assert m.snapshot()["askdata_spent"] == Decimal("0.10") and m.snapshot()["open"] == 0


@pytest.mark.parametrize("bad", ["Infinity", "-Infinity", "NaN"])
def test_a_non_finite_number_is_refused_and_never_reaches_the_file(tmp_path, bad):
    m = Meter(_meter(tmp_path))
    rid = m.reserve(Decimal("0.50"), live=False)
    with pytest.raises(MeterError):
        m.settle(Decimal("0.5"), Decimal(bad), rid)
    with pytest.raises(MeterError):
        m.settle(Decimal(bad), Decimal("0.1"), rid)
    with pytest.raises(MeterError):
        m.charge(Decimal(bad))
    assert (
        m.snapshot()["askdata_spent"] == Decimal("0.5") and m.snapshot()["open"] == 1
    )  # file intact


def test_a_settle_after_clear_open_still_books_the_overage_once(tmp_path):
    m = Meter(_meter(tmp_path))
    rid = m.reserve(Decimal("0.20"), live=False)
    assert m.clear_open() == 1
    m.settle(Decimal("0.20"), Decimal("0.60"), rid)  # the call finished above its reservation
    assert m.snapshot()["askdata_spent"] == Decimal("0.60")
    m.settle(Decimal("0.20"), Decimal("0.60"), rid)  # a duplicate settle changes nothing
    assert m.snapshot()["askdata_spent"] == Decimal("0.60")
    rid2 = m.reserve(Decimal("0.30"), live=False)
    m.clear_open()
    m.settle(
        Decimal("0.30"), Decimal("0.05"), rid2
    )  # cheaper than reserved: the booked amount is not released
    assert m.snapshot()["askdata_spent"] == Decimal("0.90")


# ============================================================ m11: Ctrl-C leaves the ledger and the meter in agreement
def test_ctrl_c_ledger_cost_equals_what_the_meter_booked(tmp_path):
    k = Kit(tmp_path)
    k.script(Q, Step(sql=COUNT_ORDERS))
    k.pipeline.llm = Wrap(k.llm, 1, KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        k.pipeline.ask(Q)
    line = k.ledger.read().items[0].line
    assert Decimal(line.cost_usd) == k.meter.snapshot()["askdata_spent"] > 0


# ============================================================ m5: roles.sql revokes the large-object creators
def test_roles_sql_revokes_the_three_large_object_creators_and_no_longer_overclaims():
    raw = (DEMO / "db" / "roles.sql").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("--"))
    for fn in ("lo_creat(integer)", "lo_create(oid)", "lo_from_bytea(oid, bytea)"):
        assert f"REVOKE EXECUTE ON FUNCTION pg_catalog.{fn} FROM PUBLIC;" in code
    assert "are what hold." not in raw  # the old comment claimed the privileges alone held the line

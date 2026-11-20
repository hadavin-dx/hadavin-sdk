"""A11 (tickets/A-audit-drain.md): quarantine by the age of the row, across processes. `hadavin-sdk tick` runs ONE pass
per process, so every tick here builds a FRESH ChainAudit over the same database and runs one reconcile."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.audit import chain as audit
from hadavin_sdk.backends.table import ChainSettings
from tests.test_audit_drain import _event, _ids, _park, _refuse
from tests.test_audit_drain_a10 import _ids_in_outbox, _psql


class _Clock:
    def __init__(self):
        self.t = datetime.now(UTC)

    def __call__(self):
        return self.t


def _tick(db, clock):
    """One process: a new ChainAudit, one reconcile."""
    log = audit.ChainAudit(db, sleep=lambda s: None, clock=clock)
    try:
        log.reconcile()
    except RuntimeError as exc:
        return log, exc
    return log, None


def _setup(n_good=1):
    db = audit._Db.memory()
    seed = audit.ChainAudit(db, sleep=lambda s: None)
    bad = _event(0, event_id="evt-bad")
    _park(seed, bad)
    for i in range(n_good):
        _park(seed, _event(i + 1, event_id=f"evt-g{i}"))
    _refuse(seed, bad)
    return db, seed, bad


def test_fresh_instance_per_tick_quarantines_an_old_poison_row_and_drains_past_it():
    db, _seed, bad = _setup()
    clock = _Clock()
    log1, exc1 = _tick(db, clock)  # young: stays, the good row drains in this first pass
    assert exc1 is not None and _ids_in_outbox(log1) == ["evt-bad"]
    assert _ids(log1) == ["evt-g0"]
    clock.t += timedelta(seconds=defaults.AUDIT_QUARANTINE_AFTER_S + 1)
    log2, exc2 = _tick(db, clock)
    assert exc2 is not None
    assert _ids_in_outbox(log2) == ["poison:evt-bad"]
    body = log2._db.run("SELECT body FROM audit_outbox WHERE event_id = 'poison:evt-bad'")[0][0]
    assert body == bad.model_dump_json()
    log3, exc3 = _tick(
        db, clock
    )  # the poison row is skipped now; the step still reports it as earlier
    assert "1 poison rows quarantined earlier" in str(exc3)
    assert _ids(log3) == ["evt-g0"]


def test_a_young_poison_row_is_not_quarantined():
    db, _seed, _bad = _setup()
    clock = _Clock()
    for _ in range(4):
        log, exc = _tick(db, clock)
        assert exc is not None
        assert _ids_in_outbox(log) == ["evt-bad"]


def test_42501_is_never_quarantined_however_old(monkeypatch):
    db = audit._Db.memory()
    seed = audit.ChainAudit(db, sleep=lambda s: None)
    ev = _event(0, event_id="evt-x")
    _park(seed, ev)
    clock = _Clock()
    clock.t += timedelta(days=30)
    for _ in range(3):
        log = audit.ChainAudit(db, sleep=lambda s: None, clock=clock)

        def boom(event):
            raise _psql("42501")

        monkeypatch.setattr(log, "_append", boom)
        with pytest.raises(RuntimeError):
            log.reconcile()
        assert _ids_in_outbox(log) == ["evt-x"]


def test_a_naive_ts_is_read_as_utc_for_the_age():
    db = audit._Db.memory()
    seed = audit.ChainAudit(db, sleep=lambda s: None)
    bad = _event(0, event_id="evt-bad", ts=datetime.now(UTC).replace(tzinfo=None))
    _park(seed, bad)
    _refuse(seed, bad)
    clock = _Clock()
    clock.t += timedelta(seconds=defaults.AUDIT_QUARANTINE_AFTER_S + 5)
    log, _exc = _tick(db, clock)
    assert _ids_in_outbox(log) == ["poison:evt-bad"]


def test_table_py_drain_batch_ceiling_equals_the_default():
    le = next(m for m in ChainSettings.model_fields["drain_batch"].metadata if hasattr(m, "le")).le
    assert le == defaults.AUDIT_DRAIN_BATCH_MAX == 2000
    assert not hasattr(defaults, "AUDIT_QUARANTINE_AFTER_TICKS")

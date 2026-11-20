"""Audit drain, fix round 5: a transient refusal stops the drain pass (nothing newer is written past it);
unreadable rows do not use the batch; a naive ts does not raise; an unclassified exception is retried, not
quarantined, and fails the step with its own text. Helpers are those of tests/test_audit_drain.py."""

from __future__ import annotations

import datetime as dt

import pytest

from hadavin_sdk import defaults
from tests.test_audit_drain import (
    _append_fails_for,
    _driver_error,
    _event,
    _ids,
    _log,
    _outbox,
    _park,
    _park_in_memory,
    _refuse,
)

T0 = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def _at(seconds, **kw):
    return _event(seconds, ts=T0 + dt.timedelta(seconds=seconds), **kw)


def test_a_transient_refusal_of_an_older_row_stops_the_pass_and_the_next_tick_keeps_ts_order(
    monkeypatch,
):
    log, older, newer = _log(), _at(1, event_id="evt-b"), _at(2, event_id="evt-a")
    _park(log, older)
    _park(log, newer)
    with monkeypatch.context() as mp:
        tried = _append_fails_for(mp, log, _driver_error("OperationalError", "55P03"), older)
        with pytest.raises(RuntimeError, match="1 rows refused for a transient error"):
            log.reconcile()
    assert tried == [older.event_id]  # the newer row was not even tried
    assert _ids(log) == []
    assert log.reconcile() == 2
    assert _ids(log) == [older.event_id, newer.event_id] and log.verify().ok


def test_a_permanent_refusal_is_still_skipped_and_newer_rows_are_written():
    log, bad, good = _log(), _at(1), _at(2)
    _park(log, bad)
    _park(log, good)
    _refuse(log, bad)
    with pytest.raises(RuntimeError):
        log.reconcile()
    assert _ids(log) == [good.event_id]


def test_a_transient_memory_event_stops_the_pass_before_a_newer_outbox_row(monkeypatch):
    log, mem, box = _log(), _at(1), _at(2)
    _park_in_memory(log, mem)
    _park(log, box)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _driver_error("OperationalError", "40001"), mem)
        with pytest.raises(RuntimeError):
            log.reconcile()
    assert _ids(log) == [] and [r[0] for r in _outbox(log)] == [box.event_id]
    assert log.reconcile() == 2
    assert _ids(log) == [mem.event_id, box.event_id]


def test_a_naive_ts_does_not_raise_and_is_ordered_as_utc():
    log = _log()
    naive = _event(1, ts=dt.datetime(2026, 1, 1, 0, 0, 5, tzinfo=None))  # noqa: DTZ001 - naive on purpose
    aware = _at(1)  # 00:00:01 UTC, older than the naive one read as UTC
    _park(log, naive)
    _park(log, aware)
    assert log.reconcile() == 2
    assert _ids(log) == [aware.event_id, naive.event_id]


def test_an_unclassified_exception_is_retried_not_quarantined_and_fails_the_step_by_name(
    monkeypatch,
):
    log, row = _log(), _at(1)
    _park(log, row)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, AttributeError("wrapped pool broke"), row)
        with pytest.raises(RuntimeError, match="1 items refused for an unclassified error"):
            log.reconcile()
    assert [r[0] for r in _outbox(log)] == [row.event_id]
    assert log._db.run("SELECT event_id FROM audit_outbox") == [(row.event_id,)]  # not renamed
    assert log.reconcile() == 1 and _ids(log) == [row.event_id]


def test_an_unclassified_exception_does_not_move_a_memory_event_aside(monkeypatch):
    log, mem = _log(), _at(1)
    _park_in_memory(log, mem)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, RuntimeError("bug"), mem)
        with pytest.raises(RuntimeError, match="unclassified"):
            log.reconcile()
    assert log._unwritable == [] and log._pending == [mem]
    assert log.reconcile() == 1


def test_unreadable_valid_json_rows_do_not_use_the_batch_and_are_counted(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_DRAIN_BATCH", 2)
    log, good = _log(), [_at(10), _at(11)]
    for i in range(3):  # valid JSON with an old ts, but not an AuditEvent
        log._db.run(
            "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)",
            (f"junk-{i}", f'{{"ts":"2025-01-0{i + 1}T00:00:00+00:00"}}'),
        )
    for e in good:
        _park(log, e)
    with pytest.raises(RuntimeError, match="3 unreadable rows kept"):
        log.reconcile()
    assert _ids(log) == [e.event_id for e in good]

"""A9: the older-first drain on the write path (`_drain_older_first`) can never keep a new event out of the chain,
never turn an intent's success into a failure, and never keep `_outbox_dirty` True because of a role that cannot
write the outbox. Helpers are those of tests/test_audit_drain.py."""

from __future__ import annotations

import time

import pytest

from hadavin_sdk.audit.protocol import AuditUnavailable
from tests.test_audit_drain import _driver_error, _event, _ids, _log, _park


def _dirty_log(*parked):
    log = _log()
    for e in parked:
        _park(log, e)
    log._outbox_dirty = True
    return log


def _raise(exc):
    def f(*a, **k):
        raise exc

    return f


def test_a_drain_that_raises_does_not_stop_the_new_intent_from_being_appended(monkeypatch):
    new = _event(2)
    log = _dirty_log(_event(1))
    monkeypatch.setattr(log, "_drain_pass", _raise(RuntimeError("drain exploded")))
    assert log.write_intent(new) == new.event_id
    assert _ids(log) == [new.event_id]  # the parked row waits for the tick


def test_a_drain_that_raises_still_lets_the_intent_raise_audit_unavailable(monkeypatch):
    log = _dirty_log(_event(1))
    monkeypatch.setattr(log, "_drain_pass", _raise(RuntimeError("drain exploded")))
    monkeypatch.setattr(log, "_append", _raise(OSError("down")))
    with pytest.raises(AuditUnavailable):
        log.write_intent(_event(2))


def test_a_drain_whose_append_raises_does_not_stop_the_new_intent(monkeypatch):
    old, new = _event(1), _event(2)
    log = _dirty_log(old)
    real = log._append

    def flaky(event):
        if event.event_id == old.event_id:
            raise RuntimeError("append exploded")
        return real(event)

    monkeypatch.setattr(log, "_append", flaky)
    assert log.write_intent(new) == new.event_id
    assert _ids(log) == [new.event_id]


def test_a_drain_that_stalls_is_bounded_by_the_lock_timeout(monkeypatch):
    """The drain's append waits for the (fake) lock timeout and fails with 55P03; the new append then runs: about
    one timeout in all here (limit (j): twice the timeout is the worst case on a sick database)."""
    timeout = 0.2
    old, new = _event(1), _event(2)
    log = _dirty_log(old)
    real = log._append

    def stalls(event):
        if event.event_id == old.event_id:
            time.sleep(timeout)  # the lock wait
            raise _driver_error("OperationalError", "55P03")
        return real(event)

    monkeypatch.setattr(log, "_append", stalls)
    start = time.monotonic()
    assert log.write_intent(new) == new.event_id
    assert time.monotonic() - start < 2 * timeout + 0.5
    assert _ids(log) == [new.event_id]
    assert log._outbox_dirty  # the parked row is still there: the next write tries again


def test_a_role_that_cannot_insert_into_the_outbox_leaves_outbox_dirty_false(monkeypatch):
    log = _log()
    log._db.run(
        "CREATE TRIGGER no_outbox BEFORE INSERT ON audit_outbox "
        "BEGIN SELECT RAISE(ABORT, 'permission denied for table audit_outbox'); END"
    )
    monkeypatch.setattr(log, "_append", _raise(OSError("down")))
    e = _event(1)
    assert log.write_outcome(e) is None
    assert log._pending == [e]  # fell through to memory
    assert (
        log._outbox_dirty is False
    )  # nothing was parked in the table: no drain pass on the next write

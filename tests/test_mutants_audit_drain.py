"""Mutation-check kills for the audit drain (src/hadavin_sdk/audit/chain.py). Each test names the mutant that the
existing drain suites let survive. Helpers are those of tests/test_audit_drain.py."""

from __future__ import annotations

import datetime as dt
import threading

from hadavin_sdk.audit import chain as audit
from tests.test_audit_drain import _event, _ids, _log, _park, _park_in_memory

T0 = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def test_same_ts_ties_are_ordered_by_event_id_across_memory_and_outbox():
    """Mutant: the sort key drops event_id (a memory event then sorts before an outbox row of the same ts)."""
    log = _log()
    mem = _event(1, ts=T0, event_id="evt-z")
    box = _event(2, ts=T0, event_id="evt-a")
    _park_in_memory(log, mem)
    _park(log, box)
    assert log.reconcile() == 2
    assert _ids(log) == ["evt-a", "evt-z"]


def test_a_short_page_ends_the_read_with_one_select():
    """Mutant: the paging loop stops only on an empty page, so it issues one more SELECT than it needs."""
    log = _log()
    for i in range(3):
        _park(log, _event(i, ts=T0 + dt.timedelta(seconds=i)))
    real, selects = log._db.run, []

    def counting(sql, params=()):
        if "FROM audit_outbox WHERE event_id NOT LIKE" in sql:
            selects.append(params)
        return real(sql, params)

    log._db.run = counting
    assert log.reconcile() == 3
    assert len(selects) == 1


def test_a_failed_outbox_read_keeps_the_outbox_dirty_flag():
    """Mutant: the flag is cleared whenever nothing was read, including when the read itself failed (the parked
    rows are then forgotten and a newer event overtakes them)."""
    log = _log()
    log._outbox_dirty = True

    def broken(sql, params=()):
        raise OSError("down")

    log._db.run = broken
    r = log._drain_pass(retry_refused=False)
    assert isinstance(r.select_error, OSError)
    assert log._outbox_dirty is True


def test_t_escapes_a_double_quote_in_the_schema_name():
    """Mutant: the schema is quoted without doubling an embedded double quote (identifier injection)."""
    db = audit._Db(None, threading.Lock(), pg=True, schema='a"b')
    out = db._t("SELECT 1 FROM audit_outbox WHERE event_id = ?")
    assert out == 'SELECT 1 FROM "a""b".audit_outbox WHERE event_id = %s'

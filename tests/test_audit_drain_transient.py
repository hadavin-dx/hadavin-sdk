"""Audit drain, fix round 4 (E9, ORDER 021): transient database errors are retried, never lost; one classifier for
the append and the outbox read; a bounded batch per tick; outbox rows enter the chain in (ts, event_id) order and
before a newer inline event; a poison row is quarantined (kept, skipped, counted). The helpers are the ones of
tests/test_audit_drain.py."""

from __future__ import annotations

import datetime as dt
import threading

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.audit import chain as audit
from tests.test_audit_drain import (  # noqa: F401 - `app` is a fixture
    _allow_all,
    _append_fails_for,
    _driver_error,
    _event,
    _ids,
    _log,
    _outbox,
    _park,
    _park_in_memory,
    _refuse,
    _release,
    app,
)

T0 = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def _at(seconds, **kw):
    return _event(seconds, ts=T0 + dt.timedelta(seconds=seconds), **kw)


# --- transient errors: the event stays in the retry set ------------------------------------------------------


@pytest.mark.parametrize("state", ["55P03", "40001", "40P01", "57014", "53300", "25006", "08006"])
def test_a_transient_error_during_a_flush_keeps_the_event_in_pending_and_the_next_append_writes_it(
    monkeypatch, state
):
    log, (a, trigger, later) = _log(), (_at(1), _at(2), _at(3))
    _park_in_memory(log, a)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _driver_error("OperationalError", state), a)
        assert log.write_outcome(trigger) == trigger.event_id
    assert log._pending == [a] and log._unwritable == []  # NOT moved aside, not lost
    assert log.write_outcome(later) == later.event_id  # the flush retries on the next append
    assert log._pending == [] and set(_ids(log)) == {a.event_id, trigger.event_id, later.event_id}


def test_reconcile_retries_a_transient_memory_event_and_says_so_while_it_is_stuck(monkeypatch):
    log, a = _log(), _at(1)
    _park_in_memory(log, a)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _driver_error("OperationalError", "55P03"), a)
        with pytest.raises(RuntimeError, match="^audit outbox: 1 events not writable in memory$"):
            log.reconcile()
    assert log._pending == [a] and log._unwritable == []
    assert log.reconcile() == 1 and _ids(log) == [a.event_id]


def test_a_plain_outage_in_reconcile_is_still_quiet(monkeypatch):
    log, a = _log(), _at(1)
    _park(log, a)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, OSError("down"), a)
        assert log.reconcile() == 0
    assert [r[0] for r in _outbox(log)] == [a.event_id]


def test_an_outbox_row_refused_with_a_timeout_stays_and_fails_the_step_with_a_text(monkeypatch):
    log, a = _log(), _at(1)
    _park(log, a)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _driver_error("OperationalError", "57014"), a)
        with pytest.raises(RuntimeError, match="1 rows refused for a transient error"):
            log.reconcile()
    assert [r[0] for r in _outbox(log)] == [a.event_id]
    assert log.reconcile() == 1 and _outbox(log) == []


# --- the outbox read uses the same classifier ---------------------------------------------------------------


def _select_fails(mp, log, exc):
    real = log._db.run

    def run(sql, params=()):
        if "FROM audit_outbox" in sql and sql.lstrip().startswith("SELECT event_id, body"):
            raise exc
        return real(sql, params)

    mp.setattr(log._db, "run", run)


@pytest.mark.parametrize("state", ["57014", "55P03", "40001", "53300"])
def test_a_timeout_reading_the_outbox_raises_a_named_step_failure(monkeypatch, state):
    log = _log()
    _park(log, _at(1))
    with monkeypatch.context() as mp:
        _select_fails(mp, log, _driver_error("OperationalError", state))
        with pytest.raises(RuntimeError, match=r"^audit outbox: read failed \(OperationalError\)$"):
            log.reconcile()


def test_an_outage_reading_the_outbox_is_quiet(monkeypatch):
    log = _log()
    with monkeypatch.context() as mp:
        _select_fails(mp, log, OSError("down"))
        assert log.reconcile() == 0
        _select_fails(mp, log, _driver_error("OperationalError", "08006"))
        assert log.reconcile() == 0


# --- a bounded batch per tick -----------------------------------------------------------------------------


def test_one_reconcile_reads_and_drains_at_most_one_batch(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_DRAIN_BATCH", 3)
    log, events = _log(), [_at(i) for i in range(8)]
    for e in events:
        _park(log, e)
    assert [log.reconcile() for _ in range(3)] == [3, 3, 2]
    assert _ids(log) == [e.event_id for e in events] and _outbox(log) == []


def test_the_batch_constant_lives_in_defaults_only():
    assert isinstance(defaults.AUDIT_DRAIN_BATCH, int) and defaults.AUDIT_DRAIN_BATCH > 0


# --- order ----------------------------------------------------------------------------------------------


def test_outbox_rows_enter_the_chain_by_ts_not_by_event_id():
    log = _log()
    older = _at(1, event_id="evt-zzz")  # sorts LAST by id, written FIRST
    newer = _at(2, event_id="evt-aaa")
    _park(log, newer)
    _park(log, older)
    assert log.reconcile() == 2
    assert _ids(log) == ["evt-zzz", "evt-aaa"] and log.verify().ok


def test_memory_events_merge_into_the_same_order_as_the_outbox_rows():
    log = _log()
    mem_old, box_mid, mem_new = _at(1), _at(2), _at(3)
    _park_in_memory(log, mem_new, mem_old)  # parked in the wrong order on purpose
    _park(log, box_mid)
    assert log.reconcile() == 3
    assert _ids(log) == [mem_old.event_id, box_mid.event_id, mem_new.event_id]


def test_a_newer_inline_event_does_not_overtake_an_older_parked_outbox_row(monkeypatch):
    log, older, newer = _log(), _at(1), _at(2)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _driver_error("OperationalError", "57014"), older)
        assert log.write_outcome(older) is None  # parked in the outbox
    assert [r[0] for r in _outbox(log)] == [older.event_id]
    assert log.write_outcome(newer) == newer.event_id
    assert _ids(log) == [older.event_id, newer.event_id] and _outbox(log) == []


def test_an_inline_intent_is_written_even_when_the_older_row_is_still_refused(monkeypatch):
    log, older, intent = _log(), _at(1), _at(2)
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, OSError("down"), older)
        assert log.write_outcome(older) is None
        assert log.write_intent(intent) == intent.event_id  # an intent never waits on a sick outbox
    assert _ids(log) == [intent.event_id] and [r[0] for r in _outbox(log)] == [older.event_id]


# --- poison rows ------------------------------------------------------------------------------------------


def test_a_poison_row_is_quarantined_once_counted_every_tick_and_never_retried(monkeypatch):
    log, bad, good1, good2 = _log(), _at(1), _at(2), _at(3)
    for e in (bad, good1, good2):
        _park(log, e)
    _refuse(log, bad)
    with pytest.raises(RuntimeError) as first:
        log.reconcile()
    assert str(first.value) == "audit outbox: 1 rows not writable"
    assert _ids(log) == [good1.event_id, good2.event_id]
    prefix = defaults.AUDIT_QUARANTINE_PREFIX
    assert log._db.run("SELECT event_id FROM audit_outbox") == [(prefix + bad.event_id,)]
    tried = _append_fails_for(monkeypatch, log, RuntimeError("must not be tried"), _at(99))
    with pytest.raises(
        RuntimeError, match=r"^audit outbox: 1 poison rows quarantined earlier .*A-audit-drain"
    ):
        log.reconcile()
    assert tried == []  # the quarantined row is skipped, not attempted
    monkeypatch.undo()
    _allow_all(log)
    _release(log)  # the operator's step (tickets/A-audit-drain.md)
    assert log.reconcile() == 1 and _ids(log)[-1] == bad.event_id


def test_poison_rows_do_not_use_up_the_batch(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_DRAIN_BATCH", 2)
    log = _log()
    bad = [_at(i) for i in range(2)]
    good = [_at(10 + i) for i in range(2)]
    for e in bad + good:
        _park(log, e)
    _refuse(log, *bad)
    with pytest.raises(RuntimeError):
        log.reconcile()  # the batch is the two oldest rows: both poison, now quarantined
    with pytest.raises(RuntimeError):
        log.reconcile()  # the next batch reaches the good rows
    assert _ids(log) == [e.event_id for e in good]


# --- the chain kind exposes reconcile (M4) ----------------------------------------------------------------


def test_the_configured_chain_kind_exposes_reconcile_and_the_tick_calls_it(app):  # noqa: F811
    assert isinstance(app.audit, audit.ChainAudit) and callable(app.audit.reconcile)
    e = _at(1)
    _park(app.audit, e)
    from hadavin_sdk.runtime.tick import run_tick

    assert run_tick(app) == 0 and _ids(app.audit) == [e.event_id]


# --- PostgreSQL (skipped without HADAVIN_TEST_PG_DSN) -----------------------------------------------------


def _pg_log(dsn):
    import psycopg

    conn = psycopg.connect(dsn, autocommit=True)
    return conn, audit.ChainAudit(audit._Db(conn, threading.Lock(), pg=True))


def test_pg_order_limit_and_a_nul_poison_row_with_a_junk_row_in_the_outbox(monkeypatch):
    pytest.importorskip("psycopg")
    from tests.contracts.kinds.store_postgres import pg_schema

    monkeypatch.setattr(defaults, "AUDIT_DRAIN_BATCH", 4)
    for dsn in pg_schema(runtime=False):
        conn, log = _pg_log(dsn)
        poison = _at(
            0, run_id="a\x00b"
        )  # the JSON body escapes the NUL; the text column refuses it
        newer, older = _at(2, event_id="evt-aaa"), _at(1, event_id="evt-zzz")
        for e in (newer, older, poison):
            conn.execute(
                "INSERT INTO audit_outbox VALUES (%s, %s)", (e.event_id, e.model_dump_json())
            )
        conn.execute("INSERT INTO audit_outbox VALUES ('junk', 'not json at all')")
        with pytest.raises(RuntimeError, match="1 unreadable rows kept, 1 rows not writable"):
            log.reconcile()
        assert _ids(log) == [
            "evt-zzz",
            "evt-aaa",
        ]  # by ts; the junk row (no ts) did not break the read
        names = {r[0] for r in conn.execute("SELECT event_id FROM audit_outbox").fetchall()}
        assert names == {"junk", defaults.AUDIT_QUARANTINE_PREFIX + poison.event_id}
        with pytest.raises(
            RuntimeError, match="1 unreadable rows kept, 1 poison rows quarantined earlier"
        ):
            log.reconcile()
        conn.close()


def test_pg_a_real_statement_timeout_reading_the_outbox_fails_the_step(monkeypatch):
    pytest.importorskip("psycopg")
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema(runtime=False):
        conn, log = _pg_log(dsn)
        conn.execute("INSERT INTO audit_outbox VALUES ('x', 'y')")
        conn.execute(
            "CREATE FUNCTION slow(text) RETURNS text LANGUAGE sql AS $$ SELECT pg_sleep(1)::text $$"
        )
        real = log._outbox_sql
        monkeypatch.setattr(
            log,
            "_outbox_sql",
            lambda real=real: real().replace("ORDER BY (", "ORDER BY slow(body), (", 1),
        )
        conn.execute("SET statement_timeout = '100ms'")
        with pytest.raises(RuntimeError, match=r"^audit outbox: read failed \(QueryCanceled\)$"):
            log.reconcile()
        conn.execute("SET statement_timeout = 0")
        conn.close()


@pytest.fixture(autouse=True)
def _quarantine_at_once(monkeypatch):
    """The cases of this file pin the quarantine mechanics with the age set to 0; the age rule is tests/test_audit_drain_a11.py."""
    monkeypatch.setattr(defaults, "AUDIT_QUARANTINE_AFTER_S", 0)

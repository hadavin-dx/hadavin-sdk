"""Spend reservations (step F-store) against a real PostgreSQL through real non-superuser logins: the crash cases
C1 to C5, settle from 8 connections, settle racing the expire step, the per-role negative tests, the two `migrate`
cases of review finding cb-1, and the `expire_reservations` tick step.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/F-store.md), not from the
code. Every database case gets a fresh schema and four LOGIN roles (runtime, portal, purge, reset) with random
names (`World` of tests/test_stop_state_roles.py: the portal and the reset login are made by hand there, as R7
asks), `migrate(...)` with all four named, and drops only what it made. "Denied" means
`psycopg.errors.InsufficientPrivilege` exactly, and the relation is proven to exist first.

The database cases are marked `pg` and need HADAVIN_TEST_PG_DSN; the tick cases at the end need no database
(a stand-in app on the memory store), so they also run without it."""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import threading
import time
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql

from hadavin_sdk import defaults
from hadavin_sdk.config import ConfigError, Retention
from hadavin_sdk.limits import Limits, SpendRefused
from hadavin_sdk.models import Run, SpendReservation, new_id, now
from hadavin_sdk.runtime import tick
from hadavin_sdk.runtime.tick import TickContext, TickStep, run_tick
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.migrate import GRANTS
from hadavin_sdk.store.protocol import NotFound
from tests.contracts.test_store_spend import _older, _rows
from tests.money_caps_seed import seed_caps
from tests.test_limits_reserve import Sink, _registry
from tests.test_stop_state_roles import World

pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
DENIED = errors.InsufficientPrivilege
TABLE = "spend_reservations"
AGENT = "agent-a"
DAY = date(now().year - 1, 1, 31)
BIG = D("1000")
WAIT_S = 60
COLUMNS = list(SpendReservation.model_fields)


@pytest.fixture(name="w")
def reservation_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        world.migrate()
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _reserve(store, usd="1.00", *, agent=AGENT, day_cap=BIG, month_cap=BIG, run_id=None):
    rid = new_id("res")
    store.reserve_spend(
        rid, agent, DAY, D(usd), day_cap=D(day_cap), month_cap=D(month_cap), run_id=run_id
    )
    return rid


def _table(w):
    """Every row as the OWNER reads it on a new connection: {id: (status, reserved, settled)}."""
    found = w.run(
        "SELECT reservation_id, status, reserved_usd, settled_usd FROM spend_reservations"
    )
    return {r[0]: tuple(r[1:]) for r in found}


def _counters(w, agent=AGENT):
    """(day, month) as the owner reads them on a new connection; None where no counter row exists."""
    day = w.run("SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent, DAY))
    month = w.run(
        "SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",
        (agent, DAY.replace(day=1)),
    )
    return (day[0][0] if day else None, month[0][0] if month else None)


def _age(w, rid, seconds):
    w.run(
        "UPDATE spend_reservations SET created_at = created_at - make_interval(secs => %s) "
        "WHERE reservation_id = %s RETURNING 1",
        (seconds, rid),
    )


def _new_run(store):
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run.run_id


def _waits_on_a_lock(w, pid):
    q = "SELECT count(*) FROM pg_stat_activity WHERE pid = %s AND wait_event_type = 'Lock'"
    for _ in range(10 * WAIT_S):
        if w.run(q, (pid,))[0][0]:
            return True
        time.sleep(0.1)
    return False


def _denied(w, role, statement, relation):
    assert w.exists(relation), f"{relation} does not exist: a refusal would prove nothing"
    with w.as_(role) as db, pytest.raises(DENIED):
        db.execute(statement)


# --- crash cases ---------------------------------------------------------------------------------------------------

CHILD = """
import os, sys, time
from datetime import date
from decimal import Decimal
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings

name = "pg-" + "dsn"
store = make("store", PostgresSettings(kind="postgres", dsn_secret_name=name),
             FakeSecretProvider({name: os.environ["RESERVE_CHILD_DSN"]}))
print("pid", store._db.info.backend_pid, flush=True)
store.reserve_spend(sys.argv[1], sys.argv[2], date.fromisoformat(sys.argv[3]), Decimal(sys.argv[4]),
                    day_cap=Decimal(1000), month_cap=Decimal(1000))
print("reserved", flush=True)
time.sleep(120)
"""


class Child:
    """Another process that reserves once through its own store and then sleeps until it is killed."""

    def __init__(self, w, rid, usd):
        seed_caps(w.scoped, w.schema, AGENT, BIG, BIG)  # the child's own store has no test hook
        self.proc = subprocess.Popen(  # noqa: S603 - this interpreter, a fixed script
            [sys.executable, "-c", CHILD, rid, AGENT, DAY.isoformat(), usd],
            stdout=subprocess.PIPE,
            text=True,
            env={**os.environ, "RESERVE_CHILD_DSN": w.dsn_of(w.runtime)},
        )

    def line(self):
        return self.proc.stdout.readline().split()

    def kill(self):
        self.proc.kill()  # SIGKILL: no handler runs, nothing is closed in order
        self.proc.wait(timeout=WAIT_S)
        self.proc.stdout.close()


@pg
def test_c1_a_child_killed_after_its_reserve_leaves_the_worst_case_booked(w):
    rid = new_id("res")
    child = Child(w, rid, "1.25")
    try:
        assert child.line()[0] == "pid"
        assert child.line() == ["reserved"], "the child did not get as far as its reserve"
    finally:
        child.kill()
    assert child.proc.returncode != 0
    assert _table(w) == {rid: ("open", D("1.25"), None)}
    assert _counters(w) == (D("1.25"), D("1.25"))
    rt = w.store(w.runtime)
    assert rt.expire_spend_reservations(3600) == 0  # still young: its call could be running
    _age(w, rid, 3601)
    assert rt.expire_spend_reservations(3600) == 1
    assert _table(w) == {rid: ("expired", D("1.25"), D("1.25"))}
    assert _counters(w) == (D("1.25"), D("1.25"))  # the totals are unchanged by the expiry


@pg
def test_c2_a_child_killed_while_it_waits_for_the_day_row_books_nothing(w):
    rt = w.store(w.runtime)
    first = _reserve(rt, "0.50")  # the day row exists, so the child's UPDATE has a row to wait on
    rid = new_id("res")
    with w.admin() as owner, owner.transaction():
        owner.execute("SELECT usd FROM spend WHERE agent_id = %s FOR UPDATE", (AGENT,))
        child = Child(w, rid, "1.25")
        try:
            tag, pid = child.line()
            assert tag == "pid"
            assert _waits_on_a_lock(w, int(pid)), "the child never waited on the day row"
        finally:
            child.kill()
    gone = "SELECT count(*) FROM pg_stat_activity WHERE pid = %s"
    for _ in range(10 * WAIT_S):  # the server ends the child's backend once the row lock is free
        if not w.run(gone, (int(pid),))[0][0]:
            break
        time.sleep(0.1)
    assert w.run(gone, (int(pid),))[0][0] == 0
    assert _table(w) == {first: ("open", D("0.50"), None)}
    assert _counters(w) == (D("0.50"), D("0.50"))


def _break(monkeypatch, store, text):
    """From now on the store's statement that holds `text` raises instead of running."""
    real = store._exec

    def faulty(query, params=()):
        shown = query.as_string(store._db) if isinstance(query, sql.Composable) else str(query)
        if text in shown:
            raise RuntimeError("injected fault")
        return real(query, params)

    monkeypatch.setattr(store, "_exec", faulty)


def _fail_inside_function(w, table):
    """A fault INSIDE the definer function (the runtime has no right on the table any more, so a revoke proves
    nothing): the owner puts a CHECK that no row can pass on the counter table, so the function's own INSERT or
    UPDATE of it raises while an earlier step of the same call has already run."""
    w.do(f"ALTER TABLE {table} ADD CONSTRAINT never CHECK (false) NOT VALID")


@pg
@pytest.mark.parametrize("fault", ["raised", "constraint"])
def test_c3_a_fault_at_the_month_update_in_reserve_changes_nothing(w, monkeypatch, fault):
    rt = w.store(w.runtime)
    kept = _reserve(rt, "0.50")
    with monkeypatch.context() as m:
        if fault == "raised":
            _break(m, rt, "hadavin_reserve_spend")  # the call itself fails
            failure = RuntimeError
        else:
            _fail_inside_function(w, "spend_month")  # the function fails after it booked the day
            failure = errors.CheckViolation
        with pytest.raises(failure):
            _reserve(rt, "1.25")
        assert _table(w) == {kept: ("open", D("0.50"), None)}  # no row
        assert _counters(w) == (D("0.50"), D("0.50"))  # the day booking was taken back
        with pytest.raises(SpendRefused) as caught:  # and through Limits: no call, no id
            Limits(rt, Sink(), _registry(daily="1000", monthly="1000")).reserve(AGENT, D("1.25"))
        assert caught.value.reason == "limits_unavailable"
    assert len(_table(w)) == 1 and w.count(TABLE) == 1
    if fault == "raised":  # the fault is gone: the same connection works again
        _reserve(rt, "1.25")
        assert _counters(w) == (D("1.75"), D("1.75"))


@pg
@pytest.mark.parametrize("fault", ["raised", "constraint"])
def test_c3_a_fault_at_the_day_update_in_reserve_leaves_no_row(w, monkeypatch, fault):
    rt = w.store(w.runtime)
    if fault == "raised":
        _break(monkeypatch, rt, "hadavin_reserve_spend")
        failure = RuntimeError
    else:
        _fail_inside_function(w, "spend")  # after the reservation row was inserted
        failure = errors.CheckViolation
    with pytest.raises(failure):
        _reserve(rt, "1.25")
    assert _table(w) == {} and _counters(w) == (None, None)


@pg
@pytest.mark.parametrize("fault", ["raised", "constraint", "counter_row_deleted"])
def test_c4_a_fault_at_the_month_update_in_settle_changes_nothing(w, monkeypatch, fault):
    rt = w.store(w.runtime)
    run_id = _new_run(rt)
    rid = _reserve(rt, "1.00", run_id=run_id)
    with monkeypatch.context() as m:
        if fault == "raised":
            _break(m, rt, "hadavin_settle_spend")
            failure, message = RuntimeError, "injected fault"
        elif fault == "constraint":
            _fail_inside_function(w, "spend_month")
            failure, message = errors.CheckViolation, "never"
        else:
            w.do("DELETE FROM spend_month")
            failure, message = RuntimeError, "spend counter row missing"
        with pytest.raises(failure, match=message):
            rt.settle_spend(rid, D("0.40"))
        assert _table(w) == {rid: ("open", D("1.00"), None)}  # the claim was rolled back
        assert _counters(w)[0] == D("1.00")  # the day counter did not move
        assert rt.get_run(run_id).cost_usd == 0
        if fault != "counter_row_deleted":
            assert _counters(w) == (D("1.00"), D("1.00"))
    if (
        fault == "raised"
    ):  # the same connection settles once the fault is gone, and it is the first settle
        row, applied = rt.settle_spend(rid, D("0.40"))
        assert applied and row.settled_usd == D("0.40")
        assert _counters(w) == (D("0.40"), D("0.40")) and rt.get_run(run_id).cost_usd == D("0.40")


@pg
def test_c4_a_missing_day_counter_row_in_settle_raises_and_changes_nothing(w):
    rt = w.store(w.runtime)
    rid = _reserve(rt, "1.00")
    w.do("DELETE FROM spend")
    with pytest.raises(RuntimeError, match="spend counter row missing"):
        rt.settle_spend(rid, D("0.40"))
    assert _table(w) == {rid: ("open", D("1.00"), None)}
    assert _counters(w) == (None, D("1.00"))


@pg
def test_a_closed_connection_refuses_through_limits_with_nothing_booked(w):
    rt = w.store(w.runtime)
    limits = Limits(rt, Sink(), _registry(daily="1000", monthly="1000"))
    kept = limits.reserve(AGENT, D("0.50"))
    rt._db.close()
    with pytest.raises(SpendRefused) as caught:
        limits.reserve(AGENT, D("0.50"))
    assert caught.value.reason == "limits_unavailable"
    assert set(_table(w)) == {kept}
    with pytest.raises(psycopg.Error):  # settle lets the store's failure through (contract point 6)
        limits.settle(kept, D("0.10"))
    assert _table(w)[kept] == ("open", D("0.50"), None)


@pg
def test_c5_a_late_settle_after_expiry_never_lowers_and_may_raise_the_booking(w):
    rt = w.store(w.runtime)
    run_id = _new_run(rt)
    low, high = _reserve(rt, "1.00", run_id=run_id), _reserve(rt, "1.00", run_id=run_id)
    for rid in (low, high):
        _age(w, rid, 4000)
    assert rt.expire_spend_reservations(3600) == 2
    assert _counters(w) == (D("2.00"), D("2.00"))
    row, applied = rt.settle_spend(low, D("0.40"))  # lower: the row is settled, the counters stay
    assert applied and (row.status, row.settled_usd) == ("settled", D("1.00"))
    assert _counters(w) == (D("2.00"), D("2.00"))
    assert rt.get_run(run_id).cost_usd == D("0.40")  # the run gets the real amount
    row, applied = rt.settle_spend(high, D("2.50"))  # higher: both counters rise to the actual
    assert applied and (row.status, row.settled_usd) == ("settled", D("2.50"))
    assert _counters(w) == (D("3.50"), D("3.50"))
    assert rt.get_run(run_id).cost_usd == D("2.90")
    assert _table(w) == {
        low: ("settled", D("1.00"), D("1.00")),
        high: ("settled", D("1.00"), D("2.50")),
    }
    # the table says what is booked (Q9): the counters equal the sum of settled_usd
    assert w.run("SELECT sum(settled_usd) FROM spend_reservations")[0][0] == D("3.50")


# --- concurrency ---------------------------------------------------------------------------------------------------


def _together(calls):
    """Run the callables at once (one thread each, one Barrier); returns their results or their exceptions."""
    gate = threading.Barrier(len(calls))
    results = [None] * len(calls)

    def one(i, call):
        try:
            gate.wait(timeout=WAIT_S)
            results[i] = call()
        except Exception as exc:  # noqa: BLE001 - reported through the result list
            results[i] = exc

    threads = [threading.Thread(target=one, args=(i, c)) for i, c in enumerate(calls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2 * WAIT_S)
    assert not [t for t in threads if t.is_alive()], "a caller never came back"
    return results


@pg
def test_settle_from_8_connections_with_different_amounts_books_exactly_one(w):
    stores = [w.store(w.runtime) for _ in range(8)]
    assert len({s._db.info.backend_pid for s in stores}) == 8
    run_id = _new_run(stores[0])
    for _round in range(5):
        before = _counters(w)[0] or D(0)
        cost = stores[0].get_run(run_id).cost_usd
        rid = _reserve(stores[0], "1.00", run_id=run_id)
        amounts = [D(n) / 10 for n in range(1, 9)]
        results = _together(
            [
                lambda s=s, a=a, r=rid: s.settle_spend(r, a)
                for s, a in zip(stores, amounts, strict=True)
            ]
        )
        assert not [r for r in results if isinstance(r, Exception)], results
        assert sorted(applied for _, applied in results) == [False] * 7 + [True]
        winner = next(row for row, applied in results if applied)
        assert winner.settled_usd in amounts
        assert all(row == winner for row, _ in results)  # every caller gets the stored row
        assert _counters(w)[0] - before == winner.settled_usd  # one amount is booked, once
        assert stores[0].get_run(run_id).cost_usd - cost == winner.settled_usd
    assert _counters(w)[0] == _counters(w)[1]


@pg
@pytest.mark.parametrize("actual", ["0.25", "1.75"])
def test_settle_racing_the_expire_step_never_lowers_a_booking(w, actual):
    """Many rounds, either may win. If the expiry won, the worst case stays (a lower settle changes no counter); if
    the settle won, the row was open and the actual amount is booked. Never anything else."""
    a, b = w.store(w.runtime), w.store(w.runtime)
    run_id = _new_run(a)
    orders = set()
    for n in range(40):
        agent = f"race-{n}"
        rid = _reserve(a, "1.00", agent=agent, run_id=run_id)
        settled, expired = _together(
            [lambda r=rid: a.settle_spend(r, D(actual)), lambda: b.expire_spend_reservations(0)]
        )
        assert not isinstance(settled, Exception) and not isinstance(expired, Exception)
        row, applied = settled
        assert applied is True and expired in (0, 1)
        orders.add(expired)
        booked = max(D(actual), D("1.00")) if expired else D(actual)
        assert (row.status, row.settled_usd) == ("settled", booked), f"round {n} expired={expired}"
        assert _table(w)[rid] == ("settled", D("1.00"), booked)
        assert _counters(w, agent) == (booked, booked), f"round {n} expired={expired}"
    assert a.get_run(run_id).cost_usd == 40 * D(actual)  # the run always gets the real amount, once
    assert orders <= {0, 1}


@pg
@pytest.mark.parametrize("actual,booked", [("0.25", "1.00"), ("1.75", "1.75")])
def test_a_settle_that_waits_for_an_uncommitted_expiry_sees_the_row_as_expired(w, actual, booked):
    """The deterministic form of the race: the expiry has changed the row and not committed; the settle waits on
    the row lock and, once the expiry commits, must treat the row as expired (its status after the wait)."""
    a, b = w.store(w.runtime), w.store(w.runtime)
    rid = _reserve(a, "1.00")
    result = []
    t = threading.Thread(target=lambda: result.append(a.settle_spend(rid, D(actual))))
    with b._db.transaction():
        assert b.expire_spend_reservations(0) == 1
        t.start()
        waited = _waits_on_a_lock(w, a._db.info.backend_pid)
    t.join(timeout=WAIT_S)
    assert waited, "the settle never waited on the expiry: the two did not overlap"
    row, applied = result[0]
    assert applied is True and (row.status, row.settled_usd) == ("settled", D(booked))
    assert _counters(w) == (D(booked), D(booked))


@pg
def test_an_expiry_that_waits_for_an_uncommitted_settle_expires_nothing(w):
    a, b = w.store(w.runtime), w.store(w.runtime)
    rid = _reserve(a, "1.00")
    result = []
    t = threading.Thread(target=lambda: result.append(a.expire_spend_reservations(0)))
    with b._db.transaction():
        assert b.settle_spend(rid, D("0.25"))[1] is True
        t.start()
        waited = _waits_on_a_lock(w, a._db.info.backend_pid)
    t.join(timeout=WAIT_S)
    assert waited, "the expiry never waited on the settle: the two did not overlap"
    assert result == [0]
    assert _table(w) == {rid: ("settled", D("1.00"), D("0.25"))}
    assert _counters(w) == (D("0.25"), D("0.25"))


@pg
def test_the_store_session_is_read_committed_and_the_age_is_the_database_clock(w):
    rt = w.store(w.runtime)
    assert rt._db.execute("SHOW transaction_isolation").fetchone()[0] == "read committed"
    rid = _reserve(rt)
    stamped, clock = w.run("SELECT created_at, clock_timestamp() FROM spend_reservations")[0]
    assert (
        abs((clock - stamped).total_seconds()) < WAIT_S
    )  # set by the server, not passed by the caller
    assert w.run(
        "SELECT column_default FROM information_schema.columns WHERE table_schema = %s "
        "AND table_name = %s AND column_name = 'created_at'",
        (w.schema, TABLE),
    )[0][0].startswith("clock_timestamp()")
    assert rt.expire_spend_reservations(3600) == 0 and _table(w)[rid][0] == "open"


# --- rights --------------------------------------------------------------------------------------------------------


def _column_rights(w, role):
    q = "SELECT has_column_privilege(%s, %s, %s, %s)"
    table = f"{w.schema}.{TABLE}"
    return {
        (c, p)
        for c in COLUMNS
        for p in ("SELECT", "INSERT", "UPDATE", "REFERENCES")
        if w.run(q, (role, table, c, p))[0][0]
    }


@pg
def test_the_four_roles_hold_exactly_the_rights_of_the_ticket_on_the_table(w):
    assert GRANTS[TABLE].kind == "table"
    assert w.rights(w.runtime)[TABLE] == {"SELECT", "INSERT", "UPDATE"}
    assert w.rights(w.purge)[TABLE] == {"DELETE"}
    assert _column_rights(w, w.purge) == {("status", "SELECT"), ("closed_at", "SELECT")}
    for role in (w.portal, w.reset):
        assert TABLE not in w.rights(role), role
        assert _column_rights(w, role) == set(), role
    for role in (w.purge, w.portal, w.reset):
        assert not {"spend", "spend_month"} & set(w.rights(role)), role
    index = w.run(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND indexname = %s",
        (w.schema, "spend_reservations_open"),
    )
    assert index and "created_at" in index[0][0] and "open" in index[0][0]


INSERT = (
    "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd) "
    "VALUES ('x', 'a', CURRENT_DATE, 1)"
)
PURGE_DENIED = [
    (TABLE, "SELECT reserved_usd FROM spend_reservations"),
    (TABLE, "SELECT agent_id FROM spend_reservations"),
    (TABLE, "SELECT run_id FROM spend_reservations"),
    (TABLE, "SELECT reservation_id FROM spend_reservations"),
    (TABLE, "SELECT settled_usd FROM spend_reservations"),
    (TABLE, "SELECT day FROM spend_reservations"),
    (TABLE, "SELECT created_at FROM spend_reservations"),
    (TABLE, "SELECT * FROM spend_reservations"),
    (TABLE, INSERT),
    (TABLE, "UPDATE spend_reservations SET status = 'open', settled_usd = NULL, closed_at = NULL"),
    (TABLE, "UPDATE spend_reservations SET closed_at = now() - interval '900 days'"),
    (TABLE, "UPDATE spend_reservations SET reserved_usd = 0"),
    (TABLE, "DELETE FROM spend_reservations WHERE reserved_usd >= 0"),
    (TABLE, "DELETE FROM spend_reservations WHERE agent_id = 'agent-a'"),
    (TABLE, "DELETE FROM spend_reservations RETURNING reserved_usd"),
    (TABLE, "TRUNCATE spend_reservations"),
    ("spend", "SELECT 1 FROM spend"),
    ("spend", "INSERT INTO spend (agent_id, day, usd) VALUES ('a', CURRENT_DATE, 0)"),
    ("spend", "UPDATE spend SET usd = 0"),
    ("spend", "DELETE FROM spend"),
    ("spend", "TRUNCATE spend"),
    ("spend_month", "SELECT 1 FROM spend_month"),
    ("spend_month", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('a', CURRENT_DATE, 0)"),
    ("spend_month", "UPDATE spend_month SET usd = 0"),
    ("spend_month", "DELETE FROM spend_month"),
    ("spend_month", "TRUNCATE spend_month"),
]  # fmt: skip


def _seeded(w):
    """One open and one settled reservation; returns what the owner sees."""
    rt = w.store(w.runtime)
    _reserve(rt, "1.00")
    rt.settle_spend(_reserve(rt, "1.00"), D("0.40"))
    return _table(w), _counters(w)


@pg
@pytest.mark.parametrize("relation,statement", PURGE_DENIED, ids=[s[:44] for _, s in PURGE_DENIED])
def test_the_purge_login_is_denied(w, relation, statement):
    before = _seeded(w)
    _denied(w, w.purge, statement, relation)
    assert (_table(w), _counters(w)) == before


@pg
def test_the_purge_login_can_run_the_purge_delete_and_removes_settled_rows_only(w):
    rt = w.store(w.runtime)
    opened, closed, expired = _reserve(rt), _reserve(rt), _reserve(rt)
    rt.settle_spend(closed, D("0.40"))
    _age(w, expired, 4000)
    assert rt.expire_spend_reservations(3600) == 1
    with w.as_(w.purge) as db:  # the statement itself, as the purge login
        assert db.execute(
            "SELECT status FROM spend_reservations WHERE closed_at IS NULL"
        ).fetchall()
        gone = db.execute(
            "DELETE FROM spend_reservations WHERE status = 'settled' AND closed_at < %s",
            (now() - timedelta(days=1),),
        ).rowcount
        assert gone == 0  # closed a moment ago: kept
    purge = w.store(w.purge)
    assert (
        purge.purge_spend_reservations(now() + timedelta(days=1)) == 1
    )  # the settled row; expired is kept (E11 M3)
    assert set(_table(w)) == {opened, expired}
    assert _counters(w) == (D("2.40"), D("2.40"))  # a purge moves no counter
    assert purge.purge_spend_reservations(now() + timedelta(days=1)) == 0


@pg
def test_the_purge_login_cannot_use_the_other_three_methods(w):
    rt, purge = w.store(w.runtime), w.store(w.purge)
    rid = _reserve(rt)
    with pytest.raises(DENIED):
        _reserve(purge)
    with pytest.raises(DENIED):
        purge.settle_spend(rid, D("0.10"))
    with pytest.raises(DENIED):
        purge.expire_spend_reservations(0)
    assert _table(w) == {rid: ("open", D("1.00"), None)}


@pg
def test_the_runtime_login_cannot_delete_or_truncate_reservations(w):
    before = _seeded(w)
    _denied(w, w.runtime, "DELETE FROM spend_reservations", TABLE)
    _denied(w, w.runtime, "TRUNCATE spend_reservations", TABLE)
    with pytest.raises(DENIED):
        w.store(w.runtime).purge_spend_reservations(now() + timedelta(days=1))
    assert (_table(w), _counters(w)) == before


NO_RIGHT = [
    "SELECT 1 FROM spend_reservations",
    "SELECT status FROM spend_reservations",
    "SELECT closed_at FROM spend_reservations",
    "SELECT count(*) FROM spend_reservations",
    INSERT,
    "UPDATE spend_reservations SET reserved_usd = 0",
    "DELETE FROM spend_reservations",
    "DELETE FROM spend_reservations WHERE status <> 'open'",
    "TRUNCATE spend_reservations",
]


@pg
@pytest.mark.parametrize("who", ["portal", "reset"])
@pytest.mark.parametrize("statement", NO_RIGHT, ids=[s[:40] for s in NO_RIGHT])
def test_the_portal_and_the_reset_login_hold_no_right_at_all(w, who, statement):
    before = _seeded(w)
    role = getattr(w, who)
    assert w.run("SELECT has_schema_privilege(%s, %s, 'USAGE')", (role, w.schema))[0][0], (
        "the login cannot even see the schema: a refusal would prove nothing about the table"
    )
    _denied(w, role, statement, TABLE)
    assert (_table(w), _counters(w)) == before


@pg
@pytest.mark.parametrize("who", ["portal", "reset"])
def test_the_portal_and_the_reset_login_cannot_use_any_of_the_four_methods(w, who):
    rt, other = w.store(w.runtime), w.store(getattr(w, who))
    rid = _reserve(rt)
    for call in (
        lambda: _reserve(other),
        lambda: other.settle_spend(rid, D("0.10")),
        lambda: other.expire_spend_reservations(0),
        lambda: other.purge_spend_reservations(now() + timedelta(days=1)),
    ):
        with pytest.raises(DENIED):
            call()
    assert _table(w) == {rid: ("open", D("1.00"), None)}


@pg
def test_a_hand_grant_of_delete_to_the_runtime_role_is_removed_by_migrate(w):
    w.grant("GRANT DELETE ON spend_reservations TO {}", w.runtime)
    w.grant("GRANT TRUNCATE ON spend_reservations TO {}", w.runtime)
    assert {"DELETE", "TRUNCATE"} <= w.rights(w.runtime)[TABLE]
    assert w.migrate() == []  # nothing to apply and no problem reported
    assert w.rights(w.runtime)[TABLE] == {"SELECT", "INSERT", "UPDATE"}
    _denied(w, w.runtime, "DELETE FROM spend_reservations", TABLE)


@pg
def test_a_hand_grant_to_the_purge_role_is_removed_by_migrate(w):
    w.grant("GRANT SELECT, UPDATE ON spend_reservations TO {}", w.purge)
    assert w.migrate() == []
    assert w.rights(w.purge)[TABLE] == {"DELETE"}
    _denied(w, w.purge, "SELECT reserved_usd FROM spend_reservations", TABLE)


@pg
def test_a_runtime_role_that_inherits_delete_through_another_role_is_refused_by_migrate(w):
    extra = w.new_role("ex", "NOLOGIN")
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, extra)
    w.grant("GRANT DELETE ON spend_reservations TO {}", extra)
    w.grant("GRANT {} TO {}", extra, w.runtime)
    with pytest.raises(
        ConfigError, match=r"runtime role holds more than the grant map.*DELETE spend_reservations"
    ):
        w.migrate()
    w.grant("REVOKE {} FROM {}", extra, w.runtime)
    assert w.migrate() == []


@pg
def test_the_table_checks_refuse_what_the_store_never_writes(w):
    """The CHECKs of 0007 as the last line: NaN, Infinity, a negative amount, an open row with a settled amount,
    an expired row whose booked amount is not the reserved one."""
    insert = (
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, "
        "status, closed_at) VALUES (%s, 'a', CURRENT_DATE, %s, %s, %s, %s)"
    )
    at = now()
    bad = [
        (D("NaN"), None, "open", None),
        (D("Infinity"), None, "open", None),
        (D("-1"), None, "open", None),
        (D(10**9), None, "open", None),
        (D(1), D("NaN"), "settled", at),
        (D(1), D(1), "open", None),
        (D(1), None, "open", at),
        (D(1), None, "settled", at),
        (D(1), D(1), "settled", None),
        (D(1), D("0.5"), "expired", at),
        (D(1), D(1), "released", at),
    ]
    with w.as_(w.runtime) as db:
        for n, row in enumerate(bad):
            with pytest.raises(errors.CheckViolation):
                db.execute(insert, (f"bad-{n}", *row))
        db.execute(insert, ("good", D(1), D(1), "expired", at))
    assert set(_table(w)) == {"good"}


# --- the tick step (no database: a stand-in app on the memory store) --------------------------------------------------


def _app(store, agents=None, llm=None, purge_store=None):
    hooks = SimpleNamespace(hold_run_ids=None)
    return SimpleNamespace(
        store=store,
        purge_store=purge_store,
        registry=SimpleNamespace(agents=agents or {}),
        config=SimpleNamespace(
            backends=SimpleNamespace(llm=llm or SimpleNamespace()), retention=Retention()
        ),
        approvals=SimpleNamespace(clock=now),
        runtime=SimpleNamespace(hooks=hooks),
    )


def _agent(max_steps):
    return SimpleNamespace(max_steps=max_steps)


def _longest_quiet_s(max_steps, call_timeout_s, max_attempts):
    """The stuck-run age as the design states it (12.7), worked out here and not taken from the code."""
    return max_steps * call_timeout_s * max_attempts + 60


def test_the_step_is_the_last_one_and_comes_after_audit_drain():
    names = [s.name for s in tick.STEPS]
    assert names[-1] == "expire_reservations", names
    assert names.count("expire_reservations") == 1
    assert names.index("audit_drain") < names.index("expire_reservations")
    last = tick.STEPS[-1]
    assert last.fn is tick.expire_reservations and last.every_s == 0 and last.interval is None


def test_the_step_expires_old_reservations_and_keeps_young_ones_and_the_totals():
    store = MemoryStore()
    app = _app(store)
    age = tick.reservation_expire_s(app)
    old, young = _reserve(store, "1.00"), _reserve(store, "0.25")
    _older(store, old, age + 5)
    _older(store, young, age - 600)
    assert run_tick(app, now=now(), steps=[tick.STEPS[-1]]) == 0
    rows = _rows(store)
    assert (rows[old].status, rows[old].settled_usd) == ("expired", D("1.00"))
    assert rows[young].status == "open"
    assert store.spend_totals(AGENT, DAY) == (D("1.25"), D("1.25"))
    state = store.get_tick_state("expire_reservations")
    assert state.last_error is None and state.last_ok_at is not None


def test_the_step_uses_the_longer_age_while_a_run_could_still_be_working():
    store = MemoryStore()
    llm = SimpleNamespace(call_timeout_s=60, max_attempts=2)
    app = _app(store, {"slow": _agent(200)}, llm)
    rid = _reserve(store, "1.00")
    _older(
        store, rid, defaults.RESERVATION_EXPIRE_S + 600
    )  # past the default, inside the run's quiet time
    assert run_tick(app, now=now(), steps=[tick.STEPS[-1]]) == 0
    assert _rows(store)[rid].status == "open"
    _older(store, rid, _longest_quiet_s(200, 60, 2))
    assert run_tick(app, now=now(), steps=[tick.STEPS[-1]]) == 0
    assert _rows(store)[rid].status == "expired"


def test_a_failing_store_marks_the_step_failed_and_the_other_steps_still_run(caplog):
    store = MemoryStore()
    ran = []

    def down(older_than_s):
        raise RuntimeError("expire failed\nsecond line")

    store.expire_spend_reservations = down
    steps = [
        TickStep("before", 0, lambda ctx: ran.append("before")),
        tick.STEPS[-1],
        TickStep("after", 0, lambda ctx: ran.append("after")),
    ]
    with caplog.at_level("INFO", logger="hadavin_sdk.tick"):
        assert run_tick(_app(store), now=now(), steps=steps) == 1
    assert ran == ["before", "after"]
    state = store.get_tick_state("expire_reservations")
    assert state.last_error.startswith("RuntimeError: ") and state.last_ok_at is None
    assert store.get_tick_state("after").last_error is None
    assert "step=expire_reservations error_kind=RuntimeError" in caplog.text
    assert "failed=expire_reservations" in caplog.text


def test_the_expiry_age_with_two_agents_is_the_larger_of_their_quiet_times():
    llm = SimpleNamespace(call_timeout_s=60, max_attempts=2)
    quick, slow = _longest_quiet_s(10, 60, 2), _longest_quiet_s(200, 60, 2)
    assert quick < defaults.RESERVATION_EXPIRE_S < slow
    for agents in (
        {"quick": _agent(10), "slow": _agent(200)},
        {"slow": _agent(200), "quick": _agent(10)},
    ):
        assert tick.reservation_expire_s(_app(None, agents, llm)) == slow
    longer = _longest_quiet_s(300, 60, 2)
    both = {"slow": _agent(200), "slower": _agent(300)}
    assert tick.reservation_expire_s(_app(None, both, llm)) == longer


def test_the_expiry_age_is_never_below_the_default():
    llm = SimpleNamespace(call_timeout_s=60, max_attempts=2)
    assert defaults.RESERVATION_EXPIRE_S == 3600 and type(defaults.RESERVATION_EXPIRE_S) is int
    assert (
        tick.reservation_expire_s(_app(None)) == defaults.RESERVATION_EXPIRE_S
    )  # no agents at all
    two = {"a": _agent(1), "b": _agent(10)}
    assert tick.reservation_expire_s(_app(None, two, llm)) == defaults.RESERVATION_EXPIRE_S


def test_the_expiry_age_is_rounded_up_to_a_whole_second():
    llm = SimpleNamespace(call_timeout_s=0.25, max_attempts=1)
    exact = _longest_quiet_s(14201, 0.25, 1)
    assert exact == 3610.25
    age = tick.reservation_expire_s(_app(None, {"a": _agent(14201)}, llm))
    assert age == 3611 and type(age) is int


def test_the_evidence_purge_also_purges_closed_reservations_before_the_hook():
    store = MemoryStore()
    opened, old, recent = (_reserve(store) for _ in range(3))
    for rid in (old, recent):
        store.settle_spend(rid, D("0.40"))
    ceiling = Retention().held_tool_calls_max_days
    with store._lock:
        row = store._reservations[old]
        store._reservations[old] = row.model_copy(
            update={"closed_at": row.closed_at - timedelta(days=ceiling + 1)}
        )
    app = _app(MemoryStore(), purge_store=store)  # the deleting identity is the one that is asked

    def hook():
        raise RuntimeError("hook down")

    app.runtime.hooks.hold_run_ids = hook
    with contextlib.suppress(
        Exception
    ):  # the step fails because of the hook; the ceilings ran before it
        tick.purge_evidence(TickContext(app, now()))
    assert set(_rows(store)) == {opened, recent}
    with pytest.raises(NotFound):
        store.settle_spend(old, D("0.10"))


# --- the tick step on PostgreSQL, as the runtime login ---------------------------------------------------------------


@pg
def test_the_step_runs_as_the_runtime_login_and_expires_only_old_rows(w):
    rt = w.store(w.runtime)
    old, young = _reserve(rt, "1.00"), _reserve(rt, "0.25")
    _age(w, old, defaults.RESERVATION_EXPIRE_S + 5)
    _age(w, young, defaults.RESERVATION_EXPIRE_S - 600)
    assert run_tick(_app(rt), now=now(), steps=[tick.STEPS[-1]]) == 0
    assert _table(w) == {old: ("expired", D("1.00"), D("1.00")), young: ("open", D("0.25"), None)}
    assert _counters(w) == (D("1.25"), D("1.25"))
    assert rt.get_tick_state("expire_reservations").last_error is None


@pg
def test_the_step_fails_and_the_next_step_runs_when_the_runtime_login_lost_its_execute_right_on_expire(
    w,
):
    rt = w.store(w.runtime)
    rid = _reserve(rt, "1.00")
    _age(w, rid, defaults.RESERVATION_EXPIRE_S + 5)
    w.grant(  # the expire is a definer function now: the right that matters is EXECUTE on it
        "REVOKE EXECUTE ON FUNCTION {}.hadavin_expire_spend_reservations(integer) FROM {}",
        w.schema,
        w.runtime,
    )
    ran = []
    steps = [tick.STEPS[-1], TickStep("after", 0, lambda ctx: ran.append("after"))]
    assert run_tick(_app(rt), now=now(), steps=steps) == 1
    assert ran == ["after"]
    assert rt.get_tick_state("expire_reservations").last_error.startswith("InsufficientPrivilege")
    assert _table(w) == {rid: ("open", D("1.00"), None)}

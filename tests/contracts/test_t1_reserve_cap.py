"""T1 (step F-store, invariant 1): the cap check and the booking are one statement, so 50 callers on 50 connections
cannot all pass the cap. PostgreSQL only: one store object is one connection behind one lock, so threads on ONE
store would prove nothing. With HADAVIN_TEST_PG_DSN set nothing here is skipped.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/F-store.md, test plan "T1",
cb-7, cb-14, cb-17 and Q8), not from the code. Every case has a fresh schema and its own non-superuser logins
(`World` of tests/test_stop_state_roles.py); the 50 callers are the runtime login on 50 connections, they start
behind one Barrier, nobody settles before all have decided, and the total is read from a 51st connection.

Invariant 1 is stated for an amount above zero, a counter that starts at 0 and no settle in between; that is what
these cases set up. `test_control_...` runs the OLD pattern (read the total, then `add_spend`) on the same schedule
and shows that the verdict used by every case here does fail when the check and the booking are two steps.
Do not run this file in parallel with itself: each case holds 51 connections (the CI server allows 100)."""

from __future__ import annotations

import os
import threading
from datetime import date, timedelta
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.models import new_id, now
from hadavin_sdk.store.protocol import SpendCapExceeded
from tests.test_stop_state_roles import World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
CALLERS = 50
AGENT = "agent-t1"
DAY = date(now().year - 1, 1, 31)
WORST = D("1.00")
BIG = D("1000")
WAIT_S = 60


@pytest.fixture(name="w")
def t1_world():
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


def _read_committed(stores):
    for s in stores:
        level = s._db.execute("SHOW transaction_isolation").fetchone()[0]
        assert level == "read committed", f"a store connection runs at {level}"


def _callers(w):
    """50 stores of the runtime login on 50 distinct server processes, plus a 51st connection to read with."""
    stores = [w.store(w.runtime) for _ in range(CALLERS)]
    reader = w.store(w.runtime)
    pids = {s._db.execute("SELECT pg_backend_pid()").fetchone()[0] for s in stores}
    assert len(pids) == CALLERS, "the callers do not have a connection each"
    assert reader._db.execute("SELECT pg_backend_pid()").fetchone()[0] not in pids
    for s in (*stores, reader):
        assert s._db.execute("SELECT current_user").fetchone()[0] == w.runtime
    return stores, reader


def _together(stores, work):
    """Run `work(i, store)` once per store, each in its own thread, all released by one Barrier. Returns one
    outcome per caller: "granted", "day" / "month" (the cap that refused) or the error that ended the call."""
    gate = threading.Barrier(len(stores))
    outcomes = [None] * len(stores)

    def one(i, store):
        try:
            gate.wait(timeout=WAIT_S)
            outcomes[i] = work(i, store)
        except SpendCapExceeded as exc:
            outcomes[i] = exc.which
        except Exception as exc:  # noqa: BLE001 - reported through the outcome list
            outcomes[i] = f"{type(exc).__name__}: {str(exc)[:120]}"

    threads = [threading.Thread(target=one, args=(i, s)) for i, s in enumerate(stores)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2 * WAIT_S)
    assert not [t for t in threads if t.is_alive()], "a caller never came back"
    return outcomes


def _reserve(day_cap, month_cap=BIG, agent=lambda i: AGENT):
    def work(i, store):
        store.reserve_spend(
            new_id("res"), agent(i), DAY, WORST, day_cap=day_cap, month_cap=month_cap
        )
        return "granted"

    return work


def _verdict(outcomes, total, *, granted, refused_by, cap):
    """The T1 verdict: exactly floor(cap / worst) grants, every other caller refused by the cap, the counter
    equal to the grants and never above the cap."""
    counts = {o: outcomes.count(o) for o in set(outcomes)}
    assert counts == {"granted": granted, refused_by: len(outcomes) - granted}, counts
    assert total == granted * WORST, f"the counter holds {total} for {granted} grants"
    assert total <= cap, f"the counter {total} is above the cap {cap}"


def _open_rows(w):
    return w.run("SELECT status, reserved_usd, settled_usd FROM spend_reservations")


def _t1(w, stores, reader):
    cap = D("3.00")
    outcomes = _together(stores, _reserve(cap))
    day, month = reader.spend_totals(AGENT, DAY)  # the 51st connection, before any settle
    _verdict(outcomes, day, granted=3, refused_by="day", cap=cap)
    assert outcomes.count("day") == CALLERS - 3 == 47
    assert (day, month) == (D("3.00"), D("3.00"))
    assert _open_rows(w) == [("open", WORST, None)] * 3  # a refused caller left no row
    return outcomes


def test_t1_cap_3_and_worst_1_grants_exactly_3_of_50(w):
    stores, reader = _callers(w)
    _read_committed([*stores, reader])
    outcomes = _t1(w, stores, reader)
    # afterwards the three settle: the worst case is replaced, and the freed budget can be reserved again
    winners = [r[0] for r in w.run("SELECT reservation_id FROM spend_reservations")]
    for rid in winners:
        assert stores[0].settle_spend(rid, D("0.10"), agent_id=AGENT)[1] is True
    assert reader.spend_totals(AGENT, DAY) == (D("0.30"), D("0.30"))
    again = _together(stores, _reserve(D("3.00")))
    assert (
        again.count("granted") == 2 and again.count("day") == CALLERS - 2
    )  # 0.30 + 2 x 1.00 fits, a third not
    assert reader.spend_totals(AGENT, DAY)[0] == D("2.30")
    assert len(outcomes) == CALLERS


def test_t1_cap_2_50_grants_exactly_2(w):
    stores, reader = _callers(w)
    cap = D("2.50")
    outcomes = _together(stores, _reserve(cap))
    day, month = reader.spend_totals(AGENT, DAY)
    _verdict(outcomes, day, granted=2, refused_by="day", cap=cap)
    assert (day, month) == (D("2.00"), D("2.00"))
    assert len(_open_rows(w)) == 2


def test_t1_the_month_cap_binds_when_it_is_the_lower_one(w):
    stores, reader = _callers(w)
    cap = D("3.00")
    outcomes = _together(stores, _reserve(BIG, month_cap=cap))
    day, month = reader.spend_totals(AGENT, DAY)
    _verdict(outcomes, month, granted=3, refused_by="month", cap=cap)
    assert day == D("3.00"), "a caller refused by the month cap left its day booking behind"
    assert len(_open_rows(w)) == 3


def test_t1_the_month_cap_holds_across_two_days_of_the_month(w):
    stores, reader = _callers(w)
    cap, eve = D("3.00"), DAY - timedelta(days=1)

    def work(i, store):
        store.reserve_spend(
            new_id("res"), AGENT, DAY if i % 2 else eve, WORST, day_cap=BIG, month_cap=cap
        )
        return "granted"

    outcomes = _together(stores, work)
    one, month = reader.spend_totals(AGENT, DAY)
    other, _ = reader.spend_totals(AGENT, eve)
    _verdict(outcomes, month, granted=3, refused_by="month", cap=cap)
    assert one + other == D("3.00")


def test_t1_fifty_agents_with_one_caller_each_do_not_block_each_other(w):
    stores, reader = _callers(w)
    outcomes = _together(stores, _reserve(WORST, WORST, agent=lambda i: f"agent-{i}"))
    assert outcomes == ["granted"] * CALLERS
    for i in range(CALLERS):
        assert reader.spend_totals(f"agent-{i}", DAY) == (WORST, WORST)
    assert len(_open_rows(w)) == CALLERS
    again = _together(stores, _reserve(WORST, WORST, agent=lambda i: f"agent-{i}"))
    assert again == ["day"] * CALLERS  # every agent is at its own cap now


def test_control_the_old_check_then_add_spend_pattern_admits_more_than_3(w):
    """The same schedule with the check and the booking as two steps (the pattern before this step: `blocked`
    reads, `charge` books). It must go over the cap, and the T1 verdict must say so: this shows T1 can fail."""
    stores, reader = _callers(w)
    cap = D("3.00")
    checked = threading.Barrier(CALLERS)

    def old_pattern(i, store):
        booked, _ = store.spend_totals(AGENT, DAY)
        checked.wait(timeout=WAIT_S)  # every caller has done its check before any of them books
        if booked + WORST > cap:
            raise SpendCapExceeded("day")
        store.add_spend(AGENT, DAY, WORST)
        return "granted"

    outcomes = _together(stores, old_pattern)
    day, _ = reader.spend_totals(AGENT, DAY)
    assert outcomes.count("granted") > 3, outcomes
    assert day > cap
    with pytest.raises(AssertionError):
        _verdict(outcomes, day, granted=3, refused_by="day", cap=cap)


def test_t1_with_a_role_default_of_repeatable_read_still_grants_exactly_3(w):
    """Q8: the session is pinned to READ COMMITTED by `connect()`. A role whose default is REPEATABLE READ would
    otherwise turn the row-lock wait of the conditional UPDATE into a serialization error."""
    w.grant("ALTER ROLE {} SET default_transaction_isolation TO 'repeatable read'", w.runtime)
    with w.as_(w.runtime) as plain:  # a plain connection of that login really gets the role default
        assert (
            plain.execute("SHOW default_transaction_isolation").fetchone()[0] == "repeatable read"
        )
        assert plain.execute("SHOW transaction_isolation").fetchone()[0] == "repeatable read"
    stores, reader = _callers(w)
    _t1(w, stores, reader)  # the behaviour first: no caller ends in a serialization error
    _read_committed([*stores, reader])
    # the settle path waits on the same rows: eight settles of one id under that role default, one applies
    rid = w.run("SELECT reservation_id FROM spend_reservations LIMIT 1")[0][0]
    applied = _together(stores[:8], lambda i, s: s.settle_spend(rid, D("0.25"), agent_id=AGENT)[1])
    assert sorted(applied, key=str) == [False] * 7 + [True]
    assert reader.spend_totals(AGENT, DAY)[0] == D("2.25")

"""T1 (step F-store, invariant 1): the cap check and the booking are one statement, so 50 callers on 50 connections
cannot all pass the cap. The 50-connection cases are PostgreSQL only: one store object is one connection behind one
lock, so threads on ONE store would prove nothing. They carry `needs_pg` and are skipped without
HADAVIN_TEST_PG_DSN; the `*_sequential_*` cases at the end take the contract `store` fixture and run on every kind
(memory and postgres). With HADAVIN_TEST_PG_DSN set nothing here is skipped.

The extra cases taken from core-a's version of this file (settle of one hold from 50 connections with 50 amounts,
settles racing the expiry sweep, the grants of the runtime, purge, portal and reset logins on spend_reservations,
and the row / still-shut / settle-at-worst checks after the cap case) are marked "core-a" in their docstrings.

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

from hadavin_sdk.models import Run, new_id, now
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, StaleState

try:
    import psycopg
    from psycopg import sql

    from tests.test_stop_state_roles import World
except ModuleNotFoundError:  # no hadavin-sdk[pg]: the sequential cases still run on the memory kind
    psycopg = sql = World = None

needs_pg = pytest.mark.skipif(
    psycopg is None or not os.environ.get("HADAVIN_TEST_PG_DSN"),
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


@needs_pg
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


@needs_pg
def test_t1_cap_2_50_grants_exactly_2(w):
    stores, reader = _callers(w)
    cap = D("2.50")
    outcomes = _together(stores, _reserve(cap))
    day, month = reader.spend_totals(AGENT, DAY)
    _verdict(outcomes, day, granted=2, refused_by="day", cap=cap)
    assert (day, month) == (D("2.00"), D("2.00"))
    assert len(_open_rows(w)) == 2


@needs_pg
def test_t1_the_month_cap_binds_when_it_is_the_lower_one(w):
    stores, reader = _callers(w)
    cap = D("3.00")
    outcomes = _together(stores, _reserve(BIG, month_cap=cap))
    day, month = reader.spend_totals(AGENT, DAY)
    _verdict(outcomes, month, granted=3, refused_by="month", cap=cap)
    assert day == D("3.00"), "a caller refused by the month cap left its day booking behind"
    assert len(_open_rows(w)) == 3


@needs_pg
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


@needs_pg
def test_t1_fifty_agents_with_one_caller_each_do_not_block_each_other(w):
    stores, reader = _callers(w)
    outcomes = _together(stores, _reserve(WORST, WORST, agent=lambda i: f"agent-{i}"))
    assert outcomes == ["granted"] * CALLERS
    for i in range(CALLERS):
        assert reader.spend_totals(f"agent-{i}", DAY) == (WORST, WORST)
    assert len(_open_rows(w)) == CALLERS
    again = _together(stores, _reserve(WORST, WORST, agent=lambda i: f"agent-{i}"))
    assert again == ["day"] * CALLERS  # every agent is at its own cap now


@needs_pg
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


@needs_pg
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


# --- cases taken from core-a's version of this file ------------------------------------------------------------


def _far_future():
    return now() + timedelta(days=1)


def _a_run(store):
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


@needs_pg
@pytest.mark.parametrize("which", ["day", "month"])
def test_t1_the_granted_rows_are_the_grants_the_cap_stays_shut_and_a_settle_at_worst_keeps_the_totals(
    w, which
):
    """core-a: after the 50 callers, the rows are exactly the three that were granted (each open at the worst
    case), a 51st reserve is still refused by the same cap, and settling the three at the worst case moves no
    counter. The same-cap-twice check also shows the refusal names the cap that binds."""
    stores, reader = _callers(w)
    cap = D("3.00")
    caps = (
        {"day_cap": cap, "month_cap": BIG} if which == "day" else {"day_cap": BIG, "month_cap": cap}
    )
    ids = {id(s): new_id("res") for s in stores}

    def work(i, store):
        store.reserve_spend(ids[id(store)], AGENT, DAY, WORST, **caps)
        return "granted"

    outcomes = _together(stores, work)
    total = reader.spend_totals(AGENT, DAY)[0 if which == "day" else 1]
    _verdict(outcomes, total, granted=3, refused_by=which, cap=cap)
    granted = sorted(ids[id(s)] for s, o in zip(stores, outcomes, strict=True) if o == "granted")
    rows = w.run("SELECT reservation_id, reserved_usd, status FROM spend_reservations ORDER BY 1")
    assert [(r[0], r[1], r[2]) for r in rows] == [(rid, WORST, "open") for rid in granted]
    with pytest.raises(SpendCapExceeded) as shut:  # the cap is still shut afterwards
        reader.reserve_spend(new_id("res"), AGENT, DAY, WORST, **caps)
    assert shut.value.which == which
    for rid in granted:
        assert reader.settle_spend(rid, WORST, agent_id=AGENT)[1] is True
    assert reader.spend_totals(AGENT, DAY) == (cap, cap)


@needs_pg
def test_t1_fifty_connections_settling_one_reservation_with_fifty_amounts_apply_it_once(w):
    """core-a (invariant 3, idempotent settle, from separate connections): 50 callers settle ONE hold with 50
    different amounts at once. Exactly one call applies; all 50 get the same stored row back; the counters and the
    cost of the run hold the winner's amount once."""
    stores, reader = _callers(w)
    run = _a_run(stores[0])
    rid = new_id("res")
    stores[0].reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    amounts = [D(i + 1) / 100 for i in range(CALLERS)]  # 0.01 .. 0.50

    results = _together(stores, lambda i, s: s.settle_spend(rid, amounts[i], agent_id=AGENT))
    assert not [r for r in results if isinstance(r, str)], results
    assert sum(1 for _, applied in results if applied) == 1
    winner = next(a for a, (_, applied) in zip(amounts, results, strict=True) if applied)
    assert {row for row, _ in results} == {results[0][0]}, "the callers saw different rows"
    assert (results[0][0].settled_usd, results[0][0].status) == (winner, "settled")
    assert reader.spend_totals(AGENT, DAY) == (winner, winner)
    assert reader.get_run(run.run_id).cost_usd == winner


@needs_pg
def test_t1_settles_racing_the_expiry_sweep_leave_the_counters_equal_to_the_rows(w):
    """core-a (invariants 3 and 4, "the counters can be reconciled from the table"): 40 callers each settle their
    own hold of 1.00 at 0.25 while 10 callers run the expiry sweep with age 0. Whichever comes first for a row,
    afterwards every row is settled, each says 0.25 (settled while open) or 1.00 (expired first: never down), and
    the day counter equals the sum over the rows; the run's cost is 40 times the real 0.25."""
    stores, reader = _callers(w)
    low = D("0.25")
    run = _a_run(stores[0])
    ids = [new_id("res") for _ in range(40)]
    for rid in ids:
        stores[0].reserve_spend(
            rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id
        )

    def work(i, store):
        if i < 40:
            return store.settle_spend(ids[i], low, agent_id=AGENT)
        return store.expire_spend_reservations(0)

    results = _together(stores[:50], work)
    assert not [r for r in results if isinstance(r, str)], results
    assert all(applied for _, applied in results[:40])  # each row's first settle, open or expired
    rows = w.run("SELECT status, settled_usd FROM spend_reservations")
    assert len(rows) == 40
    booked = [D(r[1]) for r in rows]
    expired_first = sum(1 for b in booked if b == WORST)
    assert {r[0] for r in rows} == {"settled"}
    assert set(booked) <= {low, WORST}
    assert expired_first == sum(results[40:])  # every row a sweep reported stayed at 1.00
    assert [row.settled_usd for row, _ in results[:40]].count(WORST) == expired_first
    assert reader.spend_totals(AGENT, DAY) == (sum(booked), sum(booked))
    assert reader.get_run(run.run_id).cost_usd == low * 40


# per-role negative tests: the grants on spend_reservations (the World has the four logins) ----------------------


DIRECT = (
    "SELECT * FROM spend_reservations",
    "SELECT status, closed_at FROM spend_reservations",
    "SELECT reserved_usd FROM spend_reservations",
    "INSERT INTO spend_reservations (reservation_id) VALUES ('res-x')",
    "UPDATE spend_reservations SET status = 'open'",
    "DELETE FROM spend_reservations",
    "TRUNCATE spend_reservations",
)


@needs_pg
def test_the_runtime_login_may_not_delete_reservations_or_touch_the_table_at_all(w):
    """core-a (runtime may not delete), adapted: the grants on spend_reservations are now NONE for every login (only
    the definer functions reach it), so besides DELETE and TRUNCATE the runtime login has no SELECT, INSERT or
    UPDATE either, and the purge method fails for it too (no EXECUTE on the purge function)."""
    store = w.store(w.runtime)
    rid = new_id("res")
    store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG)
    store.settle_spend(rid, WORST, agent_id=AGENT)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        store.purge_spend_reservations(_far_future())
    with w.as_(w.runtime) as db:
        for statement in DIRECT:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
    assert w.run("SELECT count(*) FROM spend_reservations") == [(1,)]


@needs_pg
def test_the_purge_login_deletes_closed_rows_through_the_function_and_reads_nothing(w):
    """core-a (purge deletes closed rows, reads only status and closed_at), adapted: the purge login deletes the
    settled row through its function and keeps the open one, but has no direct right on the table at all."""
    runtime, purge = w.store(w.runtime), w.store(w.purge)
    closed, kept = new_id("res"), new_id("res")
    for rid in (closed, kept):
        runtime.reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG)
    runtime.settle_spend(closed, WORST, agent_id=AGENT)
    assert purge.purge_spend_reservations(_far_future()) == 1
    assert (
        runtime.settle_spend(kept, WORST, agent_id=AGENT)[1] is True
    )  # the open row was not deleted
    assert w.run("SELECT reservation_id FROM spend_reservations") == [(kept,)]
    with w.as_(w.purge) as db:
        for statement in DIRECT:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


@needs_pg
@pytest.mark.parametrize("login", ["portal", "reset"])
def test_the_portal_and_reset_logins_may_not_touch_reservations(w, login):
    """core-a: portal none, reset none. The login itself works (`current_user`), so each refusal is about the
    rights on spend_reservations."""
    role = w.portal if login == "portal" else w.reset
    with w.as_(role) as db:
        assert db.execute("SELECT current_user").fetchone()[0] == role
        for statement in DIRECT:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


# sequential variants: run on every store kind (memory and postgres) -------------------------------------------


@pytest.mark.parametrize("which", ["day", "month"])
def test_sequential_cap_3_and_worst_1_grants_exactly_3_rows_cap_shut_settle_keeps_totals(
    store, which
):
    """core-a's cap case without threads, on every kind: the third reserve fits, the fourth is refused by the cap
    that binds and leaves nothing behind, and settling the three at the worst case moves no counter."""
    cap = D("3.00")
    caps = (
        {"day_cap": cap, "month_cap": BIG} if which == "day" else {"day_cap": BIG, "month_cap": cap}
    )
    ids = [new_id("res") for _ in range(3)]
    for rid in ids:
        store.reserve_spend(rid, AGENT, DAY, WORST, **caps)
    for _ in range(2):
        with pytest.raises(SpendCapExceeded) as shut:
            store.reserve_spend(new_id("res"), AGENT, DAY, WORST, **caps)
        assert shut.value.which == which
    assert store.spend_totals(AGENT, DAY) == (cap, cap)
    for rid in ids:
        assert store.settle_spend(rid, WORST, agent_id=AGENT)[1] is True
    assert store.spend_totals(AGENT, DAY) == (cap, cap)
    with pytest.raises(SpendCapExceeded):  # settled at the worst case keeps the cap shut
        store.reserve_spend(new_id("res"), AGENT, DAY, WORST, **caps)


def test_sequential_settle_of_one_hold_with_many_amounts_applies_the_first_only(store):
    """core-a's 50-amount settle without threads: the first call applies, every later one gets the same stored
    row back unapplied, and the counters and the run cost hold the first amount once."""
    run = _a_run(store)
    rid = new_id("res")
    store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    results = [store.settle_spend(rid, D(i + 1) / 100, agent_id=AGENT) for i in range(50)]
    assert [applied for _, applied in results] == [True] + [False] * 49
    assert {row for row, _ in results} == {results[0][0]}
    assert (results[0][0].settled_usd, results[0][0].status) == (D("0.01"), "settled")
    assert store.spend_totals(AGENT, DAY) == (D("0.01"), D("0.01"))
    assert store.get_run(run.run_id).cost_usd == D("0.01")


def test_sequential_settle_then_sweep_and_sweep_then_settle_end_at_the_row_totals(store):
    """core-a's settle/expire race, both orders: a hold settled while open stays at 0.25 and the sweep does not
    touch it; a hold the sweep expired first stays booked at 1.00 and the late settle is still applied (it is the
    hold's first settle) and never lowers the booking. The counters equal the sum of the rows."""
    low = D("0.25")
    run = _a_run(store)
    first, second = new_id("res"), new_id("res")
    store.reserve_spend(first, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    store.settle_spend(first, low, agent_id=AGENT)  # settle, then sweep
    store.reserve_spend(second, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    assert store.expire_spend_reservations(0) == 1  # only the open one
    row, applied = store.settle_spend(second, low, agent_id=AGENT)  # sweep, then settle
    assert applied is True and row.status == "settled"
    assert row.settled_usd == WORST, "a late settle lowered the booking of an expired hold"
    assert store.settle_spend(first, low, agent_id=AGENT)[0].settled_usd == low
    assert store.spend_totals(AGENT, DAY) == (low + WORST, low + WORST)
    assert store.get_run(run.run_id).cost_usd == low * 2


def test_sequential_a_retry_of_an_open_hold_is_success_and_of_a_closed_hold_is_stale(store):
    """The retry rule the cap case relies on: the same reserve again for an OPEN hold is the caller's own success
    (a cap now passed does not refuse it, nothing more is booked); after the settle it is StaleState."""
    rid = new_id("res")
    store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=WORST, month_cap=WORST)
    store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=WORST, month_cap=WORST)
    assert store.spend_totals(AGENT, DAY) == (WORST, WORST)
    store.settle_spend(rid, WORST, agent_id=AGENT)
    with pytest.raises(StaleState):
        store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG)
    assert store.spend_totals(AGENT, DAY) == (WORST, WORST)
    with pytest.raises(NotFound):  # and another agent's id is not this agent's hold
        store.settle_spend(rid, WORST, agent_id="agent-other")

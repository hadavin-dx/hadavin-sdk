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


# === cases merged from the core-a and core-c T1 files (the base of this file is core-b's) ========================
# Each case below pins an invariant none of the cases above pins. Skipped as duplicates (same invariant, another
# name): core-a/core-c "fifty stores are fifty backends" (`_callers` asserts it), "fifty connections against a cap of
# three" day and month (`test_t1_cap_3...`, `test_t1_the_month_cap_binds...`), the control case, the repeatable-read
# case, "the 51st connection reads the granted sum" (`_t1`), "a month cap over two days", "settles below the reserve
# free room" (`test_t1_cap_3...` settles three at 0.10 and gets exactly 2 more).
# Differences of API (core-b's): `settle_spend` takes `agent_id`; the caps passed to `reserve_spend` are seeded into
# `hadavin_caps` by the test-only wrapper of tests/conftest.py; the logins come from `World`.


def _rows(w):
    """{reservation_id: (reserved, settled, status, closed)} as the owner sees the table."""
    found = w.run(
        "SELECT reservation_id, reserved_usd, settled_usd, status, closed_at FROM spend_reservations"
    )
    return {
        r[0]: (D(r[1]), None if r[2] is None else D(r[2]), r[3], r[4] is not None) for r in found
    }


def _reserve_ids(stores, **kw):
    """Every store reserves once, all at once. Returns (outcomes, {caller index: reservation id})."""
    ids = {i: new_id("res") for i in range(len(stores))}
    day, cap = kw.pop("day", DAY), kw.pop("cap", D("3.00"))
    agent, usd = kw.pop("agent", lambda i: AGENT), kw.pop("usd", WORST)

    def work(i, store):
        store.reserve_spend(ids[i], agent(i), day, usd, day_cap=cap, month_cap=cap)
        return "granted"

    return _together(stores, work), ids


def _three_open(w):
    """50 reserve at once against 3.00 (worst 1.00): 3 granted, read back from the 51st connection."""
    stores, reader = _callers(w)
    outcomes, ids = _reserve_ids(stores)
    assert {o: outcomes.count(o) for o in set(outcomes)} == {"granted": 3, "day": CALLERS - 3}
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))
    return stores, reader, sorted(ids[i] for i, o in enumerate(outcomes) if o == "granted")


@pytest.mark.parametrize(
    ("cap", "worst", "expected"),
    [  # from core-c T1
        (D("3.50"), D("1.00"), 3),  # floor: the last 0.50 is not enough for a fourth
        (D("0.07"), D("0.01"), 7),  # cents: nothing is rounded, the cap is reached exactly
        (D("1.00"), D("0.30"), 3),  # 0.90 booked, 0.10 left
        (D("0.99"), D("1.00"), 0),  # the cap is below one call: nobody is granted
        (D("50.00"), D("1.00"), 50),  # the cap fits all 50: nobody is refused
    ],
)
def test_t1_exactly_floor_of_cap_over_worst_are_granted(w, cap, worst, expected):
    """from core-c T1: "exactly floor(cap / amount) succeed" for caps that are not a multiple of the amount."""
    assert expected == int(cap // worst)
    stores, reader = _callers(w)
    outcomes, ids = _reserve_ids(stores, cap=cap, usd=worst)
    assert {o: outcomes.count(o) for o in set(outcomes)} == {
        k: v for k, v in (("granted", expected), ("day", CALLERS - expected)) if v
    }
    total = worst * expected
    assert reader.spend_totals(AGENT, DAY) == (total, total)
    assert total <= cap
    granted = {ids[i] for i, o in enumerate(outcomes) if o == "granted"}
    assert _rows(w) == {rid: (worst, None, "open", False) for rid in granted}
    # one day row and one month row at most: a refusal books nothing anywhere
    assert w.run("SELECT (SELECT count(*) FROM spend), (SELECT count(*) FROM spend_month)")[0] == (
        (1, 1) if expected else (0, 0)
    )


def test_t1_two_agents_on_the_same_fifty_connections_each_get_their_own_cap(w):
    """from core-c T1: 25 connections reserve for one agent, 25 for another: 3 granted for each, never 6 for one."""
    stores, reader = _callers(w)
    agent_of = lambda i: "agent-a" if i % 2 == 0 else "agent-b"
    outcomes, _ = _reserve_ids(stores, agent=agent_of)
    assert sorted(agent_of(i) for i, o in enumerate(outcomes) if o == "granted") == [
        *["agent-a"] * 3,
        *["agent-b"] * 3,
    ]
    assert outcomes.count("day") == CALLERS - 6
    cap = D("3.00")
    assert reader.spend_totals("agent-a", DAY) == (cap, cap)
    assert reader.spend_totals("agent-b", DAY) == (cap, cap)
    assert reader.spend_totals("agent-c", DAY) == (D(0), D(0))


def test_t1_fifty_connections_settle_one_reservation_and_the_first_wins(w):
    """from core-a T1 / core-c T1: 50 connections settle ONE reservation with 50 different amounts: one applies, all
    50 get the same stored row, the counters and the run's cost hold the winner's amount once (b's repeatable-read
    case does this with 8 same-amount settles and reads neither the returned rows nor the run)."""
    from hadavin_sdk.models import Run

    stores, reader = _callers(w)
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    stores[0].create_run(run)
    rid = new_id("res")
    stores[0].reserve_spend(rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    amounts = [D(i + 1) / 100 for i in range(CALLERS)]  # 0.01 .. 0.50, all distinct
    results = _together(stores, lambda i, s: (s.settle_spend(rid, amounts[i], agent_id=AGENT), i))
    assert all(isinstance(r, tuple) for r in results), results
    winners = [(row, i) for (row, applied), i in results if applied is True]
    assert len(winners) == 1
    assert [applied for (_, applied), _ in results].count(False) == CALLERS - 1
    won_row, won_i = winners[0]
    won = amounts[won_i]
    assert (won_row.settled_usd, won_row.reserved_usd, won_row.status) == (won, WORST, "settled")
    assert won_row.closed_at is not None
    assert {row.model_dump_json() for (row, _), _ in results} == {won_row.model_dump_json()}
    assert reader.spend_totals(AGENT, DAY) == (won, won)
    assert reader.get_run(run.run_id).cost_usd == won
    assert _rows(w) == {rid: (WORST, won, "settled", True)}
    again, applied = reader.settle_spend(rid, D("2.00"), agent_id=AGENT)  # a later, higher amount
    assert applied is False and again.settled_usd == won
    assert reader.spend_totals(AGENT, DAY) == (won, won)


def test_t1_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap(w):
    """from core-c T1: the cap is full with three open reservations; one settles at 2.50: the counters read 4.50
    (above the cap, nothing is clipped) and the cap stays shut for all 50."""
    stores, reader, granted = _three_open(w)
    row, applied = reader.settle_spend(granted[0], D("2.50"), agent_id=AGENT)
    assert applied is True
    assert (row.reserved_usd, row.settled_usd) == (WORST, D("2.50"))
    assert reader.spend_totals(AGENT, DAY) == (D("4.50"), D("4.50"))
    again, ids = _reserve_ids(stores)
    assert again == ["day"] * CALLERS
    assert reader.spend_totals(AGENT, DAY) == (D("4.50"), D("4.50"))
    assert len(_rows(w)) == 3  # the 50 refusals left no row
    assert len(ids) == CALLERS


def test_t1_a_settle_at_zero_gives_the_whole_reservation_back(w):
    """from core-c T1: a call that cost nothing settles at 0: the counters read 0 and the next 50 get exactly 3."""
    stores, reader, granted = _three_open(w)
    for rid in granted:
        assert reader.settle_spend(rid, D(0), agent_id=AGENT)[1] is True
    assert reader.spend_totals(AGENT, DAY) == (D(0), D(0))
    again, _ = _reserve_ids(stores)
    assert {o: again.count(o) for o in set(again)} == {"granted": 3, "day": CALLERS - 3}
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))


def test_t1_expired_reservations_stay_booked_and_keep_the_cap_shut(w):
    """from core-c T1: an open row nobody closed is marked expired by the sweep and stays booked at the full amount;
    the counters do not move, the cap stays shut, a second sweep expires nothing."""
    stores, reader, granted = _three_open(w)
    assert reader.expire_spend_reservations(3600) == 0  # younger than an hour: not touched
    assert _rows(w) == {rid: (WORST, None, "open", False) for rid in granted}
    assert reader.expire_spend_reservations(0) == 3
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))
    rows = _rows(w)
    assert sorted(rows) == granted
    assert {(reserved, status, closed) for reserved, _, status, closed in rows.values()} == {
        (WORST, "expired", True)
    }
    assert reader.expire_spend_reservations(0) == 0  # an expired row is not expired twice
    again, _ = _reserve_ids(stores)
    assert again == ["day"] * CALLERS
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))
    assert len(_rows(w)) == 3


def test_t1_fifty_sweeps_at_once_expire_each_reservation_once(w):
    """from core-c T1: 50 connections run the sweep at the same moment over three open rows: counts add up to 3."""
    stores, reader, granted = _three_open(w)
    counts = _together(stores, lambda i, s: s.expire_spend_reservations(0))
    assert all(isinstance(c, int) for c in counts), counts
    assert sum(counts) == 3
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))
    rows = _rows(w)
    assert sorted(rows) == granted and {v[2] for v in rows.values()} == {"expired"}


def test_t1_a_settle_after_expiry_never_lowers_the_counters(w):
    """from core-c T1: an expired row is claimed by its first settle and its counters only move upward. Of three
    expired reservations of 1.00: one settles at 0.25 (claimed, counters stay), one at 1.75 (claimed, counters
    rise by 0.75), one is left alone. A second settle of either changes nothing."""
    _stores, reader, (low, high, untouched) = _three_open(w)
    assert reader.expire_spend_reservations(0) == 3
    row, applied = reader.settle_spend(low, D("0.25"), agent_id=AGENT)
    assert applied is True  # claimed by its first settle
    assert row.reserved_usd == WORST and row.closed_at is not None
    assert row.settled_usd == WORST  # what stays booked: not the lower actual amount
    assert reader.spend_totals(AGENT, DAY) == (D("3.00"), D("3.00"))
    row, applied = reader.settle_spend(high, D("1.75"), agent_id=AGENT)
    assert applied is True and row.settled_usd == D("1.75")
    assert reader.spend_totals(AGENT, DAY) == (D("3.75"), D("3.75"))
    for rid, later, stored in ((low, D("5.00"), WORST), (high, D(0), D("1.75"))):
        again, applied = reader.settle_spend(rid, later, agent_id=AGENT)
        assert applied is False and again.settled_usd == stored
    assert reader.spend_totals(AGENT, DAY) == (D("3.75"), D("3.75"))
    assert _rows(w)[untouched] == (WORST, WORST, "expired", True)
    assert reader.expire_spend_reservations(0) == 0  # the two claimed rows are closed, not open
    with pytest.raises(SpendCapExceeded):
        reader.reserve_spend(new_id("res"), AGENT, DAY, WORST, day_cap=D("3.00"), month_cap=BIG)


def test_t1_settles_racing_the_expiry_sweep_leave_counters_equal_to_the_rows(w):
    """from core-a T1: 40 connections each settle their own open reservation of 1.00 at 0.25 while 10 run the sweep
    (age 0). Afterwards every row is settled, each says 0.25 (settled while open) or 1.00 (expired first: never
    down), the day counter equals the sum over the rows, and the run's cost is 40 times the real 0.25."""
    from hadavin_sdk.models import Run

    stores, reader = _callers(w)
    low = D("0.25")
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    stores[0].create_run(run)
    ids = {i: new_id("res") for i in range(40)}
    for i, rid in ids.items():
        stores[i].reserve_spend(
            rid, AGENT, DAY, WORST, day_cap=BIG, month_cap=BIG, run_id=run.run_id
        )

    def work(i, store):
        if i in ids:
            return store.settle_spend(ids[i], low, agent_id=AGENT)
        return store.expire_spend_reservations(0)

    results = _together(stores, work)
    assert not [r for r in results if isinstance(r, str)], results
    assert all(applied for _, applied in results[:40])  # each row's first settle, open or expired
    rows = _rows(w)
    assert len(rows) == 40
    booked = [v[1] for v in rows.values()]
    assert {v[2] for v in rows.values()} == {"settled"}
    assert set(booked) <= {low, WORST}
    swept = sum(results[40:])
    expired_first = booked.count(WORST)
    assert expired_first == swept  # every row a sweep reported is one that stayed at 1.00
    assert [row.settled_usd for row, _ in results[:40]].count(WORST) == expired_first
    assert reader.spend_totals(AGENT, DAY) == (sum(booked), sum(booked))
    assert reader.get_run(run.run_id).cost_usd == low * 40


def test_t1_one_settle_racing_the_sweep_ends_in_one_of_the_two_stated_results(w):
    """from core-c T1: 25 connections settle ONE open reservation at 0.25 while 25 run the sweep. One settle is
    applied and the counters equal what the row says is booked: 0.25 (settle first) or the full 1.00 (sweep first)."""
    stores, reader = _callers(w)
    rid, actual = new_id("res"), D("0.25")
    reader.reserve_spend(rid, AGENT, DAY, WORST, day_cap=D("3.00"), month_cap=D("3.00"))

    def work(i, store):
        if i % 2:
            return ("sweep", store.expire_spend_reservations(0))
        return ("settle", store.settle_spend(rid, actual, agent_id=AGENT))

    results = _together(stores, work)
    assert all(isinstance(r, tuple) for r in results), results
    expired = sum(v for kind, v in results if kind == "sweep")
    settles = [v for kind, v in results if kind == "settle"]
    assert len(settles) == CALLERS // 2
    assert [applied for _, applied in settles].count(True) == 1
    assert expired in (0, 1)
    booked = WORST if expired else actual
    assert {row.settled_usd for row, _ in settles} == {booked}
    assert reader.spend_totals(AGENT, DAY) == (booked, booked)
    assert _rows(w)[rid][:2] == (WORST, booked)
    assert reader.expire_spend_reservations(0) == 0


# --- the grants on spend_reservations (from core-a T1 / core-c T1; core-b's World has all four logins) -----------


def test_t1_the_runtime_role_may_not_delete_reservations(w):
    """from core-a T1: no DELETE, no TRUNCATE, and the purge method fails for the runtime login too. core-a wrote
    "runtime holds SELECT, INSERT, UPDATE"; on core-b (migration 0011) the runtime holds NO right on the table (the
    money functions are the only way in), so the direct SELECT, INSERT and UPDATE are asserted refused as well: the
    assertion is stricter than core-a's, not weaker."""
    store = w.store(w.runtime)
    rid = new_id("res")
    store.reserve_spend(rid, AGENT, DAY, WORST, day_cap=D("3.00"), month_cap=D("3.00"))
    store.settle_spend(rid, WORST, agent_id=AGENT)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):  # no EXECUTE on the purge function
        store.purge_spend_reservations(now() + timedelta(days=1))
    assert list(_rows(w)) == [rid]  # nothing was deleted
    with w.as_(w.runtime) as db:
        for statement in (
            "DELETE FROM spend_reservations",
            "TRUNCATE spend_reservations",
            "SELECT count(*) FROM spend_reservations",
            "UPDATE spend_reservations SET status = 'open'",
            "INSERT INTO spend_reservations (reservation_id) VALUES ('res-x')",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
    assert list(_rows(w)) == [rid]


def test_t1_the_purge_role_deletes_closed_rows_only_through_the_purge_function(w):
    """from core-a T1: the purge login deletes closed rows and never an open one. core-a wrote "purge holds DELETE
    plus SELECT on status and closed_at"; on core-b (0011) the purge login holds nothing on the table and reaches it
    only through `purge_spend_reservations`, so every direct statement, SELECT of status and closed_at included, is
    asserted refused (stricter than core-a's)."""
    runtime, purge = w.store(w.runtime), w.store(w.purge)
    closed, kept = new_id("res"), new_id("res")
    for rid in (closed, kept):
        runtime.reserve_spend(rid, AGENT, DAY, WORST, day_cap=D("3.00"), month_cap=D("3.00"))
    runtime.settle_spend(closed, WORST, agent_id=AGENT)
    assert purge.purge_spend_reservations(now() + timedelta(days=1)) == 1
    assert list(_rows(w)) == [kept]  # the open row was not deleted
    assert runtime.settle_spend(kept, WORST, agent_id=AGENT)[1] is True
    with w.as_(w.purge) as db:
        for statement in (
            "SELECT status, closed_at FROM spend_reservations",
            "SELECT reserved_usd FROM spend_reservations",
            "SELECT * FROM spend_reservations",
            "DELETE FROM spend_reservations",
            "UPDATE spend_reservations SET status = 'open'",
            "INSERT INTO spend_reservations (reservation_id) VALUES ('res-x')",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


@pytest.mark.parametrize("who", ["portal", "reset"])
def test_t1_the_portal_and_the_reset_role_may_not_read_reservations(w, who):
    """from core-a T1: portal and reset hold nothing on spend_reservations."""
    role = getattr(w, who)
    with w.as_(role) as db:
        assert db.execute("SELECT current_user").fetchone()[0] == role
        for statement in (
            "SELECT * FROM spend_reservations",
            "SELECT status FROM spend_reservations",
            "DELETE FROM spend_reservations",
            "UPDATE spend_reservations SET status = 'open'",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
    assert w.rights(role).get("spend_reservations") is None

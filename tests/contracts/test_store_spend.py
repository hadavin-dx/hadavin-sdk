"""Spend reservations (step F-store, migration 0007): the store contract, over every registered store kind.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/F-store.md: the invariants
1 to 13 with the resolutions of review rounds 1 and 2), not from the code. The four methods under test are
`reserve_spend`, `settle_spend`, `expire_spend_reservations` and `purge_spend_reservations`.

The Protocol has no getter for a reservation row (the ticket rules one out), so three helpers reach behind it and
say so: `_rows` reads the rows, `_older` moves a row's `created_at` back and `_closed_earlier` its `closed_at`.
Everything else goes through the public methods. `DAY` is a fixed day that is never today and never in this
month, so a store that books on today's day or month instead of the row's own cannot pass."""

import dataclasses
import inspect
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from hadavin_sdk.models import Run, SpendReservation, new_id, now
from hadavin_sdk.store import memory as memory_mod
from hadavin_sdk.store.protocol import (
    NotFound,
    SpendCapExceeded,
    StaleState,
    Store,
    check_spend_amount,
    missing_methods,
)

D = Decimal
AGENT = "agent-a"
OTHER = "agent-b"
DAY = date(now().year - 1, 1, 31)  # last day of a January that is over
EVE = DAY - timedelta(days=1)  # another day of the same month
NEXT = DAY + timedelta(days=1)  # the first of February: another day AND another month
BIG = D("100")
MICRO = D("0.000001")
ZERO = (D(0), D(0))
METHODS = [
    "expire_spend_reservations",
    "purge_spend_reservations",
    "reserve_spend",
    "settle_spend",
]


def _is_memory(store):
    return hasattr(store, "_reservations")


def _owner_rows(store):
    """Every row of spend_reservations, read as the table owner: since F-money-definer step 4 the runtime login (the
    store's own connection) holds no right on the table."""
    import os

    from psycopg import connect
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    from psycopg.rows import dict_row

    options = conninfo_to_dict(store._db.info.dsn).get("options")
    owner = make_conninfo(os.environ["HADAVIN_TEST_PG_DSN"], options=options)
    with store._lock, connect(owner, autocommit=True, row_factory=dict_row) as db:
        return db.execute("SELECT * FROM spend_reservations").fetchall()


def _rows(store) -> dict[str, SpendReservation]:
    """Every reservation row, by id (not part of the Protocol)."""
    if _is_memory(store):
        with store._lock:
            return dict(store._reservations)
    found = _owner_rows(store)
    return {r["reservation_id"]: SpendReservation.model_validate(r) for r in found}


def _owner_update(store, query, params):
    """UPDATE as the table owner: the 0010 money guard refuses the runtime login (pattern of `_shift` in test_store_spend_model)."""
    import os

    from psycopg import connect
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    options = conninfo_to_dict(store._db.info.dsn).get("options")
    owner = make_conninfo(os.environ["HADAVIN_TEST_PG_DSN"], options=options)
    with store._lock, connect(owner, autocommit=False) as db:
        db.execute("SET LOCAL session_replication_role = replica")
        return db.execute(query, params).rowcount


def _older(store, rid, seconds):
    """Move the row's created_at back, as if it had been reserved `seconds` earlier."""
    if _is_memory(store):
        with store._lock:
            row = store._reservations[rid]
            store._reservations[rid] = row.model_copy(
                update={"created_at": row.created_at - timedelta(seconds=seconds)}
            )
        return
    done = _owner_update(
        store,
        "UPDATE spend_reservations SET created_at = created_at - make_interval(secs => %s) WHERE reservation_id = %s",
        (seconds, rid),
    )
    assert done == 1


def _closed_earlier(store, rid, days):
    if _is_memory(store):
        with store._lock:
            row = store._reservations[rid]
            store._reservations[rid] = row.model_copy(
                update={"closed_at": row.closed_at - timedelta(days=days)}
            )
        return
    done = _owner_update(
        store,
        "UPDATE spend_reservations SET closed_at = closed_at - make_interval(days => %s) WHERE reservation_id = %s",
        (days, rid),
    )
    assert done == 1


def _reserve(store, usd, *, agent=AGENT, day=DAY, day_cap=BIG, month_cap=BIG, run_id=None):
    rid = new_id("res")
    store.reserve_spend(
        rid, agent, day, D(usd), day_cap=D(day_cap), month_cap=D(month_cap), run_id=run_id
    )
    return rid


def _refused(store, usd, which, **kw):
    with pytest.raises(SpendCapExceeded) as caught:
        _reserve(store, usd, **kw)
    assert caught.value.which == which
    return caught.value


def _totals(store, agent=AGENT, day=DAY):
    return store.spend_totals(agent, day)


def _new_run(store, agent=AGENT):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run.run_id


def _cost(store, run_id):
    return store.get_run(run_id).cost_usd


def _expire_all(store):
    """Age 0: every open row is old enough."""
    return store.expire_spend_reservations(0)


# --- reserve -------------------------------------------------------------------------------------------------------


def test_reserve_books_the_day_and_the_month_and_keeps_an_open_row(store):
    rid = _reserve(store, "1.25", run_id="run-x")
    assert _totals(store) == (D("1.25"), D("1.25"))
    row = _rows(store)[rid]
    assert (row.agent_id, row.day, row.run_id) == (AGENT, DAY, "run-x")
    assert (row.status, row.reserved_usd, row.settled_usd, row.closed_at) == (
        "open",
        D("1.25"),
        None,
        None,
    )
    assert abs((now() - row.created_at).total_seconds()) < 300
    _reserve(store, "0.50", day=EVE)
    assert _totals(store) == (D("1.25"), D("1.75"))  # its own day, the shared month
    assert _totals(store, day=EVE) == (D("0.50"), D("1.75"))
    assert _totals(store, OTHER) == ZERO  # another agent has its own counters
    assert _totals(store, day=NEXT) == ZERO


def test_a_reserve_that_reaches_the_cap_exactly_passes(store):
    _reserve(store, "3.00", day_cap="3.00")
    assert _totals(store) == (D("3.00"), D("3.00"))
    _reserve(store, "2.00", agent=OTHER, day_cap="3.00")
    _reserve(store, "1.00", agent=OTHER, day_cap="3.00")
    assert _totals(store, OTHER) == (D("3.00"), D("3.00"))


def test_one_micro_dollar_over_the_day_cap_is_refused_with_which_day(store):
    assert str(_refused(store, "3.000001", "day", day_cap="3.00")) == "day cap reached"
    assert _totals(store) == ZERO and _rows(store) == {}
    _reserve(store, "2.00", day_cap="3.00")
    _refused(store, D("1.00") + MICRO, "day", day_cap="3.00")
    assert _totals(store) == (D("2.00"), D("2.00")) and len(_rows(store)) == 1


def test_the_month_cap_binds_when_it_is_the_lower_one(store):
    _refused(store, "2.000001", "month", day_cap="10", month_cap="2")
    assert _totals(store) == ZERO and _rows(store) == {}  # the day booking was taken back
    _reserve(store, "1.50", day=EVE, day_cap="10", month_cap="2")
    _refused(store, "1.00", "month", day_cap="10", month_cap="2")
    assert _totals(store) == (D(0), D("1.50"))
    assert _totals(store, day=EVE) == (D("1.50"), D("1.50")) and len(_rows(store)) == 1
    _reserve(store, "0.50", day_cap="10", month_cap="2")  # exactly the month cap
    assert _totals(store) == (D("0.50"), D("2.00"))


def test_the_day_is_checked_first_when_both_caps_would_be_passed(store):
    _refused(store, "5", "day", day_cap="1", month_cap="2")
    assert _totals(store) == ZERO and _rows(store) == {}


def test_a_budget_of_zero_refuses_even_an_amount_of_zero(store):
    _refused(store, "0", "day", day_cap="0", month_cap="5")
    _refused(store, "0", "month", day_cap="5", month_cap="0")
    assert _totals(store) == ZERO and _rows(store) == {}


def test_a_counter_at_its_cap_refuses_an_amount_of_zero(store):
    _reserve(store, "1.00", day_cap="1.00")
    _refused(store, "0", "day", day_cap="1.00")
    _reserve(store, "2.00", day=EVE, day_cap="5", month_cap="3.00")
    _refused(store, "0", "month", day=NEXT - timedelta(days=3), day_cap="5", month_cap="3.00")
    assert len(_rows(store)) == 2


def test_an_amount_of_zero_is_booked_as_a_row_below_the_cap(store):
    rid = _reserve(store, "0", day_cap="1.00")
    assert _totals(store) == ZERO
    assert _rows(store)[rid].reserved_usd == 0
    row, applied = store.settle_spend(rid, D("0.25"), agent_id=AGENT)
    assert applied and row.settled_usd == D("0.25")
    assert _totals(store) == (D("0.25"), D("0.25"))


def test_a_refused_reserve_leaves_the_totals_and_the_rows_unchanged(store):
    _reserve(store, "2.00", day_cap="3.00")
    rows, totals = _rows(store), _totals(store)
    _refused(store, "2.00", "day", day_cap="3.00")
    _refused(store, "2.00", "month", day_cap="9.00", month_cap="3.00")
    assert _rows(store) == rows and _totals(store) == totals
    _reserve(store, "1.00", day_cap="3.00")  # the store still works after a refusal
    assert _totals(store) == (D("3.00"), D("3.00"))


def test_a_retry_with_the_same_arguments_succeeds_and_books_nothing_more(store):
    """M5: reserve commits, the reply is lost, the retry must see its own success, not a collision."""
    rid = _reserve(store, "1.00")
    first = _rows(store)[rid]
    store.reserve_spend(rid, AGENT, DAY, D("1.00"), day_cap=BIG, month_cap=BIG)
    assert _rows(store) == {rid: first}
    assert _totals(store) == (D("1.00"), D("1.00"))
    store.reserve_spend(rid, AGENT, DAY, D("1.00"), day_cap=D("0.01"), month_cap=D("0.01"))
    assert _totals(store) == (
        D("1.00"),
        D("1.00"),
    )  # a cap that is now passed does not turn it into a refusal
    for agent, day, usd, run in (
        (OTHER, DAY, "1.00", None),
        (AGENT, EVE, "1.00", None),
        (AGENT, DAY, "1.01", None),
        (AGENT, DAY, "1.00", "other-run"),
    ):
        with pytest.raises(StaleState):
            store.reserve_spend(rid, agent, day, D(usd), day_cap=BIG, month_cap=BIG, run_id=run)
    assert _rows(store) == {rid: first}
    assert _totals(store) == (D("1.00"), D("1.00"))


def test_a_duplicate_id_is_stale_state_and_is_booked_once(store):
    rid = _reserve(store, "1.00")
    first = _rows(store)[rid]
    with pytest.raises(StaleState, match=f"spend reservation exists: {rid}"):
        store.reserve_spend(rid, AGENT, DAY, D("1.01"), day_cap=BIG, month_cap=BIG)
    with pytest.raises(StaleState):
        store.reserve_spend(rid, OTHER, EVE, D("7.00"), day_cap=BIG, month_cap=BIG)
    assert _rows(store) == {rid: first}
    assert _totals(store) == (D("1.00"), D("1.00"))
    assert _totals(store, OTHER, EVE) == ZERO
    _reserve(store, "1.00")  # and the store still works
    assert _totals(store) == (D("2.00"), D("2.00"))


def test_a_full_day_does_not_block_the_next_day_and_a_full_month_does(store):
    _reserve(store, "1.00", day=EVE, day_cap="1.00", month_cap="1.50")
    _refused(store, MICRO, "day", day=EVE, day_cap="1.00", month_cap="1.50")
    _reserve(store, "0.50", day_cap="1.00", month_cap="1.50")  # the next day is free
    _refused(store, MICRO, "month", day_cap="1.00", month_cap="1.50")  # the month is full now
    _reserve(store, "1.00", day=NEXT, day_cap="1.00", month_cap="1.50")  # a new month is free
    assert _totals(store, day=NEXT) == (D("1.00"), D("1.00"))


# --- settle --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("actual", ["0", "0.40", "1.00", "1.75", "5.00"])
def test_settle_lower_equal_and_higher_books_the_actual_amount(store, actual):
    rid = _reserve(store, "1.00", day_cap="3.00")
    row, applied = store.settle_spend(rid, D(actual), agent_id=AGENT)
    assert applied is True
    assert (row.status, row.settled_usd, row.reserved_usd) == ("settled", D(actual), D("1.00"))
    assert row.closed_at is not None and row.closed_at >= row.created_at
    assert _rows(store)[rid] == row
    assert _totals(store) == (D(actual), D(actual))  # 5.00 is above the cap: booked in full


def test_an_overshoot_blocks_every_later_reserve_of_that_day_until_the_next_day(store):
    rid = _reserve(store, "0.60", day_cap="1.00")
    store.settle_spend(rid, D("1.50"), agent_id=AGENT)
    assert _totals(store) == (D("1.50"), D("1.50"))
    _refused(store, MICRO, "day", day_cap="1.00")
    _refused(store, "0", "day", day_cap="1.00")
    _reserve(store, "1.00", day=EVE, day_cap="1.00")  # another day of the month is free
    _refused(store, "0", "month", day=NEXT - timedelta(days=3), day_cap="1.00", month_cap="2.50")


def test_settle_to_zero_releases_the_whole_booking(store):
    rid = _reserve(store, "1.00", day_cap="1.00")
    _refused(store, MICRO, "day", day_cap="1.00")
    row, applied = store.settle_spend(rid, D(0), agent_id=AGENT)
    assert applied and (row.status, row.settled_usd) == ("settled", D(0))
    assert _totals(store) == ZERO
    _reserve(store, "1.00", day_cap="1.00")


@pytest.mark.parametrize("second", ["0.40", "0", "0.90", "7.00"])
def test_settle_twice_the_first_wins_and_the_second_changes_nothing(store, second):
    run_id = _new_run(store)
    rid = _reserve(store, "1.00", run_id=run_id)
    first, applied = store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert applied is True
    again, applied_again = store.settle_spend(rid, D(second), agent_id=AGENT)
    assert applied_again is False
    assert again == first and again.settled_usd == D("0.40")
    assert _rows(store)[rid] == first
    assert _totals(store) == (D("0.40"), D("0.40"))
    assert _cost(store, run_id) == D("0.40")
    assert store.settle_spend(rid, D(second), agent_id=AGENT) == (
        first,
        False,
    )  # any number of times


def test_settle_with_an_unknown_id_is_not_found_and_changes_nothing(store):
    rid = _reserve(store, "1.00")
    rows = _rows(store)
    with pytest.raises(NotFound):
        store.settle_spend(new_id("res"), D("0.10"), agent_id=AGENT)
    with pytest.raises(KeyError):  # NotFound is a KeyError (contract point 4)
        store.settle_spend("res-unknown", D("0.10"), agent_id=AGENT)
    assert _rows(store) == rows and _totals(store) == (D("1.00"), D("1.00"))
    assert store.settle_spend(rid, D("0.10"), agent_id=AGENT)[1] is True  # the store still works


# --- amounts -------------------------------------------------------------------------------------------------------

HOSTILE = {
    "nan": D("NaN"),
    "signalling_nan": D("sNaN"),
    "infinity": D("Infinity"),
    "minus_infinity": D("-Infinity"),
    "negative": D("-0.000001"),
    "minus_one": D(-1),
    "float": 1.0,
    "float_nan": float("nan"),
    "bool": True,
    "int": 1,
    "none": None,
    "text": "1.00",
    "ten_to_the_ninth": D(10**9),
    "above_the_bound": D("1000000000.01"),
    "thirteen_decimals": D("0.0000000000001"),
    "huge_exponent_zero": D("0E+999999"),
    "huge_exponent": D("1E+10"),
    "tiny_exponent_zero": D("0E-999999"),
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_a_hostile_amount_on_reserve_is_a_value_error_and_nothing_is_booked(store, name):
    with pytest.raises(ValueError):
        store.reserve_spend(new_id("res"), AGENT, DAY, HOSTILE[name], day_cap=BIG, month_cap=BIG)
    assert _rows(store) == {} and _totals(store) == ZERO
    _reserve(store, "1.00")  # the store still works


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_a_hostile_amount_on_settle_is_a_value_error_and_the_row_stays_open(store, name):
    run_id = _new_run(store)
    rid = _reserve(store, "1.00", run_id=run_id)
    before = _rows(store)
    with pytest.raises(ValueError):
        store.settle_spend(rid, HOSTILE[name], agent_id=AGENT)
    assert _rows(store) == before and before[rid].status == "open"
    assert _totals(store) == (D("1.00"), D("1.00")) and _cost(store, run_id) == 0
    assert store.settle_spend(rid, D("0.50"), agent_id=AGENT)[1] is True


@pytest.mark.parametrize(
    "amount", ["0.000000000001", "999999999.999999999999", "1E+8", "0.10", "3"]
)
def test_an_amount_inside_the_bounds_is_booked_exactly_nothing_is_rounded(store, amount):
    big = D(10) ** 12
    rid = _reserve(store, amount, day_cap=big, month_cap=big)
    assert _totals(store) == (D(amount), D(amount))
    assert _rows(store)[rid].reserved_usd == D(amount)
    row, _ = store.settle_spend(rid, D(amount), agent_id=AGENT)
    assert row.settled_usd == D(amount) and _totals(store) == (D(amount), D(amount))


def test_thirds_of_a_cent_add_up_without_rounding(store):
    for _ in range(3):
        _reserve(store, "0.333333333333", day_cap="1")
    assert _totals(store) == (D("0.999999999999"), D("0.999999999999"))
    _refused(store, "0.000000000002", "day", day_cap="1")
    _reserve(store, "0.000000000001", day_cap="1")
    assert _totals(store)[0] == D(1)


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_the_amount_helper_refuses_every_hostile_amount(name):
    with pytest.raises(ValueError):
        check_spend_amount(HOSTILE[name])


def test_the_amount_helper_returns_a_good_amount_unchanged():
    for good in (D(0), D("0.000000000001"), D("999999999.999999999999"), D("1E+8"), D("-0")):
        assert check_spend_amount(good) is good

    class Money(Decimal):
        pass

    with pytest.raises(ValueError):  # the type is exactly Decimal, not a subclass
        check_spend_amount(Money("1"))


# --- the run's cost (R3, Q4, invariant 13) -------------------------------------------------------------------------


def test_settle_adds_the_actual_amount_to_the_cost_of_a_run_that_exists(store):
    run_id, bystander = _new_run(store), _new_run(store)
    first = _reserve(store, "1.00", run_id=run_id)
    second = _reserve(store, "2.00", run_id=run_id)
    assert _cost(store, run_id) == 0  # a reserve books nothing on the run
    store.settle_spend(first, D("0.40"), agent_id=AGENT)
    assert _cost(store, run_id) == D("0.40")
    store.settle_spend(second, D("2.75"), agent_id=AGENT)
    assert _cost(store, run_id) == D("3.15")  # the sum of the real amounts
    assert _cost(store, bystander) == 0
    assert _totals(store) == (D("3.15"), D("3.15"))


def test_settle_with_a_run_id_that_has_no_run_row_moves_only_the_counters(store):
    bystander = _new_run(store)
    rid = _reserve(store, "1.00", run_id="run-" + "0" * 32)
    row, applied = store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert applied and (row.status, row.settled_usd, row.run_id) == (
        "settled",
        D("0.40"),
        "run-" + "0" * 32,
    )
    assert _totals(store) == (D("0.40"), D("0.40"))
    assert _cost(store, bystander) == 0
    with pytest.raises(NotFound):
        store.get_run("run-" + "0" * 32)  # and no run row was made up


def test_settle_without_a_run_id_touches_no_run(store):
    bystander = _new_run(store)
    rid = _reserve(store, "1.00")
    row, applied = store.settle_spend(rid, D("0.40"), agent_id=AGENT)
    assert applied and row.run_id is None
    assert _cost(store, bystander) == 0 and _totals(store) == (D("0.40"), D("0.40"))


def test_a_replayed_settle_adds_to_the_run_cost_once(store):
    run_id = _new_run(store)
    rid = _reserve(store, "1.00", run_id=run_id)
    for amount in ("0.40", "0.40", "0.90"):
        store.settle_spend(rid, D(amount), agent_id=AGENT)
    assert _cost(store, run_id) == D("0.40")


@pytest.mark.parametrize("actual", ["0.40", "0", "1.00", "2.50"])
def test_expired_then_settled_adds_the_real_amount_to_the_run_cost(store, actual):
    run_id = _new_run(store)
    rid = _reserve(store, "1.00", run_id=run_id)
    assert _expire_all(store) == 1
    assert _cost(store, run_id) == 0  # an expired, unsettled reservation is not in the run's cost
    _, applied = store.settle_spend(rid, D(actual), agent_id=AGENT)
    assert applied is True
    assert _cost(store, run_id) == D(actual)
    store.settle_spend(rid, D("9"), agent_id=AGENT)
    assert _cost(store, run_id) == D(actual)


# --- expire --------------------------------------------------------------------------------------------------------


def test_expire_leaves_young_rows_alone(store):
    rid = _reserve(store, "1.00")
    assert store.expire_spend_reservations(3600) == 0
    _older(store, rid, 1800)
    assert store.expire_spend_reservations(3600) == 0
    assert _rows(store)[rid].status == "open"


def test_expire_closes_old_rows_only_and_the_counters_do_not_move(store):
    old, young, other = _reserve(store, "1.00"), _reserve(store, "0.25"), _reserve(store, "2.00")
    done = _reserve(store, "0.50")
    _older(store, old, 7200)
    _older(store, other, 3700)
    _older(store, done, 7200)
    settled, _ = store.settle_spend(done, D("0.10"), agent_id=AGENT)
    totals = _totals(store)
    assert totals == (D("3.35"), D("3.35"))
    assert store.expire_spend_reservations(3600) == 2
    rows = _rows(store)
    for rid, reserved in ((old, D("1.00")), (other, D("2.00"))):
        row = rows[rid]
        assert (row.status, row.settled_usd, row.reserved_usd) == ("expired", reserved, reserved)
        assert row.closed_at is not None
    assert rows[young].status == "open" and rows[young].settled_usd is None
    assert rows[done] == settled  # a settled row is never expired
    assert _totals(store) == totals  # the worst case stays booked
    assert store.expire_spend_reservations(3600) == 0  # a second run finds nothing
    assert _rows(store) == rows


def test_expire_with_age_zero_closes_every_open_row_with_the_totals_unchanged(store):
    a, b = _reserve(store, "1.00"), _reserve(store, "0.50", agent=OTHER, day=EVE)
    assert _expire_all(store) == 2
    assert {r.status for r in _rows(store).values()} == {"expired"}
    assert _totals(store) == (D("1.00"), D("1.00"))
    assert _totals(store, OTHER, EVE) == (D("0.50"), D("0.50"))
    assert _expire_all(store) == 0
    assert set(_rows(store)) == {a, b}


def test_an_expired_reservation_still_blocks_at_the_cap(store):
    _reserve(store, "1.00", day_cap="1.00")
    assert _expire_all(store) == 1
    _refused(store, "0", "day", day_cap="1.00")
    _refused(store, MICRO, "day", day_cap="1.00")


@pytest.mark.parametrize("actual", ["0.40", "0", "1.00"])
def test_expired_then_settled_lower_settles_the_row_and_keeps_the_counters(store, actual):
    rid = _reserve(store, "1.00")
    assert _expire_all(store) == 1
    row, applied = store.settle_spend(rid, D(actual), agent_id=AGENT)
    assert applied is True
    # what stays booked: after expiry the booking never goes down
    assert (row.status, row.settled_usd, row.reserved_usd) == ("settled", D("1.00"), D("1.00"))
    assert row.closed_at is not None
    assert _rows(store)[rid] == row
    assert _totals(store) == (D("1.00"), D("1.00"))
    assert store.settle_spend(rid, D("5"), agent_id=AGENT) == (row, False)  # settled is terminal
    assert _totals(store) == (D("1.00"), D("1.00"))
    assert _expire_all(store) == 0


def test_expired_then_settled_higher_raises_the_counters_to_the_actual(store):
    rid = _reserve(store, "1.00")
    keep = _reserve(store, "0.25")
    assert _expire_all(store) == 2
    row, applied = store.settle_spend(rid, D("2.50"), agent_id=AGENT)
    assert applied is True
    assert (row.status, row.settled_usd, row.reserved_usd) == ("settled", D("2.50"), D("1.00"))
    assert _totals(store) == (D("2.75"), D("2.75"))
    assert store.settle_spend(rid, D("0.10"), agent_id=AGENT) == (row, False)
    assert _totals(store) == (D("2.75"), D("2.75"))
    assert _rows(store)[keep].status == "expired"


# --- purge ---------------------------------------------------------------------------------------------------------


def test_purge_removes_settled_rows_only_and_keeps_an_expired_unsettled_hold(store):
    # E11 M3: purge deletes only SETTLED holds (released = settled at 0) past retention; a hold closed by expiry
    # stays until it is settled.
    open_old, settled, expired = (_reserve(store, "1.00") for _ in range(3))
    recent, open_new = _reserve(store, "0.50"), _reserve(store, "0.25")
    store.settle_spend(settled, D("0.40"), agent_id=AGENT)
    _older(store, expired, 7200)
    _older(store, open_old, 1800)
    assert store.expire_spend_reservations(3600) == 1
    store.settle_spend(recent, D("0.50"), agent_id=AGENT)
    for rid in (settled, expired):
        _closed_earlier(store, rid, 500)
    _older(store, open_old, 500 * 86400)  # very old and still open: never purged
    totals = _totals(store)
    cutoff = now() - timedelta(days=400)
    assert store.purge_spend_reservations(now() - timedelta(days=600)) == 0
    assert store.purge_spend_reservations(cutoff) == 1  # only the settled one
    left = _rows(store)
    assert set(left) == {open_old, recent, open_new, expired}
    assert left[expired].status == "expired"
    assert (left[open_old].status, left[recent].status, left[open_new].status) == (
        "open",
        "settled",
        "open",
    )
    assert _totals(store) == totals  # a purge never moves a counter
    assert store.purge_spend_reservations(cutoff) == 0
    with pytest.raises(NotFound):
        store.settle_spend(settled, D("0.10"), agent_id=AGENT)  # the purged row is gone
    assert (
        store.settle_spend(open_old, D("0.10"), agent_id=AGENT)[1] is True
    )  # the open one was kept


def test_purge_with_a_cutoff_in_the_future_still_keeps_open_rows(store):
    opened, closed = _reserve(store, "1.00"), _reserve(store, "1.00")
    store.settle_spend(closed, D("1.00"), agent_id=AGENT)
    assert store.purge_spend_reservations(now() + timedelta(days=1)) == 1
    assert set(_rows(store)) == {opened}
    assert _totals(store) == (D("2.00"), D("2.00"))


# --- midnight (invariant 6) ----------------------------------------------------------------------------------------


@pytest.fixture
def tomorrow(monkeypatch):
    """Today is the day after DAY, for every clock the two stores read in Python."""
    at = datetime(NEXT.year, NEXT.month, NEXT.day, 0, 0, 0, 1, tzinfo=UTC)
    monkeypatch.setattr(memory_mod, "now", lambda: at)
    try:
        from hadavin_sdk.store import postgres as postgres_mod
    except ImportError:  # no driver installed: only the memory kind runs
        return at
    monkeypatch.setattr(postgres_mod, "now", lambda: at)
    return at


@pytest.mark.parametrize("actual", ["0.40", "1.75"])
def test_a_settle_on_the_next_day_moves_only_the_day_and_month_of_the_reserve(store, actual):
    """January 31 into February 1: the stored day and ITS month move, never today's."""
    rid = _reserve(store, "1.00")
    today = now().date()
    assert today not in (DAY, NEXT) and (today.year, today.month) != (DAY.year, DAY.month)
    row, applied = store.settle_spend(rid, D(actual), agent_id=AGENT)
    assert applied and row.day == DAY
    assert _totals(store) == (D(actual), D(actual))  # January 31 and January
    assert _totals(store, day=NEXT) == ZERO  # February 1 and February stay empty
    assert _totals(store, day=today) == ZERO


@pytest.mark.parametrize("actual", ["0.40", "1.75"])
def test_a_settle_when_the_clock_says_the_next_day_moves_only_the_reserved_day(
    store, tomorrow, actual
):
    assert memory_mod.now().date() == NEXT
    rid = _reserve(store, "1.00")
    _reserve(store, "0.30", day=NEXT)  # February has its own counter rows
    row, applied = store.settle_spend(rid, D(actual), agent_id=AGENT)
    assert applied and row.day == DAY
    assert _totals(store) == (D(actual), D(actual))
    assert _totals(store, day=NEXT) == (D("0.30"), D("0.30"))


def test_expire_and_a_late_settle_act_on_the_stored_day(store):
    rid = _reserve(store, "1.00")
    assert _expire_all(store) == 1
    assert _rows(store)[rid].day == DAY
    assert _totals(store) == (D("1.00"), D("1.00"))
    store.settle_spend(rid, D("1.60"), agent_id=AGENT)
    assert _totals(store) == (D("1.60"), D("1.60"))
    assert _totals(store, day=NEXT) == ZERO and _totals(store, day=now().date()) == ZERO


# --- the shape of the contract -------------------------------------------------------------------------------------


def test_the_four_methods_have_the_signatures_of_the_ticket():
    reserve = inspect.signature(Store.reserve_spend).parameters
    assert list(reserve) == [
        "self",
        "reservation_id",
        "agent_id",
        "day",
        "usd",
        "day_cap",
        "month_cap",
        "run_id",
    ]
    assert all(reserve[n].kind is inspect.Parameter.KEYWORD_ONLY for n in list(reserve)[5:])
    assert reserve["run_id"].default is None
    assert (
        "created_at" not in reserve
    )  # invariant 10: the age is the database clock's, never the caller's
    settle = inspect.signature(Store.settle_spend).parameters
    assert list(settle) == [
        "self",
        "reservation_id",
        "actual_usd",
        "agent_id",  # keyword-only and REQUIRED (M2); another agent's row is NotFound
    ]
    assert settle["agent_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert settle["agent_id"].default is inspect.Parameter.empty
    assert list(inspect.signature(Store.expire_spend_reservations).parameters) == [
        "self",
        "older_than_s",
    ]
    assert list(inspect.signature(Store.purge_spend_reservations).parameters) == ["self", "before"]


def test_both_stores_have_the_same_signatures_as_the_protocol(store):
    for name in METHODS:
        mine = list(inspect.signature(getattr(store, name)).parameters)
        asked = list(inspect.signature(getattr(Store, name)).parameters)[1:]
        if mine != ["a", "k"]:  # the postgres kind wraps its purge in a pass-through
            assert mine == asked, name
    assert not hasattr(store, "release_spend") and not hasattr(Store, "release_spend")


def test_a_custom_store_without_the_four_methods_is_named_by_missing_methods(store):
    assert missing_methods(store) == []

    class Old:
        pass

    for name, value in vars(Store).items():
        if callable(value) and not name.startswith("_") and name not in METHODS:
            setattr(Old, name, value)
    assert missing_methods(Old()) == METHODS


def test_the_row_model_is_frozen_closed_and_has_exactly_the_nine_columns():
    assert list(SpendReservation.model_fields) == [
        "reservation_id",
        "agent_id",
        "day",
        "run_id",
        "reserved_usd",
        "settled_usd",
        "status",
        "created_at",
        "closed_at",
    ]
    row = SpendReservation(
        reservation_id="res-1", agent_id=AGENT, day=DAY, reserved_usd=D(1), created_at=now()
    )
    assert (row.status, row.settled_usd, row.closed_at, row.run_id) == ("open", None, None, None)
    with pytest.raises(ValidationError):
        row.status = "settled"
    with pytest.raises(ValidationError):
        SpendReservation(**row.model_dump(), schema_version=1)
    with pytest.raises(ValidationError):
        SpendReservation(**{**row.model_dump(), "status": "released"})
    assert not dataclasses.is_dataclass(row) and "schema_version" not in row.model_dump()


def test_the_cap_error_carries_which_cap_it_was():
    for which in ("day", "month"):
        exc = SpendCapExceeded(which)
        assert exc.which == which and str(exc) == f"{which} cap reached"
        assert isinstance(exc, RuntimeError)


# --- the agent is required on settle; add_spend and reserve refuse the same days and agents on both stores ---------


def test_settle_requires_an_agent_and_another_agents_hold_is_not_found(store):
    rid = _reserve(store, "1.00")
    with pytest.raises(TypeError):
        store.settle_spend(rid, D("0.50"))  # type: ignore[call-arg]  # no agent-less path
    for bad in (None, "", "a\x00b", 7):
        with pytest.raises(ValueError, match="agent_id"):
            store.settle_spend(rid, D("0.50"), agent_id=bad)  # type: ignore[arg-type]
    with pytest.raises(NotFound):
        store.settle_spend(rid, D("0.50"), agent_id=OTHER)
    assert _rows(store)[rid].status == "open"
    assert store.settle_spend(rid, D("0.50"), agent_id=AGENT)[1] is True


@pytest.mark.parametrize(
    ("agent", "day"),
    [
        ("", DAY),
        ("a\x00b", DAY),
        ("a\nb", DAY),
        (None, DAY),
        (AGENT, date(1969, 12, 31)),
        (AGENT, date(1, 1, 1)),
        (AGENT, "2025-01-01"),
        (AGENT, datetime(2025, 1, 1, tzinfo=UTC)),
    ],
)
def test_add_spend_and_reserve_refuse_the_same_bad_agent_or_day(store, agent, day):
    """core-a M6: memory used to book what the database refuses."""
    before = store.spend_totals(AGENT, DAY)
    with pytest.raises(ValueError):
        store.add_spend(agent, day, D(1))
    with pytest.raises(ValueError):
        store.reserve_spend(new_id("res"), agent, day, D(1), day_cap=BIG, month_cap=BIG)
    assert store.spend_totals(AGENT, DAY) == before
    assert _rows(store) == {}

"""P4d-a1 baseline pin (order 101 item 3): what `add_spend` and `add_cost` do TODAY with an amount that is
negative, not a number, infinite or has more than 6 decimals.

P4d-a1 is a skeleton, not a money contract. Nothing here says the behaviour is RIGHT: P4d-a2-i defines the money
rules (finite, not negative, at most 6 decimals) and changes these tests in the same commit as the code, so that
the change is a visible, deliberate edit and not an accident. Where memory and Postgres behave the same the test
runs on both backends with one expectation; where they differ today each backend has its own expectation and the
difference is named in the test's name (a finding for a2-i: the contract suite cannot be one rule until it is
gone). Today there are two, both about a value that is not a finite number: `add_cost` of NaN or infinity (memory
returns it from `get_run`, Postgres stores it and `get_run` then raises for ever), and a signaling NaN (memory
raises `decimal.InvalidOperation` and stores nothing, Postgres stores a NaN).
"""

import decimal
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from hadavin_sdk.models import Run

DAY, NEXT_DAY = date(2026, 1, 5), date(2026, 1, 6)  # the same month
NAN, SNAN = Decimal("NaN"), Decimal("sNaN")
INF, NEG_INF = Decimal("Infinity"), Decimal("-Infinity")


def _run(store):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


# --- the same on both backends ---------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "amount",
    [
        Decimal("-0.5"),
        Decimal(-1),
        Decimal("0.1234567"),
        Decimal("5E-7"),
        Decimal("1.23456789012"),
    ],
    ids=["negative", "negative-whole", "7-decimals", "below-1e-6", "11-decimals"],
)
def test_add_spend_keeps_a_negative_or_over_6_decimal_amount_exactly(store, amount):
    """No refusal, no rounding: the day and month counters hold the amount as given, and a second day of the
    same month adds to the month only."""
    assert store.add_spend("agent", DAY, amount) == (amount, amount)
    assert store.spend_totals("agent", DAY) == (amount, amount)
    assert store.add_spend("agent", NEXT_DAY, Decimal(1)) == (Decimal(1), amount + 1)
    assert store.spend_totals("agent", DAY) == (amount, amount + 1)


@pytest.mark.parametrize(
    ("amounts", "total"),
    [
        ([Decimal("-0.5")], Decimal("-0.5")),
        ([Decimal("0.25"), Decimal("-0.5")], Decimal("-0.25")),
        ([Decimal("0.1234567")], Decimal("0.1234567")),
        ([Decimal("0.0000004"), Decimal("0.0000004")], Decimal("0.0000008")),
    ],
    ids=["negative", "negative-after-positive", "7-decimals", "two-below-1e-6"],
)
def test_add_cost_keeps_a_negative_or_over_6_decimal_amount_exactly(store, amounts, total):
    run = _run(store)
    for amount in amounts:
        assert store.add_cost(run.run_id, amount) is None
    assert store.get_run(run.run_id).cost_usd == total


@pytest.mark.parametrize(
    ("first", "shown"),
    [(NAN, "NaN"), (INF, "Infinity"), (NEG_INF, "-Infinity")],
    ids=["nan", "infinity", "minus-infinity"],
)
def test_add_spend_accepts_a_non_finite_amount_and_the_counters_stay_poisoned(store, first, shown):
    """The write is not refused and the day counter keeps the value whatever is added to it afterwards; the
    month counter too (the next day's own counter is clean)."""
    day, month = store.add_spend("agent", DAY, first)
    assert (str(day), str(month)) == (shown, shown)
    day, month = store.add_spend("agent", DAY, Decimal(1))
    assert (str(day), str(month)) == (shown, shown)
    day, month = store.add_spend("agent", NEXT_DAY, Decimal(1))
    assert (day, str(month)) == (Decimal(1), shown)
    assert tuple(str(v) for v in store.spend_totals("agent", DAY)) == (shown, shown)


# --- the differences, each backend pinned as it is ---------------------------------------------------------------
@pytest.mark.parametrize("amount", [NAN, INF, NEG_INF], ids=["nan", "infinity", "minus-infinity"])
def test_add_cost_non_finite_memory_returns_it_and_postgres_makes_the_run_unreadable(store, amount):
    run = _run(store)
    assert store.add_cost(run.run_id, amount) is None  # the write is accepted on both backends
    if store.backend == "memory":
        got = store.get_run(run.run_id).cost_usd
        assert str(got) == str(amount)
    else:
        with pytest.raises(ValidationError, match="finite"):
            store.get_run(run.run_id)
        with pytest.raises(ValidationError, match="finite"):  # and it stays so
            store.get_run(run.run_id)


def test_add_spend_signaling_nan_memory_raises_and_postgres_stores_nan(store):
    if store.backend == "memory":
        with pytest.raises(decimal.InvalidOperation):
            store.add_spend("agent", DAY, SNAN)
        assert store.spend_totals("agent", DAY) == (Decimal(0), Decimal(0))  # nothing stored
    else:
        day, month = store.add_spend("agent", DAY, SNAN)
        assert (str(day), str(month)) == ("NaN", "NaN")


def test_add_cost_signaling_nan_memory_raises_and_postgres_stores_it_unreadably(store):
    run = _run(store)
    if store.backend == "memory":
        with pytest.raises(decimal.InvalidOperation):
            store.add_cost(run.run_id, SNAN)
        assert store.get_run(run.run_id).cost_usd == Decimal(0)  # nothing stored
    else:
        assert store.add_cost(run.run_id, SNAN) is None
        with pytest.raises(ValidationError, match="finite"):
            store.get_run(run.run_id)

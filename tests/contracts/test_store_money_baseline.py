"""P4d-a1 baseline pin, changed by P4d-a2-i as its own header said it would be: what `add_spend` and `add_cost` do
with an amount that is negative, not a number, infinite or has more decimals than the money rules allow.

P4d-a1 pinned the behaviour of the day (accepted and stored a negative amount, NaN and infinity; memory and Postgres
differed for a signaling NaN). P4d-a2-i defines the money rules (finite, not negative, at most 8 decimals,
`validate_usd`) and the same refusal on both backends, so each row below now asserts the refusal (`ValueError`,
nothing booked) where it asserted the old acceptance, and keeps the amounts the new rules still accept. Rebase note:
the baseline file came from P4d after P4d-a2 was written; the full edge table is `test_store_money_edges.py`."""

from datetime import date
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run

DAY, NEXT_DAY = date(2026, 1, 5), date(2026, 1, 6)  # the same month
NAN, SNAN = Decimal("NaN"), Decimal("sNaN")
INF, NEG_INF = Decimal("Infinity"), Decimal("-Infinity")
ZERO = Decimal(0)


def _run(store):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


# --- amounts the money rules still accept: held exactly, no rounding ---------------------------------------------
@pytest.mark.parametrize(
    "amount",
    [Decimal("0.1234567"), Decimal("5E-7"), Decimal("0.00108225")],
    ids=["7-decimals", "below-1e-6", "8-decimals"],
)
def test_add_spend_keeps_an_amount_of_up_to_8_decimals_exactly(store, amount):
    assert store.add_spend("agent", DAY, amount) == (amount, amount)
    assert store.spend_totals("agent", DAY) == (amount, amount)
    assert store.add_spend("agent", NEXT_DAY, Decimal(1)) == (Decimal(1), amount + 1)
    assert store.spend_totals("agent", DAY) == (amount, amount + 1)


@pytest.mark.parametrize(
    ("amounts", "total"),
    [
        ([Decimal("0.1234567")], Decimal("0.1234567")),
        ([Decimal("0.0000004"), Decimal("0.0000004")], Decimal("0.0000008")),
    ],
    ids=["7-decimals", "two-below-1e-6"],
)
def test_add_cost_keeps_an_amount_of_up_to_8_decimals_exactly(store, amounts, total):
    run = _run(store)
    for amount in amounts:
        assert store.add_cost(run.run_id, amount) is None
    assert store.get_run(run.run_id).cost_usd == total


# --- amounts the old code accepted and the money rules refuse, on BOTH backends (nothing booked) -----------------
REFUSED = [
    (Decimal("-0.5"), "negative"),
    (Decimal(-1), "negative-whole"),
    (Decimal("1.23456789012"), "11-decimals"),
    (NAN, "nan"),
    (INF, "infinity"),
    (NEG_INF, "minus-infinity"),
    (SNAN, "signaling-nan"),
]


@pytest.mark.parametrize("amount", [a for a, _ in REFUSED], ids=[i for _, i in REFUSED])
def test_add_spend_refuses_what_it_used_to_keep_and_books_nothing(store, amount):
    with pytest.raises(ValueError):
        store.add_spend("agent", DAY, amount)
    assert store.spend_totals("agent", DAY) == (ZERO, ZERO)
    assert store.add_spend("agent", DAY, Decimal(1)) == (
        Decimal(1),
        Decimal(1),
    )  # the counters are clean


@pytest.mark.parametrize("amount", [a for a, _ in REFUSED], ids=[i for _, i in REFUSED])
def test_add_cost_refuses_what_it_used_to_keep_and_the_run_stays_readable(store, amount):
    run = _run(store)
    with pytest.raises(ValueError):
        store.add_cost(run.run_id, amount)
    assert (
        store.get_run(run.run_id).cost_usd == ZERO
    )  # was: a NaN made the Postgres run unreadable for ever

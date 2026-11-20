"""Spend caps and the expiry age are validated by every store kind (the public Store Protocol only).

Written by a different agent than the builders of the validation. A bad cap must never reach the comparison:
a NaN cap would be no cap at all.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.limits import Limits, SpendRefused
from hadavin_sdk.models import new_id
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import SpendCapExceeded, StaleState

DAY = date(2026, 3, 14)
AGENT = "agent-caps"
ONE = Decimal("1.00")
CAP = Decimal("10.00")
ZERO = (Decimal(0), Decimal(0))

BAD_CAPS = [
    Decimal("NaN"),
    Decimal("-NaN"),
    Decimal("sNaN"),
    Decimal("Infinity"),
    Decimal("-Infinity"),
    Decimal(-1),
    Decimal("-0.000000000001"),
    10.0,
    float("nan"),
    float("inf"),
    True,
    False,
    10,
    0,
    "10",
    "",
    None,
]
BAD_CAP_IDS = [f"{type(c).__name__}:{c!r}" for c in BAD_CAPS]


def _reserve(store, rid, usd=ONE, day_cap=CAP, month_cap=CAP):
    store.reserve_spend(rid, AGENT, DAY, usd, day_cap=day_cap, month_cap=month_cap)


@pytest.mark.parametrize("bad", BAD_CAPS, ids=BAD_CAP_IDS)
@pytest.mark.parametrize("which", ["day_cap", "month_cap"])
def test_a_bad_cap_is_refused_and_books_nothing(store, which, bad):
    rid = new_id("res")
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, rid, **{which: bad})
    assert store.spend_totals(AGENT, DAY) == ZERO
    # no row was left behind either: the same id is still free, and the booking then counts once
    _reserve(store, rid)
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)


@pytest.mark.parametrize("bad", BAD_CAPS, ids=BAD_CAP_IDS)
def test_a_bad_cap_is_refused_also_for_an_amount_of_zero(store, bad):
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, new_id("res"), usd=Decimal(0), day_cap=bad)
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, new_id("res"), usd=Decimal(0), day_cap=bad, month_cap=bad)
    assert store.spend_totals(AGENT, DAY) == ZERO


def test_a_cap_of_zero_is_a_valid_cap_that_refuses_everything(store):
    for usd in (Decimal(0), ONE):
        with pytest.raises(SpendCapExceeded) as caught:
            _reserve(store, new_id("res"), usd=usd, day_cap=Decimal(0))
        assert caught.value.which == "day"
        with pytest.raises(SpendCapExceeded) as caught:
            _reserve(store, new_id("res"), usd=usd, month_cap=Decimal(0))
        assert caught.value.which == "month"
    assert store.spend_totals(AGENT, DAY) == ZERO


def test_the_order_of_the_checks(store):
    """The amount, then the caps (ValueError), then the id (StaleState), then the comparison (SpendCapExceeded)."""
    taken = new_id("res")
    _reserve(store, taken)
    booked = (ONE, ONE)
    nan, low = (
        Decimal("NaN"),
        Decimal("0.50"),
    )  # `low` is a valid cap that the booked 1.00 already passes

    # a bad amount wins over a bad cap, a taken id and a passed cap
    for bad_amount in (Decimal("NaN"), Decimal(-1), 1.0, 1, None):
        with pytest.raises(ValueError, match="amount"):
            _reserve(store, taken, usd=bad_amount, day_cap=nan, month_cap=nan)
        with pytest.raises(ValueError, match="amount"):
            _reserve(store, taken, usd=bad_amount, day_cap=low, month_cap=low)
    # a bad cap wins over a taken id and over the other cap being passed
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, taken, day_cap=nan, month_cap=low)
    with pytest.raises(ValueError, match="cap"):
        _reserve(store, taken, day_cap=low, month_cap=nan)
    # a taken id wins over a passed cap
    with pytest.raises(StaleState):
        _reserve(store, taken, day_cap=low, month_cap=low)
    with pytest.raises(StaleState):
        _reserve(store, taken)
    # a free id reaches the comparison: the day is checked before the month
    with pytest.raises(SpendCapExceeded) as caught:
        _reserve(store, new_id("res"), day_cap=low, month_cap=low)
    assert caught.value.which == "day"
    with pytest.raises(SpendCapExceeded) as caught:
        _reserve(store, new_id("res"), month_cap=low)
    assert caught.value.which == "month"
    # none of the refusals booked anything, and the store still works
    assert store.spend_totals(AGENT, DAY) == booked
    _reserve(store, new_id("res"))
    assert store.spend_totals(AGENT, DAY) == (ONE * 2, ONE * 2)


@pytest.mark.parametrize(
    "bad",
    [-1, -(10**9), True, False, 0.0, 1.0, -1.0, float("nan"), "1", "", Decimal(1)],
    ids=repr,
)
def test_a_bad_expiry_age_is_refused_and_expires_nothing(store, bad):
    _reserve(store, new_id("res"))
    with pytest.raises(ValueError, match="older_than_s"):
        store.expire_spend_reservations(bad)
    # the open row is still open: a valid age of 0 now expires exactly that one
    assert store.expire_spend_reservations(0) == 1
    assert store.expire_spend_reservations(0) == 0
    assert store.spend_totals(AGENT, DAY) == (ONE, ONE)  # expiry keeps the worst case booked


# --- Limits.reserve over a registry whose budget is broken ---------------------------------------------------


def _limits(daily, monthly):
    budget = SimpleNamespace(daily=daily, monthly=monthly)
    registry = SimpleNamespace(agents={AGENT: SimpleNamespace(budget_usd=budget)})
    store = MemoryStore()
    return Limits(store, None, registry), store


@pytest.mark.parametrize(
    ("daily", "monthly"),
    [
        (Decimal("NaN"), CAP),
        (CAP, Decimal("NaN")),
        (Decimal("NaN"), Decimal("NaN")),
        (Decimal("sNaN"), CAP),
        (Decimal("Infinity"), CAP),
        (CAP, Decimal(-1)),
        (10.0, CAP),
        (CAP, None),
    ],
    ids=repr,
)
def test_limits_reserve_with_a_broken_cap_is_limits_unavailable(daily, monthly):
    limits, store = _limits(daily, monthly)
    got = None
    with pytest.raises(SpendRefused) as caught:
        got = limits.reserve(AGENT, ONE)
    assert caught.value.reason == "limits_unavailable"
    assert got is None  # no id without a booking
    assert store.spend_totals(AGENT, limits_day()) == ZERO


def limits_day():
    from hadavin_sdk.models import now

    return now().date()


def test_limits_reserve_with_a_sound_budget_books_and_returns_an_id():
    """The control for the double above: the same wiring with real caps books the worst case."""
    limits, store = _limits(CAP, CAP)
    rid = limits.reserve(AGENT, ONE)
    assert isinstance(rid, str) and rid
    assert store.spend_totals(AGENT, limits_day()) == (ONE, ONE)
    with pytest.raises(SpendRefused) as caught:
        limits.reserve(AGENT, CAP)
    assert caught.value.reason == "daily_budget"

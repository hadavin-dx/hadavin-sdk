"""T1 on every store kind (the part that passes on the current code): the own-meter cap, one caller at a time.

What the code does (read, not assumed): ``Limits.blocked`` CHECKS the day and month totals BEFORE a call;
``Limits.charge`` ADDS the real cost AFTER it. There is no reserve step. So one caller at a time admits
ceil(cap / cost) calls: the overshoot is at most one call, by design.

Not here: 50 callers at the same time. All 50 pass the check before any of them charges, so the cap does not hold;
that run, the fix (a reserve step before the call) and the tests that prove it are plan rows A13 and A21b in
handover/PARALLEL-PLAN-2026-11-10.md. What IS here for them: the harness (``tests/meter_support.py``) and its
controls, which show that the schedule can tell a meter that reserves from one that does not.

Every test takes the ``store`` fixture, so each runs on the memory store and, with HADAVIN_TEST_PG_DSN set, on the
postgres store (the production ledger). Amounts are ``Decimal`` dollars because the source ``Budget`` is Decimal.
"""

from __future__ import annotations

import math
import threading
from decimal import Decimal

import pytest

from tests.meter_support import AGENT, CALLERS, HUGE, START, W, build_limits, run_parallel

# --- one caller at a time: the design the code really has -----------------------------------------------------------


@pytest.mark.parametrize(
    "cap,cost",
    [
        ("2.00", "1.00"),
        ("2.50", "1.00"),
        ("1.50", "1.00"),
        ("0.50", "1.00"),  # the cost alone is above the cap: one call goes through, then nothing
        ("1.00", "0.60"),  # a cost that is not W: admitted 2 (0.60, 1.20), overshoot 0.20 < 0.60
        ("1.00", "0.30"),  # admitted 4 (0.30 ... 1.20), overshoot 0.20 < 0.30
    ],
)
def test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call(
    cap, cost, store, monkeypatch
):
    limits, _, _ = build_limits(cap, HUGE, START, monkeypatch, store=store)
    c, k = Decimal(cap), Decimal(cost)
    admitted = 0
    for _ in range(CALLERS):
        if limits.blocked(AGENT):
            continue
        admitted += 1
        limits.charge(AGENT, k)
    day, month = store.spend_totals(AGENT, START.date())
    assert admitted == math.ceil(c / k), f"admitted {admitted} calls for cap {cap}, cost {cost}"
    assert day == month == k * admitted, f"totals {day}, {month} are not {admitted} x {cost}"
    assert day >= c, f"the cap {cap} was never reached: spent {day}"
    assert day - c < k, f"overshoot {day - c} is not less than one call of {cost}"


def test_a_cap_that_is_a_multiple_of_the_cost_is_never_overshot_when_one_at_a_time(
    store, monkeypatch
):
    limits, _, _ = build_limits("3.00", HUGE, START, monkeypatch, store=store)
    admitted = 0
    for _ in range(CALLERS):
        if not limits.blocked(AGENT):
            admitted += 1
            limits.charge(AGENT, W)
    assert admitted == 3, (
        f"admitted {admitted}, expected 3: the call at the exact cap was let through"
    )
    assert store.spend_totals(AGENT, START.date())[0] == Decimal("3.00"), (
        "the day total is not 3.00"
    )


def test_the_monthly_cap_binds_when_it_is_lower_than_the_daily_cap(store, monkeypatch):
    limits, _, _ = build_limits("100.00", "2.00", START, monkeypatch, store=store)
    admitted = 0
    for _ in range(CALLERS):
        if limits.blocked(AGENT):
            break
        admitted += 1
        limits.charge(AGENT, W)
    assert admitted == 2, f"monthly cap 2.00: admitted {admitted}, expected 2"
    assert limits.blocked(AGENT) == ["monthly_budget"], "only the monthly budget is full"


def test_a_charge_is_recorded_in_the_ledger(store, monkeypatch):
    limits, _, _ = build_limits("100.00", HUGE, START, monkeypatch, store=store)
    limits.charge(AGENT, W)
    assert store.spend_totals(AGENT, START.date()) == (W, W), (
        "charge returned totals but the ledger holds nothing"
    )


def test_both_budgets_over_their_caps_are_both_named(store, monkeypatch):
    limits, _, _ = build_limits("1.00", "1.00", START, monkeypatch, store=store)
    assert limits.blocked(AGENT) == [], "nothing is spent yet"
    limits.charge(AGENT, Decimal("2.00"))
    assert limits.blocked(AGENT) == ["daily_budget", "monthly_budget"], (
        "a caller over both caps must see both reasons"
    )


# --- the schedule that the parallel tests (A21b) will use: controls on the harness itself ---------------------------


def test_the_harness_passes_a_meter_that_reserves_before_the_call(store, monkeypatch):
    """Control, not a new meter: the real Limits, but the check and the booking of W happen under one lock at
    reserve time, and settle has nothing left to add (the real cost equals the reserved W). At most floor(cap / W)
    callers are admitted and the day total stays within the cap plus one call."""
    limits, _, _ = build_limits("3.00", HUGE, START, monkeypatch, store=store)
    gate = threading.Lock()

    def reserve() -> bool:
        with gate:
            if limits.blocked(AGENT):
                return False
            limits.charge(AGENT, W)
            return True

    admitted = run_parallel(reserve, lambda: None)
    day = store.spend_totals(AGENT, START.date())[0]
    assert admitted == 3, f"reserve-at-check admitted {admitted} of {CALLERS}, expected 3"
    assert day == Decimal("3.00"), f"day total {day}, expected 3.00"
    assert day <= Decimal("3.00") + W, "the day total passed cap + W"

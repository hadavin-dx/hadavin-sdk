"""T1 (the part that passes on the current code): the own-meter cap holds when 50 callers hit it at the same time (STANDING ORDERS 6d, plan v4 T1).

What the code does (read, not assumed): ``Limits.blocked`` CHECKS the day and month totals BEFORE a call;
``Limits.charge`` ADDS the real cost AFTER it. There is no reserve step. So:
  * one caller at a time admits ceil(cap / cost) calls: the overshoot is at most one call, by design (the same
    shape as the lead's LiteLLM laptop run: cap 1.50, cost 1.00, admitted 2);
  * 50 callers that all pass the check before any of them charges are ALL admitted. The ``blocked`` read and the
    ``charge`` write are two separate store calls with nothing between them. The tests below state the cap
    contract; the parallel ones FAIL on this code (a finding, see the lead report). They are not weakened.
"""

from __future__ import annotations

import math
import threading
from decimal import Decimal

import pytest

from hadavin_sdk.limits import Limits
from tests.meter_support import AGENT, CALLERS, HUGE, START, W, build_limits, run_parallel

# --- sequential: the design the code really has (passes) ------------------------------------------------------------


@pytest.mark.parametrize("cap", ["2.00", "2.50", "1.50", "0.50"])
def test_one_caller_at_a_time_admits_ceil_cap_over_cost_and_overshoots_by_less_than_one_call(
    cap, monkeypatch
):
    limits, store, _ = build_limits(cap, HUGE, START, monkeypatch)
    admitted = 0
    for _ in range(CALLERS):
        if limits.blocked(AGENT):
            continue
        admitted += 1
        limits.charge(AGENT, W)
    c = Decimal(cap)
    day, month = store.spend_totals(AGENT, START.date())
    assert admitted == math.ceil(c / W), f"admitted {admitted} for cap {cap}"
    assert day == month == W * admitted
    assert day - c < W, f"overshoot {day - c} is not less than one worst-case call"
    assert day >= c, "the cap was never reached"


def test_a_cap_that_is_a_multiple_of_the_cost_is_never_overshot_when_one_at_a_time(monkeypatch):
    limits, store, _ = build_limits("3.00", HUGE, START, monkeypatch)
    admitted = sum(
        1 for _ in range(CALLERS) if not limits.blocked(AGENT) and limits.charge(AGENT, W)
    )
    assert admitted == 3
    assert store.spend_totals(AGENT, START.date())[0] == Decimal("3.00")


def test_the_monthly_cap_binds_when_it_is_lower_than_the_daily_cap(monkeypatch):
    limits, _, _ = build_limits("100.00", "2.00", START, monkeypatch)
    admitted = 0
    for _ in range(CALLERS):
        if limits.blocked(AGENT):
            break
        admitted += 1
        limits.charge(AGENT, W)
    assert admitted == 2
    assert limits.blocked(AGENT) == ["monthly_budget"]


# --- harness self-check: the schedule can tell a safe admit from an unsafe one --------------------------------------


def test_the_harness_passes_a_meter_that_reserves_before_the_call(monkeypatch):
    """Control, not a new meter: the real Limits calls, but check and charge of W happen under one lock."""
    limits, store, _ = build_limits("3.00", HUGE, START, monkeypatch)
    gate = threading.Lock()
    real_charge = limits.charge
    # run_parallel charges W again after the provider call; the reserve below already did, so that call is free.
    monkeypatch.setattr(limits, "charge", lambda agent, usd: real_charge(agent, Decimal(0)))

    def admit_and_reserve(lim: Limits) -> bool:
        with gate:
            if lim.blocked(AGENT):
                return False
            real_charge(AGENT, W)
            return True

    admitted = run_parallel(limits, admit_and_reserve)
    assert admitted == 3
    assert store.spend_totals(AGENT, START.date())[0] == Decimal("3.00")

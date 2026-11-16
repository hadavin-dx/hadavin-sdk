"""T1 (the 50-parallel cap contract; FAILS on the current code, see the finding below): the own-meter cap holds when 50 callers hit it at the same time (STANDING ORDERS 6d, plan v4 T1).

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
from decimal import Decimal

import pytest

from tests.meter_support import (
    AGENT,
    CALLERS,
    HUGE,
    START,
    W,
    admit_check_then_charge,
    build_limits,
    run_parallel,
)  # fmt: skip

# --- 50 parallel: the cap contract (FAIL on the current check-then-charge code) -------------------------------------


@pytest.mark.parametrize("cap", ["2.00", "3.00"])
def test_50_parallel_calls_admit_at_most_floor_cap_over_cost(cap, monkeypatch):
    limits, store, _ = build_limits(cap, HUGE, START, monkeypatch)
    admitted = run_parallel(limits, admit_check_then_charge)
    c = Decimal(cap)
    assert admitted <= math.floor(c / W), (
        f"{admitted} of {CALLERS} parallel calls admitted for cap {cap}"
    )
    assert store.spend_totals(AGENT, START.date())[0] <= c


@pytest.mark.parametrize("cap", ["2.50", "1.50"])
def test_50_parallel_calls_overshoot_a_non_multiple_cap_by_less_than_one_call(cap, monkeypatch):
    limits, store, _ = build_limits(cap, HUGE, START, monkeypatch)
    admitted = run_parallel(limits, admit_check_then_charge)
    c = Decimal(cap)
    day = store.spend_totals(AGENT, START.date())[0]
    assert admitted <= math.ceil(c / W), (
        f"{admitted} of {CALLERS} parallel calls admitted for cap {cap}"
    )
    assert day - c < W, f"spent {day} against cap {cap}: overshoot is more than one call"

"""T1, 50 callers at the same time (A21b seed; FAILS on the current Meter, by design until plan row A13 lands).

What goes wrong today: ``Limits.blocked`` CHECKS the totals before a call and ``Limits.charge`` ADDS the cost after
it, with nothing between the two. Every caller passes ``blocked`` before any caller reaches ``charge``, so all 50
are admitted whatever the cap. The fix is a reserve step before the call (plan row A13 in
handover/PARALLEL-PLAN-2026-11-10.md); these tests state the contract it must meet and are not to be weakened.

How a fix plugs in: a caller is a (reserve, settle) pair (``tests/meter_support.py``). ``run_parallel`` calls
``reserve`` for every caller, holds all callers until every one has decided, then calls ``settle`` for each admitted
one. It never charges itself. Replace ``check_then_charge(limits)`` below with the pair of the new meter: ``reserve``
books the worst-case cost W (atomically with the check) and ``settle`` books the real cost minus W.

Every test takes the ``store`` fixture: memory and, with HADAVIN_TEST_PG_DSN set, postgres (the production ledger).
Also to add in A21b: a run with several processes on the postgres store (the lock in the store is per process).
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
    build_limits,
    check_then_charge,
    run_parallel,
)


@pytest.mark.parametrize("cap", ["2.00", "3.00"])
def test_50_parallel_calls_admit_at_most_floor_cap_over_cost(cap, store, monkeypatch):
    limits, _, _ = build_limits(cap, HUGE, START, monkeypatch, store=store)
    admitted = run_parallel(*check_then_charge(limits))
    c = Decimal(cap)
    day = store.spend_totals(AGENT, START.date())[0]
    assert admitted <= math.floor(c / W), f"{admitted} of {CALLERS} parallel calls admitted for cap {cap}"
    assert day <= c, f"spent {day} against cap {cap}"
    assert day <= c + W, "the day total passed cap + W"


@pytest.mark.parametrize("cap", ["2.50", "1.50"])
def test_50_parallel_calls_overshoot_a_non_multiple_cap_by_less_than_one_call(cap, store, monkeypatch):
    limits, _, _ = build_limits(cap, HUGE, START, monkeypatch, store=store)
    admitted = run_parallel(*check_then_charge(limits))
    c = Decimal(cap)
    day = store.spend_totals(AGENT, START.date())[0]
    assert admitted <= math.ceil(c / W), f"{admitted} of {CALLERS} parallel calls admitted for cap {cap}"
    assert day - c < W, f"spent {day} against cap {cap}: overshoot is more than one call"

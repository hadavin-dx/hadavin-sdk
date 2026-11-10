"""T1 finding for A21b: the meter accepts charge values that break a cap (FAILS on the current code, by design).

Probed on 2026-11-10 (memory store and postgres store give the same results, ``Limits`` over each):
  * ``Decimal("NaN")``:       stored without error; from then on ``Limits.blocked`` raises ``decimal.InvalidOperation``
                              for the rest of the day (day) and month (month): the agent stops by crashing.
  * ``Decimal("-1")``:        stored; the day total goes DOWN by 1, so a negative charge buys back a call (cap evasion).
  * ``Decimal("-Infinity")``: stored; day and month totals stay -Infinity for ever (adding a number to -Infinity gives
                              -Infinity), so ``blocked`` never reports a budget again for that day and month: no cap.
  * ``Decimal("Infinity")``:  stored; both budgets read as full for the rest of the day and month (fails closed).
Choke point to fix: ``Limits.charge`` (reject a value that is not finite and not >= 0, with a named error, before
the store is called), plus the same check in each store's ``add_spend`` so a direct caller cannot bypass it.
These tests accept either a raised error or an unchanged ledger, and fail when the ledger takes the value.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from tests.meter_support import AGENT, START, USD, build_limits


@pytest.mark.parametrize("bad", ["NaN", "-1", "Infinity", "-Infinity"])
def test_a_charge_that_is_not_a_finite_amount_of_zero_or_more_never_enters_the_ledger(
    bad, store, monkeypatch
):
    limits, _, _ = build_limits("1000", "1000", START, monkeypatch, store=store)
    limits.charge(AGENT, USD)
    try:
        limits.charge(AGENT, Decimal(bad))
    except (ValueError, ArithmeticError):
        pass  # rejected: fine
    assert store.spend_totals(AGENT, START.date()) == (USD, USD), (
        f"the ledger took a charge of {bad}"
    )
    assert limits.blocked(AGENT) == [], f"after a charge of {bad} the meter no longer answers normally"

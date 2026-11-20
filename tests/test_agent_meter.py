"""`Limits.for_agent` / `Budget.for_agent`: the gate's meter with the agent id bound (F1, core-c's P3 finding).
The gate calls `meter.settle(reservation_id, usd)` and `meter.reserve(agent_id, worst, run_id=...)`; the adapter
settles through `settle_for`, so a hold of another agent is NotFound."""

from decimal import Decimal as D

import pytest

from hadavin_sdk.limits import AgentMeter, Budget, SpendRefused
from hadavin_sdk.store.protocol import NotFound


def test_budget_adapter_reserves_and_settles_without_an_agent_argument():
    budget = Budget(D("1.00"))
    meter = budget.for_agent("ag")
    assert isinstance(meter, AgentMeter)
    rid = meter.reserve(D("0.40"), run_id="r1")
    assert budget.spent == D("0.40")
    assert meter.settle(rid, D("0.12")) == D(0)
    assert budget.spent == D("0.12")


def test_the_gate_call_shape_with_the_agent_id_is_accepted_for_the_bound_agent_only():
    meter = Budget(D("1.00")).for_agent("ag")
    assert meter.reserve("ag", D("0.10"), run_id="r") is not None
    with pytest.raises(ValueError):
        meter.reserve("other", D("0.10"), run_id="r")


def test_settle_of_another_agents_hold_is_not_found():
    budget = Budget(D("1.00"))
    rid = budget.for_agent("a").reserve(D("0.10"))
    with pytest.raises(NotFound):
        budget.for_agent("b").settle(rid, D("0.05"))
    assert budget.spent == D("0.10")  # nothing changed


def test_an_overshoot_is_booked_in_full_and_returned():
    meter = Budget(D("1.00")).for_agent("ag")
    rid = meter.reserve(D("0.10"))
    assert meter.settle(rid, D("0.25")) == D("0.15")


def test_the_cap_still_refuses_through_the_adapter():
    meter = Budget(D("0.30")).for_agent("ag")
    meter.reserve(D("0.20"))
    with pytest.raises(SpendRefused) as err:
        meter.reserve(D("0.20"))
    assert err.value.reason == "usd_cap"


def test_a_bad_agent_id_is_refused_when_the_adapter_is_built():
    with pytest.raises(ValueError):
        Budget(D(1)).for_agent("")


def test_limits_for_agent_settles_through_settle_for(monkeypatch):
    from hadavin_sdk.limits import Limits

    calls = []

    class Spy(Limits):
        def __init__(self):
            pass

        def reserve(self, agent_id, worst_usd, *, run_id=None):
            calls.append(("reserve", agent_id, worst_usd, run_id))
            return "res-1"

        def settle_for(self, agent_id, reservation_id, actual_usd):
            calls.append(("settle_for", agent_id, reservation_id, actual_usd))
            return D(0)

    meter = Spy().for_agent("ag")
    assert meter.reserve(D("0.4"), run_id="r") == "res-1"
    meter.settle("res-1", D("0.1"))
    assert calls == [("reserve", "ag", D("0.4"), "r"), ("settle_for", "ag", "res-1", D("0.1"))]

"""The Meter contract (interfaces/ii-meter.md, the ten points the model gate relies on) against BOTH meters:
``Limits`` (store-backed, here on the memory store) and ``Budget`` (in memory, with a lock; the eval and replay
command lines). Every check runs once per meter. A point that cannot apply to ``Budget`` (point 8 run cost, point 9
stop state, point 10 expiry tick, and the unknown-agent ``KeyError`` of point 1) is skipped for it with the reason,
and ``test_budget_has_no_...`` asserts that the thing is absent, so a skip is never a hole.

A fake inner client counts calls: a refused reserve must leave it at zero. Written by a different agent than the
builder. The fixtures live in this file, not in conftest, because the mutation runner runs with --noconftest.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from hadavin_sdk.config import Route, load_config
from hadavin_sdk.guard.model_gate import ModelGate
from hadavin_sdk.limits import Budget, Limits, Meter, SpendRefused
from hadavin_sdk.llm.common import worst_case_for
from hadavin_sdk.models import KillSwitch, Reply, Run, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound, StoreUnavailable
from tests.conftest import make_cfg

AGENT = "test-agent"
DAY_CAP = Decimal("1.00")  # the fixture agent's daily budget, and the cap given to Budget
WORST = Decimal("0.30")
MSG = [{"role": "user", "content": "go"}]
ROUTE = Route(
    model_id="fixture-model",
    input_usd_per_mtok=Decimal("3.00"),
    output_usd_per_mtok=Decimal("15.00"),
    max_tokens=1024,
)


class Sink:
    def __init__(self):
        self.rows = []

    def write_outcome(self, event):
        self.rows.append(event)
        return event.event_id

    def write_intent(self, event):
        self.rows.append(event)
        return event.event_id


class LimitsHarness:
    name = "limits"
    cap_reason = "daily_budget"

    def __init__(self, tmp_path):
        reg = load_registry(load_config(make_cfg(tmp_path)))
        self.store, self.sink = MemoryStore(), Sink()
        self.meter: Meter = Limits(self.store, self.sink, reg)

    def booked(self) -> Decimal:
        return self.store.spend_totals(AGENT, now().date())[0]

    def new_run(self) -> str:
        run = Run(
            agent_id=AGENT, principal_id="svc:test-agent", trigger_kind="event", trigger_ref="-"
        )
        self.store.create_run(run)
        return run.run_id

    def run_cost(self, run_id) -> Decimal:
        return self.store.get_run(run_id).cost_usd


class BudgetHarness:
    name = "budget"
    cap_reason = "usd_cap"

    def __init__(self, tmp_path):
        self.meter: Meter = Budget(DAY_CAP)

    def booked(self) -> Decimal:
        return self.meter.spent


@pytest.fixture(params=["limits", "budget"])
def h(request, tmp_path):
    return {"limits": LimitsHarness, "budget": BudgetHarness}[request.param](tmp_path)


def only_limits(h, why):
    if h.name != "limits":
        pytest.skip(f"does not apply to Budget: {why}")


class Client:
    """The fake inner client: counts calls, can raise, replies with a fixed cost."""

    def __init__(self, cost="0.10", raises=None):
        self.calls, self.raises = 0, raises
        self.reply = Reply(text="ok", cost_usd=Decimal(cost), model_id="m")

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.calls += 1
        if self.raises is not None:
            raise self.raises
        return self.reply


def gate_on(h, client, *, sink=None, worst=WORST):
    """The model gate over the meter under test; the worst case is fixed so the tests can name it."""
    return ModelGate(client, meter=h.meter, audit=sink, worst_case=lambda *_a: worst).bind(
        AGENT, h.new_run() if h.name == "limits" else "case-1"
    )


# ---------------------------------------------------------------------------------------------- point 1


def test_p1_reserve_returns_an_id_only_after_the_worst_case_is_booked(h):
    rid = h.meter.reserve(AGENT, WORST)
    assert isinstance(rid, str) and rid
    assert h.booked() == WORST, "an id came back before the worst case was booked"
    assert h.meter.reserve(AGENT, WORST) != rid, "two holds got one id"
    assert h.booked() == 2 * WORST


def test_p1_a_refused_reserve_books_nothing_and_the_client_is_not_called(h):
    h.meter.reserve(AGENT, Decimal("0.95"))
    client = Client()
    bound = gate_on(h, client, worst=Decimal("0.10"))
    with pytest.raises(SpendRefused) as refused:
        bound.chat(MSG, system="s", route="default")
    assert refused.value.reason == h.cap_reason
    assert h.booked() == Decimal("0.95") and client.calls == 0


def test_p1_the_amount_that_just_fits_is_booked_and_one_cent_more_is_refused(h):
    h.meter.reserve(AGENT, DAY_CAP - Decimal("0.01"))
    h.meter.reserve(AGENT, Decimal("0.01"))
    assert h.booked() == DAY_CAP
    with pytest.raises(SpendRefused) as refused:
        h.meter.reserve(AGENT, Decimal("0.000001"))
    assert refused.value.reason == h.cap_reason


def test_p1_an_unknown_agent_is_a_key_error_and_books_nothing(h):
    only_limits(h, "Budget has no registry of agents: it keeps one total for the whole invocation")
    with pytest.raises(KeyError) as unknown:
        h.meter.reserve("nobody", WORST)
    assert not isinstance(unknown.value, SpendRefused)
    assert h.booked() == 0


def test_p1_a_store_failure_is_limits_unavailable_and_no_id(h, monkeypatch):
    only_limits(h, "Budget has no store that can fail")

    def down(*args, **kw):
        raise StoreUnavailable("down")

    monkeypatch.setattr(h.store, "reserve_spend", down)
    with pytest.raises(SpendRefused) as refused:
        h.meter.reserve(AGENT, WORST)
    assert refused.value.reason == "limits_unavailable" and h.booked() == 0


def test_budget_has_no_registry_run_stop_state_or_expiry():
    budget = Budget(DAY_CAP)
    for absent in (
        "registry",
        "store",
        "blocked",
        "add_cost",
        "expire",
        "expire_reservations",
        "charge",
        "kill_switch",
    ):
        assert not hasattr(budget, absent), (
            f"Budget grew {absent}: update the contract points that skip it"
        )
    assert budget.reserve("any agent at all", WORST)  # no KeyError: there is no registry
    assert not hasattr(Limits, "charge"), "Limits.charge is deleted by the install"


# ---------------------------------------------------------------------------------------------- point 2

HOSTILE = [
    pytest.param(0, id="int zero"),
    pytest.param(1, id="int"),
    pytest.param(0.5, id="float"),
    pytest.param(0.0, id="float zero"),
    pytest.param(True, id="bool"),
    pytest.param(False, id="bool false"),
    pytest.param(None, id="none"),
    pytest.param("0.5", id="str"),
    pytest.param(Decimal("-0.01"), id="negative"),
    pytest.param(Decimal("NaN"), id="nan"),
    pytest.param(Decimal("sNaN"), id="signalling nan"),
    pytest.param(Decimal("Infinity"), id="infinity"),
    pytest.param(Decimal("-Infinity"), id="minus infinity"),
    pytest.param(Decimal(10**9), id="10**9 dollars"),
    pytest.param(Decimal(10**12), id="10**12 dollars"),
    pytest.param(Decimal("0.1234567890123"), id="thirteen places"),
]


@pytest.mark.parametrize("amount", HOSTILE)
def test_p2_a_hostile_amount_is_bad_amount_and_books_nothing(h, amount):
    with pytest.raises(SpendRefused) as refused:
        h.meter.reserve(AGENT, amount)
    assert refused.value.reason == "bad_amount" and h.booked() == 0


@pytest.mark.parametrize("amount", HOSTILE)
def test_p2_a_hostile_amount_in_the_gate_makes_no_call(h, amount):
    client = Client()
    bound = gate_on(h, client, worst=amount)
    with pytest.raises(SpendRefused) as refused:
        bound.chat(MSG, system="s", route="default")
    assert refused.value.reason == "bad_amount" and client.calls == 0


def test_p2_zero_and_the_smallest_amount_are_valid_amounts(h):
    """The rule is "0 or more": a Decimal zero is an amount, and twelve places are the most."""
    assert h.meter.reserve(AGENT, Decimal(0))
    assert h.meter.reserve(AGENT, Decimal("0.000000000001"))
    assert h.booked() == Decimal("0.000000000001")
    assert h.meter.reserve(AGENT, Decimal("0.99"))


# ---------------------------------------------------------------------------------------------- point 3


def test_p3_settle_returns_the_overshoot_from_the_first_settle(h):
    rid = h.meter.reserve(AGENT, WORST)
    assert h.meter.settle(rid, Decimal("0.10")) == 0
    assert h.booked() == Decimal("0.10")
    over = h.meter.reserve(AGENT, WORST)
    assert h.meter.settle(over, Decimal("0.50")) == Decimal("0.20")
    assert h.booked() == Decimal("0.60"), "an actual above the hold must be booked in full"


def test_p3_settle_twice_the_first_wins_and_the_repeat_returns_the_first_result(h):
    rid = h.meter.reserve(AGENT, WORST)
    first = h.meter.settle(rid, Decimal("0.50"))
    assert first == Decimal("0.20")
    assert h.meter.settle(rid, Decimal("0.10")) == first, "a repeat did not return the first result"
    assert h.meter.settle(rid, Decimal("0.99")) == first
    assert h.booked() == Decimal("0.50"), "a second settle changed what is booked"


def test_p3_settling_at_exactly_the_hold_is_no_overshoot(h):
    rid = h.meter.reserve(AGENT, WORST)
    assert h.meter.settle(rid, WORST) == 0 and h.booked() == WORST


# ---------------------------------------------------------------------------------------------- point 4


def test_p4_settle_with_an_unknown_id_is_not_found_from_both_meters(h):
    with pytest.raises(NotFound) as unknown:
        h.meter.settle("res_unknown", Decimal("0.01"))
    assert isinstance(unknown.value, KeyError)
    assert h.booked() == 0


@pytest.mark.parametrize("amount", HOSTILE)
def test_p4_settle_with_a_bad_amount_is_a_value_error_and_the_hold_stays_open(h, amount):
    rid = h.meter.reserve(AGENT, WORST)
    with pytest.raises(ValueError):
        h.meter.settle(rid, amount)
    assert h.booked() == WORST
    assert h.meter.settle(rid, Decimal("0.10")) == 0, "a refused settle closed the hold"
    assert h.booked() == Decimal("0.10")


def test_p4_a_settled_id_is_not_unknown(h):
    rid = h.meter.reserve(AGENT, WORST)
    h.meter.settle(rid, Decimal("0.05"))
    assert h.meter.settle(rid, Decimal("0.05")) == 0  # a repeat, not NotFound


# ---------------------------------------------------------------------------------------------- point 5


def test_p5_cost_known_replaces_the_worst_case_also_when_it_is_zero(h):
    client = Client(cost="0.07")
    gate_on(h, client).chat(MSG, system="s", route="default")
    assert h.booked() == Decimal("0.07")
    free = Client(cost="0")
    gate_on(h, free).chat(MSG, system="s", route="default")
    assert h.booked() == Decimal("0.07") and free.calls == 1


def test_p5_cost_unknown_keeps_the_worst_case_booked(h):
    from types import SimpleNamespace

    reply = SimpleNamespace(text="ok", cost_usd=Decimal("NaN"))
    client = Client()
    client.reply = reply
    assert gate_on(h, client).chat(MSG, system="s", route="default") is reply
    assert h.booked() == WORST, "a reply with no usable cost lowered the hold"


# ---------------------------------------------------------------------------------------------- point 6


def test_p6_a_settle_that_raises_still_returns_the_reply_and_keeps_the_worst_case(h, monkeypatch):
    if h.name == "limits":
        monkeypatch.setattr(
            h.store, "settle_spend", lambda *a, **k: (_ for _ in ()).throw(StoreUnavailable("down"))
        )
    else:
        monkeypatch.setattr(
            Budget, "settle", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
        )
    client = Client(cost="0.10")
    reply = gate_on(h, client).chat(MSG, system="s", route="default")
    assert reply.cost_usd == Decimal("0.10") and client.calls == 1
    assert h.booked() == WORST
    with pytest.raises(SpendRefused):  # and reserve is never retried by the gate: one reserve only
        h.meter.reserve(AGENT, DAY_CAP)


# ---------------------------------------------------------------------------------------------- point 7


def test_p7_the_hold_covers_the_most_one_call_can_cost(h):
    """A reply of the largest size the call allows (every input byte a token, max_tokens out) never overshoots."""
    system, messages = "s" * 500, MSG
    price = worst_case_for({"default": ROUTE}, Client())
    hold = price("default", system, messages, None, None, None)
    size = len(system) + len('[{"content": "go", "role": "user"}]')
    most = (
        Decimal(size) * ROUTE.input_usd_per_mtok
        + Decimal(ROUTE.max_tokens) * ROUTE.output_usd_per_mtok
    ) / Decimal(1_000_000)
    assert hold >= most
    rid = h.meter.reserve(AGENT, hold)
    assert h.meter.settle(rid, most) == 0


# ---------------------------------------------------------------------------------------------- point 8


def test_p8_the_settled_cost_is_added_to_the_runs_cost_by_the_store_once(h):
    only_limits(h, "Budget has no run: it keeps one total for the invocation")
    run_id = h.new_run()
    rid = h.meter.reserve(AGENT, WORST, run_id=run_id)
    assert h.run_cost(run_id) == 0, "the hold alone must not move the run's cost"
    h.meter.settle(rid, Decimal("0.12"))
    h.meter.settle(rid, Decimal("0.12"))  # a repeat adds nothing
    assert h.run_cost(run_id) == Decimal("0.12")
    other = h.meter.reserve(AGENT, WORST, run_id=run_id)
    h.meter.settle(other, Decimal("0.50"))  # an overshoot: the real amount, not the hold
    assert h.run_cost(run_id) == Decimal("0.62")


def test_p8_a_hold_without_a_run_moves_only_the_counters(h):
    only_limits(h, "Budget has no run")
    rid = h.meter.reserve(AGENT, WORST)
    h.meter.settle(rid, Decimal("0.12"))
    assert h.booked() == Decimal("0.12")


def test_p8_the_gate_adds_nothing_to_the_run_cost_by_itself(h):
    only_limits(h, "Budget has no run")
    client = Client(cost="0.10")
    bound = gate_on(h, client)
    bound.chat(MSG, system="s", route="default")
    run_id = bound._run_id
    assert h.run_cost(run_id) == Decimal("0.10"), "added twice (gate and store) or not at all"


# ---------------------------------------------------------------------------------------------- point 9


def test_p9_a_stop_takes_effect_at_the_next_reserve_and_a_hold_made_before_still_settles(h):
    only_limits(
        h, "Budget does not read the stop state (the eval and replay command lines have none)"
    )
    rid = h.meter.reserve(AGENT, WORST)
    h.store.set_kill_switch(KillSwitch(on=True, by="tester"))
    with pytest.raises(SpendRefused) as stopped:
        h.meter.reserve(AGENT, WORST)
    assert stopped.value.reason == "kill_switch" and h.booked() == WORST
    assert h.meter.settle(rid, Decimal("0.10")) == 0  # a settle is never refused by the stop


def test_p9_a_stop_set_after_the_read_lets_that_one_call_through_and_the_next_is_refused(h):
    only_limits(h, "Budget does not read the stop state")
    real = h.store.get_kill_switch

    def late():
        state = real()
        h.store.set_kill_switch(
            KillSwitch(on=True, by="tester")
        )  # set after the read, before the booking
        return state

    h.store.get_kill_switch = late
    assert h.meter.reserve(AGENT, WORST)
    with pytest.raises(SpendRefused) as stopped:
        h.meter.reserve(AGENT, WORST)
    assert stopped.value.reason == "kill_switch"


def test_budget_does_not_read_a_stop_state():
    budget = Budget(DAY_CAP)
    assert budget.reserve("a", WORST)  # nothing to read: no stop can refuse it, only the cap


# ---------------------------------------------------------------------------------------------- point 10


def test_p10_an_expired_hold_stays_at_the_worst_case_and_a_late_settle_can_only_raise_it(h):
    only_limits(h, "Budget has no tick; its equivalent is forfeit (next two tests)")
    low = h.meter.reserve(AGENT, WORST)
    assert h.store.expire_spend_reservations(0) == 1
    assert h.booked() == WORST, "expiry changed the counters"
    assert h.meter.settle(low, Decimal("0.05")) == 0
    assert h.booked() == WORST, "a late settle lowered an expired hold"
    high = h.meter.reserve(AGENT, WORST)
    h.store.expire_spend_reservations(0)
    assert h.meter.settle(high, Decimal("0.50")) == Decimal("0.20")
    assert h.booked() == WORST + Decimal("0.50")


def test_p10_budget_forfeit_is_the_equivalent_a_late_settle_can_only_raise(h):
    if h.name != "budget":
        pytest.skip("Limits is closed by the expiry tick, see the test above")
    low = h.meter.reserve(AGENT, WORST, run_id="c1")
    h.meter.forfeit("c1")
    assert h.meter.settle(low, Decimal("0.05")) == 0
    assert h.booked() == WORST, "a late settle lowered a forfeited hold"
    high = h.meter.reserve(AGENT, WORST, run_id="c2")
    h.meter.forfeit("c2")
    assert h.meter.settle(high, Decimal("0.50")) == Decimal("0.20")
    assert h.booked() == WORST + Decimal("0.50")


def test_p10_budget_forfeit_closes_only_its_own_run_id(h):
    if h.name != "budget":
        pytest.skip("Limits has no run id to close")
    h.meter.reserve(AGENT, WORST, run_id="c1")
    h.meter.forfeit("c1")
    with pytest.raises(SpendRefused) as closed:
        h.meter.reserve(AGENT, Decimal("0.01"), run_id="c1")
    assert closed.value.reason == "usd_cap"
    assert h.meter.reserve(AGENT, Decimal("0.01"), run_id="c2")
    assert h.meter.reserve(AGENT, Decimal("0.01"))


# ---------------------------------------------------------------------------------------------- ordering and failures inside the call


def test_record_then_settle_the_order_is_reserve_call_settle_then_the_audit_row(h):
    log = []

    class Logging:
        def reserve(self, agent_id, worst_usd, *, run_id=None):
            log.append("reserve")
            return h.meter.reserve(agent_id, worst_usd, run_id=run_id)

        def settle(self, reservation_id, actual_usd):
            log.append("settle")
            return h.meter.settle(reservation_id, actual_usd)

    class Row:
        def write_outcome(self, event):
            log.append("audit")
            return event.event_id

    class Logged(Client):
        def chat(self, *a, **k):
            log.append("call")
            return super().chat(*a, **k)

    run_id = h.new_run() if h.name == "limits" else "case-1"
    ModelGate(Logged(), meter=Logging(), audit=Row(), worst_case=lambda *_a: WORST).bind(
        AGENT, run_id
    ).chat(MSG, system="s", route="default")
    assert log == ["reserve", "call", "settle", "audit"]
    assert h.booked() == Decimal("0.10")


@pytest.mark.parametrize(
    "error", [ValueError("bad reply"), KeyboardInterrupt()], ids=["ValueError", "KeyboardInterrupt"]
)
def test_an_exception_inside_the_call_keeps_the_hold_at_the_worst_case(h, error):
    client = Client(raises=error)
    bound = gate_on(h, client)
    with pytest.raises(type(error)):
        bound.chat(MSG, system="s", route="default")
    assert client.calls == 1
    assert h.booked() == WORST, "an exception inside the call released or settled the hold"
    if h.name == "limits":
        assert h.store.expire_spend_reservations(0) == 1  # still open: the tick closes it
        assert h.booked() == WORST
        assert h.run_cost(bound._run_id) == 0


def test_a_refused_reserve_in_the_gate_leaves_the_client_untouched_and_nothing_booked(h):
    client = Client()
    bound = gate_on(h, client, worst=DAY_CAP + Decimal("0.01"))
    with pytest.raises(SpendRefused):
        bound.chat(MSG, system="s", route="default")
    assert client.calls == 0 and h.booked() == 0

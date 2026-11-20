"""B2 of the money lead review (handover/core-b/requests/xr-money-lead-1.md): the live call path must gate on
`Limits.reserve` BEFORE the model call and `Limits.settle` AFTER it (agent_loop.py, today `limits.charge` ->
`add_spend` after the call, and only `limits.blocked()` before). Written failing-first by a different agent than
the builder. The tests that cannot pass today carry `xfail(strict=True)`: they flip loudly when the change lands.

Contract the builder must meet at the model-call site of `Runtime` (agent_loop.py, the `self.llm.chat` call in the
step loop):
  1. before `llm.chat`:  rid = self.limits.reserve(run.agent_id, worst, run_id=run.run_id)
     where worst = worst_case_for(registry.config.routes, llm)(route, system, messages, tools, documents, None)
     (llm/common.py; route price and max_tokens). SpendRefused -> run ends NEEDS_PERSON (STOPPED for
     kill_switch) with the audit code `limits.<reason>`; no model call.
  2. reply -> self.limits.settle_for(run.agent_id, rid, reply.cost_usd) (or `settle`), exactly once.
  3. ProviderError (ProviderExhausted included) -> NO settle: the hold stays booked at the worst case.
Memory store always; the Postgres store (runtime role) too when HADAVIN_TEST_PG_DSN is set."""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest

from hadavin_sdk.limits import Limits
from hadavin_sdk.llm.common import worst_case_for
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.models import Reply, RunState, now
from hadavin_sdk.store import MemoryStore
from tests.contracts.kinds import (
    KINDS,
    store_postgres,  # noqa: F401 - registers the kind
)
from tests.k5_support import build_runtime, handle, k5_cfg

D = Decimal
S = RunState
AGENT = "test-agent"
# worst case of one call = 1000 tokens * 600 USD/Mtok = 0.60 plus a few thousand input bytes at 0.01 USD/Mtok
ROUTES = {
    "default": {
        "model_id": "fake-model",
        "input_usd_per_mtok": "0.01",
        "output_usd_per_mtok": "600.00",
        "max_tokens": 1000,
    }
}


class StubLLM:
    """Counts calls, answers 'no action' at `cost` (or raises `error`). `hold_first` parks the first call until
    `release` is set (to overlap two runs). `max_attempts` is absent: one request per call."""

    def __init__(self, cost="0.60", error=None, hold_first=False):
        self.cost, self.error, self.hold_first = D(cost), error, hold_first
        self.calls: list[dict] = []
        self.order: list[str] = []
        self.entered, self.release = threading.Event(), threading.Event()
        self._lock = threading.Lock()

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        import copy

        with self._lock:
            first = not self.calls
            self.calls.append(
                {
                    "route": route,
                    "system": system,
                    "messages": copy.deepcopy(messages),
                    "tools": copy.deepcopy(tools),
                    "documents": list(documents or []),
                }
            )
            self.order.append("chat")
        if self.hold_first and first:
            self.entered.set()
            assert self.release.wait(10)
        if self.error is not None:
            raise self.error
        return Reply(text="Nothing to do.", cost_usd=self.cost, model_id="fake-model")


@pytest.fixture(params=["memory", "postgres"])
def store(request, tmp_path):
    if request.param == "memory":
        yield MemoryStore()
        return
    gen = KINDS["store"]["postgres"](tmp_path / "pg")  # skips without HADAVIN_TEST_PG_DSN
    try:
        yield next(gen)
    finally:
        gen.close()


@pytest.fixture
def world(tmp_path, store):
    cfg = k5_cfg(tmp_path, config={"routes": ROUTES}, max_run_usd="50.00")

    def make(llm):
        rt, _cards = build_runtime(cfg, llm, store=store)
        spy = Spy(rt.limits, llm)
        rt.limits.reserve, rt.limits.settle = spy.reserve, spy.settle
        rt.limits.settle_for = spy.settle_for
        return rt, spy

    return make


class Spy:
    """Records Limits.reserve / settle calls in order, interleaved with the model call (llm.order)."""

    def __init__(self, limits: Limits, llm: StubLLM):
        self._real = (limits.reserve, limits.settle, limits.settle_for)
        self.reserves: list[tuple] = []
        self.settles: list[tuple] = []
        self.llm = llm

    def reserve(self, agent_id, worst_usd, *, run_id=None):
        self.llm.order.append("reserve")
        try:
            rid = self._real[0](agent_id, worst_usd, run_id=run_id)
        except Exception as exc:
            self.reserves.append((agent_id, worst_usd, run_id, exc))
            raise
        self.reserves.append((agent_id, worst_usd, run_id, rid))
        return rid

    def settle(self, reservation_id, actual_usd):
        self.llm.order.append("settle")
        self.settles.append((reservation_id, actual_usd))
        return self._real[1](reservation_id, actual_usd)

    def settle_for(self, agent_id, reservation_id, actual_usd):
        self.llm.order.append("settle")
        self.settles.append((reservation_id, actual_usd))
        return self._real[2](agent_id, reservation_id, actual_usd)


def _day(store) -> Decimal:
    return store.spend_totals(AGENT, now().date())[0]


def _worst(llm: StubLLM, rt) -> Decimal:
    c = llm.calls[0]
    fn = worst_case_for(rt.registry.config.routes, llm)
    return fn(c["route"], c["system"], c["messages"], c["tools"], c["documents"], None)


# (1) the cap holds across runs: a second run is refused BEFORE its model call ------------------------------


def test_second_sequential_run_is_refused_before_its_model_call(world, store):
    llm = StubLLM(cost="0.60")
    rt, _spy = world(llm)
    first = handle(rt)
    assert first.state in (S.NO_ACTION, S.NEEDS_PERSON)
    assert _day(store) == D("0.60")  # today's blocked() still passes: 0.60 < 1.00
    second = handle(rt, b"another checkout 5xx from 10.0.0.6, revision 18")
    assert len(llm.calls) == 1, (
        "the second run reached the model: 0.60 + 0.60 worst case > 1.00 cap"
    )
    assert second.state in (S.NEEDS_PERSON, S.STOPPED)
    assert _day(store) <= D("1.00")


def test_overlapping_runs_cannot_book_more_than_the_cap(world, store):
    llm = StubLLM(cost="0.60", hold_first=True)
    rt, _spy = world(llm)
    out = {}
    t = threading.Thread(target=lambda: out.setdefault("a", handle(rt)))
    t.start()
    try:
        assert llm.entered.wait(10)  # run A holds its reservation and is inside the model call
        b = handle(rt, b"another checkout 5xx from 10.0.0.6, revision 18")
        assert len(llm.calls) == 1, "run B called the model while A's worst case was open"
        assert b.state in (S.NEEDS_PERSON, S.STOPPED)
    finally:
        llm.release.set()
        t.join(10)
    assert _day(store) <= D("1.00")


# (2) the reservation comes before the model call, priced from the route -----------------------------------


def test_reserve_comes_before_the_model_call_with_the_worst_case(world):
    llm = StubLLM(cost="0.20")
    rt, spy = world(llm)
    handle(rt)
    assert llm.order[:2] == ["reserve", "chat"]
    agent_id, worst, run_id, rid = spy.reserves[0]
    assert agent_id == AGENT and run_id is not None and isinstance(rid, str)
    route = rt.registry.config.routes["default"]
    floor = D(route.max_tokens) * route.output_usd_per_mtok / D(1_000_000)
    assert worst >= floor == D("0.60")
    assert worst == _worst(llm, rt)  # llm.common.worst_case_for(routes, llm) on what was sent


# (3) a normal reply settles once with the real cost ------------------------------------------------------


def test_settle_once_with_the_actual_cost(world, store):
    llm = StubLLM(cost="0.20")
    rt, spy = world(llm)
    run = handle(rt)
    assert len(spy.reserves) == 1 and len(spy.settles) == 1
    assert spy.settles[0] == (spy.reserves[0][3], D("0.20"))
    assert llm.order == ["reserve", "chat", "settle"]
    assert _day(store) == D("0.20")
    assert rt.store.get_run(run.run_id).cost_usd == D("0.20")


# (4) a provider error leaves the hold at the worst case: no settle at 0 ----------------------------------


@pytest.mark.parametrize("error", [ProviderExhausted("quota"), ProviderError("boom")])
def test_provider_error_keeps_the_hold_at_the_worst_case(world, store, error):
    llm = StubLLM(error=error)
    rt, spy = world(llm)
    run = handle(rt)
    assert run.state == S.NEEDS_PERSON
    assert len(spy.reserves) == 1 and spy.settles == []
    assert _day(store) == spy.reserves[0][1] == _worst(llm, rt)  # booked at the worst case, not 0


# (5) a refused reserve ends the run in the spend-refused state with an audit code ------------------------


def test_refused_reserve_ends_run_with_audit_code(world, store):
    llm = StubLLM(cost="0.60")
    rt, spy = world(llm)
    handle(rt)
    refused = handle(rt, b"another checkout 5xx from 10.0.0.6, revision 18")
    assert len(spy.reserves) == 2 and isinstance(spy.reserves[1][3], Exception)
    assert (
        refused.state == S.NEEDS_PERSON
    )  # the state a spent budget gives today: limits.daily_budget
    codes = [e.error_code for e in rt.audit.events(refused.run_id) if e.error_code]
    assert any(c.startswith("limits.") or c.endswith("budget") for c in codes), codes
    assert refused.reason_code is not None and (
        "budget" in refused.reason_code or "limits" in refused.reason_code
    )


# (6) no double counting ---------------------------------------------------------------------------------


def test_day_total_is_the_actual_cost_not_actual_plus_worst_case(world, store):
    llm = StubLLM(cost="0.20")
    rt, spy = world(llm)
    handle(rt)
    day, month = store.spend_totals(AGENT, now().date())
    assert (day, month) == (D("0.20"), D("0.20"))
    assert (
        spy.reserves and spy.settles
    )  # the numbers above come from reserve + settle, not from charge


# guard: the baseline that holds today, so a regression in the fixture shows -----------------------------


def test_fixture_runs_the_agent_and_books_the_cost(world, store):
    llm = StubLLM(cost="0.20")
    rt, _ = world(llm)
    run = handle(rt)
    assert len(llm.calls) == 1 and run.state in (S.NO_ACTION, S.NEEDS_PERSON)
    assert _day(store) == D("0.20")


# (7) the settle fallback, the other refusals, the overshoot (review B2-1: M2, m2, m6) -------------------------


def _definite_errors():
    from psycopg.errors import DataError

    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.protocol import NotFound, StaleState

    return [
        RuntimeError("row missing"),
        ConfigError("HD004"),
        StaleState("x"),
        DataError("x"),
        NotFound("x"),
    ]


@pytest.mark.parametrize("error", _definite_errors(), ids=lambda e: type(e).__name__)
def test_a_rolled_back_settle_failure_books_the_run_cost_once(world, error):
    llm = StubLLM(cost="0.20")
    rt, _spy = world(llm)

    def refuse(agent_id, rid, usd):
        raise error

    rt.limits.settle_for = refuse
    run = handle(rt)
    assert run.reason_code != "limits.limits_unavailable"
    assert rt.store.get_run(run.run_id).cost_usd == D("0.20")  # the direct booking, once


def _ambiguous_errors():
    from psycopg import InterfaceError, OperationalError

    from hadavin_sdk.store.protocol import StoreUnavailable

    return [
        OperationalError("lost"),
        InterfaceError("closed"),
        ConnectionError("x"),
        TimeoutError(),
        StoreUnavailable("x"),
    ]


@pytest.mark.parametrize("error", _ambiguous_errors(), ids=lambda e: type(e).__name__)
def test_ambiguous_settle_failure_does_not_double_count_the_run_cost(world, error):
    llm = StubLLM(cost="0.20")
    rt, _spy = world(llm)
    real = rt.limits.settle_for

    def commit_then_lose_the_reply(agent_id, rid, usd):
        real(agent_id, rid, usd)  # the settle committed and booked the run cost
        raise error

    rt.limits.settle_for = commit_then_lose_the_reply
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits.limits_unavailable")
    assert rt.store.get_run(run.run_id).cost_usd == D("0.20")  # not 0.40


def test_settle_failure_with_a_store_that_is_down_never_raises(world):
    from hadavin_sdk.runtime.agent_loop import Runtime

    llm = StubLLM(cost="0.20")
    rt, _spy = world(llm)

    def down(*a, **kw):
        raise RuntimeError("store down")

    rt.limits.settle_for = down
    rt.store = type("Down", (), {"__getattr__": lambda self, n: down})()
    run = Runtime._settle_model_call(
        rt, type("R", (), {"run_id": "r", "agent_id": AGENT})(), "res-1", D("0.20")
    )
    assert run is not None  # the run is returned, nothing was raised


def test_a_bad_reply_cost_ends_the_run_and_never_raises(world):
    class BadCost(StubLLM):
        def chat(self, *a, **kw):
            super().chat(*a, **kw)
            # a client that skips Reply validation (a test double or a future client)
            return Reply.model_construct(
                text="x", cost_usd=D("NaN"), model_id="m", tool_calls=[], stop_reason=None
            )

    llm = BadCost()
    rt, _spy = world(llm)
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits.limits_unavailable")


def test_kill_switch_refusal_at_reserve_stops_the_run_before_the_model(world):
    from hadavin_sdk.limits import SpendRefused

    llm = StubLLM()
    rt, _spy = world(llm)

    def refuse(agent_id, worst, *, run_id=None):
        raise SpendRefused("kill_switch")

    rt.limits.reserve = refuse
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.STOPPED, "kill_switch")
    assert llm.calls == []


@pytest.mark.parametrize(
    ("exc", "code"),
    [("bad_amount", "limits.bad_amount"), (RuntimeError("x"), "limits.limits_unavailable")],
)
def test_a_pricing_failure_ends_the_run_before_the_model(world, monkeypatch, exc, code):
    from hadavin_sdk.limits import SpendRefused
    from hadavin_sdk.runtime import agent_loop

    def broken(routes, llm):
        def worst_case(*a):
            raise SpendRefused(exc) if isinstance(exc, str) else exc

        return worst_case

    monkeypatch.setattr(agent_loop, "worst_case_for", broken)
    llm = StubLLM()
    rt, _spy = world(llm)
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, code)
    assert llm.calls == []


def test_a_reply_above_the_worst_case_is_booked_in_full_through_the_loop(world, store):
    llm = StubLLM(cost="0.90")  # worst case is about 0.60: an overshoot of 0.30
    rt, spy = world(llm)
    run = handle(rt)
    assert spy.settles[0][1] == D("0.90")
    assert _day(store) == D("0.90")
    assert rt.store.get_run(run.run_id).cost_usd == D("0.90")

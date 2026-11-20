"""Step F-install: the model gate installed in every place that calls a model (run loop, judge inside the run,
shadow-card judge, evals gate, replay loop), the worst-case function, and the deletions.

Written by a different agent than the builder, from tickets/F-install.md (RESOLUTION of review round 2 wins over
round 1, which wins over the UPDATE, which wins over the draft) and interfaces/ii-meter.md. Fakes and scripted
clients only: no network, no real model call. The killers of ``tests/gate_install_mutants.py`` live here, so a
failing assertion carries a distinctive message (the runner reads the first failing line).

The fixtures are defined in this file, not taken from conftest, because the mutation runner runs with --noconftest.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import json
import threading
import time
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from hadavin_sdk import cli, defaults, evals
from hadavin_sdk.config import ConfigError, Route, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.injection import AnyOf, RegexDetector, injection_check
from hadavin_sdk.guard.judge import JudgeDetector
from hadavin_sdk.guard.model_gate import BoundGate, GateRefused, ModelGate, UnmaskedInput
from hadavin_sdk.k1b import loop
from hadavin_sdk.limits import Budget, Limits, SpendRefused
from hadavin_sdk.llm.common import worst_case_for, worst_case_usd
from hadavin_sdk.llm.protocol import ProviderError
from hadavin_sdk.models import AuditEvent, Reply, RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.conftest import make_cfg
from tests.contracts.kinds.detectors import JUDGE_COST, JudgeModel
from tests.fixtures import k5_tools
from tests.k1b_support import ScriptedLLM, make_bundle, submit, submit_not_sure, tool_reply
from tests.k5_support import ScriptLLM, build_runtime, k5_cfg
from tests.k5_support import handle as k5_handle
from tests.test_k1b_replay import LOG0, Env
from tests.test_k3_pilot import PROPOSE, captured, demo_cfg
from tests.test_k3_pilot import ScriptedLLM as K3Scripted
from tests.test_k3_pilot import handle as k3_handle
from tests.test_k3_pilot import reply as k3_reply
from tests.test_k3_pilot import runtime as k3_runtime
from tests.test_s5_runtime import _doc
from tests.test_s5_runtime import build as build_rt

S = RunState
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"
AGENT = "test-agent"
PRINCIPAL = "svc:test-agent"
RUN_COST = Decimal("0.00225")  # what the recorded answer of create.txt costs on the fixture route
ROUTE = Route(
    model_id="fixture-model",
    input_usd_per_mtok=Decimal("3.00"),
    output_usd_per_mtok=Decimal("15.00"),
    max_tokens=1024,
)
ONE_MILLION = Decimal(1_000_000)


@pytest.fixture
def cfg_dir(tmp_path):
    return make_cfg(tmp_path)


@pytest.fixture
def env(tmp_path, cfg_dir):
    return Env(tmp_path, cfg_dir)


# ------------------------------------------------------------------------------------------------ doubles


class Spy:
    """Stands in for ``rt.limits``: records every reserve and settle and delegates to the real meter."""

    def __init__(self, inner):
        self.inner = inner
        self.reserved: list[tuple[str, str, Decimal, str | None]] = []
        self.settles: list[tuple[str, Decimal, Decimal]] = []

    def reserve(self, agent_id, worst_usd, *, run_id=None):
        rid = self.inner.reserve(agent_id, worst_usd, run_id=run_id)
        self.reserved.append((rid, agent_id, worst_usd, run_id))
        return rid

    def settle(self, reservation_id, actual_usd):
        over = self.inner.settle(reservation_id, actual_usd)
        self.settles.append((reservation_id, actual_usd, over))
        return over

    def __getattr__(self, name):
        return getattr(self.inner, name)


class Refuser:
    """Lets the first ``after`` reserves through to the real meter, then refuses every one with a fresh ``make()``."""

    def __init__(self, inner, make, after=0):
        self.inner, self.make, self.after, self.seen = inner, make, after, 0

    def reserve(self, agent_id, worst_usd, *, run_id=None):
        self.seen += 1
        if self.seen > self.after:
            raise self.make()
        return self.inner.reserve(agent_id, worst_usd, run_id=run_id)

    def settle(self, reservation_id, actual_usd):
        return self.inner.settle(reservation_id, actual_usd)

    def __getattr__(self, name):
        return getattr(self.inner, name)


class Client:
    """A model client double: counts its calls, keeps what it was sent, returns one reply or raises."""

    def __init__(self, cost="0.004", raises=None, reply=None):
        self.calls, self.sent, self.raises = 0, [], raises
        self.reply = reply or Reply(text="nothing to do", cost_usd=Decimal(cost), model_id="m")

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.calls += 1
        self.sent.append({"messages": messages, "documents": documents, "system": system})
        if self.raises is not None:
            raise self.raises
        return self.reply


class Sink:
    """Only ``write_outcome``, as the gate may use nothing else."""

    def __init__(self, raises=None):
        self.rows, self.raises = [], raises

    def write_outcome(self, event: AuditEvent):
        if self.raises is not None:
            raise self.raises
        self.rows.append(event)
        return event.event_id


def wc(*_args) -> Decimal:
    return Decimal("0.03")


def judge_only(llm=None):
    return JudgeDetector(llm or JudgeModel(), "screen", 0.5)


def llm_rows(rt, run):
    return [e for e in rt.audit.events(run.run_id) if (e.domain, e.operation) == ("llm", "chat")]


def day_spend(rt, run) -> Decimal:
    return rt.store.spend_totals(AGENT, run.created_at.date())[0]


def handled(rt, document, *, what="the run"):
    """handle(), but a refusal that escapes it fails with a message (the run would be stranded in WORKING)."""
    return stranded_check(lambda: rt.handle(AGENT, PRINCIPAL, document), what)


def stranded_check(call, what):
    escaped = None
    try:
        return call()
    except (SpendRefused, GateRefused) as exc:
        escaped = type(exc).__name__
    # outside the except: no chained noise, and an AssertionError (the runner reads pytest.fail as a crash)
    raise AssertionError(f"the refusal escaped handle and stranded {what}: {escaped}")


# ------------------------------------------------------------------------------------------------ N: normal


def test_n1_one_run_books_spend_run_cost_and_one_audit_row(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert len(spy.reserved) == 1, "the run's chat call was not reserved on the meter"
    (rid, agent, worst, run_id) = spy.reserved[0]
    assert (agent, run_id) == (AGENT, run.run_id)
    assert worst >= Decimal("0.01536"), "the hold is below the output part of the worst case"
    assert [(r, a) for r, a, _ in spy.settles] == [(rid, RUN_COST)], "one settle of the real cost"
    assert rt.store.get_run(run.run_id).cost_usd == RUN_COST, (
        "run cost is not the sum of the settles"
    )
    assert day_spend(rt, run) == RUN_COST, "day spend is not the settled cost of the one call"
    (row,) = llm_rows(rt, run)
    assert (row.result, row.error_code, row.source, row.principal) == ("ok", None, "gate", AGENT)
    assert row.object_ref == rid


def test_n2_a_judge_in_the_run_settles_twice_into_the_run_cost(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.detector = AnyOf([RegexDetector(0.5), judge_only()])
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    amounts = [usd for _, usd, _ in spy.settles]
    assert len(amounts) == 2, "the judge call and the chat call must each settle once in the run"
    assert amounts == [JUDGE_COST, RUN_COST]
    assert {run_id for _, _, _, run_id in spy.reserved} == {run.run_id}
    assert rt.store.get_run(run.run_id).cost_usd == JUDGE_COST + RUN_COST
    assert day_spend(rt, run) == JUDGE_COST + RUN_COST
    assert len(llm_rows(rt, run)) == 2


def test_n3_the_shadow_card_judge_is_charged_to_the_runs_agent(tmp_path):
    hooks, cards = captured()
    rt = k3_runtime(
        demo_cfg(tmp_path, {"restart_service": "shadow"}), K3Scripted(k3_reply(PROPOSE)), hooks
    )
    model = JudgeModel()
    rt.detector = judge_only(model)  # replaced after construction, as tests and apps do
    rt.limits = spy = Spy(rt.limits)
    run = k3_handle(rt)
    assert (run.state, run.reason_code) == (S.NO_ACTION, "shadow")
    assert len(model.calls) == 2, "the judge screens the document and, again, the shadow diagnosis"
    assert len(spy.settles) == 3, "the shadow-card judge call was not booked (document, chat, card)"
    assert rt.store.get_run(run.run_id).cost_usd == 2 * JUDGE_COST
    assert day_spend(rt, run) == 2 * JUDGE_COST
    assert len(cards) == 1


def test_n4_evals_with_max_usd_stops_at_the_cap(cfg_dir):
    reg = load_registry(load_config(cfg_dir))
    worst = worst_case_for(reg.config.routes, Client())("default", "", [], None, None, None)
    client = Client(cost="0.01")
    qualified = reg.config.root / "qualified.jsonl"
    before = qualified.read_bytes() if qualified.exists() else b""
    with pytest.raises(SpendRefused) as stopped:
        evals.gate(reg, client, AGENT, k=3, max_usd=worst + Decimal("0.005"))
    assert stopped.value.reason == "usd_cap"
    assert client.calls == 1, "the second call passed the cap"
    assert (qualified.read_bytes() if qualified.exists() else b"") == before


def test_n4_a_cap_below_one_worst_case_makes_no_call(cfg_dir):
    reg = load_registry(load_config(cfg_dir))
    client = Client()
    with pytest.raises(SpendRefused) as stopped:
        evals.gate(reg, client, AGENT, max_usd=Decimal("0.001"))
    assert (stopped.value.reason, client.calls) == ("usd_cap", 0)


def test_n4_the_command_prints_the_reason_to_stderr_and_exits_2(cfg_dir, capsys):
    argv = ["--config", str(cfg_dir), "gate", AGENT]
    assert cli.main([*argv, "--max-usd", "0.001"]) == 2
    assert "gate stopped: usd_cap" in capsys.readouterr().err


@pytest.mark.parametrize("bad", ["0", "-1", "nan", "inf", "x"])
def test_n4_the_flag_refuses_an_amount_that_is_not_finite_and_above_zero(cfg_dir, bad, capsys):
    with pytest.raises(SystemExit) as ended:
        cli.main(["--config", str(cfg_dir), "gate", AGENT, "--max-usd", bad])
    assert ended.value.code == 2


def test_n5_replay_usd_is_the_sum_of_the_settles(env, monkeypatch):
    settles = []
    real = Budget.settle

    def spy(self, reservation_id, actual_usd):
        settles.append(actual_usd)
        return real(self, reservation_id, actual_usd)

    monkeypatch.setattr(Budget, "settle", spy)
    costs = ("0.001", "0.002", "0.003", "0.004")
    llm = ScriptedLLM(
        [
            tool_reply("list_data", cost=costs[0]),
            tool_reply("query_logs", cost=costs[1]),
            submit("api", "bad_deploy", LOG0, cost=costs[2]),
            submit_not_sure(cost=costs[3]),
        ]
    )
    env.run(llm)
    run = json.loads((env.out / "run1" / "run.json").read_text(encoding="utf-8"))
    assert len(settles) == len(llm.calls) == 4
    assert Decimal(run["usd"]) == sum(settles) == sum(Decimal(c) for c in costs), (
        "replay usd is not the sum of the settles"
    )


def test_n5_a_judge_call_in_replay_is_booked_on_the_same_budget(env):
    verdict = Reply(
        text='{"injection": false, "confidence": 0.9}', cost_usd=Decimal("0.05"), model_id="m"
    )
    judge_llm = ScriptedLLM([verdict, verdict])  # one tool result per case
    route = env.reg.agents[AGENT].model_route
    llm = ScriptedLLM([tool_reply("list_data", cost="0.002"), submit_not_sure(cost="0.003")] * 2)
    env.run(llm, detector=JudgeDetector(judge_llm, route, 0.5))
    run = json.loads((env.out / "run1" / "run.json").read_text(encoding="utf-8"))
    assert len(judge_llm.calls) == 2
    assert Decimal(run["usd"]) == Decimal("0.110"), (
        "the replay judge call was not booked on the invocation's budget"
    )


# ------------------------------------------------------------------------------------------------ E: edge


def test_e1_a_client_replaced_after_construction_is_still_metered(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    other = Client(cost="0.004")
    rt.llm = other
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"))
    assert other.calls == 1 and run.state == S.NO_ACTION
    assert [usd for _, usd, _ in spy.settles] == [Decimal("0.004")], (
        "the replaced client ran unmetered"
    )
    assert day_spend(rt, run) == rt.store.get_run(run.run_id).cost_usd == Decimal("0.004")


def test_e2_a_replaced_detector_is_metered_too(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    model = JudgeModel()
    rt.detector = judge_only(model)
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert len(model.calls) == 1
    assert JUDGE_COST in [usd for _, usd, _ in spy.settles], "the replaced detector ran unmetered"
    assert rt.store.get_run(run.run_id).cost_usd == JUDGE_COST + RUN_COST


def test_e2_a_detector_that_calls_no_model_is_used_as_it_is(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    seen = []

    class Plain:
        backend = "plain"

        def check(self, text, source):
            seen.append(source)
            return RegexDetector(0.5).check(text, source)

    rt.detector = Plain()
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen == ["document"] and run.state != S.WORKING


def test_e3_a_model_gate_in_rt_llm_is_used_as_it_is(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    own = Spy(Budget(Decimal(5)))
    sink = Sink()

    class Capturing(ModelGate):
        bound: ClassVar[list] = []

        def bind(self, agent_id, run_id, **kw):
            self.bound.append((agent_id, run_id, kw))
            return super().bind(agent_id, run_id, **kw)

    rt.llm = Capturing(rt.llm, meter=own, audit=sink, worst_case=wc)
    rt.limits = theirs = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert len(own.reserved) == 1 and not theirs.reserved, "the gate in rt.llm was wrapped again"
    assert [r.result for r in sink.rows] == ["ok"]
    ((agent_id, run_id, kw),) = Capturing.bound
    assert (agent_id, run_id) == (AGENT, run.run_id)
    assert isinstance(kw.get("mapping"), runmap.RunMap), (
        "the run's live map is not handed to the gate"
    )


def test_e3_a_bound_gate_in_rt_llm_ends_the_run_gate_error(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    client = Client()
    rt.llm = ModelGate(client, meter=Budget(Decimal(5)), audit=None, worst_case=wc).bind("a", "r")
    assert isinstance(rt.llm, BoundGate)
    run = handled(rt, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "gate_error")
    assert client.calls == 0


def test_e3_a_gate_is_never_wrapped_twice():
    gate = ModelGate(Client(), meter=Budget(Decimal(1)), audit=None, worst_case=wc)
    with pytest.raises(TypeError):
        ModelGate(gate, meter=Budget(Decimal(1)), audit=None, worst_case=wc)
    with pytest.raises(TypeError):
        ModelGate(gate.bind("a", "r"), meter=Budget(Decimal(1)), audit=None, worst_case=wc)


def test_e4_an_actual_above_the_reserved_is_booked_in_full(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(cost="5.00")
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"))
    ((_, _, worst, _),) = spy.reserved
    ((_, actual, over),) = spy.settles
    assert actual == Decimal("5.00") and over == actual - worst > 0
    assert day_spend(rt, run) == rt.store.get_run(run.run_id).cost_usd == Decimal("5.00")
    assert [e.operation for e in rt.audit.events() if e.domain == "limits"].count("overshoot") == 1


def test_e5_a_reserve_refused_with_0_001_left_makes_no_call(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.store.add_spend(AGENT, now().date(), Decimal("0.999"))
    run = handled(rt, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits.daily_budget")
    assert rt.llm.calls == []


def test_e5_the_in_memory_budget_refuses_before_the_call_too():
    client, budget = Client(), Budget(Decimal("0.001"))
    bound = ModelGate(client, meter=budget, audit=None, worst_case=wc).bind("a", "r")
    with pytest.raises(SpendRefused) as stopped:
        bound.chat([{"role": "user", "content": "x"}], system="s", route="default")
    assert stopped.value.reason == "usd_cap" and client.calls == 0 and budget.spent == 0


def test_e6_a_late_settle_after_forfeit_raises_the_booked_amount_only_above_the_worst_case():
    budget = Budget(Decimal("1.00"))
    held = budget.reserve("a", Decimal("0.30"), run_id="case-1")
    budget.forfeit("case-1")
    assert budget.spent == Decimal("0.30")
    budget.settle(held, Decimal("0.10"))
    assert budget.spent == Decimal("0.30"), "a late settle lowered a forfeited hold"
    other = budget.reserve("a", Decimal("0.30"), run_id="case-2")
    budget.forfeit("case-2")
    over = budget.settle(other, Decimal("0.50"))
    assert (budget.spent, over) == (Decimal("0.80"), Decimal("0.20")), (
        "a higher late settle was lost"
    )


def test_e6_forfeit_closes_its_run_id_and_no_other():
    budget = Budget(Decimal("1.00"))
    budget.reserve("a", Decimal("0.10"), run_id="case-1")
    budget.forfeit("case-1")
    with pytest.raises(SpendRefused) as closed:
        budget.reserve("a", Decimal("0.01"), run_id="case-1")
    assert closed.value.reason == "usd_cap", "a reserve after forfeit was not refused"
    budget.reserve("a", Decimal("0.01"), run_id="case-2")
    budget.reserve("a", Decimal("0.01"))  # run_id None is allowed (evals)


def test_e6_forfeit_keeps_the_worst_case_of_an_open_hold_but_not_of_a_settled_one():
    budget = Budget(Decimal("1.00"))
    open_hold = budget.reserve("a", Decimal("0.40"), run_id="c")
    done = budget.reserve("a", Decimal("0.40"), run_id="c")
    budget.settle(done, Decimal("0.05"))
    budget.forfeit("c")
    assert budget.spent == Decimal("0.45"), "forfeit changed a settled call or dropped an open hold"
    assert budget.settle(open_hold, Decimal("0.40")) == 0


def test_e7_evals_in_pilot_without_max_usd_is_a_config_error(cfg_dir):
    reg = load_registry(load_config(cfg_dir))
    for target in ("pilot", "prod"):
        live = dataclasses.replace(
            reg, config=reg.config.model_copy(update={"environment": target})
        )
        client = Client()
        with pytest.raises(ConfigError, match="max-usd"):
            evals.gate(live, client, AGENT)
        assert client.calls == 0


@pytest.mark.parametrize(
    "bad", [Decimal(0), Decimal(-1), Decimal("NaN"), Decimal("Infinity"), 1.5, 1, "1"]
)
def test_e7_a_cap_that_is_not_a_finite_decimal_above_zero_is_a_config_error(cfg_dir, bad):
    reg = load_registry(load_config(cfg_dir))
    with pytest.raises(ConfigError):
        evals.gate(reg, Client(), AGENT, max_usd=bad)


def test_e7_demo_without_max_usd_caps_at_the_agents_daily_budget(cfg_dir):
    reg = load_registry(load_config(cfg_dir))
    seen = []

    class Meter(Budget):
        def reserve(self, agent_id, worst_usd, *, run_id=None):
            seen.append(self.limit)
            return super().reserve(agent_id, worst_usd, run_id=run_id)

    client = Client()
    gate = ModelGate(client, meter=Meter(Decimal("0.5")), audit=None, worst_case=wc)
    evals.gate(reg, gate, AGENT)  # a gate is used as it is: its own meter and cap
    assert seen and set(seen) == {Decimal("0.5")}
    with pytest.raises(ConfigError):
        evals.gate(reg, gate.bind("a", "r"), AGENT)  # a bound gate is refused


def test_e8_twenty_threads_on_one_budget_never_pass_the_limit(monkeypatch):
    real_new_id = importlib.import_module("hadavin_sdk.limits").new_id

    def slow_new_id(prefix):  # widens the window between the check and the booking
        time.sleep(0.002)
        return real_new_id(prefix)

    monkeypatch.setattr("hadavin_sdk.limits.new_id", slow_new_id)
    budget = Budget(Decimal("1.00"))
    start, won, lost = threading.Barrier(20), [], []

    def worker():
        start.wait()
        try:
            won.append(budget.reserve("a", Decimal("0.10")))
        except SpendRefused as exc:
            lost.append(exc.reason)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert budget.spent <= Decimal("1.00"), "the budget was passed"
    assert len(won) == 10 and lost == ["usd_cap"] * 10


def test_e8_holds_count_toward_the_limit():
    budget = Budget(Decimal("1.00"))
    budget.reserve("a", Decimal("0.60"))
    with pytest.raises(SpendRefused) as full:
        budget.reserve("a", Decimal("0.60"))
    assert full.value.reason == "usd_cap", "a hold was not counted in spent"
    assert budget.spent == Decimal("0.60") and not budget.exhausted


def test_an_unknown_route_name_is_priced_at_the_largest_worst_case():
    small = Route(
        model_id="s",
        input_usd_per_mtok=Decimal(1),
        output_usd_per_mtok=Decimal(2),
        max_tokens=100,
    )
    routes = {"small": small, "big": ROUTE}
    price = worst_case_for(routes, Client())
    args = ("sys", [{"role": "user", "content": "hi"}], None, None, None)
    unknown = None
    try:
        unknown = price("nope", *args)
    except SpendRefused:
        pass
    if unknown is None:
        raise AssertionError(
            "an unknown route name was refused, not priced at the largest worst case"
        )
    assert unknown == price("big", *args) > price("small", *args)
    assert price(None, *args) == unknown  # not even a string


@pytest.mark.parametrize("target", ["demo", "pilot", "prod"])
def test_a_config_cannot_hold_an_unknown_detector_route_name(tmp_path, target):
    from tests.k5_support import edit_config
    from tests.test_p6_detectors import _with_judge

    cfg = make_cfg(tmp_path)
    edit_config(cfg, lambda d: _with_judge(d, route="nope"))
    edit_config(cfg, lambda d: d.update(environment=target))
    with pytest.raises(ConfigError, match="unknown route 'nope'"):
        load_registry(load_config(cfg))


def test_a_registry_cannot_hold_an_agent_on_an_unknown_route(tmp_path):
    from tests.k5_support import edit_config

    cfg = make_cfg(tmp_path)
    edit_config(cfg, lambda a: a[0].update(model_route="nope"), name="agents.yaml")
    with pytest.raises(ConfigError, match="unknown model_route nope"):
        load_registry(load_config(cfg))


# ------------------------------------------------------------------------------------------------ H: hostile


def bound_gate(client, *, budget=None, sink=None, mapping=None, worst_case=wc):
    budget = budget or Budget(Decimal(5))
    return ModelGate(client, meter=budget, audit=sink, worst_case=worst_case).bind(
        AGENT, "run-x", mapping=mapping
    ), budget


MSG = [{"role": "user", "content": "go"}]


def test_h1_an_unmarked_error_leaves_the_hold_booked_and_no_settle(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=ProviderError("boom"))
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "provider_error")
    assert spy.settles == [], "an unmarked provider error was settled"
    assert day_spend(rt, run) == spy.reserved[0][2] > 0, "the hold is not booked at its worst case"
    assert rt.store.get_run(run.run_id).cost_usd == 0
    assert [e.error_code for e in llm_rows(rt, run)] == ["provider_error"]
    assert rt.store.expire_spend_reservations(0) == 1  # the tick step closes it, at the worst case
    assert day_spend(rt, run) == spy.reserved[0][2]


def test_h1_with_the_refused_before_response_mark_the_hold_settles_at_zero(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    error = ProviderError("refused")
    error.refused_before_response = True
    rt.llm = Client(raises=error)
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "provider_error")
    assert [usd for _, usd, _ in spy.settles] == [Decimal(0)]
    assert day_spend(rt, run) == 0
    assert [e.error_code for e in llm_rows(rt, run)] == ["provider_refused"]


def test_h1_a_fault_that_is_not_a_provider_error_ends_the_run_and_keeps_the_hold(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=ValueError("bug in the client"))
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "model_error")
    assert spy.settles == [] and len(spy.reserved) == 1
    assert rt.store.spend_totals(AGENT, now().date())[0] == spy.reserved[0][2]


def test_h2_a_document_holding_a_known_value_reaches_the_client_with_its_placeholder():
    client = Client()
    bound, _ = bound_gate(client, mapping={"<TENANT_1>": "Zebra Holdings"})
    bound.chat(
        [{"role": "user", "content": "ledger of Zebra Holdings"}],
        system="s",
        route="default",
        documents=[b"invoice for Zebra Holdings and Walrus Industries"],
    )
    (sent,) = client.sent
    text = sent["documents"][0].decode()
    assert "<TENANT_1>" in text and "Zebra Holdings" not in text, "a known value reached the client"
    assert "Walrus Industries" in text, "a value in no map is passed as written (stated limit)"
    assert sent["messages"][0]["content"] == "ledger of <TENANT_1>"


def test_h2_the_callers_messages_and_documents_are_not_changed_in_place():
    client = Client()
    bound, _ = bound_gate(client, mapping={"<TENANT_1>": "Zebra Holdings"})
    messages, docs = [{"role": "user", "content": "Zebra Holdings"}], [b"Zebra Holdings"]
    bound.chat(messages, system="s", route="default", documents=docs)
    assert messages == [{"role": "user", "content": "Zebra Holdings"}] and docs == [
        b"Zebra Holdings"
    ]


def test_h2_a_map_that_cannot_be_enforced_ends_the_run_redaction_error(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    client = Client()

    def broken(text, mapping):
        raise ValueError("bad map")

    rt.llm = ModelGate(client, meter=rt.limits, audit=None, worst_case=wc, enforce=broken)
    run = handled(rt, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "redaction_error")
    assert client.calls == 0 and rt.store.spend_totals(AGENT, now().date())[0] == 0


def test_h3_an_audit_sink_that_raises_does_not_fail_the_call():
    client = Client()
    bound, budget = bound_gate(client, sink=Sink(raises=RuntimeError("sink down")))
    reply = bound.chat(MSG, system="s", route="default")
    assert reply.cost_usd == Decimal("0.004") and client.calls == 1
    assert budget.spent == Decimal("0.004")


def test_h4_a_judge_steered_off_schema_is_charged_once(cfg_dir):
    steered = Client(reply=Reply(text="not json", cost_usd=JUDGE_COST, model_id="m"))
    rt, cfg = build_rt(cfg_dir)
    rt.detector = judge_only(steered)
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "guard_unavailable")
    assert [usd for _, usd, _ in spy.settles] == [JUDGE_COST], "charged zero or two times"
    assert rt.store.get_run(run.run_id).cost_usd == JUDGE_COST == day_spend(rt, run)


@pytest.mark.parametrize("cost", [Decimal("-0.5"), Decimal("NaN"), Decimal("Infinity")])
def test_h5_a_reply_with_an_unusable_cost_is_returned_and_not_settled(cost):
    sink = Sink()
    reply = SimpleNamespace(text="ok", cost_usd=cost)  # a double the pydantic model would not build
    bound, budget = bound_gate(Client(reply=reply), sink=sink)
    assert bound.chat(MSG, system="s", route="default") is reply
    assert budget.spent == Decimal("0.03"), "the hold was replaced by an unusable cost"
    assert [(r.result, r.error_code) for r in sink.rows] == [("ok", "cost_unknown")]


def test_h6_reserve_raising_store_unavailable_ends_needs_person_never_working(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)

    def down(*args, **kw):
        raise StoreUnavailable("store down")

    monkeypatch.setattr(rt.store, "reserve_spend", down)
    run = handled(rt, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits_unavailable")
    assert rt.llm.calls == [] and rt.store.get_run(run.run_id).state != S.WORKING


# ------------------------------------------------------------------------------------------------ refusal paths (W1)

EXPECT = {
    "kill_switch": (S.STOPPED, "kill_switch"),
    "daily_budget": (S.NEEDS_PERSON, "limits.daily_budget"),
    "monthly_budget": (S.NEEDS_PERSON, "limits.monthly_budget"),
    "limits_unavailable": (S.NEEDS_PERSON, "limits_unavailable"),
    "bad_amount": (S.NEEDS_PERSON, "limits_unavailable"),
    "usd_cap": (S.NEEDS_PERSON, "limits_unavailable"),
    "a_reason_nobody_published": (S.NEEDS_PERSON, "limits_unavailable"),
}
SITES = ["document", "chat", "tool", "shadow"]


def run_refused(site, reason, tmp_path):
    """One run in which the meter refuses the first reserve of ``site``. Returns (run, cards, runtime)."""
    refuse = lambda: SpendRefused(reason)
    if site in ("document", "chat"):
        rt, cfg = build_rt(make_cfg(tmp_path))
        if site == "document":
            rt.detector = judge_only()
        rt.limits = Refuser(rt.limits, refuse)
        return handled(rt, _doc(cfg, "create.txt"), what=site), [], rt
    if site == "tool":
        k5_tools.RESULTS["app"] = "all quiet"
        rt, cards = build_runtime(
            k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}])
        )
        rt.detector = judge_only()
        rt.limits = Refuser(rt.limits, refuse, after=2)  # the document screen and the chat pass
        return stranded_check(lambda: k5_handle(rt), "the tool-result screen"), cards, rt
    hooks, cards = captured()
    rt = k3_runtime(
        demo_cfg(tmp_path, {"restart_service": "shadow"}), K3Scripted(k3_reply(PROPOSE)), hooks
    )
    rt.detector = judge_only()
    rt.limits = Refuser(rt.limits, refuse, after=2)  # the document screen and the chat pass
    return stranded_check(lambda: k3_handle(rt), "the shadow card"), cards, rt


@pytest.mark.parametrize("reason", sorted(EXPECT))
@pytest.mark.parametrize("site", SITES)
def test_a_meter_refusal_ends_the_run_by_the_mapping_at_every_site(site, reason, tmp_path):
    run, cards, rt = run_refused(site, reason, tmp_path)
    assert (run.state, run.reason_code) == EXPECT[reason], f"{site}/{reason}: wrong ending"
    assert rt.store.get_run(run.run_id).state == run.state != S.WORKING
    if site == "shadow":
        assert cards == [], "a refusal in the shadow judge produced a card"
        assert run.reason_code != "shadow_undelivered"


def test_a_meter_refusal_inside_a_judge_call_prints_no_injection_warning(tmp_path):
    run, cards, rt = run_refused("shadow", "daily_budget", tmp_path)
    assert cards == [] and run.reason_code == "limits.daily_budget"
    assert not [e for e in rt.audit.events(run.run_id) if e.operation == "injection"]


@pytest.mark.parametrize("site", ["document", "tool", "shadow"])
def test_a_bound_gate_as_the_judge_client_ends_the_run_gate_error(site, tmp_path):
    bound = ModelGate(JudgeModel(), meter=Budget(Decimal(5)), audit=None, worst_case=wc).bind(
        "a", "r"
    )
    if site == "document":
        rt, cfg = build_rt(make_cfg(tmp_path))
        rt.detector = judge_only(bound)
        run = handled(rt, _doc(cfg, "create.txt"))
    elif site == "tool":
        k5_tools.RESULTS["app"] = "all quiet"
        rt, _ = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}]))
        rt.detector = judge_only(bound)
        run = k5_handle(rt)
    else:
        hooks, cards = captured()
        rt = k3_runtime(
            demo_cfg(tmp_path, {"restart_service": "shadow"}), K3Scripted(k3_reply(PROPOSE)), hooks
        )
        rt.detector = judge_only(bound)
        run = k3_handle(rt)
        assert cards == []
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "gate_error")


def test_a_gate_refusal_other_than_the_map_ends_the_run_with_its_code(cfg_dir):
    class Odd(GateRefused):
        code = "odd_code"

    def refuses(*_args):
        raise Odd

    rt, cfg = build_rt(cfg_dir)
    client = Client()
    rt.llm = ModelGate(client, meter=rt.limits, audit=None, worst_case=refuses)
    run = handled(rt, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "odd_code") and client.calls == 0


def test_an_unmasked_input_refusal_is_a_redaction_failure_not_a_limit():
    assert issubclass(UnmaskedInput, GateRefused) and UnmaskedInput.code == "mask_refused"


def test_injection_check_raises_a_refusal_and_flags_any_other_error():
    class Raises:
        backend = "x"

        def __init__(self, exc):
            self.exc = exc

        def check(self, text, source):
            raise self.exc

    for exc in (SpendRefused("daily_budget"), UnmaskedInput()):
        with pytest.raises(type(exc)):
            injection_check(Raises(exc), "t", "document")
    verdict = injection_check(Raises(RuntimeError("down")), "t", "document")
    assert (verdict.flagged, verdict.reason_code) == (True, "guard_unavailable")


@pytest.mark.parametrize(
    "reason",
    [
        "kill_switch",
        "daily_budget",
        "monthly_budget",
        "limits_unavailable",
        "bad_amount",
        "usd_cap",
    ],
)
def test_the_gate_audits_each_of_the_six_published_reasons_as_the_error_code(reason):
    """ii-meter point 1: SpendRefused.reason is the audit error code; the allowlist holds all six reasons."""
    sink, client = Sink(), Client()
    meter = Refuser(Budget(Decimal(1)), lambda: SpendRefused(reason))
    bound, _ = bound_gate(client, budget=meter, sink=sink)
    with pytest.raises(SpendRefused):
        bound.chat(MSG, system="s", route="default")
    assert [(r.result, r.error_code) for r in sink.rows] == [("refused", reason)]
    assert client.calls == 0


def test_the_gate_audits_an_exception_without_a_published_reason_as_reserve_refused():
    sink = Sink()
    meter = Refuser(Budget(Decimal(1)), lambda: KeyError("unknown agent"))
    bound, _ = bound_gate(Client(), budget=meter, sink=sink)
    with pytest.raises(KeyError):
        bound.chat(MSG, system="s", route="default")
    assert [(r.result, r.error_code) for r in sink.rows] == [("refused", "reserve_refused")]


# -- replay and evals sites


def _bundle(tmp_path):
    return make_bundle(tmp_path / "b", "case-001")


def run_case(tmp_path, *, gate_meter, wrap_meter, replies, detector=None):
    from hadavin_sdk.k1b.bundle import load_bundle

    bundle = load_bundle(_bundle(tmp_path))
    client = ScriptedLLM(replies)
    budget = Budget(Decimal(10))

    def wrap(raw):
        return (
            raw
            if isinstance(raw, ModelGate)
            else ModelGate(raw, meter=wrap_meter or budget, audit=None, worst_case=wc)
        )

    gate = ModelGate(client, meter=gate_meter or budget, audit=None, worst_case=wc)
    out = loop.run_case(
        gate,
        wrap=wrap,
        agent_id=AGENT,
        run_id="k1b-x:run1",
        system="s",
        route="default",
        bundle=bundle,
        detector=detector or RegexDetector(0.5),
        budget=budget,
        max_steps=4,
        max_tool_calls=4,
        timeout_s=30,
    )
    return out, client, budget


@pytest.mark.parametrize(
    ("make", "status", "stop_reason", "halt"),
    [
        (lambda: SpendRefused("usd_cap"), "capped", "usd_cap", "capped"),
        (lambda: SpendRefused("kill_switch"), "error", "kill_switch", "aborted"),
        (lambda: SpendRefused("bad_amount"), "error", "bad_amount", "aborted"),
        (lambda: UnmaskedInput(), "error", "mask_refused", "aborted"),
        (lambda: GateRefused(), "error", "gate_refused", "aborted"),
    ],
)
def test_replay_a_refused_chat_ends_the_case_without_raising(
    make, status, stop_reason, halt, tmp_path
):
    out, client, _ = run_case(
        tmp_path,
        gate_meter=Refuser(Budget(Decimal(1)), make),
        wrap_meter=None,
        replies=[submit_not_sure()],
    )
    assert (out.status, out.stop_reason, out.halt) == (status, stop_reason, halt)
    assert client.calls == []


def test_replay_a_refused_detector_call_on_a_tool_result_ends_the_case_by_the_same_mapping(
    tmp_path,
):
    for make, expect in (
        (lambda: SpendRefused("usd_cap"), ("capped", "usd_cap", "capped")),
        (lambda: SpendRefused("kill_switch"), ("error", "kill_switch", "aborted")),
    ):
        judge_llm = ScriptedLLM([])
        out, client, _ = run_case(
            tmp_path / expect[1],
            gate_meter=None,
            wrap_meter=Refuser(Budget(Decimal(1)), make),
            replies=[tool_reply("list_data"), submit_not_sure()],
            detector=JudgeDetector(judge_llm, "default", 0.5),
        )
        assert (out.status, out.stop_reason, out.halt) == expect
        assert len(client.calls) == 1 and judge_llm.calls == []


def test_replay_the_budget_is_forfeited_per_case_whatever_the_ending(tmp_path):
    out, _client, budget = run_case(
        tmp_path,
        gate_meter=None,
        wrap_meter=None,
        replies=[tool_reply("list_data", cost="0.01"), submit_not_sure(cost="0.01")],
    )
    assert out.status == "ok"
    with pytest.raises(SpendRefused) as closed:  # the case run id is closed after the case
        budget.reserve(AGENT, Decimal("0.01"), run_id="k1b-x:run1:case-001")
    assert closed.value.reason == "usd_cap"


def test_replay_the_acknowledge_flag_is_refused_in_pilot_and_prod(tmp_path, cfg_dir):
    from hadavin_sdk.k1b.replay import replay

    env = Env(tmp_path, cfg_dir)
    for target in ("pilot", "prod"):
        live = dataclasses.replace(
            env.reg, config=env.reg.config.model_copy(update={"environment": target})
        )
        with pytest.raises(ConfigError):
            replay(
                live, ScriptedLLM([]), RegexDetector(0.5), env.audit, agent_id=AGENT,
                bundles_dir=env.bundles, cause_list_dir=env.cause, k=1, max_usd=Decimal(1),
                out=tmp_path / f"out-{target}", acknowledge_masked=True,
            )  # fmt: skip


def test_replay_a_bound_gate_is_refused(env):
    bound = ModelGate(ScriptedLLM([]), meter=Budget(Decimal(1)), audit=None, worst_case=wc).bind(
        "a", "r"
    )
    with pytest.raises(ConfigError):
        env.run(bound)


def test_replay_a_cap_below_one_worst_case_makes_no_call_and_caps_every_case(env):
    llm = ScriptedLLM([submit_not_sure(), submit_not_sure()])
    res = env.run(llm, max_usd="0.01")
    assert (res.exit_code, res.result) == (1, "capped") and llm.calls == []
    assert env.case()["status"] == "capped" and env.case("case-002")["status"] == "capped"


# ------------------------------------------------------------------------------------------------ the worst case

ONE_BYTE_PER_USD = SimpleNamespace(
    input_usd_per_mtok=Decimal(1_000_000), output_usd_per_mtok=Decimal(0), max_tokens=0
)
OVERHEAD = defaults.WORST_CASE_OVERHEAD_BYTES


def size_of(system="", messages=None, **kw) -> int:
    """The input bytes worst_case_usd counts, read back through a route that prices one byte at one dollar."""
    return (
        int(worst_case_usd(ONE_BYTE_PER_USD, system, [] if messages is None else messages, **kw))
        - OVERHEAD
    )


def test_the_overhead_constant_is_4096():
    assert OVERHEAD == 4096


def test_worst_case_on_the_documented_numbers():
    only_output = SimpleNamespace(
        input_usd_per_mtok=Decimal(0), output_usd_per_mtok=Decimal("15.00"), max_tokens=1024
    )
    assert worst_case_usd(only_output, "", []) == Decimal("0.01536")
    # the ticket's "1000-byte prompt": 998 bytes of system and the 2 bytes of the empty message list "[]"
    assert (
        worst_case_usd(ROUTE, "a" * 998, [])
        == Decimal("0.01536") + Decimal(1000 + OVERHEAD) * 3 / ONE_MILLION
    )
    assert worst_case_usd(ROUTE, "a" * 998, []) == Decimal("0.030648")


def test_worst_case_counts_system_messages_tools_documents_and_schema_twice():
    base = size_of()
    assert base == len(b"[]")
    assert size_of("x" * 10) == base + 10
    assert size_of(documents=[b"a" * 7, b"b" * 5]) == base + 12
    messages = [{"role": "user", "content": "é"}]
    assert size_of(messages=messages) == len(
        json.dumps(messages, sort_keys=True, ensure_ascii=False).encode()
    )
    tools = [{"name": "t", "input_schema": {"type": "object"}}]
    assert size_of(tools=tools) == base + len(
        json.dumps(tools, sort_keys=True, ensure_ascii=False).encode()
    )
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    schema_bytes = len(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode())
    assert size_of(output_schema=schema) == base + 2 * schema_bytes, "the schema is counted twice"


def test_worst_case_none_inputs_count_zero_bytes_and_an_empty_list_counts_its_brackets():
    base = size_of()
    assert size_of(tools=None, documents=None, output_schema=None) == base
    assert size_of(tools=[]) == base + 2
    assert size_of(documents=[]) == base
    assert size_of(output_schema={}) == base + 4


def test_worst_case_json_sizing_is_utf8_with_surrogatepass_and_default_str():
    assert size_of("é") == len(b"[]") + 2
    assert (
        size_of("\ud800") == len(b"[]") + 3
    )  # a lone surrogate sizes as three bytes, never an error
    odd = [{"role": "user", "content": Decimal("1.5")}]
    assert size_of(messages=odd) == len(
        json.dumps(odd, sort_keys=True, ensure_ascii=False, default=str).encode()
    )


def test_worst_case_is_rounded_up_to_twelve_places():
    tiny = SimpleNamespace(
        input_usd_per_mtok=Decimal("0.0000001"), output_usd_per_mtok=Decimal(0), max_tokens=1
    )
    exact = Decimal(2 + OVERHEAD) * Decimal("0.0000001") / ONE_MILLION
    got = worst_case_usd(tiny, "", [])
    assert got > exact and got == exact.quantize(Decimal("1E-12"), rounding="ROUND_CEILING")
    assert got.as_tuple().exponent == -12


@pytest.mark.parametrize(
    ("attempts", "schema", "factor"),
    [(3, None, 3), (3, {"type": "object"}, 6), (1, {"type": "object"}, 2), (None, None, 1)],
)
def test_worst_case_for_multiplies_by_the_requests(attempts, schema, factor):
    llm = SimpleNamespace() if attempts is None else SimpleNamespace(max_attempts=attempts)
    price = worst_case_for({"default": ROUTE}, llm)
    one = worst_case_usd(ROUTE, "s", MSG, output_schema=schema)
    assert price("default", "s", MSG, None, None, schema) == (one * factor).quantize(
        Decimal("1E-12")
    )


@pytest.mark.parametrize("attempts", [0, -2, True, 2.0, "3", None])
def test_worst_case_for_reads_max_attempts_only_when_it_is_a_whole_number_of_at_least_one(attempts):
    price = worst_case_for({"default": ROUTE}, SimpleNamespace(max_attempts=attempts))
    assert price("default", "s", MSG, None, None, None) == worst_case_usd(ROUTE, "s", MSG)


def test_worst_case_for_refuses_to_guess_when_sizing_fails():
    price = worst_case_for({"default": ROUTE}, Client())
    circular: list = []
    circular.append(circular)
    for system, messages in (("s", circular), (None, MSG)):
        with pytest.raises(SpendRefused) as refused:
            price("default", system, messages, None, None, None)
        assert refused.value.reason == "bad_amount"


def test_worst_case_for_needs_a_route_and_gives_a_six_argument_callable():
    with pytest.raises(ValueError):
        worst_case_for({}, Client())
    seen = []

    def spying(*args):
        seen.append(args)
        return Decimal("0.01")

    bound, _ = bound_gate(Client(), worst_case=spying)
    bound.chat(
        MSG,
        system="sys",
        route="default",
        tools=[{"name": "t"}],
        documents=[b"d"],
        output_schema={"x": 1},
    )
    assert seen == [("default", "sys", MSG, [{"name": "t"}], [b"d"], {"x": 1})]


def test_the_gate_reserves_the_worst_case_the_closure_computes(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.limits = spy = Spy(rt.limits)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert run.run_id == spy.reserved[0][3]
    assert spy.reserved[0][2] > RUN_COST, "the hold is not above the real cost"


# ------------------------------------------------------------------------------------------------ the deletions


def test_the_extract_module_is_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hadavin_sdk.extract")
    assert not (SRC / "extract.py").exists()


def test_no_recorded_file_or_fixture_of_the_extract_module_is_left():
    inputs, recorded = ROOT / "tests/fixtures/inputs", ROOT / "tests/fixtures/recorded"
    assert not (inputs / "extract.txt").exists() and not (inputs / "bad.txt").exists()
    assert not (ROOT / "tests/fixtures/schemas.py").exists()
    # the three answers recorded for extract.txt and bad.txt (named by the sha256 of those documents)
    gone = (
        "8b917fb84387987afbbdbebc5d0e8e4b524bef7933db4d3fb73f42afc171098c",
        "ad62d4017c2e97741cf27311c05e7f39019648206e303b5449a0ad76e747bf05",
    )
    left = [p.name for p in recorded.glob("*.json") if p.name.split("-")[0] in gone]
    assert left == [], f"recorded answers of the extract module are still there: {left}"
    record = (ROOT / "tests/fixtures/record.py").read_text(encoding="utf-8")
    assert "extract" not in record and "bad.txt" not in record


def _calls_named(name):
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            ):
                hits.append(f"{path.relative_to(SRC)}:{node.lineno}")
    return hits


def test_no_call_to_charge_remains_in_src_and_the_methods_are_gone():
    assert _calls_named("charge") == []
    assert not hasattr(Limits, "charge") and not hasattr(Budget, "charge")


def test_nothing_in_src_outside_the_stores_adds_run_cost_by_hand():
    outside = [h for h in _calls_named("add_cost") if not h.startswith("store/")]
    assert outside == [], f"a caller adds cost beside the meter: {outside}"


def test_every_chat_call_in_src_outside_llm_and_the_gate_is_on_a_bound_client():
    """Invariant 1, by name: the files that call ``.chat(`` are exactly the ones the install covers."""
    allowed = {
        "evals.py",  # the bound client of evals.gate
        "guard/judge.py",  # the judge's own client, bound by its caller
        "k1b/loop.py",  # the case's bound client
        "runtime/agent_loop.py",  # the run's bound client
        "guard/bedrock_guardrail.py",  # not a model client (ApplyGuardrail); stated unmetered
        "guard/model_gate.py",  # the gate itself
    }
    found = {
        h.split(":")[0]
        for h in _calls_named("chat")
        if not h.startswith("llm/") and not h.startswith("demo")
    }
    assert found <= allowed | {"approvals/cards.py"}, (
        f"a new model call site: {sorted(found - allowed)}"
    )

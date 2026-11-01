"""Independent security review of PR #48 (M1-M3, m1-m12): the agent loop reserves and settles; the fallback never
moves documents or spend-capped traffic silently; model JSON is bounded before it is parsed; deadlines and
retry-after are real; the breaker ignores stale outcomes; alternating roles on every kind."""

from __future__ import annotations

import copy
import io
import itertools
import json
import pickle
import threading
import time
import urllib.error
from decimal import Decimal
from email.message import Message
from types import SimpleNamespace
from typing import Any

import pytest
import yaml
from pydantic import BaseModel

from hadavin_sdk.config import Route
from hadavin_sdk.extract import extract
from hadavin_sdk.guard.judge import _answer
from hadavin_sdk.llm import gemini, openai_compat
from hadavin_sdk.llm.anthropic import AnthropicLLM
from hadavin_sdk.llm.anthropic import spend_limit as anthropic_spend_limit
from hadavin_sdk.llm.bedrock import BedrockLLM
from hadavin_sdk.llm.common import json_in_text, loads_bounded, turns
from hadavin_sdk.llm.protocol import (
    DeadlineExceeded,
    ProviderError,
    ProviderExhausted,
    SpendLimitReached,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.models import DeadLetter, KillSwitch, Reply, RunState, ToolCall
from tests.test_s5_runtime import S, _doc, build

D = Decimal


# --- M1: the agent loop reserves and settles --------------------------------------------------------------------


def _set_agent(cfg_dir, **fields):
    path = cfg_dir / "agents.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data[0].update(fields)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


class Canned:
    """Answers the same text every time (the recorded fake serves each input once, so it cannot take 12 runs)."""

    def chat(self, *a, **k):
        return Reply(
            text="no action", model_id="m", cost_usd=D("0.001"), input_tokens=5, output_tokens=5
        )


class Slow:
    """Wraps a model: every call takes a while, so concurrent runs overlap."""

    def __init__(self, inner, delay=0.5):
        self.inner, self.delay, self.calls = inner, delay, 0
        self._lock = threading.Lock()

    def chat(self, *a, **k):
        with self._lock:
            self.calls += 1
        time.sleep(self.delay)
        return self.inner.chat(*a, **k)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def _probe_worst_case(cfg_dir):
    rt, cfg = build(cfg_dir)
    seen = []
    real = rt.limits.reserve
    rt.limits.reserve = lambda a, usd, *r, **k: (seen.append(usd), real(a, usd, *r, **k))[1]
    rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    return seen[0]


def test_concurrent_real_runs_cannot_overshoot_the_daily_cap(cfg_dir):
    worst = _probe_worst_case(cfg_dir)
    _set_agent(cfg_dir, budget_usd={"daily": str(worst * D("3.5")), "monthly": "1000"})
    rt, cfg = build(cfg_dir)
    rt.llm = Slow(Canned())
    doc = _doc(cfg, "chat.txt")
    gate, runs = threading.Barrier(12), []

    def one():
        gate.wait()
        runs.append(rt.handle("test-agent", "svc:test-agent", doc))

    ts = [threading.Thread(target=one) for _ in range(12)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert (
        len(runs) == 12 and rt.llm.calls == 3
    )  # every run ended; room for exactly three worst cases
    assert len([r for r in runs if r.state == S.NEEDS_PERSON]) == 9
    day = rt.store.spend_totals("test-agent", runs[0].created_at.date())[0]
    assert day <= worst * D("3.5")


def test_max_run_usd_binds_in_a_real_run(cfg_dir):
    _set_agent(cfg_dir, max_run_usd="0.0000001")
    rt, cfg = build(cfg_dir)
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "run_budget")
    assert rt.llm.calls == []


def test_max_run_usd_allows_a_run_that_fits(cfg_dir):
    _set_agent(cfg_dir, max_run_usd="10")
    rt, cfg = build(cfg_dir)
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.state == S.NO_ACTION
    day = rt.store.spend_totals("test-agent", run.created_at.date())[0]
    assert day == rt.store.get_run(run.run_id).cost_usd > 0  # settled to the real cost


class _Raises:
    def __init__(self, exc):
        self.exc, self.calls = exc, []

    def chat(self, *a, **k):
        self.calls.append(1)
        raise self.exc


def test_a_provider_spend_limit_ends_the_run_over_budget_and_releases_the_reservation(cfg_dir):
    rt, cfg = build(cfg_dir)
    rt.llm = _Raises(SpendLimitReached("cap"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "over_budget")
    assert rt.store.spend_totals("test-agent", run.created_at.date()) == (0, 0)


def test_a_provider_error_releases_the_reservation(cfg_dir):
    rt, cfg = build(cfg_dir)
    rt.llm = _Raises(ProviderError("bad key"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_error"
    assert rt.store.spend_totals("test-agent", run.created_at.date()) == (0, 0)


def test_a_deadline_keeps_the_worst_case_booked_because_the_cost_is_unknown(cfg_dir):
    rt, cfg = build(cfg_dir)
    rt.llm = _Raises(DeadlineExceeded("late"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_exhausted"
    assert rt.store.spend_totals("test-agent", run.created_at.date())[0] > 0


def test_a_settle_failure_never_strands_the_run_and_leaves_the_worst_case_booked(cfg_dir):
    rt, cfg = build(cfg_dir)

    def boom(deltas):
        raise OSError("store down")

    rt.store.settle_spend = boom
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.state == S.NO_ACTION
    assert rt.store.spend_totals("test-agent", run.created_at.date())[0] > 0


def test_the_kill_switch_stops_a_real_run_through_the_reservation(cfg_dir):
    rt, cfg = build(cfg_dir)
    real = rt.limits.blocked
    rt.limits.blocked = lambda a: []  # the early read says "off": only the atomic step can stop it
    rt.store.set_kill_switch(KillSwitch(on=True, by="t"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    rt.limits.blocked = real
    assert (run.state, run.reason_code) == (RunState.STOPPED, "kill_switch")
    assert rt.llm.calls == []


def test_a_store_that_cannot_answer_fails_closed(cfg_dir):
    rt, cfg = build(cfg_dir)

    def down(*a, **k):
        raise OSError("down")

    rt.store.reserve_spend = down
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits.unavailable")
    assert rt.llm.calls == []


# --- M2: the fallback ---------------------------------------------------------------------------------------------


class Stub:
    label = "stub"

    def __init__(self, *outcomes):
        self.outcomes, self.n, self.seen = list(outcomes), 0, []

    def chat(self, messages, **kw):
        self.n += 1
        self.seen.append(kw)
        o = self.outcomes[min(self.n, len(self.outcomes)) - 1]
        if isinstance(o, BaseException):
            raise o
        return o


OK = Reply(text="ok", model_id="m")
DOWN = ProviderExhausted("down")


def test_documents_are_not_sent_to_the_fallback_by_default_and_the_call_fails_closed():
    backup = Stub(OK)
    llm = ResilientLLM(Stub(DOWN), backup)
    with pytest.raises(ProviderExhausted):
        llm.chat([], system="", route="r", documents=[b"client data"])
    assert backup.n == 0


def test_a_call_without_documents_may_use_the_fallback_and_is_marked_and_reported():
    events = []
    backup = Stub(OK)
    llm = ResilientLLM(Stub(DOWN), backup, on_fallback=events.append)
    out = llm.chat([], system="s", route="r")
    assert out.fallback_used and out.served_by == "stub" and backup.n == 1
    assert events == [
        {
            "event": "llm_fallback",
            "why": "ProviderExhausted",
            "route": "r",
            "served_by": "stub",
            "documents_sent": False,
        }
    ]


def test_documents_go_to_the_fallback_only_on_explicit_opt_in_and_the_event_says_so():
    events = []
    backup = Stub(OK)
    llm = ResilientLLM(
        Stub(DOWN), backup, send_documents_to_fallback=True, on_fallback=events.append
    )
    out = llm.chat([], system="", route="r", documents=[b"CLIENT-DOC-BYTES"])
    assert out.fallback_used and events[0]["documents_sent"] is True
    assert "CLIENT-DOC-BYTES" not in json.dumps(events)


def test_a_failing_audit_hook_stops_the_fallback_call():
    def refuse(_event):
        raise RuntimeError("audit down")

    backup = Stub(OK)
    llm = ResilientLLM(Stub(DOWN), backup, on_fallback=refuse)
    with pytest.raises(RuntimeError):
        llm.chat([], system="", route="r")
    assert backup.n == 0  # nothing leaves unrecorded


def test_a_spend_limit_on_the_primary_does_not_move_traffic_to_an_unmetered_vendor():
    backup = Stub(OK)
    llm = ResilientLLM(Stub(SpendLimitReached("cap")), backup, CircuitBreaker(1, 30.0))
    with pytest.raises(SpendLimitReached):
        llm.chat([], system="", route="r")
    with pytest.raises(SpendLimitReached):  # the open circuit does not launder it either
        llm.chat([], system="", route="r")
    assert backup.n == 0


def test_a_spend_limit_falls_back_only_when_the_fallback_is_metered_by_the_same_limits():
    backup = Stub(OK)
    llm = ResilientLLM(Stub(SpendLimitReached("cap")), backup, fallback_metered=True)
    assert llm.chat([], system="", route="r").fallback_used and backup.n == 1


def test_the_wrapper_survives_copy_and_pickle_before_init():
    llm = ResilientLLM(Stub(OK), None)
    assert copy.copy(llm).primary is llm.primary
    blank = ResilientLLM.__new__(ResilientLLM)  # what copy / pickle build before __init__ runs
    with pytest.raises(AttributeError):
        _ = blank.call_timeout_s
    assert not hasattr(blank, "anything")
    with pytest.raises(
        Exception
    ) as e:  # the Stub is a local class: not picklable, but not a recursion
        pickle.dumps(llm)
    assert not isinstance(e.value, RecursionError)


# --- m8: the breaker --------------------------------------------------------------------------------------------


def test_a_stale_failure_does_not_extend_the_open_window_or_clear_the_probe():
    now = [0.0]
    b = CircuitBreaker(2, 30.0, clock=lambda: now[0])
    t1, t2, t3 = b.allow(), b.allow(), b.allow()  # three calls start while closed
    b.failure(t1)
    b.failure(t2)  # opens at t=0
    now[0] = 31
    probe = b.allow()
    assert probe is not None and probe.probe
    now[0] = 35
    b.failure(t3)  # the stale third call fails late
    assert b.allow() is None  # the probe is still the only one out: _probing was not cleared
    b.success(probe)
    assert b.allow() is not None  # closed by the probe, not by a stale call


def test_a_stale_success_does_not_close_an_open_circuit():
    now = [0.0]
    b = CircuitBreaker(1, 30.0, clock=lambda: now[0])
    stale = b.allow()
    b.failure(b.allow())
    b.success(stale)
    assert b.allow() is None


def test_a_hung_probe_is_abandoned_after_its_timeout():
    now = [0.0]
    b = CircuitBreaker(1, 10.0, clock=lambda: now[0], probe_timeout_s=20.0)
    b.failure(b.allow())
    now[0] = 11
    hung = b.allow()  # the probe that never reports
    assert hung.probe and b.allow() is None
    now[0] = 32
    second = b.allow()
    assert second is not None and second.probe
    b.success(hung)  # the hung one finally returns: stale, ignored
    assert b.allow() is None
    b.success(second)
    assert b.allow() is not None


# --- M3 / m7: bounded parsing, classifiers that never raise ---------------------------------------------------------


class Rec(BaseModel):
    title: str


class Scripted:
    def __init__(self, texts):
        self.texts, self.calls = list(texts), []

    def chat(self, messages, **kw):
        self.calls.append(messages)
        return Reply(text=self.texts.pop(0), model_id="m")


DEEP = [
    pytest.param("[" * 200_000, id="brackets"),
    pytest.param('{"a":' * 100_000, id="objects"),
    pytest.param("[" * 5000 + "]" * 5000, id="closed"),
    pytest.param('{"title":' + "[" * 100_000, id="in-field"),
]
DEEP_TEXTS = [p.values[0] for p in DEEP]


@pytest.mark.parametrize("text", DEEP)
def test_a_deeply_nested_reply_is_an_invalid_reply_not_a_crash(text):
    out = extract(Scripted([text, text]), b"d", Rec, run_id="r", route="x")
    assert isinstance(out, DeadLetter) and len(out.errors) == 2


def test_a_deeply_nested_tool_call_input_is_an_invalid_reply_too():
    deep: Any = {}
    for _ in range(50_000):
        deep = {"child": deep}

    class Node(BaseModel):
        child: Node | None = None

    class Tooled:
        calls = 0

        def chat(self, messages, **kw):
            Tooled.calls += 1
            return Reply.model_construct(
                model_id="m",
                text="",
                cost_usd=D(0),
                tool_calls=[ToolCall.model_construct(name="submit_answer", input=deep)],
            )

    out = extract(Tooled(), b"d", Node, run_id="r", route="x")
    assert isinstance(out, DeadLetter) and Tooled.calls == 2


def test_an_oversized_reply_is_refused_before_parsing():
    out = extract(Scripted(["{" + " " * 2_000_000 + "}"] * 2), b"d", Rec, run_id="r", route="x")
    assert isinstance(out, DeadLetter)
    assert json_in_text("x" * 2_000_000 + "{}") is None


def test_json_in_text_and_loads_bounded_never_raise_recursion():
    for text in DEEP_TEXTS:
        assert json_in_text("prefix " + text) is None
        with pytest.raises(ValueError):
            loads_bounded(text)
    assert loads_bounded('{"a": [1, {"b": 2}]}') == {"a": [1, {"b": 2}]}
    assert json_in_text('noise {"a": "}{" } tail') == {
        "a": "}{"
    }  # braces inside strings are not nesting


def test_many_open_braces_do_not_make_json_in_text_quadratic():
    t0 = time.monotonic()
    assert json_in_text("{" * 500_000) is None
    assert time.monotonic() - t0 < 2


def test_the_judge_reads_a_hostile_reply_as_no_answer():
    assert _answer(Reply(text="[" * 300_000, model_id="m")) is None


def test_the_openai_tool_arguments_parser_bounds_nesting():
    assert (
        openai_compat._call({"function": {"name": "f", "arguments": "{" + '"a":{' * 100_000}})
        is None
    )


class _HostileMessage:
    def __str__(self):
        raise RuntimeError("hostile __str__")


class _Err(Exception):
    def __init__(self, status, body):
        super().__init__("x")
        self.status_code, self.body = status, body


def test_the_anthropic_classifier_never_raises_inside_the_except_block():
    assert anthropic_spend_limit(_Err(429, {"error": {"message": _HostileMessage()}})) is False
    assert anthropic_spend_limit(_Err(429, {"error": {"details": _HostileMessage()}})) is False
    assert anthropic_spend_limit(_Err(429, object())) is False
    # and through the real retry loop: the original 429 is retried, not replaced by the classifier's own error
    calls = []

    def call():
        calls.append(1)
        if len(calls) == 1:
            raise _Err(429, {"error": {"message": _HostileMessage()}})
        return "ok"

    assert (
        with_retry(
            call, label="t", max_attempts=2, sleep=lambda s: None, spend_limit=anthropic_spend_limit
        )
        == "ok"
    )


def _http_error(code, body: dict | str):
    raw = body if isinstance(body, str) else json.dumps(body)
    return urllib.error.HTTPError(
        "https://x.example", code, "m", Message(), io.BytesIO(raw.encode())
    )


def test_openai_insufficient_quota_is_a_spend_limit_and_a_plain_429_is_a_throttle():
    quota = {"error": {"message": "x", "type": "insufficient_quota", "code": "insufficient_quota"}}
    assert openai_compat.spend_limit(_http_error(429, quota))
    assert not openai_compat.spend_limit(
        _http_error(429, {"error": {"code": "rate_limit_exceeded"}})
    )
    assert not openai_compat.spend_limit(_http_error(500, quota))
    assert not openai_compat.spend_limit(_http_error(429, "not json"))
    calls = []

    def call():
        calls.append(1)
        raise _http_error(429, quota)

    with pytest.raises(SpendLimitReached):
        with_retry(
            call,
            label="t",
            max_attempts=4,
            sleep=lambda s: None,
            spend_limit=openai_compat.spend_limit,
        )
    assert len(calls) == 1


def test_gemini_per_day_quota_is_a_spend_limit_and_per_minute_is_a_throttle():
    def body(quota_id):
        return {
            "error": {
                "status": "RESOURCE_EXHAUSTED",
                "details": [{"violations": [{"quotaId": quota_id}]}],
            }
        }

    assert gemini.spend_limit(
        _http_error(429, body("GenerateRequestsPerDayPerProjectPerModel-FreeTier"))
    )
    assert not gemini.spend_limit(
        _http_error(429, body("GenerateRequestsPerMinutePerProjectPerModel"))
    )
    assert not gemini.spend_limit(_http_error(429, {"error": {"details": "weird"}}))


# --- m5 / m6: deadline and retry-after -------------------------------------------------------------------------------


def test_a_hung_attempt_is_abandoned_at_the_deadline():
    release = threading.Event()

    def hang():
        release.wait(30)
        return "late"

    t0 = time.monotonic()
    try:
        with pytest.raises(DeadlineExceeded):
            with_retry(hang, label="t", max_attempts=3, deadline_s=0.3)
        assert time.monotonic() - t0 < 3
    finally:
        release.set()


def test_the_deadline_spans_attempts_not_each_attempt():
    calls = []

    def slow_failure():
        calls.append(1)
        time.sleep(0.15)
        raise urllib.error.URLError("reset")

    t0 = time.monotonic()
    with pytest.raises((DeadlineExceeded, ProviderExhausted)):
        with_retry(
            slow_failure,
            label="t",
            max_attempts=10,
            deadline_s=0.5,
            sleep=lambda s: time.sleep(0.01),
        )
    assert time.monotonic() - t0 < 2 and len(calls) < 10


def test_the_config_default_deadline_is_not_none():
    from hadavin_sdk.backends.table import AnthropicSettings

    s = AnthropicSettings(kind="anthropic", platform="api", api_key_secret_name="k")  # noqa: S106 - a name
    assert s.deadline_s == 120.0


def _throttle(seconds: str):
    h = Message()
    h["Retry-After"] = seconds
    return urllib.error.HTTPError("https://x.example", 429, "slow", h, None)


def test_retry_after_is_honoured_beyond_the_backoff_cap_up_to_the_ceiling():
    waits, outcomes = [], iter([_throttle("30"), "ok"])

    def call():
        o = next(outcomes)
        if isinstance(o, Exception):
            raise o
        return o

    assert with_retry(call, label="t", max_attempts=2, sleep=waits.append) == "ok"
    assert waits == [30.0]


def test_a_retry_after_over_the_ceiling_is_not_retried_early():
    waits, calls = [], []

    def call():
        calls.append(1)
        raise _throttle("3600")

    with pytest.raises(ProviderExhausted, match="ceiling"):
        with_retry(call, label="t", max_attempts=4, sleep=waits.append)
    assert waits == [] and len(calls) == 1


# --- m12: alternating roles on every kind ------------------------------------------------------------------------------

ROUTES = {
    "r": Route(model_id="m-1", input_usd_per_mtok=D(1), output_usd_per_mtok=D(1), max_tokens=10),
}
TWO_USER = [{"role": "user", "content": "first"}, {"role": "user", "content": "second"}]
THREE = TWO_USER + [{"role": "assistant", "content": "a"}, {"role": "user", "content": "b"}]


def _alternates(roles):
    return all(a != b for a, b in itertools.pairwise(roles))


def test_turns_merges_consecutive_same_role_messages_and_keeps_documents_first():
    out = turns(THREE, [b"DOC"])
    assert [r for r, _ in out] == ["user", "assistant", "user"]
    assert out[0][1] == ["DOC", "first", "second"]


def test_anthropic_request_alternates_roles():
    seen = {}

    def create(**req):
        seen.update(req)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="ok")],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            stop_reason="end_turn",
        )

    llm = AnthropicLLM(SimpleNamespace(messages=SimpleNamespace(create=create)), ROUTES, 1)
    llm.chat(THREE, system="", route="r")
    assert _alternates([m["role"] for m in seen["messages"]]) and len(seen["messages"]) == 3


def test_bedrock_request_alternates_roles():
    seen = {}

    def converse(**req):
        seen.update(req)
        return {
            "output": {"message": {"content": [{"text": "ok"}]}},
            "usage": {},
            "stopReason": "end_turn",
        }

    BedrockLLM(SimpleNamespace(converse=converse), ROUTES, 1).chat(THREE, system="", route="r")
    assert _alternates([m["role"] for m in seen["messages"]]) and len(seen["messages"]) == 3


def test_openai_compat_request_alternates_roles(monkeypatch):
    seen = {}

    def post(url, body, headers, timeout):
        seen.update(body)
        return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "usage": {}}

    monkeypatch.setattr(openai_compat, "post_json", post)
    llm = openai_compat.OpenAICompatLLM("https://x.example/v1", None, ROUTES, 5.0, 1)
    llm.chat(THREE, system="", route="r")
    assert _alternates([m["role"] for m in seen["messages"]]) and len(seen["messages"]) == 3


def test_gemini_request_alternates_roles(monkeypatch):
    seen = {}

    def post(url, body, headers, timeout):
        seen.update(body)
        return {"candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}]}

    monkeypatch.setattr(gemini, "post_json", post)
    gemini.GeminiLLM(lambda: "k", ROUTES, 5.0, 1).chat(THREE, system="", route="r")
    assert _alternates([c["role"] for c in seen["contents"]]) and len(seen["contents"]) == 3


def test_the_extract_retry_is_one_user_turn_with_the_sanitized_summary_and_not_the_reply():
    canary = "canary-" + "reply-body"
    llm = Scripted([json.dumps({"title": 1, "x": canary}), json.dumps({"title": "ok"})])
    out = extract(llm, b"d", Rec, run_id="r", route="x")
    assert not isinstance(out, DeadLetter)
    retry = llm.calls[1]
    assert len(retry) == 1 and retry[0]["role"] == "user"
    assert "title: string_type" in retry[0]["content"] and canary not in json.dumps(retry)


def test_nesting_ok_boundary_and_strings():
    from hadavin_sdk.llm.common import nesting_ok

    assert nesting_ok("[" * 64 + "]" * 64) and not nesting_ok("[" * 65 + "]" * 65)
    assert nesting_ok('{"a": "[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[["}')
    assert nesting_ok("[" * 100 + "]" * 100, limit=100)


def test_each_kind_with_a_quota_429_stops_after_one_request(monkeypatch):
    quota = {"error": {"type": "insufficient_quota", "code": "insufficient_quota"}}
    per_day = {"error": {"details": [{"violations": [{"quotaId": "RequestsPerDayPerProject"}]}]}}
    cap = {"type": "rate_limit_error", "details": {"error_code": "enforced_spend_limit_reached"}}
    calls = []

    def boom(body):
        def post(url, payload, headers, timeout):
            calls.append(1)
            raise _http_error(429, body)

        return post

    monkeypatch.setattr(openai_compat, "post_json", boom(quota))
    oa = openai_compat.OpenAICompatLLM("https://x.example/v1", None, ROUTES, 5.0, 4, lambda s: None)
    with pytest.raises(SpendLimitReached):
        oa.chat([{"role": "user", "content": "q"}], system="", route="r")
    monkeypatch.setattr(gemini, "post_json", boom(per_day))
    gm = gemini.GeminiLLM(lambda: "k", ROUTES, 5.0, 4, lambda s: None)
    with pytest.raises(SpendLimitReached):
        gm.chat([{"role": "user", "content": "q"}], system="", route="r")

    def create(**req):
        calls.append(1)
        raise _Err(429, cap)

    an = AnthropicLLM(
        SimpleNamespace(messages=SimpleNamespace(create=create)), ROUTES, 4, lambda s: None
    )
    with pytest.raises(SpendLimitReached):
        an.chat([{"role": "user", "content": "q"}], system="", route="r")
    assert len(calls) == 3  # one request per kind, none retried


# --- R371 / R372: tenants never share counters; documents never reach a second vendor by default ---------------------


def _tenant_limits(store, tenant, daily="1.00"):
    from hadavin_sdk.limits import Limits

    agent = SimpleNamespace(
        budget_usd=SimpleNamespace(daily=D(daily), monthly=D("100")), max_run_usd=D("0.50")
    )
    return Limits(store, None, SimpleNamespace(agents={"a": agent}), tenant=tenant)  # type: ignore[arg-type]


def test_two_clients_on_one_store_share_no_budget_and_no_run_share():
    from hadavin_sdk.limits import OverBudget
    from hadavin_sdk.store.memory import MemoryStore

    store = MemoryStore()
    a, b = _tenant_limits(store, "client-a"), _tenant_limits(store, "client-b")
    a.reserve("a", D("0.50"), run_id="r1")  # A uses its whole run share and half its day
    a.reserve("a", D("0.50"), run_id="r2")
    with pytest.raises(OverBudget):
        a.reserve("a", D("0.10"))  # A's day is spent
    b.reserve("a", D("0.50"), run_id="r1")  # same agent id, same run id: B is untouched
    assert b.blocked("a") == [] and a.blocked("a") == ["daily_budget"]
    b.charge("a", D("0.40"))
    assert a.store.spend_totals("8:client-a/a", MID)[0] == D("1.00")
    assert store.spend_totals("8:client-b/a", MID)[0] == D("0.90")
    assert store.spend_totals("a", MID) == (0, 0)  # nothing under the bare key


MID = __import__("datetime").datetime.now(__import__("datetime").UTC).date()


def test_canary_document_never_reaches_a_second_vendor_its_events_or_logs(caplog):
    canary = "canary-" + "client-a-" + "7QX"
    events, backup = [], Stub(OK)
    llm = ResilientLLM(Stub(DOWN), backup, on_fallback=events.append)
    with caplog.at_level("DEBUG"), pytest.raises(ProviderExhausted):
        llm.chat(
            [{"role": "user", "content": "x"}], system="s", route="r", documents=[canary.encode()]
        )
    assert backup.n == 0 and backup.seen == []
    assert canary not in json.dumps(events) and canary not in caplog.text
    assert (
        events
        and events[0]["event"] == "llm_fallback_refused"
        and events[0]["documents_sent"] is False
    )


def test_each_fallback_control_has_a_negative_case():
    # documents off, spend-limit unmetered, hook failure: all three deny, each leaving the fallback uncalled
    for primary_err, kw in (
        (DOWN, {"documents": [b"d"]}),
        (SpendLimitReached("cap"), {}),
    ):
        backup = Stub(OK)
        with pytest.raises(ProviderError):
            ResilientLLM(Stub(primary_err), backup).chat([], system="", route="r", **kw)
        assert backup.n == 0

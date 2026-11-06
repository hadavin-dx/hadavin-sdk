"""P4a-1: a reply without usable token counts is REFUSED (`UsageMissing`), never estimated; a reported zero is kept
only where the reply is empty; the cost is exact and rounded up once. Rows U1 to U14c of the P4a ticket.

The shims below let this file import on a tree that predates P4a (the fail-before run): a missing name becomes a
local stand-in, so a row fails by ASSERTION and not by ImportError."""

from __future__ import annotations

import ast
import copy
import json
import logging
import math
import pickle
import random
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import defaults, models
from hadavin_sdk.config import Route
from hadavin_sdk.llm import ProviderError, ProviderExhausted
from hadavin_sdk.llm import protocol as _protocol
from hadavin_sdk.llm.common import ANSWER_TOOL  # noqa: F401 - the forced tool's name (used by readers of this file)
from tests.contracts.kinds.builtin import ROUTES
from tests.contracts.kinds.llm_wire import (
    AnthropicWire,
    GeminiWire,
    OpenAICompatWire,
)
from tests.contracts.test_llm import CALL, SCHEMA

D = Decimal
UsageMissing = getattr(_protocol, "UsageMissing", None) or type(
    "UsageMissing", (ProviderError,), {"reason": None, "field": None}
)
UnpricedUsage = getattr(_protocol, "UnpricedUsage", None) or type(
    "UnpricedUsage", (UsageMissing,), {}
)
SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
PRICED = ROUTES["default"]  # 3.00 in, 15.00 out per million tokens
FREE = PRICED.model_copy(
    update={"input_usd_per_mtok": D(0), "output_usd_per_mtok": D(0)}
)  # built directly: only the Config check of P4a-2 refuses a zero price
CANARY = "canary" + "-" + "value"  # built from parts: never one literal


def _exact(tin: int, tout: int, route: Route = PRICED) -> Fraction:
    return (
        Fraction(tin) * Fraction(route.input_usd_per_mtok)
        + Fraction(tout) * Fraction(route.output_usd_per_mtok)
    ) / 10**6


def _up8(x: Fraction) -> Decimal:
    scaled = x * 10**8
    whole = math.ceil(scaled)
    return D(whole).scaleb(-8)


class StubConverse:
    """A plain `converse` client for Bedrock: the Stubber validates against the service model and cannot serve
    a reply without `usage`, so the missing-usage rows drive `BedrockLLM.chat()` with this."""

    def __init__(self, body: dict) -> None:
        self.body, self.calls = body, 0

    def converse(self, **request):
        self.calls += 1
        return copy.deepcopy(self.body)


def _bedrock(mutate=None, scenario: str = "text"):
    pytest.importorskip("boto3", reason="needs extra aws")
    from hadavin_sdk.llm.bedrock import BedrockLLM
    from tests.fixtures.http_fake import fixture

    body = copy.deepcopy(fixture("bedrock", scenario)["body"])
    if mutate:
        mutate(body)
    stub = StubConverse(body)
    return BedrockLLM(stub, ROUTES, 3, sleep=lambda s: None), stub


ANTHROPIC_PLATFORMS = ("api", "vertex", "foundry")
HTTP_KINDS = [("anthropic", p) for p in ANTHROPIC_PLATFORMS] + [
    ("openai_compat", ""),
    ("gemini", ""),
]


@pytest.fixture(params=HTTP_KINDS, ids=[f"{k}.{p}" if p else k for k, p in HTTP_KINDS])
def wire(request):
    kind, platform = request.param
    if kind == "anthropic":
        pytest.importorskip("anthropic", reason="needs extra anthropic")
        w = AnthropicWire(platform)
    else:
        w = {"openai_compat": OpenAICompatWire, "gemini": GeminiWire}[kind]()
    yield w
    w.close()


def _empty(wire, fx):
    """The text fixture with no text and no tool call."""
    body = fx["body"]
    if isinstance(wire, AnthropicWire):
        body["content"] = []
    elif isinstance(wire, OpenAICompatWire):
        body["choices"][0]["message"]["content"] = ""
    else:
        body["candidates"][0]["content"]["parts"] = []
    return fx


def _is_usage_missing(exc: BaseException, reason: str, field: str | None = None) -> None:
    assert type(exc).__name__ in ("UsageMissing", "UnpricedUsage"), type(exc).__name__
    assert not isinstance(exc, ProviderExhausted)
    assert exc.reason == reason
    if field is not None:
        assert exc.field == field


# ---------------------------------------------------------------------------------------------------------------
# U1 absent usage is refused, per kind, with ONE provider request.


def test_u1_absent_usage_is_refused_with_one_request(wire):
    llm = wire.serve(wire.without_usage(wire.scenario("text")))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "absent", "usage")
    assert len(wire.requests) == 1


def test_u1_bedrock_absent_usage_is_refused_with_one_call():
    llm, stub = _bedrock(lambda body: body.pop("usage"))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "absent", "usage")
    assert stub.calls == 1


@pytest.mark.parametrize("bad", [[], "usage", 7])
def test_u1_a_usage_that_is_not_an_object_is_absent(bad):
    """Build note: a list or a string where the usage object should be is `absent("usage")` on the JSON kinds."""
    for cls, key in ((OpenAICompatWire, "usage"), (GeminiWire, "usageMetadata")):
        w = cls()
        try:
            fx = w.scenario("text")
            fx["body"][key] = copy.deepcopy(bad)
            with pytest.raises(ProviderError) as caught:
                w.serve(fx).chat(**CALL)
            _is_usage_missing(caught.value, "absent", "usage")
            assert len(w.requests) == 1
        finally:
            w.close()
    llm, _ = _bedrock(lambda body: body.update(usage=copy.deepcopy(bad)))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "absent", "usage")


# ---------------------------------------------------------------------------------------------------------------
# U2 a reported zero is zero where the reply is EMPTY.


def test_u2_a_zero_output_on_an_empty_reply_is_kept(wire):
    fx = _empty(wire, wire.set_tokens(wire.scenario("text"), 300, 0))
    reply = wire.serve(fx).chat(**CALL)
    assert reply.output_tokens == 0 and reply.input_tokens == 300
    assert reply.cost_usd == D("0.0009")


def test_u2_bedrock_a_zero_output_on_an_empty_reply_is_kept():
    def mutate(body):
        body["output"]["message"]["content"] = []
        body["usage"].update(inputTokens=300, outputTokens=0)

    llm, _ = _bedrock(mutate)
    reply = llm.chat(**CALL)
    assert reply.output_tokens == 0 and reply.cost_usd == D("0.0009")


def test_u2_a_blocked_gemini_prompt_has_output_zero():
    w = GeminiWire()
    try:
        fx = w.scenario("text")
        fx["body"] = {
            "promptFeedback": {"blockReason": "SAFETY"},
            "usageMetadata": {"promptTokenCount": 300, "totalTokenCount": 300},
        }
        reply = w.serve(fx).chat(**CALL)
        assert (reply.output_tokens, reply.stop_reason, reply.cost_usd) == (
            0,
            "refusal",
            D("0.0009"),
        )
    finally:
        w.close()


# U2c a reported output zero WITH content is refused.


def test_u2c_zero_output_with_text_is_refused(wire):
    llm = wire.serve(wire.set_tokens(wire.scenario("text"), 300, 0))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "implausible_zero", "output_tokens")
    assert len(wire.requests) == 1


def test_u2c_zero_output_with_a_tool_call_is_refused(wire):
    llm = wire.serve(wire.set_tokens(wire.scenario("tool_call"), 1200, 0))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "implausible_zero", "output_tokens")
    assert len(wire.requests) == 1


def test_u2c_one_output_token_with_text_is_accepted(wire):
    reply = wire.serve(wire.set_tokens(wire.scenario("text"), 300, 1)).chat(**CALL)
    assert reply.output_tokens == 1


@pytest.mark.parametrize("scenario", ["text", "tool_call"])
def test_u2c_bedrock_zero_output_with_content_is_refused(scenario):
    llm, stub = _bedrock(lambda body: body["usage"].update(outputTokens=0), scenario)
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "implausible_zero", "output_tokens")
    assert stub.calls == 1


# U2b the zero-input rule and the cache refusal live in `cost_usd`.


def test_u2b_cost_usd_refuses_a_zero_input_on_a_priced_route():
    from hadavin_sdk.llm.pricing import cost_usd

    with pytest.raises(ProviderError) as caught:
        cost_usd(models.Usage(0, 5), PRICED)
    _is_usage_missing(caught.value, "implausible_zero", "input_tokens")


def test_u2b_a_free_route_accepts_a_zero_input_at_cost_zero():
    from hadavin_sdk.llm.pricing import cost_usd

    assert cost_usd(models.Usage(0, 5), FREE) == 0


@pytest.mark.parametrize(
    ("usage_kw", "field"),
    [
        ({"cache_write_tokens": 1}, "cache_write_tokens"),
        ({"cache_read_tokens": 1}, "cache_read_tokens"),
    ],
)
def test_u2b_a_cache_count_is_unpriced_and_checked_before_zero_input(usage_kw, field):
    from hadavin_sdk.llm.pricing import cost_usd

    with pytest.raises(ProviderError) as caught:
        cost_usd(
            models.Usage(0, 5, **usage_kw), PRICED
        )  # input 0 too: the cache refusal comes first
    assert type(caught.value).__name__ == "UnpricedUsage"
    _is_usage_missing(caught.value, "unpriced_class", field)


def test_u2b_through_chat_a_zero_input_is_refused(wire):
    llm = wire.serve(wire.set_tokens(wire.scenario("text"), 0, 7))
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "implausible_zero", "input_tokens")
    assert len(wire.requests) == 1


# ---------------------------------------------------------------------------------------------------------------
# U3 hostile counts.

HOSTILE = [None, "", "7", 7.0, True, False, -1, 2**63, 10**18, {}, []]
JSON_FIELDS = {  # which side of the usage object each field is
    "openai_compat": ("prompt_tokens", "completion_tokens"),
    "gemini": ("promptTokenCount", "candidatesTokenCount"),
}


def _hostile_id(v):
    return repr(v)


@pytest.mark.parametrize("which", ["input", "output"])
@pytest.mark.parametrize("bad", HOSTILE, ids=_hostile_id)
@pytest.mark.parametrize("cls", [OpenAICompatWire, GeminiWire], ids=["openai_compat", "gemini"])
def test_u3_hostile_counts_are_refused_on_the_json_wires(cls, bad, which):
    w = cls()
    try:
        tin, tout = (bad, 7) if which == "input" else (300, bad)
        llm = w.serve(w.set_tokens(w.scenario("text"), tin, tout))
        with pytest.raises(ProviderError) as caught:
            llm.chat(**CALL)
        _is_usage_missing(caught.value, "absent" if bad is None else "invalid", f"{which}_tokens")
        assert len(w.requests) == 1
    finally:
        w.close()


@pytest.mark.parametrize("which", ["input", "output"])
@pytest.mark.parametrize("bad", HOSTILE, ids=_hostile_id)
def test_u3_hostile_counts_are_refused_through_bedrock_chat(bad, which):
    key = "inputTokens" if which == "input" else "outputTokens"

    def mutate(body):
        if bad is None:
            body["usage"].pop(key)
        else:
            body["usage"][key] = copy.deepcopy(bad)

    llm, stub = _bedrock(mutate)
    with pytest.raises(ProviderError) as caught:
        llm.chat(**CALL)
    _is_usage_missing(caught.value, "absent" if bad is None else "invalid", f"{which}_tokens")
    assert stub.calls == 1


def test_u3_anthropic_null_counts_reach_the_check_from_the_wire():
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    for which in ("input", "output"):
        w = AnthropicWire("api")
        try:
            tin, tout = (None, 7) if which == "input" else (300, None)
            llm = w.serve(w.set_tokens(w.scenario("text"), tin, tout))
            with pytest.raises(ProviderError) as caught:
                llm.chat(**CALL)
            _is_usage_missing(caught.value, "absent", f"{which}_tokens")
        finally:
            w.close()


def _anthropic_resp(usage):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hi")], stop_reason="end_turn", usage=usage
    )


@pytest.mark.parametrize("bad", [x for x in HOSTILE if x is not None], ids=_hostile_id)
@pytest.mark.parametrize("which", ["input", "output"])
def test_u3_anthropic_unit_row_not_wire(bad, which):
    """Unit row on `AnthropicLLM._parse` with a stub usage object, not wire: the SDK model carries only some forms."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    from hadavin_sdk.llm.anthropic import AnthropicLLM

    raw = {
        "input_tokens": bad if which == "input" else 300,
        "output_tokens": 7 if which == "input" else bad,
    }
    resp = _anthropic_resp(SimpleNamespace(model_dump=lambda: raw))
    with pytest.raises(ProviderError) as caught:
        AnthropicLLM._parse(resp)
    _is_usage_missing(caught.value, "invalid", f"{which}_tokens")


def test_u3_anthropic_usage_that_is_missing_or_not_an_object():
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    from hadavin_sdk.llm.anthropic import AnthropicLLM

    for usage in (None, "x", [1]):
        with pytest.raises(ProviderError) as caught:
            AnthropicLLM._parse(_anthropic_resp(usage))
        _is_usage_missing(caught.value, "absent", "usage")


@pytest.mark.parametrize("cls", [OpenAICompatWire, GeminiWire], ids=["openai_compat", "gemini"])
def test_u3_boundary_exactly_the_cap_is_accepted_and_one_more_is_refused(cls):
    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    assert cap == 10**9
    for which in ("input", "output"):
        w = cls()
        try:
            tin, tout = (cap, 7) if which == "input" else (300, cap)
            reply = w.serve(w.set_tokens(w.scenario("text"), tin, tout)).chat(**CALL)
            assert (reply.input_tokens, reply.output_tokens) == (tin, tout)
            assert reply.cost_usd == _up8(_exact(tin, tout))
        finally:
            w.close()
        w = cls()
        try:
            tin, tout = (cap + 1, 7) if which == "input" else (300, cap + 1)
            with pytest.raises(ProviderError) as caught:
                w.serve(w.set_tokens(w.scenario("text"), tin, tout)).chat(**CALL)
            _is_usage_missing(caught.value, "invalid", f"{which}_tokens")
        finally:
            w.close()


def test_u3_checked_count_boundary_and_forms():
    from hadavin_sdk.llm.protocol import checked_count

    assert checked_count(10**9, "input_tokens") == 10**9
    assert checked_count(0, "input_tokens") == 0
    for bad in (10**9 + 1, -1, True, 1.5, "1", D(5), float("nan"), float("inf")):
        with pytest.raises(ProviderError) as caught:
            checked_count(bad, "input_tokens")
        _is_usage_missing(caught.value, "invalid", "input_tokens")
    with pytest.raises(ProviderError) as caught:
        checked_count(None, "output_tokens")
    _is_usage_missing(caught.value, "absent", "output_tokens")


def _gemini(mutate):
    w = GeminiWire()
    fx = w.scenario("text")
    mutate(fx["body"])
    return w, fx


def test_u3_gemini_missing_prompt_count_is_absent():
    w = GeminiWire()
    try:
        fx = w.scenario("text")
        del fx["body"]["usageMetadata"]["promptTokenCount"]
        with pytest.raises(ProviderError) as caught:
            w.serve(fx).chat(**CALL)
        _is_usage_missing(caught.value, "absent", "input_tokens")
    finally:
        w.close()


def test_u3_gemini_missing_candidates_count_is_zero_only_for_a_blocked_prompt():
    w = GeminiWire()
    try:
        fx = w.scenario("text")
        fx["body"] = {
            "promptFeedback": {"blockReason": "SAFETY"},
            "usageMetadata": {"promptTokenCount": 300},
        }
        reply = w.serve(fx).chat(**CALL)
        assert (reply.output_tokens, reply.stop_reason) == (0, "refusal")
    finally:
        w.close()


def _no_candidates_count(
    body, *, text="Some words.", finish="STOP", thoughts=None, thought_only=False
):
    cand = body["candidates"][0]
    cand["finishReason"] = finish
    cand["content"]["parts"] = (
        [{"text": "thinking", "thought": True}] if thought_only else [{"text": text}]
    )
    usage = body["usageMetadata"]
    usage.pop("candidatesTokenCount")
    if thoughts is not None:
        usage["thoughtsTokenCount"] = thoughts


GEMINI_SHAPES = {
    "text, no thoughts count": lambda b: _no_candidates_count(b),
    "text, thoughts count": lambda b: _no_candidates_count(b, thoughts=93),
    "empty text": lambda b: _no_candidates_count(b, text=""),
    "cut off by SAFETY": lambda b: _no_candidates_count(b, finish="SAFETY"),
    "thoughts only": lambda b: _no_candidates_count(b, thoughts=93, thought_only=True),
}


@pytest.mark.parametrize("shape", list(GEMINI_SHAPES))
def test_u3_gemini_missing_candidates_count_with_a_candidate_is_absent(shape):
    w, fx = _gemini(GEMINI_SHAPES[shape])
    try:
        with pytest.raises(ProviderError) as caught:
            w.serve(fx).chat(**CALL)
        _is_usage_missing(caught.value, "absent", "output_tokens")
    finally:
        w.close()


def test_u3_gemini_malformed_function_call_stays_a_plain_provider_error():
    w, fx = _gemini(lambda b: b["candidates"][0].update(finishReason="MALFORMED_FUNCTION_CALL"))
    try:
        with pytest.raises(ProviderError) as caught:
            w.serve(fx).chat(**CALL)
        assert type(caught.value).__name__ not in ("UsageMissing", "UnpricedUsage")
    finally:
        w.close()


@pytest.mark.parametrize("total", [None, 100, 307, 250])
def test_u3_gemini_a_missing_or_low_total_is_accepted_without_a_cross_check(total):
    def mutate(body):
        if total is None:
            body["usageMetadata"].pop("totalTokenCount")
        else:
            body["usageMetadata"]["totalTokenCount"] = total

    w, fx = _gemini(mutate)
    try:
        reply = w.serve(fx).chat(**CALL)
        assert (reply.input_tokens, reply.output_tokens) == (300, 7)
    finally:
        w.close()


def test_u3_gemini_the_total_can_raise_the_output_count():
    """PL58: prompt 300, candidates 7, total 400 gives output 100 (today's code gave 7)."""
    w, fx = _gemini(lambda b: b["usageMetadata"].update(totalTokenCount=400))
    try:
        reply = w.serve(fx).chat(**CALL)
        assert reply.output_tokens == 100
        assert reply.cost_usd == D("0.0024") == _up8(_exact(300, 100))
    finally:
        w.close()


@pytest.mark.parametrize("bad", [True, -1, "5", 1.5])
def test_u3_gemini_a_bad_total_is_invalid(bad):
    w, fx = _gemini(lambda b: b["usageMetadata"].update(totalTokenCount=bad))
    try:
        with pytest.raises(ProviderError) as caught:
            w.serve(fx).chat(**CALL)
        _is_usage_missing(caught.value, "invalid")
    finally:
        w.close()


# U3b typed refusals before `Usage` is built.


def test_u3b_build_usage_and_add_usage_refuse_with_typed_errors():
    from hadavin_sdk.llm.protocol import add_usage, build_usage

    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    with pytest.raises(ProviderError) as caught:
        build_usage(cap + 1, 5)
    assert type(caught.value) is UsageMissing
    _is_usage_missing(caught.value, "invalid", "input_tokens")
    big = build_usage(6 * 10**8, 6 * 10**8)
    with pytest.raises(ProviderError) as caught:
        add_usage(big, big)
    assert type(caught.value) is UsageMissing
    _is_usage_missing(caught.value, "invalid", "input_tokens")
    out_only = build_usage(1, 6 * 10**8)
    with pytest.raises(ProviderError) as caught:
        add_usage(out_only, out_only)
    _is_usage_missing(caught.value, "invalid", "output_tokens")
    assert add_usage(build_usage(1, 2), build_usage(3, 4)) == models.Usage(4, 6)
    assert add_usage(models.Usage(cap - 1, 0), models.Usage(1, 0)).input_tokens == cap


def _text_reply(w, text, tin, tout):
    fx = w.scenario("text")
    fx["body"]["choices"][0]["message"]["content"] = text
    return w.set_tokens(fx, tin, tout)


def test_u3b_the_same_sum_through_two_openai_requests_is_a_typed_refusal():
    w = OpenAICompatWire()
    try:
        llm = w.serve(
            _text_reply(w, "no idea", 6 * 10**8, 7), _text_reply(w, "still none", 6 * 10**8, 7)
        )
        with pytest.raises(ProviderError) as caught:
            llm.chat(**CALL, output_schema=SCHEMA)
        assert type(caught.value) is UsageMissing
        _is_usage_missing(caught.value, "invalid", "input_tokens")
        assert len(w.requests) == 2
    finally:
        w.close()


# ---------------------------------------------------------------------------------------------------------------
# U4 openai_compat two-request call.


def _two(w, first, second):
    """(text, prompt, completion) for each of two requests that both lack the forced answer."""
    return w.serve(_text_reply(w, *first), _text_reply(w, *second))


def _chat_two(w, first, second):
    return _two(w, first, second).chat(**CALL, output_schema=SCHEMA)


def test_u4_both_requests_carry_usage_and_the_totals_are_the_sums():
    w = OpenAICompatWire()
    try:
        reply = _chat_two(w, ("no idea", 300, 7), ("still none", 300, 7))
        assert (reply.input_tokens, reply.output_tokens) == (600, 14)
        assert len(w.requests) == 2
    finally:
        w.close()


def test_u4_the_first_without_usage_sends_no_second_request():
    w = OpenAICompatWire()
    try:
        first = w.without_usage(_text_reply(w, "no idea", 300, 7))
        llm = w.serve(first, _text_reply(w, "still none", 300, 7))
        with pytest.raises(ProviderError) as caught:
            llm.chat(**CALL, output_schema=SCHEMA)
        _is_usage_missing(caught.value, "absent", "usage")
        assert len(w.requests) == 1
    finally:
        w.close()


def test_u4_the_second_without_usage_is_refused_after_two_requests():
    w = OpenAICompatWire()
    try:
        second = w.without_usage(_text_reply(w, "still none", 300, 7))
        llm = w.serve(_text_reply(w, "no idea", 300, 7), second)
        with pytest.raises(ProviderError) as caught:
            llm.chat(**CALL, output_schema=SCHEMA)
        _is_usage_missing(caught.value, "absent", "usage")
        assert len(w.requests) == 2
    finally:
        w.close()


U4_CASES = {
    "both report 0 with text": (("no idea", 300, 0), ("still none", 300, 0), "output_tokens", 1),
    "clause 1: request 1 output 0": (
        ("no idea", 300, 0),
        ("still none", 300, 7),
        "output_tokens",
        1,
    ),
    "clause 2: request 1 input 0": (("no idea", 0, 7), ("still none", 300, 7), "input_tokens", 1),
    "clause 3: request 2 output 0": (
        ("no idea", 300, 7),
        ("still none", 300, 0),
        "output_tokens",
        2,
    ),
    "clause 4: request 2 input 0": (("no idea", 300, 7), ("still none", 0, 7), "input_tokens", 2),
}


@pytest.mark.parametrize("case", list(U4_CASES))
def test_u4_a_zero_on_one_request_is_refused_before_the_sum_hides_it(case):
    first, second, field, requests = U4_CASES[case]
    w = OpenAICompatWire()
    try:
        with pytest.raises(ProviderError) as caught:
            _chat_two(w, first, second)
        _is_usage_missing(caught.value, "implausible_zero", field)
        assert len(w.requests) == requests
    finally:
        w.close()


def test_u4_one_empty_request_reporting_zero_is_accepted_and_summed():
    w = OpenAICompatWire()
    try:
        reply = _chat_two(w, ("", 300, 0), ("still none", 300, 7))
        assert (reply.input_tokens, reply.output_tokens) == (600, 7)
        assert len(w.requests) == 2
    finally:
        w.close()


# ---------------------------------------------------------------------------------------------------------------
# U5 FakeLLM.

import hashlib

RECORDED = Path(__file__).resolve().parent / "fixtures" / "recorded"
MSGS = [{"role": "user", "content": "u5"}]


def _fake(tmp_path, data, route=PRICED):
    from hadavin_sdk.llm.fake import FakeLLM

    digest = hashlib.sha256(json.dumps(MSGS, sort_keys=True).encode("utf-8")).hexdigest()
    (tmp_path / f"{digest}-1.json").write_text(json.dumps(data), encoding="utf-8")
    return FakeLLM(tmp_path, {"r": route})


@pytest.mark.parametrize("missing", ["input_tokens", "output_tokens"])
def test_u5_a_recording_without_a_count_is_refused(tmp_path, missing):
    data = {"text": "x", "input_tokens": 5, "output_tokens": 1}
    del data[missing]
    with pytest.raises(ProviderError) as caught:
        _fake(tmp_path, data).chat(MSGS, system="", route="r")
    _is_usage_missing(caught.value, "absent", missing)


def test_u5_with_both_counts_the_cost_is_the_formula_and_zero_is_allowed(tmp_path):
    reply = _fake(tmp_path, {"text": "x", "input_tokens": 300, "output_tokens": 0}).chat(
        MSGS, system="", route="r"
    )
    assert reply.output_tokens == 0 and reply.cost_usd == D("0.0009")


def test_u5_a_boolean_count_is_invalid(tmp_path):
    with pytest.raises(ProviderError) as caught:
        _fake(tmp_path, {"text": "x", "input_tokens": True, "output_tokens": 1}).chat(
            MSGS, system="", route="r"
        )
    _is_usage_missing(caught.value, "invalid", "input_tokens")


def test_u5_a_recording_at_the_cap_loads_and_one_above_is_refused(tmp_path):
    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    reply = _fake(tmp_path, {"text": "x", "input_tokens": cap, "output_tokens": 1}).chat(
        MSGS, system="", route="r"
    )
    assert reply.input_tokens == cap
    sub = tmp_path / "over"
    sub.mkdir()
    with pytest.raises(ProviderError) as caught:
        _fake(sub, {"text": "x", "input_tokens": cap + 1, "output_tokens": 1}).chat(
            MSGS, system="", route="r"
        )
    assert type(caught.value) is UsageMissing
    _is_usage_missing(caught.value, "invalid", "input_tokens")


def test_u5_input_zero_on_a_priced_route_is_implausible_and_on_a_free_route_is_fine(tmp_path):
    data = {"text": "x", "input_tokens": 0, "output_tokens": 5}
    with pytest.raises(ProviderError) as caught:
        _fake(tmp_path, data).chat(MSGS, system="", route="r")
    _is_usage_missing(caught.value, "implausible_zero", "input_tokens")
    free = tmp_path / "free"
    free.mkdir()
    assert _fake(free, data, FREE).chat(MSGS, system="", route="r").cost_usd == 0


def test_u5_the_output_zero_rule_does_not_apply_to_a_hand_made_recording(tmp_path):
    reply = _fake(tmp_path, {"text": "hello", "input_tokens": 5, "output_tokens": 0}).chat(
        MSGS, system="", route="r"
    )
    assert reply.text == "hello" and reply.output_tokens == 0


def test_u5_every_recorded_reply_in_the_repo_still_loads():
    from hadavin_sdk.llm.protocol import build_usage

    files = sorted(RECORDED.glob("*.json"))
    assert len(files) >= 24
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "output_tokens" in data or "input_tokens" in data:
            build_usage(data.get("input_tokens"), data.get("output_tokens"))


# ---------------------------------------------------------------------------------------------------------------
# U7 the message is fixed text.


def test_u7_the_error_message_holds_no_reply_text_or_value(caplog):
    w = OpenAICompatWire()
    try:
        fx = w.scenario("text")
        fx["body"]["choices"][0]["message"]["content"] = f"mail me at x@y.example {CANARY}"
        fx["body"]["usage"] = {"prompt_tokens": CANARY, "completion_tokens": 7}
        with caplog.at_level(logging.DEBUG), pytest.raises(ProviderError) as caught:
            w.serve(fx).chat(**CALL)
    finally:
        w.close()
    exc = caught.value
    assert str(exc) == "usage missing: invalid (input_tokens)"
    for text in (str(exc), repr(exc), caplog.text):
        assert CANARY not in text and "x@y.example" not in text


def test_u7_the_format_is_fixed_with_and_without_a_field():
    assert str(UsageMissing("absent")) == "usage missing: absent"
    assert str(UsageMissing("absent", "usage")) == "usage missing: absent (usage)"
    assert (
        str(UnpricedUsage("cache_read_tokens"))
        == "usage missing: unpriced_class (cache_read_tokens)"
    )


def test_u7_a_reason_or_field_outside_the_closed_lists_is_a_programming_error():
    from hadavin_sdk.llm.protocol import USAGE_FIELDS, USAGE_REASONS

    assert set(USAGE_REASONS) == {"absent", "invalid", "implausible_zero", "unpriced_class"}
    assert set(USAGE_FIELDS) == {
        "usage",
        "input_tokens",
        "output_tokens",
        "cache_write_tokens",
        "cache_read_tokens",
        "service_tier",
        "speed",
    }
    with pytest.raises(ValueError):
        UsageMissing("because")
    with pytest.raises(ValueError):
        UsageMissing("absent", CANARY)


# ---------------------------------------------------------------------------------------------------------------
# U8 class guard: no `or`-default, no `.get(token, default)`, no `not token` on a token count in llm/.

EXEMPT = ("max_tokens",)  # a request limit, not a count read back from a provider


def _mentions_token(source: str, node: ast.AST) -> bool:
    text = ast.get_source_segment(source, node) or ""
    for word in EXEMPT:
        text = text.replace(word, "")
    return "token" in text.lower()


def guard_findings(source: str) -> list[str]:
    """Forms that turn a missing or zero count into a number."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            if any(_mentions_token(source, v) for v in node.values):
                found.append(f"{node.lineno}: `or` on a token count")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and _mentions_token(source, node.args[0])
            and not (isinstance(node.args[1], ast.Constant) and node.args[1].value is None)
        ):
            found.append(f"{node.lineno}: `.get(token key, default)`")
        elif (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.Not)
            and _mentions_token(source, node.operand)
        ):
            found.append(f"{node.lineno}: `not` on a token count")
    return found


def test_u8_no_llm_module_turns_a_missing_count_into_a_number():
    findings = {
        str(p.relative_to(SRC)): guard_findings(p.read_text(encoding="utf-8"))
        for p in sorted((SRC / "llm").glob("*.py"))
    }
    assert {k: v for k, v in findings.items() if v} == {}


PLANTED = {
    "or": "x = tokens[0] or 5\n",
    "get": 'x = data.get("input_tokens", 0)\n',
    "not": "if not tokens:\n    pass\n",
    "or on a Gemini field": "y = usage.get('a') or usage_candidatesTokenCount or 0\n",
}


@pytest.mark.parametrize("name", list(PLANTED))
def test_u8_each_form_is_caught_in_a_planted_file(tmp_path, name):
    path = tmp_path / "planted.py"
    path.write_text(PLANTED[name], encoding="utf-8")
    assert guard_findings(path.read_text(encoding="utf-8")), name


def test_u8_max_tokens_is_exempt_and_get_with_none_is_fine(tmp_path):
    ok = 'a = x.get("input_tokens")\nb = route.max_tokens or 5\nc = not route.max_tokens\n'
    assert guard_findings(ok) == []


# U9 reply() has no `sent` and does not estimate.


def test_u9_reply_takes_no_sent_and_never_estimates():
    import inspect

    from hadavin_sdk.llm import common

    params = inspect.signature(common.reply).parameters
    assert "sent" not in params and "tokens" not in params and "usage" in params
    tree = ast.parse(inspect.getsource(common.reply))
    called = {
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "estimate_tokens" not in called and "price_cost" not in called


# U10 call-site pin and class relations; pickle and copy.


def test_u10_class_relations():
    assert issubclass(UsageMissing, ProviderError)
    assert not issubclass(UsageMissing, ProviderExhausted)
    assert issubclass(UnpricedUsage, UsageMissing)
    assert not issubclass(UnpricedUsage, ProviderExhausted)


@pytest.mark.parametrize(
    "make", [lambda: UsageMissing("absent", "usage"), lambda: UnpricedUsage("cache_read_tokens")]
)
def test_u10_pickle_and_copy_keep_type_reason_field_and_text(make):
    exc = make()
    revived = pickle.loads(pickle.dumps(exc))  # noqa: S301 - the test's own object
    for clone in (revived, copy.copy(exc)):
        assert type(clone) is type(exc)
        assert (clone.reason, clone.field, str(clone)) == (exc.reason, exc.field, str(exc))


def test_u10_the_agent_loop_ends_needs_person_provider_error_after_one_call(cfg_dir):
    from hadavin_sdk.models import RunState
    from tests.test_s5_runtime import build

    rt, cfg = build(cfg_dir)
    calls = []

    def refused(*a, **k):
        calls.append(1)
        raise UsageMissing("absent", "usage")

    rt.llm.chat = refused
    run = rt.handle("test-agent", "svc:test-agent", (cfg.inputs_dir / "create.txt").read_bytes())
    assert (run.state, run.reason_code) == (RunState.NEEDS_PERSON, "provider_error")
    assert len(calls) == 1


# U13 Usage invariants.


@pytest.mark.parametrize(
    "bad", [True, 1.0, "1", None, -1, defaults.MAX_USAGE_TOKENS_PER_CLASS + 1], ids=repr
)
@pytest.mark.parametrize("slot", [0, 1, 2, 3])
def test_u13_usage_refuses_a_bad_count_in_any_class(bad, slot):
    args = [1, 1, 0, 0]
    args[slot] = bad
    with pytest.raises(ValueError):
        models.Usage(*args)


def test_u13_usage_accepts_the_cap_sums_the_prompt_and_is_frozen():
    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    u = models.Usage(cap, cap, cap, cap)
    assert u.prompt_tokens == cap * 3
    assert models.Usage(3, 4, 5, 6).prompt_tokens == 3 + 5 + 6
    with pytest.raises((AttributeError, TypeError)):
        u.input_tokens = 1  # type: ignore[misc]
    assert not hasattr(u, "__dict__")  # slotted


# ---------------------------------------------------------------------------------------------------------------
# U14 exactness, max cases, rounding at every producer.


def test_u14_cost_usd_is_exact_over_seeded_cases():
    from hadavin_sdk.llm.pricing import cost_usd

    rng = random.Random(4242)  # noqa: S311 - a seeded test generator, not a secret
    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    top = int(defaults.MAX_ROUTE_PRICE_USD_PER_MTOK * 10**6)
    for _ in range(2000):
        pin, pout = (D(rng.randint(0, top)).scaleb(-6) for _ in range(2))
        route = PRICED.model_copy(update={"input_usd_per_mtok": pin, "output_usd_per_mtok": pout})
        tin, tout = rng.randint(1, cap), rng.randint(0, cap)
        got = cost_usd(models.Usage(tin, tout), route)
        want = (Fraction(tin) * Fraction(pin) + Fraction(tout) * Fraction(pout)) / 10**6
        assert Fraction(got) == want


def test_u14_max_case_at_the_price_bound_is_exact():
    from hadavin_sdk.llm.common import reply

    cap, top = defaults.MAX_USAGE_TOKENS_PER_CLASS, defaults.MAX_ROUTE_PRICE_USD_PER_MTOK
    route = PRICED.model_copy(update={"input_usd_per_mtok": D(top), "output_usd_per_mtok": D(top)})
    got = reply(route, text="x", calls=[], usage=models.Usage(cap, cap), stop=None, started=0.0)
    assert Fraction(got.cost_usd) == Fraction(2 * cap * top, 10**6)


def test_u14_max_case_rounding_goes_up():
    from hadavin_sdk.llm.common import reply

    assert defaults.MAX_ROUTE_PRICE_USD_PER_MTOK >= D("999.999999"), (
        "PENDING LEAD 26 lowered the price bound"
    )
    n, price = 999_999_999, D("999.999999")
    route = PRICED.model_copy(update={"input_usd_per_mtok": price, "output_usd_per_mtok": price})
    got = reply(route, text="x", calls=[], usage=models.Usage(n, n), stop=None, started=0.0)
    exact = Fraction(2 * n * 999_999_999, 10**12)
    assert exact == Fraction("1999999.996000000002")
    assert got.cost_usd == D("1999999.99600001") == _up8(exact)


def _producers(tmp_path):
    """(name, function (tin, tout, route) -> Reply) for each producer: four kinds through their `_parse` and
    `reply()`, and FakeLLM."""
    from hadavin_sdk.llm.common import reply

    out = {}

    def via_reply(tin, tout, route):
        return reply(
            route, text="x", calls=[], usage=models.Usage(tin, tout), stop=None, started=0.0
        )

    out["reply"] = via_reply

    def via_fake(tin, tout, route):
        sub = tmp_path / f"f{len(list(tmp_path.iterdir()))}"
        sub.mkdir()
        return _fake(sub, {"text": "x", "input_tokens": tin, "output_tokens": tout}, route).chat(
            MSGS, system="", route="r"
        )

    out["fake"] = via_fake

    def via_openai(tin, tout, route):
        w = OpenAICompatWire()
        try:
            return w.serve(
                w.set_tokens(w.scenario("text"), tin, tout), routes={"default": route}
            ).chat(**CALL)
        finally:
            w.close()

    out["openai_compat"] = via_openai
    return out


def test_u14b_every_producer_rounds_the_exact_cost_up_once(tmp_path):
    rng = random.Random(7)  # noqa: S311 - a seeded test generator, not a secret
    producers = _producers(tmp_path)
    for name, produce in producers.items():
        for _ in range(12):
            route = PRICED.model_copy(
                update={
                    "input_usd_per_mtok": D(rng.randint(1, 10**9)).scaleb(-6),
                    "output_usd_per_mtok": D(rng.randint(0, 10**9)).scaleb(-6),
                }
            )
            tin, tout = rng.randint(1, 10**6), rng.randint(1, 10**6)
            got = produce(tin, tout, route).cost_usd
            assert got == _up8(_exact(tin, tout, route)), name
            assert got.as_tuple().exponent >= -8


def test_u14b_an_exact_eight_decimal_cost_is_unchanged_and_cost_usd_does_not_round():
    from hadavin_sdk.llm.pricing import cost_usd

    route = PRICED.model_copy(
        update={"input_usd_per_mtok": D("0.000001"), "output_usd_per_mtok": D("0.000001")}
    )
    unrounded = cost_usd(models.Usage(1234, 1), route)
    assert unrounded == D("0.000000001235")  # nine-plus decimals: the helper has not touched it


# U14c a route that skipped validation.


def test_u14c_a_nan_or_infinite_price_is_a_value_error_not_a_provider_error(tmp_path):
    from hadavin_sdk.llm.common import reply

    for price in ("NaN", "Infinity"):
        bad = PRICED.model_copy(update={"input_usd_per_mtok": D(price)})
        with pytest.raises(ValueError) as caught:
            reply(bad, text="x", calls=[], usage=models.Usage(5, 5), stop=None, started=0.0)
        assert not isinstance(caught.value, ProviderError)
        sub = tmp_path / price
        sub.mkdir()
        with pytest.raises(ValueError) as caught:
            _fake(sub, {"text": "x", "input_tokens": 5, "output_tokens": 5}, bad).chat(
                MSGS, system="", route="r"
            )
        assert not isinstance(caught.value, ProviderError)


def test_u14c_a_signalling_nan_price_is_usage_missing_invalid():
    from hadavin_sdk.llm.pricing import cost_usd

    bad = PRICED.model_copy(update={"input_usd_per_mtok": D("sNaN")})
    with pytest.raises(ProviderError) as caught:
        cost_usd(models.Usage(5, 5), bad)
    _is_usage_missing(caught.value, "invalid")

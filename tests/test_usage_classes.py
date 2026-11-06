"""P4a-2: the cache classes of usage are read and a non-zero count is refused; the pricing words are checked; every
kind declares its request count; the k1b loop books the whole-call maximum; a zero price needs the fake kind; the k1b
replay runs only the fake kind. Rows C2 to C18 of the P4a ticket.

Shims let this file import on a tree that predates P4a-2 (the fail-before run): a missing name becomes a local
stand-in, so a row fails by ASSERTION and not by ImportError."""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import math
import threading
import urllib.error
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.config import Route, load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b import loop
from hadavin_sdk.k1b.bundle import load_bundles
from hadavin_sdk.k1b.tools import TOOL_SPECS
from hadavin_sdk.llm import FakeLLM, ProviderError, ProviderExhausted
from hadavin_sdk.llm import common as _common
from hadavin_sdk.llm import protocol as _protocol
from hadavin_sdk.models import Reply, Usage
from tests.contracts.kinds.builtin import ROUTES
from tests.contracts.kinds.llm_wire import AnthropicWire, OpenAICompatWire
from tests.contracts.test_llm import CALL, SCHEMA, TOOLS
from tests.k1b_support import (
    RecordingLLM,
    ScriptedLLM,
    make_bundle,
    submit_not_sure,
    tool_reply,
)
from tests.test_usage_refuse import _bedrock

D = Decimal
UsageMissing = getattr(_protocol, "UsageMissing", None) or type(
    "UsageMissing", (ProviderError,), {"reason": None, "field": None}
)
UnpricedUsage = getattr(_protocol, "UnpricedUsage", None) or type(
    "UnpricedUsage", (UsageMissing,), {}
)
request_bound = getattr(_common, "request_bound", None)
PRICED = ROUTES["default"]  # 3.00 in, 15.00 out per million tokens
CANARY = "canary" + "-" + "value"  # built from parts: never one literal
SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
OLD_TREE = request_bound is None  # the fail-before run: P4a-2 names are absent


def _cost(tin: int, tout: int) -> Decimal:
    exact = (Fraction(tin) * 3 + Fraction(tout) * 15) / 10**6
    return D(math.ceil(exact * 10**8)).scaleb(-8)


def _chat_once(wire, fixture, **kw):
    return wire.serve(fixture).chat(**CALL, tools=TOOLS, **kw)


# ----------------------------------------------------------------------------------------------- C2, C2-fb, C3, C3d, C9


def test_c2_anthropic_cache_fields_null_zero_or_absent_price_as_two_counts():
    wire = AnthropicWire("api")
    try:
        for value in (None, 0, "absent"):
            fx = wire.scenario("tool_call")
            if value != "absent":
                wire.set_usage(fx, cache_write_tokens=value, cache_read_tokens=value)
            reply = _chat_once(wire, fx)
            assert reply.usage == Usage(1200, 40)
            assert reply.cost_usd == D("0.0042")
            assert Fraction(1200 * 3 + 40 * 15, 10**6) == Fraction(D("0.0042"))
    finally:
        wire.close()


def test_c2_bedrock_zero_cache_counts_price_as_two_counts():
    llm, _ = _bedrock(
        lambda b: b["usage"].update(cacheReadInputTokens=0, cacheWriteInputTokens=0),
        scenario="tool_call",
    )
    reply = llm.chat(**CALL, tools=TOOLS)
    assert reply.usage == Usage(1200, 40) and reply.cost_usd == D("0.0042")


def test_c2_fb_a_cached_reply_on_a_flat_route_is_not_returned_at_the_flat_cost():
    wire = AnthropicWire("api")
    try:
        fx = wire.set_usage(wire.scenario("tool_call"), cache_read_tokens=5000)
        with pytest.raises(UnpricedUsage) as err:
            _chat_once(wire, fx)
        assert err.value.field == "cache_read_tokens"
        assert not isinstance(err.value, ProviderExhausted)
    finally:
        wire.close()


@pytest.mark.parametrize(
    ("classes", "field"),
    [
        ({"cache_write_tokens": 1}, "cache_write_tokens"),
        ({"cache_read_tokens": 1}, "cache_read_tokens"),
        ({"cache_write_tokens": 7, "cache_read_tokens": 3}, "cache_write_tokens"),
    ],
)
def test_c3_anthropic_non_zero_cache_class_is_unpriced(classes, field):
    wire = AnthropicWire("api")
    try:
        with pytest.raises(UnpricedUsage) as err:
            _chat_once(wire, wire.set_usage(wire.scenario("tool_call"), **classes))
        assert err.value.reason == "unpriced_class" and err.value.field == field
        assert isinstance(err.value, UsageMissing) and not isinstance(err.value, ProviderExhausted)
        assert len(wire.requests) == 1  # nothing is retried
    finally:
        wire.close()


@pytest.mark.parametrize(
    ("key", "field"),
    [
        ("cacheReadInputTokens", "cache_read_tokens"),
        ("cacheWriteInputTokens", "cache_write_tokens"),
    ],
)
def test_c3_bedrock_non_zero_cache_class_is_unpriced(key, field):
    llm, stub = _bedrock(lambda b: b["usage"].update({key: 4}), scenario="tool_call")
    with pytest.raises(UnpricedUsage) as err:
        llm.chat(**CALL, tools=TOOLS)
    assert err.value.field == field and stub.calls == 1


def _recording(tmp_path, **extra):
    messages = [{"role": "user", "content": "hello"}]
    digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
    data = {"text": "ok", "input_tokens": 1200, "output_tokens": 40, **extra}
    (tmp_path / f"{digest}-1.json").write_text(json.dumps(data), encoding="utf-8")
    return FakeLLM(tmp_path, {"default": PRICED}), messages


@pytest.mark.parametrize("key", ["cache_write_tokens", "cache_read_tokens"])
def test_c3_fake_recording_with_a_non_zero_cache_key_is_unpriced(tmp_path, key):
    llm, messages = _recording(tmp_path, **{key: 9})
    with pytest.raises(UnpricedUsage) as err:
        llm.chat(messages, system="s", route="default")
    assert err.value.field == key
    assert len(llm.calls) == 1


def test_c3_and_c9_zero_cache_keys_load_and_are_dropped_before_the_reply(tmp_path):
    llm, messages = _recording(tmp_path, cache_write_tokens=0, cache_read_tokens=0)
    reply = llm.chat(messages, system="s", route="default")
    assert reply.usage == Usage(1200, 40) and reply.cost_usd == D("0.0042")


def test_c9_old_recording_loads_and_a_thinking_key_is_refused(tmp_path):
    llm, messages = _recording(tmp_path)
    assert llm.chat(messages, system="s", route="default").cost_usd == D("0.0042")
    other = tmp_path / "t"
    other.mkdir()
    llm, messages = _recording(other, thinking_tokens=5)
    with pytest.raises(ValueError):  # `Reply` forbids extra fields: refused loudly, as before
        llm.chat(messages, system="s", route="default")


def test_c9_a_count_at_the_cap_loads_and_above_it_is_invalid(tmp_path):
    cap = defaults.MAX_USAGE_TOKENS_PER_CLASS
    cheap = PRICED.model_copy(
        update={"input_usd_per_mtok": D("0.000001"), "output_usd_per_mtok": D("0.000001")}
    )
    llm, messages = _recording(tmp_path, input_tokens=cap)
    llm.routes = {"default": cheap}
    assert llm.chat(messages, system="s", route="default").input_tokens == cap
    other = tmp_path / "o"
    other.mkdir()
    llm, messages = _recording(other, input_tokens=cap + 1)
    with pytest.raises(UsageMissing) as err:
        llm.chat(messages, system="s", route="default")
    assert err.value.reason == "invalid"


def test_c9_reply_usage_is_read_only_and_equals_the_two_counts():
    r = Reply(input_tokens=7, output_tokens=3, model_id="m")
    assert r.usage == Usage(7, 3)
    assert r.usage.cache_write_tokens == 0 and r.usage.cache_read_tokens == 0
    with pytest.raises((AttributeError, ValueError, TypeError)):
        r.usage = Usage(1, 1)  # type: ignore[misc]


@pytest.mark.parametrize("word", ["service_tier", "speed"])
@pytest.mark.parametrize("ok", [None, "absent", "standard"])
def test_c3d_pricing_words_standard_absent_and_null_are_accepted(word, ok):
    wire = AnthropicWire("api")
    try:
        fx = wire.scenario("tool_call")
        if ok != "absent":
            wire.set_usage(fx, **{word: ok})
        assert _chat_once(wire, fx).cost_usd == D("0.0042")
    finally:
        wire.close()


BAD_WORDS = [
    "priority",
    "batch",
    "Priority",
    "standard ",
    "Standard",
    "x" * 200,
    CANARY,
    7,
    True,
    "fast",
    "",
]


@pytest.mark.parametrize("word", ["service_tier", "speed"])
@pytest.mark.parametrize("bad", BAD_WORDS, ids=lambda v: repr(v)[:12])
def test_c3d_any_other_pricing_word_is_unpriced_and_never_echoed(word, bad):
    wire = AnthropicWire("api")
    try:
        with pytest.raises(UnpricedUsage) as err:
            _chat_once(wire, wire.set_usage(wire.scenario("tool_call"), **{word: bad}))
        assert err.value.field == word
        assert CANARY not in str(err.value) and "x" * 20 not in str(err.value)
    finally:
        wire.close()


def test_c3d_check_facts_directly_and_reply_calls_it():
    check_facts = getattr(
        __import__("hadavin_sdk.llm.pricing", fromlist=["x"]), "check_facts", None
    )
    assert check_facts is not None
    check_facts(PRICED, {})
    check_facts(PRICED, {"service_tier": None, "speed": "standard"})
    with pytest.raises(UnpricedUsage):
        check_facts(PRICED, {"service_tier": "priority"})
    assert "facts" in inspect.signature(_common.reply).parameters


def test_c4_gemini_thoughts_are_counted_once():
    from tests.contracts.kinds.llm_wire import GeminiWire

    wire = GeminiWire()
    try:
        fx = wire.set_usage(wire.scenario("tool_call"), thinking_tokens=93)
        reply = _chat_once(wire, fx)
        assert reply.output_tokens == 40 + 93
    finally:
        wire.close()


# ------------------------------------------------------------------------------------------------------- C7, C14, C12


def _kinds():
    from hadavin_sdk.llm.anthropic import AnthropicLLM
    from hadavin_sdk.llm.bedrock import BedrockLLM
    from hadavin_sdk.llm.gemini import GeminiLLM
    from hadavin_sdk.llm.openai_compat import OpenAICompatLLM

    return AnthropicLLM, BedrockLLM, GeminiLLM, OpenAICompatLLM


def test_c7d_every_kind_declares_its_request_count_whatever_max_attempts_is():
    assert request_bound is not None
    from hadavin_sdk.llm.openai_compat import OpenAICompatLLM

    for attempts in (1, 3):
        llm = OpenAICompatLLM("http://127.0.0.1:1/v1", None, ROUTES, 5.0, attempts)
        assert request_bound(llm) == 2 == defaults.OPENAI_COMPAT_REQUESTS_PER_CHAT
    for cls in _kinds()[:3]:
        assert cls.REQUESTS_PER_CHAT == 1
        assert "REQUESTS_PER_CHAT" in vars(cls)  # in the kind's own class body
    assert FakeLLM.REQUESTS_PER_CHAT == 1 and FakeLLM.max_attempts == 1
    assert "REQUESTS_PER_CHAT" in vars(_kinds()[3])


def test_c7e_request_bound_is_strict():
    assert request_bound is not None
    with pytest.raises(TypeError):
        request_bound(object())
    for bad in (0, -1, True, 2.0, "2"):
        with pytest.raises(ValueError):
            request_bound(SimpleNamespace(REQUESTS_PER_CHAT=bad))
    assert request_bound(SimpleNamespace(REQUESTS_PER_CHAT=4)) == 4


def test_c14b_the_loop_sends_exactly_the_declared_number_of_requests():
    assert request_bound is not None
    wire = OpenAICompatWire()
    try:

        def no_forced_tool():
            fx = wire.scenario("text")
            fx["body"]["choices"][0]["message"]["content"] = "no idea"
            return fx

        llm = wire.serve(no_forced_tool(), no_forced_tool())
        llm.chat(**CALL, output_schema=SCHEMA)
        assert len(wire.requests) == request_bound(llm) == 2
    finally:
        wire.close()
    for wire in (AnthropicWire("api"),):
        try:
            llm = wire.serve(wire.scenario("tool_call"))
            llm.chat(**CALL, tools=TOOLS)
            assert len(wire.requests) == request_bound(llm) == 1
        finally:
            wire.close()


def test_c12_reply_and_answer_shape_and_one_price_formula():
    params = inspect.signature(_common.reply).parameters
    assert "usage" in params and "facts" in params
    assert "tokens" not in params and "sent" not in params
    default = params["facts"].default
    assert len(default) == 0 and not isinstance(default, (dict, list, set))
    fields = {f for f in _common.Answer.__dataclass_fields__}
    assert {"usage", "facts"} <= fields
    assert guard_findings(SRC / "llm") == []


def guard_findings(root: Path) -> list[str]:
    """Class guard: no module under llm/ except pricing.py multiplies a Decimal by a `usd_per_mtok` price."""
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name == "pricing.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                text = ast.unparse(node)
                if "usd_per_mtok" in text and "Decimal" in text:
                    found.append(f"{path.name}:{node.lineno}")
    return found


def test_c12_the_guard_catches_a_planted_formula(tmp_path):
    (tmp_path / "bad.py").write_text(
        "def f(route, n):\n    return Decimal(n) * route.input_usd_per_mtok\n", encoding="utf-8"
    )
    assert guard_findings(tmp_path) == ["bad.py:2"]


# ---------------------------------------------------------------------------------------------------------- C8, C8b, C10

CFG_LLM = {
    "anthropic": "{kind: anthropic, platform: api, api_key_secret_name: k}",
    "bedrock": "{kind: bedrock, region: contract-region-1}",
    "gemini": "{kind: gemini, api_key_secret_name: k}",
    "openai_compat": "{kind: openai_compat, base_url: 'https://example.invalid/v1', api_key_secret_name: k}",
}


def _cfg(tmp_path, llm_line, inp="3.00", out="15.00"):
    from tests.conftest import make_cfg

    root = make_cfg(tmp_path)
    path = root / "config.yaml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("llm: {kind: fake, recorded_dir: ../recorded}", f"llm: {llm_line}")
    text = text.replace('input_usd_per_mtok: "3.00"', f'input_usd_per_mtok: "{inp}"')
    text = text.replace('output_usd_per_mtok: "15.00"', f'output_usd_per_mtok: "{out}"')
    path.write_text(text, encoding="utf-8")
    return root


@pytest.mark.parametrize("kind", sorted(CFG_LLM))
@pytest.mark.parametrize(("inp", "out"), [("0", "15.00"), ("3.00", "0"), ("0", "0")])
def test_c8b_a_zero_price_is_refused_at_load_for_every_real_kind(tmp_path, kind, inp, out):
    with pytest.raises(ConfigError) as err:
        load_config(_cfg(tmp_path, CFG_LLM[kind], inp, out))
    assert "default" in str(err.value) and "15.00" not in str(err.value)


@pytest.mark.parametrize("kind", sorted(CFG_LLM))
def test_c8b_small_prices_load_on_every_real_kind(tmp_path, kind):
    load_config(_cfg(tmp_path, CFG_LLM[kind], "0.000001", "0.000001"))
    other = tmp_path / "n"
    other.mkdir()
    load_config(_cfg(other, CFG_LLM[kind]))


def test_c8b_the_fake_kind_may_carry_a_zero_price(tmp_path):
    cfg = load_config(_cfg(tmp_path, "{kind: fake, recorded_dir: ../recorded}", "0", "0"))
    assert cfg.routes["default"].input_usd_per_mtok == 0


def test_c8_a_bool_price_and_the_empty_string_are_refused():
    for bad in (True, False, ""):
        with pytest.raises(ValueError):
            Route(model_id="m", input_usd_per_mtok=bad, output_usd_per_mtok=D(1), max_tokens=10)


def test_c10_config_hash_is_the_same_as_before_for_valid_prices(tmp_path):
    from hadavin_sdk.registry import load_registry

    cfg = _cfg(tmp_path, "{kind: fake, recorded_dir: ../recorded}", "3.00", "0.10")
    h = load_registry(load_config(cfg)).config_hash("test-agent")
    assert h == PINNED_HASH_3_00_0_10


PINNED_HASH_3_00_0_10 = (
    "1563712d4c46c4bc717ce705e800e50ebe5575930f7707d47c58c3497f615a99"  # computed on the base tree
)


# ------------------------------------------------------------------------------------------------------ C13 k1b bookings

ROUTE = Route(model_id="m", input_usd_per_mtok=D("3"), output_usd_per_mtok=D("15"), max_tokens=1024)


def _bytes(system: str, messages, tools=TOOL_SPECS) -> int:
    """The prompt formula of `loop._dumps`, written out here (not imported)."""
    text = (
        system
        + json.dumps(messages, sort_keys=True, ensure_ascii=False)
        + json.dumps(tools, sort_keys=True, ensure_ascii=False)
    )
    return len(text.encode("utf-8", "surrogatepass"))


def _w(prompt_bytes: int, route: Route = ROUTE) -> Fraction:
    return (
        prompt_bytes * Fraction(route.input_usd_per_mtok)
        + route.max_tokens * Fraction(route.output_usd_per_mtok)
    ) / 10**6


class Stub:
    """Declares its request count and attempts, records the messages it receives, then raises."""

    def __init__(self, exc, *declare):
        self.exc, self.messages = exc, []
        if declare:
            self.REQUESTS_PER_CHAT, self.max_attempts = declare

    def chat(self, messages, **kw):
        self.messages.append(copy.deepcopy(messages))
        raise self.exc


@pytest.fixture
def bundle(tmp_path):
    make_bundle(tmp_path / "b", "case-001")
    return load_bundles(tmp_path / "b")[0]


def _drive(llm, bundle, system="s", route_prices=ROUTE, clock=None, timeout_s=300):
    from hadavin_sdk.guard.injection import RegexDetector

    budget = loop.Budget(D("1000"))
    kw = {"clock": clock} if clock else {}
    out = loop.run_case(
        llm, system=system, route="default", route_prices=route_prices, bundle=bundle,
        detector=RegexDetector(0.5), budget=budget, max_steps=4, max_tool_calls=4, timeout_s=timeout_s, **kw,
    )  # fmt: skip
    return out, budget


@pytest.fixture
def padded(bundle):
    """A system text that makes the prompt of the first call exactly 4,000 bytes (ASSERTED before any booking)."""
    probe = Stub(ProviderError("x"), 1, 1)
    _drive(probe, bundle, system="")
    base = _bytes("", probe.messages[0])
    system = "s" * (4000 - base)
    assert _bytes(system, probe.messages[0]) == 4000, (
        "first message plus tool specs exceed 4,000 bytes"
    )
    return system


def _spent(budget) -> Fraction:
    return Fraction(budget.spent)


W = _w(4000)
assert W == Fraction(27360, 10**6)


def _um(cause=None):
    err = UsageMissing("absent", "usage")
    err.__cause__ = cause
    return err


def _booked(stub, bundle, padded, **kw):
    out, budget = _drive(stub, bundle, system=padded, **kw)
    return out, _spent(budget)


def test_c13a_usage_missing_one_request_one_attempt_books_w(bundle, padded):
    out, spent = _booked(Stub(_um(), 1, 1), bundle, padded)
    assert spent == W
    assert (out.status, out.stop_reason, out.halt) == ("error", "aborted", "aborted")


def test_c13b_b2_the_factor_is_requests_times_attempts(bundle, padded):
    assert _booked(Stub(_um(), 2, 1), bundle, padded)[1] == 2 * W
    out, spent = _booked(Stub(_um(), 2, 3), bundle, padded)
    assert spent == 6 * W == Fraction(164160, 10**6)
    assert (out.status, out.stop_reason, out.halt) == ("error", "aborted", "aborted")


class Hung:
    def __init__(self, *declare):
        self.messages, self.release = [], threading.Event()
        if declare:
            self.REQUESTS_PER_CHAT, self.max_attempts = declare

    def chat(self, messages, **kw):
        self.messages.append(copy.deepcopy(messages))  # recorded BEFORE waiting
        self.release.wait(10)
        raise ProviderError("late")


@pytest.mark.parametrize(("declare", "factor"), [((2, 3), 6), ((1, 1), 1)])
def test_c13c_an_abandoned_call_books_the_whole_call_maximum(
    monkeypatch, bundle, padded, declare, factor
):
    monkeypatch.setattr(loop, "MIN_WAIT_S", 0.05)
    stub = Hung(*declare)
    ticks = iter([0, 0, 299.99] + [1000] * 50)
    try:
        out, budget = _drive(stub, bundle, system=padded, clock=lambda: next(ticks))
    finally:
        stub.release.set()
    assert (out.status, out.stop_reason, out.halt) == ("timeout", "call_timeout", "aborted")
    assert _spent(budget) == factor * W


def test_c13d_a_plain_provider_error_books_the_whole_call_maximum(bundle, padded):
    out, spent = _booked(Stub(ProviderError("bad key"), 2, 3), bundle, padded)
    assert spent == 6 * W
    assert (out.status, out.stop_reason, out.halt) == ("error", "aborted", "aborted")


def test_c13d2_provider_exhausted_books_the_whole_call_maximum(bundle, padded):
    exc = ProviderExhausted("timed out")
    exc.__cause__ = TimeoutError()
    out, spent = _booked(Stub(exc, 2, 3), bundle, padded)
    assert spent == 6 * W
    assert (out.status, out.stop_reason) == ("error", "provider_exhausted") and out.halt is None


def test_c13e_unpriced_usage_is_booked_as_a_usage_missing(bundle, padded):
    out, spent = _booked(Stub(UnpricedUsage("cache_read_tokens"), 1, 1), bundle, padded)
    assert spent == W and out.halt == "aborted"


@pytest.mark.parametrize(
    "exc",
    [
        lambda: ProviderError("x"),
        lambda: _um(),
        lambda: ProviderExhausted("x"),
    ],
)
def test_c13f_no_prices_books_nothing_and_raises_nothing(bundle, padded, exc):
    out, spent = _booked(Stub(exc(), 2, 3), bundle, padded, route_prices=None)
    assert spent == 0 and out.status == "error"


def test_c13f_an_abandoned_call_without_prices_books_nothing(monkeypatch, bundle, padded):
    monkeypatch.setattr(loop, "MIN_WAIT_S", 0.05)
    stub = Hung(2, 3)
    ticks = iter([0, 0, 299.99] + [1000] * 50)
    try:
        out, budget = _drive(
            stub, bundle, system=padded, route_prices=None, clock=lambda: next(ticks)
        )
    finally:
        stub.release.set()
    assert out.status == "timeout" and budget.spent == 0


def _timeout_with(stub, monkeypatch, bundle, padded):
    monkeypatch.setattr(loop, "MIN_WAIT_S", 0.05)
    ticks = iter([0, 0, 299.99] + [1000] * 50)
    try:
        return _drive(stub, bundle, system=padded, clock=lambda: next(ticks))
    finally:
        stub.release.set()


def test_c13g1_an_object_that_declares_nothing_is_booked_the_fallbacks(monkeypatch, bundle, padded):
    class Plain(Hung):
        REQUESTS_PER_CHAT = None  # type: ignore[assignment]

    stub = Plain()
    del Plain.REQUESTS_PER_CHAT  # a plain object with only `chat`
    out, budget = _timeout_with(stub, monkeypatch, bundle, padded)
    factor = defaults.CHARGE_FALLBACK_REQUESTS * defaults.CHARGE_FALLBACK_ATTEMPTS
    assert (out.status, out.halt) == ("timeout", "aborted")
    assert _spent(budget) == factor * W == Fraction(547200, 10**6)


def test_c13g2_a_bad_declared_value_is_booked_the_fallback_for_that_factor(
    monkeypatch, bundle, padded
):
    _out, budget = _timeout_with(Hung(2, 0), monkeypatch, bundle, padded)
    assert _spent(budget) == 2 * defaults.CHARGE_FALLBACK_ATTEMPTS * W


def test_c13g_charge_factor_is_total():
    for bad in (None, 0, -1, True, 2.0, "2"):
        assert loop._charge_factor(SimpleNamespace(REQUESTS_PER_CHAT=bad, max_attempts=bad)) == (
            defaults.CHARGE_FALLBACK_REQUESTS * defaults.CHARGE_FALLBACK_ATTEMPTS
        )
    assert (
        loop._charge_factor(object())
        == defaults.CHARGE_FALLBACK_REQUESTS * defaults.CHARGE_FALLBACK_ATTEMPTS
    )


def test_c13h_the_fallbacks_are_not_below_any_declaration():
    from hadavin_sdk.backends.table import _LLMSettings

    declared = [cls.REQUESTS_PER_CHAT for cls in _kinds()] + [FakeLLM.REQUESTS_PER_CHAT]
    declared += [
        ScriptedLLM.REQUESTS_PER_CHAT,
        RecordingLLM.REQUESTS_PER_CHAT.fget(SimpleNamespace(inner=ScriptedLLM([]))),
    ]
    assert defaults.CHARGE_FALLBACK_REQUESTS >= max(declared)
    field = _LLMSettings.model_fields["max_attempts"]
    le = next(m.le for m in field.metadata if hasattr(m, "le"))
    assert defaults.CHARGE_FALLBACK_ATTEMPTS >= le
    assert FakeLLM.max_attempts == 1
    assert (ScriptedLLM.REQUESTS_PER_CHAT, ScriptedLLM.max_attempts) == (1, 1)


def test_c13h_recording_llm_forwards_the_inner_declarations(tmp_path):
    rec = RecordingLLM(ScriptedLLM([]), tmp_path)
    assert (rec.REQUESTS_PER_CHAT, rec.max_attempts) == (1, 1)
    inner = ScriptedLLM([])
    inner.REQUESTS_PER_CHAT, inner.max_attempts = 2, 3
    rec = RecordingLLM(inner, tmp_path)
    assert (rec.REQUESTS_PER_CHAT, rec.max_attempts) == (2, 3)


class _Coded(Exception):
    def __init__(self, code=None):
        self.code = code


def _chain(outer, cause):
    outer.__cause__ = cause
    return outer


def _exhausted(cause):
    return _chain(ProviderExhausted("x"), cause)


@pytest.mark.parametrize(
    "exc",
    [
        lambda: _um(ProviderError("parse failure")),  # j1
        lambda: _um(_exhausted(TimeoutError())),  # j2
        lambda: _um(_chain(ProviderExhausted("503"), _Coded(503))),  # j3
        lambda: _um(_chain(ProviderError("400"), _Coded(400))),  # j4 (i)
        lambda: _um(_exhausted(urllib.error.URLError(ConnectionRefusedError()))),  # j4 (ii)
        lambda: _um(_chain(ProviderError("x"), _Coded(408))),  # j6
        lambda: _um(_chain(ProviderError("x"), _Coded(429))),
        lambda: _um(ProviderError("an unknown failure")),
        lambda: _um(None),  # j7 (1)
        lambda: _um(__import__("decimal").InvalidOperation()),  # j7 (2)
    ],
    ids=[
        "j1",
        "j2",
        "j3",
        "j4i",
        "j4ii",
        "j6-408",
        "j6-429",
        "j6-unknown",
        "j7-nocause",
        "j7-decimal",
    ],
)
def test_c13j_a_failed_request_two_books_six_w_whatever_the_cause(bundle, padded, exc):
    out, spent = _booked(Stub(exc(), 2, 3), bundle, padded)
    assert spent == 6 * W == Fraction(164160, 10**6)  # equality: below fails, above fails
    assert (out.status, out.stop_reason, out.halt) == ("error", "aborted", "aborted")


def test_c13k_a_lone_surrogate_in_a_tool_call_input_does_not_crash_the_booking(bundle):
    s = json.loads('"\\ud800"')
    seen: list = []

    def step2(messages):
        seen.append(copy.deepcopy(messages))
        raise UsageMissing("absent", "usage")

    out, budget = _drive(
        ScriptedLLM([tool_reply("no_such_tool", q=s), step2]), bundle, system="sys"
    )
    assert (out.status, out.stop_reason, out.halt) == ("error", "aborted", "aborted")
    assert _spent(budget) == _w(_bytes("sys", seen[0]))
    assert any(s in json.dumps(m, ensure_ascii=False) for m in seen[0])


def test_c13k_clause_2_the_audit_hash_of_a_tool_name_with_a_lone_surrogate(tmp_path, cfg_dir):
    from hadavin_sdk.k1b import replay as k1b_replay
    from tests.test_k1b_replay import Env

    env = Env(tmp_path, cfg_dir)
    s = json.loads('"\\ud800"')
    res = env.run(ScriptedLLM([tool_reply(s), submit_not_sure(), submit_not_sure()]))
    assert res.exit_code == 0
    events = [e for e in env.sink.events() if e.operation == "hard_check_a"]
    assert len(events) == 1 and events[0].error_code == "invalid_name"
    assert events[0].inputs_hash == hashlib.sha256(s.encode("utf-8", "surrogatepass")).hexdigest()
    assert k1b_replay._sha("abc") == hashlib.sha256(b"abc").hexdigest()


# ---------------------------------------------------------------------------------------------------- C13p, C13q


def test_c13p_the_pure_function_literals():
    route = ROUTE
    got = loop.worst_case_usd(route, "s" * 296, [], tools=[])
    assert got == D("0.016260")
    assert loop.worst_case_usd(route, "s" * 296, [], tools=[], requests=2) == D("0.032520")
    assert loop.worst_case_usd(route, "s" * 296, [], tools=[], requests=6) == D("0.097560")
    assert got == _exact8(_w(300))


def _exact8(x: Fraction) -> Decimal:
    return D(math.ceil(x * 10**8)).scaleb(-8)


def test_c13p_clause_2_the_rounding_goes_up_once_on_the_exact_product():
    route = Route(
        model_id="m", input_usd_per_mtok=D("3.123457"), output_usd_per_mtok=D("15"), max_tokens=1024
    )
    exact = _w(301, route)
    assert exact != _exact8(exact)  # not whole at 8 decimals: the direction is seen
    one = loop.worst_case_usd(route, "s" * 297, [], tools=[])
    three = loop.worst_case_usd(route, "s" * 297, [], tools=[], requests=3)
    assert one == D("0.01630017") == _exact8(exact)
    assert three == D("0.04890049") == _exact8(exact * 3)


def test_c13q_bytes_not_characters_and_the_surrogate_counts_three_bytes():
    assert loop.worst_case_usd(ROUTE, "漢" * 10_000, [], tools=[]) == D("0.105372")
    s = json.loads('"\\ud800"')
    assert loop.worst_case_usd(ROUTE, s, [], tools=[]) == D("0.015381")


# ---------------------------------------------------------------------------------------------------------- C18


def _replay_env(tmp_path, cfg_dir):
    from tests.test_k1b_replay import Env

    return Env(tmp_path, cfg_dir)


def _listing(env):
    return sorted(
        p.relative_to(env.tmp).as_posix()
        for p in env.tmp.rglob("*")
        if "out" in p.parts[len(env.tmp.parts) :]
    )


def test_c18a_a_real_kind_label_is_refused_before_anything_is_written(tmp_path, cfg_dir):
    env = _replay_env(tmp_path, cfg_dir)
    before = _listing(env)
    with pytest.raises(ConfigError) as err:
        env.run(ScriptedLLM([]), llm_kind="anthropic")
    assert str(err.value) == "k1b replay runs only on the fake llm kind in v1"
    assert _listing(env) == before and not env.out.exists()
    assert env.run(ScriptedLLM([submit_not_sure()] * 2), llm_kind="fake").exit_code == 0


def test_c18b_a_detector_kind_other_than_regex_and_llm_judge_is_refused(tmp_path, cfg_dir):
    import dataclasses

    from hadavin_sdk.backends.table import GuardrailSettings

    env = _replay_env(tmp_path, cfg_dir)
    guard = GuardrailSettings(
        kind="bedrock_guardrail", guardrail_id="g", guardrail_version="1", region="r"
    )
    backends = env.reg.config.backends.model_copy(update={"detector": (guard,)})
    reg = dataclasses.replace(
        env.reg, config=env.reg.config.model_copy(update={"backends": backends})
    )
    with pytest.raises(ConfigError) as err:
        env.run(ScriptedLLM([]), reg=reg)
    assert str(err.value) == "k1b replay runs only the regex and llm_judge detector kinds in v1"
    assert not env.out.exists()
    assert env.run(ScriptedLLM([submit_not_sure()] * 2)).exit_code == 0  # the regex detector runs


def test_c18c_a_network_object_under_the_fake_label_is_refused(tmp_path, cfg_dir):
    from hadavin_sdk.llm.common import NetworkLLM

    class Sneaky(NetworkLLM):
        def chat(self, *a, **kw):
            raise AssertionError("must not be called")

    env = _replay_env(tmp_path, cfg_dir)
    with pytest.raises(ConfigError) as err:
        env.run(
            object.__new__(Sneaky), llm_kind="fake"
        )  # skips the constructor: only the type matters
    assert str(err.value) == "k1b replay runs only on the fake llm kind in v1"
    assert not env.out.exists()


# ---------------------------------------------------------------------------------------------------------- C16


def _answered_without_the_forced_tool(wire):
    fx = wire.scenario("text")
    fx["body"]["choices"][0]["message"]["content"] = "no idea"
    return wire.set_tokens(fx, 300, 7)


def _req2_failures(wire):
    throttle = wire.scenario("throttle")
    bad_request = {"status": 400, "body": {"error": {"message": "bad request", "code": "invalid"}}}
    unparsable = {"status": 200, "body": {"choices": []}}
    return {
        "i-exhausted": ([throttle] * 3, ProviderExhausted),
        "ii-http-400": ([bad_request], ProviderError),
        "iii-unparsable": ([unparsable], ProviderError),
    }


@pytest.mark.parametrize("case", ["i-exhausted", "ii-http-400", "iii-unparsable"])
def test_c16_a_failed_request_two_is_a_usage_missing_chained_from_the_real_error(case):
    wire = OpenAICompatWire()
    try:
        failures, cause_type = _req2_failures(wire)[case]
        llm = wire.serve(_answered_without_the_forced_tool(wire), *failures)
        with pytest.raises(UsageMissing) as err:
            llm.chat(**CALL, output_schema=SCHEMA)
        exc = err.value
        assert type(exc) is UsageMissing and (exc.reason, exc.field) == ("absent", "usage")
        assert isinstance(exc.__cause__, cause_type)
        if cause_type is ProviderError:
            assert not isinstance(exc.__cause__, ProviderExhausted)
        assert str(exc) == "usage missing: absent (usage)"
        assert len(wire.requests) >= 2
    finally:
        wire.close()


def test_c16_iv_a_usage_missing_of_request_two_is_not_wrapped():
    wire = OpenAICompatWire()
    try:
        second = wire.scenario("text")
        second["body"]["choices"][0]["message"]["content"] = "still none"
        wire.without_usage(second)
        llm = wire.serve(_answered_without_the_forced_tool(wire), second)
        with pytest.raises(UsageMissing) as err:
            llm.chat(**CALL, output_schema=SCHEMA)
        assert type(err.value) is UsageMissing and err.value.__cause__ is None
        assert len(wire.requests) == 2
    finally:
        wire.close()


@pytest.mark.parametrize("case", ["i-exhausted", "ii-http-400", "iii-unparsable"])
def test_c16_counter_request_one_failing_keeps_its_original_error(case):
    wire = OpenAICompatWire()
    try:
        failures, cause_type = _req2_failures(wire)[case]
        llm = wire.serve(*failures)
        with pytest.raises(ProviderError) as err:
            llm.chat(**CALL, output_schema=SCHEMA)
        assert not isinstance(err.value, UsageMissing) and isinstance(err.value, cause_type)
    finally:
        wire.close()

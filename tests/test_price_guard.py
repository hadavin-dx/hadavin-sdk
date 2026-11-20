"""H6 of the price constraint: a route whose price is not a positive finite Decimal within the config rule is
refused when a real (non-fake) llm client is built and again before each call, even if the Route skipped the config
check (`model_construct`, or a valid `Route(...)` with price 0 as the ask-your-data demo config builds it). The fake
client is exempt. Every real kind is covered, so a kind that skips `NetworkLLM.__init__` fails here."""

from __future__ import annotations

import importlib
from decimal import Decimal
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.config import Route
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm import common
from hadavin_sdk.llm.common import NetworkLLM
from hadavin_sdk.llm.fake import FakeLLM

IN, OUT = "input_usd_per_mtok", "output_usd_per_mtok"
CEIL = defaults.MAX_ROUTE_PRICE_USD_PER_MTOK
BAD = [
    Decimal(0),
    Decimal("-0"),
    Decimal(-1),
    Decimal("NaN"),
    Decimal("sNaN"),
    Decimal("Infinity"),
    Decimal("-Infinity"),
    Decimal(CEIL) + 1,
    Decimal("1E-30"),  # the config rule allows at most 6 decimals
    Decimal("0.0000001"),
]


class _Sub(Decimal):
    pass


# Every kind: (module, class name, builder from routes). A new NetworkLLM kind makes the enumeration test fail
# until it is listed here.
KINDS = {
    "anthropic": ("AnthropicLLM", lambda c, r: c(object(), r, 3)),
    "bedrock": ("BedrockLLM", lambda c, r: c(object(), r, 3)),
    "gemini": ("GeminiLLM", lambda c, r: c(lambda: "k", r, 30.0, 3)),
    "openai_compat": (
        "OpenAICompatLLM",
        lambda c, r: c("https://llm.example/v1", None, r, 30.0, 3),
    ),
}


def kind(name):
    cls_name, build = KINDS[name]
    cls = getattr(importlib.import_module(f"hadavin_sdk.llm.{name}"), cls_name)
    return lambda routes: build(cls, routes)


def route(**over):
    v = {"model_id": "m-1", IN: Decimal(3), OUT: Decimal(15), "max_tokens": 100} | over
    return Route.model_construct(**v)


def test_every_real_kind_is_listed():
    for name in KINDS:
        importlib.import_module(f"hadavin_sdk.llm.{name}")
    found = {
        c.__name__
        for c in NetworkLLM.__subclasses__()
        if c.__module__.startswith("hadavin_sdk.llm.")
    }
    assert found == {cls for cls, _ in KINDS.values()}


@pytest.mark.parametrize("name", KINDS)
@pytest.mark.parametrize("field", [IN, OUT])
@pytest.mark.parametrize("bad", BAD, ids=str)
def test_every_real_kind_refuses_a_bad_price_at_build(name, field, bad):
    with pytest.raises(ConfigError, match=field):
        kind(name)({"r": route(**{field: bad})})


@pytest.mark.parametrize("name", KINDS)
def test_every_real_kind_accepts_prices_in_range(name):
    for p in (Decimal("0.000001"), Decimal(3), Decimal(CEIL)):
        assert kind(name)({"r": route(**{IN: p, OUT: p})}).routes["r"].model_id == "m-1"


@pytest.mark.parametrize("field", [IN, OUT])
@pytest.mark.parametrize("bad", [0, 1.5, "3", None, True, _Sub(3)], ids=repr)
def test_a_price_that_is_not_a_plain_decimal_is_refused(field, bad):
    with pytest.raises(ConfigError, match=field):
        NetworkLLM({"r": route(**{field: bad})}, 3)


def test_a_valid_zero_price_route_as_the_demo_config_builds_it_is_refused():
    r = Route(model_id="m-1", input_usd_per_mtok=0, output_usd_per_mtok=1, max_tokens=10)
    with pytest.raises(ConfigError, match=IN):
        kind("anthropic")({"demo": r})


def test_the_error_names_the_route_and_field_and_never_the_price():
    with pytest.raises(ConfigError) as e:
        NetworkLLM({"ok": route(), "bad-route": route(**{OUT: Decimal("-7.123456")})}, 3)
    assert "bad-route" in str(e.value) and OUT in str(e.value) and "7.123456" not in str(e.value)


@pytest.mark.parametrize("name", KINDS)
def test_routes_swapped_after_build_are_refused_before_the_call(name):
    llm = kind(name)({"r": route()})
    llm.routes = {"r": route(**{IN: Decimal(0)})}
    with pytest.raises(ConfigError, match=IN):
        llm.chat([{"role": "user", "content": "q"}], system="s", route="r")


class _Probe(NetworkLLM):
    def _chat(self, route, system, turns, specs, forced, output_schema):
        self.seen = route
        return "reply"


def _chat(llm, name="r"):
    return llm.chat([{"role": "user", "content": "q"}], system="s", route=name)


def test_the_route_checked_is_the_route_priced(monkeypatch):
    good, other = route(), route(**{IN: Decimal(0)})
    llm = _Probe({"r": good}, 3)
    real = common.priced

    def swap_after_check(routes):
        out = real(routes)
        llm.routes = {"r": other}  # a swap between the check and the use
        return out

    monkeypatch.setattr(common, "priced", swap_after_check)
    assert _chat(llm) == "reply" and llm.seen is good


def test_only_the_called_route_is_checked():
    llm = _Probe({"ok": route(), "bad": route()}, 3)
    llm.routes["bad"] = route(**{OUT: Decimal(-1)})
    assert _chat(llm, "ok") == "reply"
    with pytest.raises(ConfigError, match="bad"):
        _chat(llm, "bad")


@pytest.mark.parametrize("bad", BAD, ids=str)
def test_fake_client_is_exempt(bad, tmp_path: Path):
    r = route(**{IN: bad, OUT: bad})
    assert FakeLLM(tmp_path, {"r": r}).routes["r"] is r

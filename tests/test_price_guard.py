"""H6 of the price constraint: a route whose price is not a positive finite Decimal within the ceiling is refused
when a real (non-fake) llm client is built, even if the Route skipped the config check (`model_construct`, or a
valid `Route(...)` with price 0 as the ask-your-data demo config builds it). The fake client is exempt."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.config import Route
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm.anthropic import AnthropicLLM
from hadavin_sdk.llm.common import NetworkLLM
from hadavin_sdk.llm.fake import FakeLLM

IN, OUT = "input_usd_per_mtok", "output_usd_per_mtok"
CEIL = defaults.MAX_ROUTE_PRICE_USD_PER_MTOK
BAD = [
    Decimal(0),
    Decimal("-0"),
    Decimal(-1),
    Decimal("NaN"),
    Decimal("Infinity"),
    Decimal(CEIL) + 1,
]


def route(**over):
    v = {"model_id": "m-1", IN: Decimal(3), OUT: Decimal(15), "max_tokens": 100} | over
    return Route.model_construct(**v)


@pytest.mark.parametrize("field", [IN, OUT])
@pytest.mark.parametrize("bad", BAD, ids=str)
def test_real_client_refuses_a_bad_price(field, bad):
    with pytest.raises(ConfigError, match=field):
        AnthropicLLM(object(), {"r": route(**{field: bad})}, 3)


@pytest.mark.parametrize("bad", [0, 1.5, "3", None])
def test_real_client_refuses_a_price_that_is_not_a_decimal(bad):
    with pytest.raises(ConfigError):
        NetworkLLM({"r": route(**{IN: bad})}, 3)


def test_a_valid_zero_price_route_as_the_demo_config_builds_it_is_refused():
    r = Route(model_id="m-1", input_usd_per_mtok=0, output_usd_per_mtok=1, max_tokens=10)
    with pytest.raises(ConfigError, match=IN):
        AnthropicLLM(object(), {"demo": r}, 3)


def test_the_error_names_the_route_and_never_the_price():
    with pytest.raises(ConfigError) as e:
        NetworkLLM({"ok": route(), "bad-route": route(**{OUT: Decimal("-7.25")})}, 3)
    assert "bad-route" in str(e.value) and "7.25" not in str(e.value)


@pytest.mark.parametrize("p", [Decimal("0.000001"), Decimal(3), Decimal(CEIL)])
def test_real_client_accepts_prices_in_range(p):
    assert NetworkLLM({"r": route(**{IN: p, OUT: p})}, 3).routes["r"].model_id == "m-1"


@pytest.mark.parametrize("bad", BAD, ids=str)
def test_fake_client_is_exempt(bad, tmp_path: Path):
    r = route(**{IN: bad, OUT: bad})
    assert FakeLLM(tmp_path, {"r": r}).routes["r"] is r

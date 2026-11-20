"""Step C, hostile review 2 fixes: H2 (a low Decimal context precision), H3 (strict price text), H5 (route names
escaped in refusals)."""

from __future__ import annotations

from decimal import Decimal, localcontext
from pathlib import Path

import pytest
import yaml

from hadavin_sdk.config import Route, load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm import common
from tests.test_k3_pilot_env import pilot_cfg


def _edit(d: Path, mut) -> Path:
    p = d / "config.yaml"
    data = yaml.safe_load(p.read_text())
    mut(data)
    p.write_text(yaml.safe_dump(data))
    return d


def _route(**kw) -> Route:
    base = {
        "model_id": "m",
        "input_usd_per_mtok": "1",
        "output_usd_per_mtok": "1",
        "max_tokens": 10,
    }
    return Route(**{**base, **kw})


def test_h2_low_precision_does_not_leak_invalid_operation_from_load_config(tmp_path):
    d = _edit(
        pilot_cfg(tmp_path),
        lambda x: x["routes"]["default"].__setitem__("input_usd_per_mtok", "123456.123456"),
    )
    with localcontext() as ctx:
        ctx.prec = 6
        cfg = load_config(d)  # a legal price must load whatever the caller's precision
    assert cfg.routes["default"].input_usd_per_mtok == Decimal("123456.123456")


def test_h2_low_precision_route_direct(tmp_path):
    with localcontext() as ctx:
        ctx.prec = 3
        r = _route(input_usd_per_mtok="123456.123456")
    assert r.input_usd_per_mtok == Decimal("123456.123456")
    with localcontext() as ctx:
        ctx.prec = 3
        with pytest.raises(ValueError, match="6 decimal"):
            _route(input_usd_per_mtok="1.0000001")


def test_h2_load_config_turns_arithmetic_error_into_config_error(tmp_path, monkeypatch):
    from hadavin_sdk import config

    def boom(*a, **k):
        raise ArithmeticError("boom")

    monkeypatch.setattr(config, "Config", boom)
    with pytest.raises(ConfigError, match="price"):
        load_config(pilot_cfg(tmp_path))


def test_h2_worst_case_is_not_rounded_by_a_low_caller_precision():
    route = _route(
        input_usd_per_mtok="123456.123456", output_usd_per_mtok="999999.999999", max_tokens=4093
    )
    exact = common.worst_case_usd(route, "s" * 100, [{"role": "user", "content": "x"}])
    with localcontext() as ctx:
        ctx.prec = 4
        low = common.worst_case_usd(route, "s" * 100, [{"role": "user", "content": "x"}])
    assert low == exact


def test_h2_reply_cost_is_not_rounded_by_a_low_caller_precision():
    route = _route(input_usd_per_mtok="123456.123456", output_usd_per_mtok="999999.999999")
    args = {
        "text": "abc",
        "calls": [],
        "tokens": (1234567, 7654321),
        "stop": "end_turn",
        "started": 0.0,
        "sent": "x",
    }
    exact = common.reply(route, **args).cost_usd
    with localcontext() as ctx:
        ctx.prec = 4
        low = common.reply(route, **args).cost_usd
    assert low == exact


def test_h2_fake_cost_is_not_rounded_by_a_low_caller_precision(tmp_path):
    from hadavin_sdk.llm.fake import FakeLLM

    sig = FakeLLM.__init__.__code__.co_varnames[: FakeLLM.__init__.__code__.co_argcount]
    assert "routes" in sig
    import hashlib
    import json

    rec = tmp_path / "rec"
    rec.mkdir()
    messages = [{"role": "user", "content": "hi"}]
    digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
    (rec / f"{digest}-1.json").write_text(
        json.dumps(
            {
                "text": "t",
                "input_tokens": 1234567,
                "output_tokens": 7654321,
                "stop_reason": "end_turn",
            }
        )
    )
    route = _route(input_usd_per_mtok="123456.123456", output_usd_per_mtok="999999.999999")

    def cost():
        llm = (
            FakeLLM(rec, {"r": route})
            if sig[1:3] == ("recorded_dir", "routes")
            else FakeLLM(**{sig[1]: rec, "routes": {"r": route}})
        )
        return llm.chat(messages, system="s", route="r").cost_usd

    exact = cost()
    with localcontext() as ctx:
        ctx.prec = 4
        assert cost() == exact


@pytest.mark.parametrize("text", ["5_0", " 5 ", "5\n", "١٢", "１２", "1,5"])
def test_h3_price_text_must_be_ascii_digits_and_one_point(tmp_path, text):
    d = _edit(
        pilot_cfg(tmp_path),
        lambda x: x["routes"]["default"].__setitem__("output_usd_per_mtok", text),
    )
    with pytest.raises(
        ConfigError, match=r"routes\.default\.output_usd_per_mtok|output_usd_per_mtok"
    ):
        load_config(d)


@pytest.mark.parametrize("text", ["5", "5.5", "0.000001", ".5", "1000000"])
def test_h3_plain_ascii_prices_still_load(tmp_path, text):
    d = _edit(
        pilot_cfg(tmp_path),
        lambda x: x["routes"]["default"].__setitem__("input_usd_per_mtok", text),
    )
    assert load_config(d).routes["default"].input_usd_per_mtok == Decimal(text)


def test_h3_error_names_field_not_value(tmp_path):
    d = _edit(
        pilot_cfg(tmp_path),
        lambda x: x["routes"]["default"].__setitem__("input_usd_per_mtok", "sk-SECRET_1"),
    )
    with pytest.raises(ConfigError) as ei:
        load_config(d)
    assert "SECRET" not in str(ei.value)
    assert "input_usd_per_mtok" in str(ei.value)


def test_h5_route_name_is_escaped_in_the_refusal(tmp_path):
    def mut(x):
        x["routes"]["sk-SECRET\nFORGED: line"] = dict(
            x["routes"]["default"], output_usd_per_mtok="0"
        )

    with pytest.raises(ConfigError) as ei:
        load_config(_edit(pilot_cfg(tmp_path), mut))
    text = str(ei.value)
    assert "\nFORGED" not in text
    assert "\\nFORGED" in text

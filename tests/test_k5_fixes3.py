"""Fixes from the third code review: M-B the secret scrub in tool results
normalised before any cap, m-A nested identifier flags for every action, m-B aggregate expansion in redact_value, m-C bare
redact() callers cut their input."""

from __future__ import annotations

import pytest
import yaml

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick as tick_mod
from tests.k5_support import ACTION, BigNormalises, k5_cfg

SECRET = "Zx9Qw+" + "ab12=Pq-secret"  # a fake, built from parts

# --- M-B: the secret scrub decodes, then normalises: that is work too ---------------------------------------------------------------


def test_a_tool_result_with_a_secret_and_an_expanding_text_is_refused_before_the_work(monkeypatch):
    """87,000 U+FDFA with a secret handed out took 13.6 s (the decode view was normalised per secret form)."""
    big = BigNormalises(monkeypatch)
    with pytest.raises(runmap.InputTooLarge):
        tools_mod.prepare_output("ﷺ" * 87000, {}, defaults.MAX_REDACT_CHARS, [SECRET])
    assert big.calls == []


def test_percent_encoded_expanding_text_is_refused_after_the_decode(monkeypatch):
    """`%EF%B7%BA` is 9 characters; decoded it is U+FDFA, which NFKC makes 18: the check runs on the DECODED text."""
    raw = "%EF%B7%BA" * 29000  # 261,000 characters, 29,000 after decoding, 522,000 after NFKC
    assert len(raw) < defaults.MAX_REDACT_CHARS
    big = BigNormalises(monkeypatch)
    with pytest.raises(runmap.InputTooLarge):
        tools_mod.prepare_output(raw, {}, defaults.MAX_REDACT_CHARS, [SECRET])
    assert big.calls == []


def test_the_decoded_view_is_computed_once_not_once_per_secret_form(monkeypatch):
    calls = []
    real = tools_mod._decoded_readings
    monkeypatch.setattr(tools_mod, "_decoded_readings", lambda text: calls.append(1) or real(text))
    out = tools_mod.prepare_output("a plain log line " * 50, {}, 16384, [SECRET, SECRET + "-two"])
    assert out.startswith("a plain log line")
    assert len(calls) == 1


def test_a_secret_behind_an_encoding_layer_is_still_scrubbed():
    hidden = "".join(f"%{b:02X}" for b in SECRET.encode())
    out = tools_mod.prepare_output(f"token {hidden} end", {}, 16384, [SECRET])
    assert SECRET not in out and "SECRET_REDACTED" in out


# --- m-A: a nested identifier flag is refused for every action, tooled or not ------------------------------------------------------------

NESTED = {
    "input_schema": {
        "type": "object",
        "required": ["target"],
        "additionalProperties": False,
        "properties": {
            "target": {
                "type": "object",
                "identifier": False,
                "properties": {"host": {"type": "string", "identifier": True}},
            }
        },
    }
}


def test_a_nested_identifier_flag_on_an_untooled_agents_action_is_refused(tmp_path):
    cfg = k5_cfg(tmp_path, tools=[], tools_allowed=[], action=NESTED)
    with pytest.raises(ConfigError, match="below the top level"):
        load_registry(load_config(cfg))


def test_a_nested_identifier_flag_on_an_action_no_agent_uses_is_refused(tmp_path):
    cfg = k5_cfg(tmp_path)
    (cfg / "actions" / "orphan.yaml").write_text(
        yaml.safe_dump({**ACTION, "id": "orphan", **NESTED}), encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="action orphan.*below the top level"):
        load_registry(load_config(cfg))


# --- m-B: many short expanding strings add up ----------------------------------------------------------------------------------------------


def test_redact_value_counts_the_expansion_of_all_strings_together(monkeypatch):
    each = "ﷺ" * 5  # 5 characters, 90 after NFKC
    value = [each] * 4000  # 20,000 characters, 360,000 after NFKC: over the cap
    assert sum(len(s) for s in value) < defaults.MAX_REDACT_CHARS
    big = BigNormalises(monkeypatch)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_value(value, {})
    assert big.calls == []
    assert runmap.redact_value([each] * 100, {})  # 9,000 after NFKC: fine


# --- m-C: the short-message callers redact FIRST, then keep a head; a card over the cap is refused --------------------------------------------


def test_a_card_text_over_the_cap_is_refused_not_cut():
    with pytest.raises(runmap.InputTooLarge):
        channel_mod.clean("x" * (defaults.MAX_REDACT_CHARS * 2))


def test_a_tick_error_message_is_redacted_then_cut_and_the_work_is_bounded(monkeypatch):
    seen = []
    real = runmap.redact_text
    monkeypatch.setattr(
        runmap,
        "redact_text",
        lambda text, m, *a, **k: seen.append(len(text)) or real(text, m, *a, **k),
    )
    assert len(tick_mod._message(ValueError("e" * 1_000_000))) <= 500
    assert seen and max(seen) <= defaults.MAX_REDACT_CHARS

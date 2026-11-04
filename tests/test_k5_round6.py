"""K5-core review round 6. Each test names the finding class it closes and fails on the round-5 source."""

from __future__ import annotations

import sys

import pytest

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.actions.contract import schema_problems
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import OPEN_STATES, RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick as tick_mod
from hadavin_sdk.sources.kubernetes import KubernetesSettings
from tests.k5_support import k5_cfg

# --- BLOCKER: a pin is checked before ANY tool module is imported ------------------------------------------------


def test_pin_mismatch_is_refused_before_the_module_is_imported(tmp_path, monkeypatch):
    mod_dir = tmp_path / "mods"
    mod_dir.mkdir()
    (mod_dir / "r6_side_effect.py").write_text(
        "import builtins\nbuiltins._r6_ran = True\n\ndef read_logs(ctx, **kw):\n    return ''\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(mod_dir))
    monkeypatch.delattr("builtins._r6_ran", raising=False)
    cfg = k5_cfg(
        tmp_path / "c",
        config={
            "tool_modules": ["r6_side_effect"],
            "tool_module_hashes": {"r6_side_effect": "0" * 64},
        },
    )
    with pytest.raises(ConfigError, match="the pin says"):
        load_registry(load_config(cfg))
    import builtins

    assert not hasattr(builtins, "_r6_ran")
    assert "r6_side_effect" not in sys.modules


def test_module_sha256_does_not_import(tmp_path, monkeypatch):
    mod_dir = tmp_path / "mods"
    mod_dir.mkdir()
    (mod_dir / "r6_hash_only.py").write_text("raise SystemExit('imported')\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(mod_dir))
    assert len(tools_mod.module_sha256("r6_hash_only")) == 64
    assert "r6_hash_only" not in sys.modules


# --- MAJOR: a run parked in NEEDS_PERSON cannot move, so its map ages normally -----------------------------------


def test_needs_person_is_not_an_open_state():
    assert RunState.NEEDS_PERSON not in OPEN_STATES
    assert RunState.WAITING_FOR_APPROVAL in OPEN_STATES


# --- MAJOR: grounding cannot be bypassed by a non-string input ----------------------------------------------------


def test_a_non_boolean_non_string_input_must_say_identifier_false():
    assert validate_contract_problems({"type": "integer", "identifier": False}) == []
    bad = validate_contract_problems({"type": "integer", "identifier": True})
    assert bad and "identifier" in bad[0]


def validate_contract_problems(sub: dict) -> list[str]:
    return schema_problems({"type": "object", "properties": {"n": sub}})


def test_registry_refuses_an_integer_input_without_an_identifier_flag(tmp_path):
    cfg = k5_cfg(
        tmp_path,
        action={
            "input_schema": {
                "type": "object",
                "properties": {"replicas": {"type": "integer"}},
                "required": ["replicas"],
            }
        },
    )
    with pytest.raises(ConfigError, match="identifier"):
        load_registry(load_config(cfg))


# --- tick: held tool calls have a ceiling; a raising hold hook does not skip it; cadence does not drift -----------


def test_cluster_suffix_must_end_in_a_private_label(tmp_path):
    cfg = k5_cfg(tmp_path, config={"evidence": {"cluster_suffixes": [".example.com"]}})
    with pytest.raises(Exception, match="private label"):
        load_config(cfg)


# (the cadence and the caught_by rule are tested by behaviour in test_k5_round7.py)


# --- redaction: a secret hidden by a look-alike, a zero-width space or an escape is still redacted ---------------


@pytest.mark.parametrize(
    "hidden",
    [
        "10.0.0.\u200b5",
        "１０.0.0.5",
        "10.0.0.5\x00",
        "\\u0031\\u0030.0.0.5",
    ],
)
def test_a_hidden_address_is_redacted(hidden):
    out = runmap.redact_text(f"host {hidden} down", {})
    assert "<IPV4_" in out and "10.0.0" not in out.replace("\x00", "") and "0.0.5" not in out


def test_nul_is_removed_before_redaction():
    assert "\x00" not in runmap.redact_text("a\x00b", {})


def test_the_storable_cache_holds_no_original_value():
    runmap.storable_original("ipv4", "10.9.9.9")
    assert all(len(k) == 64 and "10.9.9.9" not in k for k in runmap._STORABLE_CACHE)


# --- source settings: api_url is scheme and host only --------------------------------------------------------------


def test_api_url_with_a_path_is_refused():
    with pytest.raises(Exception, match="api_url"):
        KubernetesSettings(
            api_url="https://k8s.example.internal/prefix",
            namespaces=("a",),
        )


def test_a_raising_hold_hook_still_applies_the_ceilings_and_skips_the_ordinary_purge(tmp_path):
    from tests.test_k5_tools import _age, _purge_app

    def broken():
        raise RuntimeError("hold store down")

    app = _purge_app(tmp_path, hold=broken)
    ancient = app.runtime.handle("test-agent", "svc:test-agent", b"a 10.0.0.5")
    old = app.runtime.handle("test-agent", "svc:test-agent", b"b 10.0.0.6")
    _age(app, ancient.run_id, 401)
    _age(app, old.run_id, 40)
    with pytest.raises(RuntimeError):
        tick_mod.purge_evidence(tick_mod.TickContext(app, now()))
    assert app.store.list_tool_calls(ancient.run_id) == []  # the ceiling ran first
    assert app.store.list_tool_calls(old.run_id) != []  # the ordinary purge was skipped


def test_held_tool_calls_go_at_their_ceiling(tmp_path):
    from tests.test_k5_tools import _age, _purge_app

    held: set[str] = set()
    app = _purge_app(tmp_path, hold=lambda: held)
    run = app.runtime.handle("test-agent", "svc:test-agent", b"a 10.0.0.5")
    held.add(run.run_id)
    _age(app, run.run_id, 40)
    tick_mod.purge_evidence(tick_mod.TickContext(app, now()))
    assert app.store.list_tool_calls(run.run_id) != []
    _age(app, run.run_id, 401)
    tick_mod.purge_evidence(tick_mod.TickContext(app, now()))
    assert app.store.list_tool_calls(run.run_id) == []

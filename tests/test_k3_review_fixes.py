"""K3 review fixes: duplicate YAML keys, replay-record lines, build() tools, read-only card text."""

from __future__ import annotations

import json

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import replay_records
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.models import ToolCall
from hadavin_sdk.registry import load_registry
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, ScriptedLLM, _record, dev_cfg, reply


def test_k3_duplicate_levels_key_refused(tmp_path):
    cfg = dev_cfg(tmp_path)
    path = cfg / "agents.yaml"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "  levels: {lookup_record: shadow}\n  levels: {lookup_record: suggest}\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="duplicate key 'levels'"):
        load_registry(load_config(cfg))


def test_k3_duplicate_config_key_refused(tmp_path):
    cfg = dev_cfg(tmp_path)
    path = cfg / "config.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "eval_threshold: 0.5\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate key 'eval_threshold'"):
        load_config(cfg)


def test_k3_malformed_non_final_replay_line_refused(tmp_path):
    reg = load_registry(load_config(dev_cfg(tmp_path / "c")))
    good = json.dumps(_record(reg))
    path = tmp_path / replay_records.FILE
    path.write_text("{not json\n" + good + "\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="line 1: not valid JSON"):
        replay_records.read_records(tmp_path)


def test_k3_build_passes_tools_to_hooks(tmp_path):
    cfg = dev_cfg(tmp_path, {"restart_service": "shadow"}, tools=["echo"])
    qualify(load_registry(load_config(cfg)))
    echo = ToolCall(name="echo", input={"text": "hi"})
    app = app_mod.build(
        cfg,
        ["test-agent"],
        llm=ScriptedLLM(reply(echo), reply()),
        secrets=SECRETS,
        tools={"echo": lambda inp: "pong"},
    )
    app.runtime.handle("test-agent", "svc:test-agent", b"doc")
    assert app.runtime.llm.calls[0]["tools"][-1] == {"name": "echo"}


def test_k3_read_only_card_text_matches_the_suggest_cut_off():
    from hadavin_sdk.approvals.cards import would_be_text

    assert "would be refused in this release" in would_be_text("class.read_only")

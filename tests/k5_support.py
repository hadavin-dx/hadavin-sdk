"""Shared K5 test builders: a tooled agent with a manifest, a `none` action with identifier inputs, a runtime wired
the way `app.build` wires it, and a scripted model. No network, no spend."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.cards import Card, Delivery
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.config import load_config
from hadavin_sdk.guard import RegexDetector
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import Reply, ToolCall
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.store import MemoryStore
from tests.conftest import make_cfg, qualify

ACTION = {
    "id": "rollout_undo",
    "version": 1,
    "description": "Roll one host back to a revision.",
    "input_schema": {
        "type": "object",
        "required": ["host", "revision"],
        "additionalProperties": False,
        "properties": {
            "host": {
                "type": "string",
                "identifier": True,
                "pattern": r"[0-9]{1,3}(\.[0-9]{1,3}){3}",
            },
            "revision": {"type": "string", "identifier": True, "pattern": "[0-9]{1,6}"},
            "mode": {"type": "string", "enum": ["fast", "safe"], "identifier": False},
            "reason": {"type": "string", "maxLength": 80, "identifier": False},
        },
    },
    "risk_class": "reversible",
    "targets_production": True,
    "changes_spend": False,
    "target_system": "ito-prod",
    "executor": {"kind": "none"},
    "expected_outcome": "the host runs the given revision",
}
TOOL = {
    "name": "read_logs",
    "function": "tests.fixtures.k5_tools:read_logs",
    "description": "Read one recorded log by name.",
    "input_schema": {
        "type": "object",
        "required": ["name"],
        "additionalProperties": False,
        "properties": {"name": {"type": "string", "maxLength": 80}},
    },
    "side_effect": "none",
    "operations": ["bundle.read"],
    "hosts": [],
    "secret_names": [],
    "max_output_bytes": 16384,
}
SECRETS = FakeSecretProvider({"fixture-token": "t" * 8, "tool-key": "k-secret-value-123"})
BUNDLES = Path(__file__).parent / "fixtures" / "bundles" / "redteam"


def _edit(path: Path, fn) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def k5_cfg(
    tmp_path: Path,
    *,
    tools: list[dict] | None = None,
    action: dict | None = None,
    max_run_usd: str | None = None,
    config: dict | None = None,
    tools_allowed: list[str] | None = None,
    levels: dict | None = None,
) -> Path:
    """The fixture config plus a tooled test-agent: manifest tool `read_logs`, action `rollout_undo`."""
    cfg = make_cfg(tmp_path)
    for path in (cfg / "actions").glob(
        "*.yaml"
    ):  # a tooled agent's string inputs must each say identifier
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for sub in ((data.get("input_schema") or {}).get("properties") or {}).values():
            if sub.get("type") == "string":
                sub.setdefault("identifier", False)
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
    (cfg / "actions" / "rollout_undo.yaml").write_text(
        yaml.safe_dump({**ACTION, **(action or {})}), encoding="utf-8"
    )
    manifest = [TOOL] if tools is None else tools

    def agent(d):
        d[0]["scope_allowed"].append("rollout_undo")
        d[0]["tools_allowed"] = (
            [t["name"] for t in manifest] if tools_allowed is None else tools_allowed
        )
        d[0]["levels"] = levels or {"rollout_undo": "shadow"}
        d[0]["max_steps"] = 6
        if max_run_usd:
            d[0]["max_run_usd"] = max_run_usd

    _edit(cfg / "agents.yaml", agent)
    _edit(cfg / "principals.yaml", lambda d: d[0]["rights"].append("rollout_undo"))
    _edit(
        cfg / "config.yaml",
        lambda d: d.update({"tool_modules": ["tests.fixtures.k5_tools"], **(config or {})}),
    )
    (cfg / "tools").mkdir(exist_ok=True)
    (cfg / "tools" / "test-agent.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return cfg


class ScriptLLM:
    """Plays a script of steps. `{"tool": name}` reads a log, `{"propose": inputs, "evidence": ids}` proposes
    `rollout_undo` (evidence defaults to the last call id seen), `{"noaction": true}` ends. Keeps everything the
    model was sent in `sent`."""

    def __init__(self, script: list[dict], tool_name: str = "read_logs") -> None:
        self.script, self.sent, self.tool_name = list(script), [], tool_name

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.sent.append(
            {"messages": messages, "system": system, "tools": tools, "documents": documents}
        )
        step = self.script.pop(0)
        ids = re.findall(r"call_id=(\S+?)[ >]", json.dumps(messages))
        if "tool" in step:
            return Reply(
                text="reading",
                tool_calls=[ToolCall(name=self.tool_name, input={"name": step["tool"]})],
                model_id="fake-model",
            )
        if "propose" in step:
            evidence_ids = step.get("evidence", ids[-1:])
            inputs = {**step["propose"], "evidence": evidence_ids}
            if "reason" in step:
                inputs["reason"] = step["reason"]
            return Reply(
                text="The rollout is the cause.",
                tool_calls=[ToolCall(name="rollout_undo", input=inputs)],
                model_id="fake-model",
            )
        return Reply(text="Nothing to do.", model_id="fake-model")

    def everything_sent(self) -> str:
        return json.dumps(self.sent, default=lambda b: b.decode("utf-8", "replace"))


def build_runtime(
    cfg_dir: Path,
    llm,
    *,
    store: MemoryStore | None = None,
    validate: bool = True,
    secrets=SECRETS,
    do_qualify: bool = True,
):
    """A Runtime wired as app.build wires it (the toolbox, the proposal check), with cards captured."""
    cfg = load_config(cfg_dir)
    reg = load_registry(cfg)
    if do_qualify:
        qualify(reg)
    store = store or MemoryStore()
    audit = LocalDirSink(cfg.backends.audit.dir)
    cards: list[Card] = []

    def post(card: Card) -> Delivery:
        cards.append(card)
        return Delivery(ok=True, ref="m1")

    hooks = Hooks(
        post_card=post,
        toolbox=app_mod._toolbox(cfg, reg, secrets),
        validate_proposal=evidence.make_validator(store) if validate else None,
    )
    rt = Runtime(
        reg,
        store,
        audit,
        llm,
        RegexDetector(cfg.backends.detector[0].threshold),
        Limits(store, audit, reg),
        ["test-agent"],
        hooks,
    )
    return rt, cards


def handle(rt: Runtime, document: bytes = b"checkout 5xx from 10.0.0.5, revision 17", **kw):
    return rt.handle("test-agent", "svc:test-agent", document, **kw)

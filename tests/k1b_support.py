"""Shared K1b test helpers: a scripted model, bundle and cause-list builders. Zero API cost, no network."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

from hadavin_sdk.models import Reply, ToolCall

ALERT_TIME = "2026-01-01T10:00:00Z"


class ScriptedLLM:
    """Replies in call order (a Reply, or a callable taking the messages). Records every call. Keys nothing on
    ``documents`` (the K1a helper's ``documents[0]`` use is why this is a new class)."""

    def __init__(self, replies: list[Reply | Callable[[list[dict[str, Any]]], Reply]]) -> None:
        self.replies = list(replies)
        self.calls: list[dict[str, Any]] = []

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.calls.append(
            {
                "messages": [dict(m) for m in messages],
                "system": system,
                "route": route,
                "tools": tools,
            }
        )
        item = self.replies.pop(0)
        return item(messages) if callable(item) else item


def tool_reply(name: str, cost: str = "0", **inputs: Any) -> Reply:
    return Reply(
        tool_calls=[ToolCall(name=name, input=inputs)],
        cost_usd=Decimal(cost),
        model_id="fake-model",
    )


def calls_reply(*calls: tuple[str, dict[str, Any]], cost: str = "0") -> Reply:
    return Reply(
        tool_calls=[ToolCall(name=n, input=i) for n, i in calls],
        cost_usd=Decimal(cost),
        model_id="fake-model",
    )


def text_reply(text: str, cost: str = "0", stop_reason: str = "end_turn") -> Reply:
    return Reply(text=text, cost_usd=Decimal(cost), model_id="fake-model", stop_reason=stop_reason)


def submit(service: str, fault: str, *ids: str, cost: str = "0") -> Reply:
    cause = {"service": service, "fault_type": fault, "evidence_ids": list(ids)}
    return tool_reply("submit_diagnosis", cost, causes=[cause])


def submit_not_sure(cost: str = "0") -> Reply:
    return tool_reply("submit_diagnosis", cost, causes=[], not_sure=True)


def _jl(rows: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r) for r in rows) + "\n"


def default_parts() -> dict[str, Any]:
    return {
        "alert": {"title": "High latency", "severity": "page", "labels": {"team": "pay"}},
        "metrics": {
            "001": {
                "query": "cpu",
                "points": [
                    {"ts": "2026-01-01T09:00:00Z", "value": 1},
                    {"ts": "2026-01-01T09:30:00Z", "value": 2.5},
                    {"ts": "2026-01-01T10:00:00Z", "value": 9},
                ],
            }
        },
        "logs": {
            "001": [
                {
                    "ts": "2026-01-01T09:10:00Z",
                    "level": "info",
                    "message": "start",
                    "service": "api",
                },
                {
                    "ts": "2026-01-01T09:05:00Z",
                    "level": "error",
                    "message": "boom code=7",
                    "service": "db",
                },
                {
                    "ts": "2026-01-01T09:59:59.5Z",
                    "level": "error",
                    "message": "boom again",
                    "service": "api",
                },
            ]
        },
        "deploys": [
            {
                "ts": "2026-01-01T08:00:00Z",
                "service": "api",
                "version": "v2",
                "as_of": "2026-01-01T09:00:00Z",
            }
        ],
        "k8s": {
            "001": {
                "kind": "Deployment",
                "name": "api",
                "as_of": "2026-01-01T09:00:00Z",
                "spec": {"replicas": 3},
                "events": [{"ts": "2026-01-01T09:01:00Z", "reason": "Scaled", "message": "up"}],
            }
        },
        "runbooks": {
            "001": (
                "# Latency runbook\nfirst line\n\nsecond chunk\n\n\nthird",
                "2026-01-01T00:00:00Z",
            )
        },
    }


def write_manifest(case_dir: Path) -> None:
    files = {
        p.relative_to(case_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in case_dir.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    }
    (case_dir / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")


def make_bundle(
    root: Path, case_id: str = "case-001", alert_time: str = ALERT_TIME, **override: Any
) -> Path:
    """Write a valid bundle (pass ``name=None`` to drop a part, or a new value to replace it) with its manifest."""
    parts = {**default_parts(), **override}
    d = Path(root) / case_id
    d.mkdir(parents=True)
    (d / "incident.json").write_text(
        json.dumps({"alert_time": alert_time, "alert": parts["alert"]}), encoding="utf-8"
    )
    for n, obj in (parts["metrics"] or {}).items():
        (d / "metrics").mkdir(exist_ok=True)
        (d / "metrics" / f"{n}.json").write_text(json.dumps(obj), encoding="utf-8")
    for n, rows in (parts["logs"] or {}).items():
        (d / "logs").mkdir(exist_ok=True)
        (d / "logs" / f"{n}.jsonl").write_text(_jl(rows), encoding="utf-8")
    if parts["deploys"] is not None:
        (d / "deploys.json").write_text(json.dumps(parts["deploys"]), encoding="utf-8")
    for n, obj in (parts["k8s"] or {}).items():
        (d / "k8s").mkdir(exist_ok=True)
        (d / "k8s" / f"{n}.json").write_text(json.dumps(obj), encoding="utf-8")
    for n, (text, as_of) in (parts["runbooks"] or {}).items():
        (d / "runbooks").mkdir(exist_ok=True)
        (d / "runbooks" / f"{n}.md").write_text(text, encoding="utf-8")
        (d / "runbooks" / f"{n}.meta.json").write_text(
            json.dumps({"as_of": as_of}), encoding="utf-8"
        )
    write_manifest(d)
    return d


def make_cause_list(root: Path, services=("api", "db"), faults=("bad_deploy", "oom")) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "services.json").write_text(json.dumps(list(services)), encoding="utf-8")
    (root / "fault_types.json").write_text(json.dumps(list(faults)), encoding="utf-8")
    return root

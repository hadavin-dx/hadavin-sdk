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


# ---------------------------------------------------------------- outputs, answers, dry run


def record(
    case_id: str, diagnosis: Any = None, status: str = "ok", converted: bool = False, returned=()
) -> dict:
    rec: dict[str, Any] = {
        "case_id": case_id,
        "status": status,
        "diagnosis": diagnosis,
        "returned_ids": sorted(returned),
    }
    if converted:
        rec["converted"] = "uncited"
    return rec


def cause(service: str, fault: str, *ids: str) -> dict:
    return {
        "service": service,
        "fault_type": fault,
        "evidence_ids": list(ids or ["logs/001.jsonl#0"]),
    }


def _counts(recs: dict[str, dict], hard_a: int) -> dict[str, int]:
    st = [r["status"] for r in recs.values()]
    return {
        "ok": st.count("ok"),
        "unreadable": sum(r["status"] == "ok" and r["diagnosis"] is None for r in recs.values()),
        "error": st.count("error"),
        "timeout": st.count("timeout"),
        "capped": st.count("capped"),
        "uncited_conversions": sum("converted" in r for r in recs.values()),
        "hard_check_a": hard_a,
    }


def write_outputs(
    out: Path, bundles: Path, cause_dir: Path, runs: list[dict[str, dict]], hard_a=0
) -> Path:
    """Write ``run1..runK`` (each a ``{case_id: record}`` dict) with valid ``run.json`` files."""
    from hadavin_sdk.k1b.bundle import bundle_set_sha256, load_bundles
    from hadavin_sdk.k1b.causelist import load_cause_list

    cl = load_cause_list(cause_dir)
    bs = load_bundles(bundles)
    set_sha = bundle_set_sha256(bundles, bs)
    out = Path(out)
    for i, recs in enumerate(runs, 1):
        d = out / f"run{i}"
        d.mkdir(parents=True)
        for cid, rec in recs.items():
            (d / f"{cid}.json").write_text(json.dumps(rec), encoding="utf-8")
        meta = {
            "schema": 1,
            "run_index": i,
            "k": len(runs),
            "replay_run_id": "k1b-test",
            "agent": "test-agent",
            "model_id": "fake-model",
            "config_hash": "c" * 64,
            "prompt_sha256": "p" * 64,
            "agent_prompt_sha256": "a" * 64,
            "bundle_set_sha256": set_sha,
            "cause_services_sha256": cl.services_sha256,
            "cause_fault_types_sha256": cl.fault_types_sha256,
            "cases": len(recs),
            "counts": _counts(recs, hard_a),
            "usd": "0.5",
            "sdk_version": "0.0.0",
            "temperature": "provider default",
        }
        (d / "run.json").write_text(json.dumps(meta), encoding="utf-8")
    return out


def write_answers(path: Path, cases: dict[str, tuple[list[tuple[str, str]], bool]]) -> Path:
    body = {
        "sealed": True,
        "cases": {
            cid: {"accepted": [{"service": s, "fault_type": f} for s, f in acc], "no_evidence": ne}
            for cid, (acc, ne) in cases.items()
        },
    }
    Path(path).write_text(json.dumps(body), encoding="utf-8")
    return Path(path)


class RecordingLLM:
    """Wraps a ScriptedLLM and saves every reply as a recording for the ``fake`` llm kind (keyed like FakeLLM)."""

    def __init__(self, inner: ScriptedLLM, recorded_dir: Path) -> None:
        self.inner, self.dir, self.attempts = inner, Path(recorded_dir), {}

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        reply = self.inner.chat(messages, system=system, route=route, tools=tools)
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
        self.attempts[digest] = self.attempts.get(digest, 0) + 1
        data = {
            "text": reply.text,
            "tool_calls": [{"name": c.name, "input": c.input} for c in reply.tool_calls],
            "input_tokens": 1200,
            "output_tokens": 150,
            "stop_reason": reply.stop_reason,
        }
        (self.dir / f"{digest}-{self.attempts[digest]}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        return reply


DRY_CAUSES = (("api", "bad_deploy"), ("db", "oom"), ("db", "bad_deploy"), ("api", "oom"))


def dry_run_export(root: Path, cfg_dir: Path) -> dict[str, Path]:
    """A fake client export plus recordings, so the CLI can run end to end on the ``fake`` llm kind.

    case-001 right answer (Hit); case-002 unreadable reply (Miss); case-003 cites evidence never shown
    (uncited conversion, Not sure); case-004 no_evidence answered Not sure (Hit no_evidence); case-005 names a
    service not on the Cause List (Miss); case-006 honest Not sure. ``bundles-poisoned`` holds a post-alert log.
    """
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.config import load_config
    from hadavin_sdk.guard.injection import RegexDetector
    from hadavin_sdk.k1b.audit_sink import K1bAudit
    from hadavin_sdk.k1b.replay import replay
    from hadavin_sdk.registry import load_registry

    root = Path(root)
    bundles = root / "bundles"
    for i in range(1, 7):
        extra = (
            {"logs": None, "metrics": None, "deploys": None, "k8s": None, "runbooks": None}
            if i == 4
            else {}
        )
        alert = {"title": f"Incident {i}: latency up", "severity": "page"}
        make_bundle(bundles, f"case-{i:03d}", alert=alert, **extra)
    poisoned = root / "bundles-poisoned"
    make_bundle(poisoned, "case-001")
    late = {
        "ts": "2026-01-01T10:00:01Z",
        "level": "info",
        "message": "rolled back deploy v2",
        "service": "api",
    }
    with open(poisoned / "case-001" / "logs" / "001.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(late) + "\n")
    write_manifest(poisoned / "case-001")
    cause_dir = make_cause_list(root / "cause")
    answers = write_answers(
        root / "answers.json",
        {
            "case-001": ([("api", "bad_deploy")], False),
            "case-002": ([("api", "oom")], False),
            "case-003": ([("db", "oom")], False),
            "case-004": ([], True),
            "case-005": ([("db", "bad_deploy")], False),
            "case-006": ([("api", "oom")], False),
        },
    )
    unreadable = '```json\n{"causes": [{"service": "api", "fault_type": "oom", "evidence_ids": ["logs/001.jsonl#1"]}]}\n```'
    script = ScriptedLLM(
        [
            tool_reply("query_logs"),
            submit("api", "bad_deploy", "logs/001.jsonl#0"),
            text_reply(unreadable),
            submit("db", "oom", "logs/001.jsonl#2"),
            tool_reply("list_data"),
            submit_not_sure(),
            tool_reply("query_logs"),
            submit("payments", "oom", "logs/001.jsonl#1"),
            submit_not_sure(),
        ]
    )
    reg = load_registry(load_config(cfg_dir))
    recorded = cfg_dir.parent / "recorded"
    sink = LocalDirSink(root / "record-audit")
    replay(
        reg, RecordingLLM(script, recorded), RegexDetector(0.5), K1bAudit(sink),
        agent_id="test-agent", bundles_dir=bundles, cause_list_dir=cause_dir, k=1,
        max_usd=Decimal(10), out=root / "record-out", llm_kind="fake",
    )  # fmt: skip
    return {
        "bundles": bundles,
        "poisoned": poisoned,
        "cause": cause_dir,
        "answers": answers,
        "out": root / "out",
    }

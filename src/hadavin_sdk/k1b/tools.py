"""The seven tools the replay agent sees: six read-only snapshot queries plus ``submit_diagnosis``.

Every data result is a JSON list of records that each carry an ``id`` (the evidence ID grammar of
``bundle.py``), or the one uniform no-data answer. A bad window, a bad type, an unknown name and an empty
result all return the same no-data answer, so the shape of an answer never hints at what exists.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from hadavin_sdk.k1b.bundle import Bundle, parse_ts
from hadavin_sdk.k1b.diagnosis import DIAGNOSIS_SCHEMA

NO_DATA: dict[str, str] = {"result": "no data in the snapshot for this request"}
SUBMIT = "submit_diagnosis"
DATA_TOOLS = ("list_data", "query_metrics", "query_logs", "get_deploys", "get_k8s", "get_runbook")
ALLOWED_TOOLS = frozenset((*DATA_TOOLS, SUBMIT))
MAX_POINTS = 200
MAX_LOG_LIMIT = 50
MAX_RESULT_BYTES = 20_000

_STR = {"type": "string"}
_TS = {"type": "string", "description": "UTC timestamp YYYY-MM-DDTHH:MM:SSZ"}


def _tool(name: str, description: str, props: dict[str, Any]) -> dict[str, Any]:
    schema = {"type": "object", "properties": props, "additionalProperties": False}
    return {"name": name, "description": description, "input_schema": schema}


TOOL_SPECS: list[dict[str, Any]] = [
    _tool(
        "list_data",
        "List the metric queries, log services, k8s objects and runbooks available.",
        {},
    ),
    _tool(
        "query_metrics",
        "Metric points for one listed query (exact match), optionally within a time window.",
        {"query": _STR, "start": _TS, "end": _TS},
    ),
    _tool(
        "query_logs",
        "Log lines in time order, filtered by service and a case-sensitive substring.",
        {
            "service": _STR,
            "contains": _STR,
            "start": _TS,
            "end": _TS,
            "limit": {"type": "integer", "maximum": MAX_LOG_LIMIT},
        },
    ),
    _tool("get_deploys", "Deploy records, optionally for one service.", {"service": _STR}),
    _tool(
        "get_k8s",
        "Kubernetes object specs and events, optionally by kind and name.",
        {"kind": _STR, "name": _STR},
    ),
    _tool(
        "get_runbook", "Runbook chunks, optionally for one runbook file or title.", {"name": _STR}
    ),
    {
        "name": SUBMIT,
        "description": "Give the final diagnosis. Call this once, when done.",
        "input_schema": DIAGNOSIS_SCHEMA,
    },
]


def _opt_str(inputs: dict[str, Any], key: str) -> str | None:
    v = inputs.get(key)
    return v if isinstance(v, str) else None


class Snapshot:
    """Read-only queries over one loaded bundle. ``call`` returns a list of id-carrying records, or NO_DATA."""

    def __init__(self, bundle: Bundle) -> None:
        self.b = bundle

    def call(self, name: str, inputs: Any) -> Any:
        if name not in DATA_TOOLS or not isinstance(inputs, dict):
            return NO_DATA
        allowed = {
            "list_data": set(),
            "query_metrics": {"query", "start", "end"},
            "query_logs": {"service", "contains", "start", "end", "limit"},
            "get_deploys": {"service"},
            "get_k8s": {"kind", "name"},
            "get_runbook": {"name"},
        }[name]
        if not set(inputs) <= allowed:
            return NO_DATA
        out = getattr(self, f"_{name}")(inputs)
        return out if out else NO_DATA

    def _window(self, inputs: dict[str, Any]) -> tuple[datetime | None, datetime] | None:
        """(start or None, end clamped to alert time), or None for a malformed or empty window."""
        start = end = None
        if "start" in inputs:
            start = parse_ts(inputs["start"])
            if start is None:
                return None
        if "end" in inputs:
            end = parse_ts(inputs["end"])
            if end is None:
                return None
        end = min(end, self.b.alert_time) if end else self.b.alert_time
        if start is not None and (start > self.b.alert_time or start > end):
            return None
        return start, end

    def _in(self, ts: str, win: tuple[datetime | None, datetime]) -> bool:
        t = parse_ts(ts)
        return t is not None and (win[0] is None or t >= win[0]) and t <= win[1]

    def _list_data(self, inputs: dict[str, Any]) -> Any:
        b = self.b
        return {
            "metrics": [{"file": f, "query": o["query"]} for f, o in b.metrics],
            "logs": [
                {"file": f, "services": sorted({r["service"] for r in rs})} for f, rs in b.logs
            ],
            "k8s": [{"file": f, "kind": o["kind"], "name": o["name"]} for f, o in b.k8s],
            "runbooks": [
                {"file": f, "title": cs[0].splitlines()[0].lstrip("# ").strip()[:100] if cs else ""}
                for f, cs in b.runbooks
            ],
        }

    def _query_metrics(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        query = _opt_str(inputs, "query")
        win = self._window(inputs)
        if query is None or win is None:
            return []
        out: list[dict[str, Any]] = []
        for rel, obj in self.b.metrics:
            if obj["query"] != query:
                continue
            for i, pt in enumerate(obj["points"]):
                if self._in(pt["ts"], win):
                    out.append({"id": f"{rel}#{i}", "ts": pt["ts"], "value": pt["value"]})
        return out[:MAX_POINTS]

    def _query_logs(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        win = self._window(inputs)
        limit = inputs.get("limit", MAX_LOG_LIMIT)
        bad_limit = not isinstance(limit, int) or isinstance(limit, bool) or limit < 1
        service, contains = _opt_str(inputs, "service"), _opt_str(inputs, "contains")
        for key in ("service", "contains"):
            if key in inputs and not isinstance(inputs[key], str):
                return []
        if win is None or bad_limit:
            return []
        hits = []
        for rel, records in self.b.logs:
            for i, r in enumerate(records):
                if service is not None and r["service"] != service:
                    continue
                if contains is not None and contains not in r["message"]:
                    continue
                if self._in(r["ts"], win):
                    hits.append((parse_ts(r["ts"]), rel, i, {"id": f"{rel}#{i}", **r}))
        hits.sort(key=lambda h: (h[0], h[1], h[2]))
        return [h[3] for h in hits[: min(limit, MAX_LOG_LIMIT)]]

    def _get_deploys(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        if "service" in inputs and not isinstance(inputs["service"], str):
            return []
        service = _opt_str(inputs, "service")
        return [
            {"id": f"deploys.json#{i}", **d}
            for i, d in enumerate(self.b.deploys)
            if service is None or d["service"] == service
        ]

    def _get_k8s(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        if not all(isinstance(v, str) for v in inputs.values()):
            return []
        out: list[dict[str, Any]] = []
        for rel, o in self.b.k8s:
            if ("kind" in inputs and o["kind"] != inputs["kind"]) or (
                "name" in inputs and o["name"] != inputs["name"]
            ):
                continue
            out.append(
                {
                    "id": f"{rel}#spec",
                    "kind": o["kind"],
                    "name": o["name"],
                    "as_of": o["as_of"],
                    "spec": o["spec"],
                }
            )
            out += [{"id": f"{rel}#events.{i}", **e} for i, e in enumerate(o["events"])]
        return out

    def _get_runbook(self, inputs: dict[str, Any]) -> list[dict[str, Any]]:
        if "name" in inputs and not isinstance(inputs["name"], str):
            return []
        name = _opt_str(inputs, "name")
        titles = {f["file"]: f["title"] for f in self._list_data({})["runbooks"]}
        return [
            {"id": f"{rel}#{i}", "file": rel, "text": chunk}
            for rel, chunks in self.b.runbooks
            if name is None or name in (rel, titles[rel])
            for i, chunk in enumerate(chunks)
        ]


def _cap_dict(result: dict[str, Any]) -> str:
    """A dict of lists (``list_data``): drop entries from the longest list until the text fits the cap."""
    result = {k: list(v) if isinstance(v, list) else v for k, v in result.items()}
    text = json.dumps(result, ensure_ascii=False)
    while len(text.encode("utf-8")) > MAX_RESULT_BYTES:
        lists = [v for v in result.values() if isinstance(v, list) and v]
        if not lists:
            return json.dumps(NO_DATA)
        max(lists, key=len).pop()
        text = json.dumps(result, ensure_ascii=False)
    return text


def render(result: Any) -> tuple[str, set[str]]:
    """The JSON text shown to the model and the evidence IDs whose records are in that text. A record list is
    cut at ``MAX_RESULT_BYTES``; a record is shown whole or not at all. Nothing fits: the no-data answer."""
    if not isinstance(result, list):
        return _cap_dict(result), set()
    shown: list[dict[str, Any]] = []
    size = 2  # the brackets
    for rec in result:
        size += len(json.dumps(rec, ensure_ascii=False).encode("utf-8")) + (2 if shown else 0)
        if size > MAX_RESULT_BYTES:
            break
        shown.append(rec)
    if not shown:
        return json.dumps(NO_DATA), set()
    return json.dumps(shown, ensure_ascii=False), {r["id"] for r in shown}

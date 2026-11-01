"""Contract suites for the four read-source interfaces (K5-core). Each suite takes an adapter and a `Case` naming
what it holds, so any adapter (Kubernetes here; CloudWatch, PagerDuty, GitHub, Prometheus and others in the packs)
runs the same checks: records are dicts with a unique string `id`, "no data" is an empty list and never an error,
limits are honoured, and the scope probe returns a list of problems or None."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from hadavin_sdk.sources import (
    ChangeSource,
    IncidentSource,
    LogsSource,
    MetricsSource,
    Record,
    SourceError,
)

START, END = "2026-11-01T10:00:00Z", "2026-11-01T11:00:00Z"
EMPTY_START, EMPTY_END = "2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z"


@dataclass(frozen=True)
class Case:
    """What an adapter holds: a scope, log query, metric query and incident id that have data; an unknown of each."""

    scope: str = ""
    logs: str = ""
    metric: str = ""
    incident: str = ""


def assert_records(records: Any) -> list[Record]:
    assert isinstance(records, list)
    ids = []
    for r in records:
        assert isinstance(r, dict) and isinstance(r.get("id"), str) and r["id"], r
        ids.append(r["id"])
        json.dumps(r)  # plain JSON data, so a tool can hand it to the model
    assert len(ids) == len(set(ids)), "record ids are unique"
    return records


def check_probe(source: Any) -> None:
    found = source.probe_scope()
    assert found is None or (isinstance(found, list) and all(isinstance(p, str) for p in found))
    assert isinstance(source.name, str) and source.name


def check_change_source(source: ChangeSource, case: Case) -> None:
    check_probe(source)
    assert assert_records(source.recent_changes(case.scope, START, END))
    assert source.recent_changes("no-such-scope", START, END) == []
    assert_records(
        source.recent_changes(case.scope, EMPTY_START, EMPTY_END)
    )  # no data is not an error


def check_logs_source(source: LogsSource, case: Case) -> None:
    check_probe(source)
    two = assert_records(source.query_logs(case.logs, START, END, 2))
    assert 0 < len(two) <= 2
    assert len(source.query_logs(case.logs, START, END, 1)) == 1
    assert source.query_logs("no-such/query", START, END, 5) == []
    assert source.query_logs(case.logs, START, END, 0) == []
    assert_records(source.query_logs(case.logs, EMPTY_START, EMPTY_END, 5))


def check_metrics_source(source: MetricsSource, case: Case) -> None:
    check_probe(source)
    assert assert_records(source.query_metrics(case.metric, START, END, 60))
    assert source.query_metrics("no_such_metric", START, END, 60) == []
    assert source.query_metrics(case.metric, EMPTY_START, EMPTY_END, 60) == []


def check_incident_source(source: IncidentSource, case: Case) -> None:
    check_probe(source)
    found = source.get_incident(case.incident)
    assert isinstance(found, dict) and isinstance(found.get("id"), str)
    assert source.get_incident("no-such-incident") is None
    listed = assert_records(source.list_open(1))
    assert len(listed) <= 1
    assert source.list_open(0) == []


def check_failure_is_a_source_error(make_failing: Any) -> None:
    """An adapter whose backend fails raises SourceError (never a bare driver error, never silence)."""
    source, call = make_failing()
    try:
        call(source)
    except SourceError:
        return
    raise AssertionError("a failing backend must raise SourceError")


class RecordedSource:
    """The reference adapter: answers from recorded data, implements all four interfaces. `probe_scope` is None
    (a recording has no credential), so it needs a scope_inventory reference like any unprobeable source."""

    name = "recorded"

    def __init__(self) -> None:
        self.changes = {"prod": [{"id": "deploy/prod/checkout", "ts": "2026-11-01T10:15:00Z"}]}
        self.logs = {
            "prod/checkout": [
                {"id": f"log/prod/checkout#{i}", "ts": f"2026-11-01T10:0{i}:00Z", "line": f"l{i}"}
                for i in range(5)
            ]
        }
        self.metrics = {
            "error_rate": [{"id": "m/error_rate#0", "ts": "2026-11-01T10:30:00Z", "value": "3"}]
        }
        self.incidents = {"INC-1": {"id": "INC-1", "title": "checkout down"}}

    def probe_scope(self) -> list[str] | None:
        return None

    def recent_changes(self, scope: str, start: str, end: str) -> list[Record]:
        return [r for r in self.changes.get(scope, []) if start <= r["ts"] <= end]

    def query_logs(self, query: str, start: str, end: str, limit: int) -> list[Record]:
        rows = [r for r in self.logs.get(query, []) if start <= r["ts"] <= end]
        return rows[: max(limit, 0)]

    def query_metrics(self, query: str, start: str, end: str, step_s: int) -> list[Record]:
        return [r for r in self.metrics.get(query, []) if start <= r["ts"] <= end]

    def get_incident(self, incident_id: str) -> Record | None:
        return self.incidents.get(incident_id)

    def list_open(self, limit: int) -> list[Record]:
        return list(self.incidents.values())[: max(limit, 0)]


def ks(fetch, namespaces=("prod",), **settings):
    """A KubernetesSource for tests: the endpoint is a reserved, non-routable test name, never a default."""
    from hadavin_sdk.sources.kubernetes import KubernetesSettings, KubernetesSource

    return KubernetesSource(
        fetch,
        KubernetesSettings(
            api_url="https://kube.test.invalid", namespaces=tuple(namespaces), **settings
        ),
    )

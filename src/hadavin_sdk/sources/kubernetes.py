"""Kubernetes read source: deployments and events as changes, pod logs as logs, and the scope probe.

It speaks the Kubernetes REST API through an injected ``fetch`` (a tool's ``ToolContext.fetch`` with the
ServiceAccount token bound), so it holds no secret, no client library and no cloud SDK: it works against any
conformant cluster (EKS, GKE, AKS, k3s, on-premises). Only ``get`` and ``list`` calls are made, plus one
``SelfSubjectRulesReview`` (a POST that creates nothing: it asks what the token may do).

Neutral protocol: the Kubernetes REST API (HTTPS, JSON).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from hadavin_sdk.sources import Record, SourceError

# The operation ids a manifest may list for this source (design 6.4: an operation off this list is refused).
READ_OPERATIONS = frozenset(
    {
        "k8s.list_deployments",
        "k8s.list_events",
        "k8s.pod_log",
        "k8s.rules_review",
    }
)
REVISION = "deployment.kubernetes.io/revision"
DEFAULT_API = "https://kubernetes.default.svc"
# Design 6.6 / K5b M20: verbs that change state, and subresources that open a shell or a tunnel.
_WRITE_VERBS = frozenset(
    {"create", "update", "patch", "delete", "deletecollection", "escalate", "bind", "impersonate"}
)
_READ_VERBS = frozenset({"get", "list", "watch"})
_SHELL_RESOURCES = frozenset(
    {"pods/exec", "pods/attach", "pods/portforward", "nodes/proxy", "services/proxy"}
)
Fetch = Callable[..., str]


def rules_problems(namespace: str, rules: list[dict[str, Any]]) -> list[str]:
    """Problems in one namespace's ``resourceRules`` from a SelfSubjectRulesReview (empty: read-only)."""
    out: list[str] = []
    for rule in rules:
        verbs = set(rule.get("verbs") or [])
        resources = set(rule.get("resources") or [])
        any_verb = "*" in verbs
        if bad := sorted(verbs & _WRITE_VERBS):
            out.append(f"namespace {namespace}: write verb {', '.join(bad)} on {sorted(resources)}")
        if any_verb:
            out.append(f"namespace {namespace}: wildcard verb on {sorted(resources)}")
        hit = sorted(resources & _SHELL_RESOURCES) or (["*"] if "*" in resources else [])
        if hit and verbs:
            out.append(f"namespace {namespace}: access to {', '.join(hit)} ({sorted(verbs)})")
        if ("secrets" in resources or "*" in resources) and (any_verb or verbs & _READ_VERBS):
            out.append(f"namespace {namespace}: read access to secrets")
    return out


class KubernetesSource:
    name = "kubernetes"

    def __init__(self, fetch: Fetch, namespaces: list[str], api: str = DEFAULT_API) -> None:
        if not namespaces:
            raise ValueError("KubernetesSource needs at least one namespace")
        self._fetch, self.namespaces, self._api = fetch, list(namespaces), api.rstrip("/")

    def _get(self, path: str, operation: str, method: str = "GET", body: dict | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        try:
            text = self._fetch(method, self._api + path, operation=operation, body=data)
            decoded = json.loads(text)
            if not isinstance(decoded, dict):
                raise ValueError("not an object")  # noqa: TRY004 - same malformed-answer path
            return decoded
        except (ValueError, TypeError) as exc:
            raise SourceError("kubernetes: malformed answer") from exc
        except SourceError:
            raise
        except Exception as exc:  # noqa: BLE001 - whatever the fetch raised, the source cannot answer
            raise SourceError(f"kubernetes: {type(exc).__name__}") from None

    # --- ChangeSource ---------------------------------------------------------------------------------------
    def recent_changes(self, scope: str, start: str, end: str) -> list[Record]:
        try:
            return self._recent_changes(scope, start, end)
        except (AttributeError, TypeError) as exc:  # a JSON value of an unexpected shape
            raise SourceError("kubernetes: malformed answer") from exc

    def _recent_changes(self, scope: str, start: str, end: str) -> list[Record]:
        """Deployments (with their rollout revision and images) and events of one namespace. `scope` is the
        namespace; one that is not configured has no data. Events are filtered to [start, end] (UTC ISO strings
        compare in order)."""
        if scope not in self.namespaces:
            return []
        ns = quote(scope, safe="")
        out: list[Record] = []
        deployments = self._get(
            f"/apis/apps/v1/namespaces/{ns}/deployments", "k8s.list_deployments"
        )
        for item in deployments.get("items") or []:
            meta = item.get("metadata") or {}
            containers = (((item.get("spec") or {}).get("template") or {}).get("spec")) or {}
            out.append(
                {
                    "id": f"deployment/{scope}/{meta.get('name', '?')}",
                    "kind": "deployment",
                    "name": meta.get("name"),
                    "revision": (meta.get("annotations") or {}).get(REVISION),
                    "images": [c.get("image") for c in containers.get("containers") or []],
                }
            )
        events = self._get(f"/api/v1/namespaces/{ns}/events", "k8s.list_events")
        for item in events.get("items") or []:
            ts = item.get("lastTimestamp") or item.get("eventTime") or ""
            if not ts or not (start <= ts <= end):
                continue
            meta = item.get("metadata") or {}
            out.append(
                {
                    "id": f"event/{scope}/{meta.get('name', '?')}",
                    "kind": "event",
                    "ts": ts,
                    "reason": item.get("reason"),
                    "message": item.get("message"),
                    "object": (item.get("involvedObject") or {}).get("name"),
                }
            )
        return out

    # --- LogsSource -----------------------------------------------------------------------------------------
    def query_logs(self, query: str, start: str, end: str, limit: int) -> list[Record]:
        """`query` is "<namespace>/<pod>". Lines since `start` (the API has no end bound: later lines are
        dropped here), at most `limit`."""
        scope, _, pod = query.partition("/")
        if scope not in self.namespaces or not pod or limit < 1:
            return []
        path = (
            f"/api/v1/namespaces/{quote(scope, safe='')}/pods/{quote(pod, safe='')}/log"
            f"?timestamps=true&sinceTime={quote(start, safe='')}&limitBytes=65536"
        )
        text = self._get_text(path)
        out: list[Record] = []
        for i, line in enumerate(text.splitlines()):
            ts, _, rest = line.partition(" ")
            if ts > end:
                break
            out.append({"id": f"log/{scope}/{pod}#{i}", "ts": ts, "line": rest})
            if len(out) >= limit:
                break
        return out

    def _get_text(self, path: str) -> str:
        try:
            return self._fetch("GET", self._api + path, operation="k8s.pod_log", body=None)
        except Exception as exc:  # noqa: BLE001
            raise SourceError(f"kubernetes: {type(exc).__name__}") from None

    # --- scope probe (design 6.6, K5b M20) ------------------------------------------------------------------
    def probe_scope(self) -> list[str]:
        try:
            return self._probe_scope()
        except (AttributeError, TypeError) as exc:
            raise SourceError("kubernetes: malformed answer") from exc

    def _probe_scope(self) -> list[str]:
        problems: list[str] = []
        for ns in self.namespaces:
            review = self._get(
                "/apis/authorization.k8s.io/v1/selfsubjectrulesreviews",
                "k8s.rules_review",
                method="POST",
                body={
                    "apiVersion": "authorization.k8s.io/v1",
                    "kind": "SelfSubjectRulesReview",
                    "spec": {"namespace": ns},
                },
            )
            status = review.get("status") or {}
            if status.get("incomplete"):
                problems.append(f"namespace {ns}: the rules review is incomplete, scope not proven")
            problems += rules_problems(ns, status.get("resourceRules") or [])
        return problems

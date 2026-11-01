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

# The operation ids a manifest may list for this source, each bound to one method and one path (design 6.4): a
# call that fits no binding is refused by `ToolContext.fetch`, so an id is never just a label.
_NS = r"[a-z0-9]([a-z0-9.\-]*[a-z0-9])?"
READ_OPERATIONS = {
    "k8s.list_deployments": ("GET", rf"/apis/apps/v1/namespaces/{_NS}/deployments"),
    "k8s.list_events": ("GET", rf"/api/v1/namespaces/{_NS}/events"),
    "k8s.pod_log": ("GET", rf"/api/v1/namespaces/{_NS}/pods/{_NS}/log"),
    "k8s.rules_review": ("POST", r"/apis/authorization\.k8s\.io/v1/selfsubjectrulesreviews"),
}
JSON_CAP = 1024 * 1024  # a real deployment list is far larger than a tool's 16 KB output cap
LOG_BYTES = 65536  # asked of the API (limitBytes); the fetch cap leaves room for the framing
PAGE = 100  # list page size; further pages follow `metadata.continue`
MAX_PAGES = 5
REVISION = "deployment.kubernetes.io/revision"
DEFAULT_API = "https://kubernetes.default.svc"
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
# Design 6.6 / K5b M20: verbs that change state, and subresources that open a shell or a tunnel.
_WRITE_VERBS = frozenset(
    {"create", "update", "patch", "delete", "deletecollection", "escalate", "bind", "impersonate"}
)
_READ_VERBS = frozenset({"get", "list", "watch"})
_SHELL_RESOURCES = frozenset(
    {
        "pods/exec",
        "pods/attach",
        "pods/portforward",
        "pods/proxy",
        "nodes/proxy",
        "services/proxy",
    }
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

    def _call(
        self,
        path: str,
        operation: str,
        method: str = "GET",
        body: dict | None = None,
        max_bytes: int = JSON_CAP,
    ) -> str:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = JSON_HEADERS if method == "POST" else {"Accept": "application/json"}
        try:
            return self._fetch(
                method,
                self._api + path,
                operation=operation,
                body=data,
                headers=headers,
                max_bytes=max_bytes,
            )
        except SourceError:
            raise
        except Exception as exc:  # noqa: BLE001 - whatever the fetch raised, the source cannot answer
            raise SourceError(f"kubernetes: {type(exc).__name__}") from None

    def _get(self, path: str, operation: str, method: str = "GET", body: dict | None = None) -> Any:
        text = self._call(path, operation, method, body)
        try:
            decoded = json.loads(text)
        except ValueError as exc:
            raise SourceError("kubernetes: malformed answer") from exc
        if not isinstance(decoded, dict):
            raise SourceError("kubernetes: malformed answer")
        return decoded

    def _items(self, path: str, operation: str) -> list[Any]:
        """All items of a list call: `PAGE` at a time, following `metadata.continue` for at most MAX_PAGES."""
        items: list[Any] = []
        token = ""
        for _ in range(MAX_PAGES):
            query = f"?limit={PAGE}" + (f"&continue={quote(token, safe='')}" if token else "")
            page = self._get(path + query, operation)
            items += page.get("items") or []
            token = (page.get("metadata") or {}).get("continue") or ""
            if not token:
                break
        return items

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
        for item in self._items(
            f"/apis/apps/v1/namespaces/{ns}/deployments", "k8s.list_deployments"
        ):
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
        for item in self._items(f"/api/v1/namespaces/{ns}/events", "k8s.list_events"):
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
            f"?timestamps=true&sinceTime={quote(start, safe='')}&limitBytes={LOG_BYTES}"
        )
        text = self._call(path, "k8s.pod_log", max_bytes=LOG_BYTES + 8192)
        out: list[Record] = []
        for i, line in enumerate(text.splitlines()):
            ts, _, rest = line.partition(" ")
            if ts > end:
                break
            out.append({"id": f"log/{scope}/{pod}#{i}", "ts": ts, "line": rest})
            if len(out) >= limit:
                break
        return out

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

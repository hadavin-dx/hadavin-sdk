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
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from hadavin_sdk import defaults
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
REVISION = "deployment.kubernetes.io/revision"
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


class KubernetesSettings(BaseModel):
    """Where the cluster is and how much to read. Normally a tool manifest's `options`; defaults in
    `hadavin_sdk/defaults.py`. `api_url` has no default: the endpoint is the deployment's, never the code's. It is scheme and host only, no
    path: the operation paths are absolute (`/api/v1/...`), so a base path would silently shift every call."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    api_url: str = Field(pattern=r"^https?://[^\s/?#]+/?$")
    namespaces: tuple[str, ...] = Field(min_length=1)
    page_size: int = Field(default=defaults.K8S_PAGE_SIZE, gt=0)
    max_pages: int = Field(default=defaults.K8S_MAX_PAGES, gt=0)
    json_cap_bytes: int = Field(default=defaults.K8S_JSON_CAP_BYTES, gt=0)
    log_bytes: int = Field(default=defaults.K8S_LOG_BYTES, gt=0)


def covers(entry: str, target: str) -> bool:
    """Does one RBAC `resources` entry cover `target` (`pods/exec`, `secrets`)? Kubernetes rule matching
    (`ResourceMatches`): `*` covers everything, `res/*` every subresource of `res`, `*/sub` that subresource of
    every resource, and `res` alone only the resource itself, never its subresources."""
    if entry == "*":
        return True
    if "/" not in entry:
        return entry == target
    res, _, sub = entry.partition("/")
    t_res, _, t_sub = target.partition("/")
    return res in ("*", t_res) and sub in ("*", t_sub) and bool(t_sub)


# Every authenticated subject may ask the API what it may do (`system:basic-user`): `create` on exactly these
# review resources, in their own API groups, writes nothing. Any other `create` is a write.
_SELF_REVIEWS = {
    "authorization.k8s.io": {"selfsubjectaccessreviews", "selfsubjectrulesreviews"},
    "authentication.k8s.io": {"selfsubjectreviews"},
}


def _only_self_reviews(rule: dict[str, Any]) -> bool:
    """Is this rule's `create` the harmless review kind: every group and every resource named, none a wildcard?"""
    groups, resources = rule.get("apiGroups") or [], rule.get("resources") or []
    return (
        bool(groups)
        and bool(resources)
        and all(
            g in _SELF_REVIEWS and all(r in _SELF_REVIEWS[g] for r in resources) for g in groups
        )
    )


def rules_problems(namespace: str, rules: list[dict[str, Any]]) -> list[str]:
    """Problems in one namespace's ``resourceRules`` from a SelfSubjectRulesReview (empty: read-only)."""
    out: list[str] = []
    for rule in rules:
        # The API answers lists of strings; anything else (a string `"create"`) proves nothing.
        if not isinstance(rule, dict) or any(
            not isinstance(rule.get(k) or [], list)
            or not all(isinstance(x, str) for x in rule.get(k) or [])
            for k in ("verbs", "resources", "apiGroups")
        ):
            out.append(f"namespace {namespace}: a rule is malformed, so the scope is not proven")
            continue
        verbs = set(rule.get("verbs") or [])
        resources = set(rule.get("resources") or [])
        any_verb = "*" in verbs
        harmless = verbs == {"create"} and _only_self_reviews(rule)
        if (bad := sorted(verbs & _WRITE_VERBS)) and not harmless:
            out.append(f"namespace {namespace}: write verb {', '.join(bad)} on {sorted(resources)}")
        if any_verb:
            out.append(f"namespace {namespace}: wildcard verb on {sorted(resources)}")
        hit = sorted(t for t in _SHELL_RESOURCES if any(covers(r, t) for r in resources))
        if hit and verbs:
            out.append(f"namespace {namespace}: access to {', '.join(hit)} ({sorted(verbs)})")
        if any(covers(r, "secrets") for r in resources) and (any_verb or verbs & _READ_VERBS):
            out.append(f"namespace {namespace}: read access to secrets")
    return out


def _when(text: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _within(ts: str, start: str, end: str) -> bool:
    """Is `ts` in [start, end]? Compared as instants, so `Z` and `+00:00` spellings order correctly; text that
    is not a time falls back to string order."""
    t, a, b = _when(ts), _when(start), _when(end)
    if t is None or a is None or b is None:
        return start <= ts <= end
    return a <= t <= b


def _after(ts: str, end: str) -> bool:
    t, b = _when(ts), _when(end)
    return ts > end if t is None or b is None else t > b


class KubernetesSource:
    name = "kubernetes"

    def __init__(self, fetch: Fetch, settings: KubernetesSettings) -> None:
        self._fetch, self._cfg = fetch, settings
        self.namespaces, self._api = list(settings.namespaces), settings.api_url.rstrip("/")

    def _call(
        self,
        path: str,
        operation: str,
        method: str = "GET",
        body: dict | None = None,
        max_bytes: int | None = None,
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
                max_bytes=max_bytes or self._cfg.json_cap_bytes,
            )
        except SourceError:
            raise
        except Exception as exc:  # noqa: BLE001 - whatever the fetch raised, the source cannot answer
            err = SourceError(f"kubernetes: {type(exc).__name__}")
            err.too_large = bool(getattr(exc, "too_large", False))
            raise err from None

    def _get(self, path: str, operation: str, method: str = "GET", body: dict | None = None) -> Any:
        text = self._call(path, operation, method, body)
        try:
            decoded = json.loads(text)
        except ValueError as exc:
            raise SourceError("kubernetes: malformed answer") from exc
        if not isinstance(decoded, dict):
            raise SourceError("kubernetes: malformed answer")
        return decoded

    def _items(self, path: str, operation: str) -> tuple[list[Any], bool]:
        """All items of a list call, `page_size` at a time following `metadata.continue`. A page that fails (too large
        for the fetch cap, say) is asked again with half the limit, down to one. Returns (items, incomplete):
        incomplete is true when max_pages ran out with more still to read."""
        items: list[Any] = []
        token, limit = "", self._cfg.page_size
        for _ in range(self._cfg.max_pages):
            while True:
                query = f"?limit={limit}" + (f"&continue={quote(token, safe='')}" if token else "")
                try:
                    page = self._get(path + query, operation)
                    break
                except SourceError as exc:
                    if (
                        limit == 1 or not exc.too_large
                    ):  # only a too-big page is worth asking smaller
                        raise
                    limit = max(1, limit // 2)
            items += page.get("items") or []
            token = (page.get("metadata") or {}).get("continue") or ""
            if not token:
                return items, False
        return items, True

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
        deployments, more_d = self._items(
            f"/apis/apps/v1/namespaces/{ns}/deployments", "k8s.list_deployments"
        )
        for item in deployments:
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
        events, more_e = self._items(f"/api/v1/namespaces/{ns}/events", "k8s.list_events")
        for item in events:
            ts = item.get("lastTimestamp") or item.get("eventTime") or ""
            if not ts or not _within(ts, start, end):
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
        for kind, more in (("deployments", more_d), ("events", more_e)):
            if more:  # never present a cut list as the whole answer
                out.append(
                    {
                        "id": f"incomplete/{scope}/{kind}",
                        "kind": "incomplete",
                        "note": f"more than {self._cfg.page_size * self._cfg.max_pages} {kind}; the list is cut",
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
            f"?timestamps=true&sinceTime={quote(start, safe='')}&limitBytes={self._cfg.log_bytes}"
        )
        text = self._call(
            path, "k8s.pod_log", max_bytes=self._cfg.log_bytes + defaults.K8S_LOG_SLACK_BYTES
        )
        out: list[Record] = []
        lines = text.splitlines()
        for i, line in enumerate(lines):
            ts, _, rest = line.partition(" ")
            if _after(ts, end):
                break
            out.append({"id": f"log/{scope}/{pod}#{i}", "ts": ts, "line": rest})
            if len(out) >= limit:
                if i + 1 < len(lines):  # stopped at the caller's limit with lines left
                    out.append(
                        {
                            "id": f"log/{scope}/{pod}#limit",
                            "kind": "incomplete",
                            "note": f"stopped at the limit of {limit} lines; later lines exist",
                        }
                    )
                break
        else:
            if (
                len(text.encode("utf-8")) >= self._cfg.log_bytes
            ):  # the API cut the log at limitBytes
                out.append(
                    {
                        "id": f"log/{scope}/{pod}#cut",
                        "kind": "incomplete",
                        "note": f"the log was cut at {self._cfg.log_bytes} bytes; later lines are missing",
                    }
                )
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
            status = review.get("status")
            if not isinstance(status, dict) or not isinstance(status.get("resourceRules"), list):
                problems.append(
                    f"namespace {ns}: the rules review answered without status.resourceRules (not proven)"
                )
                continue
            if status.get(
                "evaluationError"
            ):  # the review could not evaluate every rule: not proven
                problems.append(f"namespace {ns}: the rules review reported an evaluation error")
            if status.get("incomplete"):
                problems.append(f"namespace {ns}: the rules review is incomplete, scope not proven")
            problems += rules_problems(ns, status["resourceRules"])
        return problems


# The permissions this kind needs. Data only: nothing here is run. `tools/policy_page.py` reads this literal
# from the source text. `tests/test_policy_guard.py` fails when it differs from the requests written above in
# the call shapes that test lists; a request sent in a way no rule of that test lists is not seen.
# `verified` = (date, source ids): the name and the path form were found, spelled so, in those vendor sources
# (the ids resolve in tests/fixtures/policy_sources_2026-11-11.txt). `confirmed_live` = accepted by a real
# account; None everywhere so far.
POLICY = {
    "platform": "kubernetes_rbac",
    "credential": {
        "how": (
            "The secret named by the source's `token_secret_name` setting: the fetch in `app.py` sends it as "
            "a bearer token, and only when that setting is set. Nothing in this code says it is a "
            "ServiceAccount token. Without it the request is sent unauthenticated. This module holds no "
            "credential."
        ),
        "lifetime": "long",
        "exception": (
            "Whether the token expires is decided by the cluster and the operator; this code cannot tell and "
            "does not shorten it. Use a token that expires. No ticket removes a "
            "long-lived token yet: ledger row BL-core-q8c1-lifetime tracks it."
        ),
    },
    "notes": (
        (
            "One Role and one RoleBinding per namespace in `namespaces`. Never a ClusterRole or a "
            "ClusterRoleBinding."
        ),
        (
            "At every start-up the kind asks the cluster what this identity may do and reports write verbs, "
            "the wildcard verb `*`, shell subresources and any read of `secrets`. It does not report the "
            "verb `watch`."
        ),
        (
            "The requests carry these query parameters and no others: `limit` and `continue` on the two "
            "list requests, `timestamps`, `sinceTime` and `limitBytes` on the log request. `watch` and "
            "`follow` are never sent, and a test refuses any other parameter written in this module. That "
            "none of these parameters changes the verb the request needs is a claim nobody has checked "
            "(see the claims column of R20 to R22)."
        ),
    ),
    "grants": (
        {
            "id": "R20",
            "name": "list",
            "resource": "apps/deployments in {namespaces}",
            "bound": (
                "Allows more than the reason says: `list` returns the whole Deployment objects, with every "
                "setting written in them (including any value set in the pod template), not only the "
                "revision and the images. A right cannot be limited to some fields of an object"
            ),
            "operations": (("k8s.list_deployments",),),
            "applies_when": "",
            "reason": "reads deployments, their rollout revision and images",
            "verified": ("2026-11-11", "K-AUTHZ", "K-SRC"),
            "confirmed_live": None,
            "claims_unverified": (
                "the query parameters `limit` and `continue` do not change the verb the request needs",
            ),
        },
        {
            "id": "R21",
            "name": "list",
            "resource": "core/events in {namespaces}",
            "bound": (
                "Allows more than the reason says: Kubernetes rights cannot be limited by time, so the right "
                "covers every event of each configured namespace, not only the time window the code asks for"
            ),
            "operations": (("k8s.list_events",),),
            "applies_when": "",
            "reason": "reads events in the time window",
            "verified": ("2026-11-11", "K-AUTHZ", "K-SRC"),
            "confirmed_live": None,
            "claims_unverified": (
                "the query parameters `limit` and `continue` do not change the verb the request needs",
            ),
        },
        {
            "id": "R22",
            "name": "get",
            "resource": "core/pods/log in {namespaces}",
            "bound": (
                "Allows more than the reason says: the right covers the log of every pod in each configured "
                "namespace, not one pod; a pod name list cannot be written in advance. Log lines can hold "
                "secrets, and what a log holds is outside this kind's control"
            ),
            "operations": (("k8s.pod_log",),),
            "applies_when": "",
            "reason": "reads one pod's log lines",
            "verified": ("2026-11-11", "K-RBAC", "K-SRC"),
            "confirmed_live": None,
            "claims_unverified": (
                "the query parameters `timestamps`, `sinceTime` and `limitBytes` do not change the verb the request needs",
            ),
        },
    ),
    "free": (
        {
            "operations": (("k8s.rules_review",),),
            "reason": (
                "asks the cluster what this identity may do; the start-up check treats it as harmless "
                "(that it changes nothing in the cluster was not found in a vendor source)"
            ),
            "note": (
                "a default cluster gives every signed-in identity this right. The request path names no "
                "namespace, so the namespaced Role on this page cannot grant it: in a cluster that took the "
                "right away, an administrator must grant `create` on `selfsubjectrulesreviews` with a "
                "cluster-wide role and binding of their own; this page produces no text for that and no test "
                "covers such a cluster"
            ),
            "verified": ("2026-11-11", "K-RBAC", "K-SRC", "K-SSRR"),
            "claims_unverified": (
                (
                    "a `create` on `selfsubjectrulesreviews` changes nothing in the cluster (the one source "
                    "for the resource, K-SSRR, does not say so)"
                ),
            ),
        },
    ),
    "never": (
        {
            "type": "role",
            "name": "cluster-admin",
            "reason": "a built-in role that may write",
            "verified": None,
        },
        {
            "type": "role",
            "name": "admin",
            "reason": "a built-in role that may write",
            "verified": None,
        },
        {
            "type": "role",
            "name": "edit",
            "reason": "a built-in role that may write",
            "verified": None,
        },
        {
            "type": "action",
            "name": "create",
            "reason": (
                "a write verb: this source only reads. One exception, the same one the start-up check "
                "makes: `create` on the self-review resources (`selfsubjectrulesreviews`, "
                "`selfsubjectaccessreviews`, `selfsubjectreviews`), which the start-up check treats as "
                "harmless; that these three requests write nothing was not found in a vendor source"
            ),
            "verified": ("2026-11-11", "K-AUTHZ"),
            "claims_unverified": (
                (
                    "`create` on `selfsubjectrulesreviews`, `selfsubjectaccessreviews` and "
                    "`selfsubjectreviews` writes nothing (the source for the first, K-SSRR, does not mention "
                    "the verb; none was found for the other two)"
                ),
            ),
        },
        {
            "type": "action",
            "name": "update",
            "reason": "a write verb: this source only reads",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "patch",
            "reason": "a write verb: this source only reads",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "delete",
            "reason": "a write verb: this source only reads",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "deletecollection",
            "reason": "a write verb: this source only reads",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "escalate",
            "reason": "lets the identity widen its own rights",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "bind",
            "reason": "lets the identity widen its own rights",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "action",
            "name": "impersonate",
            "reason": "lets the identity act as another one",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
        {
            "type": "resource",
            "name": "pods/exec",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-RBAC", "K-SRC"),
        },
        {
            "type": "resource",
            "name": "pods/attach",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-SRC"),
        },
        {
            "type": "resource",
            "name": "pods/portforward",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-SRC"),
        },
        {
            "type": "resource",
            "name": "pods/proxy",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-SRC"),
        },
        {
            "type": "resource",
            "name": "nodes/proxy",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-KUBELET"),
        },
        {
            "type": "resource",
            "name": "services/proxy",
            "reason": "opens a shell or a tunnel into a workload",
            "verified": ("2026-11-11", "K-SRC"),
        },
        {
            "type": "resource",
            "name": "secrets",
            "reason": "reading a secret reveals its value",
            "verified": ("2026-11-11", "K-AUTHZ"),
        },
    ),
}

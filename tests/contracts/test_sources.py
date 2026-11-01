"""Source contract suites (K5-core): one suite per interface, run against every adapter, with the neutral
KubernetesSource beside the recorded reference adapter."""

from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urlsplit

import pytest

from hadavin_sdk.sources import (
    ChangeSource,
    IncidentSource,
    LogsSource,
    MetricsSource,
    SourceError,
)
from hadavin_sdk.sources.kubernetes import READ_OPERATIONS, KubernetesSource, rules_problems
from tests.contracts import sources as suite
from tests.contracts.sources import ks

DEPLOYMENTS = {
    "items": [
        {
            "metadata": {
                "name": "checkout",
                "annotations": {"deployment.kubernetes.io/revision": "17"},
            },
            "spec": {
                "template": {"spec": {"containers": [{"image": "registry.example/checkout:2"}]}}
            },
        }
    ]
}
EVENTS = {
    "items": [
        {
            "metadata": {"name": "ev1"},
            "lastTimestamp": "2026-11-01T10:20:00Z",
            "reason": "ScalingReplicaSet",
            "message": "Scaled up replica set checkout-7 to 3",
            "involvedObject": {"name": "checkout"},
        },
        {"metadata": {"name": "old"}, "lastTimestamp": "2026-10-01T00:00:00Z", "reason": "Old"},
    ]
}
LOG = "\n".join(f"2026-11-01T10:0{i}:00Z line {i}" for i in range(5))


class TooLarge(OSError):
    too_large = True  # what ToolContext.fetch's refusal of an over-cap reply carries


class FakeApi:
    """The Kubernetes REST API as recorded answers, held to what the real fetch enforces: the operation's bound
    method and path, the response cap, and (for a POST) a JSON Content-Type, which a real API server needs. It
    pages lists by `limit` and `continue`. Keeps every call for the assertions."""

    def __init__(self, rules=None, fail=False, deployments=None) -> None:
        self.calls, self.fail, self.headers = [], fail, []
        self.deployments = deployments if deployments is not None else DEPLOYMENTS["items"]
        self.rules = rules or [{"verbs": ["get", "list", "watch"], "resources": ["pods", "events"]}]

    def _page(self, items, query):
        limit = int(query.get("limit", [len(items) or 1])[0])
        start = int(query.get("continue", ["0"])[0])
        page = {"items": items[start : start + limit]}
        if start + limit < len(items):
            page["metadata"] = {"continue": str(start + limit)}
        return json.dumps(page)

    def __call__(self, method, url, *, operation, body=None, headers=None, max_bytes=None):
        self.calls.append((method, url, operation))
        self.headers.append(headers or {})
        if self.fail:
            raise OSError("connection refused")
        bound_method, pattern = READ_OPERATIONS[operation]
        parts = urlsplit(url)
        assert method == bound_method and re.fullmatch(pattern, parts.path), (method, parts.path)
        if method == "POST":
            assert (headers or {}).get("Content-Type") == "application/json"
            assert json.loads(body)["kind"] == "SelfSubjectRulesReview"
        query = parse_qs(parts.query)
        if parts.path.endswith("/deployments"):
            text = self._page(self.deployments, query)
        elif parts.path.endswith("/events"):
            text = self._page(EVENTS["items"], query)
        elif parts.path.endswith("/log"):
            text = LOG
        elif parts.path.endswith("/selfsubjectrulesreviews"):
            text = json.dumps({"status": {"resourceRules": self.rules}})
        else:
            text = json.dumps({"items": []})
        cap = max_bytes or 16384  # what `ToolContext.fetch` allows when the caller names no cap
        if len(text.encode()) > cap:
            raise TooLarge(
                "the response is larger than the cap"
            )  # an explicit cap refuses, never cuts
        return text


def k8s(api=None) -> KubernetesSource:
    return ks(api or FakeApi(), ["prod"])


CASES = {
    "recorded": (suite.RecordedSource, suite.Case("prod", "prod/checkout", "error_rate", "INC-1")),
    "kubernetes": (k8s, suite.Case("prod", "prod/checkout")),
}


@pytest.fixture(params=sorted(CASES))
def adapter(request):
    make, case = CASES[request.param]
    return make(), case


def test_every_adapter_passes_the_suites_of_the_interfaces_it_implements(adapter):
    source, case = adapter
    ran = 0
    for protocol, check in (
        (ChangeSource, suite.check_change_source),
        (LogsSource, suite.check_logs_source),
        (MetricsSource, suite.check_metrics_source),
        (IncidentSource, suite.check_incident_source),
    ):
        if isinstance(source, protocol):
            check(source, case)
            ran += 1
    assert ran >= 2, "an adapter implements at least one interface beside the probe"


def test_the_recorded_adapter_implements_all_four():
    source = suite.RecordedSource()
    assert all(
        isinstance(source, p) for p in (ChangeSource, LogsSource, MetricsSource, IncidentSource)
    )


def test_kubernetes_implements_change_and_logs_only():
    source = k8s()
    assert isinstance(source, ChangeSource) and isinstance(source, LogsSource)
    assert not isinstance(source, MetricsSource) and not isinstance(source, IncidentSource)


def test_kubernetes_changes_carry_revision_images_and_windowed_events():
    changes = k8s().recent_changes("prod", suite.START, suite.END)
    by_id = {c["id"]: c for c in changes}
    assert by_id["deployment/prod/checkout"]["revision"] == "17"
    assert by_id["deployment/prod/checkout"]["images"] == ["registry.example/checkout:2"]
    assert "event/prod/ev1" in by_id and "event/prod/old" not in by_id


def test_kubernetes_makes_only_read_calls_and_the_one_review_post():
    api = FakeApi()
    source = k8s(api)
    source.recent_changes("prod", suite.START, suite.END)
    source.query_logs("prod/checkout", suite.START, suite.END, 3)
    source.probe_scope()
    assert {(m, op) for m, _, op in api.calls} == {
        ("GET", "k8s.list_deployments"),
        ("GET", "k8s.list_events"),
        ("GET", "k8s.pod_log"),
        ("POST", "k8s.rules_review"),
    }


def test_kubernetes_log_lines_after_the_window_are_dropped():
    rows = k8s().query_logs("prod/checkout", suite.START, "2026-11-01T10:02:30Z", 10)
    assert [r["line"] for r in rows] == ["line 0", "line 1", "line 2"]


def test_kubernetes_unconfigured_namespace_has_no_data_and_makes_no_call():
    api = FakeApi()
    source = k8s(api)
    assert source.recent_changes("kube-system", suite.START, suite.END) == []
    assert source.query_logs("kube-system/pod", suite.START, suite.END, 5) == []
    assert api.calls == []


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.recent_changes("prod", suite.START, suite.END),
        lambda s: s.query_logs("prod/checkout", suite.START, suite.END, 5),
        lambda s: s.probe_scope(),
    ],
)
def test_kubernetes_backend_failure_is_a_source_error(call):
    suite.check_failure_is_a_source_error(lambda: (k8s(FakeApi(fail=True)), call))


def test_kubernetes_malformed_answer_is_a_source_error():
    def junk(method, url, *, operation, body=None, headers=None, max_bytes=None):
        return "<html>not json</html>"

    with pytest.raises(SourceError, match="malformed"):
        ks(junk, ["prod"]).recent_changes("prod", suite.START, suite.END)


def test_kubernetes_needs_a_namespace_and_an_endpoint():
    from hadavin_sdk.sources.kubernetes import KubernetesSettings

    with pytest.raises(ValueError, match="namespaces"):
        ks(FakeApi(), [])
    with pytest.raises(ValueError, match="api_url"):
        KubernetesSettings(namespaces=("prod",))  # type: ignore[call-arg]  # no default endpoint in code
    with pytest.raises(ValueError, match="page_size"):
        ks(FakeApi(), page_size=0)


@pytest.mark.parametrize(
    ("rules", "needle"),
    [
        ([{"verbs": ["patch"], "resources": ["deployments"]}], "write verb patch"),
        ([{"verbs": ["create", "delete"], "resources": ["pods"]}], "write verb create, delete"),
        ([{"verbs": ["get"], "resources": ["pods/exec"]}], "access to pods/exec"),
        ([{"verbs": ["get"], "resources": ["pods/proxy"]}], "access to pods/proxy"),
        ([{"verbs": ["get"], "resources": ["nodes/proxy"]}], "access to nodes/proxy"),
        ([{"verbs": ["list", "watch"], "resources": ["secrets"]}], "read access to secrets"),
        ([{"verbs": ["get"], "resources": ["*"]}], "read access to secrets"),
        ([{"verbs": ["*"], "resources": ["pods"]}], "wildcard verb"),
        ([{"verbs": ["impersonate"], "resources": ["users"]}], "write verb impersonate"),
    ],
)
def test_the_rules_probe_names_each_forbidden_grant(rules, needle):
    assert any(needle in p for p in rules_problems("prod", rules)), rules_problems("prod", rules)


def test_a_read_only_rule_set_passes_the_probe():
    rules = [{"verbs": ["get", "list", "watch"], "resources": ["pods", "pods/log", "deployments"]}]
    assert rules_problems("prod", rules) == []
    assert k8s(FakeApi(rules)).probe_scope() == []


def test_an_incomplete_review_is_not_a_pass():
    def incomplete(method, url, *, operation, body=None, headers=None, max_bytes=None):
        return json.dumps({"status": {"incomplete": True, "resourceRules": []}})

    assert any("incomplete" in p for p in ks(incomplete, ["prod"]).probe_scope())


def test_the_probe_reviews_every_configured_namespace():
    api = FakeApi()
    ks(api, ["prod", "staging"]).probe_scope()
    assert [c[1].rsplit("/", 1)[-1] for c in api.calls] == ["selfsubjectrulesreviews"] * 2


def _answering(text):
    def fetch(method, url, *, operation, body=None, headers=None, max_bytes=None):
        return text

    return ks(fetch, ["prod"])


@pytest.mark.parametrize("answer", ["[]", "null", '"text"', "7"])
def test_kubernetes_non_object_answers_are_source_errors(answer):
    for call in (
        lambda s: s.recent_changes("prod", suite.START, suite.END),
        lambda s: s.probe_scope(),
    ):
        with pytest.raises(SourceError, match="malformed"):
            call(_answering(answer))


def test_kubernetes_oddly_shaped_items_are_source_errors():
    with pytest.raises(SourceError, match="malformed"):
        _answering('{"items": [1, 2]}').recent_changes("prod", suite.START, suite.END)
    # a rule that is not an object proves nothing: a problem, so the source is not used
    assert any(
        "malformed" in p for p in _answering('{"status": {"resourceRules": [7]}}').probe_scope()
    )


def test_kubernetes_null_pod_template_spec_is_not_an_error():
    def api(method, url, *, operation, body=None, headers=None, max_bytes=None):
        if "/deployments" in url:
            item = {"metadata": {"name": "d"}, "spec": {"template": {"spec": None}}}
            return json.dumps({"items": [item]})
        return json.dumps({"items": None})

    (found,) = ks(api, ["prod"]).recent_changes("prod", suite.START, suite.END)
    assert found["images"] == [] and found["id"] == "deployment/prod/d"


def test_kubernetes_post_carries_a_json_content_type():
    api = FakeApi()
    k8s(api).probe_scope()
    assert api.headers == [{"Content-Type": "application/json", "Accept": "application/json"}]


def test_kubernetes_a_real_sized_deployment_list_is_read_through_the_cap_and_pages():
    """150 deployments of about 3 KB each (450 KB) are far past a tool's 16 KB output cap: the source asks for a
    larger fetch cap and pages by 100, and still returns every deployment as a small record."""
    big = [
        {
            "metadata": {"name": f"d{i}", "annotations": {"note": "x" * 3000}},
            "spec": {"template": {"spec": {"containers": [{"image": f"img:{i}"}]}}},
        }
        for i in range(150)
    ]
    api = FakeApi(deployments=big)
    found = [
        c
        for c in k8s(api).recent_changes("prod", suite.START, suite.END)
        if c["kind"] == "deployment"
    ]
    assert len(found) == 150
    list_calls = [c for c in api.calls if c[2] == "k8s.list_deployments"]
    assert len(list_calls) == 8 and "continue=" in list_calls[1][1]  # 150 objects, 20 a page
    assert not any(
        c["kind"] == "incomplete" for c in k8s(api).recent_changes("prod", suite.START, suite.END)
    )


def test_kubernetes_a_response_over_the_cap_is_a_source_error_not_a_cut_json():
    big = [{"metadata": {"name": "d", "annotations": {"n": "x" * 2_000_000}}}]
    with pytest.raises(SourceError, match="TooLarge"):
        k8s(FakeApi(deployments=big)).recent_changes("prod", suite.START, suite.END)


def test_every_declared_operation_is_bound_to_a_method_and_a_path():
    for op, (method, pattern) in READ_OPERATIONS.items():
        assert method in {"GET", "POST"} and re.compile(pattern), op
    assert READ_OPERATIONS["k8s.rules_review"][0] == "POST"
    assert {m for m, _ in READ_OPERATIONS.values()} == {"GET", "POST"}

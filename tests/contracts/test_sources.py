"""Source contract suites (K5-core): one suite per interface, run against every adapter, with the neutral
KubernetesSource beside the recorded reference adapter."""

from __future__ import annotations

import json

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


class FakeApi:
    """The Kubernetes REST API as recorded answers; keeps every call for the assertions."""

    def __init__(self, rules=None, fail=False) -> None:
        self.calls, self.fail = [], fail
        self.rules = rules or [{"verbs": ["get", "list", "watch"], "resources": ["pods", "events"]}]

    def __call__(self, method, url, *, operation, body=None, headers=None):
        self.calls.append((method, url, operation))
        if self.fail:
            raise OSError("connection refused")
        assert operation in READ_OPERATIONS
        if url.endswith("/deployments"):
            return json.dumps(DEPLOYMENTS)
        if url.endswith("/events"):
            return json.dumps(EVENTS)
        if "/pods/" in url and "/log" in url:
            return LOG
        if url.endswith("/selfsubjectrulesreviews"):
            return json.dumps({"status": {"resourceRules": self.rules}})
        return json.dumps({"items": []})


def k8s(api=None) -> KubernetesSource:
    return KubernetesSource(api or FakeApi(), ["prod"])


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
    def junk(method, url, *, operation, body=None, headers=None):
        return "<html>not json</html>"

    with pytest.raises(SourceError, match="malformed"):
        KubernetesSource(junk, ["prod"]).recent_changes("prod", suite.START, suite.END)


def test_kubernetes_needs_a_namespace():
    with pytest.raises(ValueError, match="at least one namespace"):
        KubernetesSource(FakeApi(), [])


@pytest.mark.parametrize(
    ("rules", "needle"),
    [
        ([{"verbs": ["patch"], "resources": ["deployments"]}], "write verb patch"),
        ([{"verbs": ["create", "delete"], "resources": ["pods"]}], "write verb create, delete"),
        ([{"verbs": ["get"], "resources": ["pods/exec"]}], "access to pods/exec"),
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
    def incomplete(method, url, *, operation, body=None, headers=None):
        return json.dumps({"status": {"incomplete": True, "resourceRules": []}})

    assert any("incomplete" in p for p in KubernetesSource(incomplete, ["prod"]).probe_scope())


def test_the_probe_reviews_every_configured_namespace():
    api = FakeApi()
    KubernetesSource(api, ["prod", "staging"]).probe_scope()
    assert [c[1].rsplit("/", 1)[-1] for c in api.calls] == ["selfsubjectrulesreviews"] * 2

"""K1b: client data is masked before the model sees it (synthetic values only)."""

import json

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.bundle import load_bundles
from hadavin_sdk.k1b.redaction import LIMITS, STRUCTURAL_KEYS, redact_bundle
from tests.k1b_support import ScriptedLLM, calls_reply, make_bundle, submit, tool_reply
from tests.test_k1b_replay import Env, _with_k1b

# Synthetic stand-ins, one per class. None of these may reach the model.
EMAIL = "bob.smith@example.com"
IP = "10.20.30.40"
ACCT = "123456789012"
ARN = f"arn:aws:iam::{ACCT}:role/payments-admin"
HOST = "db01.corp.local"
APIKEY = "sk-ant-api03-" + "abcdefghijklmnopqrstuvwxyz0123456789"
AWSKEY = "AKIA" + "IOSFODNN7EXAMPLE"
UUID = "123e4567-e89b-12d3-a456-426614174000"
PERSON = "Rakesh Sharma"
SECRETS = [EMAIL, IP, ACCT, ARN, HOST, APIKEY, AWSKEY, UUID, PERSON, "Priya Nair"]

LOG_MSG = f"conn from {IP} to {HOST} by {EMAIL} role {ARN} token {APIKEY} {AWSKEY} req {UUID}"
PARTS = {
    "alert": {
        "title": f"High latency for Mr. {PERSON}",
        "severity": "page",
        "summary": f"account {ACCT} reported by {EMAIL}",
        "labels": {"team": "pay", "owner": f"Dear Priya Nair at {IP}"},
    },
    "logs": {
        "001": [
            {"ts": "2026-01-01T09:10:00Z", "level": "error", "message": LOG_MSG, "service": "api"},
            {
                "ts": "2026-01-01T09:20:00Z",
                "level": "error",
                "message": f"again {IP} {EMAIL}",
                "service": "db",
            },
        ]
    },
    "k8s": {
        "001": {
            "kind": "Deployment",
            "name": "api",
            "as_of": "2026-01-01T09:00:00Z",
            "spec": {"replicas": 3, "env": [{"owner": EMAIL}]},
            "events": [{"ts": "2026-01-01T09:01:00Z", "reason": "Scaled", "message": f"on {HOST}"}],
        }
    },
    "runbooks": {
        "001": (
            f"# Latency runbook\nPage {EMAIL} first\n\ncall Mr. {PERSON}",
            "2026-01-01T00:00:00Z",
        )
    },
}
SAW_ALL = [
    ("list_data", {}),
    ("query_logs", {}),
    ("get_deploys", {}),
    ("get_k8s", {}),
    ("get_runbook", {}),
    ("query_metrics", {"query": "cpu"}),
]


@pytest.fixture
def env(tmp_path, cfg_dir):
    e = Env(tmp_path, cfg_dir, cases=0)
    make_bundle(e.bundles, "case-001", **PARTS)
    return e


def _everything_sent(llm) -> str:
    return json.dumps([(c["system"], c["messages"], c["tools"]) for c in llm.calls])


def test_no_synthetic_secret_reaches_the_model(env):
    llm = ScriptedLLM([calls_reply(*SAW_ALL), submit("api", "bad_deploy", "logs/001.jsonl#0")])
    env.run(llm)
    sent = _everything_sent(llm)
    for secret in SECRETS:
        assert secret not in sent, secret
    assert "<EMAIL_1>" in sent and "<IPV4_1>" in sent  # the model sees stable placeholders
    # the same value is the same placeholder in the alert, a log, a k8s record and the runbook
    assert sent.count("<EMAIL_1>") >= 4


def test_evidence_ids_and_structure_are_unchanged_and_citations_verify(env):
    llm = ScriptedLLM([calls_reply(*SAW_ALL), submit("api", "bad_deploy", "logs/001.jsonl#0")])
    env.run(llm)
    rec = env.case()
    assert (
        rec["status"] == "ok" and "converted" not in rec
    )  # the cited id resolved, so no uncited conversion
    assert "logs/001.jsonl#0" in rec["returned_ids"] and "k8s/001.json#spec" in rec["returned_ids"]
    assert rec["diagnosis"]["causes"][0]["evidence_ids"] == ["logs/001.jsonl#0"]


def test_outputs_audit_and_report_hold_no_value(env):
    llm = ScriptedLLM([calls_reply(*SAW_ALL), submit("api", "bad_deploy", "logs/001.jsonl#0")])
    env.run(llm)
    blob = "".join(p.read_text(encoding="utf-8") for p in env.out.rglob("*") if p.is_file())
    blob += json.dumps([e.model_dump(mode="json") for e in env.sink.events()])
    for secret in SECRETS:
        assert secret not in blob, secret
    assert "<EMAIL_1>" not in blob.replace("distinct", "")  # no placeholder map either


def test_run_json_and_report_state_scheme_counts_and_limits(env):
    env.run(ScriptedLLM([calls_reply(*SAW_ALL), submit("api", "bad_deploy", "logs/001.jsonl#0")]))
    red = json.loads((env.out / "run1" / "run.json").read_text(encoding="utf-8"))["redaction"]
    assert red["mode"] == "on" and red["cases_with_masking"] == 1
    counts = red["distinct_values_masked"]
    assert (
        counts["EMAIL"] == 1 and counts["IPV4"] >= 1 and counts["ARN"] == 1 and counts["UUID"] == 1
    )
    assert all(isinstance(v, int) for v in counts.values())
    report = (env.out / "replay-report.md").read_text(encoding="utf-8")
    assert "## Redaction" in report and "EMAIL 1" in report and LIMITS in report
    assert "What the numbers cannot say" in report and "free text" in report


def test_timestamps_and_structural_values_survive(env):
    (bundle,) = load_bundles(env.bundles)
    masked, _ = redact_bundle(bundle)
    assert masked.alert_time == bundle.alert_time and masked.alert["severity"] == "page"
    assert [r["ts"] for _, rs in masked.logs for r in rs] == [
        r["ts"] for _, rs in bundle.logs for r in rs
    ]
    assert {r["service"] for _, rs in masked.logs for r in rs} == {"api", "db"}
    assert masked.k8s[0][1]["name"] == "api" and masked.ids == bundle.ids
    assert masked.logs[0][0] == bundle.logs[0][0]  # file names stay
    assert {"service", "kind", "name", "query"} <= STRUCTURAL_KEYS


def test_redaction_off_needs_the_acknowledgement_and_is_recorded(env):
    reg = _with_k1b(env.reg, redact=False)
    with pytest.raises(ConfigError, match="already masked"):
        env.run(ScriptedLLM([]), reg=reg)
    assert not env.out.exists()
    llm = ScriptedLLM([calls_reply(*SAW_ALL), submit("api", "bad_deploy", "logs/001.jsonl#0")])
    env.run(llm, reg=reg, acknowledge_masked=True)
    assert EMAIL in _everything_sent(llm)  # off means off: nothing was masked
    red = json.loads((env.out / "run1" / "run.json").read_text(encoding="utf-8"))["redaction"]
    assert red["mode"] == "off_acknowledged" and red["distinct_values_masked"] == {}
    assert "Redaction was OFF" in (env.out / "replay-report.md").read_text(encoding="utf-8")


def test_default_is_on():
    from hadavin_sdk.config import K1bSettings

    assert K1bSettings().redact is True


def test_tool_reply_for_a_masked_value_matches_nothing_in_the_original(env):
    """Queries run against the masked copy, so a query using a placeholder finds the masked line."""
    llm = ScriptedLLM(
        [
            tool_reply("query_logs", contains="<EMAIL_1>"),
            submit("api", "bad_deploy", "logs/001.jsonl#0"),
        ]
    )
    env.run(llm)
    assert "logs/001.jsonl#0" in env.case()["returned_ids"]

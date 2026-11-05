"""Documents must agree with code and data: counts are generated from the manifest and the code, one kill-switch rule, no stale claims."""

import json
import re
from pathlib import Path

from refunds import config, tools
from refunds.verdict import clopper_pearson, upper_bound_zero_wrong

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "failure_modes.md",
    "scoping.md",
    "eval-contract.md",
    "gate_rules.md",
    "runbook.md",
    "acceptance.md",
    "success-criteria.md",
    "stage2-decisions.md",
    "stage2-spec.md",
    "demo_only/demo-script.md",
)


def text(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_scorecard_numbers_in_the_docs_are_generated_from_the_manifest():
    c = json.loads((ROOT / "demo_only" / "data" / "manifest.json").read_text(encoding="utf-8"))["counts"]
    n = c["test_act"] + c["test_refuse"]
    one, two = f"{upper_bound_zero_wrong(n):.4f}", f"{clopper_pearson(0, n)[1]:.4f}"
    for doc in ("failure_modes.md", "scoping.md"):
        t = text(doc)
        assert str(n) in t and one in t and two in t, (doc, n, one, two)
    assert re.search(
        r"n_should_answer.{0,120}\*\*" + str(c["test_act"]) + r"\*\*", text("failure_modes.md")
    ) and f"smoke, n={c['test']}" in text("success-criteria.md")
    assert f"{c['cases']} cases" in text("scoping.md") and str(c["steered"]) in text("stage2-spec.md")


def test_counts_of_code_objects_in_the_docs_match_the_code():
    assert f"covers all {len(tools.HandBackReason.__args__)} values" in text("stage2-decisions.md") and len(
        config.HANDBACK_QUEUE
    ) == len(tools.HandBackReason.__args__)
    assert (
        "(27 rules)" in text("gate_rules.md")
        and len(re.findall(r"^\| R-REF-\d{3} \|", text("gate_rules.md"), re.MULTILINE)) == 27
    )


def test_one_kill_switch_rule_everywhere():
    for doc in DOCS + ("src/refunds/adapters/ports.py", "src/refunds/tools.py"):
        t = text(doc)
        for sentence in re.split(r"(?<=[.;])\s+|[\r\n]+", t):
            if re.search(r"kill[- ]switch", sentence, re.IGNORECASE):
                assert not re.search(r"\bvoids?\b", sentence, re.IGNORECASE) or re.search(
                    r"never|not (the )?kill|except|not void", sentence, re.IGNORECASE
                ), (doc, sentence[:160])
    for doc in ("runbook.md", "gate_rules.md", "src/refunds/adapters/ports.py"):
        t = text(doc)
        assert re.search(r"queued", t) and re.search(r"never void|never voids|they never void|HOLD", t), doc
    sc = {
        s["scenario_id"]: s for s in json.loads((ROOT / "demo_only" / "data" / "rule_scenarios.json").read_text(encoding="utf-8"))
    }
    assert "STAYS approved and queued" in sc["SC-06"]["cases"][0]["what"] and "never voids" in sc["SC-06"]["cases"][0]["what"]


def test_no_stale_claims_of_a_sealed_held_out_run_once_set():
    for doc in DOCS:
        t = text(doc)
        assert "run once" not in t.replace("run once; a bug", "").replace("run once, and a bug", "") or doc in (
            "eval-contract.md",
            "failure_modes.md",
        ), doc
        for m in re.finditer(r"(?i)sealed", t):
            window = t[max(0, m.start() - 40) : m.end() + 60].lower()
            assert any(
                k in window
                for k in ("not sealed", "second", "seal is gone", "sealed set needs", "blind", "truly sealed", "unsealed")
            ), (doc, window)
    assert "same templates, new values" not in text("eval-contract.md") or "same builders" in text("eval-contract.md")


def test_present_tense_test_claims_name_tests_that_exist():
    for name in (
        "tests/test_enumeration.py",
        "tests/test_ingest.py",
        "tests/test_isolation.py",
        "tests/test_segregation.py",
        "tests/test_purpose_blast_radius.py",
        "tests/test_identities.py",
        "tests/reference.py",
    ):
        assert (ROOT / name).exists(), name
    assert "658" in text("failure_modes.md")


def test_deny_code_gold_coverage_claim_matches_the_data():
    lines = (ROOT / "demo_only" / "data" / "dev.jsonl").read_text(encoding="utf-8").splitlines()
    assert (
        len({json.loads(x)["expected"]["deny_code"] for x in lines} - {None}) == 11 and len(config.DENY_RULE) == 39
    )  # test split: tests_oneshot
    assert "11 of the 39 deny codes" in text("failure_modes.md") and "11 of the 39 deny codes" in text("acceptance.md")

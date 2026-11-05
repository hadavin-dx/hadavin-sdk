"""Contract-level checks: strict export validator, rule ids exist, one exception table, dataset contract documents the semantics."""

from __future__ import annotations

import json
import re
from pathlib import Path

from intake.contract_checks import check_export
from intake.tools import ExceptionFlag

ROOT = Path(__file__).resolve().parents[1]
EXC = json.loads((ROOT / "config" / "exceptions.json").read_text())
GATE = (ROOT / "gate_rules.md").read_text(encoding="utf-8")
CASES = [json.loads(line) for sp in ("dev", "test") for line in (ROOT / "demo_only" / "data" / f"{sp}.jsonl").read_text().splitlines()]


def good_export() -> dict:
    return {
        "approvals": [
            {
                "approval_id": "a1",
                "tier": "four_eyes",
                "approvers": [{"role": "order_clerk"}, {"role": "sales_manager"}],
                "executed": {"port": "draft_store", "result": "ok"},
            },
            {"approval_id": "a2", "tier": "human", "executed": None},
        ],
        "cases": [{"case_id": "x", "outcome": "approved"}, {"case_id": "y", "outcome": "no_action", "tier": None}],
        "adapter_calls": [{"call_id": "c1", "port": "erp", "op": "get_stock"}, {"call_id": "c2", "port": "draft_store", "op": "put_draft"}],
    }


def test_clean_export_passes_and_each_violation_is_caught():
    assert check_export(good_export()) == []
    cases = [
        (lambda e: e["approvals"][0].update(tier="auto"), "never 'auto'"),
        (lambda e: e["cases"][0].update(outcome="auto_allowed"), "allowed set"),
        (lambda e: e["approvals"][0]["executed"].update(port="erp"), "draft_store"),
        (lambda e: e["adapter_calls"].append({"call_id": "c3", "port": "erp", "op": "create_order"}), "not an exact read"),
        (lambda e: e["adapter_calls"].append({"call_id": "c4", "port": "ERP", "op": "POST"}), "not an exact read"),
        (lambda e: e["adapter_calls"].append({"call_id": "c5", "port": "erp_rest", "op": "Get_Stock"}), "not an exact read"),
        (lambda e: e["approvals"][0].update(executed="draft_store"), "mapping or null"),
        (lambda e: e["approvals"][0].update(approvers=[{"role": "order_clerk"}]), "two approvers"),
        (lambda e: e["cases"][1].update(tier="auto"), "tier"),
        (lambda e: e.update(cases=[]), "empty"),
        (lambda e: e.pop("approvals"), "approvals: missing"),
        (lambda e: e.update(adapter_calls=None), "adapter_calls: missing"),
    ]
    for mutate, needle in cases:
        e = good_export()
        mutate(e)
        assert any(needle in x for x in check_export(e)), needle
    assert check_export({}) != []  # an empty export proves nothing


def test_gold_never_uses_auto_tier_or_auto_outcome():
    assert {c["expected"]["tier"] for c in CASES} <= {"human", "four_eyes", "blocked", None}
    assert {c["expected"]["outcome"] for c in CASES} == {"act", "abstain", "refuse", "no_action"}
    assert all(c["expected"]["outcome"] == "no_action" for c in CASES if c["expected"]["verdict"] == "matched")


def test_single_exception_table_and_rule_ids_exist_in_gate_rules():
    ids = set(re.findall(r"R-INTAKE-\d{3}", GATE))
    for code, v in EXC.items():
        for r in re.findall(r"R-INTAKE-\d{3}|(?<=/)\d{3}", v["rule"]):
            assert (r if r.startswith("R-") else f"R-INTAKE-{r}") in ids, (code, r)
    assert ExceptionFlag("X03", "R-INTAKE-005").code in EXC
    for c in CASES:
        assert set(c["expected"]["exceptions"]) <= set(EXC), c["case_id"]
    assert "D09" not in EXC and "reserved" in GATE.lower()
    assert EXC["X10"]["rule"] == "R-INTAKE-003/012/013"


def test_dataset_contract_documents_tier_semantics_and_fault_rules():
    ct = json.loads((ROOT / "demo_only" / "data" / "dataset_contract.json").read_text())
    assert "DATASET concept" in ct["tier_semantics"] and "never contains tier 'auto'" in ct["tier_semantics"]
    for rule in ct["fault_rules"].values():
        assert rule in set(re.findall(r"R-INTAKE-\d{3}", GATE))


def test_rule_ids_in_gate_rules_cover_1_to_24():
    assert {f"R-INTAKE-{n:03d}" for n in range(1, 25)} <= set(re.findall(r"R-INTAKE-\d{3}", GATE))


def test_hand_rederivation_ids_and_demo_script_ids_exist_and_demo_uses_dev_only():
    ids = {c["case_id"]: c["split"] for c in CASES}
    section6 = GATE.split("## 6.")[1].split("## 7.")[0]
    cited = set(re.findall(r"intake-[ehta]-\d{3}", section6))
    assert len(cited) >= 15 and cited <= set(ids)
    demo = (ROOT / "demo_only" / "demo_script.md").read_text(encoding="utf-8")
    shown = set(re.findall(r"intake-[ehta]-\d{3}", demo))
    assert shown <= set(ids) and all(ids[x] == "dev" for x in shown), "the sealed split is never used for a demo"

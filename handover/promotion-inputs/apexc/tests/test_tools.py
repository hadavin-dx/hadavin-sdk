"""Tool allowlist, adversarial replies, money-float AST scan, naive baseline, ports wiring. Offline."""

import ast
import json
from pathlib import Path

import pytest
from demo_loader import demo_file

from apexc.classify import classify_full, cumulative_minor, tier_for
from apexc.rules import proposal_denial
from apexc.tools import MODEL_TOOLS, TOOLS, check_tool_call

ROOT = Path(__file__).resolve().parents[1]
SC = {"invoice_id": "inv-1", "vendor_id": "v-001", "po_ids": [], "protected": []}


def test_release_and_hold_are_not_model_tools():
    assert "release_to_payment_queue" not in MODEL_TOOLS and "hold_payment" not in MODEL_TOOLS
    assert all("clock" not in t[0] and "advance" not in t[0] for t in TOOLS)
    assert {t[0] for t in TOOLS if t[3]} == MODEL_TOOLS


def scope_of(c):
    return {
        "invoice_id": c["invoice"]["invoice_id"],
        "vendor_id": (c["context"]["vendor"] or {}).get("vendor_id", "v-000"),
        "po_ids": c["invoice"]["po_refs"],
        "protected": [],
    }


def test_adversarial_replies_are_denied(cases, pol):
    adv = json.loads((demo_file("data", "adversarial.json")).read_text(encoding="utf-8"))
    by_id = {c["case_id"]: c for c in cases}
    assert {a["kind"] for a in adv} == {"tool_check", "proposal_check", "executor_property"} and len(adv) >= 20
    for a in adv:
        assert a["case_id"] in by_id and a["rule_id"].startswith("R-APEXC-")
        c = by_id[a["case_id"]]
        if a["kind"] == "tool_check":
            assert check_tool_call(a["call"]["name"], a["call"]["args"], scope_of(c)) == a["expect_reason"], a["id"]
        elif a["kind"] == "proposal_check":
            t, _ = classify_full(c, pol)
            tier = tier_for(t, c["invoice"]["currency"], cumulative_minor(c, pol), pol)
            args = {"amount_minor": c["invoice"]["total_minor"], "currency": c["invoice"]["currency"]} | {
                k: v for k, v in a["call"]["args"].items() if k != "amount"
            }
            if a["call"]["args"].get("amount") == "OTHER":
                args["amount_minor"] = "1"
            assert proposal_denial(args, t, tier, c["invoice"]["total_minor"], c["invoice"]["currency"], pol) == a["expect_reason"], a["id"]


def test_scope_is_required_and_reads_are_scoped_to_the_case():
    scope = {"invoice_id": "inv-1", "vendor_id": "v-001", "po_ids": ["PO-0101"], "protected": []}
    with pytest.raises(TypeError):
        check_tool_call("get_invoice", {"invoice_id": "inv-1"})  # the scope is not optional
    assert check_tool_call("get_invoice", {"invoice_id": "inv-1"}, scope) is None
    assert check_tool_call("get_invoice", {"invoice_id": "inv-2"}, scope) == "invoice_out_of_scope"
    assert (
        check_tool_call("get_po", {"po_id": "PO-0101"}, scope) is None
        and check_tool_call("get_po", {"po_id": "PO-0102"}, scope) == "po_out_of_scope"
    )
    assert check_tool_call("get_receipts", {"po_id": "PO-0102"}, scope) == "po_out_of_scope"
    assert check_tool_call("get_vendor", {"vendor_id": "v-002"}, scope) == "vendor_out_of_scope"
    assert check_tool_call("find_history", {"vendor_id": "v-002", "since": "2026-01-01"}, scope) == "vendor_out_of_scope"


def test_a_well_formed_call_passes_the_allowlist():
    ok = {
        "invoice_id": "inv-1",
        "kind": "resolution",
        "recommended_action": "await_vendor",
        "summary": "Price differs.",
        "amount_minor": "100",
        "currency": "USD",
    }
    assert check_tool_call("route_for_approval", ok, SC) is None
    assert check_tool_call("route_for_approval", {**ok, "recommended_action": "pay_now"}, SC) == "bad_enum:recommended_action"
    assert (
        check_tool_call("get_invoice", {"invoice_id": "inv-1"}, SC) is None
        and check_tool_call("get_invoice", {}, SC) == "missing_arg:invoice_id"
    )


def test_no_float_in_money_modules():
    """HZ-14: static scan of the money-path modules for float literals, float() calls and true division."""
    for name in ("normalise", "classify", "rules", "ports", "tools"):
        tree = ast.parse((ROOT / "src" / "apexc" / f"{name}.py").read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            assert not (isinstance(n, ast.Constant) and isinstance(n.value, float)), (name, n.lineno)
            assert not (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "float"), (name, n.lineno)
            assert not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)), (name, n.lineno)


def test_baseline_is_a_capability_table_not_a_score(cases, pol):
    import baseline  # demo_only/baseline.py (conftest puts it on the path when the folder exists)

    on_disk = json.loads((demo_file("data", "baseline.json")).read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(baseline.report(cases, pol)))
    assert "not a score" in on_disk["note"] and "labels are made by the rules" in on_disk["note"] and "not AI with no AI" in on_disk["note"]
    assert not any(k in on_disk for k in ("beyond_erp", "erp_native"))  # no headline split
    t = on_disk["capability_table"]
    assert all(d["standard_erp_validation"] == (k in baseline.ERP_NATIVE) for k, d in t.items())
    for k in ("bank_change", "duplicate_near", "new_vendor", "contact_change", "vendor_master_recent_edit", "payee_collision"):
        assert t[k]["standard_erp_validation"] is False and t[k]["baseline_detects"] == 0
    assert t["duplicate_exact"]["baseline_detects"] == t["duplicate_exact"]["cases"]  # no miss-rate threshold anywhere
    assert on_disk["baseline_implementation_gaps_on_standard_validations"]


def test_verdict_text_never_claims_accuracy():
    from apexc.rules import scorecard_verdict_color, scorecard_verdict_text

    for colour in ("green", "amber", "not_demonstrated", "aborted"):
        t = scorecard_verdict_text(colour)
        assert "plumbing" in t and "not a statement about live accuracy" in t
    assert scorecard_verdict_color("green", "scripted") == "amber" and scorecard_verdict_color("green", "live") == "green"
    assert scorecard_verdict_color("not_demonstrated", "scripted") == "not_demonstrated"


def test_non_ascii_digits_are_refused_in_tool_args():
    arabic = "".join(chr(0x0660 + int(c)) if c.isdigit() else c for c in "2026-10-20")
    assert check_tool_call("find_history", {"vendor_id": "v-001", "since": "2026-10-20"}, SC) is None
    assert check_tool_call("find_history", {"vendor_id": "v-001", "since": arabic}, SC) == "bad_pattern:since"

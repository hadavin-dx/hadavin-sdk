"""segregation: demo data, client data and anything learned stay segregated. Nothing learned from, or present in, one client or demo may change
another's outputs. Executed against the fakes; a canary is a unique string seeded into one client's data."""

import copy
import json
import re
from pathlib import Path

import pytest
from demo_loader import demo_files
from helpers import HarnessClock, approve_all, build, run_release, settle

from apexc.classify import classify_full
from apexc.fakes import Audit, FakeErp, FakePayments
from apexc.intake import Intake
from apexc.rules import forbidden_paths, namespace

ROOT = Path(__file__).resolve().parents[1]


def case_of(cases, recipe, split="dev"):
    return copy.deepcopy(next(c for c in cases if c["recipe"] == recipe and c["split"] == split))


def test_config_keys_carry_the_client_id_and_have_no_shared_namespace(pol):
    assert pol["client_id"] == "apexc-demo"
    for kind in pol["namespaces"]:
        assert namespace(pol, kind) == f"apexc-demo/{kind}"
    with pytest.raises(KeyError):
        namespace(pol, "shared")
    assert {"store", "index", "embeddings", "cache", "fewshot", "eval", "logs", "secrets", "model_config"} <= set(pol["namespaces"])


def test_nothing_in_apexc_reads_another_demos_data_eval_or_memory_paths(pol):
    """A static scan of the package, the generator and the tests for path fragments of other demos, the kit examples and the studio memory."""
    bad = []
    this = Path(__file__).name
    for f in [*(ROOT / "src" / "apexc").glob("*.py"), *demo_files("data", "gen.py"), *(ROOT / "tests").glob("*.py")]:
        if f.name == this:
            continue
        text = f.read_text(encoding="utf-8")
        for frag in forbidden_paths(pol):
            if frag in text:
                bad.append((f.name, frag))
    assert bad == [], bad
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "askdata" not in toml and "portal-kit" not in toml and "../" not in toml  # no dependency on another demo or the kit's data


def test_audit_chains_are_per_tenant_so_a_chain_never_carries_another_tenants_hash():
    solo, both = Audit(), Audit()
    for a in (solo, both):
        a.append("apexc-demo", "x", n=1)
    both.append("other-demo", "y", secret="CANARY-OTHER")
    solo.append("apexc-demo", "z", n=2)
    both.append("apexc-demo", "z", n=2)
    assert json.dumps(solo.chain("apexc-demo"), sort_keys=True) == json.dumps(both.chain("apexc-demo"), sort_keys=True)  # byte-identical
    assert "CANARY-OTHER" not in json.dumps(both.chain("apexc-demo")) and both.verify()


def run_apexc(cases, pol, with_other: bool):
    """The apexc flow end to end on one case, optionally with another demo's tenant sharing every piece of infrastructure."""
    c = case_of(cases, "self_edit")
    audit, intake = Audit(), Intake()
    other_canary = "CANARY-OTHER-DEMO-7731"
    if with_other:
        audit.append("other-demo", "seed", note=other_canary)
        intake.receive("other-demo", "m0", f"invoice {other_canary}".encode())
        o = FakeErp("other-demo", pol)
        o.vendors["v-001"] = {"name": other_canary, "bank": {"account": "OTHER-ACCT-1"}}
        o.rulings = [
            {
                "ruling_id": "rul-x",
                "invoice_id": c["invoice"]["invoice_id"],
                "ruling": "not_duplicate",
                "by": "u-ctl-01",
                "role": "finance_controller",
            }
        ]
        o.callbacks["cb-other"] = {"callback_id": "cb-other", "vendor_id": "v-001", "topic": "bank", "state": "confirmed"}
    erp, pay, clock, _, ex = build(c, pol, tenant=pol["client_id"], audit=audit)
    for mid, raw in (("m0", b"invoice a"), ("m1", b"invoice b POISON")):
        intake.receive(pol["client_id"], mid, raw)
    intake.drain(lambda raw: (_ for _ in ()).throw(ValueError("poison")) if b"POISON" in raw else "processed")
    settle(ex, erp, c, pol)
    out = ex.release(c["invoice"]["invoice_id"], approve_all(ex, c))
    view = {"out": out, "audit": audit.chain(pol["client_id"]), "export": intake.export(pol["client_id"]), "holds": erp.holds, "classify": sorted(classify_full(c, pol)[0]),
            "effects": sorted(k for k in intake.effects if k[0] == pol["client_id"])}  # fmt: skip
    return json.dumps(view, sort_keys=True, default=str), other_canary, audit, intake, pay


def test_apexc_outputs_are_byte_identical_with_the_other_demo_absent_and_no_canary_leaks(cases, pol):
    alone, canary, *_ = run_apexc(cases, pol, with_other=False)
    together, canary2, audit, intake, pay = run_apexc(cases, pol, with_other=True)
    assert alone == together  # A's results do not change when B's data changes or exists
    assert (
        canary not in together
        and canary2 not in json.dumps(audit.chain(pol["client_id"]))
        and canary not in json.dumps(intake.export(pol["client_id"]), default=str)
    )
    assert canary in json.dumps(audit.chain("other-demo")) and canary in json.dumps(
        intake.export("other-demo"), default=str
    )  # it IS in the other tenant's own rows


def test_apexc_canaries_never_reach_another_tenant_view_or_log_or_cache(cases, pol):
    c = case_of(cases, "self_edit")
    canary = "CANARY-APEXC-VENDOR-91827"
    c["context"]["vendor"]["name"] = canary  # seeded into the vendor master
    c["context"]["rulings"] = [
        {
            "ruling_id": "rul-c",
            "invoice_id": c["invoice"]["invoice_id"],
            "history_id": "h",
            "ruling": "not_duplicate",
            "by": "u-ctl-01",
            "role": "finance_controller",
            "note": canary,
        }
    ]
    c["scenario"]["callbacks"] = [
        {"callback_id": "cb-c", "vendor_id": c["context"]["vendor"]["vendor_id"], "topic": "bank", "state": "confirmed", "note": canary}
    ]
    audit, intake = Audit(), Intake()
    erp = FakeErp(pol["client_id"], pol)
    erp.vendors["v-x"] = c["context"]["vendor"]
    erp.rulings, erp.callbacks = c["context"]["rulings"], {"cb-c": c["scenario"]["callbacks"][0]}
    audit.append(pol["client_id"], "feedback", text=canary)  # feedback / eval example
    intake.receive(pol["client_id"], "m0", f"memo {canary}".encode())
    other = FakeErp("other-demo", pol)
    assert other.all_vendors() == [] and other.rulings == [] and other.callbacks == {} and other.holds == {} and other.history == {}
    assert canary not in json.dumps(audit.chain("other-demo")) and canary not in json.dumps(intake.export("other-demo"), default=str)
    pay_other = FakePayments("other-demo", c["context"]["directory"], pol)
    assert pay_other.rows == {} and canary not in json.dumps(other.__dict__, default=str)
    assert canary in json.dumps(intake.export(pol["client_id"]), default=str)


def test_one_clients_vendor_master_and_rulings_never_feed_another_clients_rules(cases, pol):
    """Client B has a related-vendor link, a ruling and a verification for the SAME vendor and invoice ids; client A's classification must
    be the same as if B did not exist, because the classifier only ever sees A's own context."""
    c = case_of(cases, "payee_collision")
    before = classify_full(c, pol)
    b = FakeErp("client-b", pol)
    v = copy.deepcopy(c["context"]["vendor"])
    v["related_vendors"] = [{"vendor_id": o["vendor_id"], "attested_by": "u-ctl-01", "ts": "t"} for o in c["context"]["other_vendors"]]
    b.vendors[v["vendor_id"]] = v
    b.rulings = [
        {
            "ruling_id": f"rul-{c['invoice']['invoice_id']}",
            "invoice_id": c["invoice"]["invoice_id"],
            "ruling": "not_duplicate",
            "by": "u-ctl-01",
            "role": "finance_controller",
        }
    ]
    a = FakeErp("client-a", pol)
    a.vendors[v["vendor_id"]] = c["context"]["vendor"]
    assert a.vendors[v["vendor_id"]].get("related_vendors") == [] and a.rulings == [] and b.rulings
    assert (
        b.vendors[v["vendor_id"]]["related_vendors"] and b.vendors[v["vendor_id"]] is not a.vendors[v["vendor_id"]]
    )  # no shared mutable state between clients
    assert classify_full(c, pol) == before == ({"bank_change", "payee_collision"}, set())
    # and the dup rule uses only this invoice's own ledger: the same ruling id in another client changes nothing
    d = case_of(cases, "ruling_exact_supervisor")
    assert "duplicate_exact" in classify_full(d, pol)[0]


def test_executor_outputs_do_not_depend_on_another_tenants_activity(cases, pol):
    c = case_of(cases, "clean_match")
    out_alone, ex, erp, pay = run_release(c, pol)
    erp2, pay2, clock2, audit2, ex2 = build(c, pol)
    for t in range(5):  # five other tenants hammer their own payments with the same keys and numbers
        px = FakePayments(f"other-{t}", c["context"]["directory"], pol)
        px.enqueue(
            "executor_enqueue",
            {
                "vendor_id": "v-001",
                "invoice_id": "inv-x",
                "invoice_number": "HF-1",
                "currency": "USD",
                "total_minor": "100",
                "po_key": "P",
                "received_day": "2026-10-20",
            },
            "k",
            [],
        )
    out_with, *_ = run_release(c, pol)
    assert out_alone == out_with == "queued" and re.fullmatch(r"queued", out_with)
    _ = (HarnessClock, erp2, pay2, clock2, audit2, ex2, pay, erp, ex)

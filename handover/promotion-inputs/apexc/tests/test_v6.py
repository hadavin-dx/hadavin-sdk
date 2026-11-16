"""Regression tests for the two fresh reviews of v5 : the stale
callback record (B-1), the SoD gaps (M-1), typed failures (M-2), the audit outage after the money moved (M-3), the append-only callback
ledger (M-4), tenant in every key (M-5), shared and durable controls (M-6), wired controls (M-7) and the design items. Each has a mutant in
mutation_check.py that reverts its fix."""

import ast
import copy
import re
import threading
import time
from datetime import timedelta
from pathlib import Path

import pytest
from demo_loader import demo_files
from helpers import approve_all, build, settle
from test_attacks import _bank_world, _cb, case_of, forge, world

from apexc.classify import evidence_fresh
from apexc.executor import LIFT, ApprovalRefused, ControlState, Executor
from apexc.fakes import Audit, FakeCallout, FakeErp, FakePayments
from apexc.normalise import fmt_ts, parse_ts
from apexc.ports import AdapterTimeout, FaultSchedule, FaultStep, release_key
from apexc.rules import roster_gap

ROOT = Path(__file__).resolve().parents[1]
STAGE2_ONLY = {
    "forbidden_paths",
    "model_view",
    "namespace",
    "proposal_denial",
    "purpose_of",
    "render_undo_command",
    "scorecard_verdict_color",
    "scorecard_verdict_text",
}


# ---- B-1: evidence must be newer than the change it clears -----------------------------------------------------
def test_b1_an_old_confirmed_callback_cannot_clear_a_new_bank_change(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    changed = parse_ts(c["context"]["vendor"]["bank"]["changed_at"])
    erp.callbacks["cb-old"] = _cb(
        c, "cb-old", "bank", "u-trs-01", ts=fmt_ts(changed - timedelta(days=30))
    )  # confirmed, trusted phone, valid attester
    assert not ex.clear(inv, "bank_change", clearer, "cb-old")
    # the back door: a forged clear row on the old record, the hold forged open, 100 hours later -> the release re-proves it and refuses
    erp.record_clear(LIFT, {"invoice_id": inv, "type": "bank_change", "by": clearer, "evidence_id": "cb-old", "kind": "clear"})
    for t in list(erp.open_holds(inv)):
        erp.lift_hold(LIFT, inv, t, clearer, {"evidence_id": "cb-old"})
    ex.clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(hours=100))) if hasattr(ex.clock, "set") else None
    ids = [forge(erp, c, pol, "u-ctl-02", "plan_1"), forge(erp, c, pol, "u-trs-02", "plan_2")]
    assert ex.release(inv, ids) == "denied:clear_evidence_invalid" and ex.payments.applies == 0
    # a record made after the change is accepted
    erp.callbacks["cb-new"] = _cb(c, "cb-new", "bank", "u-trs-01", ts=fmt_ts(changed + timedelta(days=1)))
    assert evidence_fresh("bank", erp.callbacks["cb-new"]["ts"], erp.read_case(inv)["context"], pol)


def test_b1_a_later_master_event_voids_earlier_evidence(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    ctx = erp.read_case(inv)["context"]
    ts = fmt_ts(parse_ts(c["context"]["vendor"]["bank"]["changed_at"]) + timedelta(days=2))
    assert evidence_fresh("bank", ts, ctx, pol)
    ctx["vendor_master_events"].append(
        {
            "vendor_id": "v",
            "field": "bank_account",
            "ts": fmt_ts(parse_ts(ts) + timedelta(hours=1)),
            "user": "u-mda-01",
            "verification": None,
        }
    )
    assert not evidence_fresh("bank", ts, ctx, pol)  # a bank edit AFTER the callback voids it
    ctx["vendor_master_events"].append(
        {"vendor_id": "v", "field": "po_exempt", "ts": fmt_ts(parse_ts(ts) + timedelta(hours=1)), "user": "u-mda-01", "verification": None}
    )
    assert not evidence_fresh("master_edit", ts, ctx, pol)
    assert evidence_fresh("master_edit", fmt_ts(parse_ts(ts) + timedelta(days=1)), ctx, pol)
    ctx["vendor"]["contact"]["phone_changed_at"] = fmt_ts(parse_ts(ts) + timedelta(hours=1))
    assert not evidence_fresh("contact", ts, ctx, pol)


# ---- M-1: SoD over every actor ------------------------------------------------------------------------------------
def test_m1_the_new_vendor_attester_cannot_also_approve(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "new_vendor_large")
    inv = c["invoice"]["invoice_id"]
    ver = next(r for r in erp.clears if r["invoice_id"] == inv and r["kind"] == "verify")
    attester = erp.read_case(inv)["context"]["callbacks"][ver["evidence_id"]]["attested_by"]
    ids = [
        ex.approve(inv, "u-sup-02", "plan_1")["approval_id"],
        ex.approve(inv, attester, "plan_2")["approval_id"],
    ]  # plan 1 is a third person: only the attester overlap is left
    assert ex.release(inv, ids) == "denied:sod"


def test_m1_a_master_editor_takes_no_approval_step_even_through_a_second_account(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    d = c["context"]["directory"]
    other = next(u for u, r in d.items() if r["employee_id"] == d["u-sup-03"]["employee_id"] and u != "u-sup-03")  # u-ap-03: same person
    erp.cases[inv]["context"]["vendor_master_events"].append(
        {"vendor_id": "v", "ts": c["context"]["now"], "user": other, "field": "payment_terms", "verification": None}
    )
    ids = [ex.approve(inv, "u-sup-03", "plan_1")["approval_id"], ex.approve(inv, "u-trs-01", "plan_2")["approval_id"]]
    assert ex.release(inv, ids) == "denied:sod"


def test_m1_a_second_lifter_who_also_signs_plan_2_is_refused(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    erp.holds.setdefault(inv, []).append({"reason": "price_variance", "open": False, "actor": "system", "placed_at": "", "lifted_by": "u-sup-01",
                                          "evidence": {"second_lifter": "u-trs-01"}})  # fmt: skip
    ids = [ex.approve(inv, "u-sup-02", "plan_1")["approval_id"], ex.approve(inv, "u-trs-01", "plan_2")["approval_id"]]
    assert ex.release(inv, ids) == "denied:sod"


# ---- M-2: typed failures ---------------------------------------------------------------------------------------------
def test_m2_a_malformed_ledger_record_is_a_typed_denial_not_a_keyerror(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    erp.callbacks["cb-bad"] = {
        "callback_id": "cb-bad",
        "vendor_id": c["context"]["vendor"]["vendor_id"],
        "topic": "bank",
        "state": "confirmed",
    }  # no ts, no attester
    assert safe(ex.clear, inv, "bank_change", clearer, "cb-bad") is False
    assert not any(e["kind"] == "internal_error" for e in ex.audit.events)  # the RULE refused it; the guard was not needed


def safe(fn, *a):
    """Call and turn a raw exception into a string, so a mutant that lets one escape fails an ASSERTION (not a crash)."""
    try:
        return fn(*a)
    except Exception as e:  # noqa: BLE001
        return "RAISED:" + type(e).__name__


def test_m2_unexpected_failures_become_denied_internal_error_with_an_audit_event(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    inv = c["invoice"]["invoice_id"]
    assert ex.change_config(
        "u-ctl-01", "u-ctl-02", "drop a limit", lambda p, d: p["limits"].pop("release_minor_per_day")
    )  # a missing limit
    ids = approve_all(ex, c)
    assert safe(ex.release, inv, ids) == "denied:internal_error"
    assert any(e["kind"] == "internal_error" and e["method"] == "release" for e in audit.events)
    c2, erp2, pay2, clock2, audit2, ex2 = world(cases, pol, "clean_match")
    ids2 = approve_all(ex2, c2)
    del ex2.erp.cases[c2["invoice"]["invoice_id"]]["invoice"][
        "currency"
    ]  # a malformed ledger row (the directory itself can no longer be edited)
    assert safe(ex2.release, c2["invoice"]["invoice_id"], ids2) == "denied:internal_error"


def test_m2_unknown_ids_are_typed_on_every_public_method(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match", do_settle=False)
    assert safe(ex.release, "inv-none", []) == "denied:unknown_invoice"
    assert safe(ex.place_holds, "inv-none") == [] and safe(ex.lift, "inv-none", "x", "u-sup-01", "confirm_receipt") is False
    assert safe(ex.clear, "inv-none", "bank_change", "u-ctl-01", "cb") is False
    with pytest.raises(ApprovalRefused):
        ex.approve("inv-none", "u-sup-01", "plan_1")
    assert safe(ex.compensate, "no-such-key", "finance_controller") == "denied:unknown_key"
    assert safe(ex.reconcile, "no-such-key") == "denied:internal_error"
    assert safe(ex.reject, "inv-none", "u-sup-01", "hist") is False


# ---- M-3: audit outage after the money moved; audit events for every step -------------------------------------------------
def test_m3_an_audit_outage_after_the_enqueue_leaves_the_payment_undoable(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    audit.fail_kinds = {"release_result", "approvals_consumed"}
    assert ex.release(inv, ids) == "queued" and pay.applies == 1  # the caller is told the truth, not given an exception
    key = ex._key(inv)
    assert key in ex.queued_at and len(ex.state.audit_backlog) == 2  # the durable marker came first; the events wait
    assert ex.compensate(key, "finance_controller") == "dequeued"
    audit.fail_kinds = set()
    assert ex.flush_audit() >= 2 and any(e["kind"] == "release_result" for e in audit.events)


def test_m3_reconcile_after_a_lost_answer_records_the_queue_time_and_returns_a_failed_reservation(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    real_enqueue = pay.enqueue

    def lost_answer(*a, **k):
        real_enqueue(*a, **k)  # the payment IS queued ...
        raise AdapterTimeout("answer lost", ambiguous=True)  # ... but the caller never hears it, every time

    pay.enqueue = lost_answer
    settle(ex, erp, c, pol)
    ids = approve_all(ex, c)
    real = pay.lookup
    pay.lookup = lambda k: None  # the port cannot answer: ambiguous, the row stays pending
    assert ex.release(c["invoice"]["invoice_id"], ids) == "handed_back:unknown_outcome"
    pay.lookup = real
    key = ex._key(c["invoice"]["invoice_id"])
    assert ex.reconcile(key) == "applied" and key in ex.queued_at and ex.compensate(key, "finance_controller") == "dequeued"
    c2 = case_of(cases, "clean_match", "test")
    e2, p2, k2, a2, x2 = build(c2, pol, schedule=FaultSchedule(1, tuple(FaultStep(i, "timeout_before_apply") for i in range(1, 6))))
    settle(x2, e2, c2, pol)
    assert x2.release(c2["invoice"]["invoice_id"], approve_all(x2, c2)) == "handed_back:unknown_outcome"
    assert sum(x2.count_by_day.values()) == 1
    assert (
        x2.reconcile(x2._key(c2["invoice"]["invoice_id"])) == "retry_safe" and sum(x2.count_by_day.values()) == 0
    )  # the cap reservation is returned


def test_m3_every_approval_denial_ruling_and_consume_is_an_audit_event(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "price_over")
    inv = c["invoice"]["invoice_id"]
    kinds = lambda: {e["kind"] for e in audit.events}  # noqa: E731
    ids = approve_all(ex, c)
    assert "approval_recorded" in kinds()
    with pytest.raises(ApprovalRefused):
        ex.approve(inv, "u-ghost", "plan_1")
    assert "approval_refused" in kinds()
    assert ex.release(inv, ids[:0]).startswith("denied") and "release_denied" in kinds()
    assert ex.release(inv, ids) == "queued" and {"approvals_consumed", "release_result"} <= kinds()
    c2 = case_of(cases, "exact_dup")
    e2, p2, k2, a2, x2 = build(c2, pol)
    settle(x2, e2, c2, pol)
    assert "ruling_recorded" in {e["kind"] for e in a2.events}


def test_m3_callback_attested_records_who_and_when(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    vid = c["context"]["vendor"]["vendor_id"]
    co.request_confirmation("agent_runtime", vid, "confirm_bank_details", {"invoice_number": "A1", "account_last4": "1234"}, "k1")
    co.attest("attest_callback_capability", "k1", "u-trs-01")
    ev = next(e for e in audit.events if e["kind"] == "callback_attested")
    assert (ev.get("attested_by"), ev.get("ts"), ev.get("state")) == ("u-trs-01", clock.now(), "confirmed")


# ---- M-4: the callback ledger is append-only -----------------------------------------------------------------------------
def test_m4_a_second_attestation_never_overwrites_the_first(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    vid = c["context"]["vendor"]["vendor_id"]
    co.request_confirmation("agent_runtime", vid, "confirm_bank_details", {"invoice_number": "A1", "account_last4": "1234"}, "k1")
    first = co.attest("attest_callback_capability", "k1", "u-trs-01")
    clock.advance(600)
    with pytest.raises(ValueError):
        co.attest("attest_callback_capability", "k1", "u-ctl-01", state="denied")
    assert erp.callbacks[first["callback_id"]] == first  # state, attester and time are as first written
    with pytest.raises(ValueError):
        co.attest("attest_callback_capability", "no-such-ticket", "u-ctl-01")
    with pytest.raises(ValueError):
        erp.add_callback("attest_callback_capability", first)


# ---- M-5: tenant in every key ------------------------------------------------------------------------------------------------
def test_m5_two_tenants_cannot_share_a_release_key_or_be_wired_together(cases, pol):
    assert release_key("acme", "inv-1") != release_key("globex", "inv-1")
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol, tenant="acme")
    with pytest.raises(ValueError):
        Executor(erp, FakePayments("globex", c["context"]["directory"], pol), clock, audit, pol, c["context"]["directory"])


# ---- M-6: shared and durable controls, TOCTOU, fail-closed level ----------------------------------------------------------------
def test_m6_kill_switch_caps_and_rows_survive_a_restart(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "queued"
    blob = ex.state.to_json()
    ex2 = Executor(erp, pay, clock, audit, pol, c["context"]["directory"], live=True, state=ControlState.from_json(blob), rebind=True)
    assert ex2.release(inv, ids) == "duplicate_ignored" and sum(ex2.count_by_day.values()) == 1  # the row and the cap came back
    assert ex2.compensate(ex._key(inv), "finance_controller") == "dequeued"
    assert ex2.release(inv, ids) == "dequeued"  # a second worker does not call a dequeued payment queued
    ex2.engage_kill_switch("finance_controller", dequeue_queued=False)
    ex3 = Executor(
        erp, pay, clock, audit, pol, c["context"]["directory"], live=True, state=ControlState.from_json(ex2.state.to_json()), rebind=True
    )
    assert ex3.killed and ex3.release(inv, ids) == "denied:kill_switch"


def test_m6_the_kill_switch_stops_approvals_and_lifts_dequeues_the_queue_and_needs_two_people_to_lift(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    assert ex.release(inv, approve_all(ex, c)) == "queued"
    c2 = case_of(cases, "price_over", "test")
    erp.cases[c2["invoice"]["invoice_id"]] = c2
    erp.vendors[c2["context"]["vendor"]["vendor_id"]] = c2["context"]["vendor"]
    ex.place_holds(c2["invoice"]["invoice_id"])  # an open hold that a valid ruling could lift if the switch were off
    out = ex.engage_kill_switch("finance_controller")
    assert out == [(ex._key(inv), "dequeued")] and pay.lookup(ex._key(inv))["status"] == "dequeued"
    with pytest.raises(ApprovalRefused):
        ex.approve(inv, "u-sup-01", "plan_1")
    assert ex.lift(c2["invoice"]["invoice_id"], "price_variance", "u-sup-01", "accept_price_variance") is False
    assert erp.open_holds(c2["invoice"]["invoice_id"]) == ["price_variance"]
    assert (
        not ex.reenable("u-ctl-01", "u-ctl-01") and not ex.reenable("u-ctl-01", "u-sup-01") and ex.killed
    )  # one person, or a non-kill-switch role
    assert ex.reenable("u-ctl-01", "u-trs-01") and not ex.killed
    assert any(e["kind"] == "kill_switch_released" for e in audit.events)


def test_m6_the_enqueue_recheck_reads_the_world_again(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    real = ex.store.execute

    def swap_then_execute(*a, **k):
        erp.vendors[c["context"]["vendor"]["vendor_id"]]["bank"]["account"] = "ATTACKER0002"  # between the gates and the enqueue
        return real(*a, **k)

    ex.store.execute = swap_then_execute
    assert ex.release(inv, ids).startswith("denied:") and pay.applies == 0


def test_m6_an_unknown_level_fails_closed(cases, pol):
    c = case_of(cases, "clean_match")
    for lvl in ("autonomous", "", "SUGGEST"):
        with pytest.raises(ValueError):
            build(c, pol, level=lvl)
    erp, pay, clock, audit, ex = build(c, pol)
    ex.level = "autonomous"  # even if it is changed after construction
    assert ex.release(c["invoice"]["invoice_id"], []) == "denied:level_unknown"


# ---- M-7: wired controls ----------------------------------------------------------------------------------------------------------
def test_m7_the_per_person_approver_cap_is_atomic_under_a_burst(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    res, bar = [], threading.Barrier(20)
    real_record = erp.record_approval
    erp.record_approval = lambda *a, **k: (time.sleep(0.01), real_record(*a, **k))[
        1
    ]  # widen the window between the cap check and the write
    ids = []
    for i in range(20):
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-cap-{i}"
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        ids.append(cc["invoice"]["invoice_id"])

    def w(i):
        bar.wait()
        try:
            ex.approve(i, "u-sup-01", "plan_1")
            res.append("ok")
        except ApprovalRefused as e:
            res.append(str(e))

    ts = [threading.Thread(target=w, args=(i,)) for i in ids]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert res.count("ok") == pol["tiers"]["approver_cap_per_vendor_window"] and res.count("approver_cap") == 17


def test_m7_one_person_cannot_alone_release_more_than_the_daily_total_at_tier_human(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["tiers"].update(approver_cap_per_vendor_window=1000, approver_cap_long=1000)
    c, erp, pay, clock, audit, ex = world(cases, p2, "clean_match")
    cur = c["invoice"]["currency"]
    total = int(c["invoice"]["total_minor"])
    cap = total * 2 + 1
    assert ex.change_config("u-ctl-01", "u-ctl-02", "daily total", lambda p, d: p["limits"]["approver_daily_minor"].update({cur: cap}))
    ok = 0
    for i in range(4):
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-day-{i}"
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        try:
            ex.config_version  # noqa: B018
            ex.approve(cc["invoice"]["invoice_id"], "u-sup-01", "plan_1")
            ok += 1
        except ApprovalRefused as e:
            assert str(e) == "approver_daily_total"
    assert ok == 2 and cap > 0


def test_m7_hold_pressure_and_the_roster_are_wired_into_place_holds(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["holds"]["max_open_invoices_per_vendor"] = 2
    c, erp, pay, clock, audit, ex = world(cases, p2, "price_over", do_settle=False)
    for i in range(3):
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-hp-{i}"
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        ex.place_holds(cc["invoice"]["invoice_id"])
    assert any(e["kind"] == "hold_pressure" for e in ex.escalations) and any(e["kind"] == "hold_pressure" for e in audit.events)
    small = {
        "u-a": {"employee_id": "E1", "roles": ["finance_controller"]},
        "u-b": {"employee_id": "E2", "roles": ["treasury_officer"]},
        "u-s": {"employee_id": "E3", "roles": ["ap_clerk"]},
    }
    assert roster_gap(small, "u-s") == ["two finance_controller people", "four distinct controller/treasury people"]
    bigger = c["context"]["directory"]
    small = {
        u: bigger[u] for u in ("u-ap-02", "u-ctl-01", "u-trs-01", "u-mda-01", "u-sup-03")
    }  # a real client's people, but only one controller
    assert roster_gap(c["context"]["directory"], c["invoice"]["submitted_by"]) == []
    cb, eb, pb, kb, ab, xb = world(cases, pol, "bank_remit", do_settle=False)
    assert xb.change_config("u-ctl-01", "u-ctl-02", "a small client", lambda p, dr: (dr.clear(), dr.update(small)))
    xb.place_holds(cb["invoice"]["invoice_id"])
    assert any(e["kind"] == "roster_gap" for e in xb.escalations) and any(e["kind"] == "escalate_external" for e in ab.events)


def test_m7_every_public_helper_and_policy_key_is_read_by_real_code():
    """AST, not text search: a docstring or a comment does not count as a use. Public helpers of rules.py must be called from another
    module (or gen.py); every policy key must appear as a string constant outside docstrings."""
    import json

    def strings(path):
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        doc = {
            id(n.body[0].value)
            for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef))
            and n.body
            and isinstance(n.body[0], ast.Expr)
            and isinstance(getattr(n.body[0], "value", None), ast.Constant)
        }
        return {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc}

    def names(path):
        return {n.id for n in ast.walk(ast.parse(Path(path).read_text(encoding="utf-8"))) if isinstance(n, ast.Name)} | {
            a.name for n in ast.walk(ast.parse(Path(path).read_text(encoding="utf-8"))) if isinstance(n, ast.ImportFrom) for a in n.names
        }

    if not demo_files("data", "gen.py"):
        pytest.skip("the generator in demo_only/ reads some helpers; without it the dead-helper list differs")
    src = [p for p in (ROOT / "src" / "apexc").glob("*.py")] + demo_files("data", "gen.py")
    used = set().union(*(names(p) for p in src))
    rules_funcs = [
        n.name
        for n in ast.parse((ROOT / "src" / "apexc" / "rules.py").read_text(encoding="utf-8")).body
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
    ]
    dead = sorted(f for f in rules_funcs if f not in used)
    assert dead == sorted(STAGE2_ONLY), (
        dead
    )  # nothing else is dead; these have no caller until the agent flow and the scorecard exist (stage 2)
    keys = set().union(*(strings(p) for p in src))
    pol = json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))

    def leaves(d, path=()):
        for k, v in d.items():
            yield from leaves(v, (*path, k)) if isinstance(v, dict) else [(*path, k)]

    # `purposes` (purpose_of) and `master_fields` (group_of iterates it) are looked up by key, so their keys are not literal reads
    missing = [
        p[-1]
        for p in leaves(pol)
        if p[0] not in ("purposes", "master_fields") and p[-1] not in ("version", "note", "_note") and p[-1] not in keys
    ]
    assert missing == [], missing


# ---- faults that were declared but never produced -------------------------------------------------------------------------------------
def test_m7_duplicate_key_replay_is_absorbed_and_a_partial_failure_is_never_a_success(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol, schedule=FaultSchedule(1, (FaultStep(1, "duplicate_key_replay"),)))
    settle(ex, erp, c, pol)
    assert ex.release(c["invoice"]["invoice_id"], approve_all(ex, c)) == "queued" and pay.applies == 1 and pay.replays_absorbed == 1
    c2 = case_of(cases, "clean_match", "test")
    e2, p2, k2, a2, x2 = build(c2, pol, schedule=FaultSchedule(1, (FaultStep(1, "partial_failure"),)))
    settle(x2, e2, c2, pol)
    out = x2.release(c2["invoice"]["invoice_id"], approve_all(x2, c2))
    assert out == "handed_back:unknown_outcome"  # the header exists but is "incomplete": a person repairs it, nothing says queued
    assert p2.lookup(x2._key(c2["invoice"]["invoice_id"]))["status"] == "incomplete"


# ---- design items --------------------------------------------------------------------------------------------------------------------------
def test_d1_reject_is_an_append_only_ledger_row_refused_for_a_queued_earlier_invoice(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "exact_dup", do_settle=False)
    inv, hist = c["invoice"]["invoice_id"], c["context"]["history"][0]
    erp.cases[inv]["context"]["history"][0]["status"] = "received"
    d = c["context"]["directory"]
    sub = c["invoice"]["submitted_by"]
    sup = next(
        u
        for u, r in d.items()
        if "ap_supervisor" in r["roles"] and r["employee_id"] not in (d[sub]["employee_id"], d[hist["submitted_by"]]["employee_id"])
    )
    before = copy.deepcopy(erp.cases[inv]["context"]["history"])
    assert ex.reject(inv, sup, hist["invoice_id"])
    assert erp.cases[inv]["context"]["history"] == before and len(erp.rejections) == 1  # history is not edited in place; a row is appended
    assert any(e["kind"] == "rejection_recorded" for e in audit.events)
    pay.enqueue(
        "executor_enqueue",
        {
            "vendor_id": "v",
            "invoice_id": hist["invoice_id"],
            "invoice_number": "X1",
            "currency": "USD",
            "total_minor": "1",
            "po_key": "",
            "received_day": "d",
        },
        "k-q",
        [],
    )
    erp.rejections.clear()
    assert ex.reject(inv, sup, hist["invoice_id"]) is False  # the earlier invoice is in the payments queue: it cannot be rejected away


def test_d2_a_config_change_needs_two_controllers_is_chained_and_voids_old_approvals(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")  # a private copy of the policy for this test
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    v0 = ex.config_version()
    bump = lambda p, d: d["u-trs-01"].update(roles=["treasury_officer", "ap_supervisor"])  # noqa: E731
    assert not ex.change_config("u-ctl-01", "u-ctl-01", "same person", bump) and not ex.change_config(
        "u-ctl-01", "u-sup-01", "not a controller", bump
    )
    assert ex.config_version() == v0
    assert ex.change_config("u-ctl-01", "u-ctl-02", "grant", bump) and ex.config_version() != v0
    ev = next(e for e in audit.events if e["kind"] == "config_changed")
    assert ev["before"] == v0 and ev["after"] == ex.config_version()
    assert ex.release(inv, ids) == "denied:config_changed" and pay.applies == 0


def test_d3_the_chain_head_can_be_exported_for_an_external_anchor():
    a = Audit()
    assert a.head("t1") == {"tenant": "t1", "seq": 0, "sha256": "0" * 64}
    e = a.append("t1", "x")
    assert a.head("t1") == {"tenant": "t1", "seq": 1, "sha256": e["sha256"]}


def test_d5_the_docs_say_what_the_system_can_and_cannot_do():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    scoping = (ROOT / "scoping.md").read_text(encoding="utf-8")
    promise = "The agent cannot move money. Only the demo-side executor can queue a payment, after the tier's recorded approvals; a queue entry is not a payment."
    assert promise in readme and promise in scoping
    assert "never releases money" not in readme and "never releases money" not in scoping
    for f in (
        "README.md",
        "failure_modes.md",
        "scoping.md",
        "acceptance.md",
        "gate_rules.md",
        "spec_stage2.md",
        "eval-contract.md",
    ):
        t = (ROOT / f).read_text(encoding="utf-8")
        assert not re.search(r"hard zeros? (are )?all 0|hard zeros all", t, re.I), f
    assert (ROOT / "PROMISES.md").exists()


def test_d6_counts_pinned(cases):
    assert len(cases) == 256
    fm = (ROOT / "failure_modes.md").read_text(encoding="utf-8")
    assert len(set(re.findall(r"\| (FM-\d+) \|", fm))) == 62 and len(set(re.findall(r"\| (HZ-\d+) \|", fm))) == 21
    assert FakeErp  # imported for the type; the suite size itself is pinned by the CI run that lists it


def test_n2_an_edit_of_the_number_or_a_line_voids_the_approvals_before_any_release(cases, pol):
    def number(case):  # a faithful re-read of the edited number: no new exception type, only the binding differs
        case["invoice"]["invoice_number"] = case["extraction"]["invoice_number"] = "TE-00001"

    for field, edit in (("invoice_number", number), ("lines", lambda case: case["invoice"]["lines"][0].update(desc="something else"))):
        c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
        inv = c["invoice"]["invoice_id"]
        ids = approve_all(ex, c)
        edit(erp.cases[inv])
        out = ex.release(inv, ids)
        assert out.startswith("denied:binding_mismatch") and field in out and pay.applies == 0, (field, out)


def test_n4_a_handler_answer_that_is_not_terminal_goes_to_the_dead_letter_instead_of_looping():
    from apexc.intake import Intake

    it = Intake(max_attempts=2)
    it.receive("t1", "m1", b"x")
    it.receive("t1", "m2", b"y")
    assert (
        safe(it.drain, lambda raw: "maybe" if raw == b"x" else None) is None
    )  # a made-up state, and None: neither may loop or crash the drain
    assert {r["state"] for r in it.ledger.values()} == {"dead_letter"} and len(it.dead) == 2

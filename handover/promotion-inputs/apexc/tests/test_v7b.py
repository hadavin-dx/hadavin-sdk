"""Regression tests for the two fresh reviews of v7 : audit before act in the callout
and the egress gate (B1), ONE approval shape checked everywhere (M1), evidence copied (M2), one lock discipline for the control state (M3), a
single config source that cannot be bypassed (M4), counts of invoices (M5), a harder summary check (M6), a per-day egress cap (M7) and the nits.
Each has a mutant in mutation_check.py that reverts its fix. No unicode escapes are typed in this file: look-alikes are built with chr()."""

import copy
import json
import threading
import time
from datetime import timedelta

import pytest
from helpers import approve_all, build, settle
from test_attacks import case_of, forge, world

from apexc.classify import classify_full
from apexc.executor import MAX_ESCALATIONS, ApprovalRefused, ControlState, Executor
from apexc.fakes import Audit, AuditWriteError, EgressDenied, EgressGate, FakeCallout, ReadOnlyErp
from apexc.rules import binding_fields, callback_slots_ok, cleared_types, validate_approval
from apexc.tools import check_tool_call, summary_leaks

CY = {"x": chr(0x445), "e": chr(0x435), "o": chr(0x43E)}  # Cyrillic look-alikes
ZW, EN_DASH, COMBINING = chr(0x200B), chr(0x2013), chr(0x301)


# ---- B1: audit BEFORE the act ------------------------------------------------------------------------------------------------------------------
def test_b1_a_failed_audit_write_places_no_call_and_sends_no_message(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    co, eg = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol)
    slots = {"invoice_number": "A1", "account_last4": "1234"}
    audit.fail_next = True
    with pytest.raises(AuditWriteError):
        co.request_confirmation("agent_runtime", v["vendor_id"], "confirm_bank_details", slots, "k1")
    assert co.dials == [] and co.tickets == {}  # no call was placed
    assert (
        co.request_confirmation("agent_runtime", v["vendor_id"], "confirm_bank_details", slots, "k1").outcome == "applied"
    )  # the retry starts clean
    assert sum(1 for e in audit.events if e["kind"] == "callback_requested") == 1 and len(co.dials) == 1
    audit.fail_next = True
    with pytest.raises(AuditWriteError):
        eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    assert eg.outbox == []  # nothing left the building and nothing counts against the cap
    eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    assert len(eg.outbox) == 1 and sum(1 for e in audit.events if e["kind"] == "egress") == 1


def test_b1_any_audit_failure_rolls_an_attestation_back_not_only_audit_write_error(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    vid = c["context"]["vendor"]["vendor_id"]
    co.request_confirmation("agent_runtime", vid, "confirm_bank_details", {"invoice_number": "A1", "account_last4": "1234"}, "k1")
    real = audit.append
    audit.append = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("audit store broke"))
    with pytest.raises(RuntimeError):
        co.attest("attest_callback_capability", "k1", "u-trs-01")
    audit.append = real
    assert "cb-tk-1" not in erp.callbacks  # not left in the ledger without its audit event


def test_b1_the_docs_claim_only_what_the_code_does():
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for f in ("README.md", "PROMISES.md"):
        text = (root / f).read_text(encoding="utf-8")
        assert re.search(r"lifts, clears.{0,420}(only a hold placement|AFTER the write)", text, re.S | re.I), (
            f
        )  # what is audited before and what after is named, not hidden


# ---- M1: ONE approval shape ----------------------------------------------------------------------------------------------------------------------
def test_m1_the_approval_shape_is_exact_and_checked_on_write(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    good = ex.approve(c["invoice"]["invoice_id"], "u-sup-01", "plan_1")
    assert validate_approval(good)
    for mutate in (
        lambda r: r.update(single_minor=float("nan")),
        lambda r: r.update(single_minor="9"),
        lambda r: r.update(single_minor=True),
        lambda r: r["bound"].update(extra=1),
        lambda r: r["bound"].update({"x": None}),
        lambda r: r["bound"].update(types="superset"),
        lambda r: r.update(consumed="no"),
        lambda r: r.update(by=7),
        lambda r: r.update(ts="yesterday"),
        lambda r: r.pop("config_version"),
        lambda r: r["bound"].update(master_version=1.5),
    ):
        bad = copy.deepcopy(good)
        mutate(bad)
        assert not validate_approval(bad)
    with pytest.raises(ValueError):
        erp.record_approval(
            "executor_approvals", {"invoice_id": "x", "vendor_id": "v", "plan": "plan_1", "by": "u", "bound": {}, "config_version": "c"}
        )


def test_m1_a_corrupted_row_is_not_an_approval_and_cannot_break_anyone_else(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["tiers"].update(approver_cap_per_vendor_window=1000, approver_cap_long=1000, vendor_cap_per_window=1000)
    c, erp, pay, clock, audit, ex = world(cases, p2, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    row = erp.approvals[ids[0]]
    original, who = copy.deepcopy(row), row["by"]
    for i, (field, poison) in enumerate(
        (("single_minor", float("nan")), ("single_minor", "9"), ("single_minor", None), ("ts", "yesterday"), ("by", None))
    ):
        row[field] = poison
        assert not validate_approval(row)
        assert ex.release(inv, ids) == "denied:approval_not_usable" and pay.applies == 0
        other = copy.deepcopy(c)
        other["invoice"]["invoice_id"] = f"inv-other-{i}"
        erp.cases[f"inv-other-{i}"] = other
        # the bad row is skipped by every count: it cannot deny the person it names, or anyone else (no internal_error)
        for person in (who, "u-sup-02"):
            err = None
            try:
                ex.approve(f"inv-other-{i}", person, "plan_1")
            except ApprovalRefused as e:
                err = str(e)
            assert err is None, f"a corrupted row ({field}) denied {person}: {err}"
        row.clear()
        row.update(copy.deepcopy(original))
    erp.approvals[ids[0]]["bound"]["odd"] = (1, 2)
    assert ex.release(inv, ids) == "denied:approval_not_usable"  # odd keys inside `bound` are rejected, not ignored


def test_m1_forged_types_superset_cannot_switch_off_the_new_types_check(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    recs = [r for r in erp.clears if r["invoice_id"] == inv]
    bound = binding_fields(erp.read_case(inv), pol, cleared_types(recs, c["context"]["directory"], pol))
    superset = {**bound, "types": sorted({*bound["types"], "bank_change", "new_vendor"})}  # would hide a NEW type from release_recheck
    with pytest.raises(ValueError):  # the ERP refuses it at the write (design M3) ...
        forge(erp, c, pol, "u-sup-02", "plan_1", bound=superset)
    ids = [forge(erp, c, pol, "u-sup-02", "plan_1"), forge(erp, c, pol, "u-trs-01", "plan_2")]
    for i in ids:  # ... so a hostile writer has to bypass it: write the rows straight into the ledger, and release still catches it
        erp.approvals[i]["bound"] = superset
    out = ex.release(inv, ids)
    assert out.startswith("denied:binding_mismatch:") and "types" in out and pay.applies == 0, out


def test_m1_bound_equality_does_not_depend_on_key_order(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    recs = [r for r in erp.clears if r["invoice_id"] == inv]
    bound = binding_fields(erp.read_case(inv), pol, cleared_types(recs, c["context"]["directory"], pol))
    flipped = dict(reversed(list(bound.items())))
    assert list(flipped) != list(bound) and flipped == bound
    ids = [forge(erp, c, pol, "u-sup-02", "plan_1", bound=bound), forge(erp, c, pol, "u-trs-01", "plan_2", bound=flipped)]
    assert ex.release(inv, ids) == "queued"


def test_m1_rulings_clears_and_lift_evidence_have_one_shape_too(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "exact_dup", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    row = {
        "ruling_id": "r1",
        "invoice_id": inv,
        "history_id": "h",
        "ruling": "not_duplicate",
        "by": "u-ctl-01",
        "role": "finance_controller",
    }
    with pytest.raises(ValueError):
        erp.add_ruling("finance_controller", {**row, "extra": 1})
    with pytest.raises(ValueError):
        erp.add_ruling("finance_controller", {**row, "by": 7})
    erp.add_ruling("finance_controller", row)
    with pytest.raises(ValueError):
        erp.record_clear("executor_lift", {"invoice_id": inv, "type": "t", "by": 5, "kind": "clear", "evidence_id": "e"})
    ex.place_holds(inv)
    with pytest.raises(ValueError):
        erp.lift_hold("executor_lift", inv, "duplicate_exact", "u-ctl-01", {"second_lifter": {"nested": "dict"}})
    assert ex.lift(inv, "duplicate_exact", "u-ctl-01", "confirm_not_duplicate", {"ruling_id": ["x"]}) is False


# ---- M2: evidence is copied on write and on read ----------------------------------------------------------------------------------------------
def test_m2_lift_evidence_is_a_copy_on_write_and_on_read(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "price_over", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    ev = {"second_lifter": "u-ctl-01"}
    assert erp.lift_hold("executor_lift", inv, "price_variance", "u-sup-01", ev)
    ev.pop("second_lifter")  # the caller edits its dict afterwards
    assert erp.hold_rows(inv)["price_variance"]["evidence"] == {"second_lifter": "u-ctl-01"}
    erp.hold_rows(inv)["price_variance"]["evidence"].clear()  # and a reader edits what it was handed
    assert erp.hold_rows(inv)["price_variance"]["evidence"] == {"second_lifter": "u-ctl-01"}


# ---- M3: one lock discipline ---------------------------------------------------------------------------------------------------------------------
def test_m3_to_json_waits_for_the_release_store_lock_too():
    st, held, go, done = ControlState(), threading.Event(), threading.Event(), threading.Event()

    def holder():
        with st.store._lock:
            held.set()
            go.wait(5)

    t1 = threading.Thread(target=holder)
    t1.start()
    held.wait(5)
    t2 = threading.Thread(target=lambda: (st.to_json(), done.set()))
    t2.start()
    assert not done.wait(0.3), "to_json read the release rows while the store lock was held"
    go.set()
    assert done.wait(5)
    t1.join()
    t2.join()


def test_m3_to_json_never_stringifies_an_unknown_object_and_keeps_the_store_counters(cases, pol):
    st = ControlState()
    st.escalations.append({"x": object()})
    with pytest.raises(TypeError):
        st.to_json()
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    assert ex.release(c["invoice"]["invoice_id"], approve_all(ex, c)) == "queued"
    back = ControlState.from_json(ex.state.to_json())
    assert (back.store.rechecks, back.store.applies) == (ex.store.rechecks, ex.store.applies) and back.store.applies == 1


def test_m3_a_snapshot_taken_in_the_middle_of_a_flush_still_holds_every_unwritten_event(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ex.state.audit_backlog[:] = [("e1", {"n": 1}), ("e2", {"n": 2})]
    seen = []
    real = audit.append

    def spying(tenant, kind, **f):
        seen.append(json.loads(ex.state.to_json())["audit_backlog"])  # a snapshot while this event is being written
        return real(tenant, kind, **f)

    audit.append = spying
    assert ex.flush_audit() == 2 and ex.state.audit_backlog == []
    assert [len(s) for s in seen] == [2, 1]  # nothing was lost from view; the chain order is e1 then e2
    assert [e["kind"] for e in audit.events if e["kind"] in ("e1", "e2")] == ["e1", "e2"]


def test_m3_escalations_are_appended_under_the_lock_and_capped():
    st = ControlState()
    ts = [threading.Thread(target=lambda: [st.escalate({"i": i}) for i in range(MAX_ESCALATIONS)]) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(st.escalations) == MAX_ESCALATIONS and st.escalations_dropped == 2 * MAX_ESCALATIONS
    assert ControlState.from_json(st.to_json()).escalations_dropped == st.escalations_dropped


# ---- M4: one config source, not bypassable ----------------------------------------------------------------------------------------------------
def test_m4_two_concurrent_config_changes_both_land(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")

    def slow(key, val):
        def mutate(p, d):
            time.sleep(0.15)  # both read the same base unless the changes take turns
            p["limits"][key] = val

        return mutate

    res = []
    ts = [
        threading.Thread(target=lambda k=k, v=v: res.append(ex.change_config("u-ctl-01", "u-ctl-02", k, slow(k, v))))
        for k, v in (("egress_per_day", 7), ("erp_connections", 9))
    ]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert res == [True, True] and ex.pol["limits"]["egress_per_day"] == 7 and ex.pol["limits"]["erp_connections"] == 9
    befores = [e["before"] for e in audit.events if e["kind"] == "config_changed"]
    assert len(set(befores)) == 2  # the second change started from the first one's result


def test_m4_a_config_change_between_the_gates_and_the_enqueue_voids_the_release(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    real = ex.store.execute

    def change_then_execute(*a, **k):
        assert ex.change_config("u-ctl-01", "u-ctl-02", "mid-release", lambda p, d: p["limits"].update(erp_connections=9))
        return real(*a, **k)

    ex.store.execute = change_then_execute
    assert ex.release(inv, ids) == "denied:config_changed" and pay.applies == 0


def test_m4_a_changed_dry_run_default_takes_effect_and_an_explicit_live_is_kept(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, _ = build(c, copy.deepcopy(pol))
    ex = Executor(erp, pay, clock, audit, erp.pol, c["context"]["directory"])  # no explicit `live`: follows the policy
    assert ex.live is False
    assert ex.change_config("u-ctl-01", "u-ctl-02", "go live", lambda p, d: p["release"].update(dry_run_default=False))
    assert ex.live is True
    ex2 = Executor(erp, pay, clock, audit, ex.pol, c["context"]["directory"], live=False)
    assert ex2.live is False


def test_m4_a_vendor_missing_from_the_live_table_is_not_read_from_a_stale_snapshot(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    del erp.vendors[c["context"]["vendor"]["vendor_id"]]
    with pytest.raises(KeyError):
        erp.read_case(inv)
    assert ex.release(inv, ids) == "denied:unknown_invoice" and pay.applies == 0


# ---- M5: caps count invoices -----------------------------------------------------------------------------------------------------------------------
def test_m5_plan_1_and_plan_2_of_one_invoice_count_once_and_a_lift_counts_for_the_lifter(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large", do_settle=False)
    cap = pol["tiers"]["vendor_cap_per_window"]
    sups, trs = ["u-sup-01", "u-sup-02"], ["u-trs-01", "u-trs-02"]
    for i in range(cap):  # six invoices, each with BOTH plans: twelve approval rows, six invoices
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-m5-{i}"
        erp.cases[f"inv-m5-{i}"] = cc
        ex.approve(f"inv-m5-{i}", sups[i // 3], "plan_1")
        ex.approve(f"inv-m5-{i}", trs[i // 3], "plan_2")
    cc = copy.deepcopy(c)
    cc["invoice"]["invoice_id"] = "inv-m5-over"
    erp.cases["inv-m5-over"] = cc
    with pytest.raises(ApprovalRefused) as e:
        ex.approve("inv-m5-over", "u-ctl-01", "plan_1")
    assert str(e.value) == "vendor_cap"
    # a lift counts for the person who made it
    c2, erp2, pay2, clock2, audit2, ex2 = world(cases, pol, "price_over", do_settle=False)
    for i in range(pol["tiers"]["approver_cap_per_vendor_window"]):
        cc = copy.deepcopy(c2)
        cc["invoice"]["invoice_id"] = f"inv-lift-{i}"
        erp2.cases[f"inv-lift-{i}"] = cc
        ex2.place_holds(f"inv-lift-{i}")
        assert ex2.lift(f"inv-lift-{i}", "price_variance", "u-sup-03", "accept_price_variance")
    with pytest.raises(ApprovalRefused) as e2:
        ex2.approve(c2["invoice"]["invoice_id"], "u-sup-03", "plan_1")
    assert str(e2.value) == "approver_cap"


# ---- M6: the summary check -------------------------------------------------------------------------------------------------------------------------
def test_m6_every_separator_homoglyph_and_combining_mark_is_normalised():
    leaks = [
        "1234_5678_9012",
        "1234:5678:9012",
        "1234|5678|9012",
        f"1234{EN_DASH}5678{EN_DASH}9012",
        "1234 - 5678 - 9012",
        f"1234{COMBINING}5678{COMBINING}9012",
        f"1234{CY['x']}5678{CY['x']}9012",
        "1234-56-78",  # eight digits that only LOOK like an ISO date (month 56)
        "10 000 000",
        "12345678",
        f"AB12{ZW}CD34{ZW}EF56GH",
        f"AB12CD34{COMBINING}EF",  # a token broken by a combining mark
        "1234 x 5678",  # digit groups bridged by a lone letter that spaces separate from them  # an alphanumeric token broken by zero-width characters, too few digits for the digit rule
        "pay GB82 WEST 1234 5698 7654 32 now",
    ]
    for text in leaks:
        assert summary_leaks(text, []), text
    assert summary_leaks(f"IBAN GB82WEST1234569876{CY['o']}432", ["GB82WEST12345698760432"])  # O for 0, a Cyrillic letter inside
    assert summary_leaks("account ACC0UNT77XY", ["ACCOUNT77XY"]) and summary_leaks("acct l234", ["1234"])  # O/0 and l/1 are one character


def test_m6_what_is_allowed_is_decided_and_pinned():
    ok = [
        "Invoice HF-52341 price differs by 2 percent",
        "dated 2026-11-01, total 5,000 USD, due in 30 days",
        "PO-1234 line 3 is short by 4 units",
        "paid 20/10/2026 and 2026.10.20",
        "total $5.00 USD, tax $2.00",
        "qty 12 at 450 each, line 7",
    ]
    for text in ok:
        assert not summary_leaks(text, []), text
    assert summary_leaks(
        "INV-2026-0482 is late", []
    )  # an 8-digit invoice number is refused unless it is the case's own, passed as `allowed` (a shorter one is plain digits, under the budget)
    assert not summary_leaks("INV-26-0482 is late", [], ["INV-26-0482"])
    assert summary_leaks("INV-26-0482 and 98765432", [], ["INV-26-0482"])  # allowing the number does not allow anything else


def test_m6_a_scope_without_protected_values_is_refused_not_silently_unchecked():
    base = {
        "invoice_id": "inv-1",
        "kind": "resolution",
        "recommended_action": "approve_match",
        "summary": "ok",
        "amount_minor": "1",
        "currency": "USD",
    }
    scope = {"invoice_id": "inv-1", "vendor_id": "v-007", "po_ids": []}
    assert check_tool_call("route_for_approval", base, scope) == "scope_incomplete"
    assert check_tool_call("route_for_approval", base, {**scope, "protected": []}) is None
    assert (
        check_tool_call(
            "route_for_approval", {**base, "summary": "INV-26-0482 late"}, {**scope, "protected": [], "invoice_number": "INV-26-0482"}
        )
        is None
    )


# ---- M7: the egress cap is per UTC day; slots take real invoice numbers ---------------------------------------------------------------------------
def test_m7_the_egress_cap_resets_at_midnight_and_real_invoice_numbers_pass(cases, pol):
    small = copy.deepcopy(pol)
    small["limits"]["egress_per_day"] = 2
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, small)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    eg = EgressGate(erp, clock, audit, small)
    to = v["contact"]["email_on_file"]
    eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": "INV-0482"})
    eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": "2026/0482-A.1"})
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": "X3"})
    clock.advance(24 * 60)  # next UTC day
    eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": "X3"})
    assert len(eg.outbox) == 3


def test_m7_slot_checks_answer_false_for_a_non_string_instead_of_raising(pol):
    for bad in (5, None, ["a"], 1.5, b"x"):
        assert callback_slots_ok("notify_hold", {"invoice_number": bad}, pol) is False
    assert callback_slots_ok("notify_hold", {"invoice_number": "INV-0482"}, pol) is True


# ---- nits -----------------------------------------------------------------------------------------------------------------------------------------------------
def test_n_garbage_calls_do_not_grow_the_chain(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    n0 = len(audit.events)
    for _ in range(20):
        assert ex.release("inv-none", []) == "denied:unknown_invoice"
        assert ex.release(c["invoice"]["invoice_id"], ["apr-nope"]) == "denied:approval_not_usable"
    assert len(audit.events) == n0  # no release_intent and no release_denied for an unknown id
    assert ex.release(c["invoice"]["invoice_id"], []).startswith("denied:")
    assert any(e["kind"] == "release_denied" for e in audit.events)  # a real denial is still on the record


def test_n_every_role_that_may_approve_a_resolution_may_also_lift(pol):
    for role, steps in pol["roles"].items():
        assert ("approve_resolution" in steps) == ("lift_hold" in steps), (
            role
        )  # can_lift_hold needs the first; the release needs the second


def test_n_the_mutant_list_is_pinned_by_hash_not_by_count():
    import hashlib
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("mc_pin", root / "mutation_check.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    digest = hashlib.sha256(json.dumps([list(m) for m in mc.M]).encode()).hexdigest()[:16]  # every field, the expected reason included
    assert f"mutant list {digest}" in (root / "acceptance.md").read_text(encoding="utf-8"), digest
    assert len({m[0] for m in mc.M}) == len(mc.M)  # no two mutants share a name
    assert all(
        all(o in (root / m[1]).read_text(encoding="utf-8") for o in (m[2] if isinstance(m[2], list) else [m[2]])) for m in mc.M
    )  # every snippet it reverts exists


_ = (Audit, ReadOnlyErp, classify_full, cleared_types, settle, timedelta)

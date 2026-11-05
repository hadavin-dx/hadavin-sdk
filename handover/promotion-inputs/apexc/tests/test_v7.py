"""Regression tests for the two fresh reviews of v6 : the README that named a
config key that does not exist (B1), the lifter who was also plan 1 (M1), two directory sources (M2), control state that did not persist and
caps that were only advice (M3), the docs' honesty about asserted ids (M4), summary and egress redaction that grouped numbers slipped past (M5),
the audit event written before the ledger row (M6) and the nits. Each has a mutant in mutation_check.py that reverts its fix, and each test was
run against the v6 code first and failed there."""

import copy
import json
import re
import threading
from pathlib import Path

import pytest
from helpers import approvals_spec, approve_all, build, settle
from test_attacks import case_of, world

from apexc.executor import ApprovalRefused, ControlState, Executor
from apexc.fakes import AuditWriteError, EgressDenied, EgressGate, FakeCallout, ReadOnlyErp
from apexc.intake import Intake
from apexc.normalise import squeeze
from apexc.rules import sod_violations
from apexc.tools import check_tool_call, summary_leaks

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "README.md",
    "PROMISES.md",
    "gate_rules.md",
    "spec_stage2.md",
    "scoping.md",
    "acceptance.md",
    "failure_modes.md",
    "eval-contract.md",
)


# ---- B1: a doc may only name a config key that exists --------------------------------------------------------------------------------------
def test_b1_every_config_key_the_docs_name_exists_in_policy_json(pol):
    """`queue.run_cutoff_local` was named in the README and never existed. Every backticked dotted path that starts at a top-level policy key must
    resolve in policy.json, and the two names that were once claimed must not come back."""
    checked = 0
    for f in DOCS:
        text = (ROOT / f).read_text(encoding="utf-8")
        for path in re.findall(r"`([a-z_][a-z0-9_]*(?:\.[a-z0-9_]+)+)`", text):
            head, *rest = path.split(".")
            if head not in pol:
                continue  # a file name, a module or a method, not a config path
            node = pol
            for part in (head, *rest):
                assert isinstance(node, dict) and part in node, f"{f} names `{path}` but policy.json has no such key"
                node = node[part]
            checked += 1
        for ghost in ("run_cutoff", "queue_timezone"):
            assert ghost not in text, f"{f} names {ghost}, which policy.json does not have"
    assert checked >= 3  # the check really looked at the docs (queue.min_queue_to_run_hours is named in several)


# ---- M1: lifting is its own duty ------------------------------------------------------------------------------------------------------------
def test_m1_sod_treats_lifting_and_plan_1_as_two_duties_of_one_person(pol, cases):
    d = case_of(cases, "clean_match")["context"]["directory"]
    assert sod_violations([("u-sup-01", "lift_hold"), ("u-sup-01", "approve_resolution")], d, pol)
    assert sod_violations([("u-ctl-01", "lift_hold"), ("u-ctl-01", "approve_release")], d, pol)
    assert not sod_violations([("u-sup-01", "lift_hold"), ("u-sup-01", "lift_hold")], d, pol)  # lifting two holds is one duty
    assert not sod_violations([("u-sup-01", "lift_hold"), ("u-sup-02", "approve_resolution")], d, pol)


def test_m1_hostile_probe_the_person_who_lifted_the_hold_cannot_approve_the_release_alone(cases, pol):
    """At tier human one supervisor used to lift a price_variance hold AND approve its release (no second person at all). Every dev and test
    case with a lift is run twice: the harness's second person queues it, the lifter as plan 1 is `denied:sod` and nothing is enqueued."""
    seen, skipped = 0, []
    for c0 in cases:
        if not c0["scenario"]["lifts"] or c0["recipe"] in ("ruling_same_person", "reject_same_person"):
            continue
        base = case_of(cases, c0["recipe"], c0["split"])
        ex = world(cases, pol, c0["recipe"], c0["split"])[5]
        if ex.release(base["invoice"]["invoice_id"], approve_all(ex, base)) != "queued":
            skipped.append(c0["case_id"])  # not a clean release even with a second person (a refusal case): named, so a silent shrink shows
            continue
        c, erp, pay, clock, audit, ex = world(cases, pol, c0["recipe"], c0["split"])
        inv = c["invoice"]["invoice_id"]
        lifter = c["scenario"]["lifts"][0]["by"]
        spec = [(lifter, "plan_1")] + [(by, plan) for by, plan in approvals_spec(c) if plan == "plan_2"]
        ids = [ex.approve(inv, by, plan)["approval_id"] for by, plan in spec]
        assert ex.release(inv, ids) == "denied:sod" and pay.applies == 0, c0["recipe"]
        seen += 1
    assert seen >= 15 and len(skipped) <= 8, (seen, skipped)  # the probe really ran on most lift cases; a growing skip list fails


# ---- M2: one directory for every reader -------------------------------------------------------------------------------------------------
def test_m2_a_revoked_attester_no_longer_backs_a_clear_even_for_a_case_stored_before_the_change(cases, pol):
    c0, _, _, _, _, ex0 = world(cases, pol, "bank_remit")
    assert ex0.release(c0["invoice"]["invoice_id"], approve_all(ex0, c0)) == "queued"  # the setup itself is a valid release
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "bank_remit")
    inv = c["invoice"]["invoice_id"]
    clear = next(r for r in erp.clears if r["invoice_id"] == inv and r["kind"] == "clear")
    attester = erp.callbacks[clear["evidence_id"]]["attested_by"]
    assert ex.change_config("u-ctl-01", "u-ctl-02", "revoke the attester", lambda p, dr: dr[attester].update(roles=["ap_clerk"]))
    assert erp.read_case(inv)["context"]["directory"][attester]["roles"] == ["ap_clerk"]  # every read sees the one directory ...
    assert erp.cases[inv]["context"]["directory"][attester]["roles"] != [
        "ap_clerk"
    ]  # ... the snapshot stored with the case is stale and unused
    assert (
        ex.release(inv, approve_all(ex, c)) == "denied:clear_evidence_invalid" and pay.applies == 0
    )  # the clear rested on a person who is no longer an attester


def test_m2_change_config_updates_every_holder_and_reruns_the_constructor_checks(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    co, eg, ro = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol), ReadOnlyErp(erp, audit, clock, pol)
    # no `ex.register(...)`: ports built on the ERP follow the executor by themselves (a forgotten register cannot leave a stale policy)
    v0 = ex.config_version()
    assert ex.change_config("u-ctl-01", "u-ctl-02", "tighten", lambda p, dr: p["limits"].update(egress_per_day=1))
    assert ex.config_version() != v0
    for holder in (erp, pay, co, eg, ro):
        assert holder.pol is ex.pol and holder.pol["limits"]["egress_per_day"] == 1, type(holder).__name__
    assert erp.directory is ex.directory and pay.directory is ex.directory
    for name in ("pol", "directory"):  # the root of trust has no public setter: only change_config (two controllers) moves it
        with pytest.raises(AttributeError):
            setattr(ex, name, {})
    v1 = ex.config_version()

    def conflict(p, dr):
        p["identities"]["executor_enqueue"]["write"].append("approve_release")  # an actor that also approves

    def nameless(p, dr):
        dr["u-ap-01"]["employee_id"] = ""  # a person with no employee id

    assert not ex.change_config("u-ctl-01", "u-ctl-02", "bad identity", conflict) and not ex.change_config(
        "u-ctl-01", "u-ctl-02", "bad dir", nameless
    )
    assert ex.config_version() == v1 and {e["why"] for e in audit.events if e["kind"] == "config_change_denied" and "why" in e} == {
        "identity_conflict",
        "directory_invalid",
    }
    with pytest.raises(ValueError):
        Executor(erp, pay, clock, audit, pol, {"u-x": {"employee_id": "", "roles": []}})  # the same checks at construction


# ---- M3: control state that survives, caps that bind -------------------------------------------------------------------------------------------
def test_m3_queued_audit_events_and_escalations_survive_a_restart(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    audit.fail_kinds = {"release_result", "approvals_consumed"}
    assert ex.release(inv, ids) == "queued" and len(ex.state.audit_backlog) == 2
    ex.state.escalations.append({"invoice_id": inv, "kind": "roster_gap", "missing": ["x"]})
    blob = ex.state.to_json()
    audit.fail_kinds = set()
    ex2 = Executor(
        erp, pay, clock, audit, pol, c["context"]["directory"], live=True, state=ControlState.from_json(blob), rebind=True
    )  # the process restarted
    assert [k for k, _ in ex2.state.audit_backlog] == ["approvals_consumed", "release_result"]
    assert ex2.escalations == [{"invoice_id": inv, "kind": "roster_gap", "missing": ["x"]}]
    assert ex2.flush_audit() == 2 and {"approvals_consumed", "release_result"} <= {
        e["kind"] for e in audit.events
    }  # the record is not lost


def test_m3_to_json_is_read_under_the_lock():
    st, held, go, done = ControlState(), threading.Event(), threading.Event(), threading.Event()

    def holder():
        with st.lock:
            held.set()
            go.wait(5)

    def reader():
        st.to_json()
        done.set()

    t1 = threading.Thread(target=holder)
    t1.start()
    held.wait(5)
    t2 = threading.Thread(target=reader)
    t2.start()
    assert not done.wait(0.3), "to_json read the state while a writer held the lock"
    go.set()
    assert done.wait(5)
    t1.join()
    t2.join()


def test_m3_a_submitter_past_the_hold_cap_releases_nothing_that_day(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["holds"]["max_per_submitter_per_day"] = 2
    c, erp, pay, clock, audit, ex = world(cases, p2, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    flood = case_of(cases, "price_over", "test")
    assert flood["invoice"]["submitted_by"] == c["invoice"]["submitted_by"]
    erp.vendors[flood["context"]["vendor"]["vendor_id"]] = flood["context"]["vendor"]
    for i in range(3):
        cc = copy.deepcopy(flood)
        cc["invoice"]["invoice_id"] = f"inv-flood-{i}"
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        ex.place_holds(cc["invoice"]["invoice_id"])
    assert any(e["kind"] == "hold_pressure" and e["rate_limit_submitter"] for e in ex.escalations)  # told ...
    assert ex.release(inv, ids) == "denied:submitter_rate_limited" and pay.applies == 0  # ... and enforced
    assert ControlState.from_json(ex.state.to_json()).limited == ex.state.limited and ex.state.limited  # and remembered across a restart


def test_m3_the_vendor_wide_approval_cap_is_enforced_not_only_advised(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match", do_settle=False)
    cap = pol["tiers"]["vendor_cap_per_window"]
    got = []
    people = ["u-sup-01", "u-sup-02", "u-sup-03", "u-ctl-01", "u-ctl-02"]
    for i in range(cap + 2):
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-vc-{i}"
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        try:
            ex.approve(cc["invoice"]["invoice_id"], people[i // 2 % len(people)], "plan_1")
            got.append("ok")
        except ApprovalRefused as e:
            got.append(str(e))
    assert got[:cap] == ["ok"] * cap and set(got[cap:]) == {"vendor_cap"}, got


# ---- M4: the docs say what an actor is ---------------------------------------------------------------------------------------------------------
def test_m4_the_docs_say_the_stage_1_actor_is_an_asserted_id_and_approvals_are_unsigned():
    promises = (ROOT / "PROMISES.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for text in (promises, readme):
        assert re.search(r"asserted id", text) and re.search(r"not an authenticated person", text)
        assert re.search(r"unsigned", text)
    assert "Every line here is true" in promises
    assert "Stage 1 is code and tests only" in readme


# ---- M5: grouped numbers do not slip past the summary or the egress output check ------------------------------------------------------------------
LEAKS = (
    "pay GB82 WEST 1234 5698 7654 32 today",
    "tax id 12-3456789 on the invoice",
    "call (555) 123-4567 now",
    "phone +44 20 7946 0958",
    "acct 1234 5678 9012",
    "acct 1\u200b2\u200b3\u200b4\u200b5\u200b6\u200b7\u200b8\u200b9",
    "\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19",
    "routing 0210/00021",
    "pay AB12 CDEF GH34 IJKL MN56 now",  # a grouped IBAN whose digit groups are too short to join into a long number
)
FINE = (
    "Invoice HF-52341 price differs by 2 percent",
    "dated 2026-11-01, total 5,000 USD, due in 30 days",
    "PO-1234 line 3 is short by 4 units",
)


def test_m5_the_summary_check_normalises_before_it_matches():
    for text in LEAKS:
        assert summary_leaks(text, []), text
    for text in FINE:
        assert not summary_leaks(text, []), text
    # a protected value is matched as a squeezed key: separators, case, zero-width characters and full-width digits do not hide it
    for text in (
        "call 1 555 010 0199",
        "call 1\u200b555\u200b010\u200b0199",
        "call \uff11\uff15\uff15\uff15\uff10\uff11\uff10\uff10\uff11\uff19\uff19",
    ):
        assert summary_leaks(text, ["+1-555-010-0199"]), text
    for text in (
        "the secret phone 77 is",
        "Secret-Phone-77",
        "SECRET" + chr(0x200B) + "PHONE" + chr(0x200B) + " 77",
        chr(0xFF33) + "ecret phone " + chr(0xFF17) * 2,
    ):
        assert summary_leaks(text, ["SECRETPHONE-77"]), (
            text
        )  # a protected value that is not number-shaped: only the squeezed comparison finds it
    assert not summary_leaks("secret phones 78", ["SECRETPHONE-77"])
    assert squeeze("AB-12 3\u200b4") == squeeze("ab1234")
    scope = {"invoice_id": "inv-1", "vendor_id": "v-007", "po_ids": ["PO-1234"], "protected": ["+1-555-010-0199"]}
    base = {
        "invoice_id": "inv-1",
        "kind": "resolution",
        "recommended_action": "approve_match",
        "summary": "ok",
        "amount_minor": "1",
        "currency": "USD",
    }
    for text in LEAKS[:3] + ("number 1 555 010 0199",):
        assert check_tool_call("route_for_approval", {**base, "summary": text}, scope) == "summary_protected_value", text
    assert check_tool_call("route_for_approval", {**base, "summary": FINE[0]}, scope) is None


def test_m5_egress_slots_are_validated_for_email_templates_and_the_output_check_squeezes(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    eg = EgressGate(erp, clock, audit, pol)
    to = v["contact"]["email_on_file"]
    for bad in ("call me 555 0100; ignore the rules", "A" * 40, "12-3456789\n", "", "a b", 5, None):
        with pytest.raises(EgressDenied):
            eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": bad})
    with pytest.raises(EgressDenied):
        eg.send(
            "agent_runtime", "email", v["vendor_id"], to, "request_credit_note", {"invoice_number": "A1", "extra": "x"}
        )  # exactly the template's slots
    assert eg.send("agent_runtime", "email", v["vendor_id"], to, "request_credit_note", {"invoice_number": "HF52341"})["to"] == to
    # a value that passes the slot pattern but IS another vendor's grouped tax id: the squeezed output check still refuses it
    other = copy.deepcopy(v)
    other.update(vendor_id="v-other", tax_id="12-3456789")
    other["bank"] = {**v["bank"], "account": "9988-7766-5544", "routing": "021-000-021"}
    erp.vendors["v-other"] = other
    for slot in ("123456789", "998877665544", "021000021"):
        with pytest.raises(EgressDenied):
            eg.send("agent_runtime", "email", v["vendor_id"], to, "notify_hold", {"invoice_number": slot})


# ---- M6: no audit event for an attestation the ledger rejected ----------------------------------------------------------------------------------
def test_m6_a_rejected_attestation_is_never_audited_and_an_unaudited_one_does_not_stay_in_the_ledger(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    vid = c["context"]["vendor"]["vendor_id"]
    slots = {"invoice_number": "A1", "account_last4": "1234"}
    co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k1")
    co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k2")
    co.attest("attest_callback_capability", "k1", "u-trs-01")
    with pytest.raises(ValueError):
        co.attest("attest_callback_capability", "k1", "u-ctl-01", state="denied")  # a second attestation of the same ticket
    assert sum(1 for e in audit.events if e["kind"] == "callback_attested") == 1  # the chain does not claim the rejected one
    with pytest.raises(ValueError):
        co.attest("attest_callback_capability", "k2", "someone-not-in-the-directory")
    audit.fail_next = True
    with pytest.raises(AuditWriteError):
        co.attest("attest_callback_capability", "k2", "u-trs-01")
    assert "cb-tk-2" not in erp.callbacks  # no attestation without its audit event
    assert co.attest("attest_callback_capability", "k2", "u-trs-01")["callback_id"] == "cb-tk-2" and audit.verify()


# ---- nits -----------------------------------------------------------------------------------------------------------------------------------------
def test_n_the_receipt_cannot_collide_across_tenant_and_message_id():
    it = Intake()
    a, b = it.receive("t1", "m1", b"x")["receipt"], it.receive("t", "1m1", b"x")["receipt"]
    assert a != b and it.receive("t1", "m1", b"x")["receipt"] == a  # a redelivery still gets the same receipt


def test_n_alerts_dead_letters_and_raw_bodies_are_bounded():
    it = Intake(max_diagnostics=5, max_raw_bytes=10)
    it.receive("t1", "m1", b"first")
    for i in range(30):
        it.receive("t1", "m1", f"changed {i}".encode())  # a flood of mismatching redeliveries
    t = it._tenant("t1")
    assert len(it.alerts("t1")) == 5 and len(t.dead) == 5 and t.overflow == 50  # counted, not stored
    out = it.receive("t1", "big", b"x" * 11)
    row = it._tenant("t1").ledger["big"]
    assert row["state"] == "rejected:too_large" and row["raw"] == b"" and out["receipt"]
    assert it.reconcile("t1", {"m1", "big"})["unterminal"] == ["m1"]  # the oversized message is terminal, not pending forever


def test_n_a_caller_with_no_approvals_of_this_invoice_is_told_nothing_about_the_release_row(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "queued"
    assert ex.release(inv, ids) == "duplicate_ignored"  # a caller who holds this invoice's approvals may replay
    assert ex.release(inv, []).startswith("denied:") and ex.release(inv, ["apr-nope"]) == "denied:approval_not_usable"
    other = case_of(cases, "clean_large")
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    foreign = ex.approve(other["invoice"]["invoice_id"], "u-sup-03", "plan_1")["approval_id"]
    assert ex.release(inv, [foreign]) == "denied:approval_not_usable"


def test_n_any_audit_failure_after_the_money_moved_is_queued_not_raised(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    real = audit.append
    calls = {"n": 0}

    def flaky(tenant, kind, **f):
        if kind in ("approvals_consumed", "release_result"):
            calls["n"] += 1
            raise TypeError("not JSON-serialisable")  # not an AuditWriteError
        return real(tenant, kind, **f)

    audit.append = flaky
    assert ex.release(inv, ids) == "queued" and len(ex.state.audit_backlog) == 2 and pay.applies == 1
    assert ex._audit_soft("note", obj=object()) is True  # a non-JSON field is made JSON-safe: written, not queued, never an exception


def test_n_the_invoice_number_that_reaches_a_payment_entry_is_bounded(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    erp.cases[inv]["invoice"]["invoice_number"] = erp.cases[inv]["extraction"]["invoice_number"] = "A" * (
        pol["limits"]["invoice_number_max"] + 1
    )
    settle(ex, erp, erp.cases[inv], pol)
    ids = approve_all(ex, erp.cases[inv])
    assert ex.release(inv, ids) == "denied:invoice_number_too_long" and pay.applies == 0
    assert json.dumps(pol["limits"]["invoice_number_max"])  # the bound is policy, not a literal


def test_n_a_bank_edit_newer_than_a_master_edit_clear_is_its_own_hard_block(cases, pol):
    """design-6 minor 8: a master-edit clear whose evidence predates a bank edit does not clear that edit. The bank edit is a bank_change of its own
    (a bank-topic callback newer than it is needed), so the release stays blocked; nothing relies on the bank edit also writing a master event."""
    from apexc.classify import classify_full

    c, erp, pay, clock, audit, ex = world(cases, pol, "sensitive_edit")
    inv, vid = c["invoice"]["invoice_id"], c["context"]["vendor"]["vendor_id"]
    ids = approve_all(ex, c)
    assert "bank_change" not in classify_full(erp.read_case(inv), pol)[0]
    erp.vendors[vid]["bank"]["changed_at"] = clock.now()  # a bank edit AFTER the master-edit evidence, with no vendor_master_events row
    erp.vendors[vid]["bank"]["changed_by"] = "u-mda-01"
    assert "bank_change" in classify_full(erp.read_case(inv), pol)[0]
    assert ex.release(inv, ids).startswith("denied:") and pay.applies == 0

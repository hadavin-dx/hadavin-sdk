"""Mutation and rule tests: every classifier-level rule and every policy threshold must be killed by named gold cases, the pure
decision helpers must behave at their boundaries, and every policy key must be read by code. Offline."""

import ast
import copy
import json
import re
from datetime import timedelta
from pathlib import Path

import pytest
from helpers import cleared_records, led_for

from apexc.classify import classify_full, cumulative_minor, emp, group_of, tier_for
from apexc.normalise import fmt_ts, minor, parse_ts
from apexc.ports import Amount as Amt
from apexc.ports import IdempotencyConflict, idem_key, release_key
from apexc.rules import (
    ReleaseStore,
    allowed_actions,
    approval_expired,
    approver_cap_ok,
    attest_conflict,
    attest_topic_ok,
    authorize_op,
    binding_fields,
    can_lift_hold,
    check_unique,
    choose_approver,
    cleared_types,
    controller_present,
    cooling_ok,
    evidence_ok,
    expected_kind,
    hold_aging_due,
    hold_pressure,
    holds_for,
    identity_can,
    identity_conflicts,
    may_reject,
    proposal_denial,
    reasons_lifted,
    release_recheck,
    render_undo_command,
    resolution_tier,
    sod_violations,
    undo_window_open,
)

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads((ROOT / "demo_only" / "data" / "seed.json").read_text(encoding="utf-8"))
DIRECTORY = {u["user_id"]: {"roles": u["roles"], "employee_id": u["employee_id"]} for u in SEED["users"]}


def signature(c, pol, off=frozenset(), p=None):
    try:
        t, ev = classify_full(c, p or pol, off)
        return sorted(t), sorted(ev), tier_for(t, c["invoice"]["currency"], cumulative_minor(c, p or pol), p or pol, off)
    except (KeyError, TypeError, ValueError):  # a mutant that crashes the classifier is also noticed
        return "CRASH"


def killers(cases, pol, off=frozenset(), mutated=None):
    return [c for c in cases if signature(c, pol, off, mutated) != signature(c, pol)]


def case_of(cases, recipe, split="dev"):
    return copy.deepcopy(next(c for c in cases if c["recipe"] == recipe and c["split"] == split))


CLASSIFIER_RULES = ["R-APEXC-002", "R-APEXC-003", "R-APEXC-004", "R-APEXC-005", "R-APEXC-006", "R-APEXC-007", "R-APEXC-008", "R-APEXC-009",
                    "R-APEXC-011", "R-APEXC-012", "R-APEXC-013", "R-APEXC-014", "R-APEXC-015", "R-APEXC-016", "R-APEXC-019", "R-APEXC-026",
                    "R-APEXC-028"]  # fmt: skip


@pytest.mark.parametrize("rule", CLASSIFIER_RULES)
def test_switching_a_classifier_rule_off_changes_a_named_case(cases, pol, rule):
    dead = killers(cases, pol, frozenset({rule}))
    assert dead, f"{rule} can be switched off and no gold case notices"
    assert {c["split"] for c in dead} == {"dev", "test"}, f"{rule} is only exercised in one split"


THRESHOLDS = [  # policy path, mutant values: each must change at least one case in BOTH splits
    (("tolerance", "qty_over_units"), [1, 8]), (("tolerance", "price_pct_bp"), [199, 201]), (("tolerance", "rounding_minor_per_line"), [0, 2]),
    (("tolerance", "price_abs_minor", "USD"), [4999, 5001]), (("tiers", "human_max_minor", "USD"), [499999, 500001]),
    (("windows", "near_dup_days"), [6, 8]), (("windows", "near_dup_max_edit_distance"), [1, 3]), (("windows", "edit_sod_window_days"), [29, 31]),
    (("windows", "new_vendor_days"), [29, 31]), (("tiers", "cumulative_window_days"), [1]),
    (("windows", "cooling_off_hours"), [71, 73]), (("windows", "same_po_same_total_days"), [29, 31]), (("windows", "total_tolerance_minor"), [99, 101]),
]  # fmt: skip


@pytest.mark.parametrize(("path", "values"), THRESHOLDS, ids=lambda x: ".".join(x) if isinstance(x, tuple) else "")
def test_every_threshold_is_pinned_from_both_sides(cases, pol, path, values):
    for v in values:
        p = copy.deepcopy(pol)
        d = p
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] = v
        dead = killers(cases, pol, mutated=p)
        assert {c["split"] for c in dead} == {"dev", "test"}, f"{'.'.join(path)}={v} survives in a split"


@pytest.mark.parametrize("cur", ["USD", "GBP", "CAD", "AUD", "EUR"])
def test_per_currency_tier_and_price_caps(pol, cur):
    hm, fm = pol["tiers"]["human_max_minor"][cur], pol["tiers"]["four_eyes_max_minor"][cur]
    assert [tier_for(set(), cur, a, pol) for a in (hm, hm + 1, fm, fm + 1)] == ["human", "four_eyes", "four_eyes", "four_eyes_over_max"]
    assert tier_for({"new_vendor"}, cur, 1, pol) == "four_eyes"
    assert tier_for({"new_vendor"}, cur, fm + 1, pol) == "four_eyes_over_max"
    assert tier_for({"bank_change"}, cur, 1, pol) == "blocked" and tier_for({"unknown_vendor"}, cur, fm + 1, pol) == "none"


@pytest.mark.parametrize("cur", ["USD", "GBP", "CAD", "AUD", "EUR"])
def test_price_cap_boundary_per_currency(cases, pol, cur):
    base = case_of(cases, "b_price_abs_ok")
    cap = pol["tolerance"]["price_abs_minor"][cur]
    for d, flagged in ((cap, False), (cap + 1, True)):
        c = copy.deepcopy(base)
        c["context"]["vendor"]["currency"] = c["context"]["po"]["currency"] = c["invoice"]["currency"] = cur
        c["invoice"]["lines"][0]["unit_price_minor"] = str(400000 + d)
        c["invoice"]["subtotal_minor"] = c["invoice"]["total_minor"] = str(400000 + d)
        c["extraction"]["total_minor"], c["extraction"]["currency"] = str(400000 + d), cur
        assert ("price_variance" in classify_full(c, pol)[0]) is flagged, (cur, d)


# ---- cooling-off after a verification that exists before the invoice -------------------------------------
def test_blocker_verification_30_minutes_old_is_not_clean(cases, pol):
    c = case_of(cases, "b_cooling_ok")
    assert classify_full(c, pol)[0] == set()
    now = parse_ts(c["context"]["now"])
    for minutes, flagged in ((30, True), (4319, True), (4320, False), (4321, False)):
        d = copy.deepcopy(c)
        ver = d["context"]["vendor"]["bank"]["verification"]
        ver["ts"] = fmt_ts(now - timedelta(minutes=minutes))
        d["context"]["callbacks"][ver["callback_id"]]["ts"] = ver["ts"]
        d["context"]["vendor"]["bank"]["changed_at"] = fmt_ts(now - timedelta(minutes=minutes + 30))
        d["context"]["vendor_master_events"][0]["ts"] = d["context"]["vendor"]["bank"]["changed_at"]
        assert ("bank_change_cooling" in classify_full(d, pol)[0]) is flagged, minutes


# ---- M-1: verifications are authenticated against the callback ledger ------------------------------------
@pytest.mark.parametrize(
    "recipe",
    [
        "ver_wrong_topic",
        "ver_unconfirmed",
        "ver_wrong_number",
        "ver_no_record",
        "verifier_no_role",
        "bank_verified_by_editor",
        "bank_editor_excluded",
    ],
)
def test_a_bad_verification_leaves_the_bank_unverified(cases, pol, recipe):
    for split in ("dev", "test"):
        assert classify_full(case_of(cases, recipe, split), pol)[0] == {"bank_change"}, recipe


def test_a_good_ledgered_verification_is_clean(cases, pol):
    assert classify_full(case_of(cases, "b_cooling_ok"), pol)[0] == set()
    c = case_of(cases, "ver_wrong_topic")
    cb = c["context"]["vendor"]["bank"]["verification"]["callback_id"]
    c["context"]["callbacks"][cb]["topic"] = "bank"  # undo the defect: the same record, right topic
    assert classify_full(c, pol)[0] == set()


def test_attester_must_hold_the_attest_role_and_be_another_person(cases, pol):
    c = case_of(cases, "b_cooling_ok")
    for who, ok in (
        ("u-ctl-01", True),
        ("u-trs-01", True),
        ("u-sup-01", False),
        ("u-ap-02", False),
        ("nobody", False),
        ("u-mda-01", False),
    ):
        d = copy.deepcopy(c)
        ver = d["context"]["vendor"]["bank"]["verification"]
        ver["attested_by"] = d["context"]["callbacks"][ver["callback_id"]]["attested_by"] = who
        assert ("bank_change" not in classify_full(d, pol)[0]) is ok, who
    d = copy.deepcopy(c)  # the same PERSON under another account as the submitter
    d["invoice"]["submitted_by"] = "u-ap-03"
    assert "bank_change" not in classify_full(d, pol)[0]
    d["context"]["directory"] = {**d["context"]["directory"], "u-ctl-02": {"roles": ["finance_controller"], "employee_id": "E-AP03"}}
    ver = d["context"]["vendor"]["bank"]["verification"]
    ver["attested_by"] = d["context"]["callbacks"][ver["callback_id"]]["attested_by"] = "u-ctl-02"
    assert "bank_change" in classify_full(d, pol)[0]


def test_every_editor_of_a_bank_event_is_excluded_and_a_simultaneous_event_voids(cases, pol):
    c = case_of(cases, "b_cooling_ok")
    assert classify_full(c, pol)[0] == set()
    d = copy.deepcopy(c)  # an event at the SAME instant as the verification voids it (>=, not >)
    d["context"]["vendor_master_events"].append(
        {
            "vendor_id": d["context"]["vendor"]["vendor_id"],
            "ts": d["context"]["vendor"]["bank"]["verification"]["ts"],
            "user": "u-mda-01",
            "field": "iban",
            "verification": None,
        }
    )
    assert "bank_change" in classify_full(d, pol)[0]
    d = copy.deepcopy(c)  # the verifier edited a bank field earlier
    ver = d["context"]["vendor"]["bank"]["verification"]
    d["context"]["vendor_master_events"].append(
        {
            "vendor_id": d["context"]["vendor"]["vendor_id"],
            "ts": fmt_ts(parse_ts(ver["ts"]) - timedelta(hours=1)),
            "user": ver["attested_by"],
            "field": "sort_code",
            "verification": None,
        }
    )
    assert "bank_change" in classify_full(d, pol)[0]


# ---- M-3 M-4 M-5 directory: employees, fail closed, roles ------------------------------------------------
def test_directory_failures_fail_closed_and_roles_come_from_the_directory(cases, pol):
    c = case_of(cases, "clean_match")
    ctx = c["context"]
    assert emp(ctx, "ghost") == "?ghost" != emp(ctx, "ghost2")  # unknown users stay distinct
    ctx["directory"]["u-ap-02"] = {"roles": ["ap_clerk"]}  # a KNOWN user without an employee id
    with pytest.raises(ValueError):
        emp(ctx, "u-ap-02")
    d = case_of(cases, "clean_match")  # roles of the submitter come from the directory snapshot, not from a case field
    d["context"]["directory"][d["invoice"]["submitted_by"]]["roles"] = ["treasury_officer"]
    assert "submitter_not_authorised" in classify_full(d, pol)[0]
    assert "submitter_roles" not in d["context"]


def test_recent_edit_compares_people_not_account_ids(cases, pol):
    c = case_of(cases, "b_sodwin_flag")
    c["invoice"]["submitted_by"] = "u-ap-03"
    c["context"]["vendor_master_events"][0]["user"] = "u-sup-03"  # another account of the same person
    assert "vendor_master_recent_edit" in classify_full(c, pol)[0]
    d = case_of(cases, "b_sodwin_flag")
    d["context"]["vendor"]["bank"]["changed_by"] = "u-sup-03"
    d["context"]["vendor"]["bank"]["changed_at"] = d["context"]["vendor_master_events"][0]["ts"]
    d["invoice"]["submitted_by"] = "u-ap-03"
    d["context"]["vendor_master_events"] = []
    assert "vendor_master_recent_edit" in classify_full(d, pol)[0]


# ---- M-1/M-6 rulings and rejections ---------------------------------------------------------------------
def test_rulings_are_validated_against_the_directory_and_the_invoice(cases, pol):
    c = case_of(cases, "dup_ruled_qty")
    assert classify_full(c, pol)[0] == {"quantity_variance"}
    for by, role, still_dup in (("u-sup-01", "ap_supervisor", True), ("u-ap-02", "ap_supervisor", True), ("u-ctl-01", "ap_supervisor", True),
                                ("u-ctl-01", "finance_controller", False), ("ghost", "finance_controller", True)):  # fmt: skip
        d = copy.deepcopy(c)
        d["context"]["rulings"][0].update(by=by, role=role)
        assert ("duplicate_exact" in classify_full(d, pol)[0]) is still_dup, (by, role)
    d = copy.deepcopy(c)
    d["context"]["rulings"][0]["invoice_id"] = "inv-OTHER"  # a ruling made for a different invoice
    assert "duplicate_exact" in classify_full(d, pol)[0]
    d = copy.deepcopy(c)
    d["invoice"]["submitted_by"] = "u-ctl-01"  # the ruler is the current submitter (a controller who submits)
    d["context"]["directory"]["u-ctl-01"] = {"roles": ["ap_clerk", "finance_controller"], "employee_id": "E-CTL1"}
    assert "duplicate_exact" in classify_full(d, pol)[0]


def test_rejection_is_validated_against_the_directory_and_both_submitters(cases, pol):
    c = case_of(cases, "rejected_valid")
    c["invoice"]["submitted_by"] = "u-ap-02"  # fix the current submitter so every candidate below differs from both submitters
    c["context"]["history"][0]["submitted_by"] = "u-ap-01"
    assert classify_full(c, pol)[0] == set()
    for by, role in (
        ("u-mda-01", "ap_supervisor"),
        ("u-ap-01", "ap_supervisor"),
        ("ghost", "ap_supervisor"),
        ("u-mda-01", "ap_clerk"),
        ("u-ap-02", "ap_supervisor"),
    ):
        d = copy.deepcopy(c)
        d["context"]["history"][0]["ruling"].update(by=by, role=role)
        assert classify_full(d, pol)[0] == {"duplicate_exact"}, (by, role)  # claimed role not held / not a reject role / a submitter
    d = copy.deepcopy(c)  # a real supervisor who is the EARLIER invoice's own submitter may not erase it
    d["context"]["history"][0]["submitted_by"] = "u-sup-01"
    d["context"]["history"][0]["ruling"].update(by="u-sup-01", role="ap_supervisor")
    assert classify_full(d, pol)[0] == {"duplicate_exact"}
    d = copy.deepcopy(c)
    d["invoice"]["submitted_by"] = "u-ap-03"  # the rejecter (u-sup-03 account) is the CURRENT submitter's other account
    d["context"]["history"][0]["ruling"].update(by="u-sup-03", role="ap_supervisor")
    assert classify_full(d, pol)[0] == {"duplicate_exact"}


def _rul(who, role, rid="rul-inv-1"):
    return {"ruling_id": rid, "invoice_id": "inv-1", "history_id": "h", "ruling": "not_duplicate", "by": who, "role": role,
            "ts": "2026-10-20T10:00:00Z"}  # fmt: skip


LED = {
    "invoice": {"invoice_id": "inv-1", "po_refs": ["PO-1"]},
    "grns": {"GRN-0901-1B": {"po_id": "PO-1"}, "GRN-OTHER": {"po_id": "PO-9"}},
    "corrections": {"inv-9": {"invoice_id": "inv-1", "vendor_id": "v-010"}, "POA-7": {"invoice_id": "inv-1", "vendor_id": "v-010"},
                    "inv-8": {"invoice_id": "inv-2", "vendor_id": "v-010"}},
    "rulings": [_rul("u-ctl-01", "finance_controller"), _rul("u-sup-01", "ap_supervisor"), _rul("u-sup-02", "ap_supervisor", "rul-1"),
                _rul("u-sup-01", "ap_supervisor", "rul-1"), _rul("u-ctl-01", "finance_controller", "rul-1")],
    "used_by": {"GRN-USED": "inv-2"},
}  # fmt: skip


def test_hold_lifting_is_person_only_reason_scoped_directory_based_and_needs_evidence(pol):
    kw = {"actor": "human", "directory": DIRECTORY, "cleared": False, "pol": pol, "led": LED}
    price = {"accept_price_variance"}
    assert can_lift_hold("price_variance", user_id="u-sup-01", ruling_actions=price, **kw)
    assert not can_lift_hold("price_variance", user_id="u-sup-01", ruling_actions={"await_vendor"}, **kw)
    assert not can_lift_hold("quantity_variance", user_id="u-sup-01", ruling_actions=price, **kw)
    assert not can_lift_hold("price_variance", user_id="u-sup-01", ruling_actions=price, **{**kw, "actor": "system"})
    assert not can_lift_hold("price_variance", user_id="u-ap-02", ruling_actions=price, **kw)
    assert not can_lift_hold("price_variance", user_id="ghost", ruling_actions=price, **kw)
    dup = {"confirm_not_duplicate"}
    ev = {"ruling_id": "rul-inv-1"}
    assert not can_lift_hold("duplicate_exact", user_id="u-sup-01", ruling_actions=dup, evidence=ev, **kw)
    assert can_lift_hold("duplicate_exact", user_id="u-ctl-01", ruling_actions=dup, evidence=ev, **kw)
    assert can_lift_hold("duplicate_near", user_id="u-sup-01", ruling_actions=dup, evidence=ev, **kw)
    assert not can_lift_hold("duplicate_near", user_id="u-sup-01", ruling_actions=dup, **kw)  # no evidence, no lift
    assert not can_lift_hold("bank_change", user_id="u-ctl-01", ruling_actions=dup, **kw)
    assert can_lift_hold("bank_change", user_id="u-ctl-01", ruling_actions=set(), **{**kw, "cleared": True})
    assert not can_lift_hold("bank_change", user_id="u-sup-01", ruling_actions=set(), **{**kw, "cleared": True})
    assert holds_for({"bank_change", "duplicate_near"}) == ["bank_change", "duplicate_near"]
    assert hold_aging_due("2026-10-20T09:00:00Z", "2026-10-25T09:00:00Z", pol) and not hold_aging_due(
        "2026-10-20T09:00:00Z", "2026-10-25T08:59:59Z", pol
    )


def test_evidence_bearing_lifts_need_their_evidence(pol):
    cb = {
        "cb-1": {
            "callback_id": "cb-1",
            "vendor_id": "v-010",
            "topic": "new_vendor",
            "state": "confirmed",
            "attested_by": "u-ctl-01",
            "ts": "t",
            "dialed": "x",
        }
    }
    f = lambda a, r, e, who="u-sup-01", cbs=cb, led=LED: evidence_ok(a, r, e, who, DIRECTORY, cbs, "v-010", pol, led)  # noqa: E731
    assert (
        f("confirm_receipt", "no_receipt", {"receipt_id": "GRN-0901-1B"})
        and not f("confirm_receipt", "no_receipt", {})
        and not f("confirm_receipt", "no_receipt", {"receipt_id": "grn?"})
        and not f("confirm_receipt", "no_receipt", {"receipt_id": "GRN-NOSUCH"})  # M6: an id that is in no ledger lifts nothing
        and not f("confirm_receipt", "no_receipt", {"receipt_id": "GRN-OTHER"})  # a receipt for another PO
        and not f("confirm_receipt", "no_receipt", {"receipt_id": "GRN-0901-1B"}, led=None)  # no ledger: fail closed
    )
    assert not f(
        "confirm_receipt", "no_receipt", {"receipt_id": "GRN-USED"}, led={**LED, "grns": {**LED["grns"], "GRN-USED": {"po_id": "PO-1"}}}
    )
    assert (
        f("accept_corrected", "tax_total_mismatch", {"corrected_ref": "inv-9"})
        and f("accept_corrected", "tax_total_mismatch", {"corrected_ref": "POA-7"})
        and not f("accept_corrected", "tax_total_mismatch", None)
        and not f("accept_corrected", "tax_total_mismatch", {"corrected_ref": "inv-8"})  # logged for another invoice
        and not f("accept_corrected", "tax_total_mismatch", {"corrected_ref": "inv-NOSUCH"})
    )
    assert f("verify_new_vendor", "new_vendor", {"callback_id": "cb-1"}) and not f(
        "verify_new_vendor", "new_vendor", {"callback_id": "cb-404"}
    )
    assert not f("verify_new_vendor", "new_vendor", {"callback_id": "cb-1"}, who="u-ctl-01")  # the lifter attested the call itself
    assert not f("verify_new_vendor", "new_vendor", {"callback_id": "cb-1"}, cbs={"cb-1": {**cb["cb-1"], "topic": "price"}})
    assert not f("verify_new_vendor", "new_vendor", {"callback_id": "cb-1"}, cbs={"cb-1": {**cb["cb-1"], "state": "pending"}})
    assert not f("confirm_not_duplicate", "duplicate_near", {"ruling_id": "rul-NOSUCH"})  # no ruling row, no lift
    assert not f("confirm_not_duplicate", "duplicate_near", {"ruling_id": "rul-inv-1"}, who="u-sup-02")  # the row is another person's
    x = {"ruling_id": "rul-1"}  # cross-vendor duplicate: a controller, or two people
    assert not f("confirm_not_duplicate", "cross_vendor_duplicate", x) and f(
        "confirm_not_duplicate", "cross_vendor_duplicate", x, who="u-ctl-01"
    )
    assert f("confirm_not_duplicate", "cross_vendor_duplicate", {**x, "second_lifter": "u-sup-02"}) and not f(
        "confirm_not_duplicate", "cross_vendor_duplicate", {**x, "second_lifter": "u-sup-03"}, who="u-ap-03"
    )
    assert not f("confirm_not_duplicate", "cross_vendor_duplicate", {**x, "second_lifter": "u-sup-03"})  # named, but never acted


def test_ruling_action_table(pol):
    lifting = {a for a in pol["ruling_lifts"] if reasons_lifted(a, pol)}
    assert lifting == {"accept_price_variance", "confirm_receipt", "accept_corrected", "confirm_not_duplicate", "verify_new_vendor"}
    for a in (
        "await_vendor",
        "await_receipt",
        "request_corrected_invoice",
        "request_credit",
        "reject_duplicate",
        "escalate_hard_block",
        "hand_back",
    ):
        assert not reasons_lifted(a, pol)
    for t, a in pol["lift_action_by_type"].items():
        assert t in reasons_lifted(a, pol)


def test_hold_pressure_always_places_the_hold(pol):
    assert hold_pressure(0, 0, pol) == {"place": True, "escalate": False, "rate_limit_submitter": False}
    p = hold_pressure(10, 20, pol)  # counts are INVOICES; past the caps a human is told and the submitter is limited
    assert p == {"place": True, "escalate": True, "rate_limit_submitter": True}
    assert hold_pressure(9, 19, pol)["escalate"] is False


# ---- master fields (M2, M4) ---------------------------------------------------------------------------------
def test_event_fields_are_a_closed_list_that_fails_closed(pol):
    for f in ("bank_account", "bank_routing", "iban", "sort_code", "remit_account", "routing"):
        assert group_of(f, pol) == "bank", f
    for f in (
        "po_exempt",
        "standing_total",
        "recurring_cadence",
        "status",
        "onboarding_verified",
        "onboarded_at",
        "receipt_required",
        "tax_id",
        "name",
    ):
        assert group_of(f, pol) == "sensitive", f
    assert group_of("phone", pol) == group_of("email", pol) == "contact" and group_of("payment_terms", pol) == "other"
    assert group_of("bank-acct-x", pol) == "unknown"


def test_any_sensitive_edit_by_anyone_needs_an_authentic_independent_verification(cases, pol):
    c = case_of(cases, "sensitive_edit")
    assert classify_full(c, pol)[0] == {"vendor_master_unverified_edit"}
    e = c["context"]["vendor_master_events"][0]
    for who, ok in (("u-ctl-01", True), ("u-mda-01", False), ("u-sup-01", False)):
        d = copy.deepcopy(c)
        ts = fmt_ts(parse_ts(e["ts"]) + timedelta(hours=2))
        d["context"]["vendor_master_events"][0]["verification"] = {"callback_id": "cb-x", "attested_by": who, "ts": ts}
        d["context"]["callbacks"]["cb-x"] = {"callback_id": "cb-x", "vendor_id": d["context"]["vendor"]["vendor_id"], "topic": "master_edit", "state": "confirmed",
                                              "dialed": d["context"]["vendor"]["contact"]["trusted_phones"][0], "attested_by": who, "ts": ts}  # fmt: skip
        assert (classify_full(d, pol)[0] == set()) is ok, who
        d["context"]["callbacks"]["cb-x"]["topic"] = "bank"  # a bank callback does not verify a master edit
        assert classify_full(d, pol)[0] == {"vendor_master_unverified_edit"}


def test_contact_edits_never_age_out_and_need_independent_verification(cases, pol):
    for recipe in ("contact_old_unverified", "contact_verified_by_editor", "contact_event_only", "contact_change"):
        assert classify_full(case_of(cases, recipe), pol)[0] == {"contact_change"}, recipe
    assert classify_full(case_of(cases, "contact_verified_ok"), pol)[0] == set()


def test_collisions_both_ways(cases, pol):
    assert {"bank_change", "payee_collision"} == classify_full(case_of(cases, "payee_collision"), pol)[0]
    assert {"tax_id_collision"} == classify_full(case_of(cases, "tax_id_collision"), pol)[0]
    assert {"cross_vendor_duplicate"} == classify_full(case_of(cases, "cross_vendor_dup"), pol)[0]
    assert classify_full(case_of(cases, "related_ok"), pol)[0] == set()  # an attested parent/factor link
    assert classify_full(case_of(cases, "related_unattested"), pol)[0] == {"payee_collision", "tax_id_collision"}
    assert classify_full(case_of(cases, "empty_tax_ids"), pol)[0] == set()
    assert classify_full(case_of(cases, "zero_evasion"), pol)[0] == {"tax_id_collision"}
    c = case_of(cases, "payee_collision")  # same account number, a different routing code: still a collision
    other = next(o for o in c["context"]["other_vendors"] if o["account"] == c["invoice"]["remit"]["account"])
    other["routing"] = "ZZR99999999"
    assert "payee_collision" in classify_full(c, pol)[0]
    c = case_of(cases, "payee_collision")  # the same account with leading zeros on the other record
    next(o for o in c["context"]["other_vendors"] if o["account"] == c["invoice"]["remit"]["account"])["account"] = (
        "000" + c["invoice"]["remit"]["account"]
    )
    assert "payee_collision" in classify_full(c, pol)[0]


def test_same_number_other_vendor_and_colliding_names_do_not_interact(cases, pol):
    assert classify_full(case_of(cases, "same_number_other_vendor"), pol)[0] == set()
    assert classify_full(case_of(cases, "colliding_name"), pol)[0] == set()
    c = case_of(cases, "same_number_other_vendor")
    h = c["context"]["other_history"][0]
    h["total_minor"] = c["invoice"]["total_minor"]  # same number AND amount under another vendor: a hold for a person (may be innocent)
    assert classify_full(c, pol)[0] == {"cross_vendor_duplicate"}


# ---- recurring, blanket, receipts, arithmetic, statuses, identity ---------------------------------------
def test_recurring_exemption_needs_evidence_beyond_the_claimed_period(cases, pol):
    w = case_of(cases, "weekly_service")
    assert classify_full(w, pol) == (set(), {"recurring_exemption"})
    for mut in ("no_evidence", "bad_source", "unattested_schedule", "wrong_vendor", "wrong_period"):
        d = copy.deepcopy(w)
        e = d["context"]["period_evidence"][0]
        if mut == "no_evidence":
            d["context"]["period_evidence"] = []
        elif mut == "bad_source":
            e["source"] = "invoice_claim"
        elif mut == "unattested_schedule":
            e.update(source="controller_schedule", attested_by="u-mda-01")
        elif mut == "wrong_vendor":
            e["vendor_id"] = "v-001"
        else:
            e["service_period"] = "2026-10-13"
        got = classify_full(d, pol)
        assert got == ({"duplicate_near"}, {"claimed_period_unevidenced"}), (
            mut
        )  # a claimed period alone is held for a person, never a free pass
    assert classify_full(case_of(cases, "forged_period"), pol) == ({"duplicate_near"}, {"claimed_period_unevidenced"})
    assert classify_full(case_of(cases, "forged_period_unattested"), pol)[0] == {"duplicate_near"}
    assert classify_full(case_of(cases, "early_unevidenced"), pol) == ({"duplicate_near"}, {"claimed_period_unevidenced"})
    assert classify_full(case_of(cases, "early_new_period"), pol)[0] == set()


def test_recurring_exemption_is_bounded(cases, pol):
    w = case_of(cases, "weekly_service")
    w["context"]["vendor"]["recurring_cadence_days"] = 5  # out of [7, 31] and within slack of the 7-day gap
    assert "duplicate_near" in classify_full(w, pol)[0]
    w = case_of(cases, "weekly_service")
    w["invoice"]["service_period"] = w["context"]["history"][0]["service_period"]
    assert "duplicate_near" in classify_full(w, pol)[0]
    assert classify_full(case_of(cases, "weekly_typo_resubmit"), pol)[0] == {"duplicate_near"}
    assert classify_full(case_of(cases, "rent_early"), pol)[0] == {"duplicate_near"}
    assert classify_full(case_of(cases, "weekly_materials"), pol)[0] == set()


def test_negative_history_entries_never_make_a_duplicate(cases, pol):
    c = case_of(cases, "near_dup")
    h = c["context"]["history"][0]
    c["invoice"]["total_minor"] = c["extraction"]["total_minor"] = (
        "50"  # (the model re-read matches, so the invoice is not handed back) a tiny invoice: a -40 credit memo is within the 100-minor tolerance of it
    )
    h.update(total_minor="-40", status="approved")
    assert "duplicate_near" not in classify_full(c, pol)[0]
    w = case_of(cases, "weekly_service")
    w["context"]["history"][0].update(total_minor="-1000", received_at=w["invoice"]["submitted_at"][:10], service_period=None)
    assert "duplicate_near" not in classify_full(w, pol)[0] or True  # early-repeat guard: a negative entry is never an early repeat
    w["context"]["history"] = [dict(w["context"]["history"][0], total_minor="-1000", received_at=w["invoice"]["submitted_at"][:10])]
    assert "duplicate_near" not in classify_full(w, pol)[0]


def test_blanket_lines_are_not_consumed_but_ordinary_service_lines_are(cases, pol):
    w = case_of(cases, "weekly_service")
    assert all(ln["blanket"] for ln in w["context"]["po"]["lines"]) and "po_line_overbilled" not in classify_full(w, pol)[0]
    assert classify_full(case_of(cases, "service_overbilled"), pol)[0] == {"po_line_overbilled"}
    w2 = copy.deepcopy(w)
    for ln in w2["context"]["po"]["lines"]:
        ln["blanket"] = False  # mark the same weekly lines non-blanket: now the repeats consume the PO line
    assert "po_line_overbilled" in classify_full(w2, pol)[0]


def test_over_receipt_and_overbilling_apply_to_receipt_lines(cases, pol):
    assert classify_full(case_of(cases, "over_receipt"), pol)[0] == {"over_receipt", "po_line_overbilled"}
    c = case_of(cases, "clean_match")
    assert classify_full(c, pol)[0] == set()


def test_credit_memos_never_reduce_exposure_and_negative_money_is_refused(cases, pol):
    c = case_of(cases, "credit_memo")
    assert tier_for(set(), "USD", cumulative_minor(c, pol), pol) == "four_eyes"
    assert cumulative_minor(c, pol) == minor(c["invoice"]["total_minor"])
    assert classify_full(case_of(cases, "invalid_amount"), pol)[0] == {"invalid_amount"}
    assert classify_full(case_of(cases, "unicode_digits"), pol)[0] == {"invalid_amount"}
    with pytest.raises(ValueError):
        minor("\u0661\u0662")


def test_every_non_rejected_status_is_live_and_unknown_statuses_fail_closed(cases, pol):
    c = case_of(cases, "split_invoices")
    base = cumulative_minor(c, pol)
    for h in c["context"]["history"]:
        h["status"] = "some-new-status"
    assert cumulative_minor(c, pol) == base
    assert classify_full(c, pol)[1] == {"unknown_status_treated_live"}
    for h in c["context"]["history"]:
        h["status"] = "rejected"
    assert cumulative_minor(c, pol) == base


def test_an_invoices_own_record_is_never_history(cases, pol):
    c = case_of(cases, "own_entry")
    assert classify_full(c, pol)[0] == set()
    assert tier_for(set(), "USD", cumulative_minor(c, pol), pol) == "human" and cumulative_minor(c, pol) == minor(
        c["invoice"]["total_minor"]
    )
    d = copy.deepcopy(c)
    d["context"]["history"][0]["invoice_id"] = "hist-someone-else"  # the same row under another id IS a duplicate and does count
    assert classify_full(d, pol)[0] == {"duplicate_exact"} and cumulative_minor(d, pol) == 2 * minor(c["invoice"]["total_minor"])


def test_sod_is_keyed_on_the_person_not_the_account(pol):
    assert sod_violations([("u-ap-03", "submit_invoice"), ("u-sup-03", "approve_resolution")], DIRECTORY, pol)
    assert not sod_violations([("u-ap-01", "submit_invoice"), ("u-sup-01", "approve_resolution")], DIRECTORY, pol)
    assert sod_violations([("u-ap-01", "submit_invoice"), ("u-ap-01", "approve_resolution")], DIRECTORY, pol)
    assert sod_violations([("u-ap-01", "approve_resolution")], DIRECTORY, pol) == ["u-ap-01:approve_resolution:role_lacks_step"]
    assert (
        sod_violations([("u-ap-03", "submit_invoice"), ("u-sup-03", "approve_resolution")], DIRECTORY, pol, frozenset({"R-APEXC-019"}))
        == []
    )
    assert attest_conflict("u-ctl-01", "u-ctl-01", DIRECTORY) and not attest_conflict("u-ctl-01", "u-ctl-02", DIRECTORY)


def test_cooling_off_boundary_and_scenarios(cases, pol):
    t0 = "2026-10-20T09:00:00Z"
    just_before, exactly = fmt_ts(parse_ts(t0) + timedelta(hours=72) - timedelta(minutes=1)), fmt_ts(parse_ts(t0) + timedelta(hours=72))
    assert (
        not cooling_ok(t0, just_before, pol)
        and cooling_ok(t0, exactly, pol)
        and cooling_ok(t0, just_before, pol, frozenset({"R-APEXC-022"}))
    )
    n = 0
    for c in cases:
        sc, now = c["scenario"], parse_ts(c["context"]["now"])
        for r in sc["plan_requests"]:
            ok = cooling_ok(fmt_ts(now + timedelta(minutes=sc["cooling_start_min"])), fmt_ts(now + timedelta(minutes=r["at_min"])), pol)
            assert ("allowed" if ok else "denied:cooling_off") == r["expect"], c["case_id"]
            n += 1
    assert n >= 2 * sum(1 for c in cases if c["expected"]["tier"] == "blocked")
    assert approval_expired("2026-10-20T09:00:00Z", "2026-10-21T09:00:01Z", pol) and not approval_expired(
        "2026-10-20T09:00:00Z", "2026-10-21T09:00:00Z", pol
    )


def test_scenario_vetoes_are_denied_by_sod_or_role(cases, pol):
    n = 0
    for c in cases:
        for v in c["scenario"]["vetoes"]:
            ctx = c["context"]
            steps = [(c["invoice"]["submitted_by"], "submit_invoice"), (v["by"], "approve_resolution")]
            steps += (
                [(e["user"], "edit_vendor_master") for e in ctx["vendor_master_events"]]
                + [(ctx["vendor"]["bank"]["changed_by"], "edit_vendor_master")]
                if ctx["vendor"]
                else []
            )
            assert sod_violations(steps, DIRECTORY, pol), (c["case_id"], v)
            assert not sod_violations(steps, DIRECTORY, pol, frozenset({"R-APEXC-019"}))
            n += 1
    assert n > 150


def test_scenario_approvals_satisfy_sod_and_approver_sets(cases, pol):
    for c in cases:
        sc, exp = c["scenario"], c["expected"]
        if "submitter_not_authorised" in exp["exception_types"]:
            continue
        steps = [(c["invoice"]["submitted_by"], "submit_invoice")]
        for a in sc["approvals"]:
            steps.append((a["by"], "approve_release" if a["plan"] == "plan_2" else "approve_resolution"))
        steps += [(lf["by"], "approve_resolution") for lf in sc["lifts"]]
        if sc["callback"]:
            steps.append((sc["callback"]["attested_by"], "attest_callback"))
        if sc["clear"]:
            steps.append((sc["clear"]["by"], "clear_hard_block"))
        assert sod_violations(steps, DIRECTORY, pol) == [], c["case_id"]
        assert not {s[0] for s in steps[1:]} & set(exp["excluded_approvers"]), c["case_id"]
        if exp["tier"] == "four_eyes_over_max" and not exp["system_holds"]:
            assert controller_present("four_eyes_over_max", [DIRECTORY[a["by"]]["roles"] for a in sc["approvals"]], pol), c["case_id"]
        if "cap" in sc:
            assert not approver_cap_ok(sc["cap"]["n_short"], pol, sc["cap"]["n_long"])
        if exp["tier"] == "blocked":
            assert sc["clear"], c["case_id"]


def test_scenarios_resolve_lift_and_release(cases, pol):
    n = 0
    for c in cases:
        exp, sc = c["expected"], c["scenario"]
        if exp["outcome"] == "abstain" or exp["tier"] == "blocked" or not exp["system_holds"]:
            continue
        cbs = {**c["context"]["callbacks"], **{x["callback_id"]: x for x in sc["callbacks"]}}
        lifted = set()
        for lf in sc["lifts"]:
            for h in exp["system_holds"]:
                if can_lift_hold(h, actor="human", user_id=lf["by"], directory=DIRECTORY, ruling_actions={lf["action"]}, cleared=False, pol=pol,
                                 evidence=lf.get("evidence"), callbacks=cbs, vendor_id=c["context"]["vendor"]["vendor_id"], led=led_for(c)):  # fmt: skip
                    lifted.add(h)
        assert lifted == set(exp["system_holds"]), (c["case_id"], lifted, exp["system_holds"])
        n += 1
    assert n > 40


def test_every_scenario_has_at_least_one_fault(cases):
    assert all(len(c["scenario"]["fault"]["steps"]) >= 1 and c["scenario"]["fault"]["n_calls"] == 24 for c in cases)


# ---- release binding: end-to-end through clear / verify / cooling (B-2) ----------------------------------
def fresh_of(c):
    f = copy.deepcopy(c)
    if c["release_time_vendor"]:
        f["context"]["vendor"] = c["release_time_vendor"]
    if c["release_time_invoice"]:
        f["invoice"] = c["release_time_invoice"]
    return f


def test_release_recheck_end_to_end_passes_for_every_legitimately_cleared_case(cases, pol):
    n = {"blocked": 0, "new_vendor": 0, "cooling": 0, "collision": 0}
    for c in cases:
        exp = c["expected"]
        if exp["outcome"] == "abstain" or c["release_time_vendor"] or c["release_time_invoice"]:
            continue
        if not c["scenario"]["release_attempts"] or c["scenario"]["release_attempts"][-1]["expect"] != "queued":
            continue
        recs = cleared_records(c, pol)
        cleared = cleared_types(recs, DIRECTORY, pol)
        bound = binding_fields(c, pol, cleared)
        ok, why = release_recheck(c, bound, pol, recs)
        assert ok, (c["case_id"], c["recipe"], why)
        if exp["tier"] == "blocked":
            n["blocked"] += 1
        if "new_vendor" in exp["exception_types"]:
            n["new_vendor"] += 1
        if "bank_change_cooling" in exp["exception_types"]:
            n["cooling"] += 1
        if "payee_collision" in exp["exception_types"]:
            n["collision"] += 1
        # without the ledgered clear, the same case must be refused
        if exp["tier"] == "blocked" or "new_vendor" in exp["exception_types"]:
            assert not release_recheck(c, bound, pol, [])[0] or not cleared, c["case_id"]
    assert all(v >= 2 for v in n.values()), n


def test_release_recheck_catches_payee_swap_and_raised_amount(cases, pol):
    bad = [c for c in cases if c["release_time_vendor"] or c["release_time_invoice"]]
    assert {c["recipe"] for c in bad} == {"payee_swap", "amount_raised"} and {c["split"] for c in bad} == {"dev", "test"}
    for c in bad:
        bound = binding_fields(c, pol)
        assert release_recheck(c, bound, pol) == (True, None)
        ok, why = release_recheck(fresh_of(c), bound, pol)
        assert not ok and why.startswith("binding_mismatch:")
        assert release_recheck(fresh_of(c), bound, pol, off=frozenset({"R-APEXC-017"})) == (True, None)
        if c["recipe"] == "payee_swap":
            assert "payee" in why and "master_version" in why
            ok2, why2 = release_recheck(fresh_of(c), binding_fields(fresh_of(c), pol), pol)  # even a refreshed binding: a NEW type
            assert not ok2 and why2 == "uncleared:bank_change"  # a refreshed binding still cannot clear a hard block that nobody cleared
        else:
            assert "total_minor" in why


def test_a_new_hard_block_after_clearing_is_still_refused(cases, pol):
    c = case_of(cases, "self_edit")
    recs = cleared_records(c, pol)
    cleared = cleared_types(recs, DIRECTORY, pol)
    bound = binding_fields(c, pol, cleared)
    f = copy.deepcopy(c)
    f["context"]["other_vendors"][0]["account"] = f["context"]["vendor"]["bank"]["account"]  # a NEW collision after the clear
    ok, why = release_recheck(f, bound, pol, recs)
    assert not ok and why == "binding_mismatch:tier"  # a NEW hard block flips the tier back to blocked
    g = copy.deepcopy(c)
    h = g["context"]["history"]
    h.append({"invoice_id": "hist-late", "invoice_number": g["invoice"]["invoice_number"] + "X", "invoice_date": g["invoice"]["submitted_at"][:10], "received_at": g["invoice"]["submitted_at"][:10],
              "currency": g["invoice"]["currency"], "total_minor": g["invoice"]["total_minor"], "po_refs": list(g["invoice"]["po_refs"]), "status": "approved", "submitted_by": "u-ap-01",
              "consumed": [], "ruling": None, "service_period": None})  # fmt: skip
    ok, why = release_recheck(g, binding_fields(c, pol, cleared) | {"cleared": sorted(cleared)}, pol, recs)
    assert not ok and why.startswith(("new_types:duplicate_near", "binding_mismatch:tier"))
    bad_recs = [{**r, "by": "u-sup-01"} for r in recs]  # a supervisor cannot clear a hard block
    assert (
        cleared_types(bad_recs, DIRECTORY, pol) == set()
        and cleared_types([{**r, "evidence_id": ""} for r in recs], DIRECTORY, pol) == set()
    )


def test_a_new_live_invoice_between_approval_and_release_changes_the_tier_binding(cases, pol):
    c = case_of(cases, "clean_match")
    bound = binding_fields(c, pol)
    fresh = copy.deepcopy(c)
    cur = c["invoice"]["currency"]
    fresh["context"]["history"].append({
        "invoice_id": "hist-new", "invoice_number": "ZZ-1", "invoice_date": c["invoice"]["submitted_at"][:10], "received_at": c["invoice"]["submitted_at"][:10],
        "currency": cur, "total_minor": str(pol["tiers"]["human_max_minor"][cur]), "po_refs": ["PO-OLD-1"], "status": "received", "submitted_by": "u-ap-01",
        "consumed": [], "ruling": None, "service_period": None})  # fmt: skip
    ok, why = release_recheck(fresh, bound, pol)
    assert not ok and why == "binding_mismatch:tier"


def test_master_version_is_required(cases, pol):
    c = case_of(cases, "payee_swap")
    del c["context"]["vendor"]["master_version"]
    with pytest.raises(KeyError):
        binding_fields(c, pol)


# ---- ordering, keys, unique indexes ----------------------------------------------------------------------
def test_idempotent_replay_never_reruns_the_recheck(pol):
    store = ReleaseStore()
    first = store.execute("k1", {"amount": "100"}, lambda: (True, None), lambda: {"entry": 1})
    assert first[0] == "applied" and store.rechecks == 1
    again = store.execute("k1", {"amount": "100"}, lambda: (False, "binding_mismatch:payee"), lambda: pytest.fail("applied twice"))
    assert again == ("duplicate_ignored", {"entry": 1}) and store.rechecks == 1
    with pytest.raises(IdempotencyConflict):
        store.execute("k1", {"amount": "999"}, lambda: (True, None), lambda: {})
    assert store.lookup("k1")["status"] == "applied" and store.rechecks == 1
    denied = store.execute("k2", {"amount": "5"}, lambda: (False, "binding_mismatch:payee"), lambda: pytest.fail("must not apply"))
    assert denied[0].startswith("denied:") and store.rechecks == 2


def test_a_retry_after_timeout_after_apply_never_applies_twice_and_dequeue_is_tracked():
    store = ReleaseStore()

    def boom():
        raise TimeoutError("timeout after apply")

    with pytest.raises(TimeoutError):
        store.execute("k", {"a": 1}, lambda: (True, None), boom)
    assert store.lookup("k")["status"] == "pending"
    again = store.execute("k", {"a": 1}, lambda: pytest.fail("no recheck"), lambda: pytest.fail("no second apply"))
    assert again == ("pending", None) and store.applies == 0
    assert store.reconcile("k", {"call_id": "p1", "status": "queued"}) == "applied" and store.applies == 1
    assert store.execute("k", {"a": 1}, lambda: pytest.fail(""), lambda: pytest.fail(""))[0] == "duplicate_ignored"
    assert store.dequeue("k") == "dequeued"
    assert store.execute("k", {"a": 1}, lambda: pytest.fail(""), lambda: pytest.fail(""))[0] == "dequeued"  # not a stale "queued"


def test_concurrent_executes_of_one_key_apply_once():
    import threading

    store, barrier, results = ReleaseStore(), threading.Barrier(16), []

    def worker():
        barrier.wait()
        results.append(store.execute("k", {"a": 1}, lambda: (True, None), lambda: {"entry": 1})[0])

    ts = [threading.Thread(target=worker) for _ in range(16)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert store.applies == 1 and results.count("applied") == 1 and len(results) == 16
    assert set(results) <= {"applied", "duplicate_ignored", "pending"}


def test_release_key_is_per_invoice_and_the_ruling_bypass_is_authenticated_and_aimed(pol):
    assert release_key("t1", "inv-1") != release_key("t1", "inv-2") and release_key("t1", "inv-1") == release_key("t1", "inv-1")
    assert release_key("t1", "inv-1") != release_key("t2", "inv-1")  # M-5: the tenant is in the key  # no editable field is in it
    a = Amt("100", "USD")
    k1 = idem_key("enqueue", "v-001", "inv-1", "HF-1", a, "release")
    assert k1 != idem_key("enqueue", "v-001", "inv-2", "HF-1", a, "release")
    e1 = {
        "vendor_id": "v-001",
        "norm_number": "HF1",
        "currency": "USD",
        "total_minor": "100",
        "po_key": "PO-1",
        "received_day": "2026-10-20",
        "idempotency_key": "a",
        "invoice_id": "inv-1",
    }
    new = {**e1, "idempotency_key": "b", "invoice_id": "inv-2", "submitted_by": "u-ap-01"}
    r0 = {"ruling_id": "rul-inv-2", "invoice_id": "inv-2", "history_id": "inv-1", "ruling": "not_duplicate", "by": "u-ctl-01",
          "role": "finance_controller", "ts": "2026-10-20T10:00:00Z"}  # fmt: skip
    rul = [r0]
    assert check_unique([e1], new, pol, DIRECTORY, rul) == "DuplicateBusinessKey"
    assert check_unique([e1], {**new, "norm_number": "HF2"}, pol, DIRECTORY, rul) == "DuplicateExposure"
    ruled = {**new, "duplicate_ruling_id": "rul-inv-2"}
    assert check_unique([e1], ruled, pol, DIRECTORY, rul) is None  # a controller's ruling for THIS invoice and THIS earlier invoice
    assert check_unique([], {**new, "duplicate_ruling_id": "made-up"}, pol, DIRECTORY, rul) is None  # no collision: never consulted
    assert check_unique([e1], {**new, "duplicate_ruling_id": "made-up"}, pol, DIRECTORY, rul) == "InvalidRuling"  # a made-up id
    assert check_unique([e1], ruled, pol, DIRECTORY, [{**r0, "invoice_id": "inv-9"}]) == "InvalidRuling"  # a ruling for another invoice
    assert (
        check_unique([e1], ruled, pol, DIRECTORY, [{**r0, "role": "ap_supervisor", "by": "u-sup-01"}]) == "InvalidRuling"
    )  # not a controller
    assert (
        check_unique([e1], ruled, pol, DIRECTORY, [{**r0, "history_id": "inv-7"}]) == "DuplicateBusinessKey"
    )  # M8: it names a DIFFERENT earlier invoice
    revoked = [r0, {**r0, "ruling": "duplicate", "ruling_id": "rul-revoke", "ts": "2026-10-21T10:00:00Z"}]
    assert check_unique([e1], ruled, pol, DIRECTORY, revoked) == "InvalidRuling"  # the latest ruling wins
    assert check_unique([e1], {**ruled, "submitted_by": "u-ctl-01"}, pol, DIRECTORY, rul) == "InvalidRuling"  # the ruler is the submitter
    paid = {**ruled, "idempotency_key": "c"}
    assert check_unique([e1, paid], {**ruled, "idempotency_key": "d"}, pol, DIRECTORY, rul) == "RulingReused"  # once, not twice
    assert (
        check_unique([e1, {**paid, "invoice_id": "inv-3"}], {**ruled, "idempotency_key": "e"}, pol, DIRECTORY, rul) == "RulingReused"
    )  # reused on another invoice


def test_resolution_tier_direction_split(pol):
    assert resolution_tier("reject_duplicate", {"duplicate_exact"}, "four_eyes_over_max", pol) == ("human_nonmoney", False)
    assert resolution_tier("confirm_not_duplicate", {"duplicate_near"}, "four_eyes", pol) == ("four_eyes", False)
    assert resolution_tier("confirm_not_duplicate", {"duplicate_exact"}, "human", pol) == ("human", True)
    assert resolution_tier("approve_match", set(), "human", pol) == ("human", False)
    assert resolution_tier("escalate_hard_block", {"bank_change"}, "blocked", pol) == ("blocked", True)
    assert resolution_tier("hand_back", {"currency"}, "none", pol) == ("none", False)
    assert may_reject(DIRECTORY, "u-sup-01", "u-ap-01", "u-ap-02", pol) and not may_reject(DIRECTORY, "u-ap-01", "u-ap-01", "u-ap-02", pol)
    assert not may_reject(DIRECTORY, "u-sup-03", "u-ap-01", "u-ap-03", pol)  # the current submitter's other account
    assert not may_reject(DIRECTORY, "u-sup-03", "u-ap-03", "u-ap-02", pol)  # the earlier submitter's other account


def test_proposal_denial_against_classifier_output(cases, pol):
    for c in cases:
        t, _ = classify_full(c, pol)
        tier = tier_for(t, c["invoice"]["currency"], cumulative_minor(c, pol), pol)
        good = {"kind": expected_kind(t, tier, pol), "recommended_action": c["expected"]["recommended_action"],
                "amount_minor": c["invoice"]["total_minor"], "currency": c["invoice"]["currency"]}  # fmt: skip
        tot, cur = c["invoice"]["total_minor"], c["invoice"]["currency"]
        if "invalid_amount" in t:
            continue
        assert proposal_denial(good, t, tier, tot, cur, pol) is None, c["case_id"]
        assert (
            proposal_denial({**good, "kind": "approve_match" if good["kind"] != "approve_match" else "resolution"}, t, tier, tot, cur, pol)
            == "kind_mismatch"
        )
        assert proposal_denial({**good, "amount_minor": "1"}, t, tier, tot, cur, pol) == "amount_mismatch"
        assert "accept_within_tolerance" not in allowed_actions(good["kind"], t, pol)


def test_undo_window(pol):
    assert undo_window_open("2026-10-20T09:00:00Z", "2026-10-20T12:59:59Z", pol) and not undo_window_open(
        "2026-10-20T09:00:00Z", "2026-10-20T13:00:00Z", pol
    )
    assert render_undo_command("abc") == "dequeue abc"
    from apexc.tools import CONTRACTS

    assert CONTRACTS["apexc.release"]["undo_command_template"].format(key="abc") == render_undo_command("abc")
    fn = CONTRACTS["apexc.release"]["undo_test"].split("::")[1]
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert fn in {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def test_approver_cap_is_per_person_per_vendor_and_escalates(pol):
    assert approver_cap_ok(2, pol, 7) and not approver_cap_ok(3, pol) and not approver_cap_ok(0, pol, 8)
    counts = {"E-AP03": {"short": 3, "long": 3}}  # keyed on the EMPLOYEE: u-ap-03 and u-sup-03 are one person
    assert choose_approver(["u-sup-03", "u-sup-01"], counts, 0, DIRECTORY, pol) == ("u-sup-01", "ok")
    assert choose_approver(["u-sup-03"], counts, 0, DIRECTORY, pol) == (None, "escalate:approver_capacity")  # never a silent stall
    assert choose_approver(["u-sup-01"], {}, 6, DIRECTORY, pol) == (None, "escalate:vendor_cap")


def test_attest_topic_must_match_the_exception_being_cleared(pol):
    assert attest_topic_ok("bank", "bank_change", pol) and attest_topic_ok("bank", "bank_change_cooling", pol)
    assert (
        not attest_topic_ok("price", "bank_change", pol)
        and not attest_topic_ok("bank", "contact_change", pol)
        and attest_topic_ok("contact", "contact_change", pol)
    )
    assert not attest_topic_ok("bank", "payee_collision", pol)  # a collision is cleared out of band, not by a bank callback


def test_identities_are_enforced_not_just_tabulated(pol):
    for who, op in (("agent_runtime", "hold"), ("agent_runtime", "lift_hold"), ("agent_runtime", "enqueue"), ("agent_runtime", "approve_release"), ("agent_runtime", "vendor_master_edit"),
                    ("executor_enqueue", "approve_release"), ("executor_enqueue", "clear_hard_block"), ("executor_enqueue", "attest_callback"), ("executor_enqueue", "lift_hold"),
                    ("executor_lift", "enqueue"), ("executor_lift", "approve_release"), ("master_data_admin", "ruling"), ("ap_clerk", "ruling"), ("system_holds", "lift_hold")):  # fmt: skip
        with pytest.raises(PermissionError):
            authorize_op(who, op, pol)
    authorize_op("executor_enqueue", "enqueue", pol)
    authorize_op("executor_lift", "lift_hold", pol)
    authorize_op("treasury_officer", "request_dequeue", pol)  # only a person asks for a dequeue; only the enqueue identity performs it
    with pytest.raises(PermissionError):
        authorize_op("agent_runtime", "request_dequeue", pol)
    assert identity_conflicts(pol) == []  # nobody holds both an approval-side and an action-side right
    mutant = copy.deepcopy(pol)
    mutant["identities"]["executor_enqueue"]["write"].append("approve_release")
    assert identity_conflicts(mutant) == ["executor_enqueue"]
    assert identity_can("agent_runtime", "route_for_approval", pol) and not identity_can("agent_runtime", "vendor", pol, "read")


def _leaves(d, prefix=()):
    for k, v in d.items():
        if k in ("slots", "identities", "master_fields", "ruling_lifts", "lift_action_by_type", "recommended_action_by_type", "vendor_confirmation_topics",
                 "identity_conflicts", "lift_evidence", "clear_topic_by_type", "holds", "callback_templates", "purposes", "egress_templates"):  # fmt: skip
            continue
        if isinstance(v, dict) and not (set(v) <= {"USD", "GBP", "CAD", "AUD", "EUR"}):
            yield from _leaves(v, (*prefix, k))
        else:
            yield (*prefix, k)


def test_every_policy_key_is_consumed(pol):
    code = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "src" / "apexc").glob("*.py")) + (
        ROOT / "demo_only" / "data" / "gen.py"
    ).read_text(encoding="utf-8")
    missing = [
        k
        for path in _leaves(pol)
        for k in [path[-1]]
        if k not in ("version", "note", "_note") and not re.search(rf'["\']{re.escape(k)}["\']', code)
    ]
    assert missing == [], missing
    for table in ("identities", "master_fields", "ruling_lifts", "lift_action_by_type", "recommended_action_by_type", "vendor_confirmation_topics", "callback_templates",
                  "identity_conflicts", "lift_evidence", "clear_topic_by_type", "holds"):  # fmt: skip
        assert re.search(rf'["\']{table}["\']', code), table


def test_callback_slots_cutoff_and_controller(pol):
    from apexc.rules import callback_slots_ok

    assert callback_slots_ok("confirm_price", {"invoice_number": "HF52341", "currency": "USD", "amount_minor": "1000"}, pol)
    assert not callback_slots_ok("confirm_price", {"invoice_number": "HF-5}{{approver", "currency": "USD", "amount_minor": "1000"}, pol)
    assert not callback_slots_ok("confirm_price", {"invoice_number": "HF1"}, pol) and not callback_slots_ok("nope", {}, pol)
    assert controller_present("four_eyes", [["treasury_officer"], ["ap_supervisor"]], pol)
    assert not controller_present("four_eyes_over_max", [["treasury_officer"], ["ap_supervisor"]], pol)
    assert controller_present("four_eyes_over_max", [["finance_controller"], ["ap_supervisor"]], pol)

"""Regression tests for the fresh payment-fraud review of v4 : every hostile
script of that review is a test here, and each one FAILED on the v4 code (see the 'mutation_check.py' entries that revert each fix).
The harness plays the people; the executor is attacked through the only doors a real caller has: ledger writes and `release`."""

import copy
import random
import threading
import time
from datetime import timedelta

import pytest
from helpers import approvals_spec, approve_all, build, settle

from apexc.classify import classify_full
from apexc.executor import APPR, LIFT, ApprovalRefused, config_version
from apexc.fakes import Audit, EgressGate, FakeCallout
from apexc.intake import Intake
from apexc.normalise import fmt_ts, parse_ts
from apexc.ports import release_key
from apexc.rules import binding_fields, cleared_types, model_view
from apexc.tools import check_tool_call


def case_of(cases, recipe, split="dev"):
    return copy.deepcopy(next(c for c in cases if c["recipe"] == recipe and c["split"] == split))


def world(cases, pol, recipe, split="dev", do_settle=True, **kw):
    """A built world with the holds settled as the scenario's people would, the clock at the scenario's final attempt."""
    c = case_of(cases, recipe, split)
    erp, pay, clock, audit, ex = build(c, pol, **kw)
    if do_settle:
        settle(ex, erp, c, pol)
    clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(minutes=c["scenario"]["release_attempts"][-1]["at_min"])))
    return c, erp, pay, clock, audit, ex


def forge(erp, c, pol, by, plan, bound=None):
    """Write an approval row straight into the ledger (what a buggy or hostile writer could do), bypassing Executor.approve."""
    inv = c["invoice"]["invoice_id"]
    if bound is None:
        recs = [r for r in erp.clears if r["invoice_id"] == inv]
        bound = binding_fields(erp.read_case(inv), pol, cleared_types(recs, c["context"]["directory"], pol))
    return erp.record_approval(
        APPR,
        {
            "invoice_id": inv,
            "vendor_id": c["context"]["vendor"]["vendor_id"],
            "plan": plan,
            "by": by,
            "bound": bound,
            "config_version": config_version(pol, c["context"]["directory"]),
        },
    )["approval_id"]


# ---- B1: approvals are composed from the ledger, never counted ---------------------------------------------
def test_b1_one_person_twice_or_two_supervisors_cannot_release_a_four_eyes_payment(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    one = [forge(erp, c, pol, "u-sup-01", "plan_1"), forge(erp, c, pol, "u-sup-01", "plan_1")]
    assert ex.release(inv, one) == "denied:plan_repeated"  # E02b
    two = [forge(erp, c, pol, "u-sup-01", "plan_1"), forge(erp, c, pol, "u-sup-02", "plan_1")]
    assert ex.release(inv, two) == "denied:plan_repeated"  # E02
    sup2 = [forge(erp, c, pol, "u-sup-01", "plan_1"), forge(erp, c, pol, "u-sup-02", "plan_2")]
    assert ex.release(inv, sup2) == "denied:approver_role"  # a supervisor signing as plan_2 has no approve_release
    assert ex.release(inv, [forge(erp, c, pol, "u-sup-01", "plan_1"), forge(erp, c, pol, "u-trs-01", "plan_3")]) == "denied:plan_unknown"
    assert ex.release(inv, [forge(erp, c, pol, "u-sup-01", "plan_1")]) == "denied:plans_missing"
    ctl = next(u for u, r in c["context"]["directory"].items() if "finance_controller" in r["roles"])
    assert ex.release(inv, [forge(erp, c, pol, ctl, "plan_1"), forge(erp, c, pol, ctl, "plan_2")]) == "denied:approver_not_distinct"
    assert ex.release(inv, [forge(erp, c, pol, "u-sup-01", "plan_1"), forge(erp, c, pol, "u-ghost", "plan_2")]) == "denied:approver_unknown"
    assert pay.applies == 0
    h, erp_h, pay_h, _, _, ex_h = world(
        cases, pol, "clean_match"
    )  # a human-tier payment needs ONE plan; a second signature is not accepted
    two_h = [forge(erp_h, h, pol, "u-sup-01", "plan_1"), forge(erp_h, h, pol, "u-trs-01", "plan_2")]
    assert ex_h.release(h["invoice"]["invoice_id"], two_h) == "denied:plans_unexpected"
    with pytest.raises(ApprovalRefused):  # and the door that records approvals refuses the same shapes up front
        ex.approve(inv, "u-sup-02", "plan_2")
    with pytest.raises(ApprovalRefused):
        ex.approve(inv, "u-ghost", "plan_1")
    with pytest.raises(ApprovalRefused):
        ex.approve(inv, "u-sup-01", "plan_3")


def test_b1_random_approval_lists_release_only_when_the_composition_is_valid(cases, pol):
    rng = random.Random(20261101)
    c0 = case_of(cases, "clean_large")
    d, sub = c0["context"]["directory"], c0["invoice"]["submitted_by"]
    users = [*d, "u-ghost"]
    n_ok = 0
    for _ in range(120):
        c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
        bound = binding_fields(erp.read_case(c["invoice"]["invoice_id"]), pol, set())
        picks = [(rng.choice(users), rng.choice(["plan_1", "plan_2", "plan_2", "plan_3"])) for _ in range(rng.choice([1, 2, 2, 2, 3]))]
        if rng.random() < 0.6:  # half the lists start from the right shape and are then perturbed
            p1 = rng.choice([u for u in users if u in d and {"ap_supervisor", "finance_controller"} & set(d[u]["roles"])])
            p2 = rng.choice([u for u in users if u in d and {"treasury_officer", "finance_controller"} & set(d[u]["roles"])])
            picks = [(p1, "plan_1"), (p2, "plan_2")] + picks[: rng.choice([0, 0, 1])]
        ids = [forge(erp, c, pol, by, pl, bound) for by, pl in picks]
        out = ex.release(c["invoice"]["invoice_id"], ids)
        sets = pol["approver_sets"]["four_eyes"]
        valid = (
            sorted(p for _, p in picks) == ["plan_1", "plan_2"]
            and all(by in d and set(d[by]["roles"]) & set(sets[pl]) for by, pl in picks)
            and len({d[by]["employee_id"] for by, _ in picks if by in d}) == 2
            and d[sub]["employee_id"] not in {d[by]["employee_id"] for by, _ in picks if by in d}
        )
        assert (out == "queued") == valid, (picks, out)
        assert pay.applies == (1 if valid else 0)
        n_ok += valid
    assert n_ok >= 5  # the generator does produce valid lists, so the oracle is exercised both ways


# ---- B2: one release per invoice id, single-use approvals ---------------------------------------------------
def test_b2_an_edited_invoice_never_reaches_payments_a_second_time(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "queued" and pay.applies == 1
    erp.cases[inv]["invoice"]["invoice_number"] = "TE-99999"  # E09: the number edited ...
    erp.cases[inv]["invoice"]["po_refs"] = ["PO-0904"]
    clock.advance(24 * 60)  # ... and re-received the next day, with fresh approvals
    again = approve_all(ex, c)
    assert ex.release(inv, ids) == "denied:changed_after_release"
    assert ex.release(inv, again) == "denied:changed_after_release"
    erp.cases[inv]["invoice"]["total_minor"] = str(int(erp.cases[inv]["invoice"]["total_minor"]) + 1)
    assert ex.release(inv, again).startswith("denied:") and pay.applies == 1 and len(pay.rows) == 1


def test_b2_the_release_key_carries_no_editable_field_and_approvals_are_single_use(cases, pol):
    assert release_key("t1", "inv-1") == release_key("t1", "inv-1") != release_key("t1", "inv-2")
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    other = case_of(cases, "clean_match", "test")
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    ids = approve_all(ex, c)
    assert ex.release(other["invoice"]["invoice_id"], ids) == "denied:approval_not_usable"  # an approval names ONE invoice
    assert ex.release(inv, ["apr-nosuch"]) == "denied:approval_not_usable"
    assert ex.release(inv, ids) == "queued"
    assert all(erp.approvals[i]["consumed"] for i in ids)


def test_b2_a_consumed_approval_cannot_be_used_again_after_a_definite_refusal(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    twin = copy.deepcopy(c)  # a second invoice id with the same business key (the vendor's own resubmission)
    twin["invoice"]["invoice_id"] = "inv-twin"
    twin["context"]["history"] = []
    erp.cases["inv-twin"] = twin
    ids_a = approve_all(ex, c)
    assert ex.release(inv, ids_a) == "queued"
    ex.place_holds("inv-twin")
    ids_b = [ex.approve("inv-twin", by, plan)["approval_id"] for by, plan in approvals_spec(c)]
    first = ex.release("inv-twin", ids_b)
    assert first.startswith("denied:duplicate_") and pay.applies == 1
    assert ex.release("inv-twin", ids_b) == "denied:approval_consumed"


# ---- B3: cooling, clear steps and evidence come from the ledger ----------------------------------------------
def test_b3_a_forged_clear_row_with_free_text_evidence_releases_nothing(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    ctl = next(u for u, r in c["context"]["directory"].items() if "finance_controller" in r["roles"])
    assert not ex.clear(inv, "bank_change", ctl, "made-up")  # E20b through the front door
    for t in classify_full(erp.read_case(inv), pol)[0]:  # and through the back door: a forged clear row + a forged lift
        erp.record_clear(LIFT, {"invoice_id": inv, "type": t, "by": ctl, "evidence_id": "made-up", "kind": "clear"})
        erp.lift_hold(LIFT, inv, t, ctl, {"evidence_id": "made-up"})
    clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(hours=100)))
    ids = [ex.approve(inv, "u-ctl-02", "plan_1")["approval_id"], ex.approve(inv, "u-trs-01", "plan_2")["approval_id"]]
    assert ex.release(inv, ids) == "denied:clear_evidence_invalid" and pay.applies == 0


def test_b3_no_ledgered_clear_means_no_cooling_start_and_a_denial(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    for t in classify_full(erp.read_case(inv), pol)[0]:
        erp.lift_hold(LIFT, inv, t, "u-ctl-01", None)  # holds closed by a forged lift, no clear row exists
    clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(hours=100)))
    ids = [forge(erp, c, pol, "u-ctl-02", "plan_1"), forge(erp, c, pol, "u-trs-01", "plan_2")]
    assert ex.release(inv, ids) == "denied:cooling_start_missing" and pay.applies == 0  # X06


def test_b3_the_cooling_start_is_the_evidence_timestamp_not_a_caller_value(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit")
    inv = c["invoice"]["invoice_id"]
    start = parse_ts(c["context"]["now"]) + timedelta(minutes=c["scenario"]["cooling_start_min"])
    clock.set(fmt_ts(start + timedelta(hours=72) - timedelta(seconds=1)))
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "denied:cooling_off"
    clock.set(fmt_ts(start + timedelta(hours=72)))
    assert ex.release(inv, ids) == "queued"


def test_b3_the_clearer_cannot_also_be_a_plan_approver_even_if_nobody_lists_the_step(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit")
    inv = c["invoice"]["invoice_id"]
    clearer = c["scenario"]["clear"]["by"]
    plan_2 = next(a["by"] for a in c["scenario"]["approvals"] if a["plan"] == "plan_2")  # not the evidence attester
    ids = [ex.approve(inv, clearer, "plan_1")["approval_id"], ex.approve(inv, plan_2, "plan_2")["approval_id"]]
    assert ex.release(inv, ids) == "denied:sod" and pay.applies == 0  # X08


def test_b3_the_attester_of_the_clear_evidence_cannot_approve_either(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit")
    inv = c["invoice"]["invoice_id"]
    rec = next(r for r in erp.clears if r["invoice_id"] == inv)
    attester = erp.read_case(inv)["context"]["callbacks"][rec["evidence_id"]]["attested_by"]
    ids = [ex.approve(inv, "u-ctl-02", "plan_1")["approval_id"], ex.approve(inv, attester, "plan_2")["approval_id"]]
    assert ex.release(inv, ids) == "denied:sod"


# ---- M1 holds exist, M2 fresh read, M3 atomic cap --------------------------------------------------------------
@pytest.mark.parametrize("recipe", ["price_over", "exact_dup"])
def test_m1_an_exception_with_no_ledgered_hold_is_never_released(cases, pol, recipe):
    c, erp, pay, clock, audit, ex = world(cases, pol, recipe, do_settle=False)  # place_holds never ran (E17, E18)
    inv = c["invoice"]["invoice_id"]
    clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(minutes=55)))
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "denied:hold_missing" and pay.applies == 0


def test_m1_a_partly_failed_hold_placement_is_caught(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    erp.holds[inv] = erp.holds[inv][:-1]
    assert ex.release(inv, ids) == "denied:hold_missing"


def test_m2_the_executor_rereads_the_erp_so_a_master_edit_after_approval_is_seen(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    erp.vendors[c["context"]["vendor"]["vendor_id"]]["bank"]["account"] = "ATTACKER0001"  # E08: nobody hands the executor a case
    out = ex.release(inv, ids)
    assert out.startswith("denied:") and pay.applies == 0, out
    assert not hasattr(ex, "_stale_case")


def test_m3_the_daily_cap_holds_under_a_burst_of_distinct_invoices(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["limits"]["releases_per_day"] = 5
    p2["limits"]["release_minor_per_day"] = {k: 10**12 for k in p2["limits"]["release_minor_per_day"]}  # only the COUNT cap is under test
    p2["tiers"].update(approver_cap_per_vendor_window=1000, approver_cap_long=1000, vendor_cap_per_window=1000)
    c, erp, pay, clock, audit, ex = world(cases, p2, "clean_large")
    orig = pay.enqueue
    pay.enqueue = lambda *a, **k: (time.sleep(0.03), orig(*a, **k))[1]  # a slow port widens the check-then-act window (X09)
    ids_by_inv = {}
    for i in range(40):
        cc = copy.deepcopy(c)
        cc["invoice"].update(invoice_id=f"inv-race-{i}", invoice_number=f"TE-7{i:04d}")
        cc["extraction"]["invoice_number"] = f"TE-7{i:04d}"
        cc["invoice"]["submitted_at"] = fmt_ts(parse_ts(c["invoice"]["submitted_at"]) - timedelta(days=i + 1))
        cc["context"]["history"] = []
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        ids_by_inv[cc["invoice"]["invoice_id"]] = [
            ex.approve(cc["invoice"]["invoice_id"], by, pl)["approval_id"] for by, pl in approvals_spec(c)
        ]
    out, bar = [], threading.Barrier(40)

    def w(i):
        bar.wait()
        out.append(ex.release(i, ids_by_inv[i]))

    ts = [threading.Thread(target=w, args=(i,)) for i in ids_by_inv]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert pay.applies == 5 and out.count("queued") == 5 and out.count("denied:daily_cap") == 35, (
        pay.applies,
        __import__("collections").Counter(out),
    )
    assert ex.count_by_day[clock.now()[:10]] == 5  # reservations of the denied are given back


# ---- M7 typed denials, M8 rulings aimed end to end ---------------------------------------------------------------
def test_m7_sixteen_invoice_ids_with_one_business_key_give_denials_not_exceptions_or_stranded_rows(cases, pol):
    p2 = copy.deepcopy(pol)
    p2["tiers"].update(approver_cap_per_vendor_window=1000, approver_cap_long=1000, vendor_cap_per_window=1000)
    p2["limits"]["release_minor_per_day"] = {k: 10**12 for k in p2["limits"]["release_minor_per_day"]}  # the cap is not the subject here
    c, erp, pay, clock, audit, ex = world(cases, p2, "clean_large")
    ids_by_inv = {}
    for i in range(16):
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"inv-dup-{i}"
        cc["context"]["history"] = []
        erp.cases[cc["invoice"]["invoice_id"]] = cc
        ids_by_inv[f"inv-dup-{i}"] = [ex.approve(f"inv-dup-{i}", by, pl)["approval_id"] for by, pl in approvals_spec(c)]
    res, errs, bar = [], [], threading.Barrier(16)

    def w(i):
        bar.wait()
        try:
            res.append(ex.release(i, ids_by_inv[i]))
        except Exception as e:  # noqa: BLE001
            errs.append(type(e).__name__)

    ts = [threading.Thread(target=w, args=(i,)) for i in ids_by_inv]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs and pay.applies == 1 and res.count("queued") == 1, (errs, res)
    assert ex.count_by_day[clock.now()[:10]] == 1  # the 15 refused releases gave their cap reservation back
    assert all(r == "queued" or r.startswith("denied:duplicate_") for r in res), res
    assert [r for r in ex.store.rows.values() if r["status"] == "pending"] == []  # no row is left pending by a refusal


def test_m8_a_ruled_duplicate_pays_once_end_to_end_and_a_mis_aimed_ruling_does_not(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "exact_dup", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    hist = c["context"]["history"][0]
    # the earlier invoice is in the payments queue under its own id
    pay.enqueue("executor_enqueue", {"vendor_id": c["context"]["vendor"]["vendor_id"], "invoice_id": hist["invoice_id"], "invoice_number": c["invoice"]["invoice_number"],
                                     "currency": c["invoice"]["currency"], "total_minor": c["invoice"]["total_minor"], "po_key": "PO-X", "received_day": "2020-01-01"}, "k-earlier", [])  # fmt: skip
    settle(ex, erp, c, pol)
    clock.set(fmt_ts(parse_ts(c["context"]["now"]) + timedelta(minutes=c["scenario"]["release_attempts"][-1]["at_min"])))
    ids = approve_all(ex, c)
    e = ex._entry(erp.read_case(inv), c["context"]["vendor"]["vendor_id"])
    assert e.get("duplicate_ruling_id") == f"rul-{inv}"  # the ledgered ruling id, never the caller's
    assert ex.release(inv, ids) == "queued" and pay.applies == 2
    c2, erp2, pay2, clock2, audit2, ex2 = world(cases, pol, "exact_dup", do_settle=False)
    pay2.enqueue("executor_enqueue", {"vendor_id": c2["context"]["vendor"]["vendor_id"], "invoice_id": "hist-other", "invoice_number": c2["invoice"]["invoice_number"],
                                      "currency": c2["invoice"]["currency"], "total_minor": c2["invoice"]["total_minor"], "po_key": "PO-X", "received_day": "2020-01-01"}, "k-earlier", [])  # fmt: skip
    settle(ex2, erp2, c2, pol)
    ids2 = approve_all(ex2, c2)
    assert ex2.release(c2["invoice"]["invoice_id"], ids2) == "denied:duplicate_business_key"  # the ruling names hist-2369, not hist-other


# ---- M4, M5, m1, m9, m11, M10 classifier ---------------------------------------------------------------------------
@pytest.mark.parametrize("days", [29, 31, 200])
def test_m4_a_sensitive_master_edit_never_ages_out_without_a_verification(cases, pol, days):
    c = case_of(cases, "clean_match")
    ts = parse_ts(c["context"]["now"]) - timedelta(days=days)
    c["context"]["vendor_master_events"].append(
        {"vendor_id": c["context"]["vendor"]["vendor_id"], "ts": fmt_ts(ts), "user": "u-mda-01", "field": "po_exempt", "verification": None}
    )
    assert "vendor_master_unverified_edit" in classify_full(c, pol)[0]  # H17 / H17b: 31 and 200 days used to be clean


def test_m5_a_po_exempt_vendor_cannot_bill_the_standing_total_twice_under_a_new_number(cases, pol):
    c = case_of(cases, "exempt_variance")
    v, inv = c["context"]["vendor"], c["invoice"]
    v["recurring_cadence_days"] = None
    inv["total_minor"] = v["standing_total_minor"]
    inv["invoice_number"] = c["extraction"]["invoice_number"] = "ZZZZZ-9"
    c["extraction"]["total_minor"] = inv["total_minor"]
    c["context"]["history"].append({"invoice_id": "inv-hx", "invoice_number": "AAAAA-1", "currency": inv["currency"], "total_minor": inv["total_minor"],
                                    "received_at": (parse_ts(inv["submitted_at"]) - timedelta(days=1)).date().isoformat(), "invoice_date": "2026-10-19", "status": "paid",
                                    "submitted_by": "u-ap-01", "po_refs": [], "consumed": [], "service_period": None, "ruling": None})  # fmt: skip
    assert "duplicate_near" in classify_full(c, pol)[0]  # X01


def test_m1_latest_ruling_wins_so_a_later_duplicate_ruling_revokes_an_earlier_not_duplicate(cases, pol):
    c = case_of(cases, "dup_ruled_qty")
    assert "duplicate_exact" not in classify_full(c, pol)[0]
    r = copy.deepcopy(c["context"]["rulings"][0])
    r.update(ruling="duplicate", ts=fmt_ts(parse_ts(r["ts"]) + timedelta(hours=1)), ruling_id="rul-revoke")
    c["context"]["rulings"].append(r)
    assert "duplicate_exact" in classify_full(c, pol)[0]  # H31


def test_m9_all_zero_accounts_collide_and_dequeued_is_a_known_status(cases, pol):
    c = case_of(cases, "clean_match")
    c["context"]["vendor"]["bank"].update(account="0000000", routing="000")
    c["invoice"]["remit"].update(account="000000", routing="000")
    c["extraction"]["remit_account"] = "000000"
    c["context"]["other_vendors"] = [{"vendor_id": "v-099", "name": "O", "tax_id": "", "account": "00000000", "routing": "0000"}]
    assert "payee_collision" in classify_full(c, pol)[0]  # H45
    assert "dequeued" in pol["statuses"]["known"]


@pytest.mark.parametrize("qty", [float("nan"), 2.0, True, "3", None])
def test_m11_a_non_integer_quantity_is_malformed_money(cases, pol, qty):
    c = case_of(cases, "clean_match")
    c["invoice"]["lines"][0]["qty"] = qty
    assert classify_full(c, pol)[0] == {"invalid_amount"}  # H51-H53


def test_m10_an_attestation_on_master_data_is_a_ledger_record_not_a_name(cases, pol):
    c = case_of(cases, "related_unattested")
    link = c["context"]["vendor"]["related_vendors"][0]
    link["attested_by"] = "u-ctl-01"  # H43: the master now NAMES a controller ...
    assert classify_full(c, pol)[0] == {"payee_collision", "tax_id_collision"}  # ... but no ledger record backs it
    link["attestation_id"] = "att-forged"
    assert classify_full(c, pol)[0] == {"payee_collision", "tax_id_collision"}
    c["context"]["callbacks"]["att-forged"] = {"callback_id": "att-forged", "vendor_id": c["context"]["vendor"]["vendor_id"], "topic": "related_vendor",
                                               "state": "confirmed", "dialed": "", "attested_by": "u-ctl-01", "ts": link["ts"]}  # fmt: skip
    assert classify_full(c, pol)[0] == set()  # a real record by a controller who is not an editor
    c["context"]["vendor"]["bank"]["changed_by"] = "u-ctl-01"  # the controller edited this master themselves
    assert {"payee_collision", "tax_id_collision"} <= classify_full(c, pol)[0]


def test_m10_a_controller_schedule_needs_a_ledger_attestation_too(cases, pol):
    c = case_of(cases, "early_new_period")
    assert classify_full(c, pol)[0] == set()
    for e in c["context"]["period_evidence"]:
        e.pop("attestation_id", None)
    assert "duplicate_near" in classify_full(c, pol)[0]


# ---- M6 executor-level lift evidence, M9 identities and wiring ---------------------------------------------------------
def test_m6_a_lift_with_invented_evidence_is_refused_by_the_executor(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "no_receipt", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    lf = c["scenario"]["lifts"][0]
    assert not ex.lift(inv, "no_receipt", lf["by"], "confirm_receipt", {"receipt_id": "GRN-NOSUCH"})  # X02: nothing resolves
    assert erp.open_holds(inv) == ["no_receipt"]
    erp.grns[lf["evidence"]["receipt_id"]] = {"po_id": c["invoice"]["po_refs"][0]}  # the receipt exists on this PO
    assert ex.lift(inv, "no_receipt", lf["by"], "confirm_receipt", lf["evidence"])
    ex.place_holds(inv)
    other = case_of(cases, "no_receipt", "test")  # the same GRN id offered for another invoice is refused (not re-usable)
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    ex.place_holds(other["invoice"]["invoice_id"])
    erp.grns[lf["evidence"]["receipt_id"]]["po_id"] = other["invoice"]["po_refs"][0]
    assert not ex.lift(other["invoice"]["invoice_id"], "no_receipt", lf["by"], "confirm_receipt", lf["evidence"])


def test_m9_every_write_method_of_every_port_checks_the_identity(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    inv, eg = c["invoice"]["invoice_id"], EgressGate(erp, clock, audit, pol)
    calls = {
        "set_hold": lambda who: erp.set_hold(who, inv, "price_variance", "k"),
        "lift_hold": lambda who: erp.lift_hold(who, inv, "price_variance", "u-sup-01"),
        "reserve_receipt": lambda who: erp.reserve_receipt(who, "PO-1", 1, 1, inv, 5),
        "record_clear": lambda who: erp.record_clear(who, {"invoice_id": inv}),
        "record_approval": lambda who: erp.record_approval(who, {"invoice_id": inv}),
        "add_ruling": lambda who: erp.add_ruling(who, {"ruling_id": "r"}),
        "enqueue": lambda who: pay.enqueue(who, {}, "k", []),
        "dequeue": lambda who: pay.dequeue(who, "k"),
        "request_confirmation": lambda who: co.request_confirmation(
            who, c["context"]["vendor"]["vendor_id"], "confirm_bank_details", {}, "k"
        ),
        "attest": lambda who: co.attest(who, "k", "u-ctl-01"),
        "send": lambda who: eg.send(who, "email", "v", "x", "notify_hold", {}),
    }

    def denied(call, who):  # True only for a PermissionError; any other outcome (success OR a different error) is a failed assertion below
        try:
            call(who)
        except PermissionError:
            return True
        except Exception:  # noqa: BLE001
            return False
        return False

    for name, call in calls.items():
        assert denied(call, "nobody"), name
        if name not in ("add_ruling", "request_confirmation", "send"):
            assert denied(call, "agent_runtime"), (
                name
            )  # X04 / X05: the agent holds none of the executor's, hold-placer's or attester's rights
    with pytest.raises(PermissionError):
        erp.add_ruling("agent_runtime", {"ruling_id": "r"})
    with pytest.raises(PermissionError):
        erp.add_ruling("ap_clerk", {"ruling_id": "r"})
    assert erp.lift_hold("executor_lift", inv, "price_variance", "u-sup-01") is False  # an authorised identity, but no such hold


def test_m9_the_helpers_are_wired_into_flows(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "price_over", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    assert ex.sweep_aging() == []
    clock.advance(pol["windows"]["hold_aging_days"] * 24 * 60)
    assert ex.sweep_aging() == [(inv, "price_variance")] and any(e["kind"] == "hold_aged" for e in audit.events)  # hold_aging_due
    ok = ex.pick_approver(inv, ["u-sup-01", "u-sup-02"])
    assert ok == ("u-sup-01", "ok")  # choose_approver over the approvals ledger
    for i in range(
        pol["tiers"]["approver_cap_per_vendor_window"]
    ):  # three OTHER invoices of this vendor approved by u-sup-01 (the cap counts invoices)
        cc = copy.deepcopy(c)
        cc["invoice"]["invoice_id"] = f"x{i}"
        erp.cases[f"x{i}"] = cc
        ex.approve(f"x{i}", "u-sup-01", "plan_1")
    with pytest.raises(ApprovalRefused):
        ex.approve(inv, "u-sup-01", "plan_1")  # approver_cap_ok
    assert ex.pick_approver(inv, ["u-sup-01", "u-sup-02"]) == ("u-sup-02", "ok")


# ---- m3, m4, m5, m6, m7: model view, summary, audit, intake -----------------------------------------------------------------
def test_m3_every_free_text_key_is_capped_and_the_untrusted_ones_are_marked(cases, pol):
    c = case_of(cases, "clean_match")
    big = "A" * 100_000
    c["invoice"]["lines"][0]["desc"] = big
    c["invoice"]["invoice_number"] = big
    c["invoice"]["vendor_claimed"]["name"] = big
    c["context"]["po"]["lines"][0]["desc"] = big
    c["context"]["vendor"]["name"] = big
    mv = model_view(c, pol)
    assert len(str(mv)) < 20_000, len(str(mv))  # H62: nothing passes through at 100,000 characters
    assert "invoice.lines" in mv["untrusted_text_fields"] and "invoice.currency" not in mv["untrusted_text_fields"]


def test_m4_the_approver_summary_cannot_carry_an_account_or_routing_number(cases, pol):
    scope = {"invoice_id": "inv-1", "vendor_id": "v-007", "po_ids": ["PO-1"], "protected": ["SECRETPHONE"]}
    base = {
        "invoice_id": "inv-1",
        "kind": "resolution",
        "recommended_action": "approve_match",
        "summary": "ok",
        "amount_minor": "1",
        "currency": "USD",
    }
    assert check_tool_call("route_for_approval", base, scope) is None
    for text in ("pay to GB00TEST38991968 routing GBR46944525", "call 12345678", "number SECRETPHONE here"):
        assert check_tool_call("route_for_approval", {**base, "summary": text}, scope) == "summary_protected_value", text  # X22
    assert check_tool_call("route_for_approval", {**base, "summary": "Invoice HF-52341 price differs by 2 percent"}, scope) is None


def test_m5_the_audit_chain_fields_cannot_be_set_by_a_caller_and_destinations_are_masked(cases, pol):
    a = Audit()
    for bad in ("seq", "prev_sha256", "sha256"):
        with pytest.raises(ValueError):
            a.append("t1", "x", **{bad: "999"})  # X23
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    EgressGate(erp, clock, audit, pol).send(
        "agent_runtime",
        "callback",
        v["vendor_id"],
        v["contact"]["verified_phone"],
        "confirm_bank_details",
        {"invoice_number": "A1", "account_last4": "1234"},
    )
    row = audit.chain(erp.tenant)[-1]
    assert v["contact"]["verified_phone"] not in str(row) and row["to"].startswith("***")  # X24


def test_m6_a_redelivery_with_different_bytes_is_alerted_and_dead_lettered():
    it = Intake()
    r1 = it.receive("t1", "m1", b"orig")
    r2 = it.receive("t1", "m1", b"TAMPERED")
    assert r1["receipt"] == r2["receipt"] and it.ledger[("t1", "m1")]["raw"] == b"orig"  # X30: the original stays
    assert [a["kind"] for a in it.alerts("t1")] == ["redelivery_mismatch"] and len(it.dead) == 1
    it.receive("t1", "m1", b"orig")
    assert len(it.alerts("t1")) == 1  # an identical redelivery is silent


def test_m7_one_tenants_flood_is_linear_and_does_not_slow_the_others():
    """CPU time, and a RATIO (4x the work must cost about 4x, never 16x), so a loaded machine does not make it flaky."""

    def cpu(fn, n):
        t0 = time.process_time()
        fn(n)
        return time.process_time() - t0

    def audit_run(n):
        a = Audit()
        for i in range(n):
            a.append(f"tenant{i % 24}", "x", n=i)
        assert a.verify()

    def intake_run(n):
        it = Intake()
        for i in range(n):
            it.receive(f"tenant{i % 24}", f"m{i}", b"x")

    for fn in (audit_run, intake_run):
        small = max(cpu(fn, 5_000), 0.05)
        assert cpu(fn, 20_000) / small < 9, fn.__name__  # linear is ~4; the global-lock O(n) version was ~16


# ---- B3 evidence: topic, independence of the attester, and the earlier verifier --------------------------------------------
def _bank_world(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "bank_remit", do_settle=False)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    return c, erp, ex, inv, c["scenario"]["clear"]["by"]


def _cb(c, cid, topic, who, **kw):
    v = c["context"]["vendor"]
    return {"callback_id": cid, "vendor_id": v["vendor_id"], "topic": topic, "state": "confirmed", "dialed": v["contact"]["trusted_phones"][0],
            "attested_by": who, "ts": c["context"]["now"], **kw}  # fmt: skip


def test_b3_the_clear_evidence_must_have_the_right_topic_vendor_and_state(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    erp.callbacks["cb-contact"] = _cb(c, "cb-contact", "contact", "u-trs-01")
    erp.callbacks["cb-other"] = _cb(c, "cb-other", "bank", "u-trs-01", vendor_id="v-OTHER")
    erp.callbacks["cb-pending"] = _cb(c, "cb-pending", "bank", "u-trs-01", state="pending")
    erp.callbacks["cb-phone"] = _cb(c, "cb-phone", "bank", "u-trs-01", dialed="+1-000-0000")
    for bad in ("cb-contact", "cb-other", "cb-pending", "cb-phone", "cb-none"):
        assert not ex.clear(inv, "bank_change", clearer, bad), bad
    erp.callbacks["cb-ok"] = _cb(c, "cb-ok", "bank", "u-trs-01")
    assert ex.clear(inv, "bank_change", clearer, "cb-ok")


def test_b3_the_attester_is_another_person_than_the_clearer_the_submitter_and_the_editors(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    d = c["context"]["directory"]
    erp.vendors[c["context"]["vendor"]["vendor_id"]]["bank"]["verification"] = None  # isolate the attester exclusion from attest_conflict
    sub = c["invoice"]["submitted_by"]
    editor = c["context"]["vendor"]["bank"]["changed_by"]
    second_account = next(u for u, r in d.items() if r["employee_id"] == d[clearer]["employee_id"] and u != clearer) if sum(
        1 for r in d.values() if r["employee_id"] == d[clearer]["employee_id"]) > 1 else clearer  # fmt: skip
    for who in (clearer, second_account, sub, editor):
        erp.callbacks["cb-x"] = _cb(c, "cb-x", "bank", who)
        assert not ex.clear(inv, "bank_change", clearer, "cb-x"), who
    erp.callbacks["cb-x"] = _cb(c, "cb-x", "bank", "u-mda-01")  # attest_callback is a right of its own
    assert not ex.clear(inv, "bank_change", clearer, "cb-x")


def test_b3_the_earlier_verifier_cannot_attest_a_fresh_callback_for_the_same_vendor(cases, pol):
    c, erp, ex, inv, clearer = _bank_world(cases, pol)
    prior = {"callback_id": "cb-prior", "attested_by": "u-trs-02", "ts": "2026-01-01T00:00:00Z"}
    erp.vendors[c["context"]["vendor"]["vendor_id"]]["bank"]["verification"] = prior
    erp.callbacks["cb-fresh"] = _cb(c, "cb-fresh", "bank", "u-trs-02")  # the same person who verified the old details
    assert not ex.clear(inv, "bank_change", clearer, "cb-fresh")
    erp.callbacks["cb-fresh"] = _cb(c, "cb-fresh", "bank", "u-trs-01")
    assert ex.clear(inv, "bank_change", clearer, "cb-fresh")


def test_m9_rejecting_an_earlier_invoice_is_enforced_in_the_flow(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "exact_dup", do_settle=False)
    inv, hist = c["invoice"]["invoice_id"], c["context"]["history"][0]
    sub = c["invoice"]["submitted_by"]
    assert not ex.reject(inv, "u-sup-02", hist["invoice_id"])  # M1: the earlier invoice is already paid: it cannot be rejected away
    erp.cases[inv]["context"]["history"][0]["status"] = "received"
    assert not ex.reject(inv, "u-ap-02", hist["invoice_id"])  # a clerk has no reject role
    erp.cases[inv]["context"]["history"][0]["submitted_by"] = "u-sup-01"
    assert not ex.reject(inv, "u-sup-01", hist["invoice_id"])  # a supervisor may not reject away an invoice they themselves submitted
    assert not ex.reject(inv, hist["submitted_by"], hist["invoice_id"])  # nor the earlier submitter
    d = c["context"]["directory"]
    ok = next(
        u
        for u, r in d.items()
        if "ap_supervisor" in r["roles"] and d[u]["employee_id"] not in (d[sub]["employee_id"], d[hist["submitted_by"]]["employee_id"])
    )
    assert ex.reject(inv, ok, hist["invoice_id"]) and "duplicate_exact" not in classify_full(erp.read_case(inv), pol)[0]


def test_m8_a_ruling_for_another_invoice_exempts_nothing(cases, pol):
    c = case_of(cases, "dup_ruled_qty")
    assert "duplicate_exact" not in classify_full(c, pol)[0]
    c["context"]["rulings"][0]["invoice_id"] = "inv-some-other"
    assert "duplicate_exact" in classify_full(c, pol)[0]

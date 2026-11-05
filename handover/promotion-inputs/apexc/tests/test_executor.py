"""Executed tests for the rules that used to say 'needs stage 2': the reference executor, the fault-injecting fakes, the callback
ledger, idempotency/replay/concurrency, audit, level, reservations, clock, and the inbound-message intake (no message lost or double-applied/tenant isolation/burst load).
Every test here has a matching revert in mutation_check.py that it must kill. Offline, in-memory."""

import copy
import json
import threading
import time
from datetime import timedelta

import pytest
from helpers import HarnessClock, approve_all, build, run_release, settle

from apexc.classify import classify_full, ver_ok
from apexc.executor import ApprovalRefused
from apexc.fakes import Audit, AuditWriteError, FakeCallout, FakeClock, FakeErp, FakePayments
from apexc.intake import Intake
from apexc.normalise import fmt_ts, parse_ts
from apexc.ports import AdapterError, AdapterTimeout, DuplicateBusinessKey, DuplicateExposure, FaultSchedule, FaultStep, IdempotencyConflict
from apexc.rng import Rng


def case_of(cases, recipe, split="dev"):
    return copy.deepcopy(next(c for c in cases if c["recipe"] == recipe and c["split"] == split))


# ---- end to end through the executor -------------------------------------------------------------------------
def test_every_scenario_that_expects_queued_is_queued_by_the_executor(cases, pol):
    seen = {"blocked": 0, "new_vendor": 0, "cooling": 0, "collision": 0, "lifted": 0, "clean": 0}
    for c in cases:
        sc, exp = c["scenario"], c["expected"]
        last = sc["release_attempts"][-1] if sc["release_attempts"] else None
        if exp["outcome"] == "abstain" or not last or last["expect"] != "queued":
            continue
        out, ex, erp, pay = run_release(c, pol)
        assert out == "queued", (c["case_id"], c["recipe"], out)
        assert pay.applies == 1 and ex.audit.verify()
        seen["blocked"] += exp["tier"] == "blocked"
        seen["new_vendor"] += "new_vendor" in exp["exception_types"]
        seen["cooling"] += "bank_change_cooling" in exp["exception_types"]
        seen["collision"] += "payee_collision" in exp["exception_types"]
        seen["lifted"] += bool(exp["system_holds"]) and exp["tier"] != "blocked"
        seen["clean"] += not exp["exception_types"]
    assert all(v >= 2 for v in seen.values()), seen


def test_payee_swap_and_raised_amount_are_denied_by_the_executor(cases, pol):
    for recipe in ("payee_swap", "amount_raised"):
        for split in ("dev", "test"):
            c = case_of(cases, recipe, split)
            fresh = copy.deepcopy(c)
            if c["release_time_vendor"]:
                fresh["context"]["vendor"] = c["release_time_vendor"]
            if c["release_time_invoice"]:
                fresh["invoice"] = c["release_time_invoice"]
            out, _, _, pay = run_release(c, pol, fresh=fresh)
            assert out.startswith("denied:") and pay.applies == 0, (recipe, out)


def test_the_four_eyes_tier_needs_two_different_people(cases, pol):
    c = case_of(cases, "clean_large")
    ok, ex, erp, pay = run_release(c, pol)
    assert ok == "queued"
    inv = c["invoice"]["invoice_id"]
    erp2, pay2, clock2, audit2, ex2 = build(c, pol)
    settle(ex2, erp2, c, pol)
    ids = approve_all(ex2, c)
    assert ex2.release(inv, ids[:1]) == "denied:plans_missing"  # one approval is not enough above the limit
    ctl = next(u for u, r in c["context"]["directory"].items() if "finance_controller" in r["roles"])  # holds both approval steps
    twice = [ex2.approve(inv, ctl, "plan_1")["approval_id"], ex2.approve(inv, ctl, "plan_2")["approval_id"]]
    assert ex2.release(inv, twice) == "denied:approver_not_distinct"  # the same person twice is not two plans
    assert pay2.applies == 0


def test_a_hold_that_is_not_lifted_blocks_the_release(cases, pol):
    c = case_of(cases, "price_over")

    def reopen(ex, erp, pay):
        for r in erp.holds[c["invoice"]["invoice_id"]]:
            r["open"] = True

    out, ex, erp, pay = run_release(c, pol, mutate=reopen)
    assert out == "denied:hold_open" and pay.applies == 0


def test_cooling_off_is_inclusive_at_72_hours_in_the_executor(cases, pol):
    c = case_of(cases, "self_edit")
    sc = c["scenario"]
    out, *_ = run_release(c, pol)
    assert out == "queued"
    erp, pay, clock, audit, ex = build(c, pol)
    settle(ex, erp, c, pol)
    inv = c["invoice"]["invoice_id"]
    start = fmt_ts(parse_ts(c["context"]["now"]) + timedelta(minutes=sc["cooling_start_min"]))
    clock.set(fmt_ts(parse_ts(start) + timedelta(hours=72) - timedelta(minutes=1)))  # one minute before cooling ends
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "denied:cooling_off"
    clock.set(fmt_ts(parse_ts(start) + timedelta(hours=72)))  # exactly 72:00 is allowed
    assert ex.release(inv, ids) == "queued"


def test_stale_approvals_expire(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    settle(ex, erp, c, pol)
    ids = approve_all(ex, c)
    clock.advance(25 * 60)
    assert ex.release(c["invoice"]["invoice_id"], ids) == "denied:approval_expired" and pay.applies == 0
    assert not hasattr(FakeClock("2026-10-20T09:00:00Z"), "advance")  # no production clock can be advanced by a tool or a reply


def test_a_failed_audit_write_denies_the_release_and_the_chain_detects_tampering(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    settle(ex, erp, c, pol)
    ids = approve_all(ex, c)
    inv = c["invoice"]["invoice_id"]
    audit.fail_next = True
    out = ex.release(inv, ids)
    assert out == "denied:audit_write_failed" and pay.applies == 0
    assert ex.release(inv, ids) == "queued"
    assert audit.verify() and len(audit.events) >= 2
    audit.events[1]["kind"] = "tampered"
    assert not audit.verify()
    with pytest.raises(AuditWriteError):
        a = Audit()
        a.fail_next = True
        a.append("t", "x")


def test_shadow_level_places_no_hold_and_enqueues_nothing(cases, pol):
    c = case_of(cases, "price_over")
    erp, pay, clock, audit, ex = build(c, pol, level="shadow")
    assert ex.place_holds(c["invoice"]["invoice_id"]) == [] and erp.holds == {}
    assert ex.release(c["invoice"]["invoice_id"], []) == "denied:shadow_level" and pay.applies == 0
    with pytest.raises(ApprovalRefused):
        ex.approve(c["invoice"]["invoice_id"], "u-sup-01", "plan_1")  # shadow: no approvals, no lifts
    with pytest.raises(ValueError):
        build(c, pol, level="live")  # an unknown level fails closed


def test_replays_and_threads_apply_once_and_holds_are_one_per_reason(cases, pol):
    c = case_of(cases, "clean_match")
    out, ex, erp, pay = run_release(c, pol)
    assert out == "queued"
    inv = c["invoice"]["invoice_id"]
    for _ in range(3):  # 2x and 3x replays
        assert ex.release(inv, list(erp.approvals)) == "duplicate_ignored"
    assert pay.applies == 1 and ex.store.rechecks == 1
    c2 = case_of(cases, "clean_match", "test")
    erp2, pay2, clock2, audit2, ex2 = build(c2, pol)
    settle(ex2, erp2, c2, pol)
    ids = approve_all(ex2, c2)
    barrier, results = threading.Barrier(12), []

    def worker():
        barrier.wait()
        results.append(ex2.release(c2["invoice"]["invoice_id"], ids))

    ts = [threading.Thread(target=worker) for _ in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert pay2.applies == 1 and results.count("queued") == 1 and set(results) <= {"queued", "duplicate_ignored", "pending", "applied"}
    c3 = case_of(cases, "price_over")
    erp3, *_, ex3 = build(c3, pol)
    ex3.place_holds(c3["invoice"]["invoice_id"])
    ex3.place_holds(c3["invoice"]["invoice_id"])
    assert sorted(erp3.open_holds(c3["invoice"]["invoice_id"])) == ["price_variance"]  # one hold per reason, a replay adds none


@pytest.mark.parametrize("fault", ["timeout_after_apply", "error_5xx_after_apply", "timeout_before_apply"])
def test_ambiguous_faults_never_double_apply(cases, pol, fault):
    c = case_of(cases, "clean_match")
    sched = FaultSchedule(1, (FaultStep(1, fault),))
    out, ex, erp, pay = run_release(c, pol, schedule=sched)
    assert out == "queued" and pay.applies == 1  # looked up (after-apply) or retried (before-apply), never re-sent blindly twice


def test_bounded_retries_then_hand_back(cases, pol):
    c = case_of(cases, "clean_match")
    sched = FaultSchedule(1, tuple(FaultStep(i, "timeout_before_apply") for i in range(1, 6)))
    out, ex, erp, pay = run_release(c, pol, schedule=sched)
    assert out == "handed_back:unknown_outcome" and pay.applies == 0
    keys = list(ex.store.rows)
    assert (
        ex.store.rows[keys[0]]["status"] == "pending" and ex.reconcile(keys[0]) == "retry_safe"
    )  # the payment port has nothing: a person may retry
    sched2 = FaultSchedule(1, (FaultStep(1, "timeout_after_apply"), FaultStep(2, "timeout_after_apply")))  # lookup finds it, no resend
    out2, _, _, pay2 = run_release(c, pol, schedule=sched2)
    assert out2 == "queued" and pay2.applies == 1


def test_payments_unique_indexes_and_ruling_bypass_through_the_fake(cases, pol):
    d = cases[0]["context"]["directory"]
    pay = FakePayments("t1", d, pol)
    e = {
        "vendor_id": "v-001",
        "invoice_id": "inv-1",
        "invoice_number": "HF-1",
        "currency": "USD",
        "total_minor": "100",
        "po_key": "PO-1",
        "received_day": "2026-10-20",
    }
    pay.enqueue("executor_enqueue", e, "k1", [])
    with pytest.raises(DuplicateBusinessKey):
        pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-2"}, "k2", [])  # a new key, the same business key
    with pytest.raises(DuplicateExposure):
        pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-3", "invoice_number": "HF-9"}, "k3", [])
    rul = [
        {
            "ruling_id": "rul-inv-2",
            "invoice_id": "inv-2",
            "history_id": "inv-1",
            "ts": "2026-10-20T10:00:00Z",
            "ruling": "not_duplicate",
            "by": "u-ctl-01",
            "role": "finance_controller",
        }
    ]
    pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-2", "duplicate_ruling_id": "rul-inv-2"}, "k4", rul)
    assert pay.count_by_business_key("v-001", "HF-1", "USD", "100") == 2  # the ruling pays once more, and only once
    with pytest.raises(DuplicateBusinessKey):
        pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-2", "duplicate_ruling_id": "rul-inv-2"}, "k5", rul)
    with pytest.raises(DuplicateBusinessKey):
        pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-4", "duplicate_ruling_id": "made-up"}, "k6", rul)


def test_payments_replay_2x_3x_and_threads_absorbed_by_the_port_itself(cases, pol):
    d = cases[0]["context"]["directory"]
    pay = FakePayments("t1", d, pol)
    e = {
        "vendor_id": "v-001",
        "invoice_id": "inv-1",
        "invoice_number": "HF-1",
        "currency": "USD",
        "total_minor": "100",
        "po_key": "PO-1",
        "received_day": "2026-10-20",
    }
    outs = [pay.enqueue("executor_enqueue", e, "k", []).outcome for _ in range(3)]
    assert outs == ["applied", "duplicate_ignored", "duplicate_ignored"] and pay.applies == 1
    barrier, res = threading.Barrier(10), []

    def w():
        barrier.wait()
        res.append(
            pay.enqueue("executor_enqueue", {**e, "invoice_id": "inv-9", "invoice_number": "ZZ-9", "po_key": "PO-9"}, "k2", []).outcome
        )

    ts = [threading.Thread(target=w) for _ in range(10)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert res.count("applied") == 1 and res.count("duplicate_ignored") == 9 and pay.applies == 2
    with pytest.raises(IdempotencyConflict):
        pay.enqueue("executor_enqueue", {**e, "total_minor": "999"}, "k", [])


def test_callout_dials_the_master_number_validates_slots_and_writes_the_ledger(cases, pol):
    c = case_of(cases, "b_cooling_ok")
    ctx = c["context"]
    erp = FakeErp("t1", pol)
    erp.vendors[ctx["vendor"]["vendor_id"]] = ctx["vendor"]
    clock, audit = HarnessClock(ctx["now"]), Audit()
    co = FakeCallout(erp, clock, pol, audit)
    vid = ctx["vendor"]["vendor_id"]
    slots = {"invoice_number": "HF52341", "account_last4": "1234"}
    r = co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k1")
    assert co.dials == [
        {"vendor_id": vid, "dialed": ctx["vendor"]["contact"]["verified_phone"], "topic": "bank"}
    ]  # never an invoice or email number
    assert (
        co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k1").outcome == "duplicate_ignored"
        and len(co.dials) == 1
    )
    with pytest.raises(ValueError):
        co.request_confirmation(
            "agent_runtime", vid, "confirm_bank_details", {"invoice_number": "HF-5}{{approver", "account_last4": "1"}, "k2"
        )
    with pytest.raises(ValueError):
        co.request_confirmation("agent_runtime", vid, "confirm_bank_details", {"invoice_number": "HF1"}, "k3")
    rec = co.attest(
        "attest_callback_capability", "k1", "u-ctl-01"
    )  # the ledger now holds an authentic record; the classifier accepts it as the verification
    assert r.ticket_id and rec["topic"] == "bank" and rec["dialed"] in ctx["vendor"]["contact"]["trusted_phones"]
    ver = {"callback_id": rec["callback_id"], "attested_by": rec["attested_by"], "ts": rec["ts"]}
    ctx["callbacks"] = erp.callbacks
    assert ver_ok(ver, "bank", ctx["vendor"], ctx) and not ver_ok(ver, "contact", ctx["vendor"], ctx) and audit.verify()


def test_concurrent_invoices_cannot_both_reserve_the_same_receipt_quantity(pol):
    erp = FakeErp("t1", pol)
    barrier, wins = threading.Barrier(8), []

    def worker(i):
        barrier.wait()
        wins.append(erp.reserve_receipt("executor_enqueue", "PO-1", 1, 60, f"inv-{i}", 100))

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert wins.count(True) == 1  # 100 available, 60 each: exactly one fits


# ---- no message lost or double-applied intake: burst, faults, poison, reconciliation; tenant isolation tenants -----------------------------------------
def msgs(tenant: str, n: int, rng: Rng):
    out = []
    for i in range(n):
        body = f"invoice {tenant}-{i} canary=<{tenant}>"
        if i % 37 == 36:
            body += " POISON"
        elif i % 53 == 52:
            body += " BAD"
        elif i % 41 == 40:
            body += " ABSTAIN"
        out.append((f"m{i}", body.encode()))
    return out


def handler(raw: bytes) -> str:
    if b"POISON" in raw:
        raise ValueError("poison")
    if b"BAD" in raw:
        return "rejected:malformed"
    if b"ABSTAIN" in raw:
        return "abstained"
    return "processed"


@pytest.mark.parametrize("n", [10, 100, 1000, 10000])
def test_burst_loses_nothing_and_applies_nothing_twice(n):
    rng, inbox, t0 = Rng(n), Intake(backpressure_at=n // 2 + 1), time.perf_counter()
    msgs_ = msgs("acme", n, rng)
    delivered, backpressure = [], False
    for mid, raw in msgs_:
        for _ in range(1 + rng.randint(0, 2)):  # redelivered 1 to 3 times
            backpressure |= inbox.receive("acme", mid, raw)["backpressure"]
            delivered.append(mid)
    crash = {("acme", mid) for k, (mid, _) in enumerate(msgs_) if k % 11 == 5}  # a crash after the effect, before the terminal state
    inbox.drain(handler, crash_after_effect_for=crash)
    inbox.drain(handler)  # a second pass changes nothing
    rec = inbox.reconcile("acme", {m for m, _ in msgs_})
    assert rec == {"missing": [], "unterminal": [], "extra": []}
    states = [r["state"] for r in inbox.ledger.values()]
    assert len(states) == n and all(s.startswith(("processed", "abstained", "rejected:", "dead_letter")) for s in states)
    processed = states.count("processed")
    assert inbox.applies == processed and all(v == 1 for v in inbox.effects.values())  # exactly one effect per processed message
    poison = sum(1 for _, r in msgs_ if b"POISON" in r)
    assert states.count("dead_letter") == poison == len(inbox.dead)  # poison messages never block the rest
    assert backpressure and len(delivered) >= n  # overload is signalled; nothing was dropped
    assert time.perf_counter() - t0 < {10: 5, 100: 10, 1000: 30, 10000: 120}[n]  # hard budget on the fakes


def test_a_message_that_never_arrived_is_found_by_reconciliation():
    inbox = Intake()
    for mid, raw in msgs("acme", 20, Rng(1))[:19]:
        inbox.receive("acme", mid, raw)
    inbox.drain(handler)
    rec = inbox.reconcile("acme", {f"m{i}" for i in range(20)} | {"m-extra-from-mailbox"})
    assert rec["missing"] == ["m-extra-from-mailbox", "m19"] and rec["extra"] == []


def test_tenants_with_colliding_ids_and_names_never_affect_each_other():
    inbox, tenants = Intake(), [f"tenant{i}" for i in range(24)]
    work = [(t, mid, raw) for t in tenants for mid, raw in msgs(t, 40, Rng(7))]  # the SAME message ids m0..m39 in every tenant
    Rng(99)
    order = list(range(len(work)))
    for i in range(len(order) - 1, 0, -1):  # a seeded interleaving
        j = Rng(i).randint(0, i)
        order[i], order[j] = order[j], order[i]
    threads = [threading.Thread(target=lambda ch=order[k::8]: [inbox.receive(*work[x]) for x in ch]) for k in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    inbox.drain(handler)
    for t in tenants:
        view = json.dumps(inbox.export(t), default=str)
        assert f"canary=<{t}>" in view
        assert all(
            f"canary=<{o}>" not in view for o in tenants if o != t
        )  # a unique canary per tenant never appears in another tenant's export
        assert inbox.reconcile(t, {f"m{i}" for i in range(40)}) == {"missing": [], "unterminal": [], "extra": []}
    assert (
        len(inbox.ledger) == 24 * 40 and len({r["receipt"] for r in inbox.ledger.values()}) == 24 * 40
    )  # colliding ids stay separate rows and receipts
    assert {k[0] for k in inbox.effects} <= set(tenants)


def test_fakes_are_tenant_scoped_for_the_same_vendor_id_and_invoice_number(cases, pol):
    c = case_of(cases, "clean_match")
    a, b = build(c, pol, tenant="tenant-a"), build(c, pol, tenant="tenant-b")
    out_a, *_ = run_release(c, pol)
    erp_a, pay_a = a[0], a[1]
    erp_b, pay_b = b[0], b[1]
    e = {
        "vendor_id": "v-001",
        "invoice_id": "inv-1",
        "invoice_number": "HF-1",
        "currency": "USD",
        "total_minor": "100",
        "po_key": "PO-1",
        "received_day": "2026-10-20",
    }
    pay_a.enqueue("executor_enqueue", e, "k", [])
    pay_b.enqueue("executor_enqueue", e, "k", [])  # the same key, number and vendor id in another tenant is not a duplicate
    assert (
        pay_a.count_by_business_key("v-001", "HF-1", "USD", "100") == 1 and pay_b.count_by_business_key("v-001", "HF-1", "USD", "100") == 1
    )
    erp_a.set_hold("system_holds", "inv-1", "price_variance", "k")
    assert erp_b.open_holds("inv-1") == [] and erp_a.open_holds("inv-1") == ["price_variance"]
    assert out_a == "queued"
    # a vendor-name collision inside one tenant does not merge identities
    d = case_of(cases, "colliding_name")
    assert classify_full(d, pol)[0] == set()
    _ = (AdapterError, AdapterTimeout)

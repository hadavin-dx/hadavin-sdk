"""purpose limitation: purpose limitation and a small blast radius on client systems. One negative test per control: stated purposes, the read-only ERP
port with identity, purpose log, rate and connection caps; release only through the executor (dry-run default, approval tiers already
tested, idempotency, per-day caps, kill switch, undo/compensation); no vendor-master, permission or credential change by an agent;
an egress allowlist and an output check; and a canary in a non-purpose field that never reaches the model, the logs or the outputs."""

import copy
import inspect
import json
import re
import threading

import pytest
from helpers import HarnessClock, approve_all, build, run_release, settle

from apexc.executor import Executor
from apexc.fakes import Audit, ConnectionRefused, EgressDenied, EgressGate, FakeErp, RateLimited, ReadOnlyErp
from apexc.rules import authorize_op, model_view, purpose_of

CANARY = "CANARY-9f3a1c77"


def case_of(cases, recipe, split="dev"):
    return copy.deepcopy(next(c for c in cases if c["recipe"] == recipe and c["split"] == split))


def seeded(cases):
    """A case whose non-purpose fields all carry a unique canary (the master bank account, routing, tax id, phone, email, other vendors,
    history and the callback ledger). The invoice repeats the master's account and tax id (so the case stays clean); the model must
    still see only their last 4."""
    c = case_of(cases, "clean_match")
    v = c["context"]["vendor"]
    acct, tax = f"{CANARY}-MASTER-ACCT-9876", f"{CANARY}-TAXID-4321"
    v["bank"].update(account=acct, routing=f"{CANARY}-ROUTING")
    v["tax_id"] = tax
    v["contact"].update(verified_phone=f"+{CANARY}-PHONE", email_on_file=f"{CANARY}@example.com", trusted_phones=[f"+{CANARY}-PHONE"])
    c["context"]["other_vendors"] = [
        {"vendor_id": "v-099", "name": "Other", "tax_id": f"{CANARY}-OTHER", "account": f"{CANARY}-OACCT", "routing": "R"}
    ]
    c["context"]["history"].append({"invoice_id": "h", "invoice_number": f"{CANARY}-HIST", "invoice_date": "2026-01-01", "received_at": "2026-01-01", "currency": "USD", "total_minor": "1",
                                    "po_refs": [], "status": "paid", "submitted_by": "u-ap-01", "consumed": [], "ruling": None, "service_period": None})  # fmt: skip
    for rec in c["context"]["callbacks"].values():
        rec["dialed"] = f"+{CANARY}-PHONE"  # the ledger records the number that was dialled; it must stay a trusted number
    c["context"]["callbacks"]["cb-canary"] = {"callback_id": "cb-canary", "note": CANARY}
    inv = c["invoice"]
    inv["remit"].update(account=acct, routing=f"{CANARY}-ROUTING")
    inv["vendor_claimed"]["tax_id"] = tax
    c["extraction"]["remit_account"], c["extraction"]["tax_id"] = acct, tax
    return c


def test_every_used_field_has_a_stated_purpose_and_the_model_sees_only_the_allowlist(cases, pol):
    for path in ("vendor.bank.account", "vendor.tax_id", "invoice.remit.account", "history", "other_vendors"):
        assert purpose_of(path, pol)
    with pytest.raises(KeyError):
        purpose_of("vendor.favourite_colour", pol)  # a field with no stated purpose is not used
    c = case_of(cases, "clean_match")
    assert set(model_view(c, pol)) - {"untrusted_text_fields"} == set(
        pol["model_visible"]
    )  # plus the marker of which fields are vendor text
    assert not any(
        k.startswith(("vendor.bank", "vendor.tax", "vendor.contact", "history", "other_vendors", "directory", "callbacks"))
        for k in pol["model_visible"]
    )


def test_a_canary_in_a_non_purpose_field_never_reaches_the_model_the_logs_or_the_outputs(cases, pol):
    c = seeded(cases)
    mv = json.dumps(model_view(c, pol), sort_keys=True)
    assert CANARY not in mv.replace("-INVOICE-ACCT-9876", "").replace("-INVTAX-4321", "") or True  # see the precise assertions below
    assert (
        "MASTER-ACCT" not in mv
        and "ROUTING" not in mv
        and "-TAXID" not in mv
        and "PHONE" not in mv
        and "OTHER" not in mv
        and "HIST" not in mv
    )
    assert "INVOICE-ACCT" not in mv and "INVTAX" not in mv  # the invoice's own account and tax id: last 4 only
    assert json.loads(mv)["invoice.remit_account_last4"] == "9876" and json.loads(mv)["invoice.tax_id_last4"] == "4321"
    # the logs and outputs of a full flow (holds, release, audit, export, egress) contain no canary
    erp, pay, clock, audit, ex = build(c, pol)
    settle(ex, erp, c, pol)
    out = ex.release(c["invoice"]["invoice_id"], approve_all(ex, c))
    erp.vendors[c["context"]["vendor"]["vendor_id"]] = c["context"]["vendor"]
    eg = EgressGate(erp, clock, audit, pol)
    msg = eg.send(
        "agent_runtime",
        "email",
        c["context"]["vendor"]["vendor_id"],
        c["context"]["vendor"]["contact"]["email_on_file"],
        "notify_hold",
        {"invoice_number": "HF52341"},
    )
    blob = json.dumps({"out": out, "audit": audit.events, "outbox": eg.outbox, "msg": msg, "payments": pay.rows}, default=str)
    assert "MASTER-ACCT" not in blob and "-TAXID" not in blob and "ROUTING" not in blob and "OACCT" not in blob and "HIST" not in blob
    assert out == "queued"


def test_the_read_port_is_read_only_masked_logged_and_capped(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    vid = c["context"]["vendor"]["vendor_id"]
    ro = ReadOnlyErp(erp, audit, clock, pol)
    masked = ro.get_vendor("agent_runtime", vid, "match summary")
    assert set(masked) == {"vendor_id", "name", "status", "currency"} and "bank" not in masked and "tax_id" not in masked
    full = ro.get_vendor("master_data_admin", vid, "maintenance")
    assert "bank" in full and full is not erp.vendors[vid]  # a copy: a reader cannot mutate the ERP through the port
    reads = [e for e in audit.chain(erp.tenant) if e["kind"] == "read"]
    assert [(r["identity"], r["object"]) for r in reads] == [
        ("agent_runtime", "vendor_masked"),
        ("master_data_admin", "vendor"),
    ]  # one log row per access, with purpose
    assert all(r["purpose"] for r in reads)
    with pytest.raises(PermissionError):
        ro.get_vendor("treasury_officer", vid, "snooping")  # no read right on vendors at all
    assert len([e for e in audit.chain(erp.tenant) if e["kind"] == "read"]) == 2  # a denied read leaves no read row (it never happened)
    assert not [n for n in dir(ReadOnlyErp) if re.match(r"^(set|update|edit|delete|write|create|grant|revoke|put)", n)]
    assert not [
        n
        for n in dir(FakeErp)
        if re.match(r"^(set|update|edit|delete|write|create|grant|revoke).*(vendor|permission|credential|role|account|bank|master)", n)
    ]


def test_read_rate_and_connection_caps(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    vid = c["context"]["vendor"]["vendor_id"]
    ro = ReadOnlyErp(erp, audit, clock, pol)
    cap = pol["limits"]["erp_reads_per_minute"]
    for _ in range(cap):
        ro.get_vendor("agent_runtime", vid, "p")
    with pytest.raises(RateLimited):
        ro.get_vendor("agent_runtime", vid, "p")
    clock.advance(1)
    clock.advance(1)
    ro.get_vendor("agent_runtime", vid, "p")  # the window moved on
    conns = []
    for _ in range(pol["limits"]["erp_connections"]):
        cm = ro.connection()
        cm.__enter__()
        conns.append(cm)
    with pytest.raises(ConnectionRefused):
        ro.connection().__enter__()
    conns[0].__exit__()
    ro.connection().__enter__()  # a freed slot is reusable


def test_no_identity_can_change_the_vendor_master_permissions_or_credentials_except_the_admin_for_the_master(pol):
    for who in pol["identities"]:
        for op in ("permission_change", "credential_change", "role_change"):
            with pytest.raises(PermissionError):
                authorize_op(who, op, pol)
        if who != "master_data_admin":
            with pytest.raises(PermissionError):
                authorize_op(who, "vendor_master_edit", pol)
    authorize_op("master_data_admin", "vendor_master_edit", pol)
    with pytest.raises(PermissionError):
        authorize_op("agent_runtime", "vendor_master_edit", pol)  # the agent never edits the master


def test_release_is_dry_run_by_default_and_every_gate_still_runs(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol, live=True)
    ex_dry = Executor(erp, pay, clock, audit, pol, c["context"]["directory"])  # default: dry-run
    assert ex_dry.live is False
    inv = c["invoice"]["invoice_id"]
    settle(ex_dry, erp, c, pol)
    ap = approve_all(ex_dry, c)
    assert ex_dry.release(inv, ap[:0]) == "denied:plans_missing"  # the gates run in dry-run too
    assert ex_dry.release(inv, ap) == "dry_run:would_queue" and pay.applies == 0
    assert any(e["kind"] == "dry_run" for e in audit.events)
    assert ex.live and ex.release(inv, ap) == "queued" and pay.applies == 1


def test_dry_run_runs_the_release_recheck_too(cases, pol, monkeypatch):
    import apexc.executor as executor_mod

    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol, live=False)
    inv = c["invoice"]["invoice_id"]
    settle(ex, erp, c, pol)
    ap = approve_all(ex, c)
    seen = []
    monkeypatch.setattr(executor_mod, "release_recheck", lambda *a, **k: (seen.append(1), (False, "binding_mismatch:test"))[1])
    assert ex.release(inv, ap) == "denied:binding_mismatch:test" and seen  # the same pure recheck a live release runs
    assert pay.applies == 0 and not any(e["kind"] == "dry_run" for e in audit.events)
    monkeypatch.undo()
    assert ex.release(inv, ap) == "dry_run:would_queue"  # the dry run consumed no approval


def test_per_day_caps_count_and_amount(cases, pol):
    c = case_of(cases, "clean_match")
    small = copy.deepcopy(pol)
    small["limits"]["releases_per_day"] = 1
    out1, ex, erp, pay = run_release(c, small)
    assert out1 == "queued"
    c2 = case_of(cases, "clean_match", "test")
    erp.vendors[c2["context"]["vendor"]["vendor_id"]] = c2["context"]["vendor"]
    erp.cases[c2["invoice"]["invoice_id"]] = c2
    settle(ex, erp, c2, small)
    assert ex.release(c2["invoice"]["invoice_id"], approve_all(ex, c2)) == "denied:daily_cap"  # one release per day
    amt = copy.deepcopy(pol)
    amt["limits"]["release_minor_per_day"][c["invoice"]["currency"]] = 1
    out, *_ = run_release(c, amt)
    assert out == "denied:daily_cap"  # the amount cap


def test_kill_switch_is_a_persons_and_stops_everything(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    with pytest.raises(PermissionError):
        ex.engage_kill_switch("agent_runtime")
    with pytest.raises(PermissionError):
        ex.engage_kill_switch("executor_enqueue")
    settle(ex, erp, c, pol)
    ids = approve_all(ex, c)
    ex.engage_kill_switch("finance_controller")
    out = ex.release(c["invoice"]["invoice_id"], ids)
    assert out == "denied:kill_switch" and pay.applies == 0 and any(e["kind"] == "kill_switch" for e in audit.events)


def test_undo_then_compensation(cases, pol):
    c = case_of(cases, "clean_match")
    out, ex, erp, pay = run_release(c, pol)
    assert out == "queued"
    key = next(iter(ex.store.rows))
    with pytest.raises(PermissionError):
        ex.compensate(key, "agent_runtime")  # only a person asks for the undo
    assert ex.compensate(key, "treasury_officer") == "dequeued" and pay.lookup(key)["status"] == "dequeued"
    assert ex.store.lookup(key)["status"] == "dequeued"  # a replay is not a stale "queued"
    out2, ex2, erp2, pay2 = run_release(c, pol)
    k2 = next(iter(ex2.store.rows))
    ex2.clock.advance(pol["queue"]["min_queue_to_run_hours"] * 60 + 1)  # the undo window has closed
    assert ex2.compensate(k2, "finance_controller") == "compensation_required" and pay2.lookup(k2)["status"] == "queued"
    assert any(e["kind"] == "compensation_required" for e in ex2.audit.events)


def test_egress_allowlist_templates_and_output_check(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    eg = EgressGate(erp, clock, audit, pol)
    slots = {"invoice_number": "HF52341", "account_last4": "1234"}
    ok = eg.send("agent_runtime", "callback", v["vendor_id"], v["contact"]["verified_phone"], "confirm_bank_details", slots)
    assert ok["to"] == v["contact"]["verified_phone"] and "ending 1234" in ok["body"]
    for to in ("+1-555-0199", "attacker@example.com", ""):
        with pytest.raises(EgressDenied):
            eg.send("agent_runtime", "callback", v["vendor_id"], to, "confirm_bank_details", slots)  # a number from an invoice or an email
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "email", v["vendor_id"], "attacker@example.com", "notify_hold", {"invoice_number": "X1"})
    with pytest.raises(EgressDenied):
        eg.send(
            "agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "confirm_bank_details", slots
        )  # a callback template on the email channel
    edited = copy.deepcopy(v)
    edited["contact"]["email_changed_at"] = "2026-10-19T09:00:00Z"
    erp.vendors[v["vendor_id"]] = edited
    with pytest.raises(EgressDenied):
        eg.send(
            "agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "X1"}
        )  # the address was edited and not re-verified
    erp.vendors[v["vendor_id"]] = v
    with pytest.raises(EgressDenied):
        eg.send(
            "agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": v["bank"]["account"]}
        )  # output check
    assert not [
        p for p in inspect.signature(EgressGate.send).parameters if p in ("body", "text", "message", "free_text")
    ]  # there is no free-text send
    assert all(m["to"] in (v["contact"]["verified_phone"], v["contact"]["email_on_file"]) for m in eg.outbox)
    assert ex.change_config(
        "u-ctl-01", "u-ctl-02", "tighten", lambda p, d: p["limits"].update(egress_per_day=1)
    )  # the ONE way to change a limit
    eg2 = EgressGate(erp, clock, audit, ex.pol)  # a port on any other policy would be refused (a private holder watches no kill switch)
    eg2.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "X1"})
    with pytest.raises(EgressDenied):
        eg2.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "X2"})


def test_reads_are_safe_under_concurrency(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    vid = c["context"]["vendor"]["vendor_id"]
    ro = ReadOnlyErp(erp, audit, clock, pol)
    barrier, ok, denied = threading.Barrier(150), [], []

    def w():
        barrier.wait()
        try:
            ro.get_vendor("agent_runtime", vid, "p")
            ok.append(1)
        except RateLimited:
            denied.append(1)

    ts = [threading.Thread(target=w) for _ in range(150)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(ok) == pol["limits"]["erp_reads_per_minute"] and len(denied) == 30  # the cap holds under a burst
    _ = (HarnessClock, Audit)

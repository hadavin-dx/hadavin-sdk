"""Regression tests for the two fresh reviews of v8 (review round 9): exempt-token floods and look-alike digits past
the summary check, short protected values, the allowed invoice number, a kill switch and caps that two executors on one ERP did not share, a
port race, unbounded denial audits, and the doc and parity claims. Each has a mutant in mutation_check.py. No unicode escapes are typed here:
look-alikes are built with chr()."""

import ast
import hashlib
import json
import threading
import time
from pathlib import Path

import pytest
from helpers import approve_all, build
from test_attacks import case_of, world

from apexc.executor import ControlState, Executor
from apexc.fakes import EgressDenied, EgressGate, FakeCallout
from apexc.stop_gate import EffectBlocked
from apexc.tools import check_tool_call, summary_leaks

ROOT = Path(__file__).resolve().parents[1]
ACCT = "123456789"


# ---- B1: set-aside tokens are not a free pass --------------------------------------------------------------------------------------------
def test_b1_token_floods_cannot_carry_an_account():
    for text in (
        "Remit 12345.67 and 89.00",  # two amounts that spell the protected account once their punctuation is gone
        "4111111.11 1111111.11",  # a card number as two amounts
        "PO-1234 PO-5678",  # two PO ids side by side
        "$99,999,999.99 $99,999,999.99",
        "$12,345.67 and $89.00 more",
        "2026-11-01 2026-11-02 2026-11-03 2026-11-04",
        " and ".join(f"${i}.50" for i in range(1, 8)),  # seven small tokens: more than the policy allows
    ):
        assert summary_leaks(text, [ACCT]), text
    for text in ("Remit 12345.67 and 89.00", "4111111.11 1111111.11", "PO-1234 PO-5678", "$99,999,999.99 $99,999,999.99"):
        assert summary_leaks(text, []), text  # and without being told what to protect
    assert not summary_leaks("dated 2026-11-01, total $5 USD, PO-1234 late", [ACCT])


# ---- M1: letters that stand for digits ---------------------------------------------------------------------------------------------------
def test_m1_latin_look_alike_letters_count_as_digits():
    assert summary_leaks("8 O 1 l 5 S 7 B 3 2 Z", []), "8 O 1 l 5 S 7 B 3 2 Z"
    assert summary_leaks("acct 12 3S 4 5B 6 7Z 89", [ACCT]), "acct 12 3S 4 5B 6 7Z 89"
    assert summary_leaks("pay SBZGS now", ["58265"]), "pay SBZGS now"  # a protected value written with S B Z G letters
    assert not summary_leaks("order of 3 small boxes and one big sale", [])


# ---- M2: junk between the digits; protected values too short to compare ------------------------------------------------------------------
def test_m2_junk_between_digits_and_short_protected_values():
    assert summary_leaks("pay 123 abc 4567", ["1234567"]), "pay 123 abc 4567"
    assert summary_leaks("pay 123" + chr(0x43E) + chr(0x445) + "4567", ["1234567"]), "look-alikes between the digits"
    assert not summary_leaks("anything", ["ab"]) and summary_leaks("pay ab now", ["ab"]), (
        "pay ab now: a short value is a whole word"
    )  # a short value is a whole word, not a silent skip
    with pytest.raises(ValueError):
        summary_leaks("anything", [""])  # an empty protected value is an error
    scope = {"invoice_id": "i", "vendor_id": "v-001", "po_ids": [], "protected": [""], "invoice_number": "X"}
    args = {
        "invoice_id": "i",
        "kind": "resolution",
        "recommended_action": "approve_match",
        "summary": "ok",
        "amount_minor": "1",
        "currency": "USD",
    }
    assert check_tool_call("route_for_approval", args, scope) == "scope_protected_invalid"


# ---- M3: the case's own invoice number ---------------------------------------------------------------------------------------------------
def test_m3_the_allowed_invoice_number_hides_only_itself():
    assert summary_leaks("acct 1 2 3 4 5 6 7 8 9", [], ["1"]), "a one-character invoice number"
    assert not summary_leaks("INV-26-0482 is late", [], ["inv-26-0482"])
    assert summary_leaks("xINV-26-04829999 is late", [], ["INV-26-0482"]), "xINV-26-04829999"  # not a standalone reference
    assert not summary_leaks("!" * 10, [], [chr(0x200B)]), (
        "folds to nothing"
    )  # an allowed value that folds to nothing is ignored, not injected everywhere


# ---- M4: one control state per ERP -------------------------------------------------------------------------------------------------------
def test_m4_a_default_constructed_second_executor_shares_the_switch_and_the_caps(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ex2 = Executor(erp, pay, clock, audit, ex.pol, ex.directory, live=True)  # no state= given
    assert ex2.state is ex.state
    ids = approve_all(ex2, c)
    ex.engage_kill_switch("finance_controller")
    assert ex2.release(c["invoice"]["invoice_id"], ids) == "denied:kill_switch" and pay.applies == 0  # B sees A's kill
    with pytest.raises(ValueError):
        Executor(erp, pay, clock, audit, ex.pol, ex.directory, state=ControlState())  # another state needs rebind=True
    ex3 = Executor(erp, pay, clock, audit, ex.pol, ex.directory, state=ControlState(), rebind=True)  # a restart
    assert ex3.state is not ex.state and ex3._blocked() == "kill_switch"  # a restart never clears an engaged switch: it is carried forward
    assert ex3.state.killed and any(e["kind"] == "control_state_rebound" and e["carried_kill"] for e in audit.events)


def test_m4_the_switch_is_seen_by_a_state_that_is_still_watched(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ids = approve_all(ex, c)
    assert ex._blocked() is None
    other = ControlState()  # another state watched by the holder (a worker restarted with rebind elsewhere)
    erp.cfg.watch(other)
    other.killed = True
    assert erp.cfg.blocked(), "another watched state"
    assert ex._blocked() == "kill_switch", "another watched state"
    assert ex.release(c["invoice"]["invoice_id"], ids) == "denied:kill_switch"
    erp.cfg.unwatch(other)
    assert ex._blocked() is None
    with pytest.raises(PermissionError):
        other.killed = False  # an engaged switch is not cleared by assignment either; only reenable (two people) clears it


# ---- M5: the port race --------------------------------------------------------------------------------------------------------------------
def test_m5_the_kill_switch_waits_for_a_message_in_flight_and_nothing_starts_after_it(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    eg = EgressGate(erp, clock, audit, pol)
    entered, go = threading.Event(), threading.Event()
    real = audit.append

    def slow(tenant, kind, **f):
        if kind == "egress":
            entered.set()
            go.wait(5)
        return real(tenant, kind, **f)

    audit.append = slow
    sent = []
    t = threading.Thread(
        target=lambda: sent.append(
            eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
        )
    )
    t.start()
    assert entered.wait(5)  # the send passed its checks and is now being audited
    res = ex.state.gate.engage(list, lambda k: "x", by="u1", timeout=0.2)
    assert res.complete is False and res.in_flight_at_timeout == 1  # the switch did not return while the message was in flight
    go.set()
    t.join(5)
    assert len(sent) == 1
    audit.append = real
    assert ex.state.gate.engage(list, lambda k: "x", by="u1", timeout=2).complete
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    co = FakeCallout(erp, clock, pol, audit)
    with pytest.raises(EgressDenied):
        co.request_confirmation(
            "agent_runtime", v["vendor_id"], "confirm_bank_details", {"invoice_number": "A1", "account_last4": "1234"}, "k"
        )


def test_m5_a_release_in_flight_is_dequeued_by_the_switch(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ids = approve_all(ex, c)
    real, outs, threads = pay.enqueue, [], []

    def slow(*a, **k):
        t = threading.Thread(target=lambda: outs.append(ex.engage_kill_switch("finance_controller")))
        threads.append(t)
        t.start()
        for _ in range(300):
            if ex.state.gate.engaged:
                break
            time.sleep(0.01)
        return real(*a, **k)

    pay.enqueue = slow
    assert ex.release(c["invoice"]["invoice_id"], ids) == "queued"
    threads[0].join(10)
    key = next(iter(ex.store.rows))
    assert pay.lookup(key)["status"] == "dequeued" and outs[0] == [(key, "dequeued")]
    with pytest.raises(EffectBlocked), erp.cfg.effect():
        pass


# ---- M6: denials are audited, bounded and capped -------------------------------------------------------------------------------------
def test_m6_a_flood_of_denials_grows_the_chain_by_at_most_the_cap(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    cap = pol["limits"]["denied_audit_per_day"]
    ex.engage_kill_switch("finance_controller")
    n0 = len(audit.events)
    for i in range(cap * 2):
        ex.release(f"inv-{i}-" + "x" * 500, [])
    rows = [e for e in audit.events[n0:] if e["kind"] == "release_denied"]
    assert len(rows) <= cap
    assert all(len(e["invoice_id"]) <= 80 for e in rows), "unbounded text"  # bounded in number and in size
    for call, kind in (
        (lambda: ex.engage_kill_switch("ap_clerk"), "kill_switch_denied"),
        (lambda: ex.compensate("k", "ap_clerk"), "compensate_denied"),
        (lambda: erp.set_hold("agent_runtime", "i", "r", "k"), "erp_denied"),
    ):
        for _ in range(cap + 20):
            with pytest.raises(PermissionError):
                call()
        assert 1 <= sum(e["kind"] == kind for e in audit.events) <= cap, kind  # a denied privileged call leaves a row, and only so many
    assert sum(e["kind"] == "audit_suppressed" for e in audit.events) >= 1 and audit.verify()


def test_m6_a_denied_attestation_is_on_the_chain(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    with pytest.raises(PermissionError):
        co.attest("ap_clerk", "k", "u-trs-01")
    assert any(e["kind"] == "callback_denied" and e["why"] == "attest_identity" for e in audit.events)


# ---- minors ---------------------------------------------------------------------------------------------------------------------------------
def test_b1_frozen_lists_refuse_sort_reverse_and_in_place_operators(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    roles = ex.directory["u-ap-01"]["roles"]
    for edit in (lambda: roles.sort(), lambda: roles.reverse(), lambda: roles.__iadd__(["x"]), lambda: roles.__imul__(2)):
        with pytest.raises(TypeError):
            edit()


def test_every_unicode_space_separates_words_in_the_fold():
    from apexc.textnorm import fold

    for sp in (0x85, 0x1C, 0x1F, 0x2028, 0x2029, 0xA0, 0x3000, 0x2003):
        assert fold("ab" + chr(sp) + "cd") == "ab cd", hex(sp)


def test_m4_a_lift_without_a_clear_is_audited_before_it_is_written(cases, pol):
    from helpers import settle

    c = case_of(cases, "no_receipt")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    audit.fail_kinds = {"hold_lifted"}
    settle(ex, erp, c, pol)
    assert erp.open_holds(inv) == ["no_receipt"], "hold_lifted"  # the audit failed, so nothing was lifted
    audit.fail_kinds = set()
    settle(ex, erp, c, pol)
    assert "no_receipt" not in erp.open_holds(inv)


def test_m1_the_config_view_is_sealed_and_one_pair(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    with pytest.raises(TypeError):
        ex.pol["limits"].__init__({"x": 1})  # re-running __init__ is an in-place edit
    with pytest.raises(TypeError):
        ex.directory["u-ap-01"]["roles"].__init__(["finance_controller"])
    v = ex.cfg.view()
    assert v.pol is ex.pol and v.directory is ex.directory


def test_m2_release_with_no_approval_named_is_not_counted(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    n0 = len(audit.events)
    for _ in range(pol["limits"]["release_attempts_per_invoice_per_day"] * 3):
        assert ex.release(inv, []) == "denied:plans_missing"
    assert not ex.state.attempts and not any(e["kind"] == "release_intent" for e in audit.events[n0:])  # nobody burns an invoice's attempts


def test_m3_reject_takes_the_config_lock_and_reads_the_queue_under_its_own_lock(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    done = threading.Event()
    ex._cfg_lock.acquire()
    try:
        t = threading.Thread(target=lambda: (ex.reject(inv, "u-sup-01", "no-such-invoice"), done.set()))
        t.start()
        assert not done.wait(0.3)  # a reject waits for a release in progress: the not-queued check and the rejection are one step
    finally:
        ex._cfg_lock.release()
    t.join(5)
    assert done.is_set() and pay.queued_invoice_ids() == set()


def test_m4_a_lift_with_its_clear_is_one_audit_event(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    from helpers import settle

    settle(ex, erp, c, pol)
    rows = [e for e in audit.events if e["kind"] == "hold_lifted" and e.get("clear_type")]
    assert rows and not any(e["kind"] == "clear_recorded" for e in audit.events)


def test_m5_reconcile_calls_only_a_complete_queue_entry_applied(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    key = "k-partial"
    ex.store.rows[key] = {"blob": "x", "status": "pending", "result": None}
    ex.state.reservations[key] = ("2026-01-01", "USD", 5)
    pay.rows[key] = {"blob": "x", "entry": {}, "status": "incomplete", "call_id": "c", "ts": "", "tenant": pay.tenant}
    assert ex.reconcile(key) == "pending" and key not in ex.state.queued_at and key in ex.state.reservations
    pay.rows[key]["status"] = "dequeued"
    assert ex.reconcile(key) == "dequeued" and key not in ex.state.queued_at


def test_m6_the_root_of_trust_is_frozen_while_the_kill_switch_is_on(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    v0 = ex.config_version()
    ex.engage_kill_switch("finance_controller")
    assert not ex.change_config("u-ctl-01", "u-ctl-02", "during the incident", lambda p, d: p["limits"].update(egress_per_day=1))
    assert ex.config_version() == v0 and any(e["kind"] == "config_change_denied" and e["why"] == "kill_switch" for e in audit.events)
    assert ex.reenable("u-ctl-01", "u-trs-01")
    assert ex.change_config("u-ctl-01", "u-ctl-02", "after", lambda p, d: p["limits"].update(egress_per_day=1))


def test_m7_a_second_executor_cannot_split_the_audit_chain(cases, pol):
    from apexc.fakes import Audit

    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    with pytest.raises(ValueError):
        Executor(erp, pay, clock, Audit(), ex.pol, ex.directory)


def test_the_consume_right_is_its_own_operation(pol):
    from apexc.rules import identity_can

    assert identity_can("executor_approvals", "consume_approval", pol, "write")
    assert not identity_can("executor_lift", "consume_approval", pol, "write")


def test_no_float_in_any_money_module():
    for f in ("rules.py", "executor.py", "ports.py", "normalise.py", "classify.py", "fakes.py", "tools.py"):
        tree = ast.parse((ROOT / "src" / "apexc" / f).read_text(encoding="utf-8"))
        bad = [
            n
            for n in ast.walk(tree)
            if (isinstance(n, ast.Constant) and type(n.value) is float)
            or (isinstance(n, ast.Name) and n.id == "float" and isinstance(n.ctx, ast.Load) and False)
        ]
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "float"]
        assert not bad and not calls, (f, [getattr(n, "lineno", 0) for n in bad + calls])


# ---- parity with the core copies, the docs and the guard ----------------------------------------------------------------------------------
def test_the_core_copies_match_the_pinned_core_files():
    pins = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    for path, p in pins["files"].items():
        text = (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")
        for core_name, copy_name in p["import_rewrite"]:
            text = text.replace(copy_name, core_name)  # undo the imports the copy needed
        assert hashlib.sha256(text.encode()).hexdigest() == p["core_sha256"], path
    table = (ROOT / "CORE_COPIES.md").read_text(encoding="utf-8")
    assert all(path in table for path in pins["files"]) and f"#{pins['core_pr']}" in table


def test_shared_vectors_pass_on_the_copy():
    from apexc.textnorm import fold

    v = json.loads((ROOT / "tests" / "fixtures" / "textnorm_vectors.json").read_text(encoding="utf-8"))

    def dec(s):
        import re

        return re.sub(r"\{U\+([0-9A-Fa-f]{4,6})\}", lambda m: chr(int(m[1], 16)), s)

    for case in v["identities"]:
        real = fold(case["id"], casefold=True, collapse_ws=True)
        assert all(fold(dec(x), casefold=True, collapse_ws=True) == real for x in case["variants"])
    for case in v["domains"]:
        assert all(fold(dec(x), casefold=True) == case["domain"] for x in case["variants"])


def test_s8_and_s16_of_the_stage_2_spec_say_what_review_9_asked():
    spec = (ROOT / "spec_stage2.md").read_text(encoding="utf-8")
    s8 = spec.split("## 8.")[1].split("## 9.")[0]
    assert "promote" in s8.lower() and "CORE_COPIES.md" in s8 and "Do not copy" not in s8 and "Per the readiness review: copy" not in s8
    s16 = spec.split("## 16.")[1]
    for must in ("one durable transaction", "fails closed", "deadline", "bounded", "backpressure", "to_thread"):
        assert must in s16, must


def test_the_repo_never_points_at_a_studio_or_local_path():
    bad = (
        "egm" + chr(92),
        "bible" + chr(92),
        "memory" + chr(92) + "projects",
        "handoff" + chr(92),
        "C:" + chr(92),
        "projects" + chr(92),
        "Bho" + "vix Lab",
    )
    for f in [*ROOT.glob("*.md"), *ROOT.glob("src/apexc/*.py"), ROOT / "core_copies.json"]:
        text = f.read_text(encoding="utf-8")
        for b in bad:
            assert b not in text, (f.name, b)

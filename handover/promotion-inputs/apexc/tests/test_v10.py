"""Regression tests for the two fresh reviews of v9 (review round 10): a restart that cleared the kill switch, a
config edited in place without a trace, ports with a private holder, payments denials with no audit row, exempt-token channels, an
attempt counter anyone could burn, lift and clear outside the config lock, and the claims about the mutation harness. Each has a mutant in
mutation_check.py. No unicode escapes are typed here: look-alikes are built with chr()."""

import ast
import json
import threading
from pathlib import Path

import pytest
from helpers import approve_all, build
from test_attacks import case_of, forge, world

from apexc.config import ConfigTampered, bind_cfg
from apexc.executor import ControlState, Executor
from apexc.fakes import EgressGate, FakeCallout, ReadOnlyErp
from apexc.tools import summary_leaks

ROOT = Path(__file__).resolve().parents[1]


# ---- B1: the config binding of a port or an executor is read-only ------------------------------------------------------------------------
def test_b1_no_port_and_no_executor_can_be_pointed_at_another_holder(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    co, eg, ro = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol), ReadOnlyErp(erp, audit, clock, pol)
    other = type(erp.cfg)(dict(pol), dict(ex.directory))
    for holder in (ex, erp, pay, co, eg, ro):
        with pytest.raises(AttributeError):
            holder.cfg = other
        assert holder.cfg is erp.cfg, type(holder).__name__
    bind_cfg(eg, erp.cfg)  # the executor's own call (_push) is the one way


# ---- M1: a restart never clears an engaged kill switch -----------------------------------------------------------------------------------
def test_m1_rebinding_a_fresh_state_after_engage_keeps_the_switch_on_and_says_so(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ids = approve_all(ex, c)
    ex.engage_kill_switch("finance_controller")
    ex2 = Executor(erp, pay, clock, audit, ex.pol, ex.directory, live=True, state=ControlState(), rebind=True)
    assert ex2._blocked() == "kill_switch" and ex2.state.killed  # carried forward
    assert ex2.release(c["invoice"]["invoice_id"], ids) == "denied:kill_switch" and pay.applies == 0
    row = next(e for e in audit.events if e["kind"] == "control_state_rebound")
    assert row["carried_kill"] is True
    with pytest.raises(PermissionError):
        ex2.state.killed = False  # assignment does not clear it
    ex2.state.gate.restore(True)
    assert ex2.reenable("u-ctl-01", "u-trs-01") and not ex2._blocked()  # only the two-person re-enable does


def test_m1_a_restart_that_loads_a_saved_engaged_state_stays_engaged(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ex.engage_kill_switch("finance_controller")
    blob = ex.state.to_json()
    ex2 = Executor(erp, pay, clock, audit, ex.pol, ex.directory, live=True, state=ControlState.from_json(blob), rebind=True)
    assert ex2._blocked() == "kill_switch"


# ---- M2: a refused payments call leaves a row, per actor -------------------------------------------------------------------------------------
def test_m2_denied_payments_calls_are_audited_capped_and_do_not_drown_other_actors(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    cap = pol["limits"]["denied_audit_per_day"]
    for _ in range(3):
        with pytest.raises(PermissionError):
            pay.enqueue("agent_runtime", {}, "k", [])
        with pytest.raises(PermissionError):
            pay.dequeue("agent_runtime", "k")
    rows = [e for e in audit.events if e["kind"] == "payments_denied"]
    assert len(rows) == 6 and {e["op"] for e in rows} == {"enqueue", "dequeue"} and all(e["identity"] == "agent_runtime" for e in rows)
    for _ in range(cap + 30):  # one flooder
        with pytest.raises(PermissionError):
            pay.enqueue("ap_clerk", {}, "k", [])
    with pytest.raises(PermissionError):
        pay.enqueue("master_data_admin", {}, "k", [])  # another actor, later: still gets its own row
    assert sum(e["kind"] == "payments_denied" and e["identity"] == "master_data_admin" for e in audit.events) == 1
    marks = [e for e in audit.events if e["kind"] == "audit_suppressed" and e["suppressed_kind"] == "payments_denied"]
    assert marks and all(m["suppressed"] >= 1 for m in marks) and audit.verify()  # the marker carries the count


def test_m2_dequeue_of_an_unknown_key_is_typed(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    assert pay.dequeue("executor_enqueue", "no-such-key") == "unknown"


# ---- M3: the exempt-token channels ---------------------------------------------------------------------------------------------------------
def test_m3_a_number_split_across_two_amounts_is_refused_even_when_nobody_listed_it():
    for text in (
        "$4111111.11 $1111111.11",
        "USD 1234567.89 ref USD 1234567.89",
        "total $41,111,111.11 and $11,111.11",
        "12345678.9 USD then 87654321.9 USD",
    ):
        assert summary_leaks(text, []), text
    assert not summary_leaks("dated 2026-11-01, total $5 USD, PO-1234 late", [])


def test_m3_a_letter_encoded_account_is_refused():
    assert summary_leaks("acct OlISBZGQ ok", []), "OlISBZGQ"


# ---- M4: a config edited in place fails closed, with a row ------------------------------------------------------------------------------------
def test_m4_a_privilege_edit_through_the_base_class_is_caught_and_gains_nothing(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    ids = approve_all(ex, c)
    list.append(ex.directory["u-ap-01"]["roles"], "finance_controller")  # the bypass the review found: a base-class method
    assert ex.cfg.tampered()
    assert not ex.change_config("u-ap-01", "u-ctl-02", "self-promoted", lambda p, d: None)  # no config change by the new "controller"
    assert ex.config_version() != "" and ex.release(c["invoice"]["invoice_id"], ids) == "denied:config_tamper" and pay.applies == 0
    with pytest.raises(Exception):  # noqa: B017 - an approval is refused too (ApprovalRefused)
        ex.approve(c["invoice"]["invoice_id"], "u-sup-01", "plan_1")
    assert any(e["kind"] == "config_tamper" for e in audit.events) and not any(e["kind"] == "config_changed" for e in audit.events)
    with pytest.raises(ConfigTampered), erp.cfg.effect():
        raise AssertionError("an outbound effect must not start on a tampered configuration")
    for who in ("agent_runtime", "executor_enqueue"):  # a ledger write on a tampered config does not even reach the identity check
        with pytest.raises(ConfigTampered):
            pay.enqueue(who, {}, "k", [])


def test_m4_a_policy_edit_through_the_base_class_is_caught_too(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    dict.__setitem__(ex.pol["release"], "dry_run_default", not ex.pol["release"]["dry_run_default"])
    assert ex.cfg.tampered() and ex._blocked() == "config_tamper"


def test_m4_a_legitimate_change_moves_the_digest_with_it(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    assert ex.change_config("u-ctl-01", "u-ctl-02", "tighten", lambda p, d: p["limits"].update(egress_per_day=1))
    assert not ex.cfg.tampered() and ex._blocked() is None


# ---- M5: a port on another policy is refused once the ERP is governed -------------------------------------------------------------------
def test_m5_a_port_on_a_different_policy_is_a_value_error_not_a_private_holder(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    other = json.loads(json.dumps(dict(pol)))
    other["limits"]["egress_per_day"] = 10**6
    for build_port in (
        lambda: EgressGate(erp, clock, audit, other),
        lambda: FakeCallout(erp, clock, other, audit),
        lambda: ReadOnlyErp(erp, audit, clock, other),
    ):
        with pytest.raises(ValueError):
            build_port()


# ---- minors ---------------------------------------------------------------------------------------------------------------------------------
def test_m3_an_incomplete_plan_set_burns_no_attempts_and_the_denial_code_is_no_oracle(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    assert len(ids) == 2
    cap = pol["limits"]["release_attempts_per_invoice_per_day"]
    for _ in range(cap * 3):
        assert ex.release(inv, [ids[0]]) == "denied:plans_missing"  # one plan of two: no authority
        assert ex.release(inv, [ids[0], ids[0]]) == "denied:plans_missing"  # the same id twice is not two plans
    assert not ex.state.attempts
    other = case_of(cases, "clean_match", "test")
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    assert {
        ex.release(inv, ["apr-nosuch", ids[1]]),
        ex.release(other["invoice"]["invoice_id"], ids),
        ex.release(inv, ["apr-0", "apr-9"]),
    } == {"denied:approval_not_usable"}
    assert ex.release(inv, ids) == "queued"  # the real release was never starved


def test_m4_lift_and_clear_wait_for_the_config_lock(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    done = threading.Event()
    ex._cfg_lock.acquire()
    try:
        t = threading.Thread(target=lambda: (ex.lift(inv, "bank_change", "u-sup-01", "x"), done.set()))
        t.start()
        assert not done.wait(0.3), "a lift decided under an old directory could commit after a config change"
    finally:
        ex._cfg_lock.release()
    t.join(5)
    assert done.is_set()
    done2 = threading.Event()
    ex._cfg_lock.acquire()
    try:
        t2 = threading.Thread(target=lambda: (ex.clear(inv, "bank_change", "u-ctl-01", "cb-x"), done2.set()))
        t2.start()
        assert not done2.wait(0.3), "clear waits for the config lock too"
    finally:
        ex._cfg_lock.release()
    t2.join(5)


@pytest.mark.parametrize("which", ["lift", "clear"])
def test_m4_a_config_change_waits_for_a_lift_or_clear_that_is_deciding(cases, pol, which):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    entered, go, changed = threading.Event(), threading.Event(), threading.Event()
    inner = getattr(ex, "_" + which)

    def slow(*a, **k):
        entered.set()
        go.wait(5)
        return inner(*a, **k)

    setattr(ex, "_" + which, slow)
    act = (
        (lambda: ex.lift(inv, "bank_change", "u-sup-01", "x"))
        if which == "lift"
        else (lambda: ex.clear(inv, "bank_change", "u-ctl-01", "cb-x"))
    )
    t1 = threading.Thread(target=act)
    t1.start()
    assert entered.wait(5)
    t2 = threading.Thread(
        target=lambda: (
            ex.change_config("u-ctl-01", "u-ctl-02", "x", lambda p, d: p["limits"].update(erp_reads_per_minute=7)),
            changed.set(),
        )
    )
    t2.start()
    assert not changed.wait(0.3), f"a configuration change landed in the middle of a {which} decision"
    go.set()
    t1.join(5)
    t2.join(5)
    assert changed.is_set()


def test_m_a_word_joiner_or_soft_hyphen_or_control_between_digits_is_dropped_by_the_summary_check():
    for ch in (chr(0xAD), chr(0x202E), chr(1)):
        assert summary_leaks("pay a" + ch + "b now", ["ab"]), hex(ord(ch))  # the word route sees only the folded text


def test_b1_the_label_check_names_the_missing_plan_when_the_count_is_right(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")  # human tier: exactly plan_1 is needed
    inv = c["invoice"]["invoice_id"]
    assert ex.release(inv, [forge(erp, c, pol, "u-trs-01", "plan_2")]) == "denied:plans_missing"


def test_m4_a_kill_switch_stops_a_lift_that_has_not_started(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    ex.engage_kill_switch("finance_controller")
    assert ex.lift(inv, "bank_change", "u-sup-01", "x") is False and any(e["kind"] == "lift_denied" for e in audit.events)


def test_m5_the_kill_sweep_also_dequeues_payments_that_have_no_queue_time(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    pay.rows["k-pre-restart"] = {
        "blob": "x",
        "entry": {"invoice_id": "i"},
        "status": "queued",
        "call_id": "c",
        "ts": "",
        "tenant": pay.tenant,
    }
    assert "k-pre-restart" not in ex.state.queued_at  # a restart lost the queue times
    out = ex.engage_kill_switch("finance_controller")
    assert ("k-pre-restart", "dequeued") in out and pay.rows["k-pre-restart"]["status"] == "dequeued"


def test_m6_a_lost_denial_row_is_counted_not_hidden(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    audit.fail_kinds = {"callback_denied"}
    with pytest.raises(PermissionError):
        co.request_confirmation(
            "ap_clerk", c["context"]["vendor"]["vendor_id"], "confirm_bank_details", {"invoice_number": "A1", "account_last4": "1234"}, "k"
        )
    assert audit.dropped == 1  # the outage is visible, and the refusal still happened


# ---- mutation claims: pins exist, counts are the ones measured -----------------------------------------------------------------------------
def _collected_test_ids() -> set[str]:
    out = set()
    for f in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        out |= {f"tests/{f.name}::{n.name}" for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    return out


def test_every_pinned_kill_names_a_test_that_exists():
    pins = json.loads((ROOT / "mutant_kills.json").read_text(encoding="utf-8"))
    ids = _collected_test_ids()
    missing = {name: tid for name, tid in pins.items() if tid.replace("\\", "/").split("[")[0] not in ids}
    assert not missing, f"stale pins (a test was renamed or removed): {sorted(missing.items())[:5]}"


def test_every_mutant_is_pinned_and_names_a_reason_of_at_least_four_characters():
    import importlib.util

    spec = importlib.util.spec_from_file_location("mc_pins", ROOT / "mutation_check.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    pins = json.loads((ROOT / "mutant_kills.json").read_text(encoding="utf-8"))
    assert {m[0] for m in mc.M} == set(pins), "mutant_kills.json and the mutant list differ: re-run the harness with --record"
    assert all(len(m) < 6 or len(m[5]) >= 4 for m in mc.M)


def test_the_docs_cite_tests_that_exist():
    ids = _collected_test_ids()
    import re

    for f in ("CORE_COPIES.md", "core_copies.json", "acceptance.md", "README.md"):
        text = (ROOT / f).read_text(encoding="utf-8")
        for m in re.finditer(r"tests/(test_\w+\.py)(?:::(test_\w+))?", text):
            assert (ROOT / "tests" / m[1]).exists(), (f, m[0])
            if m[2]:
                assert f"tests/{m[1]}::{m[2]}" in ids, (f, m[0])


def test_b1_each_layer_of_the_summary_check_holds_on_its_own():
    from apexc.egress_text import LeakPolicy, check_text

    wide = LeakPolicy(
        max_digits=30, max_exempt_digits=24, max_total_digits=12
    )  # the digit cap is lifted, so only the token cap can refuse seven small amounts
    seven = " and ".join(f"${i}.50" for i in range(1, 8))
    assert check_text(seven, [], policy=wide) is not None, "seven small tokens"
    assert summary_leaks("Remit 1234.56 and 89.00", []), "Remit 1234.56 and 89.00"  # no currency: digits, not amounts

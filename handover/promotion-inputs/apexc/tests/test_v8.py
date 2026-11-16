"""Regression tests for the two fresh reviews of v8 : a policy and a directory
that could be edited in place (B1), a second executor with its own copy (M1), a kill switch that missed a release in flight and stopped at the
first error (M2), a summary check that digit-counting beats (M3), lifts and clears written before their audit (M4), unlocked ledger iteration (M5),
a mutation harness that proved less than it said (M6), and the design findings: live objects out of the read port, unaudited refusals, an
approval `bound` that was not validated on write, and the nits. Each has a mutant in mutation_check.py that reverts its fix and an expected
kill reason. No unicode escapes are typed in this file: look-alikes are built with chr()."""

import copy
import json
import random
import threading
import time

import pytest
from helpers import approve_all, build, settle
from test_attacks import case_of, forge, world

import apexc.executor as _executor
from apexc.executor import ApprovalRefused, ControlState, Executor
from apexc.fakes import AuditWriteError, EgressDenied, EgressGate, FakeCallout, RateLimited, ReadOnlyErp
from apexc.intake import Intake
from apexc.normalise import fold
from apexc.rules import identity_conflicts
from apexc.tools import summary_leaks

LIFT = _executor.LIFT
APPR = getattr(_executor, "APPR", LIFT)  # before review 8 an approval was written under the lift identity
ZW, EN_DASH, COMBINING, NBSP = chr(0x200B), chr(0x2013), chr(0x301), chr(0xA0)


# ---- B1: the policy and the directory are read-only views ----------------------------------------------------------------------------------
def test_b1_policy_and_directory_are_deeply_read_only_for_every_holder(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    v0, user = ex.config_version(), "u-ap-01"
    co, eg, ro = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol), ReadOnlyErp(erp, audit, clock, pol)
    edits = []
    for h in (ex, erp, pay, co, eg, ro):
        edits += [
            lambda h=h: h.pol["release"].__setitem__("dry_run_default", False),
            lambda h=h: h.pol["limits"]["release_minor_per_day"].update(USD=10**12),
            lambda h=h: h.pol["hard_block_types"].append("nothing"),
            lambda h=h: h.pol["hard_block_types"].clear(),
            lambda h=h: h.pol.pop("limits"),
        ]
    for h in (ex, erp, pay):
        edits += [
            lambda h=h: h.directory[user]["roles"].append("finance_controller"),
            lambda h=h: h.directory[user].update(employee_id="e-other"),
            lambda h=h: h.directory.pop(user),
            lambda h=h: h.directory.__setitem__("evil", {"employee_id": "e", "roles": ["finance_controller"]}),
        ]
    assert len(edits) >= 40
    for edit in edits:
        with pytest.raises(TypeError):
            edit()
    assert ex.config_version() == v0 and ex.directory[user]["roles"] == ["ap_clerk"]


def test_b1_an_in_place_privilege_edit_makes_nobody_a_controller_and_flips_no_decision(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    with pytest.raises(TypeError):
        ex.directory["u-ap-01"]["roles"].append("finance_controller")  # the old route to an instant controller
    with pytest.raises(TypeError):
        ex.pol["release"]["dry_run_default"] = False  # ... and to a live release
    assert not ex.change_config("u-ap-01", "u-ctl-01", "self-promoted", lambda p, d: None)
    assert any(e["kind"] == "config_change_denied" for e in audit.events)
    with pytest.raises(PermissionError):
        ex.engage_kill_switch("ap_clerk")
    assert ex.live is True  # the harness built it live; no edit changed that
    ids = approve_all(ex, c)
    assert ex.release(c["invoice"]["invoice_id"], ids) == "queued"


def test_b1_every_port_reads_the_one_source_and_follows_a_change(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    co, eg, ro = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol), ReadOnlyErp(erp, audit, clock, pol)
    ports = (erp, pay, co, eg, ro)
    assert all(h.cfg is ex.cfg for h in ports)  # ONE holder: nothing keeps a copy of the policy or the directory
    assert ex.change_config("u-ctl-01", "u-ctl-02", "tighten", lambda p, d: p["limits"].update(egress_per_day=1))
    for h in ports:
        assert h.pol is ex.pol and h.pol["limits"]["egress_per_day"] == 1, type(h).__name__
    assert erp.directory is ex.directory and pay.directory is ex.directory
    for name in ("pol", "directory"):
        with pytest.raises(AttributeError):
            setattr(erp, name, {})  # no setter on any port either


def test_b1_frozen_views_are_deep_copies_that_behave_like_plain_json():
    from apexc.config import FrozenDict, FrozenList, freeze, thaw

    src = {"a": [1, {"b": [2, 3]}], "c": {"d": "e"}}
    f = freeze(src)
    src["a"][1]["b"].append(99)
    assert f == {"a": [1, {"b": [2, 3]}], "c": {"d": "e"}} and isinstance(f, FrozenDict) and isinstance(f["a"], FrozenList)
    assert json.loads(json.dumps(f)) == f and thaw(f) == f and type(thaw(f)) is dict and type(thaw(f)["a"][1]["b"]) is list
    assert copy.deepcopy(f) == f and type(copy.deepcopy(f)) is dict  # a deep copy is the plain, editable one
    for op in (
        lambda: f.update(x=1),
        lambda: f["a"].sort(),
        lambda: f["a"].__iadd__([1]),
        lambda: f.__ior__({"x": 1}),
        lambda: f.setdefault("z", 1),
    ):
        with pytest.raises(TypeError):
            op()


# ---- M1: one config object across executors ---------------------------------------------------------------------------------------------------
def test_m1_a_second_executor_on_the_same_erp_sees_a_config_change(cases, pol):
    from apexc.config import thaw

    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "bank_remit")
    inv = c["invoice"]["invoice_id"]
    ex2 = Executor(erp, pay, clock, audit, ex.pol, ex.directory, live=True, state=ex.state)  # worker B
    assert ex2.cfg is ex.cfg and ex2._cfg_lock is ex._cfg_lock and ex2.pol is ex.pol
    ids = approve_all(ex2, c)
    clear = next(r for r in erp.clears if r["invoice_id"] == inv and r["kind"] == "clear")
    attester = erp.callbacks[clear["evidence_id"]]["attested_by"]
    assert ex.change_config("u-ctl-01", "u-ctl-02", "revoke the attester", lambda p, dr: dr[attester].update(roles=["ap_clerk"]))
    assert ex2.config_version() == ex.config_version() and ex2.directory[attester]["roles"] == ["ap_clerk"]
    assert ex2.release(inv, ids) == "denied:config_changed" and pay.applies == 0  # worker B did not keep a stale directory
    with pytest.raises(ValueError):  # a worker built with another configuration is refused, not silently given its own
        Executor(erp, pay, clock, audit, {**thaw(pol), "version": 999}, ex.directory)


# ---- M2: the kill switch --------------------------------------------------------------------------------------------------------------------------
def test_m2_a_release_past_its_recheck_when_the_switch_is_thrown_is_still_dequeued(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    real, outs, threads = pay.enqueue, [], []

    def slow(*a, **k):
        t = threading.Thread(target=lambda: outs.append(ex.engage_kill_switch("finance_controller")))
        threads.append(t)
        t.start()
        for _ in range(300):
            if ex.killed:
                break
            time.sleep(0.01)
        time.sleep(0.2)  # the switch's scan runs now unless it waits for the release in flight
        return real(*a, **k)

    pay.enqueue = slow
    assert ex.release(inv, ids) == "queued"
    threads[0].join(10)
    key = next(iter(ex.store.rows))
    assert pay.lookup(key)["status"] == "dequeued" and outs[0] == [(key, "dequeued")]


def test_m2_one_failing_undo_does_not_stop_the_rest(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    now = clock.now()
    for k in ("k-bad", "k-good"):
        pay.rows[k] = {"blob": "x", "entry": {}, "status": "queued", "call_id": "c", "ts": "", "tenant": pay.tenant}
        ex.store.rows[k] = {"blob": "x", "status": "applied", "result": None}
        ex.state.queued_at[k] = now
    real = pay.dequeue
    pay.dequeue = lambda ident, key: (_ for _ in ()).throw(RuntimeError("store hiccup")) if key == "k-bad" else real(ident, key)
    out = ex.engage_kill_switch("finance_controller")
    assert out == [("k-bad", "denied:internal_error"), ("k-good", "dequeued")] and pay.rows["k-good"]["status"] == "dequeued"
    assert any(e["kind"] == "internal_error" and e.get("key") == "k-bad" for e in audit.events)


def test_m2_ports_refuse_while_the_kill_switch_is_on_and_work_again_after_two_people_lift_it(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    co, eg = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol)
    slots = {"invoice_number": "A1", "account_last4": "1234"}
    ex.engage_kill_switch("finance_controller")
    with pytest.raises(EgressDenied):
        co.request_confirmation("agent_runtime", v["vendor_id"], "confirm_bank_details", slots, "k1")
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    assert co.dials == [] and eg.outbox == []
    assert {e["why"] for e in audit.events if e["kind"] in ("callback_denied", "egress_denied")} == {"kill_switch"}
    assert ex.reenable("u-ctl-01", "u-trs-01")
    assert co.request_confirmation("agent_runtime", v["vendor_id"], "confirm_bank_details", slots, "k1").outcome == "applied"
    assert eg.send("agent_runtime", "email", v["vendor_id"], v["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})


# ---- M3: the summary check ---------------------------------------------------------------------------------------------------------------------------
SEPS = [" ", "_", ":", "|", "ab", " ab ", "xy", NBSP, ZW, COMBINING, EN_DASH, chr(0x2014), chr(0xE9), chr(0xDF), chr(0x65E5), chr(0x3A9), chr(0x405),
        chr(0x406), chr(0x408), chr(0x423), chr(0x43E), chr(0x445), chr(0x4AE)]  # fmt: skip


def _digit(rnd):
    return chr(rnd.choice((0x30, 0xFF10, 0x660, 0x6F0, 0x966)) + rnd.randrange(10))  # ASCII, full-width, Arabic-Indic, Persian, Devanagari


def test_m3_fuzz_no_separator_letter_or_script_hides_eight_digits():
    rnd = random.Random(80)
    for _ in range(400):
        text = "acct " + "".join(_digit(rnd) + (rnd.choice(SEPS) if rnd.random() < 0.7 else "") for _ in range(rnd.randint(8, 19)))
        assert summary_leaks(text, []), text
    for text in ("1234 ab 5678 ab 9012", "1234 ab 5678 cd 9012", f"1234 {chr(0x43E)}{chr(0x445)} 5678 xy 9012", "12 a b c 3456 d e f 78"):
        assert summary_leaks(text, []), text


def test_m3_dates_need_a_plausible_year_and_a_valid_calendar_day():
    assert summary_leaks("1234-12-12", []) and summary_leaks("1999-12-12 and 3456", []) and summary_leaks("12/12/1234", [])
    assert not summary_leaks("dated 2026-11-01 and 20.10.2026", [])
    assert summary_leaks("2026-13-45", [])  # not a calendar day


def test_m3_every_uppercase_look_alike_is_folded_and_a_protected_value_is_found():
    table = {0x405: "S", 0x406: "I", 0x408: "J", 0x423: "Y", 0x410: "A", 0x412: "B", 0x415: "E", 0x41A: "K", 0x41C: "M", 0x41D: "H",
             0x41E: "O", 0x420: "P", 0x421: "C", 0x422: "T", 0x425: "X", 0x455: "s", 0x456: "i", 0x458: "j", 0x4BB: "h", 0x51B: "q", 0x51D: "w"}  # fmt: skip
    for cp, latin in table.items():
        assert fold(chr(cp)) == latin, hex(cp)
    secret = "ACCOUNTSIJY77"
    text = "acct " + "".join(chr(cp) if (cp := {"S": 0x405, "I": 0x406, "J": 0x408, "Y": 0x423}.get(ch)) else ch for ch in secret)
    assert summary_leaks(text, [secret]) and summary_leaks(text.lower(), [secret])


def test_m3_what_still_passes():
    for text in ("Invoice HF-52341 price differs by 2 percent", "PO-1234 line 3 is short by 4 units", "dated 2026-11-01, total 5,000 USD",
                 "qty 12 at 450 each, line 7", "PO-1234 and the second PO both differ"):  # fmt: skip
        assert not summary_leaks(text, []), text


# ---- M4: lifts and clears are audited strictly BEFORE they are written -------------------------------------------------------------------
def test_m4_a_failed_audit_write_lifts_nothing(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    open_before = sorted(erp.open_holds(inv))
    assert open_before
    audit.fail_kinds = {"hold_lifted"}
    settle(ex, erp, c, pol)
    assert sorted(erp.open_holds(inv)) == open_before and erp.clears == []  # nothing was lifted, nothing cleared
    assert not any(k == "hold_lifted" for k, _ in ex.state.audit_backlog)  # and nothing waits to be written later: it never happened


def test_m4_a_failed_clear_audit_writes_neither_the_clear_nor_the_lift(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    ex.place_holds(inv)
    audit.fail_kinds = {"hold_lifted"}  # ONE event covers the lift and its clear (review 9, m4)
    settle(ex, erp, c, pol)
    assert erp.clears == [] and "bank_change" in erp.open_holds(inv)
    audit.fail_kinds = set()
    settle(ex, erp, c, pol)
    assert [r["kind"] for r in erp.clears if r["type"] == "bank_change"] == ["clear"] and "bank_change" not in erp.open_holds(inv)
    kinds = [e["kind"] for e in audit.events]
    assert kinds.index("hold_lifted") < kinds.index("hard_block_cleared") and "clear_recorded" not in kinds


def test_m4_a_lift_that_did_nothing_writes_no_clear_row(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    settle(ex, erp, c, pol)
    n = len(erp.clears)
    row = {"invoice_id": inv, "type": "bank_change", "by": "u-ctl-02", "evidence_id": "cb-x", "kind": "clear"}
    assert (
        erp.lift_hold(LIFT, inv, "bank_change", "u-ctl-02", {"evidence_id": "cb-x"}, clear=row) is False
    )  # the second lifter: nothing to lift
    assert len(erp.clears) == n


def test_m4_record_clear_is_audited_before_it_is_written(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    audit.fail_kinds = {"clear_recorded"}
    with pytest.raises(AuditWriteError):
        erp.record_clear(LIFT, {"invoice_id": inv, "type": "bank_change", "by": "u-ctl-01", "kind": "clear", "evidence_id": None})
    assert erp.clears == []


# ---- M5: ledger iteration is a snapshot under the ERP lock -------------------------------------------------------------------------------
class _Racing(dict):
    """A holds ledger whose iteration is joined by a concurrent writer: the writer lands mid-iteration unless iteration holds the ERP lock."""

    armed = False
    erp = None

    def items(self):
        first = True
        for kv in dict.items(self):
            if first and self.armed:
                first = False
                t = threading.Thread(target=lambda: self.erp.set_hold("system_holds", f"inv-race-{len(self)}", "price_variance", "k"))
                t.start()
                t.join(0.3)
            yield kv


def test_m5_a_concurrent_hold_does_not_break_pressure_or_aging(cases, pol):
    c = case_of(cases, "bank_remit")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    racing = _Racing(
        {"inv-pre-1": [], "inv-pre-2": []}
    )  # entries left to iterate after the first, so a writer landing mid-iteration breaks it
    racing.erp = erp
    erp.holds = racing
    racing.armed = True
    types = ex.place_holds(inv)  # hold_pressure iterates the ledger
    assert types and not any(e["kind"] == "internal_error" for e in audit.events)
    clock.advance(60 * 24 * 6)
    racing.armed = True
    assert ex.sweep_aging() and not any(e["kind"] == "internal_error" for e in audit.events)


# ---- minors ------------------------------------------------------------------------------------------------------------------------------------------
def test_minor_1_the_approval_write_checks_its_shape_and_the_bound_set_exactly(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    good = forge(erp, c, pol, "u-sup-02", "plan_1")
    row = erp.approvals[good]
    base = {k: copy.deepcopy(row[k]) for k in ("invoice_id", "vendor_id", "plan", "by", "bound", "config_version")}
    n = len(erp.approvals)
    for bad in (
        {**base, "bound": {**base["bound"], (1, 2): "x"}},  # a tuple key raised from json.dumps, not from validation
        {**base, "bound": {**base["bound"], 7: "x"}},  # an int key was silently coerced to a string
        {**base, "bound": {**base["bound"], "types": sorted({*base["bound"]["types"], "new_vendor", "bank_change"})}},  # a superset
        {**base, "bound": {**base["bound"], "lines": "0" * 16}},  # another invoice's lines
        {**base, "bound": {**base["bound"], "total_minor": "1"}},  # a stale amount
        {**base, "bound": {**base["bound"], "extra": 1}},
    ):
        with pytest.raises(ValueError):
            erp.record_approval(APPR, bad)
    assert len(erp.approvals) == n
    assert erp.record_approval(APPR, base)["approval_id"] and ex.release(inv, [good])  # the exact bound still goes in


def test_minor_2_a_recheck_that_crashes_strands_no_row_and_no_reservation(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    inv = c["invoice"]["invoice_id"]
    ids = approve_all(ex, c)
    real, calls = erp.read_case, []

    def flaky(i):
        calls.append(i)
        if len(calls) == 2:  # the gates' read is the first, the recheck's read at enqueue time the second
            raise RuntimeError("store hiccup")
        return real(i)

    erp.read_case = flaky
    assert ex.release(inv, ids) == "denied:internal_error"
    erp.read_case = real
    assert ex.store.rows == {} and ex.state.reservations == {} and not any(ex.count_by_day.values()) and pay.applies == 0
    assert any(e["kind"] == "internal_error" and e["method"] == "recheck" for e in audit.events)


def test_minor_3_a_second_release_never_double_counts_a_reservation(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, copy.deepcopy(pol), "clean_match")
    inv, day = c["invoice"]["invoice_id"], clock.now()[:10]
    ids = approve_all(ex, c)
    key = ex._key(inv)
    cur, amt = c["invoice"]["currency"], int(c["invoice"]["total_minor"])
    ex.state.count_by_day[day], ex.state.minor_by_day[(cur, day)], ex.state.reservations[key] = 1, amt, (day, cur, amt)  # a call in flight
    assert ex.release(inv, ids) == "queued"
    assert ex.count_by_day[day] == 1 and ex.state.minor_by_day[(cur, day)] == amt  # not 2 and not 2 x amt


def test_minor_7_lifting_clearing_and_approving_are_three_identities(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    inv = c["invoice"]["invoice_id"]
    for ident, call in (
        ("executor_lift", lambda i: erp.record_approval(i, {})),  # lifting and clearing never writes an approval
        ("executor_approvals", lambda i: erp.lift_hold(i, inv, "price_variance", "u-sup-01")),
        (
            "executor_approvals",
            lambda i: erp.record_clear(i, {"invoice_id": inv, "type": "t", "by": "u", "kind": "clear", "evidence_id": None}),
        ),
        ("executor_approvals", lambda i: erp.consume_approvals("executor_lift", [])),
    ):
        with pytest.raises(PermissionError):
            call(ident)
    assert identity_conflicts(pol) == []


def test_minor_5_a_key_replays_only_the_same_request_and_an_attestation_is_audited_before_it_is_visible(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    co = FakeCallout(erp, clock, pol, audit)
    vid = c["context"]["vendor"]["vendor_id"]
    slots = {"invoice_number": "A1", "account_last4": "1234"}
    first = co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k1")
    assert co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k1").outcome == "duplicate_ignored"
    with pytest.raises(ValueError):
        co.request_confirmation(
            "agent_runtime", vid, "confirm_price", {"invoice_number": "A1", "currency": "USD", "amount_minor": "5"}, "k1"
        )
    assert len(co.dials) == 1 and first.ticket_id
    seen, real = [], audit.append

    def spy(tenant, kind, **f):
        if kind == "callback_attested":
            seen.append(
                any(r["callback_id"] == f["callback_id"] for r in erp.callbacks.values())
            )  # visible while its audit event is written?
        return real(tenant, kind, **f)

    audit.append = spy
    rec = co.attest("attest_callback_capability", "k1", "u-trs-01")
    assert seen == [False] and rec["callback_id"] in erp.callbacks
    audit.fail_kinds = {"callback_attested"}
    co2_key = co.request_confirmation("agent_runtime", vid, "confirm_bank_details", slots, "k2")
    with pytest.raises(AuditWriteError):
        co.attest("attest_callback_capability", "k2", "u-trs-01")
    assert f"cb-{co2_key.ticket_id}" not in erp.callbacks  # nothing to roll back: it was never written


def test_minor_6_a_message_being_processed_is_not_processed_again():
    intake, started, release, calls = Intake(), threading.Event(), threading.Event(), []
    intake.receive("t1", "m1", b"hello")

    def handler(raw):
        calls.append(raw)
        started.set()
        release.wait(5)
        return "processed"

    t = threading.Thread(target=lambda: intake.process("t1", "m1", handler))
    t.start()
    assert started.wait(5)
    assert intake.process("t1", "m1", handler) == "processing" and len(calls) == 1  # the second worker does not run the handler
    release.set()
    t.join(5)
    assert intake.process("t1", "m1", handler) == "processed" and len(calls) == 1


def test_minor_flood_of_release_calls_on_one_invoice_grows_the_chain_by_at_most_the_cap(cases, pol):
    small = copy.deepcopy(pol)
    small["limits"]["denied_audit_per_day"] = 20  # review 10: the refusal rows are capped per actor by the denied-audit cap
    c, erp, pay, clock, audit, ex = world(cases, small, "clean_match")
    inv = c["invoice"]["invoice_id"]
    cap = pol["limits"]["release_attempts_per_invoice_per_day"]
    ids = approve_all(ex, c)
    assert ex.release(inv, ids) == "queued"
    before = len(audit.events)
    outs = [ex.release(inv, ids) for _ in range(cap * 3)]  # a caller who names this invoice's approvals, over and over
    assert outs[-1] == "denied:attempt_limit" and outs.count("denied:attempt_limit") >= cap * 2 - 1
    assert ex.release(inv, []) == "denied:plans_missing"  # a call that names no approval is not counted at all (review 9, m2)
    new = audit.events[before:]
    assert (
        sum(e["kind"] == "release_intent" for e in new) <= cap and 1 <= sum(e["kind"] == "release_attempt_limit" for e in new) <= 20
    )  # capped per actor, with a count in the audit_suppressed rows
    assert len(new) <= 3 * cap  # intent + denied per call, up to the cap, plus the one limit event
    assert ControlState.from_json(ex.state.to_json()).attempts == ex.state.attempts


# ---- design review 8 ------------------------------------------------------------------------------------------------------------------------
def test_design_m1_the_read_port_hands_out_copies_never_live_erp_objects(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    erp.pos["PO-1"] = {"po_id": "PO-1", "lines": [{"qty": 5}]}
    vid = c["context"]["vendor"]["vendor_id"]
    erp.vendors[vid] = copy.deepcopy(c["context"]["vendor"])
    ro = ReadOnlyErp(erp, audit, clock, pol)
    po = ro.get_po("ap_clerk", "PO-1", "match")
    po["lines"][0]["qty"] = 999
    po["extra"] = 1
    assert erp.pos["PO-1"] == {"po_id": "PO-1", "lines": [{"qty": 5}]}
    assert ro.get_po("ap_clerk", "PO-404", "match") is None
    full = ro.get_vendor("master_data_admin", vid, "maintenance")
    full["bank"]["account"] = "HACKED"
    for v in erp.all_vendors() + erp.vendor_by_account(erp.vendors[vid]["bank"]["account"]):
        v["bank"]["account"] = "HACKED"
    assert erp.vendors[vid]["bank"]["account"] != "HACKED"
    erp.history["v-other"] = [{"invoice_id": "h1", "total_minor": "5"}]
    erp.cross_vendor_history(vid)[0]["total_minor"] = "9"
    assert erp.history["v-other"][0]["total_minor"] == "5"


def test_design_m2_refused_attempts_leave_a_masked_capped_audit_row_before_the_refusal(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    v = c["context"]["vendor"]
    erp.vendors[v["vendor_id"]] = v
    eg, co = EgressGate(erp, clock, audit, pol), FakeCallout(erp, clock, pol, audit)
    slots = {"invoice_number": "HF52341", "account_last4": "1234"}
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "callback", v["vendor_id"], "+1-555-0199", "confirm_bank_details", slots)
    with pytest.raises(PermissionError):
        eg.send("ap_clerk", "callback", v["vendor_id"], v["contact"]["verified_phone"], "confirm_bank_details", slots)
    with pytest.raises(ValueError):
        co.request_confirmation(
            "agent_runtime", v["vendor_id"], "confirm_bank_details", {"invoice_number": "a b", "account_last4": "x"}, "k"
        )
    with pytest.raises(PermissionError):
        co.request_confirmation("ap_clerk", v["vendor_id"], "confirm_bank_details", slots, "k")
    ro = ReadOnlyErp(erp, audit, clock, pol)
    with pytest.raises(PermissionError):
        ro.get_po("master_data_admin", "PO-1", "p")
    rows = {e["kind"]: e for e in audit.events if e["kind"] in ("egress_denied", "callback_denied", "read_denied")}
    assert set(rows) == {"egress_denied", "callback_denied", "read_denied"}
    assert (
        "+1-555-0199" not in json.dumps(audit.events) and next(e for e in audit.events if e["kind"] == "egress_denied")["to"] == "***0199"
    )
    assert [e["why"] for e in audit.events if e["kind"] == "callback_denied"] == ["slots_rejected", "identity"]
    # a rate-limited read is on the chain too, and a flood of refusals is capped per day
    assert ex.change_config(
        "u-ctl-01", "u-ctl-02", "tight", lambda p, d: p["limits"].update(erp_reads_per_minute=1, denied_audit_per_day=3)
    )
    ro2, eg2 = ReadOnlyErp(erp, audit, clock, ex.pol), EgressGate(erp, clock, audit, ex.pol)
    ro2.get_vendor("agent_runtime", v["vendor_id"], "p")
    with pytest.raises(RateLimited):
        ro2.get_vendor("agent_runtime", v["vendor_id"], "p")
    assert any(e["kind"] == "read_denied" and e["why"] == "rate_limited" for e in audit.events)
    for _ in range(10):
        with pytest.raises(EgressDenied):
            eg2.send("agent_runtime", "callback", v["vendor_id"], "+1-555-0100", "confirm_bank_details", slots)
    assert (
        sum(e["kind"] == "egress_denied" for e in audit.events) == 3
        and 1 <= sum(e["kind"] == "audit_suppressed" for e in audit.events) <= 8
    )
    audit.fail_next = True  # an audit outage never turns a refusal into another error
    with pytest.raises(EgressDenied):
        EgressGate(erp, clock, audit, ex.pol).send(
            "agent_runtime", "callback", v["vendor_id"], "+1-555-0100", "confirm_bank_details", slots
        )


def test_design_m3_a_malformed_bound_is_rejected_not_ignored(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    good = forge(erp, c, pol, "u-sup-01", "plan_1")
    bound = copy.deepcopy(erp.approvals[good]["bound"])
    for extra in ((1, 2), 7, None):
        with pytest.raises(ValueError):
            erp.record_approval(APPR, {"invoice_id": c["invoice"]["invoice_id"], "vendor_id": bound["vendor_id"], "plan": "plan_1", "by": "u-sup-01",
                                       "bound": {**bound, extra: 1}, "config_version": ex.config_version()})  # fmt: skip
    with pytest.raises(ApprovalRefused):  # and the executor path still refuses what it cannot bind
        ex.approve("inv-none", "u-sup-01", "plan_1")


def test_design_m5_the_spec_states_the_stage_2_io_obligation():
    from pathlib import Path

    spec = (Path(__file__).resolve().parents[1] / "spec_stage2.md").read_text(encoding="utf-8")
    assert "never held across" in spec and "to_thread" in spec and "async" in spec.lower()
    assert "schema-asks.md" in (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert (Path(__file__).resolve().parents[1] / "schema-asks.md").exists()


def test_the_repo_docs_do_not_point_at_studio_root_paths():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for f in (
        "README.md",
        "acceptance.md",
        "spec_stage2.md",
        "scoping.md",
        "PROMISES.md",
        "gate_rules.md",
        "failure_modes.md",
        "eval-contract.md",
    ):
        text = (root / f).read_text(encoding="utf-8")
        for bad in (
            "eg" + "m" + chr(92),
            "eg" + "m/demos",
            "bi" + "ble" + chr(92),
            "mem" + "ory" + chr(92) + "projects",
            "hand" + "off" + chr(92),
        ):
            assert bad not in text, (f, bad)


def test_design_m4_one_vendors_flood_cannot_use_up_the_others_share(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    a = c["context"]["vendor"]
    b = {**copy.deepcopy(a), "vendor_id": "v-902"}
    erp.vendors[a["vendor_id"]], erp.vendors["v-902"] = a, b
    eg = EgressGate(erp, clock, audit, pol)
    per_vendor = pol["limits"]["egress_per_vendor_per_day"]
    assert 0 < per_vendor < pol["limits"]["egress_per_day"]
    for _ in range(per_vendor):
        eg.send("agent_runtime", "email", a["vendor_id"], a["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    with pytest.raises(EgressDenied):
        eg.send("agent_runtime", "email", a["vendor_id"], a["contact"]["email_on_file"], "notify_hold", {"invoice_number": "A1"})
    assert (
        eg.send("agent_runtime", "email", "v-902", b["contact"]["email_on_file"], "notify_hold", {"invoice_number": "B1"})["vendor_id"]
        == "v-902"
    )


# ---- M6: the mutation harness judges the reason for a kill, not only the exit code -------------------------------------------------------
def _harness():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("mc_judge", Path(__file__).resolve().parents[1] / "mutation_check.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    return mc


def test_m6_the_harness_judges_the_reason_for_a_kill_and_counts_internal_error_as_a_crash():
    mc = _harness()
    plain = "tests/test_v8.py::test_a | E   AssertionError: assert 1 == 2"
    assert mc.judge(1, plain) == "KILLED" and mc.judge(0, plain) == "SURVIVED" and mc.judge(5, plain) == "NO TESTS RAN"
    assert (
        mc.judge(1, plain, "test_a") == "KILLED" and mc.judge(1, plain, "test_other") == "KILLED-WRONG-REASON"
    )  # an unrelated test killed it
    assert mc.judge(1, plain, None, "tests/test_v8.py::test_a") == "KILLED"
    assert mc.judge(1, plain, None, "tests/test_v8.py::test_b") == "KILLED-OTHER-TEST"  # a different test than the reviewed baseline
    crash = "tests/test_v8.py::test_a | E   KeyError: 'x'"
    internal = "tests/test_v8.py::test_a | E   AssertionError: assert 'denied:internal_error' == 'queued'"
    assert mc.judge(1, crash) == "KILLED-CRASH" and mc.judge(1, internal) == "KILLED-CRASH"
    assert (
        mc.judge(1, "tests/test_v8.py::test_a | E   RuntimeError: boom") == "KILLED-CRASH"
    )  # an exception other than an assertion is not an assertion kill
    assert mc.PINS.exists() and all(
        m[0] in __import__("json").loads(mc.PINS.read_text(encoding="utf-8")) for m in mc.M
    )  # every mutant is pinned


# ---- survivors of the first full mutation run (each mutant below was alive until these tests existed) -------------------------------------
def test_minor_1_shape_a_row_with_the_exact_bound_but_the_wrong_types_is_not_stored(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    good = forge(erp, c, pol, "u-sup-02", "plan_1")
    base = {k: copy.deepcopy(erp.approvals[good][k]) for k in ("invoice_id", "vendor_id", "plan", "by", "bound", "config_version")}
    n = len(erp.approvals)
    for extra in ({"single_minor": "9"}, {"single_minor": True}, {"single_minor": -1}, {"currency": 5}):
        with pytest.raises(ValueError):
            erp.record_approval(APPR, {**base, **extra})
    assert len(erp.approvals) == n


def test_m2_a_constructor_refuses_an_unusable_configuration_on_a_fresh_erp(cases, pol):
    c = case_of(cases, "clean_match")
    erp, pay, clock, audit, ex = build(c, pol)
    from apexc.fakes import FakeErp, FakePayments

    bad = copy.deepcopy(pol)
    bad["identities"]["executor_enqueue"]["write"].append("approve_release")  # an actor that also approves
    fresh = FakeErp("t9", pol, clock)
    with pytest.raises(ValueError):
        Executor(fresh, FakePayments("t9", c["context"]["directory"], pol), clock, audit, bad, c["context"]["directory"])
    nameless = copy.deepcopy(c["context"]["directory"])
    nameless["u-ap-01"]["employee_id"] = ""
    with pytest.raises(ValueError):
        Executor(fresh, FakePayments("t9", nameless, pol), clock, audit, pol, nameless)
    assert fresh.cfg.bound is False  # a refused configuration binds nothing


def test_b1_ports_built_before_the_executor_are_pointed_at_the_shared_holder_by_it(cases, pol):
    from apexc.fakes import FakeErp, FakePayments

    c = case_of(cases, "clean_match")
    clock = build(c, pol)[2]
    audit = build(c, pol)[3]
    erp, pay = FakeErp("t7", pol, clock), FakePayments("t7", c["context"]["directory"], pol)
    co, eg, ro = FakeCallout(erp, clock, pol, audit), EgressGate(erp, clock, audit, pol), ReadOnlyErp(erp, audit, clock, pol)
    assert all(h.cfg is not erp.cfg for h in (co, eg, ro))  # each holds its own until an executor takes the ERP
    ex = Executor(erp, pay, clock, audit, pol, c["context"]["directory"])
    assert all(h.cfg is ex.cfg for h in (erp, pay, co, eg, ro))
    assert ex.change_config("u-ctl-01", "u-ctl-02", "tighten", lambda p, d: p["limits"].update(egress_per_day=1))
    assert all(h.pol["limits"]["egress_per_day"] == 1 for h in (erp, pay, co, eg, ro))

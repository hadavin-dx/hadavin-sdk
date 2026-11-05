"""Regression tests for the two fresh reviews of v10 (review round 11): the safety actions must not depend on the
configuration digest, a denial row cannot be bought with a class string, a rebind has no window, a failed constructor changes nothing, and
the client-visible documents carry no studio-internal names. Look-alikes and control characters are built with chr()."""

import json
import re
import threading
from pathlib import Path

import pytest
from helpers import approve_all, build
from test_attacks import case_of, world

from apexc.executor import ControlState, Executor
from apexc.fakes import Audit
from apexc.rules import authorize_op
from apexc.tools import summary_leaks

ROOT = Path(__file__).resolve().parents[1]


# ---- N1: the undo and the kill sweep do not stop on a tampered configuration -------------------------------------------------------------
def _tamper(ex) -> None:
    dict.__setitem__(ex.pol["limits"], "kill_drain_seconds", 99)  # an edit through the base class: the digest no longer matches
    assert ex.cfg.tampered()


def test_n1_the_kill_sweep_still_dequeues_queued_payments_on_a_tampered_configuration(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    assert ex.release(inv, approve_all(ex, c)) == "queued"
    key = pay.queued_keys()[0]
    _tamper(ex)
    out = ex.engage_kill_switch("finance_controller")
    assert (key, "dequeued") in out and pay.rows[key]["status"] == "dequeued", f"the sweep must dequeue on a tampered configuration: {out}"
    assert ex.release(inv, []) == "denied:config_tamper"  # and everything else stays shut


def test_n1_compensate_still_dequeues_inside_the_undo_window_on_a_tampered_configuration(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    assert ex.release(inv, approve_all(ex, c)) == "queued"
    key = pay.queued_keys()[0]
    _tamper(ex)
    assert ex.compensate(key, "treasury_officer") == "dequeued", "the undo must not wait for a repaired configuration"
    assert pay.rows[key]["status"] == "dequeued"


def test_n1_a_tampered_policy_cannot_widen_who_may_dequeue_or_use_the_kill_switch(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    inv = c["invoice"]["invoice_id"]
    assert ex.release(inv, approve_all(ex, c)) == "queued"
    key = pay.queued_keys()[0]
    dict.__setitem__(ex.pol["identities"]["agent_runtime"], "write", ["dequeue", "kill_switch", "request_dequeue"])  # a self-granted right
    with pytest.raises(PermissionError):
        pay.dequeue("agent_runtime", key)
    with pytest.raises(PermissionError):
        ex.engage_kill_switch("agent_runtime")
    with pytest.raises(PermissionError):
        ex.compensate(key, "agent_runtime")
    assert pay.rows[key]["status"] == "queued"


def test_n1_the_kill_switch_does_not_wait_for_the_config_lock(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    done = threading.Event()
    with ex._cfg_lock:  # a release or a config change is deciding
        t = threading.Thread(target=lambda: (ex.engage_kill_switch("finance_controller"), done.set()))
        t.start()
        assert done.wait(5), "the kill switch must not wait for a release or a config change"
    t.join(5)


# ---- N2: a denial class string cannot buy more rows; another invoice's author is not charged --------------------------------------------
def test_n2_varying_the_identity_string_cannot_grow_the_denied_audit_beyond_the_kind_ceiling(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    cap = ex.pol["limits"]["denied_audit_per_day"]
    for i in range(cap * 8):
        with pytest.raises(PermissionError):
            pay.enqueue(f"attacker-{i}", {}, f"k{i}", [])
    rows = sum(e["kind"] == "payments_denied" for e in audit.events)
    assert rows <= 5 * cap, f"kind ceiling exceeded: {rows}"  # five times the per-class cap, whatever strings the caller picked
    assert len(audit._capped) <= 5 * cap + 8  # and the bookkeeping is bounded too
    marks = [e for e in audit.events if e["kind"] == "audit_suppressed" and e.get("suppressed_kind") == "payments_denied"]
    assert marks and max(e["suppressed"] for e in marks) >= cap, "the turned-away attempts are counted in a marker"


def test_n2_a_release_refusal_is_never_charged_to_the_author_of_another_invoices_approval(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_large")
    other = case_of(cases, "clean_match", "test")
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    other_ids = approve_all(ex, other)  # approvals that belong to ANOTHER invoice
    inv = c["invoice"]["invoice_id"]
    for _ in range(5):
        ex.release(inv, [other_ids[0]])  # a third party passes the other invoice's approval id
    victim = erp.approvals[other_ids[0]]["by"]
    assert not any(e["kind"] == "release_denied" and e.get("cls") == victim for e in audit.events), "charged to another invoice's author"


# ---- N5: what the letter-encoding check does and does not count --------------------------------------------------------------------------
def test_n5_capital_letter_encodings_are_refused_and_the_lowercase_tail_is_the_documented_exception():
    assert summary_leaks("OlISBZGQ", []), "eight counted letters"
    assert summary_leaks("OlISBZGq", []), "core round 5: a weak q beside two or more strong letters in one token counts (eight)"
    assert not summary_leaks("big issue is gone", []), "the documented exception: lowercase i, b, g, q in prose are not counted"
    assert summary_leaks("OlISBZGq 12", []), "a real digit next to the run counts the run"


# ---- m-b / race: a rebind has no window and a failed constructor changes nothing ---------------------------------------------------------
def test_race_a_rebind_watches_the_new_state_before_the_old_one_is_dropped(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    seen = []
    real = erp.cfg.unwatch

    def spy(state):
        seen.append(any(s is not state for s in erp.cfg._states))  # at the moment of dropping, is another state already watched?
        real(state)

    erp.cfg.unwatch = spy
    Executor(erp, pay, clock, audit, ex.pol, ex.directory, live=True, state=ControlState(), rebind=True)
    assert seen == [True], "the old state was dropped before the new one was watched"


def test_m_b_a_constructor_that_raises_leaves_the_erp_as_it_was(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    state_before, watched_before = erp.control_state, list(erp.cfg._states)
    with pytest.raises(ValueError):
        Executor(erp, pay, clock, Audit(), ex.pol, ex.directory, state=ControlState(), rebind=True)  # a second audit chain is refused
    assert erp.control_state is state_before and erp.cfg._states == watched_before


# ---- m4 / m5: the watch list and the drop counter are written under a lock ---------------------------------------------------------------
def test_m5_the_drop_counter_is_taken_under_the_audit_lock():
    audit = Audit()
    done = threading.Event()
    with audit._meta:
        t = threading.Thread(target=lambda: (audit.count_drop(), done.set()))
        t.start()
        assert not done.wait(0.3), "count_drop must take the audit lock"
    t.join(5)
    assert audit.dropped == 1


def test_m4_the_watch_list_is_changed_under_the_config_lock(cases, pol):
    c, erp, pay, clock, audit, ex = world(cases, pol, "clean_match")
    done = threading.Event()
    with erp.cfg.lock:
        t = threading.Thread(target=lambda: (erp.cfg.watch(ControlState()), done.set()))
        t.start()
        assert not done.wait(0.3), "watch must take the config lock"
    t.join(5)


# ---- M-6 restored: a shadow executor must not lift a hold; a lift that began before the kill switch lands, and the switch waits for it -----
def _lift_world(cases, pol):
    c = case_of(cases, "no_receipt")
    erp, pay, clock, audit, ex = build(c, pol)
    inv = c["invoice"]["invoice_id"]
    assert ex.place_holds(inv)
    lf = c["scenario"]["lifts"][0]
    erp.grns[lf["evidence"]["receipt_id"]] = {"po_id": c["invoice"]["po_refs"][0]}  # the evidence exists: this lift is valid
    return c, erp, pay, clock, audit, ex, inv, lf


def test_m6_a_shadow_level_executor_refuses_a_valid_lift_on_an_erp_that_has_open_holds(cases, pol):
    c, erp, pay, clock, audit, ex, inv, lf = _lift_world(cases, pol)
    shadow = Executor(erp, pay, clock, audit, ex.pol, ex.directory, level="shadow", state=ex.state)
    assert shadow.lift(inv, "no_receipt", lf["by"], "confirm_receipt", lf["evidence"]) is False
    assert erp.open_holds(inv) == ["no_receipt"], "the shadow level changes nothing"
    assert ex.lift(inv, "no_receipt", lf["by"], "confirm_receipt", lf["evidence"]) is True  # the same call is valid at the suggest level


def test_m4_the_kill_switch_waits_for_a_lift_that_is_deciding_and_a_later_lift_is_refused(cases, pol):
    c, erp, pay, clock, audit, ex, inv, lf = _lift_world(cases, pol)
    other = case_of(cases, "no_receipt", "test")
    erp.cases[other["invoice"]["invoice_id"]] = other
    erp.vendors[other["context"]["vendor"]["vendor_id"]] = other["context"]["vendor"]
    assert ex.place_holds(other["invoice"]["invoice_id"])
    lf2 = other["scenario"]["lifts"][0]
    erp.grns[lf2["evidence"]["receipt_id"]] = {"po_id": other["invoice"]["po_refs"][0]}
    entered, go, killed, result = threading.Event(), threading.Event(), threading.Event(), []
    inner = ex._fresh  # the first read inside _lift, after its kill-switch check has passed

    def slow(*a, **k):
        entered.set()
        go.wait(5)
        return inner(*a, **k)

    ex._fresh = slow
    t1 = threading.Thread(target=lambda: result.append(ex.lift(inv, "no_receipt", lf["by"], "confirm_receipt", lf["evidence"])))
    t1.start()
    assert entered.wait(5)
    t2 = threading.Thread(target=lambda: (ex.engage_kill_switch("finance_controller"), killed.set()))
    t2.start()
    assert not killed.wait(0.3), "the switch returns only after the lift that was already deciding"
    go.set()
    t1.join(5)
    t2.join(10)
    assert killed.is_set() and result == [True], "the lift that began first lands, then the switch completes"
    ex._fresh = inner
    assert (
        ex.lift(other["invoice"]["invoice_id"], "no_receipt", lf2["by"], "confirm_receipt", lf2["evidence"]) is False
    )  # started after the switch
    assert erp.open_holds(other["invoice"]["invoice_id"]) == ["no_receipt"]


# ---- M-1: no studio-internal name in a document the client reads -------------------------------------------------------------------------
CLIENT_DOCS = (
    "README.md",
    "PROMISES.md",
    "scoping.md",
    "gate_rules.md",
    "acceptance.md",
    "eval-contract.md",
    "spec_stage2.md",
    "failure_modes.md",
    "schema-asks.md",
    "CORE_COPIES.md",
)
STUDIO_WORDS = re.compile(  # the words are built from parts so this file does not contain them contiguously
    "|".join(
        [
            "eg" + r"m[\\/]",
            r"\bbi" + r"ble\b",
            r"\bthe le" + r"ad\b",
            r"\(le" + r"ad\b",
            r"\ble" + r"ad,",
            r"\bow" + r"ner\b",
            "HARD R" + "ULE",
            r"\bBho" + r"vix\b",
            r"\bhand" + r"off\b",
            r"\bstu" + r"dio\b",
            "session scr" + "atch",
            r"\bR\d{2,3}\b",
        ]
    ),
    re.IGNORECASE,
)


def test_m1_client_visible_documents_carry_no_studio_internal_name():
    hits = []
    for name in (*CLIENT_DOCS, "../../README.md"):
        p = ROOT / name
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for m in STUDIO_WORDS.finditer(line):
                hits.append(f"{name}:{i}: {m[0]}")
    assert not hits, hits[:20]


# ---- M-2: the liability sentence is the mandated one or absent; insurance is never claimed --------------------------------------------
def test_m2_no_document_promises_insurance_or_paraphrases_the_liability_limit():
    text = "\n".join((ROOT / n).read_text(encoding="utf-8") for n in CLIENT_DOCS if (ROOT / n).exists())
    assert not re.search(r"insurance", text, re.IGNORECASE) or "own insurance position" in text
    assert "reviewed by counsel" not in text


# ---- every pointer in core_copies.json names a core PR (the sync tool downgrades a pin disagreement only for an open core PR) ---------------
def test_m3_each_core_copy_row_names_the_open_core_pr():
    pins = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    assert pins["core_pr"] == 50 and all(p.get("core_pr") == 50 for p in pins["files"].values())
    assert len(pins["core_commit"]) == 40


def test_m3_the_not_copies_table_lists_executor_py():
    assert "src/apexc/executor.py" in (ROOT / "CORE_COPIES.md").read_text(encoding="utf-8")


# ---- a negative test per identity, generated from the policy ------------------------------------------------------------------------------
def test_each_identity_is_denied_every_write_it_does_not_hold(pol):
    ops = sorted({op for r in pol["identities"].values() for op in r["write"]})
    assert len(ops) >= 10 and len(pol["identities"]) >= 8
    for ident, rights in pol["identities"].items():
        for op in ops:
            if op in rights["write"]:
                authorize_op(ident, op, pol)  # held: allowed
            else:
                with pytest.raises(PermissionError):
                    authorize_op(ident, op, pol)
    with pytest.raises(PermissionError):
        authorize_op("nobody", ops[0], pol)

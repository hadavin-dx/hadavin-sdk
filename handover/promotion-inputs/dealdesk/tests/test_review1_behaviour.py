"""Behavioural regression tests for the first code review and design review of PR #3 (head 1479888). Each test uses only APIs that exist at 1479888, so
`mutation/prefix_proof.py` can run THIS FILE against the old source and show each test FAIL there and PASS here (per-test fail-before/pass-after).
Tests that need an API added by the fixes are in test_review1_newapi.py (they fail on the old code by a missing API, which proves less; labelled so)."""

import inspect
import json
import os
import subprocess
import sys
import threading
import time

import pytest
from engine_kit import Kit, mk_deal

from dealdesk import gate_rules as g
from dealdesk import guards
from dealdesk import inbox as ib
from dealdesk.handler import make_handler

AG, DW, EX = "agent_runtime", "draft_writer", "commit_executor"


def within(seconds, fn, *a):
    """Run fn in a thread; fail if it has not finished in `seconds` (a regex that backtracks cannot be interrupted, so it is abandoned, not killed)."""
    box = {}
    th = threading.Thread(target=lambda: box.setdefault("out", fn(*a)), daemon=True)
    t0 = time.perf_counter()
    th.start()
    th.join(seconds)
    assert not th.is_alive(), f"did not finish in {seconds} s"
    return box["out"], time.perf_counter() - t0


PCT_TIMEOUT_S = 30  # generous: only a pattern that is really super-linear (minutes) misses it, even on a loaded machine


def percent_pattern_in_child(shape: str) -> None:
    """Run every match of the compiled percent pattern over `shape` in a CHILD process with a hard timeout. The regex engine holds the GIL, so a thread
    cannot time a catastrophic pattern out (a mutant of the pattern once froze the whole suite for half an hour); a killed child is a failed test, fast."""
    code = (
        "import sys; sys.meta_path=[f for f in sys.meta_path if 'editable' not in repr(f).lower()]; sys.path[:0]=[sys.argv[1]]; "
        "from dealdesk import gate_rules as g; list(g._PCT.finditer(sys.stdin.read()))"
    )
    src = os.path.dirname(os.path.dirname(g.__file__))
    try:
        r = subprocess.run(
            [sys.executable, "-c", code, src], input=shape, text=True, capture_output=True, timeout=PCT_TIMEOUT_S, check=False
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"the percent pattern did not finish in {PCT_TIMEOUT_S} s: not linear")
    assert r.returncode == 0, r.stderr[-300:]


def _k():
    return Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works", seats=40)])


# ---------------------------------------------------------------- B2 / B1: one message must not freeze the process
@pytest.mark.parametrize("shape", ["1" * 20_000, "1" * 50_000, "1," * 25_000])
def test_traceability_is_linear_on_hostile_runs(shape):
    out, took = within(5, g.traceability, shape)
    assert out["status"] == "hand_back" and took < 2.0


def test_the_inbox_pipeline_survives_a_flood_message_and_the_next_message_still_runs():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    flood = {
        "msg_id": "flood",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works " + "1" * 20_000,
    }
    good = {
        "msg_id": "good",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works wants 15% off.",
    }

    def run():
        for m in (flood, good):
            if inbox.receive("t-a", m) is not None:
                inbox.process("t-a", m["msg_id"])
        return inbox.ledger.ids("t-a")

    ids, took = within(8, run)
    assert ids.get("good") == "processed" and ids.get("flood") in (None, "rejected", "abstained") and took < 4.0
    assert ids.get("flood") != "processed"


def test_an_oversize_message_is_refused_before_any_ack():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    big = {"msg_id": "big", "kind": "request", "requester_id": "p-ae-01", "deal_id": "deal-7001", "text": "x" * 70_000}
    assert (
        inbox.receive("t-a", big) is None and inbox.ledger.ids("t-a") == {}
    )  # nothing was acked, nothing stored: the sender still holds it


def test_a_text_over_the_handler_limit_ends_rejected_without_being_scanned():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    m = {
        "msg_id": "long",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works " + "1" * 15_000,
    }
    assert inbox.receive("t-a", m) is not None
    out, took = within(5, inbox.process, "t-a", "long")
    assert out == "rejected" and took < 2.0 and k.store.names("quotes") == []


# ---------------------------------------------------------------- M1: the percent grammar is strict
@pytest.mark.parametrize(
    "text",
    [
        "Zephyr Works wants 1e2% off",
        "Zephyr Works wants 0x14% off",
        "Zephyr Works wants 10-20% off",
        "wants x15% off",
        "wants 15abc% off",
    ],
)
def test_percent_tokens_with_letters_or_ranges_are_an_invalid_figure_never_repaired(text):
    r = g.traceability(text)
    assert (r["status"], r["reason"], r["discount_bps"]) == ("hand_back", "invalid_number", None)


# ---------------------------------------------------------------- B3: egress is wired and hardened
def test_egress_check_folds_look_alike_domains_and_refuses_non_strings():
    cyr = chr(0x435)  # Cyrillic small ie, looks like Latin e
    assert "UNLISTED_LINK" in guards.egress_check(f"pay at {cyr}vil.example/pay", "a@example.com", "a@example.com")
    assert guards.egress_check(None, "a@example.com", "a@example.com") != []
    assert guards.egress_check(["x"], "a@example.com", "a@example.com") != []
    assert guards.egress_check(b"bytes", "a@example.com", "a@example.com") != []


def test_a_draft_with_an_unlisted_link_in_it_is_refused_and_nothing_is_drafted():
    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works evil.example/pay", seats=40)])
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    out = k.desk.draft_quote(DW, q)
    assert out["status"] == "denied" and out.get("rule") == "R-DEALDESK-092"
    assert k.desk.status(AG, q)["state"] == "approved" and k.store.names("drafts") == []


# ---------------------------------------------------------------- M3: least privilege is exercised with the real identity
def test_draft_and_commit_read_the_systems_of_record_as_their_own_identities():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.ports.log.entries.clear()
    k.desk.draft_quote(DW, q)
    assert {e["who"] for e in k.desk.ports.log.entries} == {"draft_writer"}
    k.desk.ports.log.entries.clear()
    k.ex.commit(EX, q, dry_run=False)
    assert {e["who"] for e in k.desk.ports.log.entries} == {"commit_executor"}


# ---------------------------------------------------------------- M4: configuration is frozen at start-up
def test_editing_the_worlds_matrix_after_start_does_not_weaken_the_running_engine():
    k = _k()
    k.world.matrix["cells"]["discount"]["s"]["d1"] = {}  # someone edits the config in memory: 15% would need nobody
    r = k.propose("deal-7001", {"discount_bps": 1500})
    assert r["steps"] == [["commercial", "sales_manager"]] and r["tier"] == "human"


def test_editing_the_executor_caps_after_start_does_not_change_the_running_engine():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    k.world.policy["executor"]["per_action_cap_minor"]["USD"] = (
        1  # a hostile lowering would block; a hostile RAISING would unblock: neither may act
    )
    assert k.ex.commit(EX, q, dry_run=False)["outcome"] == "applied"


def test_engine_objects_cannot_be_rebound():
    k = _k()
    for obj, attr in ((k.desk, "w"), (k.ex, "d"), (k.desk, "ports")):
        with pytest.raises(AttributeError):
            setattr(obj, attr, object())


# ---------------------------------------------------------------- M5: the kill switch survives a restart and is tenant-scoped
def test_the_kill_switch_is_persistent_not_a_process_attribute():
    from dealdesk.executor import Executor

    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    k.ex.set_kill_switch("kill_switch_operator", True)
    fresh = Executor(k.desk)  # a restarted process: a new executor object over the same store
    assert fresh.commit(EX, q, dry_run=False) == {"outcome": "held", "code": "KILL_SWITCH"}
    other = _k()  # another tenant's world is a separate store: its switch is its own
    assert other.store.get("logs", "kill-switch") is None


def test_the_kill_switch_also_holds_drafting():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.ex.set_kill_switch("kill_switch_operator", True)
    assert k.desk.draft_quote(DW, q) == {"status": "held", "code": "KILL_SWITCH"}
    assert k.desk.status(AG, q)["state"] == "approved"


# ---------------------------------------------------------------- M6: the inbox never drops or strands a message
def test_the_same_msg_id_with_a_different_body_is_recorded_not_dropped():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    a = {
        "msg_id": "m1",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works wants 15% off.",
    }
    b = {**a, "text": "Zephyr Works wants 5% off."}
    assert inbox.receive("t-a", a) is not None and inbox.receive("t-a", b) is not None
    states = inbox.ledger.ids("t-a")
    assert len(states) == 2 and sorted(states.values()) == [
        "received",
        "rejected",
    ]  # the second body is its own rejected row (id_reuse)
    assert json.loads(inbox.ledger.get("t-a", "m1")["raw"])["text"] == a["text"]  # the first body is untouched
    rej = next(i for i, s in states.items() if s == "rejected")
    assert inbox.ledger.get("t-a", rej)["reason"] == "id_reuse"


def test_a_handler_that_returns_a_non_terminal_state_is_dead_lettered_not_trusted():
    inbox = ib.Inbox(ib.MemoryLedger(), lambda m: ("received", None))
    inbox.receive("t-a", {"msg_id": "m1"})
    assert inbox.process("t-a", "m1") == "dead_lettered"
    inbox.receive("t-a", {"msg_id": "m2"})
    inbox.ledger.set_state("t-a", "m2", "processing", None)  # a crash left it here
    assert "m2" in ib.reconcile(inbox.ledger, "t-a", {"m1", "m2"}).get("open_ids", [])


# ---------------------------------------------------------------- M7: nothing caller-supplied is stored unbounded
def test_a_decision_with_a_huge_approval_id_is_recorded_short():
    k = _k()
    raw = {"approval_id": "apr-" + "x" * 200_000}
    if (
        "authenticated_person" in inspect.signature(k.desk.record_decision).parameters
    ):  # the old source had the default, the new one requires it
        k.desk.record_decision("approver_commercial", raw, None)
    else:
        k.desk.record_decision("approver_commercial", raw)
    rec = k.store.get("decisions", "00000000")
    assert len(json.dumps(rec)) < 2_000


# ---------------------------------------------------------------- audit before the act (design M1)
def test_a_crash_between_the_commit_record_and_the_state_change_leaves_an_audit_trace(monkeypatch):
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    orig = type(k.desk)._set_state

    def boom(self, quote, state, reason=None):
        if state == "committed":
            raise RuntimeError("crash after the commit record was written")
        return orig(self, quote, state, reason)

    monkeypatch.setattr(type(k.desk), "_set_state", boom)
    with pytest.raises(RuntimeError):
        k.ex.commit(EX, q, dry_run=False)
    events = [k.store.get("audit", n) for n in k.store.names("audit")]
    assert any("commit" in json.dumps(e) and e["kind"] != "quote_state" for e in events), "the commit left no audit trace"
    assert (
        k.store.get("commits", f"day-USD-{k.clock.today()}")["count"] == 1
    )  # and the act did happen: the trace is what makes it findable


# ---------------------------------------------------------------- design M2: the handler's two writes are crash-safe
def test_a_crash_between_propose_and_request_approval_is_repaired_by_the_retry(monkeypatch):
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    real = type(k.desk).request_approval
    calls = {"n": 0}

    def flaky(self, who, quote_id):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("crash after the quote was created, before the approval request")
        return real(self, who, quote_id)

    monkeypatch.setattr(type(k.desk), "request_approval", flaky)
    msg = {
        "msg_id": "m1",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works wants 15% off.",
    }
    inbox.receive("t-a", msg)
    assert inbox.process("t-a", "m1") == "processed"
    q = k.store.get("quotes", k.store.names("quotes")[0])
    assert len(q["approvals"]) == 1 and k.open_approval(q["quote_id"]) is not None, (
        "the quote was left pending with no approval request"
    )


# ---------------------------------------------------------------- minor: a date in the request is never silently ignored
def test_a_validity_date_in_the_request_is_handed_back_not_ignored():
    k = _k()
    h = make_handler(k.desk)
    out = h({"msg_id": "m1", "kind": "request", "tenant_id": "t-a", "requester_id": "p-ae-01", "deal_id": "deal-7001",
             "text": "Zephyr Works wants 15% off, quote valid until 2026-13-45."})  # fmt: skip
    assert out[0] == "abstained" and k.store.names("quotes") == []


# ---------------------------------------------------------------- second pass (priority review): backstops and the newest core behaviours
def test_the_scanners_have_a_backstop_for_text_nobody_bounded():
    big = "1" * 1_000_000
    out, took = within(5, g.traceability, big)
    assert (out["status"], out["reason"]) == ("hand_back", "text_too_long") and took < 1.0
    with pytest.raises(Exception, match="too long"):
        g.names_in_text(big, ["Zephyr Works"])


def test_an_account_name_that_mixes_scripts_inside_a_word_is_refused_on_a_quote():
    spoof = "Zephyr W" + chr(0x43E) + "rks"  # Cyrillic o inside a Latin word
    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", spoof, seats=40)])
    out = k.propose("deal-7001", {"discount_bps": 1500})
    assert out["status"] == "denied" and out["rule"] == "R-DEALDESK-088" and "mixed_script" in out["findings"]


def test_an_unreadable_kill_switch_holds_commit_and_draft(monkeypatch):
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    real = k.store.get

    def broken(kind, name, default=None):
        if kind == "logs" and name == "kill-switch":
            raise OSError("store unreadable")
        return real(kind, name, default)

    monkeypatch.setattr(k.store, "get", broken)
    assert k.ex.commit(EX, q, dry_run=False) == {"outcome": "held", "code": "KILL_SWITCH"}  # fail closed, not open
    assert k.desk.draft_quote(DW, q) == {"status": "held", "code": "KILL_SWITCH"}


def test_the_same_mailbox_identity_is_one_person_for_separation_of_duties():
    k = _k()
    me = next(p for p in k.world.directory if p["person_id"] == "p-ae-01")
    sm = next(p for p in k.world.directory if p["person_id"] == "p-sm-01")
    sm["email"] = me["email"].replace("@", "+boss@")  # a plus-alias of the requester's own mailbox
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    assert k.decide(k.open_approval(q), "p-sm-01")["status"] == "decision_not_accepted"
    assert k.decide(k.open_approval(q), "p-sm-02")["status"] == "accepted"
    k2 = _k()
    q2 = k2.propose("deal-7001", {"discount_bps": 1500, "sla_tier": "enhanced"})["quote_id"]
    k2.desk.request_approval(AG, q2)
    k2.decide(k2.open_approval(q2), "p-sm-01")
    lc = next(p for p in k2.world.directory if p["person_id"] == "p-lc-01")
    lc["email"] = (
        chr(0x440) + next(p for p in k2.world.directory if p["person_id"] == "p-sm-01")["email"][1:]
    )  # Cyrillic first letter: a disguised copy
    assert k2.decide(k2.open_approval(q2), "p-lc-01", identity="approver_legal")["status"] == "decision_not_accepted"


def test_a_mailbox_identity_that_collides_after_approval_voids_the_quote_at_draft_time():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    me = next(p for p in k.world.directory if p["person_id"] == "p-ae-01")
    sm = next(p for p in k.world.directory if p["person_id"] == "p-sm-01")
    sm["email"] = me["email"].replace("@", "+x@")  # the directory changes: the approver is now the requester's own mailbox
    out = k.desk.draft_quote(DW, q)
    assert out["status"] == "denied" and out["rule"] == "R-DEALDESK-087"
    k2 = _k()
    q2 = k2.propose("deal-7001", {"discount_bps": 1500, "sla_tier": "enhanced"})["quote_id"]
    k2.desk.request_approval(AG, q2)
    k2.approve_all(q2, {"commercial": "p-sm-01", "legal": "p-lc-01"})
    lc = next(p for p in k2.world.directory if p["person_id"] == "p-lc-01")
    lc["email"] = next(p for p in k2.world.directory if p["person_id"] == "p-sm-01")["email"]  # two approvers, one mailbox
    assert k2.desk.draft_quote(DW, q2)["rule"] == "R-DEALDESK-087"


@pytest.mark.parametrize("shape", ["1" * 50_000, "1," * 50_000, "1." * 100_000])
def test_the_percent_pattern_itself_is_linear_below_the_backstop(shape):
    """The text backstop would hide a slow pattern for long inputs; this calls the compiled pattern directly (child process, hard timeout)."""
    percent_pattern_in_child(shape)


# ---------------------------------------------------------------- burst scaling: the per-message name scan must not walk every account
def test_name_scan_work_per_message_does_not_grow_with_the_number_of_accounts(monkeypatch):
    """A 10,000-message burst took 27x as long as 1,000 because each message compared against EVERY account name. Count the whole-name tests one message
    costs with 1,500 accounts: it must be a handful (candidates), not 1,500."""
    from dealdesk import desk_rules as dr

    deals = [mk_deal(f"deal-{i:05d}", f"acct-{i:05d}", f"Name{i:05d} Works", seats=40) for i in range(1500)]
    k = Kit(deals=deals)
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    calls = {"n": 0}
    real_a, real_b = g._whole_name, dr._whole

    def count_a(*a):
        calls["n"] += 1
        return real_a(*a)

    def count_b(*a):
        calls["n"] += 1
        return real_b(*a)

    monkeypatch.setattr(g, "_whole_name", count_a)
    monkeypatch.setattr(dr, "_whole", count_b)
    msg = {
        "msg_id": "m1",
        "kind": "request",
        "requester_id": "p-ae-01",
        "deal_id": "deal-00007",
        "text": "Hi, Name00007 Works would like 15% off.",
    }
    inbox.receive("t-a", msg)
    inbox.process("t-a", "m1")
    assert calls["n"] < 40, f"{calls['n']} whole-name tests for ONE message with 1,500 accounts"

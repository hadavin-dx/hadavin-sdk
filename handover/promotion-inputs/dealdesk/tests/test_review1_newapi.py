"""Tests for the behaviour added by the fixes for the first code review and design review of PR #3, through APIs that did not exist at 1479888
(rate cap on the inbox, deadline, authenticated channel, public keys only, sealed objects, intent/outcome audit, recover, read cap, send_reply).
Against 1479888 they fail for a missing API, which proves less than test_review1_behaviour.py; the pre-fix proof labels them as such."""

import hashlib
import json
import time
from pathlib import Path

import pytest
from engine_kit import D, Kit, mk_deal

from dealdesk import canon
from dealdesk import inbox as ib
from dealdesk.core_copy.approvals_signed import ApprovalVerifier
from dealdesk.desk import Desk
from dealdesk.errors import Malformed, ReadThrottled
from dealdesk.guards import RateCap
from dealdesk.handler import make_handler
from dealdesk.limits import Limits

AG, DW, EX = "agent_runtime", "draft_writer", "commit_executor"
REQ = {"kind": "request", "requester_id": "p-ae-01", "deal_id": "deal-7001", "text": "Zephyr Works wants 15% off."}


def _k(**kw):
    return Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works", seats=40)], **kw)


def _pending(k):
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    return q, k.open_approval(q)


# ---------------------------------------------------------------- rate cap, deadline, size, reserved key, id length
def test_the_inbox_rate_cap_refuses_before_the_ack_and_counts_it():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk), rate_cap=RateCap(2, 1), now_s=lambda: 0.0)
    receipts = [inbox.receive("t-a", {**REQ, "msg_id": f"m{i}"}) for i in range(4)]
    assert [r is not None for r in receipts] == [True, True, False, False]
    assert inbox.refusals["rate_limited"] == 2 and set(inbox.ledger.ids("t-a")) == {
        "m0",
        "m1",
    }  # refused = not acked = the sender retries


def test_a_stalled_handler_is_dead_lettered_at_the_deadline_and_the_next_message_runs():
    def handler(m):
        if m["msg_id"] == "slow":
            time.sleep(1.0)
        return "processed", None

    inbox = ib.Inbox(ib.MemoryLedger(), handler, limits=Limits(handler_deadline_s=0.2))
    for mid in ("slow", "fast"):
        inbox.receive("t-a", {"msg_id": mid})
    t0 = time.perf_counter()
    assert inbox.process("t-a", "slow") == "dead_lettered" and inbox.ledger.get("t-a", "slow")["reason"] == "deadline"
    assert inbox.process("t-a", "fast") == "processed" and time.perf_counter() - t0 < 0.9


def test_reserved_key_overlong_id_and_bad_auth_are_refused_before_the_ack():
    inbox = ib.Inbox(ib.MemoryLedger(), lambda m: ("processed", None))
    assert inbox.receive("t-a", {"msg_id": "m1", "_auth": {"person_id": "p-sm-01", "identity": "approver_commercial"}}) is None
    assert inbox.receive("t-a", {"msg_id": "x" * 129}) is None
    assert inbox.receive("t-a", {"msg_id": "m2"}, auth={"person_id": "p", "identity": "i", "extra": 1}) is None
    assert inbox.ledger.ids("t-a") == {} and inbox.refusals["malformed"] == 3


def test_limits_are_validated():
    for bad in ({"max_message_bytes": 0}, {"max_text_chars": True}, {"handler_deadline_s": 0}, {"max_clauses": -1}):
        with pytest.raises(ValueError):
            Limits(**bad)


# ---------------------------------------------------------------- the approver identity comes from the authenticated channel
def _decision_msg(k, approval, approver, **body):
    return {"msg_id": "d1", "kind": "decision", "decision": k.signed(approval, approver), **body}


def test_a_decision_is_recorded_under_the_channel_identity_never_the_body_identity():
    k = _k()
    q, a = _pending(k)
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    forged = _decision_msg(k, a, "p-sm-01", identity="approver_legal")  # the body claims another lane; it is ignored
    assert inbox.receive("t-a", forged, auth={"person_id": "p-sm-01", "identity": "approver_commercial"}) is not None
    assert inbox.process("t-a", "d1") == "processed" and k.desk.status(AG, q)["state"] == "approved"


def test_a_decision_without_or_with_the_wrong_channel_identity_is_not_accepted():
    for auth, want in (
        (None, "rejected"),
        (
            {"person_id": "p-sm-02", "identity": "approver_commercial"},
            "abstained",
        ),  # authenticated as someone else than the signer
        ({"person_id": "p-sm-01", "identity": "approver_legal"}, "abstained"),  # wrong lane identity for the step
    ):
        k = _k()
        q, a = _pending(k)
        inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
        inbox.receive("t-a", _decision_msg(k, a, "p-sm-01"), auth=auth)
        assert inbox.process("t-a", "d1") == want and k.desk.status(AG, q)["state"] == "pending", auth


# ---------------------------------------------------------------- keys: the engine holds public keys only
def test_the_engine_holds_no_private_key_and_its_verifier_cannot_mint():
    k = _k()
    _q, a = _pending(k)
    k.decide(a, "p-sm-01")
    priv = k.device("p-sm-01")._key.private_bytes_raw()
    blob = (
        json.dumps(k.store.all_items(), sort_keys=True, default=str)
        + repr(k.desk.__dict__)
        + repr(k.keys._k)
        + repr(k.ex.__dict__)
    )
    assert priv.hex() not in blob and str(priv) not in blob
    assert all(len(pub) == 32 for keys in k.keys._k.values() for _alg, pub in keys.values())
    assert ApprovalVerifier.can_mint is False and not hasattr(k.keys, "sign")


def test_a_tampered_args_hash_and_an_unregistered_key_are_not_accepted():
    k = _k()
    q, a = _pending(k)
    assert (
        k.decide(a, "p-sm-01", args_hash="0" * 64)["status"] == "decision_not_accepted"
    )  # signed, but over a hash that does not match the fields
    assert k.decide(a, "p-sm-01", kid="k9")["status"] == "decision_not_accepted"  # a key that is not in the directory
    k.keys.revoke("p-sm-01", k.device("p-sm-01").key_id)
    assert k.decide(a, "p-sm-01")["status"] == "decision_not_accepted"  # revoked
    assert k.desk.status(AG, q)["state"] == "pending"


def test_an_unknown_decision_value_is_refused_before_anything_changes_state():
    k = _k()
    _q, a = _pending(k)
    assert k.decide(a, "p-sm-01", decision="maybe")["status"] == "decision_not_accepted"
    assert k.store.get("approvals", a["approval_id"])["state"] == "open"  # never marked decided and put back


# ---------------------------------------------------------------- sealed objects, frozen config
def test_the_config_copy_is_read_only_and_a_rebinding_trick_is_caught_at_the_re_check():
    k = _k()
    with pytest.raises(TypeError):
        k.desk.matrix["cells"]["margin"] = {}
    q, _a = _pending(k)
    k.approve_all(q, {"commercial": "p-sm-01"})
    object.__setattr__(
        k.desk, "matrix", {**k.desk.matrix, "approval_ttl_hours": 10**6}
    )  # hostile in-process rebinding (not preventable in one process)
    assert k.desk.draft_quote(DW, q) == {
        "status": "denied",
        "rule": "R-DEALDESK-040",
        "why": "matrix or policy no longer matches the hashes taken at start-up",
    }


# ---------------------------------------------------------------- audit before the act, with reconcile
def test_open_intents_lists_an_act_whose_outcome_was_never_recorded(monkeypatch):
    k = _k()
    q, _a = _pending(k)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    monkeypatch.setattr(
        Desk,
        "_outcome",
        lambda self, seq, op, ref, result: (_ for _ in ()).throw(RuntimeError("crash before the outcome was written")),
    )
    with pytest.raises(RuntimeError):
        k.ex.commit(EX, q, dry_run=False)
    monkeypatch.undo()
    open_ = k.desk.open_intents("reconciler")
    assert any(i["op"] == "commit_quote" and i["ref"] == q for i in open_)
    assert k.desk.audit.verify()


def test_a_completed_act_leaves_no_open_intent_and_the_trail_reads_intent_then_outcome():
    k = _k()
    q, _a = _pending(k)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    k.ex.commit(EX, q, dry_run=False)
    assert k.desk.open_intents("reconciler") == []
    kinds = [k.store.get("audit", n)["kind"] for n in k.store.names("audit")]
    first_commit = next(i for i, n in enumerate(k.store.names("audit")) if k.store.get("audit", n).get("op") == "commit_quote")
    assert kinds[first_commit] == "intent"


# ---------------------------------------------------------------- recover re-offers rows a crash left open
def test_recover_processes_rows_left_received_or_processing_and_reconcile_names_them():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk), queue_bound=2)
    for i in range(5):
        inbox.receive("t-a", {**REQ, "msg_id": f"m{i}", "text": f"Zephyr Works wants {10 + i}% off."})
    inbox.ledger.set_state("t-a", "m1", "processing", None)  # a crash mid-handler
    rep = ib.reconcile(inbox.ledger, "t-a", {f"m{i}" for i in range(5)})
    assert rep["non_terminal"] == 5 and rep["open_ids"] == [f"m{i}" for i in range(5)]
    assert inbox.recover("t-a") == 5
    rep = ib.reconcile(inbox.ledger, "t-a", {f"m{i}" for i in range(5)})
    assert rep["non_terminal"] == 0 and rep["counts"]["processed"] + rep["counts"]["abstained"] == 5


# ---------------------------------------------------------------- the read cap and the reply path are wired
def test_the_read_only_role_has_a_request_rate_cap():
    k = _k(desk_kw={"read_cap": RateCap(3, 1)})
    with pytest.raises(ReadThrottled):
        for _ in range(10):
            k.desk.ports.get_deal(AG, "deal-7001")


def test_replies_go_to_the_requester_only_through_the_egress_check():
    k = _k()
    ok = k.desk.send_reply(AG, "p-ae-01", "Request received. Approval needed from: sales manager.")
    assert ok["status"] == "sent" and ok["to"] == "p-ae-01@example.com"
    bad = k.desk.send_reply(AG, "p-ae-01", "see https://evil.example/pay or mail boss@evil.example")
    assert bad["status"] == "refused" and {"UNLISTED_LINK", "UNLISTED_ADDRESS"} <= set(bad["violations"])
    assert k.desk.send_reply(AG, "p-nobody", "hello")["status"] == "refused"
    assert k.desk.send_reply(AG, "p-ae-01", None)["status"] == "refused"
    assert len(k.store.names("outbox")) == 1


def test_the_rep_reply_names_roles_never_rule_ids_zones_or_figures():
    k = _k()
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    inbox.receive("t-a", {**REQ, "msg_id": "m1", "text": "Zephyr Works wants 90% off."})
    inbox.receive("t-a", {**REQ, "msg_id": "m2"})
    for mid in ("m1", "m2"):
        inbox.process("t-a", mid)
    texts = [k.store.get("outbox", n)["text"] for n in k.store.names("outbox")]
    assert len(texts) == 2 and "sales manager" in texts[1]
    assert all(
        not any(w in t.lower() for w in ("r-dealdesk", "margin", "floor", "cogs", "below_floor", "thin", "healthy"))
        for t in texts
    )


def test_claims_over_the_message_cap_clauses_and_attachment_limits_are_rejected():
    k = _k()
    h = make_handler(k.desk)
    base = {
        "msg_id": "m",
        "kind": "request",
        "tenant_id": "t-a",
        "requester_id": "p-ae-01",
        "deal_id": "deal-7001",
        "text": "Zephyr Works wants 15% off.",
    }
    for bad in (
        {"attachments": [{"text": "x"}] * 11},
        {"attachments": [{"text": "x" * 10_001}]},
        {"clauses": ["liability_cap_2x"] * 21},
    ):
        with pytest.raises(Malformed):
            h({**base, **bad})


# ---------------------------------------------------------------- the promotion table is true
def test_core_copies_json_pins_match_the_copied_files_after_reversing_the_import_rewrite():
    table = json.loads((D / "core_copies.json").read_text(encoding="utf-8"))
    assert table["core_pr"] and table["files"]
    for demo_path, row in table["files"].items():
        data = (Path(D) / demo_path).read_bytes().replace(b"\r\n", b"\n")
        for old, new in row.get("import_rewrite", []):
            data = data.replace(new.encode(), old.encode())
        assert hashlib.sha256(data).hexdigest() == row["core_sha256"], demo_path
    md = (D / "CORE_COPIES.md").read_text(encoding="utf-8")
    assert all(p in md for p in table["files"]) and "TEMPORARY" in md


def test_canon_decision_args_hash_covers_every_bound_field():
    f = {k: "x" for k in canon.BOUND_FIELDS}
    base = canon.decision_args_hash(f)
    assert all(canon.decision_args_hash({**f, k: "y"}) != base for k in canon.BOUND_FIELDS)


# ---------------------------------------------------------------- small checks that pin individual lines
def test_status_reads_under_the_store_lock(monkeypatch):
    k = _k()
    q, _a = _pending(k)
    held = []
    real = Desk._qget

    def spy(self, quote_id):
        held.append(self.store.lock._is_owned())  # is this thread holding the store lock while the quote is read?
        return real(self, quote_id)

    monkeypatch.setattr(Desk, "_qget", spy)
    k.desk.status(AG, q)
    assert held == [True]


def test_a_decision_is_verified_with_the_verifier_identity_not_the_agent_identity():
    k = _k()
    _q, a = _pending(k)
    k.desk.ports.log.entries.clear()
    k.decide(a, "p-sm-01")
    assert {e["who"] for e in k.desk.ports.log.entries} == {"decision_service"}


def test_frozen_config_has_no_mutable_list_left_and_the_ports_refuse_rebinding():
    k = _k()
    with pytest.raises(AttributeError):
        k.desk.matrix["lanes"]["commercial"].append("ceo")
    with pytest.raises(AttributeError):
        k.desk.ports._w = object()


def test_decision_fields_are_length_bounded_before_use():
    k = _k()
    _q, a = _pending(k)
    good = k.signed(a, "p-sm-01")
    assert k.desk._shape_ok(good)
    for field in ("deal_id", "terms_hash", "approver_id", "lane", "key_id", "ts"):
        assert not k.desk._shape_ok({**good, field: "x" * 5000}), field
    assert not k.desk._shape_ok({**good, "sig": "0" * 5000}) and not k.desk._shape_ok({**good, "epoch": True})


def test_egress_and_scan_inputs_are_length_bounded():
    from dealdesk import guards, textnorm

    assert guards.egress_check("x" * 5000, "a@example.com", "a@example.com") == ["TEXT_TOO_LONG"]
    with pytest.raises(Malformed):
        textnorm.views("x" * 20_001)


def test_the_draft_audit_trail_starts_with_an_intent():
    k = _k()
    q, _a = _pending(k)
    k.approve_all(q, {"commercial": "p-sm-01"})
    k.desk.draft_quote(DW, q)
    ev = [k.store.get("audit", n) for n in k.store.names("audit")]
    i = next(i for i, e in enumerate(ev) if e.get("op") == "quote_draft")
    assert ev[i]["kind"] == "intent" and any(e.get("intent_seq") == ev[i]["seq"] for e in ev)


def test_a_signed_request_time_that_differs_from_the_record_is_not_accepted():
    k = _k()
    _q, a = _pending(k)
    assert (
        k.decide(a, "p-sm-01", requested_at="2026-11-09T08:00:00Z")["status"] == "decision_not_accepted"
    )  # signed, but for another request time
    assert k.store.get("decisions", "00000000")["rule_id"] == "R-DEALDESK-085"


# ---------------------------------------------------------------- second pass: the newest core behaviours
def test_the_recipient_must_be_the_identical_string_and_a_look_alike_is_its_own_violation():
    from dealdesk import guards

    cyr = "a@" + "ex" + chr(0x430) + "mple.com"  # Cyrillic a in the domain
    assert guards.egress_check("hello", "a@example.com", "a@example.com") == []
    assert "RECIPIENT_LOOKALIKE" in guards.egress_check("hello", cyr, "a@example.com")
    assert "RECIPIENT_VARIANT" in guards.egress_check("hello", "A@Example.com", "a@example.com")
    assert "RECIPIENT_NOT_REQUESTER" in guards.egress_check("hello", "b@example.com", "a@example.com")


def test_a_rep_reply_that_carries_the_cost_per_seat_or_too_many_digits_is_refused():
    k = _k()
    cost = k.world.book["plans"]["business"]["USD"]["cogs_seat"]
    assert k.desk.send_reply(AG, "p-ae-01", "Approval needed from: sales manager.", (str(cost),))["status"] == "sent"
    leak = k.desk.send_reply(AG, "p-ae-01", f"Our cost per seat is {cost}.", (str(cost),))
    assert leak["status"] == "refused" and leak["violations"] == ["LEAK_PROTECTED_VALUE"]
    assert (
        k.desk.send_reply(AG, "p-ae-01", "ref 123 456 789 012 345", ())["status"] == "refused"
    )  # digit budget (payments profile)
    assert len(k.store.names("outbox")) == 1


def test_a_reply_that_would_carry_an_internal_figure_is_not_sent_by_the_handler():
    k = Kit(
        deals=[mk_deal("deal-7001", "acct-7001", "Zephyr 12000 Works", seats=40)]
    )  # 12000 is the business USD cost per seat (minor units)
    assert k.world.book["plans"]["business"]["USD"]["cogs_seat"] == 12000
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    inbox.receive("t-a", {**REQ, "msg_id": "m1", "text": "Zephyr 12000 Works wants 15% off."})
    assert inbox.process("t-a", "m1") == "processed"  # the request itself is handled
    assert k.store.names("outbox") == []  # but the reply naming the account would carry the cost figure: refused, not sent
    refused = [k.store.get("audit", n) for n in k.store.names("audit") if k.store.get("audit", n)["kind"] == "egress_refused"]
    assert refused and refused[0]["violations"] == ["LEAK_PROTECTED_VALUE"]

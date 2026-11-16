"""Findings of design/code review 8 (money and approval path): SoD folding, reservation flooding, the signer kind, who-approved, audit of refusals,
required identity, shape limits, ledger overlap on shipping, typed lock timeout, egress hardening, config validation, the store contract."""

import json
import sqlite3
import sys
import threading
import time
from pathlib import Path

import pytest
import wgkit as kit

from refunds import config, desk, guards, textnorm
from refunds.approval import ApprovalIssuer, ApprovalVerifier, norm
from refunds.config import LIMITS
from refunds.signers import HmacSigner, make_signer
from refunds.store import Store, StoreBusy
from refunds.storeport import StorePort
from refunds.writegate import WriteGate, hash_request

DATA = Path(__file__).resolve().parents[1] / "demo_only" / "data"
APPROVER = "lead@desk.example"
LOOKALIKES = {
    "combining acute": "\u0301",
    "variation selector": "\ufe0f",
    "hangul filler": "\u3164",
    "no-break space": "\u00a0",
    "zero-width space": "\u200b",
    "ideographic space": "\u3000",
}


def _audit(store):
    return [(r["event"], json.loads(r["detail"])) for r in store.audit_rows()]


# ------------------------------------------------------------------------------------------------ code M1: SoD folds what the scanners fold
@pytest.mark.parametrize("field", ["requester", "beneficiary"])
@pytest.mark.parametrize("name", sorted(LOOKALIKES))
def test_a_look_alike_of_the_approver_id_is_refused_outright_as_requester_or_beneficiary(field, name):
    store, svc, _clock, wg = kit.make()
    for fake in (APPROVER + LOOKALIKES[name], APPROVER[:4] + LOOKALIKES[name] + APPROVER[4:]):
        req = kit.request(**{field: fake})
        out = kit.ex(wg, req, kit.sign(svc, req), "executor", False)
        assert out == {"outcome": "denied", "code": "KEY_INVALID"}, (field, name, out)
    assert store.count_applied() == 0


@pytest.mark.parametrize("name", sorted(LOOKALIKES))
def test_the_verifier_itself_folds_look_alikes_so_requester_and_beneficiary_still_collide_with_the_approver(name):
    """Defence in depth: text that `_text_ok` would refuse never gets a verdict about the person. The verifier refuses it itself (KEY_INVALID),
    and its comparison key still folds the invisible ones (approval.norm == textnorm.normalise)."""
    _store, svc, clock, wg = kit.make()
    fake = APPROVER + LOOKALIKES[name]
    assert norm(fake) == norm(APPROVER) == textnorm.normalise(APPROVER)
    req = kit.request()
    ap = kit.sign(svc, req)
    from datetime import UTC, datetime

    now = datetime.fromisoformat(clock()).astimezone(UTC)
    common = {
        "args_hash": hash_request(req, kit.key_of(req)),
        "tenant_id": "t1",
        "tier": "human",
        "requested_at": req["requested_at"],
        "min_tier": "human",
        "now": now,
    }
    assert wg.approvals.verify(ap, requester=fake, beneficiary="pat@example.com", **common) == "ARGS_HASH_MISMATCH", (
        "requester is signed, so a forged one mismatches"
    )
    own = kit.request(requester=fake)
    own_ap = kit.sign(svc, own)  # signed over the look-alike requester: the hash holds, the SoD rule must fire
    common["args_hash"] = hash_request(own, kit.key_of(own))
    assert wg.approvals.verify(own_ap, requester=fake, beneficiary="pat@example.com", **common) == "KEY_INVALID"
    ben = kit.request()
    assert (
        wg.approvals.verify(
            ap, requester="agent-run", beneficiary=fake, **{**common, "args_hash": hash_request(ben, kit.key_of(ben))}
        )
        == "KEY_INVALID"
    )


def test_text_that_folds_to_nothing_is_not_a_requester():
    _store, svc, _clock, wg = kit.make()
    for blank in (" ", "   "):
        req = kit.request(requester=blank)
        assert kit.ex(wg, req, kit.sign(svc, req), "executor", True)["code"] == "KEY_INVALID"


def test_plain_names_with_spaces_and_precomposed_letters_are_still_accepted():
    store, svc, _clock, wg = kit.make()
    req = kit.request(requester="Jose Garcia", beneficiary="Jos\u00e9 Garc\u00eda@example.com")
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"
    assert store.count_applied() == 1


# ------------------------------------------------------------------------------------------------ code M2 / design M1: reservation flooding
def _cap_inputs(i, amount=2500):
    return {"customer_id": f"c{i}", "order_id": f"ord-{i}", "amount": amount, "sender": f"s{i}@x.example"}


def test_the_unapproved_share_of_the_day_cap_is_enforced_by_the_store_and_a_flood_cannot_block_a_legitimate_execute():
    store, svc, _clock, wg = kit.make()
    share = LIMITS["USD"].store_day_cap // config.UNAPPROVED_SHARE_DEN
    held = denied = 0
    for i in range(100):  # a looping agent files 100 valid 2500-USD proposals for 100 customers with 100 senders
        a = _cap_inputs(i)
        code = kit.reserve(
            store, "t1", f"{i:064d}", a["customer_id"], a["order_id"], a["amount"], "USD", kit.START, sender=a["sender"]
        )
        held, denied = held + (code is None), denied + (code == "PENDING_CAP")
    assert (held, denied) == (share // 2500, 100 - share // 2500), "exactly the share is held, the rest is PENDING_CAP"
    assert sum(r["amount_minor"] for r in store.reservations("t1")) <= share
    req = kit.request(order_id="ord-legit", line_ids=["l-legit"], customer_id="c-legit", cluster=["c-legit"])
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied", (
        "the legitimate execute is not blocked by the flood"
    )


def test_pending_caps_per_cluster_and_per_sender_come_from_the_store_rows():
    store, *_ = kit.make()
    m = config.MAX_PENDING_PER_CUSTOMER
    for i in range(m):  # one customer, many senders: the CLUSTER cap bites
        assert kit.reserve(store, "t1", f"a{i:063d}", "c1", f"ord-a{i}", 100, "USD", kit.START, sender=f"s{i}@x.example") is None
    assert kit.reserve(store, "t1", "b" * 64, "c1", "ord-b", 100, "USD", kit.START, sender="other@x.example") == "PENDING_CAP"
    for i in range(m):  # one sender, many customers: the SENDER cap bites
        assert (
            kit.reserve(store, "t1", f"d{i:063d}", f"cd{i}", f"ord-d{i}", 100, "USD", kit.START, sender="same@x.example") is None
        )
    assert kit.reserve(store, "t1", "e" * 64, "ce", "ord-e", 100, "USD", kit.START, sender="same@x.example") == "PENDING_CAP"
    assert kit.reserve(store, "t2", "e" * 64, "c1", "ord-e", 100, "USD", kit.START, sender="same@x.example") is None, (
        "another tenant is unaffected"
    )


def test_a_repeat_of_a_held_key_is_not_counted_against_itself_and_expired_reservations_do_not_count():
    store, *_ = kit.make()
    m = config.MAX_PENDING_PER_CUSTOMER
    for i in range(m):
        assert kit.reserve(store, "t1", f"a{i:063d}", "c1", f"ord-{i}", 100, "USD", kit.START, sender=f"s{i}@x.example") is None
    assert kit.reserve(store, "t1", f"a{0:063d}", "c1", "ord-0", 100, "USD", kit.START, sender="s0@x.example") is None, (
        "idempotent at the cap"
    )
    # the server clock moves 25 hours on (the ratchet the write path keeps): the three START holds are now older than the TTL window
    store.set_meta("last_clock", "2026-10-21T13:00:00Z")
    assert kit.reserve(store, "t1", "z" * 64, "c1", "ord-z", 100, "USD", "2026-10-21T13:00:00Z", sender="sz@x.example") is None, (
        "reservations older than the window (derived from `at` and the TTL) hold nothing"
    )


def _dev():
    world = json.loads((DATA / "world.json").read_text(encoding="utf-8"))
    cases = [json.loads(x) for x in (DATA / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    d = desk.Desk(Store(), ApprovalIssuer(desk.DIRECTORY, key=b"d" * 32), lambda: desk.DEMO_NOW)
    return d, world, next(c for c in cases if c["case_id"] == "refunds-e-003")


def test_desk_propose_feeds_the_pre_gate_from_the_store_so_real_reservations_trip_the_day_cap():
    d, world, case = _dev()
    first = d.propose(case, world, desk.recorded_call(case))
    assert first.request is not None, "the case is allowed on an empty store"
    cur, key = first.request["currency"], first.detail["key"]
    d.store.release(first.request["tenant_id"], key)
    kit.raw_reserve(
        d.store, first.request["tenant_id"], "r" * 64, "cx", "ord-x", LIMITS[cur].store_day_cap - 1, cur, desk.DEMO_NOW
    )
    again = d.propose(case, world, desk.recorded_call(case))
    assert again.deny_code == "DAY_CAP", "the gate saw the STORE's reservation (recorded port state alone would have allowed it)"
    assert (
        d.store.reservations(first.request["tenant_id"])[0]["key"] == "r" * 64
        and len(d.store.reservations(first.request["tenant_id"])) == 1
    )


def test_desk_propose_is_refused_by_the_store_cap_even_when_the_pre_gate_allowed_it():
    """The race the store cap exists for: the pre-gate read its snapshot, then other proposals landed. A stale snapshot is modelled by a store whose
    `open_state` still says "nothing open"; only `reserve` (same transaction as the insert) can then refuse."""
    d, world, case = _dev()
    first = d.propose(case, world, desk.recorded_call(case))
    r = first.request
    d.store.release(r["tenant_id"], first.detail["key"])
    for i in range(config.MAX_PENDING_PER_CUSTOMER):  # the cluster already holds its maximum open proposals, in the STORE
        kit.raw_reserve(
            d.store,
            r["tenant_id"],
            f"p{i:063d}",
            r["customer_id"],
            f"ord-p{i}",
            100,
            r["currency"],
            desk.DEMO_NOW,
            sender=f"s{i}@x.example",
        )
    real = d.store.open_state
    stale = {
        "open_reservations": [],
        "store_day_refunded_minor": {r["currency"]: "0"},
        "open_proposals": {"cluster": 0, "sender": 0},
    }
    d.store.open_state = lambda *a, **k: stale
    assert d.propose(case, world, desk.recorded_call(case)).deny_code == "PENDING_CAP", "refused by Store.reserve alone"
    assert len(d.store.reservations(r["tenant_id"])) == config.MAX_PENDING_PER_CUSTOMER, "and nothing was added"
    d.store.open_state = real
    assert d.propose(case, world, desk.recorded_call(case)).deny_code == "PENDING_CAP", (
        "(and the live snapshot refuses it in the pre-gate)"
    )


def test_a_void_releases_the_reservation_now_and_only_the_executor_class_may_void():
    d, world, case = _dev()
    dec = d.propose(case, world, desk.recorded_call(case))
    tenant = dec.request["tenant_id"]
    assert len(d.store.reservations(tenant)) == 1
    assert d.write.void("agent_runtime", tenant, dec.detail["key"], "x") == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    assert d.write.void("sweeper", tenant, dec.detail["key"], "x")["code"] == "IDENTITY_DENIED"
    assert d.write.void("executor", tenant, dec.detail["key"], "line\nbreak")["code"] == "KEY_INVALID"
    assert len(d.store.reservations(tenant)) == 1, "none of the refusals released anything"
    assert d.void(dec, "rejected by the lead")["released"] == 1 and d.store.reservations(tenant) == []
    assert ("voided" in [e for e, _ in _audit(d.store)]) and d.store.audit_chain_ok()


def test_desk_demo_clock_has_one_source():
    assert desk.DEMO_NOW is config.DEMO_NOW


# ------------------------------------------------------------------------------------------------ code M3 / design M4: the signer kind
def test_the_hmac_default_is_symmetric_and_says_so():
    """HONEST NAME: this proves the default CAN mint (label check), not that it cannot. Do not read it as separation of duties."""
    _store, _svc, _clock, wg = kit.make()
    assert wg.approvals.can_mint is True and not hasattr(wg.approvals, "issue") and not hasattr(wg, "issue")
    forger = ApprovalIssuer(kit.DIRECTORY, signer=HmacSigner(wg.approvals._sigver._key))
    req = kit.request()
    forged = kit.sign(forger, req)
    assert kit.ex(wg, req, forged, "executor", True)["outcome"] == "dry_run", (
        "whoever holds the verifier can mint under the hmac kind"
    )


def _reachable_bytes(root, secret: bytes, seen=None):
    """True if `secret` (or its hex) appears anywhere in the attribute graph reachable from `root`."""
    seen = seen if seen is not None else set()
    if id(root) in seen:
        return False
    seen.add(id(root))
    if isinstance(root, bytes | bytearray):
        return secret in bytes(root)
    if isinstance(root, str):
        return secret.hex() in root
    if isinstance(root, dict | type(vars(object))):
        return any(_reachable_bytes(x, secret, seen) for kv in root.items() for x in kv)
    if isinstance(root, list | tuple | set | frozenset):
        return any(_reachable_bytes(x, secret, seen) for x in root)
    if hasattr(root, "__dict__"):
        return _reachable_bytes(vars(root), secret, seen)
    return False


def test_ed25519_verifier_cannot_mint_and_holds_no_private_key_anywhere_reachable_from_the_gate():
    pytest.importorskip("cryptography")
    secret = b"\x07" * 32
    signer = make_signer("ed25519", secret)
    svc = ApprovalIssuer(kit.DIRECTORY, signer=signer)
    store, clock = Store(), kit.Clock()
    wg = WriteGate(store, svc.verifier(), clock)
    assert wg.approvals.can_mint is False
    assert not _reachable_bytes(wg, secret), "the private key is not reachable from the write path"
    control = WriteGate(Store(), ApprovalIssuer(kit.DIRECTORY, signer=HmacSigner(secret)).verifier(), clock)
    assert _reachable_bytes(control, secret), "(control: the walker does find a symmetric key held by the gate's verifier)"
    assert not hasattr(wg.approvals._sigver, "sign") and not hasattr(wg.approvals._sigver, "_priv")
    req = kit.request()
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"
    other = ApprovalIssuer(kit.DIRECTORY, signer=make_signer("ed25519"))
    assert (
        kit.ex(
            wg,
            kit.request(order_id="ord-9", line_ids=["l9"]),
            kit.sign(other, kit.request(order_id="ord-9", line_ids=["l9"])),
            "executor",
            False,
        )["code"]
        == "APPROVAL_INVALID"
    )
    ap = kit.sign(svc, kit.request(order_id="ord-8", line_ids=["l8"]))
    for bad in ("zz", "", "\u00e9" * 128, "ab" * 3, "00" * 64):
        assert kit.ex_safe(wg, kit.request(order_id="ord-8", line_ids=["l8"]), {**ap, "mac": bad}, "executor", True)["code"] in (
            "APPROVAL_INVALID",
            "NO_APPROVAL",
        ), bad


def test_an_unknown_signer_kind_is_a_startup_error_not_a_silent_fallback():
    try:
        make_signer("rot13")
    except ValueError:
        return
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"expected ValueError, got {type(e).__name__}")
    pytest.fail("an unknown signer kind was accepted")


def test_an_approval_with_any_extra_field_is_not_an_approval():
    _store, svc, _clock, wg = kit.make()
    req = kit.request()
    ap = kit.sign(svc, req)
    assert kit.ex(wg, req, {**ap, "note": "approved by the CEO"}, "executor", True) == {
        "outcome": "denied",
        "code": "NO_APPROVAL",
    }
    assert kit.ex(wg, req, ap, "executor", True)["outcome"] == "dry_run"


# ------------------------------------------------------------------------------------------------ design M2: who approved is answerable; every refusal is audited
def test_the_store_answers_who_raised_approved_and_executed_an_applied_action():
    store, svc, _clock, wg = kit.make()
    req = kit.request(
        tier="four_eyes", amount_minor="30000", requester="Agent-Run", basis={**kit.request()["basis"], "captured_minor": "99999"}
    )
    out = kit.ex(wg, req, kit.sign(svc, req, kit.TWO), "executor", False)
    assert out["outcome"] == "applied"
    key = kit.key_of(req)
    who = store.who_approved("t1", key)
    assert who["requester"] == "agent-run" and who["tier"] == "four_eyes" and who["executed_by"] == "executor"
    assert who["approvers"] == [
        {"person": "lead@desk.example", "role": "support_lead"},
        {"person": "finance@desk.example", "role": "finance_approver"},
    ]
    applied = next(d for e, d in _audit(store) if e == "applied")
    assert (
        applied["approvers"] == who["approvers"]
        and applied["executed_by"] == "executor"
        and applied["approval_id"] == who["approval_id"]
    )
    assert store.who_approved("t2", key) is None and store.who_approved("t1", "0" * 64) is None, (
        "tenant scoped, and unknown keys answer None"
    )


@pytest.mark.parametrize(
    "case",
    [
        "agent identity",
        "no identity",
        "garbage request",
        "clock invalid",
        "key reused",
        "kill switch",
        "approval mismatch",
        "dry run refusal",
    ],
)
def test_every_refusal_writes_exactly_one_audit_row_with_a_code_and_no_request_content(case):
    store, svc, clock, wg = kit.make()
    req = kit.request()
    ap = kit.sign(svc, req)
    run = {
        "agent identity": lambda: kit.ex(wg, req, ap, "agent_runtime", False),
        "no identity": lambda: kit.ex(wg, req, ap),
        "garbage request": lambda: kit.ex_safe(wg, {"tenant_id": "t1"}, ap, "executor", False),
        "clock invalid": lambda: (setattr(clock, "now", "not a time"), kit.ex(wg, req, ap, "executor", False))[1],
        "approval mismatch": lambda: kit.ex(wg, {**req, "order_id": "ord-2"}, ap, "executor", False),
        "dry run refusal": lambda: kit.ex(wg, {**req, "order_id": "ord-2"}, ap, "executor", True),
    }
    if case == "key reused":
        assert kit.ex(wg, req, ap, "executor", False)["outcome"] == "applied"
        run["key reused"] = lambda: kit.ex(
            wg,
            {**req, "line_ids": ["l1"], "amount_minor": "2500", "currency": "USD", "order_id": "ord-1", "tenant_id": "t1"}
            | {"basis": {**req["basis"]}},
            ap,
            "executor",
            False,
        )
    if case == "kill switch":
        assert wg.set_kill_switch("kill_switch_operator", True, "drill")["outcome"] == "ok"
        run["kill switch"] = lambda: kit.ex(wg, req, ap, "executor", False)
    before = len(store.audit_rows())
    out = run[case]()
    rows = _audit(store)[before:]
    if case == "key reused":
        assert out["outcome"] == "duplicate_ignored" and rows == [], "a replay is an answer, not a refusal: no row"
        return
    assert out["outcome"] in ("denied", "held"), (case, out)
    assert [e for e, _ in rows] == ["refused"], (case, rows)
    detail = rows[0][1]
    assert detail["code"] == out["code"] and set(detail) == {"key", "code", "identity"}
    assert detail["identity"] == {"agent identity": "agent_runtime", "no identity": "?"}.get(case, "executor"), (
        "the caller's label is recorded"
    )
    assert "pat@example.com" not in json.dumps(rows) and store.audit_chain_ok()


def test_a_reused_key_with_other_parameters_is_audited_as_a_refusal():
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"
    before = len(store.audit_rows())
    again = {**req, "line_ids": ["l1"], "customer_id": "c1"}
    key = kit.key_of(req)
    # same business key needs the same five parameters, so reuse is only reachable from a recovered/other copy of the store: simulate by editing the row
    with store.transaction() as db:
        db.execute("UPDATE applied SET amount_minor = 2501 WHERE key = ?", (key,))
    out = kit.ex(wg, again, kit.sign(svc, again), "executor", False)
    assert out == {"outcome": "denied", "code": "KEY_REUSED"} and [e for e, _ in _audit(store)[before:]] == ["refused"]


def test_an_omitted_identity_is_denied_and_never_acts_as_the_executor():
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    ap = kit.sign(svc, req)
    assert kit.ex(wg, req, ap) == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    assert kit.ex(wg, req, ap, dry_run=False) == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    assert kit.ex(wg, req, ap, None, False)["code"] == "IDENTITY_DENIED" and store.count_applied() == 0


# ------------------------------------------------------------------------------------------------ code m1, m7, m8, m11 and the shape limits
def test_duplicate_cluster_entries_are_refused_like_duplicate_line_ids():
    _store, svc, _clock, wg = kit.make()
    for cl in (["c1", "c1"], ["c1", "c2", "c2"]):
        req = kit.request(cluster=cl)
        assert kit.ex(wg, req, kit.sign(svc, req), "executor", True) == {"outcome": "denied", "code": "KEY_INVALID"}, cl


@pytest.mark.parametrize("bad", ["2501", "", "x" * 5000, "0250", 2500, None])
def test_the_signed_request_text_must_equal_the_amount(bad):
    _store, svc, _clock, wg = kit.make()
    req = kit.request(basis={**kit.request()["basis"], "request": bad})
    out = kit.ex_safe(wg, req, kit.sign(svc, req), "executor", True)
    assert out["outcome"] == "denied" and out["code"] in ("KEY_INVALID", "AMOUNT_NOT_CANONICAL"), (bad, out)


@pytest.mark.parametrize(
    "reason", ["line\nbreak", "bidi \u202e text", "look\u0301alike", "x" * (config.TEXT_MAX + 1), "   ", "nb\u00a0sp", 5, None]
)
def test_the_kill_switch_reason_cannot_carry_control_bidi_or_look_alike_text_into_the_audit_chain(reason):
    store, _svc, _clock, wg = kit.make()
    assert wg.set_kill_switch("kill_switch_operator", True, reason) == {"outcome": "denied", "code": "KEY_INVALID"}
    assert store.kill_switch()["on"] is False and [e for e, _ in _audit(store)] == ["refused"], "refused and audited, not applied"
    assert (
        wg.set_kill_switch("kill_switch_operator", True, " drill ")["outcome"] == "ok"
        and store.kill_switch()["reason"] == "drill"
    )


def test_line_count_limit_comes_from_config_and_is_exact():
    _store, svc, _clock, wg = kit.make()
    ok = kit.request(line_ids=[f"l{i}" for i in range(config.MAX_LINES)])
    assert kit.ex(wg, ok, kit.sign(svc, ok), "executor", True)["outcome"] == "dry_run"
    over = kit.request(line_ids=[f"l{i}" for i in range(config.MAX_LINES + 1)])
    assert kit.ex(wg, over, kit.sign(svc, over), "executor", True)["code"] == "KEY_INVALID"


def test_a_second_refund_of_the_shipping_charge_is_a_ledger_overlap():
    store, svc, _clock, wg = kit.make()
    a = kit.request(line_ids=["shipping"], amount_minor="500")
    assert kit.ex(wg, a, kit.sign(svc, a), "executor", False)["outcome"] == "applied"
    b = kit.request(line_ids=["shipping"], amount_minor="600")
    assert kit.ex(wg, b, kit.sign(svc, b), "executor", False)["code"] == "LINE_COMPENSATED"
    assert store.count_applied() == 1


def test_a_busy_store_is_a_typed_deny_not_a_driver_error_and_work_resumes_afterwards(tmp_path):
    path = str(tmp_path / "busy.sqlite")
    store = Store(path, timeout_s=0.2)
    svc = ApprovalIssuer(kit.DIRECTORY, key=b"k" * 32)
    wg = WriteGate(store, svc.verifier(), kit.Clock())
    req = kit.request()
    ap = kit.sign(svc, req)
    holder = sqlite3.connect(path, isolation_level=None)
    holder.execute("BEGIN IMMEDIATE")  # another process holds the write lock
    t0 = time.monotonic()
    assert kit.ex_safe(wg, req, ap, "executor", False) == {"outcome": "denied", "code": "STORE_BUSY"}
    assert time.monotonic() - t0 < 5
    try:
        store.set_meta("a", "b")
    except StoreBusy:
        pass
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"the lock timeout surfaced as {type(e).__name__}, not StoreBusy")
    else:
        pytest.fail("the write went through while another process held the lock")
    holder.execute("ROLLBACK")
    holder.close()
    assert kit.ex(wg, req, ap, "executor", False)["outcome"] == "applied"


def test_a_failing_rollback_does_not_replace_the_error_that_caused_it():
    store = Store()
    real = store._db

    class Proxy:
        def execute(self, sql, *a):
            if sql == "ROLLBACK":
                raise sqlite3.OperationalError("rollback failed")
            return real.execute(sql, *a)

        def __getattr__(self, name):
            return getattr(real, name)

    store._db = Proxy()
    caught = None
    try:
        with store.transaction():
            1 / 0  # noqa: B018
    except Exception as e:  # noqa: BLE001
        caught = type(e)
    store._db = real
    real.execute("ROLLBACK")
    assert caught is ZeroDivisionError, f"the original error was replaced by {caught}"


# ------------------------------------------------------------------------------------------------ design M4: the store kind and its contract
def check_store_contract(make_store):
    """Behaviour every `StorePort` implementation must show. Run against SQLite in memory and on a file; a second backend runs the same function."""
    s = make_store()
    assert isinstance(s, StorePort)
    with pytest.raises(ZeroDivisionError), s.transaction():
        s.set_meta("a", "1")
        1 / 0  # noqa: B018
    assert s.meta("a") is None, "a failed transaction leaves nothing"
    s.audit("t1", "e", {"k": 1}, "2026-10-20T12:00:00Z")
    s.audit("t2", "e", {"k": 2}, "2026-10-20T12:00:01Z")
    assert s.audit_chain_ok() and len(s.audit_rows()) == 2
    assert kit.reserve(s, "t1", "k" * 64, "c1", "o1", 100, "USD", kit.START) is None
    assert (
        kit.reserve(s, "t1", "k" * 64, "c1", "o1", 999, "USD", kit.START) is None
        and s.reservations("t1")[0]["amount_minor"] == 100
    )
    assert s.reservations("t2") == [] and s.release("t2", "k" * 64) == 0 and s.release("t1", "k" * 64) == 1
    assert s.who_approved("t1", "k" * 64) is None and s.get_applied("t1", "k" * 64) is None
    s.consume_approval("t1", "ap-1", "k" * 64, "r", [{"person": "p", "role": "support_lead"}], "human", "executor", kit.START)
    assert s.approval_key("t1", "ap-1") == "k" * 64 and s.approval_key("t2", "ap-1") is None
    with pytest.raises(
        sqlite3.IntegrityError
    ):  # the unique (tenant, approval) is part of the contract (a driver-specific error type is mapped by a backend)
        s.consume_approval("t1", "ap-1", "j" * 64, "r", [], "human", "executor", kit.START)


def test_the_sqlite_store_meets_the_store_contract_in_memory_and_on_a_file(tmp_path):
    check_store_contract(Store)
    check_store_contract(lambda: Store(str(tmp_path / "contract.sqlite")))


# ------------------------------------------------------------------------------------------------ code m3, m4: egress
@pytest.mark.parametrize("text", [None, 5, b"bytes", ["a"], {"a": 1}])
def test_egress_check_on_non_text_is_a_typed_violation_not_a_crash(text):
    def call(*a):
        try:
            return guards.egress_check(*a)
        except Exception as e:  # noqa: BLE001
            return f"raised {type(e).__name__}"

    assert call(text, "a@b.example", "a@b.example") == ["TEXT_NOT_STRING"]
    assert call("hi", None, "a@b.example") == ["TEXT_NOT_STRING"]


def test_egress_check_refuses_oversized_text_unscanned():
    assert guards.egress_check("a" * (config.EGRESS_MAX_TEXT + 1), "a@b.example", "a@b.example") == ["TEXT_TOO_LONG"]
    assert guards.egress_check("hello " * 100, "a@b.example", "a@b.example") == []


@pytest.mark.parametrize("name", ["a-", "x.", "1.", "a@", "a"])
def test_every_egress_pattern_is_linear_on_adversarial_text_at_the_size_limit(name):
    text = (name * config.EGRESS_MAX_TEXT)[: config.EGRESS_MAX_TEXT]
    t0 = time.perf_counter()
    guards.egress_check(text, "a@b.example", "a@b.example")
    for rx in (guards.DOMAIN, guards.EMAIL, guards.URL, guards.IPV4, guards.BANK):
        rx.findall(text)
    assert time.perf_counter() - t0 < 1.0, "an unbounded pattern is quadratic here (it took seconds before the bounds)"


@pytest.mark.parametrize("spelled", ["evil .example", "pay at evil .example/pay", "evil . example", "go to evil .com now"])
def test_a_space_before_the_dot_cannot_hide_a_host(spelled):
    assert "UNLISTED_LINK" in guards.egress_check(spelled, "a@b.example", "a@b.example"), spelled
    assert guards.egress_check("Your total was 12.50 and the ticket number is 4521. Thanks.", "a@b.example", "a@b.example") == []


# ------------------------------------------------------------------------------------------------ design m-e: config validation
def test_validate_limits_rejects_a_config_that_breaks_the_ordering_or_the_types():
    config.validate_limits()
    good = config.LIMITS["USD"]
    from dataclasses import replace

    for bad in (
        replace(good, customer_30d_cap=good.hard_cap),
        replace(good, one_approver_max=good.customer_30d_cap + 1),
        replace(good, store_day_cap=good.hard_cap - 1),
        replace(good, goodwill_amount=good.goodwill_cap + 1),
        replace(good, hard_cap=0),
        replace(good, hard_cap=True),
        replace(good, goodwill_amount=True),  # True == 1 passes every ordering check, so only the type check refuses it
    ):
        with pytest.raises(ValueError):
            config.validate_limits({"USD": bad})


def test_the_approval_verifier_type_is_the_one_the_gate_is_built_with():
    _store, _svc, _clock, wg = kit.make()
    assert isinstance(wg.approvals, ApprovalVerifier) and isinstance(wg.store, StorePort)


def test_concurrent_proposals_cannot_both_slip_under_a_pending_cap():
    store = Store()
    m = config.MAX_PENDING_PER_CUSTOMER
    out = []

    def go(i):
        out.append(kit.reserve(store, "t1", f"{i:064d}", "c1", f"ord-{i}", 100, "USD", kit.START, sender=f"s{i}@x.example"))

    ts = [threading.Thread(target=go, args=(i,)) for i in range(m + 8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert out.count(None) == m and out.count("PENDING_CAP") == 8


def test_refused_kill_switch_and_sweep_calls_are_audited_too():
    store, _svc, clock, wg = kit.make()
    assert wg.set_kill_switch("agent_runtime", True, "x")["code"] == "IDENTITY_DENIED"
    assert wg.sweep("agent_runtime")["code"] == "IDENTITY_DENIED"
    clock.now = "garbage"
    assert wg.sweep("sweeper")["code"] == "CLOCK_INVALID"
    rows = _audit(store)
    assert [(e, d["code"], d["identity"]) for e, d in rows] == [
        ("refused", "IDENTITY_DENIED", "agent_runtime"),
        ("refused", "IDENTITY_DENIED", "agent_runtime"),
        ("refused", "CLOCK_INVALID", "sweeper"),
    ]


def test_a_repeat_proposal_of_a_held_key_is_not_counted_against_itself_by_the_pre_gate():
    d, world, case = _dev()
    first = d.propose(case, world, desk.recorded_call(case))
    r = first.request
    for i in range(config.MAX_PENDING_PER_CUSTOMER - 1):  # two OTHER open proposals + this key's own = the maximum, still allowed
        kit.raw_reserve(
            d.store,
            r["tenant_id"],
            f"p{i:063d}",
            r["customer_id"],
            f"ord-p{i}",
            100,
            r["currency"],
            desk.DEMO_NOW,
            sender=f"s{i}@x.example",
        )
    again = d.propose(case, world, desk.recorded_call(case))
    assert again.request is not None and again.detail["key"] == first.detail["key"], again.deny_code


def _separators():
    import unicodedata

    return [chr(c) for c in range(sys.maxunicode + 1) if unicodedata.category(chr(c)) in ("Zs", "Zl", "Zp") and chr(c) != " "]


def test_every_space_line_and_paragraph_separator_is_refused_by_the_verifier_and_by_the_write_path():
    """Evidence 9: U+00A0 and U+3000 slipped past the verifier level. Every Zs, Zl and Zp character, at the end and inside the id, as requester, as
    beneficiary and as the approver's own name, is KEY_INVALID at the verifier AND at execute."""
    from datetime import UTC, datetime

    seps = _separators()
    assert len(seps) >= 8
    _store, svc, clock, wg = kit.make()
    now = datetime.fromisoformat(clock()).astimezone(UTC)
    base = kit.request()
    ap = kit.sign(svc, base)
    for sep in seps:
        for fake in (APPROVER + sep, APPROVER[:4] + sep + APPROVER[4:]):
            common = {"tenant_id": "t1", "tier": "human", "requested_at": base["requested_at"], "min_tier": "human", "now": now}
            for req_name, ben_name in ((fake, "pat@example.com"), ("agent-run", fake)):
                got = wg.approvals.verify(
                    ap, args_hash=hash_request(base, kit.key_of(base)), requester=req_name, beneficiary=ben_name, **common
                )
                assert got in ("KEY_INVALID", "ARGS_HASH_MISMATCH"), (hex(ord(sep)), req_name, ben_name, got)
            for field in ("requester", "beneficiary"):
                r = kit.request(**{field: fake})
                out = kit.ex(wg, r, kit.sign(svc, r), "executor", True)
                assert out == {"outcome": "denied", "code": "KEY_INVALID"}, (hex(ord(sep)), field)
            ghost = kit.sign(svc, base, [(fake, "support_lead")])
            assert wg.approvals.verify(
                ghost,
                args_hash=hash_request(base, kit.key_of(base)),
                requester="agent-run",
                beneficiary="pat@example.com",
                **common,
            ) in ("KEY_INVALID", "APPROVER_UNKNOWN"), hex(ord(sep))


def test_the_verifier_refuses_a_marked_up_requester_that_is_signed_correctly():
    """Not only a mismatch: an approval correctly signed OVER a hidden-character requester is still refused by the verifier (KEY_INVALID)."""
    from datetime import UTC, datetime

    _store, svc, clock, wg = kit.make()
    now = datetime.fromisoformat(clock()).astimezone(UTC)
    for sep in _separators():
        fake = "agent-run" + sep
        req = kit.request(requester=fake)
        ap = kit.sign(svc, req)
        got = wg.approvals.verify(
            ap, args_hash=hash_request(req, kit.key_of(req)), tenant_id="t1", tier="human", requested_at=req["requested_at"], min_tier="human", requester=fake, beneficiary="pat@example.com", now=now,
        )  # fmt: skip
        assert got == "KEY_INVALID", hex(ord(sep))


def test_a_homoglyph_requester_or_reason_is_refused_because_staff_side_ids_are_ascii():
    _store, svc, _clock, wg = kit.make()
    for fake in ("l\u0435ad@desk.example", "d\u0433ill", "\uff4c\uff45\uff41\uff44@desk.example"):
        req = kit.request(requester=fake)
        assert kit.ex(wg, req, kit.sign(svc, req), "executor", True) == {"outcome": "denied", "code": "KEY_INVALID"}, fake
    ok = kit.request(beneficiary="Jos\u00e9 Garc\u00eda@example.com")
    assert kit.ex(wg, ok, kit.sign(svc, ok), "executor", True)["outcome"] == "dry_run", (
        "a customer address may hold accented letters"
    )
    assert wg.set_kill_switch("kill_switch_operator", True, "d\u0433ill drill") == {"outcome": "denied", "code": "KEY_INVALID"}
    assert wg.set_kill_switch("kill_switch_operator", True, "drill")["outcome"] == "ok"


def test_a_spaced_dot_before_a_lowercase_word_is_read_as_a_host_but_prose_is_not():
    p = "pat@example.com"
    assert "UNLISTED_LINK" in guards.egress_check("go to evil. example now", p, p)
    assert "UNLISTED_LINK" in guards.egress_check("evil. example", p, p)
    for prose in ("Thanks. Regards, the team. See you.", "Your order total was 12.50 and the ticket is 4521. Thanks."):
        assert guards.egress_check(prose, p, p) == [], prose


def test_the_default_signer_is_ed25519_when_the_extra_is_installed_and_hmac_is_only_ever_asked_for_by_name_or_key():
    from refunds.signers import default_kind

    try:
        import cryptography  # noqa: F401
    except ImportError:
        pytest.skip("the ed25519 extra is not installed here")
    assert default_kind() == "ed25519"
    default = ApprovalIssuer(desk.DIRECTORY).verifier()
    assert default.can_mint is False and default.signer_kind == "ed25519"
    keyed = ApprovalIssuer(desk.DIRECTORY, key=b"k" * 32).verifier()
    assert keyed.can_mint is True and "dev, can mint" in keyed.signer_kind
    d = desk.Desk(Store(), ApprovalIssuer(desk.DIRECTORY), lambda: desk.DEMO_NOW)
    assert d.write.approvals.can_mint is False, "the CLI path (python -m refunds.desk) builds no minting verifier"


def test_every_applied_row_says_which_kind_of_verifier_checked_the_approval():
    store, svc, _clock, wg = kit.make()  # kit.make passes an explicit key: HMAC, labelled as dev
    req = kit.request()
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"
    applied = next(json.loads(r["detail"]) for r in store.audit_rows() if r["event"] == "applied")
    assert applied.get("signer") == "hmac (dev, can mint)"

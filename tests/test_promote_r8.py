"""Generic fixes promoted from the refunds demo (design/code review 8): identity fold, reply egress, store-enforced reservation caps, signed
approvals, intent-call-settle, refusal events. Each test fails on a tree without the module (ImportError) and on the named regression."""

import threading
import time

import pytest

from hadavin_sdk.actions import outbox
from hadavin_sdk.audit.refusal import refusal_event
from hadavin_sdk.guard.identity_fold import fold, same_person, text_ok
from hadavin_sdk.guard.reply_egress import MAX_TEXT, reply_violations
from hadavin_sdk.reservations import Reservations, StoreBusy, check_ordered_limits

LOOKALIKE = ["\u0301", "\ufe0f", "\u3164", "\u00a0", "\u200b", "\u3000"]


@pytest.mark.parametrize("ch", LOOKALIKE)
def test_look_alikes_fold_to_the_real_id_and_are_refused_as_text(ch):
    real = "lead@desk.example"
    assert fold(real + ch) == real and same_person(real + ch, real)
    if (
        ch not in ("\u00a0", "\u3000")
    ):  # a real space inside an id is a different id, so only the invisible ones fold away mid-string
        assert same_person(real[:4] + ch + real[4:], real)
    assert text_ok(real) and not text_ok(real + ch) and not text_ok(real[:4] + ch + real[4:])


def test_empty_after_fold_is_not_text_and_fullwidth_and_case_fold():
    assert not text_ok(" ") and not text_ok("") and not text_ok(5) and not text_ok("x" * 300)
    assert same_person(
        "\uff4c\uff45\uff41\uff44@Desk.example", "lead@desk.example"
    ) and not same_person("", "")
    assert text_ok("Jos\u00e9 Garc\u00eda")


def test_reply_egress_is_typed_bounded_and_catches_spaced_dots():
    ok, me = "a@b.example", "a@b.example"
    for bad in (None, 5, b"x", ["a"]):
        assert reply_violations(bad, me, ok) == ["TEXT_NOT_STRING"]
    assert reply_violations("hi", None, ok) == ["TEXT_NOT_STRING"]
    assert reply_violations("a" * (MAX_TEXT + 1), me, ok) == ["TEXT_TOO_LONG"]
    for spelled in ("evil .example", "evil . example", "evil[.]example", "evil\u3002example/pay"):
        assert "UNLISTED_LINK" in reply_violations(spelled, me, ok), spelled
    assert reply_violations("Total 12.50, ticket 4521. Thanks.", me, ok) == []
    assert "BANK_PATTERN" in reply_violations("pay GB29 NWBK 6016 1331 9268 19", me, ok)
    assert "UNLISTED_ADDRESS" in reply_violations("mail boss@x.example", me, ok)


@pytest.mark.parametrize("unit", ["a-", "x.", "1.", "a@", "a"])
def test_every_reply_pattern_is_linear_at_the_size_limit(unit):
    text = (unit * MAX_TEXT)[:MAX_TEXT]
    t0 = time.perf_counter()
    reply_violations(text, "a@b.example", "a@b.example")
    assert time.perf_counter() - t0 < 1.0


def _book(**kw):
    return Reservations(max_per_cluster=3, max_per_sender=3, share_cap_minor={"USD": 62500}, **kw)


def test_reservation_flood_is_capped_by_the_store_and_a_repeat_is_idempotent():
    b = _book()
    res = [
        b.reserve("t", f"{i:04d}", [f"c{i}"], f"s{i}", "USD", 2500, "2026-01-01T00:00:00Z", "2000")
        for i in range(100)
    ]
    assert res.count(None) == 25 and res.count("PENDING_CAP") == 75
    assert b.reserve("t", "0000", ["c0"], "s0", "USD", 9, "2026-01-01T00:00:00Z", "2000") is None, (
        "held key repeats cleanly"
    )
    assert b.release("t", "0000") == 1 and b.release("t", "0000") == 0


def test_per_cluster_per_sender_tenant_scope_and_expiry():
    b = _book()
    for i in range(3):
        assert (
            b.reserve("t", f"a{i}", ["c1"], f"s{i}", "USD", 100, "2026-01-01T00:00:00Z", "2000")
            is None
        )
    assert (
        b.reserve("t", "a9", ["c1"], "s9", "USD", 100, "2026-01-01T00:00:00Z", "2000")
        == "PENDING_CAP"
    )
    assert b.reserve("u", "a9", ["c1"], "s9", "USD", 100, "2026-01-01T00:00:00Z", "2000") is None, (
        "other tenant unaffected"
    )
    assert (
        b.reserve(
            "t", "a9", ["c1"], "s9", "USD", 100, "2026-01-02T00:00:00Z", "2026-01-01T12:00:00Z"
        )
        is None
    ), "expired do not count"
    for i in range(3):
        assert (
            b.reserve("t", f"d{i}", [f"x{i}"], "same", "USD", 100, "2026-01-01T00:00:00Z", "2000")
            is None
        )
    assert (
        b.reserve("t", "d9", ["x9"], "same", "USD", 100, "2026-01-01T00:00:00Z", "2000")
        == "PENDING_CAP"
    )
    assert (
        b.reserve("t", "e", ["z"], "q", "EUR", 100, "2026-01-01T00:00:00Z", "2000") == "PENDING_CAP"
    ), "no share configured = refused"


def test_concurrent_reservations_cannot_both_slip_under_a_cap():
    b = _book()
    out: list = []
    ts = [
        threading.Thread(
            target=lambda i=i: out.append(
                b.reserve("t", f"k{i}", ["c"], f"s{i}", "USD", 1, "2026-01-01T00:00:00Z", "2000")
            )
        )
        for i in range(11)
    ]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert out.count(None) == 3


def test_busy_lock_is_a_typed_error(tmp_path):
    import sqlite3

    path = str(tmp_path / "r.sqlite")
    b = Reservations(
        path, max_per_cluster=3, max_per_sender=3, share_cap_minor={"USD": 100}, timeout_s=0.2
    )
    holder = sqlite3.connect(path, isolation_level=None)
    holder.execute("BEGIN IMMEDIATE")
    try:
        b.reserve("t", "k", ["c"], "s", "USD", 1, "2026-01-01T00:00:00Z", "2000")
    except StoreBusy:
        pass
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"raw {type(e).__name__}")
    else:
        pytest.fail("no error while locked")
    holder.execute("ROLLBACK")


def test_limit_tables_are_validated():
    check_ordered_limits({"USD": (7500, 30000, 50000, 250000)})
    for bad in (
        (7500, 50000, 50000, 250000),
        (40000, 30000, 50000, 250000),
        (7500, 30000, 50000, 40000),
        (7500, 30000, 50000, 0),
        (True, 30000, 50000, 250000),
    ):
        with pytest.raises(ValueError):
            check_ordered_limits({"USD": bad})


def test_signed_approval_verifier_cannot_mint_and_refuses_extra_fields_and_forgeries():
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric import ed25519

    from hadavin_sdk.approvals import signed
    from hadavin_sdk.audit.signer import LocalSigner

    s = LocalSigner(ed25519.Ed25519PrivateKey.generate())
    body = {
        "approval_id": "ap-1",
        "tenant_id": "t",
        "args_hash": "0" * 64,
        "tier": "human",
        "requested_at": "2026-01-01T00:00:00Z",
        "requester": "r",
        "steps": [],
    }
    ap = signed.issue(s, body)
    v = signed.ApprovalVerifier(s.public_key())
    assert v.can_mint is False and v.verify(ap) and not hasattr(v, "sign")
    assert (
        not v.verify({**ap, "note": "x"})
        and not v.verify({**ap, "tier": "four_eyes"})
        and not v.verify({**ap, "sig": "zz"})
        and not v.verify(None)
    )
    other = LocalSigner(ed25519.Ed25519PrivateKey.generate())
    assert not v.verify(signed.issue(other, body))
    with pytest.raises(ValueError):
        signed.issue(s, {**body, "extra": 1})


class _Mem:
    def __init__(self):
        self.intent: dict[str, str | None] = {}

    def record_intent(self, key):
        if key in self.intent:
            return False
        self.intent[key] = None
        return True

    def settle(self, key, outcome):
        self.intent[key] = outcome

    def open_intents(self):
        return [k for k, v in self.intent.items() if v is None]


class _Proc:
    def __init__(self, applied=None, fail_apply=False, fail_lookup=False):
        self.applied, self.fail_apply, self.fail_lookup, self.calls = (
            applied or {},
            fail_apply,
            fail_lookup,
            0,
        )

    def apply(self, key):
        self.calls += 1
        if self.fail_apply:
            self.applied[key] = "done"  # the call happened but the response was lost
            raise TimeoutError
        self.applied[key] = "done"
        return "done"

    def lookup(self, key):
        if self.fail_lookup:
            raise TimeoutError
        return self.applied.get(key)


def test_intent_call_settle_and_reconcile():
    st, p = _Mem(), _Proc()
    assert outbox.run(st, p, "k1") == "done" and st.intent["k1"] == "done"
    assert outbox.run(st, p, "k1") == "duplicate_ignored" and p.calls == 1, (
        "a replay never calls the processor again"
    )
    st2, p2 = _Mem(), _Proc(fail_apply=True)
    assert outbox.run(st2, p2, "k2") == "unknown" and st2.open_intents() == ["k2"], (
        "a lost response leaves the intent open"
    )
    assert outbox.reconcile(st2, _Proc(fail_lookup=True, applied=p2.applied)) == {
        "k2": "unknown"
    }, "a failed lookup is never 'not applied'"
    assert outbox.reconcile(st2, p2) == {"k2": "done"} and st2.open_intents() == []
    st3 = _Mem()
    st3.record_intent("k3")
    assert outbox.reconcile(st3, _Proc()) == {"k3": "not_applied"}


def test_refusal_events_carry_a_code_and_a_label_never_content():
    e = refusal_event("r1", "gate", "KEY_INVALID", "executor", "k" * 8)
    assert (e.operation, e.result, e.error_code, e.principal, e.object_ref) == (
        "refused",
        "refused",
        "KEY_INVALID",
        "executor",
        "kkkkkkkk",
    )
    e2 = refusal_event("r1", "gate", "IDENTITY_DENIED", "Bob <bob@x.example>\n", None)
    assert e2.principal == "?" and e2.object_ref == "-" and "bob" not in e2.model_dump_json()

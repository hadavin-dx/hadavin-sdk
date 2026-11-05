"""Review 9 (round 11): homoglyph beneficiary, void tombstone, typed busy on every writer, fail-closed signer, spaced-dot variants, clock-derived window,
the core copy pin and the seam shim, the wider store contract."""

import hashlib
import importlib.util
import json
import sqlite3
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import wgkit as kit

from refunds import config, core_seam, desk, guards, identities, textnorm
from refunds.approval import ApprovalIssuer, norm
from refunds.signers import HmacSigner, SignerNotConfigured, default_kind
from refunds.store import Store
from refunds.writegate import WriteGate, hash_request

ROOT = Path(__file__).resolve().parents[1]
CYR = {
    "a": "\u0430",
    "e": "\u0435",
    "o": "\u043e",
    "p": "\u0440",
    "c": "\u0441",
    "x": "\u0445",
    "t": "\u0442",
    "m": "\u043c",
    "l": "\u04cf",
}
APPROVER = "pat@example.com"  # in kit.DIRECTORY as a support_lead (an approver who is also a customer address)


def _one_approver(req, svc, people=None):
    return kit.sign(svc, req, people or [(APPROVER, "support_lead")])


# ---------------------------------------------------------------- M1: a look-alike beneficiary cannot hide an approver
def test_the_control_case_a_plain_beneficiary_that_is_the_approver_is_refused():
    _store, svc, _clock, wg = kit.make()
    req = kit.request(beneficiary=APPROVER)
    assert kit.ex(wg, req, _one_approver(req, svc), "executor", False) == {"outcome": "denied", "code": "APPROVER_IS_BENEFICIARY"}


def test_a_mixed_script_beneficiary_is_refused_outright_end_to_end():
    store, svc, _clock, wg = kit.make()
    for pos in range(len(APPROVER)):
        ch = APPROVER[pos]
        if ch not in CYR:
            continue
        fake = APPROVER[:pos] + CYR[ch] + APPROVER[pos + 1 :]
        assert fake != APPROVER and not fake.isascii(), "the probe really contains a look-alike"
        req = kit.request(beneficiary=fake)
        assert kit.ex(wg, req, _one_approver(req, svc), "executor", False) == {"outcome": "denied", "code": "KEY_INVALID"}, fake
    assert store.count_applied() == 0


def test_a_single_script_look_alike_spelling_of_the_approver_is_the_approver():
    """Every letter replaced: one script, so the mixed-script rule does not fire; the shared skeleton still equates it with the approver."""
    _store, svc, _clock, wg = kit.make()
    fake = "".join(CYR.get(c, c) for c in APPROVER)
    assert fake != APPROVER and not any(c.isascii() and c.isalpha() for c in fake.split("@")[0])
    assert not textnorm.mixed_script(fake.split("@")[0]), (
        "the local part is one script (a probe that is mixed would only test the other rule)"
    )
    req = kit.request(beneficiary=fake)
    out = kit.ex(wg, req, _one_approver(req, svc), "executor", False)
    assert out["code"] in ("APPROVER_IS_BENEFICIARY", "KEY_INVALID"), out
    only_skeleton = "\u0440\u0430\u0442@\u0435\u0445\u0430\u043c\u0440\u04cf\u0435.\u0441\u043e\u043c"  # p a t @ e x a m p l e . c o m, all Cyrillic letters
    assert textnorm.skeleton(only_skeleton) == APPROVER
    req2 = kit.request(beneficiary=only_skeleton)
    got = kit.ex(wg, req2, _one_approver(req2, svc), "executor", False)
    assert got == {"outcome": "denied", "code": "APPROVER_IS_BENEFICIARY"}, got


def test_the_verifier_refuses_a_non_ascii_approver_name():
    _store, svc, _clock, wg = kit.make()
    svc.directory[norm("p\u0430t@example.com")] = frozenset({"support_lead"})
    req = kit.request()
    ap = kit.sign(svc, req, [("p\u0430t@example.com", "support_lead")])
    assert kit.ex(wg, req, ap, "executor", False)["code"] == "KEY_INVALID"


def test_an_nfd_beneficiary_is_refused_while_the_precomposed_one_is_accepted():
    _store, svc, _clock, wg = kit.make()
    pre, nfd = "Jos\u00e9@example.com", unicodedata.normalize("NFD", "Jos\u00e9@example.com")
    assert pre != nfd
    ok = kit.request(beneficiary=pre)
    assert kit.ex(wg, ok, kit.sign(svc, ok), "executor", True)["outcome"] == "dry_run"
    bad = kit.request(beneficiary=nfd)
    assert kit.ex(wg, bad, kit.sign(svc, bad), "executor", True) == {"outcome": "denied", "code": "KEY_INVALID"}


# ---------------------------------------------------------------- M3: void is a withdrawal
def _proposed(wg_kit):
    store, svc, _clock, wg = wg_kit
    req = kit.request()
    key = kit.key_of(req)
    assert kit.reserve(store, "t1", key, "c1", "ord-1", 2500, "USD", kit.START) is None
    return store, svc, wg, req, key


def test_a_voided_key_cannot_be_executed_even_with_a_valid_signed_approval():
    store, svc, wg, req, key = _proposed(kit.make())
    ap = kit.sign(svc, req)
    assert wg.void("executor", "t1", key, "rejected by the lead") == {"outcome": "ok", "code": None, "released": 1}
    assert store.reservations("t1") == [] and store.is_voided("t1", key)
    assert kit.ex(wg, req, ap, "executor", False) == {"outcome": "denied", "code": "KEY_VOIDED"}
    assert kit.ex(wg, req, ap, "executor", True) == {"outcome": "denied", "code": "KEY_VOIDED"}
    assert store.count_applied() == 0
    refused = [json.loads(r["detail"]) for r in store.audit_rows() if r["event"] == "refused"]
    assert [d["code"] for d in refused] == ["KEY_VOIDED", "KEY_VOIDED"]
    other = kit.request(amount_minor="2600")
    assert kit.ex(wg, other, kit.sign(svc, other), "executor", False)["outcome"] == "applied", (
        "a NEW key (other amount) is a new proposal"
    )


def test_an_applied_key_still_replays_after_a_void_and_a_second_void_is_harmless():
    _store, svc, wg, req, key = _proposed(kit.make())
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"
    assert wg.void("executor", "t1", key, "late withdrawal")["code"] is None
    assert wg.void("executor", "t1", key, "late withdrawal")["released"] == 0
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "duplicate_ignored", (
        "the replay is answered before the tombstone is read"
    )


@pytest.mark.parametrize("key", ["", "k", "g" * 64, "A" * 64, "a" * 63, "a" * 65, 5, None])
def test_void_takes_only_a_64_hex_business_key(key):
    store, _svc, _clock, wg = kit.make()
    assert wg.void("executor", "t1", key, "a proper reason") == {"outcome": "denied", "code": "KEY_INVALID"}
    assert not store.is_voided("t1", key if isinstance(key, str) else "x")


@pytest.mark.parametrize("reason", ["", "abc", "   ", "caf\u00e9 withdrawn", "line\nbreak", None, 5])
def test_reasons_need_a_floor_and_are_ascii(reason):
    _store, _svc, _clock, wg = kit.make()
    assert wg.void("executor", "t1", "a" * 64, reason)["code"] == "KEY_INVALID"
    assert wg.set_kill_switch("kill_switch_operator", True, reason)["code"] == "KEY_INVALID"
    assert wg.void("executor", "t1", "a" * 64, "x" * config.REASON_MIN)["code"] is None


# ---------------------------------------------------------------- design B: every writer is typed under a busy lock
def _busy_gate(tmp_path):
    path = str(tmp_path / "busy.sqlite")
    store = Store(path, timeout_s=0.2)
    svc = ApprovalIssuer(kit.DIRECTORY, key=b"k" * 32)
    wg = WriteGate(store, svc.verifier(), kit.Clock())
    holder = sqlite3.connect(path, isolation_level=None)
    holder.execute("BEGIN IMMEDIATE")
    return store, wg, holder


@pytest.mark.parametrize(
    "call",
    [
        lambda wg: wg.set_kill_switch("kill_switch_operator", True, "emergency stop"),
        lambda wg: wg.void("executor", "t1", "a" * 64, "withdrawn"),
        lambda wg: wg.sweep("sweeper"),
        lambda wg: wg.execute(kit.request(), {}, "executor", False),
    ],
    ids=["kill switch", "void", "sweep", "execute"],
)
def test_a_busy_write_lock_is_a_typed_store_busy_deny_on_every_entry_point(tmp_path, call):
    _store, wg, holder = _busy_gate(tmp_path)
    t0 = time.monotonic()
    try:
        out = call(wg)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"raised {type(e).__name__}")
    finally:
        holder.execute("ROLLBACK")
        holder.close()
    assert out == {"outcome": "denied", "code": "STORE_BUSY"} and time.monotonic() - t0 < 5


# ---------------------------------------------------------------- design C: the signer fails closed
def _no_cryptography(monkeypatch):
    real = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name, *a, **k: None if name == "cryptography" else real(name, *a, **k)
    )


def test_without_the_ed25519_extra_there_is_no_default_signer(monkeypatch):
    _no_cryptography(monkeypatch)
    with pytest.raises(SignerNotConfigured):
        default_kind()
    with pytest.raises(SignerNotConfigured):
        ApprovalIssuer(desk.DIRECTORY)
    with pytest.raises(SignerNotConfigured):
        desk.Desk(Store(), ApprovalIssuer(desk.DIRECTORY), lambda: desk.DEMO_NOW)


def test_a_minting_verifier_needs_an_explicit_dev_opt_in(monkeypatch):
    _no_cryptography(monkeypatch)
    dev = ApprovalIssuer(desk.DIRECTORY, key=b"k" * 32).verifier()
    assert dev.can_mint is True and "dev, can mint" in dev.signer_kind
    explicit = ApprovalIssuer(desk.DIRECTORY, signer=HmacSigner(b"s" * 32)).verifier()
    assert explicit.can_mint is True


@pytest.mark.parametrize("key", [b"", b"short", b"x" * 15, "text-key", 5])
def test_an_empty_or_short_hmac_key_is_refused(key):
    with pytest.raises(ValueError):
        HmacSigner(key)


# ---------------------------------------------------------------- m1: normalise first, then join
@pytest.mark.parametrize(
    "spelled",
    [
        "evil.  example",
        "evil.\texample",
        "evil.\nexample",
        "evil.\u00a0example",
        "evil.\u200b example",
        "evil.\u3000example",
        "evil. \u200b\u200b example",
    ],
)
def test_any_whitespace_or_hidden_character_after_the_dot_still_makes_a_host(spelled):
    p = "pat@example.com"
    assert "UNLISTED_LINK" in guards.egress_check(f"see {spelled} now", p, p), repr(spelled)


def test_prose_with_a_capital_after_the_dot_is_still_prose():
    p = "pat@example.com"
    for prose in ("Thanks.\nRegards, the team.", "Done.  Next steps follow.", "Order total 12.50.\tThen we ship."):
        assert guards.egress_check(prose, p, p) == [], prose


# ---------------------------------------------------------------- m8: the window is derived, a runaway clock is refused
def test_the_window_comes_from_the_store_and_a_far_future_at_is_refused():
    store = Store()
    assert kit.reserve(store, "t1", "a" * 64, "c1", "o1", 100, "USD", kit.START) is None
    for bad in ("2099-01-01T00:00:00Z", "not a time", None, "2026-10-20 12:00:00"):
        with pytest.raises(ValueError):
            kit.reserve(store, "t1", "b" * 64, "c2", "o2", 100, "USD", bad)  # type: ignore[arg-type]
    assert [r["key"] for r in store.reservations("t1")] == ["a" * 64]
    assert "since" not in store.reserve.__code__.co_varnames[: store.reserve.__code__.co_argcount], "no caller-supplied window"


def test_propose_side_lockout_is_bounded_by_the_unapproved_share_and_a_void_relieves_it():
    """Stated behaviour (README): a flood can hold at most the unapproved share, new proposals then get PENDING_CAP until a hold is voided or the TTL passes;
    execute of a legitimate, already-approved request is NOT blocked (see test_review8)."""
    store = Store()
    share = config.LIMITS["USD"].store_day_cap // config.UNAPPROVED_SHARE_DEN
    n = share // 2500
    for i in range(n):
        assert kit.reserve(store, "t1", f"{i:064x}", f"c{i}", f"o{i}", 2500, "USD", kit.START, sender=f"s{i}@x.example") is None
    assert kit.reserve(store, "t1", "f" * 64, "cz", "oz", 2500, "USD", kit.START, sender="sz@x.example") == "PENDING_CAP"
    _s, _svc, _c, wg = kit.make()
    wg2 = WriteGate(store, ApprovalIssuer(kit.DIRECTORY, key=b"k" * 32).verifier(), kit.Clock())
    assert wg2.void("executor", "t1", f"{0:064x}", "operator relief")["released"] == 1
    assert kit.reserve(store, "t1", "f" * 64, "cz", "oz", 2500, "USD", kit.START, sender="sz@x.example") is None
    del wg


# ---------------------------------------------------------------- desk merge dedupe (the recorded reservation of the same ref counts once)
def test_a_reservation_known_to_both_the_recorded_state_and_the_store_counts_once():
    recorded = {"open_reservations": [{"request_ref": "r1", "customer_id": "c1", "amount_minor": "5", "order_id": "o"}]}
    store = {
        "open_reservations": [
            {"request_ref": "r1", "customer_id": "c1", "amount_minor": "5", "order_id": "o"},
            {"request_ref": "r2", "customer_id": "c1", "amount_minor": "6", "order_id": "o"},
        ],
        "store_day_refunded_minor": {"USD": "0"},
        "open_proposals": {"cluster": 2, "sender": 1},
    }
    merged = desk._merge_state(recorded, store, "USD")
    assert [r["request_ref"] for r in merged["open_reservations"]] == ["r1", "r2"]


# ---------------------------------------------------------------- the core copy pin, the table and the seam
def test_the_core_copy_is_byte_for_byte_what_the_pin_says():
    """Each copy, with its import rewrite reversed, hashes to the core file's pinned sha256 (LF). Same check as tools/core_sync_check.py."""
    pin = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    assert pin["files"], "no pinned copies"
    for demo_path, meta in pin["files"].items():
        raw = (ROOT / demo_path).read_bytes()
        assert b"\r\n" not in raw, "LF only"
        text = raw.decode("utf-8")
        for core_import, demo_import in meta.get("import_rewrite", []):
            text = text.replace(demo_import, core_import)
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == meta["core_sha256"], (
            f"{demo_path} was edited: re-copy it from core, never patch it here"
        )
        assert meta["core_pr"] == 50 and meta["pr_snapshot"] == "153d217"


def test_the_promotion_table_names_every_copy_every_core_pr_and_the_pin_note():
    md = (ROOT / "CORE_COPIES.md").read_text(encoding="utf-8")
    pin = json.loads((ROOT / "core_copies.json").read_text(encoding="utf-8"))
    for demo_path, meta in pin["files"].items():
        assert meta["core_path"] in md.replace("hadavin_sdk/", "src/hadavin_sdk/") or meta["core_path"] in md
        assert demo_path in md
    for needle in (
        "PR 49",
        "PR 50",
        "textnorm",
        "egress",
        "signers",
        "reserve",
        "660814674ece8ad578293e5412633d796eddb96f",
        "153d217",
        "not been through an independent result review",
    ):
        assert needle in md, needle
    for f in (
        "src/refunds/textnorm.py",
        "src/refunds/guards.py",
        "src/refunds/signers.py",
        "src/refunds/store.py",
        "src/refunds/approval.py",
        "src/refunds/core_seam.py",
    ):
        assert f in md, f


def _core_args(**kw):
    created = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    base = {
        "tenant": "t1", "key": "a" * 64, "scopes": ["c1"], "actor": "s@x.example", "unit": "USD", "amount": 100, "created_at": created,
        "since": created - timedelta(seconds=config.APPROVAL_TTL_S), "max_per_scope": config.MAX_PENDING_PER_CUSTOMER,
        "max_per_actor": config.MAX_PENDING_PER_SENDER,
        "unit_caps": {u: lim.store_day_cap // config.UNAPPROVED_SHARE_DEN for u, lim in config.LIMITS.items()},
    }  # fmt: skip
    return {**base, **kw}


def test_the_seam_accepts_the_core_shape_and_answers_in_core_codes():
    store = Store()
    assert core_seam.reserve_core_shape(store, **_core_args()) is None
    assert core_seam.reserve_core_shape(store, **_core_args()) is None, "idempotent, as in core"
    for i in range(config.MAX_PENDING_PER_CUSTOMER - 1):
        assert core_seam.reserve_core_shape(store, **_core_args(key=f"{i + 1:064x}", actor=f"s{i}@x.example")) is None
    assert core_seam.reserve_core_shape(store, **_core_args(key="b" * 64, actor="other@x.example")) == "OPEN_LIMIT"
    assert (
        core_seam.reserve_core_shape(store, **_core_args(key="c" * 64, unit="EUR", unit_caps={**_core_args()["unit_caps"]}))
        == "UNIT_UNKNOWN"
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"created_at": datetime(2026, 10, 20, 12, 0)},
        {"since": datetime(2000, 1, 1, tzinfo=UTC)},
        {"max_per_scope": 99},
        {"unit_caps": {"USD": 1}},
    ],
)
def test_the_seam_refuses_a_shape_it_would_have_to_guess(bad):
    with pytest.raises(ValueError):
        core_seam.reserve_core_shape(Store(), **_core_args(**bad))


# ---------------------------------------------------------------- the identity table's per-action justification is complete
def _covered(action: str, why: dict) -> bool:
    for k in why:
        for part in k.split("/"):
            if part == action or (part.endswith(".*") and action.startswith(part[:-1])):
                return True
    return False


def test_every_allowed_action_of_every_identity_has_a_justification():
    missing = [(i, a) for i, e in identities.IDENTITIES.items() for a in sorted(e["allow"]) if not _covered(a, e["why"])]
    assert missing == [], missing
    assert "NO credentials" in identities.__doc__, "the module says plainly that stage 1 has no credentials"


# ---------------------------------------------------------------- the store contract, wider
def check_store_contract_wider(make_store):
    from refunds.writegate import FMT

    s = make_store()
    rec = {
        "tenant": "t1", "key": "a" * 64, "action": "refund", "order_id": "o1", "line_ids": ["l1"], "amount_minor": 700, "currency": "USD",
        "customer_id": "c1", "approval_id": "ap-1", "applied_at": "2026-10-20T12:00:00Z", "day": "2026-10-20",
    }  # fmt: skip
    s.insert_applied(rec)
    assert s.count_applied() == 1 and s.count_applied("t1") == 1 and s.count_applied("t2") == 0
    assert s.get_applied("t1", "a" * 64)["amount_minor"] == 700 and s.get_applied("t2", "a" * 64) is None
    assert s.sum_order("t1", "o1", "USD") == 700 and s.sum_order("t1", "o1", "GBP") == 0 and s.sum_order("t2", "o1", "USD") == 0
    assert s.sum_day("t1", "USD", "2026-10-20") == 700 and s.sum_day("t1", "USD", "2026-10-21") == 0
    assert s.sum_customers_since("t1", ["c1", "c1"], "USD", "2026-10-20T00:00:00Z") == 700, "a repeated id counts once"
    assert s.sum_customers_since("t1", ["c1"], "USD", "2026-10-21T00:00:00Z") == 0
    assert len(s.order_rows("t1", "o1")) == 1 and s.order_rows("t2", "o1") == []
    s.add_compensation_record("t1", "a" * 64, {"kind": "compensation_record"})
    assert s.compensation_records("t1") == [{"kind": "compensation_record"}] and s.compensation_records("t2") == []
    s.set_kill_switch(True, "kill_switch_operator", "a drill", "2026-10-20T12:00:00Z")
    ks = s.kill_switch()
    assert ks["on"] is True and ks["operator"] == "kill_switch_operator" and ks["reason"] == "a drill"
    assert kit.reserve(s, "t1", "b" * 64, "c1", "o2", 100, "USD", kit.START) is None
    state = s.open_state("t1", ["c1"], "s@x.example", "USD", kit.START, "2026-10-20")
    assert [r["request_ref"] for r in state["open_reservations"]] == ["b" * 64] and state["store_day_refunded_minor"] == {
        "USD": "700"
    }
    assert state["open_proposals"] == {"cluster": 1, "sender": 1}
    assert s.open_state("t1", ["c1"], "s@x.example", "USD", kit.START, "2026-10-20", exclude_key="b" * 64)["open_proposals"] == {
        "cluster": 0,
        "sender": 0,
    }
    assert (
        s.other_reserved("t1", "USD", "z" * 64, "2026-10-19T00:00:00Z") == 100
        and s.other_reserved("t1", "USD", "b" * 64, "2026-10-19T00:00:00Z") == 0
    )
    assert s.sweep_reservations("2026-10-21T00:00:00Z", "2026-10-21T00:00:00Z") == 1 and s.reservations("t1") == []
    assert s.is_voided("t1", "c" * 64) is False
    s.void_key("t1", "c" * 64, "withdrawn", "executor", "2026-10-20T12:00:00Z")
    s.void_key("t1", "c" * 64, "again", "executor", "2026-10-20T12:00:01Z")
    assert s.is_voided("t1", "c" * 64) and not s.is_voided("t2", "c" * 64)
    assert s.audit_chain_ok()
    s.audit("t1", "e", {"k": 1}, "2026-10-20T12:00:00Z")
    assert s.audit_chain_ok()
    del FMT


def test_the_wider_contract_holds_for_sqlite_in_memory_and_on_a_file(tmp_path):
    check_store_contract_wider(Store)
    check_store_contract_wider(lambda: Store(str(tmp_path / "wide.sqlite")))


def test_a_tampered_audit_row_breaks_the_chain():
    s = Store()
    s.audit("t1", "e", {"k": 1}, "2026-10-20T12:00:00Z")
    s.audit("t1", "e", {"k": 2}, "2026-10-20T12:00:01Z")
    assert s.audit_chain_ok()
    with s.transaction() as db:
        db.execute("UPDATE audit SET detail = ? WHERE seq = 1", ('{"k":99}',))
    assert s.audit_chain_ok() is False


def test_a_requester_that_is_a_look_alike_of_an_approver_is_caught_by_the_verifier_even_when_called_directly():
    """The write path refuses non-ASCII requesters first; the verifier is the second line and must not depend on that."""
    _store, svc, clock, wg = kit.make()
    now = datetime.fromisoformat(clock()).astimezone(UTC)
    fake = "".join(CYR.get(c, c) for c in APPROVER)
    assert fake != APPROVER and not fake.isascii()
    req = kit.request(requester=fake)
    ap = kit.sign(svc, req, [(APPROVER, "support_lead")])
    got = wg.approvals.verify(
        ap, args_hash=hash_request(req, kit.key_of(req)), tenant_id="t1", tier="human", requested_at=req["requested_at"], min_tier="human", requester=fake, beneficiary="x@example.com", now=now,
    )  # fmt: skip
    assert got == "REQUESTER_IS_APPROVER"


def test_the_scan_reads_the_normalised_lowercase_text_so_an_allowed_link_written_in_capitals_is_allowed():
    p = "pat@example.com"
    link = "https://help.example.com/returns"
    assert guards.egress_check("see HTTPS://HELP.EXAMPLE.COM/RETURNS now", p, p, allowed_links=frozenset({link})) == []
    assert "UNLISTED_LINK" in guards.egress_check("see HTTPS://HELP.EXAMPLE.COM/OTHER now", p, p, allowed_links=frozenset({link}))

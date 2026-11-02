"""Generic controls promoted from the refunds demo (review 8) and hardened by the PR #49 reviews: identity text, reply check,
reservation limits (pure part), signed approvals, intent-call-settle, refusal events, the kill-switch `by` text.
The Store half of reservations is in tests/contracts/test_store.py (memory and postgres)."""

import time
from datetime import UTC, datetime, timedelta
from typing import ClassVar

import pytest

from hadavin_sdk.actions import outbox
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.audit.refusal import refusal_event, refusal_fields
from hadavin_sdk.guard.identity_text import (
    exact_key,
    identity_key,
    lookalike_of,
    same_person,
    same_recipient,
    text_ok,
    unique_ids,
)
from hadavin_sdk.guard.reply_check import ReplyPolicy, reply_violations
from hadavin_sdk.guard.textnorm import fold
from hadavin_sdk.models import RunState
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.reservations import check_ordered_limits

LOOKALIKE = ["\u0301", "\ufe0f", "\u3164", "\u00a0", "\u200b", "\u3000"]
CYR_E, CYR_C, GREEK_O = "\u0435", "\u0441", "\u03bf"


# ---------------------------------------------------------------- identity text
@pytest.mark.parametrize("ch", LOOKALIKE)
def test_hidden_and_space_characters_are_refused_as_text_and_never_become_a_different_key(ch):
    real = "lead@desk.example"
    assert text_ok(real) and not text_ok(real + ch) and not text_ok(real[:4] + ch + real[4:])
    assert identity_key(real + ch) is None and not same_person(real + ch, real)


def test_confusable_letters_are_refused_by_default_and_fold_to_the_skeleton_on_request():
    real = "lead@desk.example"
    fake = real.replace("e", CYR_E, 1)
    assert text_ok(fake), "text_ok alone does not see a look-alike letter"
    assert identity_key(fake) is None and not same_person(fake, real)
    assert same_person(fake, real, lookalikes="fold"), (
        "folded: a disguised copy collides with the real id (fails safe)"
    )
    assert identity_key("Jos\u00e9", lookalikes="fold") == "jose"
    assert identity_key("l" + GREEK_O + "ad") is None


def test_exact_key_keeps_accents_so_a_different_mailbox_does_not_match():
    assert exact_key("Jos\u00e9@x.example") == exact_key("jos\u00e9@X.example")
    assert not same_recipient("jose@x.example", "jos\u00e9@x.example")
    assert same_person("jose@x.example", "jos\u00e9@x.example", lookalikes="fold"), (
        "SoD direction over-matches on purpose"
    )
    assert (
        exact_key("jose@x.example" + "\u200b") is None
        and exact_key(5) is None
        and exact_key(" ") is None
    )


def test_text_ok_bounds_and_unique_ids():
    assert (
        not text_ok("") and not text_ok("x" * 300) and text_ok("x" * 300, 300) and not text_ok(None)
    )
    assert text_ok("Jos\u00e9 Garc\u00eda") and not text_ok("e\u0301")
    assert (
        unique_ids(["a", "b"], max_n=3)
        and not unique_ids(["a", "a"], max_n=3)
        and not unique_ids(["a"] * 4, max_n=3)
    )
    assert (
        not unique_ids([], max_n=3)
        and not unique_ids(["A"], max_n=3)
        and not unique_ids("ab", max_n=3)
    )


# ---------------------------------------------------------------- reply check
ME = "a@b.example"


def test_reply_check_is_typed_and_refuses_oversized_text():
    for bad in (None, 5, b"x", ["a"]):
        assert reply_violations(bad, ME, ME) == ["TEXT_NOT_STRING"]
    assert reply_violations("hi", None, ME) == ["TEXT_NOT_STRING"]
    assert reply_violations("a" * 20_001, ME, ME) == ["TEXT_TOO_LONG"]
    assert reply_violations("a" * 11, ME, ME, policy=ReplyPolicy(max_text=10)) == ["TEXT_TOO_LONG"]
    with pytest.raises(ValueError):
        ReplyPolicy(max_text=0)
    with pytest.raises(ValueError):
        ReplyPolicy(allowed_patterns=("(",))


def test_homoglyph_hosts_and_addresses_are_violations_whatever_they_fold_to():
    assert "UNLISTED_LINK" in reply_violations(f"see {CYR_E}vil.com", ME, ME)
    assert "UNLISTED_LINK" in reply_violations(f"see evil.{CYR_C}om", ME, ME)
    allowed = ReplyPolicy(allowed_hosts=frozenset({"example.com"}))
    assert reply_violations("see example.com", ME, ME, policy=allowed) == []
    out = reply_violations(f"see {CYR_E}xample.com", ME, ME, policy=allowed)
    assert "NON_ASCII_HOST" in out, "a Cyrillic copy of an allowed host must not pass as that host"
    assert "UNLISTED_ADDRESS" in reply_violations(f"write to {CYR_C}@b.example", ME, ME)
    assert "UNLISTED_LINK" in reply_violations("see evil.xn--p1ai", ME, ME), (
        "punycode TLD is a host"
    )


def _not_verified(out):
    """RECIPIENT_NOT_VERIFIED, with at most the look-alike signal beside it (a hidden-character variant folds equal but is not safe_equal)."""
    return "RECIPIENT_NOT_VERIFIED" in out and set(out) <= {
        "RECIPIENT_NOT_VERIFIED",
        "RECIPIENT_LOOKALIKE",
    }


def test_recipient_is_compared_exactly_not_through_the_accent_dropping_fold():
    assert reply_violations("hi", "jose@x.example", "jos\u00e9@x.example") == [
        "RECIPIENT_LOOKALIKE",
        "RECIPIENT_NOT_VERIFIED",
    ]
    assert reply_violations("hi", "Jos\u00e9@X.example", "jos\u00e9@x.example") == []
    assert reply_violations(
        "write jose@x.example", "jos\u00e9@x.example", "jos\u00e9@x.example"
    ) == ["UNLISTED_ADDRESS"]
    assert reply_violations("hi", ME, None) == ["RECIPIENT_NOT_VERIFIED"]
    assert _not_verified(reply_violations("hi", ME + "\u200b", ME))


def test_allow_lists_match_on_the_same_folded_form_as_the_text():
    p = ReplyPolicy(allowed_links=frozenset({"https://Help.Example.com/Caf\u00e9?Id=1"}))
    assert (
        reply_violations("see https://Help.Example.com/Caf\u00e9?Id=1 now", ME, ME, policy=p) == []
    )
    assert "UNLISTED_LINK" in reply_violations(
        "see https://help.example.com/other", ME, ME, policy=p
    )
    assert (
        reply_violations(
            "see HELP.EXAMPLE.COM",
            ME,
            ME,
            policy=ReplyPolicy(allowed_hosts=frozenset({"Help.Example.com"})),
        )
        == []
    )


def test_allowed_patterns_keep_filenames_and_ids_from_tripping_the_scans():
    assert "UNLISTED_LINK" in reply_violations("attached invoice-12.pdf", ME, ME)
    p = ReplyPolicy(
        allowed_patterns=(
            r"invoice-\d{1,6}\.pdf",
            r"[A-Z]{2}\d{2} [A-Z]{2}\d{2} [A-Z]{2}\d{2} [A-Z]{2}\d{2}",
        )
    )
    assert (
        reply_violations("attached invoice-12.pdf, ref AB12 CD34 EF56 GH78", ME, ME, policy=p) == []
    )
    assert "BANK_PATTERN" in reply_violations("ref AB12 CD34 EF56 GH78", ME, ME)
    assert "BANK_PATTERN" in reply_violations("pay GB29 NWBK 6016 1331 9268 19", ME, ME, policy=p)


def test_spaced_dots_and_other_attachments():
    for spelled in ("evil .example", "evil . example", "evil[.]example", "evil\u3002example/pay"):
        assert "UNLISTED_LINK" in reply_violations(spelled, ME, ME), spelled
    assert reply_violations("Total 12.50, ticket 4521. Thanks.", ME, ME) == []
    assert reply_violations("hi", ME, ME, attachments=("x.pdf",)) == ["UNLISTED_ATTACHMENT"]
    assert (
        reply_violations(
            "hi",
            ME,
            ME,
            attachments=("x.pdf",),
            policy=ReplyPolicy(allowed_attachments=frozenset({"x.pdf"})),
        )
        == []
    )


def _best(text, n=3):
    best = 1e9
    for _ in range(n):
        t0 = time.perf_counter()
        reply_violations(text, ME, ME)
        best = min(best, time.perf_counter() - t0)
    return best


@pytest.mark.parametrize("unit", ["a-", "x.", "1.", "a@", "a", "\u0435."])
def test_every_scan_is_linear_not_quadratic(unit):
    """Doubling the text may at most ~triple the time (a quadratic scan quadruples it); min of three runs, no absolute limit."""
    small, large = (unit * 10_000)[:8_000], (unit * 20_000)[:16_000]
    _best(small, 1)
    a, b = _best(small), _best(large)
    assert b < max(a * 3.2, 0.01), (unit, a, b)


# ---------------------------------------------------------------- ordered limits (pure)
def test_limit_tables_are_validated_with_named_fields():
    order = ("one_approver_max", "customer_cap", "hard_cap", "day_cap")
    ok = {
        "USD": {
            "one_approver_max": 7500,
            "customer_cap": 30000,
            "hard_cap": 50000,
            "day_cap": 250000,
        }
    }
    check_ordered_limits(ok, order, strict_before=("hard_cap",))
    row = ok["USD"]
    for bad in (
        {**row, "customer_cap": 50000},
        {**row, "one_approver_max": 40000},
        {**row, "day_cap": 40000},
        {**row, "day_cap": 0},
        {**row, "hard_cap": True},
    ):
        with pytest.raises(ValueError):
            check_ordered_limits({"USD": bad}, order, strict_before=("hard_cap",))
    check_ordered_limits({"X": {**row, "customer_cap": 50000, "hard_cap": 50000}}, order)
    with pytest.raises(ValueError):
        check_ordered_limits({"USD": {"hard_cap": 1}}, order)


# ---------------------------------------------------------------- signed approvals
def _signed():
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric import ed25519

    from hadavin_sdk.approvals import signed
    from hadavin_sdk.audit.signer import LocalSigner

    s = LocalSigner(ed25519.Ed25519PrivateKey.generate())
    return signed, s


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _body(**kw):
    return {
        "approval_id": "ap-1",
        "tenant_id": "t",
        "args_hash": "h" * 8,
        "requested_at": NOW.isoformat(),
        **kw,
    }


def _verify(v, ap, **kw):
    args = {
        "tenant_id": "t",
        "args_hash": "h" * 8,
        "now": NOW,
        "max_age": timedelta(hours=24),
        **kw,
    }
    return v.verify(ap, **args)


def test_signed_approval_checks_tenant_hash_age_and_single_use():
    signed, s = _signed()
    ap = signed.issue(s, _body())
    v = signed.ApprovalVerifier.single(s.public_key(), s.alg, s.key_id)
    assert v.can_mint is False and not hasattr(v, "sign") and _verify(v, ap).ok
    assert _verify(v, ap, tenant_id="u").reason == "TENANT_MISMATCH"
    assert _verify(v, ap, args_hash="x").reason == "HASH_MISMATCH"
    assert _verify(v, ap, now=NOW + timedelta(hours=24)).ok, "exactly max_age is still valid"
    assert _verify(v, ap, now=NOW + timedelta(hours=24, seconds=1)).reason == "EXPIRED"
    assert _verify(v, ap, now=NOW - timedelta(seconds=1)).reason == "FROM_FUTURE"
    used = set()
    first = _verify(v, ap, consume=lambda i: not (i in used or used.add(i)))
    assert (
        first.ok
        and _verify(v, ap, consume=lambda i: not (i in used or used.add(i))).reason
        == "ALREADY_USED"
    )


def test_signed_approval_refuses_forgery_extra_fields_and_odd_signature_encodings():
    signed, s = _signed()
    ap = signed.issue(s, _body())
    v = signed.ApprovalVerifier.single(s.public_key(), s.alg, s.key_id)
    for bad in (
        {**ap, "note": "x"},
        {**ap, "tenant_id": "u"},
        {**ap, "sig": ap["sig"].upper()},
        {**ap, "sig": " " + ap["sig"][1:]},
        {**ap, "sig": ap["sig"][:-2] + ("01" if ap["sig"][-2:] == "00" else "00")},
        {**ap, "sig": "zz"},
        {**ap, "key_id": "other"},
        None,
        "x",
    ):
        assert not _verify(v, bad).ok, bad
    other = _signed()[1]
    assert _verify(v, signed.issue(other, _body())).reason in ("UNKNOWN_KEY", "BAD_SIGNATURE")
    with pytest.raises(ValueError):
        signed.issue(s, {**_body(), "extra": 1})


def test_signed_approval_verifier_validates_algorithm_and_key_and_rotates_by_key_id():
    from hadavin_sdk.errors import ConfigError

    signed, s = _signed()
    pub = s.public_key()
    for bad in (("hmac", pub), ("ed25519", pub[:-1]), ("ecdsa-p256", pub)):
        with pytest.raises(ConfigError):
            signed.ApprovalVerifier({"k": bad})
    with pytest.raises(ConfigError):
        signed.ApprovalVerifier({})
    s2 = _signed()[1]
    v = signed.ApprovalVerifier(
        {s.key_id: ("ed25519", pub), s2.key_id: ("ed25519", s2.public_key())}
    )
    assert _verify(v, signed.issue(s, _body())).ok and _verify(v, signed.issue(s2, _body())).ok


def test_signed_approval_schema_is_a_parameter_and_key_id_is_signed():
    signed, s = _signed()
    schema = signed.Schema(
        fields=("approval_id", "tenant_id", "args_hash", "requested_at", "tier", "steps")
    )
    ap = signed.issue(s, _body(tier="human", steps=[{"person": "p", "role": "r"}]), schema)
    v = signed.ApprovalVerifier.single(s.public_key(), s.alg, s.key_id, schema)
    assert _verify(v, ap).ok and not _verify(v, {**ap, "tier": "four_eyes"}).ok
    assert not _verify(signed.ApprovalVerifier.single(s.public_key(), s.alg, s.key_id), ap).ok, (
        "other schema: not accepted"
    )
    from hadavin_sdk.errors import ConfigError

    with pytest.raises(ConfigError):
        signed.Schema(fields=("approval_id", "tenant_id", "args_hash", "requested_at", "sig"))


# ---------------------------------------------------------------- outbox
class _Audit:
    def __init__(self, fail_intent=False):
        self.intents, self.outcomes, self.fail_intent = [], [], fail_intent

    def write_intent(self, event):
        if self.fail_intent:
            raise AuditUnavailable("down")
        self.intents.append(event)
        return "k"

    def write_outcome(self, event):
        self.outcomes.append(event)
        return "k"


class _Proc:
    def __init__(self, script=(), lookups=None):
        self.script, self.lookups, self.calls = list(script), lookups or {}, 0

    def apply(self, key):
        self.calls += 1
        r = self.script.pop(0) if self.script else outbox.Applied("ref-1")
        if isinstance(r, Exception):
            raise r
        return r

    def lookup(self, key):
        r = self.lookups.get(key)
        if isinstance(r, Exception):
            raise r
        return r


def _box(**kw):
    store, audit, proc = (
        MemoryStore(),
        _Audit(**{k: v for k, v in kw.items() if k == "fail_intent"}),
        _Proc(kw.get("script", ()), kw.get("lookups")),
    )
    return store, audit, proc, outbox.Outbox(store, audit, proc)


def test_outbox_applies_once_and_a_replay_never_calls_the_processor():
    _s, audit, proc, box = _box()
    r = box.run("k1")
    assert (r.status, r.ref, r.attempt) == (outbox.Status.APPLIED, "ref-1", 1) and proc.calls == 1
    again = box.run("k1")
    assert again.status is outbox.Status.DUPLICATE and again.ref == "ref-1" and proc.calls == 1
    assert [e.operation for e in audit.intents] == ["intent"] and [
        e.operation for e in audit.outcomes
    ] == ["applied"]


def test_not_applied_frees_the_key_and_a_retry_calls_the_processor_again():
    _store, audit, proc, box = _box(script=[outbox.NotApplied("refused before effect")])
    assert box.run("k1").status is outbox.Status.NOT_APPLIED and proc.calls == 1
    r = box.run("k1")
    assert r.status is outbox.Status.APPLIED and r.attempt == 2 and proc.calls == 2, (
        "retry after a definite failure"
    )
    assert len(audit.intents) == 2


def test_unknown_stays_open_and_is_never_blindly_retried():
    _s, _a, proc, box = _box(script=[outbox.Unknown("timeout")])
    assert box.run("k1").status is outbox.Status.UNKNOWN
    assert box.run("k1").status is outbox.Status.IN_DOUBT and proc.calls == 1, (
        "no second call while an attempt is open"
    )


def test_an_open_attempt_is_resolved_by_lookup_on_the_next_run():
    _s, _a, proc, box = _box(script=[outbox.Unknown("t")], lookups={"k1": outbox.Applied("ref-9")})
    assert box.run("k1").status is outbox.Status.UNKNOWN
    r = box.run("k1")
    assert r.status is outbox.Status.APPLIED and r.ref == "ref-9" and proc.calls == 1
    _s2, _a2, proc2, box2 = _box(
        script=[outbox.Unknown("t")], lookups={"k1": outbox.NotApplied("never reached")}
    )
    box2.run("k1")
    assert box2.run("k1").status is outbox.Status.APPLIED and proc2.calls == 2, (
        "lookup says not applied: a new attempt"
    )


def test_audit_down_means_no_effect():
    _s, _a, proc, box = _box(fail_intent=True)
    assert box.run("k1").status is outbox.Status.AUDIT_UNAVAILABLE and proc.calls == 0


def test_a_programmer_error_propagates_and_leaves_the_attempt_open():
    store, _a, _p, box = _box(script=[ZeroDivisionError("bug")])
    with pytest.raises(ZeroDivisionError):
        box.run("k1")
    assert [
        r.state for r in store.list_runs(RunState.EXECUTING, datetime.now(UTC) + timedelta(days=1))
    ] == [RunState.EXECUTING]
    assert box.run("k1").status is outbox.Status.IN_DOUBT


def test_reconcile_settles_isolates_failures_and_escalates_stale_attempts():
    store, _audit, _proc, box = _box(
        script=[outbox.Unknown("t")] * 4,
        lookups={"a": outbox.Applied("r"), "b": TimeoutError("x"), "c": outbox.NotApplied("n")},
    )
    for k in ("a", "b", "c", "d"):
        box.run(k)
    escalated = []
    later = datetime.now(UTC) + timedelta(hours=2)
    out = box.reconcile(
        now=later,
        min_age=timedelta(minutes=1),
        escalate_after=timedelta(hours=1),
        escalate=escalated.append,
    )
    by_key = {store.get_run(rid).trigger_ref: res for rid, res in out.items()}
    assert by_key == {"a": "applied", "b": "escalated", "c": "not_applied", "d": "escalated"}
    assert len(escalated) == 2 and box.run("d").status is outbox.Status.ESCALATED, (
        "a stopped attempt starts no new one"
    )
    assert box.run("c").status is outbox.Status.APPLIED, "not_applied freed the key"
    young = box.reconcile(now=later, min_age=timedelta(days=1), escalate_after=timedelta(days=2))
    assert young == {}


def test_settle_is_only_if_open_and_a_late_second_settle_loses():
    store, _a, _p, box = _box(script=[outbox.Unknown("t")], lookups={"k": outbox.Applied("r")})
    box.run("k")
    run_id = next(
        iter(store.list_runs(RunState.EXECUTING, datetime.now(UTC) + timedelta(days=1)))
    ).run_id
    store.transition(run_id, RunState.EXECUTING, RunState.SUCCEEDED, "someone else")
    out = box.reconcile(
        now=datetime.now(UTC) + timedelta(hours=1),
        min_age=timedelta(0),
        escalate_after=timedelta(days=1),
    )
    assert out == {}, "already settled elsewhere: not listed as open"
    assert store.get_run(run_id).reason_code == "someone else"


def test_outbox_rejects_unbounded_keys():
    _s, _a, _p, box = _box()
    for bad in ("", "x" * 201, "a\nb", 5):
        with pytest.raises(ValueError):
            box.run(bad)


# ---------------------------------------------------------------- refusal events
def test_refusal_fields_never_carry_caller_content():
    f = refusal_fields("KEY_INVALID", "executor", "k" * 8)
    assert f == {"error_code": "KEY_INVALID", "object_ref": "kkkkkkkk", "principal": "executor"}
    hostile = refusal_fields("bad code\n", "Bob <bob@x.example>\n", "alice@example.com")
    assert (
        all(v.startswith("h:") for v in hostile.values())
        and "alice" not in str(hostile)
        and "bob" not in str(hostile)
    )
    big = refusal_fields("KEY_INVALID", "svc-Agent", "k" * 10_000)
    assert (
        big["object_ref"].startswith("h:")
        and len(big["object_ref"]) == 18
        and big["principal"] == "svc-Agent"
    )
    assert (
        refusal_fields("X", 5, None)["principal"].startswith("h:")
        and refusal_fields("X", "a", None)["object_ref"] == "-"
    )
    assert refusal_fields("X", "a@x.example", None) != refusal_fields("X", "b@x.example", None), (
        "different callers stay distinguishable"
    )
    e = refusal_event("r1", "gate", "KEY_INVALID", "alice@example.com", "alice@example.com")
    assert "alice" not in e.model_dump_json() and e.operation == "refused" and e.decision == "deny"


def test_refusal_event_run_id_and_domain_are_bounded_too():
    e = refusal_event("run\n1" + "x" * 500, "dom ain", "KEY_INVALID", "executor")
    assert e.run_id.startswith("h:") and e.domain.startswith("h:")


# ---------------------------------------------------------------- the kill-switch `by` text
def test_a_hostile_stop_by_is_stored_as_a_hash_and_the_stop_still_happens():
    from hadavin_sdk.limits import Limits
    from hadavin_sdk.models import KillSwitch

    class _Reg:
        agents: ClassVar[dict] = {}

    store = MemoryStore()
    audit = _Audit()
    lim = Limits(store, audit, _Reg())  # type: ignore[arg-type]
    lim.stop("ops\nforged line \u202e")
    ks = store.get_kill_switch()
    assert (
        isinstance(ks, KillSwitch)
        and ks.on
        and ks.by.startswith("h:")
        and audit.outcomes[-1].principal == ks.by
    )
    lim.stop("user:ops")
    assert store.get_kill_switch().by == "user:ops"


# ---------------------------------------------------------------- the flaky G4 false positive on Hadavin ids (test_s4 order dependence)
def test_a_hadavin_id_is_never_taken_for_a_cloud_cmdlet_but_a_real_cmdlet_still_is():
    """A random id such as `pln-ec2c5fce...` matched the cmdlet shape `verb-ec2x` and was withheld, about 1 in 2,000 runs."""
    from hadavin_sdk.approvals.channel import clean

    ids = [
        f"{p}-ec2a{'0' * 28}" for p in ("run", "pln", "apr", "evt")
    ]  # hex ids can only start with the service name 'ec2'
    out = clean(" ".join(ids))
    assert all(i in out for i in ids) and "withheld" not in out
    assert "withheld" in clean("New-ec2xyz -Name x") and "withheld" in clean("Remove-AzVM -Name x")


# ---------------------------------------------------------------- shared vectors (guard.textnorm, also run by PR #50)
def _vec(s):
    import re

    return re.sub(r"\{U\+([0-9A-F]{4})\}", lambda m: chr(int(m.group(1), 16)), s)


def _vectors():
    import json
    from pathlib import Path

    path = Path(__file__).parent / "fixtures" / "textnorm_vectors.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_shared_identity_vector_is_refused_or_collides_and_every_different_one_does_not():
    for item in _vectors()["identities"]:
        real = item["id"]
        for v in map(_vec, item["variants"]):
            assert identity_key(v) is None or same_person(v, real), (
                "default must refuse or collide",
                v,
            )
            assert not text_ok(v) or same_person(v, real, lookalikes="fold"), (
                "fold must collide",
                v,
            )
        for d in map(_vec, item["different"]):
            assert not same_person(d, real, lookalikes="fold"), d


def test_every_shared_domain_vector_is_a_violation_in_a_reply():
    for item in _vectors()["domains"]:
        for v in map(_vec, item["variants"]):
            assert reply_violations(f"visit {v}", ME, ME), v


def test_a_punycode_host_is_matched_whole_so_an_allowed_one_passes_and_another_does_not():
    p = ReplyPolicy(allowed_hosts=frozenset({"shop.xn--p1ai"}))
    assert reply_violations("see shop.xn--p1ai", ME, ME, policy=p) == []
    assert "UNLISTED_LINK" in reply_violations("see shop.xn--80ak6aa92e", ME, ME, policy=p)


def test_a_signed_key_id_cannot_be_swapped_for_an_alias_of_the_same_key():
    signed, s = _signed()
    v = signed.ApprovalVerifier(
        {"k1": ("ed25519", s.public_key()), "k2": ("ed25519", s.public_key())}
    )

    class _Named:
        key_id = "k1"
        alg = s.alg
        sign = staticmethod(s.sign)

    ap = signed.issue(_Named(), _body())  # type: ignore[arg-type]
    assert _verify(v, ap).ok
    assert _verify(v, {**ap, "key_id": "k2"}).reason == "BAD_SIGNATURE"


def test_a_reconcile_with_a_lookup_that_raises_a_bug_still_processes_the_other_keys():
    store, _a, _p, box = _box(
        script=[outbox.Unknown("t")] * 2,
        lookups={"bad": ValueError("boom"), "good": outbox.Applied("r")},
    )
    box.run("bad")
    box.run("good")
    out = box.reconcile(
        now=datetime.now(UTC) + timedelta(hours=1),
        min_age=timedelta(0),
        escalate_after=timedelta(days=1),
    )
    by_key = {store.get_run(rid).trigger_ref: res for rid, res in out.items()}
    assert by_key == {"bad": "error:ValueError", "good": "applied"}


# ---------------------------------------------------------------- evidence-9 items (core side)
def _separators():
    import sys
    import unicodedata

    return [
        chr(c)
        for c in range(sys.maxunicode + 1)
        if unicodedata.category(chr(c)) in ("Zs", "Zl", "Zp") and chr(c) != " "
    ]


def test_every_space_line_and_paragraph_separator_is_refused_as_text_and_never_gives_a_different_identity():
    seps = _separators()
    assert len(seps) >= 8
    real = "lead@desk.example"
    for sep in seps:
        assert not text_ok(real + sep) and not text_ok(real[:4] + sep + real[4:]), hex(ord(sep))
        assert (
            identity_key(real + sep, lookalikes="fold") is None and exact_key(real + sep) is None
        ), hex(ord(sep))
        assert _not_verified(reply_violations("hi", real + sep, real)), hex(ord(sep))


def test_a_space_after_the_dot_before_a_lowercase_word_is_read_as_a_host_but_prose_is_not():
    assert "UNLISTED_LINK" in reply_violations("evil. example", ME, ME)
    assert "UNLISTED_LINK" in reply_violations("go to evil. example now", ME, ME)
    assert reply_violations("Thanks. Regards, the team. See you.", ME, ME) == []
    assert (
        reply_violations("evil. example", ME, ME, policy=ReplyPolicy(join_spaced_dots=False)) == []
    )


def test_a_homoglyph_stop_by_is_stored_as_a_hash():
    from hadavin_sdk.limits import Limits

    class _Reg:
        agents: ClassVar[dict] = {}

    store = MemoryStore()
    Limits(store, _Audit(), _Reg()).stop("d\u0433ill")  # type: ignore[arg-type]
    assert store.get_kill_switch().by.startswith("h:")


class _Body:
    def __init__(self, data):
        self.data, self.pos, self.reads = data, 0, 0

    def read(self, n=-1):
        assert n > 0, "an unbounded read() must never be made"
        self.reads += 1
        out = self.data[self.pos : self.pos + n]
        self.pos += len(out)
        return out


def test_a_response_body_is_read_with_a_byte_counter_and_never_past_the_cap():
    from hadavin_sdk.actions.executor import _read_capped

    assert _read_capped(_Body(b'{"id": "1"}')) == b'{"id": "1"}'
    assert _read_capped(_Body(b"x" * 100), 100) == b"x" * 100
    big = _Body(b"x" * 10_000_000)
    assert _read_capped(big, 1000) == b"" and big.pos <= 1001 + 65536, "stopped early, not buffered"


# ---------------------------------------------------------------- adopting the final shared fold (PR 50 round 2) and the ALLOW path
def test_the_modules_use_the_one_shared_fold_and_the_allow_helpers_of_textnorm():
    from hadavin_sdk.guard import identity_text, reply_check, textnorm

    assert identity_text.fold is textnorm.fold and reply_check.fold is textnorm.fold
    assert (
        identity_text.mixed_script is textnorm.mixed_script
        and identity_text.safe_equal is textnorm.safe_equal
    )
    assert identity_text.confusable_not_equal is textnorm.confusable_not_equal
    assert (
        identity_text.LOOKALIKES is textnorm.LOOKALIKES
        and identity_text.FILLERS is textnorm.FILLERS
    )


def test_a_word_that_mixes_scripts_is_refused_even_when_the_table_has_no_entry_for_the_letter():
    eta = "\u03b7"  # Greek eta: the table maps it, but the refusal must not depend on that
    assert identity_key("alice.ng") == "alice.ng"
    assert identity_key("alice.n" + eta) is None and identity_key("al" + eta + "ce") is None
    assert identity_key("al\u0585ce") is None, "Armenian oh inside a Latin word"
    assert exact_key("al" + eta + "ce@x.example") is None, "an ALLOW target never mixes scripts"
    assert not same_recipient("al" + eta + "ce@x.example", "al" + eta + "ce@x.example")
    assert identity_key(eta + eta, lookalikes="fold") is not None, (
        "a word wholly in one other script is not mixed"
    )


def test_unassigned_code_points_are_refused_and_cannot_make_a_different_name():
    import unicodedata

    for cp in (0x0378, 0xE0080, 0x2FE0):
        cn = chr(cp)
        assert unicodedata.category(cn) == "Cn", hex(cp)  # a probe that really is unassigned
        assert (
            not text_ok("alice" + cn)
            and identity_key("alice" + cn) is None
            and exact_key("alice@x.example" + cn) is None
        )
        assert _not_verified(reply_violations("hi", "a@b.example" + cn, ME))
        assert fold("alice" + cn) == "alice"
    assert unicodedata.category(chr(0xE0041)) == "Cf" and not text_ok("alice" + chr(0xE0041)), (
        "tag characters are Cf, refused too"
    )


def test_a_letter_the_table_does_not_list_still_cannot_hide_inside_a_latin_word():
    from hadavin_sdk.guard.textnorm import LOOKALIKES

    zhe = chr(
        0x0436
    )  # Cyrillic zhe: no Latin look-alike, so only the mixed-script backstop sees it
    assert zhe not in LOOKALIKES, "the probe must not be in the table or it proves nothing"
    assert (
        identity_key("ali" + zhe + "e") is None and exact_key("ali" + zhe + "e@x.example") is None
    )
    assert identity_key(zhe + zhe) is not None, "a word wholly in Cyrillic is not mixed"


def test_lookalike_of_is_the_allow_side_signal_and_same_recipient_is_an_allow_decision():
    assert lookalike_of("jose@x.example", "jos\u00e9@x.example") and lookalike_of(
        "p\u0430t@x.example", "pat@x.example"
    )
    assert not lookalike_of("pat@x.example", "pat@x.example") and not lookalike_of(
        "pat@x.example", "PAT@X.EXAMPLE"
    )
    assert not lookalike_of(None, "a") and not lookalike_of("a", 5)
    assert same_recipient("Pat@X.example", "pat@x.example") and not same_recipient(
        "p\u0430t@x.example", "pat@x.example"
    )
    assert not same_recipient("\uff50at@x.example", "pat@x.example"), (
        "fullwidth p folds equal under NFKC but the exact keys differ: refused"
    )


def test_a_look_alike_recipient_is_reported_as_such_and_never_verified():
    out = reply_violations("hi", "p\u0430t@example.com", "pat@example.com")
    assert "RECIPIENT_NOT_VERIFIED" in out and "RECIPIENT_LOOKALIKE" in out
    assert reply_violations("hi", "pat@example.com", "pat@example.com") == []
    assert reply_violations("hi", "other@example.com", "pat@example.com") == [
        "RECIPIENT_NOT_VERIFIED"
    ], "a plain mismatch is not a look-alike"


def test_an_allow_listed_link_or_host_needs_its_literal_spelling_in_the_text():
    p = ReplyPolicy(
        allowed_links=frozenset({"https://help.example.com/returns"}),
        allowed_hosts=frozenset({"example.com"}),
    )
    assert reply_violations("see https://help.example.com/returns", ME, ME, policy=p) == []
    assert reply_violations("see example.com", ME, ME, policy=p) == []
    cyr = reply_violations("see https://h\u0435lp.example.com/returns", ME, ME, policy=p)
    assert "UNLISTED_LINK" in cyr and "NON_ASCII_HOST" in cyr, (
        "the folded spelling equals the listed one; the literal one does not"
    )
    zw = reply_violations("see https://hel\u200bp.example.com/returns", ME, ME, policy=p)
    assert "UNLISTED_LINK" in zw, "a hidden character inside a listed link is not that link"
    host = reply_violations("see ex\u0430mple.com", ME, ME, policy=p)
    assert "UNLISTED_LINK" in host and "NON_ASCII_HOST" in host


def test_the_final_shared_vectors_hold_for_the_identity_and_domain_paths():
    for item in _vectors()["identities"]:
        for v in map(_vec, item["variants"]):
            assert identity_key(v) is None or same_person(v, item["id"]), v
    for item in _vectors()["domains"]:
        for v in map(_vec, item["variants"]):
            assert reply_violations(f"visit {v}", ME, ME), v

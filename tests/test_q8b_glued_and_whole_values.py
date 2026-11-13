"""Q8b fix batch 1 (round 1 of the result review): a key glued to an address or host, a value with spaces on a card, the
entry-shape and key-folding gaps of the case key rule, and the label for a target. Made-up data; fixed seeds.

Bug class of the glued key: a pattern that runs first swallows the key a later rule needs (the address pattern read
`example.compassword` as a domain, so `=value` was left behind). Every test message starts with a plain sentence the
mutant list (``tests/q8b_mutants.py``) matches.
"""

from __future__ import annotations

import importlib
import random
import re
import time

import pytest

from hadavin_sdk.approvals.channel import FakeChannel, clean
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from hadavin_sdk.models import Plan, Target
from tests.q8b_helpers import ONLY_PLACEHOLDERS, shown_records

redact_module = importlib.import_module("hadavin_sdk.guard.redact")

PW = "pass" + "word"
V = "zq" + "hunter2" + "secretXYZ"  # made-up; built from parts
ZW = "\u200b"
LEADS = [
    "bob.smith@example.com", "host.example.com", "10.0.0.1", "https://example.com", "arn:aws:s3:::bucket",
    "db01.corp.internal", "example.com", "user@host", "a@b.token", "bob@example.com.password", "x@y.z",
    "a@b.co.uk", "https://u@example.org", "bob%40example.com", "a" * 300 + "@example.com",
]  # fmt: skip
KEYS = [
    PW, "token", "secret", "passwd", "pwd", "api_key", "apikey", "access_key", "private_key", "client_secret",
    "credential", "Authorization", "auth_token", "session_id", "PASSWORD", "Token", "SECRET",
]  # fmt: skip
SEPS = ["", ZW, " ", ",", ";", "\n", "/", "?", "&", "(", '"', "\t", "|", "'"]


def both_paths(text):
    """What a card shows and what a tool result shows."""
    return {
        "card": clean(text),
        "tool": runmap.redact_untrusted(text, runmap.RunMap()),
    }


def test_r1_a_credential_key_glued_to_an_address_or_host_keeps_its_value_masked():
    """The ticket's blocker: `bob.smith@example.com` + `password=<value>` with no space between."""
    bad = []
    for lead in LEADS:
        for key in KEYS:
            for sep in SEPS:
                text = f"{lead}{sep}{key}={V}"
                for path, out in both_paths(text).items():
                    if V in out:
                        bad.append((path, text.replace(ZW, "<ZW>"), out))
    assert not bad, (
        f"a value glued to a credential key is readable: {len(bad)} cases, first {bad[:3]!r}"
    )


def test_r1_the_address_is_masked_too_when_a_key_is_glued_to_it():
    out = clean(f"bob.smith@example.com{PW}={V}")
    assert "bob" not in out and "smith" not in out and "example" not in out, (
        f"an address is readable beside a glued key: {out!r}"
    )
    assert out == "<EMAIL_1>password=<SECRET_1>", out


def test_r1_an_address_before_a_separated_key_is_unchanged():
    out = clean(f"bob.smith@example.com {PW}={V}")
    assert out == "<EMAIL_1> password=<SECRET_1>".replace("password", PW), out


def test_r1_property_every_assignment_value_is_masked_for_every_separator():
    """Seeded: any lead, any credential key in any letter case, any separator (none and zero width included), a made-up
    value of letters and digits; the value is never readable on a card or in a tool result."""
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, never a secret
    bad = []
    for _ in range(1500):
        lead = rng.choice(LEADS)
        key = "".join(c.upper() if rng.random() < 0.3 else c for c in rng.choice(KEYS))
        sep = rng.choice(SEPS)
        value = "zq" + "".join(rng.choice("qxzjkwvy0123456789") for _ in range(rng.randint(8, 16)))
        text = f"{lead}{sep}{key}={value} tail"
        for path, out in both_paths(text).items():
            if value in out:
                bad.append((path, text.replace(ZW, "<ZW>"), out))
    assert not bad, (
        f"a value glued to a credential key is readable: {len(bad)} cases, first {bad[:3]!r}"
    )


def test_r1_a_key_glued_to_an_identifier_in_every_case_and_with_a_quote():
    bad = [
        t
        for t in (
            f"arn:aws:s3:::bucketPASSWORD={V}",
            f'arn:aws:s3:::bucket{PW}":"{V}"',
            f"10.0.0.1Authorization={V}",
            f"HTTP_AUTHORIZATION={V}",
            f"example.comauthorization={V}",
        )
        if V in clean(t) or V in runmap.redact_untrusted(t, runmap.RunMap())
    ]
    assert not bad, f"a value glued to a credential key is readable: {bad}"


@pytest.mark.perf  # a wall-clock bound: it runs in the perf step (`pytest -m perf`), not the default suite
def test_r1_the_guard_in_front_of_the_address_pattern_is_bounded():
    """The ratio method of CI's perf step: 4x the text may take at most 12x the time (best of three, so a noisy runner
    moves both runs alike); a super-linear guard fails it."""

    def best(n):
        text = ("a@" + "b" * 250 + ".") * n + "\n" + ("x@y." * n)
        times = []
        for _ in range(3):
            started = time.perf_counter()
            runmap.redact_untrusted(text, runmap.RunMap())
            times.append(time.perf_counter() - started)
        return min(times)

    small, large = best(100), best(400)
    assert large < 12 * max(small, 0.005), (
        f"the address pattern is super-linear: {small:.3f}s -> {large:.3f}s"
    )


# ---- an unquoted value with spaces on a card -------------------------------------------------------------------------


def test_r2_a_value_with_spaces_is_masked_whole_on_a_card():
    words = "correct horse battery staple"
    rows = {
        "equals": f"{PW}={words}",
        "colon": f"{PW}: {words}",
        "percent": f"{PW}%3D{words.replace(' ', '%20')}",
        "token": f"token={words}",
        "after text": f"login with {PW}={words}",
    }
    bad = {k: clean(t) for k, t in rows.items() if any(w in clean(t) for w in words.split())}
    assert not bad, f"a value with spaces is readable on the card: {bad}"
    assert clean(f"{PW}={words}") == f"{PW}=<SECRET_1>"
    for text in rows.values():
        once = clean(text)
        assert clean(once) == once, (
            f"a value with spaces is readable on the card: second pass {once!r}"
        )


def test_r2_the_words_after_the_value_stop_at_the_next_key_and_the_line_end():
    assert clean(f"db {PW}=correct horse user=bob") == f"db {PW}=<SECRET_1> user=bob"
    assert clean(f"{PW}=correct horse\nnext line ok") == f"{PW}=<SECRET_1>\nnext line ok"
    assert clean(f'{PW}="correct horse" tail') == f'{PW}="<SECRET_1>" tail'


def test_r2_a_value_with_spaces_is_masked_whole_in_a_notice():
    ch = FakeChannel()
    ch.notify("p1", f"{PW}=correct horse battery staple")
    assert ch.notices[0][1] == f"{PW}=<SECRET_1>", (
        f"a value with spaces is readable on the card: {ch.notices[0][1]!r}"
    )


# ---- entries shaped {name, key, value} -------------------------------------------------------------------------------


def test_r3_an_entry_with_a_name_and_a_key_is_named_by_either():
    bad = []
    pairs = [("name", "db"), ("key", PW)]
    for order in (pairs, pairs[::-1]):
        for upper in (False, True):
            entry = {(k.upper() if upper else k): v for k, v in order}
            entry["Value" if upper else "value"] = V
            if V in repr(shown_records(entry)):
                bad.append(entry)
    assert not bad, f"an entry with a name and a key shows its value: {bad}"


def test_r3_every_spelling_of_value_is_masked():
    out = shown_records({"name": PW, "value": V, "Value": V + "x"})
    assert V not in repr(out), f"an entry with a name and a key shows its value: {out!r}"


# ---- the shape of a Secret --------------------------------------------------------------------------------------------


def test_r4_kind_secret_in_lower_case_is_a_secret():
    entry = "orders-svc-" + "ab12cd"
    out = shown_records(
        {"kind": "secret", "stringData": {"cfg": entry}}, {"message": f"user {entry} denied"}
    )
    assert entry not in repr(out), f"a Secret in lower case is shown: {out!r}"
    assert entry not in repr(
        shown_records(
            {"kind": "SECRET", "spec": {"stringData": {"cfg": entry}}}, {"message": entry}
        )
    ), "a Secret in upper case is shown"


@pytest.mark.parametrize(
    "data", ["correct horse battery staple", ["correct horse battery staple"], 7]
)
def test_r4_a_secret_whose_data_is_not_a_map_masks_its_copy_in_a_log(data):
    out = shown_records(
        {"kind": "Secret", "data": data}, {"message": "the correct horse battery staple came"}
    )
    log = out[1]["message"]
    if isinstance(data, int):
        assert out[0]["data"] == R.MASKED
    else:
        assert "horse" not in log, f"the copy of a Secret value is readable in a log: {log!r}"


def _entries(n):
    return {f"k{i}": f"zq{i:04d}secretvalue" for i in range(n)}


def test_r4_the_budget_of_a_secret_counts_nested_texts():
    entries = _entries(300)
    for name, data in (("flat", entries), ("nested list", {"a": list(entries.values())})):
        out = shown_records(
            {"kind": "Secret", "data": data},
            {"message": f"first zq0000secretvalue last {entries['k299']}"},
        )
        log = out[1]["message"]
        assert "zq0000secretvalue" not in log, (
            f"the first text of a Secret is readable in a log ({name}): {log!r}"
        )
        assert "zq0299secretvalue" in log, (
            f"the budget of a Secret was passed: the 300th text is masked where repeated ({name}): {log!r}"
        )


def test_r4_the_budget_holds_for_credential_keys_too():
    data = {f"DB_{PW.upper()}_{i}": f"zq{i:04d}secretvalue" for i in range(300)}
    out = shown_records(
        {"kind": "Secret", "data": data},
        {"message": "copy zq0299secretvalue and zq0000secretvalue"},
    )
    log = out[1]["message"]
    assert "zq0000secretvalue" not in log and "zq0299secretvalue" in log, (
        f"the budget of a Secret was passed under credential keys: {log!r}"
    )
    assert all(v == R.MASKED or ONLY_PLACEHOLDERS.fullmatch(v) for v in out[0]["data"].values())


def test_r4_a_common_value_of_a_secret_stays_readable_where_it_is_repeated():
    """The row of appendix A M5, as a decision with its reason: `orders` is one lower-case word, so masking every copy
    would blank ordinary log text; the Secret entry itself is masked, and LIMITS and the CHANGELOG say so."""
    import base64

    out = shown_records(
        {"kind": "Secret", "data": {"DB_NAME": base64.b64encode(b"orders").decode()}},
        {"message": "orders-api timeout"},
    )
    got = out[0]["data"]["DB_NAME"]
    assert got == R.MASKED or ONLY_PLACEHOLDERS.fullmatch(got), got
    assert out[1]["message"] == "orders-api timeout"
    assert "one lower-case word" in R.LIMITS


# ---- LIMITS says what the code does ----------------------------------------------------------------------------------


def test_r4_a_number_or_one_word_in_a_secret_is_not_registered():
    """The 8-character rule: a text of digits only, or one lower-case word, is shown where it is repeated."""
    for text in ("12345678", "postgres"):
        _, second = shown_records(
            {"kind": "Secret", "data": {"port": text}}, {"message": f"saw {text}"}
        )
        assert second == {"message": f"saw {text}"}, (
            f"a common text of a Secret was registered: {second!r}"
        )


def test_r5_every_exception_named_in_limits_is_what_the_walk_does():
    named = {
        "a text that is exactly a UTC time": (
            {PW: "2026-11-11T10:00:00Z"},
            PW,
            "2026-11-11T10:00:00Z",
        ),
        "a true, false or null value": ({PW: True}, PW, True),
        "a setting about a credential": (
            {PW + "_policy_enabled": "yes"},
            PW + "_policy_enabled",
            "yes",
        ),
    }
    bad = []
    for phrase, (record, key, expected) in named.items():
        if phrase not in R.LIMITS:
            bad.append(f"LIMITS does not name {phrase!r}")
        if shown_records(record)[0][key] != expected:
            bad.append(f"the walk does not show {phrase!r} as written")
    assert shown_records({PW: None})[0][PW] is None
    assert not bad, f"LIMITS contradicts the code: {bad}"
    # a number under a credential key is masked, so LIMITS must not promise numbers are kept without that exception
    assert shown_records({PW: 12345})[0][PW] == R.MASKED
    assert "except under a credential key" in R.SCHEME


# ---- the key rule ------------------------------------------------------------------------------------------------------

WORDS = [
    "password", "passwd", "passphrase", "secret", "token", "apikey", "authorization", "credential", "bearer",
    "session", "privatekey", "pass",
]  # fmt: skip


def _equivalents(letter):
    pat = re.compile(re.escape(letter), re.IGNORECASE)
    # the ASCII letters themselves are the plain case (a camelCase cut is the older rule's own, tested by T1)
    return [c for c in map(chr, [*range(0x80, 0x2200), 0x212A, 0xFF21, 0xFF41]) if pat.fullmatch(c)]


def test_r6_a_key_with_a_letter_the_older_rule_read_as_ascii_is_still_a_key():
    """The older rule used `re.IGNORECASE`: it also reads U+017F (long s), U+0130 and U+0131 (dotted and dotless i) and U+212A
    (Kelvin sign) as ASCII letters. Every spelling of every word is a credential key here too."""
    letters = sorted({c for w in WORDS for c in w})
    variants = {c: _equivalents(c) for c in letters}
    assert {"ſ", "İ", "ı", "K"} <= {v for vs in variants.values() for v in vs}
    camel = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")  # the older rule cut camelCase first too
    bad = []
    for word in WORDS:
        older = re.compile(rf"(^|[_.\-\s]){word}($|[_.\-\s])", re.IGNORECASE)
        for pos, ch in enumerate(word):
            for v in variants[ch]:
                key = word[:pos] + v + word[pos + 1 :]
                if older.search(camel.sub("_", key)) and not R.sensitive(key):
                    bad.append(key)
    assert not bad, f"a key the older rule accepted is refused (letter case folding): {bad[:10]}"
    # real spellings: long s, dotted capital I (U+0130) and dotless i (U+0131) inside key words
    for key in (
        "paſſword",
        "PASſWORD",
        "credentİal",
        "CREDENTİAL",
        "credentıal",
        "authorİzation",
        "secret_key",
    ):
        assert R.sensitive(key), key
    for key in ("ınternal_note", "ordınary"):
        assert not R.sensitive(key), key


def _expand(fragment):
    """Every spelling of a fragment of the redactor's key list (`[_\\-]?` written three ways, `(?:ificate)?` two)."""
    fragment = re.sub(r"\(\?=.*?\)", "", fragment)
    spellings = [""]
    for part in re.split(r"(\[_\\-\]\?|\(\?:ificate\)\?)", fragment):
        if part == r"[_\-]?":
            spellings = [s + sep for s in spellings for sep in ("", "_", "-")]
        elif part == "(?:ificate)?":
            spellings = [s + e for s in spellings for e in ("", "ificate")]
        else:
            spellings = [s + part.replace("\\.", ".") for s in spellings]
    return spellings


def test_r7_every_key_of_the_redactor_is_a_key_of_the_case_rule():
    """The two key lists must not drift apart: every spelling of every alternative of `guard.redact.KEY_ALTERNATIVES`
    (and the glued spelling of a prefixed key) is a credential key for `sensitive`."""
    missing = []
    for fragment in redact_module.KEY_ALTERNATIVES:
        for key in _expand(fragment):
            for full in (key, "db_" + key, key + "_x"):
                if not R.sensitive(full):
                    missing.append(full)
    assert not missing, (
        f"the key rule of the case differs from the redactor's: {sorted(set(missing))[:12]}"
    )
    for glued in ("accountkey", "keydata", "certdata", "certificatedata"):
        assert R.sensitive(glued), f"the key rule of the case differs from the redactor's: {glued}"


def test_r8_a_count_of_tokens_is_not_a_credential():
    shown = [
        "tokens_per_second", "tokens_remaining", "reasoning_tokens", "cache_tokens", "cache_read_tokens",
        "audio_tokens", "max_tokens", "tokens_used", "output_tokens", "tokens_limit",
    ]  # fmt: skip
    wrong = [k for k in shown if R.sensitive(k)]
    assert not wrong, f"a token count is masked as a credential: {wrong}"
    for k in ("tokens", "access_tokens", "refresh_tokens", "id_tokens", "tokens_2"):
        assert R.sensitive(k), f"a credential key is not masked: {k}"
    assert shown_records({"reasoning_tokens": 812})[0]["reasoning_tokens"] == 812


# ---- the label for a target --------------------------------------------------------------------------------------------


def _plan(system):
    return Plan(
        run_id="run_1", agent_id="agent-ops", action_id="restart_service", action_version=1,
        risk_class="reversible", inputs={"n": 1}, target=Target(system=system), idempotency_key="k1",
        expected_outcome="service restarted",
    )  # fmt: skip


def test_r9_a_host_name_target_is_masked_and_a_label_is_shown():
    plan = _plan("db01.corp.internal")
    assert "db01" not in summary(plan) and "<HOSTNAME_" in summary(plan)
    labelled = summary(plan, None, {"db01.corp.internal": "orders-db"})
    assert " on orders-db." in labelled and "db01" not in labelled, (
        f"the target label is not shown: {labelled!r}"
    )
    assert " on orders-db." not in summary(
        _plan("other.corp.internal"), None, {"db01.corp.internal": "orders-db"}
    )
    # a label that is itself a host name is masked like any text
    assert "evil" not in summary(plan, None, {"db01.corp.internal": "x.evil.corp"})


def test_r9_the_label_reaches_the_request_card(tmp_path):
    from hadavin_sdk.approvals import Approvals, FakeChannel
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.config import load_config
    from hadavin_sdk.models import GateDecision
    from hadavin_sdk.registry import load_registry
    from hadavin_sdk.store import MemoryStore
    from tests.conftest import make_cfg

    cfg = load_config(make_cfg(tmp_path))
    plan = _plan("db01.corp.internal").model_copy(
        update={"action_id": "create_draft_record", "action_version": 1, "risk_class": "reversible"}
    )
    shown = {}
    for labels in ({}, {"db01.corp.internal": "orders-db"}):
        appr = Approvals(
            MemoryStore(), LocalDirSink(cfg.backends.audit.dir), load_registry(cfg), FakeChannel(),
            lambda *a: None, target_labels=labels,
        )  # fmt: skip
        gd = GateDecision(
            run_id=plan.run_id, plan_hash=plan.hash(), outcome="needs_approval", rule_id="x"
        )
        shown[bool(labels)] = appr.request(plan, gd, "svc:test-agent").summary
    assert "<HOSTNAME_" in shown[False] and "orders-db" not in shown[False], shown[False]
    assert " on orders-db." in shown[True], (
        f"the label does not reach the request card: {shown[True]!r}"
    )

    import inspect

    from hadavin_sdk.app import build

    assert "target_labels" in inspect.signature(build).parameters, "build takes no target labels"


def test_r10_refused_credential_values_do_not_multiply_the_work(monkeypatch):
    """F13: a credential value the redactor does not mask whole (plain text with an address in it, or text with spaces)
    is tried more than once; the characters given to the redactor stay near the size of the case, per pass."""
    seen = 0
    real = runmap.redact_untrusted

    def counting(text, mapping, *args, **kwargs):
        nonlocal seen
        seen += len(text)
        return real(text, mapping, *args, **kwargs)

    monkeypatch.setattr(runmap, "redact_untrusted", counting)
    values = [f"a{i}.b@example.com-" + "x" * 170 for i in range(40)] + [
        ("qx zj; " * 30)[:200] + str(i) for i in range(300)
    ]
    shown_records({"kind": "note", "password": values})
    per_pass = seen / 2
    assert per_pass <= 2.2 * sum(len(v) for v in values), (
        f"a refused credential value multiplies the work: {per_pass}"
    )

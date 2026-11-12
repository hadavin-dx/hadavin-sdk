"""Q8b batch 7 (round 7 of the redaction path): the classes the round 7 review and the evidence probe found.

Classes (each fixed at the one place every caller routes through, `guard/redact.py` for the card, the tool result, the text of a
run and a log line, `k1b/redaction.py` for the record keys):
  1. a credential word with DIGITS glued behind it (`pass2`, `--newpass2`, `session2`, `auth1`, `oauth2`, `auth0`);
  2. the PLURAL of a credential word as a flag (`--secrets`, `--passwords`, `--apikeys`, `--api_tokens`, `--access_tokens`);
  3. a record key or header named for a COOKIE in any letter case (`Cookie`, `COOKIE`, `Set-Cookie`);
  4. an authorization SCHEME word and the token after it (`Bearer`, `Basic`, `Token`, `Digest`, `ApiKey`);
  5. an ORDINARY word that ends in `pass`, `auth` or `session` (`bypass`, `compass`, `obsession`) in every form.
The five paths: card = approvals.channel.clean, tool = tools.redact_layered, run = guard.runmap.redact_text, log =
guard.runmap.safe_head, record = k1b.redaction.redact_bundle (a message text, and a record key).
"""

from __future__ import annotations

import importlib
import json
import pathlib
import time
from datetime import UTC, datetime

import pytest

from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.tools import redact_layered

redact = importlib.import_module("hadavin_sdk.guard.redact")
ROOT = pathlib.Path(__file__).resolve().parents[1]
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

V = "Jq7" + "firstValue"  # a made-up value, built from parts
W = "Kq8" + "secondWord"
B64 = "dXNlcjpw" + "YXNzd29yZDEyMw"  # made up: base64 of a made-up "user:pass" pair
ORDINARY_VALUE = "Mq9" + "ordinaryValue"


def _bundle(**kw):
    base = {
        "case_id": "case-b7",
        "alert_time": datetime(2026, 1, 1, 10, tzinfo=UTC),
        "alert_time_text": "2026-01-01T10:00:00Z",
        "alert": {},
        "metrics": (),
        "logs": (),
        "deploys": (),
        "k8s": (),
        "runbooks": (),
        "ids": frozenset(),
        "manifest_sha256": "0" * 64,
    }
    base.update(kw)
    return Bundle(**base)


def five_paths(text: str) -> dict[str, str]:
    """What each of the five paths shows for a text."""
    bundle = _bundle(logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", "message": text},)),))
    return {
        "card": clean(text),
        "tool": redact_layered(text, {}),
        "run": runmap.redact_text(text, {}),
        "log": runmap.safe_head(text, 4000, {}),
        "record": redact_bundle_message(bundle),
    }


def redact_bundle_message(bundle) -> str:
    from hadavin_sdk.k1b.redaction import redact_bundle

    return redact_bundle(bundle)[0].logs[0][1][0]["message"]


def record_key_output(key: str, value) -> str:
    """A record key (a log record and an alert of a case bundle) under the record walk."""
    from hadavin_sdk.k1b.redaction import redact_bundle

    b = _bundle(
        logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", key: value},)),), alert={key: value}
    )
    r = redact_bundle(b)[0]
    return json.dumps(r.logs[0][1][0], ensure_ascii=False) + json.dumps(r.alert, ensure_ascii=False)


def readable_on(text: str, *pieces: str) -> list[str]:
    """`path: piece` for every path that still shows a piece."""
    return [
        f"{p}: {piece}" for p, out in five_paths(text).items() for piece in pieces if piece in out
    ]


FORMS = {
    "flag-space": "ran tool --{k} {v} --verbose",
    "flag-eq": "ran tool --{k}={v} --verbose",
    "key=": "cfg {k}={v} end of note",
    "key:": "cfg {k}: {v} end of note",
    "dq": 'cfg {k}="{v}" end of note',
}


# ---- class 1: digits glued behind a credential word ----------------------------------------------------------------------

DIGIT_KEYS = (
    "pass",
    "newpass",
    "dbpass",
    "session",
    "jenkinssession",
    "auth",
    "rootauth",
    "oauth",
    "bearer",
    "token",
    "password",
    "api_key",
)
DIGITS = ("0", "1", "2", "42", "123")


def test_b7_1_a_credential_word_with_digits_behind_it_is_masked_on_every_path_and_form():
    left = []
    for word in DIGIT_KEYS:
        for digits in DIGITS:
            key = word + digits
            assert R.sensitive(key), f"the record walk does not mask {key}: the test list is wrong"
            for form, tmpl in FORMS.items():
                left += [f"{key} {form} {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
            if V in record_key_output(key, V):
                left.append(f"{key} record key")
    assert not left, (
        f"a value behind a credential key with digits is readable: {left[:6]} ({len(left)})"
    )


def test_b7_1_auth0_and_oauth2_are_masked_like_oauth():
    """The two keys that were pinned as readable in batch 6 (a card cost) are credential keys: `oauth` itself is masked."""
    for key in ("auth0", "oauth2", "oauth"):
        for form, tmpl in FORMS.items():
            assert not readable_on(tmpl.format(k=key, v=V), V), f"{key} {form}"


def test_b7_1_digits_in_the_middle_or_a_digit_only_neighbour_do_not_make_a_key():
    """Controls: the digits must come right behind the credential word, and a word that only holds `pass` is no key."""
    for key in ("pass2word", "s3session", "auth0rity", "authority2", "sha256", "port2"):
        text = f"cfg {key}={ORDINARY_VALUE} end"
        if R.sensitive(key):
            continue
        assert clean(text) == text, (
            f"{key} was masked on the card but not by the record walk: {clean(text)!r}"
        )


class _Seq:
    """A seeded, repeatable number source for the fuzz test (a plain linear congruential step; it is never used for a secret)."""

    def __init__(self, seed: int):
        self.state = (seed * 2862933555777941757 + 3037000493) % 2**64

    def below(self, n: int) -> int:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) % 2**64
        return (self.state >> 33) % n

    def choice(self, items):
        return items[self.below(len(items))]

    def randint(self, low: int, high: int) -> int:
        return low + self.below(high - low + 1)


@pytest.mark.parametrize("seed", range(6))
def test_b7_1_fuzz_a_random_prefix_and_digits_behind_a_credential_word_stay_masked(seed):
    """Property: any lower-case prefix (no ordinary word can form: letters from a set with no vowels) + a credential word +
    1 to 3 digits is masked as a flag, as `key=value` and as a record key, whatever the prefix."""
    rng = _Seq(7000 + seed)
    words = ("pass", "auth", "session", "password", "token", "secret", "apikey", "credential")
    left = []
    for _ in range(40):
        key = (
            "".join(rng.choice("qxzjkvw") for _ in range(rng.randint(0, 8)))
            + rng.choice(words)
            + "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 3)))
        )
        if not R.sensitive(key):
            continue
        for tmpl in (FORMS["flag-space"], FORMS["key="]):
            left += [f"{key} {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
        if V in record_key_output(key, V):
            left.append(f"{key} record")
    assert not left, f"fuzz: {left[:5]} ({len(left)})"


# ---- class 2: the plural of a credential word as a flag ------------------------------------------------------------------

PLURALS = (
    "secrets",
    "passwords",
    "apikeys",
    "api_tokens",
    "access_tokens",
    "refresh_tokens",
    "credentials",
    "api-keys",
)


def test_b7_2_a_plural_credential_flag_masks_its_value_on_every_path():
    left = []
    for key in PLURALS:
        for form, tmpl in FORMS.items():
            left += [f"{key} {form} {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
        if V in record_key_output(key, V):
            left.append(f"{key} record key")
    assert not left, f"a plural credential key leaves a value readable: {left[:6]} ({len(left)})"


def test_b7_2_a_count_of_tokens_stays_readable_as_a_flag():
    """Controls (they pass on the old code too: the plural rule must not turn a count into a credential)."""
    for key in (
        "tokens",
        "max_tokens",
        "max-tokens",
        "input_tokens",
        "output_tokens",
        "reasoning_tokens",
    ):
        text = f"run --{key} 4096 --verbose"
        assert clean(text) == text, f"a count of tokens was masked as a flag: {clean(text)!r}"
        assert not R.sensitive(key) or key == "tokens", key


def test_b7_2_the_record_walk_reads_the_one_list_of_count_words():
    assert R.COUNT_WORDS_BEFORE_TOKENS is redact.COUNT_WORDS_BEFORE_TOKENS, (
        "the record walk keeps its own list of count words"
    )


def test_b7_2_the_plural_rule_follows_the_record_walk_for_tokens_after_a_non_count_word():
    for key in ("api_tokens", "access_tokens", "id_tokens", "x-refresh-tokens"):
        assert R.sensitive(key), key
        assert V not in clean(f"run --{key} {V} now"), (
            f"a plural tokens flag after a non-count word is readable: {key}"
        )
    for key in ("max_tokens", "cache_tokens", "audio_tokens"):
        assert not R.sensitive(key), key
        assert clean(f"run --{key} {V} now") == f"run --{key} {V} now", (
            f"a count of tokens was masked as a flag: {key}"
        )


# ---- class 3: a key named for a cookie, in any letter case ---------------------------------------------------------------

COOKIE_KEYS = (
    "Cookie",
    "COOKIE",
    "cookie",
    "Set-Cookie",
    "SET-COOKIE",
    "set-cookie",
    "cookies",
    "Cookies",
)
COOKIE_VALUES = {
    "plain": ("Iq6" + "plainValue", ["Iq6plainValue"]),
    "jar": ("sid=Eq5" + "sidVal; theme=Fq5" + "theme", ["Eq5sidVal", "Fq5theme"]),
    "glued": ("Aq1" + "bcd;Zx9" + "tail", ["Aq1bcd", "Zx9tail"]),
}


def test_b7_3_a_record_key_named_for_a_cookie_is_masked_whatever_its_letter_case():
    left = []
    for key in COOKIE_KEYS:
        assert R.sensitive(key), f"a cookie record key is not sensitive: {key}"
        for name, (value, pieces) in COOKIE_VALUES.items():
            out = record_key_output(key, value)
            left += [f"{key} {name} {p}" for p in pieces if p in out]
    assert not left, f"a cookie record key leaves a value readable: {left}"


def test_b7_3_a_cookie_key_in_text_is_masked_on_every_path_in_every_letter_case():
    left = []
    for key in COOKIE_KEYS:
        for name, (value, pieces) in COOKIE_VALUES.items():
            for tmpl in ("note {k}={v} end", "header {k}: {v}", '{{"{k}": "{v}"}} tail'):
                left += [
                    f"{key} {name} {x}" for x in readable_on(tmpl.format(k=key, v=value), *pieces)
                ]
            # a flag takes the one word after a space (a second word is another argument of the command): one name=value pair
            left += [
                f"{key} flag {x}"
                for x in readable_on(f"ran --{key} {pieces[0]}x --verbose", pieces[0])
            ]
            left += [
                f"{key} flag pair {x}"
                for x in readable_on(f"ran --{key} sid={pieces[0]} --verbose", pieces[0])
            ]
        # a value of only three characters: the flag rule takes it, the curl rule needs four
        left += [f"{key} short flag {x}" for x in readable_on(f"ran --{key} q7z --verbose", "q7z")]
    assert not left, f"a cookie key in text leaves a value readable: {left[:6]} ({len(left)})"


def test_b7_3_a_cookie_value_split_by_a_semicolon_with_no_space_is_one_secret():
    """`Cookie=a;b`: the older cookie rule took `;name=value` pairs only, so the word behind a bare `;` stayed readable."""
    out = clean("Cookie=Zq7xVKp9wT;Qw8tail end")
    assert "Qw8tail" not in out and "Zq7xVKp9wT" not in out, out
    assert out.endswith(" end"), out


def test_b7_3_a_setting_about_a_cookie_is_still_a_setting():
    """Controls: `cookie_policy_enabled` (a setting about a credential) shows a yes or no word."""
    assert R.sensitive("cookie_policy_enabled")
    out = record_key_output("cookie_policy_enabled", "true")
    assert "true" in out


# ---- class 4: an authorization scheme word and the token after it --------------------------------------------------------

SCHEMES = ("Bearer", "Basic", "Token", "Digest", "ApiKey", "bearer", "BASIC")


def test_b7_4_a_scheme_word_and_its_token_are_masked_after_a_flag_an_equals_sign_and_a_colon():
    left = []
    for scheme in SCHEMES:
        value = f"{scheme} {B64}"
        for tmpl in (
            "ran --authorization {v} --verbose",
            "ran --authorization={v} --verbose",
            "cfg authorization={v} more words",
            "Authorization: {v} more words",
            'cfg "authorization": "{v}" tail',
        ):
            left += [f"{scheme} {tmpl} {x}" for x in readable_on(tmpl.format(v=value), B64)]
        if B64 in record_key_output("Authorization", value):
            left.append(f"{scheme} record key")
    assert not left, f"a token after an authorization scheme is readable: {left[:6]} ({len(left)})"


def test_b7_4_the_scheme_word_after_a_credential_flag_is_masked_with_its_token():
    for scheme in ("Bearer", "Basic", "Token", "Digest", "ApiKey"):
        out = clean(f"ran --authorization {scheme} {B64} --verbose")
        assert B64 not in out, f"the token after a scheme word is readable: {out!r}"
        assert out == "ran --authorization <SECRET_1> --verbose", (
            f"the scheme word is not masked with its token: {out!r}"
        )


def test_b7_4_a_digest_header_is_masked_to_the_end_of_the_line():
    """The parameters of a Digest header hold a hash of the password (`response=`): all of them are the credential."""
    text = (
        'Authorization: Digest username="Mufasa", realm="r", nonce="dcd98b7102dd2f0e", uri="/dir", '
        'response="6629fae49393a05397450978507c4ef1", opaque="5ccc069c403ebaf9f0171e9517f40e41"'
    )
    for path, out in five_paths(text).items():
        for piece in (
            "6629fae49393a05397450978507c4ef1",
            "5ccc069c403ebaf9f0171e9517f40e41",
            "dcd98b7102dd2f0e",
        ):
            assert piece not in out, f"{path}: {out!r}"
    assert clean("Authorization: Digest username=Mufasa\nnext line stays").endswith(
        "next line stays"
    )


def test_b7_4_the_generic_second_word_after_a_credential_flag_is_a_stated_design_choice():
    """`--newpass a b`: `a` is masked and `b` is shown (it may be a file name or the next argument). Pinned, and written in
    LIMITS and the CHANGELOG, for the seven flags of the round 7 report."""
    for flag in (
        "newpass",
        "oldpass",
        "postgresauth",
        "dbpass",
        "confirmpass",
        "rootauth",
        "oauth",
    ):
        out = clean(f"run --{flag} {V} {W} now")
        assert out == f"run --{flag} <SECRET_1> {W} now", out
    assert "second word" in R.LIMITS and "second word" in CHANGELOG


# ---- class 5: ordinary words that end in pass, auth or session ----------------------------------------------------------

ORDINARY_KEYS = (
    "bypass",
    "compass",
    "obsession",
    "author",
    "encompass",
    "possession",
    "supersession",
    "bypass2",
)
CREDENTIAL_CONTROLS = (
    "newpass",
    "dbpass",
    "oauth",
    "rootauth",
    "jenkinssession",
    "bypasspass",
    "compassword",
    "xbypass",
)


def test_b7_5_an_ordinary_word_stays_readable_in_every_form_on_every_path():
    left = []
    for key in ORDINARY_KEYS:
        assert not R.sensitive(key), key
        for form, tmpl in FORMS.items():
            left += [
                f"{key} {form}: {x}"
                for x in _masked_paths(tmpl.format(k=key, v=ORDINARY_VALUE), ORDINARY_VALUE)
            ]
        if ORDINARY_VALUE not in record_key_output(key, ORDINARY_VALUE):
            left.append(f"{key} record key masked")
    assert not left, f"an ordinary word was masked: {left[:8]} ({len(left)})"


def _masked_paths(text: str, piece: str) -> list[str]:
    return [p for p, out in five_paths(text).items() if piece not in out]


def test_b7_5_a_real_credential_key_never_turns_readable_because_of_the_ordinary_list():
    """The look-behind that keeps `bypass` readable must not hide `bypasspass`, `compassword` or `xbypass` (a word of its own)."""
    left = []
    for key in CREDENTIAL_CONTROLS:
        assert R.sensitive(key), key
        for form, tmpl in FORMS.items():
            left += [f"{key} {form} {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
        if V in record_key_output(key, V):
            left.append(f"{key} record")
    assert not left, f"a credential key became readable: {left[:6]}"


def test_b7_5_the_ordinary_word_must_start_a_word_to_stay_readable():
    """`xbypass=` is a credential key for the record walk (the ordinary word is not the whole word): so for the card."""
    for key in ("xbypass", "mybypass", "nearbypass", "xcompass"):
        assert R.sensitive(key), key
        assert V not in clean(f"cfg {key}={V} end"), (
            f"an ordinary word glued behind letters is no ordinary word: {key}"
        )
    for key in ("x-bypass", "new_bypass", "x_compass"):
        assert not R.sensitive(key), key
        assert clean(f"cfg {key}={ORDINARY_VALUE} end") == f"cfg {key}={ORDINARY_VALUE} end", (
            f"an ordinary word of its own was masked: {key}"
        )


def test_b7_5_every_ordinary_word_of_the_one_list_is_readable_as_key_value_and_quoted():
    for word in sorted(redact.ORDINARY_WORDS):
        for tmpl in ("cfg {k}={v} end", 'cfg {k}="{v} {v}" end', "cfg {k}: {v} end"):
            text = tmpl.format(k=word, v=ORDINARY_VALUE)
            assert clean(text) == text, (
                f"an ordinary word was masked as key value: {word}: {clean(text)!r}"
            )


# ---- batch 7 items 6: a third prefix group ------------------------------------------------------------------------------


def test_b7_6_a_flag_with_three_prefix_words_masks_its_value():
    assert (
        clean(f"run --db-root-user-password {V} now")
        == "run --db-root-user-password <SECRET_1> now"
    )
    assert clean(f"run --a_b_c_token={V}") == "run --a_b_c_token=<SECRET_1>"


def test_b7_6_the_third_prefix_group_costs_no_extra_time_on_a_long_flag():
    """The groups are cut at a separator, so a long run of `a-a-a-` is read once per start (no backtracking blow-up)."""
    text = "--" + "a-" * 20000 + "x now " + "--a-b-c " * 2000
    t0 = time.perf_counter()
    clean(text)
    assert time.perf_counter() - t0 < 20, "a long flag takes far too long"
    assert "four or more hyphen-joined words" in R.LIMITS
    # the stated limit is real (pinned): a fourth word in front keeps the value readable
    assert clean(f"run --a-b-c-d-password {V} now") == f"run --a-b-c-d-password {V} now"


def test_b7_6_the_changelog_says_how_many_letters_may_be_glued_in_front():
    assert "up to 40 letters or digits glued in front" in CHANGELOG
    assert "any letters or digits glued in front" not in CHANGELOG

"""Q8b batch 12 (the round 12 review, redaction path): the classes the round 12 review and the independent evidence found.

Group 1: a name made of an ordinary word (`compass`, `bypass`, `possession`) and MORE characters, written as a QUOTED value
(`{"compass_direction": "v"}`, `compass2key="v"`), was masked by `main` and was left readable by batch 11. The class is "an exemption
wider than the reading it replaced": the quoted-value rules exempted every name that has an ordinary word in it, where only the
ordinary word ALONE is the stated owner question (`q-q8b-bare-bypass`, pinned below as shown).
"""

from __future__ import annotations

import importlib
import json
import random
import zlib

import pytest

from hadavin_sdk.approvals.channel import clean
from tests.test_q8b_batch7 import readable_on

redact_module = importlib.import_module("hadavin_sdk.guard.redact")

ORDINARY = (
    "compass",
    "overpass",
    "encompass",
    "bypass",
    "possession",
    "obsession",
    "underpass",
    "repossession",
)
JOINERS = ("", "_", "-", ".", "2", "_2", "2_", "-2-", ".2.", "__", "--", "1.", "12")
SECONDS = ("key", "code", "value", "phrase", "id", "cookie", "direction", "secret", "token", "name")
_ALPHA = "xkvmzwhtrpnqbdfglscyaeuJQKZ0123456789"


def made_up_value(seed: int, n: int = 20) -> str:
    rnd = random.Random(seed)  # noqa: S311 - a seeded test generator, not a secret
    return "".join(rnd.choice(_ALPHA) for _ in range(n))


def quoted_forms(name: str, value: str) -> dict[str, str]:
    return {
        "json": json.dumps({name: value}),
        "dq": f'cfg {name}="{value}" end',
        "sq": f"cfg {name}='{value}' end",
        "json-colon-space": '{"' + name + '" :   "' + value + '"}',
    }


def test_b12_1_an_ordinary_word_and_more_characters_is_masked_in_every_quoted_form_as_on_main():
    # The class, as a generator: every ordinary word x joiner x second word x quoted form. 8 x 13 x 10 x 4 = 4160 texts.
    left = []
    for o in ORDINARY:
        for j in JOINERS:
            for s in SECONDS:
                name = o + j + s
                value = made_up_value(zlib.crc32(name.encode()))
                for form, text in quoted_forms(name, value).items():
                    shown = readable_on(text, value)
                    if shown:
                        left.append(f"{form} {name}: {shown}")
    assert not left, (
        f"{len(left)} quoted values behind a name that holds an ordinary word and more are left readable, "
        f"as batch 11 left them and main did not: {left[:6]}"
    )


@pytest.mark.parametrize("word", ORDINARY)
def test_b12_1_the_session_and_pass_families_both_read_a_tail_after_the_ordinary_word(word):
    value = made_up_value(5)
    assert not readable_on(f'{{"{word}_direction": "{value}"}}', value), (
        f'`"{word}_direction": "v"` shows its value: the quoted rule exempts a name with a tail'
    )


@pytest.mark.parametrize("word", ORDINARY)
def test_b12_1_the_bare_ordinary_word_in_a_quoted_value_stays_shown_the_stated_owner_question(word):
    # `q-q8b-bare-bypass` (handover/questions-for-lead.md): shown by default until the owner decides. A pin: when the owner
    # decides to mask the bare word, this test must fail visibly, and the decision changes it.
    value = made_up_value(6)
    for text in (json.dumps({word: value}), f'{word}="{value}"', f"{word}2='{value}'"):
        assert value in clean(text), (
            f"the bare word `{word}` is masked in {text!r}: the owner question q-q8b-bare-bypass was not answered yet"
        )


def test_b12_1_a_non_ordinary_word_that_ends_in_pass_is_still_masked_bare_and_with_a_tail():
    value = made_up_value(7)
    for name in ("newpass", "dbpass", "mysession", "rootpass2", "newpass_x", "mysession_x"):
        for form, text in quoted_forms(name, value).items():
            assert not readable_on(text, value), f"{form} {name} shows its value"


# ---- group 2 and 4: killers for mutants that survived or were pinned to another test in batch 11 ------------------------------------

SCHEMES = ("Basic", "Token", "ApiKey", "Bearer", "Digest")
KEY_HEADERS = ("token: ", "secret: ", "passwd=", "X-Api-Key: ")


# Pieces made of plain lower-case words: a piece of random letters and digits is also masked by the high-entropy rules, which hides a
# fault in the header rule under test (the batch 11 killers used such pieces and the mutants survived: round 12, group 2).
LOW_ENTROPY_PIECES = ("segmentalpha", "bravosegment", "charliesegmentdelta")


def _outs(text: str) -> list[str]:
    return [clean(text), redact_module.redact(text).text]


def test_b12_2_a_credential_key_a_short_first_word_and_folded_lines_are_masked():
    # M190: the folded-header rule must read a CREDENTIAL KEY as the header name, not only `Authorization`.
    first, second, third = "qwxzv", LOW_ENTROPY_PIECES[0], LOW_ENTROPY_PIECES[1]
    left = []
    for header in KEY_HEADERS:
        for scheme in SCHEMES:
            text = f"{header}{scheme} {first}\r\n\t{second}\n {third}\nnext line ok\n"
            left += [
                f"{header.strip()} {scheme}: {p}"
                for out in _outs(text)
                for p in (second, third)
                if p in out
            ]
    assert not left, (
        f"a folded header under a credential key with a first word of 5 characters leaves its next lines readable "
        f"(the folded-header rule reads the Authorization name only): {len(left)}, first {left[:3]}"
    )


def test_b12_2_a_digest_header_is_masked_after_any_white_space_character_between_the_scheme_and_the_parameters():
    # M159: the white space after `Digest` is any white space except a line break, not only a space or a tab. The raw rule path
    # is read (`redact`): the card path also masks a value of another shape, which hid the fault in batch 11.
    left = []
    for name, sp in (
        ("vertical tab", "\x0b"),
        ("form feed", "\x0c"),
        ("no-break space", "\xa0"),
        ("ideographic space", "　"),
        ("next line", "\x85"),
        ("file separator", "\x1c"),
    ):
        text = f'Authorization: Digest{sp}username="u", realm="r", response="{LOW_ENTROPY_PIECES[0]}"\nnext\n'
        if LOW_ENTROPY_PIECES[0] in redact_module.redact(text).text:
            left.append(name)
    assert not left, (
        f"a Digest header after the white space {left} is left readable (a vertical tab is no line space)"
    )


def test_b12_2_a_digest_header_and_its_folded_lines_are_one_masked_value():
    # M163: the Digest rule goes on over the folded lines itself. Another rule masks the folded lines too, as a second value; the
    # header and its lines are ONE credential, so one placeholder stands for all of it (the map holds the whole value).
    text = f'Authorization: Digest username="u", realm="realm-x",\n response="{LOW_ENTROPY_PIECES[0]}"\n\tnonce="{LOW_ENTROPY_PIECES[1]}"\nnext\n'
    out = redact_module.redact(text).text
    assert out.count("<SECRET_") == 1 and not any(p in out for p in LOW_ENTROPY_PIECES[:2]), (
        f"a Digest header does not go on over folded lines as one value: {out!r}"
    )


# ---- Group 4: a folded Authorization header with ANY scheme word, extra words on its first line, or other line-break characters -----

from tests.test_q8b_batch11 import left_readable

G4_SCHEMES = (
    "NTLM",
    "Negotiate",
    "OAuth",
    "Splunk",
    "Hawk",
    "Custom-Scheme",
    "AWS4-HMAC-SHA256",
    "SCRAM-SHA-256",
    "Mutual",
)
G4_BREAKS = ("\n", "\r\n", "\x0b", "\x0c", "\x85", " ", " ")


def test_b12_4_a_folded_authorization_header_is_masked_for_any_scheme_word_and_every_break_character():
    left = []
    for i, scheme in enumerate(G4_SCHEMES):
        for nl in G4_BREAKS:
            a, b = LOW_ENTROPY_PIECES[0] + str(i), LOW_ENTROPY_PIECES[1] + str(i)
            text = f"Authorization: {scheme} {a}{nl} {b}{nl}Accept: shown\n"
            # The card path writes a rare break that a space or a tab follows as a LINE FEED before the rules run (batch 13, group 7), so
            # a header folded over it is read as a folded header there too; every break is checked on the card path and the rule path.
            outs = [clean(text), redact_module.redact(text).text]
            left += [
                f"{scheme} {nl!r}: {g!r}"
                for p in (a, b)
                for g in (p[:8], p[-8:])
                if any(g in o for o in outs)
            ]
    assert not left, (
        f"a folded header with a scheme word of the wide class or a rare break is readable: {left[:4]} ({len(left)})"
    )


def test_b12_4_extra_words_on_the_first_line_before_the_fold_are_masked_up_to_the_stated_reach():
    left = []
    for extra in range(8):
        words = " ".join("w" * 3 for _ in range(extra))
        a, b = LOW_ENTROPY_PIECES[0], LOW_ENTROPY_PIECES[2]
        text = f"Authorization: Custom-Scheme {a} {words}\n {b}\nAccept: shown\n"
        left += [f"{extra} extra words: {g}" for g in left_readable(text, [b])[:1]]
    assert not left, f"the folded line after extra words on the first line is readable: {left[:4]}"


def test_b12_4_a_lower_case_hyphen_token_is_not_read_as_a_scheme_word():
    # control: `ab-xy` is a token, so its first part must not stay readable as a scheme (the wide class is capitals only).
    # A word with a hyphen is the token itself; the word after it is a second word (the stated owner choice, shown). Read as a
    # scheme word, the first word would stay readable and the second would be masked instead.
    out = redact_module.redact("Authorization: abcdefgh-ijklmnop segmentalpha\n").text
    assert "abcdefgh" not in out, (
        f"a lower-case hyphen token is left readable as a scheme word: {out!r}"
    )


def test_b12_4_a_header_with_many_extra_words_and_folds_is_read_in_linear_time():
    import time

    def took(n: int) -> float:
        text = (
            "Authorization: Custom-Scheme x " * n
        )  # one long line of repeated headers, no fold: a read to the line end is quadratic
        t0 = time.perf_counter()
        redact_module.redact(text)
        return time.perf_counter() - t0

    took(500)
    small = min(took(3_000) for _ in range(3))
    big = min(took(12_000) for _ in range(3))
    assert big < small * 9, (
        f"the wide folded-header rule is not linear: {small:.3f}s and {big:.3f}s (4 times the size)"
    )


# ---- Group 3: the literal prefilter of the key-word rules (cost) ----------------------------------------------------------------

import re

G3_NAMES = [
    "password",
    "passwd",
    "pwd",
    "secret",
    "access_key",
    "accesskey",
    "account-key",
    "shared_access_key",
    "private_key",
    "api_key",
    "apikey",
    "auth_token",
    "access_token",
    "sas_token",
    "key_data",
    "cert_data",
    "certificate_data",
    "jsessionid",
    "phpsessid",
    "sessid",
    "connect.sid",
    "client_secret",
    "credential",
    "token",
    "signing_key",
    "encryption_key",
    "pass",
    "auth",
    "session",
    "bearer",
    "compass_key",
    "pass_phrase",
    "session_id",
    "session-key",
    "auth_value",
    "bearer_value",
    "protection_bypass",
    "x-vercel-protection-bypass",
    "authorization",
    "Authorization",
    "passcode",
    "possession_id",
    "bypass_key",
    "session_cookie",
    "token2",
    "pass1word",
]
G3_FOLDS = ("", "ſ", "ı", "İ", "K")  # long s, dotless i, dotted I, Kelvin sign


def _g3_corpus() -> list[str]:
    rnd = random.Random(1213)  # noqa: S311 - a seeded test generator, not a secret
    out = []
    for name in G3_NAMES:
        for variant in (
            name,
            name.upper(),
            name.capitalize(),
            name.replace("s", "ſ"),
            name.replace("i", "ı"),
            name.replace("k", "K"),
            name.replace("i", "İ"),
        ):
            v = made_up_value(zlib.crc32(variant.encode("utf-8")))
            out += [
                f"{variant}={v}",
                f'{{"{variant}": "{v}"}}',
                f"--{variant} {v}",
                f"x {variant}: {v}\n y",
                f"Authorization: {variant} {v}\n {v}\nnext",
                f"{variant}='{v} {v}' end",
                f"xx{variant}={v}",
                f"{variant}\n {v}",
            ]
    words = [
        "token",
        "pass",
        "key",
        "x",
        "  ",
        "=",
        ":",
        "\n ",
        '"',
        "'",
        "Authorization",
        "Bearer",
        "NTLM",
        "secret",
        "v" * 12,
        "\t",
        "ſ",
        "abc123XYZ",
    ]
    for _ in range(400):
        out.append("".join(rnd.choice(words) for _ in range(rnd.randint(2, 14))))
    return out


def test_b12_3_the_prefilter_gives_the_same_text_as_a_full_scan_of_every_rule(monkeypatch):
    corpus = _g3_corpus()
    with_gate = [redact_module.redact(t).text for t in corpus]
    monkeypatch.setattr(redact_module, "_GATES", {})
    without_gate = [redact_module.redact(t).text for t in corpus]
    differ = [(t, a, b) for t, a, b in zip(corpus, with_gate, without_gate, strict=True) if a != b]
    assert not differ, (
        f"the literal prefilter changes {len(differ)} of {len(corpus)} outputs: {differ[:2]!r}"
    )


def test_b12_3_every_match_of_a_prefiltered_rule_starts_at_one_of_its_literal_words():
    # The property the prefilter rests on, found by the rules themselves (not by the prefilter): a match start is a word start.
    gated = redact_module._GATES
    assert len(gated) == 9, (
        f"the number of prefiltered rules changed: {len(gated)} (a new rule needs its own proof below)"
    )
    bad = []
    for t in _g3_corpus():
        low = redact_module._gate_text(t)
        for pattern, words in gated.items():
            for m in pattern.finditer(t):
                if not any(low.startswith(w, m.start()) for w in words):
                    bad.append((pattern.pattern[:30], t[max(0, m.start() - 5) : m.start() + 20]))
    assert not bad, f"a match of a prefiltered rule starts where none of its words is: {bad[:3]}"


def test_b12_3_a_text_with_no_key_word_tries_no_prefiltered_rule_and_one_word_tries_each_key_rule_once():
    # Work, not seconds: the number of places where a prefiltered rule was tried.
    plain = ("the quick brown fox jumps over the lazy dog 12345 " * 6000)[:262_144]
    r = redact_module._Redactor(None)
    r.find(plain)
    assert r.gate_tries == 0, (
        f"{r.gate_tries} tries of a key-word rule on {len(plain)} characters with no key word"
    )
    one = plain[:100_000] + " token=abcd1234 " + plain[:100_000]
    r = redact_module._Redactor(None)
    r.find(one)
    key_rules = 5  # the folded-header rule with a key word, and the four key-word rules (unquoted, double quote, single quote, flag)
    assert r.gate_tries == key_rules, (
        f"one key word in 200,000 characters made {r.gate_tries} tries, not {key_rules}"
    )


def test_b12_3_the_characters_that_ignore_case_reads_as_an_ascii_letter_are_exactly_the_four_the_fold_knows():
    found = {}
    for cp in range(128, 0x110000):
        c = chr(cp)
        if re.fullmatch("[a-z]", c, re.IGNORECASE):
            found[c] = next(
                x for x in "abcdefghijklmnopqrstuvwxyz" if re.fullmatch(x, c, re.IGNORECASE)
            )
    folded = {chr(k): v for k, v in redact_module._GATE_FOLD.items()}
    assert found == folded, (
        f"the fold of the prefilter differs from the ignore-case reading: {found} against {folded}"
    )
    for word in redact_module.KEY_GATE_WORDS + ("authorization",):
        assert word == word.lower() and word.isascii(), word


# ---- Evidence group: a key in capitals with `cookie`, written in a compatibility form (control: it was true on 2153ad85 too) --------


def test_b12_5_a_capitals_cookie_key_in_fullwidth_circled_long_s_and_zero_width_forms_is_masked_on_the_five_paths():
    """CONTROL, passes on the old code on purpose: it backs the sentence in CHANGELOG that the five paths mask these forms (the card path
    folds compatibility forms before the rules run; the record walk folds them itself). The raw rule function `redact()` alone does not
    fold fullwidth, circled or zero-width forms, and is not a product path: every product path reads text through a folding step."""
    left = []
    for key in ("COOKIESTORE", "COOKIEſTORE", "ＣＯＯＫＩＥＳＴＯＲＥ", "COOKIE\u200bSTORE"):
        shown = readable_on(f"{key}=segmentalpha", "segmentalpha")
        if shown:
            left.append((key, shown))
    assert not left, (
        f"a capitals cookie key in a compatibility form is readable on a product path: {left}"
    )

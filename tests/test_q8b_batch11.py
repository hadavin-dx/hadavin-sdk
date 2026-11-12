"""Q8b batch 11 (round 11 of the redaction path): the classes the round 11 review and the independent evidence found.

Issue 8: a header whose credential goes on over folded lines (each next line starts with a space or a tab, RFC 9112 section 5.2)
after `Basic`, `Token`, `ApiKey`, `Bearer` or `Digest`, and a credential key with a scheme word and a token behind it that the key
rule did not read (a line break with no indent after the scheme word, or a `:` inside the token).

Both sides are pinned: what is masked, and what stays readable by a stated limit (see LIMITS in `k1b/redaction.py`):
  - a line that does not start with a space or a tab ends the header (the `Host:` line after it is shown);
  - a token ends at white space on its line: the second word after it is shown (as after a credential flag);
  - the fold run has no upper bound: an unrelated indented block right after the header is masked (a cost).
"""

from __future__ import annotations

import importlib
import itertools
import random
import time

import pytest

from hadavin_sdk.approvals.channel import clean
from tests.test_q8b_batch7 import readable_on

redact = importlib.import_module("hadavin_sdk.guard.redact")

SCHEMES = ("Basic", "Token", "ApiKey", "Bearer", "Digest")
HEADERS = ("Authorization: ", "Proxy-Authorization: ", "X-Api-Key: ", "token=", "secret: ", "passwd=")
BREAKS = ("\n", "\r\n")
INDENTS = (" ", "    ", "\t")
_ALPHA = "xkvmzwhtrpnqbdfglscyaeuJQKZ"  # made-up letters; no real value


def piece(seed: int, n: int = 32) -> str:
    """A made-up token piece of n characters (letters and digits), different for each seed."""
    rnd = random.Random(seed)
    return "".join(rnd.choice(_ALPHA + "0123456789") for _ in range(n))


def grams(s: str, k: int = 8) -> list[str]:
    return [s[i : i + k] for i in range(len(s) - k + 1)]


def left_readable(text: str, pieces: list[str]) -> list[str]:
    outs = _outs(text)
    return [f"{g!r}" for p in pieces for g in grams(p) if any(g in out for out in outs)]


def _outs(text: str) -> list[str]:
    return [clean(text), redact.redact(text).text]


# ---- Issue 8: the continuation lines of a folded header ----------------------------------------------------------------


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b11_8_the_folded_lines_of_a_header_are_masked_for_every_scheme_and_header_name(scheme):
    """Main, `c36ce0dc` and `166d1313` left the lines after the first readable for Basic, Token, ApiKey and Bearer (72 of 72 probe cells;
    Digest was fixed in batch 10). The header name is `Authorization`, `Proxy-Authorization` or a credential key."""
    left = []
    for head, nl, ind, lines in itertools.product(HEADERS, BREAKS, INDENTS, (2, 3, 4)):
        parts = [piece(i + 1) for i in range(lines)]
        text = f"{head}{scheme} {parts[0]}{nl}" + "".join(f"{ind}{p}{nl}" for p in parts[1:])
        text += "Accept: text-shown\n"
        for g in left_readable(text, parts):
            left.append(f"{head!r} {nl!r} {ind!r} {lines}: {g}")
        assert "Accept: text-shown" in clean(text), "the line after the header was masked"
    assert not left, f"a folded {scheme} header leaves its next lines readable: {left[:4]} ({len(left)})"


@pytest.mark.parametrize("scheme", ("Basic", "Token", "ApiKey", "Bearer"))
def test_b11_8_a_scheme_word_at_the_end_of_its_line_and_the_token_on_the_folded_lines(scheme):
    left = []
    for head, nl, ind in itertools.product(HEADERS[:3], BREAKS, INDENTS):
        a, b = piece(41), piece(42)
        text = f"{head}{scheme}{nl}{ind}{a}{nl}{ind}{b}{nl}Accept: text-shown\n"
        left += [g for g in left_readable(text, [a, b])]
    assert not left, f"a token on the folded lines after {scheme} is readable: {left[:4]}"


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b11_8_a_credential_key_a_scheme_word_a_break_with_no_indent_and_the_token(scheme):
    """Wrapped form of the fuzz (222 of 1005 texts readable on `166d1313`, all with a credential key that is not `Authorization`):
    `token=Bearer<LF>abcdefgh`: the key rule stopped at the line break."""
    left = []
    for key, eq, brk, shape in itertools.product(
        ("token", "secret", "passwd", "X-Api-Key"),
        ("=", ": "),
        ("\n", "\r\n", "\r", "\n\n", "\n  ", "\r\n\t"),
        ("plain", "colon", "dash", "dot"),
    ):
        base = piece(7, 27)
        tok = {
            "plain": base,
            "colon": base[:9] + ":" + base[10:],
            "dash": base[:9] + "-" + base[10:],
            "dot": base[:9] + "." + base[10:],
        }[shape]
        text = f"{key}{eq}{scheme}{brk}{tok}\nnext line ok\n"
        left += [f"{text!r}: {g}" for g in left_readable(text, [tok])[:1]]
    assert not left, f"a token after {scheme} and a line break is readable: {left[:4]} ({len(left)})"


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b11_8_a_token_with_a_colon_after_a_scheme_word_on_the_same_line_is_masked(scheme):
    """`token: ApiKey id:secret`: the key rule read `id:` as the start of another `k:v` pair and stopped there."""
    tok = "Rm0:" + piece(10, 24)
    for key, eq in itertools.product(("token", "secret", "passwd", "X-Api-Key"), ("=", ": ")):
        text = f"{key}{eq}{scheme} {tok}\nnext line ok\n"
        assert not left_readable(text, [tok]), f"a token with a colon is readable: {text!r}"


def test_b11_8_the_digest_header_folded_after_a_first_line_of_fewer_than_8_characters():
    """`Authorization: Digest u="a",<LF> response="<hash>"`: the first line has 6 characters; the Digest rule read neither form."""
    h = piece(5, 32)
    for nl, ind in itertools.product(BREAKS, INDENTS):
        text = f'Authorization: Digest u="a",{nl}{ind}response="{h}"{nl}Accept: text-shown\n'
        assert not left_readable(text, [h]), f"a folded Digest response is readable: {text!r}"
        assert "Accept: text-shown" in clean(text)


# ---- Issue 8 and 4: both sides of the limits ------------------------------------------------------------------------------


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b11_8_a_line_that_does_not_start_with_a_space_or_a_tab_ends_the_header(scheme):
    """Stated limit: the token is masked to the last folded line; the next line without an indent is a new line and stays readable,
    so `Accept:` stays (and so does a continuation without an indent: it cannot be told from a new header)."""
    a, b = piece(21), piece(22)
    for nl in BREAKS:
        text = f"Authorization: {scheme} {a}{nl} {b}{nl}Accept: text-shown{nl}x-trace-id: aaaabbbbcccc{nl}"
        out = clean(text)
        assert "Accept: text-shown" in out and "x-trace-id: aaaabbbbcccc" in out, (
            f"a line with no indent after the folds was masked: {out!r}"
        )
        assert not left_readable(text, [a, b])
        unindented = f"Authorization: {scheme} {a}{nl}{b}{nl}"
        assert b[:8] in clean(unindented), "a line with no indent was masked: it is a new line (stated limit)"


@pytest.mark.parametrize("scheme", ("Basic", "Token", "ApiKey", "Bearer"))
def test_b11_8_a_second_word_on_the_same_line_is_shown_as_after_a_credential_flag(scheme):
    """Stated limit (the owner's second-word choice, here for the header): the token ends at white space on its line
    (RFC 9110 section 11.4, a token has no space); the Digest rule masks to the end of the line (its parameters hold spaces)."""
    tok, second = piece(31, 20), piece(32, 12)
    text = f"Authorization: {scheme} {tok}  {second}\n"
    assert second in clean(text) and tok not in clean(text)


def test_b11_8_the_fold_run_has_no_upper_bound_so_an_indented_block_after_the_header_is_masked_the_stated_cost():
    tok = piece(51)
    prose = "".join(f"  indented line number {i} of a log\n" for i in range(60))
    out = clean(f"Authorization: Bearer {tok}\n{prose}Accept: text-shown\n")
    assert "indented line number 3 " not in out and "indented line number 59 " not in out, (
        f"the fold run has an upper bound: {out[:200]!r}"
    )
    assert "Accept: text-shown" in out


def test_b11_8_a_long_run_of_folded_lines_is_read_in_linear_time():
    def took(n: int) -> float:
        text = "Authorization: Bearer " + piece(61, 12) + "\n" + " abcdefgh1234\n" * n + "end"
        t0 = time.perf_counter()
        redact.redact(text)
        return time.perf_counter() - t0

    took(500)
    small = min(took(5_000) for _ in range(3))
    big = min(took(20_000) for _ in range(3))
    assert big < small * 12, f"folded lines are not read in linear time: {small:.3f}s for 5000, {big:.3f}s for 20000"


# ---- Issue 8: the fuzz of the evidence, every shape that is not a stated limit ------------------------------------------


def test_b11_8_fuzz_a_credential_wrapped_over_folds_is_never_left_readable():
    """The evidence fuzz restricted to the shapes that are not a stated limit: pieces of one secret joined by line folds
    (a break and an indent), after any scheme and header name, plus a break with no indent right after the scheme word."""
    rnd = random.Random(11)
    left = []
    for i in range(400):
        scheme = rnd.choice(SCHEMES)
        head = rnd.choice(HEADERS)
        n = rnd.randint(2, 5)
        parts = [piece(1000 * i + j, rnd.randint(16, 40)) for j in range(n)]
        nl, ind = rnd.choice(BREAKS), rnd.choice(INDENTS)
        gap = rnd.choice((" ", nl, nl + ind))
        text = f"{head}{scheme}{gap}{parts[0]}" + "".join(f"{nl}{ind}{p}" for p in parts[1:]) + "\nnext line ok\n"
        for g in left_readable(text, parts)[:1]:
            left.append(f"{text!r}: {g}")
    assert not left, f"a folded credential is readable: {left[:3]} ({len(left)})"


def test_b11_8_the_five_paths_agree_for_a_folded_bearer_header():
    a, b = piece(71), piece(72)
    text = f"Authorization: Bearer {a}\n    {b}\nAccept: text-shown\n"
    assert not readable_on(text, a[:12], b[:12])


def test_b11_8_a_line_of_repeated_headers_is_read_in_linear_time():
    """The first line of a folded header is the scheme word and one word: a read to the end of the line would start again at each
    `Authorization: Bearer x` of one long line and take quadratic time (6000 repeats took 3.3 s in the rule)."""

    def took(n: int) -> float:
        text = "Authorization: Bearer x " * n
        t0 = time.perf_counter()
        redact.redact(text)
        return time.perf_counter() - t0

    took(500)
    small = min(took(3_000) for _ in range(3))
    big = min(took(12_000) for _ in range(3))
    assert big < small * 9, f"a line of repeated headers is not read in linear time: {small:.3f}s and {big:.3f}s (4 times the size)"


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b11_8_after_a_scheme_word_and_a_break_a_first_word_of_fewer_than_8_characters_is_shown_the_stated_cost(scheme):
    """Both sides of the cost for a credential key (as for `Authorization` in batch 10): a line that starts with a word of fewer than 8
    characters after `token=<scheme><LF>` is read as prose and shown; one that starts with 8 or more is masked."""
    shown = f"token={scheme}\nshort words only\n"
    assert clean(shown).count("short words only") == 1, (
        f"the first word of fewer than 8 characters was masked: {clean(shown)!r}"
    )
    assert "authentication" not in clean(f"token={scheme}\nauthentication failed\n"), (
        "the first word of 8 or more characters after the scheme word is readable"
    )

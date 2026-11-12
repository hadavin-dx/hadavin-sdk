"""Q8b batch 10 (round 10 of the redaction path): the classes the round 10 review and the independent evidence found.

Classes (each fixed where every caller routes through, `guard/redact.py` for the card, the tool result, the text of a run and a
log line, `k1b/redaction.py` for the record keys):
  1. a wrapped authorization header read narrower than main's `\\s+`: a token of 8 to 15 characters, a lower-case one, or one with a
     dot, a tilde, a colon or a hyphen early, after a line break, was readable (810 of 2000 probe cells);
  2. a Digest header folded over more than one line left the response hash readable;
  6. an ordinary word (`compass`, `possession`) and a second word of its own family (`compass_key`, `possession_id`) is a
     credential name on every path, as `bypass_key` was in round 9; the record walk and the text rule read `COOKIEJAR` alike.
The five paths are those of `tests/test_q8b_batch7.py`: card, tool, run, log, record message (and the record key).
"""

from __future__ import annotations

import importlib
import itertools
import re
import time

import pytest

from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.k1b import redaction as R
from tests.test_q8b_batch7 import (
    CHANGELOG,
    ORDINARY_VALUE,
    V,
    readable_on,
    record_key_output,
)

redact = importlib.import_module("hadavin_sdk.guard.redact")

SCHEMES = ("Basic", "Token", "ApiKey", "Digest", "Bearer")
BREAKS = ("\n", "\r\n", "\n\n", "\n\n  ", "\r")
LENGTHS = (8, 12, 15, 16, 20)
_BASE = "xkvmzwhtrp" + "nqbdfglscy" + "aeu"  # made-up lower-case letters


def token_shapes(n: int) -> dict[str, str]:
    """Made-up tokens of n characters in the shapes of the review: a capital and a digit, lower-case only, a digit only, and a dot,
    a tilde, a colon or a hyphen early."""
    return {
        "mixed": ("Jq7" + _BASE)[:n],
        "lower": _BASE[:n],
        "lower+digit": _BASE[: n - 1] + "7",
        "capital-only": ("Q" + _BASE)[:n],
        "dot-early": ("ab." + _BASE)[:n],
        "tilde-early": ("ab~" + _BASE)[:n],
        "colon-early": ("ab:" + _BASE)[:n],
        "hyphen-early": ("ab-" + _BASE)[:n],
    }


# ---- Issue 1: a wrapped header, token of any length from 8 ------------------------------------------------------------------


@pytest.mark.parametrize("scheme", SCHEMES)
def test_b10_1_a_wrapped_authorization_token_of_8_or_more_characters_is_masked_after_any_line_break(
    scheme,
):
    """Regression of batch 9 against main (810 of 2000 probe cells): after `Authorization: <scheme>` a line break, a blank line or
    a break and spaces, then a token of 8 to 20 characters of any shape (lower case, a dot, a tilde, a colon or a hyphen early) was
    readable. The rule's own minimum is 8 and its value class is `[^\\s\"']`, as on main."""
    left = []
    for head, brk, n in itertools.product(
        ("Authorization: ", "authorization=", '"Authorization": "'), BREAKS, LENGTHS
    ):
        for shape, token in token_shapes(n).items():
            text = f"{head}{scheme}{brk}{token}"
            out = clean(text)
            if any(token[i : i + 6] in out for i in range(len(token) - 5)):
                left.append(f"{shape} {text!r}")
    assert not left, (
        f"a wrapped {scheme} header leaves a token of 8 or more characters readable: {left[:5]} ({len(left)})"
    )


def test_b10_1_the_exact_inputs_of_the_review_are_masked_on_every_path():
    cases = (
        ("Authorization: Basic\n" + "dXNlcjpw" + "YXNz", "dXNlcjpw"),  # 12 characters
        ("Authorization: Token\n" + "abcd1234" + "efgh", "abcd1234efgh"),
        ("Authorization: Token\n" + "ab.cdefgh" + "ijklmnopqrstu", "ab.cdefghijklmnopqrstu"),
        ("Authorization: Basic\n\n  " + "cm9vdDp0" + "b29y", "cm9vdDp0"),
        ("Authorization: Basic\n" + "abcdefghij" + "klmnopqrstuv", "abcdefghijklmnopqrstuv"),
        ("Authorization: Token\n" + "abcdefghij" + "klmnopqrstuv", "abcdefghijklmnopqrstuv"),
        ("Authorization: ApiKey\r\n" + "q1w2e3r4" + "t5y6", "q1w2e3r4"),
        ("Authorization: Digest\r\n" + "q1w2e3r4" + "t5y6", "q1w2e3r4"),
    )
    left = []
    for text, piece in cases:
        left += [f"{text!r}: {x}" for x in readable_on(text, piece)]
    assert not left, f"a wrapped header of the review is readable: {left[:6]}"


def test_b10_1_the_basic_rule_alone_masks_a_bare_wrapped_value_of_8_to_15_characters():
    """The Basic rule has no `Authorization` in front of it (main: `\\bbasic\\s+([a-z0-9+/<>_]{8,}`): `Basic<LF><8 characters>` is masked."""
    for brk, n in itertools.product(BREAKS, (8, 9, 12, 15)):
        token = ("dXNlcj" + "pwYXNzd29yZA")[:n]
        text = f"curl -H Basic{brk}{token} end"
        assert not readable_on(text, token), f"a short wrapped Basic value is readable: {text!r}"


def test_b10_1_a_first_word_of_8_or_more_characters_after_a_scheme_word_is_masked_the_stated_cost():
    """Both sides of the cost (round 10 Issue 1): the line after a scheme word is read as the token when its first word has 8 or
    more characters (main did the same: `Authorization: Basic<LF>authentication failed` was masked), and stays readable
    when it starts with a word of fewer than 8 characters."""
    for scheme in ("Basic", "Token", "ApiKey", "Digest"):
        for line, masked_word in (
            ("readable-prose-line here", "readable-prose-line"),
            ("authentication failed", "authentication"),
            ("abcdefghijklmnopqrstuvwx", "abcdefghijklmnopqrstuvwx"),
        ):
            out = clean(f"Authorization: {scheme}\n{line}")
            assert masked_word not in out, (
                f"the first word of 8 or more characters is readable: {out!r}"
            )
        for line in ("short words only", "an ordinary line", "seven77 chars"):
            text = f"Authorization: {scheme}\n{line}"
            assert clean(text) == text, (
                f"a first word of fewer than 8 characters was masked: {clean(text)!r}"
            )


def test_b10_1_the_fix_changes_nothing_for_a_text_that_has_no_scheme_word_before_a_line_break():
    """Control (it passes on the old code too): an Authorization line whose value is on the same line is read as before."""
    text = "Authorization: Bearer " + "Jq7" + "firstValueXyz" + "\nnext line"
    assert V not in clean(text) and clean(text).endswith("\nnext line")


def test_b10_1_a_long_run_of_line_breaks_after_a_scheme_word_is_read_in_linear_time():
    size = 150_000
    for text in (
        "Authorization: Token" + "\n" * size + "x",
        "Authorization: Basic" + "\r\n" * (size // 2) + "short",
        "Authorization: ApiKey" + "\n \t" * (size // 3) + "x",
        "Authorization: Token\nab\n" * (size // 24),
    ):
        t0 = time.perf_counter()
        clean(text)
        assert time.perf_counter() - t0 < 20, "a gap after a scheme word takes far too long"


def test_b10_1_the_differential_against_main_for_every_generated_token_length_shape_gap_and_scheme():
    """The two rules of main written out as they were (`\\s+` between the scheme word and the token). Every generated text that
    one of them masks is masked by the redactor: any length from 8, any shape, any gap of white space, any scheme word, the rule
    bare and inside an Authorization header. Batch 9 passed this only for tokens of 16 or more characters."""
    main_basic = re.compile(r"(?i)\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})")
    main_auth = re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']?(?:[a-z]+\s+)?([^\s\"']{8,})")
    gaps = (
        " ",
        "\t",
        "\n",
        "\r\n",
        "\r",
        "\n\n",
        "\n ",
        "\r\n\t",
        "\x0b",
        "\x0c",
        "\x85",
        "\xa0",
        "  \n  ",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x1f",
        "\u2028",
        "\u2029",
    )
    heads = ("Authorization: ", "authorization=", 'x "Authorization": "', "")
    schemes = ("Basic", "Token", "ApiKey", "Digest", "Bearer", "Negotiate", "Foo")
    checked = 0
    for n in (8, 9, 12, 15, 16, 24):
        for shape, token in token_shapes(n).items():
            for scheme, gap, head in itertools.product(schemes, gaps, heads):
                text = f"{head}{scheme}{gap}{token} tail"
                taken = []
                if scheme == "Basic" and (m := main_basic.search(text)):
                    taken.append(m.group(1))
                if head and (m := main_auth.search(text)):
                    taken.append(m.group(1))
                for piece in taken:
                    if len(piece) < 8 or not set(piece) <= set(token):
                        continue
                    checked += 1
                    left = readable_on(text, piece[:8])
                    assert not left, (
                        f"main masked {text!r} ({shape}), the redactor does not: {left[:3]}"
                    )
    assert checked > 2000, f"the differential compared only {checked} generated texts"


# ---- Issue 2: a Digest header folded over several lines ------------------------------------------------------------------


DIGEST_HASH = "8ca523f5" + "e9506fed" + "4657c970" + "0ebdbec1"
DIGEST_NONCE = "dcd98b72" + "02ab31cd" + "9fe0"


@pytest.mark.parametrize("brk", ["\n", "\r\n", "\r"])
def test_b10_2_a_digest_header_folded_over_three_lines_is_masked_whole(brk):
    """RFC 7616 style: username, realm, nonce and response over several lines, each continuation starting with a space or a tab
    (the line fold of RFC 9112 section 5.2). Main and batch 9 left `response=` and `nonce=` readable."""
    for indent in ("    ", "\t", " "):
        text = (
            f'Authorization: Digest username="u",{brk}{indent}realm="r",{brk}{indent}nonce="{DIGEST_NONCE}",'
            f'{brk}{indent}response="{DIGEST_HASH}"{brk}Next line stays'
        )
        left = readable_on(text, DIGEST_HASH, DIGEST_NONCE)
        assert not left, f"a folded Digest header leaves a hash readable: {left[:4]} for {text!r}"
        assert (
            clean(text).endswith("Next line stays") and "Next line stays" not in clean(text)[:-15]
        ), clean(text)


def test_b10_2_a_digest_header_ends_at_the_first_line_that_does_not_start_with_a_space_or_a_tab():
    text = f'Authorization: Digest username="u",\n  response="{DIGEST_HASH}"\nplain=line and more text here'
    out = clean(text)
    assert DIGEST_HASH not in out
    assert out.endswith("\nplain=line and more text here"), (
        "a Digest header goes on over a line that does not start with a space or a tab: " + out
    )


def test_b10_2_a_long_run_of_digest_fold_lines_is_read_in_linear_time():
    size = 120_000
    texts = (
        'Authorization: Digest a="bbbbbbbb"' + ",\n x" * (size // 4),
        "Authorization: Digest" + "\n" + " x\n" * (size // 3),
        "Authorization: Digest aaaaaaaa" + "\r\n\t" * (size // 3) + "end",
    )
    for text in texts:
        t0 = time.perf_counter()
        out = clean(text)
        assert time.perf_counter() - t0 < 20, "a folded Digest header takes far too long"
        assert "bbbbbbbb" not in out


# ---- Issue 6: an ordinary word and a second word of its family ---------------------------------------------------------------

SEPARATORS = ("_", "-", "")
FORMS = (
    "cfg {k}={v} end",
    "cfg {k}: {v} end",
    'cfg {k}="{v} {v}" end',
    '{{"{k}": "{v}"}}',
    "ran --{k} {v} --verbose",
    "ran --{k}={v} --verbose",
)
ALL_SECOND_WORDS = ("key", "phrase", "code", "value", "id", "cookie")


def _family_pairs():
    return [(w, s) for w in sorted(redact.ORDINARY_WORDS) for s in redact.ordinary_second_words(w)]


def test_b10_6_every_ordinary_word_has_the_second_words_of_its_family_from_the_one_table():
    pairs = _family_pairs()
    assert len(pairs) >= 50, f"the table of second words has only {len(pairs)} pairs"
    for w in redact.ORDINARY_WORDS:
        bare = "pass" if w.endswith("pass") else "session"
        assert w.endswith(bare)
        assert redact.ordinary_second_words(w) == tuple(
            s for b, s in redact._GUARDED_PAIRS if b == bare
        ), f"the second words of {w} are not those of its bare word {bare}"
        assert redact.ordinary_second_words(w), f"{w} has no second words in the table"
    assert redact.ordinary_second_words("compass") == ("phrase", "code", "key", "value")
    assert redact.ordinary_second_words("possession") == ("id", "key", "cookie", "value")
    assert redact.ordinary_second_words("author") == ()
    assert redact.is_ordinary_pair("compass", "key") and not redact.is_ordinary_pair(
        "compass", "id"
    )


@pytest.mark.parametrize("word", sorted(redact.ORDINARY_WORDS))
def test_b10_6_an_ordinary_word_and_a_second_word_of_its_family_is_masked_on_every_path_and_form(
    word,
):
    left = []
    for second in redact.ordinary_second_words(word):
        for sep in SEPARATORS:
            key = f"{word}{sep}{second}"
            assert R.sensitive(key), f"the record walk shows the key {key}"
            for form in FORMS:
                if second == "cookie" and form.startswith("ran --"):
                    continue  # a cookie FLAG is an exact name (round 8 Issue 2); the key rules mask the rest
                left += [f"{key} {form}: {x}" for x in readable_on(form.format(k=key, v=V), V)]
            if V in record_key_output(key, V):
                left.append(f"{key} record key")
    assert not left, (
        f"an ordinary word and a second word of its family is readable: {left[:6]} ({len(left)})"
    )


@pytest.mark.parametrize("word", sorted(redact.ORDINARY_WORDS))
def test_b10_6_a_name_that_ends_in_key_secret_token_or_password_after_an_ordinary_word_is_masked(
    word,
):
    left = []
    for ending in ("key", "secret", "token", "password", "passwd"):
        for sep in ("_", "-"):
            name = f"{word}{sep}{ending}"
            if not R.sensitive(name):
                left.append(f"{name} record walk")
            for form in FORMS:
                left += [f"{name} {form}: {x}" for x in readable_on(form.format(k=name, v=V), V)]
            if V in record_key_output(name, V):
                left.append(f"{name} record key")
    # `key` is a second word of its family; the other three need no entry in the table (credential words after any word)
    assert not left, (
        f"a name ending in key, secret, token or password is readable: {left[:6]} ({len(left)})"
    )


@pytest.mark.parametrize("word", sorted(redact.ORDINARY_WORDS))
def test_b10_6_an_ordinary_word_alone_or_with_a_second_word_of_no_family_stays_readable(word):
    """The other side, pinned: the bare word and a second word that is no word of its family (`compass_direction`, a bare
    `possession`) stay readable in every form. A word of ANOTHER family's table is no entry here (`compass_id`)."""
    # `cookie` is a credential ending after any word (round 8), so it is no "second word of no family"
    other = tuple(
        s for s in ALL_SECOND_WORDS if s != "cookie" and s not in redact.ordinary_second_words(word)
    )
    keys = [word] + [f"{word}{sep}{s}" for s in other for sep in ("_", "-")]
    keys += [f"{word}_direction", f"{word}-name", f"{word}_level"]
    left = []
    for key in keys:
        assert not R.sensitive(key), f"the record walk masks {key}"
        for form in FORMS:
            if form.startswith("ran --") and key.endswith("cookie"):
                continue
            text = form.format(k=key, v=ORDINARY_VALUE)
            # Round 13 (group 1): a QUOTED value behind a name with a tail is masked as `main` masked it; the bare word stays shown
            # in every form (owner question q-q8b-bare-bypass), and every unquoted and flag form of the other names stays shown.
            quoted = '"' in form and key != word
            if (clean(text) == text) is quoted:
                left.append(f"{key} {form}: {clean(text)!r}")
        if ORDINARY_VALUE not in record_key_output(key, ORDINARY_VALUE):
            left.append(f"{key} record key masked")
    assert not left, f"an ordinary name was masked: {left[:6]} ({len(left)})"


def test_b10_6_a_bare_word_that_holds_nothing_stays_readable_and_the_credential_neighbours_are_masked():
    """Both sides in one place for the names the review named: `compass_key`, `overpass_key`, `encompass_key`, `compass_code`,
    `overpass_value`, `encompass_phrase`, `possession_id`, `obsession_id` are masked; the bare `bypass` stays readable
    (question `q-q8b-bare-bypass` to the owner; default: shown)."""
    for key in (
        "compass_key", "overpass_key", "encompass_key", "compass_code", "overpass_value", "encompass_phrase",
        "possession_id", "obsession_id", "bypass_key",
    ):  # fmt: skip
        assert R.sensitive(key), key
        for form in FORMS:
            assert not readable_on(form.format(k=key, v=V), V), f"{key} {form}"
    for key in ("bypass", "compass", "possession", "obsession", "author"):
        assert not R.sensitive(key), key
        for form in FORMS[:3] + FORMS[4:5]:
            text = form.format(k=key, v=ORDINARY_VALUE)
            assert clean(text) == text, f"{key}: {clean(text)!r}"


def test_b10_6_an_ordinary_word_must_start_a_word_to_stay_readable_so_xcompass_key_is_a_key_as_before():
    for key in ("xcompass_key", "xpossession_id", "xbypass_key", "mycompasskey"):
        assert R.sensitive(key), key
        assert not readable_on(f"cfg {key}={V} end", V), key
    for key in ("xcompass", "xbypass", "xpossession", "xoverpass"):
        assert R.sensitive(key), f"the record walk shows {key}"
        assert not readable_on(f"cfg {key}={V} end", V), (
            f"an ordinary word that does not start a word (the bare key {key}) is read as an ordinary word"
        )


# ---- Issue 6: the text rule and the record walk read a key written in capitals alike -------------------------------------------


def _spellings(base: str, rest: str) -> list[str]:
    return [
        base.lower() + rest.lower(),
        base.upper() + rest.upper(),
        base.capitalize() + rest.capitalize(),
        base.lower() + "_" + rest.lower(),
        base.upper() + "_" + rest.upper(),
        base.lower() + rest.capitalize(),
        base.upper() + rest.lower(),
    ]


def test_b10_6_the_text_rule_and_the_record_walk_agree_for_a_cookie_word_and_one_more_word():
    """A text `KEY=value` and a record key `KEY` are read alike for `cookie` + `jar` | `store` | `policy` | `name` in seven
    spellings (the r7 class: text versus record drift). `COOKIEJAR` was masked as text and readable as a record key."""
    left = []
    for rest in ("jar", "store", "policy", "name", "domain"):
        for key in _spellings("cookie", rest):
            as_text = V not in clean(f"cfg {key}={V} end")
            as_record = R.sensitive(key)
            if as_text != as_record:
                left.append(f"{key}: text masks {as_text}, record masks {as_record}")
    assert not left, f"the text rule and the record walk disagree: {left[:8]} ({len(left)})"


def test_b10_6_cookiejar_and_cookiestore_in_capitals_are_masked_as_a_record_key_and_in_lower_case_they_are_not():
    for key in ("COOKIEJAR", "COOKIESTORE", "COOKIES2JAR"):
        assert R.sensitive(key), key
        assert V not in record_key_output(key, V), key
        assert V not in clean(f"cfg {key}={V} end"), key
    for key in ("cookiejar", "cookiestore", "mycookiejar", "MYCOOKIEJAR"):
        assert not R.sensitive(key), key
        assert clean(f"cfg {key}={ORDINARY_VALUE} end") == f"cfg {key}={ORDINARY_VALUE} end", key


# ---- notes: LIMITS and CHANGELOG --------------------------------------------------------------------------------------------


def test_b10_limits_and_changelog_say_what_the_round_10_code_does():
    block = CHANGELOG.split("round 10 (batch 10)", 1)[1].split("round 9 (batch 9)", 1)[0]
    for word in (
        "810",
        "10,403,890",
        "Digest",
        "compass_key",
        "possession_id",
        "COOKIEJAR",
        "q-q8b-bare-bypass",
        "bypass=true",
    ):
        assert word in block, f"the batch 10 entry does not name {word}"
    assert "Owner decision not needed" not in CHANGELOG
    assert "authorization=a b" in R.LIMITS and "not a flag" in R.LIMITS, (
        "LIMITS calls `authorization=a b` a flag"
    )
    assert "q-q8b-bare-bypass" in R.LIMITS
    assert "line fold" in R.LIMITS and "folded" in R.LIMITS
    assert re.search(r"8 or more characters", R.LIMITS)

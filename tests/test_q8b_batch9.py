"""Q8b batch 9 (round 9 of the redaction path): the classes the round 9 review and the independent evidence found.

Classes (each fixed at the one place every caller routes through, `guard/redact.py` for the card, the tool result, the text of a
run and a log line, `k1b/redaction.py` for the record keys):
  1. a wrapped authorization header (`Authorization: Basic<line break><token>`): a gap between a scheme word and its token is a
     space of any kind that does not end the line, a line fold, or a line break in front of a long token (as main read `\\s+`);
  2. pins for the claims of batch 8 that had none (`--pass2 a b`, `authorization=a b`, `--apiInputTokens`, `COOKIEJAR`);
  4. a key tail and a look-ahead that disagreed (`pass` + 21 or 40 digits + `=`; `cookie2`, `cookie_name2`);
  5. copies of one list that were not tied (`_AUTH_FLAG` bound, the cookie flag names) and rules that no test timed;
  6. the cells of the evidence list that were readable on the last head (`bypass_key`, `x-vercel-protection-bypass`, the wget
     switches, `Digest` and a prose line, `possession_id`, `compass_code`).
The five paths are those of `tests/test_q8b_batch7.py`: card, tool, run, log, record message (and the record key).
"""

from __future__ import annotations

import importlib
import itertools
import pathlib
import re
import time

import pytest

from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.k1b import redaction as R
from tests.test_q8b_batch7 import (
    CHANGELOG,
    ORDINARY_VALUE,
    V,
    W,
    five_paths,
    readable_on,
    record_key_output,
)

redact = importlib.import_module("hadavin_sdk.guard.redact")

# A made-up token of 23 characters with a capital and digits (a wrapped header needs a token of at least 16).
TOKEN = "Qb7" + "WrappedToken" + "Abc01234"

# Every character that `\s` reads as a space and that is no line break of the rule (the same-line gaps), then the line breaks.
SAME_LINE_GAPS = (
    " ", "\t", " ", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x1f", "\x85", " ", " ", " ",
)  # fmt: skip
FOLDED_GAPS = ("\n ", "\n\t", "\r\n ", "\r\n\t", "\r ", "\n   ")
LONG_TOKEN_BREAKS = ("\n", "\r\n", "\r")
HEADERS = ("Authorization: {s}{g}{t}", "authorization={s}{g}{t}", '"Authorization": "{s}{g}{t}"')


# ---- Issue 1: a wrapped header, and every separator `\s` read on main -----------------------------------------------------


@pytest.mark.parametrize("scheme", ["Basic", "Token", "ApiKey"])
def test_b9_1_a_scheme_word_and_its_token_are_masked_across_every_gap_that_main_read(scheme):
    """Regression of batch 8 against main: `Authorization: Basic<LF><token>` (and Token, ApiKey) was readable. Every same-line
    space, a line fold and a line break in front of a long token are a gap again, in all three header spellings."""
    left = []
    for header in HEADERS:
        for gap in SAME_LINE_GAPS + FOLDED_GAPS + LONG_TOKEN_BREAKS:
            text = header.format(s=scheme, g=gap, t=TOKEN)
            left += [f"{text!r}: {x}" for x in readable_on(text, TOKEN)]
    assert not left, (
        f"a wrapped or oddly spaced {scheme} header leaves its token readable: {left[:6]} ({len(left)})"
    )


def test_b9_1_the_basic_rule_alone_masks_a_bare_wrapped_value_as_main_did():
    """The Basic rule has no `Authorization` in front of it (main: `\\bbasic\\s+`): `Basic<LF><token>` is masked on every path."""
    for gap in SAME_LINE_GAPS + FOLDED_GAPS + LONG_TOKEN_BREAKS:
        text = f"curl -H Basic{gap}{TOKEN} end"
        assert not readable_on(text, TOKEN), f"{text!r}"


def test_b9_1_a_prose_line_after_a_scheme_word_stays_readable_when_its_first_word_is_short():
    """Controls (they pass on the old code too): the line after a scheme word stays readable when its first word has fewer than 8
    characters (main read `\\s+` and a token of 8 or more; round 10 Issue 1 restored that reach, so a first word of 8 or more
    characters is masked again: pinned in `tests/test_q8b_batch10.py`)."""
    for scheme in ("Basic", "Token", "ApiKey", "Digest"):
        for line in (
            "short",
            "an ordinary sentence follows here",
            "the line of prose",
        ):
            text = f"Authorization: {scheme}\n{line}"
            assert clean(text) == text, f"a line after the scheme word was masked: {clean(text)!r}"


@pytest.mark.parametrize("scheme", ["Basic", "Token", "ApiKey"])
def test_b9_1_a_line_fold_continues_the_header_whatever_the_token_looks_like(scheme):
    """A line break followed by a space or a tab is a fold (RFC 9112 section 5.2): the next word is still the header value, even a
    short or lower-case one (the long-token branch alone would leave it readable)."""
    for fold in FOLDED_GAPS:
        text = f"Authorization: {scheme}{fold}abcdefgh1 end"
        assert not readable_on(text, "abcdefgh1"), (
            f"a short token after a fold leaves it readable: {text!r}"
        )


def test_b9_1_a_digest_header_goes_on_after_a_line_fold_and_a_no_break_space_but_not_after_a_plain_line_break():
    secret = "Qd9" + "DigestValue"
    for gap in (" ", "\t", " ", "\x0b", "\x0c", "\x85", " ", "\n ", "\r\n\t"):
        out = clean(f"Authorization: Digest{gap}username=u, response={secret}")
        assert secret not in out, f"a Digest value after {gap!r} is readable: {out!r}"
    prose = "a plain line of prose here"
    assert clean(f"Authorization: Digest\n{prose}") == f"Authorization: Digest\n{prose}", (
        "a plain line break after Digest does not end the header (a header ends at a line break unless it is folded)"
    )


def test_b9_1_every_shape_that_main_masked_is_masked_now_a_differential_against_the_main_rules():
    """The two rules of main written out as they were (`\\s+` between the scheme word and the token); any generated text that
    they mask, with a token of 16 or more characters holding a capital or a digit, is masked by the redactor too. (Batch 10 widens
    this to every length from 8 and every shape: `test_b10_1_the_differential_against_main...`.)"""
    main_basic = re.compile(r"(?i)\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})")
    main_auth = re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']?(?:[a-z]+\s+)?([^\s\"']{8,})")
    tokens = (
        "Qb7WrappedTokenAbc01",
        "abcXYZ0129+/_abcXYZ",
        "aaaaaaaaaaaaaaaaA",
        "0129012901290129x",
        "Zz9" * 8,
    )
    gaps = SAME_LINE_GAPS + FOLDED_GAPS + LONG_TOKEN_BREAKS + ("  ", " \t ", "\n\n", "\r\n\r\n")
    checked = 0
    heads = ("Authorization: ", "authorization=", 'x "Authorization": "', "")
    schemes = ("Basic", "Token", "ApiKey", "Negotiate", "Digest", "Foo")
    for scheme, gap, token, head in itertools.product(schemes, gaps, tokens, heads):
        text = f"{head}{scheme}{gap}{token} tail"
        main_takes = (
            main_basic.search(text)
            if scheme == "Basic"
            else (main_auth.search(text) if head else None)
        )
        if main_takes is None or token not in main_takes.group(1):
            continue
        checked += 1
        assert not readable_on(text, token), f"main masked {text!r}, the redactor does not"
    assert checked > 100, f"the differential compared only {checked} generated texts"


def test_b9_1_a_long_run_of_gaps_and_wrapped_headers_is_read_in_linear_time():
    size = 100_000
    for text in (
        "Authorization: Basic" + " \t" * (size // 2) + "x",
        "Authorization: Token" + "\n" * size + "x",
        "Basic\n" * (size // 6),
        "Authorization: Token\n " * (size // 22),
        "Authorization: ApiKey" + " " * size + "\n" + "a" * size,
    ):
        t0 = time.process_time()
        clean(text)
        assert time.process_time() - t0 < 20, "a gap after a scheme word takes far too long"


# ---- Issue 2 and 8: pins for the claims that had none --------------------------------------------------------------------


@pytest.mark.parametrize(
    "flag",
    [
        "pass2",
        "password",
        "newpass",
        "oldpass",
        "postgresauth",
        "dbpass",
        "confirmpass",
        "rootauth",
        "oauth",
    ],
)
def test_b9_2_the_second_word_after_a_credential_flag_is_shown_for_every_flag_named_in_limits(flag):
    """The stated cost, pinned (nine flags, `--pass2` included; batch 8 named it and pinned only seven): the first word is
    masked, the second is shown, on a card (the other paths read the same rule)."""
    assert clean(f"run --{flag} {V} {W} now") == f"run --{flag} <SECRET_1> {W} now", (
        f"the second word after the flag --{flag} is not shown"
    )
    assert V not in "".join(five_paths(f"run --{flag} {V} {W} now").values())


def test_b9_2_authorization_with_an_equals_sign_masks_the_first_word_and_shows_the_second():
    out = clean(f"cfg authorization={V} {W} end")
    assert out == f"cfg authorization=<SECRET_1> {W} end", (
        f"the second word after authorization= is not shown: {out!r}"
    )
    assert "authorization=a b" in R.LIMITS and "pass2" in R.LIMITS, (
        "LIMITS does not name the pinned cases"
    )


def test_b9_8_the_text_of_a_flag_that_batch_8_called_an_exception_is_pinned_both_ways():
    """`--apiInputTokens <v>`: masked as a flag (the safe direction), read as a count by the record walk (stated)."""
    assert clean(f"run --apiInputTokens {V} now") == "run --apiInputTokens <SECRET_1> now"
    assert not R.sensitive("apiInputTokens")


def test_b9_8_a_cookie_jar_name_in_capitals_is_masked_and_in_lower_case_it_is_not():
    """`COOKIEJAR=v` and `COOKIESTORE=v` are masked as text and, since batch 10, as record keys too (a capital after the word
    `cookie` starts a new word); the lower case words are one word and stay readable."""
    for key in ("cookiejar", "cookiestore"):
        assert clean(f"cfg {key}={ORDINARY_VALUE} end") == f"cfg {key}={ORDINARY_VALUE} end"
        assert not R.sensitive(key)
    for key in ("COOKIEJAR", "COOKIESTORE"):
        assert ORDINARY_VALUE not in clean(f"cfg {key}={ORDINARY_VALUE} end"), key
        assert R.sensitive(key) is True, "the record walk shows COOKIEJAR that the text rule masks"


def test_b9_8_a_quoted_text_after_an_authorization_flag_is_read_to_512_characters():
    short = "Ab1" + "x" * 400
    out = clean(f'ran --authorization Bearer "{short}" now')
    assert short not in out and out.endswith(" now"), out
    assert redact._QUOTED_TEXT.count("512") == 2
    assert "512" in R.LIMITS, (
        "LIMITS does not name the 512 character cap of a quoted text after a scheme word"
    )


def test_b9_8_the_changelog_numbers_the_mutants_of_batch_8_from_116():
    assert "M115 and later" not in CHANGELOG and "M116" in CHANGELOG


# ---- Issue 4: a key tail and its look-ahead are one bound ----------------------------------------------------------------


@pytest.mark.parametrize("word", ["pass", "auth", "session", "bearer", "password", "token"])
@pytest.mark.parametrize("n", [1, 9, 20, 21, 40, 200])
def test_b9_4_any_run_of_digits_after_a_key_word_still_masks_the_value_as_text_and_as_a_record_key(
    word, n
):
    key = word + "7" * n
    assert R.sensitive(key), key
    for tmpl in (
        "cfg {k}={v} end",
        "cfg {k}: {v} end",
        'cfg {k}="{v} {v}" end',
        "ran --{k} {v} --verbose",
    ):
        text = tmpl.format(k=key, v=V)
        assert not readable_on(text, V), f"{key[:12]}...({n} digits) {tmpl}: a value is readable"


def test_b9_4_a_key_tail_is_one_name_used_by_all_six_rules():
    assert redact.KEY_TAIL == r"[0-9]*+[\w.\-]{0,20}"
    src = pathlib.Path(redact.__file__).read_text(encoding="utf-8")
    assert src.count("[\\w.\\-]{0,20}") == 1, (
        "a key rule still carries its own copy of the tail bound"
    )


@pytest.mark.parametrize(
    "key",
    [
        "cookie2",
        "Cookie2",
        "cookie_name2",
        "cookie21",
        "set-cookie3",
        "cookies2",
        "Cookie_Name2",
        "cookie0",
    ],
)
def test_b9_4_a_cookie_word_with_digits_is_a_key_as_text_and_as_a_record_key(key):
    assert R.sensitive(key), key
    for tmpl in ("cfg {k}={v} end", "cfg {k}: {v}", 'cfg {k}="{v}" end', '{{"{k}": "{v}"}} tail'):
        assert not readable_on(tmpl.format(k=key, v=V), V), f"{key} {tmpl}"
    assert V not in record_key_output(key, V)


def test_b9_4_a_word_that_only_holds_cookie_and_digits_inside_is_no_key():
    for key in ("mycookie2", "cookiejar2", "cookie2jar"):
        assert not R.sensitive(key), key
        text = f"cfg {key}={ORDINARY_VALUE} end"
        assert clean(text) == text, f"{key} was masked as text: {clean(text)!r}"


def test_b9_4_a_very_long_run_of_digits_after_a_key_word_is_read_in_linear_time():
    # batch 14: a ratio, not a limit of 20 seconds (a quadratic read of 50,000 digits fits in 20 seconds, so the old limit let it pass).
    # 4 times the digits: linear is 4, quadratic 16; measured on the head 4.0 to 4.3 (best of three each), bound 7; repeated up to three times, it fails only when all three are over the bound.
    for word in ("pass", "cookie", "password"):

        def best(digits: int, word: str = word) -> float:
            text = (word + "1" * digits + " ") * 2 + ("pass" + "1" * digits + "x ") * 2
            times = []
            for _ in range(3):
                t0 = time.process_time()
                clean(text)
                times.append(time.process_time() - t0)
            return min(times)

        best(1_000)
        for _attempt in range(3):  # a real slowdown fails all three; a busy machine rarely does
            small, large = best(5_000), best(20_000)
            if large < max(small, 0.02) * 7:
                break
        assert large < max(small, 0.02) * 7, (
            f"a very long run of digits after the key word {word} takes far too long: {small:.3f}s and {large:.3f}s for 4 times the digits"
        )


# ---- Issue 5: copies tied to one list, and rules that were not timed -----------------------------------------------------


def test_b9_5_the_authorization_flag_reads_the_same_bound_as_the_other_flags(monkeypatch):
    assert f"{{0,{redact.FLAG_PREFIX_WORDS}}}" in redact._AUTH_FLAG, (
        "the authorization flag has its own bound of prefix words"
    )
    for n in range(1, redact.FLAG_PREFIX_WORDS + 1):
        key = "-".join(["w"] * n) + "-authorization"
        assert clean(f"run --{key} Token {V} now") == f"run --{key} <SECRET_1> now", key
    seven = "-".join(["w"] * (redact.FLAG_PREFIX_WORDS + 1)) + "-authorization"
    assert V in clean(f"run --{seven} Token {V} now"), (
        "the authorization flag reads more words than the other flags"
    )


@pytest.mark.parametrize("flag", ["password", "token", "api-key"])
def test_b9_5_a_flag_other_than_the_authorization_flags_keeps_the_one_word_rule(flag):
    """Control (it passes on the old code too; the mutant M177 kills it): only `--authorization` and `--bearer` take a scheme word
    and its token; the first word after `--password` is the value and the second word is shown (stated in LIMITS)."""
    out = clean(f"run --{flag} abcdefgh {W} now")
    assert out == f"run --{flag} <SECRET_1> {W} now", (
        f"a flag other than the authorization flags takes a scheme word: {out!r}"
    )


@pytest.mark.parametrize("encoded", ["%0b", "%0B", "%0c", "%1f", "%c2%85"])
def test_b9_1_a_white_space_control_inside_an_encoded_header_does_not_join_the_scheme_word_to_its_token(
    encoded,
):
    """The card turns a white-space control into a space before it reads a decoded view; a control that was only deleted joined
    `Basic` to its token and left the token readable (the sibling of Issue 1 on the card path)."""
    text = f"curl -H Basic{encoded}{TOKEN} end"
    assert not readable_on(text, TOKEN), (
        f"a control inside an encoded header leaves the token readable: {text!r}"
    )


def test_b9_5_the_cookie_flag_names_of_curl_and_of_the_generic_flag_rule_are_one_table():
    names = (
        "cookie",
        "set-cookie",
        "set_cookie",
        "session_cookie",
        "session-cookie",
        "sessioncookie",
        "Set_Cookie",
    )
    left = []
    for name in names:
        for tmpl in (
            "ran --{k} {v} --verbose",
            "ran --{k}={v} --verbose",
            "ran --{k} sid={v} --verbose",
        ):
            left += [f"{name} {tmpl}: {x}" for x in readable_on(tmpl.format(k=name, v=V), V)]
    assert not left, f"a cookie flag name of the table leaves its value readable: {left[:6]}"
    for pattern in (p for _, p in redact.PATTERNS if "--(?:" in p.pattern and "-b)" in p.pattern):
        for exact in redact.FLAG_EXACT_WORDS:
            assert exact in pattern.pattern, (
                "the curl cookie rule keeps its own copy of the cookie flag names"
            )


def test_b9_5_the_rules_that_batch_8_added_are_timed_on_hostile_text():
    size = 200_000
    hostile = {
        "authorization flags": "--a-authorization " * (size // 18),
        "unclosed quote digest": "Authorization: Digest " + '"' * (size // 2),
        "digest words": "--authorization Digest " + 'a="b" ' * (size // 7),
        "cookie run": "cookie" + "_a" * (size // 2),
        "cookie digits": "cookie" + "1" * size,
        "many cookie starts": "set-cookie2 " * (size // 12),
        "scheme and tab runs": "Basic" + "\t" * size,
        "scheme and breaks": "Authorization: Token" + "\r\n" * (size // 2),
        "bypass pairs": "bypass_" * (size // 7),
        "protection": "protection-" * (size // 11),
    }
    for name, text in hostile.items():
        t0 = time.process_time()
        redact.redact(text)
        took = time.process_time() - t0
        assert took < 15, f"{name}: redact() takes {took:.1f} s on 200 kB"
    for pattern in (
        redact._AUTH_FLAG,
        redact._DIGEST_WORD,
        redact._COOKIE_KEY,
        redact._COOKIE_ASSIGN_KEY,
    ):
        r = re.compile(pattern)
        for name, text in hostile.items():
            t0 = time.process_time()
            sum(1 for _ in r.finditer(text))
            took = time.process_time() - t0
            assert took < 10, f"{name}: {pattern[:40]!r} takes {took:.1f} s"


# ---- Issue 6: the cells of the evidence list ------------------------------------------------------------------------------

BYPASS_CREDENTIALS = (
    "bypass_key", "bypass_code", "bypass-code", "bypass_value", "bypass_phrase", "bypasskey", "bypasscode", "bypass_token",
    "bypass_secret", "x-vercel-protection-bypass", "protection-bypass", "protectionBypass", "X-Vercel-Protection-Bypass",
)  # fmt: skip


@pytest.mark.parametrize("key", BYPASS_CREDENTIALS)
def test_b9_6_a_bypass_name_that_holds_a_secret_is_masked_in_every_form_on_every_path(key):
    assert R.sensitive(key), key
    for tmpl in (
        "cfg {k}={v} end",
        "cfg {k}: {v} end",
        'cfg {k}="{v} {v}" end',
        "ran --{k} {v} --verbose",
        "ran --{k}={v} x",
    ):
        assert not readable_on(tmpl.format(k=key, v=V), V), f"{key} {tmpl}"
    assert V not in record_key_output(key, V)


def test_b9_6_a_bare_bypass_and_the_other_ordinary_words_stay_readable_by_choice_the_owner_list():
    """Not masked on purpose (question `q-q8b-bare-bypass` for the bare `bypass`; a bare ordinary word holds nothing):
    `bypass=<v>` (a switch such as `bypass=true`), `compass`, `possession`. Batch 10 masks the second-word names this test
    listed in batch 9 (`compass_code`, `possession_id`, `obsession_id`: see `tests/test_q8b_batch10.py`). Both sides pinned."""
    for key in ("bypass", "compass", "possession", "compass_id", "compass_direction"):
        assert not R.sensitive(key), key
        for tmpl in ("cfg {k}={v} end", "cfg {k}: {v} end", "ran --{k} {v} --verbose"):
            text = tmpl.format(k=key, v=ORDINARY_VALUE)
            assert clean(text) == text, f"{key}: {clean(text)!r}"
    for key in (
        "session_id",
        "xcompass_code",
        "xpossession_id",
        "bypass_key",
        "compass_code",
        "possession_id",
    ):
        assert R.sensitive(key), key
        assert not readable_on(f"cfg {key}={V} end", V), key


def test_b9_6_the_second_words_of_a_bypass_name_are_the_pass_pairs_read_from_one_list():
    assert redact.ordinary_second_words("bypass") == ("phrase", "code", "key", "value")
    for second in redact.ordinary_second_words("bypass"):
        assert R.sensitive(f"bypass_{second}") and R.sensitive(f"bypass{second}"), (
            f"a bypass name with the second word {second} is readable as a record key"
        )
        assert R.sensitive(f"compass_{second}") and R.sensitive(f"compass{second}"), (
            f"a compass name with the second word {second} is readable as a record key"
        )


WGET_FLAGS = (
    "no-cookies", "keep-session-cookies", "junk-session-cookies", "load-cookies", "save-cookies", "cookies", "no-keep-cookies",
)  # fmt: skip


def test_b9_6_a_wget_cookie_switch_or_file_flag_is_not_known_to_take_a_credential_and_stays_readable():
    """The honest wording of the pin (the CHANGELOG of batch 8 said: switches or file names): these flags are not known to take a
    credential (`--no-cookies` and the two `--...-session-cookies` take nothing, `--load-cookies` and `--save-cookies` take a file
    name). The word after them is shown. If a tool is found where one takes a value, this test changes with the rule."""
    for flag in WGET_FLAGS:
        for tail in ("cookiefile", ORDINARY_VALUE):
            text = f"wget --{flag} {tail} --verbose"
            assert clean(text) == text, f"{flag}: {clean(text)!r}"
    assert "<SECRET" not in clean("wget --no-cookies http://example.com/path")
    assert (
        "not known to take a credential" in CHANGELOG
        and "not known to take a credential" in R.LIMITS
    )


def test_b9_6_a_line_break_ends_a_digest_header_so_the_prose_line_is_readable_by_the_rule_of_a_header():
    """`Authorization: Digest<LF>prose` stays readable: a header value ends at a line break unless the next line starts with a
    space or a tab (RFC 9112, obsolete line fold); main read the prose too only when it held 8 characters in one word."""
    prose = "the quick brown fox jumps"
    assert clean(f"Authorization: Digest\n{prose}") == f"Authorization: Digest\n{prose}"
    assert prose not in clean(f"Authorization: Digest\n {prose}")


def test_b9_6_the_changelog_of_batch_9_names_every_cell_that_changed_in_both_directions():
    block = CHANGELOG.split("batch 9", 1)[1].split("round 8 (batch 8)", 1)[0]
    for word in (
        "bypass_key",
        "x-vercel-protection-bypass",
        "possession_id",
        "compass_code",
        "Basic",
        "cookie2",
        "21",
    ):
        assert word in block, f"the batch 9 entry does not name {word}"
    for number in ("3.44", "3.05", "3.26"):
        assert number in block, f"the batch 9 entry does not give the cost ratio {number}"

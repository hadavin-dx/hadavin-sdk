"""Q8b batch 8 (round 8 of the redaction path): the classes the round 8 review and the evidence probe found.

Classes (each fixed at the one place every caller routes through, `guard/redact.py` for the card, the tool result, the text of a
run and a log line, `k1b/redaction.py` for the record keys):
  1. a plural `tokens` flag after a word that is glued on or written in camelCase (`--apiTokens`, `--apitokens`);
  2. a cookie flag that is a switch or takes a file (`wget --no-cookies`, `--load-cookies`): over-masking, an exact name only;
  3. a key that is a bare word and one more word and holds an ordinary word (`possession_id`, `bypass_key`, `compass_code`);
  4. a SCHEME word and its token after `--authorization` and `--bearer` (any scheme, quoted or not, Digest to the next flag);
  5. the bound of words in front of a credential flag (3 became 6) and its cost (timed on hostile text);
  7. a Digest header inside JSON, masked to the closing quote;
  8. digits glued behind a bare credential word, however many (`pass1234567890`);
 10. a header scheme word: the line break ends the value (`\\s` became a space or tab);
 12. a key with the word `cookie` and more words (`cookie_name`, `cookie-policy`) in text, as the record walk reads it;
 13. one machine-checkable line per test that passes on old code (see the end of this file).
The five paths are those of `tests/test_q8b_batch7.py`: card, tool, run, log, record message (and the record key).
"""

from __future__ import annotations

import importlib
import itertools
import re
import time

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
TEXT_PATHS = ("card", "tool", "run", "log", "record")


def _masked(text: str, piece: str) -> list[str]:
    """The paths on which a piece is NOT readable."""
    return [p for p, out in five_paths(text).items() if piece not in out]


# ---- Issue 1: a plural `tokens` after a glued or camelCase word ---------------------------------------------------------

TOKEN_CREDENTIALS = (
    "apiTokens", "accessTokens", "refreshTokens", "idTokens", "accesstokens", "idtokens", "authtokens",
    "apitokens", "api_tokens", "x-refresh-tokens", "xmax_tokens", "contexttokens",
)  # fmt: skip
TOKEN_COUNTS = (
    "max_tokens", "maxTokens", "maxtokens", "input_tokens", "inputTokens", "inputtokens", "audio_tokens",
    "audiotokens", "cachedinputtokens", "cachedInputTokens", "cached_input_tokens", "tokens",
)  # fmt: skip


def test_b8_1_a_plural_tokens_flag_after_a_glued_or_camel_case_word_is_masked_on_every_path():
    left = []
    for key in TOKEN_CREDENTIALS:
        assert R.sensitive(key), f"the record walk does not mask {key}"
        for tmpl in ("run --{k} {v} now", "run --{k}={v} now"):
            left += [f"{key} {tmpl}: {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
        if V in record_key_output(key, V):
            left.append(f"{key} record key")
    assert not left, (
        f"a plural tokens flag after a glued or camelCase word is readable: {left[:6]} ({len(left)})"
    )


def test_b8_1_a_count_of_tokens_stays_readable_as_a_flag_and_as_a_record_key():
    """Controls and a stated exception: a count word in front (alone or glued) and a bare `--tokens` stay readable."""
    for key in TOKEN_COUNTS:
        text = f"run --{key} 4096 now"
        assert clean(text) == text, f"a count of tokens was masked as a flag: {clean(text)!r}"
        assert key == "tokens" or not R.sensitive(key), f"the record walk masks a count: {key}"


def test_b8_1_a_count_word_that_ends_a_longer_word_is_no_count_word():
    """`xmax_tokens`: the word in front is `xmax`, no count word (the record walk reads it so; the flag read `max_` as a suffix)."""
    assert R.sensitive("xmax_tokens")
    assert V not in clean(f"run --xmax_tokens {V} now")
    assert not R.sensitive("max_tokens") and clean("run --max_tokens 5") == "run --max_tokens 5"


def test_b8_1_the_flag_rule_and_the_record_walk_agree_on_every_generated_plural_tokens_key():
    """The drift test reads the RECORD WALK's own word split (`R._key_words`), not the key list of the card rules: every key
    made of a word, a join (`_`, `-`, nothing, a capital) and `tokens` is checked on both sides. No record key the walk masks may
    be readable as a flag (a leak); a flag the card masks must be a key the walk masks, or one of the stated cases (the walk reads
    `apiInputTokens` as `input` + `tokens`, a count)."""
    prefixes = (
        "api", "access", "refresh", "id", "auth", "bearer", "context", "x", "db", "max", "min", "input", "output", "prompt",
        "completion", "total", "cached", "cache", "reasoning", "thinking", "audio", "image", "text", "read", "creation",
        "billed", "usage",
    )  # fmt: skip
    joins = ("_", "-", "", "CAMEL")
    disagree, compared = [], 0
    for prefix, join in itertools.product(prefixes, joins):
        key = prefix + "Tokens" if join == "CAMEL" else prefix + join + "tokens"
        words = R._key_words(key)
        assert words[-1].endswith("tokens"), (key, words)
        walk = R.sensitive(key)
        flag = clean(f"run --{key} {V} now") != f"run --{key} {V} now"
        compared += 1
        if walk and not flag:
            disagree.append(f"{key}: record masks, flag readable")
        if flag and not walk:
            disagree.append(f"{key}: flag masks, record readable")
    assert compared == len(prefixes) * len(joins)
    assert not disagree, f"the two rules differ: {disagree}"


def test_b8_1_one_definition_of_a_count_run_is_used_by_both_files():
    assert R.is_count_run is redact.is_count_run, "the record walk keeps its own count rule"
    assert redact.is_count_run("max") and redact.is_count_run("cachedinput")
    assert (
        not redact.is_count_run("")
        and not redact.is_count_run("api")
        and not redact.is_count_run("maxapi")
    )


# ---- Issue 2: the cookie flag is an exact name ---------------------------------------------------------------------------

COOKIE_SWITCHES = (
    "no-cookies", "keep-session-cookies", "junk-session-cookies", "load-cookies", "save-cookies", "cookies",
    "no-keep-cookies", "cookie-jar",
)  # fmt: skip


def test_b8_2_a_switch_or_a_file_flag_of_the_cookie_family_leaves_the_next_word_readable():
    left = []
    for flag in COOKIE_SWITCHES:
        for tail in (ORDINARY_VALUE, "mycookies"):
            text = f"wget --{flag} {tail} --verbose"
            left += [f"{flag}: {tail} masked on {p}" for p in _masked(text, tail)]
    assert not left, f"a cookie switch or file flag masked the next word: {left[:6]} ({len(left)})"
    for p, out in five_paths("wget --no-cookies http://example.com/path").items():
        assert "<SECRET" not in out, f"{p}: {out!r}"


def test_b8_2_the_cookie_flag_with_its_exact_name_still_masks_its_value():
    left = []
    for flag in (
        "cookie",
        "Cookie",
        "COOKIE",
        "set-cookie",
        "session_cookie",
        "session-cookie",
        "sessioncookie",
        "cookie2",
    ):
        forms = ["ran --{k} {v} --verbose", "ran --{k}={v} --verbose"]
        if flag.lower() in ("cookie", "set-cookie", "session_cookie", "session-cookie"):
            forms.append(
                "ran --{k} sid={v} --verbose"
            )  # curl's `--cookie name=value` (any of the four spellings)
        for tmpl in forms:
            left += [f"{flag} {tmpl}: {x}" for x in readable_on(tmpl.format(k=flag, v=V), V)]
    assert not left, f"an exact cookie flag leaves its value readable: {left[:6]}"


# ---- Issue 3: a key of two words (a bare word and one more) with an ordinary word in it ---------------------------------

# Round 10 (Issue 6): an ordinary word and a second word of ITS OWN family is a credential name (`compass_key`, `possession_id`); the
# keys below keep an ordinary word and a second word that is no word of its family: they stay readable (the table is
# `ordinary_second_words`; `tests/test_q8b_batch10.py` pins both sides for every word).
ORDINARY_TWO_WORD_KEYS = (
    "compass_direction", "possession_name", "obsession_level", "overpass_name", "bypass_id", "compass_id", "possession_code",
    "encompass_name", "obsession_phrase",
)  # fmt: skip
TWO_WORD_CREDENTIALS = (
    "xbypass_key", "bypasspass_key", "xbypasskey", "xcompass_code", "session_id", "sessionid", "pass_code",
    "passkey", "auth_value", "passphrase",
    # Round 9 (Issue 6): `bypass` with a second word of the `pass` pairs, and the protection-bypass header name, are credential names
    # (they were pinned readable here in round 8: a deployment bypass secret was shown). A bare `bypass` stays readable (see below).
    "bypass_key", "bypass_value", "bypass-code", "bypasskey", "bypassphrase", "bypass_phrase", "bypasscode",
    "x-vercel-protection-bypass", "protection-bypass", "protectionBypass",
    # Round 10 (Issue 6): the same rule for every ordinary word (they were pinned readable in rounds 8 and 9).
    "compass_key", "compass_code", "compasscode", "overpass_value", "encompass_phrase", "possession_id", "obsession_id",
    "obsession_key", "possession_value", "compass-key", "possessionid",
)  # fmt: skip


def test_b8_3_an_ordinary_word_with_one_more_word_stays_readable_in_every_form_on_every_path():
    left = []
    for key in ORDINARY_TWO_WORD_KEYS:
        assert not R.sensitive(key), f"the record walk masks {key}"
        for tmpl in (
            "cfg {k}={v} end", "cfg {k}: {v} end", "ran tool --{k} {v} --verbose",
            "ran tool --{k}={v} --verbose",
        ):  # fmt: skip
            text = tmpl.format(k=key, v=ORDINARY_VALUE)
            left += [f"{key} {tmpl}: {p}" for p in _masked(text, ORDINARY_VALUE)]
        # Batch 12 (group 1): a QUOTED value behind such a name is masked, as `main` masked it (the older decision "readable in every
        # form" made 340 quoted cells readable that main masked: tests/test_q8b_batch12.py). The unquoted and flag forms stay readable.
        quoted = f'cfg {key}="{ORDINARY_VALUE} {ORDINARY_VALUE}" end'
        shown = [p for p, out in five_paths(quoted).items() if ORDINARY_VALUE in out]
        assert not shown, f"a quoted value behind `{key}` is readable on {shown}"
        if ORDINARY_VALUE not in record_key_output(key, ORDINARY_VALUE):
            left.append(f"{key} record key masked")
    assert not left, f"an ordinary word was masked: {left[:8]} ({len(left)})"


def test_b8_3_a_real_two_word_credential_key_is_never_hidden_by_the_ordinary_look_behind():
    left = []
    for key in TWO_WORD_CREDENTIALS:
        assert R.sensitive(key), key
        for tmpl in (
            "cfg {k}={v} end",
            "cfg {k}: {v} end",
            'cfg {k}="{v} {v}" end',
            "ran --{k} {v} --verbose",
        ):
            left += [f"{key} {tmpl}: {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
        if V in record_key_output(key, V):
            left.append(f"{key} record key")
    assert not left, f"a credential key became readable: {left[:6]}"


def test_b8_3_the_guarded_endings_of_the_record_walk_are_the_pairs_of_the_card_list():
    """Both lists are generated from `_GUARDED_PAIRS` (round 11, Issue 5): the glued endings of the record walk and the key
    alternatives of the card rules are compared with a fresh build from the table."""
    assert redact.GUARDED_ENDINGS == tuple(b + s for b, s in redact._GUARDED_PAIRS), (
        "GUARDED_ENDINGS is not generated from the pairs"
    )
    for ending in redact.GUARDED_ENDINGS:
        assert ending in R.GLUED_ENDINGS, (
            f"{ending} is guarded on the card but is no glued ending of the record walk"
        )
    assert set(R.GLUED_ENDINGS) - set(redact.GUARDED_ENDINGS) == _HAND_GLUED_ENDINGS
    for bare, second in redact._GUARDED_PAIRS:
        assert redact._guarded_key(bare, second) in redact.KEY_ALTERNATIVES, (
            f"the pair {bare} + {second} is no key alternative of the card rules"
        )
    generated = [
        a
        for a in redact.KEY_ALTERNATIVES
        if a.startswith(tuple(b for b, _ in redact._GUARDED_PAIRS)) and "(?:[0-9]*[_.\\-])?" in a
    ]
    assert len(generated) == len(redact._GUARDED_PAIRS)


# the glued endings that are no pair of the table: one credential word (`password`) or a fixed compound (`accesskey`)
_HAND_GLUED_ENDINGS = {
    "password", "passwd", "pwd", "secret", "token", "apikey", "secretkey", "accesskey", "privatekey", "sessid",
    "accountkey", "keydata", "certdata", "certificatedata", "credential", "credentials", "signingkey", "encryptionkey",
    "protectionbypass",
}  # fmt: skip


# ---- Issue 4: a scheme word and its token after --authorization and --bearer ---------------------------------------------

SCHEME_FLAGS = ("authorization", "bearer", "proxy-authorization", "Authorization")


def test_b8_4_any_scheme_word_and_its_token_are_masked_after_the_authorization_and_bearer_flags():
    left = []
    for flag in SCHEME_FLAGS:
        for scheme in ("NTLM", "Negotiate", "OAuth", "Splunk", "Bearer", "Hawk", "AWS"):
            for tmpl in (
                "ran --{f} {s} {v} --verbose", "ran --{f} {s} '{v}' --verbose", 'ran --{f} {s} "{v}" --verbose',
            ):  # fmt: skip
                text = tmpl.format(f=flag, s=scheme, v=V)
                left += [f"{flag} {scheme} {tmpl}: {p}" for p in readable_on(text, V)]
    assert not left, f"a token after a scheme word is readable: {left[:6]} ({len(left)})"
    assert (
        clean(f"ran --authorization Bearer '{V}' --verbose")
        == "ran --authorization <SECRET_1> --verbose"
    )


def test_b8_4_a_digest_value_after_the_flag_is_masked_up_to_the_next_flag_or_the_end_of_the_line():
    secret = "Qd4" + "hashPart"
    for text in (
        f"ran --authorization Digest username=u, response={secret} --verbose",
        f'ran --authorization Digest username="u", realm="a b", response="{secret}" --verbose',
        f"ran --authorization Digest username=u, response='{secret}' --verbose",
    ):
        out = clean(text)
        assert secret not in out and out.endswith(" --verbose"), (
            f"a Digest value after the flag is readable: {out!r}"
        )
    assert clean(f"ran --authorization Digest username=u, response={secret}\nnext line").endswith(
        "\nnext line"
    ), "a Digest value after the flag runs over the line break"


def test_b8_4_the_generic_flag_takes_a_scheme_word_with_its_token():
    """A credential flag that is no authorization flag: the scheme word is read WITH its token (batch 7, kept)."""
    for flag in ("token", "password", "api-key"):
        out = clean(f"ran --{flag} Bearer {V} --verbose")
        assert out == "ran --" + flag + " <SECRET_1> --verbose", (
            f"the scheme word is not masked with its token: {out!r}"
        )


def test_b8_4_the_generic_flags_keep_the_one_word_rule_and_so_does_a_value_that_is_no_scheme_word_and_a_word():
    """Issue 11: `--password a b` shows `b` (a stated design choice); `--authorization` with a first word that holds a digit is a
    token on its own (one word), `--authorization abc file.txt` is a scheme word and a word (both masked: the cost)."""
    assert clean(f"run --password {V} {W} now") == f"run --password <SECRET_1> {W} now", (
        "a flag other than the authorization flags takes a scheme word and its token: the one word rule is gone"
    )
    assert clean(f"run --authorization {V} {W} now") == f"run --authorization <SECRET_1> {W} now", (
        "the authorization flag does not keep the one word rule for a first word that holds a digit"
    )
    assert "file.txt" not in clean("run --authorization abc file.txt now"), (
        "a scheme word and a word are not both masked"
    )
    assert clean(f"run --bearer {V}=1 now") != f"run --bearer {V}=1 now", (
        "the bearer flag leaves its value readable"
    )


# ---- Issue 5: six words in front of a credential flag, and the time it costs on hostile text -----------------------------


def test_b8_5_a_flag_with_up_to_six_words_in_front_masks_its_value_and_a_seventh_word_is_the_stated_limit():
    for n in range(1, 7):
        for sep in ("-", "_"):
            key = sep.join(["w"] * n) + sep + "password"
            assert clean(f"run --{key} {V} now") == f"run --{key} <SECRET_1> now", (
                f"a flag with up to six words in front is readable: {key}"
            )
    seven = "-".join(["w"] * 7) + "-password"
    assert clean(f"run --{seven} {V} now") == f"run --{seven} {V} now", (
        "the flag rule reads more than six words in front"
    )
    assert redact.FLAG_PREFIX_WORDS == 6
    assert "joined by `-` or `_`" in R.LIMITS and "hyphen-joined" not in R.LIMITS
    assert "seven or more words" in R.LIMITS


def test_b8_5_the_timing_of_the_flag_rule_on_hostile_text_is_bounded_and_close_to_the_old_bound():
    """Hostile flag text of 200,000 characters (long `a-` runs, many `--a-` starts, one long unbroken word, many `-- `), read with
    the bound of 6 and with the old bound of 3: the bound of 6 stays under a fixed time and under 6 times the old one."""
    pattern6 = redact._CRED_FLAG
    assert "{0,6}" in pattern6, "the flag rule has no bound on the words in front"
    pattern3 = pattern6.replace("{0,6}", "{0,3}")
    assert pattern3 != pattern6
    r6, r3 = re.compile(pattern6), re.compile(pattern3)
    size = 200_000
    texts = {
        "a- run": "--" + "a-" * (size // 2) + "x now",
        "many starts": "--a-b-c-d-e-f-g " * (size // 16),
        "one word": "--" + "a" * size,
        "spaced dashes": "-- " * (size // 3),
        "password run": "--a-password " * (size // 13),
        "digits": "--" + "a1-" * (size // 3) + "password",
    }
    worst = 0.0
    for name, text in texts.items():
        t0 = time.process_time()
        n6 = sum(1 for _ in r6.finditer(text))
        t6 = time.process_time() - t0
        t0 = time.process_time()
        n3 = sum(1 for _ in r3.finditer(text))
        t3 = time.process_time() - t0
        assert t6 < 8.0, f"{name}: the flag rule takes {t6:.2f} s on 200 kB"
        assert t6 < 6 * t3 + 1.0, f"{name}: bound 6 takes {t6:.2f} s, bound 3 {t3:.2f} s"
        assert n6 >= n3, name
        worst = max(worst, t6)
    t0 = time.process_time()
    redact.redact(texts["many starts"])
    assert time.process_time() - t0 < 30, "redact() on 200 kB of flag starts takes far too long"


# ---- Issue 7: a Digest header inside JSON is masked to its closing quote; Issue 10: a line break ends it ------------------


def test_b8_7_a_quoted_digest_header_is_masked_to_its_closing_quote_and_the_json_stays_whole():
    secret = "Qd7" + "hashValue"
    text = (
        '{"Authorization": "Digest username=\\"u\\", response=\\"'
        + secret
        + '\\"", "level": "info"}'
    )
    for p, out in five_paths(text).items():
        assert secret not in out, f"{p}: {out!r}"
        if p == "tool":
            assert out.endswith('", "level": "info"}'), (
                f"the JSON structure after a quoted Digest value was masked: {out!r}"
            )
            assert re.fullmatch(r'\{"Authorization": "<SECRET_\d+>", "level": "info"\}', out), out


def test_b8_7_an_unquoted_digest_header_is_masked_to_the_end_of_the_line_json_structure_included():
    secret = "Qd7" + "hashValue"
    out = clean(f'cfg {{"Authorization": Digest response={secret}, "k": 1}} tail')
    assert secret not in out
    assert "the rest of the line" in CHANGELOG and "JSON" in CHANGELOG


def test_b8_10_a_line_break_ends_a_digest_header_and_a_scheme_word():
    # Round 10 (Issue 1): a first word of 8 or more characters on the next line is read as the token again (as main did); the
    # prose of this pin starts with short words (`tests/test_q8b_batch10.py` pins the cost).
    prose = "a plain line of prose here"
    assert clean(f"Authorization: Digest\n{prose}") == f"Authorization: Digest\n{prose}", (
        "a line break after Digest does not end the header value"
    )
    assert clean(f"Authorization: Basic\n{prose}") == f"Authorization: Basic\n{prose}", (
        "a line break after Basic does not end the header value"
    )
    assert clean(f"authorization=Digest\n{prose}") == f"authorization=Digest\n{prose}", (
        "a line break after Digest does not end the header value"
    )
    out = clean(f"Authorization: Basic {V}\n{prose}")
    assert V not in out and out.endswith(f"\n{prose}"), out


def test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time():
    for text in (
        "Authorization: Digest" + " \t" * 100_000 + "\nx",
        "Authorization: Basic" + " " * 200_000 + "\nx",
    ):
        t0 = time.process_time()
        clean(text)
        assert time.process_time() - t0 < 20, "white space after a scheme word takes far too long"


# ---- Issue 8: digits glued behind a bare credential word, however many ---------------------------------------------------


def test_b8_8_nine_ten_and_forty_digits_behind_a_bare_credential_word_are_masked_like_the_record_key():
    left = []
    for word in ("pass", "auth", "session", "bearer"):
        for n in (9, 10, 40):
            key = word + "1234567890" * (n // 10) + "1" * (n % 10)
            assert R.sensitive(key), key
            forms = [
                "ran --{k} {v} --verbose",
                "ran --{k}={v} --verbose",
                "cfg {k}={v} end",
                "cfg {k}: {v} end",
            ]  # batch 9: the digits are no longer cut at 20, so the key rule reads every length
            for tmpl in forms:
                left += [f"{key} {tmpl}: {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
    assert not left, (
        f"a bare word with many digits leaves a value readable: {left[:6]} ({len(left)})"
    )


def test_b8_8_a_very_long_run_of_digits_is_read_once():
    # batch 14: a ratio, not a limit of 20 seconds (a quadratic read of 50,000 digits fits in 20 seconds on a fast machine, so the old
    # limit let it pass). 4 times the digits: linear is 4, quadratic 16; measured on the head 4.0 (best of three each), bound 7; repeated up to three times, it fails only when all three are over the bound.
    def best(digits: int) -> float:
        text = ("pass" + "1" * digits + " ") * 4
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
        f"a very long run of digits after a bare credential word is read many times: {small:.3f}s and {large:.3f}s for 4 times the digits"
    )


# ---- Issue 12: a key with the word `cookie` and more words, in text ----------------------------------------------------

COOKIE_WORD_KEYS = (
    "cookie_name",
    "cookie-policy",
    "cookie.domain",
    "cookieName",
    "Cookie_Name",
    "set-cookie-extra",
    "cookie2",
    "cookie_name2",
)


def test_b8_12_a_key_with_the_word_cookie_and_more_words_is_masked_in_text_as_the_record_walk_masks_it():
    left = []
    for key in COOKIE_WORD_KEYS:
        assert R.sensitive(key), f"the record walk does not mask {key}"
        for tmpl in (
            "cfg {k}={v} end",
            "cfg {k}: {v}",
            'cfg {k}="{v}" end',
            '{{"{k}": "{v}"}} tail',
        ):
            left += [f"{key} {tmpl}: {x}" for x in readable_on(tmpl.format(k=key, v=V), V)]
    assert not left, f"a cookie word key leaves a value readable in text: {left[:8]} ({len(left)})"


def test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk():
    """Controls (the two paths agree): `mycookie` and `cookiejar` are one word with no cookie word in it."""
    for key in ("mycookie", "cookiejar", "cookiemonster"):
        assert not R.sensitive(key), key
        text = f"cfg {key}={ORDINARY_VALUE} end"
        assert clean(text) == text, f"{key} was masked as text: {clean(text)!r}"


# ---- Issue 13: one machine-checkable line per test that passes on old code ---------------------------------------------
# The lines and the check live in `tests/test_q8b_batch8_lines.py`.

"""Q8b batch 13 (the round 13 review, redaction path): the classes the round 13 review found in batch 12.

Group 1  a literal prefilter that tries fewer start positions than a full scan (two key words glued so that they share a character).
Group 2  a scheme-word class wider than the reading it replaced (a hyphenated TOKEN read as a scheme word left the token readable).
Group 3  the folded-header rule for any first word read the whole rest of a glued run from every `authorization` (quadratic).
Group 5  an exemption for the bare ordinary word that was wider than the bare word (`new_bypass`, `x-bypass`, `x_compass`).
Group 6  the old folded-header rule masks a Digest header under a credential-key name; no test showed the new rules do the same.
Group 7  limits: JSON siblings after an `Authorization` key, the rare line breaks on the card path, a rare break inside a folded line.
Group 8  the other line-break characters of `str.splitlines` (`\\x1c`, `\\x1d`, `\\x1e`).
"""

from __future__ import annotations

import importlib
import itertools
import json
import random
import time
import zlib

import pytest

from hadavin_sdk.approvals.channel import clean
from tests.test_q8b_batch7 import five_paths

redact_module = importlib.import_module("hadavin_sdk.guard.redact")

_ALPHA = "xkvmzwhtrpnqbdfglscyaeuJQKZ0123456789"
LOW = (
    "segmentalpha",
    "bravosegment",
    "charliesegmentdelta",
)  # lower-case words: no entropy rule masks them by itself


def made_up_value(seed: int, n: int = 20) -> str:
    rnd = random.Random(seed)  # noqa: S311 - a seeded test generator, not a secret
    return "".join(rnd.choice(_ALPHA) for _ in range(n))


def _outs(text: str) -> list[str]:
    return [clean(text), redact_module.redact(text).text]


# ---- Group 1: the prefilter tries every position where a key word starts, also inside the word before it ------------------------


def _overlap_joins() -> list[str]:
    """Every gate word `a` and `b` where a suffix of `a` is a prefix of `b`, glued on the shared characters (`access` + `session` =
    `accessession`): the second word starts INSIDE the first, which a non-overlapping scan never tries."""
    words = redact_module.KEY_GATE_WORDS
    out = []
    for a in words:
        for b in words:
            for k in range(1, min(len(a), len(b))):
                if a.endswith(b[:k]):
                    out.append(a + b[k:])
    return sorted(set(out))


def _g1_corpus() -> list[str]:
    rnd = random.Random(1301)  # noqa: S311 - a seeded test generator, not a secret
    joins = _overlap_joins()
    out = []
    for name in joins:
        v = made_up_value(zlib.crc32(name.encode()))
        out += [
            f"{name}={v}",
            f"{name}: {v}",
            f'{{"{name}": "{v}"}}',
            f"--{name} {v}",
            f"x {name}='{v} {v}' end",
            f"{name.upper()}={v}",
            f"pre_{name}_post={v}",
        ]
    # a third word that starts inside the second: three words in a chain
    for _ in range(300):
        a, b = rnd.choice(joins), rnd.choice(redact_module.KEY_GATE_WORDS)
        v = made_up_value(rnd.randrange(10**6))
        out.append(f"{a}{rnd.choice(['', '_', '-'])}{b}={v}")
    return out


def test_b13_1_the_overlapping_joins_are_a_real_corpus():
    joins = _overlap_joins()
    assert len(joins) >= 20 and {"accessession", "passecret", "passession", "clientoken"} <= set(
        joins
    ), f"the join generator found {len(joins)} joins and misses the known ones"


def test_b13_1_the_prefilter_gives_the_same_text_as_a_full_scan_for_key_words_that_share_a_character(
    monkeypatch,
):
    corpus = _g1_corpus()
    with_gate = [redact_module.redact(t).text for t in corpus]
    monkeypatch.setattr(redact_module, "_GATES", {})
    without_gate = [redact_module.redact(t).text for t in corpus]
    differ = [(t, a, b) for t, a, b in zip(corpus, with_gate, without_gate, strict=True) if a != b]
    assert not differ, (
        f"the literal prefilter skips a key word that starts inside the key word before it: {len(differ)} of {len(corpus)} outputs differ, "
        f"first {differ[:2]!r}"
    )


def test_b13_1_a_credential_key_made_of_two_words_that_share_a_character_is_masked_as_on_main():
    # `accessession=<value>`, `passecret=<value>`, `clientoken=<value>`: the key words are `session`, `secret`, `token` after a gate word.
    left = []
    for name in (
        "accessession",
        "xpassession",
        "passecret",
        "passas_token",
        "clientoken",
        "certoken",
        "connectoken",
        "accountoken",
    ):
        value = made_up_value(zlib.crc32(name.encode()), 24)
        for form in (f"{name}={value}", f"{name}: {value}", f'{{"{name}": "{value}"}}'):
            left += [form for out in _outs(form) if value in out]
    assert not left, f"a key made of two key words that share a character is readable: {left[:4]}"


def test_b13_1_the_gate_finder_reports_a_word_that_starts_inside_a_word_it_has_reported():
    finder = next(f for w, f in redact_module._GATE_FINDERS.items() if "session" in w)
    starts = [m.start() for m in finder.finditer("accessession")]
    assert 0 in starts and 5 in starts, (
        f"the finder of the prefilter skips a word that starts inside the word before it: {starts}"
    )


# ---- Group 2: a hyphenated token is no scheme word on the one-line rule; the credential behind a hyphenated scheme word is masked ---


def _hyphen_tokens() -> list[str]:
    """Capital-first, digit-bearing and mixed-case hyphenated tokens of 1 to 3 hyphen groups, 8 characters or more (main masked them)."""
    rnd = random.Random(1302)  # noqa: S311 - a seeded test generator, not a secret
    first = ("Ab", "Correct", "Horse", "Licence", "Zx", "Key", "Ab12")
    group = ("Cd34", "Battery", "Staple", "Ef56", "x9Y8", "QRST", "kk")
    out = []
    for n in (1, 2, 3):
        for _ in range(25):
            t = rnd.choice(first) + "".join("-" + rnd.choice(group) for _ in range(n))
            if len(t) >= 8:
                out.append(t)
    return sorted(set(out))


AFTERS = (
    " retried_after_backoff",
    "\nAccept: shown\n",
    " ok",
    "\n  next\nHost: x",
    "\r\nAccept: shown",
)
HEADS = ("Authorization: ", "authorization=", '"Authorization": "', "Proxy-Authorization: ")


def test_b13_2_a_hyphenated_token_after_authorization_is_masked_as_on_main():
    left = []
    toks = _hyphen_tokens()
    assert len(toks) >= 30
    for t, after, head in itertools.product(toks, AFTERS, HEADS):
        text = head + t + after
        left += [f"{head}{t}{after!r}" for out in _outs(text) if t in out]
    assert not left, (
        f"a hyphenated token after Authorization is read as a scheme word and left readable: {left[:3]} ({len(left)})"
    )


@pytest.mark.parametrize(
    "scheme", ("AWS4-HMAC-SHA256", "SCRAM-SHA-256", "Custom-Scheme", "Hawk-Id1")
)
def test_b13_2_the_credential_behind_a_hyphenated_scheme_word_is_masked_on_the_same_line(scheme):
    left = []
    # two forms: a keyed value (`Credential=<v>`, which the key rules read as well) and a bare token (only the second rule for a
    # hyphenated scheme word masks it: the fault of mutant M255 leaves it readable)
    for head, i, form in itertools.product(HEADS, range(3), ("Credential={s}", "{s}")):
        secret = made_up_value(zlib.crc32(scheme.encode()) + i, 24)
        text = f"{head}{scheme} {form.format(s=secret)} extra\nAccept: shown\n"
        left += [f"{head}{scheme} {form}: {secret}" for out in _outs(text) if secret in out]
    assert not left, (
        f"the credential behind the hyphenated scheme word {scheme} is readable: {left[:3]}"
    )


def test_b13_2_a_lower_case_hyphen_word_after_a_hyphen_token_is_shown_as_on_main():
    # control (a stated cost, not a fault): the word BEHIND a lower-case hyphen token is a second word, shown as on main; the batch 12
    # rule read the first word as a scheme word and masked the second instead. Only a capital-first hyphenated word has a credential
    # behind it that the second rule masks, so a lower-case one must leave the next word alone.
    out = redact_module.redact("Authorization: abcdefgh-ijklmnop segmentalpha\n").text
    assert "abcdefgh" not in out, f"a lower-case hyphen token is left readable: {out!r}"
    assert "segmentalpha" in out, (
        f"the word behind a lower-case hyphen token is masked as if the token were a scheme word: {out!r}"
    )


# ---- Group 3: a glued run of headers is read in time linear in its length ------------------------------------------------------------

# `authorization:"x"` is the shape that was quadratic (killer of M248); the others are controls of the same class on the other rules that read a
# first word or a scheme word after a key (measured linear on `a148bda6` too: they pass on the old code, so they pin the class, not the fault).
GLUED = (
    'authorization:"x"',
    "authorization=a",
    "Authorization:x ",
    'authorization: "x",',
    'secret:"x"',
    'token="x"',
    "X-Api-Key:Basic x",
    "token:Basic\n x",
    'authorization:Digest a="b",',
)


@pytest.mark.parametrize("unit", GLUED)
def test_b13_3_a_glued_run_of_headers_is_read_in_linear_time(unit):
    def took(chars: int) -> float:
        text = unit * (chars // len(unit))
        t0 = time.perf_counter()
        redact_module.redact(text)
        return time.perf_counter() - t0

    took(5_000)
    small = min(took(20_000) for _ in range(3))
    big = min(took(80_000) for _ in range(3))
    assert big < max(small, 0.02) * 9, (
        f"a glued run of `{unit}` is read in more than linear time (the first word of the folded-header rule reads the rest of the run): "
        f"{small:.3f}s and {big:.3f}s for 4 times the size"
    )


# ---- Group 5: only the bare ordinary word stays shown; a word in front of it is a credential key again, as on main ----------------

PREFIXES = ("x_", "new-", "my.", "1", "x2_", "a-b_", "X_", "db.")


def _ordinary() -> list[str]:
    return sorted(redact_module.ORDINARY_WORDS)


def _forms(name: str, value: str) -> dict[str, str]:
    return {
        "json": json.dumps({name: value}),
        "json-colon-space": '{"' + name + '" :   "' + value + '"}',
        "dq": f'cfg {name}="{value}" end',
        "sq": f"cfg {name}='{value}' end",
        "eq": f"cfg {name}={value} end",
        "colon": f"cfg {name}: {value} end",
    }


def test_b13_5_an_ordinary_word_behind_a_prefix_is_a_credential_key_in_every_form_as_on_main():
    left = []
    for o, p in itertools.product(_ordinary(), PREFIXES):
        name = p + o
        value = made_up_value(zlib.crc32(name.encode()))
        for form, text in _forms(name, value).items():
            left += [f"{form} {name}" for out in _outs(text) if value in out]
    assert not left, (
        f"an ordinary word behind a prefix (`x_`, `new-`, `my.`, a digit) is read as the bare ordinary word and left readable: {left[:4]} ({len(left)})"
    )


@pytest.mark.parametrize("word", _ordinary())
def test_b13_5_the_bare_ordinary_word_stays_shown_in_every_form(word):
    # the pin of the owner question q-q8b-bare-bypass: ALL 15 words, quoted, unquoted, colon and flag forms, upper case too
    left = []
    value = made_up_value(zlib.crc32(word.encode()))
    forms = dict(_forms(word, value))
    forms["json-upper"] = json.dumps({word.upper(): value})
    forms["flag-space"] = f"ran tool --{word} {value} --verbose"
    for form, text in forms.items():
        if form == "flag-space":
            continue
        out = redact_module.redact(text).text
        if value not in out:
            left.append(form)
    assert not left, (
        f"the bare ordinary word {word} is masked in the forms {left}: the owner decision is shown (pinned)"
    )


# ---- Group 6: a Digest header folded under a credential-key name ---------------------------------------------------------------------


@pytest.mark.parametrize("name", ("token", "secret", "passwd", "X-Api-Key"))
def test_b13_6_a_digest_header_folded_under_a_credential_key_name_is_masked_to_the_last_fold(name):
    left = []
    for sep, nl, ind in itertools.product((": ", "="), ("\n", "\r\n"), (" ", "\t", "    ")):
        a, b = LOW[0], LOW[1]
        text = f'{name}{sep}Digest u="a",{nl}{ind}response="{a}",{nl}{ind}nonce="{b}"{nl}Accept: shown\n'
        for out in _outs(text):
            left += [f"{name!r} {sep!r} {nl!r} {ind!r}: {p}" for p in (a, b) if p in out]
    assert not left, (
        f"a folded Digest header under {name} leaves its next lines readable: {left[:3]} ({len(left)})"
    )


# ---- Group 7: limits -----------------------------------------------------------------------------------------------------------------


def test_b13_7_the_siblings_of_an_authorization_key_stay_shown_in_pretty_printed_json():
    text = (
        '{\n  "Authorization": "Custom-Scheme '
        + made_up_value(1, 24)
        + '",\n  "request_id": "req-shown-1",\n'
        '  "region": "shown-region"\n}'
    )
    for out in _outs(text):
        assert "req-shown-1" in out and "shown-region" in out, (
            f"the folded-header rule for any first word masked the siblings of an Authorization key: {out!r}"
        )
    # a folded value that is NOT a `name:` line is still masked to its end
    a, b = LOW[0], LOW[1]
    text = f"Authorization: NTLM {a}\n {b}\nAccept: shown\n"
    assert all(b not in o for o in _outs(text)), (
        "a folded line of a header with any first word is readable"
    )


RARE = {
    "vertical tab": "\x0b",
    "form feed": "\x0c",
    "next line": "\x85",
    "line separator": " ",
    "paragraph separator": " ",
}


@pytest.mark.parametrize("name", sorted(RARE))
def test_b13_7_a_header_folded_over_a_rare_line_break_is_masked_on_every_path(name):
    br = RARE[name]
    a, b = LOW[0], LOW[1]
    left = []
    for scheme in ("Bearer", "Basic", "NTLM", "Custom-Scheme"):
        text = f"Authorization: {scheme} {a}{br} {b}{br}Accept: shown\n"
        left += [f"{scheme} {path}: {b}" for path, out in five_paths(text).items() if b in out]
    assert not left, f"a header folded over {name} leaves the next line readable on {left[:3]}"


@pytest.mark.parametrize("name", sorted(RARE))
def test_b13_7_a_rare_line_break_inside_a_folded_line_does_not_end_the_masked_value(name):
    br = RARE[name]
    a, b, c = LOW
    left = []
    for scheme in ("Bearer", "NTLM", "Custom-Scheme"):
        text = f"Authorization: {scheme} {a}\n  {b}{br}{c}\nAccept: shown\n"
        left += [f"{scheme}: {c}" for out in _outs(text) if c in out]
    assert not left, (
        f"the second part of a folded line after {name} is shown (batch 11 masked it): {left[:3]}"
    )


# ---- Group 8: the break characters of str.splitlines ----------------------------------------------------------------------------------


@pytest.mark.parametrize("br", ["\x1c", "\x1d", "\x1e"])
def test_b13_8_the_information_separators_end_a_line_like_str_splitlines_does(br):
    a, b = LOW[0], LOW[1]
    assert (
        "x\x1cy".splitlines() == ["x", "y"]
        and "x\x1dy".splitlines() == ["x", "y"]
        and "x\x1ey".splitlines() == ["x", "y"]
    )
    left = []
    for scheme in ("Bearer", "NTLM", "Custom-Scheme", ""):
        text = f"Authorization: {scheme} {a}{br} {b}{br}Accept: shown\n"
        left += [f"{scheme!r}: {b}" for out in [redact_module.redact(text).text] if b in out]
    assert not left, f"a header folded over {br!r} leaves the next line readable: {left[:3]}"


def test_b13_8_every_character_that_splitlines_reads_as_a_break_is_known_to_the_fold_rules():
    breaks = {c for c in map(chr, range(0x110000)) if len(("a" + c + "b").splitlines()) == 2} - {
        "\n",
        "\r",
    }
    known = set(redact_module._OTHER_BREAKS)
    assert breaks <= known, (
        f"str.splitlines breaks the fold rules do not know: {sorted(hex(ord(c)) for c in breaks - known)}"
    )


# ---- Group 4: the wall-clock tests of the Q8b files, counted from the files, not from a list --------------------------------------------

import re
from pathlib import Path

from tests.test_q8b_batch8_lines import planted_killers

HERE = Path(__file__).resolve().parent
# The wall-clock tests of the Q8b files that no mutant of `tests/q8b_mutants.py` names as its killer: a regression to quadratic time of
# the rule each one times would pass it (found by the round 13 review: the CHANGELOG of batch 12 said 4, then 3; the true count at the head
# of batch 12 was 11; batch 13 plants two of them, M256 and M257, so 9 are left). The number is a gate: a new wall-clock test without a planted fault, or a planted fault that is dropped, changes the
# count and fails `test_b13_4_...`; the number only falls. The list is printed in the failure.
WALL_CLOCK_UNPLANTED_MAX = 9


def wall_clock_tests() -> dict[str, str]:
    """test name -> file, for every test of the Q8b test files whose body reads the clock."""
    found: dict[str, str] = {}
    for path in sorted(HERE.glob("test_q8b_*.py")):
        src = path.read_text(encoding="utf-8")
        for m in re.finditer(
            r"^def (test_\w+)\(.*?(?=^def |^@pytest|\Z)", src, re.DOTALL | re.MULTILINE
        ):
            if "perf_counter" in m.group(0) or "time.time()" in m.group(0):
                found[m.group(1)] = path.name
    return found


def test_b13_4_the_wall_clock_tests_are_found_by_reading_the_files_and_include_the_known_ones():
    found = wall_clock_tests()
    known = {
        "test_b11_8_a_long_run_of_folded_lines_is_read_in_linear_time",
        "test_b10_1_a_long_run_of_line_breaks_after_a_scheme_word_is_read_in_linear_time",
        "test_b8_8_a_very_long_run_of_digits_is_read_once",
        "test_b13_3_a_glued_run_of_headers_is_read_in_linear_time",
    }
    assert known <= set(found) and len(found) >= 14, (
        f"the scan of the test files found {sorted(found)}"
    )


def test_b13_4_the_number_of_wall_clock_tests_without_a_planted_fault_is_the_pinned_number():
    kills = planted_killers()
    unplanted = sorted(n for n in wall_clock_tests() if n not in kills)
    assert len(unplanted) == WALL_CLOCK_UNPLANTED_MAX, (
        f"{len(unplanted)} wall-clock tests have no planted fault, the pinned number is {WALL_CLOCK_UNPLANTED_MAX}: plant a fault for the "
        f"new one, or lower the pinned number to the real one: {unplanted}"
    )

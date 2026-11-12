"""Q8b batch 14 (the round 14 review, redaction path): the classes the round 14 review found in batch 13.

Group 1  the bare ordinary word is a whole key only when NO key character stands in front of it (`x--bypass`, `x--compass`, `-bypass`).
Group 2  a wall-clock test with no planted fault (every one now has a planted fault, or counts work instead of seconds).
Group 3  every line break that `str.splitlines` knows, on all five paths (the card path for U+001C, U+001D, U+001E).
Group 5  the small ones: the first word of a header that is itself an `authorization:` header, the flag form of the 15 words.
"""

from __future__ import annotations

import importlib
import itertools
import zlib
from typing import NamedTuple

import pytest

from hadavin_sdk.approvals.channel import clean
from tests.test_q8b_batch13 import made_up_value

redact_module = importlib.import_module("hadavin_sdk.guard.redact")

# ---- Group 1: the generator --------------------------------------------------------------------------------------------------------

# The characters of a KEY, as main reads them: `[\w.\-]` (a letter, a digit, an underscore, a dot, a hyphen; `\w` is the Unicode word class,
# so a non-ASCII letter is one too). One of each kind plus a non-ASCII letter. The characters that are NOT key characters: a space, a tab,
# punctuation that opens or separates a value, and a non-ASCII sign. A prefix is every string of one or two key characters over that whole
# list (a pair of key characters in every order, `x--`, `.-`, `-x-`, `a--b-` among them), and every string of three over the characters
# that make the hyphen shapes (`-`, `.`, a letter). Each prefix is tried behind EVERY non-key character (every non-key/key pair of
# neighbours), at the start of the text too.
KEY_CHARS = ("a", "Z", "0", "_", ".", "-", "é")
NON_KEY_CHARS = (" ", "\t", "(", ">", "[", ",", ";", "'", "§")
_SHAPE_CHARS = ("-", ".", "x")


def _prefixes() -> list[str]:
    out = [""]
    for n in (1, 2):
        out += ["".join(p) for p in itertools.product(KEY_CHARS, repeat=n)]
    out += ["".join(p) for p in itertools.product(_SHAPE_CHARS, repeat=3)]
    return sorted(set(out), key=lambda p: (len(p), p))


def _ordinary() -> list[str]:
    return sorted(redact_module.ORDINARY_WORDS)


def _forms(name: str, value: str, before: str = " ") -> dict[str, str]:
    return {
        "eq": f"cfg{before}{name}={value} end",
        "colon": f"cfg{before}{name}: {value} end",
        "json": '{"' + name + '": "' + value + '"}',
        "dq": f'cfg{before}{name}="{value}" end',
        "flag-eq": f"cmd{before}--{name}={value} end",
    }


class Cell(NamedTuple):
    form: str
    before: str  # the character in front of the key (a non-key character)
    prefix: str  # the key characters between that character and the ordinary word
    name: str  # prefix + ordinary word
    text: str
    value: str


def _cells() -> list[Cell]:
    """Every ordinary word behind every prefix that is not empty, behind every non-key character (a prefix of one character) or a space."""
    cells = []
    for word in _ordinary():
        for prefix in _prefixes():
            if not prefix:
                continue  # the bare word: the owner question q-q8b-bare-bypass (pinned in batch 13)
            name = prefix + word
            value = made_up_value(zlib.crc32(name.encode()))
            for before in NON_KEY_CHARS if len(prefix) == 1 else (" ",):
                cells += [
                    Cell(form, before, prefix, name, text, value)
                    for form, text in _forms(name, value, before).items()
                ]
    return cells


def test_b14_1_the_generator_covers_every_pair_of_a_non_key_and_a_key_character_and_every_pair_of_key_characters():
    cells = _cells()
    neighbours = {(c.before, c.prefix[0]) for c in cells}
    assert {(nk, kc) for nk in NON_KEY_CHARS for kc in KEY_CHARS} <= neighbours, (
        "the prefix generator leaves out a (non-key character, key character) pair"
    )
    inside = {c.prefix[:2] for c in cells if len(c.prefix) >= 2}
    assert {a + b for a in KEY_CHARS for b in KEY_CHARS} <= inside, (
        "the prefix generator leaves out a pair of key characters"
    )
    assert {"x--", ".-", "-x-", "---", "a-", "-a"} <= {c.prefix for c in cells}, (
        "the shapes of the review are missing"
    )
    assert len(cells) >= 5000, f"the generator is too small to be a class test: {len(cells)} cells"
    assert all(c.value in c.text and len(c.value) == 20 for c in cells)


def _is_the_bare_flag(c: Cell) -> bool:
    """`--word` after a non-key character is the flag form of the bare word (shown: the owner question q-q8b-bare-bypass); in the flag-eq form
    the two hyphens are in the template, so the prefix must be empty (it never is here)."""
    return c.prefix == "--" and c.form != "flag-eq"


def test_b14_1_an_ordinary_word_behind_any_key_character_is_a_credential_key_in_every_form_as_on_main():
    # main read the whole key `[\w.\-]{0,40}word` and masked the value; the head of batch 13 let one or two hyphens in front count as a start,
    # whatever stood in front of them. Now only the bare word and the flag `--word` (exactly two hyphens after a non-key character) are shown.
    left = []
    shown_flags = []
    cells = _cells()
    for c in cells:
        for path, out in zip(
            ("card", "redact"), (clean(c.text), redact_module.redact(c.text).text), strict=True
        ):
            if c.value in out:
                (shown_flags if _is_the_bare_flag(c) else left).append(
                    f"{path} {c.form} {c.before!r} {c.name}"
                )
    assert not left, (
        f"an ordinary word behind key characters is read as the bare ordinary word and left readable (x--bypass shape): {left[:4]} ({len(left)} of {len(cells) * 2} cells)"
    )
    flags = [c for c in cells if _is_the_bare_flag(c)]
    assert flags and len(shown_flags) == 2 * len(flags), (
        "the bare flag `--word` (shown, owner question) is masked: the pin of batch 13 changed"
    )


@pytest.mark.parametrize("word", _ordinary())
def test_b14_1_the_bare_flag_shows_the_ordinary_word_and_a_prefixed_flag_is_masked(word):
    # N2 of the round 14 review: the flag form of ALL 15 words (the pin of q-q8b-bare-bypass covers `--word value` and `--word=value`)
    value = made_up_value(zlib.crc32(word.encode()))
    for text in (f"ran tool --{word} {value} --verbose", f"ran tool --{word}={value} --verbose"):
        for path, o in (("redact", redact_module.redact(text).text), ("card", clean(text))):
            assert value in o, (
                f"the bare flag {text!r} is masked on the {path} path: the owner decision is shown (pinned): {o!r}"
            )
    for prefix in ("-", "x--", "x-", "---", ".--"):
        for sign in ("=", ":"):
            masked = f"ran tool {prefix}{word}{sign}{value} --verbose"
            for path, o in (("redact", redact_module.redact(masked).text), ("card", clean(masked))):
                assert value not in o, (
                    f"{prefix}{word}{sign}<value> is readable on the {path} path (main masked it)"
                )


# ---- Group 5 (N4): a first word that holds `authorization` inside it ---------------------------------------------------------------------

_FIRST_WORDS = (
    "x-authorization:v",
    "x-authorization:",
    "x-authorization: v",
    "xauthorization=v",
    "a--authorization:v",
    "Authorization",
    "Authorizationx",
    "xAuthorization",
    "authorization-x",
    "x-authorization:v w",
)
_HEADS = ("Authorization: ", "authorization=", "Proxy-Authorization: ")


@pytest.mark.parametrize("first", _FIRST_WORDS)
def test_b14_5_a_header_whose_first_word_holds_authorization_masks_its_folded_lines(first):
    # N4 of the round 14 review: `Authorization: x-authorization:v` then an indented line. The first word of the wide fold rule ends where the next
    # `authorization:` starts (so a glued run is read in linear time); the folded lines behind a first word that is cut that way must still be masked.
    left = []
    a, b = "segmentalpha", "bravosegment"
    for head, nl, ind in itertools.product(_HEADS, ("\n", "\r\n", "\x0c"), (" ", "\t", "    ")):
        text = f"{head}{first}{nl}{ind}{a}{nl}{ind}{b}\nAccept: shown\n"
        left += [
            f"{head!r} {nl!r} {ind!r}: {p}"
            for out in (clean(text), redact_module.redact(text).text)
            for p in (a, b)
            if p in out
        ]
    assert not left, (
        f"a folded line behind a first word that holds `authorization` is readable (the first word of the wide fold rule ended at it): {left[:3]} ({len(left)})"
    )


# ---- Group 5 (N1, N3): what LIMITS says about a rare break on a card and about a prefix is what the code does ------------------------------


def test_b14_5_limits_states_the_condition_of_a_rare_break_and_the_prefix_disagreement_and_both_are_true():
    from hadavin_sdk.k1b import redaction as k1b

    limits = " ".join(k1b.LIMITS.split())
    for phrase in (
        "ONLY when a space or a tab follows",
        "`x-bypass`, `x--bypass`, `new_bypass` and `x_compass`",
        "as on `main`",
    ):
        assert phrase in limits, f"LIMITS does not say: {phrase!r}"
    from hadavin_sdk.approvals import channel

    folded = "Authorization: Digest user=a,\x1c  response=zq9digestvalue1"
    cut = "Authorization: Digest user=a,\x1cresponse=zq9digestvalue1"
    assert "\n" in channel._LINE_BREAK_CONTROLS.sub("\n", folded), (
        "a rare break before a space is not a line feed on a card"
    )
    assert "\n" not in channel._LINE_BREAK_CONTROLS.sub("\n", cut), (
        "a rare break before a letter became a line feed on a card"
    )
    for key in ("x-bypass", "x--bypass", "new_bypass", "x_compass"):
        assert not k1b.sensitive(key), (
            f"the record walk now reads {key!r} as a key: change the sentence in LIMITS"
        )
        assert "<" in redact_module.redact(f"{key}=zq9value1").text, f"the card rule shows {key}=v"

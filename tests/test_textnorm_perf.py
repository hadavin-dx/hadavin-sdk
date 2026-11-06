"""Timing rows of the text fold (marker ``perf``: CI runs them in their own step). They are NOT in any mutation test list, because the
runner does not copy ``pyproject.toml`` and the marker would be unregistered there. Ceilings are generous (about 20 times the time
measured on the build machine) and say what the row is about."""

import time

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.textnorm import TextTooLong, has_hidden_channel, identity_key, squeeze

pytestmark = pytest.mark.perf
CAP = defaults.TEXTNORM_MAX_CHARS


def _seconds(fn, *args):
    start = time.perf_counter()
    try:
        fn(*args)
    except TextTooLong:
        pass
    return time.perf_counter() - start


def test_a_million_expanding_characters_are_refused_before_any_work():
    """1,000,000 x U+FDFA expands to 18 million characters; the size rule refuses it from the weight, without building the key."""
    assert _seconds(identity_key, chr(0xFDFA) * 1_000_000) < 2.0


def test_a_text_at_the_cap_of_distinct_kinds_of_character_is_folded_in_linear_time():
    text = ("a" + chr(0x301) + "b" + chr(0x200B) + "c" + chr(0x430) + chr(0xFF21) + " \t") * (
        CAP // 9
    )
    assert len(text) <= CAP
    assert _seconds(identity_key, text) < 5.0
    assert _seconds(squeeze, text) < 5.0
    assert _seconds(has_hidden_channel, text) < 1.0


def test_the_refusal_of_an_oversize_ascii_text_is_immediate():
    assert _seconds(identity_key, "a" * (CAP + 1)) < 0.5


def _distinct(start, n):
    """``n`` different code points from ``start`` on, none of them a lone surrogate."""
    out, cp = [], start
    while len(out) < n:
        if not 0xD800 <= cp <= 0xDFFF:
            out.append(chr(cp))
        cp += 1
    return "".join(out)


def test_a_huge_text_of_distinct_characters_is_refused_from_its_length_alone():
    """Review 3 (F6): 983,040 DIFFERENT characters (about 4 MB) used to cost seconds, because every distinct character was weighed (about six
    normalisations each) before the cap was compared. The length is compared first now, so the refusal is immediate for every function."""
    text = _distinct(0x20000, 983_040)
    assert len(set(text)) == len(text) > CAP
    for fn in (
        identity_key,
        squeeze,
        textnorm.identity_keys,
        textnorm.fold_views,
        textnorm.squeeze_views,
        has_hidden_channel,
    ):
        assert _seconds(fn, text) < 0.5, fn.__name__
    assert _seconds(textnorm.same_person, "a", text) < 0.5


def test_a_text_of_distinct_characters_at_the_cap_is_weighed_and_read_in_linear_time():
    """The most work a text within the length cap can cost: every character different (CAP of them), so each is weighed once, and then every
    reading is made. The ceiling is generous (about 8 times the time measured on the build machine)."""
    text = _distinct(0x4E00, CAP)
    assert len(set(text)) == len(text) == CAP
    for fn in (identity_key, textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
        assert _seconds(fn, text) < 5.0, fn.__name__
    assert _seconds(textnorm.same_person, text, text) < 8.0


def test_a_text_of_a_greek_letter_and_ypogegrammeni_pairs_at_the_cap_is_read_in_linear_time():
    text = ("\u03b1\u0345" + "\u0397\u0345" + "\u1fb3") * (CAP // 5)
    assert len(text) <= CAP
    for fn in (identity_key, textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
        assert _seconds(fn, text) < 5.0, fn.__name__
    assert _seconds(textnorm.same_person, text, text[::-1]) < 8.0

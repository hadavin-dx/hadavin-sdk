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
    """The time of ``fn(*args)``. A refusal (``TextTooLong``) is NOT swallowed: a row that is meant to time the real fold fails if its text is refused."""
    start = time.perf_counter()
    fn(*args)
    return time.perf_counter() - start


def _refusal_seconds(fn, *args):
    """The time until ``fn(*args)`` raises ``TextTooLong``; fails if it does not raise (a row about a refusal must see the refusal)."""
    start = time.perf_counter()
    with pytest.raises(TextTooLong):
        fn(*args)
    return time.perf_counter() - start


def test_a_million_expanding_characters_are_refused_from_the_length_before_any_work():
    """1,000,000 x U+FDFA is over the LENGTH cap (262,144), so it is refused from its length alone, without weighing a character."""
    assert _refusal_seconds(identity_key, chr(0xFDFA) * 1_000_000) < 2.0


def test_sixteen_thousand_expanding_characters_are_refused_from_the_weight_before_any_work():
    """16,000 x U+FDFA is far below the length cap (262,144), so the WEIGHT path runs: 18 characters each, 288,000 in all, over the cap. The
    refusal must come from the weight, without building a key (``tests/test_textnorm.py`` proves "no fold step ran" with no clock; this row
    is the time ceiling)."""
    text = chr(0xFDFA) * 16_000
    assert len(text) < CAP < textnorm._weight(text)
    assert _refusal_seconds(identity_key, text) < 0.5
    assert _refusal_seconds(textnorm.squeeze_views, text) < 0.5


def test_a_text_at_the_cap_of_distinct_kinds_of_character_is_folded_in_linear_time():
    text = ("a" + chr(0x301) + "b" + chr(0x200B) + "c" + chr(0x430) + chr(0xFF21) + " \t") * (
        CAP // 9
    )
    assert len(text) <= CAP and textnorm._weight(text) <= CAP, (
        "the row would be refused, not folded"
    )
    assert _seconds(identity_key, text) < 5.0
    assert _seconds(squeeze, text) < 5.0
    assert _seconds(has_hidden_channel, text) < 1.0


def test_the_refusal_of_an_oversize_ascii_text_is_immediate():
    assert _refusal_seconds(identity_key, "a" * (CAP + 1)) < 0.5


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
        assert _refusal_seconds(fn, text) < 0.5, fn.__name__
    assert _refusal_seconds(textnorm.could_be_same_person, "a", text) < 0.5


def _distinct_within_weight(start, cap):
    """Different code points from ``start`` on, one after the other while the total WEIGHT stays within ``cap`` (a code point that NFKC expands
    uses more of it), so the text is folded and not refused."""
    out, total, cp = [], 0, start
    while True:
        if not 0xD800 <= cp <= 0xDFFF:
            weight = textnorm._weight(chr(cp))
            if total + weight > cap:
                return "".join(out)
            out.append(chr(cp))
            total += weight
        cp += 1


def test_a_text_of_distinct_characters_at_the_cap_is_weighed_and_read_in_linear_time():
    """The most work a text within the cap can cost: every character different (about CAP of them), so each is weighed once, and then every
    reading is made. The text is built so that its WEIGHT is within the cap (it is folded, not refused). The ceiling is generous (about 8
    times the time measured on the build machine)."""
    text = _distinct_within_weight(0x4E00, CAP)
    assert len(set(text)) == len(text) > CAP * 4 // 5, (
        "the text is not most of the cap in distinct characters"
    )
    assert textnorm._weight(text) <= CAP, "the row would be refused, not folded"
    for fn in (identity_key, textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
        assert _seconds(fn, text) < 5.0, fn.__name__
    assert _seconds(textnorm.could_be_same_person, text, text) < 8.0


def test_a_text_of_a_greek_letter_and_ypogegrammeni_pairs_at_the_cap_is_read_in_linear_time():
    unit = "\u03b1\u0345" + "\u0397\u0345" + "\u1fb3"
    text = unit * (
        CAP // textnorm._weight(unit)
    )  # the unit weighs more than its 5 characters: count by weight
    assert textnorm._weight(text) <= CAP < textnorm._weight(text) + textnorm._weight(unit), (
        "the row would be refused, or is far below the cap"
    )
    for fn in (identity_key, textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
        assert _seconds(fn, text) < 5.0, fn.__name__
    assert _seconds(textnorm.could_be_same_person, text, text[::-1]) < 8.0


def test_a_text_at_the_cap_with_spacing_marks_is_scanned_in_linear_time_with_the_marks_dropped_views():
    """A text with a spacing combining mark (Mc), a modifier letter (Lm) and a modifier symbol (Sk) in it gets the marks-dropped
    readings too, so ``squeeze_views`` builds up to six views and ``fold_views`` up to nine of a text at the cap (``fold_views`` builds more than one here). This is the cost of the extra
    readings; it must stay linear (a ceiling of about 20 times the time measured on the build machine)."""
    unit = "pass" + chr(0x0903) + chr(0x02C6) + chr(0x02C2) + "word " + chr(0x430)
    text = unit * (CAP // textnorm._weight(unit))
    assert len(text) <= CAP and textnorm._weight(text) <= CAP, (
        "the row would be refused, not folded"
    )
    views = textnorm.fold_views(text, casefold=True)
    assert 2 <= len(views) <= 9
    assert all(len(v) <= textnorm._weight(text) for v in views)
    assert _seconds(lambda t: textnorm.fold_views(t, casefold=True), text) < 5.0
    assert _seconds(textnorm.squeeze_views, text) < 5.0
    assert _seconds(lambda t: textnorm.squeeze_views(t, loose=True), text) < 5.0


def test_scan_needles_and_the_script_views_of_a_text_at_the_cap_are_built_in_linear_time():
    """fix7 (round 7): the cost of a scan at the cap with the script views really built. The unit (an ideograph, a Latin t with a stroke, a Greek
    capital Nu, U+0345 and a spacing mark) makes SEVEN views of ``fold_views`` with the scripts of the value (three spelling variants, the same
    three without the spacing mark, and the script view): the highest count found, so the most work per call that this package knows of (nine is the
    bound, not reached). The old marks row used a Cyrillic a, so its script view was empty. The value is the text itself, so ``scan_needles`` builds
    its views and the squeeze views too. Ceiling: about 8 times the time measured on the build machine."""
    unit = "\u5bc6\u2c66\u039d\u0345\u0903"
    text = unit * (CAP // textnorm._weight(unit))
    assert len(text) <= CAP and textnorm._weight(text) <= CAP, (
        "the row would be refused, not folded"
    )
    scripts = textnorm.value_scripts(unit)
    views = textnorm.fold_views(text, casefold=True, collapse_ws=True, scripts=scripts)
    assert len(views) == 7 and any(v and not v.isascii() and v.isalpha() for v in views), (
        "the row does not build the script view and the seven views"
    )
    assert all(len(v) <= textnorm._weight(text) for v in views)
    assert (
        _seconds(
            lambda t: textnorm.fold_views(t, casefold=True, collapse_ws=True, scripts=scripts),
            text,
        )
        < 5.0
    )
    assert _seconds(textnorm.scan_needles, text) < 8.0
    assert _seconds(textnorm.value_scripts, text) < 5.0
    assert textnorm.scan_needles(text), "the value was refused"

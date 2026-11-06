"""Timing rows of the text fold (marker ``perf``: CI runs them in their own step). They are NOT in any mutation test list, because the
runner does not copy ``pyproject.toml`` and the marker would be unregistered there. Ceilings are generous (about 20 times the time
measured on the build machine) and say what the row is about."""

import os
import time

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.textnorm import TextTooLong, has_hidden_channel, identity_key, squeeze

pytestmark = pytest.mark.perf
CAP = defaults.TEXTNORM_MAX_CHARS


def _record(name, seconds):
    """Print the time of one call and, when the environment names a file (``HADAVIN_PERF_LOG``), append it there as ``name seconds`` so a run
    leaves its per-call numbers behind (the ceilings below are only the gate)."""
    print(f"perf {name}: {seconds:.4f} s")
    path = os.environ.get("HADAVIN_PERF_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write(f"{name} {seconds:.6f}\n")


def _fold_views_plain(raw):
    """``fold_views`` of a text with no protected value (``scripts`` is a required keyword)."""
    return textnorm.fold_views(raw, scripts=frozenset())


_fold_views_plain.__name__ = "fold_views"


def _seconds(fn, *args):
    """The time of ``fn(*args)``. A refusal (``TextTooLong``) is NOT swallowed: a row that is meant to time the real fold fails if its text is refused."""
    start = time.perf_counter()
    fn(*args)
    took = time.perf_counter() - start
    _record(getattr(fn, "__name__", "call"), took)
    return took


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


# ---- scan_keyset (P1b): evidence rows, printed with -s; the ceilings are generous and are not merge gates of the design ------------------
def test_s_call_the_worst_scan_keyset_call_at_the_size_rule():
    """S_call: capital Eta x CAP, Ze x CAP and a tag-heavy text, up to 8 key builds each (a reading is a bounded loop of linear passes)."""
    from hadavin_sdk.guard.textnorm import scan_keyset

    texts = {
        "eta": chr(0x397) * CAP,
        "ze": chr(0x437) * CAP,
        "tags": ("a" + chr(0xE0061)) * (CAP // 2),
    }
    for name, text in texts.items():
        took = _seconds(scan_keyset, text)
        print(f"S_call {name}: {took:.3f} s")
        assert took < 60.0, f"S_call {name} took {took:.1f} s"


def test_sk5_a_thousand_calls_on_twenty_character_texts():
    from hadavin_sdk.guard.textnorm import scan_keyset

    start = time.perf_counter()
    for i in range(1000):
        scan_keyset(f"ba{i % 10}nk\u200b12345 {chr(0x437)}x{i % 7}")
    took = time.perf_counter() - start
    print(f"SK-5: 1000 calls in {took:.3f} s")
    assert took < 10.0


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
        _fold_views_plain,
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
    for fn in (identity_key, textnorm.identity_keys, _fold_views_plain, textnorm.squeeze_views):
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
    for fn in (identity_key, textnorm.identity_keys, _fold_views_plain, textnorm.squeeze_views):
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
    views = textnorm.fold_views(text, casefold=True, scripts=frozenset())
    assert 2 <= len(views) <= 9
    assert all(len(v) <= textnorm._weight(text) for v in views)
    assert (
        _seconds(lambda t: textnorm.fold_views(t, casefold=True, scripts=frozenset()), text) < 5.0
    )
    assert _seconds(textnorm.squeeze_views, text) < 5.0
    assert _seconds(lambda t: textnorm.squeeze_views(t, loose=True), text) < 5.0


def test_the_deny_check_of_a_text_at_the_cap_with_spacing_marks_stays_within_its_ceiling_and_a_text_without_marks_is_not_slower():
    """F6-1 and F6-1b: the check names read the marks-dropped text too, but only when the text (or its NFKD text) holds a spacing mark. A text
    at the cap WITH marks stays under the ceiling of 8 s; the same-size text WITHOUT marks is no more than 2.5 times the time of the one with
    them (it makes fewer readings, so a gate that did all the work twice for every text would break this on a slow day only by chance: the
    wall-clock ceiling is the real guard, this ratio is a sanity bound)."""
    unit = "pass" + chr(0x0903) + chr(0x02C6) + chr(0x02C2) + "word " + chr(0x430)
    marked = unit * (CAP // textnorm._weight(unit))
    plain = ("password " + chr(0x430)) * (CAP // textnorm._weight("password " + chr(0x430)))
    assert textnorm._weight(marked) <= CAP and textnorm._weight(plain) <= CAP
    with_marks = _seconds(textnorm.could_be_same_person, marked, marked[::-1])
    without = _seconds(textnorm.could_be_same_person, plain, plain[::-1])
    assert with_marks < 8.0, with_marks
    assert without < 8.0 and without <= 2.5 * with_marks + 0.05, (without, with_marks)


def test_scan_needles_and_the_script_views_of_a_text_at_the_cap_are_built_in_linear_time():
    """The cost of a scan at the cap with the script views really built. The unit (an ideograph, a Latin t with a stroke, a Greek
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
    # ``== 7`` is kept on purpose: it pins that this row builds the highest count found (the search is saved with the evidence; the maximum of
    # 150,000 random texts was seven for ``fold_views``). If a change of the fold alters the count, this fails loudly and the row must be re-made
    # for the new maximum, rather than silently timing a lighter case.
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


# ---- the DENY scan at the cap (fix batch): scan_views, scan_holds, the one-inserted-letter match and the injection check --------------------
def _cap_text(unit):
    text = unit * (CAP // textnorm._weight(unit))
    assert len(text) <= CAP and textnorm._weight(text) <= CAP, (
        "the row would be refused, not scanned"
    )
    return text


def test_scan_views_of_a_text_at_the_cap_is_built_in_linear_time():
    """``scan_views`` with a value (all views, scripts of the value) and without one (the injection check's case). Ceiling: about 20 times the time
    measured on the build machine."""
    unit = "\u5bc6\u2c66\u039d\u0345\u0903"
    text = _cap_text(unit)
    views = textnorm.scan_views(text, unit)
    assert 3 <= len(views) <= 31
    assert _seconds(lambda t: textnorm.scan_views(t, unit), text) < 10.0
    assert _seconds(lambda t: textnorm.scan_views_no_value(t), text) < 10.0


def test_scan_holds_of_a_text_at_the_cap_for_a_latin_and_for_a_script_value():
    """The exact scan (no hit) for a Latin value and for a Chinese value, at the cap."""
    text = _cap_text("pass\u0903word \u5bc6\u7801 ")
    assert textnorm.scan_holds(text, "password")
    assert _seconds(lambda t: textnorm.scan_holds(t, "no-such-value"), text) < 10.0
    assert _seconds(lambda t: textnorm.scan_holds(t, "\u4e2d\u6587\u6d4b\u8bd5\u4fdd"), text) < 10.0


def test_the_one_inserted_letter_match_is_linear_for_a_text_built_to_defeat_it():
    """The worst case of the matcher: the text is copies of the first half of the longest needle, so every position is a hit of the intact
    half (one letter repeated). The work is bounded (``tests/test_textnorm_fixbatch.py`` counts the comparisons); this row times it at the cap with the longest needle."""
    top = defaults.TEXTNORM_INSERTION_MAX_CHARS
    first = chr(0x5000) * (
        top // 2
    )  # one repeated letter: the intact half is a hit at EVERY position of the text
    second = chr(0x6000) * (top - top // 2)
    needle = first + second
    text = chr(0x5000) * CAP
    assert len(text) <= CAP
    assert textnorm.scan_holds(text, needle) is False
    assert _seconds(lambda t: textnorm.scan_holds(t, needle), text) < 20.0
    assert (
        _seconds(lambda t: textnorm.scan_holds(t, first[:1] + chr(0x4FFF) + needle[1:]), text)
        < 20.0
    )


def test_a_hundred_values_against_one_text_at_the_cap_cost_one_text_pass():
    """The cache of the text's views: 100 values scanned against one text at the cap take about the time of the first value, plus a small
    amount per value (not 100 times the first)."""
    text = _cap_text("pass\u0903word \u5bc6\u7801 abc ")
    # The views are shared only inside ``scan_cache()``: outside a scope nothing is kept between calls, by design (the views are as sensitive as the
    # text), and every call costs a full text pass. The scope is the documented way to scan one text for many values.
    with textnorm.scan_cache():
        first = _seconds(lambda t: textnorm.scan_holds(t, "value-000-none"), text)
        start = time.perf_counter()
        for i in range(1, 100):
            textnorm.scan_holds(text, f"value-{i:03d}-none")
        took = time.perf_counter() - start
    _record("scan_holds 99 more values", took)
    assert took < 10 * max(first, 0.05) + 5.0, (
        f"99 values took {took:.2f} s, the first {first:.2f} s"
    )


def test_the_injection_check_of_a_text_at_the_cap():
    """``RegexDetector._score`` reads the text and its ``scan_views`` (no value): at the cap it must stay linear."""
    from hadavin_sdk.guard import injection

    detector = injection.RegexDetector(0.5)
    for name, unit in (
        ("ascii", "plain words in a log line "),
        ("marks", "pass\u0903word \u0436 "),
    ):
        text = _cap_text(unit)
        assert _seconds(lambda t: detector.check(t, "perf"), text) < 10.0, name

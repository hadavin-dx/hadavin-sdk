"""Pins of the limits of ``textnorm.has_mixed_script`` (review-code-F-gate-3 m-4, ORDER 020).

MEASURED ANSWER (run on Python 3.13, Unicode 15.1.0, confusables table of 15.1.0, 852 entries) to the lead's open question
"Han and kana look-alikes of Latin letters, if any, would pass as not mixed":
  Of the code points of the exempt scripts (Han, Hiragana, Katakana, Hangul, Bopomofo) that have a Latin look-alike entry in
  ``guard/_confusables.TABLE``, there is exactly ONE: U+3007 IDEOGRAPHIC NUMBER ZERO (script Han) -> "O".
  Hiragana: 0, Katakana: 0, Hangul: 0, Bopomofo: 0.
  A Latin word with U+3007 inside ("pay" + U+3007 + "al") passes as NOT mixed (Han is exempt with Latin). The test
  ``test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed`` PINS that limit: only the look-alike check (the fold and the
  table, not this signal) can catch it. If a regenerated table adds more such code points, the completeness test names them.
"""

from __future__ import annotations

import unicodedata

import pytest

from hadavin_sdk.guard import _confusables, textnorm
from hadavin_sdk.guard.textnorm import has_mixed_script

MICRO = "µ"
OHM = "Ω"
CYR_A = "а"  # CYRILLIC SMALL LETTER A
EXEMPT = ("Han", "Hiragana", "Katakana", "Hangul", "Bopomofo")
# measured (see the top of the file): the exempt-script code points with a Latin look-alike entry
MEASURED = {"Han": [0x3007], "Hiragana": [], "Katakana": [], "Hangul": [], "Bopomofo": []}


def test_micro_sign_plus_latin_letters_is_not_mixed():
    # docstring: "The micro sign and the ohm sign are exempt (unit symbols)": removed before the analysis.
    assert has_mixed_script(MICRO + "abc") is False
    assert has_mixed_script("5 " + MICRO + "s") is False


def test_micro_sign_plus_latin_plus_cyrillic_is_mixed_because_of_the_latin_and_cyrillic_letters():
    # TRUE behaviour today: True. The micro sign is dropped first (docstring: "The micro and ohm signs are removed BEFORE the analysis"),
    # so the word is "abc" + Cyrillic a, and Latin next to Cyrillic is rule (a). The sign adds nothing and hides nothing.
    assert has_mixed_script(MICRO + "abc" + CYR_A) is True
    assert has_mixed_script("abc" + CYR_A) is True


def test_micro_sign_plus_cyrillic_only_is_not_flagged():
    # docstring: "a word that holds only such a sign plus a look-alike letter (micro sign + Cyrillic a) is not flagged by this function;
    # the fold and the table still see the Cyrillic letter."
    assert has_mixed_script(MICRO + CYR_A) is False


def test_a_greek_mu_typed_as_a_greek_letter_next_to_latin_is_flagged_unlike_the_micro_sign():
    # docstring: "a Greek mu or omega typed as a Greek letter next to Latin letters is flagged".
    assert has_mixed_script("μ" + "abc") is True
    assert has_mixed_script("Ω" + "abc") is True
    assert has_mixed_script(MICRO + "abc") is False


def test_ohm_sign_cases():
    assert has_mixed_script(OHM + "abc") is False  # removed before the check
    assert has_mixed_script("50 k" + OHM) is False
    assert has_mixed_script(OHM + "abc" + CYR_A) is True  # the Latin+Cyrillic pair still counts
    assert (
        has_mixed_script(OHM + CYR_A) is False
    )  # only the sign plus a look-alike: same as the micro sign
    assert has_mixed_script("abc" + "Ω") is True  # the real Greek capital omega is NOT exempt


def test_the_two_unit_symbols_are_exactly_micro_and_ohm():
    assert textnorm._UNIT_SYMBOLS == frozenset({MICRO, OHM})


def test_a_code_point_newer_than_unicode_15_1_0_counts_as_neutral():
    # docstring: "A code point added to Unicode after the pinned version is not in the data and counts as neutral."
    # U+1C89 CYRILLIC CAPITAL LETTER TJE is new in Unicode 16.0; U+10D40 GARAY DIGIT ZERO is new in 16.0 as well.
    assert unicodedata.unidata_version >= "15.1.0"
    for cp in (0x1C89, 0x1C8A, 0x10D4A):
        ch = chr(cp)
        if unicodedata.unidata_version <= "15.1.0":
            assert unicodedata.category(ch) == "Cn"  # not assigned in this interpreter
        assert textnorm._script(ch) is None  # not in the pinned Scripts data
        assert has_mixed_script("abc" + ch) is False
        assert (
            has_mixed_script("abc" + ch + "def") is False
        )  # whether or not the interpreter calls it a letter


def test_the_check_uses_script_not_script_extensions():
    # docstring: "rule (a) uses the Script property, not Script_Extensions": U+0640 ARABIC TATWEEL is Script=Common (scx Arabic, Syriac, ...).
    tatweel = "ـ"
    assert unicodedata.category(tatweel) == "Lm"
    assert textnorm._script(tatweel) is None
    assert has_mixed_script("abc" + tatweel + "def") is False
    # contrast: a letter whose Script is Arabic is flagged
    assert has_mixed_script("abc" + "ا") is True


def _exempt_with_latin_lookalike(script: str) -> list[int]:
    return sorted(cp for cp in _confusables.TABLE if textnorm._script(chr(cp)) == script)


@pytest.mark.parametrize("script", EXEMPT)
def test_the_list_of_exempt_script_code_points_with_a_latin_lookalike_is_the_measured_one(script):
    found = _exempt_with_latin_lookalike(script)
    assert found == MEASURED[script], (
        f"{script}: the confusables table now lists {[hex(c) for c in found]}, measured {[hex(c) for c in MEASURED[script]]}: "
        "decide for each new code point what has_mixed_script says and pin it"
    )


@pytest.mark.parametrize("script", EXEMPT)
def test_every_listed_lookalike_of_an_exempt_script_is_pinned_as_not_mixed_in_a_latin_word(script):
    for cp in _exempt_with_latin_lookalike(script):
        for word in ("pay" + chr(cp) + "al", chr(cp) + "pay", "pay" + chr(cp)):
            assert has_mixed_script(word) is False  # the pinned limit: exempt script next to Latin


def test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed():
    # THE LIMIT (measured): U+3007 looks like "O" (table entry) and Han is exempt, so a Latin word using it is not flagged by this
    # function. Other protections (fold + look-alike table) must catch a known value written with it.
    ch = "〇"
    assert _confusables.TABLE[0x3007] == "O"
    assert textnorm._script(ch) == "Han"
    assert has_mixed_script("L" + ch + "gin") is False
    assert has_mixed_script("R" + ch + "OT") is False


def test_table_and_script_data_are_the_pinned_version():
    assert _confusables.DATA_VERSION == "15.1.0"

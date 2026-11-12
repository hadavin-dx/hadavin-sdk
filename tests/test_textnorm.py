"""The shared text fold (``hadavin_sdk.guard.textnorm``): the moved controls, the new input rules, the version string, the hidden channel.

Look-alikes are built with ``chr()``. No wall-clock assertions: timing rows live in ``tests/test_textnorm_perf.py`` (marker ``perf``), which
no mutation run lists. Facts of one Unicode version (entry counts, digit counts) are never written here: the tests state properties that
hold on every interpreter. The assertions a mutant must trip carry a message; the mutant list (``tests/textnorm_mutants.py``) names a
fragment of that message, so a message is never reworded without the list.
"""

import ast
import enum
import functools
import hashlib
import html
import importlib.util
import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import _confusables, textnorm
from hadavin_sdk.guard.textnorm import (
    FILLERS,
    FOLD_VERSION,
    AllowVerdict,
    NotText,
    TextnormError,
    TextTooLong,
    UnidataMismatch,
    allow_equal,
    could_be_same_person,
    fold,
    has_hidden_channel,
    has_mixed_script,
    identity_key,
    key_tag,
    names_equal,
    require_pinned_unidata,
    squeeze,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
CAP = defaults.TEXTNORM_MAX_CHARS
SSS = chr(0x1F75C)  # weight 3: its fold is three letters (the one table value of length 3)
FDFA = chr(0xFDFA)  # weight 18: NFKC makes 18 characters from it
# The two coverage sentences. Each must stand WORD FOR WORD (whitespace aside) in every place that states it.
SCAN_COVERAGE = (
    "A value with NO ASCII letter or digit (Chinese, Arabic, Hindi, Thai) is found by the script views of ``fold_views`` (the non-ASCII letters of the "
    "value's own scripts, with whitespace, punctuation, symbols, ASCII characters and the letters of every other script removed), so an inserted "
    "space, hyphen, line break, ASCII letter, mark or foreign-script letter does not hide it."
)
NAME_COVERAGE = (
    "NAME RULES COVER: small capitals, negative circled and negative squared letters, the crossed negative squared P, regional indicator letters, "
    "the squared small d, Latin letters with a stroke, hook or similar mark, and the circled, negative circled, double circled and sans-serif digits "
    "and numbers (0 to 10); the circled numbers 11 to 20 are read by NFKC, the negative circled numbers 11 to 20 are not read (a named gap)."
)


def _squash(text):
    """``text`` with every run of whitespace (a line break inside a docstring) as one space."""
    return " ".join(text.split())


def bare(key):
    """A key without the tag of an interpreter whose Unicode version is not the pin (``key_tag()`` is empty on the pinned version)."""
    return key.removeprefix(key_tag())


def _fold_views_no_scripts(raw):
    """``fold_views`` for a text with no protected value (``scripts`` is a required argument)."""
    return textnorm.fold_views(raw, scripts=frozenset())


_fold_views_no_scripts.__name__ = "fold_views"


def refused(exc, message, fn, *args, **kwargs):
    """Call ``fn``; it must raise ``exc``. Anything else fails with ``message`` as the first line of the report."""
    try:
        fn(*args, **kwargs)
    except exc:
        return
    except Exception as other:  # noqa: BLE001 - reported with its class as the failure
        raise AssertionError(f"{message} (raised {type(other).__name__} instead)") from None
    raise AssertionError(message)


def accepted(message, fn, *args, **kwargs):
    """Call ``fn``; it must NOT raise a ``TextnormError``. A refusal fails with ``message`` as the first line of the report."""
    try:
        return fn(*args, **kwargs)
    except TextnormError as refusal:
        raise AssertionError(f"{message} (raised {type(refusal).__name__})") from None


def _numbers(seed):
    """Integer arithmetic only (a linear congruential generator), so the rows are the same on every interpreter."""
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % (2**31)
        yield state >> 8


# ---- one text fold: the moved controls ---------------------------------------------------------------------------------------------------
def test_fold_is_stable_under_combining_marks_format_unassigned_and_tag_characters():
    marks = [chr(0x301), chr(0x300), chr(0x200B), chr(0xFE0F), chr(0x3164), chr(0x202E), chr(0xAD), chr(0xE000), chr(0xE0002), chr(0xE0000),
             chr(0x2065), chr(0xFFF0)]  # fmt: skip
    alphabet = "abcXYZ019 -."
    nxt = _numbers(7)
    for _ in range(300):
        x = "".join(alphabet[next(nxt) % len(alphabet)] for _ in range(next(nxt) % 13))
        for m in marks:
            assert fold(x + m) == fold(x) == fold(m + x), f"mark U+{ord(m):04X} changes the fold"
    assert fold("admin" + chr(0xE0002)) == fold("admin"), (
        "the same-looking name is not the same person"
    )


def test_fold_covers_the_listed_look_alikes_and_all_map_to_ascii():
    listed = {0x405: "S", 0x406: "I", 0x408: "J", 0x423: "Y", 0x41E: "O", 0x455: "s", 0x3B9: "i", 0x3BA: "k", 0x3C1: "p", 0x3C4: "t",
              0x3C5: "u", 0x3C7: "x", 0x501: "d", 0x131: "i", 0x130: "I", 0x585: "o", 0x57D: "u", 0x555: "O", 0x54D: "U", 0x3BF: "o",
              0x433: "r", 0x3B7: "n", 0x3B3: "y", 0x3BC: "u", 0x3C9: "w", 0x461: "w", 0x581: "g", 0x251: "a", 0xF8: "o", 0x142: "l", 0x111: "d",
              0x1D0F: "o", 0x1D21: "w", 0x417: "3", 0x437: "3", 0x3B5: "e", 0x261: "g"}  # fmt: skip
    for cp, latin in listed.items():
        assert fold(chr(cp)) == latin, f"look-alike U+{cp:04X} is not folded to {latin}"
    assert all(
        re.fullmatch("[A-Za-z0-9]+", v) and v.isascii() for v in textnorm._LOOKALIKES.values()
    )
    assert fold(chr(0x661) + chr(0x662) + chr(0xFF13)) == "123", (
        "other-script digits are not folded"
    )
    assert fold("a\nb\tc") == "a b c"
    for sp in (0x85, 0x1C, 0x1F, 0x2028, 0x2029, 0xA0, 0x3000, 0x2003):
        assert fold("ab" + chr(sp) + "cd") == "ab cd", hex(sp)
    assert squeeze("AB-12 3" + chr(0x200B) + "4") == squeeze("ab1234")
    assert squeeze("O0Il1", loose=True) == "00111"
    assert not any(
        unicodedata.category(c) in ("Cc", "Cf") for c in fold("x" + chr(0x200B) + chr(0x202E))
    )


def test_the_digit_table_is_complete_at_import():
    scanned = {
        cp
        for cp in range(sys.maxunicode + 1)
        if chr(cp).isdecimal() and not ("0" <= chr(cp) <= "9")
    }
    assert (
        set(textnorm._DIGITS) == scanned
    )  # the table is built once at import: no lazy fill to race on
    assert textnorm._DIGITS[0x661] == "1" and len(textnorm._DIGITS) > 400
    assert all(textnorm._DIGITS[cp] == str(int(chr(cp))) for cp in scanned)


def test_allow_decisions_are_exact_and_a_look_alike_is_reported_as_one():
    real, spoof = "alice@bank.example", "alice@bank.ex" + chr(0x430) + "mple"
    assert fold(real) == fold(spoof)  # DENY direction: the same person
    assert could_be_same_person(real, spoof), "could_be_same_person does not fold a look-alike"
    assert allow_equal(real, real) is AllowVerdict.EQUAL
    assert allow_equal(real, spoof) is AllowVerdict.LOOKALIKE, "a look-alike is not reported as one"
    assert allow_equal("alice", "bob") is AllowVerdict.DIFFERENT, (
        "an ordinary mismatch is not DIFFERENT"
    )
    # every pair that NFKC + casefold + whitespace used to call equal is NOT equal for an ALLOW
    pairs = [
        (chr(0xFF20), "@"),  # fullwidth at-sign
        ("stra" + chr(0xDF) + "e.de", "strasse.de"),  # sharp s versus ss: two different domains
        (chr(0xFB01) + "le", "file"),  # fi ligature
        (" alice@bank.example", "alice@bank.example"),
        ("alice@bank.example ", "alice@bank.example"),
        ("Alice@Bank.example", "alice@bank.example"),
        ("a  b", "a b"),
    ]
    for x, y in pairs:
        verdict = allow_equal(x, y)
        assert verdict is AllowVerdict.VARIANT, (
            f"variant pair {x!r} {y!r} gave {verdict.name}, wanted VARIANT"
        )  # refused, but not a spoof alarm
        assert could_be_same_person(x, y), f"could_be_same_person does not fold {x!r} and {y!r}"
        assert names_equal(x, y), (x, y)  # the name comparison stays tolerant, and is not an ALLOW
    assert not names_equal("alice", "bob") and not could_be_same_person("alice", "bob")
    assert could_be_same_person(real, spoof) and not names_equal(real, spoof)
    refused(
        TypeError,
        "an AllowVerdict has a truth value",
        bool,
        allow_equal(real, real),
    )  # 'if allow_equal(a, b):' would always be true: it is refused instead
    refused(
        TypeError, "an AllowVerdict has a truth value (not)", lambda: not allow_equal(real, spoof)
    )
    assert allow_equal("a" + chr(0x200B), "a") is AllowVerdict.LOOKALIKE, (
        "an invisible character is not reported as a spoof"
    )
    assert allow_equal("alice@bank.example", spoof) is not AllowVerdict.EQUAL
    assert allow_equal("", "") is AllowVerdict.EQUAL


def test_mixed_script_is_a_fail_closed_deny_signal():
    for word in ("al" + chr(0x456) + "ce", "bank" + chr(0x3B7) + "x", "a" + chr(0x581)):
        assert has_mixed_script(word), f"a mixed word {word!r} is not flagged"
    assert not has_mixed_script("alice")
    assert not has_mixed_script(chr(0x430) + chr(0x43B) + chr(0x438))
    assert not has_mixed_script("INV-2026 " + chr(0x65E5))


def test_one_invisible_character_cannot_split_a_mixed_script_word():
    cher_a = chr(0x13AA)
    assert has_mixed_script("b" + cher_a + "nk"), "Cherokee next to Latin is not flagged"
    for invisible in (
        chr(0x200B),
        chr(0x301),
        chr(0xAD),
        chr(0x2060),
        chr(0xE0002),
        chr(0x3164),
        chr(0xFE0F),
    ):
        assert has_mixed_script("b" + invisible + cher_a + invisible + "nk"), (
            f"U+{ord(invisible):04X} splits a mixed word"
        )
    assert not has_mixed_script(cher_a + chr(0x13A0))  # one script


def test_the_micro_and_ohm_signs_are_unit_symbols_not_a_mixed_script():
    assert not has_mixed_script(
        "5 " + chr(0xB5) + "s and 50 k" + chr(0x2126) + " and 3 " + chr(0xB5) + "g"
    ), "a micro or ohm sign is flagged"
    assert has_mixed_script(
        "m" + chr(0x3BC) + "s"
    )  # a Greek mu typed as a letter inside Latin text is flagged


def _decode(s):
    return re.sub(r"\{U\+([0-9A-Fa-f]{4,6})\}", lambda m: chr(int(m[1], 16)), s)


VECTORS = json.loads((FIX / "textnorm_vectors.json").read_text(encoding="utf-8"))


def test_vectors_ids_with_homoglyphs_fold_to_the_real_id():
    for case in VECTORS["identities"]:
        real = fold(case["id"], casefold=True, collapse_ws=True)
        for variant in case["variants"]:
            assert fold(_decode(variant), casefold=True, collapse_ws=True) == real, (
                case["id"],
                variant,
            )
        for other in case.get("different", []):
            assert fold(_decode(other), casefold=True, collapse_ws=True) != real, (
                case["id"],
                other,
            )


def test_vectors_domains_with_cyrillic_and_greek_letters_fold_to_the_ascii_domain_but_are_lookalikes():
    for case in VECTORS["domains"]:
        for variant in case["variants"]:
            v = _decode(variant)
            assert fold(v, casefold=True) == case["domain"], (case["domain"], variant)
            assert allow_equal(v, case["domain"]) is AllowVerdict.LOOKALIKE, variant


def test_a_newline_or_tab_separates_words_in_the_mixed_script_check():
    ru = "".join(map(chr, (0x43F, 0x440, 0x438, 0x432, 0x435, 0x442)))
    ru_name = chr(0x418) + chr(0x43C) + chr(0x44F)
    for sep in ("\n", "\t", "\r\n", chr(0x2028), "\x0b"):
        assert not has_mixed_script("ab" + sep + ru), f"{sep!r} joins the words of the script check"
    assert not has_mixed_script("Name\t" + ru_name)
    assert has_mixed_script(
        "ab" + chr(0x200B) + ru
    )  # a zero-width space INSIDE a word does not split it
    assert has_mixed_script("b" + chr(0x200B) + chr(0x13AA) + "nk")


# ---- squeeze, fillers, unassigned code points ---------------------------------------------------------------------------------------------
def test_squeeze_loose_reads_the_digit_like_letters_as_digits():
    assert squeeze("SBZGQ", loose=True) == "58269", "the loose map is short"
    assert squeeze("OIL", loose=True) == "011"
    assert squeeze("SBZGQ") == "SBZGQ"  # without ``loose`` the letters stay letters


def test_squeeze_keeps_upper_case_letters_and_digits_only():
    assert squeeze("a.b-c_d" + chr(0xFFFD) + "e") == "ABCDE", "squeeze lost a letter"
    assert squeeze("a1") == "A1", "squeeze removed a digit"
    refused(NotText, "squeeze accepted bytes", squeeze, b"x")
    refused(TextTooLong, "squeeze accepted a text over the size rule", squeeze, "a" * (CAP + 1))
    refused(NotText, "squeeze(loose) accepted bytes", squeeze, b"x", loose=True)


def test_every_filler_is_dropped_and_every_filler_named_letter_is_listed():
    for c in sorted(FILLERS):
        assert fold("a" + c + "b") == "ab", f"filler U+{ord(c):04X} is kept"
    named = []
    for cp in range(sys.maxunicode + 1):
        c = chr(cp)
        if unicodedata.category(c) == "Cn":
            continue
        name = unicodedata.name(c, "")
        if ("FILLER" in name or "BLANK" in name) and c.isalnum():
            named.append(c)
    print(
        "filler or blank letters of this interpreter:", " ".join(f"U+{ord(c):04X}" for c in named)
    )
    assert named, "the scan found no blank-named letter at all: the predicate is broken"
    assert set(named) <= FILLERS, (
        f"not in FILLERS: {[hex(ord(c)) for c in named if c not in FILLERS]}"
    )
    assert chr(0x13441) in FILLERS and chr(0x13442) in FILLERS


def test_an_unassigned_code_point_is_dropped_before_anything_else():
    pick = next(
        cp
        for cp in range(0x378, sys.maxunicode + 1)
        if unicodedata.category(chr(cp)) == "Cn"
        and (cp & 0xFFFE) != 0xFFFE
        and not 0xFDD0 <= cp <= 0xFDEF
        and cp not in _confusables.TABLE
    )
    assert fold("a" + chr(pick) + "b") == "ab", f"unassigned U+{pick:04X} is kept"
    assert bare(identity_key("a" + chr(pick) + "b")) == "ab"


def test_the_empty_and_invisible_only_texts_have_the_empty_key():
    assert bare(identity_key("")) == "" and fold("") == ""
    assert bare(identity_key(chr(0x200B) + chr(0x200C))) == ""
    assert bare(identity_key(" \t\n")) == ""
    assert not hasattr(textnorm, "fold_key"), "the old alias fold_key is back"


# ---- the tables --------------------------------------------------------------------------------------------------------------------------
def _assign(table, key):
    table[key] = "x"


def _delete(table, key):
    del table[key]


def test_the_tables_are_read_only_and_a_later_change_of_the_source_does_not_reach_fold(monkeypatch):
    for name in ("_TABLE", "_LOOKALIKES", "_DIGITS", "_LOOSE"):
        table = getattr(textnorm, name)
        key = next(iter(table))
        refused(TypeError, f"{name} accepts an assignment", _assign, table, key)
        refused(TypeError, f"{name} accepts a delete", _delete, table, key)
    before = fold(chr(0x430))
    monkeypatch.setitem(_confusables.TABLE, 0x430, "z")
    monkeypatch.setitem(_confusables.TABLE, 0x2013, "q")
    assert fold(chr(0x430)) == before == "a", "a later change of _confusables.TABLE changes fold"
    assert fold(chr(0x2013)) == "-", (
        "a later change of _confusables.TABLE changes the punctuation map"
    )


def test_the_checked_in_table_matches_its_digest():
    table = _confusables.TABLE
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    assert hashlib.sha256(lines.encode("utf-8")).hexdigest() == _confusables.TABLE_DIGEST, (
        "the checked-in table does not match TABLE_DIGEST: regenerate it"
    )
    assert re.fullmatch("[0-9a-f]{64}", _confusables.TABLE_DIGEST)
    assert _confusables.ENTRIES == len(table), "ENTRIES is not the size of the table"
    assert len(table) > 0


def test_max_value_len_is_the_longest_value_of_the_table():
    longest = max(len(v) for v in _confusables.TABLE.values())
    assert _confusables.MAX_VALUE_LEN == longest, "MAX_VALUE_LEN is not the table maximum"
    assert len(fold(SSS)) == _confusables.MAX_VALUE_LEN, "the longest value is not made by U+1F75C"


# ---- FOLD_VERSION ------------------------------------------------------------------------------------------------------------------------
def test_the_version_string_names_the_algorithm_the_table_and_both_unicode_versions():
    m = re.fullmatch(r"alg=fold5\|tbl=([0-9a-f]{12}):(\d+)\|ucd=([^|]+)\|ud=([^|]+)", FOLD_VERSION)
    assert m, f"FOLD_VERSION has the wrong shape: {FOLD_VERSION}"
    assert m[4] == unicodedata.unidata_version, "FOLD_VERSION has no ud= part of this interpreter"
    assert m[3] == _confusables.DATA_VERSION
    live = textnorm._table_digest(textnorm._TABLE)
    assert m[1] == live[:12] and int(m[2]) == len(textnorm._TABLE), "tbl= is not the live table"
    assert "beh=" not in FOLD_VERSION


def test_a_changed_table_gives_another_version_string_without_reloading_the_module(monkeypatch):
    patched = dict(_confusables.TABLE)
    patched[0x430] = "b"
    monkeypatch.setattr(_confusables, "TABLE", patched)
    spec = importlib.util.spec_from_file_location("_textnorm_probe", textnorm.__file__)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)  # a private copy: the module the other tests use is not reloaded
    assert probe.FOLD_VERSION != FOLD_VERSION, "a changed table keeps the version string"
    assert probe.fold(chr(0x430)) == "b"
    assert fold(chr(0x430)) == "a"


# ---- idempotence and case symmetry, for every code point and for pairs ---------------------------------------------------------------------
def _non_surrogates():
    return (chr(cp) for cp in range(sys.maxunicode + 1) if not 0xD800 <= cp <= 0xDFFF)


def _pairs():
    """Every ordered two-character string over the keys of the look-alike table, the characters of its values, a combining mark and a space."""
    alphabet = [chr(cp) for cp in _confusables.TABLE]
    alphabet += sorted(set("".join(_confusables.TABLE.values())))
    alphabet += [chr(0x301), " "]
    return (a + b for a in alphabet for b in alphabet)


def _not_idempotent(texts):
    bad = []
    for t in texts:
        key = identity_key(t)
        if (
            key != t and identity_key(key) != key
        ):  # a key equal to the text is trivially a fixed point (only a speed-up)
            bad.append(t)
    return bad


def _case_asymmetric(texts, key=None):
    key = key or identity_key
    return [
        t for t in texts if (u := t.upper()) != (l := t.lower()) and key(u) != key(l)
    ]  # u == l: nothing to compare


def _show(texts):
    return [" ".join(f"U+{ord(ch):04X}" for ch in t) for t in texts[:5]]


YPOGEGRAMMENI = "\u0345"  # COMBINING GREEK YPOGEGRAMMENI: the one mark that is an iota after a Greek letter (module docstring)


# written out here, not read from the module under test (a fault in the module's sets must not change the test)
_TEST_DROPPED = frozenset({"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"})


def _unattached_ypogegrammeni(text):
    """The exact shape that is not case symmetric: the NFKD text holds a U+0345 with no Greek letter before it (the characters the fold
    drops are skipped when looking). ``str.upper`` turns such a mark into the letter Iota while the fold removes it. A U+0345 that comes after
    a Greek letter is NOT this shape: it is symmetric (the iota rule of the reading ``identity_key`` is)."""
    last = ""
    for ch in unicodedata.normalize("NFKD", text):
        if ch == YPOGEGRAMMENI:
            if not (last and last.isalpha() and unicodedata.name(last, "").startswith("GREEK ")):
                return True
            last = "\u03b9"
            continue
        if ch.isspace() or (
            unicodedata.category(ch) not in _TEST_DROPPED and ord(ch) not in FILLER_CODE_POINTS
        ):
            last = ch
    return False


def _exempt_from_symmetry(text):
    """The stated exemption, narrowed in fix3: only a text with a U+0345 that has no Greek letter before it (``_unattached_ypogegrammeni``).
    A text with U+0345 after a Greek letter is not exempt. ``test_u0345_*`` pins what the fold does there."""
    return _unattached_ypogegrammeni(text)


def _unexpected_asymmetry(texts, key=None):
    """The case asymmetric texts that are NOT exempt, and the exempt ones that are asymmetric (the exemption must still be needed)."""
    bad = _case_asymmetric(texts, key)
    return [t for t in bad if not _exempt_from_symmetry(t)], [
        t for t in bad if _exempt_from_symmetry(t)
    ]


def test_identity_key_is_idempotent_for_every_code_point():
    bad = _not_idempotent(_non_surrogates())
    assert not bad, f"identity_key is not idempotent for {len(bad)} code points, first {_show(bad)}"


def test_identity_key_is_case_symmetric_for_every_code_point():
    bad, exempt = _unexpected_asymmetry(_non_surrogates())
    assert not bad, (
        f"identity_key is not case symmetric for {len(bad)} code points, first {_show(bad)}"
    )
    assert exempt == [YPOGEGRAMMENI], (
        f"the exemption of U+0345 is stale: the asymmetric exempt texts are {_show(exempt)}"
    )


def test_identity_key_is_idempotent_for_pairs_built_from_the_table():
    bad = _not_idempotent(_pairs())
    assert not bad, f"identity_key is not idempotent for {len(bad)} pairs, first {_show(bad)}"


def test_identity_key_is_case_symmetric_for_pairs_built_from_the_table():
    bad, _ = _unexpected_asymmetry(_pairs())
    assert not bad, f"identity_key is not case symmetric for {len(bad)} pairs, first {_show(bad)}"


def test_squeeze_is_case_symmetric_for_every_code_point():
    bad, _ = _unexpected_asymmetry(_non_surrogates(), squeeze)
    assert not bad, f"squeeze is not case symmetric for {len(bad)} code points, first {_show(bad)}"


def test_the_old_failures_are_gone_a_capital_o_stroke_and_the_small_one_are_one_person():
    assert could_be_same_person("B\u00d8B", "bob") and could_be_same_person("b\u00f8b", "BOB")
    assert bare(identity_key("\u00d8")) == bare(identity_key("\u00f8")) == "o", (
        "O with stroke is not case symmetric"
    )
    assert bare(identity_key("\u1f80")) == bare(identity_key("\u1f80".upper())), (
        "a Greek letter with iota is not case symmetric"
    )


# ---- marks, U+0345 and random strings (P1a fix2, review 2) ------------------------------------------------------------------------------
DROP_CATEGORIES = (
    "Cc",
    "Cf",
    "Mn",
    "Me",
    "Zl",
    "Zp",
    "Co",
    "Cs",
    "Cn",
)  # what the fold drops (whitespace among them turns into a space)
LATIN_BASES = (
    "a",
    "B",
    "i",
    "K",
    "z",
    "\u00df",
    "\u0130",
    "\u0131",
    "\u00d8",
    "\u00e6",
)  # a, B, i, K, z, sharp s, I dot, dotless i, O stroke, ae
GREEK_BASES = (
    "\u03b1",
    "\u0391",
    "\u03b9",
    "\u0399",
    "\u03c3",
    "\u03c2",
    "\u03a3",
    "\u03c9",
    "\u03a9",
    "\u03b7",
)  # alpha .. eta
BULK_BASES = (
    "a",
    "\u03b9",
    "\u0391",
)  # Latin a, Greek iota, Greek capital alpha: the bases of the runs below
BIG_CLASSES = (
    "Co",
    "Cn",
)  # 960,000 code points that no table, decomposition or case rule touches: checked in runs
KEY_FUNCTIONS = (("identity_key", identity_key), ("squeeze", squeeze))


def _assigned_drop_code_points():
    """Every code point of the drop categories except the two big classes (about 4,300)."""
    wanted = set(DROP_CATEGORIES) - set(BIG_CLASSES)
    return [chr(cp) for cp in range(sys.maxunicode + 1) if unicodedata.category(chr(cp)) in wanted]


def _bulk_drop_code_points():
    return [
        chr(cp) for cp in range(sys.maxunicode + 1) if unicodedata.category(chr(cp)) in BIG_CLASSES
    ]


def _breaks_a_key(mark, bases=LATIN_BASES + GREEK_BASES):
    """The (function, base, side) rows where ``mark`` next to a base changes the key. The only allowed difference is U+0345 AFTER a Greek base."""
    rows = []
    for name, fn in KEY_FUNCTIONS:
        for base in bases:
            want = fn(base)
            if fn(base + mark) != want and not (mark == YPOGEGRAMMENI and base in GREEK_BASES):
                rows.append((name, base, "suffix"))
            if fn(mark + base) != want:
                rows.append((name, base, "prefix"))
    return rows


def _run_breaks(marks):
    """True when a run of marks does not leave the key of its letters alone. Each mark ``m`` goes into the unit ``a m iota m`` and the units are
    joined, so it is the suffix and the prefix of a Latin letter (a) and of a Greek letter (iota): any mark that is not dropped, or that
    changes a neighbour, makes the key differ from the key of the plain letters repeated. One call per function for a run of 256 marks
    (the exact check over the other, 4,300, code points uses ten Latin and ten Greek bases)."""
    text = "".join(f"a{m}\u03b9{m}" for m in marks)
    for _, fn in KEY_FUNCTIONS:
        if fn(text) != fn("a\u03b9") * len(marks):
            return True
    return False


def test_every_drop_category_code_point_leaves_the_key_of_a_latin_or_greek_letter_unchanged():
    broken = {}
    for mark in _assigned_drop_code_points():
        rows = _breaks_a_key(mark)
        if rows:
            broken[mark] = rows
    bulk = _bulk_drop_code_points()
    for start in range(0, len(bulk), 256):
        run = bulk[start : start + 256]
        if _run_breaks(run):
            for mark in run:  # a run failed: find the code points one by one
                rows = _breaks_a_key(mark, BULK_BASES)
                if rows:
                    broken[mark] = rows
    shown = [(f"U+{ord(m):04X}", rows[0]) for m, rows in list(broken.items())[:5]]
    assert not broken, (
        f"a drop-category code point changes the key of a letter ({len(broken)} code points), first {shown}"
    )
    # all categories were visited: the two parts together are exactly the drop categories
    assert len(_assigned_drop_code_points()) + len(bulk) == sum(
        1 for cp in range(sys.maxunicode + 1) if unicodedata.category(chr(cp)) in DROP_CATEGORIES
    )


def test_the_big_classes_are_nothing_but_private_use_and_unassigned_code_points():
    assert {unicodedata.category(m) for m in _bulk_drop_code_points()} == set(BIG_CLASSES)
    assert 900_000 < len(_bulk_drop_code_points()) < 1_000_000, "the Unicode data changed shape"


def test_u0345_is_an_iota_after_a_greek_letter_and_is_removed_everywhere_else():
    # removed after a Latin (or any non-Greek) letter, a digit, a space, and at the start: the name is the same name
    assert identity_key("admin" + YPOGEGRAMMENI) == identity_key("admin"), (
        "U+0345 after a Latin letter changes the key"
    )
    assert bare(identity_key("admin" + YPOGEGRAMMENI)) == "admin"
    assert identity_key(YPOGEGRAMMENI + "admin") == identity_key("admin")
    assert could_be_same_person("admin" + YPOGEGRAMMENI, "admin") and could_be_same_person(
        "Admin" + YPOGEGRAMMENI, "ADMIN"
    )
    for text in (
        "a" + YPOGEGRAMMENI,
        "7" + YPOGEGRAMMENI,
        "\u0430" + YPOGEGRAMMENI,
        "a " + YPOGEGRAMMENI + "b",
        "a\n" + YPOGEGRAMMENI + "b",
    ):
        assert identity_key(text) == identity_key(text.replace(YPOGEGRAMMENI, "")), ascii(text)
    assert bare(identity_key(YPOGEGRAMMENI)) == "" and squeeze(YPOGEGRAMMENI) == ""
    # an iota after a Greek letter, with or without a mark that is dropped anywhere in between
    alpha_iota = identity_key("\u03b1\u03b9")
    assert bare(alpha_iota) == "ai"
    for text in (
        "\u03b1" + YPOGEGRAMMENI,
        "\u1fb3",
        "\u1fbc",
        "\u0391\u0399",
        "\u03b1\u0301" + YPOGEGRAMMENI,
        "\u03b1\u200b" + YPOGEGRAMMENI,
    ):
        assert identity_key(text) == alpha_iota, ascii(text)
        assert squeeze(text) == "AI", ascii(text)
    assert identity_key("\u03b1" + YPOGEGRAMMENI) != identity_key("\u03b1"), (
        "the one base + mark pair that differs"
    )
    assert bare(identity_key("\u03b1" + YPOGEGRAMMENI * 2)) == "aii", (
        "a run of marks after a Greek letter is a run of iotas"
    )
    assert identity_key("\u1f80".upper()) == identity_key("\u1f80"), (
        "a Greek letter with iota is not case symmetric"
    )
    # what is NOT promised, pinned so that a change is a decision: the text with U+0345 not after a Greek letter is not case symmetric
    assert bare(identity_key("\u0399")) == "i" and bare(identity_key(YPOGEGRAMMENI)) == ""
    assert _exempt_from_symmetry(YPOGEGRAMMENI) and not _exempt_from_symmetry("\u1fb3")


def test_u0345_after_every_greek_letter_is_case_symmetric_and_idempotent():
    greek = [  # the letters by name (U+0374 and U+037A are signs whose NFKD is not a Greek letter: the mark after them is removed)
        chr(cp)
        for cp in range(sys.maxunicode + 1)
        if unicodedata.name(chr(cp), "").startswith("GREEK")
        and " LETTER " in unicodedata.name(chr(cp))
    ]
    assert len(greek) > 300
    bad = [
        g + YPOGEGRAMMENI
        for g in greek
        if identity_key((g + YPOGEGRAMMENI).upper()) != identity_key((g + YPOGEGRAMMENI).lower())
        or squeeze((g + YPOGEGRAMMENI).upper()) != squeeze((g + YPOGEGRAMMENI).lower())
    ]
    assert not bad, (
        f"Greek letter + U+0345 is not case symmetric for {len(bad)} letters, first {_show(bad)}"
    )
    for g in greek:
        text = g + YPOGEGRAMMENI
        assert identity_key(identity_key(text)) == identity_key(text), (
            f"not idempotent: {_show([text])}"
        )
        assert squeeze(text) == squeeze(g) + "I", (
            f"Greek letter + U+0345 is not letter + iota: {_show([text])}"
        )


def test_other_dropped_characters_between_a_greek_letter_and_u0345_do_not_move_the_iota():
    marks = [m for m in _assigned_drop_code_points() if m != YPOGEGRAMMENI and not m.isspace()]
    assert len(marks) > 2000
    for base, want in (("\u03b1", "ai"), ("\u0391", "ai"), ("a", "a"), ("\u0430", "a")):
        for mark in marks:
            for text in (base + mark + YPOGEGRAMMENI, base + mark + mark + YPOGEGRAMMENI):
                assert bare(identity_key(text)) == want, (
                    f"a dropped character moves the iota: {_show([text])}"
                )
    # a space IS a base: the mark after a space has no letter before it
    assert bare(identity_key("\u03b1 " + YPOGEGRAMMENI)) == "a"


RANDOM_SEED = 20261106
# the invisible filler letters, written out here and not read from the module under test (a fault in that set must not change the test)
FILLER_CODE_POINTS = (0x3164, 0x115F, 0x1160, 0x2800, 0xFFA0, 0x13441, 0x13442)
RANDOM_STRINGS = 30_000
RANDOM_CLASSES = {
    "hangul jamo and fillers": [chr(c) for c in range(0x1100, 0x1200)]
    + [chr(c) for c in range(0x3131, 0x318F)]
    + [chr(c) for c in range(0xA960, 0xA97D)]
    + [chr(c) for c in range(0xD7B0, 0xD7FC)]
    + [chr(c) for c in FILLER_CODE_POINTS]
    + ["\u3164", "\uffa0"],
    "ligatures": [chr(c) for c in range(0xFB00, 0xFB07)]
    + [chr(c) for c in range(0xFB13, 0xFB18)]
    + list(
        "\u0132\u0133\u01c4\u01c5\u01c6\u01c7\u01c8\u01c9\u01ca\u01cb\u01cc\u00df\u1e9e\u00e6\u00c6\u0153\u0152\ufdfa\u2160\u2169"
    ),
    "dotted and dotless i": list("Ii\u0130\u0131\u0307"),
    "sigma": list("\u03a3\u03c3\u03c2"),
    "zero-width": [chr(c) for c in range(0x200B, 0x2010)]
    + [chr(c) for c in range(0x2060, 0x2065)]
    + list("\ufeff\u180e\u034f\u00ad\u2028\u2029"),
    "bidi": [chr(c) for c in range(0x202A, 0x202F)]
    + [chr(c) for c in range(0x2066, 0x206A)]
    + ["\u061c"],
    "variation selectors": [chr(c) for c in range(0xFE00, 0xFE10)]
    + list("\u180b\u180c\u180d\u180f")
    + [chr(c) for c in range(0xE0100, 0xE01F0, 7)],
    "tag characters": [chr(c) for c in range(0xE0000, 0xE0080)],
    "width forms": [chr(c) for c in range(0xFF01, 0xFF5F)]
    + [chr(c) for c in range(0xFF61, 0xFFDD)]
    + ["\u3000"],
    "greek, cyrillic and ypogegrammeni": list(
        "\u03b1\u0391\u03b7\u0397\u03b9\u0399\u03c9\u03a9\u0430\u0435\u043e\u0440\u0441\u1fb3\u1fbc\u1f88"
    )
    + [YPOGEGRAMMENI] * 6,
    "latin, digits, space, marks": list("abcXYZkK019 -.\u0301\u0338\u0e31\u0942"),
}
# marks that are inserted between the characters of a random text (U+0345 is inserted in a separate row: its reading depends on the letter before it)
INSERTED = (
    [
        c
        for name in ("zero-width", "bidi", "variation selectors", "tag characters")
        for c in RANDOM_CLASSES[name]
        if c not in "\u2028\u2029"
    ]
    + [chr(c) for c in FILLER_CODE_POINTS]
    + ["\u0301", "\u0300", "\ue000", "\u0000", "\u0090", "\ufff0"]
)


def _random_texts():
    nxt = _numbers(RANDOM_SEED)
    classes = list(RANDOM_CLASSES.values())
    for _ in range(RANDOM_STRINGS):
        yield "".join(
            (pool := classes[next(nxt) % len(classes)])[next(nxt) % len(pool)]
            for _ in range(1 + next(nxt) % 10)
        )


def test_random_strings_are_idempotent_case_symmetric_and_stable_under_inserted_marks():
    nxt = _numbers(RANDOM_SEED + 1)
    not_idempotent, asymmetric, not_stable, seen = [], [], [], set()
    set_asymmetric, set_unstable, too_long = [], [], []
    for text in _random_texts():
        seen.update(text)
        key = identity_key(text)
        if identity_key(key) != key:
            not_idempotent.append(text)
        if any(
            len(v) > textnorm._weight(text)
            for v in textnorm.fold_views(text, casefold=True, scripts=frozenset())
        ):
            too_long.append(
                text
            )  # a view is never longer than W (the size rule bounds the work of every reading)
        sq = squeeze(text)
        if squeeze(sq) != sq:
            not_idempotent.append(text)
        if not _exempt_from_symmetry(text):
            upper, lower = text.upper(), text.lower()
            if identity_key(upper) != identity_key(lower) or squeeze(upper) != squeeze(lower):
                asymmetric.append(text)
            if not could_be_same_person(
                upper, lower
            ):  # the DENY comparator (the readings) is case symmetric as well
                set_asymmetric.append(text)
        cut = next(nxt) % (len(text) + 1)
        mark = INSERTED[next(nxt) % len(INSERTED)]
        moved = text[:cut] + mark + text[cut:]
        if identity_key(moved) != key or squeeze(moved) != sq:  # one reading: every mark but U+0345
            not_stable.append(moved)
        cut = next(nxt) % (len(text) + 1)
        with_iota_mark = (
            text[:cut] + YPOGEGRAMMENI + text[cut:]
        )  # U+0345 anywhere: the readings still match
        if not could_be_same_person(with_iota_mark, text) or not (
            set(textnorm.squeeze_views(with_iota_mark)) & set(textnorm.squeeze_views(text))
        ):
            set_unstable.append(with_iota_mark)
    assert not not_idempotent, (
        f"a key is not idempotent for {len(not_idempotent)} random texts, first {_show(not_idempotent)}"
    )
    assert not asymmetric, (
        f"a key is not case symmetric for {len(asymmetric)} random texts, first {_show(asymmetric)}"
    )
    assert not not_stable, (
        f"an inserted mark changes the key of {len(not_stable)} random texts, first {_show(not_stable)}"
    )
    assert not set_asymmetric, (
        f"could_be_same_person is not case symmetric for {len(set_asymmetric)} random texts, first {_show(set_asymmetric)}"
    )
    assert not set_unstable, (
        f"a U+0345 inserted into a random text defeats the readings for {len(set_unstable)} texts, first {_show(set_unstable)}"
    )
    assert not too_long, (
        f"a view is longer than the weight for {len(too_long)} random texts, first {_show(too_long)}"
    )
    for name, pool in RANDOM_CLASSES.items():  # every class took part
        assert seen & set(pool), f"the random texts never used the class {name}"


def test_a_raw_text_that_starts_with_the_interpreters_own_tag_has_it_stripped_and_another_tag_is_not(
    monkeypatch,
):
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "15.1.0")
    monkeypatch.setattr(unicodedata, "unidata_version", "15.0.0")
    tag = key_tag()
    assert tag.startswith("\ue000alg=fold5|ud=15.0.0") and tag.endswith("\ue000")
    # the stated over-collision: the tag of THIS interpreter in front of a text is read as "already a key"
    assert identity_key(tag + "Bob") == identity_key("Bob") == tag + "bob"
    assert could_be_same_person(tag + "Bob", "bob")
    once = identity_key(tag + tag + "bob")
    assert once == identity_key(once) and once != tag + "bob", (
        "a double tag is stripped once, not twice"
    )
    # the tag of ANOTHER version is not stripped: its text stays in the key, so the two never collide
    monkeypatch.setattr(unicodedata, "unidata_version", "9.9.9")
    assert key_tag() != tag
    other = identity_key(tag + "bob")
    assert other.startswith(key_tag()) and "ud=15.0.0" in other and other != identity_key("bob")
    # on the pinned version there is no tag to strip and U+E000 is dropped like any private-use character
    monkeypatch.setattr(unicodedata, "unidata_version", "15.1.0")
    assert key_tag() == "" and identity_key(tag + "bob") == "alg=fold5|ud=15.0.0bob"


def test_the_case_fold_table_is_on_the_case_fold_image_and_its_conflicts_are_the_known_eleven():
    table = textnorm._CF_TABLE
    for cp, value in table.items():
        ch = chr(cp)
        assert cp >= 0x80 and ch.casefold() == ch, f"U+{cp:04X} is not a casefolded non-ASCII key"
        assert value.isascii() and value == value.casefold() and value, (
            f"U+{cp:04X} has a value that is not lower-case ASCII"
        )
    reaching = {}
    for cp, value in _confusables.TABLE.items():
        folded = chr(cp).casefold()
        assert len(folded) == 1, (
            f"U+{cp:04X} has a case fold of {len(folded)} characters: look it up through its parts"
        )
        assert ord(folded) in table, f"U+{cp:04X} lost its look-alike through the case fold"
        reaching.setdefault(ord(folded), {})[cp] = value.casefold()
    conflicts = sorted(f for f, sources in reaching.items() if len(set(sources.values())) > 1)
    assert conflicts == [
        0x1BD,
        0x3B7,
        0x3BC,
        0x3BD,
        0x3C5,
        0x4CF,
        0x118C3,
        0x118C4,
        0x118C6,
        0x118D5,
        0x118DC,
    ], "the letters whose capital and small forms disagree changed: " + str(
        [hex(c) for c in conflicts]
    )
    for folded in (
        conflicts
    ):  # the entry of the letter that is its own case fold wins; otherwise the lowest code point
        own = reaching[folded].get(folded)
        expected = own if own is not None else reaching[folded][min(reaching[folded])]
        assert table[folded] == expected, (
            f"U+{folded:04X} does not take the entry of its own letter"
        )


# ---- the Unicode pin ---------------------------------------------------------------------------------------------------------------------
def test_require_pinned_unidata_is_the_guard_and_fails_closed(monkeypatch):
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "15.1.0")
    monkeypatch.setattr(unicodedata, "unidata_version", "15.0.0")
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # it must RAISE UnidataMismatch, never warn
        refused(
            UnidataMismatch,
            "require_pinned_unidata accepted another Unicode version",
            require_pinned_unidata,
        )
        refused(
            UnidataMismatch,
            "require_pinned_unidata ignored its argument",
            require_pinned_unidata,
            "15.1.0",
        )
        accepted(
            "require_pinned_unidata refused the version it was given",
            require_pinned_unidata,
            "15.0.0",
        )
    assert not issubclass(UnidataMismatch, (ValueError, TypeError)), (
        "a DENY caller's except clause would swallow it"
    )
    with pytest.raises(UnidataMismatch) as info:
        require_pinned_unidata()
    assert str(info.value) == (
        "this Python uses Unicode 15.0.0; run Python 3.13 (Unicode 15.1.0) for pilot or prod"
    ), "the pin message does not say plainly what to run"
    monkeypatch.setattr(unicodedata, "unidata_version", "14.0.0")
    with pytest.raises(UnidataMismatch) as info:
        require_pinned_unidata()
    assert "uses Unicode 14.0.0" in str(info.value), (
        "the message does not name the detected version"
    )
    monkeypatch.setattr(unicodedata, "unidata_version", "15.1.0")
    accepted("require_pinned_unidata refused the pinned version", require_pinned_unidata)
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "16.0.0")
    refused(UnidataMismatch, "the patched pin is not read", require_pinned_unidata)


def test_a_key_made_on_another_unicode_version_carries_that_version_and_never_equals_another(
    monkeypatch,
):
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "15.1.0")
    monkeypatch.setattr(unicodedata, "unidata_version", "15.1.0")
    assert key_tag() == "" and identity_key("Bob") == "bob", "the pinned version has the bare key"
    pinned_key = identity_key("bob")
    monkeypatch.setattr(unicodedata, "unidata_version", "15.0.0")
    other = identity_key("Bob")
    assert other != pinned_key, "a key made on another Unicode version equals the pinned key"
    assert other.endswith("bob") and "ud=15.0.0" in other and "alg=fold5" in other, (
        "the tag does not name the algorithm and the Unicode version"
    )
    assert identity_key(other) == other, "the key of another version is not idempotent"
    assert could_be_same_person("BØB", "bob") and not could_be_same_person("bob", "bobb")
    monkeypatch.setattr(unicodedata, "unidata_version", "9.9.9")
    assert identity_key("Bob") != other, "keys of two non-pinned versions are equal"
    # on the pinned version nothing a person types can reach a tagged key: U+E000 is private use and is dropped
    monkeypatch.setattr(unicodedata, "unidata_version", "15.1.0")
    assert identity_key(other) != other and "\ue000" not in identity_key(other)


# ---- input rules: type, then size --------------------------------------------------------------------------------------------------------
class _Name(enum.StrEnum):
    RED = "red"


class _Sub(str):
    pass


class _Hostile(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


ONE_ARG = (fold, squeeze, identity_key, has_hidden_channel, has_mixed_script)
TWO_ARG = (could_be_same_person, allow_equal, names_equal)


def test_every_public_function_refuses_what_is_not_a_plain_str():
    for bad in (b"x", 1, None, ["x"], _Sub("x"), _Name.RED, bytearray(b"x")):
        for fn in ONE_ARG:
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__}", fn, bad)
        for fn in TWO_ARG:
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__} first", fn, bad, "a")
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__} second", fn, "a", bad)
    for fn in ONE_ARG:
        assert fn(str(_Name.RED)) is not None  # the plain text of a member is accepted
    assert could_be_same_person(str(_Name.RED), "red") and names_equal(str(_Name.RED), "RED")


def test_a_str_subclass_is_refused_by_exact_type_not_by_isinstance():
    refused(NotText, "a str subclass is accepted", identity_key, _Sub("alice"))
    refused(
        NotText,
        "a str subclass is accepted as the second argument",
        allow_equal,
        "alice",
        _Sub("alice"),
    )


def test_a_hostile_eq_cannot_make_two_texts_equal():
    refused(
        NotText,
        "a text with its own __eq__ reached the comparison",
        allow_equal,
        _Hostile("a"),
        "b",
    )
    refused(
        NotText,
        "a text with its own __eq__ reached the comparison (second)",
        allow_equal,
        "b",
        _Hostile("a"),
    )
    assert allow_equal("a", "b") is AllowVerdict.DIFFERENT


def test_the_cap_itself_is_accepted_and_one_more_ascii_character_is_refused():
    assert (
        len(bare(accepted("a text of exactly the cap is refused", identity_key, "a" * CAP))) == CAP
    )
    refused(TextTooLong, "a text over the cap is accepted", identity_key, "a" * (CAP + 1))
    for fn in ONE_ARG:
        refused(TextTooLong, f"{fn.__name__} accepted a text over the cap", fn, "a" * (CAP + 1))
    for fn in TWO_ARG:
        refused(
            TextTooLong, f"{fn.__name__} accepted a text over the cap", fn, "a", "a" * (CAP + 1)
        )


def test_the_size_rule_counts_what_a_character_becomes_not_its_length():
    # U+1F75C becomes three letters: SEAM-1
    refused(TextTooLong, "87,382 x U+1F75C (W 262,146) is accepted", identity_key, SSS * 87382)
    assert bare(accepted("W 262,143 is refused", identity_key, SSS * 87381)) == "s" * 262143
    refused(
        TextTooLong,
        "262,144 x U+1F75C (plain length at the cap) is accepted",
        identity_key,
        SSS * CAP,
    )
    # U+FDFA becomes eighteen characters in NFKC
    refused(TextTooLong, "cap/18 + 1 x U+FDFA is accepted", identity_key, FDFA * (CAP // 18 + 1))
    assert len(bare(accepted("cap/18 x U+FDFA is refused", identity_key, FDFA * (CAP // 18)))) > 0
    # NFKD makes two characters of an accented letter
    assert (
        len(bare(accepted("W exactly at the cap is refused", identity_key, chr(0xE9) * (CAP // 2))))
        == CAP // 2
    )
    refused(
        TextTooLong,
        "an accented text over the weight is accepted",
        identity_key,
        chr(0xE9) * (CAP // 2 + 1),
    )


def test_the_size_rule_checks_every_argument_left_to_right():
    big = SSS * 87382
    refused(
        TextTooLong,
        "could_be_same_person skipped the second argument",
        could_be_same_person,
        "a",
        big,
    )
    refused(TextTooLong, "allow_equal skipped the first argument", allow_equal, big, "a")
    refused(TextTooLong, "allow_equal skipped the second argument", allow_equal, "a", big)
    refused(TextTooLong, "names_equal skipped the second argument", names_equal, "a", big)
    refused(
        TextTooLong,
        "could_be_same_person(big, 1) is not a size refusal",
        could_be_same_person,
        big,
        1,
    )
    refused(
        NotText, "could_be_same_person(1, big) is not a type refusal", could_be_same_person, 1, big
    )


def test_the_cap_is_read_when_the_function_runs(monkeypatch):
    monkeypatch.setattr(defaults, "TEXTNORM_MAX_CHARS", 5)
    assert bare(accepted("the patched cap refuses a short text", identity_key, "abcde")) == "abcde"
    refused(TextTooLong, "the patched cap is not used", identity_key, "abcdef")


def test_a_refusal_message_holds_lengths_and_constants_never_the_input():
    canary = "ZQXCANARY"
    for text in (canary + "a" * CAP, canary + SSS * 90000):
        with pytest.raises(TextTooLong) as info:
            identity_key(text)
        assert canary not in str(info.value) and "ZQX" not in str(info.value)
    with pytest.raises(NotText) as info:
        identity_key(_Sub(canary))
    assert canary not in str(info.value)


def test_the_refusal_messages_say_in_plain_words_what_is_wrong():
    with pytest.raises(TextTooLong) as info:
        identity_key("a" * (CAP + 1))
    assert str(info.value) == f"the text is too long: {CAP + 1} of {CAP} allowed", (
        "the length message is not in plain words"
    )
    with pytest.raises(TextTooLong) as info:
        identity_key(SSS * 87382)
    assert str(info.value) == (
        f"the text is too long once look-alike letters are expanded: {87382 * 3} of {CAP} allowed"
    ), "the weight message is not in plain words"


def test_the_errors_are_their_own_family_and_not_value_or_type_errors():
    for cls in (TextTooLong, NotText, UnidataMismatch):
        assert issubclass(cls, TextnormError)
    assert not issubclass(TextnormError, (ValueError, TypeError))
    for cls in (TextTooLong, NotText, UnidataMismatch):
        assert not issubclass(cls, (ValueError, TypeError))


def test_a_deny_caller_that_catches_value_error_does_not_swallow_a_refusal():
    with pytest.raises(TextTooLong):
        try:
            identity_key("a" * (CAP + 1))
        except ValueError:  # the shape of an old caller: it must not catch this
            pytest.fail("a ValueError handler caught a TextnormError")


# ---- the hidden channel ------------------------------------------------------------------------------------------------------------------
def test_tag_characters_and_free_variation_selectors_are_a_hidden_channel():
    for cp in (0xE0000, 0xE0001, 0xE0061, 0xE007F):
        assert has_hidden_channel("alice" + chr(cp)), f"tag character U+{cp:05X} is not reported"
    assert has_hidden_channel("approved " + "".join(chr(0xE0000 + ord(c)) for c in "yes"))
    for cp in (*range(0xFE00, 0xFE0E),):
        assert has_hidden_channel("a" + chr(cp)), f"selector U+{cp:04X} is not reported"
    for cp in (0x180B, 0x180C, 0x180D, 0x180F):
        assert has_hidden_channel("a" + chr(cp)), f"Mongolian selector U+{cp:04X} is not reported"
    assert has_hidden_channel("a" + chr(0xE0100)), (
        "selector U+E0100 (the first of 17 to 256) is not reported"
    )
    assert has_hidden_channel("a" + chr(0xE01EF)), "selector U+E01EF (the last) is not reported"
    assert has_hidden_channel(
        "" + chr(0x8FBB) + "" + chr(0xE0101)
    )  # an ideographic selector after a Japanese name is reported
    assert has_hidden_channel(
        "\U0001f3f4\U000e0067\U000e0062\U000e007f"
    )  # a flag written with tag letters


def test_the_two_emoji_selectors_and_other_invisible_characters_are_not_counted():
    assert not has_hidden_channel((chr(0x2764) + chr(0xFE0F)) * 200), (
        "a colour emoji is reported as a hidden channel"
    )
    assert not has_hidden_channel(chr(0x2764) + chr(0xFE0E)), "the text selector U+FE0E is reported"
    invisible = (
        0x301,
        0x200B,
        0x202E,
        0x200D,
        0x180E,
    )  # a mark, a zero-width space, a bidi override, a joiner, the Mongolian vowel separator
    for text in (
        "alice",
        "",
        "a b\n",
        chr(0xE000),
        chr(0xE0080),
        *("a" + chr(cp) + "b" for cp in invisible),
    ):
        assert not has_hidden_channel(text), repr(text)


def test_the_hidden_channel_is_read_on_the_raw_text_without_any_decoder():
    assert has_hidden_channel("&#xE0061;" * 20) is False  # an HTML entity is only a spelling
    assert (
        has_hidden_channel(html.unescape("&#xE0061;" * 20)) is True
    )  # the caller decodes the view it wants checked


def test_the_hidden_channel_signal_refuses_what_is_not_text():
    refused(NotText, "has_hidden_channel accepted bytes", has_hidden_channel, b"x")
    refused(
        TextTooLong,
        "has_hidden_channel accepted a text over the cap",
        has_hidden_channel,
        "a" * (CAP + 1),
    )


# ---- names ---------------------------------------------------------------------------------------------------------------------------------
def test_the_public_names_are_exactly_the_listed_thirty_three():
    assert sorted(textnorm.__all__) == sorted(
        [
            "FILLERS",
            "FOLD_VERSION",
            "AllowVerdict",
            "Coverage",
            "CoverageRefused",
            "EmptyView",
            "FoldNotConverged",
            "NotText",
            "TextTooLong",
            "TextnormError",
            "UnidataMismatch",
            "ViewTooShort",
            "allow_equal",
            "could_be_same_person",
            "fold",
            "fold_views",
            "has_hidden_channel",
            "has_mixed_script",
            "identity_key",
            "identity_keys",
            "key_tag",
            "names_equal",
            "register_value",
            "require_pinned_unidata",
            "scan_cache",
            "scan_holds",
            "scan_keyset",
            "scan_needles",
            "scan_views",
            "scan_views_no_value",
            "squeeze",
            "squeeze_views",
            "value_scripts",
        ]
    )
    assert len(textnorm.__all__) == len(set(textnorm.__all__)) == 33


def test_every_name_the_module_defines_is_public_and_listed_or_private():
    """Imports are not definitions: a name made by ``def``, ``class`` or an assignment is either in ``__all__`` or starts with ``_``."""
    tree = ast.parse(Path(textnorm.__file__).read_text(encoding="utf-8"))
    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            defined.update(t.id for t in targets if isinstance(t, ast.Name))
    public = {n for n in defined if not n.startswith("_")}
    assert public == set(textnorm.__all__), public ^ set(textnorm.__all__)
    assert all(hasattr(textnorm, n) for n in textnorm.__all__)


# ---- the readings (P1a fix3, review 3): one text has a small fixed set of keys, and two texts are the same person when any two match ----------
ETA, MU, NU, UPSILON = (
    "\u0397",
    "\u039c",
    "\u039d",
    "\u03a5",
)  # Greek capitals that look exactly like Latin H M N Y


def _greek_letters():
    """Every Greek letter by Unicode name (lower and upper case are both in the set; U+0374 and U+037A are signs, not letters)."""
    return [
        chr(cp)
        for cp in range(sys.maxunicode + 1)
        if unicodedata.name(chr(cp), "").startswith("GREEK")
        and " LETTER " in unicodedata.name(chr(cp))
    ]


def _any_shared(a, b):
    return bool(set(a) & set(b))


def _scan_finds(secret, haystack):
    """A redaction-style scan: does any view of the haystack hold any view of the secret?"""
    needles = textnorm.fold_views(secret, casefold=True, scripts=frozenset())
    return any(
        n in v
        for v in textnorm.fold_views(haystack, casefold=True, scripts=frozenset())
        for n in needles
    )


def test_a_greek_look_alike_with_ypogegrammeni_is_the_latin_word_for_could_be_same_person_and_for_a_scan():
    hostile = "\u03b1\u0345dmin"  # alpha + U+0345 + "dmin": the reader sees "admin"
    assert could_be_same_person(hostile, "admin") and could_be_same_person("admin", hostile), (
        "alpha + U+0345 + dmin is not the person admin"
    )
    assert allow_equal(hostile, "admin") is AllowVerdict.LOOKALIKE, (
        "allow_equal does not report alpha + U+0345 + dmin as a look-alike"
    )
    assert "admin" in textnorm.fold_views(hostile, casefold=True, scripts=frozenset()), (
        "fold_views of alpha + U+0345 + dmin has no view that reads admin"
    )
    assert "ADMIN" in textnorm.squeeze_views(hostile), "squeeze_views has no view that reads ADMIN"
    assert _scan_finds("password=", "token passw\u03bf\u0345rd=hunter"), (
        "the scan misses passw + omicron + U+0345 + rd="
    )
    assert _scan_finds("password=", "token passw\u03bf\u0345\u0345\u0345rd=hunter"), (
        "a run of U+0345 hides the secret from the scan"
    )
    assert not _scan_finds("password=", "token passwd=hunter"), (
        "the scan finds a text that is not there"
    )
    assert not could_be_same_person(hostile, "admins") and not could_be_same_person(hostile, "adm")


def test_a_ypogegrammeni_after_any_greek_letter_leaves_the_readings_of_the_word_matching():
    letters = sorted({x for g in _greek_letters() for x in (g, g.upper(), g.lower())})
    assert len(letters) > 300
    bad = []
    for g in letters:
        for tail in ("", "dmin"):
            plain = g + tail
            for marked in (
                g + YPOGEGRAMMENI + tail,
                YPOGEGRAMMENI + g + tail,
                g + YPOGEGRAMMENI * 3 + tail,
            ):
                same = could_be_same_person(marked, plain)
                for casefold in (False, True):
                    same = same and _any_shared(
                        textnorm.fold_views(marked, casefold=casefold, scripts=frozenset()),
                        textnorm.fold_views(plain, casefold=casefold, scripts=frozenset()),
                    )
                same = same and _any_shared(
                    textnorm.squeeze_views(marked), textnorm.squeeze_views(plain)
                )
                if not same:
                    bad.append(marked)
    assert not bad, (
        f"a U+0345 next to a Greek letter changes every reading for {len(bad)} texts, first {_show(bad)}"
    )


def test_every_greek_look_alike_of_the_table_plus_ypogegrammeni_is_the_latin_word():
    checked = 0
    for cp, value in _confusables.TABLE.items():
        ch = chr(cp)
        if not (ch.isalpha() and unicodedata.name(ch, "").startswith("GREEK ")):
            continue
        checked += 1
        assert could_be_same_person(ch + YPOGEGRAMMENI + "dmin", value + "dmin"), (
            f"Greek U+{cp:04X} + U+0345 is not the Latin {value}"
        )
        assert _scan_finds(value + "dmin", "x " + ch + YPOGEGRAMMENI + "dmin y"), (
            f"the scan misses Greek U+{cp:04X} + U+0345 for the Latin {value}"
        )
    assert checked > 20


def test_the_four_greek_capitals_that_look_like_latin_capitals_are_could_be_the_same_person():
    for greek, latin, rest in (
        (ETA, "H", "oward"),
        (MU, "M", "ark"),
        (NU, "N", "ick"),
        (UPSILON, "Y", "an"),
    ):
        for text_latin, text_greek in (
            (latin + rest, greek + rest),
            (latin.lower() + rest, greek + rest),
            ((latin + rest).upper(), (greek + rest).upper()),
            ((latin + rest).upper(), greek + rest.upper()),
        ):
            assert could_be_same_person(text_latin, text_greek) and could_be_same_person(
                text_greek, text_latin
            ), f"{text_latin!a} and {text_greek!a} are not the same person"
            assert allow_equal(text_latin, text_greek) is AllowVerdict.LOOKALIKE, (
                f"allow_equal does not report {text_greek!a} as a look-alike of {text_latin!a}"
            )
            assert _scan_finds(text_latin, "see " + text_greek + " here"), (
                f"the scan misses {text_greek!a} for {text_latin!a}"
            )
            assert _any_shared(
                textnorm.squeeze_views(text_latin), textnorm.squeeze_views(text_greek)
            ), f"no squeeze view of {text_greek!a} reads {text_latin!a}"
        assert could_be_same_person(latin + rest, greek + YPOGEGRAMMENI + rest), (
            f"a capital Greek letter + U+0345 is not the Latin capital {latin}"
        )
    assert could_be_same_person("Ho", ETA + "\u0275"), (
        "the upper-side reading lacks the table of the case-fold image"
    )


def test_every_table_source_is_could_be_the_same_person_as_the_text_it_looks_like():
    """The table entry of a letter is how it LOOKS, whatever its case: the readings keep the entry of the letter itself (capital Eta reads H)
    and the entry of its case-fold image (Eta reads n like eta). Every source, as a word and next to Latin letters. A decimal digit of
    another script is left out: the digit step reads it as the digit it is, before the table (pinned by the digit tests)."""
    bad = [
        cp
        for cp, value in _confusables.TABLE.items()
        if not chr(cp).isdecimal()
        and not (
            could_be_same_person(chr(cp), value)
            and could_be_same_person("ab" + chr(cp) + "yz", "ab" + value + "yz")
        )
    ]
    assert not bad, (
        f"{len(bad)} table sources are not the person they look like, first {[hex(c) for c in bad[:5]]}"
    )


def test_the_readings_are_not_transitive_and_over_match_on_purpose():
    """Capital Eta reads h (own case) and n (case-fold image): it matches both words, and the two words do not match each other."""
    eta_word = ETA + "oward"
    assert could_be_same_person(eta_word, "howard"), "the upper-side reading was dropped"
    assert could_be_same_person(eta_word, "noward"), (
        "the lower-side reading of a capital was dropped"
    )
    assert not could_be_same_person("howard", "noward"), (
        "could_be_same_person became transitive over the readings"
    )
    # the lower-side reading of capital Eta + U+0345 (mark dropped, eta read n) is kept
    assert could_be_same_person(ETA + YPOGEGRAMMENI + "oward", "noward"), (
        "the lower-side reading with U+0345 dropped was removed"
    )
    # the iota reading is kept: a precomposed letter with ypogegrammeni against its capitals
    assert could_be_same_person("\u1fb3", "\u0391\u0399") and could_be_same_person(
        "\u1fb3", "\u1fbc"
    ), "the iota reading was dropped"


def test_identity_keys_is_a_small_fixed_set_that_holds_the_single_key():
    keys = textnorm.identity_keys("Bob")
    assert type(keys) is tuple and keys == (identity_key("bob"),), (
        "a text with one reading has one key"
    )
    cases = [
        "admin",
        "\u03b1\u0345dmin",
        ETA + YPOGEGRAMMENI + "oward",
        ETA + YPOGEGRAMMENI,
        "\u1fb3" + ETA + MU + NU + UPSILON,
        "\u0391\u0399\u0397\u0397\u039c\u039c" + YPOGEGRAMMENI * 40,
        "".join(chr(c) for c in range(0x370, 0x400)),
        "".join(chr(c) for c in range(0x1F00, 0x2000) if chr(c).isalpha()) + YPOGEGRAMMENI,
    ]
    for text in cases:
        keys = textnorm.identity_keys(text)
        # at most three spelling variants; a text with a spacing mark, modifier letter or modifier symbol also has those of its marks-dropped text
        limit = 6 if any(unicodedata.category(ch) in ("Mc", "Lm", "Sk") for ch in text) else 3
        assert type(keys) is tuple and 1 <= len(keys) <= limit, (
            f"{len(keys)} readings for {_show([text])}"
        )
        assert len(set(keys)) == len(keys), "a reading is listed twice"
        assert identity_key(text) in keys, "the single key is not one of the readings"
        assert keys == textnorm.identity_keys(text), "the readings are not deterministic"
        for key in keys:
            assert key == bare(key) or key.startswith(key_tag())
    assert set(map(bare, textnorm.identity_keys("\u03b1\u0345dmin"))) == {"admin", "aidmin"}
    assert set(map(bare, textnorm.identity_keys(ETA + "oward"))) == {"noward", "howard"}
    # the number of readings does not grow with the text: a text with every kind of ambiguity but no spacing mark still has three at most
    assert len(textnorm.identity_keys(ETA + YPOGEGRAMMENI + "oward")) <= 3, (
        "more than three readings"
    )
    assert (
        len(textnorm.identity_keys((ETA + MU + NU + UPSILON + "\u03b1" + YPOGEGRAMMENI) * 50)) <= 3
    )


def test_fold_views_and_squeeze_views_hold_the_single_fold_and_are_bounded():
    for text in ("admin", "\u03b1\u0345dmin", ETA + "oward  x\u200b", "\u1fb3 Mark", ""):
        for casefold in (False, True):
            for collapse_ws in (False, True):
                views = textnorm.fold_views(
                    text, casefold=casefold, collapse_ws=collapse_ws, scripts=frozenset()
                )
                assert type(views) is tuple and 1 <= len(views) <= 6
                assert len(set(views)) == len(views)
                assert fold(text, casefold=casefold, collapse_ws=collapse_ws) in views, (
                    "the single fold is not one of the views"
                )
        for loose in (False, True):
            views = textnorm.squeeze_views(text, loose=loose)
            assert type(views) is tuple and 1 <= len(views) <= 6
            assert squeeze(text, loose=loose) in views, "the single squeeze is not one of the views"
    assert set(textnorm.fold_views("\u03b1\u0345dmin", casefold=False, scripts=frozenset())) == {
        "admin",
        "aidmin",
    }
    assert "howard" in textnorm.fold_views(ETA + "oward", casefold=True, scripts=frozenset())
    assert "Howard" in textnorm.fold_views(ETA + "oward", casefold=False, scripts=frozenset())
    for fn in (textnorm.identity_keys, _fold_views_no_scripts, textnorm.squeeze_views):
        refused(NotText, f"{fn.__name__} accepted a str subclass", fn, _Sub("a"))
        refused(TextTooLong, f"{fn.__name__} accepted a text over the cap", fn, "a" * (CAP + 1))


def test_identity_keys_and_could_be_same_person_hold_for_every_code_point_the_single_key_and_case_symmetry():
    """Every code point except the 960,000 private-use and unassigned ones (which are dropped; checked in runs elsewhere)."""
    missing, asymmetric, too_long = [], [], []
    for ch in _non_surrogates():
        if unicodedata.category(ch) in ("Co", "Cn"):
            continue
        keys = textnorm.identity_keys(ch)
        if identity_key(ch) not in keys:
            missing.append(ch)
        if any(len(bare(k)) > textnorm._weight(ch) for k in keys):
            too_long.append(ch)  # the size rule bounds the work of every reading
        upper, lower = ch.upper(), ch.lower()
        if (
            upper != lower
            and not _exempt_from_symmetry(ch)
            and not could_be_same_person(upper, lower)
        ):
            asymmetric.append(ch)
    assert not missing, (
        f"the single key is not a reading for {len(missing)} code points, first {_show(missing)}"
    )
    assert not asymmetric, (
        f"could_be_same_person is not case symmetric for {len(asymmetric)} code points, first {_show(asymmetric)}"
    )
    assert not too_long, (
        f"a reading is longer than the weight for {len(too_long)} code points, first {_show(too_long)}"
    )


def test_could_be_same_person_is_case_symmetric_for_pairs_built_from_the_table_and_the_narrowed_exemption_is_exact():
    bad = [
        t
        for t in _pairs()
        if (u := t.upper()) != (l := t.lower())
        and not _exempt_from_symmetry(t)
        and not could_be_same_person(u, l)
    ]
    assert not bad, (
        f"could_be_same_person is not case symmetric for {len(bad)} pairs, first {_show(bad)}"
    )
    # the exemption is the exact shape (a U+0345 with no Greek letter before it), not "any text that holds U+0345"
    assert _exempt_from_symmetry(YPOGEGRAMMENI) and _exempt_from_symmetry(
        "a" + YPOGEGRAMMENI + "\u03b1"
    )
    assert _exempt_from_symmetry("\u03b1 " + YPOGEGRAMMENI) and _exempt_from_symmetry(
        "\u0430" + YPOGEGRAMMENI
    )
    for attached in (
        "\u03b1" + YPOGEGRAMMENI,
        "\u03b1\u200b" + YPOGEGRAMMENI + "dmin",
        "a\u03b1" + YPOGEGRAMMENI + "z",
        "\u1fb3",
        "\u0391" + YPOGEGRAMMENI,
        "\u03b1" + YPOGEGRAMMENI * 3,
    ):
        assert not _exempt_from_symmetry(attached), f"{attached!a} is wrongly exempt"
        assert identity_key(attached.upper()) == identity_key(attached.lower()), (
            f"an attached U+0345 is not case symmetric: {attached!a}"
        )
        assert could_be_same_person(attached.upper(), attached.lower())
    # and the asymmetric shapes really are asymmetric, so the exemption is still needed
    assert identity_key(YPOGEGRAMMENI.upper()) != identity_key(YPOGEGRAMMENI.lower())
    assert identity_key(("a" + YPOGEGRAMMENI).upper()) != identity_key(
        ("a" + YPOGEGRAMMENI).lower()
    )


def test_names_equal_and_the_canonical_form_are_case_symmetric_for_every_code_point():
    """Unicode caseless matching (D146): case fold, NFKD, case fold. The one code point that is not symmetric is the dotless i (U+0131): its
    upper case is I, whose case fold is i, not the dotless i. That is the Unicode rule (names_equal does not fold look-alikes); the DENY
    comparator ``could_be_same_person`` reads the dotless i as i."""
    asymmetric = [
        ch
        for ch in _non_surrogates()
        if (u := ch.upper()) != (l := ch.lower()) and textnorm._canon(u) != textnorm._canon(l)
    ]
    assert asymmetric == ["\u0131"], (
        f"_canon is not case symmetric for {len(asymmetric)} code points, first {_show(asymmetric)}"
    )
    assert not names_equal("I", "\u0131") and could_be_same_person("I", "\u0131")
    pairs = [
        t
        for t in _pairs()
        if "\u0131" not in t and (u := t.upper()) != (l := t.lower()) and not names_equal(u, l)
    ]
    assert not pairs, (
        f"names_equal is not case symmetric for {len(pairs)} pairs, first {_show(pairs)}"
    )
    for text in (
        "\u0390",
        "\u03b0",
        "\u1fd2",
        "\u1fd3",
        "\u1fd7",
        "\u1fe2",
        "\u1fe3",
        "\u1fe7",
        "\ufb05",
    ):
        assert names_equal(text, text.upper()), f"names_equal is not case symmetric for {text!a}"
    not_fixed = [
        ch
        for ch in _non_surrogates()
        if textnorm._canon(textnorm._canon(ch)) != textnorm._canon(ch)
    ]
    assert not not_fixed, (
        f"_canon is not idempotent for {len(not_fixed)} code points, first {_show(not_fixed)}"
    )


def test_the_cheap_length_check_runs_before_any_per_character_work(monkeypatch):
    calls = []

    def spy(text):
        calls.append(len(text))
        return len(text)

    monkeypatch.setattr(textnorm, "_weight", spy)
    for text in (
        "a" * (CAP + 1),
        "\u00e9" * (CAP + 1),
        "".join(map(chr, range(0x4E00, 0x4E00 + CAP + 1))),
    ):
        for fn in (identity_key, squeeze, fold, has_mixed_script, has_hidden_channel):
            refused(TextTooLong, f"{fn.__name__} accepted a text longer than the cap", fn, text)
        for fn in (textnorm.identity_keys, _fold_views_no_scripts, textnorm.squeeze_views):
            refused(TextTooLong, f"{fn.__name__} accepted a text longer than the cap", fn, text)
        refused(
            TextTooLong,
            "could_be_same_person accepted a long text",
            could_be_same_person,
            "a",
            text,
        )
    too_long = [n for n in calls if n > CAP]
    assert not too_long, (
        f"the weight was computed for a text longer than the cap (lengths {too_long[:3]})"
    )
    calls.clear()
    accepted("a short text is refused", identity_key, "\u00e9abc")
    assert calls == [4], "the weight is computed for a text within the cap"


def test_a_key_made_on_another_unicode_version_carries_the_tag_on_every_reading(monkeypatch):
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "15.1.0")
    monkeypatch.setattr(unicodedata, "unidata_version", "15.1.0")
    pinned = textnorm.identity_keys("\u03b1\u0345dmin")
    assert key_tag() == "" and all(k == bare(k) for k in pinned)
    monkeypatch.setattr(unicodedata, "unidata_version", "15.0.0")
    other = textnorm.identity_keys("\u03b1\u0345dmin")
    assert all(k.startswith(key_tag()) and "ud=15.0.0" in k for k in other), "a reading has no tag"
    assert not set(other) & set(pinned), "a key of another version equals a key of the pinned one"
    assert textnorm.identity_keys(other[0]) == (other[0],), (
        "the key of another version is not stable"
    )
    assert could_be_same_person("\u03b1\u0345dmin", "admin")
    assert could_be_same_person(ETA + "oward", "Howard")


def test_lead_probe_3_a_greek_look_alike_with_ypogegrammeni_against_the_latin_word():
    """The lead's probe 3 of review 3, as a test: alpha + U+0345 + "dmin" and "passw" + omicron + U+0345 + "rd" against the Latin words, through
    every function the probe printed, and the table has no source that is unassigned on this interpreter."""
    alpha, omicron, iota_sub = "\u03b1", "\u03bf", "\u0345"
    hostile = alpha + iota_sub + "dmin"
    # the single readings are what the probe printed: one invisible mark away from admin
    assert bare(identity_key(hostile)) == bare(fold(hostile, casefold=True)) == "aidmin"
    assert squeeze(hostile) == "AIDMIN" and squeeze("admin") == "ADMIN"
    # the DENY comparator and the scan views see through it
    assert could_be_same_person(hostile, "admin"), (
        "could_be_same_person(alpha + U+0345 + dmin, admin) is False"
    )
    assert could_be_same_person("passw" + omicron + iota_sub + "rd", "password"), (
        "passw + omicron + U+0345 + rd is not password"
    )
    assert "ADMIN" in textnorm.squeeze_views(hostile) and "admin" in textnorm.fold_views(
        hostile, casefold=True, scripts=frozenset()
    )
    table_sources_unassigned_here = [
        cp for cp in _confusables.TABLE if unicodedata.category(chr(cp)) == "Cn"
    ]
    assert table_sources_unassigned_here == [], (
        "a look-alike table source is unassigned on this interpreter"
    )


def test_lead_probe_4_the_four_capitals_against_the_latin_names():
    """The lead's probe 4 of review 3: Eta Howard, Mu Mark, Nu Nick, Upsilon Yan. The single key reads n, u, v, u; the readings read the capital."""
    for latin, greek, single in (
        ("Howard", "\u0397oward", "noward"),
        ("Mark", "\u039cark", "uark"),
        ("Nick", "\u039dick", "vick"),
        ("Yan", "\u03a5an", "uan"),
    ):
        assert bare(identity_key(greek)) == single, f"the single reading of {greek!a} changed"
        assert bare(identity_key(latin)) != bare(identity_key(greek)), (
            "the single key became a comparator"
        )
        assert could_be_same_person(latin, greek), (
            f"could_be_same_person({latin}, {greek!a}) is False"
        )
        assert (
            could_be_same_person(greek, latin)
            and could_be_same_person(latin.lower(), greek)
            and could_be_same_person(latin.upper(), greek)
        )


# ---- spacing marks, modifier letters and modifier symbols (P1a fix4, review 4 finding 2) -----------------------------------------------
def _code_points_of(*categories):
    return [
        chr(cp) for cp in range(sys.maxunicode + 1) if unicodedata.category(chr(cp)) in categories
    ]


def test_squeeze_views_finds_a_secret_hidden_with_every_spacing_mark_modifier_letter_or_modifier_symbol():
    """The redaction contract for letters and digits: for EVERY code point of category Mc (spacing combining mark), Lm (modifier letter) or Sk
    (modifier symbol) of this interpreter, ``squeeze_views("pass" + c + "word")`` holds ``PASSWORD``. There is NO exemption list: the
    characters that NFKC or the look-alike table read as a letter (superscript h, a Telugu or Malayalam anusvara that the table reads as o,
    an Oriya visarga that it reads as 8) are removed by the marks-dropped views before either runs."""
    for category in ("Mc", "Lm", "Sk"):
        chars = _code_points_of(category)
        assert chars, f"this interpreter has no code point of category {category}"
        for ch in chars:
            views = textnorm.squeeze_views("pass" + ch + "word")
            assert "PASSWORD" in views, (
                f"squeeze_views misses a secret hidden with U+{ord(ch):04X} ({category}): {views}"
            )
            assert "PASSWORD" in textnorm.squeeze_views("PASS" + ch + "WORD", loose=False)
    # the letters the old views read in the mark's place are still there as the OTHER views: the spelling variants are unchanged
    assert "PASSOWORD" in textnorm.squeeze_views("pass\u0c02word"), (
        "the spelling-variant views changed: U+0C02 no longer reads as the letter o there"
    )


def test_squeeze_views_removes_every_character_that_reads_as_no_ascii_letter_or_digit():
    """For every assigned code point ``c`` that ``squeeze`` reads as nothing (a space, punctuation, a symbol, a mark, a format
    character), ``squeeze_views("pass" + c + "word")`` holds ``PASSWORD``: the pattern that keeps only upper-case letters and digits is the
    last step of every view, so no separator hides a word."""
    checked = 0
    for cp in range(0x30000):
        ch = chr(cp)
        if unicodedata.category(ch) in ("Cs", "Co", "Cn", "Lu", "Ll", "Lt", "Lo", "Nd", "Nl", "No"):
            continue
        if re.search(r"[A-Za-z0-9]", unicodedata.normalize("NFKC", ch)) or cp in _confusables.TABLE:
            continue  # it reads as a letter or a digit itself: it is not a separator
        if squeeze(ch) != "":
            continue  # ``squeeze`` (its own pattern, not the one under test) reads it as a letter or digit
        checked += 1
        assert "PASSWORD" in textnorm.squeeze_views("pass" + ch + "word"), (
            f"squeeze_views does not remove U+{cp:04X} ({unicodedata.category(ch)}) from the middle of a word"
        )
    assert checked > 3000, "too few code points were checked"


def test_the_marks_dropped_views_are_at_most_six_for_squeeze_and_nine_for_fold_and_keep_every_script_and_letter():
    """``squeeze_views`` returns the spelling variants (at most three) and the same spelling variants of the text without its Mc, Lm and Sk
    characters: at most six, none repeated. ``fold_views`` adds the script view of each marks-dropped variant: at most nine. A text without
    such a mark has no extra view. ``identity_keys`` also holds at most six (F6-1): for each text with a spacing mark it holds the check name of
    the marks-dropped text, and a text without one has at most three."""
    eta = "\u0397"
    for text in (
        "pass\u0c02word",
        eta + "\u0903oward",
        "plain",
        "\u0928\u092e\u0938\u094d\u0924\u0947\u0903",
    ):
        for views, limit in (
            (
                textnorm.fold_views(text, casefold=True, scripts=textnorm.value_scripts(text)),
                9,
            ),
            (textnorm.squeeze_views(text), 6),
        ):
            assert 1 <= len(views) <= limit and len(set(views)) == len(views), (
                f"a view is repeated or there are more than the limit {limit}: {views}"
            )
        keys = textnorm.identity_keys(text)
        assert 1 <= len(keys) <= 6, "identity_keys grew past six check names"
        has_mark = any(unicodedata.category(ch) in ("Mc", "Lm", "Sk") for ch in text)
        assert len(keys) <= (6 if has_mark else 3), (
            "a text with no spacing mark has more than three"
        )
        if has_mark:
            dropped = "".join(
                ch for ch in text if unicodedata.category(ch) not in ("Mc", "Lm", "Sk")
            )
            assert identity_key(dropped) in keys, (
                "identity_keys does not hold the check name of the marks-dropped text"
            )
    assert len(textnorm.fold_views("plain", casefold=True, scripts=frozenset())) == 1, (
        "a text with no mark has an extra view"
    )
    # a Greek capital Eta (reads H in the upper-side variant) AND an inserted mark in one text: the marks-dropped views carry every variant
    assert "HOWARD" in textnorm.squeeze_views(eta + "\u0903oward"), (
        "capital Eta + a spacing mark hides howard from the scan"
    )
    # nothing else is lost: the marks-dropped view keeps the script
    assert "\u5bc6\u7801" in textnorm.fold_views(
        "\u5bc6\u02c6\u7801", casefold=True, scripts=frozenset()
    )


def test_the_marks_dropped_views_are_never_longer_than_the_weight_of_the_text():
    """The size rule still holds with the extra views: no view of ``fold_views`` or ``squeeze_views`` is longer than the weight of its text, for
    every code point alone (a view only drops characters, so a longer text is the sum)."""
    for cp in range(sys.maxunicode + 1):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        text = chr(cp)
        weight = textnorm._weight(text)
        for views in (
            textnorm.fold_views(text, casefold=True, collapse_ws=True, scripts=frozenset()),
            textnorm.squeeze_views(text, loose=True),
        ):
            assert all(len(v) <= weight for v in views), (
                f"a view of U+{cp:04X} is longer than its weight {weight}"
            )


def test_identity_key_keeps_a_spacing_mark_while_the_deny_check_and_the_scan_views_drop_it():
    """Decision: Mc is KEPT by the spelling variants (``fold``, ``identity_key``): a Hindi or Thai spacing vowel sign changes the single check
    name. This is REVERSED for the DENY check only (F6-1, ORDER 177): for EVERY Mc code point ``could_be_same_person`` is True for the text with the
    mark and the text without it (a person must look), the pin of the reversal of ORDER 79 item 3. The scan is not affected: for EVERY Mc code
    point ``fold_views`` holds the secret in its marks-dropped views, so the module docstring's rule (scan both views) is the whole contract."""
    marks = _code_points_of("Mc")
    assert marks
    for ch in marks:
        text = "pass" + ch + "word"
        assert "password" not in identity_key(text), (
            f"identity_key dropped the spacing mark U+{ord(ch):04X}"
        )
        assert identity_key(text) != identity_key("password"), (
            f"identity_key dropped the spacing mark U+{ord(ch):04X}"
        )
        assert could_be_same_person(text, "password"), (
            f"could_be_same_person does not see through the spacing mark U+{ord(ch):04X}"
        )
        assert "password" in textnorm.fold_views(text, casefold=True, scripts=frozenset()), (
            f"fold_views does not hold the secret hidden with the spacing mark U+{ord(ch):04X}"
        )
    doc = textnorm.__doc__ or ""
    assert "BOTH" in doc and "fold_views" in doc and "squeeze_views" in doc, (
        "the module docstring does not say that a scan must read both views"
    )
    for false_claim in ("drops legitimate marks", "for any combining mark,"):
        assert false_claim not in doc, f"the module docstring claims again: {false_claim}"
    assert "KEEPS the spacing" in doc and "Mc" in doc, (
        "the docstring does not say that spacing marks are kept"
    )
    assert "DENY check" in doc and "DROPS those three kinds" in doc, (
        "the docstring does not say that the DENY check drops the spacing marks"
    )


def _scan_holds(secret, text):
    """The documented two-view scan, with the refusal of an empty needle: True when some view of ``text`` (``fold_views``, then
    ``squeeze_views``) holds a NON-EMPTY view of ``secret`` taken the same way."""
    scripts = textnorm.value_scripts(secret)
    for views_of in (
        lambda t: textnorm.fold_views(t, casefold=True, scripts=scripts),
        textnorm.squeeze_views,
    ):
        needles = [n for n in views_of(secret) if n]
        if any(n in v for v in views_of(text) for n in needles):
            return True
    return False


def test_a_value_with_no_ascii_letter_or_digit_is_found_by_the_fold_views_scan_when_a_mark_is_inserted():
    """Chinese, Hindi and Thai protected values: ``squeeze_views`` is empty for them (a caller must refuse an empty view), so the scan relies on
    the marks-dropped views of ``fold_views``. A Devanagari word with a visarga (Mc), Chinese with a modifier letter, Thai with a tone mark
    and with a modifier letter inserted: each is found, and a text that does not hold the value is not found."""
    devanagari = "\u092a\u093e\u0938\u0935\u0930\u094d\u0921"
    chinese = "\u5bc6\u7801\u6d4b\u8bd5"
    thai = "\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19"
    cases = (
        ("Devanagari + U+0903", devanagari, devanagari[:3] + "\u0903" + devanagari[3:]),
        ("Chinese + U+02C6", chinese, chinese[:2] + "\u02c6" + chinese[2:]),
        ("Thai + the maiyamok U+0E46 (Lm)", thai, thai[:4] + "\u0e46" + thai[4:]),
        ("Thai + U+02C6", thai, thai[:4] + "\u02c6" + thai[4:]),
    )
    for label, secret, hidden in cases:
        assert textnorm.squeeze_views(secret) == ("",), (
            f"{label}: the value has an ASCII letter or digit"
        )
        assert _scan_holds(secret, "token: " + hidden + " end"), (
            f"{label}: the scan misses the value with the mark inserted"
        )
        assert not _scan_holds(secret, "token: nothing here"), (
            f"{label}: the scan finds a text without the value"
        )
    assert not _scan_holds(chinese, "\u5bc6\u7801"), "a different value was found"
    doc = textnorm.fold_views.__doc__ or ""
    assert _squash(SCAN_COVERAGE) in _squash(doc), (
        "the fold_views docstring does not say what a scan of a value with no ASCII letter or digit relies on"
    )


# ---- fix6: the script views, the minimum length, the case rule, the documented limits --------------------------------------------------
CHINESE = "\u5bc6\u7801\u6d4b\u8bd5"  # four ideographs
HINDI = "\u092a\u093e\u0938\u0935\u0930\u094d\u0921"  # "password" in Devanagari, with an Mc (U+093E) and an Mn (virama)
THAI = "\u0e23\u0e2b\u0e31\u0e2a\u0e1c\u0e48\u0e32\u0e19"
INSERTED_TEXTS = {
    "a space": " ",
    "a hyphen": "-",
    "a line feed": "\n",
    "a carriage return and line feed": "\r\n",
    "a line separator (U+2028)": "\u2028",
    "a no-break space": "\u00a0",
    "a full stop": ".",
    "an ASCII letter": "q",
    "an upper-case ASCII letter": "Q",
    "an ASCII digit": "7",
    "a zero-width space": "\u200b",
}


def _scan(value, text):
    """The documented scan, whole: the needles of ``scan_needles(value)`` against every ``fold_views(text, casefold=True, collapse_ws=True,
    scripts=value_scripts(value))`` and ``squeeze_views(text)`` view. ``ViewTooShort`` propagates (a caller refuses)."""
    needles = textnorm.scan_needles(value)
    views = (
        *textnorm.fold_views(
            text, casefold=True, collapse_ws=True, scripts=textnorm.value_scripts(value)
        ),
        *textnorm.squeeze_views(text),
    )
    return any(n in v for n in needles for v in views)


def _must_refuse(value, why):
    """``scan_needles(value)`` must raise ``ViewTooShort``; otherwise fail with ``why`` as the first line of the report."""
    try:
        needles = textnorm.scan_needles(value)
    except textnorm.ViewTooShort:
        return
    raise AssertionError(f"scan_needles accepted {value!r}: {why} (needles {needles})")


def _accepted(value, why):
    """``scan_needles(value)``, failing with ``why`` as the first line of the report when it raises ``ViewTooShort``."""
    try:
        return textnorm.scan_needles(value)
    except textnorm.ViewTooShort as caught:
        raise AssertionError(f"scan_needles refused {value!r}: {why} ({caught})") from None


def test_a_separator_an_ascii_letter_or_a_mark_inserted_into_a_chinese_hindi_or_thai_value_does_not_hide_it():
    """For a value with no ASCII letter or digit ``squeeze_views`` is ``""`` and the old scan relied on the marks-dropped views, which a
    space, a hyphen, a line break or an ASCII letter defeated. The script view removes them. Every value, at every position, with every
    inserted text of ``INSERTED_TEXTS`` is found; and a benign text (the value missing a character, the characters swapped, another value
    of the same script) is not."""
    benign = {
        CHINESE: (
            "token: nothing here",
            "\u5bc6\u6d4b\u8bd5",
            "\u7801\u5bc6\u6d4b\u8bd5",
            "\u5bc6 \u7801",
        ),
        HINDI: (
            "token: nothing here",
            HINDI[:-1],
            HINDI[::-1],
            "\u0928\u092e\u0938\u094d\u0924\u0947",
        ),
        THAI: (
            "token: nothing here",
            THAI[:-1],
            THAI[::-1],
            "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35",
        ),
    }
    for value, negatives in benign.items():
        assert textnorm.squeeze_views(value) == ("",), "the value has an ASCII letter or digit"
        assert _scan(value, value), "the value is not found in itself"
        for label, extra in INSERTED_TEXTS.items():
            for pos in range(1, len(value)):
                hidden = value[:pos] + extra + value[pos:]
                assert _scan(value, "token: " + hidden + " end"), (
                    f"the scan misses {value!r} with {label} inserted at {pos}"
                )
        for text in negatives:
            assert not _scan(value, text), f"the scan finds {value!r} in the benign text {text!r}"


def test_a_value_in_a_script_view_is_found_across_every_inserted_text_at_once():
    """Several insertions in one text (a space, a letter, a line break and a hyphen) and the script view of the text itself."""
    for value in (CHINESE, HINDI, THAI):
        pieces = [value[0]] + [c for c in value[1:]]
        hidden = " q-\n".join(pieces)
        assert _scan(value, hidden), f"several insertions hide {value!r}"
        scripts = textnorm.value_scripts(value)
        assert (
            textnorm.fold_views(value, casefold=True, collapse_ws=True, scripts=scripts)[-1]
            in textnorm.fold_views(hidden, casefold=True, collapse_ws=True, scripts=scripts)[-1]
        ), "the last (script) view of the text does not hold the value"


def test_the_script_view_keeps_only_letters_of_the_given_scripts_and_is_left_out_when_empty_or_repeated():
    """The script view holds LETTERS only. The old docstrings said "letters and marks", but no mark can reach the view
    (Mn and Me are dropped, Mc, Lm and Sk are removed before the marks-dropped views are made), so the real rule is letters of the value's scripts."""
    han = frozenset({"HAN"})
    views = textnorm.fold_views("ab \u5bc6-\u7801 7", casefold=True, scripts=han)
    assert "\u5bc6\u7801" in views, (
        "the script view of a text with a separator, ASCII letters and a digit is missing"
    )
    assert textnorm._script_view("ab \u5bc6-\u7801 7!", han) == "\u5bc6\u7801"
    # a value of Latin letters that the table leaves alone has the group LATIN: the ASCII letters of a text are still not in the view
    assert textnorm._script_view("\u0294x\u0295Y", frozenset({"LATIN"})) == "\u0294\u0295", (
        "the script view keeps an ASCII letter"
    )
    # not a letter: an ideographic full stop (Po), a currency sign (Sc), an emoji (So), the ideographic zero (Nl), a Chinese numeral is a letter
    # (U+2E80 and U+31C0 are symbols whose name starts with CJK, so only the letter test keeps them out)
    for non_letter in ("\u3002", "\u20ac", "\U0001f600", "\u3007", "\u2460", "\u2e80", "\u31c0"):
        assert textnorm._script_view("\u5bc6" + non_letter + "\u7801", han) == "\u5bc6\u7801", (
            f"the script view keeps the non-letter U+{ord(non_letter):04X}"
        )
    thai = frozenset({"THAI"})  # U+0E3F is a currency symbol whose name starts with THAI
    assert textnorm._script_view("\u0e01\u0e3f\u0e02", thai) == "\u0e01\u0e02", (
        "the script view keeps the non-letter U+0E3F"
    )
    for ascii_text in ("plain", "pass word 12", "-- ++"):
        assert all(v.isascii() for v in textnorm.fold_views(ascii_text, casefold=True, scripts=han))
        assert all(v for v in textnorm.fold_views(ascii_text, casefold=True, scripts=han)[1:]), (
            "an empty script view was kept"
        )
    assert len(textnorm.fold_views("plain", casefold=True, scripts=han)) == 1, (
        "an ASCII text got a script view"
    )
    chinese_views = textnorm.fold_views(CHINESE, casefold=True, scripts=han)
    assert chinese_views == (CHINESE,), "the script view of a text that is only script is repeated"
    assert textnorm.fold_views(CHINESE, casefold=True, scripts=frozenset()) == (CHINESE,)
    assert (
        textnorm.fold_views("ab \u5bc6-\u7801", casefold=True, scripts=frozenset())[-1]
        == "ab \u5bc6-\u7801"
    ), "fold_views without scripts made a script view"


def test_the_script_view_of_a_hindi_value_is_its_letters_with_the_vowel_signs_gone():
    """The real rule, shown on Hindi "password". U+093E (aa) is a spacing mark (Mc): the marks-dropped views remove it
    before the fold, and the virama U+094D is a non-spacing mark (Mn): the fold drops it. What is left is the consonant skeleton. The scan still finds
    the value, and a text with the vowel signs left out is found too: the skeleton is the same (an over-match, the safe side)."""
    assert unicodedata.category("\u093e") == "Mc" and unicodedata.category("\u094d") == "Mn"
    scripts = textnorm.value_scripts(HINDI)
    assert scripts == {"DEVANAGARI"}
    skeleton = "\u092a\u0938\u0935\u0930\u0921"
    views = textnorm.fold_views(HINDI, casefold=True, scripts=scripts)
    assert skeleton in views, "the script view of the Hindi value is not its consonant skeleton"
    spelling = textnorm.fold(HINDI, casefold=True)
    assert spelling in views and spelling != skeleton, "the spelling view that keeps the Mc is gone"
    assert "\u093e" in spelling and "\u094d" not in spelling
    assert textnorm._script_view(spelling, scripts) == skeleton, "a mark is in a script view"
    assert all(unicodedata.category(ch)[0] == "L" for ch in skeleton), "a mark is in the skeleton"
    assert _scan(HINDI, "x " + skeleton + " y"), "the skeleton alone is not found"
    doc = _squash(textnorm.__doc__ or "") + _squash(textnorm.fold_views.__doc__ or "")
    assert "no mark is ever in a script view" in doc, (
        "the module docstring does not say that no mark reaches a script view"
    )
    assert "letters and marks" not in doc and "letters or marks" not in doc, (
        "a docstring says again that the script view keeps marks"
    )
    log = ROOT / "CHANGELOG.md"
    if log.exists():
        fix7 = log.read_text(encoding="utf-8").split("`fold4` fix7", 1)[-1]
        assert "keeps the non-ASCII letters and marks" not in fix7


def test_the_minimum_view_length_is_one_number_per_kind_of_view_and_a_short_value_is_refused(
    monkeypatch,
):
    """``defaults`` holds one minimum per KIND of view: spelling 2, squeeze 4, script 4, ideograph 2. Each is read when
    ``scan_needles`` runs. The error is a ``TextnormError`` (not a ``ValueError``) and carries no part of the value."""
    assert (
        defaults.TEXTNORM_MIN_SPELLING_CHARS,
        defaults.TEXTNORM_MIN_SQUEEZE_CHARS,
        defaults.TEXTNORM_MIN_SCRIPT_CHARS,
        defaults.TEXTNORM_MIN_IDEOGRAPH_CHARS,
        defaults.TEXTNORM_MIN_DIGIT_CHARS,
    ) == (2, 4, 4, 2, 6), "a minimum of defaults is not the pinned one"
    assert not hasattr(defaults, "TEXTNORM_MIN_VIEW_CHARS"), "the one global minimum is back"
    for short in (
        "",
        "x",
        "\u200b",
        "\u5bc6",
        "\u5bc6 ",
        "7",
        " \u5bc6\n",
        "Li",
        "Amy",
        "\u0e23\u0e2b\u0e31",
    ):
        try:
            textnorm.scan_needles(short)
        except textnorm.ViewTooShort as caught:
            refusal = caught
        else:
            raise AssertionError(f"scan_needles accepted {short!r}: no view is long enough")
        # asserted outside the handler, so the first failing line is the assertion and not the refusal that was caught
        assert isinstance(refusal, TextnormError) and not isinstance(refusal, ValueError)
        text = str(refusal)
        if short.strip():
            assert repr(short) not in text, "the message holds the value"
            if short == "x":
                # the one value that is a letter of the fixed words ("exact-match"): it must not stand alone as a token (between spaces,
                # quotes, brackets or at an end), which is how a leaked value would show
                assert re.search(r"(?<![\w-])x(?![\w-])", text) is None, (
                    "the message holds the value"
                )
            else:
                assert short not in text and short.strip() not in text, (
                    "the message holds the value"
                )
    value = "\u5bc6\u7801\u6d4b\u8bd5abcd"
    families = {
        "spelling view": value.casefold(),
        "script view": CHINESE,
        "squeeze view": "ABCD",
    }
    for squeeze_min, script_min, spelling_min, expected in (
        (4, 4, 2, {"spelling view", "script view", "squeeze view"}),
        (5, 4, 2, {"spelling view", "script view"}),
        (4, 5, 2, {"spelling view", "squeeze view"}),
        (4, 4, 9, {"script view", "squeeze view"}),
        (4, 4, 8, {"spelling view", "script view", "squeeze view"}),
    ):
        monkeypatch.setattr(defaults, "TEXTNORM_MIN_SQUEEZE_CHARS", squeeze_min)
        monkeypatch.setattr(defaults, "TEXTNORM_MIN_SCRIPT_CHARS", script_min)
        monkeypatch.setattr(defaults, "TEXTNORM_MIN_SPELLING_CHARS", spelling_min)
        needles = textnorm.scan_needles(value)
        present = {name for name, v in families.items() if v in needles}
        assert present == expected, (
            f"wrong views at the minimums {(squeeze_min, script_min, spelling_min)}: needles {needles}, kinds {present}"
        )
    monkeypatch.setattr(defaults, "TEXTNORM_MIN_SQUEEZE_CHARS", 5)
    monkeypatch.setattr(defaults, "TEXTNORM_MIN_SCRIPT_CHARS", 5)
    _must_refuse(value, "no squeeze or script view reaches its minimum of 5")


def test_a_squeeze_view_needs_four_characters_so_a_short_latin_name_is_refused():
    """The squeeze view of a 2 or 3 letter Latin value ("Li", "Amy") is found in almost any English text; the old single minimum of 2
    let it in. Now it is refused (the caller uses its own exact search), and four letters are scanned."""
    for name, text in (("Li", "a believer"), ("Amy", "ha my day")):
        assert name.upper() in textnorm.squeeze_views(text)[0], (
            "the row does not show the over-match"
        )
        _must_refuse(name, "a squeeze view of fewer than four letters is a needle")
    assert "ANNA" in _accepted("Anna", "a four-letter squeeze view is not a needle"), (
        "a four-letter squeeze view is not a needle"
    )
    assert not _scan("Anna", "the family")
    assert _scan("Anna", "x A-n n.a y")


def test_a_script_view_needs_four_letters_but_two_ideographs_are_a_name():
    """The script minimum is tied to the value's own script letters. A 3-letter Thai or Cyrillic value gives a 3-letter
    needle that any text of that script holds: refused. A value that is only Han ideographs may be two long (a name); one ideograph is refused. A
    mixed value ("pw" plus ideographs) has a script part that alone is a weak needle: it needs four."""
    thai3 = "\u0e01\u0e02\u0e04"
    thai4 = "\u0e01\u0e02\u0e04\u0e07"
    cyr3 = "\u0436\u0434\u0436"
    for value in (thai3, cyr3, "\u674e", "\u674e\U0001f600"):
        _must_refuse(value, "a script view of fewer than four letters is a needle")
    assert _accepted(thai4, "a four-letter script view is not a needle") == (thai4,)
    assert _accepted("\u674e\u660e", "a two-ideograph name is not a needle") == ("\u674e\u660e",)
    assert _accepted("\u674e \u660e", "a two-ideograph name with a space is not a needle") == (
        "\u674e \u660e",
        "\u674e\u660e",
    ), "the spelling view of a two-ideograph name with a space is not a needle"
    for mixed in ("pw\u4e2d\u6587", "\u4e2d\u6587" + "7", "w\u4e2d"):
        _must_refuse(mixed, "the script part of a mixed value is a needle at two letters")
    assert "\u4e2d\u6587\u6d4b\u8bd5" in _accepted(
        "pw\u4e2d\u6587\u6d4b\u8bd5", "a four-letter script part of a mixed value is not a needle"
    ), "a four-letter script part of a mixed value is not a needle"
    # the ideograph minimum applies to a value of Han alone, not to Han plus kana
    _must_refuse("\u674e\u3042", "the ideograph minimum was used for Han plus kana")


def test_a_value_found_only_by_a_view_that_keeps_separators_is_refused():
    """A value of "w" plus one ideograph, an ideograph plus "5", a one-letter name: the squeeze and script views are one character and dropped; the
    exact-spelling view alone is left, and one inserted space would hide the value. ``scan_needles`` raises ``ViewTooShort`` and says so."""
    for value in ("w\u5bc6", "\u5bc6" + "5", "ab", "a\u5bc6", "\u0e01 \u0e02"):
        try:
            textnorm.scan_needles(value)
        except textnorm.ViewTooShort as caught:
            assert "squeeze" in str(caught) and "script" in str(caught)
            assert value not in str(caught)
        else:
            raise AssertionError(
                f"scan_needles returned a needle for {value!r}, which a space hides"
            )
    assert (
        textnorm.fold_views("w\u5bc6", casefold=True, collapse_ws=True, scripts=frozenset())[0]
        == "w\u5bc6"
    ), "the spelling view the old code would have returned is not there"


def test_scan_needles_returns_each_needle_once_and_checks_the_text_first():
    needles = textnorm.scan_needles("Password")
    assert len(needles) == len(set(needles)) and "password" in needles and "PASSWORD" in needles
    with pytest.raises(NotText):
        textnorm.scan_needles(b"password")  # type: ignore[arg-type]
    with pytest.raises(TextTooLong):
        textnorm.scan_needles("a" * (CAP + 1))
    doc = textnorm.__doc__ or ""
    assert "scan_needles" in doc and all(
        name in doc
        for name in (
            "TEXTNORM_MIN_SPELLING_CHARS",
            "TEXTNORM_MIN_SQUEEZE_CHARS",
            "TEXTNORM_MIN_SCRIPT_CHARS",
            "TEXTNORM_MIN_IDEOGRAPH_CHARS",
        )
    ), "the module docstring does not name the minimums for P1b"


def test_loose_loosens_only_the_squeeze_half_of_the_needles():
    """``loose=True`` reads the digit-like letters as digits in the squeeze views only; the spelling views and the script views are the same."""
    plain = textnorm.scan_needles("Password")
    loose = textnorm.scan_needles("Password", loose=True)
    assert "PASSWORD" in plain and "PA55W0RD" not in plain
    assert "PA55W0RD" in loose, "loose=True did not loosen the squeeze half"
    assert "password" in loose and "pa55w0rd" not in loose, "loose=True changed a spelling view"
    mixed = "Password\u5bc6\u7801\u6d4b\u8bd5"
    assert [n for n in textnorm.scan_needles(mixed) if not n.isascii()] == [
        n for n in textnorm.scan_needles(mixed, loose=True) if not n.isascii()
    ], "loose=True changed a script view"
    doc = _squash(textnorm.scan_needles.__doc__ or "")
    assert "loosens only the squeeze half" in doc, "the docstring does not say what loose loosens"


def test_a_scan_built_without_casefold_misses_a_case_variant_and_the_rule_says_to_pass_casefold():
    """``fold_views(casefold=False)`` keeps case (for display and comparison callers). A scan built on it misses "SECRET" for the value
    "secret"; the documented scan passes ``casefold=True`` and finds both. The default is kept; this test documents why the docstring says
    to pass the flag, and fails if the documented scan stops finding an upper/lower variant."""
    for value, text in (
        ("secret-token", "x SECRET-TOKEN x"),
        ("SECRET-TOKEN", "x secret-token x"),
        ("Straße", "STRASSE"),
    ):
        assert _scan(value, text), (
            f"the documented scan misses a case variant: {value!r} in {text!r}"
        )
        folded_value = textnorm.fold_views(
            value, scripts=frozenset()
        )  # casefold=False, the default
        folded_text = textnorm.fold_views(text, scripts=frozenset())
        assert not any(n in v for n in folded_value for v in folded_text if n), (
            "the case-keeping default found the variant: the default changed, so the rule in the docstring is out of date"
        )
    doc = _squash((textnorm.__doc__ or "") + (textnorm.fold_views.__doc__ or ""))
    assert "pass ``casefold=True``" in doc.replace(
        "PASS ``casefold=True, collapse_ws=True``", "pass ``casefold=True``"
    ), "THE RULE FOR A SCAN does not say to pass casefold=True"


def test_the_documented_limit_a_modifier_letter_that_replaces_a_letter_with_another_inserted_is_not_caught():
    """A limit stated in the module docstring ("No exemption" holds for INSERTION only). "pa" + superscript s + "s" + superscript h + "word":
    the first modifier letter stands for the letter s, the second is inserted. The marks-dropped views lose the s the first one stood for; the
    other views read the inserted one as an h. No view holds PASSWORD. If this starts to pass, move the case into the insertion test and update the docstring."""
    text = "pa\u02e2s\u02b0word"
    assert unicodedata.category("\u02e2") == "Lm" and unicodedata.category("\u02b0") == "Lm"
    assert not any("PASSWORD" in v for v in textnorm.squeeze_views(text)), (
        "a modifier-letter replacement is now caught: the documented limit is out of date"
    )
    assert any("PASWORD" in v for v in textnorm.squeeze_views(text)), (
        "the marks-dropped view changed"
    )
    doc = _squash(textnorm.__doc__ or "")
    assert "INSERTION only" in doc and "NOT caught" in doc, "the docstring does not state the limit"


def test_the_coverage_sentences_are_the_same_in_every_place_that_states_them():
    """ONE coverage sentence for the name rules in ``textnorm.py``, ``tools/gen_confusables.py`` and the CHANGELOG, and one for the
    scan of a script value in ``textnorm.py`` (module and ``fold_views`` docstrings) and the CHANGELOG."""
    gen = (ROOT / "tools" / "gen_confusables.py").read_text(encoding="utf-8")
    sources = {
        "textnorm module docstring": textnorm.__doc__ or "",
        "generator docstring": gen,
    }
    log = ROOT / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        sources["CHANGELOG"] = log.read_text(encoding="utf-8")
    for place, text in sources.items():
        assert _squash(NAME_COVERAGE) in _squash(text), (
            f"{place}: the name-rule coverage sentence differs"
        )
    scan_places = {
        "textnorm module docstring": textnorm.__doc__ or "",
        "fold_views docstring": textnorm.fold_views.__doc__ or "",
    }
    if "CHANGELOG" in sources:
        scan_places["CHANGELOG"] = sources["CHANGELOG"]
    for place, text in scan_places.items():
        assert _squash(SCAN_COVERAGE) in _squash(text), (
            f"{place}: the scan coverage sentence differs"
        )


def test_the_module_does_not_export_a_second_name_for_the_table():
    """The import alias ``CONFUSABLES`` was a public-looking name beside ``_confusables.TABLE``; it is private now."""
    assert not hasattr(textnorm, "CONFUSABLES") and "CONFUSABLES" not in textnorm.__all__
    assert textnorm._CONFUSABLES is _confusables.TABLE


def test_step_three_keeps_every_whitespace_character_and_the_sk_wording_is_exact():
    """The docstring said that line and paragraph separators are dropped; they are kept and become a space, like tab and line feed. And only a
    COMPATIBILITY Sk becomes a space: the diaeresis and the small tilde do, the grave accent and the circumflex stay."""
    for ws in ("\t", "\n", "\r", "\u2028", "\u2029", "\u00a0", "\u3000"):
        assert fold("a" + ws + "b") == "a b", f"U+{ord(ws):04X} did not become a space"
    for compat in ("\u00a8", "\u02dc"):
        assert unicodedata.category(compat) == "Sk" and fold("a" + compat + "b") == "a b"
    for other in ("`", "^", "\u02c2"):
        assert unicodedata.category(other) == "Sk" and fold("a" + other + "b") == "a" + other + "b"
    doc = _squash(textnorm.__doc__ or "")
    assert "EXCEPT that every whitespace character" in doc and "U+2028" in doc
    assert "a compatibility Sk" in doc and "line and paragraph separator, private-use" not in doc, (
        "the docstring step 3 or the Sk wording is the old one"
    )


# ---- fix7: the script view per script, the minimum per kind, the documented limits ----------------------------------------------------
ARABIC = "\u0643\u0644\u0645\u0629\u0645\u0631\u0648\u0631"  # "password" in Arabic: no letter of it reads as an ASCII letter
HEBREW = "\u05d1\u05d2\u05d3\u05d4\u05d6\u05d7"  # six Hebrew letters that the table leaves alone (samekh would read "o")
SCRIPT_VALUES = {
    "Chinese": (CHINESE, "HAN"),
    "Hindi": (HINDI, "DEVANAGARI"),
    "Thai": (THAI, "THAI"),
    "Arabic": (ARABIC, "ARABIC"),
    "Hebrew": (HEBREW, "HEBREW"),
}
# one letter of another script each; the fold keeps every one of them as a non-ASCII letter (a test checks it)
FOREIGN_LETTERS = {
    "a Cyrillic zhe": "\u0436",
    "a Greek delta": "\u03b4",
    "a Hebrew alef": "\u05d0",
    "a hiragana a": "\u3042",
    "a katakana a": "\u30a2",
    "a Latin glottal stop": "\u0294",
    "a Latin wynn": "\u01bf",
    "an Arabic beh": "\u0628",
    "a Thai ko kai": "\u0e01",
    "a Devanagari ka": "\u0915",
    "a Han ideograph": "\u7684",
}
SAME_SCRIPT_LETTER = {
    "Chinese": "\u7684",
    "Hindi": "\u0915",
    "Thai": "\u0e01",
    "Arabic": "\u0628",
    "Hebrew": "\u05d0",
}


def test_a_letter_of_another_script_inserted_at_any_position_does_not_hide_a_script_value():
    """The script view keeps only the letters of the VALUE's scripts. A Cyrillic zhe, a Greek delta, a Hebrew alef, a kana, a
    Latin letter that the table does not fold, and the letters of the other scripts, inserted at EVERY position (also the first and the last) of a
    Chinese, Hindi, Thai, Arabic and Hebrew value, are dropped like an ASCII letter; the value is found. Before fix7 every one of the interior
    positions hid the value."""
    for label, (value, script) in SCRIPT_VALUES.items():
        assert textnorm.value_scripts(value) == {script}, label
        assert textnorm.squeeze_views(value) == ("",), (
            f"{label}: the value has an ASCII letter or digit"
        )
        for what, letter in FOREIGN_LETTERS.items():
            if script in textnorm.value_scripts(letter):
                continue  # the same script: the documented limit, pinned in the next test
            kept = [
                v
                for v in textnorm.fold_views(letter, casefold=True, scripts=frozenset())
                if not v.isascii()
            ]
            assert kept and textnorm.value_scripts(letter), (
                f"{what} is folded to ASCII: the row would prove nothing"
            )
            for pos in range(len(value) + 1):
                hidden = value[:pos] + letter + value[pos:]
                assert _scan(value, "token: " + hidden + " end"), (
                    f"{label}: the scan misses the value with {what} inserted at {pos}"
                )
        assert not _scan(value, "token: nothing here"), (
            f"{label}: a text without the value was found"
        )


def test_a_letter_of_the_same_script_inserted_into_a_script_value_still_hides_it_the_documented_limit():
    """fix7: the limit that the coverage sentence states. Another Han ideograph in a Chinese value, another Thai letter in a Thai value and so on is a
    different spelling, not a foreign mark: the script view keeps it and the value is NOT found at an interior position. If this starts to fail, the
    limit is gone: move the cases into the test above and update the sentence."""
    for label, (value, _script) in SCRIPT_VALUES.items():
        letter = SAME_SCRIPT_LETTER[label]
        assert letter not in value
        for pos in range(1, len(value)):
            hidden = value[:pos] + letter + value[pos:]
            assert not _scan(value, "token: " + hidden + " end"), (
                f"{label}: the scan finds the value with a letter of its own script inserted at {pos}: the documented limit is out of date"
            )
        assert _scan(value, "token: " + value + letter + " end"), "the value is not found at an end"
    assert "SAME script" in _squash(textnorm.fold_views.__doc__ or "")


def test_every_letter_of_another_script_is_dropped_from_the_script_view_of_a_chinese_value():
    """fix7, the CLASS: no letter of any other script, anywhere in Unicode, hides a Chinese value. Every code point is inserted into the middle of
    the value; the value is found unless the fold turns the code point into a Han ideograph (a Kangxi radical is the ideograph written another way:
    the same-script limit)."""
    han = frozenset({"HAN"})
    left, right = CHINESE[:2], CHINESE[2:]
    checked = 0
    for cp in range(sys.maxunicode + 1):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        reads = unicodedata.normalize("NFKC", unicodedata.normalize("NFKD", ch))
        if textnorm._scripts_in([reads]) & han:
            continue
        checked += 1
        views = textnorm.fold_views(left + ch + right, casefold=True, collapse_ws=True, scripts=han)
        assert CHINESE in views, f"U+{cp:04X} inserted into a Chinese value hides it"
    assert checked > 1_000_000, "too few code points were checked"


def test_the_script_groups_are_the_first_word_of_the_name_with_han_and_kana_merged():
    """fix7: how the scripts are grouped (``unicodedata`` names only): the first word of the character name; two words for the families that share a
    first word; every CJK ideograph is HAN; Hiragana, Katakana and the old variant kana are KANA; a letter with no name is UNNAMED. The ideographic
    closing mark (a letter by category) is not HAN: only a value that holds it keeps it."""
    group = textnorm._script_of
    assert group("\u5bc6") == group("\U00020000") == group("\uf900") == "HAN", (
        "the CJK ideographs are not one group"
    )
    assert group("\u3042") == group("\u30a2") == group("\U0001b000") == "KANA", (
        "Hiragana and Katakana are not one group"
    )
    hentai = next(
        chr(cp)
        for cp in range(0x1B100, 0x1B200)
        if unicodedata.name(chr(cp), "").startswith("HENTAIGANA")
    )
    assert group(hentai) == "KANA", "the old variant kana are not kana"
    assert group("\u1100") == group("\uac00") == "HANGUL", "Hangul is not one group"
    assert group("\U00010c00") == "OLD TURKIC" and group("\U00010300") == "OLD ITALIC", (
        "OLD TURKIC and OLD ITALIC are one group"
    )
    assert group("\u1950") == "TAI LE" and group("\u1a20") == "TAI THAM", (
        "the Tai scripts are one group"
    )
    assert group("\U00017000") == "UNNAMED" and group("\U00018d00") == "UNNAMED", (
        "a letter with no name is not UNNAMED"
    )
    assert group("\u3006") == "IDEOGRAPHIC", "the ideographic closing mark is read as Han"
    for ch, name in (
        ("\u0436", "CYRILLIC"),
        ("\u03b4", "GREEK"),
        ("\u05d0", "HEBREW"),
        ("\u0294", "LATIN"),
        ("\u0628", "ARABIC"),
    ):
        assert group(ch) == name, f"U+{ord(ch):04X} is not in the group {name}"
    # a Japanese value holds both groups, a Chinese value one, a Latin value none (a letter of the ASCII range is not a script letter)
    assert textnorm.value_scripts("\u5c71\u7530\u3055\u3093") == {"HAN", "KANA"}, (
        "the scripts of a Japanese value are not Han and kana"
    )
    assert textnorm.value_scripts("password") == frozenset(), "a Latin value has a script"
    assert textnorm.value_scripts("password\u5bc6\u7801") == {"HAN"}, (
        "the ASCII letters of a mixed value are a script"
    )
    # a letter whose name starts with FULLWIDTH, HALFWIDTH or MATHEMATICAL never reaches a view: NFKC has made it another letter
    for cp in range(0x80, sys.maxunicode + 1):
        ch = chr(cp)
        if ch.isalpha() and unicodedata.name(ch, "").startswith(
            ("FULLWIDTH", "HALFWIDTH", "MATHEMATICAL")
        ):
            assert unicodedata.normalize("NFKC", ch) != ch, (
                f"U+{cp:04X} would keep its own script group"
            )
    # a Japanese value (Han and kana): a Cyrillic letter inserted is dropped, a kana inserted is the same-script limit; a Han-only
    # value is found with a kana inserted
    japanese = "\u5c71\u7530\u592a\u90ce\u3055\u3093"
    assert _scan(japanese, "x " + japanese[:3] + "\u0436" + japanese[3:] + " y"), (
        "a Cyrillic letter hides a Japanese value"
    )
    assert not _scan(japanese, "x " + japanese[:3] + "\u3042" + japanese[3:] + " y"), (
        "a kana inserted into a Japanese value is found: the same-script limit is gone"
    )
    yamada = "\u5c71\u7530\u592a\u90ce"
    assert _scan(yamada, "x \u5c71\u7530\u3042\u592a\u90ce y"), (
        "a kana hides a value that is only Han"
    )
    assert _scan(yamada, "x \u5c71\u7530\u0436\u592a\u90ce y"), (
        "a Cyrillic letter hides a value that is only Han"
    )


def test_the_scripts_of_a_value_do_not_come_from_its_modifier_letters_or_ascii_letters():
    """fix7: ``value_scripts`` reads the marks-dropped views only. A Chinese value that holds a Thai modifier letter (maiyamok, Lm) has the scripts {HAN}:
    otherwise a Thai letter inserted into the text would be kept and hide the value."""
    value = "\u5bc6\u7801\u0e46\u6d4b\u8bd5"
    assert unicodedata.category("\u0e46") == "Lm"
    assert textnorm.value_scripts(value) == {"HAN"}, "a modifier letter made a script of the value"
    hidden = CHINESE[:2] + "\u0e01" + CHINESE[2:]
    assert _scan(value, "x " + hidden + " y"), (
        "a Thai letter hides a Chinese value with an Lm in it"
    )
    # the script views are made from the text WITHOUT its modifier letters: a Thai maiyamok in the text is not in any script view
    thai = textnorm.value_scripts("\u0e01\u0e02\u0e04\u0e07")
    views = textnorm.fold_views(
        "\u0e01-\u0e02 \u0e46 \u0e04", casefold=True, collapse_ws=True, scripts=thai
    )
    assert "\u0e01\u0e02\u0e46\u0e04" not in views, "a script view keeps a modifier letter"
    assert "\u0e01\u0e02\u0e04" in views, "the script view of the marks-dropped text is missing"


def test_scripts_given_to_fold_views_must_be_a_frozenset_of_text():
    for bad in (None, {"HAN"}, ["HAN"], "HAN", frozenset({1}), frozenset({b"HAN"})):
        try:
            textnorm.fold_views("x", scripts=bad)  # type: ignore[arg-type]
        except NotText:
            continue
        raise AssertionError(f"fold_views accepted scripts = {bad!r}")
    assert textnorm.fold_views("x", scripts=frozenset()) == textnorm.fold_views(
        "x", scripts=frozenset()
    )


def test_the_minimum_constants_are_checked_when_the_module_is_imported_and_when_a_scan_takes_its_needles(
    monkeypatch,
):
    """A minimum of 0, a negative number, a bool, a float, a text or None would let an empty or one-character needle through.
    Each of the five is refused with the name of the constant: by the module when it is imported (a private copy, the module the other tests use
    is not reloaded) and by every ``scan_needles``."""
    names = textnorm._MINIMUM_NAMES
    assert names == (
        "TEXTNORM_MIN_SPELLING_CHARS",
        "TEXTNORM_MIN_SQUEEZE_CHARS",
        "TEXTNORM_MIN_SCRIPT_CHARS",
        "TEXTNORM_MIN_IDEOGRAPH_CHARS",
        "TEXTNORM_MIN_DIGIT_CHARS",
    )
    assert textnorm._validated_minimums() == (2, 4, 4, 2, 6)

    def import_message():
        """The message with which a private copy of the module refuses to be imported, or None when it was imported."""
        spec = importlib.util.spec_from_file_location("_textnorm_probe_minimums", textnorm.__file__)
        probe = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(probe)
        except probe.TextnormError as caught:  # the copy has its own TextnormError class
            return str(caught)
        return None

    for name in names:
        for bad in (0, -1, True, False, 2.0, "4", None):
            monkeypatch.setattr(defaults, name, bad)
            for where, call in (
                ("_validated_minimums", textnorm._validated_minimums),
                ("scan_needles", lambda: textnorm.scan_needles("password")),
            ):
                error = None
                try:
                    call()
                except TextnormError as caught:
                    error = caught
                assert error is not None, f"{where} accepted {name} = {bad!r}"
                assert name in str(error), f"the message does not name {name}"
                assert not isinstance(error, ValueError), "the error is a ValueError"
        monkeypatch.setattr(defaults, name, 0)
        message = import_message()
        assert message is not None, f"the module was imported with {name} = 0"
        assert name in message, f"the message does not name {name}"
        monkeypatch.undo()
    monkeypatch.delattr(defaults, "TEXTNORM_MIN_SQUEEZE_CHARS")
    message = import_message()
    assert message is not None, "the module was imported without TEXTNORM_MIN_SQUEEZE_CHARS"
    assert "TEXTNORM_MIN_SQUEEZE_CHARS" in message, "the message does not name the constant"
    monkeypatch.undo()
    assert textnorm.scan_needles("password")


def test_the_view_bounds_hold_with_the_script_views_and_nine_is_an_upper_bound():
    """fix7: ``fold_views`` with scripts gives at most nine views and ``squeeze_views`` at most six. The highest number found (a search of 150,000
    random texts built from the table) is seven; the perf row builds a text with seven. Nine is the bound by construction, not a count reached."""
    unit = "\u5bc6\u2c66\u039d\u0345\u0903"
    views = textnorm.fold_views(unit, casefold=True, scripts=textnorm.value_scripts(unit))
    assert len(views) == 7 and len(set(views)) == 7, views
    assert "\u5bc6" in views, "the script view of the Han letter is missing"
    assert len(textnorm.squeeze_views(unit)) <= 6


# ---- letter and digit forms (the Unicode-name rules of the generator) ------------------------------------------------------------------
_DIGIT_WORD = dict(
    zip(
        ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"],
        "0123456789",
        strict=True,
    )
)
_NAMED_LETTER = re.compile(r"(?:.* )?(?:LETTER|CAPITAL|SMALL) ([A-Z])(?: WITH .+)?")
_NAMED_DIGIT = re.compile(r"(?:.* )?(?:DIGIT|NUMBER|NUMERAL) (" + "|".join(_DIGIT_WORD) + ")")
# The families of code points that the sweep finds NOT read as the ASCII letter or digit their name says, and why. Every unread row of the
# sweep must be in one of these (a new family is a failing test, so a gap is never silent). The raw list is in the evidence file.
KNOWN_NAME_GAPS = {
    "G1 dropped on purpose": "a combining Latin letter or digit (Mn) and a tag letter or digit (Cf) is dropped like every mark and format "
    "character: reading it would break fold(x + mark) == fold(x); the tag block is reported by has_hidden_channel",
    "G2 numeral of another script or system": "a number sign with a numeric value 0-9 whose glyph is not a digit (Ethiopic, Brahmi, Aegean, "
    "Kaktovik, counting rods, tally marks, ideographic numerals, Siyaq and the like): it has the value but not the look of the digit, so it is "
    "not read as the digit (a reader does not see the digit); the look-alike table may read a few as a letter",
    "G3 turned digit": "TURNED DIGIT TWO and THREE (U+218A, U+218B) are the digits turned over, which are not the digits",
    "G4 read as another letter by UTS #39": "the vendored UTS #39 data reads the letter as a different one than its name says "
    "(V with hook as u, V with palatal hook as y): the data is the authority, the table follows it",
    "G6 letter of another script named like a Latin letter": "SAMARITAN MODIFIER LETTER I and MODIFIER LETTER CYRILLIC SMALL I/U/E "
    "end their names in a Latin letter but are letters of the Samaritan and Cyrillic scripts: the sweep's name grammar catches them, "
    "they are not Latin look-alikes, and a Cyrillic modifier letter next to Latin letters is a mixed-script signal",
    "G7 symbol named like a letter": "SCRIPT CAPITAL P (U+2118, the Weierstrass p) is a mathematical symbol (Sm), not the letter P",
    "G5 negative circled number 11 to 20": "NEGATIVE CIRCLED NUMBER ELEVEN to TWENTY (U+24EB to U+24F4) have no decomposition and the name rules "
    "stop at ten (the circled numbers 11 to 20 are read by NFKC): a named gap, not read",
}


@functools.cache
def _data_prototypes():
    """The vendored UTS #39 file as {source code point: prototype text} (MA lines), read once."""
    text = (ROOT / "tools" / "data" / "confusables.txt").read_text(encoding="utf-8")
    return {
        int(m[1], 16): "".join(chr(int(h, 16)) for h in m[2].split())
        for m in re.finditer(r"^([0-9A-F]{4,6}) ;\t?([0-9A-F ]+);\s*MA\b", text, re.MULTILINE)
    }


# The code point classes of gap G2, one named entry per class (the first word of the character name). A new class is a failing test.
G2_CLASSES = {
    **dict.fromkeys(
        (
            *(
                "AEGEAN",
                "BHAIKSUKI",
                "BRAHMI",
                "CHORASMIAN",
                "COPTIC",
                "ETHIOPIC",
                "HATRAN",
                "IMPERIAL",
                "INDIC",
            ),
            *(
                "INSCRIPTIONAL",
                "KAKTOVIK",
                "KHAROSHTHI",
                "KHMER",
                "MANICHAEAN",
                "MAYAN",
                "MEDEFAIDRIN",
                "MENDE",
            ),
            *(
                "MEROITIC",
                "NABATAEAN",
                "NEW",
                "OLD",
                "OTTOMAN",
                "PALMYRENE",
                "PHOENICIAN",
                "PSALTER",
                "RUMI",
            ),
            *("SINHALA", "SOGDIAN", "TELUGU", "GREEK"),
        ),
        "a number of a script or numeral system with its own glyphs",
    ),
    **dict.fromkeys(
        ("COUNTING", "TALLY"), "a counting rod or a tally mark: a stroke pattern, not a digit"
    ),
    **dict.fromkeys(
        ("IDEOGRAPHIC", "CIRCLED", "PARENTHESIZED"),
        "an ideographic numeral (one, two, ... nine), alone or in a circle or parentheses: an ideograph, not the digit",
    ),
}


def _data_sources():
    """The code points the vendored UTS #39 file lists as sources (MA lines)."""
    return set(_data_prototypes())


def _data_reading(ch):
    """What the vendored UTS #39 data reads ``ch`` as, or else its other-case form (a name rule never splits a capital from its small letter);
    ``None`` when it lists neither."""
    protos = _data_prototypes()
    for c in (ch, ch.lower(), ch.upper()):
        if len(c) == 1 and ord(c) in protos:
            return protos[ord(c)]
    return None


def _g4_reading(ch):
    """What the data reads ``ch`` as, directly or through its NFKC form (a modifier letter small v with hook is NFKC-read as the Latin small v
    with hook, which the data reads as u); ``None`` when the data lists neither."""
    reading = _data_reading(ch) or _data_reading(unicodedata.normalize("NFKC", ch))
    return reading if reading and re.fullmatch(r"[A-Za-z0-9]", reading) else None


# Names that say one ASCII letter outside the plain Latin block: NFKC reads most of them (mathematical, fullwidth, circled, parenthesized,
# modifier letters, double-struck, script and black-letter capitals); the sweep requires every one to be read or to be in a named gap.
_LETTER_FORMS = re.compile(
    r"LATIN|REGIONAL INDICATOR|MATHEMATICAL|MODIFIER LETTER|DOUBLE-STRUCK|BLACK-LETTER|^SCRIPT "
)
_NUMBER_WORD = {
    "TEN": 10, "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15, "SIXTEEN": 16,
    "SEVENTEEN": 17, "EIGHTEEN": 18, "NINETEEN": 19, "TWENTY": 20,
}  # fmt: skip


def _name_sweep():
    """Every code point whose name says one ASCII letter (LATIN ... LETTER x, REGIONAL INDICATOR SYMBOL LETTER x, MATHEMATICAL ... CAPITAL x, ...)
    or one ASCII digit (a name with DIGIT, or any No/Nd code point with a value 0-9) or a circled number 10 to 20, with what ``squeeze_views`` reads
    for it alone. Returns (cp, name, expected, views)."""
    rows = []
    for cp in range(sys.maxunicode + 1):
        ch = chr(cp)
        name = unicodedata.name(ch, "")
        if not name:
            continue
        expected = None
        letter = _NAMED_LETTER.fullmatch(name)
        if letter and _LETTER_FORMS.search(name):
            expected = letter[1]
        elif unicodedata.category(ch) in ("No", "Nd"):
            value = unicodedata.numeric(ch, None)
            if value is not None and value == int(value) and 0 <= value <= 9:
                expected = str(int(value))
            elif "CIRCLED NUMBER" in name and name.rsplit(" ", 1)[-1] in _NUMBER_WORD:
                expected = str(_NUMBER_WORD[name.rsplit(" ", 1)[-1]])
        elif "DIGIT" in name:
            digit = _NAMED_DIGIT.fullmatch(name)
            expected = _DIGIT_WORD[digit[1]] if digit else None
        if expected is not None:
            rows.append((cp, name, expected, textnorm.squeeze_views(ch)))
    return rows


def _gap_family(cp, name):
    ch = chr(cp)
    if unicodedata.category(ch) in textnorm._DROP_CATEGORIES:
        return "G1 dropped on purpose"
    if name.startswith("TURNED DIGIT"):
        return "G3 turned digit"
    if "NEGATIVE CIRCLED NUMBER" in name:
        return "G5 negative circled number 11 to 20"
    if unicodedata.category(ch) in ("No", "Nd"):
        return "G2 numeral of another script or system"
    if _g4_reading(ch) is not None:
        return "G4 read as another letter by UTS #39"
    if name.startswith(("SAMARITAN MODIFIER LETTER", "MODIFIER LETTER CYRILLIC")):
        return "G6 letter of another script named like a Latin letter"
    if name == "SCRIPT CAPITAL P":
        return "G7 symbol named like a letter"
    return None


def test_every_code_point_whose_name_says_one_ascii_letter_or_digit_is_read_as_it_or_is_in_a_named_gap_family():
    """THE SWEEP. For every code point whose Unicode name says one ASCII letter or digit, ``squeeze_views`` of it holds that letter or digit,
    unless it is in a family of ``KNOWN_NAME_GAPS``. (The names are the interpreter's: 15.0.0 and 15.1.0 are both run.)"""
    rows = _name_sweep()
    assert len(rows) > 1000, "the sweep found too few code points: the name grammar is broken"
    unread = [(cp, name, exp) for cp, name, exp, views in rows if not any(exp in v for v in views)]
    unnamed = [
        f"U+{cp:04X} {name} (says {exp})"
        for cp, name, exp in unread
        if _gap_family(cp, name) is None
    ]
    assert not unnamed, (
        "code points read as nothing that their name says, in no named gap family: "
        + "; ".join(unnamed[:20])
    )
    math_rows = [(n, views) for _, n, e, views in rows if "MATHEMATICAL" in n]
    assert len(math_rows) > 600, "the MATHEMATICAL letter and digit forms are not in the sweep"
    assert all(any(e in v for v in views) for _, n, e, views in rows if "MATHEMATICAL" in n), (
        "a MATHEMATICAL form is not read (NFKC reads them all)"
    )
    assert any("CIRCLED NUMBER ELEVEN" in n for _, n, _, _ in rows) and any(
        _gap_family(cp, n) == "G5 negative circled number 11 to 20" for cp, n, _ in unread
    ), (
        "the circled numbers 11 to 20 are not in the sweep or the negative circled ones are not named as a gap"
    )
    assert {_gap_family(cp, name) for cp, name, _ in unread} <= set(KNOWN_NAME_GAPS)
    for cp, name, _ in unread:
        if _gap_family(cp, name).startswith("G2"):
            assert name.split()[0] in G2_CLASSES, (
                f"U+{cp:04X} {name}: a new class of numeral that is not read; name it in G2_CLASSES with its reason"
            )
    for cp, name, exp, views in rows:
        if (cp, name, exp) in unread and _gap_family(cp, name).startswith("G4"):
            reading = _g4_reading(chr(cp))
            assert reading.upper() != exp.upper(), (
                f"U+{cp:04X} {name} is in G4 but the data does not read it as ANOTHER letter ({reading!r}, expected {exp})"
            )
            assert any(reading.upper() in v for v in views), (
                f"U+{cp:04X} {name}: the table does not follow the data (it should read {reading!r})"
            )
    # a gap family is only a gap: the circled and negative circled digits and the letter forms are NOT in it
    for cp, name, _ in unread:
        assert not re.search(
            r"CIRCLED (?:SANS-SERIF )?DIGIT|SQUARED LATIN|REGIONAL INDICATOR|LATIN \w+ LETTER [A-Z] WITH ",
            name,
        ) or _gap_family(cp, name) in (
            "G1 dropped on purpose",
            "G4 read as another letter by UTS #39",
        ), name


def _chars_named(pattern):
    found = [
        chr(cp)
        for cp in range(sys.maxunicode + 1)
        if re.fullmatch(pattern, unicodedata.name(chr(cp), ""))
    ]
    assert found, f"no code point is named like {pattern}"
    return found


def test_negative_circled_negative_squared_and_regional_indicator_letters_read_as_their_letter():
    for pattern in (
        r"NEGATIVE CIRCLED LATIN CAPITAL LETTER [A-Z]",
        r"NEGATIVE SQUARED LATIN CAPITAL LETTER [A-Z]",
        r"REGIONAL INDICATOR SYMBOL LETTER [A-Z]",
        r"(?:CROSSED )?NEGATIVE SQUARED LATIN CAPITAL LETTER P",
        r"SQUARED LATIN SMALL LETTER D",
    ):
        for ch in _chars_named(pattern):
            letter = unicodedata.name(ch)[-1]
            assert letter in textnorm.squeeze_views(ch), (
                f"U+{ord(ch):04X} ({unicodedata.name(ch)}) is not read as the letter {letter}"
            )
            assert bare(identity_key(ch)) == letter.lower(), f"U+{ord(ch):04X} has the wrong key"
    for start in (
        0x1F150,
        0x1F170,
        0x1F1E6,
    ):  # negative circled, negative squared, regional indicator letters
        word = "".join(chr(start + ord(x) - 65) for x in "PASSWORD")
        assert "PASSWORD" in textnorm.squeeze_views(word), (
            f"PASSWORD written from U+{start:04X} is read as {textnorm.squeeze_views(word)}"
        )
        assert _scan_holds("password", "token " + word + " end")


def test_circled_negative_circled_double_circled_and_sans_serif_digits_read_as_their_digit():
    pattern = r"(?:DINGBAT )?(?:NEGATIVE |DOUBLE )?CIRCLED (?:SANS-SERIF )?(?:DIGIT|NUMBER) (?:ZERO|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)"
    chars = [ch for ch in _chars_named(pattern) if unicodedata.normalize("NFKC", ch) == ch]
    assert len(chars) >= 40, "the digit family is smaller than the Unicode data lists"
    for ch in chars:
        word = unicodedata.name(ch).split()[-1]
        digit = "10" if word == "TEN" else _DIGIT_WORD[word]
        assert digit in textnorm.squeeze_views(ch), (
            f"U+{ord(ch):04X} ({unicodedata.name(ch)}) is not read as {digit}"
        )
    for start in (
        0x2776,
        0x278A,
        0x2780,
    ):  # dingbat negative circled, negative circled sans-serif, circled sans-serif: one to nine
        word = "".join(chr(start + i) for i in range(9))
        assert "123456789" in textnorm.squeeze_views(word), (
            f"the digits written from U+{start:04X} are read as {textnorm.squeeze_views(word)}"
        )
    assert textnorm.squeeze_views("\u24ff") == ("0",) and textnorm.squeeze_views(
        "\U0001f10b\U0001f10c"
    ) == ("00",)


def test_latin_letters_with_a_stroke_hook_bar_or_tail_read_as_their_letter_in_the_case_of_the_name():
    letters = _chars_named(r"LATIN (?:CAPITAL|SMALL) LETTER [A-Z] WITH .+")
    checked = 0
    for ch in letters:
        if (
            unicodedata.normalize("NFKD", ch) != ch
            or unicodedata.category(ch) in textnorm._DROP_CATEGORIES
        ):
            continue  # composed letters (A WITH GRAVE) are read through their parts
        checked += 1
        letter = re.fullmatch(
            r"LATIN (?:CAPITAL|SMALL) LETTER ([A-Z]) WITH .+", unicodedata.name(ch)
        )[1]
        views = textnorm.squeeze_views(ch)
        assert views and all(v != "" for v in views), (
            f"U+{ord(ch):04X} ({unicodedata.name(ch)}) is read as nothing"
        )
        reading = _g4_reading(
            ch
        )  # the data reads some letters as another one (V with hook as u): the data is the authority
        letter = (reading or letter).upper()
        assert letter in views[0], (
            f"U+{ord(ch):04X} ({unicodedata.name(ch)}) is not read as {letter}"
        )
    assert checked > 100, "the family is smaller than the Unicode data lists"
    assert squeeze("\u0126unter") == "HUNTER" and squeeze("\u0127unter") == "HUNTER", (
        "H with stroke is not read as h"
    )
    assert identity_key("\u0181ob") == identity_key("Bob") and bare(identity_key("Bob")) == "bob", (
        "B with hook is not read as b"
    )
    assert (
        identity_key("\u01b2") == identity_key("\u028b") and bare(identity_key("\u028b")) == "u"
    ), "V with hook: the capital must follow the small letter"
    assert bare(identity_key("\u1d0c")) == "l" and bare(identity_key("\u029b")) == "g", (
        "a small capital with a mark is not read as its letter"
    )
    assert _scan_holds("hunter2", "token: \u0126unt\u0113r2")


def _collisions(names):
    groups = {}
    for name in names:
        groups.setdefault(identity_key(name), []).append(name)
    colliding = [g for g in groups.values() if len(g) > 1]
    return len(names), len(groups), len(colliding), sum(len(g) for g in colliding)


def test_the_false_collision_rate_of_hindi_and_thai_names_after_non_spacing_marks_are_dropped():
    """Review 4: names that differ only by a non-spacing mark (Mn) compare equal (a false lockout in a DENY, never a bypass). The lists are
    hand-written (``tests/fixtures/textnorm_names.json``), not a sample of a population: the counts below are what the evidence file quotes
    as the rate, and they are asserted so the quoted figure cannot drift. (names, distinct check names, collision groups, names in a group)"""
    lists = json.loads((FIX / "textnorm_names.json").read_text(encoding="utf-8"))
    assert _collisions(lists["hindi"]) == (94, 94, 0, 0), (
        "Hindi: names collide after the marks are dropped"
    )
    assert _collisions(lists["thai"]) == (64, 63, 1, 2), "Thai: the rate of ordinary names changed"
    assert _collisions(lists["thai_chosen_pairs"]) == (15, 8, 6, 13), (
        "Thai: the minimal pairs chosen to collide changed"
    )


def test_a_text_over_the_weight_is_refused_before_any_fold_work(monkeypatch):
    """The claim "refused before any work" (perf file) is proven here without a clock: 16,000 x U+FDFA is far below the length cap but its
    weight (18 each, 288,000) is over it; every fold step is replaced by one that fails, and the text must still be refused."""

    def work(*args, **kwargs):
        raise AssertionError("fold work was done for a text that must be refused")

    for name in ("_prefix", "_finish", "_views", "_fold", "_keys", "_canon"):
        monkeypatch.setattr(textnorm, name, work)
    text = FDFA * 16_000
    assert len(text) < CAP < textnorm._weight(text)

    def must_refuse(label, fn, *args):
        try:
            fn(*args)
        except TextTooLong:
            return
        except AssertionError as work_done:  # ``work`` ran: say so in the first line of the report
            raise AssertionError(f"{label}: {work_done}") from None
        except Exception as other:  # noqa: BLE001 - reported with its class as the failure
            raise AssertionError(f"{label} raised {type(other).__name__} instead") from None
        raise AssertionError(f"{label} did not refuse an over-weight text")

    for fn in (
        identity_key,
        textnorm.identity_keys,
        textnorm.fold,
        _fold_views_no_scripts,
        textnorm.squeeze,
        textnorm.squeeze_views,
    ):
        must_refuse(fn.__name__, fn, text)
    must_refuse("could_be_same_person", could_be_same_person, "a", text)
    must_refuse("allow_equal", allow_equal, text, "a")
    must_refuse("names_equal", names_equal, text, "a")


# ---- P1a fix8: the DENY check sees through spacing marks, fails closed on unnamed characters, and the mixed-script signal ----------------
SPACING_CATEGORIES = ("Mc", "Lm", "Sk")


def test_a_spacing_mark_inserted_into_a_name_is_still_the_same_person():
    """F6-1 (ORDER 177): for EVERY Mc, Lm and Sk code point of the interpreter, "alice" and "ali" + c + "ce" are "could be the same person" and
    ``allow_equal`` says LOOKALIKE. NO exemption list (ORDER 90 item 2). The reversal of ORDER 79 item 3 for the DENY check."""
    marks = _code_points_of(*SPACING_CATEGORIES)
    assert len(marks) > 500, "too few spacing marks were found"
    for c in marks:
        text = "ali" + c + "ce"
        assert could_be_same_person("alice", text), (
            f"could_be_same_person does not see through the spacing mark U+{ord(c):04X}"
        )
        assert could_be_same_person(text, "alice"), (
            f"could_be_same_person is not symmetric for the spacing mark U+{ord(c):04X}"
        )
        assert allow_equal("alice", text) is AllowVerdict.LOOKALIKE, (
            f"allow_equal does not report the spacing mark U+{ord(c):04X} as a look-alike"
        )


def _name_pairs(names):
    return [
        (a, b) for i, a in enumerate(names) for b in names[i + 1 :] if could_be_same_person(a, b)
    ]


HINDI_PAIRS = [
    ("\u0926\u0940\u092a\u0915", "\u0926\u0940\u092a\u093f\u0915\u093e"),
    ("\u0938\u094d\u0935\u093e\u0924\u093f", "\u0938\u0935\u093f\u0924\u093e"),
]
THAI_PAIRS = [("\u0e19\u0e34\u0e20\u0e32", "\u0e19\u0e20\u0e32")]
THAI_CHOSEN_PAIRS = [
    ("\u0e28\u0e23\u0e35", "\u0e28\u0e23"),
    ("\u0e2a\u0e34\u0e19", "\u0e2a\u0e19"),
    ("\u0e1b\u0e34\u0e15\u0e34", "\u0e1b\u0e35\u0e15\u0e34"),
    ("\u0e19\u0e32", "\u0e19\u0e49\u0e32"),
    ("\u0e19\u0e32", "\u0e19\u0e48\u0e32"),
    ("\u0e19\u0e49\u0e32", "\u0e19\u0e48\u0e32"),
    ("\u0e44\u0e02\u0e48", "\u0e44\u0e02"),
    ("\u0e40\u0e2a\u0e37\u0e2d", "\u0e40\u0e2a\u0e37\u0e49\u0e2d"),
]


def test_the_deny_check_false_matches_on_the_names_lists_are_exactly_the_listed_pairs():
    """F6-1 cost, measured on the hand-made lists (not a sample of a real population): the pairs of different names that the DENY check now
    calls "could be the same person" are exactly the ones listed (Hindi 2 of 4,371 pairs, 0 before; Thai 1 of 2,016, unchanged; the Thai
    pairs chosen to collide 8 of 105, unchanged), plus one example each for the other scripts that write with Mc or Lm."""
    lists = json.loads((FIX / "textnorm_names.json").read_text(encoding="utf-8"))
    assert _name_pairs(lists["hindi"]) == HINDI_PAIRS, "the Hindi false matches changed"
    assert _name_pairs(lists["thai"]) == THAI_PAIRS, "the Thai false matches changed"
    assert _name_pairs(lists["thai_chosen_pairs"]) == THAI_CHOSEN_PAIRS, (
        "the chosen Thai false matches changed"
    )
    for a, b in (
        ("\u4f50\u3005\u6728", "\u4f50\u6728"),  # the Japanese iteration mark (Lm)
        ("\u30b3\u30fc\u30d2\u30fc", "\u30b3\u30d2"),  # the prolonged sound mark (Lm)
        ("\u0645\u062d\u0640\u0645\u062f", "\u0645\u062d\u0645\u062f"),  # the Arabic tatweel (Lm)
        ("\u0e14\u0e35\u0e46", "\u0e14\u0e35"),  # the Thai repetition mark (Lm)
    ):
        assert could_be_same_person(a, b), f"{_show([a, b])} do not match"
    # a text made only of spacing marks has the empty check name from its marks-dropped text: it matches any other text whose check name is empty
    assert textnorm.key_tag() in textnorm.identity_keys(
        "\u0903"
    ) and textnorm.key_tag() in textnorm.identity_keys("\u200b")
    assert could_be_same_person("\u0903", "\u200b"), "the empty check names do not match"
    assert not could_be_same_person("\u0903", "a"), "the empty check name matches a letter"


def test_a_character_this_python_cannot_name_makes_the_deny_check_fail_closed():
    """F6-5: the fold DROPS an unassigned (Cn), private-use (Co) or surrogate (Cs) character, so one that REPLACES a letter would read "alce". The
    DENY check answers True when either text holds one; ``allow_equal`` follows (LOOKALIKE); identical strings stay EQUAL."""
    unassigned = "\u0378"
    assert unicodedata.category(unassigned) == "Cn", "U+0378 is assigned on this Python"
    for c in (unassigned, "\ue000", "\ud800"):
        for text in ("al" + c + "ce", "ali" + c + "ce"):
            assert could_be_same_person("alice", text), (
                f"the DENY check misses U+{ord(c):04X} in {len(text)} characters"
            )
            assert could_be_same_person(text, "alice")
            assert allow_equal("alice", text) is AllowVerdict.LOOKALIKE, (
                f"allow_equal misses U+{ord(c):04X}"
            )
        assert allow_equal("al" + c + "ce", "al" + c + "ce") is AllowVerdict.EQUAL
    # the stated cost: such a name is "could be the same person" with every other name
    assert could_be_same_person("bob", "al\ue000ce")
    assert not could_be_same_person("bob", "alice")
    # a tag of THIS interpreter (private use U+E000 at the start) is taken off first, as the check names do, so it is not an unnamed character
    tag = key_tag()
    if tag:
        assert could_be_same_person(tag + "bob", "bob") and not could_be_same_person(
            tag + "bob", "alice"
        )


def test_the_deny_check_skips_the_marks_dropped_reading_only_when_it_changes_nothing():
    """F6-1b: ``_keys`` makes the marks-dropped reading only when the raw text or its NFKD text holds a spacing mark. For EVERY code point alone, and
    for every name of the names lists, that gated result equals the ungated one (so skipping it loses no check name). 61 code points on Unicode
    15.1 (for example U+0149 and U+1B06) hold no spacing mark themselves but decompose into one: a gate on the raw text alone would miss them.
    A Chinese, Hindi and Thai text without a mark still gets its script view in ``fold_views``: the gate lives in ``_keys`` only."""

    def ungated(raw):
        return tuple(
            key_tag() + view
            for view in textnorm._views(raw, casefold=True, collapse_ws=True, marks_dropped=True)
        )

    differ = [ch for ch in _non_surrogates() if textnorm._keys(ch) != ungated(ch)]
    assert not differ, (
        f"the gate drops a check name for {len(differ)} code points, first {_show(differ)}"
    )
    lists = json.loads((FIX / "textnorm_names.json").read_text(encoding="utf-8"))
    names = [n for key in ("hindi", "thai", "thai_chosen_pairs") for n in lists[key]]
    assert all(textnorm._keys(n) == ungated(n) for n in names), (
        "the gate drops a check name of a name"
    )
    assert (
        textnorm._keys("\u0149")
        == ungated("\u0149")
        != tuple(key_tag() + v for v in textnorm._views("\u0149", casefold=True, collapse_ws=True))
    ), "the NFKD case is not the case that needs the marks-dropped reading"
    for text in (
        "\u5bc6 a \u7801",  # Han with an ASCII letter inserted
        "\u0928 - \u092e - \u0938",  # Devanagari letters, no vowel sign
        "\u0e01 x \u0e02 x \u0e04",  # Thai consonants, no vowel sign
    ):
        assert textnorm._without_spacing_marks(text) == text, "the text holds a spacing mark"
        letters = "".join(ch for ch in text if not ch.isascii() and ch.isalpha())
        views = textnorm.fold_views(text, casefold=True, scripts=textnorm.value_scripts(text))
        assert letters in views, "a text without a mark lost its script view"
        assert letters != text


def test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a_mark_of_the_words_own_script_does_not_flag():
    """F6-2: ``has_mixed_script`` removes Sk before the word split, a spacing mark (Mc) does not split a word, and a Latin letter with an Mc of
    another script that no letter of the word owns is mixed (rule b)."""
    for text in (
        "ali\u0903ce",
        "iPhone\u093e",
        "\u0440\u0430^ypal",  # Cyrillic ra, a circumflex, Latin ypal
        "\u0440\u0430\u00b4ypal",  # the same with the acute accent (Sk, a space under NFKC)
    ):
        assert has_mixed_script(text), f"the mixed word {_show([text])} is not flagged"
    # rule (a) of P1b reads the script data, so a Latin letter with a Devanagari LETTER is flagged whatever mark follows (the P1a fix8 row said
    # "Ramesh" + a syllable with its own sign was not flagged: that was true while rule (a) named only look-alike scripts)
    assert has_mixed_script("Ramesh\u091c\u0940"), (
        "a Latin letter next to a Devanagari letter is not flagged"
    )
    mcs = _code_points_of("Mc")
    assert len(mcs) > 400
    missed = [c for c in mcs if not has_mixed_script("ali" + c + "ce")]
    assert not missed, (
        f"a spacing mark hides a mixed word for {len(missed)} code points, first {_show(missed)}"
    )
    for text in (
        "\u0930\u093e\u092e",  # a Devanagari word alone
        "cafe\u0301",
        "caf\u00e9",
        "na\u00efve",
        "ok\ufe0f",
        "al\u02b0ice",  # a modifier letter: NFKC makes it a Latin h
        "ali^ce",
        "x^y",
        "\u0903",
    ):
        assert not has_mixed_script(text), f"{_show([text])} is flagged"
    # a mark next to a letter of its own script group does not flag: with a Latin letter in front, the result is the one of the letters alone
    own_letter = {}
    for cp in range(sys.maxunicode + 1):
        ch = chr(cp)
        if ch.isalpha() and not ch.isascii():
            own_letter.setdefault(textnorm._script_of(ch), ch)
    checked = 0
    for c in mcs:
        letter = own_letter.get(textnorm._script_of(c))
        if letter is None:
            continue  # no letter of the mark's group (two groups): the mark alone decides, and it flags inside a Latin word
        checked += 1
        assert not has_mixed_script(letter + c), f"{_show([letter + c])} is flagged"
        assert has_mixed_script("a" + letter + c) == has_mixed_script("a" + letter), (
            f"a mark of the word's own script group flags {_show(['a' + letter + c])}"
        )
    assert checked > 350, "too few marks were checked against a letter of their own group"


def test_the_pin_message_and_the_pin_constants_come_from_defaults(monkeypatch):
    """F-R5: the Python version in the ``require_pinned_unidata`` message is ``defaults.TEXTNORM_PINNED_PYTHON``, the Unicode version is
    ``defaults.TEXTNORM_PINNED_UNIDATA`` (no second copy in the module), and a pin that is not a non-empty ``str`` fails closed."""
    monkeypatch.setattr(unicodedata, "unidata_version", "14.0.0")
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "99.1.0")
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_PYTHON", "9.99")
    with pytest.raises(UnidataMismatch) as info:
        require_pinned_unidata()
    assert str(info.value) == (
        "this Python uses Unicode 14.0.0; run Python 9.99 (Unicode 99.1.0) for pilot or prod"
    ), "the message does not follow the two constants of defaults"
    with pytest.raises(UnidataMismatch) as info:
        require_pinned_unidata("98.0.0")
    assert "run a Python with Unicode 98.0.0" in str(info.value)
    for name in ("TEXTNORM_PINNED_PYTHON", "TEXTNORM_PINNED_UNIDATA"):
        for bad in ("", None, 3.13):
            with monkeypatch.context() as patch:
                patch.setattr(defaults, name, bad)
                refused(TextnormError, f"{name} of {bad!r} was accepted", require_pinned_unidata)
    source = (ROOT / "src/hadavin_sdk/guard/textnorm.py").read_text(encoding="utf-8")
    assert '"3.13"' not in source and '"15.1.0"' not in source, (
        "a literal copy of the pin is back in the module"
    )


def test_the_docstrings_state_the_new_behaviour_and_the_corrected_wording():
    """F6-3, F-R2, F-R3 and F-R9: the words that the review found wrong are gone, and the sentences that were asked for stand."""
    assert "ONE reading, not a scan" in _squash(textnorm.squeeze.__doc__ or ""), (
        "the squeeze docstring still calls itself a check name for a scan"
    )
    assert "Check name for a scan" not in (textnorm.squeeze.__doc__ or "")
    assert "NFKC" not in (names_equal.__doc__ or ""), "the names_equal docstring says NFKC again"
    source = (ROOT / "src/hadavin_sdk/guard/textnorm.py").read_text(encoding="utf-8")
    variant_line = next(ln for ln in source.splitlines() if ln.lstrip().startswith("VARIANT ="))
    assert "NFKC" not in variant_line, "the VARIANT comment says NFKC again"
    canon = textnorm._canon.__doc__ or ""
    assert "eight code points" in canon and "nine" not in canon, (
        "the _canon docstring does not say eight code points"
    )
    module_doc = _squash(textnorm.__doc__ or "")
    assert (
        "checked first, once" not in module_doc and "TextTooLong``, checked first" not in module_doc
    ), "the size cap is again said to be checked first, once"
    assert "checked before any fold work" in module_doc
    wired = "wired into NO approval check"
    assert wired in module_doc and wired in _squash(could_be_same_person.__doc__ or ""), (
        "the docstrings do not say where could_be_same_person is used"
    )
    assert "no approval compares people's names" in module_doc
    log = ROOT / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        changelog = _squash(log.read_text(encoding="utf-8"))
        assert wired in changelog and "behaviour change" in changelog, (
            "the CHANGELOG does not state the F-R9 sentence and the behaviour change"
        )
    for sentence in ("UNNAMED CHARACTERS", "fails closed"):
        assert sentence in module_doc or sentence.lower() in module_doc.lower()


def test_no_approval_code_names_the_deny_check():
    """F-R9 (ORDER 179): ``could_be_same_person`` is wired into NO approval check. A use in an approval is a new ticket with its own plan review."""
    approvals = ROOT / "src" / "hadavin_sdk" / "approvals"
    files = sorted(approvals.rglob("*.py"))
    assert files, "the approvals package was not found"
    for path in files:
        text = path.read_text(encoding="utf-8")
        for name in ("could_be_same_person", "allow_equal", "identity_key", "textnorm"):
            assert name not in text, f"{path.name} names {name}"


def test_every_key_and_view_of_seeded_multi_character_texts_is_within_the_weight():
    """F-R6: the weight bound on texts of SEVERAL expanding characters (the single-code-point tests cannot see a sum), with spacing marks among
    them so the marks-dropped check names are made too. Seeded; integer arithmetic only."""
    pool = [chr(cp) for cp in range(0, 0x110000, 61) if not 0xD800 <= cp <= 0xDFFF]
    pool += [FDFA, SSS, "\u1fb3", "\u0345", "\u0903", "\u02b0", "^", "\u0397", "\u00df", "\ufb03"]
    nxt = _numbers(20260109)
    for n in range(400):
        text = "".join(pool[next(nxt) % len(pool)] for _ in range(2 + next(nxt) % 40))
        weight = textnorm._weight(text)
        keys = textnorm.identity_keys(text)
        assert 1 <= len(keys) <= 6 and len(set(keys)) == len(keys), (
            f"text {n}: {len(keys)} check names"
        )
        views = (
            *keys,
            *textnorm.fold_views(text, scripts=frozenset(), casefold=True, collapse_ws=True),
            *textnorm.squeeze_views(text, loose=True),
        )
        assert all(len(bare(v)) <= weight for v in views), (
            f"text {n}: a check name or view is longer than the weight"
        )
        assert could_be_same_person(text, text), (
            f"text {n}: a text is not the same person as itself"
        )


# last on purpose: a mutation of a pinned file must be judged by the test aimed at it, not by this hash pin
def test_the_manifest_pins_the_files_a_demo_copies():
    manifest = json.loads((FIX / "textnorm_manifest.json").read_text(encoding="utf-8"))
    for rel, sha in manifest["files"].items():
        data = (ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == sha, (
            rel,
            "changed: re-sync the demos and update the manifest and the CHANGELOG",
        )
    assert set(manifest["files"]) == {
        "src/hadavin_sdk/guard/textnorm.py",
        "src/hadavin_sdk/guard/_confusables.py",
        "src/hadavin_sdk/guard/_scripts.py",
        "tests/fixtures/textnorm_vectors.json",
        "tests/fixtures/textnorm_corpus.json",
    }
    log = ROOT / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        text = log.read_text(encoding="utf-8")
        for rel, sha in manifest["files"].items():
            assert sha in text, rel  # the CHANGELOG re-copy list names every pinned hash

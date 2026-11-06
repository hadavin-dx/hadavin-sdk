"""The shared text fold (``hadavin_sdk.guard.textnorm``): the moved controls, the new input rules, the version string, the hidden channel.

Look-alikes are built with ``chr()``. No wall-clock assertions: timing rows live in ``tests/test_textnorm_perf.py`` (marker ``perf``), which
no mutation run lists. Facts of one Unicode version (entry counts, digit counts) are never written here: the tests state properties that
hold on every interpreter. The assertions a mutant must trip carry a message; the mutant list (``tests/textnorm_mutants.py``) names a
fragment of that message, so a message is never reworded without the list.
"""

import ast
import enum
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


def bare(key):
    """A key without the tag of an interpreter whose Unicode version is not the pin (``key_tag()`` is empty on the pinned version)."""
    return key.removeprefix(key_tag())


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
    assert fold(chr(0x2013)) == chr(0x2013)


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
    m = re.fullmatch(r"alg=fold4\|tbl=([0-9a-f]{12}):(\d+)\|ucd=([^|]+)\|ud=([^|]+)", FOLD_VERSION)
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
        if any(len(v) > textnorm._weight(text) for v in textnorm.fold_views(text, casefold=True)):
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
    assert tag.startswith("\ue000alg=fold4|ud=15.0.0") and tag.endswith("\ue000")
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
    assert key_tag() == "" and identity_key(tag + "bob") == "alg=fold4|ud=15.0.0bob"


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
    assert other.endswith("bob") and "ud=15.0.0" in other and "alg=fold4" in other, (
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
def test_the_public_names_are_exactly_the_listed_twenty():
    assert sorted(textnorm.__all__) == sorted(
        [
            "FILLERS",
            "FOLD_VERSION",
            "AllowVerdict",
            "NotText",
            "TextTooLong",
            "TextnormError",
            "UnidataMismatch",
            "allow_equal",
            "fold",
            "fold_views",
            "has_hidden_channel",
            "has_mixed_script",
            "identity_key",
            "identity_keys",
            "key_tag",
            "names_equal",
            "require_pinned_unidata",
            "could_be_same_person",
            "squeeze",
            "squeeze_views",
        ]
    )
    assert len(textnorm.__all__) == len(set(textnorm.__all__)) == 20


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
    needles = textnorm.fold_views(secret, casefold=True)
    return any(n in v for v in textnorm.fold_views(haystack, casefold=True) for n in needles)


def test_a_greek_look_alike_with_ypogegrammeni_is_the_latin_word_for_could_be_same_person_and_for_a_scan():
    hostile = "\u03b1\u0345dmin"  # alpha + U+0345 + "dmin": the reader sees "admin"
    assert could_be_same_person(hostile, "admin") and could_be_same_person("admin", hostile), (
        "alpha + U+0345 + dmin is not the person admin"
    )
    assert allow_equal(hostile, "admin") is AllowVerdict.LOOKALIKE, (
        "allow_equal does not report alpha + U+0345 + dmin as a look-alike"
    )
    assert "admin" in textnorm.fold_views(hostile, casefold=True), (
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
                        textnorm.fold_views(marked, casefold=casefold),
                        textnorm.fold_views(plain, casefold=casefold),
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
    assert could_be_same_person("Ho", ETA + "\u00d8"), (
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
        assert type(keys) is tuple and 1 <= len(keys) <= 3, (
            f"{len(keys)} readings for {_show([text])}"
        )
        assert len(set(keys)) == len(keys), "a reading is listed twice"
        assert identity_key(text) in keys, "the single key is not one of the readings"
        assert keys == textnorm.identity_keys(text), "the readings are not deterministic"
        for key in keys:
            assert key == bare(key) or key.startswith(key_tag())
    assert set(map(bare, textnorm.identity_keys("\u03b1\u0345dmin"))) == {"admin", "aidmin"}
    assert set(map(bare, textnorm.identity_keys(ETA + "oward"))) == {"noward", "howard"}
    # the number of readings does not grow with the text: a text with every kind of ambiguity still has three at most
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
                views = textnorm.fold_views(text, casefold=casefold, collapse_ws=collapse_ws)
                assert type(views) is tuple and 1 <= len(views) <= 3
                assert len(set(views)) == len(views)
                assert fold(text, casefold=casefold, collapse_ws=collapse_ws) in views, (
                    "the single fold is not one of the views"
                )
        for loose in (False, True):
            views = textnorm.squeeze_views(text, loose=loose)
            assert type(views) is tuple and 1 <= len(views) <= 3
            assert squeeze(text, loose=loose) in views, "the single squeeze is not one of the views"
    assert set(textnorm.fold_views("\u03b1\u0345dmin", casefold=False)) == {"admin", "aidmin"}
    assert "howard" in textnorm.fold_views(ETA + "oward", casefold=True)
    assert "Howard" in textnorm.fold_views(ETA + "oward", casefold=False)
    for fn in (textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
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
        for fn in (textnorm.identity_keys, textnorm.fold_views, textnorm.squeeze_views):
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
        hostile, casefold=True
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


def _reads_as_letters(ch):
    """True when the character is itself read as an ASCII letter or digit, from the Unicode DATA and the table, not from the fold: its
    NFKC form holds an ASCII letter or digit (a modifier letter such as U+02B0, superscript h, is the letter h), or a character of that form
    is a table source (U+02E0, modifier small gamma, is a gamma, which the table reads as y), or the table maps the character itself
    (a Telugu or Malayalam anusvara reads as o, Oriya visarga as 8)."""
    return any(
        (c.isascii() and c.isalnum())
        or ord(c) in _confusables.TABLE
        or ord(c.casefold()) in textnorm._CF_TABLE
        for c in {ch, *unicodedata.normalize("NFKC", ch)}
        if unicodedata.category(c)
        not in textnorm._DROP_CATEGORIES  # a mark of the image (U+037A: space + U+0345) is dropped, not read
    )


def test_squeeze_views_finds_a_secret_hidden_with_any_spacing_mark_modifier_letter_or_modifier_symbol():
    """The redaction contract: a scan looks through BOTH ``fold_views`` and ``squeeze_views``. This is the half that makes ``squeeze_views``
    safe for a secret hidden by an inserted character of category Mc (spacing combining mark), Lm (modifier letter) or Sk (modifier symbol).
    EVERY such code point of this interpreter is tried; nothing is skipped. The only exceptions are the code points that are themselves read
    as a letter or digit (``_reads_as_letters``: superscript h, the letter-like Lm; an anusvara that the look-alike table reads as o): for
    those the view must read the letter in their place, ``PASS`` + letter + ``WORD``, so the inserted character still shows. The
    exception set is DERIVED from the Unicode data (NFKC form and the table), never written by hand."""
    seen = {}
    for category in ("Mc", "Lm", "Sk"):
        chars = _code_points_of(category)
        assert chars, f"this interpreter has no code point of category {category}"
        letters = 0
        for ch in chars:
            views = textnorm.squeeze_views("pass" + ch + "word")
            if _reads_as_letters(ch):
                letters += 1
                assert any(re.fullmatch("PASS[A-Z0-9]+WORD", v) for v in views), (
                    f"squeeze_views hides U+{ord(ch):04X} ({category}), which reads as a letter, from the scan: {views}"
                )
            else:
                assert "PASSWORD" in views, (
                    f"squeeze_views misses a secret hidden with U+{ord(ch):04X} ({category}): {views}"
                )
        seen[category] = (len(chars), letters)
    # the exception set is small and only of letter-like characters: no Mc (apart from the table's anusvaras and visarga) and no Sk is one
    assert seen["Sk"][1] == 0, f"a modifier symbol reads as a letter: {seen}"
    assert seen["Mc"][1] <= 10, f"more spacing marks read as letters than the table lists: {seen}"


def test_fold_views_keeps_a_spacing_combining_mark_so_a_scan_must_also_read_squeeze_views():
    """Decision (order 79): Mc is KEPT by ``fold``: a Hindi or Thai spacing vowel sign changes a name, so two names that differ only by one
    are different keys. The price is stated in the module docstring: ``fold_views`` alone does NOT find a secret hidden with a spacing mark
    (``squeeze_views`` does). This test pins the decision for EVERY Mc code point, so the docstring cannot drift."""
    marks = _code_points_of("Mc")
    assert marks
    for ch in marks:
        text = "pass" + ch + "word"
        for view in textnorm.fold_views(text, casefold=True):
            assert "password" not in view, f"fold_views dropped the spacing mark U+{ord(ch):04X}"
        assert identity_key(text) != identity_key("password"), (
            f"identity_key dropped the spacing mark U+{ord(ch):04X}"
        )
        assert not could_be_same_person(text, "password") or ord(ch) in _confusables.TABLE, ch
    # the realistic case: a Devanagari vowel sign hides a password from fold_views and not from squeeze_views
    text = "passाword"
    assert all("password" not in v for v in textnorm.fold_views(text, casefold=True))
    assert "PASSWORD" in textnorm.squeeze_views(text)
    doc = textnorm.__doc__ or ""
    assert "BOTH" in doc and "fold_views" in doc and "squeeze_views" in doc, (
        "the module docstring does not say that a scan must read both views"
    )
    for false_claim in ("drops legitimate marks", "for any combining mark,"):
        assert false_claim not in doc, f"the module docstring claims again: {false_claim}"
    assert "KEEPS the spacing" in doc and "Mc" in doc, (
        "the docstring does not say that spacing marks are kept"
    )


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
        textnorm.fold_views,
        textnorm.squeeze,
        textnorm.squeeze_views,
    ):
        must_refuse(fn.__name__, fn, text)
    must_refuse("could_be_same_person", could_be_same_person, "a", text)
    must_refuse("allow_equal", allow_equal, text, "a")
    must_refuse("names_equal", names_equal, text, "a")


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
        "tests/fixtures/textnorm_vectors.json",
        "tests/fixtures/textnorm_corpus.json",
    }
    log = ROOT / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        text = log.read_text(encoding="utf-8")
        for rel, sha in manifest["files"].items():
            assert sha in text, rel  # the CHANGELOG re-copy list names every pinned hash

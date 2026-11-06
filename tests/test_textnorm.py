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
    check_pinned_unidata,
    fold,
    fold_key,
    has_hidden_channel,
    has_mixed_script,
    identity_key,
    key_tag,
    names_equal,
    require_pinned_unidata,
    same_person,
    squeeze,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
CAP = defaults.TEXTNORM_MAX_CHARS
A516 = chr(0xA516)  # weight 3: its fold is three letters
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
    assert same_person(real, spoof), "same_person does not fold a look-alike"
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
        assert same_person(x, y), f"same_person does not fold {x!r} and {y!r}"
        assert names_equal(x, y), (x, y)  # the name comparison stays tolerant, and is not an ALLOW
    assert not names_equal("alice", "bob") and not same_person("alice", "bob")
    assert same_person(real, spoof) and not names_equal(real, spoof)
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
    assert fold_key is identity_key


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
    assert len(fold(A516)) == _confusables.MAX_VALUE_LEN, "the longest value is not made by U+A516"


# ---- FOLD_VERSION ------------------------------------------------------------------------------------------------------------------------
def test_the_version_string_names_the_algorithm_the_table_and_both_unicode_versions():
    m = re.fullmatch(r"alg=fold2\|tbl=([0-9a-f]{12}):(\d+)\|ucd=([^|]+)\|ud=([^|]+)", FOLD_VERSION)
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


def test_identity_key_is_idempotent_for_every_code_point():
    bad = _not_idempotent(_non_surrogates())
    assert not bad, f"identity_key is not idempotent for {len(bad)} code points, first {_show(bad)}"


def test_identity_key_is_case_symmetric_for_every_code_point():
    bad = _case_asymmetric(_non_surrogates())
    assert not bad, (
        f"identity_key is not case symmetric for {len(bad)} code points, first {_show(bad)}"
    )


def test_identity_key_is_idempotent_for_pairs_built_from_the_table():
    bad = _not_idempotent(_pairs())
    assert not bad, f"identity_key is not idempotent for {len(bad)} pairs, first {_show(bad)}"


def test_identity_key_is_case_symmetric_for_pairs_built_from_the_table():
    bad = _case_asymmetric(_pairs())
    assert not bad, f"identity_key is not case symmetric for {len(bad)} pairs, first {_show(bad)}"


def test_squeeze_is_case_symmetric_for_every_code_point():
    bad = _case_asymmetric(_non_surrogates(), squeeze)
    assert not bad, f"squeeze is not case symmetric for {len(bad)} code points, first {_show(bad)}"


def test_the_old_failures_are_gone_a_capital_o_stroke_and_the_small_one_are_one_person():
    assert same_person("B\u00d8B", "bob") and same_person("b\u00f8b", "BOB")
    assert bare(identity_key("\u00d8")) == bare(identity_key("\u00f8")) == "o", (
        "O with stroke is not case symmetric"
    )
    assert bare(identity_key("\u1f80")) == bare(identity_key("\u1f80".upper())), (
        "a Greek letter with iota is not case symmetric"
    )


def test_the_case_fold_table_is_on_the_case_fold_image_and_its_conflicts_are_the_known_thirteen():
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
        0x3ED,
        0x442,
        0x4CF,
        0x575,
        0x118C3,
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
def test_check_pinned_unidata_raises_when_strict_and_warns_otherwise(monkeypatch):
    # independent of the interpreter: its Unicode version is stubbed, and so is the pin
    monkeypatch.setattr(unicodedata, "unidata_version", "7.7.7")
    check_pinned_unidata("7.7.7", strict=True)  # the same version: silent
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_pinned_unidata("7.7.7")
    refused(
        UnidataMismatch,
        "strict mode accepted another version",
        check_pinned_unidata,
        "0.0.0",
        strict=True,
    )
    with pytest.warns(UserWarning, match="not the pinned"):
        check_pinned_unidata("0.0.0")
    # the default is read when the function runs: a patched constant is seen
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "0.0.0")
    refused(
        UnidataMismatch,
        "the patched pinned version is not used",
        check_pinned_unidata,
        strict=True,
    )
    monkeypatch.setattr(defaults, "TEXTNORM_PINNED_UNIDATA", "7.7.7")
    accepted("the patched pinned version is not used", check_pinned_unidata, strict=True)


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
    try:
        require_pinned_unidata()
    except UnidataMismatch as err:
        assert "15.0.0" in str(err) and "15.1.0" in str(err)
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
    assert other.endswith("bob") and "ud=15.0.0" in other and "alg=fold2" in other, (
        "the tag does not name the algorithm and the Unicode version"
    )
    assert identity_key(other) == other, "the key of another version is not idempotent"
    assert same_person("BØB", "bob") and not same_person("bob", "bobb")
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


ONE_ARG = (fold, squeeze, identity_key, fold_key, has_hidden_channel, has_mixed_script)
TWO_ARG = (same_person, allow_equal, names_equal)


def test_every_public_function_refuses_what_is_not_a_plain_str():
    for bad in (b"x", 1, None, ["x"], _Sub("x"), _Name.RED, bytearray(b"x")):
        for fn in ONE_ARG:
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__}", fn, bad)
        for fn in TWO_ARG:
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__} first", fn, bad, "a")
            refused(NotText, f"{fn.__name__} accepted {type(bad).__name__} second", fn, "a", bad)
    for fn in ONE_ARG:
        assert fn(str(_Name.RED)) is not None  # the plain text of a member is accepted
    assert same_person(str(_Name.RED), "red") and names_equal(str(_Name.RED), "RED")


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
    # U+A516 becomes three letters: SEAM-1
    refused(TextTooLong, "87,382 x U+A516 (W 262,146) is accepted", identity_key, A516 * 87382)
    assert bare(accepted("W 262,143 is refused", identity_key, A516 * 87381)) == "l" * 262143
    refused(
        TextTooLong,
        "262,144 x U+A516 (plain length at the cap) is accepted",
        identity_key,
        A516 * CAP,
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
    big = A516 * 87382
    refused(TextTooLong, "same_person skipped the second argument", same_person, "a", big)
    refused(TextTooLong, "allow_equal skipped the first argument", allow_equal, big, "a")
    refused(TextTooLong, "allow_equal skipped the second argument", allow_equal, "a", big)
    refused(TextTooLong, "names_equal skipped the second argument", names_equal, "a", big)
    refused(TextTooLong, "same_person(big, 1) is not a size refusal", same_person, big, 1)
    refused(NotText, "same_person(1, big) is not a type refusal", same_person, 1, big)


def test_the_cap_is_read_when_the_function_runs(monkeypatch):
    monkeypatch.setattr(defaults, "TEXTNORM_MAX_CHARS", 5)
    assert bare(accepted("the patched cap refuses a short text", identity_key, "abcde")) == "abcde"
    refused(TextTooLong, "the patched cap is not used", identity_key, "abcdef")


def test_a_refusal_message_holds_lengths_and_constants_never_the_input():
    canary = "ZQXCANARY"
    for text in (canary + "a" * CAP, canary + A516 * 90000):
        with pytest.raises(TextTooLong) as info:
            identity_key(text)
        assert canary not in str(info.value) and "ZQX" not in str(info.value)
    with pytest.raises(NotText) as info:
        identity_key(_Sub(canary))
    assert canary not in str(info.value)


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
def test_the_public_names_are_exactly_the_listed_nineteen():
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
            "check_pinned_unidata",
            "fold",
            "fold_key",
            "has_hidden_channel",
            "has_mixed_script",
            "identity_key",
            "key_tag",
            "names_equal",
            "require_pinned_unidata",
            "same_person",
            "squeeze",
        ]
    )
    assert len(textnorm.__all__) == len(set(textnorm.__all__)) == 19


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

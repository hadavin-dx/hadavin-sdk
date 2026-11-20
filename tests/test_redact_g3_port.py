"""Ticket G, part G3: what the port of the fold scan (P2d-1) adds on the fold head, beside P2d-1's own tests.

1. ``RedactionResult.actions``: the redactor counts its own changes of the text (review finding cb-1-1). A withheld line swallows the
   placeholders it held and gains one per hit, so the number of placeholders and the map can both be EQUAL before and after although a
   value was hidden; only the redactor knows that it acted.
2. ``runmap._views``: the six views of the fold, then the two views of the text without its spacing marks (canonical, composed).

Every value here is made up; the look-alike letters are built from escapes.
"""

import re

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import FOLD_NOTE, RedactionResult, redact
from hadavin_sdk.guard.textnorm import fold, without_spacing_marks

PH = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")
CYRILLIC_A = "а"
MAIL = "alice@example.com"
KNOWN = {"<EMAIL_1>": MAIL, "<IPV4_1>": "10.0.0.5"}


# ---- 1. the action counter ---------------------------------------------------------------------------------------------------------
def test_actions_a_lookalike_of_a_known_value_beside_another_placeholder_is_an_action():
    """cb-1-1: the count of placeholders and the map are the same before and after; ``actions`` is not 0 and the value is not readable."""
    text = f"host <IPV4_1> mail {CYRILLIC_A}{MAIL[1:]}"
    assert MAIL not in text and fold(text).count(MAIL) == 1  # hidden as written, readable folded
    result = redact(text, mapping=dict(KNOWN))
    assert result.actions > 0, "ACTIONS-1: a withheld line is not counted as an action"
    out = result.text
    assert MAIL not in out and MAIL not in fold(out) and MAIL[1:] not in out, out
    assert CYRILLIC_A not in out, out
    assert out == f"{FOLD_NOTE} <EMAIL_1>"
    # why a counter is needed: neither the placeholder count nor the map shows that anything happened
    assert len(PH.findall(out)) == len(PH.findall(text)) == 1
    assert result.mapping == KNOWN


def test_actions_a_text_that_is_left_as_it_is_counts_zero():
    for text in (
        "",
        "nothing to hide here",
        "host <IPV4_1> mail ok",  # already masked: a placeholder is not a new value
        "host <IPV4_1> café ok",  # a non-ASCII line the fold scan reads and leaves alone
        "x ‹IPV4_2› y café",  # a look-alike of a placeholder: no view finds a value
    ):
        result = redact(text, mapping=dict(KNOWN))
        assert result.text == text, text
        assert result.actions == 0, f"ACTIONS-2: {text!r} is unchanged and counts {result.actions}"
        assert result.mapping == KNOWN


def test_actions_each_kind_of_change_is_counted():
    # a pattern mask: one per value masked
    assert redact("mail bob@example.com").actions == 1
    # the sweep: one per copy replaced (the second copy touches `_`, which the pattern's word boundary does not accept)
    uid = "123e4567-e89b-12d3-a456-426614174000"
    swept = redact(f"uid {uid} and x_{uid}_0")
    assert swept.text == "uid <UUID_1> and x_<UUID_1>_0" and swept.actions == 2
    # a known value written in clear: every copy
    again = redact(f"mail {MAIL} and {MAIL}", mapping=dict(KNOWN))
    assert again.text == "mail <EMAIL_1> and <EMAIL_1>" and again.actions == 2
    # the fold scan masks in place (an accent; a spacing mark inside a key)
    assert redact("josé@example.com wrote").actions == 1
    key = "AKIA" + "ा" + "IOSFODNN7EXAMPLE"
    marked = redact(f"the key {key} end")
    assert marked.text == "the key <APIKEY_1> end" and marked.actions == 1
    # a withheld line: one per hit and one for the line
    held = redact(f"mail {CYRILLIC_A}{MAIL[1:]}")
    assert held.text.startswith(FOLD_NOTE) and held.actions == 2


def test_actions_is_a_field_with_a_default_so_older_callers_are_untouched():
    assert RedactionResult(text="x").actions == 0
    assert RedactionResult("x", {"<A_1>": "v"}).actions == 0


def test_actions_the_masks_of_a_discarded_fold_round_are_not_counted_twice():
    """A line whose first in-place round masks one value and whose second value sits behind a look-alike is withheld: the registrations
    of the in-place round are rolled back, and so is its count (two hits and the line, not three masks and the line)."""
    text = f"mail josé@example.com and {CYRILLIC_A}{MAIL[1:]}"
    result = redact(text)
    assert result.text.startswith(FOLD_NOTE), result.text
    hits = PH.findall(result.text)
    assert result.actions == len(hits) + 1, (result.actions, result.text)


# ---- 2. the views of runmap --------------------------------------------------------------------------------------------------------
def test_views_the_marks_dropped_views_come_after_the_six_of_the_fold_and_can_differ():
    # e, a spacing mark (Devanagari visarga), a combining acute: `canonical` composes nothing, `composed` joins e and the accent once
    # the mark between them is gone
    text = "mail joseः́@example.com x"
    unmarked = without_spacing_marks(text)
    plain, joined = runmap.canonical(unmarked), runmap.composed(unmarked)
    assert plain != joined and "é" in joined and "é" not in plain
    views = runmap._views(text)
    assert views == [plain, joined], (
        views
    )  # the six views of the fold equal the text here, so only the two new ones are returned
    # with a full-width letter the first of the six differs too, and it stays first
    wide = "ａ" + text
    views = runmap._views(wide)
    assert views[0] == runmap.canonical(wide)
    assert views[-2:] == [
        runmap.canonical(without_spacing_marks(wide)),
        runmap.composed(without_spacing_marks(wide)),
    ]


def test_views_an_ascii_text_without_a_modifier_symbol_gets_no_new_view():
    text = "pw=ab%41 x end"
    assert without_spacing_marks(text) == text
    assert runmap._views(text) == [runmap.canonical(runmap.undo(text))]


# ---- 3. fold5 reads a dash and a typographic quote as ASCII (the one place the port's code differs from P2d-1's) --------------------
def test_fold5_a_dash_or_a_typographic_quote_on_a_line_does_not_withhold_it():
    """On P2d-1's base (fold4) the fold left these characters alone. fold5 writes them as ``-``, ``'`` and ``"``; unported, every line
    with one of them and a fold hit was withheld whole. They are ordinary typography: the value is masked in the line as written."""
    out = redact("“alice@example.com” wrote — josé@example.com")
    assert out.text == "“<EMAIL_1>” wrote — <EMAIL_2>"
    assert out.mapping == {"<EMAIL_1>": "alice@example.com", "<EMAIL_2>": "josé@example.com"}
    minus = redact("ip 10−1 josé@example.com − 5")
    assert minus.text == "ip 10−1 <EMAIL_1> − 5"


def test_fold5_a_value_written_with_typographic_dashes_is_masked_in_place_as_written():
    uid = "123e4567–e89b–12d3–a456–426614174000"  # en dashes: not a UUID as written, one after the fold
    out = redact(f"uid {uid} end")
    assert out.text == "uid <UUID_1> end" and out.mapping == {"<UUID_1>": uid}


def test_fold5_a_full_width_hyphen_is_still_a_compatibility_character_and_withholds_the_line():
    key = "AKIA－IOSFODNN7EXAMPLE"
    out = redact(f"key {key} and josé@example.com").text
    assert out.startswith(FOLD_NOTE) and "IOSFODNN7EXAMPLE" not in out and "example.com" not in out


def test_fold5_the_class_of_every_dash_quote_and_slash_of_the_fold_table_is_pinned():
    import importlib
    import unicodedata

    module = importlib.import_module("hadavin_sdk.guard.redact")
    typed = {}
    for cp in range(0x80, 0x110000):
        ch = chr(cp)
        if 0xD800 <= cp <= 0xDFFF:
            continue
        f = fold(ch)
        if f in ("-", "'", '"', "/") and f != ch:
            typed[cp] = module._char_class(ch)
    plain = {cp for cp, cls in typed.items() if cls is not None and cls[1] == 0}
    # masked around or inside: the dashes (Pd) that are not compatibility forms, the minus sign, the six typographic quotes
    assert all(
        unicodedata.category(chr(cp)) in ("Pd", "Pi", "Pf") or cp == 0x2212 for cp in plain
    ), sorted(map(hex, plain))
    assert {0x2010, 0x2013, 0x2014, 0x2212, 0x2018, 0x2019, 0x201C, 0x201D} <= plain
    assert len(plain) == 26, len(plain)
    # a slash: only the fraction slash is read (masked around, never inside); every other one is refused
    assert typed[0x2044] == ("/", 1)
    assert all(typed[cp] is None for cp in (0x2215, 0x29F8, 0xFF0F, 0x2571))
    # a compatibility dash is refused
    assert typed[0xFF0D] is None and typed[0xFE63] is None and typed[0x2011] is None


# ---- 4. one test per class of the typography decision (ORDER 014 items 9 to 11, confirmed by the lead) ----------------------------
ACCENTED = "josé@example.com"  # a value the fold scan finds (not ASCII as written)


def test_typography_an_em_dash_is_ordinary_the_value_beside_it_is_masked_in_the_line():
    out = redact(f"mail {ACCENTED} — thanks")
    assert out.text == "mail <EMAIL_1> — thanks", "TYPO-EMDASH: " + out.text
    assert out.mapping == {"<EMAIL_1>": ACCENTED} and out.actions == 1


def test_typography_a_curly_quote_is_ordinary_the_value_inside_the_quotes_is_masked_in_the_line():
    out = redact(f"‘{ACCENTED}’ said so, it’s fine")
    assert out.text == "‘<EMAIL_1>’ said so, it’s fine", "TYPO-QUOTE: " + out.text
    assert out.mapping == {"<EMAIL_1>": ACCENTED} and out.actions == 1


def _slash_lookalike(cp: int) -> None:
    slash = chr(cp)
    out = redact(f"a{slash}b mail {ACCENTED}")
    # refused: the line is never shown masked-in-place, it is withheld whole; the slash and the written value are gone
    assert out.text == f"{FOLD_NOTE} <EMAIL_1>", f"TYPO-SLASH-{cp:04X}: {out.text}"
    assert slash not in out.text and "example.com" not in out.text
    assert out.actions == 2  # the hit and the withheld line
    # the character alone hides nothing: a line with no protected value is left as written
    alone = redact(f"a{slash}b and nothing else")
    assert alone.text == f"a{slash}b and nothing else" and alone.actions == 0


def test_typography_the_division_slash_u2215_withholds_a_line_with_a_lookalike_value():
    _slash_lookalike(0x2215)


def test_typography_the_box_drawing_diagonal_u2571_withholds_a_line_with_a_lookalike_value():
    _slash_lookalike(0x2571)


def test_typography_the_big_solidus_u29f8_withholds_a_line_with_a_lookalike_value():
    _slash_lookalike(0x29F8)

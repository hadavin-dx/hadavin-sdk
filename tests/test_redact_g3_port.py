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

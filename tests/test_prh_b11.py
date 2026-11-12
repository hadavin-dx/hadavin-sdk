"""PR H batch 11: the rows of the round-10 review (groups 1 to 6). Every credential-shaped value is built from parts; the only literal is
the allowed example key. Each test names the group it guards and, where one exists, the mutant (tests/prh_mutants.py, numbers 161
and up) that reverts the guard; the failing message of a killer names the planted fault. Cost tests count WORK (characters,
builds, calls), never seconds. A test that also passes on the batch 10 head (5c430b6a) says so and names the one reason it exists."""

import importlib
import re
import unicodedata

import pytest

from hadavin_sdk import defaults, tools
from hadavin_sdk.guard import runmap
from tests.test_prh_b10 import BSL, ESC, KEY, on_the_run_path, spaced, stands

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
SCRUB = tools._DEFAULT_SCRUB
LONG_PW = "Tr0ub4dor" + "3xyzQabc"  # a made-up password


# ---- group 4: one rule for a crash of the redactor at every catcher ---------------------------------------------------------


def _crash(*a, **kw):
    raise runmap.RedactorCrash("RuntimeError")


def _refusal(*a, **kw):
    raise runmap.RedactionError("a plain refusal")


def test_b11_g4_found_values_lets_a_crash_of_the_redactor_pass(monkeypatch):
    """Group 4 (class: one error type handled by opposite rules at sibling catchers; mutant 161). `_found_values` answered "found
    nothing" for a crash, so the last guard (`_remnant_stands`) reported "no remnant" and passed the result."""
    monkeypatch.setattr(runmap, "redact_untrusted", _crash)
    with pytest.raises(runmap.RedactorCrash):
        tools._found_values("a text", [], SCRUB)


def test_b11_g4_found_values_refuses_for_any_other_refusal_of_the_redactor(monkeypatch):
    """Group 4 (mutant 162): a refusal that is not a work limit (a plain one) means "nothing is shown", like `redact_layered`: None,
    and the last guard then reports a remnant. It was `[]` ("found nothing") and the guard passed the result."""
    monkeypatch.setattr(runmap, "redact_untrusted", _refusal)
    assert tools._found_values("a text", [], SCRUB) is None, (
        "mutant 162: a plain refusal of the redactor was read as 'found nothing'"
    )
    assert tools._remnant_stands("one " + ESC + "[0m two", "one two", SCRUB) is True


def test_b11_g4_a_crash_in_the_last_guard_stops_the_tool_path(monkeypatch):
    """Group 4 (end to end, mutant 161): a text with a hidden item reaches the last guard; a crash of the redactor there stops the run
    instead of passing the text."""
    real = runmap.redact_untrusted

    def crash_for_the_guard(text, mapping, refuse_remnants=True):
        if refuse_remnants is False:  # the one call `_found_values` makes
            raise runmap.RedactorCrash("RuntimeError")
        return real(text, mapping, refuse_remnants)

    monkeypatch.setattr(runmap, "redact_untrusted", crash_for_the_guard)
    with pytest.raises(runmap.RedactorCrash):
        tools.prepare_output("line one " + ESC + "[0m line two", {}, 4000, [LONG_PW])


def test_b11_g4_safe_head_lets_a_crash_pass_and_notes_a_refusal(monkeypatch):
    """Group 4 (mutant 163): `safe_head` turned a crash into the fixed note, so the run went on after a bug of the redactor."""
    monkeypatch.setattr(runmap, "redact_bounded", _crash)
    with pytest.raises(runmap.RedactorCrash):
        runmap.safe_head("an error text", 100)
    monkeypatch.setattr(runmap, "redact_bounded", _refusal)
    assert runmap.safe_head("an error text", 100) == runmap.SAFE_HEAD_NOTE


def test_b11_g4_error_reason_lets_a_crash_pass_and_notes_a_refusal(monkeypatch):
    """Group 4 (mutant 202, added in batch 12; the number 164 was never used): the reason shown for a failed tool call; a crash of the redactor stops the run, a refusal is the note."""
    monkeypatch.setattr(runmap, "redact_bounded", _crash)
    with pytest.raises(runmap.RedactorCrash):
        tools.error_reason(ValueError("bad value"))
    monkeypatch.setattr(runmap, "redact_bounded", _refusal)
    assert runmap.SAFE_HEAD_NOTE in tools.error_reason(ValueError("bad value"))


def test_b11_g4_first_decoded_lets_a_crash_pass_and_reads_a_refusal_as_the_character(monkeypatch):
    """Group 4 (mutant 165): the reading of one character in the cut-end check."""
    char = "％"  # a full-width percent sign: a character no earlier test fed the cache
    tools._first_decoded.cache_clear()
    monkeypatch.setattr(runmap, "undo", _crash)
    with pytest.raises(runmap.RedactorCrash):
        tools._first_decoded(char)
    tools._first_decoded.cache_clear()
    monkeypatch.setattr(runmap, "undo", _refusal)
    assert tools._first_decoded(char) == char
    tools._first_decoded.cache_clear()


def test_b11_g4_a_forged_marker_refusal_is_a_withheld_note_on_the_tool_path(monkeypatch):
    """Group 4 (mutant 166). Passes on the batch 10 head too; the one reason it exists: it pins the behaviour the batch 10 notes did not
    name: a refusal for a "forged marker or placeholder" no longer raises on the tool path (it did before batch 10), it is the
    withheld note, and the text is never shown. A work limit and a size limit are the same note."""

    def forged(text, mapping, refuse_remnants=True):
        raise runmap.RedactionError("forged marker or placeholder")

    monkeypatch.setattr(runmap, "redact_untrusted", forged)
    shown = tools.redact_layered("<IPV4_9> " + tools.MARKER, {})
    assert shown == tools.MARKER + tools.TRUNCATED, (
        "mutant 166: a refusal for a forged marker was not turned into the withheld note"
    )


# ---- group 1: any character that is no letter, digit or mark glued to a run is a wrapper -------------------------------------

GLUED = [
    ("“", "”"),  # curly double quotes
    ("‘", "’"),  # curly single quotes
    ("«", "»"),  # guillemets
    ("「", "」"),  # corner brackets
    ("$", ""),
    ("#", ""),
    ("@", ""),
    ("%", ""),
    ("&", ""),
    ("+", ""),
    ("/", ""),
    (BSL, ""),
    ("^", ""),
    ("!", ""),
    ("?", ""),
    ("-", ""),
    ("", "”"),
    ("", "!"),
    ("", "?"),
    ("", "»"),
    ("", "/"),
    ("", "%"),
]


@pytest.mark.parametrize(
    ("front", "back"), GLUED, ids=[f"{a}{b}|{ord((a + b)[0]):x}" for a, b in GLUED]
)
def test_b11_g1_any_character_that_is_no_letter_digit_or_mark_glued_to_a_spaced_key_is_a_wrapper(
    front, back
):
    """Group 1 (mutants 167, 149; class: a spaced secret slips past a rule because of a character glued next to it, fixed with a
    list in batch 10). The characters of the rows are not in the batch 10 list of nine (the two rows with "!" or "?" BEHIND the key pass on the batch 10
    head too: its end rule already held them; they stay as the pin of the other half of the rule). Exact output on the run path; no 6-stretch of
    the key, spaced or not, on the tool path."""
    text = "key: " + front + spaced(KEY) + back + " end"
    want = "key: " + front + "<APIKEY_1>" + back + " end"
    assert on_the_run_path(text) == want, (
        f"mutant 167: a spaced key with {front!r} in front and {back!r} behind was not masked whole"
    )
    out = tools.prepare_output(text, {}, 4000, [])
    assert not stands(out.replace(" ", ""), KEY, 6)


@pytest.mark.parametrize(
    "glued", ["x", "7", "é", "क"], ids=["letter", "digit", "latin_accent", "devanagari"]
)
def test_b11_g1_a_letter_or_a_digit_glued_in_front_makes_the_run_part_of_a_longer_word(glued):
    """Group 1 (no mutant of its own: the lookbehind only matters for a mark, the next test, which kills mutant 168). Passes on the batch 10 head too; the one reason it exists: it pins the other half of the rule, that a
    letter or a digit (of any script) glued to the first character is NOT a wrapper, so the first character belongs to a word
    and the run starts one token later (`xA K I A ...` reads `K I A ...`, which no pattern knows)."""
    text = "key: " + glued + spaced(KEY) + " end"
    assert on_the_run_path(text) == text, f"a run started in the middle of the word {glued + 'A'!r}"


def test_b11_g1_a_combining_mark_glued_in_front_makes_the_run_part_of_a_longer_word():
    """Group 1 (mutant 168). Passes on the batch 10 head too; the one reason it exists: a combining mark (category M) is part of a
    word like a letter (`e` + U+0301 in front), so the run is not started there."""
    text = "key: é" + spaced(KEY) + " end"
    assert on_the_run_path(text) == text, "mutant 168: a combining mark was read as a wrapper"


def test_b11_g1_the_word_class_is_every_letter_digit_and_mark_of_unicode():
    """Group 1 (mutant 170). The class is built from the planes that hold letters, digits and marks; derived here over ALL 1,114,112
    code points and compared (a new Unicode version that adds letters to another plane fails this test). Passes on the batch 10 head
    only by not existing (it has no such class): the check is on the new constant."""
    word = re.compile(f"[{redact_mod._WORD_BODY}]")
    wrong = [
        c
        for c in range(0x110000)
        if (word.fullmatch(chr(c)) is not None)
        != (
            unicodedata.category(chr(c))[0] in "LNM"
            and not redact_mod._IGNORABLE_CHAR.fullmatch(chr(c))
        )
    ]  # batch 12, issue 6: a gap character is no part of a word even when it is a mark or a letter
    assert wrong == [], (
        f"mutant 170: {len(wrong)} code points are in the wrong class, first U+{wrong[0]:04X}"
    )


@pytest.mark.parametrize(
    ("text", "read"),
    [
        (BSL + "e[", True),
        (BSL + "e]", True),
        (BSL + "e(", True),
        (BSL + "e)", True),
        (BSL + "eP", False),
        (BSL + "eX", False),
        (BSL + "e^", False),
        (BSL + "e_", False),
        (BSL + "en", False),
        (BSL + "e", False),
        ("C:" + BSL + "env", False),
        ("C:" + BSL + "Users" + BSL + "err" + BSL + "x", False),
        (
            "ab" + BSL + "eb",
            True,
        ),  # batch 12, issue 2: glued inside a word is read (it was a length rule)
        ("abcdef" + BSL + "eghijkl", True),
        ("abcde" + BSL + "eghijkl", True),  # batch 12, issue 2: 5 characters in front are read too
        (BSL + "eabcdefghijkl", True),
        (BSL + "eabcdefghijk", False),
        ("q" + BSL + "eZ" + BSL + "e7", True),
        ("q" + BSL + "eZ", True),  # batch 12, issue 2: one character on each side is glue
    ],
)
def test_b11_g1_the_shapes_of_backslash_e_that_are_read_as_esc_are_exactly_these(text, read):
    """Group 1, item C5 and group 8 (mutants 171, 142, 183, 184). Passes on the batch 10 head too; the one reason it exists: it lists the backslash-e shapes that are
    read as ESC (before a bracket or a parenthesis; glued between two characters of one word; 12 or more token characters after it)
    and the ones that are not (the string openers `P`, `X`, `^` and `_` standing alone, a letter standing alone, the end of the
    text, a Windows path); SECURITY.md names the same list."""
    assert (runmap.hex_unescape(text) != text) is read, (
        f"mutant 171: {text!r} is {'not ' if read else ''}read as ESC"
    )


# ---- group 2: the dropped-view test compares copies of a held secret, of a secret kind -----------------------------------------


def test_b11_g2_a_secret_that_is_only_a_piece_of_a_held_identifier_is_not_already_found():
    """Group 2, item n1 (mutant 173). The held value is an identifier (an ARN: not a secret kind) that holds the key; the only copy of the
    key in the view stands inside it. The key is not "already found": no secret of the run holds it."""
    arn = "arn:aws:iam::123456789012:user/" + KEY
    current = {"<ARN_1>": arn}
    assert runmap._only_inside_held(KEY, current, ("see " + arn + " end",)) is False, (
        "mutant 173: a secret that is a piece of a held identifier was called already found"
    )


def test_b11_g2_a_copy_outside_every_held_value_is_not_covered_by_a_held_value_that_contains_it():
    """Group 2, item C2 (mutants 174, 177). A held secret holds the shorter value as a piece; the view also holds a second copy of the
    shorter value that no held value covers. The test of batch 10 (`value in held value`) called it found."""
    held = {"<APIKEY_1>": KEY}
    piece = KEY[:12]
    covered = "a " + KEY + " b"
    assert runmap._only_inside_held(piece, held, (covered,)) is True
    with_other_copy = covered + " c " + spaced(piece) + " d"
    assert runmap._only_inside_held(piece, held, (with_other_copy,)) is False, (
        "mutant 174: a copy of the piece outside the held value was not counted"
    )
    assert runmap._only_inside_held(piece, held, (covered, with_other_copy)) is False
    assert runmap._only_inside_held(piece, held, ("a " + spaced(KEY) + " b",)) is True, (
        "a copy written with spaces inside a held value is covered"
    )


def test_b11_g2_a_view_with_no_copy_of_the_value_is_not_proved_covered():
    """Group 2 (mutant 175): a value found in a spelling no gap rule can see is not proved to lie inside a held one."""
    held = {"<APIKEY_1>": KEY}
    assert runmap._only_inside_held(KEY[:12], held, ("nothing of it here",)) is False, (
        "mutant 175: a view with no copy of the value was called covered"
    )


def test_b11_g2_a_view_that_alone_found_the_only_spaced_copy_of_a_shorter_secret_is_not_dropped(
    monkeypatch,
):
    """Group 2 (end to end, mutant 174; fails on the batch 10 head). A made-up password is held; 12 characters of it stand spaced out
    elsewhere, more than the context width away. Only the collapsed view reads that copy. When the check for a remnant refuses that
    view (forced here: the remnant itself is hard to reach, see the batch 11 notes), the view must not be dropped: the text is refused,
    never shown with the spaced copy readable."""
    short = LONG_PW[:12]
    text = (
        f"password={LONG_PW}\n" + "filler words here. " * 8 + f"note password={spaced(short)} end"
    )

    def remnant(out, current):
        raise runmap.InputTooLarge("InputTooLarge")

    monkeypatch.setattr(runmap, "_refuse_remnant", remnant)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_untrusted(text, {})


# ---- group 5: the spaced reads of a call are counted together; the automaton is built once per map version ------------------


def test_b11_g5_the_reads_of_every_view_are_counted_in_the_one_budget_of_the_call(monkeypatch):
    """Group 5 (mutant 178; fails on the batch 10 head). One run that stands in the text as written and in its decoded view is read in
    both; the batch 10 count was per view (each under the budget, the call over it). The budget is set to 1.5 times the cost of ONE
    view, measured by counting the characters the reads will scan."""
    run = " ".join("bcdfghjkmnpqbcdfghjkmnpq")  # 24 characters, 12 different, no pattern reads it
    text = "n: " + run + " %41 end"  # a percent escape makes a decoded view that holds the run too
    seen: list[int] = []
    redact_mod.spaced_unknown("n: " + run + " A end", seen.append)
    one_view = sum(seen)
    assert one_view > 0
    monkeypatch.setattr(defaults, "SPACED_READ_MAX_CHARS", int(one_view * 1.5))
    with pytest.raises(runmap.RedactionLimit):
        runmap.redact_untrusted(text, {})


def test_b11_g5_a_read_is_counted_against_the_call_and_the_clock_before_it_runs():
    """Group 5 (mutants 179, 180): the call's work count refuses over the budget and after the time budget."""
    work = runmap._Work()
    work.charge_spaced(defaults.SPACED_READ_MAX_CHARS)
    assert work.spaced_chars == defaults.SPACED_READ_MAX_CHARS
    with pytest.raises(redact_mod.SpacedRunLimit):
        work.charge_spaced(1)
    late = runmap._Work()
    late.started -= defaults.REDACT_BUDGET_S + 1
    with pytest.raises(runmap.RedactionLimit):
        late.charge_spaced(1)


def test_b11_g5_the_automaton_of_the_held_values_is_built_once_per_map_version(monkeypatch):
    """Group 5 (mutant 176; fails on the batch 10 head). A text with gaps and a known key goes through several sweeps of one map; the
    automaton is built when the map changed, not for every sweep."""
    builds: list[int] = []
    real = redact_mod.spaced_index

    def counting(values):
        values = list(values)
        builds.append(len(values))
        return real(values)

    monkeypatch.setattr(redact_mod, "spaced_index", counting)
    text = "a: " + KEY + " b: one two three " + spaced("bcdfghjkmnpq") + " c: " + KEY + " d: " + KEY
    cache: dict = {}
    r = redact_mod._Redactor({}, cache)
    out = r._patterns(text)
    for _ in range(5):
        r.sweep(out)
    non_empty = [n for n in builds if n]
    assert len(non_empty) <= 1, (
        f"mutant 176: the automaton was built {len(non_empty)} times for one map"
    )


def test_b11_g5_a_value_added_after_the_automaton_was_built_is_in_the_next_one():
    """Group 5 (mutant 181). Passes on the batch 10 head too; the one reason it exists: it pins that the cached automaton is dropped
    with the old map version (a second sweep after the map grew finds the new value written with spaces)."""
    second = "Zq4n" + "Ws8k" + "Lpv3Tr"
    r = redact_mod._Redactor({"<APIKEY_1>": KEY}, {})
    first = r.sweep("one " + spaced(KEY) + " two")
    assert first == "one <APIKEY_1> two"
    r.mapping["<APIKEY_2>"] = second
    r.reverse[second] = "<APIKEY_2>"
    out = r.sweep("three " + spaced(second) + " four")
    assert out == "three <APIKEY_2> four", (
        "mutant 181: the automaton of the old map version was used for the new map"
    )


# ---- group 6: the copy rule is the one of the placeholder the sweep uses --------------------------------------------------


@pytest.mark.parametrize(
    ("order", "stays"),
    [
        (("<APIKEY_1>", "<EMAIL_1>"), False),
        (("<EMAIL_1>", "<APIKEY_1>"), True),
    ],
    ids=[
        "secret first: the sweep masks every copy",
        "identifier first: the sweep masks only standalone copies",
    ],
)
def test_b11_g6_a_value_under_two_placeholders_is_judged_by_the_one_the_sweep_uses(order, stays):
    """Group 6, item D7 (mutant 172; fails on the batch 10 head). One value is held under a secret placeholder and an identifier placeholder;
    the sweep uses the first of them in the map order, `_copy_stays` used the last (the reverse map). A copy glued inside a word
    stays only when the sweep uses the identifier rule."""
    value = "Zq8x" + "Kw3v" + "Lm"
    r = redact_mod._Redactor({order[0]: value, order[1]: value})
    shown = "ab" + value + "cd"
    assert r._copy_stays(value, shown, True) is stays, (
        f"mutant 172: the copy rule came from the other placeholder (order {order})"
    )
    swept = r.sweep(shown)
    assert (value in swept) is stays, "the sweep itself does not follow the same rule"


# ---- group 8: a literal backslash-e spelled inside a secret (the independent runner's cells esc_mid, esc_pre, esc_each, /11) -----


def _glue(*parts):
    """Fakes are built from parts, never written whole."""
    return "".join(parts)


HANDED = _glue("qZ7k", "M3vR", "t9Lx", "P2wB", "n5Hc", "D8fJ", "s4Yg")  # made-up, 28 characters
SHAPED = _glue("gh", "p_", "Ab3dE6gH", "9jK2mN5p", "Q8sT1vW4", "yZ7aC0eF")  # made-up token shape
CELLS = {
    "mid": lambda v: v[:9] + BSL + "e" + v[9:],
    "pre": lambda v: BSL + "e" + v,
    "each": lambda v: (BSL + "e").join(v),
    "ctx": lambda v: "token=" + BSL + "e" + v,
}


@pytest.mark.parametrize("cell", sorted(CELLS))
@pytest.mark.parametrize(
    ("name", "value"), [("hand", HANDED), ("shaped", SHAPED)], ids=["hand", "shaped"]
)
def test_b11_g8_a_value_with_a_literal_backslash_e_spelled_into_it_is_not_shown(cell, name, value):
    """Group 8 (mutants 182, 183, 184; fails on 5c430b6a for mid and pre of the token shape and for mid and each of the handed-out
    value; class: batch 10 narrowed the backslash-e rule and a literal spelling inside a value broke the masking). Whatever the
    redactor does with the text (mask it or withhold it), no 8-character stretch of the value stands in the result, with or
    without the backslash-e spellings in it. Passes on 5c430b6a for the cells that already held (the other rows of the grid): the one
    reason it stays is that it pins the whole grid, not a single cell."""
    text = CELLS[cell](value)
    out = tools.prepare_output(text, {}, 4000, [HANDED])
    for shown in (out, out.replace(BSL + "e", "")):
        assert not stands(shown, value, 8), (
            f"mutants 182 to 184: the value of cell {cell}/{name} is readable"
        )


def test_b11_g8_a_windows_path_takes_no_heavier_path_and_is_left_as_written():
    """Group 8 (no mutant since batch 12; passes on 5c430b6a: the one reason is that it pins the part of batch 10 that must not be undone): paths with
    `\\env`, `\\err` or a short word after a backslash-e are no spelling of ESC, so they add no reading and are shown as written."""
    for path in (
        "C:" + BSL + "env",
        "C:" + BSL + "Users" + BSL + "err" + BSL + "x",
        "D:" + BSL + "tmp" + BSL + "ex" + BSL + "data",
    ):
        assert runmap.hex_unescape(path) == path, f"the path rule: {path!r} was read as ESC"
        assert tools._HIDDENISH.search(path) is None
        assert tools.prepare_output(path, {}, 4000, [HANDED]) == path


def test_b11_g8_the_inside_rule_reads_six_token_characters_on_each_side_and_no_fewer():
    """Group 8 (mutant 183; the cell grid cannot reach it because every cell has 12 or more characters after the spelling or a
    bracket or a chain). Exactly 6 token characters on each side is read as ESC. Batch 12 (issue 2) changed the second half of this
    test: 5 on either side is read too (the glued rule; the name keeps "no fewer" because mutant 183 names this test); it was left as
    written under batch 11's length rule. The 6-and-6 alternative still reads a spelling that a backslash follows within 12 characters
    (the glued rule leaves that shape as a path name)."""
    left, right = "abcdef", "ghijkl"
    assert runmap.hex_unescape(left + BSL + "e" + right) == left + "\x1b" + right, (
        "mutant 183: the inside rule of backslash-e is gone"
    )
    assert (
        runmap.hex_unescape(left + BSL + "e" + right + BSL + "x")
        == left + "\x1b" + right + BSL + "x"
    ), (
        "mutant 183: the inside rule of backslash-e is gone (6 token characters on each side, a backslash after)"
    )
    assert runmap.hex_unescape(left[:5] + BSL + "e" + right) == left[:5] + "\x1b" + right
    assert runmap.hex_unescape(left + BSL + "e" + right[:5]) == left + "\x1b" + right[:5]

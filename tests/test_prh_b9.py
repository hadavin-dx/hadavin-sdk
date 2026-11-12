"""PR H batch 9: the rows of the round-8 review (groups 1 to 11). Every credential-shaped value is built from parts; the only
literal is the allowed example key. Each test names the group it guards and the mutant (tests/prh_mutants.py) that reverts the
guard; the failing message of a killer names the planted fault."""

import pytest

from hadavin_sdk import defaults, tools
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import WITHHELD_NOTE, redact, spaced_unknown

ESC, BEL, ZWSP = "\x1b", "\x07", "\u200b"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HAND = "Tr0ub4dor" + "-3xyzQ"
GH = "gh" + "p_" + "abcdefghijklmnopqrstuv"
MARKER = tools.MARKER
WITHHELD = tools.MARKER + tools.TRUNCATED


def spaced(value: str) -> str:
    return " ".join(value)


# ---- group 1: one killer per survivor of the mutant gate ---------------------------------------------------------------


@pytest.mark.parametrize("tail", ["", " done"])
def test_b9_g1_a_secret_cut_by_a_charset_sequence_is_masked_not_withheld(tail):
    """Mutant 54 (the scrub does not search the consuming reading). `ESC ( B ESC [ m` (what `tput sgr0` writes) cuts a handed-out
    secret: only the consuming reading holds it whole. The result is the text with the value MASKED. Without that reading the
    scrub still withholds the whole text (the mixed reading holds the value), so a test that only asks that no piece stands
    cannot tell the two apart: this one asks for the masked text itself."""
    text = "result: " + HAND[:9] + ESC + "(B" + ESC + "[m" + HAND[9:] + tail
    want = "result: " + MARKER + tail
    for out in (
        tools._scrub(text, [HAND]),
        tools.prepare_output(text, {}, 4000, [HAND]),
    ):
        assert out == want, (
            f"the consuming reading was not searched (withheld instead of masked): {out!r}"
        )


@pytest.mark.parametrize("how", ["%1b", "&#27;", "&#x1b;", "\\u001b"])
def test_b9_g1_an_encoded_escape_before_the_last_letters_of_a_key(how):
    """Mutant 84 (the scrub's decoded readings lack the character reading). `ESC` + `P` is a short control sequence in the
    grammar's reading, so the decoded text loses the `P` of `...EXAMPLE` there; only the character reading of the DECODED text
    holds the whole key. Written as a percent or an entity, the handed-out key must still be found: the scrub gives the marker."""
    text = "INFO " + KEY[:-3] + how + KEY[-3:]
    for out in (
        tools._scrub(text, [KEY]),
        tools.prepare_output(text, {}, 4000, [KEY]),
    ):
        assert out == "INFO " + MARKER, f"the decoded character reading was not searched: {out!r}"


FOLD_ROWS = {
    "zero-width, ESC then a letter, and a key cut again after it": "INFO g"
    + ESC
    + "hp"
    + ESC
    + "K_abcdefghi"
    + ZWSP
    + "jklmnopqrstuv done",
    "bell, zero-width and an ESC taking one letter": "INFO "
    + GH[:1]
    + ESC
    + GH[1:3]
    + ESC
    + "K"
    + GH[3:12]
    + BEL
    + GH[12:]
    + " done",
    "zero-width, an ESC that takes the first letter of the key": "INFO "
    + GH[:1]
    + ESC
    + GH[1:3]
    + ESC
    + "K"
    + GH[3:12]
    + ZWSP
    + GH[12:]
    + " done",
}


@pytest.mark.parametrize("name", list(FOLD_ROWS))
def test_b9_g1_g2_the_stripped_reading_is_one_of_the_folded_readings(name):
    """Mutants 93 and 116 (direct `redact()`: the reading with the ignorable characters taken out is not folded). A text with an
    ESC that opens no sequence (it takes nothing after it) and a zero-width or bell character cuts one key in a way only that
    reading joins: without it the key is masked in front and its tail `jklmnopqrstuv` stands readable. The result masks the
    whole key (no stretch of eight characters of it stands), never a front only (group 2: the reason the fold exists)."""
    text = FOLD_ROWS[name]
    out = redact(text).text
    stretch = [GH[i : i + 8] for i in range(len(GH) - 7)]
    assert out == WITHHELD_NOTE or not any(s in out for s in stretch), (
        f"direct redact() left the tail of a key readable (the stripped reading was not folded): {out!r}"
    )
    assert "<APIKEY" in out or out == WITHHELD_NOTE, repr(out)
    assert ZWSP not in out and BEL not in out, f"the stripped reading was not folded: {out!r}"


SPACED_AND_CUT = [
    spaced(KEY[:17]) + KEY[17:] + "\n" + KEY[:12] + "%1b" + KEY[12:],
    spaced(KEY[:16]) + KEY[16:] + "\n" + KEY[:12] + "%1b" + KEY[12:],
    spaced(KEY[:17]) + KEY[17:] + " " + KEY[:12] + ESC + "(B" + KEY[12:],
]


@pytest.mark.parametrize("text", SPACED_AND_CUT, ids=["pct_a", "pct_b", "charset"])
def test_b9_g1_a_spaced_run_with_a_cut_copy_is_masked_not_refused(text):
    """Mutant 111 (the collapsed spaced run may refuse a text on its own). A key written with spaces, its last letters glued, next
    to a second copy cut by a percent escape or a charset sequence: the collapsed reading masks the first copy, and a stretch of
    the key standing in what that reading leaves is the business of the other readings. The text is masked, not withheld."""
    out = tools.prepare_output(text, {}, 4000, [])
    assert out != WITHHELD, f"the collapsed spaced run refused the text on its own: {out!r}"
    assert "AKIAIOS" not in out and "OSFODNN" not in out and "FODNN7E" not in out, repr(out)
    assert "A K I A" not in out, repr(out)


# ---- group 5: a secret written with separators between its characters ------------------------------------------------------
SEPARATORS = {
    "two spaces": "  ",
    "tab": "\t",
    "new line": "\n",
    "no-break space": " ",
    "space and zero-width": " \u200b",
    "zero-width alone": "\u200b",
    "dash with spaces": " - ",
    "dash": "-",
    "comma and space": ", ",
}


def on_the_run_path(text: str) -> str:
    return runmap.redact_untrusted(text, {})


def stands(out: str, value: str, size: int = 8) -> bool:
    return any(value[i : i + size] in out for i in range(len(value) - size + 1))


@pytest.mark.parametrize("name", list(SEPARATORS))
def test_b9_g5_a_key_written_with_any_separator_is_masked(name):
    """Group 5 (mutant 117, 118): every separator of the review (two spaces, tab, new line, no-break space, zero-width, a dash)
    between the characters of a key-shaped value. Class: a separator the spaced-run reader does not know (it knew one space)."""
    out = on_the_run_path("key: " + SEPARATORS[name].join(KEY) + " end")
    assert out.startswith("key: <APIKEY_1>"), f"a key spaced with {name} was not masked: {out!r}"
    assert not stands(out, KEY)


@pytest.mark.parametrize(
    ("name", "text", "want"),
    [
        ("glued to its key name", "key=" + spaced(KEY), "key=<APIKEY_1>"),
        ("a one-letter word in front", "a " + spaced(KEY), "a <APIKEY_1>"),
        ("a full stop after it", "see " + spaced(KEY) + ".", "see <APIKEY_1>."),
        ("a bracket and a comma after it", "(" + spaced(KEY) + "), next", "(<APIKEY_1>), next"),
    ],
)
def test_b9_g5_a_spaced_key_with_text_around_it(name, text, want):
    """Group 5 (mutants 119 to 121): the value glued to its key (the first character was lost), a one-letter word in front (the whole
    run collapsed to `aAKIA...`), trailing punctuation (the last letter stayed). Exact outputs."""
    assert on_the_run_path(text) == want, name


def test_b9_g5_a_spaced_value_after_its_key_word_is_read_with_the_key_word():
    """Group 5 (mutant 122): `password=` and a value spaced out: the collapsed value alone matches no pattern, the key word
    in front makes it one (the value is read together with the 64 characters before the run)."""
    secret = "hunter2" + "xyzabc"
    out = on_the_run_path("pass" + "word= " + spaced(secret))
    assert out.startswith("pass" + "word= <SECRET_") and out.endswith(">"), out
    assert "h u n" not in out and not stands(out, secret, 6), out


def test_b9_g5_a_value_of_no_pattern_shape_is_not_read_and_the_statement_is_pinned():
    """Group 5 (class: an UNKNOWN value that no pattern reads). A value of no pattern's shape written with spaces is not masked on
    the run path: the reader finds only values the patterns read (SECURITY.md says so, this test pins the statement). A KNOWN
    handed-out value is masked in every spelling (`_mask_spaced_out`)."""
    unknown = "Qx7m" + "Lp9v" + "RtzK" + "w2Ab"
    assert spaced_unknown("note: " + spaced(unknown) + " end") == []
    assert on_the_run_path("note: " + spaced(unknown)) == "note: " + spaced(unknown)
    out = tools.prepare_output("note: " + spaced(unknown) + " end", {}, 4000, [unknown])
    assert out == "note: " + MARKER + " end", out


# ---- group 4: what the spaced-run rule leaves alone, and the 5-against-6 boundary ----------------------------------------------
ORDINARY_ROWS = {
    "alphabet": ("the alphabet: " + spaced("abcdefghijklmnopqrstuvwxyz") + " end"),
    "upper alphabet": spaced("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "hex with letters only": "dump: " + spaced("deadbeefcafe0123"),
    "CJK list": "list: " + spaced("一二三四五六七八九十甲乙丙"),
    "single-character words": "I a m a b c d e f g h i j k l m n o p end",
}


@pytest.mark.parametrize("name", list(ORDINARY_ROWS))
def test_b9_g4_ordinary_spaced_text_is_returned_as_written(name):
    """Group 4 (mutants 109, 115, 123 and the floor): an alphabet, a list of single letters or characters, spaced hex that holds no
    digit table, a CJK list: no pattern reads the collapsed text as a secret, so nothing changes, on both paths. Every row
    has single-character tokens, so `_SPACED_RUN` is reached (the old row had none)."""
    text = ORDINARY_ROWS[name]
    assert on_the_run_path(text) == text
    assert tools.prepare_output(text, {}, 4000, []) == text


def test_b9_g4_a_digit_table_is_masked_by_the_phone_pattern_not_by_the_spaced_run_rule():
    """Group 4: ten digits with spaces are a phone number to the old phone pattern (the same text on main); the spaced-run
    reader finds no secret in them (`spaced_unknown` is empty): exact output."""
    text = "digits 0 1 2 3 4 5 6 7 8 9 end"
    assert spaced_unknown(text) == []
    assert on_the_run_path(text) == "digits <PHONE_1> 8 9 end"


def test_b9_g4_a_repeated_letter_run_has_too_few_different_characters():
    """Group 4 (mutant 115): `x x x x ...` 400 times is not read: the rule needs `SPACED_RUN_MIN_DISTINCT` different
    characters, and the test asserts the output, not only the letter count."""
    text = "x " * 400
    assert spaced_unknown(text) == []
    assert on_the_run_path(text) == text


def test_b9_g4_the_boundary_is_five_against_six_different_characters():
    """Group 4: the rule, written as a claim: a run is read only when it holds at least `SPACED_RUN_MIN_DISTINCT` (6) different
    characters. A key-shaped value of 5 different characters, spaced out, is NOT read (no real key has so few: a key of 20
    characters from 36 symbols holds 5 or fewer different ones with a chance far under one in a million); with 6 it is."""
    assert defaults.SPACED_RUN_MIN_DISTINCT == 6
    three = "AKIA" + "AKIAKIIAKIAKAIAK"  # A, K, I: three different characters
    five = "AKIA" + "AKIQRAKIQRAKIQRA"  # A, K, I, Q, R: five different characters
    six = "AKIA" + "AKQRSAKQRSAKQRSA"  # A, K, I, Q, R, S: six different characters
    assert len(set(three)) == 3 and len(set(five)) == 5 and len(set(six)) == 6
    assert spaced_unknown("v: " + spaced(three)) == []
    assert spaced_unknown("v: " + spaced(five)) == []
    found = spaced_unknown("v: " + spaced(six))
    assert [token for _, _, token in found] == [six]


def test_b9_g4_the_floor_for_a_known_value_is_twelve_characters():
    """Group 4 (mutants 109, 11x): a handed-out value of 11 characters is NOT looked for spaced out (ordinary words would be
    masked), one of 12 is; both through the tool scrub."""
    eleven, twelve = "Qx7mLp9vRtz", "Qx7mLp9vRtzK"
    assert len(eleven) == 11 and len(twelve) == 12 == defaults.SPACED_VALUE_MIN_CHARS
    t11 = "n: " + spaced(eleven) + " e"
    t12 = "n: " + spaced(twelve) + " e"
    assert tools.prepare_output(t11, {}, 4000, [eleven]) == t11
    assert tools.prepare_output(t12, {}, 4000, [twelve]) == "n: " + MARKER + " e"


# ---- group 7: the cost of a spaced run ----------------------------------------------------------------------------------------
def _runs(n: int) -> str:
    return " word ".join(spaced("abcdefghij") for _ in range(n)) + " end"


def test_b9_g7_more_runs_than_the_cap_withhold_the_text():
    """Group 7 (mutant 123): `defaults.SPACED_RUN_MAX_RUNS` candidate runs are read; one more withholds the text (a refusal,
    never a skip, so no run goes unread). Both sides of the bound, on both paths."""
    cap = defaults.SPACED_RUN_MAX_RUNS
    ok, over = _runs(cap), _runs(cap + 1)
    try:
        assert runmap.redact_untrusted(ok, {}) == ok
    except (runmap.RedactionError, runmap.RedactionLimit):
        raise AssertionError("a text with exactly the cap's number of runs was refused") from None
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_untrusted(over, {})
    assert tools.prepare_output(over, {}, 40000, []) == WITHHELD, (
        "a text with more spaced runs than the cap must be withheld"
    )
    assert tools.prepare_output(ok, {}, 40000, []) == ok


def test_b9_g7_the_index_search_finds_what_the_old_loop_found():
    """Group 7 (mutant 124): `spaced_spans` looks each window of the compact text up in an index; over 300 seeded texts (values
    of 12 to 20 characters, copies spaced, cut, doubled and overlapping) it returns what the one-`find`-per-value loop returned."""
    from hadavin_sdk.guard.redact import spaced_spans
    from tests.seeded import rng

    def reference(text, values):
        if " " not in text:
            return []
        wanted = [v for v in values if len(v) >= defaults.SPACED_VALUE_MIN_CHARS and " " not in v]
        pos = [i for i, c in enumerate(text) if c != " "]
        compact = "".join(text[i] for i in pos)
        found = []
        for v in wanted:
            j = compact.find(v)
            while j >= 0:
                a, b = pos[j], pos[j + len(v) - 1] + 1
                if b - a > len(v):
                    found.append((a, b, v))
                j = compact.find(v, j + 1)
        return found

    r = rng(9009)
    alphabet = "abcdeAB-_"  # few letters: copies overlap and share prefixes
    for n in range(300):
        values = [
            "".join(r.choice(alphabet) for _ in range(r.randint(12, 20)))
            for _ in range(r.randint(1, 8))
        ]
        text = ""
        for _ in range(r.randint(1, 6)):
            v = r.choice(values)
            text += (
                r.choice(["", " ", "  "])
                + (" ".join(v) if r.random() < 0.7 else v)
                + r.choice(["", " ", "x"])
            )
        assert sorted(spaced_spans(text, values)) == sorted(reference(text, values)), (
            n,
            text,
            values,
        )


# ---- group 8: a short value that the soft reading masks and the grammar's reading does not --------------------------------------
def test_b9_g8_one_copy_of_a_short_value_cut_by_a_charset_sequence_is_not_left_readable():
    """Group 8 (mutants 125, 127): `ESC ( B` + `1.2.3.4` next to `1.2` + `ESC .` + `3.4`: the grammar's reading masks the second
    copy, the consuming reading the first, and neither output holds both. The old output left the first copy readable
    (`(B1.2.3.4`); the text is withheld now (direct `redact()`). Found by a seeded search of 60,000 texts."""
    text = "x: " + ESC + "(B1.2.3.4 ; 1.2" + ESC + ".3.4"
    out = redact(text).text
    assert out == WITHHELD_NOTE, f"a short value stood readable beside its masked copy: {out!r}"


def test_b9_g8_a_short_value_in_a_soft_conflict_withholds():
    """Group 8 (mutant 125): the same with a second, e-mail shaped value after it; the final guard of `find` compares whole values of 4 or
    more characters that any reading masked."""
    text = "x: " + ESC + "(B1.2.3.4 ; 1.2" + ESC + ".3.4 ; a@b." + ESC + "Kio end"
    assert redact(text).text == WITHHELD_NOTE


# ---- group 9: a find of a soft view is never dropped silently -----------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "log: "
        + spaced(KEY[:3])
        + BEL
        + spaced(KEY[3:])
        + " "
        + spaced(KEY[:3])
        + " "
        + KEY[4:]
        + " end",
        "log: " + spaced(KEY) + " " + spaced(KEY[:3]) + " " + KEY[4:] + " end",
    ],
    ids=["bell_inside_the_run", "plain_run"],
)
def test_b9_g9_a_spaced_key_beside_a_cut_copy_is_masked_or_the_text_is_withheld(text):
    """Group 9 (mutant 126): a spaced-out key whose collapsed reading leaves a stretch of a masked value standing. The old code
    dropped the view (`wins = False`) and the key stayed readable (`A K I A ...` as written, 20 letters). The text is withheld
    now; a view that found a value alone is never dropped."""
    out = tools.prepare_output(text, {}, 4000, [])
    assert out == WITHHELD, f"a spaced-out key was left readable, or the find was dropped: {out!r}"


# ---- group 3: a value only inside an unterminated string body no longer withholds the whole text ---------------------------------
@pytest.mark.parametrize("opener", ["\x90", "\x9d", ESC + "]0;"], ids=["dcs", "osc_c1", "osc_esc"])
def test_b9_g3_a_value_only_inside_an_unterminated_string_body_is_not_shown_and_not_withheld(
    opener,
):
    """Group 3 (mutant 127): a string opener that no terminator closes swallows the rest of its line, the key with it. The
    old code withheld the whole text (`(details withheld)`); the text before the opener is now kept and nothing of the key
    stands. Exact output on the direct call."""
    text = "a " + opener + KEY + " tail words"
    out = redact(text).text
    assert out == "a ", f"the text was withheld or the body was shown: {out!r}"


def test_b9_g3_a_front_of_the_value_before_the_opener_still_withholds():
    """Group 3 (mutant 128): `AKIA` stands before the opener and the rest of the key after it: the character reading finds
    the key, the grammar's output shows the front: the text is withheld (no stretch of 4 characters of a found value stands)."""
    text = "x " + KEY[:4] + "\x90" + KEY[4:] + " rest"
    assert redact(text).text == WITHHELD_NOTE


# ---- evidence leak groups fixed in this batch -------------------------------------------------------------------------------------
BSL = chr(92)


@pytest.mark.parametrize("seq", ["[0m", "(B"], ids=["colour", "charset"])
def test_b9_e1_a_key_cut_by_a_backslash_e_spelling_of_esc_is_masked(seq):
    """Evidence group `\\e` (55 texts of the evidence runner's 4,691; mutant 129): `\\e[0m` (shell and log spelling of ESC) inside a
    key cut it; the run path and the tool path now read `\\e` before `[`, `]`, `(` or `)` as ESC. Exact masked output."""
    text = "log: " + KEY[:6] + BSL + "e" + seq + KEY[6:] + " end"
    assert on_the_run_path(text) == "log: <APIKEY_1> end"
    assert tools.prepare_output(text, {}, 4000, []) == "log: <APIKEY_1> end"


def test_b9_e1_a_backslash_e_that_starts_no_sequence_is_left_alone():
    """Evidence group `\\e` (mutant 130): a Windows path and prose keep their `\\e`; only `\\e` directly before `[`, `]`, `(` or `)` is read."""
    text = "C:" + BSL + "env" + BSL + "path and " + BSL + "e plain, " + BSL + "etc"
    assert on_the_run_path(text) == text
    assert tools.prepare_output(text, {}, 4000, []) == text


def test_b9_e2_a_value_whose_tail_an_unterminated_string_opener_swallowed_is_withheld():
    """Evidence group rand (12 of 4,691, 9 fixed; mutant 131): the string opener U+0090 closes with no terminator, so the grammar's
    reading swallows the rest of the line, the tail of a handed-out value with it; a colour code before it keeps the character
    reading from standing in. No reading holds the value whole and its front stood readable (17 characters). A stretch of the
    value standing in a text that holds such an opener withholds it."""
    value = "Tr0ub4dor" + "-3xyzQ" + "-Vb9mK2"
    text = "x T\x7fr0ub\x1b[1;31m" + value[5:-1] + "\x90" + value[-1] + " y"
    assert tools.prepare_output(text, {}, 4000, [value]) == WITHHELD, (
        "the front of a value stood readable"
    )
    plain = "x " + value[:-1] + " y"
    assert tools.prepare_output(plain, {}, 4000, [value]) == plain, (
        "no hidden item: the text is returned as written"
    )


def _many_runs(n: int, letters: str) -> str:
    return " word ".join(spaced(letters * 3) for _ in range(n)) + " end"


@pytest.mark.parametrize("letters", ["a", "abcde"], ids=["one_letter", "five_letters"])
def test_b9_g7_runs_with_too_few_different_characters_do_not_count_toward_the_cap(letters):
    """Group 7 (mutants 115, 126): 40 stretches of spaced letters with fewer than 6 different characters are not candidates, so
    they cost nothing and the text is not withheld. The distinct-character test sits before the count; with it gone, or one too
    low, 40 candidates pass the cap."""
    text = _many_runs(40, letters)
    assert len(set(letters)) < defaults.SPACED_RUN_MIN_DISTINCT
    try:
        out = runmap.redact_untrusted(text, {})
    except (runmap.RedactionError, runmap.RedactionLimit):
        raise AssertionError(
            "runs with too few different characters were counted toward the cap"
        ) from None
    assert out == text


@pytest.mark.parametrize(
    "gap",
    ["\t", " ", ZWSP + " ", " \t", "\n"],
    ids=["tab", "nbsp", "zwsp_space", "space_tab", "newline"],
)
def test_b9_e3_a_handed_out_value_spaced_out_with_any_whitespace_is_masked(gap):
    """Evidence group spaced (9 of 21 other separators; mutant 132): the gap between the characters of a handed-out value may be
    a tab, a no-break space, an invisible character or a line break, not only one space. Exact masked output."""
    value = HAND + "abc"
    text = "n: " + gap.join(value) + " e"
    assert tools.prepare_output(text, {}, 4000, [value]) == "n: " + MARKER + " e"


# ---- group 1 (resume): two guards whose old killers were random corpora -------------------------------------------------------

_CUT_ONLY_IN_THE_MIXED_READING = [
    "Tr0u" + ESC + "b4dor" + ESC + "[m-3" + ESC + "(BxyzQ",
    "a Tr" + ESC + "0" + ESC + "(Bub4dor-3" + ESC + "xyzQ",
    "T" + ESC + "r0ub4" + ESC + "[0m" + ESC + "(Bdor-3xyzQ; end",
]


@pytest.mark.parametrize("text", _CUT_ONLY_IN_THE_MIXED_READING)
def test_b9_g1_mutant_114_a_value_only_the_mixed_reading_holds_is_not_returned_as_written(text):
    """Mutant 114 (the tool scrub returns the text as written when only the mixed reading holds a value). A lone ESC that keeps
    its byte next to a charset sequence cuts the value in a way only the mixed reading reads whole; the text must not come back
    as it was written."""
    out = tools._scrub(text, [HAND])
    # the exact oracle (batch 10, group 3): the text is withheld, or the value is masked: no 8-character stretch of it stands and the
    # placeholder or the note is there
    withheld_or_masked = out == WITHHELD or (
        not any(HAND[i : i + 8] in out for i in range(len(HAND) - 7)) and MARKER in out
    )
    assert withheld_or_masked, (
        f"mutant 114: the text came back as written, with the value readable in one reading: {out!r}"
    )
    assert out != text and "Tr0ub4d" not in out, (
        f"mutant 114: the text came back as written: {out!r}"
    )


def test_b9_g1_mutant_31_the_scrub_returns_the_checked_result_not_the_first_scrubbed_reading():
    """Mutant 31 (_scrub returns the scrubbed joined text). The character reading would show `[0m` and the value; the result
    that went through the later steps is the one returned."""
    # its own witness text (batch 10, group 3: it shared one with the killer of mutant 59 in tests/test_prh_tools.py)
    text = "b " + ESC + HAND + " | WARN host" + ESC + "[1m" + KEY
    out = tools._scrub(text, [HAND])
    assert "[1m" not in out, (
        f"mutant 31: a reading that shows a control-sequence body was returned: {out!r}"
    )
    assert out == "b " + MARKER + " | WARN host " + MARKER, (
        f"mutant 31: a value stands or the text changed: {out!r}"
    )

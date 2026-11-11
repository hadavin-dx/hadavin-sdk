"""The mutants of the text fold (``guard/textnorm.py``), the look-alike table (``guard/_confusables.py``) and its generator.

Each mutant changes ONE thing in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in ``only_test`` must
fail, it must be the test pinned in ``pinned``, and the first failing line must hold ``expect``: a fragment of the assertion MESSAGE the test
gives for that one guard (never a fragment of the test's own name). Every mutant names both the file of its killer (``test_file``) and the
killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the test placement table. Not collected by
pytest. Run from the repo root:

    uv run python tests/textnorm_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/textnorm_mutants.py squeeze    # only mutants whose name contains the text

78 mutants. The first 53 are P1a's: 28 are the re-pointed mutants of the earlier text-fold list (the killers moved with their tests), 13 are new, 9 are the mutants of fold2 (order 44; the tenth, "no case fold before the marks are dropped", is gone with that case fold, which fix2 showed to be redundant) and 3 are the mutants of fold3 (order 49, U+0345). The next 18 are P1b's (the scan keys); the last 7 are P5a's (the scan time budget: 4, the wrong clock: 1, the Mc exemption: 1, the length check before the weight: 1). Tests with no
mutant: the golden test, the differential rows, the manifest test, the notices test, the perf rows (they are outside every test list below:
the runner copies no ``pyproject.toml`` or notices file) and the meta-tests.

Search strings are exact copies of the formatted source; ``tests/test_textnorm_meta.py`` (g) fails if any occurs 0 or 2+ times. A mutant of
test code is never used: a claim about a test is a meta-test.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
T = "tests/test_textnorm.py"  # the killers of the fold, the input rules and the hidden channel
G = "tests/test_textnorm_generator.py"  # the killers of the table and the generator
SC = "tests/test_textnorm_scan.py"  # the killers of the DENY keys (P1b)
D = "tests/test_textnorm_differential.py"  # the differential rows and the golden test: they have no mutant, they run in the baseline
TESTS = [T, G, SC, D]  # killer files first; golden, differential last
S = "src/hadavin_sdk/guard/"
TN, CF, GEN = S + "textnorm.py", S + "_confusables.py", "tools/gen_confusables.py"


def mutant(name, file, old, new, killer, expect, *, test_file=T, **kw):
    """One mutant: ``killer`` (a test of ``test_file``) must fail first, with a line that holds ``expect``."""
    pin = test_file.removesuffix(".py") + "::" + killer
    return Mutant(
        name, file, old, new, expect, test_file=test_file, only_test=killer, pinned=pin, **kw
    )


# the killers
MARKS = "test_fold_is_stable_under_combining_marks_format_unassigned_and_tag_characters"
LOOKS = "test_fold_covers_the_listed_look_alikes_and_all_map_to_ascii"
ALLOW = "test_allow_decisions_are_exact_and_a_look_alike_is_reported_as_one"
MIXED = "test_mixed_script_is_a_fail_closed_deny_signal"
INVISIBLE = "test_one_invisible_character_cannot_split_a_mixed_script_word"
MICRO = "test_the_micro_and_ohm_signs_are_unit_symbols_not_a_mixed_script"
NEWLINE = "test_a_newline_or_tab_separates_words_in_the_mixed_script_check"
LOOSE = "test_squeeze_loose_reads_the_digit_like_letters_as_digits"
SQUEEZE = "test_squeeze_keeps_upper_case_letters_and_digits_only"
TABLE = "test_the_table_is_generated_from_the_unicode_data_and_every_value_is_ascii"
GENERATOR = "test_the_generator_refuses_an_unpinned_file_and_is_deterministic"
OFFLINE = "test_the_generator_reproduces_the_checked_in_table_offline"
VERSION = "test_the_version_string_names_the_algorithm_the_table_and_both_unicode_versions"
READONLY = "test_the_tables_are_read_only_and_a_later_change_of_the_source_does_not_reach_fold"
SUBCLASS = "test_a_str_subclass_is_refused_by_exact_type_not_by_isinstance"
CAPROW = "test_the_cap_itself_is_accepted_and_one_more_ascii_character_is_refused"
WEIGHT = "test_the_size_rule_counts_what_a_character_becomes_not_its_length"
ORDER = "test_the_size_rule_checks_every_argument_left_to_right"
MAXLEN = "test_max_value_len_is_the_longest_value_of_the_table"
HIDDEN = "test_tag_characters_and_free_variation_selectors_are_a_hidden_channel"
EMOJI = "test_the_two_emoji_selectors_and_other_invisible_characters_are_not_counted"
PINCHECK = "test_check_pinned_unidata_raises_when_strict_and_warns_otherwise"
REQUIRE = "test_require_pinned_unidata_is_the_guard_and_fails_closed"
TAG = "test_a_key_made_on_another_unicode_version_carries_that_version_and_never_equals_another"
IDEM = "test_identity_key_is_idempotent_for_every_code_point"
SYMM = "test_identity_key_is_case_symmetric_for_every_code_point"
SQUEEZE_SYMM = "test_squeeze_is_case_symmetric_for_every_code_point"
DROPS = "test_every_drop_category_code_point_leaves_the_key_of_a_latin_or_greek_letter_unchanged"
MOVES = "test_other_dropped_characters_between_a_greek_letter_and_u0345_do_not_move_the_iota"
ETA = "test_capital_and_small_eta_read_h_and_n_in_both_directions_and_both_readings"
SIGMA = "test_sigma_needs_two_changing_passes_and_the_bound_is_exact"
SK1 = "test_sk1_scan_keyset_has_exactly_one_parameter_named_raw"
SK2 = "test_sk2_at_most_eight_keys_none_longer_than_the_weight_and_the_input_rules_hold"
SK3 = "test_sk3_the_az3x9_rows_ze_reads_as_three_and_z"
SK6 = "test_sk6_hash_tilde_at_pipe_and_the_replacement_character_are_dropped"
TAG0 = "test_tag_t0_the_text_without_its_tag_characters"
TAG1 = "test_tag_t1_the_tag_characters_decoded_in_place"
TAG2 = "test_tag_t2_the_text_followed_by_the_decoded_tag_characters"
TAG3 = "test_tag_t3_the_decoded_tag_characters_alone"
GAP4 = "test_gap4_dashes_slashes_and_quotes_read_as_ascii_in_identity_key"
GAP5 = "test_gap5_hidden_separators_are_dropped_and_the_scan_key_has_no_spaces"
SAMEID = "test_same_person_the_identity_half_and_the_empty_key_sets"
EMPTYMATCH = "test_the_scan_match_of_two_empty_key_sets_is_false_and_x_x_is_true_when_x_has_keys"
L2I = "test_l_to_i_rows"
LMRAW = "test_r12_lm_inserting_any_modifier_letter_still_finds_the_value"
LMFOLD = "test_r12_lm_fold_a_modifier_letter_that_nfkd_turns_into_a_letter_still_matches"
G7A = "test_g7_a_scan_that_ran_over_the_budget_is_refused_with_text_too_long"
G7B = "test_g7_the_budget_is_the_defaults_value_read_at_the_call"
MCX = "test_a_spacing_combining_mark_is_the_tested_exemption_of_the_mark_property"
LENF = "test_the_size_rule_refuses_by_length_before_it_counts_weights"
G7C = "test_g7_the_budget_is_over_only_when_the_clock_is_past_it_not_at_it"
CFTABLE = (
    "test_the_case_fold_table_is_on_the_case_fold_image_and_its_conflicts_are_the_known_conflicts"
)

M = [
    # ---- the 28 re-pointed mutants (rows 1 to 28 of the placement table in the ticket) ----
    mutant("fold: combining marks kept", TN,
        '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}',
        '{"Cc", "Cf", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', MARKS, "U+0301 changes the fold"),
    mutant("fold: unassigned characters kept", TN, '"Co", "Cs", "Cn"}', '"Co", "Cs"}',
        MARKS, "U+E0002 changes the fold"),
    mutant("fold: look-alikes not folded", TN,
        "    s = s.casefold().translate(_CF_TABLE) if casefold else s.translate(_TABLE)",
        "    s = s.casefold() if casefold else s", LOOKS, "look-alike U+0405 is not folded"),
    mutant("fold: other digits not folded", TN,
        "    return s.translate(_DIGITS).translate(_PUNCT)", "    return s.translate(_PUNCT)",
        LOOKS, "other-script digits are not folded"),
    mutant("fold: the digit table is empty", TN,
        "_DIGITS = types.MappingProxyType(\n    _build_digit_table()\n)", "_DIGITS = {}",
        LOOKS, "other-script digits are not folded"),
    mutant("fold: fillers kept", TN, "    if ch in FILLERS or ch == _REPLACEMENT:\n        return False", "    if ch == _REPLACEMENT:\n        return False",
        MARKS, "U+3164 changes the fold"),
    mutant("fold: Greek eta missing", CF, '    0x03B7: "n",\n', "", LOOKS, "look-alike U+03B7 is not folded"),
    mutant("fold: Armenian missing", CF, '    0x0585: "o",\n', "", LOOKS, "look-alike U+0585 is not folded"),
    mutant("fold: dotless i missing", CF, '    0x0131: "i",\n', "", LOOKS, "look-alike U+0131 is not folded"),
    mutant("fold: loose map short", TN,
        'str.maketrans("OILSBZGQ", "01158269")', 'str.maketrans("OIL", "011")',
        LOOSE, "the loose map is short"),
    mutant("fold: confusable pair not detected", TN,
        "        return AllowVerdict.LOOKALIKE", "        return AllowVerdict.DIFFERENT",
        ALLOW, "a look-alike is not reported as one"),
    mutant("fold: mixed script never true", TN,
        "            if latin and other:\n                return True",
        "            if False:\n                return True", MIXED, "is not flagged"),
    mutant("allow: equality is normalised", TN,
        "    if a == b:\n        return AllowVerdict.EQUAL",
        "    if _canon(a) == _canon(b):\n        return AllowVerdict.EQUAL", ALLOW, "gave EQUAL, wanted VARIANT"),
    mutant("allow: a mismatch is always a look-alike", TN,
        "    return AllowVerdict.DIFFERENT", "    return AllowVerdict.LOOKALIKE",
        ALLOW, "an ordinary mismatch is not DIFFERENT"),
    mutant("mixed: invisible characters not removed first", TN,
        "            ch not in _UNIT_SYMBOLS\n            and ch not in FILLERS\n            and unicodedata.category(ch) not in _DROP_CATEGORIES\n",
        "            ch not in _UNIT_SYMBOLS\n", INVISIBLE, "splits a mixed word"),
    mutant("mixed: the micro sign is flagged", TN,
        "            ch not in _UNIT_SYMBOLS\n", "            True\n", MICRO, "a micro or ohm sign is flagged"),
    mutant("mixed: Cherokee exempt next to Latin", TN,
        '{"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo"}', '{"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo", "Cherokee"}',
        INVISIBLE, "Cherokee next to Latin is not flagged"),
    mutant("table: Cherokee A missing", CF, '    0x13AA: "A",\n', "", TABLE,
        "named look-alike U+13AA is not folded", test_file=G),
    mutant("table: small capital rule missing", GEN, "            out.setdefault(cp, m[1])", "            pass",
        GENERATOR, "the small capital rule is missing", test_file=G),
    mutant("table: ASCII sources accepted", GEN, "        if src < 0x80 or not re.fullmatch", "        if not re.fullmatch",
        GENERATOR, "an ASCII source was accepted", test_file=G),
    mutant("table: capital I prototype stays l", GEN, '            dst = "I"', '            dst = "l"',
        GENERATOR, "capital I prototype read as l", test_file=G),
    mutant("table: the generator accepts any file", GEN, "    if sha != pinned_sha256:", "    if False:",
        GENERATOR, "accepted an unpinned file", test_file=G),
    mutant("table: the pin in the generator differs", GEN, 'PINNED_SHA256 = "8289f833', 'PINNED_SHA256 = "9289f833',
        TABLE, "pins another sha256", test_file=G),
    mutant("allow: a case difference is a spoof alarm", TN,
        "    if _canon(a) == _canon(b):\n        return AllowVerdict.VARIANT",
        "    if False:\n        return AllowVerdict.VARIANT", ALLOW, "gave LOOKALIKE, wanted VARIANT"),
    mutant("allow: a verdict has a truth value", TN,
        "        raise TypeError(\"an AllowVerdict has no truth value: compare with 'is AllowVerdict.EQUAL'\")",
        "        return True", ALLOW, "an AllowVerdict has a truth value"),
    mutant("deny: same_person does not fold", TN,
        "    return identity_key(a) == identity_key(b) or _scan_match(a, b)", "    return a == b", ALLOW, "same_person does not fold a look-alike"),
    mutant("textnorm: a newline joins the words of the script check", TN,
        '        " " if ch.isspace() else ch  # a newline or tab separates words, as in fold',
        '        "" if ch.isspace() else ch  # a newline or tab separates words, as in fold',
        NEWLINE, "joins the words of the script check"),
    mutant("table: the vendored data file differs from the pin", "tools/data/confusables.txt",
        "# Date: 2023-08-11, 17:46:40 GMT", "# Date: 2023-08-12, 17:46:40 GMT",
        OFFLINE, "is not the pinned one", test_file=G),
    # ---- the 13 new mutants ----
    mutant("version: FOLD_VERSION built without ud=", TN,
        '    f"|ucd={_confusables.DATA_VERSION}|ud={unicodedata.unidata_version}"',
        '    f"|ucd={_confusables.DATA_VERSION}"', VERSION, "FOLD_VERSION has the wrong shape"),
    mutant("table: the table is a mutable dict", TN,
        "_TABLE = types.MappingProxyType(dict(CONFUSABLES))", "_TABLE = dict(CONFUSABLES)",
        READONLY, "_TABLE accepts an assignment"),
    mutant("input: isinstance instead of the exact type", TN,
        "if type(text) is not str:", "if not isinstance(text, str):", SUBCLASS, "a str subclass is accepted"),
    mutant("size: a text of exactly the cap is refused", TN,
        "if weight > defaults.TEXTNORM_MAX_CHARS:", "if weight >= defaults.TEXTNORM_MAX_CHARS:",
        CAPROW, "a text of exactly the cap is refused"),
    mutant("size: plain length instead of the weight", TN,
        "        weight = _weight(text)", "        weight = len(text)", WEIGHT,
        "87,382 x U+1F75C (W 262,146) is accepted"),
    mutant("size: only the first argument is checked", TN,
        "    for text in texts:\n        if type(text) is not str:", "    for text in texts[:1]:\n        if type(text) is not str:",
        ORDER, "names_equal skipped the second argument"),
    mutant("table: MAX_VALUE_LEN set to 2", CF, "MAX_VALUE_LEN = 3", "MAX_VALUE_LEN = 2",
        MAXLEN, "MAX_VALUE_LEN is not the table maximum"),
    mutant("hidden: the selector supplement E0100 to E01EF missing", TN,
        r"\ufe00-\ufe0d\U000e0100-\U000e01ef]", r"\ufe00-\ufe0d]", HIDDEN, "selector U+E0100"),
    mutant("hidden: the four Mongolian selectors missing", TN,
        r"\u180b-\u180d\u180f\ufe00", r"\ufe00", HIDDEN, "Mongolian selector U+180B"),
    mutant("hidden: the emoji selectors counted", TN,
        r"\ufe00-\ufe0d\U000e0100", r"\ufe00-\ufe0f\U000e0100", EMOJI, "a colour emoji is reported as a hidden channel"),
    mutant("pin: the pinned version bound at definition", TN,
        "def check_pinned_unidata(expected: str | None = None, *, strict: bool = False) -> None:",
        "def check_pinned_unidata(expected: str | None = defaults.TEXTNORM_PINNED_UNIDATA, *, strict: bool = False) -> None:",
        PINCHECK, "the patched pinned version is not used"),
    mutant("squeeze: the pattern keeps no digits", TN,
        '_NON_ALNUM = re.compile(r"[^A-Z0-9]")', '_NON_ALNUM = re.compile(r"[^A-Z]")', SQUEEZE, "squeeze removed a digit"),
    mutant("squeeze: no upper-casing", TN, "    s = _fold(raw, casefold=True).upper()", "    s = _fold(raw, casefold=True)", SQUEEZE, "squeeze lost a letter"),
    # ---- the mutants of fold2 (order 44): the order of the fold, the Unicode pin and its tag ----
    mutant("order: the look-alike table runs before the case fold (the old order)", TN,
        "    s = s.casefold().translate(_CF_TABLE) if casefold else s.translate(_TABLE)",
        "    s = s.translate(_TABLE).casefold() if casefold else s.translate(_TABLE)",
        IDEM, "identity_key is not idempotent for"),
    mutant("order: the case fold table is the raw table", TN,
        "_CF_TABLE = types.MappingProxyType(_build_cf_table(CONFUSABLES))",
        "_CF_TABLE = types.MappingProxyType(dict(CONFUSABLES))", CFTABLE, "is not a casefolded non-ASCII key"),
    mutant("order: a capital wins over its own small letter", TN,
        "    return {**derived, **own}", "    return {**own, **derived}", CFTABLE, "does not take the entry of its own letter"),
    mutant("squeeze: no case fold before the look-alike table", TN,
        "    s = _fold(raw, casefold=True).upper()", "    s = _fold(raw).upper()", SQUEEZE_SYMM, "squeeze is not case symmetric for"),
    mutant("pin: require_pinned_unidata only warns", TN,
        "    check_pinned_unidata(expected, strict=True)", "    check_pinned_unidata(expected)", REQUIRE, "UserWarning: Unicode data"),
    mutant("pin: require_pinned_unidata binds the pin at definition", TN,
        "def require_pinned_unidata(expected: str | None = None) -> None:",
        "def require_pinned_unidata(expected: str | None = defaults.TEXTNORM_PINNED_UNIDATA) -> None:",
        REQUIRE, "the patched pin is not read"),
    mutant("tag: a key of another Unicode version has no tag", TN,
        "    if version == defaults.TEXTNORM_PINNED_UNIDATA:", "    if True:", TAG, "a key made on another Unicode version equals the pinned key"),
    mutant("tag: the tag does not name the version", TN,
        '    return f"\\ue000alg={_ALG}|ud={version}\\ue000"', '    return f"\\ue000alg={_ALG}\\ue000"', TAG, "the tag does not name the algorithm"),
    mutant("tag: the key of another version is folded again with its tag", TN,
        "    if tag and raw.startswith(tag):", "    if False:", TAG, "the key of another version is not idempotent"),
    # ---- the mutants of fold3 (order 49): U+0345 ----
    mutant("iota: U+0345 is an iota after any letter, not only a Greek one", TN,
        "            if last and _is_greek_letter(last):", "            if True:", DROPS, "a drop-category code point changes the key of a letter"),
    mutant("iota: U+0345 is always removed, also after a Greek letter", TN,
        "            if last and _is_greek_letter(last):", "            if False:", SYMM, "identity_key is not case symmetric for"),
    mutant("iota: a dropped character hides the Greek letter in front of U+0345", TN,
        "        if _kept(ch):\n            last = ch",
        "        last = ch", MOVES, "a dropped character moves the iota"),
    # ---- the 18 mutants of P1b (scan_keyset, same_person, gap 4, the modifier letters); each names its killer in tests/test_textnorm_scan.py ----
    mutant("scan: reading B omitted", TN, "        for step in (_pass_a, _pass_b)", "        for step in (_pass_a,)",
        ETA, "reading B is missing", test_file=SC),
    mutant("scan: the not-converged raise returns the last output", TN,
        '    raise FoldNotConverged(\n        f"a reading was still changing after {defaults.TEXTNORM_MAX_PASSES} passes"\n    )',
        "    return text", SIGMA, "did not raise FoldNotConverged", test_file=SC),
    mutant("scan: class map z to 3 removed", TN, '_CLASS_MAP = str.maketrans("zl", "3i")', '_CLASS_MAP = str.maketrans("l", "i")',
        SK3, "the class map z to 3 is missing", test_file=SC),
    mutant("scan: no drop of whitespace in the key", TN, 'ch.isalnum() and unicodedata.category(ch) != "Lm"',
        '(ch.isalnum() or ch.isspace()) and unicodedata.category(ch) != "Lm"', GAP5, "a hidden separator splits the value", test_file=SC),
    mutant("tag: T0 dropped", TN, '    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]',
        '    return ["".join(t1), text0 + "".join(decoded), "".join(decoded)]', TAG0, "T0 (the text without its tag characters)", test_file=SC),
    mutant("tag: T1 dropped", TN, '    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]',
        '    return [text0, text0 + "".join(decoded), "".join(decoded)]', TAG1, "T1 (the tag characters decoded in place)", test_file=SC),
    mutant("tag: T2 dropped", TN, '    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]',
        '    return [text0, "".join(t1), "".join(decoded)]', TAG2, "T2 (the text followed by the decoded", test_file=SC),
    mutant("tag: T3 dropped", TN, '    return [text0, "".join(t1), text0 + "".join(decoded), "".join(decoded)]',
        '    return [text0, "".join(t1), text0 + "".join(decoded)]', TAG3, "T3 (the decoded tag characters alone)", test_file=SC),
    mutant("scan_keyset: a clock parameter added", TN, "def scan_keyset(raw: str) -> frozenset[str]:",
        "def scan_keyset(raw: str, clock=None) -> frozenset[str]:", SK1, "a clock or a deadline was added", test_file=SC),
    mutant("scan_keyset: a text over the size rule does not raise", TN,
        '    _checked(raw)\n    deadline = _clock() + defaults.REDACT_BUDGET_S\n    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")',
        '    deadline = _clock() + defaults.REDACT_BUDGET_S\n    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")', SK2, "accepted a text over the size rule", test_file=SC),
    mutant("gap 4: the dash, slash and quote map removed", TN, "    return s.translate(_DIGITS).translate(_PUNCT)",
        "    return s.translate(_DIGITS)", GAP4, "gap 4 map", test_file=SC),
    mutant("same_person: the identity half removed", TN, "    return identity_key(a) == identity_key(b) or _scan_match(a, b)",
        "    return _scan_match(a, b)", SAMEID, "the identity half of same_person is missing", test_file=SC),
    mutant("fold: U+FFFD kept in step S2", TN, "    if ch in FILLERS or ch == _REPLACEMENT:", "    if ch in FILLERS:",
        SK6, "U+FFFD is kept by the fold", test_file=SC),
    mutant("scan: class map l to i removed", TN, '_CLASS_MAP = str.maketrans("zl", "3i")', '_CLASS_MAP = str.maketrans("z", "3")',
        L2I, "row 1: the class map l to i is missing", test_file=SC),
    mutant("scan: the drop keeps non-whitespace punctuation", TN, 'ch.isalnum() and unicodedata.category(ch) != "Lm"',
        'not ch.isspace() and unicodedata.category(ch) != "Lm"', L2I, "row 1: the key holds a character", test_file=SC),
    mutant("scan: both empty key-sets count as a match", TN, "    return bool(scan_keyset(a) & scan_keyset(b))",
        "    return bool(scan_keyset(a) & scan_keyset(b)) or not (scan_keyset(a) or scan_keyset(b))", EMPTYMATCH,
        "two empty key-sets match", test_file=SC),
    mutant("scan: the raw removal of modifier letters skipped", TN,
        '    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")', "    raw = raw", LMRAW, "hides the value", test_file=SC),
    mutant("scan: the modifier-letter test removed from the key drop", TN, ' and unicodedata.category(ch) != "Lm"', "",
        LMFOLD, "survives in the key", test_file=SC),
    mutant("scan: the budget check before a pass removed", TN, "        if deadline is not None and _clock() > deadline:",
        "        if False:", G7A, "DID NOT RAISE", test_file=SC),
    mutant("scan: the deadline is not passed to the reading", TN, "        _scan_key(text, step, deadline)",
        "        _scan_key(text, step)", G7A, "DID NOT RAISE", test_file=SC),
    mutant("scan: the budget is a constant, not the defaults value", TN, "    deadline = _clock() + defaults.REDACT_BUDGET_S",
        "    deadline = _clock() + 6.0", G7B, "DID NOT RAISE", test_file=SC),
    mutant("scan: a call exactly at the budget is refused", TN, "        if deadline is not None and _clock() > deadline:",
        "        if deadline is not None and _clock() >= deadline:", G7C, "exactly at the budget", test_file=SC),
    mutant("scan: the clock is time.time, not time.monotonic", TN, "    return time.monotonic()", "    return time.time()",
        G7A, "DID NOT RAISE", test_file=SC),
    mutant("fold: spacing combining marks (Mc) dropped", TN,
        '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', '{"Cc", "Cf", "Mn", "Mc", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}',
        MCX, "'Mc' not in", test_file=T),
    mutant("size rule: the length check before the weight removed", TN,
        "        # every character weighs at least 1, so a text longer than the cap is refused before the linear count of _weight\n        if len(text) > defaults.TEXTNORM_MAX_CHARS:\n            raise TextTooLong(\n                f\"text length {len(text)} is over the limit {defaults.TEXTNORM_MAX_CHARS}\"\n            )\n",
        "", LENF, "the weight was counted", test_file=T),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    first_lines = {}

    def show(
        row,
    ):  # one line per mutant, as soon as it finishes: a timeout of the whole run still leaves a kill list
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        TESTS,
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)

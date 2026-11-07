"""The mutants of the text fold (``guard/textnorm.py``), the look-alike table (``guard/_confusables.py``) and its generator.

Each mutant changes ONE thing in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in ``only_test`` must
fail, it must be the test pinned in ``pinned``, and the first failing line must hold ``expect``: a fragment of the assertion MESSAGE the test
gives for that one guard (never a fragment of the test's own name). Every mutant names both the file of its killer (``test_file``) and the
killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the test placement table. Not collected by
pytest. Run from the repo root:

    uv run python tests/textnorm_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/textnorm_mutants.py squeeze    # only mutants whose name contains the text

128 mutants: 28 are the re-pointed mutants of the earlier text-fold list (the killers moved with their tests), 12 are new (one of the 13 went with the deleted ``check_pinned_unidata``), 9 are the mutants of fold2 (order 44), 3 are the mutants of fold3 (order 49, U+0345) and 16 are the mutants of fold4 (fix3, review 3: the spelling variants, the length check, the caseless form; the first of the 16 is the fold2 mutant "no case fold before the marks are dropped" that fold3 removed and that is restored here: it changes only the single key, and the U+0345 test kills it) and 9 are the mutants of fix4 (order 79: the 15.1.0 data pin, the marks, the plain-words messages, the weight pre-check) and 14 are the mutants of fix5 (the marks-dropped views, the letter and digit name rules, the pin constant), 5 are the mutants of fix6 (the script views, the minimum view length, the supplement merge) and 32 are the mutants of fix7 (the script view per script, the minimum per kind of view, the checks of the minimums, the proof rule, what loose loosens). The dead branch of the old script view is an equivalent mutant (it could not change a result), so it has no entry. Tests with no
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
D = "tests/test_textnorm_differential.py"  # the differential rows and the golden test: they have no mutant, they run in the baseline
TESTS = [T, G, D]  # killer files first; golden, differential last
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
MCKEPT = (
    "test_the_spelling_variants_keep_a_spacing_combining_mark_while_the_scan_views_find_the_secret"
)
MCSQUEEZE = "test_squeeze_views_finds_a_secret_hidden_with_every_spacing_mark_modifier_letter_or_modifier_symbol"
NONALNUM = "test_squeeze_views_removes_every_character_that_reads_as_no_ascii_letter_or_digit"
SIXVIEWS = "test_the_marks_dropped_views_are_at_most_six_for_squeeze_and_nine_for_fold_and_keep_every_script_and_letter"
SCRIPTINS = "test_a_separator_an_ascii_letter_or_a_mark_inserted_into_a_chinese_hindi_or_thai_value_does_not_hide_it"
MINVIEW = "test_the_minimum_view_length_is_one_number_per_kind_of_view_and_a_short_value_is_refused"
SQUEEZE4 = "test_a_squeeze_view_needs_four_characters_so_a_short_latin_name_is_refused"
SCRIPT4 = "test_a_script_view_needs_four_letters_but_two_ideographs_are_a_name"
SEPONLY = "test_a_value_found_only_by_a_view_that_keeps_separators_is_refused"
FOREIGN = "test_a_letter_of_another_script_inserted_at_any_position_does_not_hide_a_script_value"
SAMESCRIPT = "test_a_letter_of_the_same_script_inserted_into_a_script_value_still_hides_it_the_documented_limit"
CLASSSWEEP = (
    "test_every_letter_of_another_script_is_dropped_from_the_script_view_of_a_chinese_value"
)
GROUPS = "test_the_script_groups_are_the_first_word_of_the_name_with_han_and_kana_merged"
VALSCRIPTS = "test_the_scripts_of_a_value_do_not_come_from_its_modifier_letters_or_ascii_letters"
SCRIPTARG = "test_scripts_given_to_fold_views_must_be_a_frozenset_of_text"
MINCONST = "test_the_minimum_constants_are_checked_when_the_module_is_imported_and_when_a_scan_takes_its_needles"
SCRIPTVIEW = "test_the_script_view_keeps_only_letters_of_the_given_scripts_and_is_left_out_when_empty_or_repeated"
HINDI = "test_the_script_view_of_a_hindi_value_is_its_letters_with_the_vowel_signs_gone"
LOOSEHALF = "test_loose_loosens_only_the_squeeze_half_of_the_needles"
BOUNDS = "test_the_view_bounds_hold_with_the_script_views_and_nine_is_an_upper_bound"
SUPPLEMENT = "test_a_supplement_entry_is_never_overridden_by_a_name_rule_and_the_data_wins_over_the_supplement"
NOASCII = "test_a_value_with_no_ascii_letter_or_digit_is_found_by_the_fold_views_scan_when_a_mark_is_inserted"
PINTABLE = "test_no_table_source_is_in_a_dropped_category"
RULES = "test_the_name_rules_of_the_generator_read_the_letter_and_digit_forms"
NEGLETTERS = (
    "test_negative_circled_negative_squared_and_regional_indicator_letters_read_as_their_letter"
)
EMPTYKEY = "test_the_empty_and_invisible_only_texts_have_the_empty_key"
PLAINMSG = "test_the_refusal_messages_say_in_plain_words_what_is_wrong"
NOWORK = "test_a_text_over_the_weight_is_refused_before_any_fold_work"
GENVER = "test_the_generator_refuses_any_other_unicode_version_before_it_looks_at_the_hash"
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
REQUIRE = "test_require_pinned_unidata_is_the_guard_and_fails_closed"
TAG = "test_a_key_made_on_another_unicode_version_carries_that_version_and_never_equals_another"
IDEM = "test_identity_key_is_idempotent_for_every_code_point"
SYMM = "test_identity_key_is_case_symmetric_for_every_code_point"
SQUEEZE_SYMM = "test_squeeze_is_case_symmetric_for_every_code_point"
DROPS = "test_every_drop_category_code_point_leaves_the_key_of_a_latin_or_greek_letter_unchanged"
MOVES = "test_other_dropped_characters_between_a_greek_letter_and_u0345_do_not_move_the_iota"
NOTTRANS = "test_the_readings_are_not_transitive_and_over_match_on_purpose"
FOURCAP = "test_the_four_greek_capitals_that_look_like_latin_capitals_are_could_be_the_same_person"
KEYSET = "test_identity_keys_is_a_small_fixed_set_that_holds_the_single_key"
GREEKLOOK = "test_a_greek_look_alike_with_ypogegrammeni_is_the_latin_word_for_could_be_same_person_and_for_a_scan"
TAGKEYS = "test_a_key_made_on_another_unicode_version_carries_the_tag_on_every_reading"
CHEAP = "test_the_cheap_length_check_runs_before_any_per_character_work"
NAMESSYM = "test_names_equal_and_the_canonical_form_are_case_symmetric_for_every_code_point"
U0345 = "test_u0345_is_an_iota_after_a_greek_letter_and_is_removed_everywhere_else"
CFTABLE = (
    "test_the_case_fold_table_is_on_the_case_fold_image_and_its_conflicts_are_the_known_eleven"
)

M = [
    # ---- the 28 re-pointed mutants (rows 1 to 28 of the placement table in the ticket) ----
    mutant("fold: combining marks kept", TN,
        '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}',
        '{"Cc", "Cf", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', MARKS, "U+0301 changes the fold"),
    mutant("fold: unassigned characters kept", TN, '"Co", "Cs", "Cn"}', '"Co", "Cs"}',
        MARKS, "U+E0002 changes the fold"),
    mutant("fold: look-alikes not folded", TN,
        "    if not casefold:\n        s = s.translate(_TABLE)\n    elif table_first:\n        s = s.translate(_TABLE).casefold().translate(_CF_TABLE)\n    else:\n        s = s.casefold().translate(_CF_TABLE)\n",
        "    s = s.casefold() if casefold else s\n", LOOKS, "look-alike U+0405 is not folded"),
    mutant("fold: other digits not folded", TN,
        "    return s.translate(_DIGITS)", "    return s",
        LOOKS, "other-script digits are not folded"),
    mutant("fold: the digit table is empty", TN,
        "_DIGITS = types.MappingProxyType(\n    _build_digit_table()\n)", "_DIGITS = {}",
        LOOKS, "other-script digits are not folded"),
    mutant("fold: fillers kept", TN, "_DROP_CATEGORIES and ch not in FILLERS)", "_DROP_CATEGORIES and True)",
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
    mutant("mixed: Cherokee not a look-alike script", TN,
        '"CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE", "COPTIC",', '"CYRILLIC", "GREEK", "ARMENIAN", "COPTIC",',
        INVISIBLE, "Cherokee next to Latin is not flagged"),
    mutant("table: Cherokee A missing", CF, '    0x13AA: "A",\n', "", TABLE,
        "named look-alike U+13AA is not folded", test_file=G),
    mutant("table: small capital rule missing", GEN, "            out.setdefault(cp, value)", "            pass",
        GENERATOR, "the small capital rule is missing", test_file=G),
    mutant("table: ASCII sources accepted", GEN, "        if src < 0x80 or not re.fullmatch", "        if not re.fullmatch",
        GENERATOR, "an ASCII source was accepted", test_file=G),
    mutant("table: capital I prototype stays l", GEN, '            dst = "I"', '            dst = "l"',
        GENERATOR, "capital I prototype read as l", test_file=G),
    mutant("table: the generator accepts any file", GEN, "    if sha != PINNED_SHA256:", "    if False:",
        GENVER, "an edited file is accepted", test_file=G),
    mutant("table: the pin in the generator differs", GEN, 'PINNED_SHA256 = "8289f833', 'PINNED_SHA256 = "9289f833',
        TABLE, "pins another sha256", test_file=G),
    mutant("allow: a case difference is a spoof alarm", TN,
        "    if _canon(a) == _canon(b):\n        return AllowVerdict.VARIANT",
        "    if False:\n        return AllowVerdict.VARIANT", ALLOW, "gave LOOKALIKE, wanted VARIANT"),
    mutant("allow: a verdict has a truth value", TN,
        "        raise TypeError(\"an AllowVerdict has no truth value: compare with 'is AllowVerdict.EQUAL'\")",
        "        return True", ALLOW, "an AllowVerdict has a truth value"),
    mutant("deny: could_be_same_person does not fold", TN,
        "    return not set(_keys(a)).isdisjoint(_keys(b))", "    return a == b", ALLOW, "could_be_same_person does not fold a look-alike"),
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
        "_TABLE = types.MappingProxyType(dict(_CONFUSABLES))", "_TABLE = dict(_CONFUSABLES)",
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
        ORDER, "could_be_same_person skipped the second argument"),
    mutant("table: MAX_VALUE_LEN set to 2", CF, "MAX_VALUE_LEN = 3", "MAX_VALUE_LEN = 2",
        MAXLEN, "MAX_VALUE_LEN is not the table maximum"),
    mutant("hidden: the selector supplement E0100 to E01EF missing", TN,
        r"\ufe00-\ufe0d\U000e0100-\U000e01ef]", r"\ufe00-\ufe0d]", HIDDEN, "selector U+E0100"),
    mutant("hidden: the four Mongolian selectors missing", TN,
        r"\u180b-\u180d\u180f\ufe00", r"\ufe00", HIDDEN, "Mongolian selector U+180B"),
    mutant("hidden: the emoji selectors counted", TN,
        r"\ufe00-\ufe0d\U000e0100", r"\ufe00-\ufe0f\U000e0100", EMOJI, "a colour emoji is reported as a hidden channel"),
    mutant("squeeze: the pattern keeps no digits", TN,
        '_NON_ALNUM = re.compile(r"[^A-Z0-9]")', '_NON_ALNUM = re.compile(r"[^A-Z]")', SQUEEZE, "squeeze removed a digit"),
    mutant("squeeze: no upper-casing", TN, "    s = _fold(raw, casefold=True).upper()", "    s = _fold(raw, casefold=True)", SQUEEZE, "squeeze lost a letter"),
    # ---- the mutants of fold2 (order 44): the order of the fold, the Unicode pin and its tag ----
    mutant("order: the look-alike table runs before the case fold (the old order)", TN,
        "        s = s.casefold().translate(_CF_TABLE)\n",
        "        s = s.translate(_TABLE).casefold()\n",
        IDEM, "identity_key is not idempotent for"),
    mutant("order: the case fold table is the raw table", TN,
        "_CF_TABLE = types.MappingProxyType(_build_cf_table(_CONFUSABLES))",
        "_CF_TABLE = types.MappingProxyType(dict(_CONFUSABLES))", CFTABLE, "is not a casefolded non-ASCII key"),
    mutant("order: a capital wins over its own small letter", TN,
        "    return {**derived, **own}", "    return {**own, **derived}", CFTABLE, "does not take the entry of its own letter"),
    mutant("squeeze: no case fold before the look-alike table", TN,
        "    s = _fold(raw, casefold=True).upper()", "    s = _fold(raw).upper()", SQUEEZE_SYMM, "squeeze is not case symmetric for"),
    mutant("pin: require_pinned_unidata only warns", TN,
        '        raise UnidataMismatch(\n            f"this Python uses', '        print(\n            f"this Python uses', REQUIRE, "require_pinned_unidata accepted another Unicode version"),
    mutant("pin: require_pinned_unidata binds the pin at definition", TN,
        "def require_pinned_unidata(expected: str | None = None) -> None:",
        "def require_pinned_unidata(expected: str | None = defaults.TEXTNORM_PINNED_UNIDATA) -> None:",
        REQUIRE, "the patched pin is not read"),
    mutant("tag: a key of another Unicode version has no tag", TN,
        "    if version == defaults.TEXTNORM_PINNED_UNIDATA:", "    if True:", TAG, "a key made on another Unicode version equals the pinned key"),
    mutant("tag: the tag does not name the version", TN,
        '    return f"\\ue000alg={_ALG}|ud={version}\\ue000"', '    return f"\\ue000alg={_ALG}\\ue000"', TAG, "the tag does not name the algorithm"),
    mutant("tag: the key of another version is folded again with its tag", TN,
        "    if tag and raw.startswith(tag):\n        # already a check name of this interpreter: the function stays idempotent\n        raw = raw[len(tag) :]", "    if False:\n        # already a check name of this interpreter: the function stays idempotent\n        raw = raw[len(tag) :]", TAG, "the key of another version is not idempotent"),
    # ---- the mutants of fold3 (order 49): U+0345 ----
    mutant("iota: U+0345 is an iota after any letter, not only a Greek one", TN,
        "            if last and _is_greek_letter(last):", "            if True:", DROPS, "a drop-category code point changes the key of a letter"),
    mutant("iota: U+0345 is always removed, also after a Greek letter", TN,
        "            if last and _is_greek_letter(last):", "            if False:", SYMM, "identity_key is not case symmetric for"),
    mutant("iota: a dropped character hides the Greek letter in front of U+0345", TN,
        "        if _kept(ch):\n            last = ch",
        "        last = ch", MOVES, "a dropped character moves the iota"),
    # ---- the mutants of fold4 (fix3, review 3): the readings, the length check, the caseless form; the first one is the mutant of fold2 that fold3 removed ----
    mutant("fold: case folded before the marks are dropped (the fold2 order)", TN,
        '    prefix = _prefix(unicodedata.normalize("NFKD", raw), iota=True)',
        '    prefix = _prefix(unicodedata.normalize("NFKD", raw.casefold()), iota=True)',
        U0345, "U+0345 after a Latin letter changes the key"),
    mutant("readings: reading (a), the lower side with U+0345 dropped, is missing", TN,
        "    (False, False),\n    (True, False),\n    (False, True),\n)", "    (True, False),\n    (False, True),\n)",
        NOTTRANS, "the lower-side reading with U+0345 dropped was removed"),
    mutant("readings: reading (b), the iota reading, is missing", TN,
        "    (False, False),\n    (True, False),\n    (False, True),\n)", "    (False, False),\n    (False, True),\n)",
        NOTTRANS, "the iota reading was dropped"),
    mutant("readings: reading (c), the upper side, is missing", TN,
        "    (False, False),\n    (True, False),\n    (False, True),\n)", "    (False, False),\n    (True, False),\n)",
        NOTTRANS, "the upper-side reading was dropped"),
    mutant("readings: only the first reading is used", TN,
        "    for iota, table_first in _READINGS:", "    for iota, table_first in _READINGS[:1]:",
        FOURCAP, "are not the same person"),
    mutant("readings: a fourth reading (the number of readings is not bounded)", TN,
        "    (False, False),\n    (True, False),\n    (False, True),\n)", "    (False, False),\n    (True, False),\n    (False, True),\n    (True, True),\n)",
        KEYSET, "4 readings for"),
    mutant("readings: reading (c) applies the iota rule", TN,
        "    (False, False),\n    (True, False),\n    (False, True),\n)", "    (False, False),\n    (True, False),\n    (True, True),\n)",
        FOURCAP, "a capital Greek letter + U+0345 is not the Latin capital"),
    mutant("readings: reading (c) has no table of the case-fold image after the case fold", TN,
        "        s = s.translate(_TABLE).casefold().translate(_CF_TABLE)\n", "        s = s.translate(_TABLE).casefold()\n",
        FOURCAP, "the upper-side reading lacks the table of the case-fold image"),
    mutant("deny: could_be_same_person compares one reading (identity_key)", TN,
        "    return not set(_keys(a)).isdisjoint(_keys(b))", "    return identity_key(a) == identity_key(b)",
        GREEKLOOK, "is not the person admin"),
    mutant("allow: a look-alike is judged by one reading", TN,
        "    if could_be_same_person(a, b):\n        return AllowVerdict.LOOKALIKE", "    if identity_key(a) == identity_key(b):\n        return AllowVerdict.LOOKALIKE",
        FOURCAP, "allow_equal does not report"),
    mutant("scan: fold_views gives one view", TN,
        "    return _views(\n        raw, casefold=casefold, collapse_ws=collapse_ws, marks_dropped=True, scripts=scripts\n    )\n", "    return (_fold(raw, casefold=casefold, collapse_ws=collapse_ws),)\n",
        GREEKLOOK, "has no view that reads admin"),
    mutant("scan: squeeze_views gives one view", TN,
        "    for view in _views(raw, casefold=True, collapse_ws=False, marks_dropped=True):", "    for view in (_fold(raw, casefold=True),):",
        GREEKLOOK, "squeeze_views has no view that reads ADMIN"),
    mutant("tag: a reading of identity_keys has no tag", TN,
        "    return tuple(tag + view for view in _views(raw, casefold=True, collapse_ws=True))",
        "    return tuple(view for view in _views(raw, casefold=True, collapse_ws=True))",
        TAGKEYS, "a reading has no tag"),
    mutant("size: the length check before the weight is missing", TN,
        '        if len(text) > defaults.TEXTNORM_MAX_CHARS:\n            raise TextTooLong(\n                f"the text is too long: {len(text)} of {defaults.TEXTNORM_MAX_CHARS} allowed"\n            )\n',
        "", CHEAP, "the weight was computed for a text longer than the cap"),
    mutant("size: a text of exactly the cap in length is refused", TN,
        "        if len(text) > defaults.TEXTNORM_MAX_CHARS:", "        if len(text) >= defaults.TEXTNORM_MAX_CHARS:",
        CAPROW, "a text of exactly the cap is refused"),
    mutant("canon: the old NFKC and one case fold (not Unicode D146)", TN,
        '    folded = unicodedata.normalize("NFKD", unicodedata.normalize("NFKD", s).casefold()).casefold()\n    return " ".join(unicodedata.normalize("NFKD", folded).split())',
        '    folded = unicodedata.normalize("NFKC", s).casefold()\n    return " ".join(folded.split())',
        NAMESSYM, "_canon is not case symmetric"),
    mutant("table: the generator accepts any Unicode version", GEN,
        "    if version != unidata or PINNED_VERSION != unidata:", "    if False:",
        GENVER, "an other Unicode version is not refused by its version", test_file=G),
    mutant("table: the generator accepts any date", GEN,
        "    if (date[1].strip() if date else \"?\") != PINNED_DATE:", "    if False:",
        GENVER, "an other date is accepted", test_file=G),
    # ---- the mutants of fix4 (order 79): the 15.1.0 data pin, the marks, the plain-words messages, the weight pre-check ----
    mutant("table: the palochka override is removed", GEN, '{0x4CF: "l"}', "{}",
        OFFLINE, "differs from the checked-in table", test_file=G),
    mutant("marks: the fold drops spacing marks (Mc)", TN, '"Mn", "Me", "Zl"', '"Mn", "Mc", "Me", "Zl"',
        MCKEPT, "dropped the spacing mark"),
    mutant("marks: squeeze_views keeps non-alphanumeric characters", TN,
        '        s = _NON_ALNUM.sub("", s)\n        if s not in out:', "        if s not in out:",
        NONALNUM, "does not remove U+"),
    mutant("names: the alias fold_key is back", TN,
        "    return tag + _fold(raw, casefold=True, collapse_ws=True)\n",
        "    return tag + _fold(raw, casefold=True, collapse_ws=True)\n\n\nfold_key = identity_key\n",
        EMPTYKEY, "the old alias fold_key is back"),
    mutant("words: the weight message is the old one", TN,
        '"the text is too long once look-alike letters are expanded: "', '"text weight "',
        PLAINMSG, "the weight message is not in plain words"),
    mutant("words: the pin message does not say what to run", TN,
        'f"this Python uses Unicode {unicodedata.unidata_version}; {fix} for pilot or prod"',
        'f"Unicode data {unicodedata.unidata_version} is not the pinned {expected}"',
        REQUIRE, "does not say plainly what to run"),
    mutant("size: the weight check is missing (the key is built first)", TN,
        "        if weight > defaults.TEXTNORM_MAX_CHARS:\n            raise TextTooLong(", "        if False:\n            raise TextTooLong(",
        NOWORK, "fold work was done for a text that must be refused"),
    # ---- the mutants of fix5 (the marks-dropped views, the letter and digit name rules) ----
    mutant("marks: the marks-dropped reading is not built", TN,
        "    if marks_dropped:\n        texts.append(_without_spacing_marks(raw))", "    if False:\n        texts.append(_without_spacing_marks(raw))",
        MCSQUEEZE, "misses a secret hidden with U+"),
    mutant("marks: the marks are dropped after NFKD, not from the raw text", TN,
        "        texts.append(_without_spacing_marks(raw))", "        texts.append(raw)",
        MCSQUEEZE, "misses a secret hidden with U+"),
    mutant("marks: fold_views has no marks-dropped views", TN,
        "collapse_ws=collapse_ws, marks_dropped=True, scripts=scripts\n    )",
        "collapse_ws=collapse_ws, marks_dropped=False, scripts=scripts\n    )",
        NOASCII, "the scan misses the value with the mark inserted"),
    mutant("marks: squeeze_views has no marks-dropped views", TN,
        "    for view in _views(raw, casefold=True, collapse_ws=False, marks_dropped=True):",
        "    for view in _views(raw, casefold=True, collapse_ws=False, marks_dropped=False):",
        MCSQUEEZE, "misses a secret hidden with U+"),
    mutant("marks: a spacing combining mark (Mc) is not dropped", TN,
        '    {"Mc", "Lm", "Sk"}\n)  # kept by', '    {"Lm", "Sk"}\n)  # kept by',
        MCSQUEEZE, "misses a secret hidden with U+"),
    mutant("marks: a modifier letter (Lm) is not dropped", TN,
        '    {"Mc", "Lm", "Sk"}\n)  # kept by', '    {"Mc", "Sk"}\n)  # kept by',
        MCSQUEEZE, "misses a secret hidden with U+"),
    mutant("marks: a view is repeated", TN,
        "        if view not in out:\n            out.append(view)", "        out.append(view)",
        SIXVIEWS, "repeated or there are more than the limit"),
    mutant("names: the negative circled and squared letters are not read", GEN,
        '        (r"(?:CROSSED )?NEGATIVE (?:CIRCLED|SQUARED) LATIN CAPITAL LETTER ([A-Z])", "upper"),\n', "",
        RULES, "negative circled letters are not read", test_file=G),
    mutant("names: the regional indicator letters are not read", GEN,
        '        (r"REGIONAL INDICATOR SYMBOL LETTER ([A-Z])", "upper"),\n', "",
        RULES, "regional indicator letters are not read", test_file=G),
    mutant("names: the squared small letter is not read", GEN,
        '        (r"SQUARED LATIN SMALL LETTER ([A-Z])", "lower"),\n', "",
        RULES, "squared small letter d is not read", test_file=G),
    mutant("names: the circled digits are not read", GEN,
        "            return _DIGIT_WORDS[m[1]]", "            return None",
        RULES, "circled digits are not read", test_file=G),
    mutant("names: a letter with a stroke or a hook is not read", GEN,
        '        (r"LATIN (?:CAPITAL|SMALL) LETTER ([A-Z]) WITH .+", "case"),\n', "",
        RULES, "letter with a stroke is not read", test_file=G),
    mutant("names: a capital does not follow its small letter", GEN,
        "        value = _follow_case_partner(ch, value, listed)\n", "",
        RULES, "capital follows the other-case form", test_file=G),
    mutant("pin: the pin constant differs from the data of the table", "src/hadavin_sdk/defaults.py",
        'TEXTNORM_PINNED_UNIDATA = "15.1.0"', 'TEXTNORM_PINNED_UNIDATA = "15.0.0"',
        PINTABLE, "the table data is not the Unicode version of the pin", test_file=G),
    # ---- the mutants of fix6 (the script views, the minimum view length, the supplement merge) ----
    mutant("script: fold_views has no script views", TN,
        "collapse_ws=collapse_ws, marks_dropped=True, scripts=scripts\n    )",
        "collapse_ws=collapse_ws, marks_dropped=True\n    )",
        SCRIPTINS, "the scan misses"),
    mutant("script: the script view keeps the ASCII letters", TN,
        "        if ch.isascii() or not ch.isalpha():\n            continue\n", "        if not ch.isalpha():\n            continue\n",
        SCRIPTVIEW, "the script view keeps an ASCII letter"),
    mutant("scan: the minimum view length is not applied", TN,
        "        if len(view) < minimums[kind]:\n            continue\n", "",
        MINVIEW, "scan_needles accepted"),
    mutant("scan: the minimums are bound when the module is read", TN,
        "    spelling_min, squeeze_min, script_min, ideograph_min = _validated_minimums()\n",
        "    spelling_min, squeeze_min, script_min, ideograph_min = (2, 4, 4, 2)\n",
        MINVIEW, "wrong views at the minimums"),
    mutant("names: the supplement is not merged before the name rules", GEN,
        "    out = {**sup, **out}\n", "",
        SUPPLEMENT, "a name rule overrode a supplement entry", test_file=G),
    # ---- the mutants of fix7 (the script view per script, the minimum per kind of view, the checks of the minimums) ----
    mutant("script: the script view keeps the letters of every script", TN,
        "            group[ch] = _script_of(ch) in scripts\n", "            group[ch] = True\n",
        FOREIGN, "the scan misses the value with"),
    mutant("script: the script view keeps the letters of every script (the whole range)", TN,
        "            group[ch] = _script_of(ch) in scripts\n", "            group[ch] = True\n",
        CLASSSWEEP, "inserted into a Chinese value hides it"),
    mutant("script: every letter is a script of its own", TN,
        "    return _SCRIPT_GROUPS.get(head, head)\n", "    return ch\n",
        SAMESCRIPT, "the documented limit is out of date"),
    mutant("script: OLD TURKIC and OLD ITALIC are one script", TN,
        '_TWO_WORD_SCRIPTS = frozenset({"OLD", "NEW",', '_TWO_WORD_SCRIPTS = frozenset({"NEW",',
        GROUPS, "OLD TURKIC and OLD ITALIC are one group"),
    mutant("script: the ideographic closing mark is Han", TN,
        '{"CJK": "HAN", "HIRAGANA"', '{"CJK": "HAN", "IDEOGRAPHIC": "HAN", "HIRAGANA"',
        GROUPS, "the ideographic closing mark is read as Han"),
    mutant("script: Katakana is not kana", TN,
        '"KATAKANA": "KANA", ', "",
        GROUPS, "Hiragana and Katakana are not one group"),
    mutant("script: the old variant kana are not kana", TN,
        ', "HENTAIGANA": "KANA"}', "}",
        GROUPS, "the old variant kana are not kana"),
    mutant("script: the Han ideographs are not named HAN", TN,
        '{"CJK": "HAN", "HIRAGANA"', '{"HIRAGANA"',
        GROUPS, "the CJK ideographs are not one group"),
    mutant("script: a letter with no name is Han", TN,
        '        return "UNNAMED"\n', '        return "HAN"\n',
        GROUPS, "a letter with no name is not UNNAMED"),
    mutant("script: a symbol with a script word in its name is kept", TN,
        "        if ch.isascii() or not ch.isalpha():\n            continue\n", "        if ch.isascii():\n            continue\n",
        SCRIPTVIEW, "the script view keeps the non-letter"),
    mutant("script: the scripts of a value include its modifier letters", TN,
        "            raw, casefold=True, collapse_ws=False, marks_dropped=True, marks_only=True\n",
        "            raw, casefold=True, collapse_ws=False, marks_dropped=True\n",
        VALSCRIPTS, "a modifier letter made a script of the value"),
    mutant("script: the scripts of a value include its ASCII letters", TN,
        "        out.update(_script_of(ch) for ch in set(view) if not ch.isascii() and ch.isalpha())",
        "        out.update(_script_of(ch) for ch in set(view) if ch.isalpha())",
        GROUPS, "a Latin value has a script"),
    mutant("script: the scripts given to fold_views are not checked", TN,
        "    _checked(raw)\n    _checked_scripts(scripts)\n", "    _checked(raw)\n",
        SCRIPTARG, "fold_views accepted scripts"),
    mutant("script: the value has no scripts in scan_needles", TN,
        "    scripts = _value_scripts(raw)\n    squeezed", "    scripts = frozenset()\n    squeezed",
        SCRIPT4, "a four-letter script view is not a needle"),
    mutant("script: an empty script view is kept", TN,
        '                if only and ("script", only) not in pairs:', '                if ("script", only) not in pairs:',
        SCRIPTVIEW, "an empty script view was kept"),
    mutant("script: the docstring says again that marks stay in a script view", TN,
        "no mark is ever in a script view;", "a mark may stay in a script view;",
        HINDI, "does not say that no mark reaches a script view"),
    mutant("minimum: the minimums are not checked when the module is read", TN,
        "_validated_minimums()  # fail closed at import\n", "",
        MINCONST, "the module was imported with"),
    mutant("minimum: scan_needles does not check the minimums", TN,
        "    spelling_min, squeeze_min, script_min, ideograph_min = _validated_minimums()\n",
        "    spelling_min, squeeze_min, script_min, ideograph_min = (\n        defaults.TEXTNORM_MIN_SPELLING_CHARS,\n        defaults.TEXTNORM_MIN_SQUEEZE_CHARS,\n        defaults.TEXTNORM_MIN_SCRIPT_CHARS,\n        defaults.TEXTNORM_MIN_IDEOGRAPH_CHARS,\n    )\n",
        MINCONST, "scan_needles accepted"),
    mutant("minimum: a bool is a minimum", TN,
        "        if type(value) is not int or value < 1:", "        if not isinstance(value, int) or value < 1:",
        MINCONST, "_validated_minimums accepted"),
    mutant("minimum: zero is a minimum", TN,
        "        if type(value) is not int or value < 1:", "        if type(value) is not int or value < 0:",
        MINCONST, "accepted TEXTNORM_MIN_SPELLING_CHARS = 0"),
    mutant("minimum: the message does not name the constant", TN,
        'f"defaults.{name} must be a whole number', 'f"a minimum must be a whole number',
        MINCONST, "the message does not name"),
    mutant("minimum: a squeeze view needs only the spelling minimum", TN,
        '        "squeeze": squeeze_min,\n', '        "squeeze": spelling_min,\n',
        SQUEEZE4, "a squeeze view of fewer than four letters is a needle"),
    mutant("minimum: a script view always needs only the ideograph minimum", TN,
        '        "script": ideograph_min if ideographs_only else script_min,\n', '        "script": ideograph_min,\n',
        SCRIPT4, "a script view of fewer than four letters is a needle"),
    mutant("minimum: a value of Han ideographs needs the script minimum", TN,
        "    ideographs_only = scripts == frozenset({\"HAN\"}) and not any(squeezed)\n", "    ideographs_only = False\n",
        SCRIPT4, "a two-ideograph name is not a needle"),
    mutant("minimum: a mixed value with ASCII letters gets the ideograph minimum", TN,
        "    ideographs_only = scripts == frozenset({\"HAN\"}) and not any(squeezed)\n", "    ideographs_only = scripts == frozenset({\"HAN\"})\n",
        SCRIPT4, "the script part of a mixed value is a needle at two letters"),
    mutant("minimum: a value of Han and kana gets the ideograph minimum", TN,
        "    ideographs_only = scripts == frozenset({\"HAN\"}) and not any(squeezed)\n", "    ideographs_only = \"HAN\" in scripts and not any(squeezed)\n",
        SCRIPT4, "the ideograph minimum was used for Han plus kana"),
    mutant("scan: a value found only by a spelling view is a needle", TN,
        "    if not proof:\n", "    if not needles:\n",
        SEPONLY, "which a space hides"),
    mutant("scan: the proof flag is set by a spelling view", TN,
        '        proof = proof or kind != "spelling"\n', "        proof = True\n",
        SEPONLY, "which a space hides"),
    mutant("scan: the squeeze views are not needles", TN,
        '        *(("squeeze", view) for view in squeezed),\n', "",
        MINVIEW, "wrong views at the minimums"),
    mutant("scan: a script view is made for the text that keeps the marks", TN,
        "            if scripts and marks:\n", "            if scripts:\n",
        VALSCRIPTS, "a script view keeps a modifier letter"),
    mutant("scan: loose is not passed to the squeeze views", TN,
        "    squeezed = squeeze_views(raw, loose=loose)\n", "    squeezed = squeeze_views(raw)\n",
        LOOSEHALF, "loose=True did not loosen the squeeze half"),
    mutant("words: the docstring does not say what loose loosens", TN,
        "``loose=True`` loosens only the squeeze half", "``loose=True`` loosens the views",
        LOOSEHALF, "the docstring does not say what loose loosens"),
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

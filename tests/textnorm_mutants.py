"""The mutants of the text fold (``guard/textnorm.py``), the look-alike table (``guard/_confusables.py``) and its generator.

Each mutant changes ONE thing in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in ``only_test`` must
fail, it must be the test pinned in ``pinned``, and the first failing line must hold ``expect``: a fragment of the assertion MESSAGE the test
gives for that one guard (never a fragment of the test's own name). Every mutant names both the file of its killer (``test_file``) and the
killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the test placement table. Not collected by
pytest. Run from the repo root:

    uv run python tests/textnorm_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/textnorm_mutants.py squeeze    # only mutants whose name contains the text

180 mutants, in the order of the list: 28 re-pointed mutants of the earlier text-fold list (the killers moved with their tests), 12 new ones of the first package, 9 of fold2, 3 of fold3 (U+0345), 16 of fold4 (the spelling variants, the length check, the caseless form; the first of them is the fold2 mutant "no case fold before the marks are dropped" that fold3 removed and that is restored here), 9 of fix4 (the 15.1.0 data pin, the marks, the plain-words messages, the weight pre-check), 27 of P1b (the scan keys, the scan, the callers), 14 of fix5 (the marks-dropped views, the letter and digit name rules, the pin constant), 5 of fix6 (the script views, the minimum view length, the supplement merge), 30 of fix7 (the script view per script, the minimum per kind of view, the checks of the minimums, the proof rule, what loose loosens) and 27 of the P1b fix batch (the composed view of the redactor, the Mc and Sk keys, the digit and key minimums, the proof rule of EmptyView, the cache, the one required value of scan_views, the floor, the one-inserted-letter match and its limits). Two mutants of fix7 are gone: "a bool is a minimum" (the floor of 2 refuses a bool anyway, so it cannot change a result: equivalent) and "scan_views: the scripts are not checked" (scan_views no longer takes scripts). The dead branch of the old script view is an equivalent mutant (it could not change a result), so it has no entry. Tests with no
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
SB = "tests/test_textnorm_siblings.py"  # the Mc, Lm and Sk code points on every scan path (P1b)
FB = "tests/test_textnorm_fixbatch.py"  # the killers of the fix batch: the composed view, the Mc and Sk keys, the minimums, the cache, the choke point, the insertion match
O = "tests/test_textnorm_order137.py"  # the killers of order 137: the strict scan_views, the registration check, the cache scope, the cap, the Japanese minimum, the Russian word
D = "tests/test_textnorm_differential.py"  # the differential rows and the golden test: they have no mutant, they run in the baseline
TESTS = [T, G, SC, SB, FB, O, D]  # killer files first; golden, differential last
S = "src/hadavin_sdk/guard/"
TN, CF, GEN = S + "textnorm.py", S + "_confusables.py", "tools/gen_confusables.py"
RM, INJ = S + "runmap.py", S + "injection.py"
DEF = "src/hadavin_sdk/defaults.py"


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
MCKEPT = "test_identity_key_keeps_a_spacing_mark_while_the_deny_check_and_the_scan_views_drop_it"
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
KEEPSAME = "test_a_spacing_mark_inserted_into_a_name_is_still_the_same_person"
GATE = "test_the_deny_check_skips_the_marks_dropped_reading_only_when_it_changes_nothing"
UNNAMED = "test_a_character_this_python_cannot_name_makes_the_deny_check_fail_closed"
MIXED2 = "test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a_mark_of_the_words_own_script_does_not_flag"
PINMSG = "test_the_pin_message_and_the_pin_constants_come_from_defaults"
DOCS = "test_the_docstrings_state_the_new_behaviour_and_the_corrected_wording"
U0345 = "test_u0345_is_an_iota_after_a_greek_letter_and_is_removed_everywhere_else"
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
L2I = "test_l_to_i_rows"
LMRAW = "test_r12_lm_inserting_any_modifier_letter_still_finds_the_value"
SCANVIEWS = "test_scan_views_has_the_fold_the_squeeze_and_the_scan_keys_and_no_empty_view"
HOLDSBOTH = "test_scan_holds_reads_both_fold_views_and_squeeze_views_on_both_sides"
HOLDSEMPTY = "test_scan_holds_refuses_a_value_with_an_empty_view_and_a_text_may_have_one"
HOLDSSCRIPTS = "test_scan_holds_reads_the_text_with_the_scripts_of_the_value_so_a_foreign_letter_does_not_hide_it"
HOLDSSHORT = "test_scan_holds_refuses_a_value_too_short_to_scan_instead_of_answering_false"
HOLDSKEYS = "test_scan_holds_reads_the_scan_keys_of_the_value"
VIEWSCRIPTS = "test_scan_views_takes_the_scripts_of_the_value_and_has_a_script_view_only_with_them"
INJVIEWS = "test_the_injection_detector_reads_the_scan_views_so_a_cyrillic_o_or_a_hidden_mark_does_not_hide_a_phrase"
CANONVIEW = "test_runmap_canonical_and_its_per_character_view_are_the_same_text_on_the_whole_corpus"
SIBLINGS = "test_scan_holds_finds_the_password_for_every_mc_lm_and_sk_code_point"
LMFOLD = "test_r12_lm_fold_a_modifier_letter_that_nfkd_turns_into_a_letter_still_matches"
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
        "        if latin and other:\n            return True",
        "        if False:\n            return True", MIXED, "is not flagged"),
    mutant("allow: equality is normalised", TN,
        "    if a == b:\n        return AllowVerdict.EQUAL",
        "    if _canon(a) == _canon(b):\n        return AllowVerdict.EQUAL", ALLOW, "gave EQUAL, wanted VARIANT"),
    mutant("allow: a mismatch is always a look-alike", TN,
        "    return AllowVerdict.DIFFERENT", "    return AllowVerdict.LOOKALIKE",
        ALLOW, "an ordinary mismatch is not DIFFERENT"),
    mutant("mixed: invisible characters not removed first", TN,
        "            ch not in _UNIT_SYMBOLS\n            and ch not in FILLERS\n            and unicodedata.category(ch) not in _MIXED_REMOVED\n",
        "            ch not in _UNIT_SYMBOLS\n", INVISIBLE, "splits a mixed word"),
    mutant("mixed: the micro sign is flagged", TN,
        "            ch not in _UNIT_SYMBOLS\n", "            True\n", MICRO, "a micro or ohm sign is flagged"),
    mutant("mixed: Cherokee exempt next to Latin", TN,
        '{"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo"}', '{"Han", "Hiragana", "Katakana", "Hangul", "Bopomofo", "Cherokee"}',
        INVISIBLE, "Cherokee next to Latin is not flagged"),
    mutant("table: Cherokee A missing", CF, '    0x13AA: "A",\n', "", TABLE,
        "named look-alike U+13AA is not folded", test_file=G),
    mutant("table: small capital rule missing", GEN, "            out.setdefault(cp, value)", "            pass",
        GENERATOR, "the small capital rule is missing", test_file=G),
    mutant("table: ASCII sources accepted", GEN, "        if src < 0x80 or not re.fullmatch", "        if not re.fullmatch",
        GENERATOR, "an ASCII source was accepted", test_file=G),
    mutant("table: capital I prototype stays l", GEN, '            dst = "I"', '            dst = "l"',
        GENERATOR, "capital I prototype read as l", test_file=G),
    mutant("table: the generator accepts any file", GEN, "    if sha != pinned_sha256:", "    if False:",
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
    # ---- the mutants of fold2: the order of the fold, the Unicode pin and its tag ----
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
    # ---- the mutants of fold3: U+0345 ----
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
        "    return tuple(\n        tag + view\n        for view in _views(raw, casefold=True, collapse_ws=True, marks_dropped=marks_dropped)\n    )\n",
        "    return tuple(\n        view\n        for view in _views(raw, casefold=True, collapse_ws=True, marks_dropped=marks_dropped)\n    )\n",
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
        "    if version != unidata or pinned_version != unidata:", "    if False:",
        GENVER, "an other Unicode version is not refused by its version", test_file=G),
    mutant("table: the generator accepts any date", GEN,
        "    if (date[1].strip() if date else \"?\") != pinned_date:", "    if False:",
        GENVER, "an other date is accepted", test_file=G),
    # ---- the mutants of fix4: the 15.1.0 data pin, the marks, the plain-words messages, the weight pre-check ----
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
    # ---- the mutants of P1b (scan_keyset, gap 4, the modifier letters); each names its killer in tests/test_textnorm_scan.py ----
    mutant("scan: reading B omitted", TN, "        for step in (_pass_a, _pass_b)", "        for step in (_pass_a,)",
        ETA, "reading B is missing", test_file=SC),
    mutant("scan: the not-converged raise returns the last output", TN,
        '    raise FoldNotConverged(f"a spelling variant was still changing after {passes} passes")',
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
        "    _checked(raw)\n    return _scan_keys(raw)", "    return _scan_keys(raw)", SK2, "accepted a text over the size rule", test_file=SC),
    mutant("gap 4: the dash, slash and quote map removed", TN, "    return s.translate(_DIGITS).translate(_PUNCT)",
        "    return s.translate(_DIGITS)", GAP4, "gap 4 map", test_file=SC),
    mutant("fold: U+FFFD kept in step S2", TN, "    if ch in FILLERS or ch == _REPLACEMENT:", "    if ch in FILLERS:",
        SK6, "U+FFFD is kept by the fold", test_file=SC),
    mutant("scan: class map l to i removed", TN, '_CLASS_MAP = str.maketrans("zl", "3i")', '_CLASS_MAP = str.maketrans("z", "3")',
        L2I, "row 1: the class map l to i is missing", test_file=SC),
    mutant("scan: the drop keeps non-whitespace punctuation", TN, 'ch.isalnum() and unicodedata.category(ch) != "Lm"',
        'not ch.isspace() and unicodedata.category(ch) != "Lm"', L2I, "row 1: the key holds a character", test_file=SC),
    mutant("scan: the raw removal of modifier letters skipped", TN,
        '    no_lm = "".join(ch for ch in raw if unicodedata.category(ch) != "Lm")', "    no_lm = raw", LMRAW, "hides the value", test_file=SC),
    mutant("scan: the modifier-letter test removed from the key drop", TN, ' and unicodedata.category(ch) != "Lm"', "",
        LMFOLD, "survives in the key", test_file=SC),
    mutant("scan_holds: the squeeze view of the value is not read", TN,
        "    needles = _needles_or_refuse(value, scripts)\n", "    needles = [(\"spelling\", v) for v in _views(value, casefold=True, collapse_ws=True)]\n",
        HOLDSBOTH, "the value side misses the squeeze view", test_file=SC),
    mutant("scan_holds: the squeeze view of the text is not read", TN,
        "    views = [view for view in _all_views(text, scripts, bundle) if view]\n", "    views = [view for view in _views(text, casefold=True, collapse_ws=True) if view]\n",
        HOLDSBOTH, "the text side misses the squeeze view", test_file=SC),
    mutant("scan_holds: an empty view of the value is accepted", TN,
        "        if not _has_proof_character(value, scripts):\n", "        if False:\n",
        HOLDSEMPTY, "scan_holds accepted the value", test_file=SC),
    mutant("scan_views: only fold_views are read (no squeeze views, no scan keys)", TN,
        "    for view in (*(v for _kind, v in _pairs_from(readings, scripts)), *squeezed, *keys):\n",
        "    for view in (*(v for _kind, v in _pairs_from(readings, scripts)),):\n",
        SCANVIEWS, "scan_views leaves out the view", test_file=SC),
    mutant("injection: the scan views are not read", "src/hadavin_sdk/guard/injection.py",
        "        for view in (text, *textnorm.scan_views_no_value(text)):", "        for view in (text,):",
        INJVIEWS, "the injection detector misses", test_file=SB),
    mutant("runmap: canonical normalises the whole text again", "src/hadavin_sdk/guard/runmap.py",
        "    return _canonical_view(text)[0]\n",
        '    return "".join(c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf")\n',
        CANONVIEW, "canonical and the view differ on", test_file=SB),
    # ---- P1b merge 7: the P1a fix7 API (scripts per value, ViewTooShort) ----
    mutant("scan_holds: the text is read without the scripts of the value", TN,
        "    views = [view for view in _all_views(text, scripts, bundle) if view]\n", "    views = [view for view in _all_views(text, frozenset(), bundle) if view]\n",
        HOLDSSCRIPTS, "scan_holds misses the value with", test_file=SC),
    mutant("scan_holds: a value too short to scan is answered", TN,
        "    needles = _needles_or_refuse(value, scripts)\n", "    needles = [(\"spelling\", v) for v in _all_views(value)]\n",
        HOLDSSHORT, "answered for the value", test_file=SC),
    mutant("scan_holds: the scan keys of the value are not needles", TN,
        "    needles = _needles_or_refuse(value, scripts)\n", "    needles = _needle_pairs(value)\n",
        HOLDSKEYS, "the value side misses the scan key", test_file=SC),
    mutant("scan_views: the scripts are not read", TN,
        "_all_views(raw, _value_scripts(value)) if view", "_all_views(raw) if view",
        VIEWSCRIPTS, "gives no script view for the scripts", test_file=SC),
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
        "        scripts=scripts,\n    ):\n        if view not in out:\n            out.append(view)", "        scripts=scripts,\n    ):\n        out.append(view)",
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
        "        if len(view) < minimum:\n            continue\n", "",
        MINVIEW, "scan_needles accepted"),
    mutant("scan: the minimums are bound when the module is read", TN,
        "    spelling_min, squeeze_min, script_min, ideograph_min, digit_min = _validated_minimums()\n",
        "    spelling_min, squeeze_min, script_min, ideograph_min, digit_min = (2, 4, 4, 2, 6)\n",
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
        "    _checked(raw)\n    _checked_scripts(scripts)\n    return _views(\n", "    _checked(raw)\n    return _views(\n",
        SCRIPTARG, "fold_views accepted scripts"),
    mutant("script: the value has no scripts in scan_needles", TN,
        "    scripts = _value_scripts(raw)\n    squeezed", "    scripts = frozenset()\n    squeezed",
        SCRIPT4, "a four-letter script view is not a needle"),
    mutant("script: an empty script view is kept", TN,
        '            if only and ("script", only) not in pairs:', '            if ("script", only) not in pairs:',
        SCRIPTVIEW, "an empty script view was kept"),
    mutant("script: the docstring says again that marks stay in a script view", TN,
        "no mark is ever in a script view;", "a mark may stay in a script view;",
        HINDI, "does not say that no mark reaches a script view"),
    mutant("minimum: the minimums are not checked when the module is read", TN,
        "_validated_minimums()  # fail closed at import\n", "",
        MINCONST, "the module was imported with"),
    mutant("minimum: scan_needles does not check the minimums", TN,
        "    spelling_min, squeeze_min, script_min, ideograph_min, digit_min = _validated_minimums()\n",
        "    spelling_min, squeeze_min, script_min, ideograph_min, digit_min = (\n        defaults.TEXTNORM_MIN_SPELLING_CHARS,\n        defaults.TEXTNORM_MIN_SQUEEZE_CHARS,\n        defaults.TEXTNORM_MIN_SCRIPT_CHARS,\n        defaults.TEXTNORM_MIN_IDEOGRAPH_CHARS,\n        defaults.TEXTNORM_MIN_DIGIT_CHARS,\n    )\n",
        MINCONST, "scan_needles accepted"),
    mutant("minimum: zero is a minimum", TN,
        "_MINIMUM_FLOOR = 2  #", "_MINIMUM_FLOOR = 0  #",
        MINCONST, "accepted TEXTNORM_MIN_SPELLING_CHARS = 0"),
    mutant("minimum: the message does not name the constant", TN,
        'f"defaults.{name} must be a whole number', 'f"a minimum must be a whole number',
        MINCONST, "the message does not name"),
    mutant("minimum: a squeeze view needs only the spelling minimum", TN,
        "            minimum = digit_min if view.isdigit() else squeeze_min\n", "            minimum = digit_min if view.isdigit() else spelling_min\n",
        SQUEEZE4, "a squeeze view of fewer than four letters is a needle"),
    mutant("minimum: a script view always needs only the ideograph minimum", TN,
        "            minimum = ideograph_min if ideographs_only else script_min\n", "            minimum = ideograph_min\n",
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
        "        if scripts and marks:\n", "        if scripts:\n",
        VALSCRIPTS, "a script view keeps a modifier letter"),
    mutant("scan: loose is not passed to the squeeze views", TN,
        "    squeezed = squeeze_views(raw, loose=loose)\n", "    squeezed = squeeze_views(raw)\n",
        LOOSEHALF, "loose=True did not loosen the squeeze half"),
    mutant("words: the docstring does not say what loose loosens", TN,
        "``loose=True`` loosens only the squeeze half", "``loose=True`` loosens the views",
        LOOSEHALF, "the docstring does not say what loose loosens"),
    # ---- the mutants of fix8 (ORDER 177/179: the marks-dropped check name, the mixed-script rules, the unnamed characters, the pin, two wordings) ----
    mutant("deny: the check names have no marks-dropped reading", TN,
        '    marks_dropped = _holds_spacing(raw) or _holds_spacing(unicodedata.normalize("NFKD", raw))\n',
        "    marks_dropped = False\n", KEEPSAME, "does not see through"),
    mutant("deny: the marks-dropped gate is turned round", TN,
        '    marks_dropped = _holds_spacing(raw) or _holds_spacing(unicodedata.normalize("NFKD", raw))\n',
        '    marks_dropped = not (_holds_spacing(raw) or _holds_spacing(unicodedata.normalize("NFKD", raw)))\n',
        KEEPSAME, "does not see through"),
    mutant("mixed: rule (b) is never true", TN,
        '    return any(group != "LATIN" and group not in own for group in map(_script_of, marks))\n',
        "    return False\n", MIXED2, "is not flagged"),
    mutant("mixed: a modifier symbol is not removed before the split", TN,
        '_MIXED_REMOVED = _DROP_CATEGORIES | {"Sk"}', "_MIXED_REMOVED = _DROP_CATEGORIES",
        MIXED2, "is not flagged"),
    mutant("mixed: a mark of the word's own script flags", TN,
        '    return any(group != "LATIN" and group not in own for group in map(_script_of, marks))\n',
        '    return any(group != "LATIN" for group in map(_script_of, marks))\n',
        MIXED2, "is flagged"),
    mutant("mixed: a spacing mark splits the word", TN,
        '        if ch.isalnum() or ch == "_" or unicodedata.category(ch) == "Mc":\n',
        '        if ch.isalnum() or ch == "_":\n', MIXED2, "is not flagged"),
    mutant("pin: the Python version of the message is a literal", TN,
        "run Python {defaults.TEXTNORM_PINNED_PYTHON} (Unicode", "run Python 3.13 (Unicode",
        PINMSG, "does not follow the two constants"),
    mutant("deny: an unnamed character does not fail closed", TN,
        "    if _holds_unnamed(_untagged(a)) or _holds_unnamed(_untagged(b)):\n", "    if False:\n",
        UNNAMED, "the DENY check misses"),
    mutant("words: the squeeze docstring calls itself a check name for a scan", TN,
        '"""ONE reading, not a scan: a scan uses', '"""Check name for a scan: a scan uses',
        DOCS, "still calls itself"),
    mutant("words: the names_equal docstring says NFKC", TN,
        "caseless equality (NFKD, case fold, NFKD, case fold), whitespace insensitive. NOT an ALLOW",
        "NFKC caseless equality (NFKD, case fold, NFKD, case fold), whitespace insensitive. NOT an ALLOW",
        DOCS, "says NFKC again"),
    mutant("runmap: the composed view is not listed", RM,
        "        composed(text),\n        composed(unescaped),\n        composed(undone),\n", "",
        "test_redact_text_masks_a_decomposed_copy_of_a_known_name", "a decomposed copy of a known name is not masked", test_file=FB),
    mutant("runmap: the composed view keeps the invisible characters", RM,
        '    kept = "".join(c for c in text if unicodedata.category(c) != "Cf")\n', "    kept = text\n",
        "test_redact_text_masks_a_decomposed_secret_after_an_invisible_character", "keeps the letter and its accent apart", test_file=FB),
    mutant("runmap: the composed view is replaced by the canonical one", RM,
        "    return unicodedata.normalize(\"NFKC\", kept)\n", "    return kept\n",
        "test_the_composed_view_is_a_view_and_canonical_stays_per_character", "composed does not join the letter and its mark", test_file=FB),
    mutant("keys: only the modifier letters are dropped", TN,
        '    no_marks = "".join(ch for ch in no_lm if unicodedata.category(ch) not in ("Mc", "Sk"))\n', "    no_marks = no_lm\n",
        "test_every_mc_and_sk_code_point_hides_nothing_from_the_scan_keys", "hides the word from every scan key", test_file=FB),
    mutant("keys: only the marks-dropped reading", TN,
        "        for variant in dict.fromkeys((no_lm, no_marks))\n", "        for variant in (no_marks,)\n",
        "test_a_spacing_mark_written_instead_of_a_letter_is_still_read_by_the_scan_keys", "is not read", test_file=FB),
    mutant("digits: a digit view needs only the squeeze minimum", TN,
        "            minimum = digit_min if view.isdigit() else squeeze_min\n", "            minimum = squeeze_min\n",
        "test_a_digit_string_needs_the_digit_minimum_and_a_letter_string_the_squeeze_minimum", "a digit string under the digit minimum is scanned", test_file=FB),
    mutant("scan: a scan key needs no minimum", TN,
        "        if key not in known and len(key) >= (digit_min if key.isdigit() else squeeze_min):\n", "        if key not in known:\n",
        "test_a_scan_key_shorter_than_its_minimum_is_not_a_needle", "of digits is a needle", test_file=FB),
    mutant("scan: a value with no squeeze view is EmptyView", TN,
        "    views = [view for view in _all_views(text, scripts, bundle) if view]\n",
        "    if not any(_squeezed(value)):\n        raise EmptyView(\"no squeeze view\")\n    views = [view for view in _all_views(text, scripts, bundle) if view]\n",
        "test_a_script_value_is_scanned_and_found_with_a_separator_inserted", "is not found (or is refused)", test_file=FB),
    mutant("scan: EmptyView is never raised", TN,
        "    return any(_squeezed(value)) or any(\n", "    return True or any(\n",
        "test_a_value_with_nothing_to_rely_on_is_still_empty_view", "does not refuse the empty value", test_file=FB),
    mutant("scan: EmptyView for every short value", TN,
        "        if not _has_proof_character(value, scripts):\n", "        if True:\n",
        "test_a_one_ideograph_value_is_too_short_not_empty", "one ideograph is not ViewTooShort", test_file=FB),
    mutant("cache: the scope never uses its cache", TN,
        "        hit = cache.get(key)\n", "        hit = None\n",
        "test_scanning_one_text_for_many_values_builds_the_text_views_once", "the text was read", test_file=FB),
    mutant("scan_views: the value has a default", TN,
        "def scan_views(raw: str, value: str) -> tuple[str, ...]:", "def scan_views(raw: str, value: str | None = None) -> tuple[str, ...]:",
        "test_scan_views_has_no_default_for_the_value", "scan_views has a default for the value", test_file=FB),
    mutant("fold_views: the scripts have a default", TN,
        "    *,\n    scripts: frozenset[str],\n", "    *,\n    scripts: frozenset[str] = frozenset(),\n",
        "test_fold_views_has_no_default_for_the_scripts", "fold_views has a default for the scripts", test_file=FB),
    mutant("scan_views: the scripts of the value are not used", TN,
        "_all_views(raw, _value_scripts(value)) if view)\n", "_all_views(raw, frozenset()) if view)\n",
        "test_a_caller_that_names_only_the_value_cannot_miss_an_inserted_foreign_letter", "gives no script view for the value", test_file=FB),
    mutant("injection: the call names no value", INJ,
        "textnorm.scan_views_no_value(text)", "textnorm.scan_views(text)",
        "test_no_caller_in_the_package_omits_the_value_or_the_scripts", "names no value", test_file=FB),
    mutant("minimum: the floor is one", TN,
        "_MINIMUM_FLOOR = 2  #", "_MINIMUM_FLOOR = 1  #",
        "test_a_minimum_below_the_floor_or_not_a_plain_int_is_refused", "is accepted by scan_needles", test_file=FB),
    mutant("passes: the number of passes is not checked", TN,
        '    return _whole_number("TEXTNORM_MAX_PASSES", 1)\n', '    return defaults.TEXTNORM_MAX_PASSES\n',
        "test_the_number_of_passes_must_be_a_plain_int_of_at_least_one", "is accepted", test_file=FB),
    mutant("passes: a bool is a number of passes", TN,
        "    if type(value) is not int or value < floor:\n", "    if not isinstance(value, int) or value < floor:\n",
        "test_the_number_of_passes_must_be_a_plain_int_of_at_least_one", "is accepted", test_file=FB),
    mutant("insertion: the match is never made", TN,
        "    return any(\n        _holds_with_one_insertion(view, needle) for view in script_views for needle in inserts\n    )\n", "    return False\n",
        "test_one_inserted_letter_of_the_same_script_is_found_at_every_inner_position", "is not found", test_file=FB),
    mutant("insertion: the first half is not searched", TN,
        "    start = view.find(first)\n", "    start = -1\n",
        "test_the_matcher_agrees_with_the_brute_force_definition_on_every_small_string", "the matcher and the definition differ", test_file=FB),
    mutant("insertion: the second half is not searched", TN,
        "    start = view.find(second)\n", "    start = -1\n",
        "test_one_inserted_letter_of_the_same_script_is_found_at_every_inner_position", "is not found", test_file=FB),
    mutant("insertion: a changed letter is a match", TN,
        "    return window[i + 1 :] == target[i:] if i < n else True\n", "    return window[i + 1 :] == target[i + 1 :] if i < n else True\n",
        "test_a_changed_letter_is_not_found", "a changed letter is found", test_file=FB),
    mutant("insertion: a missing letter is a match", TN,
        "    return window[i + 1 :] == target[i:] if i < n else True\n", "    return window[i:] == target[i + 1 :] if i < n else True\n",
        "test_a_missing_letter_is_not_found", "a missing letter is found", test_file=FB),
    mutant("insertion: the tail past a mismatch is not compared", TN,
        "    return window[i + 1 :] == target[i:] if i < n else True\n", "    return True\n",
        "test_two_inserted_letters_are_not_found", "two inserted letters are found", test_file=FB),
    mutant("insertion: a window that agrees to the end is not a match", TN,
        "    return window[i + 1 :] == target[i:] if i < n else True\n", "    return window[i + 1 :] == target[i:] if i < n else False\n",
        "test_the_matcher_takes_a_window_that_agrees_with_the_needle_to_the_end", "is not matched", test_file=O),
    mutant("insertion: the minimum is one too high", TN,
        "if kind == \"script\" and _insertion_minimum(needle) <= len(needle) <= limit", "if kind == \"script\" and _insertion_minimum(needle) < len(needle) <= limit",
        "test_one_inserted_letter_of_the_same_script_is_found_at_every_inner_position", "is not found", test_file=FB),
    mutant("insertion: the minimum is one too low", TN,
        "if kind == \"script\" and _insertion_minimum(needle) <= len(needle) <= limit", "if kind == \"script\" and _insertion_minimum(needle) - 1 <= len(needle) <= limit",
        "test_a_needle_below_the_minimum_of_its_script_is_matched_exactly_only", "a needle under the minimum is matched with an insertion", test_file=FB),
    mutant("insertion: the minimum ignores the script", TN,
        "by_script.get(group, defaults.TEXTNORM_INSERTION_MIN_CHARS) for group in groups", "defaults.TEXTNORM_INSERTION_MIN_CHARS for group in groups",
        "test_each_script_has_its_own_minimum", "is not the one of the table", test_file=FB),
    mutant("insertion: the maximum is one too high", TN,
        "if kind == \"script\" and _insertion_minimum(needle) <= len(needle) <= limit", "if kind == \"script\" and _insertion_minimum(needle) <= len(needle) <= limit + 1",
        "test_a_needle_longer_than_the_maximum_is_matched_exactly_only", "over the maximum is matched with an insertion", test_file=FB),
    mutant("tables: the dash table drops the minus sign", TN,
        "    table[0x2212] = \"-\"\n", "",
        "test_the_unicode_dependent_tables_have_a_pinned_digest_for_each_version_we_run", "changed", test_file=FB),

    # ---- order 137 (D1, D2, D3, D5, D7, F1, F9, F11 and the R2-04 pins that had no mutant)
    mutant("scan_views: None is a value that has no scripts", TN,
        "    _checked(raw, value)\n    return tuple(view for view in _all_views(raw, _value_scripts(value)) if view)\n",
        "    _checked(raw, value or \"\")\n    return tuple(view for view in _all_views(raw, _value_scripts(value or \"\")) if view)\n",
        "test_scan_views_refuses_none_as_the_value_and_the_other_function_gives_the_views_of_no_value", "raised nothing, not NotText", test_file=O),
    mutant("register: a value in the band is exact only", TN,
        "        coverage, reason = (\n            _FUZZY,\n", "        coverage, reason = (\n            _EXACT_ONLY,\n",
        "test_a_value_in_the_insertion_band_is_registered_as_fuzzy_and_strict_accepts_it", "register_value raised CoverageRefused", test_file=O),
    mutant("register: the band minimum is one too high", TN,
        "if any(_insertion_minimum(n) <= len(n) <= limit for n in script_needles)", "if any(_insertion_minimum(n) < len(n) <= limit for n in script_needles)",
        "test_the_band_edges_of_a_script_value", "4 Han letters: exact_only, not fuzzy", test_file=O),
    mutant("register: the band maximum is one too low", TN,
        "if any(_insertion_minimum(n) <= len(n) <= limit for n in script_needles)", "if any(_insertion_minimum(n) <= len(n) < limit for n in script_needles)",
        "test_the_band_edges_of_a_script_value", "64 Han letters: exact_only, not fuzzy", test_file=O),
    mutant("register: the band maximum is one too high", TN,
        "if any(_insertion_minimum(n) <= len(n) <= limit for n in script_needles)", "if any(_insertion_minimum(n) <= len(n) <= limit + 1 for n in script_needles)",
        "test_the_band_edges_of_a_script_value", "65 Han letters: fuzzy, not exact_only", test_file=O),
    mutant("register: strict is not the default", TN,
        "        strict = defaults.TEXTNORM_STRICT_COVERAGE\n", "        strict = False\n",
        "test_a_latin_value_is_exact_only_and_strict_refuses_it_by_default", "raised nothing, not CoverageRefused", test_file=O),
    mutant("register: the default of strict ignores the constant", TN,
        "        strict = defaults.TEXTNORM_STRICT_COVERAGE\n", "        strict = True\n",
        "test_the_default_of_strict_is_the_constant_in_defaults", "where a value was expected", test_file=O),
    mutant("register: a narrowed value is accepted in strict mode", TN,
        "    if strict and (coverage == _EXACT_ONLY or narrowed):", "    if strict and coverage == _EXACT_ONLY:",
        "test_a_value_with_a_script_part_and_an_ascii_part_that_has_no_needle_is_narrowed", "raised nothing, not CoverageRefused", test_file=O),
    mutant("register: the refusal does not name the setting", TN,
        "(the setting defaults.TEXTNORM_STRICT_COVERAGE, True by default, or strict=True), ", "",
        "test_the_strict_refusal_names_the_setting_that_makes_it_strict", "the refusal does not name the setting", test_file=O),
    mutant("refusal: the value is in the ViewTooShort message", TN,
        "f\"this protected value ({len(raw)} characters) is too short to mask:", "f\"this protected value {raw} ({len(raw)} characters) is too short to mask:",
        "test_the_minimum_view_length_is_one_number_per_kind_of_view_and_a_short_value_is_refused", "the message holds the value", test_file=T),
    mutant("refusal: the value is in the CoverageRefused message", TN,
        "f\"this protected value ({len(value)} characters) is covered", "f\"this protected value {value} ({len(value)} characters) is covered",
        "test_a_latin_value_is_exact_only_and_strict_refuses_it_by_default", "the message holds the value", test_file=O),
    mutant("digits: the default minimum is five", DEF,
        "TEXTNORM_MIN_DIGIT_CHARS = 6\n", "TEXTNORM_MIN_DIGIT_CHARS = 5\n",
        "test_the_minimum_view_length_is_one_number_per_kind_of_view_and_a_short_value_is_refused", "is not the pinned one", test_file=T),
    mutant("register: a refused value is registered", TN,
        "    needles = _needles_or_refuse(value, _value_scripts(value))\n    limit = defaults.TEXTNORM_INSERTION_MAX_CHARS\n    script_needles",
        "    needles = [(\"script\", value)]\n    limit = defaults.TEXTNORM_INSERTION_MAX_CHARS\n    script_needles",
        "test_a_value_that_cannot_be_scanned_is_refused_in_both_modes", "not EmptyView", test_file=O),
    mutant("register: the coverage is not logged at its level", TN,
        "    level = logging.INFO if coverage == _FUZZY and not narrowed else logging.WARNING\n", "    level = logging.INFO\n",
        "test_registration_is_logged_with_the_coverage_and_never_the_value", "instead of INFO then WARNING", test_file=O),
    mutant("injection: a module builds its own views", INJ,
        "for view in (text, *textnorm.scan_views_no_value(text)):", "for view in (text, *textnorm.scan_keyset(text)):",
        "test_no_module_outside_textnorm_builds_its_own_views", "a module builds its own views", test_file=O),
    mutant("cache: the views are kept outside a scope", TN,
        "\"hadavin_textnorm_scan_cache\", default=None", "\"hadavin_textnorm_scan_cache\", default={}",
        "test_nothing_of_a_text_is_kept_between_calls_outside_a_scope", "kept between two calls", test_file=O),
    mutant("cache: the key is the text", TN,
        "        key = hashlib.sha256(raw.encode(\"utf-8\", \"surrogatepass\")).hexdigest()\n", "        key = raw\n",
        "test_the_scope_keeps_digests_not_texts_at_most_two_and_empties_itself", "a key is not a digest", test_file=O),
    mutant("cache: the scope is not emptied", TN,
        "        if cache is not None:\n            cache.clear()\n", "        if cache is not None:\n            pass\n",
        "test_the_scope_keeps_digests_not_texts_at_most_two_and_empties_itself", "did not empty the cache", test_file=O),
    mutant("cache: more than two texts are kept", TN,
        "_SCAN_CACHE_TEXTS = 2\n", "_SCAN_CACHE_TEXTS = 3\n",
        "test_the_scope_keeps_digests_not_texts_at_most_two_and_empties_itself", "texts kept, two allowed", test_file=O),
    mutant("squeeze: the minimum is five", DEF,
        "TEXTNORM_MIN_SQUEEZE_CHARS = 4\n", "TEXTNORM_MIN_SQUEEZE_CHARS = 5\n",
        "test_the_russian_word_for_password_is_accepted_at_the_pinned_outcome", "scan_needles raised ViewTooShort", test_file=O),
    mutant("insertion: Han and kana take the larger minimum", TN,
        "    return min(minimums) if groups == _JAPANESE_GROUPS else max(minimums)\n", "    return max(minimums)\n",
        "test_a_japanese_needle_of_han_and_kana_takes_the_han_minimum_and_other_mixtures_the_largest", "at the Han minimum is not matched", test_file=O),
    mutant("insertion: any mixture that holds Han and kana takes the smaller minimum", TN,
        "    return min(minimums) if groups == _JAPANESE_GROUPS else max(minimums)\n", "    return min(minimums) if _JAPANESE_GROUPS <= groups else max(minimums)\n",
        "test_a_japanese_needle_of_han_and_kana_takes_the_han_minimum_and_other_mixtures_the_largest", "three groups do not take the largest", test_file=O),
    mutant("insertion: several scripts take the smallest minimum", TN,
        "    return min(minimums) if groups == _JAPANESE_GROUPS else max(minimums)\n", "    return min(minimums)\n",
        "test_a_japanese_needle_of_han_and_kana_takes_the_han_minimum_and_other_mixtures_the_largest", "three groups do not take the largest", test_file=O),
    mutant("keys: the cap guard refuses the cap itself", TN,
        "    if len(keys) > _SCAN_KEY_CAP:\n", "    if len(keys) >= _SCAN_KEY_CAP:\n",
        "test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused", "scan_keyset raised TextTooLong", test_file=O),
    mutant("keys: the cap guard is gone", TN,
        "    if len(keys) > _SCAN_KEY_CAP:\n", "    if False:\n",
        "test_exactly_the_cap_in_scan_keys_is_allowed_and_one_over_is_refused", "raised nothing, not TextTooLong", test_file=O),
    mutant("keys: the cap is fifteen", TN,
        "_SCAN_KEY_CAP = 16\n", "_SCAN_KEY_CAP = 15\n",
        "test_the_scan_key_cap_is_sixteen_by_construction_and_the_most_a_text_can_make_is_thirteen", "15 == 16", test_file=FB),
    mutant("tables: the digit table drops the Thai five", TN,
        "if chr(cp).isdecimal() and not (\"0\" <= chr(cp) <= \"9\")", "if chr(cp).isdecimal() and not (\"0\" <= chr(cp) <= \"9\") and cp != 0x0E55",
        "test_the_unicode_dependent_tables_have_a_pinned_digest_for_each_version_we_run", "tables for Unicode", test_file=FB),
    mutant("docs: the digit decision is not in the module docstring", TN,
        "ticket (P1) asked for 6 digits", "ticket (P1) asked for six numerals",
        "test_the_decisions_are_in_the_module_docstring_and_li_na_is_not_lina", "does not state the digit decision", test_file=FB),
    mutant("injection: a refused text is not flagged", INJ,
        "return Verdict(flagged=True, score=1.0, backend=name, reason_code=\"guard_unavailable\")", "return Verdict(flagged=False, score=0.0, backend=name, reason_code=\"guard_unavailable\")",
        "test_the_injection_detector_check_method_is_called_by_injection_check_only", "does not flag a refused text", test_file=FB),
    mutant("insertion: the window is longer than the needle", TN,
        "        if _one_off(view[stop : stop + (m - h) + 1], second):\n", "        if _one_off(view[stop:], second):\n",
        "test_the_work_of_the_matcher_is_linear_in_the_view_for_a_text_built_to_defeat_it", "more than the needle's length", test_file=FB),
    mutant("squeeze: the minimum is two (the ASCII part of a mixed value)", DEF,
        "TEXTNORM_MIN_SQUEEZE_CHARS = 4\n", "TEXTNORM_MIN_SQUEEZE_CHARS = 2\n",
        "test_the_mixed_value_claim_of_the_changelog_holds", "the ASCII part alone is found", test_file=FB),
    mutant("squeeze: the minimum is three (the cost of the refusal)", DEF,
        "TEXTNORM_MIN_SQUEEZE_CHARS = 4\n", "TEXTNORM_MIN_SQUEEZE_CHARS = 3\n",
        "test_a_short_cyrillic_or_greek_word_is_refused_at_a_measured_cost", "the measured cost changed", test_file=FB),
    mutant("refusal: the plain words say skipped", TN,
        "A value that cannot be masked is REFUSED, never ignored. What to do:", "A value that cannot be masked is skipped. What to do:",
        "test_the_refusal_names_the_rule_the_length_and_what_to_do_and_never_the_value", "is not in the refusal for a value of", test_file=FB),
]  # fmt: skip


def is_wording_only(mutant_) -> bool:
    """True when the mutated module's syntax tree equals the original after the docstrings and the message arguments of every ``raise`` are
    removed. Such a mutant changes only words, not behaviour (ORDER 177 Q4: the split is derived, not typed)."""
    import ast

    def plain(source: str) -> str:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = node.body
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    body[0] = ast.Pass()
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                node.exc.args = []
                node.exc.keywords = []
        return ast.dump(tree)

    if not mutant_.file.endswith(".py"):
        return False  # a data file: its words are its data
    text = (ROOT / mutant_.file).read_text(encoding="utf-8")
    assert text.count(mutant_.old) == 1, mutant_.name
    return plain(text) == plain(text.replace(mutant_.old, mutant_.new))


def split_counts() -> tuple[int, int]:
    """(behaviour, wording-only) over the whole list."""
    wording = sum(is_wording_only(m) for m in M)
    return len(M) - wording, wording


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    behaviour, wording = split_counts()
    print(f"{len(M)} mutants: {behaviour} change behaviour, {wording} change only words")
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

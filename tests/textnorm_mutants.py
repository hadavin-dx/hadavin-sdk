"""The mutants of the text fold (``guard/textnorm.py``), the look-alike table (``guard/_confusables.py``) and its generator.

Each mutant changes ONE thing in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in ``only_test`` must
fail, it must be the test pinned in ``pinned``, and the first failing line must hold ``expect``: a fragment of the assertion MESSAGE the test
gives for that one guard (never a fragment of the test's own name). Every mutant names both the file of its killer (``test_file``) and the
killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the test placement table. Not collected by
pytest. Run from the repo root:

    uv run python tests/textnorm_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/textnorm_mutants.py squeeze    # only mutants whose name contains the text

51 mutants: 28 are the re-pointed mutants of the earlier text-fold list (the killers moved with their tests), 13 are new and 10 are the mutants of fold2 (order 44). Tests with no
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
CFTABLE = (
    "test_the_case_fold_table_is_on_the_case_fold_image_and_its_conflicts_are_the_known_thirteen"
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
        "    s = s.translate(_DIGITS)\n    # casefold BEFORE", "    # casefold BEFORE",
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
    mutant("table: small capital rule missing", GEN, "            out.setdefault(cp, m[1])", "            pass",
        GENERATOR, "the small capital rule is missing", test_file=G),
    mutant("table: ASCII sources accepted", GEN, "        if src < 0x80 or not re.fullmatch", "        if not re.fullmatch",
        GENERATOR, "an ASCII source was accepted", test_file=G),
    mutant("table: capital I prototype stays l", GEN, '            dst = "I"', '            dst = "l"',
        GENERATOR, "capital I prototype read as l", test_file=G),
    mutant("table: the generator accepts any file", GEN, "    if sha != PINNED_SHA256:", "    if False:",
        GENERATOR, "accepted an unpinned file", test_file=G),
    mutant("table: the pin in the generator differs", GEN, 'PINNED_SHA256 = "6ed3ee96', 'PINNED_SHA256 = "7ed3ee96',
        TABLE, "pins another sha256", test_file=G),
    mutant("allow: a case difference is a spoof alarm", TN,
        "    if _canon(a) == _canon(b):\n        return AllowVerdict.VARIANT",
        "    if False:\n        return AllowVerdict.VARIANT", ALLOW, "gave LOOKALIKE, wanted VARIANT"),
    mutant("allow: a verdict has a truth value", TN,
        "        raise TypeError(\"an AllowVerdict has no truth value: compare with 'is AllowVerdict.EQUAL'\")",
        "        return True", ALLOW, "an AllowVerdict has a truth value"),
    mutant("deny: same_person does not fold", TN,
        "    return fold_key(a) == fold_key(b)", "    return a == b", ALLOW, "same_person does not fold a look-alike"),
    mutant("textnorm: a newline joins the words of the script check", TN,
        '        " " if ch.isspace() else ch  # a newline or tab separates words, as in fold',
        '        "" if ch.isspace() else ch  # a newline or tab separates words, as in fold',
        NEWLINE, "joins the words of the script check"),
    mutant("table: the vendored data file differs from the pin", "tools/data/confusables.txt",
        "# Date: 2026-08-06, 01:05:35 GMT", "# Date: 2026-08-07, 01:05:35 GMT",
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
        "87,382 x U+A516 (W 262,146) is accepted"),
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
    mutant("order: no case fold before the marks are dropped", TN,
        "raw.casefold() if casefold else raw)", "raw)", SYMM, "identity_key is not case symmetric for"),
    mutant("order: the case fold table is the raw table", TN,
        "_CF_TABLE = types.MappingProxyType(_build_cf_table(CONFUSABLES))",
        "_CF_TABLE = types.MappingProxyType(dict(CONFUSABLES))", CFTABLE, "is not a casefolded non-ASCII key"),
    mutant("order: a capital wins over its own small letter", TN,
        "    return {**derived, **own}", "    return {**own, **derived}", CFTABLE, "does not take the entry of its own letter"),
    mutant("squeeze: no case fold before the look-alike table", TN,
        "    s = _fold(raw, casefold=True).upper()", "    s = _fold(raw).upper()", SQUEEZE_SYMM, "squeeze is not case symmetric for"),
    mutant("pin: require_pinned_unidata only warns", TN,
        "    check_pinned_unidata(expected, strict=True)", "    check_pinned_unidata(expected)", REQUIRE, "require_pinned_unidata accepted another Unicode version"),
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

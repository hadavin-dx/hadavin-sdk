"""Meta-tests of the text-fold tests and mutants. They read the test files, the mutant list and the sources; they are NOT in any mutant's
test list (a mutant tree holds only the listed test files), so they are checked on the real tree only. Letters as in the plan:
(a) the mutant list is the test placement table and every killer exists, (b) every ``xfail`` of the differential file is strict and
names ``AssertionError``, (c) the corpus keeps at least 3 rows per class and 150 rows, (g) every search string occurs exactly once in the file it
targets, (h) ``guard/textnorm.py`` holds no ``assert`` statement. The letters d, e and f are not used in this package (e is the caller lint
of a later package).
"""

import ast
import json
import re
import tomllib
from collections import Counter
from pathlib import Path

from tests import textnorm_mutants as mm

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
TEXTNORM = ROOT / "src" / "hadavin_sdk" / "guard" / "textnorm.py"
CORPUS = TESTS / "fixtures" / "textnorm_corpus.json"

REPOINTED = (
    "fold: combining marks kept",
    "fold: unassigned characters kept",
    "fold: look-alikes not folded",
    "fold: other digits not folded",
    "fold: the digit table is empty",
    "fold: fillers kept",
    "fold: Greek eta missing",
    "fold: Armenian missing",
    "fold: dotless i missing",
    "fold: loose map short",
    "fold: confusable pair not detected",
    "fold: mixed script never true",
    "allow: equality is normalised",
    "allow: a mismatch is always a look-alike",
    "mixed: invisible characters not removed first",
    "mixed: the micro sign is flagged",
    "mixed: Cherokee exempt next to Latin",
    "table: Cherokee A missing",
    "table: small capital rule missing",
    "table: ASCII sources accepted",
    "table: capital I prototype stays l",
    "table: the generator accepts any file",
    "table: the pin in the generator differs",
    "allow: a case difference is a spoof alarm",
    "allow: a verdict has a truth value",
    "deny: could_be_same_person does not fold",
    "textnorm: a newline joins the words of the script check",
    "table: the vendored data file differs from the pin",
)
EXPECTED_CLASSES = {
    "zero-width",
    "bidi controls",
    "tag characters",
    "variation selectors",
    "emoji sequences and keycaps",
    "full-width",
    "Cyrillic, Greek, Armenian and Cherokee look-alikes",
    "combining marks",
    "filler letters",
    "NFKC expansion",
    "other-script digits",
    "Unicode whitespace",
    "private use",
    "unassigned code points",
    "ideographic variation selector",
    "controls",
    "lone surrogates",
    "mixed scripts",
    "unlisted script",
    "cap, empty and whitespace-only",
    "case",
    "dashes, slashes and quotes",
    "letters written as digits",
    "allow side",
    "Intake invoice steps",
    "Hindi and Thai marks",
    "letters written as symbols",
    "digits written as symbols",
}


def _functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def test_a_the_list_has_226_mutants_77_of_p1a_fix4_26_of_p1b_14_of_p1a_fix5_5_of_fix6_31_of_fix7_10_of_p1a_fix8_and_63_of_the_p1b_fix_batch_with_unique_names():
    names = [m.name for m in mm.M]
    assert len(names) == 226 and len(set(names)) == 226, names
    assert tuple(names[:28]) == REPOINTED, (
        "the first 28 are the re-pointed mutants, in the order of the placement table"
    )
    assert (
        len(names[28:]) == 198
    )  # 12 of the first package, 9 of fold2, 3 of fold3, 16 of fold4, 9 of fix4, 26 of P1b, 14 of fix5, 5 of fix6, 31 of fix7, 63 of the P1b fix batch (30 of the first batch and 33 of order 137) and 10 of P1a fix8 (the list order is the merge order, not the date order)
    assert names[52:53] == ["fold: case folded before the marks are dropped (the fold2 order)"], (
        "the restored fold2 mutant is the first of the fold4 mutants"
    )
    assert all(n.split(":")[0] in {"marks", "names", "pin"} for n in names[103:117]), (
        "names 104 to 117 are the mutants of fix5"
    )
    assert sum(n.startswith("names:") for n in names[103:117]) == 6, (
        "the six name-rule mutants of fix5"
    )
    assert all(n.split(":")[0] in {"script", "scan", "names"} for n in names[117:122]), (
        "names 118 to 122 are the mutants of fix6"
    )
    assert sum(n.startswith("readings:") for n in names) == 7, (
        "the mutants of the readings (drop one, first only, unbounded, ...)"
    )
    assert len(names[77:103]) == 26, (
        "P1b adds 22 mutants (and 4 more in merge 7: a fifth, 'scan_views: the scripts are not checked', was removed because scan_views no longer takes scripts), after the 77 of P1a fix4 (the 14 of P1a fix5, the 5 of fix6 and the 32 of fix7 come last)"
    )
    assert len(names[103:117]) == 14, "the 14 of P1a fix5"
    assert len(names[117:122]) == 5, "the 5 of P1a fix6"
    assert len(names[122:153]) == 31, (
        "the 32 of P1a fix7, less the one that the fix batch removed (a bool as a minimum is refused by the floor of 2 anyway)"
    )
    assert len(names[153:163]) == 10, "the 10 of P1a fix8 (they come first after the fix7 mutants)"
    assert len(names[163:]) == 63, (
        "the 63 of the P1b fix batch: 30 of the first batch and 33 of order 137"
    )
    assert all(
        n.split(":")[0]
        in {
            "runmap",
            "keys",
            "digits",
            "scan",
            "scan_views",
            "fold_views",
            "injection",
            "minimum",
            "passes",
            "insertion",
            "tables",
            "register",
            "cache",
            "squeeze",
            "docs",
            "refusal",
        }
        for n in names[153:]
    ), "the fix batch mutants"


def test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists():
    defined = {}
    for m in mm.M:
        assert m.test_file and m.only_test, f"{m.name}: test_file and only_test are both required"
        path = ROOT / m.test_file
        assert path.is_file(), (m.name, m.test_file)
        defined.setdefault(m.test_file, _functions(path))
        assert m.only_test in defined[m.test_file], (m.name, m.only_test, "is not in", m.test_file)
        assert m.pinned == m.test_file.removesuffix(".py") + "::" + m.only_test, (m.name, m.pinned)
        # ``expect`` is a fragment of an assertion MESSAGE, never of the killer's own name
        assert m.expect.replace(" ", "_").lower() not in m.only_test, (
            m.name,
            "expect is part of the test name",
        )
        assert m.test_file in mm.TESTS, (m.name, "the killer's file is not in the test list")


def test_a_the_test_list_puts_the_killer_files_first_and_leaves_out_perf_meta_and_notices():
    assert list(mm.TESTS[:3]) == [mm.T, mm.G, mm.SC]
    assert mm.TESTS[-1] == mm.D, "the differential and golden file runs last"
    for left_out in ("perf", "meta", "notices"):
        assert not any(left_out in t for t in mm.TESTS), left_out
    assert {m.test_file for m in mm.M} == {mm.T, mm.G, mm.SC, mm.SB, mm.FB, mm.O}


def test_a_the_moved_tests_and_the_new_killers_exist_once_each():
    for path in (
        TESTS / "test_textnorm.py",
        TESTS / "test_textnorm_generator.py",
        TESTS / "test_textnorm_differential.py",
        TESTS / "test_textnorm_scan.py",
        TESTS / "test_textnorm_callers.py",
        TESTS / "test_textnorm_app.py",
    ):
        tests = [n for n in _functions(path) if n.startswith("test_")]
        assert len(tests) == len(set(tests)), (
            f"{path.name}: a test name is defined twice, the first would be shadowed"
        )
    assert (
        _functions(TESTS / "test_textnorm.py")[-1]
        == "test_the_manifest_pins_the_files_a_demo_copies"
    ), "the manifest test stays last on purpose"


def test_a_print_the_placement_table():
    rows = [f"{m.name} | {m.test_file} | {m.only_test}" for m in mm.M]
    print("\n".join(rows))
    assert len(rows) == 226


def test_b_every_xfail_of_the_differential_file_is_strict_and_names_assertion_error():
    tree = ast.parse((TESTS / "test_textnorm_differential.py").read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "xfail"
    ]
    assert calls, "the differential file has no xfail: a row with status p1b would not be marked"
    for call in calls:
        kw = {k.arg: k.value for k in call.keywords}
        assert isinstance(kw.get("strict"), ast.Constant) and kw["strict"].value is True
        assert isinstance(kw.get("raises"), ast.Name) and kw["raises"].id == "AssertionError"
    assert "pytest.mark.xfail" not in (TESTS / "test_textnorm.py").read_text(encoding="utf-8")


def test_c_the_corpus_has_150_rows_and_3_rows_in_every_class():
    rows = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert len(rows) >= 150, len(rows)
    per_class = Counter(r["class"] for r in rows)
    assert set(per_class) == EXPECTED_CLASSES, set(per_class) ^ EXPECTED_CLASSES
    assert min(per_class.values()) >= 3, {k: v for k, v in per_class.items() if v < 3}
    assert len({r["id"] for r in rows}) == len(rows), "a row id is used twice"
    for r in rows:
        assert set(r) == {"id", "class", "source", "a", "b", "relation", "status"}, r["id"]
        assert r["relation"] in ("equal", "different", "refused"), r["id"]
        assert r["status"] in ("current", "p1b", "not_taken"), r["id"]
        assert r["source"].strip(), f"{r['id']}: a row without a stated principle"
        if r["status"] == "not_taken":
            assert r["relation"] == "different", r["id"]
    assert any(
        r["status"] == "not_taken" for r in rows
    )  # no row is p1b any more: the whole principle is taken


def test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets():
    sources = {}
    for m in mm.M:
        text = sources.setdefault(m.file, (ROOT / m.file).read_text(encoding="utf-8"))
        n = text.count(m.old)
        print(f"{'occurs once' if n == 1 else 'OCCURS ' + str(n) + ' TIMES'}: {m.name} [{m.file}]")
        assert n == 1, f"{m.name}: the search string occurs {n} times in {m.file}"
        assert m.old != m.new, m.name


def test_h_textnorm_holds_no_assert_statement():
    tree = ast.parse(TEXTNORM.read_text(encoding="utf-8"))
    found = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert not found, (
        f"assert statements at lines {found}: every check must raise explicitly so it holds under python -O"
    )


def test_i_the_changelog_states_the_true_mutant_count_the_stale_names_and_the_golden_skip():
    """The CHANGELOG counts the mutants right (it said 90 for 91), names the stale ticket names and the live ones, and says what the golden test
    does on an unknown Unicode version (it skips; it does not claim that nothing is skipped)."""
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"{len(mm.M)} mutants in\n  `tests/textnorm_mutants.py`" in log, (
        "the CHANGELOG does not state the number of mutants in the list"
    )
    for stale, live in (
        ("check_pinned_unidata", "require_pinned_unidata"),
        ("same_person", "could_be_same_person"),
        ("fold_key", "identity_key"),
        ("TEXTNORM_MAX_PASSES", "nothing reads it"),
    ):
        assert f"`{stale}`" in log and live in log, stale
    assert "STALE NAMES" in log
    assert "none is skipped" not in log, "the CHANGELOG says again that nothing is skipped"
    assert "SKIPS with the fingerprint" in log


def test_the_changelog_marks_the_two_stale_notes_as_superseded_and_states_the_limits_once():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for needle in ("module has 20 public names", "P1b must refuse an empty view before it scans"):
        line = next(ln for ln in text.splitlines() if needle in ln)
        assert "superseded" in line.lower(), f"the stale note is not marked: {needle}"
    assert text.count("MIXED VALUES OVER-MATCH") == 1, (
        "the mixed-value over-match is not stated exactly once"
    )
    assert "loosens only the squeeze" in text, "the loose=True note is missing"
    assert "MAX_VALUE_LEN" in text


# --- T6-5: the ban on the single readings is durable (no subprocess here: the two ruff runs are CI steps A and B) ------------------

BAN_TABLE = "hadavin_sdk.guard.textnorm."
BANNED = ("fold", "squeeze", "identity_key")
# rows of code (not tests) that may keep a single reading: path of the file, with its reason. Empty in P1a; PR 77 adds its own row.
EXEMPTIONS: dict[str, str] = {}
CI = ROOT / ".github" / "workflows" / "ci.yml"
STEP_A = "ruff check --select TID251 --ignore-noqa src demos tools"
STEP_B = (
    "out=$(ruff check --select TID251 --ignore-noqa --config 'lint.per-file-ignores = {}' "
    "--output-format concise tests/fixtures/tid251_forms || true)\n"
    "test \"$(printf '%s\\n' \"$out\" | grep -c ' TID251 ')\" -eq 6"
)


def _code_files():
    for top in ("src", "demos", "tools"):
        yield from (ROOT / top).rglob("*.py")


def test_the_ruff_config_bans_the_single_readings_outside_the_tests():
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["ruff"][
        "lint"
    ]
    assert "TID" in cfg["extend-select"]
    banned = cfg["flake8-tidy-imports"]["banned-api"]
    assert set(banned) == {BAN_TABLE + n for n in BANNED}
    for name in BANNED:
        msg = banned[BAN_TABLE + name]["msg"]
        assert msg.strip()
        assert ("identity_keys" in msg) or ("fold_views" in msg), name
    ignores = cfg["per-file-ignores"]
    assert ignores["tests/**"] == ["S101", "TID251"]
    for path, rules in ignores.items():
        if "TID251" in rules and path != "tests/**":
            assert path in EXEMPTIONS, f"{path}: an exemption without a row and a reason"
    for path in EXEMPTIONS:
        assert "TID251" in ignores.get(path, []), path


def test_no_code_file_hides_the_ban_with_a_comment_or_uses_the_key_list_outside_textnorm():
    hide = re.compile(
        r"#\s*noqa(?!\s*:)|#\s*noqa\s*:[^\n]*TID251|#\s*ruff\s*:\s*noqa", re.IGNORECASE
    )
    seen = 0
    for path in _code_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        seen += 1
        assert not hide.search(text), f"{rel}: a comment that switches the ban off"
        if rel != "src/hadavin_sdk/guard/textnorm.py":
            assert "identity_keys" not in text, f"{rel}: names identity_keys (never a unique index)"
    assert seen > 50, seen


def test_the_ci_lint_job_holds_the_two_ban_steps_word_for_word():
    text = CI.read_text(encoding="utf-8")
    assert f"run: {STEP_A}\n" in text
    indented = STEP_B.replace("\n", "\n          ")
    assert f"run: |\n          {indented}\n" in text
    assert (
        text.index("ruff check src tests demos tools")
        < text.index(STEP_A)
        < text.index("ruff format --check")
    )
    forms = sorted(p.name for p in (TESTS / "fixtures" / "tid251_forms").glob("*.py"))
    assert len(forms) == 6 and not any(n.startswith("test_") for n in forms), forms


def test_the_split_of_the_mutants_into_behaviour_and_wording_only_is_derived_from_the_syntax_trees():
    behaviour, wording = mm.split_counts()
    assert behaviour + wording == len(mm.M) == 226
    new = mm.M[153:163]  # the 10 of P1a fix8
    assert len(new) == 10
    assert [m.name for m in new if mm.is_wording_only(m)] == [
        "words: the squeeze docstring calls itself a check name for a scan",
        "words: the names_equal docstring says NFKC",
    ], "the wording-only mutants of fix8 are exactly these two"
    assert sum(not mm.is_wording_only(m) for m in new) == 8
    print(f"{behaviour} mutants change behaviour, {wording} change only words")
    assert wording >= 2 and behaviour > wording

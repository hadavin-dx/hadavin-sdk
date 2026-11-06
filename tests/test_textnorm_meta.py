"""Meta-tests of the text-fold tests and mutants. They read the test files, the mutant list and the sources; they are NOT in any mutant's
test list (a mutant tree holds only the listed test files), so they are checked on the real tree only. Letters as in the plan:
(a) the mutant list is the test placement table and every killer exists, (b) every ``xfail`` of the differential file is strict and
names ``AssertionError``, (c) the corpus keeps at least 3 rows per class and 150 rows, (g) every search string occurs exactly once in the file it
targets, (h) ``guard/textnorm.py`` holds no ``assert`` statement. The letters d, e and f are not used in this package (e is the caller lint
of a later package).
"""

import ast
import json
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
    "deny: same_person does not fold",
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
}


def _functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def test_a_the_list_has_71_mutants_28_repointed_25_of_p1a_and_18_of_p1b_with_unique_names():
    names = [m.name for m in mm.M]
    assert len(names) == 71 and len(set(names)) == 71, names
    assert tuple(names[:28]) == REPOINTED, (
        "the first 28 are the re-pointed mutants, in the order of the placement table"
    )
    assert len(names[28:]) == 43  # 25 of P1a (13 new, 9 of fold2, 3 of fold3) and the 18 of P1b
    assert len(names[53:]) == 18, "P1b adds 18 mutants"


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
    assert {m.test_file for m in mm.M} == {mm.T, mm.G, mm.SC}


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
    assert len(rows) == 71


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

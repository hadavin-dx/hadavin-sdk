"""Meta-tests of ``tests/redact_mutants.py`` (G1 Q9 review F7; like ``test_textnorm_meta.py``). They read the mutant list, the test files and the
sources; they are NOT in any mutant's test list, so they run on the real tree only. They would have caught the mis-pinned DM-1 killer: every
``only_test`` must exist in its file, every ``pinned`` id must be ``file::only_test`` (with a parameter id only for a parametrized test), the
count is pinned, the 30 ``Q9 U+XXXX`` code points are the list of section 6 of the G3 evidence, names are unique and every search string
occurs exactly once in its file (the one exception is declared)."""

import ast
import re
from collections import Counter
from pathlib import Path

from tests import redact_mutants as rm

ROOT = Path(__file__).resolve().parents[1]
SECTION6 = ROOT / "handover" / "core-c" / "evidence" / "G3-p2d-port.md"
EXPECTED_COUNT = 137  # 63 older + 3 E9 + 30 Q9 = 96, minus N1 and N14 (deleted with the dead U+2044 code, G1 Q9 review F3); + 29 G9 (22 + G9-24, the G8 joins, + G9-25 .. G9-30 the E17 feasibility window) + 7 G9b (G9-31 .. G9-37) + 7 G9c (G9-38 .. G9-44)
OCCURS_TWICE = {
    "21 the views get no shared deadline"
}  # its docstring says why: both ``_deadline=`` arguments


def _test_functions(path: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _is_parametrized(fn: ast.FunctionDef) -> bool:
    return any("parametrize" in ast.unparse(d) for d in fn.decorator_list)


def test_the_count_of_mutants_is_pinned():
    assert len(rm.M) == EXPECTED_COUNT, (
        f"MUTANT-COUNT: {len(rm.M)} mutants, the pin says {EXPECTED_COUNT} (update the evidence with it)"
    )


def test_the_names_are_unique():
    dup = [n for n, c in Counter(m.name for m in rm.M).items() if c > 1]
    assert not dup, dup


def test_every_mutant_names_a_killer_that_exists_in_its_file():
    for m in rm.M:
        assert m.test_file and m.only_test, f"{m.name}: test_file and only_test are required"
        assert (ROOT / m.test_file).is_file(), f"{m.name}: {m.test_file} does not exist"
        assert m.only_test in _test_functions(m.test_file), (
            f"{m.name}: {m.only_test} is not a test of {m.test_file}"
        )


def test_every_pinned_id_is_file_double_colon_test_with_a_parameter_id_only_for_a_parametrized_test():
    for m in rm.M:
        match = re.fullmatch(r"(tests/[a-z0-9_]+)::([a-z0-9_]+)(\[[^\]]+\])?", m.pinned)
        assert match, f"{m.name}: pinned {m.pinned!r} is not file::test or file::test[id]"
        assert match[1] + ".py" == m.test_file, (
            f"{m.name}: pinned {m.pinned!r} is not in {m.test_file}"
        )
        assert match[2] == m.only_test, (
            f"{m.name}: pinned {m.pinned!r} is not the test {m.only_test}"
        )
        if match[3]:
            assert _is_parametrized(_test_functions(m.test_file)[m.only_test]), (
                f"{m.name}: {m.only_test} is not parametrized"
            )


def test_every_search_string_occurs_exactly_once_in_its_file():
    for m in rm.M:
        found = (ROOT / m.file).read_text(encoding="utf-8").count(m.old)
        want = 2 if m.name in OCCURS_TWICE else 1
        assert found == want, (
            f"{m.name}: the search text occurs {found} times in {m.file}, expected {want}"
        )


def test_the_q9_code_points_are_the_list_of_section_6():
    text = SECTION6.read_text(encoding="utf-8")
    section = text.split("## 6. The 30 code points", 1)[1].split("\n## ", 1)[0]
    listed = [
        int(c, 16) for c in re.findall(r"^\| U\+([0-9A-F]{4,6}) \|", section, flags=re.MULTILINE)
    ]
    assert len(listed) == 30, len(listed)
    mutants = [int(mm[1], 16) for m in rm.M if (mm := re.match(r"Q9 U\+([0-9A-F]{4,6}) ", m.name))]
    assert mutants == listed, (
        f"Q9-LIST: mutants {[hex(c) for c in mutants]} != section 6 {[hex(c) for c in listed]}"
    )

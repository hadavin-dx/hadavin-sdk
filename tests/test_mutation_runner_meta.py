"""Meta-tests of the mutant list of the mutation runner (P1m): the list names real killers, and every search string is usable.

These tests read ``tests/mutation_runner_mutants.py`` (the 21 mutants) and the files the mutants target. They are NOT in the test
list the mutants run against (a mutant tree holds only the runner's own test file), so they are checked on the real tree only.
Letters follow the P1 ticket: (a) the list is the test placement table and every killer exists, (g) every search string occurs
exactly once in the file it targets.
"""

import ast
from pathlib import Path

from tests import mutation_runner_mutants as mm

ROOT = Path(__file__).resolve().parents[1]
RUNNER_TESTS = ROOT / "tests" / "test_mutation_runner.py"

# the 21 tests moved from the PR #50 head (the manifest test is the 22nd function of the file and has no mutant)
MOVED = (
    "test_mutation_judge_verdicts",
    "test_the_runner_kills_a_mutant_of_a_tiny_package",
    "test_the_runner_refuses_paths_that_leave_its_tree",
    "test_the_runner_children_see_an_allowlisted_environment_only",
    "test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant",
    "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
    "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
    "test_a_failing_tree_kill_still_kills_the_child",
    "test_the_baseline_run_gets_its_own_timeout",
    "test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout",
    "test_a_timeout_kills_the_whole_process_tree_not_only_pytest",
    "test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried",
    "test_the_runner_keeps_a_symlink_a_link",
    "test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs",
    "test_junit_with_a_doctype_or_entity_is_refused_not_parsed",
    "test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
    "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on",
    "test_a_junit_text_over_the_ceiling_is_refused",
    "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
    "test_allow_crash_without_a_crash_type_is_refused_and_a_truncated_junit_marks_the_mutant_error",
    "test_taskkill_is_resolved_under_system_root",
)
MANIFEST_TEST = "test_the_manifest_pins_the_files_a_demo_copies"


def _functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def test_a_the_test_file_holds_the_21_moved_tests_and_the_manifest_test_once_each():
    names = _functions(RUNNER_TESTS)
    tests = [n for n in names if n.startswith("test_")]
    assert len(tests) == len(set(tests)), (
        "a test name is defined twice: the first would be shadowed"
    )
    assert sorted(tests) == sorted((*MOVED, MANIFEST_TEST))
    assert tests[-1] == MANIFEST_TEST, "the manifest test stays last on purpose"


def test_a_there_are_21_mutants_with_unique_names():
    names = [m.name for m in mm.M]
    assert len(names) == 21 and len(set(names)) == 21, names
    assert {m.file for m in mm.M} == {mm.MU, mm.MR}
    assert sum(m.file == mm.MU for m in mm.M) == 5 and sum(m.file == mm.MR for m in mm.M) == 16


def test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists():
    defined = {}
    for m in mm.M:
        assert m.test_file and m.only_test, f"{m.name}: test_file and only_test are both required"
        path = ROOT / m.test_file
        assert path.is_file(), (m.name, m.test_file)
        defined.setdefault(m.test_file, _functions(path))
        assert m.only_test in defined[m.test_file], (m.name, m.only_test, "is not in", m.test_file)
        assert m.only_test in MOVED, (m.name, m.only_test, "is not one of the 21 moved tests")
        # the judge looks for ``expect`` in the failing test id or in its first E line
        assert m.expect in m.only_test or m.crash_type, (m.name, "expect is not the killer's name")


def test_a_the_two_crash_mutants_declare_their_exception_class_and_the_other_19_do_not():
    crash = {m.name: m.crash_type for m in mm.M if m.allow_crash}
    assert crash == {
        "runner: a failing tree kill is not caught": "PermissionError",
        "b2: a refused junit stops the run": "ValueError",
    }
    assert sum(not m.allow_crash and not m.crash_type for m in mm.M) == 19


def test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets():
    lines = []
    for m in mm.M:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        count = text.count(m.old)
        assert count == 1, f"{m.name}: the search string occurs {count} times in {m.file}"
        assert m.new != m.old, m.name
        lines.append(f"{m.name}: occurs once in {m.file}")
    assert len(lines) == 21
    print("\n".join(lines))  # shown by ``pytest -rP``

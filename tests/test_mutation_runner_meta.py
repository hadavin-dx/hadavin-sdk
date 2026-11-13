"""Meta-tests of the mutant list of the mutation runner: the list names real killers, and every search string is usable.

These tests read ``tests/mutation_runner_mutants.py`` (the mutants) and the files the mutants target. They are NOT in the test
list the mutants run against (a mutant tree holds only the runner's own test file), so they are checked on the real tree only.
Checks: (a) the list is the test placement table and every killer exists, (g) every search string occurs exactly once in the file it
targets; the script that runs the list exits 2 when its filter selects nothing.
"""

import ast
import subprocess
import sys
from pathlib import Path

from tests import mutation_runner_mutants as mm

ROOT = Path(__file__).resolve().parents[1]
RUNNER_TESTS = ROOT / "tests" / "test_mutation_runner.py"

# every test of the runner file (the first 21 came from an earlier version, with the refuses-paths test split one per guard; later fixes added
# the rest); the manifest test is the last function of the file and has no mutant
MOVED = (
    "test_mutation_judge_verdicts",
    "test_the_runner_kills_a_mutant_of_a_tiny_package",
    "test_a_mutant_path_that_is_absolute_or_names_a_drive_is_refused",
    "test_a_mutant_path_with_a_dotdot_part_is_refused",
    "test_a_mutant_path_with_a_stream_name_is_refused",
    "test_a_mutant_with_a_short_expect_is_refused",
    "test_inside_refuses_a_path_through_a_link_out_of_the_tree",
    "test_inside_refuses_the_tree_itself",
    "test_locate_does_not_list_a_file_link_out_of_the_tree",
    "test_locate_does_not_list_a_file_through_a_folder_link_out_of_the_tree",
    "test_the_runner_checks_a_forged_mutant_path_again",
    "test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree",
    "test_the_runner_children_see_an_allowlisted_environment_only",
    "test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant",
    "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
    "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
    "test_a_path_that_starts_with_a_dash_is_refused_in_both_grammars_and_dot_slash_is_the_way_out",
    "test_a_path_that_starts_with_an_at_sign_is_refused_because_pytest_reads_it_as_an_argument_file",
    "test_a_failing_tree_kill_still_kills_the_child",
    "test_the_baseline_run_gets_its_own_timeout",
    "test_a_baseline_timeout_of_zero_is_not_unset",
    "test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout",
    "test_a_timeout_kills_the_whole_process_tree_not_only_pytest",
    "test_an_interrupt_while_waiting_kills_the_run_and_is_not_swallowed",
    "test_a_background_process_left_by_a_finished_run_is_killed_too",
    "test_a_pytest_ini_planted_in_a_parent_folder_is_not_picked_up",
    "test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried",
    "test_the_runner_keeps_a_symlink_a_link",
    "test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs",
    "test_junit_with_a_doctype_or_entity_is_refused_not_parsed",
    "test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
    "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on",
    "test_a_junit_text_over_the_ceiling_is_refused",
    "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
    "test_the_leading_class_of_an_error_line_is_parsed_not_searched",
    "test_allow_crash_without_a_crash_type_is_refused",
    "test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on",
    "test_taskkill_is_resolved_under_system_root",
    "test_a_termination_signal_cleans_up_the_run",
    "test_the_signal_handlers_are_restored_and_an_ignored_sighup_stays_ignored",
    "test_a_refused_run_leaves_no_temp_folder",
    "test_the_first_lines_of_an_earlier_run_do_not_leak_into_the_next",
    "test_a_finished_run_does_not_kill_the_tree_on_windows",
    "test_a_signal_during_the_cleanup_does_not_cut_the_cleanup_short",
    "test_a_second_signal_cannot_cut_short_the_cleanup_of_the_first",
    "test_a_signal_while_the_child_is_being_started_still_kills_the_child",
    "test_a_signal_while_the_temp_folders_are_removed_leaves_none",
    "test_the_process_group_is_killed_while_its_leader_is_not_yet_reaped",
    "test_the_pytest_run_writes_no_file_into_its_working_folder_and_leaves_no_temp_folder",
    "test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not",
    "test_a_leader_reaped_by_someone_else_is_known_as_ended_so_its_group_is_not_signalled",
    "test_run_mutants_is_not_re_entrant_and_a_nested_call_leaves_the_outer_one_alone",
    "test_a_relative_link_that_points_out_of_the_tree_is_refused_at_snapshot_time",
    "test_a_junction_under_src_or_a_fixture_folder_is_refused_before_the_copy",
    "test_the_colon_refusal_says_a_path_may_not_contain_a_colon_and_the_docstring_states_it",
    "test_a_child_reaped_by_someone_else_is_an_error_result_not_exit_code_zero",
    "test_a_reaped_child_is_an_error_row_for_a_mutant",
    "test_a_reaped_baseline_is_refused_as_reaped_not_as_a_failing_baseline",
    "test_a_junction_as_the_folder_itself_or_a_part_of_its_path_is_refused",
    "test_a_junction_in_the_folder_part_of_an_extra_file_is_refused",
    "test_only_the_path_of_an_extra_file_that_exists_is_looked_at_for_a_junction",
)
EXPECTED_MUTANTS = 69
MANIFEST_TEST = "test_the_manifest_pins_the_files_a_demo_copies"


def _functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def _string_constants(path: Path, name: str) -> list[str]:
    """Every string constant in the function ``name`` of ``path`` (the parts of an f-string included)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    return [
        n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each():
    names = _functions(RUNNER_TESTS)
    tests = [n for n in names if n.startswith("test_")]
    assert len(tests) == len(set(tests)), (
        "a test name is defined twice: the first would be shadowed"
    )
    assert sorted(tests) == sorted((*MOVED, MANIFEST_TEST))
    assert tests[-1] == MANIFEST_TEST, "the manifest test stays last on purpose"


def test_a_there_are_the_listed_number_of_mutants_with_unique_names():
    names = [m.name for m in mm.M]
    assert len(names) == EXPECTED_MUTANTS and len(set(names)) == EXPECTED_MUTANTS, names
    assert {m.file for m in mm.M} == {mm.MU, mm.MR}
    assert sum(m.file == mm.MU for m in mm.M) == 6
    assert sum(m.file == mm.MR for m in mm.M) == EXPECTED_MUTANTS - 6


def test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists():
    defined = {}
    for m in mm.M:
        assert m.test_file and m.only_test, f"{m.name}: test_file and only_test are both required"
        path = ROOT / m.test_file
        assert path.is_file(), (m.name, m.test_file)
        defined.setdefault(m.test_file, _functions(path))
        assert m.only_test in defined[m.test_file], (m.name, m.only_test, "is not in", m.test_file)
        assert m.only_test in MOVED, (m.name, m.only_test, "is not one of the runner file's tests")
        # the judge looks for ``expect`` in the first E line only (not in the test id). A fragment of the killer's own name is
        # still forbidden, so a mutant that breaks another guard of the same test is never counted: ``expect`` must come from the
        # assertion message of the guard
        assert m.expect != m.only_test, (m.name, "expect is the killer's name")
        assert m.expect not in m.only_test, (m.name, "expect is a part of the killer's name")
        assert m.only_test not in m.expect, (m.name, "expect holds the killer's name")
        assert m.expect not in m.pinned, (m.name, "expect is a part of the pinned test id")
        # an ``expect`` that appears nowhere in the killer can never be matched by an assertion message: the mutant would not be
        # killed for the reason it names. The three crash mutants are the exception: their ``expect`` is the text of the exception
        # that the mutant raises (the reason is the class, which ``crash_type`` pins), not a message written in the test
        if not m.allow_crash:
            texts = _string_constants(path, m.only_test)
            assert any(m.expect in t for t in texts), (
                m.name,
                "expect is in no string of the killer",
            )
        # and every mutant pins its own killer, so another failing test is OTHER_TEST and not a kill
        assert m.pinned == mm.PIN + m.only_test, (m.name, m.pinned)


def test_a_the_three_crash_mutants_declare_their_exception_class_and_the_others_do_not():
    crash = {m.name: m.crash_type for m in mm.M if m.allow_crash}
    assert crash == {
        "runner: a failing tree kill is not caught": "PermissionError",
        "b2: a refused junit stops the run": "ValueError",
        "runner: a truncated junit stops the run": "ParseError",
    }
    assert sum(not m.allow_crash and not m.crash_type for m in mm.M) == EXPECTED_MUTANTS - 3


def test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets():
    lines = []
    for m in mm.M:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        count = text.count(m.old)
        assert count == 1, f"{m.name}: the search string occurs {count} times in {m.file}"
        assert m.new != m.old, m.name
        lines.append(f"{m.name}: occurs once in {m.file}")
    assert len(lines) == EXPECTED_MUTANTS
    print("\n".join(lines))  # shown by ``pytest -rP``


def test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant():
    script = ROOT / "tests" / "mutation_runner_mutants.py"
    done = subprocess.run(  # noqa: S603  # our own interpreter and a file of this repository, no shell
        [sys.executable, str(script), "no mutant has a name like this zzz"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert done.returncode == 2, (done.returncode, done.stdout[-200:], done.stderr[-200:])
    assert "nothing was run" in done.stderr

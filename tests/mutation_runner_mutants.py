"""The mutants of the mutation runner (``tools/mutation_runner.py``) and the judge (``hadavin_sdk.testing.mutation``).

Each mutant reverts ONE guard in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in
``only_test`` must fail, it must be the test pinned in ``pinned``, and the failing line must hold ``expect``: a fragment of the
assertion MESSAGE the test gives for that one guard (never the killer's own name, so a mutant that breaks another guard of the
same test is not counted: the meta-test forbids an ``expect`` that is part of the test name). Every mutant names both the file of
its killer (``test_file``) and the killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the
test placement table. Not collected by pytest. Run from the repo root:

    uv run python tests/mutation_runner_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/mutation_runner_mutants.py judge      # only mutants whose name contains the text

Good means KILLED, or CRASH with the declared exception class (three mutants declare one: ``allow_crash=True`` and ``crash_type``,
compared with the leading class name of the failing line).

Which mutants need what on Windows (this list is run on Linux and on Windows; the Windows run is the lead's):
- POSIX only: "a finished run's background process lives on" (its killer skips on Windows: ``taskkill /T`` walks parent links and
  the parent of a finished run is gone).
- Need the symlink privilege on Windows: "a symlink is copied as a file" and "a link out of the tree is listed" (a file link; the
  killers skip there, and only there, when the account lacks it, and a skipped killer makes the mutant SURVIVE in that run).
  The folder-link killer uses a junction on Windows, which needs no privilege.
- Every other killer runs on both systems (the tree-kill killers use ``taskkill /T`` on Windows).

Tests with no mutant (the guard is checked by the test only): the list-based path checks of ``run_mutants`` for tests and fixtures
(each is also checked again by ``_inside``, so a mutant that removes the first check is equivalent), the timeout and baseline
defaults, and the streaming of each result.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_mutation_runner.py"  # the file that holds every killer
PIN = "tests/test_mutation_runner::"  # the id prefix of a test in the JUnit file
MU = "src/hadavin_sdk/testing/mutation.py"
MR = "tools/mutation_runner.py"


def mutant(name, file, old, new, killer, expect, **kw):
    """One mutant: ``killer`` is the test that must fail first, with a line holding ``expect``."""
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer, **kw
    )


JUDGE = "test_mutation_judge_verdicts"
ABS = "test_a_mutant_path_that_is_absolute_or_names_a_drive_is_refused"
DOTDOT = "test_a_mutant_path_with_a_dotdot_part_is_refused"
INSIDE = "test_inside_refuses_a_path_through_a_link_out_of_the_tree"
LOCATE = "test_locate_does_not_list_a_file_through_a_link_out_of_the_tree"
FORGED = "test_the_runner_checks_a_forged_mutant_path_again"
CRASHROW = "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one"
TREE = "test_a_timeout_kills_the_whole_process_tree_not_only_pytest"
CRASH_OK = "crash_ok = v is Verdict.CRASH and m.allow_crash and declared"
TIMEOUT_TAIL = (
    "            # a mutant that loops forever is reported, never allowed to hang the run\n"
)

M = [
    mutant("judge: an exception line counts as a kill", MU,
        "return Verdict.KILLED if _ASSERTION.search(first_line.strip()) else Verdict.CRASH",
        "return Verdict.KILLED", JUDGE, "an exception line counted as a kill"),
    mutant("judge: crash markers ignored", MU, "for m in crash_markers:", "for m in ():",
        JUDGE, "a crash marker was ignored"),
    mutant("judge: short expect accepted", MU, "if expect is not None and len(expect) < 4:", "if False:",
        JUDGE, "a one-letter expect was accepted by the judge"),
    mutant("runner: crash counts as good", MR, CRASH_OK, "crash_ok = v is Verdict.CRASH",
        CRASHROW, "a crash row was good for another exception class"),
    mutant("runner: an absolute path is accepted", MR,
        '        if pure.is_absolute() or pure.anchor or pure.drive or ".." in pure.parts:',
        '        if ".." in pure.parts:', ABS, "an absolute, drive or empty mutant path"),
    mutant("runner: a dotdot part is accepted", MR,
        '        if pure.is_absolute() or pure.anchor or pure.drive or ".." in pure.parts:',
        "        if pure.is_absolute() or pure.anchor or pure.drive:",
        DOTDOT, "a mutant path with a dotdot part"),
    mutant("runner: a link out of the tree is accepted", MR,
        "    if path == root or not path.is_relative_to(root):", "    if False:",
        INSIDE, "a path through a link out of the tree"),
    mutant("runner: the mutant file is not checked again", MR,
        "            p = _locate(tmp, m.file)", "            p = tmp / m.file",
        FORGED, "a forged mutant path"),
    mutant("runner: a short expect is accepted", MR, "        if len(self.expect) < 4:", "        if False:",
        "test_a_mutant_with_a_short_expect_is_refused", "an expect of three characters"),
    mutant("runner: a timeout is reported as an exit code", MR, TIMEOUT_TAIL + "            return TIMED_OUT",
        "            return 1", "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
        "a timeout was not reported as one"),
    mutant("runner: a dash path is an option", MR, '"--", *tests', "*tests",
        "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
        "a test path with a dash was taken as a pytest option"),
    mutant("runner: the mutant file is joined as a path", MR,
        "            p = _locate(tmp, m.file)", "            p = Path(tmp) / m.file",
        FORGED, "a forged mutant path"),
    mutant("runner: a link out of the tree is listed", MR,
        "            if os.path.commonpath([real_base, real_full]) == real_base:", "            if True:",
        LOCATE, "a file link out of the tree was listed"),
    mutant("runner: a timeout leaves the grandchildren running", MR,
        "            _kill_tree(proc)\n" + TIMEOUT_TAIL, "            proc.kill()\n" + TIMEOUT_TAIL,
        TREE, "the grandchild survived the timeout"),
    # Both kill paths of the killer raise ``PermissionError`` (``os.killpg`` on POSIX, the faked ``taskkill`` call on Windows), so
    # the declared crash class is the same on both systems.
    mutant("runner: a failing tree kill is not caught", MR,
        "    except (OSError, subprocess.TimeoutExpired):\n        pass\n",
        "    except ZeroDivisionError:\n        pass\n",
        "test_a_failing_tree_kill_still_kills_the_child", "PermissionError",
        allow_crash=True, crash_type="PermissionError"),
    mutant("runner: the baseline timeout is ignored", MR,
        "timeout if baseline_timeout is None else baseline_timeout", "timeout",
        "test_the_baseline_run_gets_its_own_timeout", "the baseline run did not get its own timeout"),
    mutant("fix: junit with a DOCTYPE is parsed", MU, 'if "<!doctype" in low or "<!entity" in low:', "if False:",
        "test_junit_with_a_doctype_or_entity_is_refused_not_parsed", "a JUnit file with a DOCTYPE was parsed"),
    mutant("fix: the runner drops pinned", MR, "pinned=m.pinned or None", "pinned=None",
        "test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
        "pinned was dropped: another failing test was not OTHER_TEST"),
    mutant("b2: a refused junit stops the run", MR, "except JUNIT_REFUSED:", "except KeyError:",
        "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on", "ValueError: refused",
        allow_crash=True, crash_type="ValueError"),
    mutant("b2: the junit has no size ceiling", MU, "if len(xml_text) > MAX_JUNIT_CHARS:", "if False:",
        "test_a_junit_text_over_the_ceiling_is_refused", "a JUnit text over the size ceiling was parsed"),
    mutant("b3: a crash row is good whatever the exception", MR, CRASH_OK,
        "crash_ok = v is Verdict.CRASH and m.allow_crash",
        CRASHROW, "a crash row was good for another exception class"),
    # ---- guards of the moved tests that had no mutant, and the guards added by the fixes of the first result review
    mutant("runner: the child inherits the whole environment", MR,
        "env = {k: os.environ[k] for k in CHILD_ENV if k in os.environ}", "env = dict(os.environ)",
        "test_the_runner_children_see_an_allowlisted_environment_only",
        "a secret of the caller reached the child process"),
    mutant("runner: a later mutant is built from the live tree", MR,
        'shutil.copytree(snap / "src", tmp / "src", symlinks=True)',
        'shutil.copytree(root / "src", tmp / "src", symlinks=True)',
        "test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant",
        "an edit of the tree during the run leaked into a later mutant"),
    mutant("runner: the mutation is not applied", MR,
        'p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\\n")',
        'p.write_text(text, encoding="utf-8", newline="\\n")',
        "test_the_runner_kills_a_mutant_of_a_tiny_package",
        "a mutant of a tiny package was not killed as expected"),
    mutant("runner: a timeout code equals SIGKILL", MR, "TIMED_OUT = -1000", "TIMED_OUT = -9",
        "test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout",
        "TIMED_OUT equals a process exit status"),
    mutant("runner: a setup failure is not retried", MR, "SETUP_TRIES = 5", "SETUP_TRIES = 1",
        "test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried",
        "or a blip was not retried"),
    mutant("runner: a symlink is copied as a file", MR,
        'symlinks=True, ignore=shutil.ignore_patterns("__pycache__")',
        'symlinks=False, ignore=shutil.ignore_patterns("__pycache__")',
        "test_the_runner_keeps_a_symlink_a_link", "a symlink of the package was copied as a plain file"),
    mutant("runner: a test_file outside the copied tests is accepted", MR,
        "if m.test_file and m.test_file not in tests:", "if False:",
        "test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs",
        "a test_file that is not among the copied tests"),
    mutant("runner: allow_crash without a crash_type is accepted", MR,
        "if self.allow_crash and not self.crash_type.isidentifier():", "if False:",
        "test_allow_crash_without_a_crash_type_is_refused", "allow_crash without a crash_type"),
    mutant("runner: a truncated junit stops the run", MR,
        "JUNIT_REFUSED = (ValueError, SyntaxError)", "JUNIT_REFUSED = (ValueError,)",
        "test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on", "no element found",
        allow_crash=True, crash_type="ParseError"),
    mutant("runner: taskkill is not taken from System32", MR,
        'str(Path(root) / "System32" / "taskkill.exe")', 'str(Path(root) / "taskkill.exe")',
        "test_taskkill_is_resolved_under_system_root",
        "taskkill was not run from System32"),
    mutant("runner: an interrupt leaves the run going", MR, "except BaseException:", "except ZeroDivisionError:",
        "test_an_interrupt_while_waiting_kills_the_run_and_is_not_swallowed",
        "an interrupt while waiting did not kill the run before it propagated"),
    mutant("runner: a finished run's background process lives on", MR,
        "        # a normal exit can leave a background process of the run behind: it is killed too\n        _kill_tree(proc)\n",
        "", "test_a_background_process_left_by_a_finished_run_is_killed_too",
        "a background process of a finished run was left running"),
    mutant("runner: a planted pytest.ini is picked up", MR,
        '"-x", "-c", str(ini), f"--rootdir={cwd}", ', '"-x", ',
        "test_a_pytest_ini_planted_in_a_parent_folder_is_not_picked_up",
        "a pytest.ini planted in a parent folder was picked up"),
    mutant("runner: a baseline timeout of 0 is unset", MR,
        "timeout if baseline_timeout is None else baseline_timeout", "baseline_timeout or timeout",
        "test_a_baseline_timeout_of_zero_is_not_unset", "a baseline_timeout of 0 was treated as unset"),
    mutant("runner: a crash class is matched as a substring", MR,
        "declared = _leading_class(first) == m.crash_type", "declared = m.crash_type in first",
        CRASHROW, "a crash row was good for a lookalike class name"),
    mutant("runner: a stream name is accepted", MR, '    if ":" in rel:', "    if False:",
        "test_a_mutant_path_with_a_stream_name_is_refused", "a mutant path with a stream name"),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]

    def show(
        row,
    ):  # one line per mutant, as soon as it finishes: a timeout of the whole run still leaves a kill list
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            import tools.mutation_runner as _mr

            print("      first line:", _mr.FIRST_LINES.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)

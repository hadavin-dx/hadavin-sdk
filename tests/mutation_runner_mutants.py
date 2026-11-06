"""The 21 mutants of the mutation runner (``tools/mutation_runner.py``) and the judge (``hadavin_sdk.testing.mutation``).

Each mutant reverts ONE guard in a temp copy of the package (``tools.mutation_runner`` does the copy) and the test named in
``only_test`` must fail for the reason named in ``expect``. Every mutant names both the file of its killer (``test_file``) and the
killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the test placement table. Not collected by
pytest. Run from the repo root:

    uv run python tests/mutation_runner_mutants.py            # all 21 mutants; exit 1 if any is not good
    uv run python tests/mutation_runner_mutants.py judge      # only mutants whose name contains the text

Good means KILLED, or CRASH with the declared exception class (two mutants declare one: ``allow_crash=True`` and ``crash_type``).
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_mutation_runner.py"  # the file that holds every killer
MU = "src/hadavin_sdk/testing/mutation.py"
MR = "tools/mutation_runner.py"

M = [
    Mutant(
        "judge: an exception line counts as a kill",
        MU,
        "return Verdict.KILLED if _ASSERTION.search(first_line.strip()) else Verdict.CRASH",
        "return Verdict.KILLED",
        "test_mutation_judge_verdicts",
        test_file=TEST,
        only_test="test_mutation_judge_verdicts",
    ),
    Mutant(
        "judge: crash markers ignored",
        MU,
        "for m in crash_markers:",
        "for m in ():",
        "test_mutation_judge_verdicts",
        test_file=TEST,
        only_test="test_mutation_judge_verdicts",
    ),
    Mutant(
        "judge: short expect accepted",
        MU,
        "if expect is not None and len(expect) < 4:",
        "if False:",
        "test_mutation_judge_verdicts",
        test_file=TEST,
        only_test="test_mutation_judge_verdicts",
    ),
    Mutant(
        "runner: crash counts as good",
        MR,
        "crash_ok = v is Verdict.CRASH and m.allow_crash and m.crash_type in first",
        "crash_ok = v is Verdict.CRASH",
        "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
        test_file=TEST,
        only_test="test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
    ),
    Mutant(
        "runner: an absolute path is accepted",
        MR,
        '        if pure.is_absolute() or pure.anchor or pure.drive or ".." in pure.parts:',
        '        if ".." in pure.parts:',
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a dotdot part is accepted",
        MR,
        '        if pure.is_absolute() or pure.anchor or pure.drive or ".." in pure.parts:',
        "        if pure.is_absolute() or pure.anchor or pure.drive:",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a link out of the tree is accepted",
        MR,
        "    if path == root or not path.is_relative_to(root):",
        "    if False:",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: the mutant file is not checked again",
        MR,
        "            p = _locate(tmp, m.file)",
        "            p = tmp / m.file",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a short expect is accepted",
        MR,
        "        if len(self.expect) < 4:",
        "        if False:",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a timeout is reported as an exit code",
        MR,
        "            # a mutant that loops forever is reported, never allowed to hang the run\n            return TIMED_OUT",
        "            return 1",
        "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
        test_file=TEST,
        only_test="test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
    ),
    Mutant(
        "runner: a dash path is an option",
        MR,
        '"--", *tests',
        "*tests",
        "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
        test_file=TEST,
        only_test="test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
    ),
    Mutant(
        "runner: the mutant file is joined as a path",
        MR,
        "            p = _locate(tmp, m.file)",
        "            p = Path(tmp) / m.file",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a link out of the tree is listed",
        MR,
        "            if os.path.commonpath([real_base, real_full]) == real_base:",
        "            if True:",
        "test_the_runner_refuses_paths_that_leave_its_tree",
        test_file=TEST,
        only_test="test_the_runner_refuses_paths_that_leave_its_tree",
    ),
    Mutant(
        "runner: a timeout leaves the grandchildren running",
        MR,
        "            _kill_tree(proc)\n",
        "            proc.kill()\n",
        "test_a_timeout_kills_the_whole_process_tree_not_only_pytest",
        test_file=TEST,
        only_test="test_a_timeout_kills_the_whole_process_tree_not_only_pytest",
    ),
    # On Linux the killer makes ``os.killpg`` raise ``PermissionError`` (the branch for a missing ``taskkill``, which would show
    # ``FileNotFoundError``, runs only on Windows), so the declared crash class is the one the kill shows here.
    Mutant(
        "runner: a failing tree kill is not caught",
        MR,
        "    except (OSError, subprocess.TimeoutExpired):\n        pass\n",
        "    except ZeroDivisionError:\n        pass\n",
        "PermissionError",
        allow_crash=True,
        crash_type="PermissionError",
        test_file=TEST,
        only_test="test_a_failing_tree_kill_still_kills_the_child",
    ),
    Mutant(
        "runner: the baseline timeout is ignored",
        MR,
        "baseline_timeout or timeout",
        "timeout",
        "test_the_baseline_run_gets_its_own_timeout",
        test_file=TEST,
        only_test="test_the_baseline_run_gets_its_own_timeout",
    ),
    Mutant(
        "fix: junit with a DOCTYPE is parsed",
        MU,
        'if "<!doctype" in low or "<!entity" in low:',
        "if False:",
        "test_junit_with_a_doctype_or_entity_is_refused_not_parsed",
        test_file=TEST,
        only_test="test_junit_with_a_doctype_or_entity_is_refused_not_parsed",
    ),
    Mutant(
        "fix: the runner drops pinned",
        MR,
        "pinned=m.pinned or None",
        "pinned=None",
        "test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
        test_file=TEST,
        only_test="test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
    ),
    Mutant(
        "b2: a refused junit stops the run",
        MR,
        "except JUNIT_REFUSED:",
        "except KeyError:",
        "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on",
        allow_crash=True,
        crash_type="ValueError",
        test_file=TEST,
        only_test="test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on",
    ),
    Mutant(
        "b2: the junit has no size ceiling",
        MU,
        "if len(xml_text) > MAX_JUNIT_CHARS:",
        "if False:",
        "test_a_junit_text_over_the_ceiling_is_refused",
        test_file=TEST,
        only_test="test_a_junit_text_over_the_ceiling_is_refused",
    ),
    Mutant(
        "b3: a crash row is good whatever the exception",
        MR,
        "crash_ok = v is Verdict.CRASH and m.allow_crash and m.crash_type in first",
        "crash_ok = v is Verdict.CRASH and m.allow_crash",
        "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
        test_file=TEST,
        only_test="test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
    ),
]


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

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
compared with the leading class name of the failing line). The script exits 1 if any mutant is not good, and 2 if the filter
selects no mutant at all (a typo in the filter must not look like a pass).

Which mutants need what on Windows (this list is run on Linux and on Windows; the Windows run is made by whoever has a Windows machine):
- POSIX only (the killer skips on Windows, so the mutant SURVIVES there): "a finished run's background process lives on"
  (``taskkill /T`` walks parent links and the parent of a finished run is gone), "a termination signal does not clean up",
  "a signal during the cleanup cuts it short", "a second signal cuts the cleanup of the first short", "a signal while the child
  starts orphans it" and "a signal while the temp folders go leaves one" (SIGTERM and SIGHUP are POSIX signals), and "the group is
  killed after its leader was reaped" (``os.waitid`` is POSIX).
- Need the symlink privilege on Windows: "a symlink is copied as a file" and "a link out of the tree is listed" (both killers make a
  FILE link; they skip there, and only there (error 1314), when the account lacks the privilege, and a skipped killer makes the
  mutant SURVIVE in that run). The folder-link case (a junction on Windows, no privilege needed) is a separate test with no mutant:
  on Linux ``os.walk`` never enters a symlinked folder, so that test cannot tell the mutant from the original there.
- Every other killer runs on both systems (the tree-kill killers use ``taskkill /T`` on Windows; the Windows branch after a normal
  exit is run on any system with the Windows flag faked).

Tests with no mutant (the guard is checked by the test only; names as in ``tests/test_mutation_runner.py``):
- ``test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree``: the list-based path checks of ``run_mutants`` for tests
  and fixtures (each is also checked again by ``_inside``, so a mutant that removes the first check is equivalent). The same holds
  for the dash and at-sign refusal of a fixture folder (``extra_dirs`` never reaches the argv; ``_relative`` is called again by ``_inside``).
- ``test_a_refused_run_leaves_no_temp_folder`` (the place of the ``try``), ``test_the_signal_handlers_are_restored_and_an_ignored_sighup_stays_ignored``
  (restore of the old handlers) and ``test_locate_does_not_list_a_file_through_a_folder_link_out_of_the_tree`` (see above).
- ``test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout``: only the ``TIMED_OUT`` constant has a mutant;
  the in-order streaming of each result is checked by the test only.
- ``test_the_manifest_pins_the_files_a_demo_copies``: a hash pin, by design not mutated.
- The tests of the Windows probe helpers in ``tests/test_mutation_runner_helpers.py`` (they test test helpers, not the runner).
- The default ``baseline_timeout`` fallback (the baseline gets the mutant timeout when none is given) is covered only together
  with the "baseline timeout is ignored" mutant, which replaces the whole expression.
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
LOCATE = "test_locate_does_not_list_a_file_link_out_of_the_tree"
TINY = "test_the_runner_kills_a_mutant_of_a_tiny_package"
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
        TINY, "was counted as a good kill"),
    mutant("runner: an absolute path is accepted", MR,
        '        if pure.is_absolute() or pure.anchor or ".." in pure.parts:',
        '        if ".." in pure.parts:', ABS, "an absolute, drive or empty mutant path"),
    mutant("runner: a dotdot part is accepted", MR,
        '        if pure.is_absolute() or pure.anchor or ".." in pure.parts:',
        "        if pure.is_absolute() or pure.anchor:",
        DOTDOT, "a mutant path with a dotdot part"),
    mutant("runner: a link out of the tree is accepted", MR,
        "    if path == root or not path.is_relative_to(root):", "    if False:",
        INSIDE, "a path through a link out of the tree"),
    mutant("runner: the mutant file is not checked again", MR,
        "            p = _locate(tmp, m.file)", "            p = tmp / m.file",
        FORGED, "a forged mutant path"),
    mutant("runner: the tree itself is accepted as a file", MR,
        "    if path == root or not path.is_relative_to(root):", "    if not path.is_relative_to(root):",
        "test_inside_refuses_the_tree_itself", "the tree itself was accepted"),
    mutant("runner: a short expect is accepted", MR, "        if len(self.expect) < 4:", "        if False:",
        "test_a_mutant_with_a_short_expect_is_refused", "an expect of three characters"),
    mutant("runner: a timeout is reported as an exit code", MR, TIMEOUT_TAIL + "            return TIMED_OUT",
        "            return 1", "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
        "a timeout was not reported as one"),
    mutant("runner: a dash path reaches the pytest argv", MR,
        "    for operand in tests:  # the one place", "    for operand in ():  # the one place",
        "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
        "a test path with a dash or an at sign reached the pytest argv"),
    mutant("runner: a dash path is accepted as a relative path", MR,
        '    if arg.startswith(("-", "@")):', '    if arg.startswith(("@",)):',
        "test_a_path_that_starts_with_a_dash_is_refused_in_both_grammars_and_dot_slash_is_the_way_out",
        "a path that starts with a dash was accepted"),
    mutant("runner: an at-sign path is accepted", MR,
        '    if arg.startswith(("-", "@")):', '    if arg.startswith(("-",)):',
        "test_a_path_that_starts_with_an_at_sign_is_refused_because_pytest_reads_it_as_an_argument_file",
        "a path that starts with an at sign was accepted"),
    mutant("runner: a leader reaped by someone else stays unknown", MR,
        "            proc.poll()  # sets returncode (0, a guess) so ``_kill_tree`` will not signal a reaped group\n            raise", "            raise",
        "test_a_leader_reaped_by_someone_else_is_known_as_ended_so_its_group_is_not_signalled",
        "the reaped leader was still unknown to its Popen object"),
    mutant("runner: a child reaped by someone else is read as exit code 0", MR,
        "            raise _ReapedElsewhere from None\n", "            return\n",
        "test_a_child_reaped_by_someone_else_is_an_error_result_not_exit_code_zero",
        "a child reaped by someone else was read as exit code 0"),
    mutant("runner: a reaped mutant run is not an error row", MR,
        "            if rc == REAPED_ELSEWHERE:", "            if False:",
        "test_a_reaped_child_is_an_error_row_for_a_mutant",
        "a mutant run reaped by someone else was not an error row"),
    mutant("runner: a junction under src is copied", MR,
        '        _refuse_junctions(root, "src")\n', "",
        "test_a_junction_under_src_or_a_fixture_folder_is_refused_before_the_copy",
        "a junction under src was copied"),
    mutant("runner: the folder itself is not asked about junctions", MR,
        "        if isjunction(here):", "        if False:",
        "test_a_junction_as_the_folder_itself_or_a_part_of_its_path_is_refused",
        "the src folder itself was a junction and was copied"),
    mutant("runner: only the last part of a path is asked about junctions", MR,
        "        if isjunction(here):", '        if isjunction(here) and part == rel.split("/")[-1]:',
        "test_a_junction_as_the_folder_itself_or_a_part_of_its_path_is_refused",
        "a junction in the middle of a fixture path was copied"),
    mutant("runner: a reaped baseline is reported as a failing baseline", MR,
        "        if base_rc == REAPED_ELSEWHERE:", "        if False:",
        "test_a_reaped_baseline_is_refused_as_reaped_not_as_a_failing_baseline",
        "a reaped baseline was not named as reaped"),
    mutant("runner: a junction in a fixture folder is copied", MR,
        "                _refuse_junctions(root, d)\n", "",
        "test_a_junction_under_src_or_a_fixture_folder_is_refused_before_the_copy",
        "a junction in a fixture folder was copied"),
    mutant("runner: the colon refusal gives the old message", MR,
        "raise ValueError(f\"a path may not contain ':': {rel!r}\")", "raise ValueError(f\"path escapes its tree: {rel!r}\")",
        "test_the_colon_refusal_says_a_path_may_not_contain_a_colon_and_the_docstring_states_it",
        "the colon message for a stream name"),
    mutant("runner: a nested run_mutants call is accepted", MR,
        '    if _SIGNALS["active"]:\n        raise RuntimeError(', '    if False:\n        raise RuntimeError(',
        "test_run_mutants_is_not_re_entrant_and_a_nested_call_leaves_the_outer_one_alone",
        "a nested run_mutants call was not refused"),
    mutant("runner: a relative link out of the tree is copied", MR,
        "        _refuse_links_out(snap)\n", "",
        "test_a_relative_link_that_points_out_of_the_tree_is_refused_at_snapshot_time",
        "a relative link out of the tree was copied"),
    mutant("runner: a link out of the tree is listed", MR,
        "            if os.path.commonpath([real_base, real_full]) == real_base:", "            if True:",
        LOCATE, "a file link out of the tree was listed"),
    mutant("runner: a timeout leaves the grandchildren running", MR,
        "            _kill_tree(proc)\n" + TIMEOUT_TAIL, "            proc.kill()\n" + TIMEOUT_TAIL,
        TREE, "the grandchild survived the timeout"),
    # Both kill paths of the killer raise ``PermissionError`` (``os.killpg`` on POSIX, the faked ``taskkill`` call on Windows), so
    # the declared crash class is the same on both systems.
    mutant("runner: a failing tree kill is not caught", MR,
        "        except (OSError, subprocess.TimeoutExpired):\n            pass\n",
        "        except ZeroDivisionError:\n            pass\n",
        "test_a_failing_tree_kill_still_kills_the_child", "PermissionError",
        allow_crash=True, crash_type="PermissionError"),
    mutant("runner: the baseline timeout is ignored", MR,
        "timeout if baseline_timeout is None else baseline_timeout", "timeout",
        "test_the_baseline_run_gets_its_own_timeout", "the baseline run did not get its own timeout"),
    mutant("judge: an expect found in the test id is accepted", MU,
        "if expect and expect not in first_line:",
        "if expect and expect not in test_id and expect not in first_line:",
        JUDGE, "an expect found only in the test id was accepted"),
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
    # ---- guards of the moved tests that had no mutant, and the guards added by later fixes
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
    mutant("runner: a link named in extra_files is copied as the file it points to", MR,
        "if not _through_a_link(root, f) and _inside(root, f).is_file():",
        "if _inside(root, f).is_file() and not _inside(root, f).is_symlink():",
        "test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not",
        "a link named in extra_files was copied"),
    mutant("runner: a link to a file outside the tree is asked about after it is resolved", MR,
        "if not _through_a_link(root, f) and _inside(root, f).is_file():",
        "if _inside(root, f).is_file() and not _through_a_link(root, f):",
        "test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not",
        "a link to a file outside the tree named in extra_files refused the run"),
    mutant("runner: a junction in the folder part of an extra file is not refused", MR,
        "                _refuse_junctions(root, f)\n",
        "                pass\n",
        "test_a_junction_in_the_folder_part_of_an_extra_file_is_refused",
        "a junction in the folder part of an extra file was copied"),
    mutant("runner: an extra file walks its whole folder for a junction", MR,
        "                _refuse_junctions(root, f)\n",
        "                _refuse_junctions(root, Path(f).parent.as_posix())\n",
        "test_only_the_path_of_an_extra_file_that_exists_is_looked_at_for_a_junction",
        "an extra file was refused for a junction beside its path"),
    mutant("runner: a missing extra file is looked at for a junction", MR,
        "            if not _through_a_link(root, f) and _inside(root, f).is_file():\n                # only",
        "            _refuse_junctions(root, f)\n            if not _through_a_link(root, f) and _inside(root, f).is_file():\n                # only",
        "test_only_the_path_of_an_extra_file_that_exists_is_looked_at_for_a_junction",
        "a missing extra file under a junction refused the run"),
    mutant("runner: a file behind a folder link named in extra_files is copied", MR,
        "    for part in Path(rel).parts:\n        path = path / part\n",
        "    for part in Path(rel).parts[-1:]:\n        path = path / part\n",
        "test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not",
        "a file behind a folder link named in extra_files was copied"),
    mutant("runner: the copy of a mutant makes no folder for a file of extra_files", MR,
        "                _inside(tmp, f).parent.mkdir(parents=True, exist_ok=True)\n",
        "",
        "test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not",
        "a nested extra file made the copy fail"),
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
        "        # a normal exit can leave a background process of the run behind: on POSIX it is killed too. Not on Windows: the parent is\n"
        "        # gone, taskkill /T finds no children, and the pid may already belong to an unrelated process\n"
        "        if not _IS_WINDOWS:\n            _kill_tree(proc)\n",
        "", "test_a_background_process_left_by_a_finished_run_is_killed_too",
        "a background process of a finished run was left running"),
    mutant("runner: a finished run's tree is killed on Windows too", MR,
        "        if not _IS_WINDOWS:\n            _kill_tree(proc)\n", "        if True:\n            _kill_tree(proc)\n",
        "test_a_finished_run_does_not_kill_the_tree_on_windows", "the tree was killed after a normal exit on Windows"),
    mutant("runner: a termination signal does not clean up", MR,
        '_TERMINATING = ("SIGTERM", "SIGHUP")', "_TERMINATING = ()",
        "test_a_termination_signal_cleans_up_the_run", "did not end through its"),
    mutant("runner: the first lines of an earlier run are kept", MR,
        "    first_lines.clear()  # the diagnostics of an earlier run must not answer for this one", "    pass",
        "test_the_first_lines_of_an_earlier_run_do_not_leak_into_the_next",
        "the diagnostics of an earlier run were kept"),
    mutant("runner: the E marker is cut as a letter", MR,
        '    head = re.sub(r"^E\\s+", "", first.strip()).split(":", 1)[0].strip()',
        '    head = first.strip().removeprefix("E").strip().split(":", 1)[0].strip()',
        "test_the_leading_class_of_an_error_line_is_parsed_not_searched", "the first letter of EOFError was cut off"),
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
    # ---- review round 3: pid reuse, signals during the cleanup, the ini file
    mutant("runner: the group is killed after its leader was reaped", MR,
        "os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None", "os.WEXITED | os.WNOHANG) is not None",
        "test_the_process_group_is_killed_while_its_leader_is_not_yet_reaped",
        "after its leader was reaped"),
    mutant("runner: a signal during the cleanup cuts it short", MR,
        '        if _SIGNALS["depth"] or _SIGNALS["ended"]:', '        if _SIGNALS["ended"]:',
        "test_a_signal_during_the_cleanup_does_not_cut_the_cleanup_short",
        "a signal during the cleanup cut it short"),
    mutant("runner: a second signal cuts the cleanup of the first short", MR,
        '        if _SIGNALS["depth"] or _SIGNALS["ended"]:', '        if _SIGNALS["depth"]:',
        "test_a_second_signal_cannot_cut_short_the_cleanup_of_the_first",
        "a second signal cut the cleanup short"),
    mutant("runner: a signal while the child starts orphans it", MR,
        "``proc`` is known, then raised inside this ``try``: the child is killed\n        with _signals_held():\n",
        "``proc`` is known, then raised inside this ``try``: the child is killed\n        if True:\n",
        "test_a_signal_while_the_child_is_being_started_still_kills_the_child",
        "left the child running"),
    mutant("runner: a signal while the temp folders go leaves one", MR,
        "        with _signals_held():  # a signal is raised after the removal\n",
        "        if True:  # a signal is raised after the removal\n",
        "test_a_signal_while_the_temp_folders_are_removed_leaves_none", "left a temp folder behind"),
    mutant("runner: the ini file is written into the working folder", MR,
        '        ini = ini_dir / "mutant_run.ini"', '        ini = cwd / "mutant_run.ini"',
        "test_the_pytest_run_writes_no_file_into_its_working_folder_and_leaves_no_temp_folder",
        "written into the working folder"),
    mutant("runner: the folder of the ini file is left behind", MR,
        "                shutil.rmtree(ini_dir, ignore_errors=True)", "                pass",
        "test_the_pytest_run_writes_no_file_into_its_working_folder_and_leaves_no_temp_folder",
        "was left behind"),
]  # fmt: skip


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

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

    first_lines = {}
    res = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)

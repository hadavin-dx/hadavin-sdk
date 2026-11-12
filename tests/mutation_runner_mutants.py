"""The mutants of the mutation runner (``tools/mutation_runner.py``) and the judge (``hadavin_sdk.testing.mutation``).

Each mutant reverts ONE guard in a temp copy of the package (``tools.mutation_runner`` does the copy). The test named in
``only_test`` must fail, it must be the test pinned in ``pinned``, and the failing line must hold ``expect``: a fragment of the
assertion MESSAGE the test gives for that one guard (never the killer's own name, so a mutant that breaks another guard of the
same test is not counted: the meta-test forbids an ``expect`` that is part of the test name). Every mutant names both the file of
its killer (``test_file``) and the killer itself (``only_test``), so no verdict depends on the order of the test list. This list is the
test placement table. Not collected by pytest. Run from the repo root:

    uv run python tests/mutation_runner_mutants.py            # all mutants; exit 1 if any is not good
    uv run python tests/mutation_runner_mutants.py judge      # only mutants whose name contains the text

Good means KILLED, or CRASH with the declared exception class (four mutants declare one: ``allow_crash=True`` and ``crash_type``,
compared with the leading class name of the failing line). The script exits 1 if any mutant is not good, and 2 if the filter
selects no mutant at all (a typo in the filter must not look like a pass).

Which mutants need what on Windows (only Linux is run in CI; nobody has run this list on Windows, so the notes below are written from the skip markers of the killers, not from a Windows run):
- POSIX only (the killer skips on Windows, so the mutant SURVIVES there): "a finished run's background process lives on"
  (``taskkill /T`` walks parent links and the parent of a finished run is gone), "a termination signal does not clean up",
  "a signal during the cleanup cuts it short", "a second signal cuts the cleanup of the first short", "a signal while the child
  starts orphans it" and "a signal while the temp folders go leaves one" (SIGTERM and SIGHUP are POSIX signals), and "the group is
  killed after its leader was reaped" (``os.waitid`` is POSIX). The lock-file killers of the keyword tests are POSIX only too: "any lock
  failure is called another run" (``flock``), "a lock file that is a symbolic link is followed" and "the lock file is open to others"
  (links and file modes), "a lock file with a wide mode is accepted" (modes), "a lock file of another user is accepted" (owners), "a lock folder that others can enter is accepted" (modes), "a lock
  file with two names is accepted" (hard links), "a lock file that is not a regular file is accepted" (modes), "the lock file is opened for
  writing on POSIX" (Windows needs write access to lock a byte) and "a FIFO lock file blocks the open" (named pipes),
  the lock-folder killers "a lock folder of another user is accepted", "what was opened as the lock folder is not checked to be a folder",
  "the lock folder is opened without the folder and no-link flags" and "the lock file is opened by its path, not under the opened folder"
  (Windows has no lock folder of its own: the lock file lies in the temp folder),
  also "a leader reaped by someone else stays unknown" and "a child reaped by someone else is read as exit code 0" (both killers skip on
  win32 or without ``waitid``), "a nested run_mutants call is accepted" (its killer skips on win32).
  (Two more mutants that survive on Windows are in none of these two kinds of list: their killers drop a case by the system name. See the third list below.)
- Need the symlink privilege on Windows: "a relative link out of the tree is copied", "a symlink is copied as a file" and "a link out of the tree is listed" (both killers make a
  FILE link; they skip there, and only there (error 1314), when the account lacks the privilege, and a skipped killer makes the
  mutant SURVIVE in that run). The folder-link case (a junction on Windows, no privilege needed) is a separate test with no mutant:
  on Linux ``os.walk`` never enters a symlinked folder, so that test cannot tell the mutant from the original there.
- Named in the second list below although it NEVER skips: "a link out of the tree is accepted". Its killer links a FOLDER through the helper ``_dir_link``, which makes a
  junction on Windows and calls ``_symlink_or_skip`` elsewhere; that helper skips only on Windows with error 1314, and on Windows ``_dir_link`` does not call it. So the skip
  cannot fire for this killer on any system, and the mutant is killed everywhere. The name is in the list only because the test that reads the skips follows a helper of
  the same file without looking at the system. ``test_the_folder_link_killer_never_skips_and_the_header_says_so`` in ``tests/test_mutation_runner_meta.py`` guards this sentence.
- Killers that skip through a MARK (``posix_only``, or ``skipif`` on ``sys.platform`` or ``os.name``): the mutants below SURVIVE on Windows. This list is
  derived, not typed: ``tests/test_mutation_runner_meta.py`` reads the decorators of every killer and fails when the list between the two marker
  lines differs from what it reads. A condition of a ``skipif`` that the reader cannot evaluate, and a decorator it cannot read, are errors of that test,
  never "no skip"; the module-level ``pytestmark`` of a test file is read too.
POSIX-ONLY-MUTANTS-BEGIN
runner: a leader reaped by someone else stays unknown
runner: a child reaped by someone else is read as exit code 0
runner: a nested run_mutants call is accepted
runner: a finished run's background process lives on
runner: a termination signal does not clean up
runner: the group is killed after its leader was reaped
runner: a signal during the cleanup cuts it short
runner: a second signal cuts the cleanup of the first short
runner: a signal while the child starts orphans it
runner: a signal while the temp folders go leaves one
runner: a lock folder that others can enter is accepted
runner: a private XDG_RUNTIME_DIR is not used for the lock folder
runner: a link to a private folder counts as a private folder
runner: the error for an unusable baseline result file is raised inside the except block
runner: a lock folder of another user is accepted
runner: what was opened as the lock folder is not checked to be a folder
runner: the lock folder is opened without the folder and no-link flags
runner: the lock file is opened by its path, not under the opened folder
runner: the temp folder is removed and made again at a rebuild
runner: the temp folder is not checked before a rebuild empties it
runner: the temp folder is not checked after a rebuild
runner: the snapshot folder is made without the private helper
runner: the snapshot folder is not checked after the copy
runner: the folder of the settings file is not checked
runner: the settings file is made by the umask
runner: the result file is made by the umask
runner: a folder check uses stat and follows a link
runner: a folder check never raises
runner: a folder that cannot be looked at is accepted
runner: a private folder is not put back to 0700
runner: a private folder is made without the mode
runner: a private folder is not checked after it is made
runner: the parts between are made with the default mode
runner: a file in the way of a part is accepted
runner: emptying a folder follows a link
runner: emptying a folder removes the folder
runner: a private file is not put back to 0600
runner: a private file is not emptied
runner: a private file follows a link
runner: a private file is made with a wide mode first
runner: the lock folder is made with the default mode
runner: a lock folder inside the tree is accepted
runner: the lock folder is not resolved before the tree check
runner: a file that is not a regular file passes the file check
runner: a file of a lower user number passes the file check
runner: a file with the owner run bit passes the file check
runner: a file with two or three names passes the file check
runner: a made file is not checked
runner: a made file that fails the check is not refused
runner: a temp folder is not checked by its helper
runner: a temp folder is not put back to 0700 when a umask took owner bits
runner: a refused temp folder is left behind
runner: the folders between are made without the private helper
runner: a private file is emptied before it is checked
runner: a file with a second name is narrowed before it is checked
runner: a named pipe under the name of a made file blocks the open
POSIX-ONLY-MUTANTS-END
- Killers that skip INSIDE their body (a ``pytest.skip(...)`` in the killer or in a helper of its file; some skip only on Windows, some only where
  the account has no symbolic link privilege or the system has no named pipes). They have no mark, so they are not in the list above, and on
  such a system the mutant SURVIVES, with ONE exception: the folder-link killer is named only because its helper holds a skip that can never fire for it
  (see the paragraph that begins "Named in the second list below"), so that mutant is killed on every system. The second list between the marker lines below is read by
  the same test file in both directions: it fails when a named killer has no ``pytest.skip`` call, in its body or in a helper of its file that it calls (the follow is static: it does not look at
  the system), or when a killer with one is not named. The prose above says why each one skips, or, for that one killer, why it does not.
BODY-SKIP-MUTANTS-BEGIN
runner: a link out of the tree is accepted
runner: a relative link out of the tree is copied
runner: a link out of the tree is listed
runner: a symlink is copied as a file
runner: any lock failure is called another run
runner: a lock file that is a symbolic link is followed
runner: the lock file is open to others
runner: a lock file of another user is accepted
runner: a lock file with a wide mode is accepted
runner: a lock file that is not a regular file is accepted
runner: a lock file with two names is accepted
runner: the lock file is opened for writing on POSIX
runner: a FIFO lock file blocks the open
BODY-SKIP-MUTANTS-END
- Killers that skip nothing but drop the case that tests the guard where ``os.name`` is ``"nt"`` (no mark and no ``pytest.skip`` call, so neither list above finds them), and
  the mutant SURVIVES on Windows because the guard is a POSIX branch: "the descriptor of the lock folder leaks" (Windows has no lock folder, so only the file's
  descriptor is opened) and "a JUnit symbolic link is followed" (the symbolic-link case is left out on Windows). This third list is KEPT BY HAND between the marker lines
  below. ``tests/test_mutation_runner_meta.py`` checks it in both directions against the killers that read ``os.name`` or ``sys.platform`` in their body and are in neither list above
  (the two others it finds, "the descriptor leaks when no file object is made" and "a JUnit path that is no regular file is read", still have a case that kills them on Windows;
  they are named in that test). It follows no helper: a killer that reads the system only inside a helper of another file is NOT found.
OS-BRANCH-MUTANTS-BEGIN
runner: the descriptor of the lock folder leaks
runner: a JUnit symbolic link is followed
OS-BRANCH-MUTANTS-END
- Every other killer, in none of the three lists above, carries no skip on Windows and no case left out there by the system name. The tree-kill killers use ``taskkill /T`` on Windows; the
  Windows branch after a normal exit is run on any system with the Windows flag faked.

Keyword tests (``tests/test_mutation_runner_keywords.py``): 267 mutants there (conftest, ``pass_env``, masking, canary, ``forbid_skips``,
fixture errors, the snapshot of the environment, the lock name). Many tests of that file have no mutant of their own, and this header does NOT
list them all: a test either guards the test code itself (the guard test of the database address), an old behaviour that no replacement
can bring back (the check that the old text is gone), a place that one replacement cannot move ("a missing conftest is noticed only at the
copy" stands for "move the check after ``mkdtemp``": the mutant turns the early check off and the error comes late), or a property that a
neighbouring mutant already breaks (the lock-name property test and the one-spelling test are broken by the grammar mutants, the pass_env
tests by the masking mutants). Where that matters, the test's own docstring says so.

Round 23 (private folders and files, bare strings, port range, lock folder in the tree, 300 texts): 38 mutants, one per guard. The two guards of
``throwaway_hosts`` and ``shown_classes`` that had no mutant before got one each.

Round 24 (the files are checked like the folders, every creation site is a helper, class names equal to a secret, the order of the refusals): 21
mutants. The order of the secret-count step against the address step, and the order of the junction checks against the first temp folder, HAVE
mutants now ("the address step comes before the count of the secrets", "the junction checks come after the temp folder is made"): a mutant may
replace several lines at once, so a block can be moved. Tests with no mutant of their own: the text of the module docstring and the D-023 limit
(the text is the guard), the table test of the ``os.`` and ``signal.`` names (the mypy test and the ``os.fchmod`` test have mutants), and the
two runs of mypy themselves (skipped where mypy is not installed, so no mutant could depend on them).

Round 26 (7 mutants added: a built-in class name hidden for a password that is a piece of it (the control test that passed on the old code now has its mutant), a name the caller owns equal to a secret in another letter case, the address check for a password equal to a class name (three: refusal off, case-sensitive, caller names not given), the folders between made without the helper, a file emptied before the check; 7 re-pointed because the text they search for moved: "a name of Python itself goes through the second layer", "a built-in class name equal to a secret is shown", "a private file is not emptied", "the parts between are made with the default mode", "the run does not call the address check", "a made file is not checked", "the address step comes before the count of the secrets"). Tests with no mutant of their own: the walk test of the creation-site pin (it guards the test code), the three tests of the skip reader (they guard the meta-test), the mypy pattern test (it guards the mypy test), and the mypy test itself (skipped where mypy is not installed, which is the CI case).

Round 27 (2 mutants added: "a file with a second name is narrowed before it is checked" and "a named pipe under the name of a made file blocks the open"; 2 re-pointed because the text they search for moved: "a private file is not put back to 0600" and "os.fchmod is used again"; 329 mutants in all). Tests with no mutant of their own: the mypy docstring test and the test that CI does not run the mypy count (both guard texts and files, not the runner), the test that every decorator is read (it guards the reader in the meta-test, which is test code), the test that the header names the killers that drop a case by the system name (it guards this header), the folder-link killer test (it guards the header), and the pin of the creation sites by spelling and count. The mode test of ``_narrowable`` pins the three-way effect (second name, mode, kind of file) and cannot tell its clauses apart: the mode check of ``_file_problem`` refuses a wide mode before the second-name check is reached; the clauses on the owner, the number of names and the kind of file have no mutant of their own. ``handover/evidence/PR89/r28/NOTES.md`` gives the reason for each test that passed on the old code.

Masking (the refusal of odd characters, the plain match, the head and tail beside ``...``): the refusal has one mutant per guard (a quote
mark, a backslash, a control character below the space, DEL, a non-ASCII character, its first value 128, the whole value, the percent-decoded
forms, a message that shows the value) and each is killed by the refusal test of its own class through a fixed failure text. Equivalent mutants,
so none: ``lo = max(at, marked)`` in ``_masked`` (the text before ``marked`` is already marked; a lower start marks the same characters twice),
the sort of the secrets longest first (every span is found in the original text and all are cut out at once, so the order cannot change the
result) and the second refusal of an ``unquote_plus`` form (a ``+`` only becomes a space, which is plain). A fourth: the early return of ``_fragment_spans`` for a secret of fewer than ``EDGE_MIN + 1`` characters (the two passes would find no piece of ``EDGE_MIN`` characters in a window that short either).

No mutant for a password-word check of the address grammar: there is no such check. A password key in any spelling is refused because it
is not on the key allowlist. The killer of the mutant "a key that is not on the allowlist is accepted"
(``test_every_allowed_key_has_a_reason_and_a_refused_sibling``) tries five spellings of a password key (``_REFUSED_PASSWORD_KEYS``) and
asserts that no allowed key can carry a password.

The second layer (a slot of caller text that holds the address or its password is replaced whole by its fixed text) has one mutant per slot
(test id, class name, expect text, mutant name in a message) and one for "cut instead of replace". Tested without a mutant of their own: the
lock folder that cannot be looked at (``fstat`` fails), the required ``shown`` argument, the lower-case rule for keys (an upper-case key is
already refused because it is not on the key allowlist, so a mutant of the key pattern would be equivalent), and the weak-password fuzz with
its control.

Tests with no mutant (the guard is checked by the test only; names as in ``tests/test_mutation_runner.py``):
- ``test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree``: the list-based path checks of ``run_mutants`` for tests
  and fixtures (each is also checked again by ``_inside``, so a mutant that removes the first check is equivalent). The same holds
  for the dash and at-sign refusal of a fixture folder (``extra_dirs`` never reaches the argv; ``_relative`` is called again by ``_inside``).
- ``test_a_refused_run_leaves_no_temp_folder`` (the place of the ``try``), ``test_the_signal_handlers_are_restored_and_an_ignored_sighup_stays_ignored``
  (restore of the old handlers) and ``test_locate_does_not_list_a_file_through_a_folder_link_out_of_the_tree`` (see above).
- ``test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout``: only the ``TIMED_OUT`` constant has a mutant;
  the in-order streaming of each result is checked by the test only.
- ``test_the_manifest_pins_the_files_a_demo_copies``: a hash pin, by design not mutated.
- ``test_run_mutants_refuses_an_odd_value_before_any_temp_folder_and_names_no_secret``: the failing check of a ``pytest.raises`` has no fixed text
  to name (it reads ``DID NOT RAISE``); the refusal itself is killed through ``_secret_values`` above, and the place before the temp folder is
  checked by the test only.
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
KW = "tests/test_mutation_runner_keywords.py"  # the killers of the keyword mutants
KWPIN = "tests/test_mutation_runner_keywords::"


def mutant(name, file, old, new, killer, expect, **kw):
    """One mutant: ``killer`` is the test that must fail first, with a line holding ``expect``."""
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer, **kw
    )


def kmutant(name, file, old, new, killer, expect, **kw):
    """One mutant whose killer is a test of the keyword test file (``tests/test_mutation_runner_keywords.py``)."""
    return Mutant(
        name, file, old, new, expect, test_file=KW, only_test=killer, pinned=KWPIN + killer, **kw
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
        "    if rc == REAPED_ELSEWHERE:", "    if False:",
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
        "                _refuse_junctions(root, d)\n", "                pass\n",
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
    mutant("b2: a refused junit stops the run", MR, "except _UNUSABLE_JUNIT:  # refused or unreadable", "except KeyError:  # refused or unreadable",
        "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on", "ValueError: refused",
        allow_crash=True, crash_type="ValueError"),
    mutant("b2: the junit has no size ceiling", MU, "if len(xml_text) > MAX_JUNIT_CHARS:", "if False:",
        "test_a_junit_text_over_the_ceiling_is_refused", "a JUnit text over the size ceiling was parsed"),
    mutant("b3: a crash row is good whatever the exception", MR, CRASH_OK,
        "crash_ok = v is Verdict.CRASH and m.allow_crash",
        CRASHROW, "a crash row was good for another exception class"),
    # ---- guards of the moved tests that had no mutant, and the guards added by later fixes
    mutant("runner: the child inherits the whole environment", MR,
        "env = {k: source[k] for k in CHILD_ENV if k in source}", "env = dict(os.environ)",
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
        "declared = _leading_class(report.first_line) == m.crash_type", "declared = m.crash_type in report.first_line",
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
    # ---- keyword tests (conftest, pass_env, forbid_skips, fixture errors): killers in tests/test_mutation_runner_keywords.py
    kmutant('runner: a mutant run does not load the conftest', MR, '                timeout,\n                plugin=conftest,\n                env_names=env_names,\n                environ=environ,\n                hosts=hosts,\n            )', '                timeout,\n                env_names=env_names,\n                environ=environ,\n                hosts=hosts,\n            )', 'test_a_mutant_is_judged_with_the_conftest_loaded', 'was not judged with the conftest loaded'),
    kmutant('runner: a mutant run does not get the passed variables', MR, '                timeout,\n                plugin=conftest,\n                env_names=env_names,\n                environ=environ,\n                hosts=hosts,\n            )', '                timeout,\n                plugin=conftest,\n                environ=environ,\n                hosts=hosts,\n            )', 'test_a_mutant_run_sees_the_passed_variable', 'did not see the passed variable'),
    kmutant('runner: the shared name check accepts any name', MR, '        if name not in PASS_ENV_ALLOWED:', '        if False:', 'test_an_unlisted_env_name_is_refused_before_anything_runs', 'an unlisted pass_env name was accepted'),
    kmutant('runner: the pytest step passes any name it is given', MR, '    for name in _checked_env_names(env_names):\n        if name in source:', '    for name in env_names:\n        if name in source:', 'test_the_pytest_step_refuses_an_unlisted_env_name_by_itself', 'the pytest step passed an unlisted name'),
    kmutant('runner: run_mutants does not check the names before it starts', MR, '    env_names = _checked_env_names(pass_env)  # an unlisted name is refused, never passed', '    env_names = tuple(pass_env)  # (mutant)', 'test_an_unlisted_env_name_is_refused_before_anything_runs', 'an unlisted pass_env name was accepted'),
    kmutant('runner: a conftest path with a keyword part is accepted', MR, 'p.isascii() and p.isidentifier() and not keyword.iskeyword(p) for p in names', 'p.isascii() and p.isidentifier() for p in names', 'test_a_conftest_with_a_python_keyword_part_is_refused', 'a keyword part in'),
    kmutant('runner: a conftest path with a non-ASCII part is accepted', MR, 'p.isascii() and p.isidentifier() and not keyword.iskeyword(p) for p in names', 'p.isidentifier() and not keyword.iskeyword(p) for p in names', 'test_a_conftest_with_a_non_ascii_part_is_refused', 'a non-ascii part in'),
    kmutant('runner: a conftest path that does not end in .py is accepted', MR, '    if not parts[-1].endswith(".py") or not all(', '    if not all(', 'test_a_conftest_that_does_not_end_in_py_is_refused', 'a conftest without the .py ending'),
    kmutant('runner: any tree file is accepted as a conftest', MR, '    if parts[-1] != "conftest.py" and "tests" not in parts[:-1]:', '    if False:', 'test_a_conftest_must_be_called_conftest_or_lie_in_a_tests_folder', 'a tree file that is no conftest and no test helper'),
    kmutant('runner: the conftest is not copied into the run', MR, '    copied = (*tests, conftest) if conftest and conftest not in tests else tuple(tests)', '    copied = tuple(tests)', 'test_conftest_loads_the_given_file_as_a_plugin_and_without_it_nothing_is_loaded', 'the conftest was not loaded for the baseline'),
    kmutant('runner: a missing conftest is noticed only at the copy', MR, '            not _inside(root, conftest).is_file()\n', '            False\n', 'test_a_conftest_path_that_is_valid_but_missing_is_a_value_error_before_any_temp_folder', 'a missing conftest was noticed late'),
    kmutant('judge: a failing run with no test id can be a kill', MU, '    if not test_id:  # a failing run', '    if False:  # a failing run', 'test_judge_never_returns_killed_for_an_empty_failing_test_id', 'an empty failing test id was judged as a kill'),
    kmutant('runner: a baseline that skips is accepted', MR, '        if forbid_skips:\n            _refuse_skips_in_baseline(tmp / "base.xml", shown)\n', '        if False:\n            _refuse_skips_in_baseline(tmp / "base.xml", shown)\n', 'test_forbid_skips_refuses_a_baseline_that_skips', 'a baseline that skips was accepted'),
    kmutant('judge: an expected failure is not counted as a skip', MU, '    return [_case_id(case) for case in root.iter("testcase") if case.find("skipped") is not None]', '    return [_case_id(case) for case in root.iter("testcase") if case.find("skipped") is not None and case.find("skipped").get("type") != "pytest.xfail"]', 'test_forbid_skips_counts_an_expected_failure_as_a_skip', 'an expected failure was not counted as a skip'),
    kmutant('runner: the baseline skip message shows the passed value', MR, '{[_shown_id(t, shown) for t in skipped[:3]]}', '{skipped[:3]}', 'test_the_baseline_skip_message_never_holds_the_passed_value', 'the baseline skip message held the passed value'),
    kmutant('runner: a skip is an error without forbid_skips', MR, '        forbid_skips and report.skipped\n', '        report.skipped\n', 'test_default_counts_a_run_with_a_skipped_test_as_before', 'a skipped test changed the result of a run without forbid_skips'),
    kmutant('runner: a skipped run is judged as a kill', MR, '        forbid_skips and report.skipped\n', '        False\n', 'test_forbid_skips_makes_a_mutant_run_with_a_skipped_test_an_error_not_a_kill', 'a skipped test was counted as a kill under forbid_skips'),
    kmutant('runner: no JUnit file is judged under forbid_skips', MR, '        forbid_skips and not xml_text\n', '        False\n', 'test_forbid_skips_with_a_missing_or_empty_junit_file_is_an_error_row_never_judged', 'was not the JUNIT MISSING row'),
    kmutant('runner: no JUnit file is JUNIT MISSING without forbid_skips', MR, '        forbid_skips and not xml_text\n', '        forbid_skips or not xml_text\n', 'test_a_run_that_fails_with_no_junit_file_is_never_a_kill_even_without_forbid_skips', 'was not the plain empty ERROR row'),
    kmutant('runner: a fixture error is judged like a failure', MR, '    if report.fixture_failed:', '    if False:', 'test_a_fixture_error_in_the_mutant_run_is_an_error_row_not_a_kill', 'a fixture that failed at setup was not the FIXTURE ERROR row'),
    kmutant('runner: a skip is judged before a fixture error', MR, '    if report.fixture_failed:', '    if report.fixture_failed and not (forbid_skips and report.skipped):', 'test_a_fixture_error_and_a_skipped_test_in_one_run_are_a_fixture_error', 'a skip was judged before a fixture error'),
    kmutant('runner: the FIXTURE ERROR row keeps no message', MR, '        first_lines[m.name] = _shown_line(report.first_line, shown)\n        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)', '        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)', 'test_a_fixture_error_in_the_mutant_run_is_an_error_row_not_a_kill', 'the FIXTURE ERROR row kept no message'),
    kmutant('runner: the SKIPPED TESTS row keeps no message', MR, '        first_lines[m.name] = why\n', '', 'test_a_skipped_tests_row_without_a_failure_says_which_tests_were_skipped', 'the SKIPPED TESTS row did not say which tests were skipped'),
    kmutant('runner: the SKIPPED TESTS message shows the passed value', MR, '            _shown_line(report.first_line, shown)\n            or f"skipped: {\', \'.join(_shown_id(t, shown, _own_names(m)) for t in report.skipped[:3])}"', '            report.first_line\n            or f"skipped: {\', \'.join(report.skipped[:3])}"', 'test_the_skipped_tests_row_keeps_a_masked_message', 'the SKIPPED TESTS message held the passed value'),
    kmutant('runner: first_lines shows the passed value', MR, '        first_lines[m.name] = _shown_line(report.first_line, shown, m.expect)\n    declared', '        first_lines[m.name] = report.first_line\n    declared', 'test_pass_env_values_never_reach_first_lines', 'the passed value reached first_lines'),
    kmutant('runner: the row id shows the passed value', MR, '_shown_id(report.test_id, shown, _own_names(m)) if report.test_id else ""', 'report.test_id', 'test_pass_env_values_never_reach_the_failing_test_id_of_a_row', 'the passed value reached the test id of a row'),
    kmutant('runner: the password of a URL is not a secret', MR, '    decoded += url_decoded\n    plain += url_plain\n', '', 'test_masked_replaces_the_value_and_the_url_password', 'the secrets were not the value and its password'),
    kmutant('runner: the database is not checked again after a mutant', MR, '            if canary:  # the passed database', '            if False:  # the passed database', 'test_a_database_that_a_mutant_left_dirty_stops_the_run_after_that_mutant', 'a dirty database did not stop the run'),
    kmutant('runner: the result of the database check is ignored', MR, '    if rc != 0:\n        return (\n            f"the unmutated copy no longer passes', '    if False:\n        return (\n            f"the unmutated copy no longer passes', 'test_a_database_that_a_mutant_left_dirty_stops_the_run_after_that_mutant', 'a dirty database did not stop the run'),
    kmutant('runner: the database is checked again without a passed value too', MR, '            if canary:  # the passed database', '            if True:  # the passed database', 'test_without_a_passed_value_there_is_no_extra_run', 'a run with no passed value made an extra run'),
    kmutant('mutation: a teardown error is not a fixture error', MU, '    "failed on teardown",\n', '', 'test_a_teardown_error_of_a_fixture_is_an_error_row_not_a_kill', 'a fixture that failed at teardown was not the FIXTURE ERROR row'),
    kmutant('mutation: a setup error is not a fixture error', MU, '    "failed on setup",\n', '', 'test_a_fixture_error_in_the_mutant_run_is_an_error_row_not_a_kill', 'a fixture that failed at setup was not the FIXTURE ERROR row'),
    kmutant('mutation: any fixture error of the file decides, not the first failure', MU, '        _fixture_errors(root),\n        kind == "fixture",', '        _fixture_errors(root),\n        bool(_fixture_errors(root)),', 'test_a_failing_body_and_a_failing_teardown_are_judged_by_the_failure', 'a test body that failed was hidden behind its failing teardown'),
    kmutant('runner: the edge minimum is longer than what pytest shows', MR, 'EDGE_MIN = 2  #', 'EDGE_MIN = 14  #', 'test_a_shortened_value_is_masked_by_its_fragments', 'a fragment of the shortened value survived the masking'),
    kmutant('runner: a passed name set to an empty text is not checked', MR, '        if env_name in environ:\n            _refuse_unsafe_address(', '        if environ.get(env_name):\n            _refuse_unsafe_address(', 'test_a_passed_name_set_to_an_empty_text_is_refused_before_any_run', 'a passed name set to an empty text was accepted'),
    kmutant('runner: a canary run that skips is accepted', MR, '    if forbid_skips:\n        try:\n            _refuse_skips_in_baseline(junit, shown)', '    if False:\n        try:\n            _refuse_skips_in_baseline(junit, shown)', 'test_a_canary_run_that_skips_is_refused_under_forbid_skips', 'a canary run that skipped was accepted'),
    kmutant('runner: a failed canary carries no rows', MR, 'failure.rows = tuple(out)', 'pass', 'test_a_database_that_a_mutant_left_dirty_stops_the_run_after_that_mutant', 'the failure did not carry the rows so far'),
    kmutant('runner: a failed canary rebuild is not a clear refusal', MR, '                except OSError as exc:\n                    rebuild_failed = type(exc).__name__', '                except ZeroDivisionError as exc:\n                    rebuild_failed = type(exc).__name__', 'test_a_copy_that_cannot_be_rebuilt_for_the_canary_is_a_clear_refusal', 'the canary copy failure was not a clear refusal'),
    kmutant('runner: the canary runs the mutated copy', MR, '                try:\n                    fresh()\n                except OSError as exc:\n                    rebuild_failed', '                try:\n                    pass\n                except OSError as exc:\n                    rebuild_failed', 'test_the_canary_runs_the_unmutated_copy', 'the canary ran the mutated copy'),
    kmutant('runner: a baseline with no usable JUnit file is not refused', MR, '    except _UNUSABLE_JUNIT as exc:\n        # only the class name', '    except ZeroDivisionError as exc:\n        # only the class name', 'test_a_baseline_that_left_no_usable_junit_file_is_refused_under_forbid_skips', 'no refusal for a baseline without a JUnit file'),
    kmutant('runner: a collection error is judged like a failure', MR, '    if report.collection_failed:', '    if False:', 'test_a_test_file_that_cannot_be_imported_is_an_error_row_never_a_kill', 'an assert at import time was counted as a kill'),
    kmutant('judge: a collection error is not marked', MU, '            kind = "collection"', '            kind = ""', 'test_read_junit_marks_a_collection_error_of_a_real_pytest_run', 'a real collection error was not read as one'),
    kmutant('runner: an ERROR row with no failing test names none', MR, '        shown_id or no_id,', '        shown_id,', 'test_a_run_that_fails_with_no_junit_file_is_never_a_kill_even_without_forbid_skips', 'was not the plain empty ERROR row'),
    kmutant('runner: a second runner on the same database is not refused', MR, '    if canary:  # before any temp folder: a second runner on the same database is refused', '    if False:  # before any temp folder: a second runner on the same database is refused', 'test_a_second_runner_with_the_same_passed_value_is_refused', 'a second runner on the same passed value was accepted'),
    kmutant('runner: the pytest step does not load the conftest', MR, '"--noconftest", *load),', '"--noconftest"),', 'test_conftest_loads_the_given_file_as_a_plugin_and_without_it_nothing_is_loaded', 'the conftest was not loaded for the baseline'),
    kmutant('runner: a bare string is read letter by letter', MR, '    if isinstance(names, str):\n        raise TypeError("pass_env is', '    if False:\n        raise TypeError("pass_env is', 'test_a_bare_string_for_pass_env_is_refused_not_read_letter_by_letter', 'a bare string was read as names'),
    kmutant('runner: the edge minimum is one too long', MR, 'EDGE_MIN = 2  #', 'EDGE_MIN = 3  #', 'test_a_piece_of_exactly_the_edge_minimum_is_masked_and_a_shorter_one_is_not', 'a 2-character head next to the dots was not masked'),
    kmutant('runner: the edge minimum is one too short', MR, 'EDGE_MIN = 2  #', 'EDGE_MIN = 1  #', 'test_a_piece_of_exactly_the_edge_minimum_is_masked_and_a_shorter_one_is_not', 'a 1-character head was masked next to the dots, below the minimum'),
    kmutant('runner: the lock is given back while the run goes on', MR, '        yield  # the lock goes with the closed file', '        handle.close()\n        yield  # the lock goes with the closed file', 'test_the_lock_is_still_held_while_the_mutants_run', 'the lock was not held while a mutant result came in'),
    kmutant('runner: any lock failure is called another run', MR, '                if exc.errno in _LOCK_HELD\n', '                if True\n', 'test_a_lock_that_fails_for_another_reason_is_not_called_another_run', 'a lock failure that is not a second run was called one'),
    kmutant('runner: a lock file that cannot be opened is not a clear refusal', MR, '            except OSError as exc:\n                problem = (\n                    f"could not be opened', '            except ZeroDivisionError as exc:\n                problem = (\n                    f"could not be opened', 'test_a_lock_file_that_cannot_be_opened_is_a_clear_refusal', 'the open failure was not a clear refusal'),
    kmutant('runner: a canary that skips is a plain RuntimeError', MR, '                    failure = CanaryFailed(reason)', '                    failure = RuntimeError(reason)', 'test_a_canary_run_that_skips_is_refused_under_forbid_skips', 'a canary run that skipped was not a CanaryFailed'),
    kmutant('runner: the head scan window is one short', MR, 'text[max(0, start - top) : start]', 'text[max(0, start - top + 1) : start]', 'test_the_fragment_scan_finds_the_largest_head_and_tail_at_every_size', 'the largest head of a'),
    kmutant('runner: a lock file that is a symbolic link is followed', MR, ' | getattr(os, "O_NOFOLLOW", 0)', '', 'test_a_lock_file_that_is_a_symbolic_link_is_refused_and_the_file_has_mode_0600', 'a planted symbolic link was followed or refused otherwise'),
    kmutant('runner: the lock file is open to others', MR, 'fd = os.open(name, flags, 0o600, dir_fd=folder)', 'fd = os.open(name, flags, 0o666, dir_fd=folder)', 'test_a_lock_file_that_is_a_symbolic_link_is_refused_and_the_file_has_mode_0600', 'the lock file was not private'),
    kmutant('runner: a canary timeout is shown as a number', MR, '    TIMED_OUT: "the run timed out",\n', '', 'test_a_canary_run_that_timed_out_says_so', 'the canary timeout was not in words'),
    kmutant('runner: a reaped canary is shown as a number', MR, '    REAPED_ELSEWHERE: "the run was reaped by another waiter, its exit status is lost",\n', '', 'test_a_canary_run_that_was_reaped_says_so', 'the reaped canary was not in words'),
    kmutant('runner: the exit code of a canary run is lost', MR, '    return _RUN_END_IN_WORDS.get(rc, f"exit code {rc}")', '    return _RUN_END_IN_WORDS.get(rc, "")', 'test_a_canary_run_with_an_exit_code_shows_the_code', 'the exit code of the canary run was lost'),
    kmutant('runner: a short secret is cut out before the long one is matched', MR, '    chosen = tuple(v for v in secrets if v)\n', '    chosen = tuple(v for v in secrets if v)\n    text = text.replace(min(chosen, key=len), MASK) if chosen else text\n', 'test_a_short_secret_inside_a_shortened_long_one_does_not_hide_the_long_one', 'a short secret inside the tail hid the shortened long secret'),
    kmutant('runner: the unencoded-separator URL passwords are not read', MR, '    decoded += url_decoded\n    plain += url_plain\n', '    decoded += [urlsplit(value).password or ""]\n', 'test_a_url_password_with_unencoded_separators_is_masked', 'an unencoded slash or hash was not hidden in full'),
    kmutant('runner: only the first @ ends the login of a URL', MR, '        while at != -1:\n            found.append(rest[colon + 1 : at])', '        if at != -1:\n            found.append(rest[colon + 1 : at])', 'test_a_url_password_with_unencoded_separators_is_masked', 'an unencoded slash or hash was not hidden in full'),
    kmutant('runner: a text with no secret is rebuilt', MR, '    if not chosen:\n        return text\n', '', 'test_nothing_is_rebuilt_when_no_secret_is_set', 'a text with no secret was rebuilt'),
    kmutant('runner: a lock file of another user is accepted', MR, '    if info.st_uid != os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o177:', '    if stat.S_IMODE(info.st_mode) & 0o177:', 'test_a_lock_file_of_another_user_is_refused', 'a lock file of another user was accepted'),
    kmutant('runner: a lock file with a wide mode is accepted', MR, '    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open', '    if False:\n        return "is open', 'test_a_lock_file_with_a_wider_mode_is_refused', 'a lock file with a wide mode was accepted'),
    kmutant('runner: a lock file that is not a regular file is accepted', MR, '    if not stat.S_ISREG(info.st_mode):\n        return "is not a regular file"', '    if False:\n        return "is not a regular file"', 'test_a_lock_file_that_is_not_a_regular_file_is_refused', 'a lock file that is not a regular file was accepted'),
    kmutant('runner: the descriptor of the lock folder leaks', MR, '            if folder is not None:\n                os.close(folder)', '            if folder is not None:\n                pass', 'test_the_descriptor_is_closed_when_no_file_object_can_take_it', 'the descriptor stayed open'),
    kmutant('runner: the descriptor leaks when no file object is made', MR, '            os.close(fd)  # no file object took the descriptor over', '            pass  # no file object took the descriptor over', 'test_the_descriptor_is_closed_when_no_file_object_can_take_it', 'the descriptor stayed open'),
    kmutant('runner: a lock file with two names is accepted', MR, '    if info.st_nlink > 1:\n        return "has more', '    if False:\n        return "has more', 'test_a_lock_file_with_two_hard_links_is_refused', 'a lock file with two hard links was accepted'),
    kmutant('runner: a folder is not named as the cause', MR, '    errno.EISDIR: "it is a folder",\n', '', 'test_a_lock_file_that_cannot_be_opened_names_the_cause', 'did not name its cause'),
    kmutant('runner: a not-a-folder path is not named as the cause', MR, '    errno.ENOTDIR: "a part of its path is not a folder",\n', '', 'test_a_lock_file_that_cannot_be_opened_names_the_cause', 'did not name its cause'),
    kmutant('runner: a refused permission is not named as the cause', MR, '    errno.EACCES: _NO_ACCESS,', '    errno.EXDEV: _NO_ACCESS,', 'test_a_lock_file_that_cannot_be_opened_names_the_cause', 'did not name its cause'),
    kmutant('runner: the lock file is opened for writing on POSIX', MR, '(os.O_RDWR if _IS_WINDOWS else os.O_RDONLY)', '(os.O_RDWR)', 'test_the_lock_file_is_opened_read_only_on_posix', 'the lock file was opened for writing'),
    kmutant('runner: a FIFO lock file blocks the open', MR, '        | getattr(os, "O_NONBLOCK", 0)\n', '', 'test_a_lock_file_that_is_a_fifo_is_refused_and_does_not_hang', 'hung the runner'),
    kmutant('runner: a JUnit path that is no regular file is read', MR, '    if not stat.S_ISREG(info.st_mode):\n        raise ValueError("junit path is not a regular file")\n', '', 'test_a_junit_path_that_is_not_a_regular_file_is_refused_and_does_not_hang', ' as the JUnit file was read'),
    kmutant('runner: a JUnit symbolic link is followed', MR, '        info = junit.lstat()\n', '        info = junit.stat()\n', 'test_a_junit_path_that_is_not_a_regular_file_is_refused_and_does_not_hang', ' as the JUnit file was read'),
    kmutant('runner: the JUnit size ceiling is not checked', MR, '    if info.st_size > MAX_JUNIT_CHARS:  # looked at BEFORE the file is read\n        raise ValueError("junit file over the ceiling")\n', '', 'test_an_over_sized_junit_file_is_refused_before_it_is_read', 'the file was read before its size was looked at'),
    kmutant('runner: dots that share a dot are not all found', MR, '_DOTS = re.compile(r"(?=\\.\\.\\.|\\u2026)")', '_DOTS = re.compile(r"\\.\\.\\.|\\u2026")', 'test_dots_that_share_a_dot_are_all_found', 'a head that ends in a dot, before the cut, was not all hidden'),
    kmutant('runner: a value with a quote mark is accepted', MR, '        _refuse_odd(name, "its value", value)\n', '', 'test_a_value_with_a_quote_mark_is_refused_and_the_message_names_no_secret', 'a value with a quote mark was not refused'),
    kmutant('runner: a quote mark is not an odd character', MR, '        if char in "\'\\"":\n', '        if False:\n', 'test_a_value_with_a_quote_mark_is_refused_and_the_message_names_no_secret', 'a value with a quote mark was not refused'),
    kmutant('runner: a backslash is not an odd character', MR, '        if char == "\\\\":\n', '        if False:\n', 'test_a_value_with_a_backslash_is_refused_and_the_message_names_no_secret', 'a value with a backslash was not refused'),
    kmutant('runner: a control character below the space is not odd', MR, 'if ord(char) < 32 or ord(char) == 127:', 'if ord(char) < 31 or ord(char) == 127:', 'test_a_value_with_a_control_character_is_refused_and_the_message_names_no_secret', 'a value with a control character below the space was not refused'),
    kmutant('runner: the DEL character is not odd', MR, 'if ord(char) < 32 or ord(char) == 127:', 'if ord(char) < 32:', 'test_a_value_with_a_control_character_is_refused_and_the_message_names_no_secret', 'a value with the DEL character was not refused'),
    kmutant('runner: a space is a control character', MR, 'if ord(char) < 32 or ord(char) == 127:', 'if ord(char) <= 32 or ord(char) == 127:', 'test_the_printable_ascii_range_is_accepted_and_the_characters_next_to_it_are_not', 'a value of the plain printable characters (space to tilde) was refused'),
    kmutant('runner: the first non-ASCII character is accepted', MR, 'if ord(char) > 127:', 'if ord(char) > 128:', 'test_a_value_with_a_non_ascii_character_is_refused_and_the_message_names_no_secret', 'a value with the first non-ASCII character was not refused'),
    kmutant('runner: a non-ASCII character is accepted', MR, 'if ord(char) > 127:', 'if False:', 'test_a_value_with_a_non_ascii_character_is_refused_and_the_message_names_no_secret', 'a value with a non-ASCII character was not refused'),
    kmutant('runner: a password that decodes to an odd character is accepted', MR, '            _refuse_odd(name, what, decoded)\n', '', 'test_a_password_that_decodes_to_an_odd_character_is_refused_and_the_message_names_no_secret', 'a password that decodes to a quote mark was not refused'),
    kmutant('runner: the refusal shows the value', MR, '{what} holds {kind}. The runner', '{what} holds {kind} ({text}). The runner', 'test_a_value_with_a_quote_mark_is_refused_and_the_message_names_no_secret', 'holds a piece of the secret'),
    kmutant('runner: the passwd word is not read', MR, '(?:password|passwd|pwd)', '(?:password|pwd)', 'test_passwd_and_pwd_words_are_secrets', 'the password after passwd= was not a secret'),
    kmutant('runner: the pwd word is not read', MR, '(?:password|passwd|pwd)', '(?:password|passwd)', 'test_passwd_and_pwd_words_are_secrets', 'the password after pwd= was not a secret'),
    kmutant('runner: the password word is read only in lower case', MR, 'r"(?is)(?:password|passwd|pwd)', 'r"(?s)(?:password|passwd|pwd)', 'test_passwd_and_pwd_words_are_secrets', 'the password after PWD= was not a secret'),
    kmutant('runner: the password after a password word is not a secret', MR, '    decoded = [m.group(2) for m in matches if not m.group(1)]\n', '    decoded = []\n', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'the text up to the first semicolon of an unquoted password was not a secret'),
    kmutant('runner: a semicolon does not end an unquoted password', MR, '([^\\s&;]+)"', '([^\\s]+)"', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'the text up to the first semicolon of an unquoted password was not a secret'),
    kmutant('runner: the rest of an unquoted password is not a secret', MR, '    plain += words\n', '', 'test_an_unquoted_password_with_a_semicolon_or_an_ampersand_is_masked_in_full_when_printed_alone', 'printed alone was not masked in one mark'),
    kmutant('runner: the pieces of an unquoted password are not secrets', MR, 'for piece in re.split(r"[;&]", word)', 'for piece in []', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'a long piece of an unquoted password after a semicolon was not a secret'),
    kmutant('runner: an ampersand does not split an unquoted password', MR, 're.split(r"[;&]", word)', 're.split(r"[;]", word)', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'a piece of an unquoted password after an ampersand was not a secret'),
    kmutant('runner: a piece of exactly the password piece minimum is not a secret', MR, 'if len(piece) >= PASSWORD_PIECE_MIN', 'if len(piece) > PASSWORD_PIECE_MIN', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'a piece of exactly PASSWORD_PIECE_MIN characters was not a secret'),
    kmutant('runner: a piece one short of the password piece minimum is a secret', MR, 'if len(piece) >= PASSWORD_PIECE_MIN', 'if len(piece) >= PASSWORD_PIECE_MIN - 1', 'test_the_pieces_of_an_unquoted_password_that_holds_a_semicolon_or_an_ampersand_are_secrets', 'a piece shorter than PASSWORD_PIECE_MIN characters was a secret'),
    kmutant('runner: a line with a hostile number of dots is scanned', MR, '    if len(dots) > MAX_FRAGMENT_HITS:', '    if False:', 'test_a_line_with_a_hostile_number_of_dots_is_replaced_fast', 'a line with a hostile number of dots was not replaced as a whole'),
    kmutant('runner: a shortened value is not masked at its start', MR, '        if size >= EDGE_MIN:\n            spans.append((start - size, start))', '        if False:\n            spans.append((start - size, start))', 'test_the_fragment_scan_agrees_with_the_plain_definition', 'the fast scan found other spans than the plain definition'),
    kmutant('runner: a shortened value is not masked at its end', MR, '        if size >= EDGE_MIN:\n            spans.append((end, end + size))', '        if False:\n            spans.append((end, end + size))', 'test_the_fragment_scan_agrees_with_the_plain_definition', 'the fast scan found other spans than the plain definition'),
    kmutant('runner: the tail scan window is one short', MR, 'text[end : end + top][::-1]', 'text[end : end + top - 1][::-1]', 'test_the_fragment_scan_finds_the_largest_head_and_tail_at_every_size', 'the largest tail of a'),
    kmutant('runner: the environment is read again for each mutant run', MR, '                timeout,\n                plugin=conftest,\n                env_names=env_names,\n                environ=environ,\n                hosts=hosts,\n            )', '                timeout,\n                plugin=conftest,\n                env_names=env_names,\n                hosts=hosts,\n            )', 'test_the_environment_is_read_once_and_a_change_during_the_run_changes_nothing', 'the second mutant run got the changed value'),
    kmutant('runner: the environment is read again for the canary run', MR, '                    plugin=conftest,\n                    env_names=env_names,\n                    environ=environ,\n                    hosts=hosts,\n                )', '                    plugin=conftest,\n                    env_names=env_names,\n                    hosts=hosts,\n                )', 'test_the_environment_is_read_once_and_a_change_during_the_run_changes_nothing', 'a canary run got the changed value'),
    kmutant('runner: the prefix table of a secret falls back to zero', MR, '        while k and pattern[i] != pattern[k]:\n            k = table[k - 1]', '        while k and pattern[i] != pattern[k]:\n            k = 0', 'test_the_fragment_scan_agrees_with_the_plain_definition_on_repeating_secrets', 'on a repeating secret'),
    kmutant('runner: the pass over a window falls back to zero', MR, '        while k and ch != pattern[k]:\n            k = table[k - 1]', '        while k and ch != pattern[k]:\n            k = 0', 'test_the_fragment_scan_agrees_with_the_plain_definition_on_repeating_secrets', 'on a repeating secret'),
    kmutant('runner: the tail is read in the order of the text', MR, 'text[end : end + top][::-1]', 'text[end : end + top]', 'test_the_fragment_scan_agrees_with_the_plain_definition', 'the fast scan found other spans than the plain definition'),
    kmutant('runner: a value that overlaps itself is found once', MR, '            at = text.find(value, at + 1)', '            at = text.find(value, at + len(value))', 'test_a_value_inside_a_bigger_secret_or_overlapping_another_is_masked_in_full', 'a secret that overlaps itself left a rest readable'),
    kmutant('runner: every masked character gets its own mark', MR, '        elif not out or out[-1] != MASK:\n', '        else:\n', 'test_an_unquoted_password_with_a_semicolon_or_an_ampersand_is_masked_in_full_when_printed_alone', 'printed alone was not masked in one mark'),
    kmutant('runner: a plus in a URL password is not read as a space', MR, '("the password in it, percent-decoded with + read as a space", unquote_plus),', '("the password in it, percent-decoded with + read as a space", unquote),', 'test_a_plus_in_a_url_password_is_also_read_as_a_space', 'the plus-as-space form of the password was not a secret'),
    kmutant('conftest: a changed database address is not noticed', "tests/conftest.py", '    if after != before:\n', '    if False:\n', 'test_the_fixture_that_guards_the_database_address_fails_a_test_that_changes_it', 'the fixture did not fail a test that changed the database address'),
    kmutant('runner: the message of a COLLECTION ERROR row shows the passed value', MR, '        first_lines[m.name] = _shown_line(report.first_line, shown)\n        return (m.name, Verdict.ERROR, "COLLECTION ERROR", False)', '        first_lines[m.name] = report.first_line\n        return (m.name, Verdict.ERROR, "COLLECTION ERROR", False)', 'test_the_message_of_a_collection_error_never_holds_the_passed_value', 'the passed value reached the first line of a COLLECTION ERROR row'),
    kmutant('runner: the message of a FIXTURE ERROR row shows the passed value', MR, '        first_lines[m.name] = _shown_line(report.first_line, shown)\n        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)', '        first_lines[m.name] = report.first_line\n        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)', 'test_the_message_of_a_fixture_error_never_holds_the_passed_value', 'the passed value reached the first line of a FIXTURE ERROR row'),
    kmutant('runner: the canary skip message shows the passed value', MR, '            _refuse_skips_in_baseline(junit, shown)\n        except RuntimeError as exc:', '            _refuse_skips_in_baseline(junit, _Shown())\n        except RuntimeError as exc:', 'test_the_canary_skip_message_never_holds_the_passed_value', 'the canary skip message held the passed value'),
    kmutant("runner: the quote(safe='') form of a password is not a secret", MR, '    for form in (quote(text, safe=""), quote(text), quote_plus(text)):', '    for form in (quote(text), quote_plus(text)):', 'test_the_re_encoded_forms_of_a_url_password_are_secrets', "the password encoded with quote(safe='') was not a secret"),
    kmutant('runner: the quote_plus form of a password is not a secret', MR, '    for form in (quote(text, safe=""), quote(text), quote_plus(text)):', '    for form in (quote(text, safe=""), quote(text)):', 'test_the_re_encoded_forms_of_a_url_password_are_secrets', 'the quote_plus form was not a secret'),
    kmutant('runner: the quote form with the slash kept is not a secret', MR, '    for form in (quote(text, safe=""), quote(text), quote_plus(text)):', '    for form in (quote(text, safe=""), quote_plus(text)):', 'test_the_re_encoded_forms_of_a_url_password_are_secrets', 'the form of quote() that keeps the slash was not a secret'),
    kmutant('runner: the lower-case hex forms of a password are not secrets', MR, '        forms.add(re.sub(r"%[0-9A-F]{2}", lambda m: m.group().lower(), form))\n', '', 'test_the_re_encoded_forms_of_a_url_password_are_secrets', "the lower-case hex form of quote(safe='') was not a secret"),
    kmutant('runner: a password is decoded only twice', MR, '            len(password) + 1\n', '            2\n', 'test_a_password_that_was_encoded_twice_or_more_is_decoded_until_it_stops_changing', 'a password encoded three times was not decoded to the end'),
    kmutant('runner: only the first decoding step is checked for odd characters', MR, '            _refuse_odd(name, what, decoded)\n', '            if decoded == decode(password):\n                _refuse_odd(name, what, decoded)\n', 'test_a_password_that_was_encoded_twice_or_more_is_decoded_until_it_stops_changing', 'a password that decodes to a quote mark at the third depth was not refused'),
    kmutant('runner: a password word inside a longer word is not read', MR, 'r"(?is)(?:password|passwd|pwd)', 'r"(?is)(?<![A-Za-z0-9])(?:password|passwd|pwd)', 'test_a_password_word_inside_a_longer_word_and_in_any_case_is_read', 'the password after sslpassword= was not a secret'),
    kmutant('runner: the lock is entered before the try, so an exit right after it leaves the lock held', MR, '    try:\n        if canary:  # before any temp folder: a second runner on the same database is refused\n            _refuse_lock_folder_in_tree(root)\n            held.enter_context(\n                _one_run_per_database([environ[n] for n in env_names if n in environ])\n            )\n        # the junction checks', '    if canary:  # before any temp folder: a second runner on the same database is refused\n        _refuse_lock_folder_in_tree(root)\n        held.enter_context(\n            _one_run_per_database([environ[n] for n in env_names if n in environ])\n        )\n    try:\n        # the junction checks', 'test_an_exit_right_after_the_lock_is_taken_still_gives_the_lock_back', 'left the lock held'),
    kmutant('runner: the lock file name depends on the password', MR, 'sorted(_address_parts(v) for v in values)', 'sorted(values)', 'test_the_lock_file_name_does_not_depend_on_the_password', 'two addresses that differ only in the password got two lock file names'),
    kmutant('runner: the lock file name ignores the port of a URL', MR, '"port": url.group(2) or "",', '"port": "",', 'test_the_lock_file_name_does_not_depend_on_the_password', 'two addresses with another port got one lock file name'),
    kmutant('runner: the lock file name ignores the database of a URL', MR, '"dbname": url.group(3),', '"dbname": "",', 'test_the_lock_file_name_does_not_depend_on_the_password', 'two addresses with another database got one lock file name'),
    kmutant('runner: values that are no address get a name of their own', MR, '    if fields is None:\n        return "unparsed"', '    if fields is None:\n        return value', 'test_the_lock_file_name_does_not_depend_on_the_password', 'did not get the name of the values outside the grammar'),
    kmutant('runner: the lock grammar reads text after the database (a prefix match)', MR, 'url = _URL_ADDRESS.fullmatch(value)', 'url = _URL_ADDRESS.match(value)', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar reads a URL query', MR, '/([A-Za-z0-9_.-]+)"\n)  # the WHOLE value', '/([A-Za-z0-9_.-]+)(?:[?#;]\\S*)?"\n)  # the WHOLE value', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar reads a path of more than one part', MR, '/([A-Za-z0-9_.-]+)"\n)  # the WHOLE value', '/([A-Za-z0-9_./-]+)"\n)  # the WHOLE value', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar lets the login hold a slash', MR, '(?:[^@/?#\\s]*@)?', '(?:[^@\\s]*@)?', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar keeps the case of a URL host', MR, '"host": url.group(1).strip("[]").lower(),', '"host": url.group(1).strip("[]"),', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar reads a key=value host of any shape', MR, '"host": re.compile(rf"{_NAME_HOST}|{_IP6_HOST}"),', '"host": re.compile(r".+"),', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar reads a key=value port of any length', MR, '"port": re.compile(r"[0-9]{1,5}"),', '"port": re.compile(r"[0-9]+"),', 'test_a_port_is_one_to_five_digits_and_from_1_to_65535_in_both_forms', 'was accepted'),
    kmutant('runner: the lock grammar reads a key=value database of any shape', MR, '"dbname": re.compile(r"[A-Za-z0-9_.-]+"),', '"dbname": re.compile(r".+"),', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar reads a key=value host address of any shape', MR, '"hostaddr": re.compile(r"[0-9A-Fa-f.:]+"),', '"hostaddr": re.compile(r".+"),', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: the lock grammar skips blank words of a key=value address', MR, 'for word in value.split(" "):', 'for word in value.split():', 'test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed', 'a lock name input was not the expected one'),
    kmutant('runner: a repeated password word adds a word each time', MR, 'if m.start(2) >= reached:', 'if True:', 'test_many_repeats_of_one_option_are_few_secrets_and_fast', 'a repeated option was refused as too many texts'),
    kmutant('runner: the number of texts to hide has no ceiling', MR, 'if len(bases) > MAX_SECRETS:', 'if False:', 'test_a_password_in_many_encoded_layers_is_refused_fast_without_showing_it', 'a value with hundreds of layers was accepted'),
    kmutant('runner: a line with many dots and many values is scanned', MR, 'if len(dots) * len(chosen) > MAX_FRAGMENT_WORK:', 'if False:', 'test_a_line_with_many_dots_and_many_secrets_is_replaced_not_scanned', 'the line was scanned'),
    kmutant('runner: the plus step stops at a form seen before', MR, 'if decoded == text:', 'if decoded in forms:', 'test_a_plus_that_comes_from_a_percent_code_is_read_as_a_space_on_the_next_step', 'a plus from a percent code was not read as a space'),
    kmutant('runner: every password word text is decoded and refused', MR, 'decoded = [m.group(2) for m in matches if not m.group(1)]', 'decoded = [m.group(2) for m in matches]', 'test_the_text_after_a_password_word_and_a_space_is_not_decoded_as_a_password', 'the text after the space was decoded as a password'),
    kmutant('runner: a text with ? or # between a colon and an @ is decoded and refused', MR, 'return [proper, *(c for c in found if not re.search(r"[?#]", c))], [', 'return [proper, *found], [', 'test_a_host_with_a_port_is_not_read_as_a_url_login_and_a_numeric_password_still_is', 'a non-ASCII option beside an @ refused the run'),
    kmutant('runner: the text between a colon and an @ is not a candidate', MR, '        at = rest.find("@", colon + 1) if colon != -1 else -1', '        at = -1', 'test_a_host_with_a_port_is_not_read_as_a_url_login_and_a_numeric_password_still_is', 'a password of digits then a slash was not found'),
    kmutant('runner: a value of exactly the ceiling is refused', MR, '        if len(value) > MAX_VALUE_CHARS:\n', '        if len(value) >= MAX_VALUE_CHARS:\n', 'test_a_value_longer_than_the_ceiling_is_refused_without_showing_it', 'a value of exactly MAX_VALUE_CHARS characters was refused'),
    kmutant('runner: a value over the ceiling is accepted', MR, '        if len(value) > MAX_VALUE_CHARS:\n', '        if False:\n', 'test_a_value_longer_than_the_ceiling_is_refused_without_showing_it', 'a value of MAX_VALUE_CHARS + 1 characters was not refused'),
    kmutant('runner: the one-character ellipsis is not looked for', MR, '_DOTS = re.compile(r"(?=\\.\\.\\.|\\u2026)")', '_DOTS = re.compile(r"(?=\\.\\.\\.)")', 'test_a_piece_beside_a_unicode_ellipsis_is_masked_like_one_beside_three_dots', 'a piece beside the ellipsis'),
    kmutant('runner: the one-character ellipsis has the width of three dots', MR, '            1 if text[start] == "\\u2026" else 3\n', '            3\n', 'test_the_scan_gives_the_unicode_ellipsis_the_width_of_one_character', 'the one-character ellipsis was given the width of three dots'),
    kmutant('runner: the line is cut at the ceiling of dots, one too early', MR, 'itertools.islice(_DOTS.finditer(text), MAX_FRAGMENT_HITS + 1)', 'itertools.islice(_DOTS.finditer(text), MAX_FRAGMENT_HITS)', 'test_a_piece_next_to_dots_hides_only_that_piece_of_a_short_secret', "a line with one more '...' than MAX_FRAGMENT_HITS was not replaced as a whole"),
    kmutant('runner: a line with exactly the ceiling of dots is replaced', MR, '    if len(dots) > MAX_FRAGMENT_HITS:', '    if len(dots) >= MAX_FRAGMENT_HITS:', 'test_a_piece_next_to_dots_hides_only_that_piece_of_a_short_secret', 'a line full of pieces next to dots was replaced or masked wrongly'),
    kmutant('runner: an empty secret is not left out', MR, '    chosen = tuple(v for v in secrets if v)\n    if not chosen:', '    chosen = tuple(secrets)\n    if not chosen:', 'test_nothing_is_rebuilt_when_no_secret_is_set', 'a text with no secret was rebuilt'),
    kmutant('conftest: the old address is not put back', "tests/conftest.py", '            os.environ[name] = before\n', '            pass\n', 'test_the_fixture_that_guards_the_database_address_fails_a_test_that_changes_it', 'the fixture did not put the old value back'),
    kmutant('conftest: an address that a test added is not removed', "tests/conftest.py", '            os.environ.pop(name, None)\n', '            pass\n', 'test_the_fixture_that_guards_the_database_address_removes_an_address_that_a_test_added', 'the fixture did not remove an address that a test added'),
    kmutant('conftest: a changed address does not fail the test', "tests/conftest.py", '        pytest.fail(f"a test changed', '        print(f"a test changed', 'test_the_fixture_that_guards_the_database_address_fails_a_test_that_changes_it', 'the fixture did not fail a test that changed the database address'),
    kmutant('runner: an address outside the grammar is accepted', MR, '    if fields is None:\n        raise ValueError(\n            f"{env_name} is refused: its address is not in a shape', '    if fields is None:\n        return\n        raise ValueError(\n            f"{env_name} is refused: its address is not in a shape', 'test_the_address_check_refuses_an_address_outside_the_grammar', 'an address outside the grammar was accepted'),
    kmutant('runner: the host of an address is not checked', MR, '    for part in ("host", "hostaddr"):', '    for part in ("hostaddr",):', 'test_the_address_check_refuses_a_host_that_is_not_on_the_allowlist', 'a host that is not allowed was accepted'),
    kmutant('runner: the hostaddr of an address is not checked', MR, '    for part in ("host", "hostaddr"):', '    for part in ("host",):', 'test_the_address_check_refuses_a_hostaddr_that_is_not_on_the_allowlist', 'a hostaddr that is not allowed was accepted'),
    kmutant('runner: a passed address does not imply forbid_skips', MR, '        forbid_skips = bool(env_names)', '        forbid_skips = False', 'test_a_passed_address_implies_forbid_skips_and_an_explicit_false_turns_it_off', 'a passed address did not imply forbid_skips'),
    kmutant('runner: a lock folder that others can enter is accepted', MR, '    if stat.S_IMODE(info.st_mode) & 0o077:\n        return "is open', '    if False:\n        return "is open', 'test_a_lock_folder_that_others_can_enter_or_that_is_not_the_users_is_refused', 'a lock folder that others can enter was accepted'),
    kmutant('runner: a class name that is not on the allowlist is shown', MR, '    if head not in shown.classes:\n        return CLASS_HIDDEN\n', '', 'test_a_class_name_is_shown_only_when_it_is_on_the_allowlist_of_the_call', 'a class name that is not on the allowlist was shown'),
    kmutant('runner: the parameters of a test id are shown', MR, '            end = PARAMETERS_HIDDEN if bracket else ""', '            end = bracket + _rest', 'test_the_projection_replaces_the_parameters_of_a_test_id', 'the parameters of a test id were shown'),
    kmutant("runner: a test id with a file part that is not the caller's is shown", MR, '        if path == file_part:\n            classes: list[str] = []', '        if True:\n            classes: list[str] = []', 'test_a_test_id_is_shown_only_when_it_is_made_of_the_callers_own_text', "the file part is not one of the caller's tests"),
    kmutant('runner: a function name that is not in the snapshot is shown', MR, 'all(name in allowed for name in (*classes, function))', 'all(name in allowed for name in classes)', 'test_a_test_id_is_shown_only_when_it_is_made_of_the_callers_own_text', 'the function is not defined in the snapshot of that file'),
    kmutant('runner: a test class name that is not in the snapshot is shown', MR, 'all(name in allowed for name in (*classes, function))', 'all(name in allowed for name in (function,))', 'test_a_test_id_is_shown_only_when_it_is_made_of_the_callers_own_text', 'a class that is not defined in the snapshot of that file'),
    kmutant('runner: the crash_type of a mutant of the call is not on the allowlist', MR, '{m.crash_type for m in mutants if m.crash_type}', 'set()', 'test_a_class_name_is_shown_only_when_it_is_on_the_allowlist_of_the_call', 'the crash_type of a mutant of this call was not shown'),
    kmutant("runner: the caller's shown_classes are not on the allowlist", MR, ' | set(shown_classes),', ',', 'test_a_class_name_is_shown_only_when_it_is_on_the_allowlist_of_the_call', 'a class the caller listed in shown_classes was not shown'),
    kmutant('runner: a class name of the caller that holds a secret is not replaced', MR, '    return _own_text(head, CLASS_HIDDEN, shown.secrets)', '    return head', 'test_the_second_layer_replaces_a_whole_slot_of_caller_text_that_holds_a_secret', 'a class name of the caller that holds a secret was not replaced whole'),
    kmutant('runner: a test id that holds a secret is not replaced', MR, '            own = _own_text(f"{text}{tail}::{function}", ID_HIDDEN, shown.secrets)', '            own = f"{text}{tail}::{function}"', 'test_the_second_layer_replaces_a_whole_slot_of_caller_text_that_holds_a_secret', 'a test id that holds a secret was not replaced whole by the fixed text'),
    kmutant("runner: an expect text that holds a secret is not replaced", MR, '        word = found + _own_text(expect, EXPECT_HIDDEN, shown.secrets)', '        word = found + expect', 'test_the_second_layer_replaces_a_whole_slot_of_caller_text_that_holds_a_secret', 'an expect text that holds a secret was not replaced whole'),
    kmutant("runner: a mutant name that holds a secret is shown in the canary message", MR, '    name = _own_text(m.name, MUTANT_HIDDEN, shown.secrets)', '    name = m.name', 'test_the_second_layer_replaces_a_whole_slot_of_caller_text_that_holds_a_secret', 'a mutant name that holds a secret was not replaced whole in the canary message'),
    kmutant("runner: the second layer cuts the secret out of a slot instead of replacing the slot", MR, '    return fixed if _holds_secret(text, secrets) else text', '    return _masked(text, secrets)', 'test_a_test_id_that_holds_the_password_is_the_fixed_text_and_never_a_name_with_a_piece_cut_out', 'a test id was shown with a piece cut out of a file name'),
    kmutant("runner: a bare assert line gets no fixed word", MR, '    if _BARE_ASSERT.match(raw.strip()):\n        return ASSERT_SHOWN\n', '', 'test_a_bare_assert_line_shows_the_fixed_word_assert', 'a bare assert line did not give the fixed word'),
    kmutant("runner: a name of Python itself goes through the second layer", MR, '    if head in _BUILT_IN_CLASSES:\n        return head\n', '', 'test_a_name_of_python_itself_is_shown_whole_also_when_it_holds_the_password', 'a name of Python itself was replaced'),
    kmutant("runner: a tests entry written with a leading dot is not put in the id form", MR, '    return PurePosixPath(test_path.replace("\\\\", "/")).as_posix().removesuffix(".py")', '    return test_path.replace("\\\\", "/").removesuffix(".py")', 'test_a_tests_entry_written_with_a_leading_dot_slash_still_shows_its_ids', 'did not give the id form of pytest'),
    kmutant("runner: the function that starts a child does not check the address", MR, '            _refuse_unsafe_address(name, source[name], hosts)\n            env[name] = source[name]', '            env[name] = source[name]', 'test_the_function_that_starts_a_child_checks_the_address_itself', 'the function that starts a child handed over an unchecked address'),
    kmutant("runner: a scheme in upper case is accepted", MR, 'rf"postgres(?:ql)?://', 'rf"(?i:postgres(?:ql)?)://', 'test_the_scheme_and_the_keys_are_lower_case_and_the_two_options_take_listed_values', 'a scheme that is not in lower case was accepted'),
    kmutant("runner: sslmode and connect_timeout take any value", MR, '        if key in _OPTION_VALUE and not _OPTION_VALUE[key].fullmatch(token):\n            return None\n', '', 'test_the_scheme_and_the_keys_are_lower_case_and_the_two_options_take_listed_values', 'an sslmode that is not listed was accepted'),
    kmutant("runner: a private XDG_RUNTIME_DIR is not used for the lock folder", MR, '    if runtime and os.path.isabs(runtime) and _own_private_dir(runtime):', '    if False:', 'test_the_lock_folder_prefers_the_runtime_folder_of_the_user_when_it_is_private', 'a private XDG_RUNTIME_DIR of this user was not preferred'),
    kmutant("runner: a link to a private folder counts as a private folder", MR, '        info = os.lstat(path)', '        info = os.stat(path)', 'test_a_link_to_a_private_folder_is_no_runtime_folder_for_the_lock', 'a link to a private folder was taken as a private folder'),
    kmutant("runner: a failed baseline with an unusable result file raises the parser error", MR, '    except _UNUSABLE_JUNIT:\n        first = ""', '    except ZeroDivisionError:\n        first = ""', 'test_a_failed_baseline_with_an_unusable_result_file_says_only_how_the_run_ended', 'did not give the run end alone'),
    kmutant("runner: the error for an unusable baseline result file is raised inside the except block", MR, '        unusable = type(exc).__name__\n', '        unusable = type(exc).__name__\n        raise RuntimeError(unusable) from None\n', 'test_no_error_the_runner_raises_keeps_another_exception_or_child_text_in_its_chain', 'keeps another exception in its chain'),
    kmutant('runner: the baseline failure message shows the line of the child', MR, '    return f"{message}: {_shown_line(first, shown)}" if first else message', '    return f"{message}: {first}" if first else message', 'test_a_failed_baseline_with_a_passed_value_says_how_it_ended_and_names_only_the_class', 'not the run end and the class name alone'),
    kmutant('runner: shown_classes is not checked', MR, '    classes = _checked_shown_classes(shown_classes)', '    classes = tuple(shown_classes)', 'test_shown_classes_takes_plain_class_names_only_and_is_checked_before_anything_runs', 'a shown_classes entry that is no class name was accepted'),
    kmutant('runner: the run does not call the address check', MR, '            _refuse_unsafe_address(\n                env_name,\n                environ[env_name],\n                hosts,\n                (*classes, *(m.crash_type for m in mutants if m.crash_type)),\n            )\n', '            pass\n', 'test_run_mutants_refuses_an_address_before_any_folder_or_run', 'run_mutants did not refuse an address the check refuses'),
    kmutant('runner: the host list is checked only when a variable is passed', MR, '    hosts = _checked_throwaway_hosts(throwaway_hosts)\n', '    hosts = tuple(throwaway_hosts)\n', 'test_the_host_list_is_checked_for_every_call_also_when_no_variable_is_passed', 'a host list with a pattern was accepted'),
    kmutant('runner: a unix socket folder with a dot-dot part is read as a folder', MR, '    return bool(_SOCKET_DIR.fullmatch(token)) and ".." not in token.split("/")', '    return bool(_SOCKET_DIR.fullmatch(token))', 'test_the_address_check_refuses_an_address_outside_the_grammar', 'an address outside the grammar was accepted'),
    kmutant('runner: a key that is not on the allowlist is accepted', MR, '        if key not in ADDRESS_KEYS_ALLOWED:\n            return None', '        if False:\n            return None', 'test_every_allowed_key_has_a_reason_and_a_refused_sibling', 'a key that is not on the allowlist was accepted'),
    kmutant('runner: a key written twice is accepted', MR, '        if key in seen:\n            return None', '        if False:\n            return None', 'test_no_key_of_a_key_value_address_may_be_written_twice', 'written twice was accepted'),
    kmutant('runner: a unix socket folder is accepted without being listed', MR, '        if host and host not in allowed:', '        if host and not host.startswith("/") and host not in allowed:', 'test_a_unix_socket_folder_is_accepted_only_as_an_exact_member_of_the_host_list', 'a unix socket folder that is not listed was accepted'),
    kmutant('runner: an address with no host is accepted', MR, '    if not fields.get("host") and not fields.get("hostaddr"):', '    if False:', 'test_the_address_check_refuses_an_address_with_no_host', 'an address with neither host nor hostaddr was accepted'),
    kmutant('runner: a key=value host keeps its letter case', MR, '        found[key] = token.lower() if key in ("host", "hostaddr") and not socket else token', '        found[key] = token', 'test_the_grammar_reads_the_parts_that_the_address_check_uses', 'a host name of a key=value address was not read in lower case'),
    kmutant('runner: a unix socket folder is read in lower case', MR, '        found[key] = token.lower() if key in ("host", "hostaddr") and not socket else token', '        found[key] = token.lower() if key in ("host", "hostaddr") else token', 'test_the_grammar_reads_the_parts_that_the_address_check_uses', 'a unix socket folder was not read as written'),
    kmutant('runner: a listed host keeps its letter case', MR, '            chosen.append(host.lower())', '            chosen.append(host)', 'test_property_a_host_that_is_not_exactly_in_the_list_is_refused', 'a member written in another letter case was refused'),
    kmutant('runner: a listed name whose variable is absent does not switch the skip check on', MR, '        forbid_skips = bool(env_names)', '        forbid_skips = any(name in environ for name in env_names)', 'test_a_listed_name_whose_variable_is_absent_still_refuses_a_baseline_that_skips', 'a listed name whose variable is absent did not switch the skip check on'),
    kmutant('judge: judge_report counts a fixture or collection error as a kill', MU, '        if rc == 1 and (report.fixture_failed or report.collection_failed)', '        if False', 'test_judge_report_never_counts_a_fixture_or_collection_error_as_a_kill_and_judge_alone_would', 'a fixture or collection error was a kill'),
    kmutant('runner: every ERROR row with no failing test says no test was named', MR, '(NO_TEST_NAMED if rc == 1 else f"EXIT CODE {rc}")', '(NO_TEST_NAMED)', 'test_an_error_row_with_no_failing_test_names_the_exit_code_unless_it_is_one', 'did not name it'),
    kmutant('runner: a JUnit file that cannot be read stops the run', MR, '_UNUSABLE_JUNIT = (\n    OSError,\n', '_UNUSABLE_JUNIT = (\n', 'test_an_unreadable_junit_file_is_that_mutants_error_row_and_the_run_goes_on', 'denied', allow_crash=True, crash_type='PermissionError'),
    kmutant('runner: a lock folder of another user is accepted', MR, '    if info.st_uid != os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o077:', '    if False:\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o077:', 'test_a_lock_folder_of_another_user_is_refused', 'a lock folder of another user was accepted'),
    kmutant('runner: what was opened as the lock folder is not checked to be a folder', MR, '    if not stat.S_ISDIR(info.st_mode):\n        return "is not a folder"', '    if False:\n        return "is not a folder"', 'test_what_was_opened_as_the_lock_folder_must_be_a_folder', 'something that is not a folder was accepted'),
    kmutant('runner: the lock folder is opened without the folder and no-link flags', MR, 'os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW', 'os.O_RDONLY', 'test_the_lock_folder_is_opened_as_a_folder_without_following_a_link_and_the_file_is_made_under_it', 'the lock folder was not opened as a folder without following a link'),
    kmutant('runner: the lock file is opened by its path, not under the opened folder', MR, 'fd = os.open(name, flags, 0o600, dir_fd=folder)', 'fd = os.open(_lock_dir() / name, flags, 0o600)', 'test_the_lock_folder_is_opened_as_a_folder_without_following_a_link_and_the_file_is_made_under_it', 'the lock file was opened by a path'),
    kmutant('runner: the temp folder is removed and made again at a rebuild', MR, '        _empty_dir(tmp)\n', '        shutil.rmtree(tmp, ignore_errors=True)\n        os.mkdir(tmp)\n', 'test_every_folder_and_file_the_run_makes_is_private_under_umask_0_also_after_a_rebuild', 'were not private while it ran'),
    kmutant('runner: the temp folder is not checked before a rebuild empties it', MR, '        _refuse_unless_private(tmp, "temp folder")\n        _empty_dir(tmp)', '        _empty_dir(tmp)', 'test_the_temp_folder_is_checked_at_the_start_of_every_rebuild', 'was emptied before its mode was checked at the rebuild'),
    kmutant('runner: the temp folder is not checked after a rebuild', MR, '                )\n        _refuse_unless_private(tmp, "temp folder")\n\n    def fresh', '                )\n\n    def fresh', 'test_the_temp_folder_is_checked_after_a_rebuild_and_before_anything_is_removed_in_it', 'after the rebuild'),
    kmutant('runner: the snapshot folder is made without the private helper', MR, '        _make_private_dir(snap, "snapshot folder")', '        os.mkdir(snap)', 'test_every_folder_and_file_the_run_makes_is_private_under_umask_0_also_after_a_rebuild', 'were not private while it ran'),
    kmutant('runner: the snapshot folder is not checked after the copy', MR, '        _refuse_unless_private(snap, "snapshot folder")\n        _refuse_links_out(snap)', '        _refuse_links_out(snap)', 'test_the_snapshot_folder_is_checked_after_the_copy', 'was not checked after the copy'),
    kmutant('runner: the folder of the settings file is not checked', MR, '        ini_dir = _make_private_temp_dir("mutant_ini_", "folder of the pytest settings file")\n', '        ini_dir = Path(tempfile.mkdtemp(prefix="mutant_ini_"))\n', 'test_the_folder_of_the_settings_file_is_checked', 'was not checked'),
    kmutant('runner: the settings file is made by the umask', MR, '        _make_private_file(ini, "pytest settings file")\n', '        ini.write_text("", encoding="utf-8")\n', 'test_every_folder_and_file_the_run_makes_is_private_under_umask_0_also_after_a_rebuild', 'were not private while it ran'),
    kmutant('runner: the result file is made by the umask', MR, '        _make_private_file(junit, "result file")\n', '        open(junit, "w").close()\n', 'test_every_folder_and_file_the_run_makes_is_private_under_umask_0_also_after_a_rebuild', 'were not private while it ran'),
    kmutant('runner: a folder check uses stat and follows a link', MR, '        problem = _dir_problem(os.lstat(path))', '        problem = _dir_problem(os.stat(path))', 'test_a_folder_that_is_not_private_is_refused_with_its_reason', 'link'),
    kmutant('runner: a folder check never raises', MR, '``except`` block: the error keeps no other exception in its chain\n    if problem:\n        raise RuntimeError(f"the {what}', '``except`` block: the error keeps no other exception in its chain\n    if False:\n        raise RuntimeError(f"the {what}', 'test_a_folder_that_is_not_private_is_refused_with_its_reason', 'was accepted'),
    kmutant('runner: a folder that cannot be looked at is accepted', MR, '        problem = f"could not be looked at ({type(exc).__name__})"', '        problem = ""', 'test_a_folder_that_is_not_private_is_refused_with_its_reason', 'a missing folder was accepted'),
    kmutant('runner: a private folder is not put back to 0700', MR, '    if not _IS_WINDOWS:\n        os.chmod(path, 0o700)\n    _refuse_unless_private(path, what)', '    _refuse_unless_private(path, what)', 'test_a_private_folder_is_made_with_mode_0700_whatever_the_umask_and_never_over_a_name', 'under umask'),
    kmutant('runner: a private folder is made without the mode', MR, '    os.mkdir(path, 0o700)\n    if not _IS_WINDOWS:', '    os.mkdir(path)\n    if not _IS_WINDOWS:', 'test_a_private_folder_is_made_with_mode_0700_whatever_the_umask_and_never_over_a_name', 'was not given the mode 0700'),
    kmutant('runner: a private folder is not checked after it is made', MR, '        os.chmod(path, 0o700)\n    _refuse_unless_private(path, what)', '        os.chmod(path, 0o700)', 'test_a_private_folder_is_made_with_mode_0700_whatever_the_umask_and_never_over_a_name', 'was accepted right after it was made'),
    kmutant('runner: the parts between are made with the default mode', MR, '            _make_private_dir(here, "folder of the copy")\n        except FileExistsError:', '            os.mkdir(here)\n        except FileExistsError:', 'test_the_parts_between_are_made_private_too_and_a_file_in_the_way_is_refused', 'was made with mode'),
    kmutant('runner: a file in the way of a part is accepted', MR, '            if not here.is_dir():\n                raise', '            if False:\n                raise', 'test_the_parts_between_are_made_private_too_and_a_file_in_the_way_is_refused', 'a file in the way of a part was accepted'),
    kmutant('runner: emptying a folder follows a link', MR, '        if child.is_dir(follow_symlinks=False):', '        if child.is_dir():', 'test_emptying_a_folder_keeps_the_folder_and_its_mode_and_follows_no_link', 'was not emptied'),
    kmutant('runner: emptying a folder removes the folder', MR, '            with contextlib.suppress(OSError):\n                os.unlink(child.path)', '            with contextlib.suppress(OSError):\n                os.unlink(child.path)\n    os.rmdir(folder)', 'test_emptying_a_folder_keeps_the_folder_and_its_mode_and_follows_no_link', 'folder itself was removed'),
    kmutant('runner: a private file is not put back to 0600', MR, '            if _narrowable(os.fstat(fd)):\n                os.chmod(fd, 0o600)\n', '', 'test_a_private_file_is_mode_0600_whatever_the_umask_is_emptied_and_follows_no_link', 'had mode'),
    kmutant('runner: a private file is not emptied', MR, '        if not problem:\n            os.ftruncate(fd, 0)\n', '', 'test_a_private_file_is_mode_0600_whatever_the_umask_is_emptied_and_follows_no_link', 'was not made private and empty'),
    kmutant('runner: a private file follows a link', MR, '    flags |= getattr(os, "O_NOFOLLOW", 0)\n', '    flags |= 0\n', 'test_a_private_file_is_mode_0600_whatever_the_umask_is_emptied_and_follows_no_link', 'a link under the name of the file was followed'),
    kmutant('runner: a private file is made with a wide mode first', MR, '    fd = os.open(path, flags, 0o600)\n    try:', '    fd = os.open(path, flags, 0o666)\n    try:', 'test_a_private_file_is_mode_0600_whatever_the_umask_is_emptied_and_follows_no_link', 'before it was made private'),
    kmutant('runner: the lock folder is made with the default mode', MR, '            os.mkdir(path, 0o700)\n        fd = os.open(path, os.O_RDONLY', '            os.mkdir(path)\n        fd = os.open(path, os.O_RDONLY', 'test_the_lock_folder_and_the_lock_file_are_private_under_umask_0', 'was not made private'),
    kmutant('runner: a bare string for tests is read letter by letter', MR, '    _refuse_bare_string(tests, "tests")\n', '', 'test_a_bare_string_for_tests_is_a_type_error_not_letters', 'was read letter by letter'),
    kmutant('runner: a bare string for extra_dirs is read letter by letter', MR, '    _refuse_bare_string(extra_dirs, "extra_dirs")\n', '', 'test_a_bare_string_for_extra_dirs_is_a_type_error_not_letters', 'was read letter by letter'),
    kmutant('runner: a bare string for only is read letter by letter', MR, '    _refuse_bare_string(only, "only")\n', '', 'test_a_bare_string_for_only_is_a_type_error_not_letters', 'was read letter by letter'),
    kmutant('runner: a bare string for throwaway_hosts is accepted', MR, '    if isinstance(hosts, str):\n        raise TypeError("throwaway_hosts is', '    if False:\n        raise TypeError("throwaway_hosts is', 'test_a_bare_string_for_throwaway_hosts_is_a_type_error_not_letters', 'was read as hosts'),
    kmutant('runner: a bare string for shown_classes is accepted', MR, '    if isinstance(names, str):\n        raise TypeError("shown_classes is', '    if False:\n        raise TypeError("shown_classes is', 'test_a_bare_string_for_shown_classes_is_a_type_error_not_letters', 'was read as names'),
    kmutant('runner: the port limit is raised', MR, 'PORT_MAX = 65_535', 'PORT_MAX = 99_999', 'test_the_port_boundaries_are_the_tcp_port_numbers', 'the port limits are'),
    kmutant('runner: the port limit is lowered', MR, 'PORT_MAX = 65_535', 'PORT_MAX = 65_534', 'test_the_port_boundaries_are_the_tcp_port_numbers', 'the port limits are'),
    kmutant('runner: port 0 is allowed', MR, 'PORT_MIN = 1  #', 'PORT_MIN = 0  #', 'test_the_port_boundaries_are_the_tcp_port_numbers', 'the port limits are'),
    kmutant('runner: the port of a URL is not range checked', MR, '        if url.group(2) and not _port_in_range(url.group(2)):', '        if False:', 'test_a_port_is_one_to_five_digits_and_from_1_to_65535_in_both_forms', 'was accepted'),
    kmutant('runner: the port of a key=value address is not range checked', MR, '        if key == "port" and not _port_in_range(token):', '        if False:', 'test_a_port_is_one_to_five_digits_and_from_1_to_65535_in_both_forms', 'was accepted'),
    kmutant('runner: a URL port may have six digits', MR, '(?::([0-9]{{1,5}}))?/', '(?::([0-9]{{1,6}}))?/', 'test_a_port_is_one_to_five_digits_and_from_1_to_65535_in_both_forms', 'was accepted'),
    kmutant('runner: a lock folder inside the tree is accepted', MR, '    if lock.is_relative_to(base):', '    if False:', 'test_a_lock_folder_inside_the_tree_under_test_is_refused', 'a lock folder in the tree was accepted'),
    kmutant('runner: the lock folder is not resolved before the tree check', MR, '    lock = _lock_dir().resolve()', '    lock = _lock_dir()', 'test_a_lock_folder_inside_the_tree_under_test_is_refused', 'inside the tree'),
    kmutant('runner: the secrets are counted with a limit one too high', MR, '        if len(bases) > MAX_SECRETS:', '        if len(bases) > MAX_SECRETS + 1:', 'test_exactly_300_texts_to_search_for_are_accepted_and_301_are_refused', 'were accepted'),
    kmutant('runner: the secrets are counted with a limit one too low', MR, '        if len(bases) > MAX_SECRETS:', '        if len(bases) >= MAX_SECRETS:', 'test_exactly_300_texts_to_search_for_are_accepted_and_301_are_refused', '300 texts to search for were refused'),
    kmutant('runner: a file that is not a regular file passes the file check', MR, '    if not stat.S_ISREG(info.st_mode):\n        return "is not a regular file"\n    if info.st_uid != os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open to group or others (it must', '    if stat.S_ISDIR(info.st_mode):\n        return "is not a regular file"\n    if info.st_uid != os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open to group or others (it must', 'test_a_file_that_is_not_private_is_refused_with_its_reason', 'gave'),
    kmutant('runner: a file of a lower user number passes the file check', MR, '    if info.st_uid != os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open to group or others (it must', '    if info.st_uid < os.getuid():\n        return "belongs to another user"\n    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open to group or others (it must', 'test_a_file_that_is_not_private_is_refused_with_its_reason', 'gave'),
    kmutant('runner: a file with the owner run bit passes the file check', MR, '    if stat.S_IMODE(info.st_mode) & 0o177:\n        return "is open to group or others (it must', '    if stat.S_IMODE(info.st_mode) & 0o077:\n        return "is open to group or others (it must', 'test_a_file_that_is_not_private_is_refused_with_its_reason', 'gave'),
    kmutant('runner: a file with two or three names passes the file check', MR, '    if info.st_nlink > 1:\n        return "has more than one name"\n    return ""', '    if info.st_nlink > 2:\n        return "has more than one name"\n    return ""', 'test_a_file_that_is_not_private_is_refused_with_its_reason', 'gave'),
    kmutant('runner: a made file is not checked', MR, '            problem = _file_problem(os.fstat(fd))\n        if not problem:', '            problem = ""\n        if not problem:', 'test_a_made_private_file_is_checked_on_the_open_file_and_a_second_name_is_refused', 'was accepted'),
    kmutant('runner: a made file that fails the check is not refused', MR, '    if problem:\n        raise RuntimeError(f"the {what} of this run {problem}")\n\n\ndef _lock_dir', '    if False:\n        raise RuntimeError(f"the {what} of this run {problem}")\n\n\ndef _lock_dir', 'test_a_made_private_file_is_checked_on_the_open_file_and_a_second_name_is_refused', 'was accepted'),
    kmutant('runner: a temp folder is not checked by its helper', MR, '        _refuse_unless_private(path, what)\n        checked = True', '        checked = True', 'test_a_temp_folder_is_made_by_the_one_helper_and_checked_and_a_refused_one_is_removed', 'was accepted'),
    kmutant('runner: a temp folder is not put back to 0700 when a umask took owner bits', MR, '        if not _IS_WINDOWS and stat.S_IMODE(os.lstat(path).st_mode) & 0o700 != 0o700:\n            os.chmod(path, 0o700)', '        if False:\n            os.chmod(path, 0o700)', 'test_a_temp_folder_is_made_by_the_one_helper_and_checked_and_a_refused_one_is_removed', 'under umask 0277'),
    kmutant('runner: a refused temp folder is left behind', MR, '        if not checked:\n            shutil.rmtree(path, ignore_errors=True)\n    return path', '        if not checked:\n            pass\n    return path', 'test_a_temp_folder_is_made_by_the_one_helper_and_checked_and_a_refused_one_is_removed', 'was left behind'),
    kmutant('runner: the tests folder of the copy is made without the private helper', MR, '        _make_private_dir(tmp / "tests", "tests folder")', '        os.mkdir(tmp / "tests", 0o700)', 'test_the_temp_folder_the_tests_folder_and_the_settings_folder_are_made_by_the_helpers', 'folders made by the helper'),
    kmutant('runner: the temp folder is made without the private helper', MR, '            made.append(_make_private_temp_dir("mutants_", "temp folder"))', '            made.append(Path(tempfile.mkdtemp(prefix="mutants_")))', 'test_the_temp_folder_the_tests_folder_and_the_settings_folder_are_made_by_the_helpers', 'mkdtemp was called outside the helper'),
    kmutant('runner: a creation site moved out of the helpers', MR, '    os.mkdir(path, 0o700)\n    if not _IS_WINDOWS:\n        os.chmod(path, 0o700)\n    _refuse_unless_private(path, what)\n\n\ndef _make_private_temp_dir', '    os.mkdir(path, 0o700)\n    if not _IS_WINDOWS:\n        os.chmod(path, 0o700)\n    _refuse_unless_private(path, what)\n    Path(path).joinpath("note").write_text("x", encoding="utf-8")\n\n\ndef _make_private_temp_dir', 'test_every_folder_and_file_the_runner_creates_is_made_by_one_of_the_helpers', 'a creation site that is not a private helper'),
    kmutant('runner: os.fchmod is used again', MR, '            if _narrowable(os.fstat(fd)):\n                os.chmod(fd, 0o600)', '            if _narrowable(os.fstat(fd)):\n                os.fchmod(fd, 0o600)', 'test_the_runner_does_not_call_os_fchmod_which_mypy_does_not_know_on_windows_before_python_3_13', 'was used again'),
    kmutant('runner: a built-in class name equal to a secret is shown', MR, '    folded = head.casefold()  # ONE rule for every name of ``shown.classes``: equal to a secret up to letter case hides the name\n    if any(secret.casefold() == folded for secret in shown.secrets):\n        return CLASS_HIDDEN\n', '', 'test_a_password_equal_to_a_built_in_class_name_is_not_shown_as_the_class', 'was shown as the class:'),
    kmutant('runner: a built-in class name equal to a secret in another letter case is shown', MR, 'secret.casefold() == folded for secret in shown.secrets', 'secret == head for secret in shown.secrets', 'test_a_password_equal_to_a_built_in_class_name_is_not_shown_as_the_class', 'in lower case was shown as the class'),
    kmutant('runner: a built-in class name is hidden for any secret that holds it', MR, 'secret.casefold() == folded for secret in shown.secrets', 'folded in secret.casefold() for secret in shown.secrets', 'test_a_password_that_holds_a_whole_class_name_does_not_hide_the_class', 'was hidden for a password that holds it'),
    kmutant('runner: a bare string for crash_markers is read letter by letter', MR, '        if isinstance(self.crash_markers, str):\n            raise TypeError("crash_markers is', '        if False:\n            raise TypeError("crash_markers is', 'test_a_bare_string_for_crash_markers_of_a_mutant_is_a_type_error_not_letters', 'was read letter by letter'),
    kmutant('runner: connect_timeout may have six digits', MR, '"connect_timeout": re.compile(r"[0-9]{1,5}"),', '"connect_timeout": re.compile(r"[0-9]{1,6}"),', 'test_connect_timeout_takes_one_to_five_digits_in_the_texts_and_in_the_code', 'connect_timeout='),
    kmutant('runner: the three bare-string guards come after the path check', MR, '    _refuse_bare_string(tests, "tests")\n    _refuse_bare_string(extra_dirs, "extra_dirs")\n    _refuse_bare_string(only, "only")\n    for t in (*tests, *extra_dirs):\n        _relative(t)\n', '    for t in (*tests, *extra_dirs):\n        _relative(t)\n    _refuse_bare_string(tests, "tests")\n    _refuse_bare_string(extra_dirs, "extra_dirs")\n    _refuse_bare_string(only, "only")\n', 'test_the_order_of_the_bare_string_guards_is_the_one_the_docstring_gives', 'the path check came before the guard of only'),
    kmutant('runner: the address step comes before the count of the secrets', MR, '    secrets = _secret_values(env_names, environ)\n    for env_name in env_names:  # a variable that is present, also with an empty text, must hold an address the check accepts\n        if env_name in environ:\n            _refuse_unsafe_address(\n                env_name,\n                environ[env_name],\n                hosts,\n                (*classes, *(m.crash_type for m in mutants if m.crash_type)),\n            )\n', '    for env_name in env_names:  # a variable that is present, also with an empty text, must hold an address the check accepts\n        if env_name in environ:\n            _refuse_unsafe_address(\n                env_name,\n                environ[env_name],\n                hosts,\n                (*classes, *(m.crash_type for m in mutants if m.crash_type)),\n            )\n    secrets = _secret_values(env_names, environ)\n', 'test_the_refusals_come_in_the_order_the_docstring_gives', 'was not the refusal the docstring gives'),
    kmutant('runner: the junction checks come after the temp folder is made', MR, '        _refuse_junctions(root, "src")\n        for d in extra_dirs:\n            if _inside(root, d).exists():\n                _refuse_junctions(root, d)\n        with _signals_held():\n            made.append(_make_private_temp_dir("mutants_", "temp folder"))\n', '        with _signals_held():\n            made.append(_make_private_temp_dir("mutants_", "temp folder"))\n        _refuse_junctions(root, "src")\n        for d in extra_dirs:\n            if _inside(root, d).exists():\n                _refuse_junctions(root, d)\n', 'test_a_junction_is_refused_before_any_folder_is_made', 'a folder was made before the junction'),
    kmutant('runner: a name the caller owns equal to a secret in another letter case is shown', MR, '    folded = head.casefold()  # ONE rule for every name of ``shown.classes``: equal to a secret up to letter case hides the name\n    if any(secret.casefold() == folded for secret in shown.secrets):\n        return CLASS_HIDDEN\n    if head in _BUILT_IN_CLASSES:\n        return head\n', '    if head in _BUILT_IN_CLASSES:\n        folded = head.casefold()\n        if any(secret.casefold() == folded for secret in shown.secrets):\n            return CLASS_HIDDEN\n        return head\n', 'test_every_name_of_shown_classes_is_hidden_when_equal_to_a_secret_in_any_letter_case', 'equal to the password'),
    kmutant('runner: the address check accepts a password equal to a class name', MR, '    names = {n.casefold() for n in (*_BUILT_IN_CLASSES, *class_names)}\n    if any(text.casefold() in names for text in _password_forms(env_name, value)):\n        raise ValueError(CLASS_NAME_REFUSAL.format(env_name=env_name))\n', '', 'test_a_password_equal_to_the_class_the_child_raises_is_refused_before_any_run', 'a built-in class name was accepted'),
    kmutant('runner: the address check compares a password to a class name in the same letter case only', MR, 'if any(text.casefold() in names for text in _password_forms(env_name, value)):', 'if any(text in names for text in _password_forms(env_name, value)):', 'test_a_password_equal_to_the_class_the_child_raises_is_refused_before_any_run', 'a built-in class name was accepted'),
    kmutant('runner: the address check gets no class name of the caller', MR, '                (*classes, *(m.crash_type for m in mutants if m.crash_type)),\n', '                (),\n', 'test_run_mutants_gives_its_crash_types_and_shown_classes_to_the_address_check', 'accepted a password equal to a name of the call'),
    kmutant('runner: the folders between are made without the private helper', MR, '            _make_private_dir(here, "folder of the copy")\n', '            os.mkdir(here, 0o700)\n', 'test_the_parts_between_are_made_by_the_private_helper_also_under_umask_0277', 'under umask 0277 the part'),
    kmutant('runner: a private file is emptied before it is checked', MR, '    flags = os.O_WRONLY | os.O_CREAT\n', '    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC\n', 'test_a_file_with_a_second_name_keeps_its_content_when_it_is_refused', 'was emptied before it was refused'),
    kmutant('runner: a file with a second name is narrowed before it is checked', MR, '            if _narrowable(os.fstat(fd)):\n', '            if True:\n', 'test_a_file_with_a_second_name_keeps_its_mode_when_it_is_refused', 'was narrowed before it was refused'),
    kmutant('runner: a named pipe under the name of a made file blocks the open', MR, '    flags |= getattr(os, "O_NONBLOCK", 0)\n', '    flags |= 0\n', 'test_a_named_pipe_under_the_name_of_a_made_file_does_not_block_the_open', 'blocked the open for writing'),
    kmutant('runner: a built-in class name is hidden for a password that is a piece of it', MR, 'secret.casefold() == folded for secret in shown.secrets', 'secret.casefold() in folded for secret in shown.secrets', 'test_a_password_that_is_only_a_piece_of_a_class_name_does_not_hide_the_class', 'was hidden for a password that is a piece of it'),
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
        [TEST, KW],
        extra_dirs=("tests/fixtures", "tools"),
        conftest="tests/conftest.py",  # the guard fixture of the database address is mutated too
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)

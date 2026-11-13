# lane3-fix-5 round 2 (builder B5b), applies the 4 MINOR findings of review-lane3-fix-5-r1.md
Patch: evidence/lane3-fix-5-r2.patch (full diff against f3c39cf8; replaces lane3-fix-5.patch, which is kept). sha256 is printed at the end of this file's creation step: see below.
Deviations and gaps first
- Brief item 3b said a pid file "abc" / "1 ; true" must exit 6. It does not, on old or new script: `ps -p abc` fails, so the file counts as stale (removed, reset goes on, exit 0). I kept that behaviour and tested what is true: exit 0, pid file removed, a marker file proves nothing from the pid file's text was run (4 texts incl. `$(...)` and backticks). These 4 tests PASS on the old script too (regression guards, not defect tests).
- One xdist run (of about 17 under `-n 2`) failed test_reset_sh_treats_a_pid_file_of_an_ended_but_uncollected_process_as_gone (pre-existing test); I did not capture the message and could not reproduce in 16 reruns. Cause unknown; not fixed.
- A really empty /proc cmdline could not be built portably; finding 1 is tested with a stand-in `tr` that prints nothing (a live pid, real /proc).
- Existing `# noqa` in tests/test_reset_scripts.py and the moved `_run` (S603) are untouched (not part of the finding); the new test file has 0 noqa.
Findings
| # | change | proof | first failure line (old) |
|1| reset.sh proc_args: /proc result accepted only if non-empty (global var proc_line, no `local`), else `ps -ww`, else `ps` | test_proc_args_asks_ps_when_proc_gives_an_empty_command_line | on lane3-fix-5 (r1) script: `AssertionError: assert ('', 0) == ('[kernel-thread]\n', 0)`; passes patched |
|2| `book` fixture moved to tests/conftest.py; reset_run, reset_kept, RESET_SCRIPT, WINDOWS to tests/support.py (free_port already there, same code, reused); no noqa in new file | tests/test_reset_scripts.py: 45 passed before and after | n/a |
|3a| 4 `bash -c` tests on the function text cut from reset.sh, PATH-shadowed `ps` stub recording args: non-numeric pid -> `-ww` first (1 call); -ww fails -> plain ps second; live pid -> /proc used, ps not called | pass patched | old script: `ValueError: substring not found` (no proc_args function) |
|3b| 4 pid-file texts run nothing (see deviation) | pass old and patched | passes on old |
|4| test 3 (COLUMNS=20) run on OLD script (f3c39cf8 reset.sh + new tests) | fails | `AssertionError: ('', 'refused: pid N in .../desk.pid is not the desk or the demo server; ...` (exit 6, wanted 5). Tests 1 and 2 fail the same way on old. |
procps 4.0.4 on a 406-char command line (marker last): plain `ps` COLUMNS=80 -> 80 chars, marker cut; COLUMNS=20 -> 20 chars, cut; COLUMNS=1 -> 3 chars (small minimum), cut; `ps -ww` -> 406 chars, marker present for all. So 20 is honoured (no 80 floor) and the test is valid.
Other hygiene fix: first draft had the literal ":/bin" in PATH (test_hygiene hardcoded-literal scan failed); now uses os.environ PATH.
Counts (patched, files staged with git add -A in /home/user/work/b5b-base): xdist `-n 2` (q1-xdist-venv) test_reset_scripts + test_reset_ps_width: 56 passed (0 failed; 1 unexplained flake in an earlier run, see above). Serial test_reset_scripts + new file + test_hygiene: 76 passed, 4 skipped, 0 failed. Old script + new tests: 7 failed, 4 passed (3 width tests, 4 proc_args tests fail; 4 pid-file tests pass).
git apply --check on fresh f3c39cf8: OK. After claims-stack-on-f3c39cf8.patch: OK. After + lane3-fix-1-r2.patch: OK. After + lane3-fix-3-r3.patch: OK. No conflicts (the --check output was empty at each step).
Worktrees (left, mine): /home/user/work/b5b-base b5b-old b5b-r1 b5b-clean b5b-chk; temp /home/user/work/b5b-tmp.
sha256 of lane3-fix-5-r2.patch: d6edf82cbf1d87af7a97fcebe6ff7e0f8cbc8fc4258a4c85696ca8cf108ad09f

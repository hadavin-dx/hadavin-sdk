# F7 results (builder; numbers below are builder-claimed, not independently run)

FAILED / UNCERTAIN FIRST
- start_all.ps1 / reset.ps1 cannot run here (no PowerShell). The new `catch { ...; exit 4 }` in start_all.ps1 is pinned by a text test only, never executed.
- tests/test_hygiene.py: 4 tests SKIP here (no gitleaks program): the secret-scan checks did not run. Not run: the full suite, mutation sample, other test files.
- Run under `unshare -n` + lo_up (loopback only). No prompt appeared; nothing answered y.
- My first edit of start_all.ps1 turned its CRLF line endings into LF (python text mode). Found by `diff -rq`, fixed (CRLF restored), patch rebuilt, re-verified (below).

## 1. Regression test_demo_launchers_name_the_demo_file_and_the_off_switch (tests/test_lead_step_route.py)
Right fix = the TEST. The test is for: the launcher names the demo file before the first read of the settings. That first read now sits inside scripts/desk_setting.py, called as `desk_setting data-dir` (sh) / `Get-DeskSetting 'data-dir'` (ps1). The `python -c` index is replaced by those call sites; the other asserts (off switch, demo file, nudge address) are unchanged.
Mutation shown: start_all.sh with `set DESK_LEADFLOW_FILE=off` text removed -> the test FAILS (AssertionError at test_lead_step_route.py:437). Unmutated: passes.

## 2. Bug class: a folder under the lead-book path that cannot be made raised a traceback (the standard: a CLI refuses bad input with one line and its documented exit code, never a stack trace)
Reproduced before: DESK_DB_PATH=/dev/null/x.db -> FileExistsError traceback, exit 1; /proc/<name>/book.db -> FileNotFoundError traceback printing the typed name '/proc/zzname'.
Fix at the choke point (src/lead_desk/desk.py, beside book_problem):
- `_folder_part_is_not_a_folder` (looks only) is now part of `book_problem` (so Desk(), server.main, run_real_check, desk_setting all get it): /dev/null/x.db -> "the desk refuses to start: the lead book folder cannot be made: a part of its path is a file (or a pipe or a device), not a folder", exit 4.
- new `make_book_folder` = the one place the desk makes that folder; catches OSError/ValueError and answers one fixed line (no typed path). server.py:~1140 now calls it instead of `.parent.mkdir`. /proc case -> "...cannot be made here (no such place, or no write access)", exit 4, no lock file made.
- scripts/desk_setting.py `data-dir` also runs book_problem (so start_all.sh/.ps1 refuse before `mkdir`); start_all.sh `mkdir -p` and start_all.ps1 `New-Item` now end in the same refusal line + exit 4 instead of the shell's own message (which printed the typed path).
Sibling sweep (grep mkdir|makedirs|New-Item in src scripts tools demo_only load_tools):
- server.py:1140 FIXED. start_all.sh:25 FIXED. start_all.ps1:18 FIXED (text-pinned only).
- live_claude.py:163 not needed: already inside try/except OSError -> LiveCapReached line.
- run_real_check.py:1295 not needed: already try/except (OSError, ValueError) -> refusal, after folder_part_is_a_file/folder_cannot_be_made look.
- run_real_check.py:193 not needed: makes a sub-folder inside the run folder made one step before (a temp dir of its own).
- tools/, demo_only/, load_tools/: no mkdir on a user-given path.
- Note: scripts/precheck.py has a similar look (folder_part_is_a_file); src cannot import scripts, so desk.py has its own 10-line copy. Duplication is real; merging needs the owner's call on where shared code lives (not done).
New tests: tests/test_book_folder_refusals.py (8 tests): child-process desk main() for file/deeper file/link-to-nothing/device/pipe in the way + /proc; make_book_folder and book_problem directly; a property test (150 generated paths, fixed seed, file at a random depth; also checks nothing is made over the file and a free chain is made); start_all.sh run for the same set + /proc; text pin for ps1/sh/helper.
Fails on old code (old src+scripts, constants stubbed so the file imports): 7 failed, 1 passed (the pipe test, old behaviour already right). Raw: out/F7/failing-before.log (e.g. `'FileExistsError|[Errno 17] File exists: ...zqx-typed-name'` instead of exit 4).
Passes after: out/F7/passing-after.log.

## 3. Mutation survivor (start_all.sh without its `data-dir` desk_setting call)
Killed by test_start_all_sh_refuses_a_book_folder_that_cannot_be_made_in_one_line (settings are all valid, only the data-dir call can see the bad folder). Scratch copy, line `data_dir="$(desk_setting data-dir)"` deleted: `2 failed, 21 passed` over test_wrapper_setting_refusals.py + test_book_folder_refusals.py (the two start_all.sh tests of the new file fail). Raw: out/F7/mutant-M8b-killed.log. Scratch copy removed.
(The /proc test also kills removal of the mkdir guard: not mutated separately; not run.)

## Runs (final tree, loopback only)
- Big run: test_book_folder_refusals, test_lead_step_route, test_hygiene, test_reset_scripts, test_cli_refusals, test_file_reader_refusals, test_special_files_and_plain_text, test_special_output_files, test_script_refusals_feed, test_wrapper_setting_refusals, test_take_script_refusals, test_reset_ps1_links: `526 passed, 4 skipped in 223.46s` (the 4 skips are gitleaks).
- After a pure refactor of make_book_folder + docstring wrap (made while that run was going): re-ran book_folder, wrapper_setting, special_output_files, lead_step_route, take_script_refusals: `233 passed in 208.15s`.
- After the CRLF fix: test_book_folder_refusals + test_wrapper_setting_refusals + test_lead_step_route: `43 passed`.
- ruff check: All checks passed (touched .py). ruff format --check (repo line length 120): 5 files already formatted. bandit -ll -r src tools scripts: exit 0.

## Files
src/lead_desk/desk.py, src/lead_desk/server.py, scripts/desk_setting.py, scripts/start_all.sh, scripts/start_all.ps1 (CRLF kept), tests/test_lead_step_route.py, tests/test_book_folder_refusals.py (new).
Patch: out/F7/f7-on-combine.patch (7 files). `git apply --check` + apply on a fresh copy of tree-COMBINE: applied; `diff -rq` (excluding .git, caches, data) IDENTICAL. Tree: /home/user/build/rr6/tree-F7 (no commit made). No process of mine left running (only monitors that timed out; no pytest of tree-F7 alive).

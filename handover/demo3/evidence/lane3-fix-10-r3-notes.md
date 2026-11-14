# lane3 fix-10 round 3: builder B20 notes

Base f3c39cf89ec989f032ea48a23cfd824b88da9c68. Tree `/home/user/work/b20-tree` (not committed; `git add -A` then edits). Python 3.13.
Patch: `evidence/lane3-fix-10-r3.patch` (the WHOLE fix-10 against the base; it REPLACES `lane3-fix-10-r2.patch`), recut `lane3-fix-10-r3-recut.patch`,
five part files in `evidence/lane3-fix-10-r3-parts/` (each under 90 KB). Hashes and tree hash: `evidence/raw/b20-patch-sha256.txt`.
Plan implemented: `resolve-lane3-fix-10-r2.md`.

## FAILED / NOT RUN / NOT CHECKED (read first)
FAILED (and fixed in this round, so they are history, not open):
- FIRST full run on the final-looking head: 13 failed, 4147 passed, 211 skipped (`raw/b20-full-first-FAILED-13.log`). 12 were in `tests/test_real_check_dry.py`, a file I had NOT run among my touched files (my slip: I ran only the files I edited, not the files that call `run_real_check`); 1 was `tests/test_hygiene.py` (a made-up address with user and password written out in one string in my own new test). Fix at the class: a refused SETTING of `run_real_check` gave exit 2 for some values and 8 for others (e.g. REAL_DRAIN_SECONDS=0 gave 2, =nan gave 8). Now every refused setting of that script is exit 8 (missing required name, REAL_PERSONS too low, a range, bad mailbox folder, an old book file, a bad config line, a file the config names that cannot be used) and exit 2 only means a wrong command line (no --config, --assume-yes without --dry-fakes) or a missing tool (openssl). Tests (`test_real_check_dry.py`, `test_path_confinement.py`, `test_bad_setting_entry_points.py`), `docs/settings.md` and the table meaning text changed to match. 25 of those changed tests fail on the old code (raw/b20-fails-before.log, supplement).
- First lint run (ruff, mypy, bandit; `raw/b20-lint-first-run-findings.log`): 5 ruff findings (2 import order, 1 unused `re`, S603, S607) and 2 unformatted files; fixed. Hand 120-column sweeps with awk had not caught them. mypy linux and win32 and bandit were clean.
- Second full run on the FINAL head (lint-clean, in a clone nobody else used, Python 3.13, DPLD_REQUIRE_SCAN=1, gitleaks on PATH, no extra git ref, no data/): `4160 passed, 211 skipped in 924.97s`, no failure, no KeyboardInterrupt (`raw/b20-full-final.log`). The 211 skips are the repo's own skips (Windows-only, tools not installed); I did not list them one by one. Note: that run had 3 other builders' test runs on the same 4 cores, so timing tests ran under load; the timing-sensitive guards were then run ALONE on the same head: `tests/test_clock_steps.py tests/test_burst_retry.py` 47 passed rc=0 (`raw/b20-guard-wallclock-alone.log`), `tests/test_hygiene.py` 24 passed rc=0 (`raw/b20-guard-hygiene-alone.log`). I took "wall-clock guard test" to mean the two wall-clock-step files; if the lead meant another file, it was part of the full run only.
- Lint after the fixes, on `git ls-files` of the final index in a clean folder: ruff check rc=0, ruff format --check rc=0, mypy linux rc=0, mypy win32 rc=0, bandit -ll rc=0 (`raw/b20-lint-*.log`). The lint fixes touched six files BEFORE the passing full run, so no change followed it.
- Failing-before (`raw/b20-fails-before.log`), split: 27 real-behaviour failures, 8 function-absent, 6 text/syntax-tree checks, 9 text-only ps1 pins; `tests/test_start_all_late_refusal.py` (20 tests) could not even be imported on the old code, so those are not counted one by one. `tests/test_late_refusal_value_echo.py` passes on the old code: the old code already hid named values at those sites, so it is a pin, not proof of a fix. Plus the 25 of the supplement above.
- Mutation (`raw/b20-mutation.log`): 19 planted changes, 19 killed.
- Not covered by the unchanged-tree run: `docs` and `contract.md` text checks other than the tests above.

## What I did not run or check
- PowerShell: nothing here runs `start_all.ps1` or `reset.ps1` (no Windows, no pwsh). The tests on the new `start_all.ps1` are TEXT-ONLY pins (each has a
  mutant it must reject); they prove the lines are present, not that Windows PowerShell 5.1 does the right thing. Four new Windows-only tests (a bad
  setting, a bad nudge address, a late refusal, a taken port) are skipped here. The Windows run stays open under rule 2(c) (needs a Windows machine).
- Python 3.12: not run (only 3.13).
- Bible rule texts (R448 and others): not read here; I cite R448 only as the brief did.
- CodeQL, SonarCloud, CodeRabbit: not run (CI only). ruff, mypy, bandit were run (see above).
- The whole stack (fix-5 r7, fix-8 r3, core-fix-on-frozen-r7e): not applied; this tree is the r2 base plus this round only.

## What the stack builder must change (fix-5 r7 adds reset exit 7; it is NOT in my tree)
1. `src/lead_desk/constants.py`: add `EXIT_RESET_<name> = 7` (fix-5 r7's meaning text as a `MEANING_*` constant) and the rows `("reset.sh", 7, ...)` and
   `("reset.ps1", 7, ...)` to `_RESET_ROWS` (the two reset scripts keep one list; `test_the_two_reset_scripts_have_one_list_of_codes` fails if only one gets it).
2. Check `SAME_NUMBER_DIFFERENT_MEANING`: 7 must not be added unless 7 means something else in another program (computed test fails and says so).
3. `contract.md`: where it says the reset codes run "2 to 6", write "2 to 7". `docs/settings.md` "Exit codes" section: add the 7 row for the reset scripts.
4. `README.md` line 90 (the reset refusal sentence) and the note at line 68: add the 7 case; I did not touch README (fix-5's file).
5. `tests/test_reset_scripts.py`: the start_all stand-in now needs a listening demo-server port (see the stub); fix-5 r7's tests that call `start_all.sh` need the same `STUB_FAKES_PORT`/`STUB_REAL_PYTHON` environment.
6. Check whether core-fix-on-frozen-r7e is in the stack; if it touches `config.py` path readers, they must go through `envnum.env_path` (the AST test `test_no_path_is_read_from_setting_text_except_through_the_one_helper` fails otherwise).

## Decisions where the plan was terse
- Exit rule for `run_real_check`: 8 = a setting was refused; 2 = wrong command line or missing tool; 1/3 unchanged. (Added after the first full run; see above.)
- Exit table is keyed by PROGRAM (server, crash_desk, feed, reset.sh, reset.ps1, reset_check, start_all.sh, start_all.ps1, run_real_check). The same text in two programs
  is one meaning. `SAME_NUMBER_DIFFERENT_MEANING = (1, 2, 3, 4, 5)` is pinned; a test computes the overlap from the table and compares.
- `start_all` passes on ONLY desk codes 3, 4, 5. Any other desk code (0, 1, 2, 137, ...) becomes the script's own 1, because 2 is already "not bash" in the .sh and must not be read as a desk code.
- "Not ready in time" stays exit 1 (recommendation: keep it; the desk may still be starting, which is not a refusal). The message says so.
- One waiting budget `START_ALL_WAIT_SECONDS` (whole number 1 to 999, default 15, not a DESK_ setting) covers both the demo-server wait and the desk wait; a distinct message tells "the demo server did not start" from "desk not ready".
- Scrub trade-off: the value of any setting the message NAMES is blanked, even if harmless (a valid word). That is the safe backstop; settings the message does not name stay readable unless their name is secret-like (KEY, PASSWORD, SECRET, TOKEN, USER, FROM, RECIPIENT, ADDRESS, URL, HOST, `_TO`).
- `run_real_check.py` cannot use `config_or_exit` for its whole block (its env comes from a config file), so it keeps the bare `Config.from_env` inside its own try (allow-listed in the guard test); the except branch uses `refusal_line` and exit 8. Its own `scrub()` is deleted.
- `server.main` keeps its own reader: it must print on stdout and exit 4 (the desk's code), `config_or_exit` prints on stderr and exits 8. One-sentence reason is in the `config_exit` docstring and `contract.md`.
- Row 19 (one shared `Read-DeskSetting`): the resolve file itself says DECLINE (the copies stay; a pin test checks they are equal). Nothing changed there.
- Renamed `EXIT_SETTING_REFUSED` to `EXIT_OPEN_FILE_LIMIT` (it was the open-file-limit code 3 and shared a name with the setting refusal): `server.py`, `tests/test_stall_eviction.py`.
- "refused:" lines no longer carry the exception class name.

## Share of the plan covered
Every row of the resolve file is done in the tree except row 19 (the plan declines it) and the fix-5 r7 exit 7 (not in this tree; instructions above). Rows with a Windows part are done as text plus skipped Windows-only tests.

## What I re-checked by diff
- `b20-tree` equals `b20-final` (the clone the full run used): `diff -rq` with no output (excluding .git, data, caches).
- Whole patch, the five parts and the final tree give the same git tree hash on two fresh worktrees; the recut has the same sha256.
- After wrapping long lines (an automatic comment/docstring rewrap plus hand edits) I checked: the only changes the wrap tool made are comment and docstring lines, and one shell stub line in `tests/test_reset_scripts.py`, which now spans two lines inside a Python `-c` bracket (valid; the suite passes).
- Pre-existing over-120 lines in changed files (`config.py` 2, `tests/support.py` 1) were wrapped too.

## R-numbers
R448 (as in the brief). Others not re-read.

## Files changed (29, `git diff --cached --name-only` of the final clone)
- contract.md
- docs/settings.md
- docs/tests.md
- scripts/crash_desk.py
- scripts/feed.py
- scripts/reset.ps1
- scripts/reset.sh
- scripts/reset_check.py
- scripts/run_real_check.py
- scripts/start_all.ps1
- scripts/start_all.sh
- src/lead_desk/config.py
- src/lead_desk/config_exit.py
- src/lead_desk/constants.py
- src/lead_desk/crm_hubspot.py
- src/lead_desk/envnum.py
- src/lead_desk/server.py
- src/lead_desk/smtp_provider.py
- tests/support.py
- tests/test_bad_setting_entry_points.py
- tests/test_exit_code_table.py
- tests/test_late_refusal_value_echo.py
- tests/test_path_confinement.py
- tests/test_ps1_pins.py
- tests/test_real_check_dry.py
- tests/test_reset_scripts.py
- tests/test_setting_reader_guard.py
- tests/test_stall_eviction.py
- tests/test_start_all_late_refusal.py

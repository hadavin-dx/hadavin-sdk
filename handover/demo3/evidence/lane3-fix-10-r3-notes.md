# lane3 fix-10 round 3: builder B20 notes

Base f3c39cf89ec989f032ea48a23cfd824b88da9c68. Tree `/home/user/work/b20-tree` (not committed; `git add -A` then edits). Python 3.13.
Patch: `evidence/lane3-fix-10-r3.patch` (the WHOLE fix-10 against the base; it REPLACES `lane3-fix-10-r2.patch`), recut `lane3-fix-10-r3-recut.patch`,
five part files in `evidence/lane3-fix-10-r3-parts/` (each under 90 KB). Hashes and tree hash: `evidence/raw/b20-patch-sha256.txt`.
Plan implemented: `resolve-lane3-fix-10-r2.md`.

## FAILED / NOT RUN / NOT CHECKED (read first)
@@RESULTS@@

## What I did not run or check
- PowerShell: nothing here runs `start_all.ps1` or `reset.ps1` (no Windows, no pwsh). The tests on the new `start_all.ps1` are TEXT-ONLY pins (each has a
  mutant it must reject); they prove the lines are present, not that Windows PowerShell 5.1 does the right thing. Four new Windows-only tests (a bad
  setting, a bad nudge address, a late refusal, a taken port) are skipped here. The Windows run stays open under rule 2(c) (needs a Windows machine).
- Python 3.12: not run (only 3.13).
- Bible rule texts (R448 and others): not read here; I cite R448 only as the brief did.
- `ruff`, `mypy`, `bandit`: not run (CI only). I swept 120-column lines with awk and unused imports with a scratch script instead.
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

## Files changed (27)
@@FILES@@

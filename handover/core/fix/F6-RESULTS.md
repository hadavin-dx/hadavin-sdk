# F6 RESULTS (tree RR/tree-F6, baseline e23a1cb, nothing committed; new files marked with `git add -N` so they show in the diff)

## What failed, is uncertain, or was not run (first)
1. The two .ps1 wrappers (reset.ps1, start_all.ps1) were NOT run (no PowerShell here). They are pinned by a text test only
   (tests/test_wrapper_setting_refusals.py::test_no_wrapper_builds_a_config_inside_python_dash_c_any_more). On a Windows machine
   the same test file runs them for real (it uses the `_run` helper of test_reset_scripts, which switches to PowerShell there).
2. `tests/test_hygiene.py::test_hygiene_scan_public` FAILS in the final run. It also fails on the baseline: it lists
   tests/test_special_files_and_plain_text.py:156-194 (F3's file, literal http addresses). None of my files is in its list
   (checked after `git add -N`, so the scan, which reads tracked files, sees them). I did not touch F3's file: the lead decides.
3. Not run: the full suite, mutation, Windows (O_BINARY, no pipes), macOS, browser tests (no playwright), gitleaks, load runs.
   The neighbour run is 31 test files: `1838 passed, 13 skipped, 1 failed` (the failure is item 2), 650 s.
4. A pipe named as the spend ledger or the lock file did NOT hang on this Linux before the fix: opening a pipe for read and write
   does not wait, and the later seek fails by accident. The 6 ledger cases (3 kinds x 2 sites) pass on old code (they are pins).
   The `lock` site was worse than a refusal: on old code the lock file on a pipe gave `LockUnavailableError ... UnsupportedOperation`
   only by accident; the wanted text now is fixed (`NotRegularFile`). Real hangs on old code: trace.py (append "a"), run_stats `.tmp`
   ("w"), fake_model_server call log, catcher --out, load_driver --log and its `.partN` files (see failing-before.log: `waited for ever`).
5. I did NOT use O_NOFOLLOW: it would also refuse a link to a regular file, which an operator may use for a log. A link to a pipe is
   refused anyway because the kind is read from the OPEN handle (fstat), not from the name.
6. The brief file also holds the F4 and F4b texts (lines 7-17). I followed only the F6 task (lines 18-21).

## Bug class
Writer side: a path the operator names for OUTPUT is opened without checking its kind. Opening a pipe (FIFO) write-only waits
until someone reads (POSIX open(2) O_WRONLY on a FIFO blocks; O_NONBLOCK makes it fail with ENXIO); a pipe, device or socket is
not a file to append to. Also found, same class: a pipe/folder named as the lead book (DESK_DB_PATH) ended in a raw
`sqlite3.OperationalError: disk I/O error` traceback after the lock file was already made.
Wrapper side: CWE-248 (uncaught exception) and CWE-209 (error text leaks internals): the four wrappers ran `python -c "...Config.from_env()..."`
so a bad DESK_* value showed a Python traceback and exit 1 instead of the desk's refusal line and exit 4.

## Fix (choke points)
- src/lead_desk/regfile.py: new `open_output(path, mode, encoding)` beside `open_regular` (modes "a", "a+b", "w"): os.open with
  O_NONBLOCK|O_CLOEXEC|O_BINARY, O_CREAT (new names are created, mode 0o666 minus umask, as open() does), fstat on the open handle,
  anything but a regular file -> NotRegularFile (an OSError; also ENXIO, EISDIR, NUL in the name); "w" empties the file only AFTER the check.
- tools/pathconfine.py `_step(..., written=True)` (called only from `_locate`, i.e. `confine`): an existing pipe/device/socket for a written
  file -> PathRefused. This is the choke point for every tool/load_tools output (they already pass `confine`; they cannot import src).
- src/lead_desk/desk.py `book_problem` (the check main runs BEFORE the lock step, and Desk repeats): existing path that is not a regular
  file -> refusal `the desk refuses to start: the lead book path names a pipe, a device or a folder: ...`, exit 4, no `.lock` left.
- Wrappers: new scripts/desk_setting.py (`db-path | data-dir | fakes-port | port`) prints the value, or `the desk refuses a setting: <text>`
  and exit 4 (the desk's own code; text names the setting, never the value), usage + exit 2 for a wrong command line. reset.sh/start_all.sh
  call it through a small `desk_setting` shell function (prints the line to stderr, exits with its code); the .ps1 pair through `Get-DeskSetting`.
- README.md:90 states the new exit-4 case in plain words.

## Every changed file:line (git diff e23a1cb)
src/lead_desk/regfile.py (open_output, ~48-90) | lockfile.py:53 | live_claude.py:~163, ~292 | trace.py:58 | run_stats.py:17-19 |
desk.py (NOT_A_FILE_BOOK_PROBLEM, book_problem) | tools/pathconfine.py (_step, _locate, module text) | load_tools/load_driver.py:~362 (part files
confined) | demo_only/fake_model_server.py (log_call; main refuses a bad --call-log / --key-file, exit 2; the key file is now read with open_regular) |
scripts/desk_setting.py (new) | scripts/reset.sh:14-21 | start_all.sh:16-24,35 | reset.ps1:15-21 | start_all.ps1:10-17,29 | README.md:90 |
tests/test_reset_scripts.py (stub `python` answers `scripts/desk_setting.py data-dir|fakes-port|port`; comment) |
tests/test_special_output_files.py (new, 47 tests) | tests/test_wrapper_setting_refusals.py (new, 15 tests).

## Sibling sweep (every open( / os.open / .open( / write_text / write_bytes / touch / mkstemp / sqlite3.connect in src scripts tools load_tools demo_only)
SWITCHED to open_output: lockfile.py:53, live_claude.py:~163 (_FileLock) and ~292 (_append), trace.py:58, run_stats.py (the `.tmp` file), demo_only/fake_model_server.py log_call.
SWITCHED through `confine` (refuses a pipe): tools/scrub_n8n_export.py:207 (dst), load_tools/catcher.py:91 and :193 (--out), load_tools/load_driver.py
  (--log, --facts, each `.partN` file: opened at :271, written :374 and :385), load_tools/check_invariants.py:741 (--json).
SWITCHED by the book check: db.py:95 / desk.py (lead book; sqlite on a pipe = "disk I/O error" traceback before).
NOT switched, with reason: scripts/run_real_check.py:209,210,1016,1290 (names the script makes itself inside its own new run folder);
  :883 write_result (an existing non-regular --out is already refused by its own check at ~875); scripts/http_guard.py, hubspot_probe.py, n8n_api.py:96
  (network or read only; reads belong to F3); demo_only/portal_demo.py:311 (read) and :435 (mkstemp makes a NEW unique name, then os.replace swaps the name: cannot wait);
  src/lead_desk/portal_api.py:100 and db.py:122 (read-only / packaged file); regfile.py itself (the helper).
Known race, unchanged and stated in tools/pathconfine.py: confine checks the name, then the tool opens it (two steps); the library sites use the handle check and have no such gap.

## Tests (all in child processes with a 5 s limit, no network, made-up data; fake secret built from parts)
tests/test_special_output_files.py: 6 library sites x (pipe, link to pipe, folder); open_output unit cases (create, append, "a+b", "w", link to a regular file,
every kind x every mode, NUL, bad mode, missing folder stays an ordinary OSError); `confine` (pipe, link to pipe refused; new name, regular file, link kept);
scrub, catcher, load_driver (--log and a pipe under a `.part0` name), check_invariants --json, fake_model_server (--call-log, --key-file); desk main with a pipe/link/folder
as the lead book (exit 4, one line, no `.lock`); book_problem unit.
tests/test_wrapper_setting_refusals.py: reset.sh and start_all.sh (ps1 on Windows) with DESK_BIND="a b", DESK_PORT=<fake secret>, and both: exit 4, first line
`the desk refuses a setting:`, one line, no Traceback, no typed value, nothing deleted or created; text pin for all four wrappers; helper values, refusal, usage.

FAILS BEFORE (failing-before.log, old src/tools/load_tools/demo_only/scripts at e23a1cb + the new test files): `54 failed, 8 passed in 56.97s`.
  The 8 passes are pins that already held: ledger-lock x3, ledger-append x3 (item 4 above), stats-folder, trace-folder (a folder gave an OSError before too).
  Raw wrapper failure: `Traceback ... lead_desk.envnum.SettingRefused: DESK_BIND and DESK_FAKES_HOST must be plain ASCII text ...` with exit 1.
  Raw lead-book failure before: `sqlite3.OperationalError: disk I/O error` (my manual probe through server.main on loopback), also failing-before-book.log (4 failed).
  Other logs: failing-before-classA.log, failing-before-classB.log (earlier partial runs).
PASSES AFTER (passing-after.log): `1838 passed, 13 skipped, 1 failed in 650.43s`; failure = test_hygiene_scan_public, same as baseline (item 2).
  The 13 skips are environment (no playwright, no gitleaks, Python 3.12, a load-measurement switch). passing-after-readme.log: `147 passed, 27 skipped` after the README edit.
Note: test_hygiene's DPLD_REQUIRE_SCAN skips are gitleaks only.

## Lint and types
ruff.log: `All checks passed!` and `13 files already formatted` (pyproject line length 120). mypy --platform linux and --platform win32: `Success: no issues found in 31 source files`.
bandit -ll -r src tools scripts: no medium or high severity issues (run before the book_problem edit; desk.py adds only os.stat).
No noqa, no ignore added. (Existing noqa lines I removed: 2 in lockfile.py/live_claude.py `SIM115`, because the helper call is not an `open()`.)

## Product notes for the lead
- Behaviour change: fake_model_server with a missing `--key-file` now prints one refusal line and exits 2 (was a traceback).
- Decision for the lead: scripts/desk_setting.py prints its refusal on STANDARD OUTPUT (like the desk), and the wrappers forward it; the wrappers print it on standard error in bash.
- Multi-thread DeprecationWarning from fork() in the new tests (same as F3's test file, which also forks).

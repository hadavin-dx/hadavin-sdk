# V6 evidence for F6 (raw output only; no judging). Trees: tree-V6 (F6 copy), tree-V6old (baseline e23a1cb + the 2 new test files), tree-V6mut (F6 copy for mutations/hostile). tree-F6 untouched (fix.patch md5 b498dd28... = diff of tree-F6).
Run recipe: out/V6/run.sh (TMPDIR outside tree, PYTHONPATH=<tree>/src, venv-br python, inside `unshare -n` + lo_up). lead_desk.__file__ printed as first log line (points into the tree under test).

## FAILURES / SURPRISES FIRST
1. REGRESSION FOUND (not in builder's report): tests/test_lead_step_route.py::test_demo_launchers_name_the_demo_file_and_the_off_switch
   PASSES on baseline (leadstep-baseline.log), FAILS on F6 (leadstep-f6.log, neighbour.log): `ValueError: substring not found` at test line 429
   `assert ps.index("DESK_LEADFLOW_FILE") < ps.index("python -c")` -> start_all.ps1 (and probably .sh line 430) no longer contain "python -c" because F6 replaced it with desk_setting.py.
   Builder's neighbour set missed this file.
2. test_hygiene_scan_public fails on F6 AND on baseline; the 10 printed lines are IDENTICAL (diff of hygiene-baseline.log vs neighbour.log: identical). Lines printed (all in tests/test_special_files_and_plain_text.py):
   156 http://127.0.0.1\n:1 | 168 https://api.example.test | 168 https://api | 174 https://api.example.test | 184 https://api.example.test | 185 https://api.example.test | 191 http://h | 191 http://h:1 | 191 http://h:1 | 194 http://h.example:1
3. Hostile input, same on baseline and F6 (F6 did not fix it): DESK_DB_PATH whose PARENT is a device or does not exist/cannot be made: `/dev/null/x.db` -> raw Python Traceback, exit 1 (FileExistsError at server.py:1140 `config.db_path.parent.mkdir(...)`); `/proc/<name>/book.db` -> Traceback, exit 1 (FileNotFoundError, same line). The typed path appears in the traceback text. Logs: hostile-tb.txt.
4. Neighbour set: the builder's list of 31 files is not in RESULTS.md. I ran my own 39-file superset (every test file that mentions a changed module/script; list in neighbour-files.txt, minus conftest): 2 failed, 2244 passed, 6 skipped, 847 s (neighbour.log). Not the builder's 1838/13/1: different set, so numbers are not comparable. Skips here: gitleaks x3, 1 path-confinement (other users), 1 Python 3.13 only, 1 Windows only.
5. Mutation M8b (only the data-dir desk_setting call removed from start_all.sh) SURVIVED (62 passed): the other two calls still refuse. Removing all three calls (M8c) is killed. Not run: .ps1 files, Windows, macOS, full 4118-test suite, gitleaks.
6. Hostile case 7 (read-only folder) is not valid evidence: running as root, mode bits do not bind (server went on to "cannot reach the demo servers"). Cases 10/11 (unicode, newline in DESK_DB_PATH) are accepted as valid names (desk went on to the demo-server check, exit 1); not refusals. Cases 14 (reset.sh with a FIFO in data/) ran "reset done" (removed the FIFO).

## (1) New tests 3x (new-tests-1..3.log): 62 passed each time (47 + 15 = builder's count), 3.0 s / 3.3 s / 3.9 s, rc=0.
## (2) Fails before (fails-before.log, baseline e23a1cb + new test files): 54 failed, 8 passed in 59 s (builder: 54/8, matches). Many fail only because `open_output` does not exist (ImportError); hangs are caught by the tests' 5 s limit.
First error line of 10 different tests (fails-before-short.log):
- test_a_writer_refuses_a_pipe_...[lock-pipe]: AssertionError: LockUnavailableError|cannot open the lock file: UnsupportedOperation
- test_the_special_file_is_left_as_it_was: Failed: _trace waited for ever (more than 5 s) on a pipe or a folder
- test_open_output_creates_a_missing_file_and_appends_to_it: ImportError: cannot import name 'open_output' from 'lead_desk.regfile'
- test_open_output_refuses_every_special_kind_in_every_mode[a-pipe]: AssertionError ImportError|... == 'NotRegularFile...'
- test_confine_refuses_an_existing_pipe_for_a_written_file...[pipe]: Failed: DID NOT RAISE PathRefused
- test_scrub_catcher_and_burst_driver_refuse_a_pipe_as_their_output[pipe]: Failed: run_scrub_n8n_export waited for ever (more than 5 s)
- the lead-book / wrapper tests, see fails-before-short.log for all 54 lines (each has file:line + error).
The 8 passes = ledger-lock x3, ledger-append x3, stats-folder, trace-folder (as builder said).
## (3) Neighbour: see item 4 above. test_hygiene alone on baseline: 1 failed, 20 passed, 3 skipped (hygiene-baseline.log): same failure as F6.
## (4) ruff check (pyproject line length 120): All checks passed (both ruff 0.17.4 venv and 0.16.9 global); ruff format --check: 173 files already formatted; bandit -ll -r src tools scripts: Medium 0, High 0 (Low 9) rc=0. Logs ruff-*.log, bandit.log.
## (5) Mutations (mutations.txt; each restored and verified with cmp = True; tree-V6mut equals tree-F6 afterwards):
| mutation | new tests result |
| M1 open_output skips kind check | KILLED 4 failed |
| M2 confine accepts a pipe | KILLED 6 failed |
| M3 load_driver .partN not confined | KILLED 1 failed |
| M4 desk_setting echoes typed value | KILLED 7 failed |
| M5 exit code 4 -> 1 (server.py book_problem refusal) | KILLED 3 failed |
| M6 lockfile plain open | KILLED 3 failed |
| M7 trace.py plain open | KILLED 3 failed |
| M8 reset.sh does not call desk_setting | KILLED 3 failed |
| M8b start_all.sh one call (data-dir) removed | SURVIVED 62 passed |
| M8c start_all.sh all three calls removed | KILLED 3 failed |
| M8d reset.sh calls python -c Config.from_env instead | KILLED 4 failed |
## (6) Hostile inputs (hostile.txt, hostile-rerun.txt; timeout 10 s, stdin /dev/null, loopback-only namespace; canary string in values). exit | traceback | hang | typed value echoed
| 1 server DESK_DB_PATH=FIFO | 4 | no | no | no |
| 2 server ... symlink to FIFO | 4 | no | no | no |
| 3 server ... /dev/null | 4 | no | no | no |
| 4 server ... directory | 4 | no | no | no |
| 5 server ... /dev/null/x.db | 1 | YES | no | no (path in traceback is /dev/null) |
| 6 server ... unix socket | 4 | no | no | no |
| 7 server ... read-only folder (root, not valid) | 1 | no | no | no |
| 8 server ... /proc/<canary>/book.db | 1 | YES | no | YES (canary in traceback) |
| 9 server ... 5000-char name | 2 | no | no | no ("cannot take the lock file: LockUnavailableError") |
| 10 server ... unicode name | 1 | no | no | no (went past the book check) |
| 11 server ... newline in name | 1 | no | no | no (went past the book check) |
| 12 desk_setting db-path, newline in DESK_DB_PATH | 0 | no | no | yes (it prints the path: that is its job; output is 2 lines) |
| 13 desk_setting port, DESK_PORT=canary | 4 | no | no | no |
| 14 reset.sh, DESK_DB_PATH=FIFO inside data/ | 0 ("reset done") | no | no | no |
| 15 reset.sh DESK_BIND="a b canary" | 4 | no | no | no |
| 16 start_all.sh DESK_PORT=canary | 4 | no | no | no |
| 17 start_all.sh DESK_FAKES_PORT=canary | 4 | no | no | no |
| 18 fake_model_server --call-log FIFO | 2 | no | no | no |
| 19 fake_model_server --key-file FIFO | 2 | no | no | no |
| 20 catcher --out FIFO (LEAD_DESK_PATH_ROOTS set; first run without it was refused for "outside folders", not for the kind) | 2 | no | no | no |
| 21 load_driver --log symlink to FIFO | 2 | no | no | no |
| 22 scrub_n8n_export dst FIFO | 2 | no | no | no |
| 23 scrub_n8n_export dst socket | 2 | no | no | no |
| 24 catcher --out /dev/null/x | 2 ("outside the allowed folders", even with the root set) | no | no | no |
Hangs: none (no exit 124/137). 
## (7) Builder vs measured: 54 failed/8 passed before = measured 54/8. 47 + 15 new tests = measured 47 + 15 (62). Builder's 1838/13/1 neighbour: NOT reproduced (different, larger set: 2244 passed/6 skipped/2 failed); the builder's 1 failure (hygiene) is reproduced identically, the 2nd failure (item 1) is new.
## Cleanup: no process of mine running (checked pgrep). Copies left on disk: tree-V6, tree-V6old, tree-V6mut, tmp-V6.

# Hang hunt (agent C, both halves): evidence only, no judgement

Studio files with backslash paths are not in this checkout (said as asked). Product test only. Copy of main 61ded9e at /home/user/work/hang, venv /home/user/work/hangvenv (pytest 9.2.0, still worked; not rebuilt).

## Failures and gaps first
- No hang, no test failure, no faulthandler stack dump in any run (faulthandler_timeout=120; no "Timeout (" dump in any log).
- GAP 1: the hog window of (d2) was only 20 s (10:24:47Z to 10:25:07Z, 15:54:47 to 15:55:07 IST) because the 5 runs took 3 to 4 s each, so it did not overlap agent D's suite for long. The test is fast; the 5 runs finished well inside the 12-minute limit.
- GAP 2 (tool problem, not a test failure): the first full run (c, `-v`, plain) ended with EXIT_CODE=0 after 1121 s but its log file stops at test 204 (5 percent, test_crm_hubspot.py::test_429_uses_the_backoff_without_retry_after_and_gives_up_busy) while the run kept going (basetemp dirs grew to about 3300 afterwards). Output to the file was lost after the first 22 KB: so no summary line in that log; counts there are 204 PASSED only. This matches the earlier "stops at about 71 percent, no summary" symptom: a missing log tail does not mean a crash. Cause of the lost output not found (not investigated further).
- To get real counts I ran the full suite a second time (c2) with `python -u`, PYTHONUNBUFFERED=1 and --junitxml. That log is complete. Strictly this is two full runs, not one.
- Skips (198): 6 need playwright (not installed), 3 need gitleaks (not on PATH), 1 Windows-only, 1 needs LEAD_DESK_LOAD_N, 1 root can read no-permission file; the rest not itemised here (see log, `grep ^SKIPPED`).

## Table
| task | run | duration | result | note |
|---|---|---|---|---|
| a | 1 | 3 s | PASS (exit 0) | |
| a | 2 | 2 s | PASS (exit 0) | |
| a | 3 | 3 s | PASS (exit 0) | |
| a | 4 | 2 s | PASS (exit 0) | |
| a | 5 | 3 s | PASS (exit 0) | |
| a | 6 | 2 s | PASS (exit 0) | |
| a | 7 | 4 s | PASS (exit 0) | |
| a | 8 | 2 s | PASS (exit 0) | |
| a | 9 | 2 s | PASS (exit 0) | |
| a | 10 | 2 s | PASS (exit 0) | |
| b | 1 | 11 s | PASS (exit 0) | |
| b | 2 | 11 s | PASS (exit 0) | |
| b | 3 | 11 s | PASS (exit 0) | |
| b | 4 | 11 s | PASS (exit 0) | |
| b | 5 | 10 s | PASS (exit 0) | |
| d1 | 1 | 4 s | PASS (exit 0) | |
| d1 | 2 | 4 s | PASS (exit 0) | |
| d1 | 3 | 3 s | PASS (exit 0) | |
| d1 | 4 | 2 s | PASS (exit 0) | |
| d1 | 5 | 4 s | PASS (exit 0) | |
| d2 | 1 | 4 s | PASS (exit 0) | nice 10 + 3 hogs |
| d2 | 2 | 4 s | PASS (exit 0) | nice 10 + 3 hogs |
| d2 | 3 | 3 s | PASS (exit 0) | nice 10 + 3 hogs |
| d2 | 4 | 4 s | PASS (exit 0) | nice 10 + 3 hogs |
| d2 | 5 | 3 s | PASS (exit 0) | nice 10 + 3 hogs |
| c | 1 | 1121 s | exit 0, log cut at test 204 | hang-c-full.log, no summary (see gap 2) |
| c2 | 1 | 1067 s (0:17:46) | PASS: 3407 passed, 198 skipped, 0 failed, 0 errors, exit 0 | hang-c2-full.log, hang-c2-junit.xml; collected 3605 |

Tasks a, b, d1 rows are copied from raw/hang-summary.txt. a = test alone x10, b = its file x5, d1 = one core x5.

## Commands
- Helper (a, b, d1): /home/user/work/hang-run.sh task n prefix target...  which runs
  `TMPDIR=<private>/tmp <prefix> timeout 660 hangvenv/bin/python -m pytest -q -rs -o faulthandler_timeout=120 -p no:cacheprovider --basetemp=<private>/tmp/bt <target>` in /home/user/work/hang.
- d2 (script /home/user/work/d2.sh): 3 x `timeout 600 sh -c 'while :; do :; done'` (PIDs 349 350 351, killed by PID at the end, none left), then 5 serial runs of the same pytest flags as above under `nice -n 10 timeout 660`, target `tests/test_load_tools.py::test_burst_run_logs_every_request`. Logs raw/hang-d2-run1..5.log (each "1 passed in about 2.2 s").
- c: `TMPDIR=/home/user/work/hangtmp/c/tmp timeout 2400 python -m pytest -v -rs -o faulthandler_timeout=120 -p no:cacheprovider --basetemp=/home/user/work/hangtmp/c/tmp/bt` then `EXIT_CODE=$? WALL_SECONDS=...` appended. Log raw/hang-c-full.log.
- c2: same plus `python -u`, PYTHONUNBUFFERED=1, `--junitxml=raw/hang-c2-junit.xml`. Log raw/hang-c2-full.log. Summary line: `3407 passed, 198 skipped in 1066.37s (0:17:46)`, then `EXIT_CODE=0 WALL_SECONDS=1067`.

## Machine facts
4 cores, 16 GB RAM (about 14.7 GB free at start), Linux 6.18, Python 3.12, pytest 9.2.0. Other pytest runs by other agents (agent D in /home/user/work/final, others) were running at the same time during c and c2, so wall times include that load. The full-suite slowest stretch was tests that start real local servers (about 40 tests per 2 minutes at the slowest).

## Stack dumps
None. During c a gdb attach (read only, detached at once) showed the main thread in time.sleep inside a test and new server threads appearing; no python stack was available (no py-spy, gdb py-bt missing). That was a normal progressing test, not a hang.

## Cleanup
Hogs killed by PID (none left); no pytest or helper of mine running at the end. Time marks in raw/progress-C.txt.

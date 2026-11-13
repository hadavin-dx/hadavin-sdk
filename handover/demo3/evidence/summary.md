# NUMBERS (valid rows first; updated 10:46Z / 16:16 IST). head | passed | failed | skipped | wall time | hang yes/no

| head | passed | failed | skipped | wall time | hang | note |
|---|---|---|---|---|---|---|
| PR #14 d5b4451 (STALE head, replaced by edadd00), run 1, -v, basetemp inside TMPDIR | at least 3426 (counted from the recovered log up to 97 percent; the last ~3 percent of its output was lost when the process ended before my last copy) | 0 FAILED lines in the recovered part | 197 in the recovered part | 1127 s | no | **exit code 0** (EXIT_CODE line survived): pytest itself reports no failure. No summary line saved. Run 2 NOT run (order 5). |
| main 61ded9e, -v, basetemp inside TMPDIR (agent C2, hang hunt full run) | running: 3226 passed, 0 FAILED, 183 skipped at 10:44Z | | | | | recovered log, not finished |
| PR #14 edadd00 (current head), 1 run, -v | agent E running (started 10:42Z) | | | | | table row filled when E ends |

The four older rows below (A runs, `-q`, basetemp outside TMPDIR) are INVALID as pass/fail evidence: see evidence/failures.md.

# Summary of numbers (evidence runner lane; raw facts, no verdict)

IMPORTANT: none of the four runs below printed a pytest summary line. pytest ended at 71-72 percent of the tests with exit code 1 and no "N passed" line (the container also restarted at about 10:20Z, which stopped agents A and C; the logs of these four runs were already complete before that, each ends with its EXIT_CODE line). The counts below are counted from the progress marks in the raw log (`.` passed, `F` failed, `s` skipped, `E` error) up to the point where pytest ended, NOT from a pytest summary. The tests after the stop point did not run. Failing test names are not in these logs (run with -q, no -rf); runs of D and C2 use -v to name them.

| head | run | passed (dots) | failed (F) | skipped (s) | error (E) | stopped at | exit code | wall time | hang yes/no |
|---|---|---|---|---|---|---|---|---|---|
| main 61ded9e | 1 | 2412 | 56 | 182 | 0 | 71% | 1 | 1110 s | no (no test over 10 min seen) |
| main 61ded9e | 2 | 2412 | 56 | 182 | 0 | 71% | 1 | 1125 s | no |
| PR #12 8d65577 | 1 | 2489 | 57 | 182 | 0 | 72% | 1 | 1172 s | no |
| PR #12 8d65577 | 2 | 2488 | 57 | 188 | 2 | 72% | 1 | 1126 s | no |

Python 3.12.3 (/usr/bin/python3.12), 4 cores, hash-locked install of requirements-dev.txt, no Playwright (browser tests skip), main and PR copies ran at the same time (2 heavy runs).
Not known yet: why pytest ends at 71-72 percent (agent A started a `-v` diagnostic run on main at 10:15:52Z; it was stopped by the container restart at about 21 percent, log raw/suite-main-diag-v.log). C2's full run (hang-c-full.log, -v) and D's runs on d5b4451 (suite-final-run1/2.log, -v) will name the last test.
Open rows: PR #14 (d5b4451) numbers come from agent D (evidence/suite-pr14.md).

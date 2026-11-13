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

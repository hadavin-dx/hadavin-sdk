# CURRENT HEAD c14a514: path tests only (agent G), last full suite: 6b1fe49 (below)

| head | scope | passed | failed | skipped | errors | wall time | note |
|---|---|---|---|---|---|---|---|
| **c14a514** (current) | tests/test_path_confinement.py alone | **378** | **0** | **1** (isreserved needs Python 3.13; machine has 3.12.3) | 0 | 67.56 s | exit 0; the delta's only test file; no full suite on this head (order 7) |
| 6b1fe49 | same file, side by side | 378 | 0 | 1 | 0 | 36.69 s | exit 0; the wall time difference is not investigated (machine load not measured) |

# NUMBERS (valid rows first; updated 10:46Z / 16:16 IST). head | passed | failed | skipped | wall time | hang yes/no

| head | passed | failed | skipped | wall time | hang | note |
|---|---|---|---|---|---|---|
| PR #14 d5b4451 (STALE head), run 1, -v, basetemp inside TMPDIR | at least 3426 (counted from the recovered log up to 97 percent; the last ~3 percent of its output was lost when the process ended before my last copy) | 0 FAILED lines in the recovered part | 197 in the recovered part | 1127 s | no | **exit code 0** (EXIT_CODE line survived): pytest itself reports no failure. No summary line saved. Run 2 NOT run (order 5). |
| main 61ded9e, full suite -v -u with junitxml, basetemp inside TMPDIR (agent C2, run c2) | 3407 | 0 | 198 | 1067 s | no | **exit 0, 3605 tests collected (3407+198=3605)**; complete summary from junit. Skips mostly: Playwright missing (6), no gitleaks (3), Windows-only or root-only tests. Run c1 (same head, -v) also exit 0 in 1121 s but its log was cut by my git slip |
| main 61ded9e, -v, basetemp inside TMPDIR (agent C2, hang hunt full run 1) | at least 3328 (recovered log up to 97 percent; last ~3 percent lost) | 0 FAILED lines | 197 | about 1130 s (10:25:50Z to 10:44:53Z) | no | **exit code 0**; no summary line saved. C2 started a second full run with `-u` and junitxml at 10:44:53Z (ends about 11:04Z) to get a complete summary |
| **PR #14 6b1fe49**, 1 run, -v, basetemp inside TMPDIR (agent F) | **3683** | **0** | **200** (166 Playwright, 30 gitleaks, 4 other) | **1155 s (19:15)** | no | 0 errors, **exit 0**, counts from pytest's summary line; 2 more passing tests than edadd00; one run (no flake data) |
| **PR #14 edadd00** (older head), 1 run, -v, basetemp inside TMPDIR | **3681** | **0** | **200** | **1215 s (20:15)** | no | 0 errors, **exit 0**, all counts from pytest's own summary line; run once only (no flake data); skips: Playwright missing, no gitleaks, Windows-only, root-user and env-gated tests (reasons in the log with -rs) |

**INVALID rows (agent A, `-q -rs`, basetemp OUTSIDE TMPDIR, logs cut by my git operations):** main 61ded9e run1 and run2 (56 F each), PR #12 8d65577 run1 and run2 (57 F each). Reason: path confinement refused the test folders (56 tests fail with "path is outside the allowed folders" when `--basetemp` is outside `TMPDIR`, pass when inside) and the logs lost their tails; see evidence/failures.md. Do not use these four rows as pass/fail evidence.

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

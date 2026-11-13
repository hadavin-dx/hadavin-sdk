# Suite on PR #14, head d5b44512e841cb389886ade81636651425102f6e (STALE: PR head is now edadd00, per lead order 5)

Failures and gaps first
- The log is TRUNCATED and has NO pytest summary line. pytest exited with exit code 0 (not 1) after the test `tests/test_desk_edge_cases.py::test_burst_distinct_emails` had started; the log stops at 7 percent, 290 PASSED lines, 0 FAILED/SKIPPED/ERROR lines. 0 does not mean the full suite passed. Same symptom agent C saw ("exit 0, log truncated"). Cause not investigated (I do not judge). Note: I ran without `-u` as the brief's exact command said, so lost buffered output is one possibility; not tested.
- Run 2 was NOT run (lead order 5; the head is stale). So no second serial run exists.
- Run 1 overlapped agent C's CPU-hog window (C: START d2 hog window 10:24:47Z; run 1 started about 10:26Z, wall 1127 s, ended about 10:45Z; C logged END c at 10:44:53Z).

| head | run | passed | failed | skipped | wall time | hang yes/no | overlapped C hog window yes/no |
|---|---|---|---|---|---|---|---|
| d5b4451 | 1 | 290 (counted from -v lines; no summary) | 0 | 0 (-rs section absent because no summary) | 1127 s | no hang killed by me; but the run ended early with exit 0 | yes |

Last 5 lines of log (raw/suite-final-run1.log): ends `tests/test_desk_edge_cases.py::test_burst_distinct_emails EXIT_CODE=0 WALL_SECONDS=1127` (the marker joined the unfinished test line, no newline was written by pytest).

Exact command (TMPDIR=/home/user/work/final-tmp1, script /home/user/work/final-run.sh):
`timeout 2400 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt > raw/suite-final-run1.log 2>&1`
Facts: Linux 6.18.44, 4 cores, /usr/bin/python3.12 venv at /home/user/work/final-venv, deps from requirements-dev.txt with --require-hashes (rc 0, pytest 9.2.0), no browser lock (browser tests would skip). Worktree /home/user/work/final at d5b4451 (git rev-parse confirmed).

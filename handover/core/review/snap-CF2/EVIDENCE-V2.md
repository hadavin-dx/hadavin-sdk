# V2 evidence (runner, no judgement)
Patch sha256 a5cece28...; tree-V2 == tree-V2old + fix.patch (diff -rq clean before runs; afterwards only a new untracked folder tree-V2/data created by the full suite).
FULL SUITE tree-V2 (AF env): 1 failed, 4103 passed, 4 skipped in 1657.86s, rc=1 (full.log). Baseline AF: 3978 passed, 0 failed, 4 skipped (+125 passed, +1 failed).
FAILED tests/test_clock_steps.py::test_wall_clock_is_only_used_for_calendar_stamps: scripts/run_live_check.py:192 `datetime.now(UTC)` line has no "# wall-clock:" marker (line added by the patch).
Fails-before (stub LIVE_EFFORTS + SECRET_FILE_MAX_BYTES appended to old constants.py, then restored): 106 failed, 20 passed. No stub: ImportError cannot import name LIVE_EFFORTS (before-nostub.log).
Passes-after x3: 126 passed each (after-1..3.log). Builder claimed 109 failed/32 passed (141): differs from 106/20 (126).
Ruff check: All checks passed (21 files). Format: 21 files already formatted. Added lines over 100 cols: 93 (44 in test_cli_refusals.py); repo line length 120.
Mutation 8/8 killed (mutation.log). Hostile: 25 cases, 0 key echo, 0 Traceback, 0 prompt (hostile.log).

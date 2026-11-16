# PR 71 fix 2 independent evidence (EVIDENCE RUNNER: records only, no judgement)
Time (UTC): 2026-11-12 ~20:50 to 21:40. Raw logs are in this folder.

## FAILED / NOT RUN (first)
- gitleaks: NOT RUN at either head. The tool is not installed. I downloaded a release binary, but the permission system refused to let me run it; I deleted it and did not work around the refusal. Exit code: none. Next step: install gitleaks and run `gitleaks git --log-opts="origin/main..HEAD"`.
- Full pytest at 9d1e135f, first run: 1 failed, 10734 passed, 1 skipped, 28 deselected (rc nonzero, 257.69 s). Failing test: tests/demo_askdata/test_validate_harm.py::...[dblink-connect]. Cause: my own Postgres server listened on port 55437 with a private socket folder, and the test's dblink_connect('dbname=postgres') uses the server's default socket path (/var/run/postgresql), which does not exist. Environment problem of my setup, not a code fault.
- Re-run of that file after restarting my Postgres with PGHOST=127.0.0.1 PGPORT=55437 in the server's environment: 253 passed (5b-rerun-validate-harm.log). This is a file-level re-run only; I did NOT repeat the whole suite. The full run at 9d1e135f therefore stays "1 failed" on record.
- Not run: Vault tests; Python 3.12 (only 3.13 venv present); fail-before for the new guard (see item 3).
- Full pytest was NOT run at 04cfa501 (delta run only, as instructed).

## Head 9d1e135fe42900edd54f170381a9368c0c769467 (clean detached worktree, status clean)
1. tests/test_no_pglast_in_runtime.py: 108 passed, rc 0 (1-pglast-new.log)
2. ruff check src tests demos tools: All checks passed, rc 0. ruff format --check: 321 files already formatted, rc 0. bandit -ll -r src tools demos: rc 0 (only a nosec warning at src/hadavin_sdk/tools.py:389). tools/scan_repo.py: rc 0, no output (2-*.log)
3. Old file (from 8b982dd3) run in the same tree: 62 passed, rc 0 (3-pglast-old.log). New file has 108 tests, old 62. Strictly, "new tests fail on old guard" is not testable since the guard lives in the test file; I did not make that claim.
4. Full pytest -m "not live and not perf" via heavy.sh, own Postgres 16 (-E UTF8 --locale=C.UTF-8, port 55437, started as the postgres OS user): 1 failed, 10734 passed, 1 skipped, 28 deselected (5-full-pytest.log); failure explained above.

## Head 04cfa501b02e8021e9ef88f94ad0fdc03a8f7936 (second clean detached worktree, status clean)
- git diff --stat 9d1e135f 04cfa501: only tests/test_no_pglast_in_runtime.py, 42 insertions, 16 deletions (6-diffstat.log)
- tests/test_no_pglast_in_runtime.py: 117 passed, rc 0 (7-delta-pglast.log)
- ruff check: pass rc 0; ruff format --check: 321 files already formatted rc 0; bandit -ll: rc 0; scan_repo: rc 0 (7-delta-*.log)
- gitleaks: not run (above).

## Cleanup
Postgres stopped and data folder removed; both worktrees removed. Nothing committed to any branch. The heavy.sh queue wait was about 35 minutes (other jobs held the 3 slots and a higher priority waiter), so the 60-minute box was exceeded slightly.

## Lead addendum (not the runner)
- gitleaks: runner could not run it; the lead ran `gitleaks git --log-opts origin/main..04cfa501` rc=0 and `gitleaks dir` on the raw evidence rc=0.
- Full pytest ran at 9d1e135f only (1 failed: runner Postgres socket setup, the file passed after the fix, 253 passed); the delta 9d1e135f..04cfa501 changes only tests/test_no_pglast_in_runtime.py (117 passed). No full pytest at 04cfa501.
- No "new tests fail on old code" claim: the guard test file replaced the old one (old file 62 passed).

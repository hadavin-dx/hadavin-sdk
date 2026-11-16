# Evidence for core/P6a head d392200 (EVIDENCE RUNNER: recorded only, no judgement)
Head checked: `git rev-parse HEAD` in the detached worktree = d3922003925722275704b84f580152d35dd90c9c (first line of each log). Base for fail-before = 0dabf1fa7a2ed58e14b8bca13be1141ac59f9c71.
Cloud env vars (AWS_, ANTHROPIC_, AZURE_, GOOGLE_, GCP_, VAULT_, OPENAI_, GEMINI_, CLOUDSDK_) unset in every command. HADAVIN_TEST_VAULT_ADDR not set (Vault tests skip or are not exercised; CI sets one). Postgres 16 own throwaway cluster, 127.0.0.1:5432, trust, UTF8, socket dir /var/run/postgresql, stopped at the end. HADAVIN_REQUIRE_PINNED_UNIDATA=1 on 3.13 only (as CI).

| # | Command | Python | Result | Exit | Log |
|---|---|---|---|---|---|
| 1a | ruff check src tests demos tools | 3.13 | All checks passed | 0 | 01a-ruff-check.log |
| 1b | ruff format --check src tests demos tools | 3.13 | 319 files already formatted | 0 | 01b-ruff-format.log |
| 1c | bandit -q -r src demos tools -ll (scan-group venv, as CI) | 3.13 | no issues printed (only nosec warnings) | 0 | 01c-bandit.log (attempt 1 failed: bandit not in test venv, exit 127: 01c-bandit-attempt1-notinstalled.log) |
| 1d | python tools/scan_repo.py | 3.13 | no output | 0 | 01d-scan-repo.log |
| 2 | pytest -m "not live and not perf", run as 10 file batches (14 files each, 10516 tests collected = same as one full run) | 3.13 | batch00 509 passed 1 skipped; 01 551; 02 845; 03 4107; 04 2450; 05 650; 06 393; 07 407; 08 555; 09 48 (all passed) | all 0 | 02-full-py3.13-batchNN.log |
| 2 | same | 3.12 | batch00 509 passed 1 skipped; 01 551; 02 845; 03 4107; 04 2450; 05 650; 06 393; 07 407; 08 555; 09 48 (all passed) | all 0 | 02-full-py3.12-batchNN.log |
| 3 | pytest -m perf (alone) | 3.13 | 28 passed, 10516 deselected | 0 | 03-perf-py3.13.log |
| 4 | tests/test_client_profile.py + tests/test_strict_flags.py | 3.13 | 118 passed | 0 | 04a-profile-strict-py3.13.log |
| 4 | same | 3.12 | 118 passed | 0 | 04b-profile-strict-py3.12.log |
| 5 | python tools/p6a1_mutants.py | 3.13 | TOTAL mutants 63, planted 63, KILLED 63 (named 63), SURVIVED 0, other problems 0 (108 s); final git status '' (worktree clean) | 0 | 05-p6a1-mutants-py3.13.log (first run exited 0 but its log has only the baseline line, no mutant lines: aborted-full-runs/05-first-run-output-missing.log, cause not found; second run, alone, complete) |
| 6 | python tests/stage_mutants.py | 3.13 | 37 of 37 good; problems: [] | 0 | 06-stage-mutants.log |
| 7 | fail-before at base 0dabf1f, two test files copied in (they do not exist at base) | 3.13 | test_client_profile: 48 FAILED, 21 PASSED; test_strict_flags: 49 FAILED, 0 PASSED. Per-test rows: 07-failbefore-ROWS.txt | 1,1 | 07-failbefore-*.log |

## Things that went wrong during the run (all kept in aborted-full-runs/)
1. Single un-batched full runs (3.13 and 3.12, several attempts) ended with no pytest summary and a shell exit code of 1 (once 0) in the middle of the run, at different tests each time (e.g. test_validate_harm, test_k5_fixes6, test_executor, test_cuj). Cause NOT found. The same files pass when run alone. I therefore ran the full suite as 10 file batches; batches 3.12 b00, 3.12 b02 and 3.13 b02 also ended early or failed on first attempt and passed on re-run (first attempts in aborted-full-runs/first-attempt-batches/). One of those (3.13 b02) failed because the test dblink-connect used the default socket /var/run/postgresql, which my first cluster did not use; fixed by putting the cluster's socket there. Two of the early deaths happened while two suites shared one cluster.
2. First cluster was created as SQL_ASCII (container locale C): 100+ database test failures ("bytes found", SQLSTATE 25006). Logs kept in aborted-full-runs/sql-ascii-cluster/. Cluster recreated as UTF8; all results in the table above are from the UTF8 cluster. Items 4 and 6 ran before that change (they do not use the database; items 3 and 5 were re-run after).
3. Not run: Vault-backed tests (no HADAVIN_TEST_VAULT_ADDR, no Vault server); live tests; a single un-batched full run to completion on either Python (never completed; see 1).
4. Concurrent load: other agents' pytest runs were on the same machine throughout.

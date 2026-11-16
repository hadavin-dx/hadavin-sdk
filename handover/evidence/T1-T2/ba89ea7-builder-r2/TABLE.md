# Evidence, head 98a3ed95bca4acac88d77b29d4f26846f7f9ce9b (builder r2). Raw logs are in this folder.
Cleared before every run: CI, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL, GH_TOKEN, GITHUB_TOKEN, HADAVIN_TEST_PG_DSN (set again only for the DSN runs). Postgres 16, 127.0.0.1:56300.
WARNING: logs written through heavy.sh (names without "direct-") were cut short in places (cause not found); the "direct-*" logs and the *-final logs of the contract runs are the complete ones.
| Run | Result |
|---|---|
| ruff check / ruff format --check / bandit -ll / scan_repo | exit 0 each (lint-*.log, bandit.log, scan-repo.log) |
| meter_mutants.py (memory) | 18 of 18 good (mutants-memory-all.log) |
| postgres_mutants.py with DSN | 12 of 12 killed as described, exit 0 (mutants-postgres-direct.log) |
| postgres_mutants.py without DSN | exit 2 (mutants-postgres-no-dsn-final.log) |
| contract + harness files twice on one DSN | 187 passed, 187 passed (contract-twice-run1/2-final.log) |
| same, random order seed 1 and 2 (3.13) | 187 passed each |
| contract files without DSN, 3.12 | 97 passed, 92 skipped |
| contract files with CI=true, no DSN | FAILS (11 errors, exit 1) as intended (contract-ci-env-nodsn-final.log) |
| full suite 3.12 with DSN | 10586 passed, 1 skipped (direct-full-py312-dsn.log) |
| full suite 3.12 without DSN | 10041 passed, 546 skipped, exit 0 (full-py312-nodsn.log) |
| full suite 3.13 with DSN | 1 failed, 10585 passed (direct-full-py313-dsn.log) |
| full suite 3.13 without DSN | 1 failed, 10040 passed, 546 skipped (direct-full-py313-nodsn.log) |
The one 3.13 failure is tests/test_mutation_runner.py::test_the_runner_wires_pinned_so_another_failing_test_is_other_test. File and tools/ are untouched by this branch; the same test fails 2 of 3 runs on the base ba89ea7 (flaky, not from this work). Rerun logs: rerun-mutation-runner-py313.log.
Fail-before: failbefore-ci-guard.log, harness-mutant.log, seed-check.log, mut-*.log.
## New test -> mutant that kills it
recorded in ledger L4; both budgets L9; year in month key S7, S8, P9; past date P10; tiny scale P11; two charges add up S1, S6, P1, P2, P7, P8; 23:30 UTC L6; daily read for today L7; reads change nothing L5; cost not W L10; agent filter S3, S5, P5, P6; stub control harness-mutant.log; CI guard failbefore-ci-guard.log.

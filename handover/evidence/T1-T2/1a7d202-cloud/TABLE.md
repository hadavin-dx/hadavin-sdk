# Evidence table, head 1a7d2029013deff2054c4c18f73663f21aaa7c3c (branch core/T1-T2-tests)
EVIDENCE RUNNER: runs and records only. Each log starts with `HEAD=` (printed by run.sh) and says what was unset
(AWS_ ANTHROPIC_ AZURE_ GOOGLE_ GCP_ VAULT_ OPENAI_ GEMINI_ CLOUDSDK_ CI GH_TOKEN GITHUB_TOKEN and HADAVIN_TEST_PG_DSN, then the DSN set where given).
Postgres 16, UTF8 (initdb -E UTF8 --locale=C.UTF-8), trust, 127.0.0.1:5432, socket dir /var/run/postgresql, own cluster, stopped at the end.
Heavy jobs went through /home/user/build/heavy.sh (detached, nohup).

| # | command | python | DSN | counts | exit | log |
|---|---|---|---|---|---|---|
| 1 | ruff check src tests demos tools | 3.13 | - | All checks passed | 0 | 1-lint.log |
| 1 | ruff format --check src tests demos tools | 3.13 | - | 325 files already formatted | 0 | 1-lint.log |
| 1 | python tools/scan_repo.py | 3.13 | - | no output | 0 | 1-lint.log |
| 1 | bandit -q -r src demos tools -ll (needs `--group scan`; first attempt without it: exit 2, tool missing, recorded in 1-lint.log) | 3.13 | - | no issues printed | 0 | 1b-bandit.log |
| 2 | pytest -m "not live and not perf" full | 3.12 | yes | 10601 passed, 1 skipped, 28 deselected, 322 s | 0 | 2-full-py312-dsn.log |
| 2 | same | 3.13 | yes | 10601 passed, 1 skipped, 28 deselected, 299 s | 0 | 2-full-py313-dsn.log |
| 2 | same | 3.12 | no | 10050 passed, 552 skipped, 28 deselected, 273 s | 0 | 2-full-py312-nodsn.log |
| 2 | FIRST runs, cluster on port 55433 (superseded, kept) 3.12 and 3.13 | both | yes | 1 failed, 10600 passed, 1 skipped each | 1 | 2-full-py3*-dsn.first-run-*.log |
| 2b | dblink rerun of the failing file on port 55433, PGHOST/PGPORT set (still failed) | 3.12 | yes | 1 failed, 270 passed | 1 | 2b-dblink-rerun-port55433-still-fails.log |
| 3 | python tests/meter_mutants.py (memory, all) | 3.13 | - | 22 of 22 good, problems [] | 0 | 3-mutants.log |
| 3 | python tests/postgres_mutants.py | 3.13 | yes | 13 of 13 killed as described | 0 | 3-mutants.log |
| 3 | python tests/postgres_mutants.py without DSN (expected 2) | 3.13 | no | refused | 2 | 3-mutants.log |
| 3 | git status after each mutant run | | | 0 changed lines both times | | 3-mutants.log |
| 4 | CI=true, no DSN: tests/test_pg_dsn_guard.py tests/contracts | 3.13 | no | 289 passed, 1 skipped, 126 errors (all 126 carry "HADAVIN_TEST_PG_DSN not set"; 0 other) | 1 (by design) | 4-ci-guard.log |
| 4 | CI=true with DSN, same files | 3.13 | yes | 415 passed, 1 skipped | 0 | 4-ci-guard.log |
| 5 | flaky test x10 on head (clean worktree) | 3.12 | no | 10 pass, 0 fail | 10x0 | 5-flaky-head-py312.log |
| 5 | flaky test x10 on origin/main 2a8c2aa (clean worktree) | 3.12 | no | 10 pass, 0 fail | 10x0 | 5-flaky-main-py312.log |
| 6 | fail-before: origin/main 2a8c2aa + head's new tests copied, 4 test files | 3.12 | yes | 204 passed, 0 failed | 0 | 6-failbefore-dsn.log |
| 6 | same without DSN | 3.12 | no | 106 passed, 98 skipped | 0 | 6-failbefore-nodsn.log |

## Notes (facts, no verdicts)
- The first full DSN runs had 1 failure, tests/demo_askdata/test_validate_harm.py [dblink-connect]: the database server's own dblink connects to the default socket /var/run/postgresql port 5432, and my first cluster was on port 55433 with socket /tmp. After restarting my cluster on 5432 with that socket dir, the same file passes (253 passed) and both full runs pass. The first logs are kept.
- Flaky runs used python 3.12 only (not 3.13). The flaky "exit=1" at the end of each flaky log is the shell loop's last `[ ] &&` test, not a pytest result; every run line shows exit=0.
- Fail-before: the branch changes ONLY test files versus its merge-base 0dabf1f (no src change), and origin/main (2a8c2aa) has moved on from that base (git diff main..head also shows main-only files). The copied tests all PASS on main (no test fails before), no shim was needed (collection fine, 204 tests). tests/contracts/test_store.py was not copied (branch removed a test there; main's copy kept).
- Not run: python tests/stage_mutants.py, pytest -m perf, py3.13 flaky, py3.13 without DSN, vault tests (VAULT_ unset so they skip; 1 skip in DSN runs is test_llm.py:95 Stubber). HADAVIN_REQUIRE_PINNED_UNIDATA not set.
- Worktrees remain in /home/user/build/EV-A21a-1a7d202 (wt wt312 wt313 wt312nodsn wtmut wtflakyhead wtflakymain wtfb); flaky worktrees hold untracked run*.out files only.
- Scripts used: run.sh lint.sh flaky.sh fb.sh mut.sh guard.sh (copied here).

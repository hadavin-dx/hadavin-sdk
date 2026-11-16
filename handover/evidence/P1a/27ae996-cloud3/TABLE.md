# A8 evidence, PR63 core/P1a head 27ae996 (copy /home/user/build/EV-A8a, .git dropped). Raw logs in this folder. No verdict.
Run 16:34-17:38 UTC (IST +5:30). Shared machine, all 3 heavy slots busy with other agents most of the time.

| Check | Python | Result (from the log) | File |
|---|---|---|---|
| ruff check src tests demos tools | 3.13 | exit=0 | ruff-check.log |
| TID251 step A (no noqa) | 3.13 | exit=0 | tid251-A.log |
| TID251 step B (six fixture forms) | 3.13 | count=6 | tid251-B.log |
| ruff format --check | 3.13 | exit=0, 332 files already formatted | ruff-format.log |
| bandit -q -r src demos tools -ll | 3.13 | exit=0 (one nosec warning line) | bandit.log |
| tools/scan_repo.py (run in WT-A8a, needs .git) | 3.13 | exit=0 | scan_repo.log |
| pytest -m "not live and not perf" | 3.12.3 (unidata 15.0.0) | 2 failed, 11071 passed, 1 skipped, 38 deselected, 9 xfailed in 747s; exit=1 | pytest-py312.log |
| pytest, same | 3.13 | NO RESULT: three runs died or were stopped, see below | pytest-py313-run1/run2/run3-*.log, pytest-py313.log, strace-py313.txt |

## The 2 failures on 3.12 (raw text in pytest-py312.log)
1. tests/test_licences_are_proprietary: `git ls-files` exit 128. Cause is the brief's rule to drop .git from the copy (ENV, not a code result). Not re-run in a git checkout.
2. tests/test_textnorm.py:2964 (test `test_the_deny_check_false_matches_on_the_names_lists_are_exactly_the_listed_pairs`): `assert "" in textnorm.identity_keys("ः") and "" in textnorm.identity_keys("​")` fails; identity_keys("ः") = ('<marker>alg=fold4|ud=15.0.0<marker>ः', '<marker>alg=fold4|ud=15.0.0<marker>'). The test passes no pin env on 3.12 (HADAVIN_REQUIRE_PINNED_UNIDATA not set, as in ci.yml for the 3.12 job). Not checked whether this also fails in the old head or on 3.13.

## 3.13 full pytest: what happened
- run1 (-q): exit=1 at about 11%, no summary, no traceback (pytest-py313-run1-died.log).
- run2 (-v): exit=1 at test_k5_postgres.py::test_a_whole_tooled_run_on_postgres, no summary (that test passes alone, 0.48 s).
- run3 (-v, setsid): exit=1 at tests/demo_askdata/test_allowlist.py ...[D17.gold_sql_alt], no summary.
- run4 (-v, under strace): reached tests/test_k5_tools.py::test_k5_execute_stops_when_the_map_is_gone (79%), shown running for more than 5 minutes at 68% CPU (that test passes alone in 0.35 s); I stopped it at the time box. pytest-py313.log is the partial log. strace-py313.txt holds only the first part (SIGPIPE lines from pid 4881's children; no exit cause found).
- Cause of the silent exit=1 deaths: NOT FOUND. Not verified whether it is a test, the machine, or another agent.

## NOT RUN
- pytest 3.13 full (no complete result), see above.
- pytest -m perf: queued for a heavy slot the whole time, never started.
- tests/stage_mutants.py: same, never started.
- tests/textnorm_mutants.py (138 mutants): same, never started.
- Vault contract tests: no vault server on 127.0.0.1:8200 here, those tests skip (the skip line shows 1 skipped test; the vault tests were not run against a server).
- ci.yml jobs semgrep, zizmor, pip-audit, gitleaks, trivy: not part of this brief, not run.
- Postgres: shared cluster 127.0.0.1:55400, databases a8a_ev and a8a_ev312 (left in place).

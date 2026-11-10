# Evidence P3a-2 head ef2adc75c1a8086c0cd3fd0f389c0676f10d5cdd (EVIDENCE RUNNER: records, does not judge)

Worktree `/home/user/build/EV-P73-ef2adc7/wt`, detached at the head above (`git rev-parse HEAD` printed first in every log).
Note: the local branch `core/P3a-2` in the builder checkout points at 6f2493a; the head ef2adc7 is on `origin/core/P3a-2` and was checked out by sha.
Environment variables removed in every command (by prefix): AWS_ ANTHROPIC_ AZURE_ GOOGLE_ GCP_ VAULT_ OPENAI_ GEMINI_ CLOUDSDK_ (scripts/clean.sh).
Every job ran through /home/user/build/heavy.sh (detached, nohup). Ports are scrubbed to `<port>`.

## Failures and problems first

| # | What | Where | Detail |
|---|---|---|---|
| F1 | One test fails on a throwaway cluster that is not on port 5432 | 02a (3.13) and 02b-rerun1 (3.12) | `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: the traceback says the Postgres SERVER could not connect to its own default socket `/var/run/postgresql/.s.PGSQL.5432` (dblink dials from inside the server). Same test run alone with the cluster restarted with PGHOST/PGPORT in the SERVER environment: 253 passed (02a-single-askdata-dblink-server-env-py313.log). Run alone with the variables only in the client environment: still 1 failed (02a-single-askdata-dblink-test-py313.log). CI's service sits on 5432. |
| F2 | First 3.12 full run ended with no pytest summary | 02b-full-py312-dsn.log | Output stops after test_cuj.py::test_sign_off_denied_and_read_only_runs_without_approval (13 percent), then `exit=1`. Cause not found. Rerun 02b-rerun1 completed normally (same single failure as F1). |
| F3 | My own setup slip | `_superseded-sql-ascii-cluster/` | My first Postgres cluster was created in SQL_ASCII (no encoding flag). psycopg then returned bytes (`TypeError ... got b'postgres'`; 195 failed, 51 errors on 3.12; mutant baseline error). All logs from that cluster are moved to `_superseded-sql-ascii-cluster/` and every DSN job was rerun on a UTF8 cluster (`initdb -E UTF8 --locale=C.UTF-8`). Only the logs outside that folder count. The first full runs on that cluster also ended without a summary (3.13 at 55 percent exit=1, no-DSN 3.13 at 78 percent exit=0), also unexplained; the later no-DSN 3.13 run (02c) and the DSN 3.13 run (02a) completed. |
| F4 | Postgres version | all DSN jobs | 16.15 (Ubuntu package), NOT 17.10 as in CI. apt has no postgresql-17 (apt.postgresql.org unreachable: HTTP 000). A 17 binary from a PyPI wheel (pgembed, advertises 17) was downloaded and unpacked, but the sandbox denied running it as code from an external source, so I deleted it and did not work around it. Next step for the owner or lead: allow it, or run these on a 17 service. |
| F5 | Install flag differs from CI | all venvs | `uv sync --locked --no-build` fails here (`hadavin-sdk ... marked --no-build but has no binary distribution`; local uv 0.11.32, CI pins 0.13.6). Used `uv sync --locked --all-extras --group test --group scan` (builds the project itself). Lock file honoured. |
| F6 | Not run exactly as CI | see Not run | Vault service and 17.10 absent; mutants not alone on the machine (other agents' jobs ran at the same time through the same slots). |

## Results (exit code is the `exit=` line at the end of each log)

| Step | Command | Python | Counts | Exit | Log |
|---|---|---|---|---|---|
| 1a | `ruff check src tests demos tools` (ruff 0.17.1) | 3.13 | All checks passed | 0 | 01-lint-bandit.log |
| 1b | `ruff format --check src tests demos tools` | 3.13 | 324 files already formatted | 0 | 01-lint-bandit.log |
| 1c | `bandit -q -r src demos tools -ll` (bandit 1.9.4, from the scan group) | 3.13 | no findings (only "nosec ... no failed test" warnings) | 0 | 01-lint-bandit.log |
| 2a | `pytest -v -m "not live and not perf" -rfEs`, DSN set, PG 16.15, HADAVIN_REQUIRE_PINNED_UNIDATA=1 (as CI on 3.13) | 3.13 | 1 failed, 10683 passed, 1 skipped, 28 deselected | 1 | 02a-full-py313-dsn.log |
| 2b | same, DSN set, pin variable unset (as CI py312 job) | 3.12 | FIRST RUN: no summary (F2) | 1 | 02b-full-py312-dsn.log |
| 2b-rerun | same | 3.12 | 1 failed, 10683 passed, 1 skipped, 28 deselected | 1 | 02b-rerun1-full-py312-dsn.log |
| 2c | same, NO DSN, pin variable set | 3.13 | 10165 passed, 520 skipped, 28 deselected (519 more skips than with the DSN) | 0 | 02c-full-py313-nodsn.log |
| F1 check | `pytest -v tests/demo_askdata/test_validate_harm.py`, server restarted with PGHOST/PGPORT in its environment | 3.13 | 253 passed | 0 | 02a-single-askdata-dblink-server-env-py313.log |
| F1 check (client env only) | same file, PGHOST/PGPORT only in the client | 3.13 | 1 failed, 252 passed | 1 | 02a-single-askdata-dblink-test-py313.log |
| 3a | `python tests/migrate_mutants.py` (DSN set) | 3.13 | 100 of 100 killed; baseline passed; not killed: [] | 0 | 03-mutants-py313.log |
| 3b | `python tests/migration_numbers_mutants.py` | 3.13 | 40 of 40 good; problems: [] | 0 | 03-mutants-py313.log |
| 3c | `git status --short` in the worktree after 3a and after 3b | 3.13 | 0 lines both times (clean) | n/a | 03-mutants-py313.log |
| 4 | The 9 migration test files (test_k2_migrations, test_k5_fixes2, test_migration_names, _numbers, _numbers_guards, _postgres, _rules, _wiring, test_p2_postgres), DSN set, run 1 | 3.12 | 576 passed, 3 deselected, 0 skipped | 0 | 04-migtests-py3.12-dsn-run1.log |
| 4 | run 2, same cluster | 3.12 | 576 passed, 3 deselected | 0 | 04-migtests-py3.12-dsn-run2.log |
| 4 | random order, seed 7311 (own plugin scripts/shufplugin.py; pytest-randomly not installed) | 3.12 | 576 passed, 3 deselected | 0 | 04-migtests-py3.12-dsn-random-seed7311.log |
| 4 | run 1 | 3.13 | 576 passed, 3 deselected | 0 | 04-migtests-py3.13-dsn-run1.log |
| 4 | run 2 | 3.13 | 576 passed, 3 deselected | 0 | 04-migtests-py3.13-dsn-run2.log |
| 4 | random order, seed 7311 | 3.13 | 576 passed, 3 deselected | 0 | 04-migtests-py3.13-dsn-random-seed7311.log |
| 5 | Fail-before: base 0dabf1fa7a2ed58e14b8bca13be1141ac59f9c71 (merge-base of origin/main and ef2adc7) in `/home/user/build/EV-P73-ef2adc7/base`; head's 9 test files, tests/conftest.py and tests/fixtures/{dsn_skip,migration_role,runbook}.py copied on; `PYTHONPATH=base/src` (log prints the import path); DSN set; `--continue-on-collection-errors` | 3.13 | per-test: 118 FAIL, 236 PASS, 3 collection ERROR (the 3 files cannot be imported on base: test_migration_numbers_guards.py AttributeError, test_migration_postgres.py, test_migration_rules.py, so their tests count as not run). By file: wiring 72 FAIL/1 PASS; names 35 FAIL/27 PASS; numbers 8 FAIL/129 PASS; k2 2 FAIL/43 PASS; k5_fixes2 1 FAIL/20 PASS; p2_postgres 0 FAIL/16 PASS | 1 | 05b-failbefore-base-py313-dsn.log, 05b-failbefore-junit.xml, 05b-failbefore-per-test.tsv |
| 5 (first try) | same without `--continue-on-collection-errors` | 3.13 | interrupted: 3 errors during collection, nothing ran | 2 | 05a-* |
| 6 | `python tools/scan_repo.py` | 3.13 | no output | 0 | 06-scan-repo.log |

## Not run
- CI's separate steps: `python tests/stage_mutants.py` and `pytest -m perf` (not in the brief).
- Anything needing the Vault service (HADAVIN_TEST_VAULT_ADDR unset): those tests did not run against Vault.
- Postgres 17.10 (see F4); all DSN results are on 16.15.
- Mutant runs were not alone on the machine (other agents held other heavy slots).
- Fail-before for the 3 test files that cannot be imported on base (no per-test result exists).
- Full suite with the test-run path for `--no-build` install (F5).

## Cleanup
Postgres cluster stopped; data in /tmp/ev73-pg (throwaway, not in the repo). Downloaded pgembed wheel and its unpacked copy deleted. No other process of mine is running. A Postgres on another port belonging to another agent was left untouched. Nothing committed or pushed. The base worktree `/home/user/build/EV-P73-ef2adc7/base` has the copied test files as uncommitted changes (by design).

R-numbers: none consulted (evidence run only; no studio bible available in this environment).
Token use: about 60 tool calls, no model calls made by the runs.

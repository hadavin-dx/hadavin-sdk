# PR 73 (core/P3a-2) head 2b0941b7092e09a209c9808dcc8aab20b109869f, evidence run cloud2

Postgres 16.15 own cluster (port 55430, UTF8), HADAVIN_TEST_PG_DSN set, uv --frozen --all-extras --group test. Every log's first line names the head. Inner rc = the `exit=` line the log ends with.
Note: the first `bandit` attempt (no scan group) failed to spawn and is not included; the bandit.log here is the rerun with --group scan, `-r src demos tools -ll` as in CI.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed | ruff-check-tools.log (src tests demos only: ruff-check.log) |
| ruff format --check src tests demos tools | 3.13 | 0 | 322 files formatted | ruff-format-tools.log (ruff-format.log) |
| bandit -q -r src demos tools -ll | 3.13 | 0 | no issue lines | bandit.log |
| pytest -m "not live and not perf" -rs | 3.12 | 1 | 1 failed, 10631 passed, 1 skipped, 28 deselected | pytest-312.log |
| pytest -m "not live and not perf" -rs | 3.13 | 1 | 1 failed, 10631 passed, 1 skipped, 28 deselected | pytest-313.log |
| pytest -m perf | 3.12 | 0 | 28 passed | perf-312.log |
| pytest -m perf | 3.13 | 0 | 28 passed | perf-313.log |
| tests/migration_numbers_mutants.py (P3a-1) | 3.13 | 0 | 40 of 40 good | p3a1-mutants.log |
| tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good | stage-mutants.log |
| tools/scan_repo.py | 3.13 | 0 | clean | scan-repo.log |

The one failure on both pythons: tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]: dblink on the server connects through the default socket /var/run/postgresql/.s.PGSQL.5432, which this cluster (socket in /tmp, port 55430) does not provide. Same failure seen earlier on base (q195, q275). Not rerun with a server on 5432 (other clusters on the machine).

NOT RUN: the P3a-2 mutants runner (66 mutants, mutants.py): not in the repo or handover, only a hand-edited log of an earlier run exists; fail-before; hand probes (psql probe files are not scripted); Postgres 17; CI; semgrep, zizmor, pip-audit, gitleaks; pytest -m live.

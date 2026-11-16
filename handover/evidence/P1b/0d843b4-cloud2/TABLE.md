# P1b evidence at 0d843b4 (cloud2). Postgres 16 own cluster, HADAVIN_TEST_PG_DSN set.
| command | python | inner rc | counts | log |
|---|---|---|---|---|
| pytest -m "not live and not perf" | 3.12 | 1 | 1 failed, 11267 passed, 1 skipped (dblink-connect, environmental: server-side dblink_connect('dbname=postgres') looks for socket /var/run/postgresql/.s.PGSQL.5432, cluster is on port 55410) | pytest312.txt |
| pytest -m "not live and not perf" | 3.13 | 1 | same: 1 failed, 11267 passed, 1 skipped | pytest313.txt |
| pytest -m perf | 3.12 | 0 | 44 passed | perf312.txt |
| pytest -m perf | 3.13 | 0 | 44 passed | perf313.txt |
| tests/textnorm_mutants.py | 3.13 | 0 | 216 of 216 good | textnorm-mutants313.txt |
| tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good | stage-mutants313.txt |
| tests/mutation_runner_mutants.py | 3.13 | 0 | 62 of 62 good | runner-mutants313.txt |
| ruff check . | 3.13 | 0 | all passed | ruff-check.txt |
| ruff format --check . | 3.13 | 0 | | ruff-format.txt |
| bandit -ll -r src tools (uvx bandit==1.9.4; not in the venv) | 3.13 | 0 | clean | bandit.txt |
| tools/scan_repo.py | 3.13 | 0 | | scan_repo.txt |
NOT RUN: fail-before vs core/P1a (no earlier P1b evidence did it); hygiene; ruff/bandit/mutants on 3.12 (mutants as in earlier evidence, 3.13 only); Postgres 17.
Discarded: INVALID-pytest312-no-DSN.txt (first attempt, DSN unset, killed); bandit-FAILED-notinstalled.txt (rc 127, bandit absent from venv).

# PR 84 (ci-evidence) round 1, egm-codebase-details, head 8a677ad (condensed). Retry on snapshot with DIFF. ci.yml and uv.lock not in snapshot.
Blockers: none confirmed.
M1 evidence.yml:98 `uv sync --locked --no-build ...`: unverified; project build backend uv_build might be refused by --no-build; needs uv.lock; compare ci.yml.
M2 evidence.yml:109,112 hashFiles guard turns a missing stage_mutants runner into silent skip (loop at :122 exits 2).
M3 evidence.yml:26 example runner tests/textnorm_mutants.py does not exist; real: stage_mutants.py, mutation_runner_mutants.py, migration_numbers_mutants.py.
M4 evidence.yml:117-124 `exit $rc` in a pipeline subshell does not stop loop; failing first runner masked by last. Record failures in a variable, exit after loop.
M5 evidence.yml:130-137 summary `|| true` and lists head.txt/env.txt as sections.
Nits: psql --version may fail under bash -e; image digests may drift vs ci.yml; cancel-in-progress discards evidence (state it); pythons input untyped.
Verified: markers perf/live exist; extras and group test exist; env names HADAVIN_TEST_PG_DSN/VAULT_ADDR; mutant runners exist and run from repo root; permissions contents: read, no secrets.

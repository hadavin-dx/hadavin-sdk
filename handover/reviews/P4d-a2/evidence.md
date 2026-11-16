# P4d-a2 evidence (head 7a844087fa9ba843c4f68374be7f96d5b94a78e1)
NOT BUILT: a2-ii (write wrapper, retry, StoreBusy), anything needing P3a. Mutation run was NOT through heavy.sh.
- fail-before (base, new tests): 88 failed, 46 passed, 2 collection errors (fail-before.txt)
- final full pytest py3.13 at head (heavy.sh, PG 16.15 :55432, REQUIRE_PG=1): 1 failed, 10355 passed, 1 skipped (pytest-313-final.txt)
  - failure: demo_askdata test_validate_harm[dblink-connect] needs PG on 5432; fails identically on base (environmental)
- py3.12 full run was at c31f336 (before 2 extra test commits): 1 failed (same dblink), 10348 passed, 1 skipped (pytest-312.txt). Not re-run at head.
- ruff check, ruff format --check: clean. bandit -ll -r src (uvx): 0 issues (nosec warnings only).
- mutation: ~54 hand-written mutants (mutate.py, mutants.md, mutants2.md); m19/m20 equivalent; rest killed after added tests.

# a2-ii final (head f8b9056599e944809dac7a6e4e833fdcd09b20ed, origin/main c709df3 merged)
- UV env: UV_PROJECT_ENVIRONMENT=<build-dir>/.venv (3.13) and <build-dir>/.venv312 (3.12); mutants with PYTHONPATH=<mut worktree>/src. PG 16.15 on 127.0.0.1:55432, HADAVIN_REQUIRE_PG=1.
- full pytest 3.13 (heavy.sh): 10563 passed, 1 skipped, 0 failed (pytest-313-final2.txt). 3.12 (heavy.sh): 10563 passed, 1 skipped, 0 failed (pytest-312-final2.txt). dblink-connect now passes (it was an environmental failure).
- stage tests: tests/test_stage_names.py 97 passed; tests/stage_mutants.py 37 of 37 good (stage-mutants.txt).
- ruff check and format --check: clean. bandit -ll -r src tools: No issues identified (no nosec in postgres.py; 6 existing nosec elsewhere, none mine). No noqa added in a2-ii files.
- fail-before: fail-before-a2ii.txt (hostile file: 30 failed on base with two no-op stubs; wrapper file: ImportError at collection, no _writes).
- mutants of a2-ii through heavy.sh at this head: mutants-final.md: 40 killed, 1 survived (w10f). w10f: the Postgres wrapper's check_text of plain str arguments; the driver refuses the same NUL and lone-surrogate values and the wrapper maps them to ValueError, so the test sees no difference. Kept as defence in depth, equivalent survivor. (Earlier runs mutants3/4/5.md: w13 hung a first harness because a plain Lock deadlocks test setup; fixed with a thread-guarded setup and a 60 s watchdog; w15, w21 survived first and got tests; w07 predicate layer and w16 StoreBusy guard were redundant and removed from the code.)
- a2-i/b mutants: mutants.md, mutants2.md (m19, m20 equivalent: equivalent-survivors.md).
- NOT DONE: check_id on existing writes (ticket item 7, BN-P4d-3); the 4 is_connectivity_error caller rows (audit/chain.py, cli.py, tick.py) beyond the unit rows; real concurrent A2 race rows with pg_stat_database.deadlocks; the 8-process test; mutation of a2-i/b not re-run at this head (run at c31f336, tests only added since).

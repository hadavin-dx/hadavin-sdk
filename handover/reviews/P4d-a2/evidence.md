# P4d-a2 evidence (head 7a844087fa9ba843c4f68374be7f96d5b94a78e1)
NOT BUILT: a2-ii (write wrapper, retry, StoreBusy), anything needing P3a. Mutation run was NOT through heavy.sh.
- fail-before (base, new tests): 88 failed, 46 passed, 2 collection errors (fail-before.txt)
- final full pytest py3.13 at head (heavy.sh, PG 16.15 :55432, REQUIRE_PG=1): 1 failed, 10355 passed, 1 skipped (pytest-313-final.txt)
  - failure: demo_askdata test_validate_harm[dblink-connect] needs PG on 5432; fails identically on base (environmental)
- py3.12 full run was at c31f336 (before 2 extra test commits): 1 failed (same dblink), 10348 passed, 1 skipped (pytest-312.txt). Not re-run at head.
- ruff check, ruff format --check: clean. bandit -ll -r src (uvx): 0 issues (nosec warnings only).
- mutation: ~54 hand-written mutants (mutate.py, mutants.md, mutants2.md); m19/m20 equivalent; rest killed after added tests.

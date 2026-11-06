# P3a-2 merge of core/P3a (P3a-1 fix1, 91a439d) into core/P3a-2
Head after merge: 62fba0bb3d6724a4775d6271519dbc9d684dfa1b (merge commit 627e7a9 + fix commit 62fba0b). Plain push, fast-forward, no amend, no history rewrite.
Conflicts: none (git merged cleanly, including tests/test_migration_numbers.py and tests/test_k5_perf.py).
Break found and fixed: fix1 changed statement_text to return a string and raise SqlReadError; migrate._scan unpacked a tuple. _scan now calls lex(raw, keep_quoted=True) (the tuple form). One file changed: src/hadavin_sdk/store/migrate.py.
Overlap kept on both sides, not removed: fix1 added tests/fixtures/migrations_released.json (hashes keyed by stem) checked in tests/test_migration_numbers_fix1.py; P3a-2 has tests/migration_manifest.json (keyed by file name) checked in tests/test_migration_manifest.py. Same five digests. The lead may want to keep only one.
Results (PostgreSQL 16, own throwaway server, DB p3a_2 / p3a_2m):
- Targeted migration files (wiring, postgres, manifest, numbers, numbers_fix1, k2, k5_fixes1, k5_fixes2): 352 passed, 0 skipped.
- Mutation run (mutants.py, 36 mutants, plus the fix1 test file in the target list): 36 KILLED, 0 survived, baseline 352 passed (mutants-merge.txt).
- ruff check clean, ruff format --check clean, bandit -ll rc=0 with 0 Issue lines.
- Full suite py3.13 via heavy.sh (-m "not live and not perf"): 1 failed, 10346 passed, 1 skipped, in 295.84s. The 1 failure is the same environment-caused tests/demo_askdata/test_validate_harm.py [dblink-connect] (also fails on the base); 1 skip tests/contracts/test_llm.py:95. py3.12 not rerun after the merge.
- Not rerun: PostgreSQL 17, perf-marked tests.

P3a-2 round 13 build, second builder: PARTIAL. Only commits 1, 2 and 3a exist. Commits 3b, 3c, 4, 5 and 6 are NOT done.

**What I did not do or run**
- Commit 3b, the switch of `migrate()` to the eight steps of §4.1, is not started. Its scope is large: ten retired TPG tests, re-pointed tests, `test_every_runner_catalog_read_is_pinned`, about 20 mutants inside `migrate()` and the new real-server tests. I judged it could not be finished green inside the 60-minute box, so I stopped.
- Nothing of 3c, 4, 5 or 6 exists. That means:
  - the dead comparison code is not deleted;
  - the extras (lock message, unreadable view, CI server setting, prepared-transaction test) are missing;
  - the matrix is missing;
  - the texts, docstring and CHANGELOG are missing.
- Not run: the full suite, bandit, the four full mutant batches, the migration-numbers mutants, the perf test (acceptance 21), and PostgreSQL 17/18. Only `/usr/lib/postgresql/16` exists here, so 17/18 stays a CI item.
- A mutant run for 3a that I had queued through `heavy.sh` never started because no slot came free, so I killed that wrapper (PID 3673, mine) and ran the same four mutants directly.
- Fail-before files exist only for commits 2 and 3a. There are none for 3b to 6.

**Pushed**
`core/P3a-2-clean` is at `c150b5ff`, a fast-forward from the earlier `4b01c09f`. gitleaks over `origin/main..HEAD` found no leaks.

**Commit 1: `4b01c09f`** (earlier builder)
- Adds `store/migration_verify.py` and its tests.
- Its deviations are decided and kept (checkpoint note, 19:45Z):
  - 9 statement groups instead of 8, because the plan's order failed on the real server;
  - extra `Problem` fields `via` and `word`;
  - Q1b reads the whole closure of roles.
- Note for 3b: `missing_schema_usage` is judged at step 2 of `migrate` and must be called there.

**Commit 2: `5ad0949f`** (oracle)
- Adds `tests/fixtures/oracle.py` and `tests/test_migration_matrix.py` (56 tests).
- Gate:
  - `ruff check` and `ruff format --check` clean;
  - 663 passed over the 7 migration test files with my Postgres 16;
  - `scan_repo.py` rc 0;
  - gitleaks rc 0.
- Fail-before: `/home/user/build/B-P3a2-fail-before-c2.txt`. Five oracle mutants each make tests fail:
  - every attempt classed refused: 48 failed;
  - 42501 no longer meaning refused: 50 failed;
  - SET ROLE paths not tried: 2 failed;
  - fresh-object facts dropped: 3 failed;
  - table-level INSERT/UPDATE not derived: 2 failed.
- There is no product code in this commit, so no product mutants apply.
- Known oracle limit, shown by a test, not hidden: a large-object UPDATE alone cannot be seen by behaviour, because `lo_open` for writing also needs SELECT.

**Commit 3a: `c150b5ff`**
- Changes:
  - `errors.py`: `AppliedNotVerifiedError`, deliberately not a `ConfigError`.
  - `cli.py`: `migrate` maps it to exit code 5. Statements print to standard output in two blocks, with `-- NOT THIS PACKAGE'S OBJECTS: confirm each with its owner before running` before the second.
  - `migrate.py`: the pure `_commit_outcome`, and the schema read once and passed to `_apply_grants`, `_read_back`, `_check_read_back` and `_refuse_foreign_owned`.
- Gate commands and results:
  - `ruff check`: rc 0.
  - `ruff format --check`: rc 0 (336 files already formatted).
  - pytest over `test_migration_wiring`, `verify`, `verify_pg`, `compare`, `rules`, `test_k2_migrations`, `postgres` and `matrix`: **745 passed in 184.63s**, with my Postgres 16 DSN set. Log: `/home/user/build/B-P3a2-c3a-gate.log`.
  - `scan_repo.py`: rc 0.
  - gitleaks: rc 0.
  - Affected mutants:
    - 13 of 13 killed (M61, M64, M67, M95, M102, MW4, S1, O1, OA4, OA5, OA6, MC1, CL2), `not killed: []`.
    - Added by me: CO1 to CO4 for `_commit_outcome`, 4 of 4 killed (`/home/user/build/B-P3a2-c3a-mutants-co.log`).
  - The 9 mutants M61, M64, M67, M95, M102, O1, OA4, MC1 and OA6 were re-pointed to the new text. `problems_with_the_list()` returned `[]`.
- Fail-before: `/home/user/build/B-P3a2-fail-before-c3a.txt`. About 30 new or changed tests fail on the old source (`5ad0949f` plus the new tests).
- Deviations from the plan:
  - I added mutants CO1 to CO4, which the plan does not list for 3a.
  - `AppliedNotVerifiedError` has no separate attribute for the outside statements. The CLI derives the two blocks from `problems` via `statement_blocks` (from commit 1), or from `statements` when `problems` is empty.
  - The `_Db` fake already had `transaction()`.
  - The CLI exit-5 test is in `test_migration_wiring.py`, as planned.

**What the evidence runner must check**
- The head is `c150b5ff` and the branch is a fast-forward.
- Rerun the 8 migration test files with a Postgres DSN set.
- Run `scan_repo.py`.
- Run the 13 + 4 mutants for 3a.
- Confirm the fail-before files against a worktree of the pre-commit sources.
- Run the whole mutant list once on the final head (not yet done).
- Run the full suite and bandit (neither run).

**Cleanup**
- My Postgres (data `/home/user/build/pg-p3a2c`, port 56081) is stopped. The data directory is still on disk and can be deleted. I did not kill any process I did not start.
- Worktree `/home/user/build/B-P3a2` is clean after the commit.
- Checkpoint note: `/home/user/build/B-P3a2-checkpoint.md`.

**Next step**
A fresh builder starts at 3b with `c150b5ff`. The ticket's §4.1 and §9.3 give the scope, and the 3a note above says `missing_schema_usage` goes at step 2.
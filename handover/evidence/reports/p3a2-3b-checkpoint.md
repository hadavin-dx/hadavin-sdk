# P3a-2 commit 3b checkpoint (22:05Z)

State: NOT green, NOT committed, NOT pushed. Branch core/P3a-2-clean still at c150b5ff.

Done (uncommitted, in worktree /home/user/build/B-P3a2; patch copy /home/user/build/B-P3a2-c3b-wip.patch):
- migrate() switched to the eight steps (migrate.py, migration_verify.py).
- New tests/test_migration_steps.py (28 pass). Wiring, steps, verify, k2 files: 282 passed (/home/user/build/B-P3a2-c3b-quick.log). ruff check clean.
- Mutants file edited (E1-E27 added, some re-pointed, four retired); none run yet.

Not done:
- test_migration_postgres.py: 19 failed, 195 passed (/home/user/build/B-P3a2-c3b-tpg8.log; names in /home/user/build/B-P3a2-c3b-failing.txt). Wording and behaviour re-points still to do.
- The 17 real-server tests of ticket 7.6 and test_the_rights_table_equals_what_apply_grants_is_called_with: not written.
- Mutant runs, fail-before proof, scan_repo, gitleaks, bandit, full suite: not run.
Next: fix the 19, write the 17, run mutants via heavy.sh, gates, commit, push.

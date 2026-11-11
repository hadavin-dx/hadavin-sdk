# P3a-2 commit 3b, builder 2, checkpoint 2 (2026-11-11 22:46 UTC)

Head: f468bde0 plus uncommitted edits in worktree /home/user/build/B-P3a2-b2 (branch wip/b2-p3a2-3b). Nothing committed or pushed yet by builder 2.

## Done
- 19 failing tests in tests/test_migration_postgres.py re-pointed. Full file: 214 passed (/home/user/build/B2-tpg-b.log).
- New real-server tests in tests/test_migration_verify_pg.py: after-commit exit 5, step 8 cannot connect, any error inside step 8 (3 cases), saved statement timeout, role switch in the DSN, one snapshot, commit refused (exit 2), lost connection at commit (exit 5), upgrade from main's state, public schema (pass and CREATE-for-everyone refused), pg_monitor at step 2, grant-option holder not dropped at step 2, ledger trigger that disables audit triggers, reviewed definer, third-role owner of a managed name (3 kinds), verify cost on a large catalog (perf).
- Unit test test_the_rights_table_equals_what_apply_grants_is_called_with (tests/test_migration_verify.py).
- Mutant list: 11 retired (SD4 SD5 OW7 OW8 FB1 FB2 FB3 SO1 SO2 SO3 CS2) plus OW9; E5, E22, OA3 text fixed; OW5 OW6 SD7 SD8 re-planted in live code. test_migration_rules.py: 159 passed. ruff check and format clean.
- gitleaks on the staged diff: no leaks.

## Not done / found
- The comparison code ticket 5.3 says to delete (effective_problems, _refuse_unlisted_grantees, _Objects, _Changed, _changed_since and their SQL, plus the TCMP tests of test_migration_compare.py) is STILL in migrate.py (dead, not called). The previous builder did not delete it. Not done by me yet; needs the lead's decision (time box).
- Section 6 tests (unreadable lock view, duplicate CREATE) belong to commit 4 and are not written; the code for 6.1/6.2 is not in migrate.py.
- Ticket text said one problem line for pg_monitor; the code gives four lines (membership plus three implied built-in roles) and one distinct statement. Test pins that.

## Next
- Mutants E1-E27 running (log /home/user/build/B2-mut-E.log), then a 60-mutant sample, then full run alone on the final head.
- Fail-before proof, scan_repo, bandit, one full suite, commit, push.

## Checkpoint 3 (23:10 UTC)
- Done: E1-E27 run: 22 of 27 first; fixed E11/E14/E16 (harness reports escaping errors as assertions), E25 (new killer), E5 retired (dead branch removed from step 4; server writes no `*`). Fail-before proof in /home/user/build/B-P3a2-fail-before-c3b.txt (103 failed on c150b5ff). ruff, scan_repo, bandit, gitleaks clean. Local commit 811fddf7 (not pushed).
- Running: full mutant run alone (B2-mut-full.log). Next: full suite, push wip then core/P3a-2-clean if green.
- Blockers: none. Open for lead: ticket 5.3 dead-code deletion, commit-4 tests.

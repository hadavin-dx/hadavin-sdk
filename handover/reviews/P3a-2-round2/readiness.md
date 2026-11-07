# PR 73 (P3a-2) @ea40242: round 2, implementation-readiness review (condensed by the coordinator, ids kept)
Verdict: code sound on a read, no Blocker in migrate.py; NOT sign-off ready as evidence. Ran nothing.
M-1 Major | evidence/P3a-2/ea40242/fail-before.txt | 48 failed on old code, but only runbook/rename/name/dollar tests. No read-back (H11) test, role-switch, hidden-COMMIT, test_migration_wiring.py, test_h11_same_run in the fail-before set (those files were not copied). Re-run with wiring + full postgres test file against main's migrate.py; say per test.
M-2 Major | all logs, ci.yml:41,111 | Every DB result is Postgres 16.15; CI uses 17.10. Evidence command 7 (lexer/scs/lock probes on 16 and 17) missing (build note 17). Run on 17.10 or treat first green CI as proof and block merge until then. UNVERIFIED on 17.
M-3 Major | test_migration_postgres.py:1103-1121,1048-1076; ci.yml:89,151 | All tests connect as superuser; docs say run migrate as a non-superuser role. Add a test with a LOGIN owner role running two plants (DISABLE TRIGGER, SET LOCAL ROLE).
M-4 Major | CHANGELOG case (c) and Upgrade bullet; migration_numbers.py:316 | Runbook says migrate checks released files' hash/name; released_problems is called nowhere in src. False safety claim. Call it from migrate() or reword to "the tests refuse".
M-5 Major | CHANGELOG case (e); tests | Case (e) E1/E2/E3 repair untested (CHANGELOG admits). Add psql tests or remove (e). Open point 12 precondition answer unconfirmed.
M-6 Major | test_migration_postgres.py:940 | PREVIOUS_RELEASE_LAST 0004 vs lead's 0005_evidence (same as C2).
M-7 Major | scope | Layer 1 pg_dump comparer, BN-20 pg_dump check, M63 and M72-M86 not in PR (deferred to P3a-3); 124 mutants not reproducible. Lead to confirm split in writing; PR closes only the wiring half.
N-1 Nit definitions after use. N-2 Nit read-back filters on current_schema() each read. N-3 Nit keep the dblink-failing run, name the verdict run.
Held: 66/66 mutants; 10579 passed on both pythons (one dblink-connect run documented); perf 28.

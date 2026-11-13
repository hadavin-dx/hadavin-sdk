# B-P3a2-5 builder notes (round 15, security path)

## For the lead: replacement wording for handover/questions-for-lead.md, q-p3a2-o8-schema-owner (I did not edit that file; the branch has no handover/ folder)
Replace "The stricter reading is built and tested but OFF behind ... Safe default: keep it OFF." with:
"The stricter reading sits behind the named switch ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START in store/migrate.py. The default is OFF, the PERMISSIVE value: ticket line O8 stays UNMET until the ticket line is edited or the switch is turned ON (a role outside the family that owns the schema of the run can drop the package's tables). Real-server cell for each value: test_o8_a_schema_owned_outside_the_family_at_the_start_is_refused_only_with_the_switch_on (ON refuses and keeps nothing; OFF applies the file; both passed on PostgreSQL 16 in this worktree). ON would refuse the printed setup (an administrator-owned schema with CREATE granted to the migration role)."

## Issues (round 15; order 4, 2, 3, 1, 6, 5)
4. O13-O16 now built under carrier C10 (statements use the named role or everyone on `{o}`); empty-by-logic table: one written reason per effect (16 pairs: 13 map objects, 1 default right with no schema, 2 large objects), explicit id list asserted in the count test; C8 and C13 asserted as sets with reasons (C13 is a dict now). Computed: 580 cells, 32 empty, 548 built, 32 stop at step 0, 516 reach the data checks, 523 refused, 25 return.
2. Real-server cells for the O8 switch ON and OFF (`test_o8_a_schema_owned_outside_the_family_at_the_start_is_refused_only_with_the_switch_on`), plus ON on the `public` schema with and without the migration role owning the database. migrate.py comment and the question wording say OFF is looser than the ticket. Question-file wording is at the top of this file (not edited in handover/: the branch has none).
3. Two PG16 branches are visible skips (`UNRUN: PostgreSQL 17 only`; three PG17 tests named in the CHANGELOG); the PG16 fact became `test_the_server_version_decides_whether_a_role_can_save_a_transaction_timeout` (runs on every server); `connect()` runs exactly one statement (pinned; comment in postgres.py; CHANGELOG says the exit-2 promise starts after connect); 25P04 assertion names three spellings; PG16 idle-timeout margin 200 ms / 1.5 s (7.5 times).
1. CHANGELOG owner sentence fixed; `test_the_changelog_does_not_state_rule_o8_more_strictly_than_the_code_keeps_it` (+ planted-sentence test, + PG17-CI-claim test).
6/5. Mutants V104-V112, V102 gains the real-server killer; assertion messages name the planted fault; wrong docstrings fixed.

## New tests that PASS on c3b2efdb (clean detached worktree, only the 5 test files copied; logs B-P3a2-5-old-fail-*.log), one line each
- O13/O14/O15/O16 x C10 x 2 variants (8 cells): old code already judges them (cells were missing, not the code); killers V109 (O15), V110 (O13), V111 (O16).
- test_o8_a_schema_owned_...[switch-on] / [switch-off]: old code has the same switch; the cells are the missing proof; killer V102 (switch ignored).
- test_o8_switch_on_the_public_schema_...: same reason; killer V108.
- test_c9_a_table_owned_by_the_login_...: old code right; killer V107.
- test_connect_runs_exactly_one_statement_...: old connect has one statement; killer V112 (a second statement).
- test_the_server_version_decides_...: moved assertions of the old PG16 branches; true reason, no mutant.
- test_c13_every_effect_has_a_table_to_move_or_a_reason_it_has_none, count test, test_the_o8_wording_check_sees_a_planted_unconditional_sentence: table/guard tests of the test file itself; the guard is shown able to fail by the planted-sentence test.
- Third-role test (changed, not new): killer V104. C8: V106. C13: V105.
FAIL on c3b2efdb: test_the_changelog_does_not_state_rule_o8_more_strictly_than_the_code_keeps_it, test_the_changelog_does_not_state_a_postgresql_17_run_as_fact (2 failed, 6 passed, 3 skipped in the second selection; 104 passed in the matrix selection).

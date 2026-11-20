# B-mutant-cases: mutants for plan step B and the test that kills each

Revised 2026-11-20 by the test-writer of core-c (not the builder of step B, which is core-b). Test file:
`tests/test_grants_negative_roles.py` (T). The 12 former "cases to enable" are real tests now (docstring of T);
they run when `STEP_B` is true (`migrate()` takes `reset_role`) and skip with a reason on main's tree.
"APPLIED" = the mutant was applied by hand in the worktree of core-b 576f292 (never in /home/user/hadavin-sdk/src),
run with PostgreSQL 16, and the named tests failed; see `evidence/B-grants-rework.md` for the raw lists.
"NOT APPLIED" = the killing test exists and is green on the real code, the mutant itself was not run.
Test names are shortened to the part after `test_`.

| # | Mutant | Killed by | Status |
|---|---|---|---|
| 1 | A grant gets wider in `GRANTS` (any role, table, write privilege) | T `every_write_privilege_is_on_the_reviewed_list`, `the_portal_role_writes_nothing_...`, `the_purge_role_holds_delete_only_...`; PG `pg_each_role_is_refused_what_the_map_does_not_give[*]` | APPLIED as M1, M2: killed |
| 2 | Runtime role gets UPDATE on the stop table (`kill_switch` row `"SELECT, UPDATE"`) | T `step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off`, `every_write_privilege_...`, `only_the_reviewed_roles_hold_anything_on_the_stop_state`; also `migrate()` itself refuses ("roles other than the reset role could clear a stop"), so all 52 PG tests error in the fixture. PG `pg_step_b_the_runtime_role_cannot_switch_the_stop_off` and `pg_case3_...` need a map migrate() accepts: NOT APPLIED that way | APPLIED (M1): killed. On main's tree these two are strict xfail (feature test `STEP_B`) |
| 3 | The stop state moves to a new relation and the runtime role may switch it OFF there | `pg_case3_every_way_to_switch_the_stop_off_is_refused_to_the_runtime_role`, `only_the_reviewed_roles_hold_anything_on_the_stop_state` (a new `kill_switch*` relation is not on the list) | NOT APPLIED |
| 4 | A fourth role keyword or `Grant` field added without negative tests | `the_identities_are_the_ones_this_file_knows`, `the_feature_test_agrees_with_the_grant_map` | NOT APPLIED (pin) |
| 5 | Reset role holds more than stop-OFF plus audit append (reads evidence, writes runs or spend, DELETE, TRUNCATE) | `case2_the_reset_identity_holds_exactly_the_reviewed_cells`, `pg_case2_the_reset_role_is_refused_everything_outside_its_reviewed_cells`, `pg_each_role_is_refused_...[reset]`, `no_role_may_truncate_any_table[reset]` | APPLIED as M2 (DELETE on `audit_entries`): 7 tests failed |
| 6 | Reset role cannot append the audit intent | `pg_case5_the_reset_role_appends_its_audit_intent_...`, `pg_case7_limits_reset_with_the_reset_dsn_works_...`, `pg_case2_...` (holds INSERT) | NOT APPLIED |
| 7 | Reset without the audit intent first (intent dropped, or written after the switch) | `reset_writes_the_audit_intent_before_it_touches_the_switch`, `reset_leaves_the_switch_alone_when_the_audit_intent_fails`, `pg_case8_reset_with_the_audit_intent_refused_leaves_the_stop_on`, `case8_...reset_failed` | APPLIED as M4 (line `write_intent` removed from `Limits.reset`): 9 tests failed |
| 8 | Reset through the runtime DSN (`cli.py` builds the store from `dsn_secret_name`, not `reset_credential_ref`) | `case7_limits_reset_builds_its_store_and_audit_from_the_reset_dsn_only`, `case7_..._refused_before_anything_is_built[*]`, `pg_case7_limits_reset_with_the_runtime_login_...`, `pg_case7_limits_reset_with_the_reset_dsn_works_...` | APPLIED as M3: 3 tests failed |
| 9 | Reset role is the same role as, or a member of, another identity | `case1_the_reset_role_is_refused_when_it_is_another_identity[*]`, `pg_case1_migrate_refuses_membership_...[*]` | NOT APPLIED |
| 10 | Stop that waits for the audit write | `stop_switches_first_and_does_not_wait_for_the_audit_write`, `pg_case9_stop_by_the_runtime_role_works_with_the_audit_tables_refusing_writes` | NOT APPLIED |
| 11 | Step B takes so much from the runtime role that it cannot switch the stop ON | `pg_the_runtime_role_can_switch_the_stop_on` (statement chosen per tree) | NOT APPLIED |
| 12 | A grant row without its migration | `a_grant_row_without_its_migration_stops_migrate_before_it_connects`, `case10_a_reset_grant_row_without_its_migration_stops_migrate`, `case10_the_real_migrations_and_the_grant_map_agree` | APPLIED as M6 (row `no_such_relation` in the real map): killed |
| 13 | A migration without its grant row | `a_migration_without_its_grant_row_stops_migrate_before_it_connects`, `case10_a_stop_state_relation_without_its_grant_row_stops_migrate[*]`, `case10_the_stop_state_migration_and_its_grant_rows_arrived_together` | APPLIED as M5 (row `kill_switch_clears` deleted): killed |
| 14 | A migration grants to PUBLIC or leaves a default privilege | `pg_each_role_is_refused_...[stranger]`, `pg_the_catalog_agrees_with_the_matrix_...`, `pg_case11_migrate_refuses_a_reset_role_...[public_grant]` | NOT APPLIED |
| 15 | `_apply_grants` gives a role a privilege the map does not name | `pg_each_role_is_refused_what_the_map_does_not_give[runtime, portal, purge, reset]` | NOT APPLIED |
| 16 | Portal or purge role can read or write the stop state | `pg_no_role_but_the_runtime_and_reset_role_can_read_or_write_the_stop_state[*]` | NOT APPLIED |
| 17 | Runtime role can DELETE or TRUNCATE a stop row | `pg_the_runtime_role_cannot_remove_a_row_of_the_stop_state`, `only_the_reviewed_roles_hold_anything_on_the_stop_state` | NOT APPLIED |
| 18 | Wildcard or `ALL` in a grant row; UPDATE on a sequence | `no_grant_uses_a_wildcard_...`, `no_role_but_the_runtime_role_may_use_a_sequence`, `pg_only_the_runtime_role_may_draw_from_a_sequence[*]` | NOT APPLIED |
| 19 | A role may UPDATE or DELETE an audit row | `nobody_may_change_or_remove_an_audit_row[*]`, `pg_case5_...` (as the reset role) | APPLIED as M2: killed |
| 20 | `migrate()` again does not take back a hand-made grant of the reset role; a superuser reset role is accepted | `pg_case11_migrate_again_takes_back_...`, `pg_case11_migrate_refuses_a_reset_role_that_holds_more_...[*]` | NOT APPLIED |
| 21 | A missing stop row reads as OFF, or a reset turns it into OFF | `pg_case12_a_missing_stop_row_reads_as_on`, `pg_case12_a_reset_cannot_turn_a_missing_stop_row_into_off` | NOT APPLIED |

## Pins the builder of a later step must change on purpose
- `WRITES_AFTER_STEP_B` and its siblings (`STOP_HOLDS_*`, `RESET_HOLDS`, `DELETES_*`, `PURGE_COLS_*`, `PORTAL_NEVER_*`,
  `AUDIT_HOLDERS_*`): the hand-written, reviewed lists; a new table or privilege goes in by someone who is not the builder.
- `STEP_B` is the one feature test; `the_feature_test_agrees_with_the_grant_map` fails on a half-built tree.
- `TABLES_AT_LEAST`, `GRANT_FIELDS_*`, `ROLE_KEYWORDS_*`.

## Findings on main (not fixed, not ours)
- main `migrate.py:55`: the runtime role may UPDATE the one stop row (what step B removes).
- `redaction_maps` is granted `_RW` while the comment says "append and purge only (no UPDATE)". See evidence/B-grants-rework.md.

## Runs
See `handover/core-c/evidence/B-grants-rework.md` (core-b tree with PostgreSQL 16: 106 passed; main's tree: 37 passed,
39 skipped, 2 xfailed with a DSN). PostgreSQL 17, Python 3.12: NOT RUN.

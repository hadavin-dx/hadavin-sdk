# B-mutant-cases: mutants for plan step B and the test that kills each

Written 2026-11-20 by the test-writer of core-c (not the builder of step B). Test file:
`tests/test_grants_negative_roles.py` (short name below: T). "Case n" is entry n of the list "Cases to enable when
step B lands" in the docstring of T: it is NOT code yet, because it needs a role, table or migration name that
step B has not chosen.

Status words: KILLED = a test in T fails today when the mutant is applied (the first row was run, see the end);
KILLED-PG = the same, but only with `HADAVIN_TEST_PG_DSN` set; XFAIL = the test exists, is marked
`xfail(strict=True)` and turns red when step B makes it pass (remove the marker then); TO ENABLE = not code.

| # | Mutant | Killed by | Status |
|---|---|---|---|
| 1 | A grant row gets wider in `GRANTS` (any role, any table, any write privilege; example: `purge="UPDATE"` or `portal=True` on `kill_switch`) | T `test_every_write_privilege_is_on_the_reviewed_list`, `test_only_the_runtime_role_holds_anything_on_the_stop_table`, `test_the_portal_role_writes_nothing_and_reads_no_secret_or_control_table`, `test_the_purge_role_holds_delete_only_and_no_whole_table_read` | KILLED (run) |
| 2 | Grant UPDATE on the stop table to the runtime role (the state of main: `migrate.py:55`) | T `test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off`; T `test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off` (plain UPDATE and the upsert of `postgres.py:453-457`, checks the row afterwards) | XFAIL (case 3) |
| 3 | The stop state moves to a new relation and the runtime role may switch it OFF there | case 3 (statements to update), case 2 | TO ENABLE |
| 4 | Reset identity added without negative tests (a fourth role keyword in `migrate()` or a new `Grant` field) | T `test_the_identities_are_the_ones_this_file_knows` goes red until `HOLDS` and `WRITES` name the role | KILLED (pin) |
| 5 | Reset role holds more than stop-OFF plus audit append (reads evidence, writes runs or spend, DELETE, TRUNCATE) | case 2 (the matrix by statement, once the role is in `HOLDS`); T `test_no_role_may_truncate_any_table`, `test_delete_is_held_only_on_the_outbox_and_the_purged_evidence` | TO ENABLE (TRUNCATE and DELETE parts KILLED once the role is in `HOLDS`) |
| 6 | Reset role cannot append the audit intent (reset is then impossible, or done without audit) | case 5 | TO ENABLE |
| 7 | Reset without the audit intent first (switch, then audit; or `write_outcome` in place of `write_intent`) | T `test_reset_writes_the_audit_intent_before_it_touches_the_switch`, `test_reset_leaves_the_switch_alone_when_the_audit_intent_fails`; existing `tests/test_review_fixes.py::test_stop_works_when_audit_is_down`; database level: case 8 | KILLED (in memory) |
| 8 | Reset through the runtime DSN (`limits reset` keeps building one store, `cli.py:184-209`) | case 7; and row 2 at database level (the runtime identity is refused whatever the CLI does) | TO ENABLE / XFAIL |
| 9 | Reset role is the same role as, or a member of, the runtime role (one identity under two names) | case 1 | TO ENABLE |
| 10 | Stop that waits for audit (intent before the switch, or an audit error stops the switch) | T `test_stop_switches_first_and_does_not_wait_for_the_audit_write`; existing `test_stop_works_when_audit_is_down`; database level: case 9 | KILLED (in memory) |
| 11 | Step B takes so much from the runtime role that it cannot switch the stop ON | T `test_pg_the_runtime_role_can_switch_the_stop_on` (a pin on today's table and column: update it if the stop state moves) | KILLED-PG |
| 12 | A grant row without its migration | T `test_a_grant_row_without_its_migration_stops_migrate_before_it_connects` (the real files, and `migrate()` refuses before `connect`) | KILLED |
| 13 | A migration without its grant row (new relation, no `GRANTS` entry) | T `test_a_migration_without_its_grant_row_stops_migrate_before_it_connects`; case 10 for the manifest pins | KILLED |
| 14 | A migration grants to PUBLIC, or leaves a default privilege (a role nobody granted can read or write) | T `test_pg_each_role_is_refused_what_the_map_does_not_give[stranger]`, `test_pg_the_catalog_agrees_with_the_matrix_for_every_relation_of_the_schema` | KILLED-PG |
| 15 | `_apply_grants` gives a role a privilege the map does not name, or the three roles granted together leak into each other | T `test_pg_each_role_is_refused_what_the_map_does_not_give[runtime, portal, purge]` (one statement per cell, connected as the role) | KILLED-PG |
| 16 | Portal or purge role can read or write the stop state | T `test_pg_no_role_but_the_runtime_role_can_read_or_write_the_stop_state`; after step B: case 6 | KILLED-PG |
| 17 | Runtime role can DELETE or TRUNCATE the stop row (a missing row reads as ON, but the "by" is lost) | T `test_pg_the_runtime_role_cannot_remove_the_stop_row`, `test_only_the_runtime_role_holds_anything_on_the_stop_table` | KILLED |
| 18 | A wildcard or `ALL` in a grant row; UPDATE (setval) on a sequence; a sequence opened to portal or purge | T `test_no_grant_uses_a_wildcard_or_a_privilege_outside_the_plain_ones`, `test_no_role_but_the_runtime_role_may_use_a_sequence`, `test_pg_only_the_runtime_role_may_draw_from_a_sequence` | KILLED |
| 19 | Runtime role may UPDATE or DELETE an audit row | T `test_nobody_may_change_or_remove_an_audit_row`; existing `tests/test_k2_migrations.py::test_the_runtime_role_cannot_update_or_delete_the_audit_log` | KILLED |
| 20 | `migrate()` run again does not take back a hand-made grant to the reset role; a superuser reset role is accepted | case 11 | TO ENABLE |
| 21 | The stop row is missing in the new shape and reads as OFF | case 12 | TO ENABLE |

## Pins the builder of step B must change on purpose (plan v4 B2, last bullet)

- T `test_the_identities_are_the_ones_this_file_knows`: the role keywords of `migrate()` and the fields of `Grant`.
- T `WRITES`: the hand-written list of every write privilege. A new row for the reset role and any change to the
  runtime row of the stop table go here, reviewed by someone who is not the builder.
- T `test_only_the_runtime_role_holds_anything_on_the_stop_table` and
  `test_pg_the_runtime_role_can_switch_the_stop_on`: named after today's `kill_switch` table and its "on" column.
- The two XFAIL tests: remove the marker when they pass (strict: an unexpected pass is reported as a failure).

## Run on 2026-11-20 (this box)

- Without a database: 19 passed, 13 skipped, 1 xfailed.
- With a throwaway PostgreSQL 16 (trust on loopback like CI, stopped and removed afterwards): 31 passed, 2 xfailed.
  CI runs PostgreSQL 17.10: NOT RUN there.
- Mutant 1 applied in memory (`GRANTS['kill_switch'] = Grant('table', 'SELECT, INSERT, UPDATE', portal=True,
  purge='UPDATE')`, no source file changed): 4 failed, 15 passed in the pure layer.
- Rows 11, 14, 15, 16 were NOT mutated and run: their tests pass on the unmutated code only. Rows marked
  TO ENABLE kill nothing today.

## Finding (not fixed, not ours)

- `src/hadavin_sdk/store/migrate.py:55`: `"kill_switch": Grant("table", _RW)`. The runtime role (the identity
  the agent's process uses) may UPDATE the one row that holds the stop state, so it can switch the stop OFF
  with one statement. This is what step B removes; the two XFAIL tests show it on main.
- `src/hadavin_sdk/store/migrate.py:60` and `:65`: the comment says "append and purge only (no UPDATE)" for the
  K5 evidence tables, and `redaction_maps` is granted `_RW` (UPDATE) to the runtime role. Either the comment
  is about `tool_calls` only or the grant is wider than the comment. Not decided here; `WRITES` records main.

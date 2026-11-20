# B-grants-rework: tests/test_grants_negative_roles.py correct on main's map and on core-b's map

Written 2026-11-20 by the test-writer of core-c (not the builder; core-b built step B and the money store).
Only tests/test_grants_negative_roles.py, tests/test_grants_negative_0007.py (untouched this round) and
handover/core-c/tickets/B-mutant-cases.md were edited in /home/user/hadavin-sdk. Nothing committed or pushed.

## What the file is now (the unverified edit of the earlier agent was read and kept: it was complete and correct)
- ONE feature test: `STEP_B = "reset_role" in inspect.signature(mig.migrate).parameters`. `test_the_feature_test_agrees_with_the_grant_map`
  fails on a half-built tree (keyword without `Grant.reset`, or the reverse).
- Two hand-written reviewed lists: `WRITES_BEFORE_STEP_B` (main) and `WRITES_AFTER_STEP_B` (core-b 576f292), with sibling
  lists per tree (`STOP_HOLDS_*`, `AUDIT_HOLDERS_*`, `DELETES_*`, `PURGE_COLS_*`, `PORTAL_NEVER_*`, `RESET_HOLDS`).
  `test_the_two_reviewed_lists_differ_only_where_step_b_and_the_money_store_say` pins the difference.
- The 12 cases are real tests (map in the module docstring); `@needs_step_b` skips them with the reason "step B is not in this
  tree: migrate() has no reset_role". The two strict xfails are `xfail(not STEP_B, strict=True, raises=AssertionError)`.
- Added by the earlier agent and kept: runtime cannot switch the stop OFF (16 statements), reset role by statement on every
  table, reset role audit intent, `limits reset` with the reset DSN and with the runtime DSN, intent before clear, missing stop
  row, migrate() again takes back hand grants, membership and superuser refusals.

## Commands and raw tails
PostgreSQL 16.15, data /tmp/core-c-grants-pg, loopback, trust, a free port, as user postgres; DSN
`host=127.0.0.1 port=<port> user=postgres dbname=postgres`. Worktree /tmp/core-c-grants = core-b 576f292 (file copied in).
```
core-b tree, DSN set:   pytest -q -p no:cacheprovider tests/test_grants_negative_roles.py tests/test_grants_negative_0007.py
106 passed in 16.51s
core-b tree, no DSN:    (same command, env -u HADAVIN_TEST_PG_DSN)
54 passed, 52 skipped in 0.39s          (all 52 skips: "HADAVIN_TEST_PG_DSN not set")
main (/home/user/hadavin-sdk), no DSN:   tests/test_grants_negative_roles.py
23 passed, 54 skipped, 1 xfailed in 0.27s  (skips: 54 = PG tests without DSN + step-B tests "step B is not in this tree")
main, with DSN:
37 passed, 39 skipped, 2 xfailed in 2.86s  (39 skips = step-B only)
$ ruff check tests/test_grants_negative_roles.py tests/test_grants_negative_0007.py   -> All checks passed!
$ ruff format --check (same two files)                                                -> 2 files already formatted
```
Each run passed on the first try; nothing was retried.

## Mutants (applied by hand in the WORKTREE only, DSN set, both files, `git checkout -- src` after each)
| id | change | result |
|---|---|---|
| M1 | `kill_switch` row `Grant("table", "SELECT, UPDATE", reset=...)`: runtime may UPDATE the stop flag | 3 failed (`every_write_privilege_...`, `only_the_reviewed_roles_hold_anything_on_the_stop_state`, `step_b_the_grant_map_...no_way_to_switch_the_stop_off`) and 52 PG tests ERROR: migrate() itself refuses it ("roles other than the reset role could clear a stop", migrate.py:413) |
| M2 | `audit_entries` reset right `"SELECT, INSERT, DELETE"` | 7 failed: `every_write_privilege_...`, `nobody_may_change_or_remove_an_audit_row[audit_entries]`, `delete_is_held_only_...`, `case2_the_reset_identity_holds_exactly_...`, `pg_case2_...`, `pg_case5_...`, `pg_case11_migrate_again_...` |
| M3 | cli.py: `limits reset` builds its store from `b.store.dsn_secret_name` (runtime DSN) not `reset_ref` | 3 failed: `case7_limits_reset_builds_its_store_and_audit_from_the_reset_dsn_only`, `pg_case7_...runtime_login...`, `pg_case7_...reset_dsn_works...` |
| M4 | limits.py: `write_intent` line removed from `Limits.reset` | 9 failed: `reset_writes_the_audit_intent_before_...`, `reset_leaves_the_switch_alone_...`, `case8_...`, `case7_...only`, `pg_case5`, `pg_case7` (x2), `pg_case8`, `pg_case12` |
| M5 | row `kill_switch_clears` deleted from GRANTS (migration without grant row) | 9 failed + PG errors: `case10_a_stop_state_relation_without_its_grant_row...`, `case10_the_real_migrations_and_the_grant_map_agree`, `test_migration_0007_...` and others |
| M6 | row `no_such_relation` added to GRANTS (grant row without migration) | `case10_the_real_migrations_and_the_grant_map_agree` failed, PG fixtures ERROR (migrate refuses) |
Not mutated: rows marked NOT APPLIED in tickets/B-mutant-cases.md. M1 does not reach the PG negative test
`pg_case3_...` because migrate() already refuses the map; a variant that bypasses migrate()'s own check was NOT run.

## The reviewed write list of core-b's map (one reason per privilege; full text with comments is in WRITES_AFTER_STEP_B)
runtime: runs INSERT/UPDATE (start, state moves); plans INSERT/UPDATE (store, status); gate_decisions INSERT; approval_requests
INSERT/UPDATE (ask, decide/expire); approval_decisions INSERT; dead_letters INSERT; spend_reservations INSERT/UPDATE (book, settle/expire);
spend, spend_month INSERT/UPDATE (counters); kill_switch_stops INSERT (a stop is a new row); tick_state INSERT/UPDATE; audit_entries,
audit_checkpoints INSERT (append); audit_outbox INSERT/DELETE (park, reconcile); tool_calls INSERT; redaction_maps INSERT/UPDATE.
portal: none. purge: DELETE on tool_calls, redaction_maps, spend_reservations (retention).
reset: kill_switch UPDATE (old flag off); kill_switch_clears INSERT (the reset); audit_entries INSERT (the intent).

## Findings about core-b's grants (not accepted, only recorded; line numbers on refs/inputs/cloud-core-b 576f292)
1. src/hadavin_sdk/store/migrate.py:56 `spend_reservations` is `_RW` for the runtime: UPDATE is table-wide, so the runtime login can rewrite
   `reserved_usd` or reopen a closed row (CHECKs in 0007 lines 10-17 keep the row consistent, not honest). No new power over the counters
   (it holds UPDATE on spend, :57-58) but the cap rests on the code, not on the grant.
2. migrate.py:56 purge `DELETE` on `spend_reservations` is table-wide: the purge login can delete an OPEN reservation; only the WHERE of the
   purge statement limits it. Counters stay booked, so the safe side.
3. migrate.py:61 `kill_switch` reset `UPDATE` is table-wide (also sets the old flag ON or changes `id`); both read as ON. Ticket B S4 accepts it.
4. migrate.py:62 runtime `INSERT` on `kill_switch_stops` is table-wide: `by`, `ts` and `id` are free, so the runtime login can sign a stop with any name.
5. migrate.py:65 the reset role holds `INSERT` on all of `audit_entries`: it can append any audit row, not only a reset intent (same right as the
   runtime). Named in ticket B as a known cost.
6. migrate.py:73 (old, also on main) `redaction_maps` is `_RW` while the comment at :71 says "append and purge only (no UPDATE)".
7. migrate.py:413 positive: migrate() refuses a map where another role could clear a stop (defense in depth for M1).
No test is red on core-b's tree: no guarantee of ticket B or F in the tests is violated.

## NOT RUN
PostgreSQL 17 (CI runs 17.10); Python 3.12; the full test suite of either tree; mutants marked NOT APPLIED in tickets/B-mutant-cases.md;
the M1 variant that bypasses migrate()'s own refusal. cloud/core-c has no step B: its path through the step-B tests is "skipped with reason".

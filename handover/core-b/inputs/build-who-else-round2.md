# build-who-else-round2 (lead's local Sonnet builder, 2026-11-20; summary written by the lead from the builder hand-back; claims UNVERIFIED until the fresh review and the evidence campaign)

Branch wip/lead-fix-B-who-else on hadavin-sdk, pushed. Commits: c73b6afae (round 1), c2d5ea4a7, 93fcc5790, c0d8f5ec8, and 7caa8c15c (round 2). Base 2dae86b68. Remote hash equals local hash 7caa8c15c (checked 08:27 UTC).

Round 2 closes review findings B-WE-M1, B-WE-M2, B-WE-M3, B-WE-m1.

Rule in plain words (who_else_can_clear in src/hadavin_sdk/store/migrate.py, from line 279):
- Listed (migrate refuses): any role holding UPDATE, DELETE, TRUNCATE or TRIGGER on kill_switch; INSERT or TRIGGER on kill_switch_clears; TRIGGER on kill_switch_stops. Covers table grants, column grants (UPDATE, INSERT only) and PUBLIC. Any direct or indirect member of such a role or of the reset role, with or without inheritance. Below PG16 every non-superuser role with CREATEROLE. From PG16 a membership counts if SET, INHERIT or ADMIN is true.
- M2: if the three stop tables are not all in current_schema(), or a bare name resolves to another relation (for example a temp table), the function raises ConfigError naming schema, search_path, missing tables.
- Not covered (stated in docs/stop-state-runbook.md and SECURITY.md): the schema owner (closing step: the runtime login must not own the schema or belong to its owner), superusers, managed-database admin roles (rds_superuser, azure_pg_admin, cloudsqlsuperuser; they are not rolsuper), SECURITY DEFINER functions or views (closing step: review every function in the schema), roles whose only path is membership in the owner, a superuser or a predefined role such as pg_write_all_data.

Decisions to check:
- The ADMIN-only creator of the reset role is now LISTED. The old test expectation (empty list, migrate passes) was changed to: listed, migrate raises, and after REVOKE ADMIN OPTION FOR the reset role FROM the creator it passes. Test renamed test_s2_the_creator_of_the_reset_role_with_the_admin_option_only_is_listed. To undo: drop OR m.admin_option.
- M2 requires three tables (kill_switch_stops is read by the TRIGGER check).
- Risk, untested: on managed PG15 and older a CREATEROLE admin role that does not own the tables (for example rds_superuser) is now listed and refuses migrate; the way out is PG16 or later or removing CREATEROLE.
- Equivalent mutant: grantee <> 0 removed (oid 0 matches no role row; PUBLIC has its own branch).

Tests and mutants: new tests for ADMIN, CREATEROLE (PG15 listed, PG16 not unless member), superuser never listed, dropped column, reset-role members, empty search_path, missing schema or table, temp table shadow, DELETE/TRUNCATE on the flag, TRIGGER on all three tables. A shared advisory lock (GATE) keeps parallel tests from seeing a server-wide CREATEROLE role on PG15. New mutants plus a version gate GE16/LT16 (N/A on the other server).

Claimed results (raw logs h17.log and h15.log are in the builder scratchpad, not copied): stop-state files with -n 3, three runs each: PG17.10 199 passed 1 skipped; PG15.20 197 passed 3 skipped. --hand mutants: PG17 KILLED 61, 3 N/A, 1 EQUIVALENT, no SURVIVED or FAILED; PG15 KILLED 60, 4 N/A, 1 EQUIVALENT. ruff check and format clean on 3 files. Test files run: test_stop_state_roles.py, test_stop_state_loop.py, test_stop_state_unit.py.

Not run: full suite outside those three files; PG14, PG16, managed services; CHANGELOG not edited; no EGM re-review yet (fresh egm-codebase-details review started 08:27 UTC).
Containers hvfix2-pg15 and hvfix2-pg17 removed (docker ps -a --filter name=hvfix shows none, checked 08:27 UTC).

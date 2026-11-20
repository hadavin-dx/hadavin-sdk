# H3 round 2 review 1 (reviewer, hostile)

Head 9b7610007 (f66eb784d). tests/test_money_start_check_pg.py: 43 passed on my own database. No Blocker, no Major.

## Blocker
none

## Major
none

## Minor

m1. postgres.py:282,309,319: `_WARNED_OWNER` is one flag per schema shared by the stop check and the money check, and the
   "skipped for ..." list names only the tables of the first check that ran. The stop check runs first, so a login that
   owns a money table (test_owning_one_money_table_exempts_only_that_table) gets NO warning naming the skipped money
   tables, and the "tables not found" warning (line 309) is silenced the same way once the owner warning fired (it never
   adds the schema itself, so it repeats per build otherwise). Scenario: dev login owns all tables; log says stop tables
   skipped, money check skipped silently. Fix: key the flag on (schema, check) or on (schema, table name set).

m2. postgres.py:277-281: the closure follows every pg_auth_members row, including ADMIN-only membership
   (INHERIT FALSE, SET FALSE) and a chain whose second hop has SET FALSE after a SET TRUE first hop (A -SET-> B, B has
   C with SET FALSE INHERIT FALSE: A cannot reach C). False POSITIVE only (refuses a login that cannot actually use the
   right); safe direction, and ADMIN OPTION can grant itself SET, so refusing is defensible. Fix: none needed, or one line
   in the error text that membership counts "whatever the options".

m3. postgres.py:315-329: when all money tables are absent `_scoped_tables` returns None and the function check is skipped
   too. A runtime login on a pre-0007 schema starts (a warning is logged). Safe in practice: no money tables means no money
   functions can book and a later `migrate` resets the grants; the store fails at first reserve (HD004/relation missing).
   I agree with "log, not refuse"; the one residual is a half-migrated schema where some money tables exist and others do
   not: the existing ones are still checked, so no gap. Fix: none; optionally say "run migrate" in the warning text.

m4. No check of pg_default_acl for FUTURE tables (migrate checks default privileges only for EXECUTE on functions,
   migrate.py:923). Start check is a point in time; a later table is created by migrate which resets grants. Fix: none
   (doc line "start check judges the tables present now").

m5. Tests do not name PUBLIC (a `GRANT UPDATE ON spend TO PUBLIC`): has_table_privilege(role) folds PUBLIC in, so it is
   caught, but untested. Fix: one parametrized case.

## Checked and fine
- Cycle safety: closure uses UNION (dedups), so even a hypothetical cycle terminates; PG forbids cycles anyway.
- Owner exemption: `pg_has_role(current_user, relowner, 'MEMBER')` ignores inherit/set options, is per table
  (kept list), covers a member-of-a-member-of-owner (transitive MEMBER). Superuser: rolsuper of current_user only; a
  superuser role inside the closure is caught through has_table_privilege (superuser role gives every right). rds_superuser
  (not rolsuper, no table grants) is not a false positive.
- pg_monitor / pg_read_all_data: only reads; money check counts writes only; stop check allows runtime SELECT.
  pg_write_all_data is correctly a problem.
- Column grants: has_any_column_privilege limited to SELECT/INSERT/UPDATE/REFERENCES (money: INSERT/UPDATE).
- Ownership transfer: read live from pg_class at start. Sole risk is the point-in-time nature (m4).
- BookingDayRefused(ValueError): every `except ValueError` that could see it (limits.py:94 memory path, :178 amount check
  before the store call; the store call is under `except Exception`) is unaffected; subclass behaves as ValueError
  elsewhere. agent_loop.py, tick.py, cli.py do not touch store reserve/add_spend ValueErrors.
- limits.py keys the hint on isinstance, not text. 0011 is still in UNRELEASED_MIGRATIONS (migrate.py:1072), so the in-place
  edit is allowed; a database that applied the old text raises plain ValueError (22023 text `p_day`), the hint just does
  not show, and migrate warns about the changed draft. Harmless.

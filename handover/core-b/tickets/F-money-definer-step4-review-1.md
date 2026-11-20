# F-money-definer step 4 review 1 (hostile, fresh reviewer)

Scope: migrate.py GRANTS rows, `_money_table_writers`, tests/test_money_step4_grants.py, re-pointed tests, CHANGELOG/runbook, closure of lead B1, M3, M7.
Run: tests/test_limits_reserve.py 68 passed (memory store only, it never touches the grants); tests/test_money_step4_grants.py 45 passed (real PG16). Nothing else run.

Verdict: B1 closed, M3 closed, M7 closed for table-level rights; one Major (column-level hole in M7), one Major doc contradiction, two Minors.

## Blocker
none.

## Major

### MA1. `_money_table_writers` is blind to column-level grants (M7 only half closed)
migrate.py:953-980 uses `has_table_privilege`, which is FALSE for a role holding only `GRANT UPDATE (usd) ON spend` or `GRANT INSERT (reservation_id, agent_id, day, status, settled_usd, ...) ON spend_reservations` (verified on the test server: a role with `UPDATE(b), INSERT(a)` gives `has_table_privilege` f/f, `has_column_privilege` t). `effective_problems` does check columns, but only for the 5 NAMED roles. So an UNNAMED role (the very case M7 was about) with column-level UPDATE on `spend.usd` plus column INSERT on `spend_reservations` passes `migrate`, and that pair is exactly the H1/H2 bypass (forge a settled row, lower the counter by the difference in the same tx; the 0010 trigger is only a tripwire). Also a TRIGGER-less case: column grants are invisible to the PUBLIC probe too (`aclexplode(c.relacl)` ignores `attacl`).
Fix: also test `has_any_column_privilege(r.oid, c.oid, 'INSERT')` / `'UPDATE'` per role, and `aclexplode(att.attacl)` with grantee 0 for PUBLIC (as `_CAN_CLEAR` already does for the stop tables); add a test in test_money_step4_grants.py (`GRANT UPDATE (usd) ON spend TO stranger` must refuse).

### MA2. Runbook still says the redesign is "planned" and tells the operator the guard does not stop the runtime
docs/stop-state-runbook.md:200-211 (the 0010 "TRIPWIRE ... does NOT stop a runtime login that writes its own SQL ... The real fix is a planned redesign: the runtime gets no UPDATE/INSERT ... Until then keep the runtime login separate") contradicts lines 242-246 and CHANGELOG:9-19 in the same file/release. After step 4 the three reproduced bypasses need a write right the runtime no longer has (case (3), a shared owner login, is still real and is checked by `_owner_problems`).
Fix: rewrite lines 200-211 as "since step 4 (grants flip) the runtime has no write right; the trigger is the second line; the three bypasses apply only to a login that holds a write right or is the owner".

## Minor

### Mi1. Writers check exempts members of the owner and ignores NOINHERIT paths
migrate.py:964-973: a NOINHERIT member of the owner (or of the writing role) is not flagged by `has_table_privilege` yet can `SET ROLE`; for unnamed roles only the direct holder is named. `_unnamed_money_executors` has the same documented exception, so this is consistent but should be stated in the docstring/runbook ("members of the owner are the owner").
Fix: one sentence in the docstring; optionally `pg_auth_members` walk.

### Mi2. Check only runs when a role is named
migrate.py:1232 `if any(roles)`: `--no-roles` on a database that kept an old runtime write grant passes silently. Intended (first install) but the CHANGELOG says "a role that inherits one is refused" without that qualifier.
Fix: add "(when roles are named)" to CHANGELOG:12-13.

Also (info): 0008/0010/0011 SQL header comments still say "until step 4"/"stays a tripwire"; those files are immutable once applied, so fine, but 0011:3-6 reads wrong after step 4 for a new reader.

## Findings of the lead, each tried
- B1 (runtime holds RW on the three tables): CLOSED. GRANTS (migrate.py:77-83) give runtime SELECT on spend/spend_month, "" on spend_reservations; `_apply_grants` REVOKE ALL then GRANT; `effective_problems` (also catches membership, PUBLIC, sequences, views, default ACL via effective has_*_privilege) runs in the same tx. test_migrate_with_only_the_runtime_role... asserts it from `migrate` alone (no hand-stripping). TRUNCATE/REFERENCES/TRIGGER are in `_TABLE_PRIVS`. No sequences on the money tables. Definer functions: pinned `pg_catalog, <schema>, pg_temp` (pg_temp last, so a temp `spend`/`hadavin_limits` cannot shadow; operators/functions resolve from pg_catalog first). Only counter-lowering path left in a definer function is `hadavin_settle_spend(id, 0, NULL)` on an open hold it can name = the documented residual; reserve+settle nets to zero; expire never lowers; add_spend only adds; no function takes a cap.
- M3 (purge direct DELETE): CLOSED. `purge=""`, purge mutant in tests, purge login test shows DELETE and SELECT refused and the function works.
- M7 (unnamed roles): CLOSED for table-level INSERT/UPDATE/DELETE/TRUNCATE, PUBLIC and INHERIT memberships (pg_write_all_data members are caught because `has_table_privilege` honours it); NOT closed for column-level grants (MA1).
- Runtime read path: spend_totals reads only `{spend}`/`{spend_month}` (postgres.py:655-661), no code in src reads spend_reservations as runtime (grep). Tick calls expire/purge through the functions. test_limits_reserve.py passes; step4 cycle test (reserve/settle/add/expire with EXECUTE only) passes.

<!-- full hand-back report of sub-agent a98329b0, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT CLEAN. 1 Blocker, 6 Major, 11 Minor. Mode: REVIEW, snapshot /home/user/build/snap/p3a2-r12-4d328e3 only.

Nothing was run. Every finding is by reading the code. PostgreSQL behaviour is from memory unless marked otherwise; the evidence runner should reproduce F1 to F5 and F7 before anyone relies on them.

Evidence: not yet available. /home/user/hadavin-sdk/handover/evidence/P3a-2/4d328e3/ does not exist (glob returned nothing). Every run-dependent claim is unproven: all "Fails on 8382bdd", "Killed by mutant ..." and "Pin" statements, and the two-session tests.

All line numbers are in src/hadavin_sdk/store/migrate.py unless another file is named.

## Findings

### F1. Blocker: a deferred constraint trigger runs file code at COMMIT, after every check
- **Where:** `_check_read_back` 1427-1432 (a new trigger is refused only when its state is D or R); `migrate` 1662-1672 (last check, then commit); `_SAFE_CREATE` 173-178.
- **Class:** code controlled by a file runs after the last check (time of check, time of use).
- **SQL** (one file; needs only a plain migration role that owns its tables):
```sql
CREATE OR REPLACE FUNCTION late() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN EXECUTE 'GRANT ALL ON audit_entries TO PUBLIC'; RETURN NULL; END $f$;
CREATE OR REPLACE FUNCTION plant() RETURNS void LANGUAGE plpgsql AS $f$
BEGIN EXECUTE 'CRE' || 'ATE CONSTRAINT TRIGGER late_t AFTER INSERT ON schema_migrations '
  || 'DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION late()'; END $f$;
SELECT plant();
```
- **Why the text rules pass it:** `refused_statements` reads the emptied view, so the bodies are `$$`. `_scan` reads the bodies, but the split word `'CRE' || 'ATE'` hides the `CREATE`. The package's own test at tests/test_migration_postgres.py:3030 uses the same spelling.
- **Why the catalog checks pass it:** the read-back sees `late_t` as a new trigger in state `O`. Both functions are new, not SECURITY DEFINER, and only lose the PUBLIC right.
- **What happens:** `migrate` itself inserts the ledger row at 1622, which queues the trigger. It fires at COMMIT, after `_refuse_unlisted_grantees`. The GRANT (or `ALTER FUNCTION ... SECURITY DEFINER`, or an owner change) is committed and the run returns "applied".
- **Fact (memory):** an `INITIALLY DEFERRED` constraint trigger fires at commit inside the committing transaction.
- **Rule broken:** docstring 38-41 claims "by any statement, also by dynamic SQL"; honest-tamper-evidence-claims.
- **Smallest fix at the choke point:** in `migrate`, straight before `changed = _changed_since(...)` at 1662, execute `SET CONSTRAINTS ALL IMMEDIATE`, then run one last `_check_read_back` and `_recheck_roles`. Run no file-reachable statement after the final comparison. Also read `tgdeferrable`, `tginitdeferred` and `tgconstraint` in `_READBACK_TRIGGERS_SQL` and refuse a new deferrable trigger.
- **Siblings:** F2; any Python step other packages add after the loop (P2a-1).

### F2. Major: a plain trigger on the ledger table runs after the last file's read-back
- **Where:** 1613-1622. The order is file, read-back, recheck, then `INSERT INTO schema_migrations`.
- **SQL** (no obfuscation; passes `_SAFE_CREATE` and `refused_statements`):
```sql
CREATE OR REPLACE FUNCTION after_ledger() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN ALTER TABLE audit_entries DISABLE TRIGGER USER; RETURN NULL; END $f$;
CREATE TRIGGER after_ledger AFTER INSERT ON schema_migrations
  FOR EACH STATEMENT EXECUTE FUNCTION after_ledger();
```
- **What happens:** for the last pending file nothing reads triggers, memberships, saved settings or session values again. The final check reads only rights, owners and SECURITY DEFINER. The append-only audit triggers are committed disabled. The same route can replace a trigger function body or grant a role membership.
- **Middle files:** the change is found one file late and blamed on the wrong file.
- **Fix:** move the ledger INSERT before the read-back, or refuse any user trigger on `schema_migrations`; plus the final read-back of F1.

### F3. Major: an object made a member of an extension escapes every catalog check
- **Where:** `_NOT_SYSTEM_PARTS` 833-837 excludes `pg_depend.deptype = 'e'`. It is used in the state queries (878-900) and in `_ACL_RELATION_SQL`, `_ACL_FUNCTION_SQL` and `_ACL_OWNER_SQL` (929, 956, 966, 972), so the SECURITY DEFINER rule (3) is excluded too. `_BLIND` (migration_numbers.py:665-670) has no `alter extension`.
- **SQL when the migration role already owns an extension** (plain statements, no text rule fires):
```sql
CREATE OR REPLACE FUNCTION door(q text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
  AS $f$ BEGIN EXECUTE q; END $f$;
ALTER EXTENSION citext ADD FUNCTION door(text);
```
- **What happens:** `door` is invisible before and after, so it is not "changed" and not refused. PUBLIC keeps EXECUTE, so the runtime role can run any SQL as the migration role.
- **Without an existing extension:** a migration role with CREATE on the database (for example the database owner, which line 611 allows) can first run `EXECUTE 'CRE'||'ATE EXTENSION citext'` in a function body.
- **Facts (memory):** trusted extensions can be installed by a role with CREATE on the database since PostgreSQL 13; `ALTER EXTENSION ... ADD` needs ownership of the extension and of the object.
- **Fix:** exclude an extension member only when its owner is not in `@MINE@`; or add "is an extension member" as a state field and refuse a change. Add `alter{_W}extension` to `_BLIND`.
- **Siblings:** `_FOREIGN_OWNED_SQL` 674-683 has the same exclusion.

### F4. Major: rights on kinds the catalog check never reads are guarded only by a text rule that dynamic SQL bypasses
- **Where:** `_GRANT_TARGET` (migration_numbers.py:680-684) is the only control for database, large object, foreign server, foreign-data wrapper, type, domain, language and tablespace. There is no state query for them (only 878-908 exist). CHANGELOG line 18 says so.
- **SQL (a), no precondition:**
```sql
CREATE OR REPLACE FUNCTION g() RETURNS void LANGUAGE plpgsql AS $f$
DECLARE o oid := lo_create(0);
BEGIN EXECUTE format('GRANT SELECT, UPDATE ON LARGE OBJECT %s TO PUBLIC', o); END $f$;
SELECT g();
```
- **SQL (b), migration role owns the database** (same shape): `EXECUTE format('GRANT ALL ON DATABASE %I TO PUBLIC', current_database())`. Every role, the named ones included, can then create schemas it owns.
- **Rule broken:** D-009 "no right on anything outside the grant map"; fix-dont-defer (a stated limit that is fixable).
- **Fix:** add state rows (owner and scoped ACL) for `pg_database` (current database), `pg_largeobject_metadata`, `pg_foreign_server`, `pg_foreign_data_wrapper`, `pg_type` and `pg_language` to `_objects` and `_changed_since`, and judge them in `_refuse_unlisted_grantees`. Add `has_database_privilege(role, current_database(), 'CREATE')` to `effective_problems`.
- **Sibling:** owner changes of the same kinds ("for no other kind of object", docstring 46-48).

### F5. Major: a named role that is a member of a powerful role is accepted
- **Where:** `effective_problems` 303-312 reads only the role's own five flags. `_BORROWED_ROLES_SQL` 609-615 asks only about `current_user` and `session_user`.
- **SQL (an administrator, before the run):**
  - `GRANT pg_execute_server_program TO runtime_role;`
  - `GRANT pg_read_server_files TO portal_role;`
  - `CREATE ROLE boss SUPERUSER; GRANT boss TO runtime_role WITH INHERIT FALSE;`
- **What happens:** `migrate(runtime_role=...)` passes. `has_table_privilege` does not show any of these: no table grant is involved, and non-inherited rights are not counted.
- **In-run changes** are caught by the membership read-back; an existing membership is not.
- **Rule broken:** least-privilege-hard-rule item 2; the docstring at 296-301 claims "however it got it".
- **Fix:** run the `_BORROWED_ROLES_SQL` predicate for each named role inside `effective_problems` (flagged roles and `pg_*`, by `pg_has_role(..., 'MEMBER')`). Also refuse a named role that is a member of the migration role or of any role in `@MINE@`.

### F6. Major: "no right outside the grant map" is enforced only for objects that changed in this run
- **Where:** `_ACL_RELATION_SQL` 926-927 and `_ACL_FUNCTION_SQL` 950-955 read an object outside the managed names only when it is in `changed_*`. `effective_problems` 313-321 reads only `current_schema()`.
- **SQL (before the run, objects owned by the migration role, so inside the D-009 scope):**
  - `GRANT SELECT, INSERT ON other.t TO runtime_role;`
  - `GRANT EXECUTE ON FUNCTION run_schema.f() TO runtime_role;` on an untouched function
  - `GRANT CREATE ON SCHEMA other TO runtime_role;`
- **What happens:** all three are accepted on every run.
- **Inconsistency:** default rights and SECURITY DEFINER are judged as state; these are judged as a change only.
- **A test pins the gap:** `test_a_function_of_another_application_owned_by_the_migration_role_is_left_alone` (tests/test_migration_postgres.py, about 3805).
- **Texts that claim more than is checked:**
  - refusal message 1241-1244: "a named role gets ... nothing on any other table, view, sequence or function";
  - CHANGELOG.md:17: "gets no right at all ... in any schema, and no right on a function";
  - CHANGELOG.md:15 contradicts it: "Not looked at by this check: rights in other schemas, EXECUTE on functions".
- **Fix:** one state query per named role: `aclexplode` over `pg_class`, `pg_attribute`, `pg_proc` and `pg_namespace` where the grantee is the role and the owner or grantor is in `@MINE@`; refuse everything that is not the grant map or schema USAGE. If the lead means D-009 as change-only, the three texts must say so.

### F7. Major: the scope uses `current_user` only; the role checks use `current_user` and `session_user`
- **Where:** `@ME@` and `@MINE@` 838-839; `_ACL_DEFAULT_SQL` 1004.
- **Setup:** login L connects with `options=-c role=M`, a common pattern. L holds no flags and is a member of M.
- **SQL in a file:**
```sql
CREATE OR REPLACE FUNCTION h() RETURNS void LANGUAGE plpgsql AS $f$
BEGIN PERFORM set_config('role','none',true);
  EXECUTE 'GRANT ALL ON other.l_table TO PUBLIC';
  PERFORM set_config('role','m',true); END $f$;
SELECT h();
```
- **What happens:** after the file `current_user` is M again, so the read-back passes. `other.l_table` is owned by L and the grantor is L, which is not in `@MINE@`. The object is out of scope before and after and is never compared. The same holds for default rights L sets for itself and for groups only L belongs to.
- **Fix:** define `@MINE@` as the union for `current_user` and `session_user`, and add a mutant for it.

### Minor
- **m1. Function fields not compared** (867-886): `proname`, `pronamespace`, `provolatile`, `proleakproof`, `proparallel`, `proisstrict`, `proargdefaults`, `prokind`, `prosupport`, extension membership. An existing SECURITY DEFINER function can be silenced with `ALTER FUNCTION f() SET SCHEMA other`: it is not "changed" and no longer matches rule (3). The trigger read-back (471-477) also lacks `prolang` and `probin`.
- **m2. Column REFERENCES is not asked** in `effective_problems` 359. CHANGELOG.md:15 states it as a limit; it is a one-word fix.
- **m3. Relation state has no row-security or view fields** (888-900): `relrowsecurity`, `relforcerowsecurity`, policies, the view definition, `reloptions` (`security_invoker`). `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` passes. A view runs with its owner's rights, like SECURITY DEFINER. I found no row security or views in the grant map today.
- **m4. The lowest server version is stated but not enforced.** PostgreSQL 16 is named at migration_numbers.py:35 and CHANGELOG item 11. `_SERVER_VERSION_SQL` is used only for MAINTAIN (286-292). Add a plain refusal below 160000.
- **m5. PostgreSQL 18 default rights for large objects** (kind `L`, from memory): `_DEFAULT_WORDS.get(kind, 'TABLES')` at 1234 would print a wrong undo statement.
- **m6. `REVIEWED_DEFINER_FUNCTIONS` matches by name only** (1194): no schema, no argument list. Harmless while empty.
- **m7. Messages.**
  - The untouched SECURITY DEFINER refusal (1196-1202) does not say what to do (drop it, change its owner or remove the flag); the three steps say "revokes the right".
  - `effective_problems` lines such as "{role}: can SELECT {name}" and "owns {name}" (324, 339, 353, 365) give no kind and no schema per item.
- **m8. False refusal:** when a group owns a managed relation and granted a right to the migration role, 1160 reports the migration role as a stranger.
- **m9. Round-11 minor 7 is still open:** hand-recipe and between-run changes are never compared; only stated at 1087.
- **m10. Test wording:**
  - tests/test_migration_wiring.py:192 and 208 still say and build an md5 for a query that now returns `prosrc`.
  - `test_every_part_of_a_function_...` runs three of the eight fields on a server; `probin`, `prolang` and owner are covered only by the unit comparison.
- **m11. Docstring 38-41** ("by any statement") and 1081-1083 claim more than F1, F3 and F4 allow.

## Round-11 checklist (verified by reading only)
| Item | Status | Where |
|---|---|---|
| M1 named role rights outside the map | Partly: fixed for changes made in the run and for default rights | 1160-1165, 1208-1212, 1226-1235; open: F6 |
| M2 unmanaged SECURITY DEFINER function | Fixed, with the extension hole | 955, 1194-1203; open: F3 |
| M3 function state hash | Fixed: separate fields, `pg_get_function_sqlbody`, `probin`, `prolang`, no md5 | 867-886; rest: m1 |
| M4 another session stops the run | Fixed by reading | 862, 878-907, 1062-1068, 1247-1249; new hole: F7 |
| M5 fail-before proof | Not proven: docstrings now mark pins, no evidence exists | n/a |
| Minor 1 `rename` switch | Fixed | migration_numbers.py:689-712 |
| Minor 2 prepared-transaction message | Fixed | 1301-1312 |
| Minor 3 ids from three catalogs | Fixed | 1050-1059 |
| Minor 4 dead CREATE allowance | Fixed | 1224 |
| Minor 5 `pg_database_owner` | Fixed | 986-992 |
| Minor 6 md5 | Fixed in src; stale in a test helper | m10 |
| Minor 7 hand-recipe changes | Not fixed | m9 |
| Minor 8 wording and test hygiene | Partly: five flags, PO2 and the always-true assert are fixed | diff of tests/test_migration_postgres.py |

## Route table (point 1)
| Route | Status | Where / note |
|---|---|---|
| Tables, partitions, views, materialized views, foreign tables, sequences in the run schema, named role | Enforced, effective rights | 317-354 |
| Columns | Enforced for SELECT, INSERT, UPDATE; REFERENCES not | 355-365; m2 |
| Same kinds in other schemas | Enforced only when changed in the run | 926-927; F6 |
| Access through a parent table (inheritance, attached partition) | Not enforced | no check exists |
| Functions, procedures, aggregates | A change is enforced; an existing right on an untouched function is not | 950-955; F6; hidden by F3 |
| Types and domains | Not enforced in the catalog; text rule only | F4 |
| Schemas | Run schema enforced; others only when changed | 315, 986-992, 1217-1225; F6 |
| Database | Not enforced | F4 |
| Large objects, languages, foreign servers and wrappers, tablespaces | Not enforced | F4 |
| Parameters (PostgreSQL 15+) | Enforced for the migration role only; not for named roles | 618-627 |
| Default rights, global and per schema, for the migration role and its memberships | Enforced as state | 998-1006, 1226-1235 |
| Default rights set by the login when it differs from the current user | Not enforced | F7 |
| Role membership of named roles, with ADMIN, INHERIT, SET options | A change in the run is enforced; an existing membership is not | 457-466; F5 |
| PUBLIC | Enforced on managed and changed objects and through `has_*_privilege`; kept on untouched functions (documented) | 1160, 1209 |
| A named role owning an object | Relations in the run schema only | 323; not functions, schemas elsewhere or other kinds |
| Row-level security, policies | Not enforced | m3 |
| BYPASSRLS, SUPERUSER, CREATEROLE, CREATEDB, REPLICATION flags | Enforced for the role's own flags, migration and named roles | 303-312, 432-435 |
| Predefined roles (`pg_*`) | Enforced for the migration role; named roles only where `has_table_privilege` shows it in the run schema | 609-615; F5 |
| Code that runs after the checks | Not enforced | F1, F2 |

## Answers to points 2 to 8
- **(2) Scoping.**
  - An owner change to a third role cannot leave the scope: a non-superuser must be a member of the new owner, so the owner is in `@MINE@`, and 961-978 reports the handover.
  - A grant by a third role on an object the migration role owns is read, because the owner clause includes every ACL item.
  - SET ROLE inside a file: objects made under a group are new, in scope and refused as "handed to".
  - Holes: F3 (extension), F7 (session user), F6 (unchanged objects).
- **(3) SECURITY DEFINER and the field comparison.** Compared: owner, SECURITY DEFINER flag, scoped ACL, `prosrc`, SQL-standard body, `probin`, `prolang`, `proconfig` (which holds the `search_path` setting). Missing: see m1. Return type and argument types cannot change without a new id, which is seen. Unseen changes: argument defaults, volatility, strictness, parallel, leakproof (superuser only), name, schema, extension membership.
- **(4) Owner text rule.** It is a tripwire. Comments and quoting do not bypass it (lexer, emptied view). Dynamic SQL in a function body bypasses it. The catalog backs it for relations, functions and schemas only; nothing backs it for types, domains, large objects, servers and so on (F4). `REASSIGN OWNED` by dynamic SQL is caught for the same three kinds only. A function made now and run later: F1 and F2.
- **(5) Time of check.** F1 and F2. Another session can still change an in-scope object between the second `_objects` read (1662) and COMMIT without being seen; the advisory lock is cooperative only. This is not fixable from the client and is not stated in the texts. The prepared-transaction holder is handled at 1301-1312.
- **(6) Messages.** F6 overclaims, m7, m11.
- **(7) Tests that changed meaning.** By reading, none is weakened; the renamed tests tighten. Exception: the pin named in F6 holds a D-009 gap in place. Mutant removals (RA3, GO7, PO1, PDO1, RO2) match the builder notes; not run.
- **(8) Single dependency and versions.** PostgreSQL sits behind the store kind and `psycopg` stays in `store.*`; no new dependency. PostgreSQL 16 is stated as the lowest version but not enforced (m4). Version 17 (MAINTAIN, `pg_maintain`) is handled only through a faked version in tests and has not been run. Versions 14 and 15 are untested. Version 18: m5.

## Not checked
- Any run, any probe, any mutant.
- `cli.py`, most of `migration_numbers.py` (the lexer body), `tests/migrate_mutants.py` content, `tests/test_migration_compare.py` body, DIFF-main-to-head.patch as a whole, TICKET-P3a.md beyond line 51, CHANGELOG beyond line 60 (the repair runbook).
- The migration SQL files: they are not in the snapshot, so the "no row security, no views today" statement rests on a grep of src and tests only.
- PostgreSQL 14, 15, 17 and 18 behaviour.

<!-- full hand-back report of sub-agent a20099a3, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

NOT CLEAN. Blocker 0, Major 2, Minor 10. Nothing was run. `/home/user/hadavin-sdk/handover/evidence/P3a-2/4d328e3/RESULTS.md` was absent at the end of the review, so every run-dependent claim is UNPROVEN: "Fails on 8382bdd", "Pin", mutant kills, all server behaviour.

Snapshot root: `/home/user/build/snap/p3a2-r12-4d328e3/`. MIG = `src/hadavin_sdk/store/migrate.py`, MN = `src/hadavin_sdk/store/migration_numbers.py`, TPG = `tests/test_migration_postgres.py`, TCMP = `tests/test_migration_compare.py`, MUT = `tests/migrate_mutants.py`. PostgreSQL facts marked (memory) were not probed.

## Major

### F1. "A named role gets no right outside the grant map" holds only for objects that are managed, changed in this run, or in the run schema
- **Where:** MIG:921-941 (`_ACL_RELATION_SQL`), MIG:946-958 (`_ACL_FUNCTION_SQL`), MIG:1062-1068 (`_changed_ids`), MIG:317-321 (`effective_problems`, run schema only).
- **Written rule broken:**
  - CHANGELOG.md line 17: "a role named in the run (runtime, portal, purge) gets no right at all on a table, view, sequence or column that is not in the grant map, in any schema, and no right on a function ... A setup that passed before is refused now"; and at the end of the line "on a function they get no right".
  - The refusal text at MIG:1242-1243 says the same.
- **Input A (standing right, other schema):** before the run an administrator runs `GRANT SELECT ON other_schema.t TO <runtime_role>`; then `migrate(dsn, runtime_role=...)`.
  - Expected by the CHANGELOG: refused.
  - Actual by reading: `other_schema.t` is not in `managed_rel`, its state is unchanged so it is not in `changed_rel`, and `effective_problems` reads only the run schema. The run passes.
- **Input B (standing right on a function):** `GRANT EXECUTE ON FUNCTION <run_schema>.f() TO <runtime_role>` on a plain function that no file names or touches. No query selects it (MIG:954-955 lists only managed, changed, or SECURITY DEFINER functions). The run passes.
- **Input C (move):** a pending file holds `ALTER TABLE audit_entries SET SCHEMA other; CREATE TABLE audit_entries (...);`, and the migration role has CREATE on `other`.
  - The state key is the oid, and the state tuple holds neither name nor namespace (MIG:889-900), so the moved table is "unchanged".
  - It keeps the runtime role's SELECT/INSERT outside the grant map in another schema, unreported.
  - `_scan` accepts a second `CREATE TABLE` of a GRANTS name (MIG:232-234, no duplicate check).
  - The role gains nothing on those rows beyond what it had; the written rule is still false for it.
- **Smallest fix at the choke point:** one extra query in `_refuse_unlisted_grantees`, over `pg_class`/`pg_attribute`/`pg_proc` with `@NOT_SYSTEM_*@`, listing every ACL item whose grantee is one of `named` and whose object is not `(schema, managed_rel)`. Feed its rows through the existing loops.
- **Alternative:** reword CHANGELOG line 17, MIG:55 and MIG:1242-1243 to "on an object that a file of this run made or changed, and on the relations of the schema of the run".
- **Siblings:** add name and namespace to the three state tuples so a rename or move is a change; give `_scan` a duplicate-CREATE check.

### F2. The extension filter also covers the package's own objects, so making one an extension member hides it from every rights query (memory, needs a probe)
- **Where:** MIG:833-837 (`@NOT_SYSTEM_C@`/`@NOT_SYSTEM_P@`), applied to the managed branches at MIG:928-929, 938-939, 956, 966, 972, to all state queries at MIG:885 and 899, and to MIG:674-675 and 682-683.
- **Input:** the migration role owns the database, or holds CREATE on it. That is ACL-level and not one of the five flags; MIG:630-656 does not look at it. A pending file holds a function body, called by `SELECT f();`, that runs:
  - `EXECUTE 'CRE'||'ATE EXTENSION citext';` (the split spelling TPG itself uses to pass `_ANY_CREATE`),
  - `EXECUTE 'ALTER EXTENSION citext ADD TABLE audit_entries';`
  - `EXECUTE 'GRANT ALL ON audit_entries TO PUBLIC';`
- **PostgreSQL facts (memory):** a trusted extension can be created by a role with CREATE on the database, which then owns the extension; `ALTER EXTENSION ... ADD` needs ownership of the extension and of the added object.
- **Expected:** "PUBLIC has ... on the table <schema>.audit_entries" is refused (CHANGELOG line 17 gives `GRANT SELECT ON audit_entries TO PUBLIC` as an example).
- **Actual by reading:** `audit_entries` has a `pg_depend` row with deptype `e`, so it drops out of the before/after state and out of the `_ACL_RELATION_SQL`/`_ACL_OWNER_SQL` managed branches. With no role arguments nothing refuses. With role arguments `effective_problems` would still catch it. The same route hides a SECURITY DEFINER function.
- **Smallest fix:**
  - Do not apply the extension filter to the `(n.nspname = %(schema)s AND ... = ANY(%(managed_*)s))` branches or to the run-schema SECURITY DEFINER branch.
  - Add "is an extension member" as a state field, so an object that becomes a member during the run counts as changed and is refused.
- **Sibling:** `_FOREIGN_OWNED_SQL` MIG:674-675 and 682-683.

## Minor

### F3. Owner-text rule: `ONLY` is accepted as the object name
- **Where:** MN:699-703, MN:707-712.
- **Input:** `ALTER TABLE ONLY rename OWNER TO r`; also `ALTER TABLE IF EXISTS ONLY rename OWNER TO r` and `ALTER FOREIGN TABLE ONLY rename OWNER TO r`.
- **By reading:** `(?:only{_W})?` is skipped, `_NAME_PART` takes `only`, then `rename`, `owner to`. `_RENAME_OWNER` matches and ends where the single `_OWNER_TO` match ends, so `_hands_over` returns False and the statement passes.
- **Server (memory):** `rename` is an unreserved keyword, so this changes the owner of a table called `rename`.
- **Effect:** the read-back still refuses it for a relation (MIG:961-966), so there is no end-to-end bypass.
- **False statements:** CHANGELOG line 18 "a table, a type or a column that is called `rename` does not make an owner change pass"; the comment at MN:694-696; the docstring at `tests/test_migration_rules.py:437-439`.
- **Tests:** `OWNER_FORMS` has no such case; mutant OT3's killers do not cover it.
- **Fix:** put `(?!(?:only|if){_NAME_END})` in front of `_NAME_PART`; add the three inputs to `OWNER_FORMS`.
- **Other checks of the rule, all sound by reading:**
  - Comments become one space and quoted names become `""` before the rule runs.
  - Case-insensitive; `_W` covers newlines.
  - Statements are split at `;`.
  - `RENAME owner TO x, OWNER TO r` is refused (the second match has a different end).
  - Dollar bodies are emptied, so the rule only reads the start of a statement (documented).
  - No nested quantifier; I found no catastrophic backtracking in `_RENAME_OWNER`, `_OWNER_TO`, `_GRANT_TARGET` or `_ROLE_MEMBERSHIP` (each is matched from the statement start).

### F4. Two false "cannot" statements
- **Types and domains.** CHANGELOG line 18 "a file cannot create a type or a domain, the text scan refuses `CREATE TYPE` and `CREATE DOMAIN`", repeated at MIG:747-748.
  - A function body with `EXECUTE 'CRE'||'ATE TYPE ...'` creates one (same trick as TPG:3033).
  - A later dynamic `ALTER TYPE ... OWNER TO` is then not read back, by the code's own statement.
  - Fix: say "by a statement the scan can read".
- **Foreign owner.** CHANGELOG line 17 and MIG:1084-1086 "an object that already had a foreign owner before the files is not refused here, `_refuse_foreign_owned` looked at it first".
  - `_refuse_foreign_owned` reads only managed names in the run schema (MIG:669-684).
  - For a changed unmanaged object, or one in another schema, nothing looked.

### F5. Prepared-transaction branch (MIG:1265-1271, 1301-1312)
- **(a) The holder is not identified.** The message lists the 5 oldest prepared transactions of the database, not the one holding the lock, then says "finishes the one that holds the lock". With more than 5, or with several, the administrator is not told which; a wrong `ROLLBACK PREPARED` loses another system's two-phase work.
  - Fix (memory): join `pg_locks.virtualtransaction = '-1/' || pg_prepared_xacts.transaction::text`.
  - `_shown(listed)` can never print "and N more" because of `LIMIT 5`.
- **(b) Unreadable view.** If `pg_prepared_xacts` cannot be read, the error is raised inside the `except LockNotAvailable` handler. It is not a `ConfigError` and is not caught at MIG:1673, so the user gets a raw driver error instead of the lock message. Nothing is changed (fail closed).
- **(c) What each branch of TPG:4497-4530 proves.**
  - `max_prepared_transactions = 0` (the server default): it asserts only that the server refuses `PREPARE TRANSACTION`, then returns. `migrate` is never called and the test reports as passed, not skipped.
  - Above 0: it proves the real message, the name in it, and a clean run after `ROLLBACK PREPARED`.
  - On a default server `_LOCK_PREPARED_SQL` and `_PREPARED_SQL` are never executed against a server. Their only proof is TCMP:444-465 with made-up rows.
  - The evidence must state the server's `max_prepared_transactions`; mutant LW8's TPG killer is vacuous at 0.
- **(d) Race.** The holder releasing between the timeout and the query gives "a session this login cannot see holds it"; harmless.

### F6. Database names printed without escaping
- **MIG:316, 324, 339, 353, 365** (`effective_problems`): `{schema}`, `{name}`, `{col}` go raw into the message that MIG:1633-1660 raises. A relation or column name with a newline or ESC, made by any role with CREATE in the schema, reaches the log. The body is older than this branch; round 12 touched the function and its callers.
- **MIG:1314:** `_seen(row[1])` prints `usename` raw (branch code). `application_name` is cleaned by the server (memory).
- **Fix:** `_label(...)` at these places, the shared helper the round-12 loops already use.
- **Length:** the `; `.join at MIG:1454, 1458 and 1463 is uncapped; nothing is hidden from the decision.

### F7. Rules with no mutant and no server test
- **"or gave a right on it" (the grantor half of the scope).** No mutant on:
  - the `EXISTS (... a.grantor IN @MINE@)` clauses, MIG:879, 890-891, 903;
  - the row filters `(owner IN @MINE@ OR a.grantor IN @MINE@)`, MIG:882, 894, 897, 906, 927, 937, 951, 991.
  - SO1 and SO3 replace the whole expression by `true`; SO2 replaces only the owner half.
  - No server test has the migration role grant on an object that another role owns. A mutant that drops the grantor clause survives by reading.
- **`p.prolang` and `p.probin` (MIG:883).** FB1/FB2/FB3 cover prosrc, sqlbody and proconfig only. TCMP:66-76 proves the Python comparison, not the SQL column.
- **`l.pid IS NULL` (MIG:1266)** and the column half of `is_managed` (MIG:933): IM1 plants only the table half.
- **Sample check of `old` uniqueness.** `problems_with_the_list()` (MUT:2997-3016) machine-checks "exactly once" and that the killer function exists; it strips the `[param]` id, so ids are not checked. By my own reading of the head source these 63 are unique:
  - OA4, OA5, OA6, MC1, MC2, SD4, SD5, SD6, SD7, SD8, SD9, RN6, SC9, SC10, SC12, SC13, SC14
  - OW3, OW4, OW5, OW6, OW7, OW8, OW9, GO4, LW7, LW8
  - RA1, RA1b, RA2, RA4, FB1, FB2, FB3, RO1, RO3, RO4, RO5
  - DP4, DP5, DP6, DP7, DP8, DP9, OT1, OT2, OT3, OT4
  - SO1, SO2, SO3, CS1, CS2, CS4, CS5, KC1, KC2, KC3, PDO2, IM1, RK2, SH1
  - the "changed = _changed_since" mutant at MUT ~1788.
- **Param ids** I checked against the parametrisations all exist: `functions-4`, `relations-2`, `schemas-2`, `sequence-sequence`, `view-view`, the `_DEFAULT_OK`/`_DEFAULT_REFUSED` keys, the OWNER_FORMS strings.
- **Removed mutants.** RA3 is covered by SD5, GO7 by GO4, PO1 by SD6-SD9, PDO1 by PDO2, RO2 by RO3/RO5. No rule is left bare by the removals.

### F8. PostgreSQL 13 and earlier now crash every run
- **Where:** MIG:883 calls `pg_get_function_sqlbody`, which exists from 14 (memory; BUILDER note m says the same).
- **Effect:** `_objects(db)` at MIG:1607 raises `UndefinedFunction`, a raw error, on every run on 13.
- **Not written down:** CHANGELOG lines 15 and 17 speak of "PostgreSQL 14 and earlier" as a running case. No minimum is in the CHANGELOG or `pyproject.toml`.
- **Fix:** state the minimum, or refuse with a `ConfigError` from `server_version_num` (already read at MIG:286).

### F9. `REVIEWED_DEFINER_FUNCTIONS` is matched by bare name
- **Where:** MIG:1194 uses `name not in REVIEWED_DEFINER_FUNCTIONS`: no schema, no argument list.
- **Effect:** a listed name would also excuse a changed SECURITY DEFINER function of that name in any other schema, or an overload. Latent, because the set is empty.
- **Fix:** key by `(schema of the run, name, identity arguments)`.

### F10. Wording against the code
- **MIG:56** "any default right for a role other than the migration role itself" and **MIG:1130** omit exemptions the code has: the role the default is set for, and the built-in PUBLIC entry (MIG:1005, 1227).
- **MIG:1234** `_DEFAULT_WORDS.get(kind, 'TABLES')` prints a wrong undo statement for a default-ACL kind not in the map (PostgreSQL 18 large objects, kind `L`, memory).
- **MIG:455** says "Names, not OIDs", but the JSON at MIG:464 keeps `grantor` as an oid.
- **False refusal:** on a relation or function whose kept owner is a group role, an explicit right for the migration role itself is reported as a stranger's (MIG:923, 949 exempt only the owner; the schema query at MIG:988 exempts `@ME@`). Fails closed.

### F11. Test hygiene
- **Roles created before the `try`:**
  - TPG `test_what_another_session_commits...`: `_create_roles(stranger)`, then `_admin(CREATE TABLE)`.
  - `test_with_the_printed_role_an_owner_handed_over...`: `_create_roles(owner)`, then `_printed_role_in`.
  - `test_with_the_printed_role_the_schema_and_default_right_checks_hold`: `_create_roles(group)`, then `_printed_role_in`.
  - A failure in the second call leaks the role, unless the sweep fixture catches the prefix (not read).
- **No weakened assertion found in the diff.** The three reversed tests (`..._may_only_read...`, `..._pseudo_role_may_have_rights...`, the `named_select`/`member_role_select` cases) are reversed on purpose and say so. The always-true `and schema` assert is fixed (TPG diff hunk at 3953).
- **Made-up credential** is built from parts (`"made-up-" + uuid`).
- **`_problems` (TCMP:160-174)** asserts inside `except`, then returns the list. It is not vacuous: every caller compares the list.

### F12. Reuse
- **MIG:1101-1106** `_routine_name` hand-builds quoted identifiers, while `sql.Identifier(schema, name)` is already used at MIG:784. It can be `sql.SQL("{}({})").format(sql.Identifier(schema, name), sql.SQL(args))`.
- **Three caps of 20:** `_PROBLEMS_SHOWN`, `_FOREIGN_OWNED_SHOWN` (MIG) and `MAX_PROBLEMS_SHOWN` (MN). MIG:793-802 still hand-rolls "and N more" next to `_shown`.

## Checked and sound by reading

- **Injection.**
  - `_sql` (MIG:845-848) replaces fixed markers with fixed text. `@ME@` is `(SELECT oid FROM pg_roles WHERE rolname = current_user)`: no role name is put into SQL text, so a quote in a role name cannot reach a query.
  - Named roles are held to `[a-z_][a-z0-9_]{0,62}` (MIG:164, 1563-1565) and passed as parameters or `sql.Identifier`.
  - Python-formatted SQL exists in two places only:
    - MIG:1289, `int(wait_seconds) * 1000`, range-checked;
    - MIG:1254, `sql.SQL(ident)`: schema and name are quoted by doubling, and `args` is the raw output of `pg_get_function_identity_arguments`. This is safe only because the server quotes type and argument names there (memory).
  - Edge: an ordered-set or zero-argument aggregate gives a `ROUTINE` text the server rejects. That is a raw error and a rollback (fail closed).
- **NULL ACL.**
  - Function: handled by `p.proacl IS NULL` plus `LEFT JOIN LATERAL` (MIG:947, 953) and the REVOKE.
  - Relation and schema: NULL means owner only, so "no rows" is correct.
  - State: `coalesce(..., '')` makes NULL and empty equal. No security-relevant transition is lost.
- **`pg_default_acl`:** `defaclnamespace = 0` is handled by the `LEFT JOIN` and `where is None` (MIG:1002, 1227-1229).
- **`pg_auth_members`** is read through `to_jsonb`, so the PostgreSQL 16 columns are covered.
- **relkind:** `r,p,v,m,S,f` everywhere; `c`, `t`, `I` and `i` carry no relation ACL.
- **`has_*_privilege`** (membership with inherit, and PUBLIC) is used for the named roles; ACL reading for everything else. A named role that is a NOINHERIT member of a group with rights is not seen by `has_*` (older code, not this round).
- **oid.** One dict per catalog (MIG:1026-1046). DROP + CREATE gives a new oid, hence "changed". A dropped object is not listed, which is correct for rights. No oid reuse inside one transaction (memory).
- **"and N more".** Every decision is taken on the full list before `_shown` (MIG:1236-1239, 773, 1631-1661).
- **`except` clauses:** none turns a failed catalog read into "nothing found". `fetchone()` fallbacks at MIG:1301 and 1666 fail closed; MIG:292 would only drop MAINTAIN on an impossible empty row.

## Round-11 checklist

| Item | Status | Where verified |
|---|---|---|
| M1 | Partly | Changed/managed objects and default rights: MIG:1160-1165, 1208-1212, 1226-1235. Standing rights are not read (F1). |
| M2 | Fixed by reading | MIG:955, 1194-1203; run schema only, as asked. |
| M3 | Fixed by reading | MIG:878-886, no md5 left in the file. prolang/probin unpinned (F7); PostgreSQL 14 floor (F8). |
| M4 | Fixed by reading | MIG:862, 1062-1068 and the scope SQL; two-session test TPG `test_what_another_session_commits...`; message MIG:1247-1249. Grantor half untested (F7). |
| M5 | Not provable | No RESULTS.md. Docstrings now mark "Pin" / "Fails on 8382bdd", but these are claims. |
| Minor 1 | Partly | F3; the types over-claim is replaced by the new false sentence in F4. |
| Minor 2 | Fixed | MIG:1301-1312. |
| Minor 3 | Fixed | `_Changed`, KC1-KC3. |
| Minor 4 | Fixed | MIG:1224. |
| Minor 5 | Fixed | MIG:1218, PDO2. |
| Minor 6 | Fixed | No md5 in the state queries. |
| Minor 7 | Documented as a limit, not fixed | "covers ONE run". |
| Minor 8 | Fixed where seen | Five flags, PO2 reference removed, always-true assert, `_READ_ONLY_DEFAULT` removed. |

## Not checked

- Any run.
- `DIFF-main-to-head.patch`, beyond three greps.
- `cli.py`, `store/postgres.connect` (connection timeouts), the fixtures, `tests/conftest.py`.
- TICKET-P3a.md beyond line 51.
- CHANGELOG outside the lines in the round-12 diff.
- The head text of tests outside the diff hunks.
- The full MUT list (only the round-12 hunks and the sample above).
- PostgreSQL 14, 15, 17, 18 behaviour.

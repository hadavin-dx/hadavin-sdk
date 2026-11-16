<!-- full hand-back report of sub-agent a5a5ac6b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW, round 1: P3a-2 round 13 (TICKET.md rev 1)

VERDICT: NOT READY. Blocker 0, Major 8, Minor 12.

The central design holds up. The state judgement, the three calls, the honest promise table and the "applied but not verified" outcome are sound in principle. The Majors are all fixable in the ticket text.

What I read: the ticket (all of it), D-009/D-019/D-020 (D-019 and D-020 in full), the headings of the design review, and the old code at MIG:1098-1254 and 1575-1677. I ran no SQL. Every PostgreSQL behaviour I state below is from reading and from memory, and I mark each one that needs a probe.

======== MAJOR FINDINGS ========

**M1. The oracle cannot see about half of the 37 effects (7.2 against 7.3). Acceptance items 8 and 9 cannot pass as written.**
- 7.2 lists these attempts: SELECT, INSERT, UPDATE on the FIRST column, DELETE, TRUNCATE, LOCK, per-column SELECT, nextval/currval/setval, EXPLAIN of a function, CREATE TABLE in a schema, CREATE SCHEMA, lo_get/lo_put, and SET ROLE.
- Effects with no listed attempt that could reveal them:
  - E03 REFERENCES and TRIGGER: no `ALTER TABLE ADD FOREIGN KEY` or `CREATE TRIGGER`.
  - E05 UPDATE on a column other than the first.
  - E14 procedure: no `CALL`.
  - E16 and E26 grant option: no attempt to `GRANT` to the fresh role.
  - E19 TEMPORARY: no `CREATE TEMP TABLE`.
  - E20 USAGE on a type or domain: no `CREATE TABLE (c type)` or cast.
  - E21 language: no `CREATE FUNCTION ... LANGUAGE`.
  - E23 foreign server: no `CREATE FOREIGN TABLE ... SERVER`.
  - E24 tablespace: no `CREATE TABLE ... TABLESPACE`.
  - E25 parameter: no `SET <param>`.
  - E31 and E32, the pg_* roles and flags: no `pg_read_file`, `COPY ... PROGRAM`, `CREATE ROLE` or `CREATE DATABASE`.
  - E34, E35 and E36 default rights: they act only on a FUTURE object. The oracle never creates one as the migration role and then probes it.
- 7.2 says "an effect the oracle cannot see fails the suite". So the ticket fails its own sensitivity control.
- There is a second unsound point. "UPDATE on the first column" needs SELECT as well if it names the column on the right of `SET c=c`. UPDATE and SELECT blur together.
- Smallest change:
  - Add to 7.2 a table "effect to the oracle attempt that shows it".
  - Add a step "as the migration role create a fresh table, function, sequence and type, then probe it as each role" for E34-E36.
  - State that the oracle tries every column, not only the first.

**M2. Step 8 (4.1 and 4.2) handles only "cannot connect". Every other failure after the COMMIT can come out as exit 2 with the words "Nothing was changed".**
- Scenario A, QueryCanceled. The migration role has a saved `statement_timeout` (common, for example 30 s) or the hostile file set one with `ALTER ROLE mig SET statement_timeout = 1`. The `RECIPE_TIMEOUTS` are `SET LOCAL` in the main transaction only, so the fresh connection never gets them. Q2 is cancelled at step 8. The existing `except (LockNotAvailable, QueryCanceled)` handler at MIG:1673-1676 runs `_limit_error` and raises a plain-words `ConfigError`, exit 2. That says "refused, nothing happened" after the files are committed. Exactly the false claim this ticket is meant to remove.
- Scenario B. The 3.5 version refusal and the 3.6 self-check both raise `ConfigError(... "Nothing was changed")`. If they fire at step 8 (a failover to a different server, say) the same thing happens.
- Scenario C. Any `psycopg.Error` in the verify queries at step 8, for example `pg_describe_object` on an object another session just dropped.
- Smallest change:
  - Wrap ALL of step 8 so that any exception, `ConfigError` included, becomes `AppliedNotVerifiedError` ("could not run").
  - Keep step 8 outside the `try` that feeds `_limit_error`.
  - Decide the time limits for the step 8 transaction explicitly: either set a recipe `statement_timeout` there, or `SET LOCAL statement_timeout = 0`.
  - Add a dedicated test: role-level `statement_timeout = 1`, expect exit 5.

**M3. Step 7: "A server error at COMMIT: raised as it is, exit 3; the server has rolled back" is not always true.**
- A connection reset after the COMMIT was sent is an unknown outcome. The commit may have succeeded.
- Then the ledger holds the files, the run reports a rollback, and no check has run.
- This is the same honesty class as step 8.
- Smallest change:
  - A COMMIT error that is not a server-reported transaction abort (a connection error, not an SQLSTATE class 40 or 23 reported by the server) takes the "applied, not verified" path.
  - Say in the message: "the commit may or may not have happened; run migrate again to find out".

**M4. The printed fix for a right held by a built-in role damages the server.**
- 3.1(a) and 3.4 line 1 judge a system-schema item whose grantee is a subject. A subject includes every role in the closure.
- Fact 21: a fresh server grants `pg_monitor` and `pg_read_all_stats` explicitly on `pg_catalog` objects.
- Scenario: runtime role `rt` is a member of `pg_monitor`. S2 refuses the membership, but S5 also emits one problem line per system relation granted to `pg_monitor`, each with `fix = REVOKE SELECT ON TABLE "pg_catalog"."pg_stat_activity" FROM "pg_monitor";`.
- 4.2 prints "every one, in this order (memberships first)". The test in 4.2 runs all of them as superuser and checks that verify then returns nothing. It would pass, and it would strip monitoring rights from the whole cluster.
- Smallest change:
  - S5 on a system-schema object is judged only when the grantee is the named role itself, or a non-built-in role. A right that comes through a `pg_*` role is one S2 line, with only the membership fix.
  - Add a rule: a fix is never printed against a system schema.
  - Add a test: a named role in `pg_monitor` prints exactly one statement, `REVOKE "pg_monitor" FROM "rt";`.

**M5. The printed fix statements ignore the grantor. Q2 and Q1b return it, but `Problem` has no field for it.**
- Per the PostgreSQL manual, a superuser's GRANT or REVOKE acts as the object owner, and a REVOKE only removes what that effective user granted.
- Scenario: `GRANT SELECT ON other.secret TO boss WITH GRANT OPTION`; `boss` grants SELECT to `rt`. The owner's (or a superuser's) `REVOKE SELECT ... FROM rt` leaves the entry whose grantor is `boss`.
- Same for a role membership granted by a CREATEROLE role: the PG16 REVOKE defaults to the bootstrap or current grantor. It needs `GRANTED BY` or a warning is printed and nothing is revoked. This needs a probe.
- The "run all printed statements, verify is clean" test only covers generated cases with the owner as grantor.
- Smallest change:
  - Carry `grantor` in `Problem`.
  - Print `... GRANTED BY "<grantor>"` where PostgreSQL has the form (memberships in 16), and `CASCADE` or the grantor-first order for table rights.
  - Add generator cells "grantor is not the owner" (E02 through a grant-option holder, a membership granted by a boss role).
  - Part of the same probe: `REVOKE ALL ... FROM named` at step 4 does not remove another grantor's entry. See m5 below.

**M6. The object side is limited to the schema of the run. D-020 does not say that, and the ticket does not list it in 10.3. It also drops a detection the old code had.**
- D-020: "from the side of the objects the migration role family owns". 3.3 narrows this to "each object in the schema of the run".
- Old code, MIG:1115-1119 and the `_changed_since` scope: "every relation, function and schema that is new or changed after the files, in any schema". It refused any right for a role that is not the owner or a named role (MIG:1121-1124).
- Not judged now: `CREATE TABLE other.t ...; GRANT SELECT ON other.t TO some_third_role;` in a file, with `other` owned by the migration role. The grantee is not a subject, not everyone, and not in the run schema.
- Also not judged: `ALTER TABLE other.t OWNER TO g` where `g` is a role the migration role belongs to. The retired comparison refused that. The kept test `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind` is "kept with the same intent". It would fail for a third-role target in another schema, or silently pass only because the target is a named role.
- This contradicts 5.3, which says "the comparison finds nothing that the state check does not find". It also contradicts the matrix: carrier C10 ("object lives in another schema that the migration role owns") x E37 (a right for a third role) is expected to be outcome (i) refused, and the code does not refuse it.
- Smallest change, either of:
  - (a) Extend the object side to every family-owned object in the database. This has the same shared-database cost as the subject side.
  - (b) Add it to 10.3 as an AUTHOR ADDITION that narrows D-020. Add a CHANGELOG sentence. Take the C10 third-role cells out of (i) and mark them "not promised".

**M7. Rule O5 (other members of an owning group count as owners) gives a false refusal on a normal setup. It goes beyond D-020. There is no escape except removing colleagues from the group.**
- Scenario: `CREATE ROLE app_owner; CREATE ROLE mig LOGIN IN ROLE app_owner; CREATE ROLE alice IN ROLE app_owner;` The tables are owned by `app_owner`. Step 2 refuses with `REVOKE app_owner FROM alice`.
- A named role in that group is already refused by S3, so O5 only adds third parties, such as other administrators.
- That is not a right of the grant map. It is also not an "owner handed over by a file"; the comparison it replaces needed a before-state.
- The upgrade note even lists "a login ... member of a group" as typical, but gives no way out for this.
- Smallest change: strike O5 (10.3 item 3 says the lead may). State "other members of an owning group are not judged" in 1.4. Or make it a printed notice that does not refuse.

**M8. Step 8 sends `options="-c search_path=pg_catalog,pg_temp"` (4.1). It buys nothing and can break connecting.**
- `verify`'s first statement is `SET LOCAL search_path`. The only statement `connect` sends earlier is `SET TIME ZONE 'UTC'`, which looks nothing up. So the startup option is redundant.
- Cost 1: a pooler or managed proxy that does not accept the `options` startup parameter (PgBouncer without `ignore_startup_parameters = options`) fails to connect. Then every run ends exit 5 permanently, even when nothing is wrong. That is a false alarm on a supported managed-database path.
- Cost 2: the keyword argument replaces an `options=-c role=M` that already sits in the DSN (carrier C9). The fresh connection then loses the role switch. 10.4 admits the pass-through is unchecked.
- Smallest change: drop the option; rely on the `SET LOCAL` first statement. Add a test with a DSN that carries `options=-c role=M` (C9) through step 8.

======== MINOR FINDINGS ========

**m1. Fact 26 ("operator capture NOT shown") is the wrong conclusion.**
- A user-defined operator with the same signature in a schema listed before `pg_catalog` does capture an unqualified operator. That is the documented class behind CVE-2018-1058. The probe failed to show it, which is not evidence of safety.
- Inside `verify` this is closed: `SET LOCAL search_path = pg_catalog, pg_temp` is the first statement, and pg_temp is never searched for functions or operators. Unqualified `~`, `=`, `||`, `bool_or`, `min` and `::text[]` are fine there.
- The kept queries are NOT pinned. These are the step 1 checks, the read-back at steps 3 and 6, and `_recheck_roles`. They run with whatever path the role or a file set. 5.2 qualifies catalog names and functions, not operators.
- Smallest change: run each kept catalog read in a savepoint with the same pinned path, or state this as a limit. Correct fact 26.

**m2. The Q1 closure is `UNION ALL` over a role graph.**
- A ladder of diamonds (n groups, each a member of two parents) gives 2^n paths; a depth of 30 hangs step 1.
- Use `UNION` on `(root, role)`, and compute `at_once` separately.
- Add a cost cell: a 25-level diamond ladder.

**m3. 4.2 prints every fix statement, with no cap.**
- A shared database with 50,000 other-application tables readable by everyone prints 50,000 lines to stderr.
- Suggest a cap on stderr plus a full list written to a file (or the same list in the exception attribute `statements`).

**m4. Step 5 wording.**
- `SET CONSTRAINTS ALL IMMEDIATE` also raises on deferred FK, unique and exclusion violations, on a timeout, and on a lost connection.
- The fixed text says "a trigger ... failed". Say "a deferred check or trigger".

**m5. `repaired_by_run` (step 2) is derived from the grant map, not from the grantor.**
- Step 4's `REVOKE ALL ... FROM role` removes only entries the migration role granted. Fact 16 shows only the owner-grantor case.
- Scenario: a named role's right granted by another grantor on a map table. Step 2 drops the line, step 4 does not remove it, and step 6 refuses after the files ran. The step 6 message says "remove that statement from the file". It is the wrong blame, and the loop never ends.
- Fix: mark `repaired_by_run` only when the grantor is the migration role. Add a cell.

**m6. The upgrade note says "give this package a database or a schema of its own".**
- A schema alone does not help: the subject side judges the whole database. Say "a database of its own, or roles that are not shared".
- It also conflicts with D-020's "the package does NOT require a schema of its own": in effect a shared database needs no other application to grant to PUBLIC. Name that plainly in the CHANGELOG.

**m7. Promise table (1.3): "STOPPED ... everything it did is undone" lacks the case where a file ends the transaction itself.**
- 4.1 step 3 and step 6 still carry the "hidden COMMIT" sentence. Step 6's "Nothing kept" column is then false in that case.
- Add "unless the file ended the transaction itself; that is reported separately" to 1.3 and to the step 6 failure column.

**m8. Oracle expectation for "everyone" and clean controls (7.2, 7.4).**
- A fresh role can also call other applications' functions (default EXECUTE) and use their types, and it has TEMPORARY and CONNECT on the database.
- The expected set for "everyone" must contain the 3.4 baseline. Otherwise the clean control "another application's schema" fails as soon as that schema holds a function.
- Add a function and a type to the controls.

**m9. 3.4 line 3 carve-out ("the row type that every table carries") is specified only for tables.**
- Rows in pg_type that default to USAGE for everyone:
  - Row types of tables, partitions, views, materialized views and foreign tables.
  - Sequences: I am not sure whether they have a row type in 16 and 17. Probe it.
  - Standalone composite types (relkind `c`), which are NOT a row type of a relation. A dynamic `CREATE TYPE x AS (...)` must stay refused.
  - Enum, range, multirange, domain and base types are real types and stay refused.
- Everything else with a default everyone-right: functions, procedures and aggregates (EXECUTE), languages (USAGE), the database (CONNECT and TEMPORARY). I found nothing else that gets one by default in 16. Table, view, sequence, column, schema (except `public`), large object, FDW, foreign server, tablespace and parameter have none.
- The carve-out must key on `typrelid <> 0 AND relkind <> 'c'`, not on a name pattern. Make a generator cell for each of the six kinds plus a standalone composite type. The 3.4 sentence "named subject grant on a row type is still refused" must be tested after the GRANT has materialised `typacl` (the `=U/owner` entry for everyone appears next to it).

**m10. Cost fixture (7.6, acceptance 21).**
- 5,000 tables test only `pg_class`. Add functions (around 50,000), columns with `attacl`, many large objects, many roles and memberships, and many `pg_shdepend` rows.
- Q2's inner UNION ALL is materialised for the whole database once per call. 30 s is also above the `RECIPE_TIMEOUTS` statement limit that steps 2 and 6 run under. State the actual limit value and test below it.
- Also: under READ COMMITTED the eight statements use eight snapshots. Say so in the CHANGELOG (the post-commit check is not a single snapshot).

**m11. Round-12 coverage in 5.6.**
- F2, the variant that disables the audit triggers: refused by the kept read-back, but no generator cell is named for it.
- C-F9: only one unit test for the reviewed-definer key. It should also have a real-server cell (same name in another schema, overload).
- Minimum counts in 7.4 ("every buildable effect x every carrier") include pairs that are logically empty (for example C6 x E33). Define "not buildable" for logical reasons, not only for server refusals.
- The mapping between oracle findings and problem lines for outcome (ii) is not defined ("every excess the oracle finds is named"). Give the mapping per effect.

**m12. Step 8 has no lock, so two runners can interleave.**
- Another runner's committed files can show up in this run's step 8, under "Applied in this run".
- An unrelated administrator's grant a second after the COMMIT also gives exit 5 to a deployment pipeline. Say so in the message: "or by another session since".

Also small points:
- Identity-argument text (`ALTER FUNCTION ... (args)`) comes from the server and may carry control characters in argument names. The "plain name" test must cover the whole argument list.
- S2 refuses every `pg_*` role, including benign ones. That is consistent with D-020. State it in the CHANGELOG.
- The 288 against 280 mutant difference is open.

======== THE QUESTIONS YOU ASKED ========

**(1) Promise table and the after-commit design.**
- Row 1 (our mistake, STOPPED) holds for deferred triggers: `SET CONSTRAINTS ALL IMMEDIATE`, then verify, before COMMIT.
- Row 2 (careless, lasting rights only) holds, with the transaction-ending exception from m7.
- Row 3 (hostile, DETECTED) is honestly worded. The re-defer route (fact 4) is a correct finding by the author. Concrete SQL, as the ticket's p3: a trigger function that runs `SET CONSTRAINTS ALL DEFERRED` and queues an `INSERT` into a table with a deferred constraint trigger, which grants at COMMIT.
- Completeness gaps: only M2, M3 and m12. The "applied but not verified" wording itself is right. Also:
  - The pre-commit check is "not the sound one". The ticket says so correctly in fact 4.
  - A hostile file can make step 8 fail (role-level timeout, connection limit). That ends in exit 5 only if M2 is fixed.
  - A right a trigger gives one second after step 8 stays outside every promise. 1.4 says so.
- Failure handling:
  - A distinct class and exit 5: acceptable, and correct to not make it a `ConfigError`.
  - Printed statements: acceptable only after M4 and M5.
  - No automatic repair: acceptable. The 4.3 reasons hold.
  - The first sentence is fixed and clear.

**(2) `verify`.**
- Subject side:
  - Q1 closure with all options: right. Counting a membership with ADMIN OPTION only is conservative and correct, because that role can grant itself the membership.
  - `pg_database_owner` pseudo-membership (fact 8): right.
  - Predefined roles: S2 is blunt but consistent.
  - Cost: m2, m10.
- Object side: restricted to the run schema, M6.
- 13+1 column list with a run-time self-check: right. It covers ACL columns only. A new membership semantic in a later version is not covered by Q0 (the CI run on 17 is the guard).
- Ownership via `pg_shdepend` with `dbid IN (0, current)`: right. Objects in other databases are named as not checked (10.1).
- Baseline: carve-out incomplete as specified (m9). List of default everyone-rights: no other kind found.
- Path pinning:
  - Inside `verify`: closed. Role-level and database-level path settings, function-level SET and temp objects cannot capture, because `SET LOCAL` is first and pg_temp is last and not searched for functions or operators.
  - Not closed for the kept queries: m1.
  - The same applies to the CTE names (`named`, `fam`, `subj`, `obj`): CTEs shadow tables, so a temp table cannot capture them.
- Author additions:
  - Grant on a system object naming a named role is judged: right for the named role itself or a non-built-in grantee. Wrong as written for roles reached through the closure (M4).
  - O5: wrong, M7.
  - Pre-first-file check ignoring two things: right in principle, and needed for the upgrade from main. Needs the grantor refinement (m5).
  - Exit code 5 and a new class: right. Needs the M2 and M3 completeness.
  - `verify` takes `schema` and `login_role`: right. A pass-through of values read once.

**(3) Order of `migrate`.**
- Between steps another session can:
  - Commit a grant on any object the transaction has not locked, between the step 6 read and the COMMIT. Step 8 then catches it (m12).
  - Fire an `ALTER ROLE` that changes how a fresh connection behaves (M2, M8).
- Race with the advisory lock: step 8 is outside the lock (m12).
- Which login, which options: see M8. Step 8 must keep the DSN options and add nothing.

**(4) Keep, change, delete: what the old code caught that the state check does not replace.**
1. A third-role grant on a family-owned object in any other schema (M6).
2. A family-owned object handed to a role the migration role belongs to, in another schema (M6). In the run schema it is caught only when the group has another member (O5, M7).
3. A SECURITY DEFINER function in another schema, owned by the family, that only its owner may call. The old code refused it if it changed. The new S7 passes it. That is probably acceptable, but it must be in the CHANGELOG.
4. The "another session changed an object" message is deleted on purpose.
5. A function body change was not refused by the old code either, only its rights. No loss.
6. A named role's pre-run excess is repaired by step 4 only if the grantor is the migration role (m5).

**(5) Test design.**
- `SET SESSION AUTHORIZATION` per attempt, in a savepoint, with the error class as the signal, is sound in itself (fact 18). The soundness problem is the attempt list (M1).
- Sensitivity controls are mandatory and good. They expose M1.
- Cells and counts: see m8 and m11. Fully covered by a named cell: F1, F3, F4, F5, F6, F7, F8 and most C-F items. Not covered: F2's audit-trigger variant.
- PostgreSQL versions: 16 here, 17 in CI (acceptance 19). 18 not run and not claimed. This is honest. The CHANGELOG must say what it claims for 17, which is "the whole suite green in CI". The expected-table for the oracle must know the 17 MAINTAIN privilege.

**(6) Scope and splitting; contradictions.**
- With D-020:
  - Object side narrowed (M6).
  - "No exception list" is kept (a code constant only).
  - "The package does NOT require a schema of its own" is true in letter and false in effect (m6).
  - The family is read from the current user (as a passed-in value). Allowed.
- Inside the ticket:
  - C10 x third role (M6).
  - Step 6 "Nothing kept" against the file-COMMIT sentence (m7).
  - The 7.2 oracle against 7.3's list (M1).
  - 5.3's "finds nothing the state check does not find" (M6).
- Splitting: keep section 6 in this round, as the ticket says. It is operator safety. The commit split in 9.3 is sensible. A better split of the round itself: do M1, M4 and M5 inside the matrix commit rather than as follow-ups.

**(7) Wording of section 1 for an owner.**
- Plain and mostly clear. The ticket explains "role", "grant map" and "migration role".
- Fix:
  - 1.3 "STOPPED ... undone": add the file-ending-the-transaction case (m7).
  - 1.3 row 3: add "the check after the commit can itself be cheated by a hostile file (see 1.4); the check can also fail to run" in the table, not only in 1.4.
  - 1.4: add "other members of a group that owns the tables are not judged" if O5 is struck.
  - The word "family" is not in section 1, which is good. Keep it that way.

======== D-020 points I think wrong or incomplete ========
- "From the side of the objects the migration role family owns": wording is not limited to a schema, but the cost and false-refusal implications were not worked through. The ticket narrowed it silently (M6).
- Row 2 "careless or copied file: STOPPED for lasting rights" is true only up to the commit and the transaction-ending exception (m7).
- "After commit: loud, distinct error" does not say what happens when the check itself errors. The ticket must decide (M2, M3).

======== Not checked ========
- No SQL run. Q0-Q4 and v1.sql were not read; I judged them from the ticket's sketches and result shapes.
- The evidence file RESULTS.md, the r12 reviews and the design review body were not read in full.
- cli.py, ci.yml, the mutant list and the test files were not read.
- Facts to probe before build: the PG16 REVOKE grantor behaviour for memberships and table rights (M5, m5); whether sequences have a row type in 16 and 17 (m9); psycopg `options` replacement of a DSN `options` (M8).

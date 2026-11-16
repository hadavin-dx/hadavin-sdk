<!-- full hand-back report of sub-agent a2b6f315, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, design critic, P3a-2 round 11 delta (head 8382bdd5b0e3). Read-only, snapshot only: /home/user/build/snap/p3a2-r11-8382bdd/.

## Failures and limits first

- **No independent evidence exists for this delta.** Nothing was run by me or by an evidence runner. Every "killed by", "fails on the old code" and "passes" below is by reading only. This round cannot count as a clean round and nothing here is "verified".
- **Verdict: not clean.** 0 Blocker, 5 Major, 8 Minor.
- **The ticket does not cover this delta.** P3a.md (frozen revision 10 plus build notes, read in full) has nothing on the whole-database before/after comparison, the `REPLICATION` flag, the `ALTER ... OWNER TO` text rule or the default-rights widening. I had no resolve or disposition file for round 10, so I could not check the delta against the findings it claims to answer.
- **Out of scope of the delta:** numbering and ordering rules, the advisory lock, the one-transaction structure and the ledger code are not changed by these four commits (only new tests for the lock-wait bounds). I did not re-review them.

## Major

**M1. A named role may be given read rights on anything outside the grant map, and sequence `USAGE` is called "reading".**
- Where: `src/hadavin_sdk/store/migrate.py` `_READ_ONLY_RIGHTS` / `_READ_ONLY_DEFAULT` and their use at lines 1030 and 1067.
- Scenario: a file holds `GRANT SELECT ON "other_schema".secrets TO <portal role>` (the text rules allow a table grant). `migrate` accepts it. `effective_problems` only looks at the run schema (line 309-313), so the same right is refused in the run schema and accepted in every other schema.
- `USAGE` on a sequence allows `nextval`, which writes; a read-only portal role can burn another application's ids.
- A default right `SELECT ON TABLES` for a named role, for all schemas, is also accepted.
- The tests pin the over-breadth as wanted: `test_a_named_role_may_only_read_what_is_not_in_the_grant_map[select_ok]` and `[sequence_usage_ok]`, and `test_default_rights_...[named_select]` and `[member_role_select]`; mutant RO2 forces the `USAGE` allowance to stay.
- This breaks deny-by-default and exact grants in least-privilege-hard-rule.md points 2 and 5; no per-action reason is given.
- Fix: refuse every right of a named role on an object outside the grant map, and every default right for a named role. If a real need exists, name it per right with a negative test, and never list `USAGE` on a sequence as reading.

**M2. The SECURITY DEFINER refusal was dropped for functions the migration role owns but no file names.**
- Where: `migrate.py` `_ACL_FUNCTION_SQL` and `_ACL_OWNER_SQL` (the `OR p.proowner = @ME@` clause is removed); pinned by mutant PO1.
- Scenario: a SECURITY DEFINER function owned by the migration role sits in the run schema, callable by PUBLIC. It was made by hand, by the hand recipe, or by dynamic SQL under a release before the check existed. Round 10 refused it on every run; round 11 accepts it for ever while no file touches it. It runs with the rights of the owner of all tables.
- `test_a_function_of_another_application_owned_by_the_migration_role_is_left_alone` only covers a plain function.
- Fix: keep leaving the rights of unmanaged functions alone, but still refuse an unreviewed SECURITY DEFINER function owned by the migration role (or a role it belongs to) in the run schema. Add the test and a mutant.

**M3. The function state hash misses body changes it claims to catch.**
- Where: `migrate.py:838-843`, `md5(coalesce(p.prosrc,'') || coalesce(p.proconfig::text,''))`.
- Gap (a): `prosrc` is empty for SQL-standard bodies (`BEGIN ATOMIC` / `RETURN`); the body is in `prosqlbody`. Scenario: an unmanaged SECURITY DEFINER function with such a body, owned by the migration role. A file runs `EXECUTE 'CREATE OR REPLACE FUNCTION ... SECURITY DEFINER RETURN (...)'` with a new body. Flag, rights, owner and hash are all equal, so it is not "changed", not looked at and not refused. (`_FUNCTION_CREATE` is anchored at `\A` or `;`, so a name inside an `EXECUTE '...'` string is not managed.)
- Gap (b): `probin` and `prolang` are not hashed.
- Gap (c): no separator between the two parts. Body `select 1 --{search_path=pg_temp}` with no saved setting hashes the same as body `select 1 --` with `SET search_path=pg_temp`.
- My statement that `prosrc` is empty for SQL-standard bodies is from memory of the PostgreSQL catalog, not probed.
- Fix: compare the fields themselves (no hash needed): `prosrc`, `pg_get_function_sqlbody(oid)`, `probin`, `prolang`, `proconfig`, separately. Add a test with a `RETURN`-form body and a mutant for the `proconfig` part (none is listed).

**M4. Another session's ordinary work in the same database now stops the run, with a message that blames a file.**
- Where: `migrate.py` `_objects` / `_changed_since`, called at lines 1425 and 1480; message at 1074-1087.
- Scenario: while `migrate` runs, another application commits `CREATE TABLE other.part_2026_11 ...` or `GRANT SELECT ON other.t TO app_reader`. The second read sees it as changed and the run is refused with "was handed to app2" or "app_reader has SELECT on other.t", under "after the migration files ran ... If a migration file made it".
- New relations and functions had this exposure before; round 11 widens it to every rights change on an existing relation, every schema and every function body.
- The same class was already fixed for roles (comment near line 439, tests `test_another_session_changing_unrelated_roles_does_not_stop_the_run`), so this is an unfixed sibling under class-level-fixes.md. No such test exists for objects.
- Fix: limit the comparison to what this role can change: objects owned (before or after) by the migration role or a role it belongs to, and rights whose grantor is one of those. Add a two-session test and say in the message that another session may be the cause.

**M5. The new fail-before claims are unproven, and several new tests cannot fail on the previous head.**
- By reading, these pass on the round-10 code (they are pins or mutant killers only):
  - `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind[function]` (function owner was already in the state)
  - `test_a_function_whose_body_a_file_replaced_is_treated_as_changed` (round 10 revoked PUBLIC on every owned function in the schema)
  - `test_a_named_role_that_may_pass_a_function_right_on_is_refused`
  - `test_the_database_owner_pseudo_role_may_have_rights_on_a_schema`
  - the two lock-wait tests in `tests/test_k2_migrations.py`
  - the positive cases `select_ok`, `sequence_usage_ok`, `named_select`, `member_role_select`
- The rest look fail-before by reading, but class-level-fixes.md asks for a run against the old code.
- Fix: the evidence runner runs the new tests on the parent of the four commits and saves which fail; the docstrings say which tests are pins.

## Minor

1. **`_ALTER_OWNER` can be switched off by the word `rename`** (`migration_numbers.py:688-690`). `ALTER TABLE t ALTER COLUMN rename SET NOT NULL, OWNER TO r` or `ALTER TYPE rename OWNER TO r` is not refused by text. The read-back backs tables, functions and schemas only, so the CHANGELOG sentence "`ALTER <anything> OWNER TO <role>` is refused" over-claims for types, domains, operators and large objects. Fix: exempt only `RENAME [COLUMN] owner TO` right before the word; add forms with `rename` as an identifier and a mutant for the exemption.
2. **CHANGELOG says what the code does not do.** Item 6, "How long it waits", now says that for a prepared transaction `migrate` "says so". `migrate.py:1135` still prints "a session this login cannot see holds it" and advises `pg_terminate_backend`, which cannot end a prepared transaction. No test pins either text. Fix the code and add a test with `PREPARE TRANSACTION`, or revert the sentence.
3. **`kept` mixes ids from three catalogs** (`_changed_since`). Ids are unique per catalog only; a collision lets a handed-over function pass as "kept". Fix: three sets, three parameters.
4. **Dead allowance for `CREATE` on the run schema** (`migrate.py:1062`, `who in allowed and sname == schema`). `effective_problems` (line 307) refuses it first. The comment and docstring ("the roles named in this run may create in the schema of the run") contradict the CHANGELOG, and no test can kill its removal. Remove it.
5. **`pg_database_owner` is skipped on a schema with any right** (line 1056, pinned by PDO1). If the database owner is a third role, it may create in the run schema unseen. Give the reason, or accept it only where it is the schema owner.
6. **`md5()` fails on a FIPS-mode server**, as a raw error (exit 3) on every run. Dropping the hash (M3) removes this.
7. **The comparison only covers one run.** What the hand recipe (runbook case (a)) changes on an object outside the grant map is never compared by the follow-up `migrate`. The CHANGELOG sentence "also an object that existed before the run" should state this limit, or the recipe path needs its own check.
8. **Wording and test hygiene.**
   - CHANGELOG.md:15 still says "any of the four role flags" for the named roles; the code now reads five. The `effective_problems` docstring was not updated either.
   - A test docstring names mutant PO2, which does not exist.
   - `test_a_function_that_kept_a_foreign_owner...` names OW5; the list says OW7.
   - `assert "hadavin_test_gf" in str(e.value) and schema` is always true in its second half.
   - `_READ_ONLY_DEFAULT` kinds `S`, `f`, `T`, `n` have no test and no mutant.
   - No mutant for `schemas = frozenset()`.

## Checked and found sound (by reading)

- **REPLICATION flag:** read at the start, after every file, for borrowed roles and for named roles; mutants RF1, RF2, RF3 and RF5 have named killers.
- **SQL built from strings:** the new SQL is constants plus `%(name)s` parameters; `@RELKINDS@` is a constant marker.
- **Failure half-way:** every new refusal is raised inside the one transaction, before the `REVOKE` loop.
- **Sweep fixture:** the savepoint is correct, because the failing `DROP` is already in its own savepoint.
- **Mutant FB1:** the name inside the `EXECUTE` string is not managed, so the claimed killer does kill it.

## Not checked

- No test, mutant, ruff or bandit run; no PostgreSQL probe.
- `src/hadavin_sdk/cli.py` is not in the snapshot, so mutant CL2's anchor is unverified.
- DIFF-vs-main.patch was not read; of `migrate.py` and `migration_numbers.py` I read only the changed regions and their callers, not the whole files.
- Row security and policies, view definitions, `relrowsecurity`, and rights on types, large objects and foreign servers reached by dynamic SQL are not in the compared state; I did not analyse them further.
- Cost of two whole-catalog reads per run on a very large catalog under the 60 s statement limit.
- Linear-time behaviour of the `_ALTER_OWNER` pattern.
- Behaviour on PostgreSQL 14, 15, 17 and 18 (for example default-rights kind `L`).
- Whether all three hunks of the `closure` to `via_membership` rename still anchor their mutants.

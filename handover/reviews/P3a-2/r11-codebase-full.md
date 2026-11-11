<!-- full hand-back report of sub-agent a573bc87, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, P3a-2 round 11 delta, head 8382bdd5b0e3. Snapshot only: /home/user/build/snap/p3a2-r11-8382bdd/

## Status of this review

- **Nothing was executed.** I have read-only tools, so no test, mutant or SQL was run. Every finding below is from reading; nothing in round 11 is proven to pass.
- **No Blocker found by reading.** No new test looks certain to fail, and every new mutant's `old` text is in its file exactly once (CL2 targets `cli.py`, which I could only see as a diff).
- **Read in full:** `migrate.py`, `migration_numbers.py`, `DIFF-round11.patch`, `tests/fixtures/migration_role.py`.
- **Read in part:** the ticket (lines 1-51 and 270-287 of 287, plus greps), `DIFF-vs-main.patch` (the `cli.py` and `conftest.py` hunks), and the test files beyond the round-11 hunks.
- **Timing-harness flake: cannot answer.** `test_the_timing_harness_flags_a_quadratic_stand_in` is in no snapshot file and in neither patch. The only "timing flake" texts are the lock-wait tests (`tests/test_migration_postgres.py:2260, 2929, 3350`).
- **The package's own text says PostgreSQL 17 is unrun.** The CHANGELOG sentence "Not yet run on PostgreSQL 17.10, the CI version" is pinned by `tests/test_migration_rules.py:658`.

## Major

**M1. The before/after object comparison is database-wide and unscoped by session, so another session's DDL refuses the run.**
- Where: `src/hadavin_sdk/store/migrate.py:960-978` (`_changed_since`), `:888-903` (`_ACL_OWNER_SQL`), `:1425` and `:1480` (the two `_objects` calls).
- Round 11 widens "changed" from new relations to every relation ACL, every function body and every schema owner or ACL in the database. The transaction is READ COMMITTED, so commits by other sessions between the two snapshots count as changes "a file made".
- Reproducing sequence:
  1. Session A runs `migrate` and holds the lock.
  2. Session B (another application, or a second test process) commits `CREATE SCHEMA other_app` or `ALTER SCHEMA s2 OWNER TO r2`, or `GRANT SELECT ON other.t TO app_reader`.
  3. A's second snapshot puts that object in `changed_schemas` or `changed_rel`; it is not in `kept`.
  4. A refuses with "the schema s2 was handed to r2 (it is not owned by the migration role)" or "app_reader has SELECT on other.t", and step (1) of the message blames a migration file.
- Test-suite form: `plain_role_connect` runs `ALTER SCHEMA <scratch> OWNER TO <role>` (`tests/fixtures/migration_role.py:365-369`) before the second process blocks on the migrate lock. Two test processes on one database, which the fixture header says it supports (`:35-36`), can therefore fail each other's `== REAL` assertions. The schema branch is new this round.
- The members read-back was scoped for exactly this reason (comment at `migrate.py:431-432`); the object read-back is not.
- Proposed fix: count an object as changed by this run only when its catalog row was written by this transaction, or when its owner before or after is the migration role or a role it belongs to. At the least, word the refusal as the membership one is ("it may be another session; run migrate again"). Add a test with a second connection that commits a schema or grant change mid-run.

**M2. A default right granted to the migration role itself by a role it belongs to is refused as a stranger's right.**
- Where: `migrate.py:916-924` (`_ACL_DEFAULT_SQL`) and `:1066-1071`.
- The query now takes every `defaclrole` the current user is a member of and drops only `a.grantee = d.defaclrole`. The loop allows only `named`.
- Reproducing input: `CREATE ROLE grp; GRANT grp TO migrator; ALTER DEFAULT PRIVILEGES FOR ROLE grp IN SCHEMA s GRANT SELECT ON TABLES TO migrator;` then `migrate(dsn)`.
- Result: "migrator gets SELECT on every new table that grp makes in s". The same message says at `:1078` "Only the migration role itself and the runtime, portal and purge roles … may have rights".
- Before this round only `defaclrole = @ME@` was read, so this row could not appear.
- The five cases of `test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to` do not include grantee = migration role.
- Proposed fix: add `AND a.grantee <> @ME@` to the query (or skip `who == current_user` in the loop) and add that case with a mutant.

**M3. User-facing CHANGELOG text contradicts the code.** Under the persona's rule a document that contradicts the code is Blocker class; I rate it Major because each fix is one sentence.
- `CHANGELOG.md:23` (edited this round) says that when the server shows no session (for example a prepared transaction) the message "says so". `migrate.py:1135` still prints "a session this login cannot see holds it". No test pins either wording.
- `CHANGELOG.md:15` (edited this round) still lists "any of the four role flags (superuser, `CREATEROLE`, `CREATEDB`, `BYPASSRLS`)" for the named roles. `effective_problems` (`migrate.py:295-304`) now refuses `REPLICATION` too, and the new test `test_a_named_role_with_the_replication_flag_is_refused` proves the intent.
- `CHANGELOG.md:20` says of `ALTER <anything> OWNER TO`: "A function body that does it by dynamic SQL is found by the read-back." The read-back covers only relations, functions and schemas (`migrate.py:835-853`; the comment at `migration_numbers.py:685-687` says so correctly). A type, domain or foreign server handed over by `EXECUTE` is not found.
- `CHANGELOG.md:19` says a named role "may only read an object that is not in the grant map". In the schema of the run `effective_problems` refuses even `SELECT` (`migrate.py:333-346`). The new rule only takes effect in other schemas, which is why every new test uses `second_schema`.

**M4. The ticket does not describe the built result.** Ticket: `/home/user/hadavin-sdk/handover/tickets/P3a.md`, revision 10, frozen.
- Line 13 says P3a does not change `cli.py`; `DIFF-vs-main.patch:279-330` adds `--lock-wait-seconds` there.
- Line 45 lets `SET LOCAL lock_timeout` and `statement_timeout` pass; `migration_numbers.py:695-697, 720-724` refuses every `SET`.
- Line 276 (BN-P3a-2-a) says nine read-back values; `_READBACK_VALUES` has eleven (`migrate.py:399-411`).
- Line 280 names `tests/fixtures/migrations_released.json`; the code uses `src/hadavin_sdk/store/migrations_released.json` (`migration_numbers.py:79`).
- In the parts read or grepped, the ticket has no text for the round-11 behaviour: the `REPLICATION` refusal, the owner and ACL read-back of existing objects, the default rights of member roles, the `ALTER … OWNER TO` text rule.
- Proposed fix: a build note per item, as BN-P3a-2-a to -e already do.

## Minor: code

**m1. The `rename` exemption in `_ALTER_OWNER` lets real owner changes pass, and breaks the file's own boundary rule.**
- Where: `migration_numbers.py:688-690`; allow-list widened at `tests/test_migration_names.py:~112`.
- `ALTER TABLE t ADD COLUMN rename int, OWNER TO r` is valid (RENAME is an unreserved word; `OWNER TO` is an ordinary action) and is not refused: the tempered dot stops at `rename`.
- `ALTER TABLE a$rename OWNER TO r` also passes, because `\brename\b` breaks at `$`. The comment at `:651-656` says a match that lets a statement pass must use `_NAME_START`/`_NAME_END`; `_ALTER_OWNER` was instead added to `BOUNDARY_ALLOWED_IN`.
- The read-back still catches a table, function or schema, so this is a tripwire gap only.
- Proposed fix: exempt only `owner` directly preceded by `RENAME` or `RENAME COLUMN|ATTRIBUTE|CONSTRAINT` (check the text before the match in Python), using the name boundaries. Add both inputs to `OWNER_FORMS`.

**m2. The function state hashes only `prosrc` and `proconfig`.**
- Where: `migrate.py:838-843`.
- A SQL-standard body is stored in `prosqlbody`, with `prosrc` empty as far as I know (not probed).
- Reproducing input: a file with `CREATE OR REPLACE FUNCTION "other".f() RETURNS int LANGUAGE sql RETURN 2;`. It passes `_SAFE_CREATE` and is not "managed" because of the other schema. The body change is not seen, so the PUBLIC default is not revoked. Mutant FB1's property does not hold for this form.
- Proposed fix: hash `pg_get_functiondef(p.oid)` for non-aggregates, or add `prosqlbody::text`, `prolang` and `probin`.

**m3. A global default right on functions or types is always refused, blaming PUBLIC.**
- Where: `migrate.py:916-935, 1066-1071`.
- A global `pg_default_acl` row holds the whole ACL, including the built-in `=X/role` entry.
- Reproducing input: `ALTER DEFAULT PRIVILEGES FOR ROLE migrator GRANT EXECUTE ON FUNCTIONS TO runtime;` then `migrate(dsn, runtime_role='runtime')`. Result: "PUBLIC gets EXECUTE on every new function…".
- The `"f"` and `"T"` entries of `_READ_ONLY_DEFAULT` are therefore unreachable for global entries. Only `ON TABLES` is tested.
- This existed for the migration role's own entries; round 11 widens it to every role it belongs to.
- Proposed fix: decide the policy, then either ignore the built-in PUBLIC entry or say in the message that `REVOKE … FROM PUBLIC` is needed in the default. Add cases for functions and sequences.
- Related: the query uses `pg_has_role(current_user, …)` only, while the other role checks use both `current_user` and `session_user`.

**m4. `kept` mixes ids from three catalogs.**
- Where: `migrate.py:971-978`, used at `:860, 868, 880, 891, 896, 900`.
- OIDs are unique per catalog only. After OID wraparound, a function that kept its owner can excuse a relation or schema with the same number that a file handed over. Schemas were added to the mix this round.
- Proposed fix: three `kept` sets, one per catalog.
- Same shape: `managed` mixes relation and function names, so a table named like a managed function counts as managed in `is_managed` (`:861`).

**m5. `USAGE` on a sequence counts as "may only read".**
- Where: `migrate.py:928`.
- `USAGE` allows `nextval`, which changes the sequence. Test case `[sequence_usage_ok]` and mutant RO2 pin this.
- Proposed fix: allow `SELECT` only, or change the words.

**m6. `effective_problems` still lists relkinds without `'f'`.**
- Where: `migrate.py:311`.
- A named role's rights on a foreign table in the run schema are checked only if a file changed that table in this run.
- Proposed fix: use the same `@RELKINDS@`.

**m7. Message quality.**
- `_ACL_OWNER_SQL` prints an unqualified `relname` for objects of any schema, and calls a view or foreign table "table or sequence" (`migrate.py:889`).
- `sorted(set(problems))[:20]` drops the rest with no "and N more" (`:1073`).

## Minor: tests, mutants, fixture

**t1. No test of the round-11 object read-back runs without a server.**
- `_changed_since` is pure and has no unit test.
- The wiring fake returns `[]` for every new query (`tests/test_migration_wiring.py:151`).
- So every RA, OW, SC, GO, RO, DP, PO, FB and RK mutant depends on `HADAVIN_TEST_PG_DSN` and a superuser login. `_admin` raises rather than skips for a plain login.
- Proposed fix: unit tests of `_changed_since` (new, changed, kept, per catalog) and a fake-row test of the four loops in `_refuse_unlisted_grantees`.

**t2. One assertion cannot fail.**
- `test_a_named_role_that_may_pass_a_function_right_on_is_refused` ends with `assert "hadavin_test_gf" in str(e.value) and schema`; `and schema` is always true.
- Proposed fix: assert `second_schema in str(e.value)`.

**t3. Mutant references and gaps.**
- The docstring of `test_a_function_of_another_application_owned_by_the_migration_role_is_left_alone` cites mutant PO2, which is not in `tests/migrate_mutants.py`. It would also be an equivalent mutant, because the owner query has `p.proowner <> @ME@`.
- The docstring of `test_a_function_that_kept_a_foreign_owner_is_not_refused_for_that_owner` cites OW5; the mutant that test kills is OW7.
- No mutant exists for:
  - the `changed_rel` clause of the column half of `_ACL_RELATION_SQL` (RA2 covers the table half only);
  - `sname == schema` at `migrate.py:1062` (no test gives a named role CREATE on another changed schema);
  - schemas in the `kept` loop;
  - `is_managed`;
  - `a.grantee = @ME@` in `_ACL_SCHEMA_SQL`.

**t4. One refusal test has two causes.**
- `test_an_owner_handed_over_in_the_run_schema_is_refused` grants `other` CREATE on the run schema, so the run is also refused for "has CREATE on the schema". Only the `match="was handed to"` pin keeps the test specific.
- Proposed fix: add `assert "has CREATE" not in …`, or put the right on another schema.

**t5. The fixture gives more than production does.**
- `plain_role_connect` makes the test role the owner of the schema (`tests/fixtures/migration_role.py:365-369`). The printed production role gets only CREATE and USAGE WITH GRANT OPTION.
- All round-11 tests therefore run as owner. The non-owner path is exercised only by chance, by the two older `real_connect` tests (`tests/test_migration_postgres.py:1697-1726`). That path relies on `kept` for the run schema after `GRANT USAGE ON SCHEMA`.
- Proposed fix: run the new schema and default-right tests once with the printed role.
- Stale text: the fixture docstring at `:3` and the test docstrings at `tests/test_migration_postgres.py:1348, 1457` still say three or four flags.

**t6. The lock-wait tests need a closed local port.**
- `tests/test_k2_migrations.py:159-185` connect to `127.0.0.1:1` and run the real folder checks first. A filtered port would hang until the connect timeout.
- Proposed fix: patch `mig.connect` to raise.

## Checked and found consistent (by reading)

- Tuple indexes in `_changed_since` (function owner at `[2]`, relation and schema owner at `[0]`).
- The UNION column types and named parameters of the new queries; no stray `%`.
- The five-flag wiring: `_ROLE_FLAGS` against `_ROLE_FLAGS_SQL`, `_BORROWED_ROLES_SQL`, `effective_problems`, and the fake's five-tuples.
- The printed production role passes the new schema grant-option check through `a.grantee = @ME@`.
- The savepoint in `sweep_stale_roles` and its test.
- The `MAX_LOCK_WAIT_SECONDS` arithmetic.
- The lexer's `$`, `E''` and carried-name logic: no hiding direction found.
- The parametrised ids named by the new killers match the `parametrize` values.

## Not checked

- Any execution: pytest, the mutant run, PostgreSQL 16 or 17 behaviour. The catalog facts in m2 and m3 are from memory.
- The mutant runner's kill logic (`tests/migrate_mutants.py:2440` onward) and the mutants older than round 11.
- `cli.py`, `store/postgres.py` (`connect`), `ci.yml`, `pyproject.toml`, the five migration files and both JSON lists.
- `tests/test_migration_numbers*.py`, `tests/migration_numbers_mutants.py`, `tests/fixtures/runbook.py`.
- Ticket lines 52-269.
- The CHANGELOG beyond the round-11 hunks.
- The unchanged bodies of the round-10 tests that round 11 only re-worded.

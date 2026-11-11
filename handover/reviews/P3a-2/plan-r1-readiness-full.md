<!-- full hand-back report of sub-agent a4014d7c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT READY. Blocker 2, Major 9, Minor 11. (Plan review round 1 of 3, implementation readiness. I read the ticket in full, the snapshot code, the five studio rules plus CLAUDE.md, and the author's v1.sql. I only skimmed the design review headings.)

Snapshot caveat: /home/user/build/snap/p3a2-r12-4d328e3/ has no src/hadavin_sdk/errors.py, store/postgres.py, store/migrations/*.sql, .github/ci.yml or tools/heavy_slot.py. Citations to those files could not be checked.

## A. Citation sample (34 checked)

OK, exactly as stated:
- MIG 1-78 (docstring), 36-37, 38-41, 45-48, 56-57.
- MIG 118-163, 203-257, 232-237, 260-280, 296 (effective_problems starts at 295), 384-400.
- MIG 780, 784, 821-824, 826-848, 851-908, 1007-1015, 1019-1023, 1026-1095, 1098, 1101-1106.
- MIG 1217-1225, 1234, 1240, 1241-1244, 1247-1249, 1257-1325, 1364, 1471, 1492-1509, 1524-1554.
- MIG 1579-1672, 1607 and 1662-1663.
- cli.py:9 and :19; MUT:2997-3016; MN:722-723.
- TPG:4499 and :4520.
- All 29 TPG test names in 5.4 exist. All 16 TCMP tests exist, and the retired/rewritten/kept split adds up to 16.
- The three TW tests that call `effective_problems` exist.

Wrong or stale:
1. CL:12 is stale. The "reach beyond this package's own objects" sentence is on CL:11. CL:12 is the "powerful flags" bullet.
2. MN:680-683 is stale. The comment is at MN:677-679 and `_GRANT_TARGET` starts at 680.
3. TPG:242 is misdescribed (ticket 6.3 and 7.8). Line 242 is the plain `return` after `yield` in the `_plain_role_may_set` contextmanager. It is not a vacuous pass after a server-setting read. The 7.8 AST rule as worded would flag a legitimate generator exit.
4. TW:192 and :208 ("stale md5 wording goes with its helper") are wrong. They are inside the helper for `_READBACK_TRIGGERS_SQL` (the trigger read-back), which is kept.
5. "`test_migrate_refuses_a_changed_released_file_before_it_connects` only mentions `changed_rel` in a helper" is wrong. `changed_rel` does not appear in test_migration_wiring.py at all, and that test (TW:1244) needs no re-pointing.
6. MIG:283-366 is loose. `_TABLE_PRIVS` starts at 283, `effective_problems` is 295-372, and `_no_duplicate_names` starts at 374.
7. MUT header "about 10 minutes". The studio measures 30+ minutes for 288 mutants (see E).
8. "280 vs 288 mutants". My grep of `Mutant(` literals gives 279, so the list is probably also built by helper functions such as `cmp_mutant`. Not resolved here.

## B. DELETE list: callers the ticket forgot

- `_TABLE_PRIVS`, `_SERVER_VERSION_SQL`, `_MAINTAIN_FROM` and `_table_privs` (MIG:283-292) are deleted in prose in 5.4 but are missing from the 5.3 DELETE list.
- `_SCHEMA_USAGE_SQL` (MIG:694) is used only at MIG:1665, which moves into `verify`. It is not listed.
- Tests that call `effective_problems`: TW:1196-1235 only.
- `_TABLE_PRIVS` is read by TW:1227.
- Mutants whose planted line sits in `_table_privs`/`_MAINTAIN_FROM`: **MT1 and MT2** (MUT:1210-1225). They are in none of the retired, re-pointed or unchanged lists. Their killer `test_the_maintain_privilege_is_asked_about_from_postgresql_17_only` is retired, so they would be reported as "killer does not exist". This also explains why the ticket says "100" changed mutants while its lists add up to about 98.
- Mutants killed by `test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim` (TR:672-715), for example R23 at MUT:942-947, are not listed. That test pins CHANGELOG text the ticket deletes (see C3).
- `REVIEWED_DEFINER_FUNCTIONS` is monkeypatched by TPG:2804 and pinned by TR:704. Its type changes to a tuple frozenset (rule O4), which breaks the old test.
- Mutants killed by retired tests were all listed correctly. I checked OW7, FB1-3, SO1-3, CS1-5, KC1-3, OW8 and SD9.

## C. Findings

### Blockers

**B1. Commit order is not buildable (9.3).**
- Commit 1 deletes `_changed_since` and its inputs. `_refuse_unlisted_grantees` takes `changed` and its `_ACL_*` SQL filters on `changed_*` and `kept_*`. "The old final check reduced to the kept loops" is undefined.
- With empty `changed`, the kept tests that need that code fail. Examples: `test_a_right_given_on_a_table_of_another_schema_is_refused`, `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind`, `test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is`. Commit 1 cannot be green.
- `problems_with_the_list()` (MUT:2997) runs in an ordinary test, `test_every_migrate_mutant_still_applies_to_the_source` (TR:834). It requires every mutant's old text to be in its file exactly once and every killer to exist. Re-pointed mutants are scheduled for commit 5, so commits 1-4 are red.
- Fix: make "delete + verify + new order" one commit, or order it verify-in-parallel, then switch, then delete. Update retired and re-pointed mutants in the same commit as the code and tests they depend on. The ticket should state the per-commit green command: ruff, the affected tests, and `tests/test_migration_rules.py::test_every_migrate_mutant_still_applies_to_the_source`.

**B2. Rule O2 contradicts 3.4 line 2 and O7, and would refuse every default install.**
- O2 says "nothing for everyone", with only the row-type exception. The code comment at MIG:1135 says "PUBLIC has [USAGE] by default on `public`".
- On PostgreSQL 15 and later the `public` schema carries `=U/pg_database_owner`. O2 applied to the schema of the run (O1 covers "the schema of the run whoever owns it") refuses that on every `public`-schema setup, fresh or upgraded. The printed fix, `REVOKE USAGE ... FROM PUBLIC`, would break other users.
- 3.4 line 2 and O7 say "USAGE on a schema is allowed". Today's code and CHANGELOG say the same. The ticket tests only scratch schemas, so no test would catch this.
- Fix: add to O2 "USAGE on a schema for everyone is allowed". State whether O7's "role" includes everyone. Add one test where the run schema is `public` with the PostgreSQL default access list, plus the sensitivity control for it.

### Majors

**M1. The step 8 connection option breaks the shared test fixtures.**
- Step 8 passes `options="-c search_path=pg_catalog,pg_temp"`.
- `tests/fixtures/migration_role.py:354-359` (`plain_role_connect`, autouse via tests/conftest.py:94-108) reads `current_schema()` on the first connection when the login is a superuser, and raises `NotAScratchSchema` unless it starts with `hadavin_test_`. With that option `current_schema()` is `pg_catalog`, so every real-server test with a superuser DSN fails at step 8.
- Fix: either pin only inside `verify` (the `SET LOCAL` at 3.1 already does) and drop the option, or state that `plain_role_connect` must pass the option through and take the schema from the DSN.
- Also state that `AppliedNotVerifiedError` must wrap any failure in step 8: a query error, a statement timeout, or a `ConfigError` from the version or self-check. Otherwise exit 2 ("nothing happened") would be printed after a commit.

**M2. Oracle environment is under-specified (7.2, 7.4, 7.7).**
- The oracle needs a superuser connection. Existing tests get one from `psycopg.connect(DSN, autocommit=True)` with `HADAVIN_TEST_PG_DSN` (TPG:85, 245). conftest says "any other login is used as given", so a non-superuser DSN would silently break `SET SESSION AUTHORIZATION`.
- Fix: the oracle fixture must fail (not skip) if the DSN login is not a superuser.
- "Every non-system schema" of the shared test database includes other tests' scratch schemas, other processes' `PLAIN_ROLE`s, and a mutant run in parallel. A leftover PUBLIC grant elsewhere would fail unrelated cases, because the subject side judges the whole database.
- Fix: say whether each case runs in a dedicated database, or define the oracle's and `verify`'s scope in the test database.
- The "migration role owns the database" and "holds CREATE on the database" fixture variants (7.4) have no definition. `plain_role_connect` makes `PLAIN_ROLE` own only the schema.
- Oracle details a builder must invent:
  - Procedures and aggregates cannot be tested with `EXPLAIN SELECT f(NULL...)`. A procedure is refused with 42809 before the ACL check, so it is always "allowed". Use `CALL`.
  - A savepoint with `SET SESSION AUTHORIZATION` needs `RESET SESSION AUTHORIZATION` between roles.
  - An overloaded `f(NULL)` can raise 42725 (ambiguous function), which would be classed "allowed". Give typed NULLs or skip.
- 7.2 forbids the words `acl` in the oracle module. "oracle" contains "acl" as a substring. State "whole word".

**M3. Tests and mutants needing change are not in 5.4 or 5.5.**
- About 10 fake-database wiring tests drive `migrate()` end to end with scripted `_Db` answers. Examples: TW:170-173, 306-309, 842-845, 857-860, 887-890, 917-920, 953-956, 1124-1127, 1149-1152, 1360-1363, 1643-1646. The new order adds many statements, so every scripted answer list breaks. The mutants READS_BEFORE, `WIRING_VAL` and others rely on them.
- tests/test_k2_migrations.py (13 `migrate` calls, 2 connect patches) includes `test_migrate_refuses_a_portal_role_that_inherits_write_rights`, the killer of PC1 and PT1. It is not mentioned.
- tests/test_migration_rules.py pins CHANGELOG and docstring wording, and the ticket deletes the text it pins:
  - `test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim` (TR:672-715) pins the CL:17 heading, `REVIEWED_DEFINER_FUNCTIONS`, "asks for `MAINTAIN` only from 17" and "Not yet run on PostgreSQL 17.10... fake the server version" (CL:34).
  - `_upgrade_bullet()` slices from "- **Migrations: stricter checks" to the next "\n- **". If the new "What migrate promises" is a new top-level bullet, the slice loses text.
  - `test_the_scope_the_order_and_the_file_own_limits_are_written_down` pins docstring phrases.
- The ticket also does not list which docstring phrases must survive: `RECIPE_TIMEOUTS`, `pg_auth_members`, "AFTER it, on purpose".
- Plus MT1 and MT2 (B above).
- Fix: add a "tests and mutants outside the lists" section. Name each test above as re-pointed. Say where the promise table is nested so `_upgrade_bullet()` still works, or that it is updated.

**M4. Acceptance commands cannot be run by an independent runner (9.1).**
- Items 4, 6, 8, 9, 10, 13, 14, 16, 17, 20, 21 and 22 name no test id or command. The ids are chosen by the builder. Examples: "the repository test 'every catalog name is qualified'", "the count test", "a test compares the two texts".
- Item 2: plain `grep -n ... -r src tests` also hits the committed `tests/__pycache__/*.pyc`, which prints "Binary file matches". Use `--include='*.py'`.
- Item 3 also matches comments and docstrings, so the new module must avoid those words even in prose. Say so.
- Item 12 does not say `HADAVIN_TEST_PG_DSN` and runs bare, not through heavy_slot.
- The command for `tests/migration_numbers_mutants.py` is not given.
- Item 13 "exit code 5 shown through `hadavin-sdk migrate`" needs a scenario. Name the test or give a procedure.
- Fix: fix the test ids in the ticket, or require a builder-notes table "item -> exact command" as a Blocker-level deliverable.

**M5. Runtime and heavy-job rules (7.10, acceptance 12 and 23).**
- The ticket estimates the mutant list at 10 minutes now and 15 after. The measured value is 30+ minutes for 288, about 6-7 s per mutant.
- After the change: 288 - 27 retired + 42 new (my count of 7.5 is 42, not "about 44") = 303 mutants.
- The 42 new V* mutants have real-server generator killers (migrate plus oracle, several principals). Allow roughly 10-20 s each, so +7-14 min. Expected total is about 40-50 min, over the 2400 s limit of `heavy_slot.py --slots 3 --timeout 2400`.
- Studio rule 2 says heavy jobs run only through heavy_slot. The ticket mentions it only for the full suite and "where that tool exists", and acceptance 12 runs bare.
- The generator adds at least 884 cases to every ordinary pytest run and to CI, also about 15-20 min.
- Fix: batch the mutant run into id groups (for example 3 groups of about 100, each under its own heavy_slot call with a timeout above 2400). Run the changed ids (about 114: re-pointed + new + LW7/LW8) while building and the full list once on the final head, alone. Say what the evidence runner does if a batch hits the timeout.
- The 60-minute builder time box (rule 1) is not addressed. The scope is a new module, an oracle, a 900-case generator, 42 mutants, 72 retired/re-pointed mutants, CI and texts, which is several builder sessions. Split into work packages with checkpoint notes (for example A: verify + order; B: oracle + generator; C: mutants + texts).

**M6. Circular import and a default argument (3.1).**
- `migration_verify.py` needs `_label` and `REVIEWED_DEFINER_FUNCTIONS`, which stay in migrate.py (5.2), while `migrate` imports `verify`. The ticket says only "Grant/GRANTS: builder's choice".
- `verify(..., reviewed_definers=REVIEWED_DEFINER_FUNCTIONS)` binds at definition time. TPG:2804 monkeypatches `mig.REVIEWED_DEFINER_FUNCTIONS`, so the patch would be invisible.
- Fix: decide here. Either move `_label`, `_shown`, `Grant`/`GRANTS` and the reviewed list into the new module (migrate re-exports them), or make `verify` take everything as arguments. Require `migrate()` to pass `reviewed_definers=REVIEWED_DEFINER_FUNCTIONS` at call time.

**M7. Missing definitions that `_judge` needs (3.1, 3.3, 4.1).**
- The mapping "named role kind -> allowed rights per relation kind" is spelled out only in the `migrate()` lambdas (MIG:1630-1654):
  - runtime: `g.runtime`.
  - portal: SELECT if `g.portal` (also for sequences).
  - purge: `g.purge`, plus SELECT on `purge_cols` columns.
  Ticket S5 says only "allowed by the grant map". Write the table.
- The missing-right check "each named role can use the schema" is moved into `verify`, but 3.2 says `has_*_privilege` is not used. Say how it is derived (a USAGE item in the schema's access list, directly or through PUBLIC; that is fact 6 again for non-inheriting roles).
- The query for step 4's "functions of the family in the schema of the run with EXECUTE for everyone" has no sketch.
- `PROBLEM_KINDS` is not listed, although tests and about 30 mutants refer to it.
- The Q2 text in the ticket is a fragment (CTEs `subj`, `fam`, `obj` are missing). The full text is only in /home/user/build/p3a2-r13-author/v1.sql, outside the repository.
- Changes (a)-(d) to Q2 are only described. (a) reading `pg_catalog` and `information_schema` while keeping out `pg_temp_N` and `pg_toast_N` needs a different filter than `!~ '^pg_'`; give it.
- Fix: paste the full Q2 and the step-4 query into the ticket (or commit them), and list `PROBLEM_KINDS`.

**M8. Old head proof (7.9).**
- New test files copied onto 4d328e3 will fail at import (`migration_verify`, `AppliedNotVerifiedError`) and so fail for the wrong reason. The "thin adapter" is not defined.
- Fix: state that the failure must be the assertion "migrate returned and the oracle finds an excess" (stub imports so collection works), and that import errors do not count.

**M9. Upgrade-from-main test (7.6).**
- A database "built by main's `migrate` (main 2a8c2aa)" cannot be built in CI. The test has no way to run main's code.
- Fix: say it emulates main's state (current files plus a PUBLIC EXECUTE on the trigger function, no REVOKE) and that this is the whole claim.

### Minors

- Mn1. 5.2 and 10.3(9) say `effective_problems` is kept "only if a caller outside migrate exists". Callers exist, but only in tests that are retired. Decide: remove.
- Mn2. CL:34's other claims also go stale: "MAINTAIN check ... fake the server version" and "asks for MAINTAIN only from 17". CL:15 also says "On PostgreSQL 17 and later ... MAINTAIN is also counted". Say what happens to those sentences.
- Mn3. 6.4 changes `_scan`'s `found: dict[name -> kind]`; `check_grants` iterates `created.items()` as `(name, kind)`. Say it keeps the dict and tracks the first file separately.
- Mn4. 6.3 CI approach: GitHub service containers cannot take a command. `options:` takes docker create flags, not postgres `-c`. The likely working route is a `docker run` step or `ALTER SYSTEM` plus `docker restart`. Say which to try first.
- Mn5. The row-type exception (3.4 line 3) must say exactly which types: `typtype='c'` with `typrelid` whose `relkind <> 'c'` (so standalone composite types are not exempt). Array types are already excluded.
- Mn6. Step 6 calls the existing `_check_read_back(db, saved, file_name, ...)`. What `file_name` goes in the message at step 6?
- Mn7. Step 5's `ConfigError` wrapper versus the outer `_limit_error` handler for 57014/55P03. Which wins?
- Mn8. 4.2 exit code 5: cli.py:9 documents only the migrate command line, not exit codes; the docstring line needs the new code text.
- Mn9. The promise-table equality test (acceptance 6) needs an extractable marker in the docstring and CHANGELOG. Name it.
- Mn10. Mutant count: 7.5 lists 42, not "about 44"; 288 - 27 + 42 = 303.
- Mn11. The `migrate()` docstring rewrite is vague ("Promise table first; section 1.5; section 9.3"). The module docstring "What `migrate` does, in order" list (items 1-5) also needs the new 8-step order, but only item 5 is rewritten.

## D. Other answers asked for

- SQL style: it matches the code. `%(name)s` is used by `_ACL_*_SQL` with `db.execute(sql, dict)`, and `%s` by the lock queries (MIG:1257-1271). The sketches contain no literal `%`. `ANY(%(named)s::text[])` is typed, so it is fine with server-side binding. As written they run as a plain login: every catalog and view used is world-readable, and the author ran them as `r13_mig`.
- Fixture facts: `tests/conftest.py` swaps `mig.connect` for `plain_role_connect` unless the test has the marker `real_connect`. `tests/fixtures/migration_role.py` makes one login role per process (`PLAIN_ROLE`) that owns only the scratch schema (named `hadavin_test_*`; anything else raises `NotAScratchSchema`). It provides `create_login_role`, `login_dsn` and `set_login_password`. It gives no superuser connection, no role owning the database, and no fresh-role fixture for the oracle. The oracle must use the `psycopg.connect(DSN, autocommit=True)` pattern.
- Stop rule (9.2): fine for a security path (no cap, rounds until a fresh round has no Blocker or Major). It lacks a stated builder time box and resume procedure (see M5), and does not say what ends the loop when the classing rule disagrees with a reviewer.
- Upgrade behaviour: the ticket describes it well (pre-flight, REVOKE statements, the two self-repairs, the operator text). It is undermined by B2: a default `public` schema would be refused before the first file. It is also untested for the `public` default.
- CHANGELOG about 900 words (CL:17) and docstring (78 lines): fate is stated (delete and replace, 1.5). Missing: where the new item is nested, and the tests that pin the old text (M3).
- Decisions the ticket already makes: exit code 5, error class outside `ConfigError`, message texts for steps 2, 5, 6, 8, parameter names `%(named)s`, `%(family)s`, `%(schema)s`.
- Decisions left to the builder that should be made here:
  - circular-import resolution (M6);
  - `PROBLEM_KINDS` words;
  - `Problem.line()` phrases for the 13 object kinds and for flag and membership problems;
  - `file_name` at step 6;
  - how to build main's state for the upgrade test;
  - CI max_prepared_transactions route;
  - fixture variants for the database-owner cases.

## E. Questions a builder would have to ask

1. What does commit 1 look like given `changed`/`kept` inputs? Which kept tests may fail until commit 3?
2. Is everyone's USAGE on the schema of the run (the `public` default) allowed?
3. Do I drop the connection option at step 8, or change `plain_role_connect`? Does any step-8 failure become `AppliedNotVerifiedError`?
4. Is each test case run in its own database? How does the oracle get a superuser (and fail if it cannot)?
5. How do I rewrite the CHANGELOG-pinning tests and the ~10 fake-db wiring tests and test_k2? What happens to MT1 and MT2?
6. Where exactly do `_label` and `REVIEWED_DEFINER_FUNCTIONS` live?
7. What is the full text of Q2 and the step-4 query, and the list of `PROBLEM_KINDS`?
8. Which rights are allowed per (named role kind, relation kind), and how does the missing-USAGE check run without `has_*_privilege`?
9. What are the test ids behind acceptance items 4, 6, 8-10, 13-17 and 20-22?
10. How are the mutants batched under heavy_slot (about 40-50 min), and how is the work split into 60-minute time boxes?
11. How is "main's state" built for the upgrade test?
12. How is the CI container started with `max_prepared_transactions` above 0?

## F. What I did not check

- PostgreSQL behaviour of any SQL (no server run). Q1-Q4 syntax was read, not executed.
- Whether `store/postgres.connect` passes `options=` through its `**extra`, and `.github/ci.yml` lines.
- The design review r13-design-zoomout-full.md beyond its headings and the sections quoted.
- The wiring and k2 fake-db tests' scripted answers in detail. I counted `mig.connect` patches and `migrate()` calls but did not read each body.
- Mutant killers for non-listed ids beyond a grep for retired test names and deleted-code names. Some of the 188 "outside the changed regions" may still reference deleted code.
- TICKET-P3a.md, BUILDER-ticket-notes.md, handover/ files (not in the snapshot), r12 reviews and evidence files.
- Whether the 280 vs 288 mutant difference is a helper-built-entry effect (279 literal `Mutant(` plus helpers).
- Facts 1-29 (author's PostgreSQL runs). I only checked the ones that touch the code (9, 11, 13, 17) against code comments.

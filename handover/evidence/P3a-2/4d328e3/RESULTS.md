# P3a-2 independent evidence — head 4d328e3

EVIDENCE RUNNER (record only, no judgement). Model: Fable 5.2.
Branch `core/P3a-2-clean`, head `4d328e3d68c6b9f132e7a0777210b956f6f79339` ("P3a-2 round 12: mutant SD3 plants the new result type").
Previous reviewed head: `8382bdd5b0e356bb794800f8c05f7dfa88ed0229` (branch `core/P3a-2-rewritten`).
Subject: `src/hadavin_sdk/store/migrate.py` — the database-migration runner / role-rights read-back. Security path.
Run started 2026-11-11 15:37Z. Server for every database probe: **PostgreSQL 16.15** (Ubuntu), my own cluster, port 56170, `initdb -E UTF8 --locale=C.UTF-8`, trust auth on 127.0.0.1, `max_prepared_transactions=10`. PostgreSQL 17 and 18 are **not installed on this machine** (only `/usr/lib/postgresql/16`), so they were not tested.
Env guard on every test/probe command: `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`. venv `/home/user/build/venv-evp3a2r12`, `uv sync --all-extras --group test` rc=0.

## FAILURES AND NOT-RUN FIRST
- **No failures in any run on the head.** Full suite, lint, format, bandit, scan_repo, stage-mutants, step-5 lock/prepared subsets, gitleaks: all exit 0.
- **Whole mutant list (`tests/migrate_mutants.py`, step 3): finished, rc=0.** Final line **`288 of 288 killed`**, printed counter line **`not killed: []`** — **0 SURVIVED / BROKEN / ERROR**. Duration ~20 min (15:52Z→16:12Z) through heavy.sh.
- **Not run:** nothing of the assigned work was dropped. The split-word dynamic-SQL second pass of probe 6c that I began earlier was interrupted by a safety classifier and not retried; its substance is covered by the step-9 F1/F2 route probes (which use exactly that `'CRE' || 'ATE ...'` split) and by the `_dynamic` wrapper rows already in probe 6c.

## Step 1 — full suite once on the head (through heavy.sh)
CI marker selection copied from `.github/workflows/ci.yml` line 92: `pytest -q -m "not live and not perf" -rs`. My command: `pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml=... -rfEs`.
- **rc = 0.** Duration 368.05 s (0:06:08). From the JUnit XML: tests=11015, **failures=0, errors=0, skipped=1**.
- Only skip: `tests/contracts/test_llm.py::...test_a_malformed_answer_is_a_provider_error[bedrock]` — reason "Stubber refuses a malformed Converse shape before the kind sees it" (an intentional, non-migration skip; unrelated to this branch). No failing test, so no per-file rerun was needed. Raw: `full-pytest.log`, `full-junit.xml`, `full-times.txt`.

## Step 2 — static gates
| gate | command | rc | result |
|---|---|---|---|
| ruff check | `uv run --all-extras --group test ruff check` | 0 | All checks passed |
| ruff format | `ruff format --check` | 0 | 331 files already formatted |
| bandit | `uv run --with bandit bandit -ll -r src tools` | 0 | 0 issues at -ll (metrics: Low 12, Medium 0, High 0; no `>> Issue` lines) |
| scan_repo | `python tools/scan_repo.py` | 0 | no output lines (clean) |
| stage mutants | `python tests/stage_mutants.py` (heavy.sh) | 0 | `37 of 37 good; problems: []` |
- **Suppressions added in the diff** (`git diff origin/main...4d328e3d | grep -nE '^\+.*(noqa|nosec|type: ignore|pragma: no cover|pytest.mark.skip|xfail)'`): **8 hits, none are a suppression of a check.** All 8 are in the test that *forbids* skips (`test_migration_rules.py`): a `pytest.mark.skipif(not DSN...)` guard added for the postgres tests, plus the literal strings `importorskip`/`xfail`/`skip` inside that guard-test's own data. Full list: `suppressions.txt`. No `# noqa`, `# nosec`, `# type: ignore` or `pragma: no cover` was added to product code.

## Step 3 — whole mutant list (`tests/migrate_mutants.py`, heavy.sh)
Command: `uv run --all-extras --group test python tests/migrate_mutants.py` (heavy.sh). Baseline killer run passes first (the script requires it). **288 mutants, all KILLED; final line `288 of 288 killed`, counter line `not killed: []`, rc=0.** No SURVIVED/BROKEN/ERROR. Duration ~20 min. Raw: `migrate-mutants.log`, `migrate-mutants-times.txt`.

## Step 4 — fail-before (head tests vs old source 8382bdd)
Clean worktree of `8382bdd`; overlaid ONLY the six head test files (`test_migration_postgres.py`, `test_migration_rules.py`, `test_migration_wiring.py`, `test_k2_migrations.py`, `test_migration_compare.py`, `migrate_mutants.py`). `hadavin_sdk` imported from the **8382bdd** source (`PYTHONPATH=<8382bdd>/src`, `uv run --project <head> --no-sync`). No extra conftest/helper overlay was needed (conftest and `tests/fixtures/*` already resolve from 8382bdd; the fixtures the new tests use exist there).
- **Import/collection:** `tests/test_migration_compare.py` fails at COLLECTION on 8382bdd: `AttributeError: module 'hadavin_sdk.store.migrate' has no attribute '_FUNCTION_FIELDS'` (head added it). So all compare tests are "not collected" against the old source — recorded as ERROR, not a pass. I reran with `--continue-on-collection-errors` to get the rest.
- **Result on old source: 68 failed, 1 collection error, 490 passed** (559 collected after the one uncollected file). So **69 of the new migration tests do not pass on 8382bdd** — they are genuinely fail-before. Breakdown of the 69: test_migration_postgres 51, test_migration_rules 12, test_migration_wiring 5, test_migration_compare 1 (whole-file collection error). Full per-test list with the first assertion/error line: `fail-before-failures.txt`. The 490 that PASS on the old source: `fail-before-passes.txt` (test_migration_postgres 179, test_migration_rules 143, test_migration_wiring 113, test_k2_migrations 55).
- Sample fail-before first lines: owner-text rules `ALTER TYPE rename OWNER TO r` etc. return `[]` on old source (12 `test_handing_an_object...`/`...holds_under_noise` cases); `DID NOT RAISE ConfigError` for the "no right outside the grant map" and default-privileges cases; `too many values to unpack (expected 2)` for the ownership-handover prints (head widened a return tuple); `test_a_prepared_transaction...` regex did not match (old message said "a session this login cannot see").

## Step 5 — second server configuration (`max_prepared_transactions`)
Restarted my own cluster with `max_prepared_transactions=0`, ran `tests/test_migration_postgres.py -k "prepared or lock"` (9 tests), then restored 10 and reran.
- **mpt=0: 9 passed, 221 deselected, rc=0** (incl. `test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one`, which handles the mpt=0 default internally). Raw `step5-mpt0.log`.
- **mpt=10 (restored): 9 passed, rc=0.** Raw `step5-mpt10.log`. Cluster left at `max_prepared_transactions=10`.

## Step 6 — catalog probes (verbatim psql in `probe-6ab-psql.txt`; package probes in `probe-6c-states.txt`)
- (a) `CREATE FUNCTION f() ... RETURN 1;` → `prosrc` is empty (not null), `prosqlbody IS NOT NULL = t`, `pg_get_function_sqlbody` = `RETURN 1`. An SQL-standard-body function carries its body in `prosqlbody`, not `prosrc`.
- (b) `ALTER DEFAULT PRIVILEGES ... GRANT EXECUTE ON FUNCTIONS TO x` globally → one `pg_default_acl` row with `defaclnamespace=0` (no schema); again `IN SCHEMA s` → a second row with the schema oid. Both shown. `DROP OWNED BY` removes them.
- (c) Package entry point used by the tests: **`hadavin_sdk.store.migrate.migrate(dsn, runtime_role=<named role>)`**, with `store.migrate.connect` swapped for `tests/fixtures/migration_role.plain_role_connect` (the superuser login is turned into a plain migration login role that owns the scratch schema), exactly as `tests/conftest.py` does; planted files via the tests' `_with_files`; roles via `_create_roles` / `_let_the_plain_role_belong_to` / `_let_the_plain_role_grant`. States built and the recorded outcome (ACCEPTED = migrate applied; REFUSED = ConfigError, nothing kept — full messages and the catalog read after each in `probe-6c-states.txt`):

| state | built via | run outcome |
|---|---|---|
| named role EXECUTE on a plain function in the run schema | plain file | REFUSED — plain file: text guard "statement the guard does not read: CREATE FUNCTION..."; via `CREATE OR REPLACE` (P01) REFUSED at the read-back "a role named in this run gets no right outside the grant map" |
| named role USAGE on a new sequence in the run schema | plain file | REFUSED (sequence not in grant map / text guard) |
| named role USAGE on the package's own sequence `approval_decisions_seq_seq` | plain file | **ACCEPTED** (that sequence is in the grant map; ACL after shows the named role with U) |
| SECURITY DEFINER fn owned by a role the migration role is a MEMBER of, same schema | pre-made | REFUSED — read-back names the SECURITY DEFINER fn "no file made or changed it; the migration role or a role it belongs to owns it" |
| SECURITY DEFINER fn in ANOTHER schema owned by a role the migration role is a member of | pre-made | **ACCEPTED** (C03o) — not in the run's own schema and owned by that other role |
| SECURITY DEFINER fn in ANOTHER schema owned by the migration role, made in the file | plain file | REFUSED (text guard); made BEFORE the run (C04p) → **ACCEPTED** |
| fn whose only change is `ALTER FUNCTION ... SET search_path = public` (step 2) | 2-step plain file | **ACCEPTED** (C05: proconfig = search_path=public after) |
| the package's own trigger fn `ALTER FUNCTION hadavin_audit_append_only() SET search_path = public` | 2-step | REFUSED — "migration ... changed a trigger: ... function settings" |
| fn whose only change is `ALTER FUNCTION ... OWNER TO` another role | 2-step | REFUSED — step-1 setup gives that role CREATE on the schema → read-back refuses; step-2 text rule "ALTER ... OWNER TO" also refuses |
| table in the run schema owned by a 3rd role that grants SELECT to the named role (before the run, and via a 2nd session) | pre-made / 2nd session | REFUSED both ways — "the runtime role has more than the grant map ... can SELECT ... (not in the grant map)" |
| foreign table (postgres_fdw) made in the file ± grant | plain file / `_dynamic` | REFUSED (text guard "CREATE FOREIGN TABLE"); via `_dynamic` also REFUSED |
| materialized view made in the file ± grant | plain file / `_dynamic` | REFUSED — "(view) is created by a migration but is not in GRANTS" |
| partitioned table with a partition in another schema ± grant on the partition | plain file / `_dynamic` | REFUSED — parent "not in GRANTS" / text guard |
| column-level `GRANT SELECT(col)` to the named role on a table outside the grant map | plain file / `_dynamic` | REFUSED — "(table) is created by a migration but is not in GRANTS" |
| a role granted membership in the named role during the run (`GRANT named TO other`) | plain file / `_dynamic` | REFUSED — plain: "GRANT without ON: the guard cannot read"; `_dynamic`: read-back "a role membership changed ... has a new member" |
| `ALTER DEFAULT PRIVILEGES FOR ROLE <member-of role> IN SCHEMA s GRANT SELECT ON TABLES TO named` | plain file / `_dynamic` | REFUSED — plain: text guard "ALTER DEFAULT PRIVILEGES"; `_dynamic`: read-back "gets SELECT on every new table that <role> makes ..." |
| `GRANT SELECT ON audit_entries TO named WITH GRANT OPTION` (grant-map table) | plain file | **ACCEPTED** (named role is a runtime role; grant-map table) — but `TO <other, unnamed> WITH GRANT OPTION` (C14o) REFUSED |
| large object made in the file, granted to the named role / to PUBLIC | plain file / `_dynamic` | plain file REFUSED (text guard "GRANT on ... LARGE"); via `_dynamic` **ACCEPTED** (D15) — large-object rights are not read back (see F4) |
| domain / enum type USAGE to the named role | plain / `_dynamic` | REFUSED (text guard "GRANT on ... DOMAIN/TYPE") |
| `GRANT CREATE ON SCHEMA <run schema> TO PUBLIC` | plain / `_dynamic` | REFUSED (text guard "GRANT on ... SCHEMA") |
| RLS on + policy for the named role on a grant-map table | plain / `_dynamic` | REFUSED (text guard "CREATE POLICY") |
| 2nd session commits an unrelated table in another schema while a file waits | 2nd session (slow file) | **ACCEPTED** — unrelated change does not stop the run |

## Step 7 — owner-text rule (`migration_numbers.refused_statements`, `probe-7-owner-text.txt`)
Criterion: the statement is treated as an owner-handover when any returned reason contains `OWNER TO`.
| input | refused as OWNER TO? | returned reason |
|---|---|---|
| `ALTER TABLE t OWNER TO r` | YES | ALTER ... OWNER TO |
| `ALTER TABLE t RENAME owner TO x` | no | [] |
| `ALTER TABLE t RENAME COLUMN owner TO x` | no | [] |
| `ALTER TYPE rename OWNER TO r` | YES | ALTER ... OWNER TO |
| `ALTER TABLE "RENAME" OWNER TO r` | YES | ALTER ... OWNER TO |
| `ALTER TABLE t RENAME TO owner` | no | [] |
| `alter table t owner/**/to r` | YES | ALTER ... OWNER TO |
| `ALTER TABLE t OWNER TO CURRENT_USER` | YES | ALTER ... OWNER TO |
| `REASSIGN OWNED BY a TO b` | no (but refused) | "REASSIGN OWNED: the guard cannot read what this statement does" |
| `ALTER TABLE t RENAME owner TO x; ALTER TABLE t OWNER TO r` | YES | ALTER ... OWNER TO |
| `DO $$ ... EXECUTE 'ALTER TABLE t OWNER TO r' ... $$` | no (but refused) | "DO: the guard cannot read ..." |
| `ALTER TABLE t\nOWNER\nTO r` | YES | ALTER ... OWNER TO |
| `COMMENT ON TABLE t IS 'owner to r'` | no | [] |
| `ALTER SCHEMA s OWNER TO r` | YES | ALTER ... OWNER TO |
| `ALTER FUNCTION f() OWNER TO r` | YES | ALTER ... OWNER TO |

## Step 8 — gitleaks
- `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..4d328e3d"`: rc=0, 51 commits, **0 findings**. Raw `gitleaks-git.log`/`.json`.
- `gitleaks dir --redact --no-banner --exit-code 0 <handover/evidence/.../4d328e3>`: rc=0, **0 findings** (so nothing was moved to evidence-raw). Raw `gitleaks-dir.log`/`.json`.

## Step 9 — route probes for review findings F1,F2,F3,F4,F5,F7 (`route-probes.txt`)
Built with the tests' own helpers and the real `migrate` entry point; plain migration role unless the finding needs another precondition. **These are recorded observations, not a verdict.**
| finding | precondition met? | run result | catalog fact after the run |
|---|---|---|---|
| **F1** deferred constraint trigger on `schema_migrations` runs `GRANT ALL ON audit_entries TO PUBLIC` at COMMIT (SQL verbatim, split-word `CRE`||`ATE`) | yes (plain role) | **ACCEPTED** — `0006_f1` in the ledger | `audit_entries` relacl now holds `=arwdDxt/<migrator>` → **PUBLIC has ALL** on audit_entries; trigger `late_t` present |
| **F2** plain `AFTER INSERT FOR EACH STATEMENT` trigger on `schema_migrations` runs `ALTER TABLE audit_entries DISABLE TRIGGER USER` (verbatim, and a split-word variant) | yes | **ACCEPTED** both ways — `0006_f2` applied | `audit_entries_append_only` and `audit_entries_no_truncate` tgenabled = **'D' (disabled)**; `after_ledger` present |
| **F3** a SECURITY DEFINER fn added to an extension (`ALTER EXTENSION citext ADD FUNCTION door(text)`) | **NOT MET** | file with `CREATE EXTENSION` REFUSED at the text guard ("CREATE EXTENSION: the guard cannot read"); and the migration role can never own `citext`: a trusted extension installed by a non-superuser is owned by `postgres`, and `ALTER EXTENSION ... OWNER TO` is a syntax error in PG16 | (extension/door not created) |
| **F4** large object granted to PUBLIC by dynamic SQL (verbatim) | yes | **ACCEPTED** — `0006_f4` applied | large object lomacl now `=rw/<migrator>` → **PUBLIC has SELECT,UPDATE** on the large object (large-object rights are not read back). Database-ACL half: a migration role owning a throwaway database was not built inside the one-database scratch model — NOT RUN for that half; P5 shows database-ACL deps are shared rows (dbid=0). |
| **F5** a named (runtime) role that is itself a MEMBER of a powerful role is accepted | yes (schema owned by the migration role) | **ACCEPTED** for all three: member of a SUPERUSER role (WITH INHERIT FALSE), member of `pg_execute_server_program`, member of `pg_read_server_files` — same as the no-membership control | files applied; the run checks the named role's own flags, not its memberships |
| **F7** scope uses the switched-to role; login L member of M, `options=-c role=M` | yes (schema owned by M) | **ACCEPTED** — `current_user=M`, `session_user=L`; the run proceeded and applied the real files | — |
(An earlier F5/F7 attempt stopped on a schema-grant setup artifact when the schema was owned by the superuser instead of the migration role; the corrected run above is the one recorded. Both raw files kept: `step9-f5f7.txt` = first attempt, `step9-f5f7-v2.txt` = corrected.)

## Addendum 2 — design probes (plain PostgreSQL 16.15 facts; `design-probes.txt` + raw)
One-line each (full text and verbatim psql in `design-probes.txt` / `design-probes-*.txt`):
| id | observed |
|---|---|
| F8 | a non-superuser `CREATE TEMP TABLE pg_class` **shadows** the unqualified name (count 0 vs 416; `'pg_class'::regclass` resolves to the temp); `SET search_path = pg_catalog, pg_temp` restores the catalog (416, regclass=catalog) |
| P1 | temp `pg_roles`/`pg_namespace` likewise shadow (a later `FROM pg_roles` returned the empty temp table); a temp FUNCTION `has_table_privilege` did **not** win — PG searches `pg_temp` **last** for functions/operators (the built-in's "role x does not exist" fired) |
| P2 | `SET CONSTRAINTS ALL IMMEDIATE` fires an already-queued deferred constraint trigger at once; a constraint trigger created AFTER the SET and queued later fires at that statement (immediate mode is transaction-wide), not at COMMIT |
| P3 | after the SET, a newly created+queued deferred constraint trigger fired at its INSERT (before COMMIT); an `ON COMMIT DROP` temp table dropped silently at COMMIT with no user code — no user trigger code observed at COMMIT in an already-immediate transaction |
| P4 | `GRANT boss TO r WITH INHERIT FALSE`: `has_table_privilege(r,tbl,SELECT)=false`, `pg_has_role MEMBER=true`, `USAGE=false`, `SET=true`; r may `SET ROLE boss` then SELECT |
| P5 | ownership → `pg_shdepend` deptype `o` (pg_class/pg_proc/pg_namespace/pg_type/pg_default_acl×2); ACL grantee → deptype `a` (pg_class, pg_proc, pg_namespace, pg_type, pg_language, pg_largeobject, pg_default_acl×2); **database** owner/grantee rows use classid `pg_database` with **dbid=0 (shared)** — a current_database() filter misses them |
| P6 | 14 pg_catalog tables (relkind r) carry an `aclitem[]` column: pg_attribute, pg_class, pg_database, pg_default_acl, pg_foreign_data_wrapper, pg_foreign_server, pg_init_privs, pg_language, pg_largeobject_metadata, pg_namespace, pg_parameter_acl, pg_proc, pg_tablespace, pg_type |
| P7 | fresh role defaults: db CONNECT=t, TEMP=t, CREATE=f; public schema USAGE=t, CREATE=f; fresh fn EXECUTE=t, fresh type USAGE=t, plpgsql=t, sql=t; a non-superuser CAN `ALTER ROLE <itself> SET search_path = evil, pg_catalog` and a new session then shows it |
| P8 | with that role default in force: `options=-c search_path=pg_catalog` → `pg_catalog` (per-connection option overrides the role default); plain session → `evil, pg_catalog`; a first `SET search_path = ...` in the session overrides the role default |

## Housekeeping
Worktrees made: `/home/user/build/EV-P3a2-4d328e3` (head), `/home/user/build/EV-P3a2-8382bdd` (old source for fail-before). My Postgres cluster: `/home/user/build/pg-evp3a2r12` port 56170. venv `/home/user/build/venv-evp3a2r12`. All removed at the end of the run (see hand-back). Every throwaway role/schema/database/large-object/extension made by a probe was dropped in the probe's own cleanup.

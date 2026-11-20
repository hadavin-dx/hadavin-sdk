# B review 7: fresh re-read of the merge (who-else round 3 + B5c) and of B5c, branch cloud/core-b

Reviewer: fresh, read-only on source. Tests run once, no parallel workers:
`tests/test_step_b_e5c_role_settings.py tests/test_step_b_e5c_units.py tests/test_step_b_e5_search_path.py` -> `22 passed` (PG16 test server). Plus a 6-statement psql experiment with one throwaway role and schema (dropped again; no leftovers, checked).

Verdict: CLEAN (nothing above Minor). No Blocker, no Major. 3 Minors, 2 Nits.

## 1. The merge

- migrate.py `migrate()` (599-755): both feature sets are present and combined. Signature has `release_role`, `no_roles`, `accepted_admin_roles`, `on_role_change` (:610-619). Validation order is sound: role-name check, duplicates, `no_roles` with a named role (:643), accepted-name check, `accepted` without named roles, overlap of accepted with named, ledger, then the "no role named and not no_roles" refusal (:669). `release_role` is in `roles`, `named`, the membership loop, `_apply_grants`, `effective_problems`, `_apply_release_function` (others = named minus release), and therefore in `check_role_settings`/`check_maintain` (both take `named`).
- `_LOG` (logger `hadavin_sdk.store`, :22) and `_log` (`hadavin_sdk.migrate`, :24) are both defined and each used once, as intended: `_log.warning` for role-setting changes (:735, matching the docstring "logged (`hadavin_sdk.migrate`)"), `_LOG.warning` for the accepted admin roles (:740, matching "logger `hadavin_sdk.store`"). No other use of either.
- Order in the transaction: grants -> release function -> portal -> (if named) `check_role_settings`, `check_maintain` -> accepted-roles warning -> `who_else_can_clear(db, reset_role, accepted)` (:731-755). Arguments are right (`accepted` is the validated tuple). Reasonable: role-setting repair and MAINTAIN revoke happen before the final who-else listing, and any refusal rolls the whole transaction back. The accepted warning is logged even if who-else then refuses; harmless.
- cli.py: flags `--accept-admin-role` (append, default []), `--no-roles`, `--release-role` all exist (:124-150) and the usage text (:18-20) lists them. The call at :185-194 passes `cfg, runtime, portal, purge, reset, release, no_roles, tuple(accepted)` POSITIONALLY; I checked it against the `_migrate` signature (:418-427: cfg, runtime_role, portal_role, purge_role, reset_role, release_role, no_roles, accepted_admin_roles): the order matches, so every argument lands in the right parameter. `_migrate` then calls `migrate()` entirely by keyword (:450-464). See Nit N1.
- CLI behaviours checked: `--no-roles` with a role -> migrate's ConfigError (exit 2 through `main`); accepted without roles -> ConfigError; `on_role_change` prints `changed: ...` on stderr; accepted roles are printed on stdout.
- docs/stop-state-runbook.md (:5-16, 80-115, 142) and SECURITY.md (:30-38) match the code after both changes: no-role migrate is refused unless `--no-roles`; `--accept-admin-role` rules (plain name, not a granted role, left out of the CREATEROLE listing only, printed and logged, no effect from PG16); release role in the command at :142. CHANGELOG:24-25 and SECURITY.md:37 (the stale text of review 6, R6-1) are fixed.

## 2. B5c against B-review-6

R6-1 closed: CHANGELOG "Breaking: search_path, role names and `--no-roles`" (CHANGELOG.md:~37-58) has ordered upgrade steps. Checked each statement against code: refusal at start for runtime/purge/reset/release logins; stock `"$user", public` login unchanged; `db_schema` is only the expected schema; `app,\ public` escape (the pin parser accepts it: ran `_PIN`/`names_of`); migrate reset/override/print/log behaviour; exit 2 with no role; MAINTAIN revoke and `pg_maintain` refusal (PG17+, untested here); `lock_timeout` set on the store connection (postgres.py:281). Accurate.

R6-2 closed (migrate.py:436-488). Verified on the server:
- PostgreSQL precedence confirmed: role `r` with role-wide `search_path=decoy` and `IN DATABASE hadavin_test SET search_path=public` connects with `public`; `current_schemas(false)` and `SHOW` follow the in-database row. With a mixed-case schema (`"Ap p"`) the stored row is `search_path="Ap p"` and a new connection shows it, so `names_of` on the read-back compares equal to the schema.
- Role with BOTH a role-wide decoy and an in-database decoy: both rows are effective, `wide` contains the role, the in-database row is skipped (:461) and overwritten by the `SET` (same row, same key) -> one statement, one note. Correct.
- Role-wide decoy plus in-database row already = schema: role-wide row is shadowed (`_effective_rows` :424-433) and left alone. Correct. In-database decoy plus role-wide row = schema: the in-database row is RESET and the role-wide row (= schema) takes over. Correct.
- Read-back (:483-487): `_effective_rows(_path_rows(...))` must be empty, else ConfigError. Correct, including the shadow rule.
- Roles not named are never touched (SQL filter on `rolname = ANY(named)` plus `setrole = 0`); rows of other databases excluded (`d.datname = current_database()`); `setrole = 0` rows refused.
- InsufficientPrivilege -> ConfigError naming role, old value, schema and the manual statement (:477-483); covers both the RESET and SET statements; the whole transaction rolls back (nothing half-applied). Exit 2 via `main`; unit test present.
- `names_of` (postgres.py:177-186) run on: `app`, `"$user", public`, `"A,b", c` (comma inside quotes kept), `App,Public` (folded), `"a""b"` (doubled quote), `"x" , "Y"`, empty and `  ,  `, `public,pg_catalog,pg_temp` (-> `public`). All as the server reads them. Malformed input (`"a,b`, `a b`) is tolerated, not rejected: harmless, the server would reject it and `verify_schema` compares against the live value anyway.
- `_PIN` (postgres.py:173): `-c search_path=app,public -c x=1` -> `app,public`; `-c search_path="A b" --x=1` -> `"A b"`; `-csearch_path=app` and `--search_path=app` accepted; a space after the comma works once libpq unescaped it (`expected_schemas` removes the backslashes first). See Minor M2 for the multi-pin case.
- `quote_ident` regclass (`_holds`, :512-520): `(quote_ident(schema) || '.' || quote_ident(table))::regclass`, resolves capitals/quotes/dots; unit test present. The `REVOKE MAINTAIN` uses `sql.Identifier` for both parts. Correct.
- CHANGELOG 'Breaking' entry: accurate (see above). One wording point in M3.

## Findings

### Minor

**M1. A database-wide search_path row is refused even when every named role is pinned past it** (migrate.py:452-458). PostgreSQL applies role-in-database over the database-wide row, so a named role that has an in-database (or just repaired) row `= schema` is unaffected by `ALTER DATABASE x SET search_path = app`. Migrate still raises "a database-wide ... default reaches the named roles" for it, and `_effective_rows` does not model the shadowing for `setrole = 0` rows the way it does for role-wide rows. Scenario: the old runbook's `ALTER DATABASE x SET search_path = app` with `app` != the migrated schema while all logins carry in-database pins: migrate refuses although the logins are safe. Safe direction (false refusal, actionable message). Also: the loop raises on the first `setrole == 0` row after earlier ALTERs, which roll back with the transaction, so nothing is half-applied.

**M2. `_PIN.search` takes the FIRST `search_path` option of the DSN options, the server applies the LAST** (postgres.py:200). `options=-c search_path=decoy -c search_path=app` gives expected `[decoy]` while the effective path is `app`: a false refusal at start (safe; `verify_schema` compares with the live value). Related: `-c search_path=a -csearch_path=b` is read as one value `a -csearch_path=b`. Rare; no safety effect.

**M3. CHANGELOG/runbook say migrate "refuses (exit 2) and names the role" when ALTER ROLE lacks the privilege; that is true, but the same refusal is also raised for the in-database RESET of a decoy row**, which the text describes only for the role-wide case. Wording only, the message itself is correct (CHANGELOG ~line 51-55; runbook :109-113). Also the runbook sentence "`PGOPTIONS` in the environment overrides a DSN-less path and is refused the same way" (runbook ~:115) was not verified by a test.

### Nit

**N1. Positional call of `_migrate` from `main` (cli.py:185-194).** Correct today (checked against the signature), but eight positional arguments with five optional `str | None` of the same type invite a transposition on the next added role. Passing them by keyword (`runtime_role=args.runtime_role, ...`) costs nothing.

**N2. If `current_schema()` is NULL, `check_role_settings` would build `sql.Identifier(None)`** (migrate.py:466-468, schema is None) and fail with a TypeError (exit 3) instead of the ConfigError `_check_stop_relations` gives later (:333-360). Effectively unreachable: with no usable schema the migration files themselves fail first, unless all are already applied and a role-wide row exists. Running `_check_stop_relations` first in the named branch would close it.

## Not run
PG17 `MAINTAIN` paths (server is PG16; the real-server test is skipped here, runs in CI on postgres:17). No live model calls, no secrets, source untouched, no commit.

## Disposition (core-b)
CLEAN. Minors M1 (database-wide search_path row refused even when every named role is pinned past it), M2 (`_PIN` takes the first `-c search_path`, the server applies the last), M3 (the privilege refusal text covers the role-wide case only; the PGOPTIONS sentence is untested) and Nits N1 (pass the migrate arguments by keyword in `main`), N2 (NULL current_schema) are recorded as stated limits; M1 and M2 refuse in the safe direction. Fix with the next change to migrate.py/cli.py (the lead's who_else round 4 will touch the same files: avoid two builders on them).

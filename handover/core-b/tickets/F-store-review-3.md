# F-store review 3: release of expired spend holds (ORDER 020), fresh hostile reviewer

Scope read: migrations/0008_release_expired_spend.sql, store/migrate.py, store/postgres.py (release_expired_spend,
settle), store/protocol.py, cli.py (release_expired_cmd, dispatch), limits.py, backends/table.py, app.py,
tests/test_release_expired_spend_pg.py, tests/test_release_minors.py, docs/stop-state-runbook.md.
Run: tests/test_release_expired_spend_pg.py once, no parallel workers: 40 passed (49 s). One scratch script (in the
session scratchpad, outside the repo) built a World, migrated, and ran the exploit below; it dropped its schema and
roles afterwards. Source edited: none.

Verdict: NOT CLEAN. 1 Blocker, 0 Major, 5 Minor, 2 Nit.

## Blocker

### B1. The release login escalates to the function owner (here a superuser) through pg_temp shadowing
File: src/hadavin_sdk/store/migrations/0008_release_expired_spend.sql:12-17 (`SET search_path FROM CURRENT`, unqualified
`spend_reservations`, `spend`, `spend_month`).

`FROM CURRENT` only copies the migrate session's search_path (the test world: the bare schema name; production default:
`"$user", public`). It never lists `pg_catalog` first nor `pg_temp` last, so PostgreSQL searches the session's
temporary schema FIRST for relations. Every login can create temp tables (TEMP on the database is granted to PUBLIC),
and the release login is the one that may call the function.

Scenario, run for real against the test server (owner `postgres`, rolsuper = true, `proconfig = {search_path=<schema>}`):
as the release role: CREATE TEMP TABLE spend_reservations / spend / spend_month with the columns the function uses and
one matching row; CREATE FUNCTION pg_temp.evil() RETURNS trigger; CREATE TRIGGER ... BEFORE UPDATE ON
pg_temp.spend_reservations EXECUTE FUNCTION pg_temp.evil(); then `SELECT * FROM hadavin_release_expired_spend(...)`.
The function updates the temp table, the trigger fires inside the SECURITY DEFINER frame, and the trigger body read
`current_user = postgres`, `rolsuper = true`. So the role that was built to hold "EXECUTE on one function and the audit
append, and nothing else" runs arbitrary SQL as the migration owner (all money tables, role creation, the audit tables
that are otherwise append-only through the owner's triggers if the owner may drop them, and on a superuser owner the
whole server). All the "denied on every other relation" tests pass because they test the login directly, not through
the definer frame. The brief asked for a pinned, schema-qualified function: it is neither.

Same root, smaller: with `public` (or any schema in the stored path) writable by another role (PostgreSQL before 15, or
a grant), a planted `date_trunc(text, date)` overload wins overload resolution over the catalog `date_trunc(text,
timestamptz)` (exact match) and also runs as the owner.

Fix: pin the path to the catalog first and the temp schema last, with the real schema in the middle, e.g. the migrate
step runs `ALTER FUNCTION hadavin_release_expired_spend(text, date) SET search_path = pg_catalog, <current_schema>,
pg_temp` (the 0008 file cannot know the schema; or qualify every relation in the body via a `format('%I...')`
dynamic statement), and call functions as `pg_catalog.date_trunc`. Also consider `REVOKE TEMP ON DATABASE ... FROM
PUBLIC` in the runbook. Add a test: the release login creates the temp tables and trigger above; the call must not run
the trigger (or must fail), and `proconfig` must contain `pg_temp` last and `pg_catalog` first.

## Minor

### m-1. The release reference is compared by raw string, not by canonical form
src/hadavin_sdk/cli.py:497-506 (`ref in others`). `release_credential_ref = "DB-PASS"` against
`dsn_secret_name = "db_pass"`, `reset_credential_ref`, `purge_dsn_secret_name` passes the check, yet
secret_name.canonical_secret_name folds both to `db_pass` and the env or mounted_file provider resolves them to one
secret. Result: the command connects with the runtime (or reset, or purge) DSN. The database still refuses it
(EXECUTE is revoked from every other role, the function test proves it) so no money moves, but the "refused before any
connection" promise is false for the folded names, and the failure is reported as exit 2 "Is this the release role's
login?" Fix: compare `canonical_secret_name` of both sides (the same helper platform_secrets.check_senders uses). The
pre-existing reset check (cli.py:241) has the same raw comparison.

### m-2. The release secret is only protected from senders, not from the runtime's other secret names
src/hadavin_sdk/app.py:185-189. `release_credential_ref` (and `reset_credential_ref`) is added to the set that
`check_senders` compares canonically, but not to the platform/executor/read-tool overlap check
(`platform_secrets.check(secrets, backends, executor_names, extra_secret_names)`). A tool `secret_names`, a source
`token_secret_name`, an executor secret or `restored_hash_key_secret_name` that folds to the release ref is read by the
runtime process at start-up, so the runtime then holds the release DSN, against the docstring in backends/table.py:127
("never the runtime's login"). Impact is bounded (release only frees expired holds, audited) but the isolation claim
is not enforced. Not run; read from code.

### m-3. A failed outcome row is invisible to the operator
src/hadavin_sdk/store/postgres.py:794-807 `_write_outcome` swallows the exception and only logs
`release outcome not audited`; cli.py:541-545 then prints "released ..." and returns 0. Result: money counters lowered,
audit holds an intent row with no outcome, and the operator at the terminal is told everything is recorded. The
intent-first order itself is right (intent failure changes nothing, test covers it; a failed release writes
`release_failed`; a failed outcome after commit leaves a dangling intent). Fix: return a flag or raise a distinct
exception after commit so the CLI prints "released, but the outcome could not be audited: the intent row is the only
record" and exits non-zero (say 3), and put the dangling-intent meaning in the runbook. No test covers the
outcome-fails-after-commit case (grep of tests: only intent failure and runtime-login refusal).

### m-4. Limits.settle now always passes `agent_id=` to the store, which breaks stores with the old signature
src/hadavin_sdk/limits.py:188-196. `Limits.settle` -> `settle_for(None, ...)` -> `store.settle_spend(rid, usd,
agent_id=None)`. Before, `settle` called it positionally with two arguments. A custom Store written to the previous
protocol (the protocol comment promises optional pieces "so a custom store without it still starts") raises TypeError
on every settle, including from callers that never use m2. Fix: pass `agent_id` only when it is not None. Also,
nothing in src calls `settle_for` (grep: only the two definitions and `settle`), so m2 is not wired to the gate: the
cross-agent check exists but no caller uses it. The in-memory Budget/Limits tests pass because they call it directly.

### m-5. m3 clamp can still skip a NaN age
src/hadavin_sdk/runtime/tick.py (`reservation_expire_s`): `longest = max((stuck_after_s(...) ...))`. `max` with NaN
depends on order (`max([5, nan])` is 5, `max([nan, 5])` is nan), so a NaN stuck age on an agent after the first one is
silently ignored and that agent's reservations can expire early; inf and a lone NaN are clamped correctly. Fix:
validate each `stuck_after_s` (finite, else treat as MAX_EXPIRY_AGE_S) before taking max.

## Nit

### n-1. The counters silently stop at zero
0008 sql lines 36-41: `GREATEST(usd - total, 0)` hides a drift (counter lower than the expired sum) with no signal;
the CLI prints `released_usd` as the full sum while the counter fell by less. Return or audit the shortfall
(`total - (old - new)`), do not clamp quietly. The test names this behaviour, so it is a decision, not a bug.

### n-2. Month is derived with date_trunc on a date
0008 sql lines 26, 38, 43: `date_trunc('month', p_day)::date` goes through timestamptz in the caller's TimeZone; the
Python writer uses `day.replace(day=1)`. I checked every zone of the server for the first of every month 1970-2040: all
equal; the only deviation is a calendar day that a zone skipped (Kiritimati 1994-12-31), so no real hold is affected.
Plain date arithmetic would remove the dependence.

## Checked and found sound
- EXECUTE: revoked from PUBLIC in the file; migrate revokes from every other named role and refuses any named role that
  still has it by PUBLIC or membership (has_function_privilege); a roles-must-not-be-members check precedes it.
  Roles not named in the command are not checked (same scope as the existing grant checks).
- Live hold: the claim filters `status = 'expired'`; open rows, settled rows, other days and other agents are untouched
  (tests assert it).
- Double release and release racing a late settle: the claim sets status settled, so a second release matches 0 rows;
  settle's claim locks the row and re-reads status after the wait (READ COMMITTED), so one of the two wins and the other
  sees a settled row and changes nothing; both take row, day, month in that order (no lock cycle). Counters cannot go
  below zero (GREATEST) and cannot be lowered twice for one row. closed_at is kept, so the table CHECKs hold.
- Month ends: reserve books `day.replace(day=1)`, the function uses the month of p_day: same key (Jan 31 hold, Jan 30
  hold, tests use them).
- Dispatch: `release-expired` returns before the registry load and before any `limits` branch; release_expired_cmd
  has no path to limits.reset (test monkeypatches both).
- m5: Budget now refuses limit values the store refuses and refuses a zero reserve at the cap like `usd < cap`.
- Runbook: m1 window (kill switch then reserve is not one transaction) is stated; release section matches the code and
  warns that a billed call released is lost from the counters.

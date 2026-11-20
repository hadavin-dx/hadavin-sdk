# F-store review 4: release of expired spend holds (ORDER 020), after fix round 1, fresh hostile reviewer

Scope read: store/migrations/0008_release_expired_spend.sql, store/migrate.py (`_apply_release_function`, `migrate`),
store/postgres.py (`release_expired_spend`, `_write_outcome`), store/protocol.py (`SpendRelease`), cli.py
(`release_expired_cmd`), app.py (secret name checks), limits.py, runtime/tick.py (`reservation_expire_s`),
audit/chain.py (`write_intent`, `write_outcome`), the three test files, docs/stop-state-runbook.md.
Run once, no workers: `tests/test_release_expired_spend_pg.py tests/test_release_function_search_path_pg.py
tests/test_release_minors.py`: 74 passed (39.6 s). Scratch (outside the repo): /tmp/core-b-scratch-REL/probe.py and
probe2.py (World from the tests; each creates and drops its own schema and roles). Source edited: none.

Verdict: NOT CLEAN. 0 Blocker, 1 Major, 4 Minor, 1 Nit. The B1 hijack is fixed; the m-3 fix does not work against the
real audit.

## Major

### M1. Exit code 5 can never fire with the real audit chain: a lost outcome row is reported as success (exit 0)
src/hadavin_sdk/store/postgres.py:811-819 (`_write_outcome` returns False only when `audit.write_outcome` RAISES),
src/hadavin_sdk/audit/chain.py:298-318 (`write_outcome` "Never raises": on a failed append it tries the
`audit_outbox` INSERT, then falls back to the in-memory `_pending` list, and returns None), cli.py:558-564 (exit 5
branch), docs/stop-state-runbook.md:81-85 (promises exit 5).

Scenario, run for real (probe2.py): release login, real `chain` audit, `_append` made to fail from the second call on
(the intent succeeds, the outcome append fails after the commit). Result: `done.outcome_audited == True`,
`len(audit._pending) == 1`, `_outbox_dirty == False`. The release role has no INSERT on `audit_outbox` (migrate.py:70:
the grant has no `release=`), so the outbox fallback is refused and the event parks in memory; the CLI then exits 0
with "released ..." and the process ends, the parked outcome is lost, and the audit holds an intent row with no
outcome. That is the m-3 scenario of review 3, unchanged: the operator is told everything is recorded. The only test
of the exit-5 path (tests/test_release_minors.py, `test_the_outcome_failing_after_commit_exits_5...`) hands the CLI a
hand-built `SpendRelease(outcome_audited=False)` and a fake store, so it proves the print and the code but not that the
store ever produces `False`; no test makes the real `write_outcome` fail after the commit.
Fix: after `audit.write_outcome` look at what it did: it returns the key on success and None when parked, so
`audited = key is not None` (or, for the chain, check `not audit._pending and not _outbox_dirty`); keep the except
branch too. Add a Postgres test with the failing `_append` above that asserts exit 5 and the intent id on stderr.

## Minor

### m-1. The m-2 (secret-name overlap) test is a source grep and passes with the check deleted
tests/test_release_minors.py `test_a_tool_secret_that_folds_to_the_release_ref_stops_the_start`: it asserts only that
the strings "release_credential_ref" and "canonical_secret_name" occur in app.py's text. app.py:37 imports
`canonical_secret_name` and app.py:190 already names `release_credential_ref` for the sender check, so the test stays
green if the whole loop at app.py:195-203 is removed. No behavioural test exists (none builds an App with a tool
`secret_names` / source `token_secret_name` / executor / restored-hash secret that folds to the ref and expects
ConfigError). The code itself reads correct (canonical compare of the release and reset refs against
`extra_secret_names | executor_names`); NOT run. Also unchecked: the ref against the runtime's own backend secret
names (`dsn_secret_name`, the audit and LLM secrets in `b.entries()`); only the sender check sees them
(app.py:185-192). The CLI side (cli.py:502-517) compares dsn, reset and purge canonically, and that one has a
behavioural test (the m-1 canonical-form check is sound and tested: "PG.DSN" vs "pg-dsn", "R-X" vs "r_x").

### m-2. `settle_for` is still not called by anything in src
src/hadavin_sdk/limits.py:193 (also Budget at :105). `grep settle_for src`: only the definitions. The agent check
(ORDER 020 m2) therefore protects no real caller, the point already made in review 3 (m-4, second half). The first half
is fixed: `_settle` passes `agent_id=` only when given (limits.py:198-203), tested with an old-signature store.
Either wire the gate to `settle_for` or record in the ticket that m2 is built but unused.

### m-3. The pin tests are narrower than the claim
tests/test_release_function_search_path_pg.py. (a) Every case runs with a schema-only search_path (`World.scope`
sets `-c search_path=<schema>`); the default production path (`"$user", public`) and a migrate run with a second
schema after the first are not exercised. By reading, `current_schema()` is the schema `CREATE TABLE` used, so the pin
is right for any path, and the non-default-schema case (the one that matters) IS covered: proconfig in the run was
`search_path=pg_catalog, sb_s_<id>, pg_temp`. (b) `test_the_pin_survives_a_second_migrate` asserts only that some
entry ends in `pg_temp` (`cfg[0].endswith(...) or any(...)`); it would pass on the 0008 placeholder
`pg_catalog, pg_temp`, i.e. it does not prove the schema is re-pinned. Tighten it to the same three-part check as the
first test.

### m-4. Re-creating the function drops the pin until the next migrate (safe, undocumented)
0008 line 25 placeholder `SET search_path = pg_catalog, pg_temp`. I ran `CREATE OR REPLACE` with the 0008 body (probe.py):
proconfig became `pg_catalog, pg_temp`; the next `migrate` re-pinned it to `pg_catalog, <schema>, pg_temp`
(`_apply_release_function` runs on every migrate, after the migration loop, so the pin survives a later migration that
replaces the function). In between, the function cannot find the money tables, so it fails closed; it is not
hijackable. Say so in the runbook (a hand-run `CREATE OR REPLACE` needs a migrate afterwards), and add a test for it.

## Nit

### n-1. `ALTER FUNCTION ... SET search_path` fails if the migrating login is not the function owner
migrate.py:368-372. A second migrate run by another login (not the owner) gets "must be owner of function" with no
remedy text. Name the owner in the error, or document that migrate must always run as the owner.

## Checked and found sound

- B1 (pg_temp hijack): FIXED and the exploit test discriminates. In probe2.py I seeded temp copies of all three
  tables, a temp trigger function and a BEFORE UPDATE trigger, as the release login. With the old pin
  (`ALTER FUNCTION ... SET search_path FROM CURRENT`, proconfig `{search_path=<schema>}`, the old state) the call
  returned the planted temp row (1 reservation, 1 USD) and the trigger fired as `postgres`, rolsuper = true
  (`[('postgres', True)]`). With the new pin the same script returns (2, 3.00) from the real rows and `fired` is
  empty. The test in the repo (tables created without rows in `spend` / `spend_month`) fails on the old function too:
  the old call raises "spend counter row missing" from the temp table, so the assertion line is never reached
  (a failure by exception, not by the `fired` count; add the two INSERTs the probe uses if you want the `fired`
  assertion itself to be the one that fails).
- Other functions and operators the body calls: all are `pg_catalog` or syntax (`count`, `sum`, `COALESCE`,
  `GREATEST`, `=`, `-`, `<>`-free); `date_trunc` is explicitly `pg_catalog.date_trunc`; the types are exact
  (numeric, date, text) so a planted overload in a writable schema cannot win on a better type match and loses a tie
  because `pg_catalog` is first. The schema is second and pg_temp last.
- Pin applied for the right schema under a non-default schema: proconfig shows the test's own schema, from
  `current_schema()` of the migrating session, quoted with `sql.Identifier`.
- n=0 path, month math, applied_usd: `applied_usd = old_day - day_usd` from `FOR UPDATE` row and the clamped result;
  0 when no row matched. The outcome text carries `rows=`, `requested_usd=`, `applied_usd=`; the CLI prints both. The
  drift case has a test (counter below the sum stops at zero).
- m-1/canonical (CLI): behavioural, see Minor m-1 above. Reset check at cli.py:241 already canonical.
- NaN clamp (m3): `reservation_expire_s` now returns MAX_EXPIRY_AGE_S on any NaN before `max`, tested with NaN in
  second position; `-inf` would OverflowError in `math.ceil` but `call_timeout_s` is `gt=0` (NaN also fails `gt=0`), so
  config cannot produce it.
- settle vs settle_for: `settle` keeps the two-argument signature and passes no `agent_id`; `settle_for` passes it
  (see Minor m-2 for the unwired part).

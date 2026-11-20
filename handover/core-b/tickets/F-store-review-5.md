# F-store review 5: release of expired spend holds (ORDER 020), after fix round 2, fresh reviewer

Scope read: store/postgres.py (`release_expired_spend`, `_write_outcome`), store/migrate.py (`_apply_release_function`),
cli.py (`release_expired_cmd`), app.py (secret overlap), audit/chain.py and audit/local_dir.py (`write_outcome`),
docs/stop-state-runbook.md (release section), the three test files, the F-store-review-4 ticket.
Run once, no workers: `tests/test_release_expired_spend_pg.py tests/test_release_function_search_path_pg.py
tests/test_release_minors.py`: 78 passed (51.5 s). Mutation probe in a copy under the scratchpad (repo untouched):
deleting the app.py overlap loop makes both parametrized m-2 tests fail. Source edited: none.

Verdict: CLEAN (0 Blocker, 0 Major; 3 Minor, 1 Nit). M1, m-1, m-3, m-4, n-1 of review 4 are fixed; m-2 is recorded below.

## Minor

### m-1. Runbook paragraph order is broken: an inserted block splits a sentence
docs/stop-state-runbook.md:90-98. "Consider" (line 90) is continued by "`REVOKE TEMP ON DATABASE <db> FROM PUBLIC`"
only after the "hand-run CREATE OR REPLACE" and "Exit 5 is decided ..." paragraphs. The advice to revoke TEMP now reads
as part of the exit-5 explanation, and the "Consider" line has no object. Move the two new paragraphs below the
REVOKE TEMP / secret-name lines (or give the REVOKE advice its own sentence).

### m-2. `settle_for` is still wired to nothing in src (carried from review 4 m-2, 3 m-4)
limits.py:105 and :193; `grep settle_for src` finds only the two definitions. The agent check protects no real caller
until the gate (core-c) calls it. The ticket F-store.md:401 already says "the gate should call `settle_for` (request to
core-c)", so this is recorded, not hidden; not a defect of this command. Nothing in this round changed it.

### m-3. A parked outcome is reported as "could NOT be audited ... record by hand" even when it is durably parked and will land
src/hadavin_sdk/store/postgres.py:811-826, audit/local_dir.py:110-125, cli.py:558-564. `_write_outcome` maps every None
to False. For the chain with the release login that is right: the login has no INSERT on `audit_outbox`
(migrate.py:70, no `release=`), so the event goes to `_pending` in memory and is lost when the CLI ends. I read
`chain.write_outcome` (audit/chain.py:298-318): None only when `_append` raised and the event was parked; a
DuplicateEvent returns the event id (True), so a row already in the chain is not reported as lost. No code path in the
CLI process drains `_pending` afterwards (no atexit, no `close`), so for the chain None is always a loss. Not always
for `local_dir` audit: its None means the event was written to `outbox/<id>.json` (durable) and the tick's `reconcile`
writes it later. With a postgres store plus a `local_dir` audit the command would exit 5 and tell the operator to
record the outcome by hand, and the row then also appears on its own (a double record). Low odds (the release needs
the chain's tables for its grant model; `local_dir` with the postgres store is an unusual pairing) and exit 5 is the
safe direction. Either word the message "may be missing; check the audit for the intent id before recording it" or
let the audit report durable parking separately. Also: a commit whose reply is lost (the row is in the chain but
`_append` raised) is reported False; conservative, same wording fix covers it.

## Nit

### n-1. `release_failed` outcome loss is silent
postgres.py:772. The return of `_write_outcome` is ignored on the failure path (the warning is logged inside, which is
enough in the log, but the CLI prints "nothing was changed" and exit 2 with no hint that the `release_failed` row is
missing). Nothing changed in the money tables, so only the audit trail is short by one row; the intent row exists.

## Checked and found sound

- Exit 5 is truthful for the real chain: `test_a_lost_outcome_with_the_real_chain...` makes `_append` fail from the
  second call with the real `chain` (`outcome_audited is False`, `len(_pending) == 1`, counters changed, one intent row
  in the chain) and `test_the_command_exits_5_...` drives the CLI over the same, asserts exit 5 and the intent id on
  stderr. The except branch (an audit that raises) also returns False. Not reported False when written inline: the
  success path returns the key (a str); DuplicateEvent returns the id.
- The intent row failing changes nothing: `write_intent` is the first call (postgres.py:766), outside the `try`, so
  `AuditUnavailable` propagates, the function is never called (the cli maps it to exit 3, "Nothing was changed");
  `test_when_the_intent_cannot_be_written_nothing_changes` covers it with the real function and counters. A
  `DuplicateEvent` from the intent would go to exit 2 with the same "nothing was changed" text, also true.
- m-2 of review 4 is now behavioural: `test_a_secret_that_folds_to_the_release_or_reset_ref_stops_the_start` builds the
  app with a restored-hash key secret `Release.Login` against ref `release-login` and expects the ConfigError for both
  fields; it fails when the loop is removed (mutation run above). It covers one of the four sources named in the error
  (restored-hash); tool, source and executor names reach the same set expression (`extra_secret_names | executor_names`)
  so the same loop covers them by reading, not by test. Still unchecked: the refs against the runtime's own backend
  secret names (`b.entries()`); only the sender check sees those (app.py:185-192).
- Pin tests (non-default schema): every case runs in the test's own schema. `test_proconfig_...` and
  `test_the_pin_survives_a_second_migrate` now assert the exact `["pg_catalog", <schema>, "pg_temp"]`; the hand-run
  CREATE OR REPLACE test asserts the placeholder `["pg_catalog", "pg_temp"]` and the re-pin by `migrate`. The temp-trigger
  test now seeds counter rows so the old function would run to the end and the `fired` count would be what fails.
  `_apply_release_function` owner error (migrate.py:374-382) names the owner; the runbook says migrate must run as the owner.
- Release path unchanged otherwise: transaction, `applied_usd`, canonical ref compare in the CLI (`PG.DSN`, `R-X`/`r_x`),
  refusals before any connection, the settle signature pin.

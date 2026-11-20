# review-code-AB-3 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

RESULT REVIEW, cloud/core-b, steps A, B (without who_else_can_clear) and C. Read-only. I had no shell, so I did not run any test, mutant, lint or PostgreSQL, and I could not read git log or the head SHA.

COUNTS: Blocker 0, Major 2, Minor 4.

Earlier items I checked and found fixed in the code (not re-reported):
- A-1: non-outage append failures are counted and reconcile raises, chain.py:308-349. Tests exist at test_audit_drain.py:670 and :986.
- A-2: refused events are moved aside, chain.py:261-290.
- A-4: a failed delete is counted and the loop continues, chain.py:325-329.
- B-2: the reset reads the state back and exits 2 when still ON, cli.py:469-484. Tests at test_stop_state_roles.py:1331 and test_stop_state_unit.py:256.
- B-4: the equal-names refusal is at cli.py:205-213, with tests at roles:1401 and unit:309.
- stop_state_mutants.py is no longer stale: the HAND list holds the mutants and the PENDING comment now reads "the two that were PENDING".
- The search_path decoy for the stop state is handled. The stop tables are schema-qualified with a schema resolved once (postgres.py:221, 470-478), and test_stop_state_roles.py:1031-1132 builds shadow tables and proves they are what an unqualified name finds.

MAJOR

1. Outbox rows are drained in random order, not write order.
- Where: chain.py:303 (`SELECT event_id, body FROM audit_outbox ORDER BY event_id`) and 311-330. Event ids are uuid4 hex (models.py:24-25), and the outbox table has no sequence or timestamp column.
- Failure scenario: the database blips during one run and its two outcomes (for example "approved", then "executed") both go to the outbox. The next tick appends them in uuid order, so they can land in the chain reversed. `events(run_id)` then returns the reverse of the causal order.
- The same inversion happens between the memory list and the outbox. Reconcile drains `_pending` first (chain.py:301), and those events are newer than the outbox rows.
- The earlier review marked "chain order is write order" as held, but that only covers `_pending`. No test pins outbox order: test_audit_drain.py:256 checks only "memory first then outbox".
- The hash chain still verifies, because verify checks links and not timestamps. The evidence ordering is what is wrong.
- Fix: in reconcile, parse all rows, sort by `event.ts` then `event_id`, and drain in that order. This needs no migration. Add a test with two outcomes of one run and ids that sort the opposite way. Consider merging the memory events into the same sort.

2. A transient database error is treated as permanent, and the event is then lost when the process exits.
- Where: `_is_outage` at chain.py:76-90, and the flush at chain.py:270-280, which calls `_unwritable.append(event)`.
- What counts as an outage: only class 08 and 57P errors, no SQLSTATE, or an interface error. Everything else counts as "can never succeed".
- What does not count: lock timeout 55P03, deadlock 40P01, serialization failure 40001 and statement timeout 57014. All of these are transient. postgres.py:194-196 sets `lock_timeout` on the shared connection, and `pg_advisory_xact_lock` at chain.py:138 honours it, so a busy chain with many writers can hit 55P03.
- Failure scenario: the database was down, so the runtime holds events in `_pending`. When it returns, the first flush meets a 55P03. The event moves to `_unwritable`, which only `reconcile()` re-queues (chain.py:300). The runtime process never calls reconcile (the tick is another process, as the cross-process test shows). The event is retried by nothing and dies with the process, with one WARNING line. SECURITY.md:16 states this limit for events that cannot be written, but a lock timeout is not one of those.
- A direct outbox row survives this case: the tick counts it as "not writable", the step fails loudly, and the row is retried next tick. Only memory-parked events are lost.
- Fix: either treat SQLSTATE 55P03, 40001, 40P01 and 57014 as "retry later" (stop the flush, keep the event in `_pending`), or on a non-outage refusal write the event to `audit_outbox` instead of memory, so the tick owns it. Add a test that raises 55P03 from `_append` during a flush and asserts the event is still queued.

MINOR (no file:line demands, listed for the lead)
- M1. The reset DSN's isolation from the runtime process is by naming convention and `check_senders` only (app.py:180-190). Nothing in code stops a custom secrets provider from handing the runtime the reset secret, because the secrets reader is IAM or policy and out of scope here. The runbook should say the runtime's secrets policy must not list the reset secret. I did not see a negative test of that.
- M2. `current_schema()` at postgres.py:221 returns the first existing schema on the search_path, not the schema that holds `kill_switch`. If an empty earlier schema exists, the read fails with an undefined-table error and the loop fails closed. That is safe, but the error text is not an operator hint. Also, the reset login can have a different role-level search_path than the runtime and then clear the wrong schema. migrate checks effective_problems against `current_schema()`, which would catch this only if both logins are checked.
- M3. Sibling class that remains: the audit chain, the spend tables and the reservations still use unqualified names, so a session can shadow them with temp tables (a temp `audit_entries` would swallow rows). Only the stop state was qualified. This is a pre-existing class, not a hole in B itself.
- M4. The tick's `audit_drain` is a silent no-op when `app.audit` has no `reconcile` (a wrapped or composite audit sink). A wrapper that hides the chain's reconcile would leave the outbox growing with the step green. I did not verify whether any shipped wrapper does this. Add a test that the configured chain kind exposes `reconcile`.

Check results
- Step C: all six ticket invariants held by reading.
  - Zero price is refused unless the llm kind is fake AND the stage is demo (config.py:572-578). Negative, minus zero and non-finite prices are refused on Route (config.py:83-97). The ceiling check runs before quantize.
  - `prices_as_of` is on Config (config.py:479), not on Route, so the config hash is not touched.
  - It is required in pilot and prod, may not be in the future, and old dates load (config.py:579-584). Only a plain date or YYYY-MM-DD text is accepted (config.py:485-492).
  - "Unknown model refused" is not coded, and the ticket says no code is needed because the existing unknown model_route check at registry.py:364 already refuses it. A route model id is never checked against a price list, so a route can name any model id with any positive price. This is a stated ticket limit, not a defect.
- Step B, runtime cannot clear:
  - The runtime role holds SELECT only on kill_switch and the clears table, and SELECT plus INSERT on the stops table (migrate.py:61-63).
  - UPDATE, DELETE and TRUNCATE on the stop tables are refused by triggers (0006_stop_state.sql:17-24).
  - A stop is one INSERT and needs no audit.
  - `get_kill_switch` reads ON when the flag row is missing, when the flag is on, or when any stop has no clear (postgres.py:480-506).
  - The reset runs in one transaction under READ COMMITTED, and a stop committed after the clear statement began stays ON (postgres.py:517-539). The CLI then exits 2 with "still ON".
  - Live stages refuse a reset without a reset login before any connection (cli.py:196-204).
- Audit, no lost row after a crash:
  - write_outcome falls from the chain to the outbox, then to memory.
  - A crash after append and before delete is deduped by event id (chain.py:208-209, 357-358).
  - Outbox rows are deleted only after the chain append.
  - The advisory lock serialises chain writers (chain.py:138).
  - Memory-only events are lost on exit, and that limit is stated and tested (test_audit_drain.py:560).
- Tests that cannot fail: none found in the parts I read. The only skip is when HADAVIN_TEST_PG_DSN is unset (test_audit_drain.py:5, 455), plus the psycopg importorskip at :455 and :647, which skips silently if psycopg is missing even when the DSN is set. Weak spots carried over from the earlier reviews: test_h1 in test_stop_state_roles.py accepts exit 0 or 2, and the fake-in-demo half of test_price_constraint.py:384-392 passes either way.

NOT CHECKED
- Nothing was run (no pytest, mutants, ruff, bandit, PostgreSQL), and no git log or head SHA.
- The sha256 of 0006 and 0007 in migrations_released.json was not recomputed.
- who_else_can_clear (migrate.py:279-303, 410-417), as instructed.
- Step F (reserve and settle) and the trigger config, beyond the secrets wiring at app.py:176-190.
- k1b/replay.py and the other pilot or prod test fixtures.
- Whether a shipped audit wrapper hides `reconcile` (M4).
- PostgreSQL behaviour for 55P03 inside an advisory-lock transaction. I took the classification from the code and the documented SQLSTATE classes.
- The runtime role's secrets-store IAM policy.
- tests/test_stop_state_unit.py in full.

Worktree: C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-b

# review-code-AB-2-Fstore-1 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

Review of cloud-core-b: A/B round 2 and F-store round 1 (read-only, nothing executed)

Verdict: no Blocker found by reading. A-1 and the cheap A/B minors are fixed in code. B-1 and B-2 are only PARTLY fixed (stale mutant script, untested new CLI paths). F-store source is in the tree and every invariant holds by reading, but none of its five test files exist, so nothing proves it and there is no 50-connection test.

All paths below are under C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-b\ unless absolute.

## What I reviewed (state at read time; no commit id, no git access)

Read in full (line count):
- src\hadavin_sdk\audit\chain.py (630), limits.py (138), cli.py (490)
- src\hadavin_sdk\store\postgres.py (721), protocol.py (239), memory.py (377), migrate.py (418)
- src\hadavin_sdk\store\migrations\0006_stop_state.sql (24), 0007_spend_reservations.sql (19)
- src\hadavin_sdk\runtime\tick.py (407)
- tests\test_stop_state_roles.py (991), test_audit_drain.py (1037), stop_state_mutants.py (222), test_stop_state_loop.py (40), contracts\kinds\store_postgres.py (87), fixtures\migrations_released.json (9)
- docs\stop-state-runbook.md (70)
- handover\core-b\tickets\F-store.md (387), F-store-review-2.md (20), ORDERS.md (124), interfaces\ii-meter.md (26), evidence\B-mutants-after-fix.log (22)
- C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\tickets\review-code-AB-1.md (150) and the persona file

Read in part or by search only: models.py 300-335, config.py 45-69, tests\test_p7_store.py 120-259, tests\test_p7_tick.py 70-99, agent_loop.py, defaults.py, CHANGELOG.md, SECURITY.md, README.md, interfaces\README.md.

## Part 1: steps A and B, round 2

| Id | Verdict | Where | Note |
|---|---|---|---|
| A-1 (Major) | FIXED | chain.py:298-302, 309-326, 329-338 | Non-outage append failures are counted and reconcile raises after the loop. |
| A-2 | FIXED, one residual | chain.py:252-263 | See finding AB-4. |
| A-3 | NOT FIXED in code | chain.py:220-221, 240-241 | The order asked for a stated limit only; I did not find that text in the lines I searched. |
| A-4 | FIXED | chain.py:303-307 | A failed DELETE is counted and the loop continues. |
| B-1 (Major) | PARTLY | tests\test_stop_state_roles.py, tests\stop_state_mutants.py, docs\stop-state-runbook.md | Role tests and docs exist; the mutant script is stale (AB-1). |
| B-2 (Major) | PARTLY | cli.py:469-486 | Code reads the state back and exits 2 when still ON; no test reaches it (AB-2). |
| B-3 | FIXED by documentation | runbook:49, SECURITY.md:28-29 | Grant is still table-wide at migrate.py:61. |
| B-4 | PARTLY | cli.py:205-213 | Refusal exists; no test (AB-2). |
| B-5 | FIXED in code, untested | migrate.py:279-303, 410-417; runbook:10-15 | Went beyond the order with a new guard; see AB-3. |
| B-6 | FIXED by documentation | runbook:10-12 | Code unchanged at cli.py:387-391. |
| B-7 | FIXED | runbook:50-51 | |
| B-8 | FIXED | tests\test_stop_state_loop.py:33, 40; test_stop_state_roles.py:949 | Asserts the fake model saw zero calls. |
| 0006 sha256 | NOT CHECKED | migrations_released.json:7 | Value present; I could not recompute it. |

Can the new tests fail?
- **A-1 tests:** yes. test_audit_drain.py:668-707 uses a real sqlite trigger refusal. Lines 982-1011 revoke INSERT on audit_entries from a real runtime role, run the tick in a child process, and expect exit 1 and the row kept.
- **Real non-owner logins:** yes. `World.store` asserts `current_user == role` (test_stop_state_roles.py:95); raw connections use `dsn_of(role)` (69-76).
- **Missing relation not counted as a refusal:** yes. `_denied` asserts the relation exists first (195-198) and expects `InsufficientPrivilege` exactly (43).
- **Skip when the database variable is set:** the only skip is on an unset `HADAVIN_TEST_PG_DSN` (38-41), plus `importorskip("psycopg")` at line 20, which skips silently if psycopg is absent even with the variable set.
- **Weak spots:**
  - `test_h1` accepts exit 0 or 2 (910, 916), though it checks the state matches the code.
  - The superuser test accepts either of two messages (630-633).
  - The two no-database tests at 968-991 are skipped without the DSN because the module-level mark covers them.

### Findings, A and B

**AB-1 (Major). tests\stop_state_mutants.py no longer matches the source and its last recorded run failed.**
- evidence\B-mutants-after-fix.log:14 and 21 show `SURVIVED | reset: ON CONFLICT is removed` and exit 1 on 2110ab3.
- Since then postgres.py moved to schema-qualified names (`{flag}`, `{stops}`, `{clears}` at postgres.py:473-527), so three mutants' old text is gone and they would report NOT APPLIED:
  - "read: the NOT EXISTS is dropped" (mutants:109-113 against postgres.py:488)
  - "reset: ON CONFLICT is removed" (125-127 against postgres.py:524, which has no trailing comma)
  - "reset: not one transaction" (128-132 against postgres.py:505-507)
- The killer `test_e6_a_deleted_flag_row_reads_on_and_stays_on_after_a_reset` (mutants:124) does not exist; the test is now `test_e6_a_deleted_flag_row_reads_on_and_a_reset_fails_loudly_and_stays_on` (roles:433). That mutant would report BASELINE FAILS.
- The three PENDING mutants (152-159: serial id, two loop hunks) have their guards in the source now but were never moved to HAND.
- Fix: update the four entries, move the three PENDING ones, add mutants for the new guards, and re-run until exit 0.

**AB-2 (Major). The B-2 and B-4 fixes have no test and no mutant.**
- No test under tests\ contains "still ON" or "same secret". The state read-back (cli.py:469-486) and the equal-names refusal (cli.py:205-213) can be deleted without a test failing.
- `test_e6` (roles:445) gets exit 2 from the ConfigError path, not the read-back.
- The parametrised case `pilot_ref_names_the_runtime_dsn` (roles:860-877) puts the runtime DSN value under a different name, which is not the B-4 check.
- Fix: one CLI test with a stop committed during the reset (the pattern of `test_e3`, roles:402-411) expecting exit 2 and "still ON"; one test with `reset_credential_ref == dsn_secret_name` expecting exit 2 before any `make`; a mutant for each.

**AB-3 (Major, needs a run to confirm). `who_else_can_clear` is new, untested, and may lock migrate out on managed PostgreSQL 16 or later.**
- Where: migrate.py:279-303, 410-417. No test references it.
- Why: it lists any non-superuser role that is a MEMBER of a role able to clear, including the owner and the reset role. From PostgreSQL 16 a non-superuser CREATEROLE user who creates a role is automatically granted membership in it with ADMIN OPTION. If `pg_has_role(..., 'MEMBER')` counts that grant (my reading), every `migrate` that names a role is refused on such a setup, and the creator cannot revoke a grant made by the bootstrap superuser. The refusal is technically right, because that user can grant itself the role.
- Fix: test it with roles created by a non-superuser CREATEROLE login on PostgreSQL 16 or 17; then either document the exception or add an explicit, audited allow-list of administrator roles. Add tests for a direct grant, a NOINHERIT member, and a reset role not named in the run.

**AB-4 (Minor). Events moved to `_unwritable` are never retried and never fail a step.**
- Where: chain.py:177-179, 262; pinned by test_audit_drain.py:921-931. SECURITY.md:16 states the limit.
- Why: a long-lived runtime process can lose audit outcomes with only a WARNING line.
- Fix: have `reconcile` add `len(self._unwritable)` to its failure text.

**AB-5 (Minor). A refused reset under the reset login cannot park its `reset_failed` outcome.**
- Where: limits.py:137; the reset role has no right on `audit_outbox` (migrate.py:67).
- Why: if the chain append also fails, the outcome goes to memory and dies with the CLI process.
- Fix: accept and state it in the runbook.

## Part 2: F-store, round 1

What exists:
- **Source:** all of it. Migration 0007, the GRANTS row, the four store methods on both stores, `SpendReservation`, `SpendRefused`, `Meter`, `Limits.reserve` and `settle`, `RESERVATION_EXPIRE_S`, the tick step and the purge line.
- **Pins and docs:** the pins (test_p7_tick.py:82-91, test_audit_drain.py:99-104, test_stop_state_roles.py:458-467, manifest line 8), `_SplitStore` routing (store_postgres.py:75-76) and CHANGELOG.md:31-64.
- **Tests: NOT IMPLEMENTED YET.** None of these exist: tests\contracts\test_store_spend.py, tests\contracts\test_t1_reserve_cap.py, tests\test_limits_reserve.py, tests\test_spend_reservations_pg.py, tests\reserve_mutants.py. No test anywhere calls `reserve_spend`, `settle_spend`, `expire_spend_reservations`, `Limits.reserve` or `Limits.settle`.

### Invariants (code by reading; none has a test)

| # | Invariant | Verdict | Where |
|---|---|---|---|
| 1 | Cap check and booking are one conditional UPDATE, in the insert's transaction | HELD | postgres.py:617-647 |
| 2 | All or nothing | HELD | reserve raises inside the transaction (634-635, 646-647); settle rolls the claim back (696-697) |
| 3 | Idempotent settle, (row, applied) | HELD | postgres.py:655-678; memory.py:337-338 |
| 4 | Expired keeps the worst case; never lowered | HELD | postgres.py:705-713, 658-659, 681-684; memory.py:340 |
| 5 | Day then month, no deadlock cycle | HELD | postgres.py:623-647, 686-697 |
| 6 | Midnight: the row's own day and month | HELD | limits.py:77; models.py:20-21 (UTC); postgres.py:688-693 |
| 7 | Overshoot booked in full, recorded, blocks later reserves | HELD | postgres.py:631, 643; limits.py:97-111 |
| 8 | Fail closed; no exception path returns an id | HELD | limits.py:65-90 |
| 9 | Amounts: exact Decimal, finite, 0 to below 10^9, 12 places | HELD | protocol.py:67-80; 0007:10-11. Caps are not checked (F-2). |
| 10 | Expiry on the database clock; `created_at` never passed | HELD | postgres.py:619-621, 709-712; 0007:13 |
| 11 | Stated limit: runtime can UPDATE its counters | HELD | CHANGELOG.md:64 |
| 12 | Purge deletes closed rows only | HELD | postgres.py:719; memory.py:373 |
| 13 | Run cost gets the real amount, in the settle transaction | HELD | postgres.py:698-702; memory.py:342-346 |
| Q3 | Age = max(3600, largest stuck age), rounded up | HELD | tick.py:263-267 |
| Q8 | READ COMMITTED pinned once per session | HELD | postgres.py:158 |
| Q9 | `settled_usd` is what stays booked | HELD | postgres.py:658-659 |
| R5 | Overshoot audit only when applied, never raises | HELD | limits.py:98-111 |
| R8 | Frozen model, nine fields, not a Shape | HELD | models.py:322-335 |
| cb-11 | Purge line before the hook | HELD | tick.py:205-208 |
| Step | `expire_reservations` is last | HELD | tick.py:303 |

### Attack results

- **Select-then-update race:** none. Each counter is seeded with `ON CONFLICT DO NOTHING`, then one UPDATE with `usd < cap AND usd + amt <= cap`. A second connection waits on the row lock and re-checks under READ COMMITTED.
- **Two connections both passing the cap:** not possible by reading; unproven, because T1 does not exist.
- **Failed month update:** `SpendCapExceeded("month")` rolls back the reservation row, the day seed and the day booking.
- **Settle racing expire:** the claim reads the prior status under `FOR UPDATE` in the same statement, and the counters only move by `GREATEST(actual, reserved) - reserved` for a was-expired row. I believe this is right, but it depends on PostgreSQL re-evaluating the join after a lock wait; the test the ticket requires (Q2) is missing.
- **`Limits.reserve` exception paths:** `return rid` is reached only after `reserve_spend` returns. A KeyError for an unknown agent comes before the try. Nothing else returns.
- **NaN, Infinity, negative, float, int, bool, None, sNaN, `0E+999999`, more than 12 places:** all refused by `check_spend_amount` before any SQL; `Limits.reserve` maps them to `bad_amount`.
- **Sweep clock:** database clock only.
- **Grants:** runtime SELECT, INSERT, UPDATE; purge DELETE plus SELECT on `status` and `closed_at`; portal and reset none (migrate.py:56). This matches the ticket.
- **Grant guard:** both statements of 0007 match `_SAFE_CREATE`; no serial, identity or sequence; the comment text holds no CREATE.
- **SQL built from input:** none in the new code; every value is a parameter and `_CLAIM` is a constant.
- **50-separate-connections test:** does not exist.

### Findings, F-store

**F-1 (Major). No F-store behaviour test and no mutant script exist.**
- Where: the five files named above (ticket R1 table and Q5, Q7).
- Why: invariants 1 to 13 are unproven. ORDER 008 item 1 counts a guarantee with no mutant script as not done, and item 3's batch run looks for `tests/contracts/test_t1_*.py`.
- Fix: a non-builder writes them. T1 must build 50 stores through `make(...)`, assert 50 distinct `pg_backend_pid()`, read the total from a 51st connection, include the check-then-`add_spend` control that admits more than 3, and include the repeatable-read variant (Q8). Also required: settle racing expire, C1 to C5, 8-connection settle, per-role negatives with the relation shown to exist, and no skip when the DSN is set.

**F-2 (Minor). `day_cap` and `month_cap` are not validated in either store.**
- Where: postgres.py:603-647; memory.py:298-318.
- Why: on PostgreSQL a NaN cap compares greater than every number, so both conditions pass and the cap is off; an Infinity cap does the same. The memory store would raise instead, so the two stores disagree. Through `Limits` the caps come from the registry `Money` type (config.py:60-67), which I believe pydantic keeps finite; I did not run it. A direct store caller is unprotected.
- Fix: run the caps through the same helper as the amount in both stores.

**F-3 (Minor). `expire_spend_reservations` accepts a negative or non-integer age.**
- Where: postgres.py:705-713; memory.py:353-366.
- Why: a negative age expires in-flight reservations. The booking stays, so the direction is safe, but their later lower settles no longer reduce the counters.
- Fix: refuse `older_than_s < 0`.

**F-4 (Minor). Deploying code before migrate 0007 also stops the ordinary evidence purge.**
- Where: tick.py:206-208.
- Why: `purge_spend_reservations` raises before the 30-day purge at 218-223 runs. CHANGELOG.md:45 names only the `expire_reservations` step as failing.
- Fix: add the purge step to that sentence.

**F-5 (Minor). interfaces\ii-meter.md:2 still says "not built yet, nothing run".**
- Fix: update the status line; core-c reads this file.

## Not checked

- Nothing was executed: no tests, no mutants, no ruff, no PostgreSQL.
- The sha256 values of 0006 and 0007 in the manifest.
- The baseline sdk-main: I opened no file there, so "unchanged from main" claims (`charge`, `blocked`, `add_spend`) rest on the ticket's description.
- handover\core-b\tickets\F-store-review-1.md, interfaces\README.md and i_store_spend.py beyond search hits.
- CHANGELOG, SECURITY and README beyond matching lines.
- tests\test_k5_fixes2.py, test_p2_postgres.py, test_migration_numbers_guards.py and test_k2_migrations.py beyond search hits.
- tools\mutation_runner.py.
- Whether other test doubles of the store lack `purge_spend_reservations`.
- agent_loop.py beyond the limits call sites. `reserve` and `settle` are not called by any model call site yet (F-install); the old `charge` sites remain at agent_loop.py:328 and 488.
- The PostgreSQL behaviours I reasoned about but could not run: the claim statement under a concurrent expire, `ON CONFLICT DO NOTHING` waiting on an uncommitted seed, and `pg_has_role` for an ADMIN-only membership.

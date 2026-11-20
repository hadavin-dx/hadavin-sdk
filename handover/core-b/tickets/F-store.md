# TICKET F-store: store-backed reserve before a model call and settle after it (owner core-b SPINE)
Written 2026-11-20 05:33 UTC from the lead's draft (inputs/draft-ticket-F-store-with-INTERFACE-ii.md, kept word for word below the line). Path class: money. Migration: 0007_spend_reservations.sql. Depends on: step B merged first (migration 0006, the GRANTS rows and the two pins shift). Ticket review: one EGM round, together with core-c's gate ticket. NO source code before the lead writes GO BUILD F.

## core-b's check of the draft (origin/main 51c9fc4, opened by core-b itself)
- CONFIRMED: limits.py:17-18 charge after the call and 20-30 blocked is a read; store/protocol.py:107-110 only add_spend and spend_totals; postgres.py:416-431 add_spend is an upsert with no cap, in one transaction, day then month; 0001_core.sql:87-92 spend; 0003_approvals_tick.sql:15-20 spend_month; tick.py:249-266 STEPS has no reservation step (step A appended audit_drain, so the new step goes after it); migrate.py GRANTS row format; agent_loop.py:485-486 and 324-326 charge sites.
- NOT opened by core-b: memory.py:196-204, the test files and line numbers named in the draft, the branch line ranges under "Branch mining" (the lookup note notes/heads-money.md covers the branches and agrees on what exists there).
- RUNG TABLE (scale: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code): component "pre-call reservation with an atomic cap" | need: 50 callers must not all pass the cap check | rung 1: n8n model nodes document no spend cap (plan-v2 item 2, n8n atlas 8.6, read by the lead, UNVERIFIED by core-b) | rung 2: Limits and Store exist but check and book in two steps (limits.py:17-30) | rung 4: LiteLLM budgets ruled out as a dependency (plan-v2 item 2) | rung 5: about 225 lines | only our code gives: the cap check and the booking in one database statement | verdict KEEP-CODE. ONE-PLACE-PER-JOB: the existing counters spend and spend_month stay the only counters; no second meter.
- NEEDED verdict: NEEDED.

## core-b's decisions on points the two lead drafts leave open or state differently
1. Argument order: reserve(agent_id, worst_usd, *, run_id=None) as in THIS draft (the lead ruled F-store wins over F-install).
2. Per-run cost: settle_spend adds the settled amount to the run's cost (runs.cost_usd) in the SAME transaction as the counter move, when the row has a run_id and that run exists; a missing run row moves only the counters. Reason: invariant 9 of F-install (run cost equals the sum of that run's settles) then holds exactly and a repeated settle cannot add twice. Stated limit: an expired, never settled reservation is in the day and month counters but not in the run's cost.
3. Interface (ii) contract point 10 is binding on the gate: the worst case covers system prompt, messages, tool schemas and documents at one token per byte at most, plus max_tokens of output, times the client's max_attempts. The shared helper lives in llm/common.py (F-install open question 1).
4. Open questions of the draft: 1 raise-only after expiry YES; 2 expiry age constant 3600 s YES, with a test that it is larger than the longest call the runtime allows (to be read in the build: UNVERIFIED today); 3 overshoot audit in Limits.settle YES; 4 pg_dsn.py from the T1 branch: WITHDRAWN in R1; 5 retention reuses the 400-day ceiling YES; 6 unknown agent stays KeyError YES.
5. Evidence commands: uv run --all-extras --group test pytest tests/contracts/test_store.py tests/contracts/test_t1_reserve_cap.py tests/test_limits_reserve.py (PostgreSQL cases with HADAVIN_TEST_PG_DSN set; in this container PostgreSQL 16.15 as an extra signal; the run that counts is the lead's on PostgreSQL 17). Rollback: the migration is additive (one new table, one index); reverting the source leaves an unused table.


## RESOLUTION of review round 2 (binding; wins over round 1's resolution and the draft where they differ). Report: tickets/F-store-review-2.md. Sent to the running builder at 05:54 and 05:57 UTC.
Q1 (file list). Added to the builder's list, pins only: tests/test_audit_drain.py (select the audit_drain step by name instead of STEPS[-1]; assert audit_drain comes before expire_reservations and expire_reservations is last), tests/test_k5_fixes2.py (the renamed-tree helper covers 0007), tests/test_stop_state_roles.py (the upgrade test's GRANTS filter and applied list). Removed: tests/test_k5_round6_contracts.py (needs no edit).
Q2 (settle claim). One statement: WITH old AS (SELECT status FROM spend_reservations WHERE reservation_id = %(id)s AND status IN ('open', 'expired') FOR UPDATE) UPDATE spend_reservations r SET status = 'settled', settled_usd = ..., closed_at = clock_timestamp() FROM old WHERE r.reservation_id = %(id)s RETURNING r.*, old.status AS was. Zero rows: the stored row with applied False, or NotFound. New test: settle racing the expire step never lowers a booking. New mutant 21: the delta ignores the prior status.
Q3 (expiry age). age = max(defaults.RESERVATION_EXPIRE_S, the LARGEST stuck_after_s over all agents of the registry), rounded up to an int; no agents: the default. Corrected claim: this is a quiet-time bound, not a bound on one call; a call slower than the age is charged its worst case, inside a run too.
Q4 (expired, then settled lower): R3's sentence "settled lower after expiry ... not in the run's cost" is struck. The row is claimed, the run's cost gets the real amount, the day and month counters do not move. Invariant 3: for one id the counters move at most once from open, or at most once upward from expired. C5: a lower settle after expiry settles the row and adds the real cost to the run; counters unchanged. Mutant 13: the counters go down after expiry. Invariant 13: for a run whose reservations were all settled, runs.cost_usd equals the sum of the real amounts.
Q5 (tests for the changes), all in the test writer's files of R1: run cost (run exists; run_id set but no run row; no run_id; replay adds once; expired then settled adds the real amount; both stores) in tests/contracts/test_store_spend.py; applied flag and audit written once across a replay, NotFound from Limits.settle in tests/test_limits_reserve.py; the age rule (two agents, the larger wins; no agents) in tests/test_spend_reservations_pg.py or a unit test beside it. Mutant 20 (runs update removed) is killed by the run-cost contract test.
Q6 (interface text). interfaces/ii-meter.md is the only contract text and numbering; README 2.2 points to it. tests/contracts/test_meter.py (both meters) belongs to the F-install test writer.
Q7 (evidence command): uv run --all-extras --group test pytest tests/contracts/test_store_spend.py tests/contracts/test_t1_reserve_cap.py tests/test_limits_reserve.py tests/test_spend_reservations_pg.py tests/test_p7_tick.py tests/test_audit_drain.py tests/test_p2_postgres.py tests/test_migration_numbers_guards.py tests/test_k2_migrations.py tests/test_k5_fixes2.py tests/test_stop_state_roles.py, with HADAVIN_TEST_PG_DSN set; then python tests/reserve_mutants.py (the mutant file is named tests/reserve_mutants.py as the lead's ORDER 008 asks, not spend_reservation_mutants.py).
Q8 (isolation). The connection sets READ COMMITTED once in connect() (SET SESSION CHARACTERISTICS), covering every writer; no per-transaction SET. T1 runs a second time with the test role's default_transaction_isolation set to repeatable read and still grants exactly 3. New mutant 22: the SET removed (killed by that T1 variant).
Q9 (the table says what is booked). A row that was expired gets settled_usd = max(actual, reserved) = what stays on the counters; a row that was open gets settled_usd = actual. The run's cost always gets the real amount. So the counters can be reconciled from the table, and the overshoot from the stored row is right in every case. Stated limit: for a was-expired row settled lower, the real cost is visible only in the run's cost, not in the reservation row.
Q10 (nits). Seed and update strictly day before month. SpendCapExceeded.which is mapped with a default of limits_unavailable. The amount helper refuses more than 12 decimal places. RESERVATION_EXPIRE_S is a plain constant. The purge count joins the purge log line. Stated limit: the overshoot audit row is written after the settle commits; a crash in between loses it (the row still shows it). Phases: the tick-step pins go green in P4; the test writer's files land after the builder's commit. Status: GO BUILD F-store was given in ORDER 010.

## RESOLUTION of review round 1 (binding; where it differs from the draft text below, THIS section wins)
Review report: tickets/F-store-review-1.md. Every Blocker and Major is answered here by a text change; none is contested.

### R1. Files (answers Blocker B1). B = builder, T = test writer (a different agent). Nothing else may be written.
| path | action | who |
|---|---|---|
| src/hadavin_sdk/store/migrations/0007_spend_reservations.sql | create | B |
| src/hadavin_sdk/store/migrate.py | modify: one GRANTS row | B |
| src/hadavin_sdk/store/protocol.py | modify: SpendCapExceeded, four methods on Store, amount check helper, missing_methods docstring | B |
| src/hadavin_sdk/store/postgres.py, store/memory.py | modify: the four methods | B |
| src/hadavin_sdk/models.py | modify: SpendReservation | B |
| src/hadavin_sdk/limits.py | modify: SpendRefused, Meter, Limits.reserve, Limits.settle (charge and blocked untouched) | B |
| src/hadavin_sdk/defaults.py | modify: RESERVATION_EXPIRE_S | B |
| src/hadavin_sdk/runtime/tick.py | modify: step expire_reservations (last), one purge line, the step list in the module docstring | B |
| tests/fixtures/migrations_released.json; tests/test_migration_numbers_guards.py (count 6 to 7); tests/test_p2_postgres.py (applied list); tests/test_p7_tick.py (step order pin) | modify: pins only | B |
| tests/contracts/kinds/store_postgres.py | modify: _SplitStore sends purge_spend_reservations to the purge login (as it does for the two existing purge methods) | B |
| CHANGELOG.md | modify: upgrade steps and behaviour changes (R9) | B |
| tests/contracts/test_store_spend.py | create: store contract cases, both stores | T |
| tests/contracts/test_t1_reserve_cap.py | create: T1, PostgreSQL only | T |
| tests/test_limits_reserve.py | create: Limits.reserve and settle, every SpendRefused reason, overshoot, unreadable store, midnight with a patched clock | T |
| tests/test_spend_reservations_pg.py | create: crash cases C1 to C5, settle from 8 connections, per-role negative tests, tick step | T |
| tests/spend_reservation_mutants.py | create: the mutants, in the format of tests/stage_mutants.py, each with the name of the test that kills it | T |
Not brought in from the branches: tests/pg_dsn.py, test_pg_dsn_guard.py, meter_support.py, reserve_workers.py, test_store_time_rules.py, postgres_mutants.py, meter_mutants.py and the demo conftest edit. Decision 4.4 above is withdrawn (it would edit files outside this list); the test writer may copy ideas into its own new files. Line citations of those branch files in the test plan are pointers to ideas, not to files in this tree.

tests/contracts/test_store_spend_caps.py and tests/contracts/test_store_spend_model.py (added later by the test writers, 2026-11-20 06:00 and 06:30 UTC) belong to the T rows above. Reviewer finding 16 of the hostile re-read.

### R2. Who lands what (M1)
F-store lands SpendRefused, the Meter Protocol, Limits.reserve and Limits.settle. F-install commit 3 lands only the k1b Budget changes.

### R3. Per-run cost inside settle_spend (M2)
In the settle transaction, after the claim and the two counter moves: `UPDATE runs SET cost_usd = cost_usd + %(add)s WHERE run_id = %(run)s`, only when the row has a run_id. `add` is the full actual amount on open to settled, and the full actual amount on expired to settled (an expired row never added anything to the run). Zero rows (no such run) is ignored. Stated limits: a reservation that expired and was never settled, or was settled lower after expiry, is in the day and month counters but not in the run's cost. The memory store does the same on its run dict. New invariant 13: for a run whose calls all settled before expiry, runs.cost_usd equals the sum of its settles. New mutant 20: the runs update removed. The interfaces README section 1 gets this sentence.

### R4. settle result, replay and unknown id (M3)
settle_spend returns `tuple[SpendReservation, bool]`: the stored row and `applied` (true only for the call that changed the row). Limits.settle returns max(0, row.settled_usd minus row.reserved_usd) from the STORED row (so a replay with another amount returns the first result) and writes the overshoot audit row only when applied is true and the overshoot is above zero. An unknown id raises NotFound from both Meter implementers (Limits and Budget); the gate already returns the reply when settle raises (contract point 5). F-install's "no-op for an unknown reservation" is replaced by this.

### R5. The overshoot audit event (M4)
AuditEvent(run_id=row.run_id or "-", domain="limits", operation="overshoot", principal=row.agent_id, source="meter", result="booked"), written with audit.write_outcome inside a try that swallows any exception (logged at WARNING).

### R6. Limits.reserve, exact order and mapping (M5)
1. Amount: `type(worst_usd) is Decimal`, finite, 0 <= worst_usd < 10**9; anything else (float, bool, int, None, NaN, Infinity, negative, too large) raises SpendRefused("bad_amount"). 2. `budget = self.registry.agents[agent_id].budget_usd` OUTSIDE any try: an unknown agent is a KeyError even when the stop state is on. 3. Inside one try: read the stop state (on: SpendRefused("kill_switch")); `rid = new_id("res")`; store.reserve_spend(...); return rid. 4. except SpendRefused: re-raise; except SpendCapExceeded: SpendRefused("daily_budget") or ("monthly_budget") by `which`; except Exception: SpendRefused("limits_unavailable").
The store's own amount check is one helper in store/protocol.py used by both stores: Decimal, finite, 0 <= x < 10**9, else ValueError (so the memory store and the table CHECK agree). Limits.settle passes the store's ValueError through for a bad actual amount.

### R7. Fixtures (M6, M7)
_SplitStore routes purge_spend_reservations to the purge login (file list). The per-role tests create the portal and reset logins by hand, the way tests/test_stop_state_roles.py (step B) does; pg_schema is not changed.

### R8. The row model (M8)
SpendReservation is a frozen pydantic BaseModel with extra forbidden and exactly the nine columns; it is NOT a Shape (no schema_version). status is Literal["open", "settled", "expired"]. The generic helpers _insert, _select and _one are not used for this table; the SQL is written out.

### R9. Rollback and rollout (M9)
Rollout order: run migrate first, then deploy the code (code first makes the tick step fail and, after the install, refuses every model call as limits_unavailable). Rollback: revert only the Python; keep the 0007 file, the GRANTS row, the manifest entry and the pins (migrate refuses an applied migration without its file). CHANGELOG upgrade steps: run migrate; a custom store must add the four methods or the app refuses to start; plus the two behaviour changes already listed.

### R10. Expiry age (M10)
The test "3600 s is larger than the longest call" is dropped: no upper bound exists in config (call_timeout_s has none). Stated cost instead: a call that takes longer than 3600 seconds is charged its worst case (a late settle only raises, never lowers).

### R11. Phases, each leaves the tree importable and the touched tests green (M11)
P1 migration file, GRANTS row, manifest entry, pins. P2 SpendReservation, Protocol additions, both stores, _SplitStore. P3 limits.py. P4 tick step, purge line, docstring, CHANGELOG.

### R12. One numbering for interface (ii) (M12)
The ten contract points of interfaces/README.md section 2 are the only numbering. Points 6 and 7 of the block "INTERFACE (ii)" below (the order inside Limits.reserve, the overshoot audit) are implementation notes of THIS ticket, now R6 and R5, not contract points. Point 8 reads "at the next reserve".

### R13. Nits taken
N1 line numbers moved after steps A and B: the builder re-reads the cited places. N2 no row needed in tests/test_migration_numbers.py. N3 the .charge( hits are 2 on Limits and 9 on the demo meter, none on k1b Budget. N4 in the file list. N5 the memory store expires with `created_at <= now - age` on models.now(). N6 seed statement: `INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING` (same for spend_month); a counter row missing at settle raises RuntimeError("spend counter row missing") and rolls back; ids come from new_id("res"). N7 the overshoot and midnight tests use month cap 100.00. N8 in the file list; RESERVATION_EXPIRE_S must pass tests/test_no_hardcoded_values.py (if that test demands a config field, it becomes Config.limits-style validated config with default 3600: the builder reports which).

### R14. Findings of the second reviewer (codebase-details) not already answered above
- cb-1 (Blocker): the test "migrate refuses after a hand GRANT DELETE to the runtime role" contradicts the code: migrate does REVOKE ALL before it checks (migrate.py:188), so a direct hand grant is repaired, not refused (pinned by tests/test_k2_migrations.py:275-289). REPLACED by two tests: (a) after a hand GRANT DELETE ON spend_reservations to the runtime role, running migrate again returns no problem and the role no longer holds DELETE; (b) a runtime role that INHERITS DELETE through another role is refused (the pattern of tests/test_k5_round10_postgres.py:118-128). Mutant 17 is killed by the existing generic loop tests/test_k2_migrations.py:214-227.
- cb-2 (run cost): R3 stands, with these additions. The runs UPDATE is written inline after the month step (add_cost cannot be called: it takes the same non-reentrant lock and raises NotFound for a missing run). CHANGE to the settle claim: an expired row is ALWAYS claimed by its first settle (status settled, settled_usd = the actual amount); the day and month counters move by max(0, actual minus reserved), so the booked amount still never goes down after expiry; the run's cost gets the full actual amount. This closes the gap "expired, later settled lower: the real cost never reaches the run". Only a reservation that is never settled stays out of the run's cost. The claim statement becomes: WHERE reservation_id = %(id)s AND status IN ('open', 'expired'). The table CHECK "status <> 'expired' OR settled_usd = reserved_usd" stays valid. Reuse: the run hunk of branch core/P4d-a2 _close (postgres.py:784 there) is the model for the inline UPDATE; "drop the run step" in the branch-mining list applies to reserve only. Contract point 9 everywhere now reads: no run cap is enforced by reserve; the settled cost is added to the run's cost.
- cb-4: tests/test_k5_round6_contracts.py:11-31 pins missing_methods with an OldStore: added to the builder's file list (pin edit only, if it enumerates method names).
- cb-5 (replaces R10's "bare constant"): the tick step computes the age as max(defaults.RESERVATION_EXPIRE_S, the existing stuck-run age of tick.py:100-109, which is max_steps x call_timeout_s x max_attempts + 60), so a reservation is never expired while its run could still be working. No new config field. The stated cost of R10 stays for calls outside a run.
- cb-7: the reserve and the settle transaction each start with SET TRANSACTION ISOLATION LEVEL READ COMMITTED, and T1 asserts SHOW transaction_isolation, so a server or role default of REPEATABLE READ cannot turn into a false daily_budget refusal.
- cb-10: the CHANGELOG behaviour list also names the two other readers of blocked: the action authorizer (agent_loop.py:716, deny limits.*) and the pre-execution recheck (agent_loop.py:790) can now refuse because another call's hold is open or expired.
- cb-11: the purge line sits with the ceilings in purge_evidence, before the hook, so a raising hook cannot skip it.
- cb-12: per-role tests to write are only the purge column checks and the reset and portal "no right" checks; runtime DELETE and TRUNCATE are already covered by the generic loops once the GRANTS row lands.
- cb-14: invariant 1 holds for an amount above zero, a counter starting at 0 and no settle in between; T1 states this.
- cb-17: CI PostgreSQL has the default 100 connections (.github/workflows/ci.yml:41, 111): T1's 51 fit as long as T1 is not run in parallel with itself.
- cb-19: CHANGELOG.md still says the evidence migration is 0006_evidence.sql and follows a reservations migration; the real files are 0005_evidence, 0006_stop_state and (this ticket) 0007_spend_reservations. core-b corrects those CHANGELOG lines in the step B docs commit (plan-v3 A1 gave this correction to SPINE).
- OPEN after this round (sent to the lead in ESCALATIONS.md, no round 2 by order): none of the Blockers or Majors is left without a text answer, but the answers above are NOT reviewed by a fresh reviewer, and three of them change the lead's draft design: settle returns (row, applied); an expired row is always claimed by its first settle; the expiry age is derived from the stuck-run age.

---
# DRAFT TICKET F-store (owner: SPINE): store-backed pre-call reserve and settle

Read-only draft; nothing was run, edited or checked out. S = `src/hadavin_sdk` on main 51c9fc4fb (snapshot `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main`). Line numbers are main's today; steps A and B land first and will shift `tick.py` STEPS, `migrate.py` GRANTS and the two pins.

## Purpose
Today a model call is checked before (`Limits.blocked`) and booked after (`Limits.charge`), so 50 callers can all pass the check before any of them books. After F-store the worst-case cost is booked on the day and month counters before the call, in one database transaction that refuses at the cap. The real cost replaces it after the call. A process that dies in between leaves the worst case booked.

## NEEDED-CHECK
- Check and booking are two separate calls: `S/limits.py:17-18` (charge) and `20-30` (blocked, "a read, no write").
- Booking happens after the call: `S/runtime/agent_loop.py:485` (reply) and `325` (judge verdict); the pre-check is `251`.
- `add_spend` is an unconditional upsert with no cap: `S/store/postgres.py:416-431`, `S/store/memory.py:196-204`.
- No reservation table exists: migrations stop at `0005_evidence.sql`; `spend` is `0001_core.sql:87-92`, `spend_month` is `0003_approvals_tick.sql:15-20`.
- One store object is one connection behind one lock (`S/store/postgres.py:193-197`), so a threaded test on one store proves nothing.
- No tick step for reservations: `S/runtime/tick.py:249-266`.
- Not needed, already there: UTC day and month buckets, `spend_totals`, the `store` fixture over both kinds (`tests/contracts/conftest.py:30`), the purge-identity wiring (`S/app.py:198-207`).

## Smallest shape
- The counters `spend` and `spend_month` now include open holds; no second counter. So `spend_totals` and `Limits.blocked` need no code change.
- Reserve is one transaction: insert the reservation row, seed the two counter rows with 0, then one conditional UPDATE per counter (day first, then month). Zero rows from either UPDATE raises and rolls everything back.
- Settle is one transaction: claim the row first, then move day and month by `actual - reserved` on the reservation's own day.
- Expire is a status change only; the counters do not move, so the worst case stays booked.
- A release is `settle(id, Decimal(0))`; there is no release method or status.
- Reservation ids are always fresh (`res-` + uuid4 hex) and reserve is never retried, so reserve needs no replay logic: a duplicate id is `StaleState`.

```sql
-- reserve, steps 3 and 4 (cap passed as a parameter; zero rows = refused, whole transaction rolls back)
UPDATE spend SET usd = usd + %(amt)s
 WHERE agent_id = %(agent)s AND day = %(day)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd;
UPDATE spend_month SET usd = usd + %(amt)s
 WHERE agent_id = %(agent)s AND month = %(month)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd;
-- settle, step 1 (the claim); zero rows = return the stored row unchanged, or NotFound
UPDATE spend_reservations SET status = 'settled', settled_usd = %(a)s, closed_at = clock_timestamp()
 WHERE reservation_id = %(id)s AND (status = 'open' OR (status = 'expired' AND %(a)s > reserved_usd))
 RETURNING *;
-- settle, steps 2 and 3: usd = usd + (actual - reserved) on the row's day, then its month; zero rows raises
-- expire
UPDATE spend_reservations SET status = 'expired', settled_usd = reserved_usd, closed_at = clock_timestamp()
 WHERE status = 'open' AND created_at <= clock_timestamp() - make_interval(secs => %(age)s);
-- purge (purge role)
DELETE FROM spend_reservations WHERE status <> 'open' AND closed_at < %(before)s;
```
`usd < cap` keeps today's rule that an agent at its cap is blocked even for a zero-cost call (`limits.py:26`).

## INVARIANTS
1. **Atomic reserve.** On PostgreSQL the cap check and the booking are the same UPDATE statement, in the same transaction as the reservation insert. For N concurrent reserves of amount w against cap c from separate connections, exactly floor(c/w) succeed, and the counter never exceeds c through reserves.
2. **All or nothing.** A refused or failed reserve leaves no reservation row and no counter change. A failed settle leaves the row open and both counters unchanged.
3. **Idempotent settle.** For one reservation id the counters move at most once (open to settled), plus at most one upward move (expired to settled when actual > reserved). `settled` is terminal; any later settle returns the stored row and changes nothing.
4. **Crash rule.** An open reservation older than the expiry age becomes `expired` with `settled_usd = reserved_usd`. The counters keep the worst case; after expiry the booked amount never goes down.
5. **Day and month together.** Both counters move in one transaction, always day then month (the same order as `add_spend`), so no deadlock.
6. **Midnight rule.** The day is the UTC date at reserve time (`now().date()`, as `limits.py:18`), stored in the row. Settle and expire act on that stored day and its month, never on today's.
7. **Overshoot.** A settle above the reserved amount is booked in full with no cap check. It is recorded as `settled_usd > reserved_usd` in the row plus one audit outcome. Every later reserve on that day or month is refused until the counter is below the cap.
8. **Fail closed.** Any exception from the store or the kill switch read inside `Limits.reserve` becomes `SpendRefused("limits_unavailable")`. No exception path returns an id.
9. **Amounts.** `worst_usd` and `actual_usd` are finite Decimals >= 0. The table CHECK also refuses NaN and Infinity (upper bound). Nothing is rounded.
10. **Expiry clock.** Expiry age uses the database clock only; `created_at` is never passed by the store method.
11. **Stated limit.** The runtime login can UPDATE its own counters (as today, `migrate.py:53-54`). Reservations protect against races and crashes, not against a hostile runtime login. The memory store guarantees nothing across processes.
12. **Purge.** Purge deletes closed rows only. If the purge role deletes an open row, the worst case stays booked (the safe direction).

## Migration `0007_spend_reservations.sql`
```sql
CREATE TABLE spend_reservations (
    reservation_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    day DATE NOT NULL,
    run_id TEXT,
    reserved_usd NUMERIC NOT NULL CHECK (reserved_usd >= 0 AND reserved_usd < 1000000000),
    settled_usd NUMERIC CHECK (settled_usd >= 0 AND settled_usd < 1000000000),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    closed_at TIMESTAMPTZ,
    CHECK ((status = 'open') = (settled_usd IS NULL)),
    CHECK ((status = 'open') = (closed_at IS NULL)),
    CHECK (status <> 'expired' OR settled_usd = reserved_usd)
);
CREATE INDEX spend_reservations_open ON spend_reservations (created_at) WHERE status = 'open';
```
- No foreign key, trigger, sequence or change to `spend` / `spend_month`. Both statements pass the guard's `_SAFE_CREATE` (`migrate.py:80-85`).
- **GRANTS** (one row, same PR, `check_grants` is two-way at `migrate.py:150-166`): `"spend_reservations": Grant("table", _RW, purge="DELETE", purge_cols=("status", "closed_at"))`.

| Role | Rights on `spend_reservations` |
|---|---|
| runtime | SELECT, INSERT, UPDATE |
| purge | DELETE, plus SELECT on `status` and `closed_at` only |
| portal | none |
| reset (step B) | none |

- **Manifest**: `tests/fixtures/migrations_released.json` gains `0007_spend_reservations` with the sha256 of the LF-normalised file, written at merge.
- **Pins**: `tests/test_migration_numbers_guards.py:363` goes from 6 (after B) to 7; `tests/test_p2_postgres.py:290` list gains `"0007_spend_reservations"`; `tests/test_p7_tick.py:82-89` gains the new step name.
- Not needed: a `TABLES` row at `tests/test_p2_postgres.py:31` (the loop at 63 covers listed tables only).
- UNVERIFIED: whether `tests/test_migration_numbers.py:486-491` needs a row; it looks like a synthetic list (it holds `0004_x.sql`).

## Store Protocol additions (`S/store/protocol.py`, both stores)
```python
class SpendCapExceeded(RuntimeError):
    def __init__(self, which: str) -> None:  # "day" or "month"; day is checked first
        super().__init__(f"{which} cap reached"); self.which = which

def reserve_spend(self, reservation_id: str, agent_id: str, day: date, usd: Decimal, *,
                  day_cap: Decimal, month_cap: Decimal, run_id: str | None = None) -> None:
    """Book usd on day and month or book nothing: SpendCapExceeded, StaleState (id exists), ValueError (amount)."""
def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendReservation:
    """The stored row after the call. NotFound for an unknown id; ValueError for a bad amount."""
def expire_spend_reservations(self, older_than_s: int) -> int: ...
def purge_spend_reservations(self, before: datetime) -> int: ...
```
- `SpendReservation(Shape)` goes in `S/models.py` (Shape is at `models.py:55`) with the nine table columns.
- **Postgres**: each write is `with self._lock, self._db.transaction()` (pattern at `postgres.py:419`). `UniqueViolation` maps to `StaleState` (pattern at `postgres.py:302`). The isolation level stays the default READ COMMITTED: the conditional UPDATE relies on the re-check after a row-lock wait, and T1 proves it.
- **Memory**: a dict of reservations under `self._lock`. The month is the existing sum over days (`memory.py:199-203`); a settle adjusts `_spend[(agent, row.day)]`.
- `missing_methods` (`protocol.py:151`, `app.py:194`) will refuse a custom store without the four methods; update its docstring.
- No getter, list, release, run cap, meta, retry wrapper or timeouts.

## INTERFACE (ii): what the gate wrapper calls
```python
# S/limits.py
class SpendRefused(RuntimeError):
    """Do not call the model. reason is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount"""
    def __init__(self, reason: str) -> None:
        super().__init__(reason); self.reason = reason

class Meter(Protocol):  # implemented by Limits (store) and by k1b Budget (memory, install ticket)
    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str: ...
    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal: ...
```
Contract:
1. `reserve` returns a reservation id only after the worst case is booked. Any exception from `reserve` means no model call; `SpendRefused.reason` is the audit error code. An unknown agent is a `KeyError`, as in `blocked` today (`limits.py:25`).
2. `settle` returns the overshoot (`max(0, actual - reserved)`, 0 when none). It may be called any number of times; the first call wins.
3. Real cost known, including a refused request that cost nothing: call `settle(id, reply.cost_usd)` or `settle(id, Decimal(0))`.
4. Real cost unknown (timeout, abandoned thread, crash): do not settle. The worst case stays booked and the sweep closes the row.
5. If `settle` raises (store down after the call), the gate returns the reply anyway. The worst case stays booked; the gate does not retry `reserve`.
6. `Limits.reserve` order: validate the amount, read the kill switch, then `store.reserve_spend(id, agent_id, now().date(), worst_usd, day_cap=budget.daily, month_cap=budget.monthly, run_id=run_id)`. `SpendCapExceeded.which` maps to `daily_budget` / `monthly_budget`, the same codes as `agent_loop.py:251-255`.
7. `Limits.settle` writes one `audit.write_outcome` (domain `limits`, operation `overshoot`, the row's `run_id`) when the overshoot is above zero. It never raises from the audit.
8. A stop set between the kill switch read and the booking lets that one call through (plan B3: "takes effect at the next gate check").
9. `run_id` is stored for investigation only; no run cap is enforced here.
10. Note for the gate ticket, not F-store: `worst_case_usd` (`S/k1b/loop.py:115-122`) counts the system prompt and messages only, not documents or tools, and counts one attempt. The runtime passes documents and tools (`agent_loop.py:470-476`) and `NetworkLLM._retry` can re-send (`llm/common.py:233`). Unless the gate's estimate covers those, overshoot becomes the normal path.

## Sweep tick step
- `expire_reservations(ctx)` calls `ctx.app.store.expire_spend_reservations(defaults.RESERVATION_EXPIRE_S)` and logs the count at WARNING when it is above zero.
- Appended last as `TickStep("expire_reservations", 0, expire_reservations)` (the contract at `tick.py:4-5` is append-only). It runs on the runtime DSN.
- Purge: one line in `purge_evidence` (`tick.py:186+`) on `app.purge_store or app.store`: `store.purge_spend_reservations(ctx.now - timedelta(days=keep.held_tool_calls_max_days))`. This reuses the 400-day ceiling; no new config.

## `Limits.charge` and `Limits.blocked`
- **`charge`**: untouched in F-store. It books on the same counters, so mixed use stays consistent. The install change deletes it together with `agent_loop.py:325` and `485`. The 11 `.charge(` hits under `tests/` then split: those on `Limits` (for example `tests/test_s5_runtime.py:109, 116`) switch to `store.add_spend`; those on k1b `Budget` belong to the install ticket.
- **`Store.add_spend`**: stays.
- **`blocked`**: code unchanged. Its totals now include open holds. It remains the cheap pre-check and kill switch read for `_limits_stop` (`agent_loop.py:251, 716, 790`); `reserve` is the authority.
- **Behaviour changes to state in CHANGELOG**: a call whose worst case does not fit is refused even when some budget is left (today one call may overshoot). A run can see `daily_budget` while another call's hold is still open.

## Tests (written by a different agent than the builder)
**Contract, both stores (`tests/contracts/test_store.py`, `store` fixture)**
- Reserve books day and month; settle lower, equal and higher.
- Exact-cap reserve passes; one micro over is refused with `which="day"`; the month cap binds when lower.
- Budget 0 refuses even amount 0.
- A refused reserve leaves totals and rows unchanged; a duplicate id is `StaleState` and booked once.
- Unknown id on settle is `NotFound`.
- NaN, Infinity and negative amounts are `ValueError` on reserve and settle, with nothing booked.
- Expire with age 0 closes the row with totals unchanged; expire leaves young rows alone; expire twice returns 0 the second time.
- Purge removes closed rows only.

**T1 (Postgres only, `tests/contracts/test_t1_reserve_cap.py`)**
- 50 `PostgresStore` objects from `make(...)`, one per thread (pattern `tests/test_p7_store.py:176-193`), one Barrier. Assert 50 distinct `pg_backend_pid()`.
- Cap 3.00, worst 1.00: exactly 3 granted, 47 `SpendCapExceeded`, total 3.00 read from a 51st connection before any settle.
- No caller settles until all have decided (Schedule from T1-T2-tests `meter_support.py:135`).
- Variants: cap 2.50 gives 2; month cap binding; 50 agents times 1 caller each do not block each other.
- Control: the same schedule with check-then-`add_spend` admits more than 3, which shows the test can fail.
- UNVERIFIED: that the CI Postgres service allows 51+ connections (default 100).

**Crash**
- C1: a spawned child reserves, commits and is killed. The totals hold the worst case; after expire the row is `expired` and the totals are unchanged.
- C2: a child blocked on a day row the parent holds `FOR UPDATE` is killed. No row and no counter change.
- C3: fault injected at the month UPDATE in reserve. No row, day unchanged.
- C4: fault injected at the month UPDATE in settle. Row still open, both counters unchanged.
- C5: late settle after expiry. A lower amount changes nothing; a higher amount raises both counters to the actual.

**Midnight**
- Reserve with day D, settle when today is D+1: only D and D's month move.
- Jan 31 into Feb 1: January's month moves, February stays 0.
- A full day D does not block D+1; a full month blocks D+1.
- `Limits.reserve` at 23:59:59.999999 UTC books D, using FakeClock from T1-T2-tests `meter_support.py:60`.

**Idempotent settle**
- Twice with the same amount; twice with different amounts (the first wins and the returned row is equal).
- 8 connections settle one id with different amounts: one is booked.

**Overshoot**
- Cap 1.00, reserve 0.60, settle 1.50: total 1.50, the row shows 1.50 > 0.60, `Limits.settle` returns 0.90 and writes one audit outcome.
- The next reserve of 0.000001 and of 0 is refused; the next day is free.

**Unreadable store**
- `reserve_spend` raising `OperationalError`, `StoreUnavailable` or `RuntimeError` gives `SpendRefused("limits_unavailable")`.
- `get_kill_switch` raising gives the same.
- A closed connection, and UPDATE on `spend` revoked from the runtime role, both refuse with nothing booked.
- Kill switch on gives `SpendRefused("kill_switch")` with nothing booked.

**Negative per role (real logins via `pg_schema(runtime=True)`; expect `InsufficientPrivilege`, a missing relation is not a pass)**
- Runtime: DELETE and TRUNCATE on `spend_reservations`.
- Purge: SELECT on `reserved_usd`, `agent_id`, `run_id`; INSERT; UPDATE; any right on `spend` or `spend_month`.
- Purge positive: the purge DELETE works.
- Portal and reset: no right at all.
- `migrate` refuses after a hand `GRANT DELETE ON spend_reservations` to the runtime role (`effective_problems`, `migrate.py:342`).

**Tick**
- The step is last in STEPS; a failing store marks the step FAILED and the other steps still run.

**Mutants**
1. Day cap clause removed.
2. Month cap clause removed.
3. `<=` becomes `<`.
4. `usd < cap` removed.
5. Check by SELECT, then an unconditional UPDATE.
6. Reservation insert outside the transaction.
7. Settle claim without the status test.
8. Delta sign flipped.
9. Settle uses today's day.
10. Month key taken from today.
11. Expire sets `settled_usd` to 0 or lowers the counters.
12. Expire ignores the age.
13. An expired row may settle lower.
14. Actual clamped to reserved.
15. `Limits.reserve` returns an id after a store error.
16. `Limits.reserve` skips the kill switch.
17. Runtime grant gains DELETE.
18. Tick step row removed.
19. Purge deletes open rows.

## Branch mining
All three PRs are OPEN. None of the four branches is an ancestor of another. Their merge-bases are 8 to 13 commits behind main.

| Branch | Drags along | As is | With edits | Not reused |
|---|---|---|---|---|
| `origin/core/P4d` (PR 66, da08ce2e2) | 13 files: 8 existing, 5 new; +1824 | Nothing | `test_store_money_baseline.py` as a checklist of bad amounts (it pins that `add_spend` books negatives and NaN) | `store_support.py`, `test_store_registry.py` (604), `test_pg_driver.py`; main already has the `store` fixture over both kinds |
| `origin/core/P4d-a2` (PR 75, a8abba0f9) | 39 files: 22 existing, 17 new; +6681; also `pyproject.toml` and `uv.lock` (which dependency is UNVERIFIED) | Nothing (its migration is numbered 0006, taken by step B) | See list below | See list below |
| `origin/core/P4b1` (PR 79, 8cc2021f7) | 37 files: 18 existing, 19 new; +5676; carries its own copy of the 0006 migration and store changes | The one-line map `{"day": "daily_budget", "month": "monthly_budget"}` (`meter.py:47`) | Nothing | `meter.py` (434) and `money.py` (112), replaced by the two `Limits` methods; `Limits.caps`, `hold`, callbacks. Only the header and outline of `meter.py` were read; `test_meter_processes.py` not read |
| `origin/core/T1-T2-tests` (1a7d20290) | 11 files: 2 existing, 9 new; +1536 | `tests/pg_dsn.py` (16 lines) plus the 8-line `kinds/store_postgres.py` hunk (missing DSN fails when `CI=true`) and `tests/test_pg_dsn_guard.py` (60, not read); it also edits `tests/demo_askdata/conftest.py` (6 lines). `test_store_time_rules.py` (23 tests) as a regression suite while `Limits.charge` exists | See list below | `meter_memory_killers.py` |

P4d-a2 with edits:
- The table DDL: drop `schema_version`, `meta`, `expired_at`, `released`, the foreign key to `runs`, the lock timeout and both trigger functions (about 45 of 69 lines).
- `postgres.py` 647-763: keep the counter-row seeding and the day and month conditional UPDATEs; drop the run step, the kill switch read, meta, the day-bound check and the replay branch.
- `_close` 765-815: keep the claim-first order; change the delta.
- The sweep statement 848-866: drop SKIP LOCKED, the limit and the sort.
- `SpendCapExceeded`, trimmed.
- `tests/contracts/reserve_workers.py` `race` and `reserve_then_hang`: remove `lock_timeout_ms` and `call_budget_ms`, which `PostgresSettings` on main lacks (`S/backends/table.py:116`); use the new signature.
- Test ideas from `test_store_reserve_proofs_pg.py` lines 300, 313, 540, 761, 1070.

P4d-a2 not reused: the `_writes` retry wrapper, `StoreBusy`, `_map_error`, the `check_usd` / `check_cap` / `check_meta` / `check_text` / `check_id` family (about 150 lines of `protocol.py`), `release_spend`, `list_open_reservations`, `get_spend_reservation`, `SpendOutcome`, `MAX_COUNTER_USD`, the config price validator (that is step C), `pg_owner.py`, `test_store_writes_pg.py`, `test_store_hostile.py`. Only the test names of `test_store_reserve.py` were read (30 tests).

T1-T2-tests with edits:
- `tests/meter_support.py`: FakeClock, `build_limits`, Schedule and oracle are reusable; `run_parallel` is threads on one store, so use it for the memory store only.
- `test_t1_meter_cap.py`: the "admits ceil(cap/cost)" cases become floor; the two negative and NaN pin tests flip to refused.
- `postgres_mutants.py` / `meter_mutants.py`: keep the file format; replace the mutant bodies.

## Out
- Run cap inside the store (`agent_loop.py:256-260` and `add_cost` stay).
- Caller-supplied reservation ids or reserve replay.
- A release status.
- Triggers or append-only rules on the table.
- Retry, lock timeout or call budget.
- A database-clock bound on `day`.
- A CHECK on `spend.usd`.
- Per-expiry audit rows.
- Sweep limit or SKIP LOCKED.
- Six-decimal rounding and `SpendMicro`.
- k1b `Budget.reserve` / `settle`, deleting the charge sites, the gate wrapper and the judge binding (install and TEXT tickets).
- A stale-price check.

## Open questions (recommended answer)
1. **May a late settle after expiry lower the booking?** No, raise-only. The cost is that a call slower than the expiry age is charged its worst case.
2. **Expiry age.** Constant `defaults.RESERVATION_EXPIRE_S = 3600`, no config field. It must exceed the longest model call including retries; UNVERIFIED what that maximum is on the runtime path.
3. **Overshoot audit: in `Limits.settle` or in the gate?** In `Limits.settle`, about 4 lines, so both `Meter` implementers keep one signature.
4. **Does the T1 branch's `pg_dsn.py` (CI fails on a missing DSN) come in with F?** Yes, since "NOT RUN = not done" (`resolve-plan-1.md:7`).
5. **Retention of closed rows.** Reuse the 400-day ceiling.
6. **Should `reserve` refuse an unknown agent as `SpendRefused`?** No, keep the `KeyError`; it is still no call.

## Size
- SQL: about 16 lines.
- Source: about 225 lines (protocol 35, postgres 75, memory 45, limits 40, models 12, tick 10, migrate and defaults 4, pins 4).
- Tests: about 600 lines.
- Docs: about 20 lines.

## Files read
- `C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\plan-v4-final.md`, `review-plan-1-design.md` (the six D5 invariants are at line 17 of this file, not in `review-plan-2-design.md`), `review-plan-2-design.md`, `review-plan-3-codebase.md`, `tickets\draft-A-B.md`
- `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main\src\hadavin_sdk\`: `limits.py`, `store\protocol.py`, `store\postgres.py`, `store\memory.py`, `store\migrate.py`, `store\migrations\`, `runtime\tick.py`, `runtime\agent_loop.py`, `k1b\loop.py`, `llm\common.py`
- `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main\tests\`: `contracts\test_store.py`, `contracts\kinds\store_postgres.py`, `test_p7_store.py`, `test_p7_tick.py`, `test_p2_postgres.py`, `test_migration_numbers_guards.py`, `fixtures\migrations_released.json`
- Branches read with `git show` / `git diff` in `C:\Users\rakes\Downloads\Hadavin\projects\hadavin-sdk`

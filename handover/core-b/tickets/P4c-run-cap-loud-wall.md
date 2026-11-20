# TICKET P4c: per-run cap and loud-wall alert (owner core-b, money and guarantee kit)
DRAFT, written 2026-11-20 for QUEUE row Q15. No source edited. Path class: money. Migration: needed or not is decided by the lead (see "Migration"); core-b does NOT pick a number. Ticket review: one EGM round (ORDER 003). NO source code before the lead writes GO BUILD P4c.
- S = src/hadavin_sdk. Stages are demo, pilot, prod. Tests are written by a different agent than the builder.
- Format taken from tickets/F-store.md and tickets/C-price-constraint.md; read-back rules from PLAN-READBACK.md (sections 3 and 4) and the module map in LANE-MAP.md.

## Purpose in plain words
Two things, one ticket.
1. A run may not spend more than its own cap, and the check happens BEFORE the model call, together with the daily and monthly booking, not after it. Today a run is only checked between steps by a read of what it has already cost, so one expensive call can pass the cap by its whole size, and parallel calls of one run can all pass.
2. When any spending wall stops work (the run cap, the daily budget, the monthly budget), a person is told at once in a way that cannot be missed: one audit event, one alert card, and a tick step that fails (exit 1, `tick_state.last_error`) while an agent sits at its day or month wall. Today a wall stop is only an abstain card with the reason text, which looks like any other abstain.

## NEEDED-CHECK
Question: does n8n, Make, the CRM, a free library or a module already in S do it?
Files and lines read (all on this checkout, 2026-11-20):
- S/limits.py:24-27 (`SpendRefused`, its reason list, `usd_cap` only from the in-memory `Budget`), 34-44 (`Meter` Protocol), 47-127 (`Budget`: ONE total cap per invocation, no run id cap), 130 (`_CAP_REASON`: day and month only), 152-185 (`Limits.reserve`: reads the agent's `budget_usd` daily and monthly; never reads `max_run_usd`; passes `run_id` to the store only as a label), 187-219 (`settle`, overshoot audit), 232-245 (`stop`, `reset`).
- S/runtime/agent_loop.py:85-88 (`GUARD_STOP_REASONS` already contains `run_budget`; `_REASON_TEXT` has only `ungrounded`), 252-263 (`_limits_stop`), 327-329 (`_screen` charges then `store.add_cost`), 455-497 (the model loop: `_limits_stop` at 468 area before each call; `limits.charge` and `store.add_cost` at 488-489), 617-637 (`_abstain` posts the abstain card, audits `card/abstain`).
- S/runtime/tick.py:1-12 (step contract, a failing step is loud: logged, saved in `tick_state`, exit 1), 102 (`stuck_after_s`), 233-252 (`reprobe_sources`: the existing example of a step that raises on purpose so the failure is loud), 255-283 (`audit_drain`, `reservation_expire_s`, `expire_reservations`), 292-310 (`STEPS`, last entry `expire_reservations`).
- S/registry.py:54-56 (`AgentRecord.max_run_usd: Money | None`, "required in pilot and prod"); S/deferred.py:62-63 (refuses a pilot or prod registry whose agent has no `max_run_usd`); S/models.py:98-107 (`Run.cost_usd`); S/store/protocol.py:197 (`add_cost`), 300-314 (`reserve_spend`: `day_cap`, `month_cap`, `run_id`, no run cap); S/store/migrations/0001..0008 exist (listing); S/store/migrations/0003_approvals_tick.sql (`tick_state.step ~ '^[a-z_]+$'`).
- handover/core-b/interfaces/ii-meter.md (six reasons; point 8: settle adds the real cost to the run; point 5 and 10: unsettled holds stay booked at the worst case; point 9: the stop-state window).

Findings:
- An EXISTING per-run cap exists: `AgentRecord.max_run_usd` (registry.py:54) is required in pilot and prod (deferred.py:62) and is enforced in `Runtime._limits_stop` (agent_loop.py:259-263) as `store.get_run(run_id).cost_usd >= cap` before each step, ending the run `needs_person` with reason `run_budget`. This ticket does NOT replace it and does not add a second config key.
- What that check cannot do: (a) it compares what was ALREADY settled, so the call that crosses the cap is allowed and its cost lands above the cap (overshoot up to one call's worst case, times the retry factor); (b) it is a read then a later write, so two calls of one run in flight both pass; (c) it ignores open holds of the same run, which are booked on the day and month counters but not yet in `runs.cost_usd` (interface point 2 of F-store: run cost moves only at settle); (d) `Limits.reserve` knows nothing about it, so the in-memory and store meters give no run-cap refusal to the gate.
- Loud wall: no module sends an alert. The only signals are an abstain card (agent_loop.py:617-637) with the raw code and `result="posted"`, and the overshoot audit row (limits.py:205-218). `GUARD_STOP_REASONS` labels `run_budget` a caught mistake, which a cap hit is not (it counts in the K6 catch rate); see Decision D2.
- n8n and Make: a workflow node runs after the model call or around it, never inside the booking, so it cannot refuse before spend or be atomic (plan-v2 item 2; n8n atlas 8.6, read by the lead, UNVERIFIED by core-b). The CRM holds no run data. A tool could ONLY carry the alert (a message), which S already does through the card hook and the audit sink; no new tool is needed.
- Free library: a per-run cap needs the run's settled cost plus its open holds under the same lock or statement as the day and month check. No free library knows our reservation table (the LiteLLM budget route was ruled out as a dependency, plan-v2 item 2).
Verdict: NEEDED, small, own code. Part 1 (pre-call run cap) NEEDED; the existing after-the-fact check (agent_loop.py:259-263) stays as the fast path and is NOT a duplicate once part 1 lands, it is a second line. Part 2 (alert): NEEDED for the tick step and the audit event; the card is TOOL-COULD-DO through the existing card hook (no new channel code).

## RUNG TABLE (CODE-LAST v1; scale of 2026-11-06: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code)
| Component | Need | Rung tried | Evidence (2026-11-20) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Run cap checked in the booking | one call cannot pass the run's cap; parallel calls cannot both pass | 1 n8n / Make nodes | they run around a model call, not inside the booking (UNVERIFIED atlas 8.6) | the check beside the day and month check in one lock or statement | KEEP-CODE |
| | | 2 core: `Limits.reserve`, `reserve_spend`, `max_run_usd` | all exist; none joins them (limits.py:152-185, protocol.py:300-314) | the join: run cost plus its open holds, read inside the booking | KEEP-CODE as an added argument, not a new module |
| | | 4 library | none knows our table | n/a | not applicable |
| Alert on a wall | a person sees a wall stop, once, not buried in abstain cards | 2 core: card hook (agent_loop.py:617-637), audit sink, tick step failing loudly (tick.py:233-252) | all exist; nothing names a wall | the rule that picks which refusals are walls and the one-event-per-stop dedup | KEEP-CODE, glue (about 40 lines) |
| | | 1 / 3 tool (n8n, chat webhook) | could carry the message; the SDK must not hold a vendor channel | n/a | TOOL-COULD-DO for delivery only, out of scope |

## GENERIC-WORDS CHECK
Core types and names use only: run, agent, reservation, cap, limit, meter, hold, alert. The new reason string is `run_cap`. The tick step is `limit_wall` (`[a-z_]+`). The word "wall" appears in this ticket's title and in prose only, never in a public name or a stored value. No customer, product, vendor, demo-project or stage word other than demo, pilot, prod. The alert text carries the agent id, the run id, the reason code and the cap name only: no price, no cap value, no document text. Checked by the test list item H6.

## DECISIONS core-b makes (each reversible; lead says OK or CHANGE in DECISIONS.md)
D1. The cap source is the existing `AgentRecord.max_run_usd`. No new key, no change to `config_hash` (registry.py: it is not in the hash today; this ticket leaves that so).
D2. A cap hit is NOT a guard catch. The runtime ends the run with reason `run_cap` via a limits path (like `limits.daily_budget`, agent_loop.py:258), and `run_cap` is NOT added to `GUARD_STOP_REASONS`. The old `run_budget` reason from `_limits_stop` keeps its meaning and its place in that set (changing it moves K6 numbers: out of scope; open question 2).
D3. The run cap applies only when `run_id` is given to `reserve`. The gate always passes it (ii-meter.md point 8). A call with no `run_id` is limited by the day and month counters only; a test pins that.
D4. Run headroom = `max_run_usd - (run cost settled + open and expired holds of that run at their worst case)`. An expired, unsettled hold stays counted (same rule as ii-meter.md points 5 and 10).
D5. The alert is raised by the runtime when `reserve` refuses with `run_cap`, `daily_budget` or `monthly_budget`; `kill_switch` and `limits_unavailable` are NOT walls here (a stop is a person's own act; an unavailable store is already `needs_person` and tick exit 4 or 1).

## INVARIANTS
1. A reservation that would make (run settled cost + run holds + this worst case) exceed `max_run_usd`, or that finds the run already at or over it, books nothing and raises `SpendRefused("run_cap")`. A cap of exactly 0 refuses every call of that run.
2. The run check and the day and month check are one booking: either all three pass and all counters move, or nothing moves. Order of reasons when several fail: kill_switch, then run_cap, then daily_budget, then monthly_budget (stated, tested; open question 3).
3. Under 50 parallel reserves for one run with a cap that fits exactly K of them, exactly K succeed (same shape as test T1, but over the run).
4. A settle below the worst case frees run headroom at once; a settle above it never refuses and is audited as overshoot (existing rule, unchanged).
5. An agent with `max_run_usd` None (demo only; deferred.py:62 refuses it live) has no run cap in the booking.
6. One alert per refused run: the run ends at the wall, so one audit event `limits/wall` and one alert card per run end. The alert is never raised twice for the same run id.
7. A failing alert (card hook raises, audit write fails) never changes the run's end state and never raises out of the runtime (same rule as `_deliver` and `_note_card`).
8. The tick step `limit_wall` raises (step failed, exit 1, `tick_state.last_error` set) while any registry agent has day spend >= daily budget or month spend >= monthly budget, and passes otherwise. It writes nothing and reads only `spend_totals`.
9. No alert text or audit field holds a price, a cap value, a document word or a secret.
10. Existing behaviour unchanged: `config_hash`, the six existing reasons, `Budget` (in-memory) semantics, the check at agent_loop.py:259-263.

## FILES
Create: tests/test_run_cap.py, tests/test_limit_wall.py, tests/run_cap_mutants.py (names follow tests/reserve_mutants.py). Test files are written by a different agent.
Modify (all in core-b's own file list, PLAN-READBACK section 2; nothing owned by core-a or core-c):
- S/limits.py: `SpendRefused` reason list gets `run_cap`; `Limits.reserve` reads `max_run_usd` and passes it on; `_CAP_REASON` extended for the store's `which == "run"`; the in-memory `Budget` is NOT given a run cap (its one total cap is its run cap; open question 4).
- S/store/protocol.py: `SpendCapExceeded.which` gains `"run"`; `reserve_spend` gains the keyword `run_cap: Decimal | None = None` (default keeps a custom store with the old signature working, as limits.py:199 already does for settle); docstring order of checks.
- S/store/postgres.py and S/store/memory.py: the check inside the existing booking (same transaction or lock): the run's settled cost plus the sum of its open and expired holds. In PostgreSQL the run row is locked first (`runs`), then the day row, then the month row; the order is fixed and tested for deadlock with the existing T1 setup.
- S/runtime/agent_loop.py: map `SpendRefused` reasons `run_cap`, `daily_budget`, `monthly_budget` to the run end `needs_person` with that reason (the existing model call path after the gate wrapper lands in core-c's ticket; this ticket adds only the reason mapping and the alert call at the one place a refusal ends a run); `_REASON_TEXT` gets a sentence for `run_cap`; one private method `_wall_alert(run, reason)`.
- S/runtime/tick.py: one new step appended after `expire_reservations`: `TickStep("limit_wall", 0, limit_wall)`; docstring line 5 lists it.
- S/store/migrate.py: only if a migration is needed (below).
- tests/test_audit_drain.py and the tick-step pin tests that select steps by name: assert `limit_wall` is last (same pins F-store touched; the exact list comes from the builder's grep, not guessed here).
- interfaces/ii-meter.md: version bump, point 3 of the reasons list: SEVEN reasons; the `run_cap` sentence (needs the lead's ruling because ii-meter.md is already FINAL, open question 1).
- CHANGELOG.md: one entry (cap checked before the call; new reason; new tick step).
Delete: nothing. Not touched: S/config.py, S/registry.py, S/deferred.py, S/guard/*, S/approvals/gate.py, the gate wrapper module (core-c), triggers/ and testing/ (core-a), README and SECURITY (a guarantee sentence enters only with the change that lands it, PLAN-READBACK 3).

## PUBLIC SIGNATURES
```python
# S/limits.py  (reason added; no new class)
class SpendRefused(RuntimeError):  # reason: kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount | usd_cap | run_cap
# Meter Protocol: UNCHANGED  reserve(agent_id, worst_usd, *, run_id=None) -> str ; settle(reservation_id, actual_usd) -> Decimal
# S/store/protocol.py
class SpendCapExceeded(...):  # .which in {"day", "month", "run"}
def reserve_spend(self, reservation_id: str, agent_id: str, day: date, usd: Decimal, *,
                  day_cap: Decimal, month_cap: Decimal, run_id: str | None = None,
                  run_cap: Decimal | None = None) -> None: ...
# S/runtime/tick.py
def limit_wall(ctx: TickContext) -> None  # raises RuntimeError("limit wall: <agent id>: daily|monthly") listing every agent at a wall; no value in the text
# S/runtime/agent_loop.py (private)
def Runtime._wall_alert(self, run: Run, reason: str) -> None  # never raises
```
Audit event of the alert: `AuditEvent(run_id=<run>, domain="limits", operation="wall", principal=<agent id>, source="meter", result="refused", error_code=<run_cap|daily_budget|monthly_budget>)`. Card: the existing abstain card path with the label from `_REASON_TEXT`; a distinct alert card type is NOT built (open question 5).

## MIGRATION
Needed: ASK THE LEAD. Question: does the run check need a new index on `spend_reservations(run_id)` (the sum of one run's holds scans by run id)? core-b cannot tell without a plan of the query and a row-count estimate (UNVERIFIED: the existing table's indexes are in 0007_spend_reservations.sql, not re-read for this draft). If an index or a column is needed, core-b asks for ONE migration number from the lead (files 0001 to 0008 exist in S/store/migrations today; later numbers may be taken by other lanes; core-b does not pick, and the migration-numbers pin tests would otherwise break). If no index is needed: no migration, and the lead is told so in DECISIONS.md. Either way the migration is additive and a revert leaves it unused.

## INTERFACES
Offered to other lanes:
- To core-c (gate wrapper): `SpendRefused.reason` may now be `run_cap`. The wrapper's error-code allowlist must accept the seventh code (the allowlist is core-c's file; core-b only tells them). The wrapper still passes `run_id` on every `reserve` (ii-meter.md point 8); without it the run cap is silent.
- To core-a (triggers, testing helpers): nothing. A test helper that builds a registry must give `max_run_usd` to agents in pilot and prod fixtures (already required, deferred.py:62).
Needed from other lanes:
- From core-c: the gate wrapper exists on the model call path before the run cap can be exercised end to end; until then the contract tests below run against `Limits` and the stores directly. Also their word on whether `run_cap` needs a wording line in the gate text (core-b assumes NO: it is a limits reason, not outbound text).
- From the lead: rulings on open questions 1 to 5, and the migration answer.

## TESTS
Helpers that exist: `MemoryStore`, contract suite tests/contracts/test_store_spend.py, tests/contracts/test_t1_reserve_cap.py, tests/test_limits_reserve.py (names from interfaces/ii-meter.md and the F-store ticket; builder re-greps before writing).
Normal:
- N1 cap 1.00, worst 0.40: two reserves pass, the third raises `run_cap`; nothing moves on the refused one (counters, run cost, table).
- N2 settle 0.10 on the first reserve frees headroom: a fourth reserve of 0.40 then passes.
- N3 the refusal text and `.reason` are exactly `run_cap`.
- N4 the alert: a run refused with `run_cap` ends `needs_person` with reason `run_cap`; one audit row `limits/wall`; one card posted.
Edge:
- E1 worst case exactly equal to the headroom passes; one unit of the smallest decimal above it refuses.
- E2 `max_run_usd` = 0: first reserve refuses `run_cap`; a worst case of 0 also refuses (same "at the cap refuses" rule as the day counter, limits.py:89-92).
- E3 `run_id` None: no run cap is applied (D3); the day and month caps still apply.
- E4 `run_id` given but no run row (store memory and PostgreSQL): decision pinned by test; recommended: refuse `limits_unavailable` is NOT used; the run cost counts as 0 and the holds are summed from the table (open question 6).
- E5 an expired, never settled hold of the run still counts (D4); a later settle above it raises the run's cost and keeps it refused.
- E6 two agents, two runs: holds of run B never count against run A; one run's cap does not touch another agent's counters.
- E7 order of reasons (invariant 2): kill_switch on plus run over cap gives `kill_switch`; run over cap plus day over cap gives `run_cap`; day and month over give `daily_budget`.
- E8 settle overshoot above the run cap never raises (existing rule) and the NEXT reserve of that run refuses.
- E9 `limit_wall` step: no agent at a wall gives ok; agent at day wall gives failed with the agent id in `last_error` and no number; agent at month wall; two agents listed together; `spend_totals` raising is a failed step, not a pass.
- E10 cap changed in the registry between two calls of one run: the new value is read on the next reserve (no caching).
Hostile:
- H1 50 parallel reserves on one run through 50 separate PostgreSQL connections (as T1, extra signal on PostgreSQL 16 in this container; the lead's PostgreSQL 17 run counts): exactly K succeed, the run cost plus holds never exceeds the cap; repeat with the role's isolation set to repeatable read.
- H2 60 parallel reserves split over two runs of the same agent with a tight day cap: no deadlock (fixed lock order run, day, month), counters equal the sum of the winners.
- H3 a `run_cap` that is NaN, a float, a negative or a string passed straight to `reserve_spend` raises `ValueError` before any lock (same helper as `check_spend_cap`); through `Limits` it can only come from a registry that already refuses it, so a custom store test only.
- H4 a custom store with the OLD `reserve_spend` signature (no `run_cap`): `Limits` with a registry where `max_run_usd` is set fails CLOSED with `limits_unavailable`, never silently with no run check; with `max_run_usd` None it keeps working.
- H5 the card hook raises, and the audit write raises: the run still ends `needs_person` with `run_cap`, nothing raises out of the runtime.
- H6 the alert and the audit row of a refused run whose agent id, run id and document hold a price-like string and a secret-like string: neither appears in card text, audit fields or the `limit_wall` error text; no cap value appears.
- H7 a refused run does not alert twice if the run end is replayed (`StaleState` on the second `_to`): at most one alert row.
- H8 a worst case so large that the sum overflows the amount bound (`check_spend_amount`, below 10**9): `bad_amount` first, before any run read.
CONTRACT TESTS (one per interface):
- C1 meter contract (both meters, in tests/contracts/test_meter.py of F-install's test writer, or a sibling file): `reserve` with `run_id` on `Limits` raises `SpendRefused` with a reason inside the seven; on `Budget` the same call never raises `run_cap` (D3 and the Budget decision).
- C2 store contract (memory and PostgreSQL, tests/contracts/test_store_spend.py): `reserve_spend(..., run_cap=X)` raises `SpendCapExceeded` with `which == "run"`, books nothing, and checks in the order stated; `run_cap=None` behaves exactly as before (the whole existing contract suite stays green unchanged).
- C3 tick-step contract: the step name matches `[a-z_]+`, is unique, last in `STEPS`, `every_s` 0, and a failing step leaves the others running (existing tick tests).
FAIL-BEFORE: on today's tree, N1 and H1 must fail by assertion (the third reserve does not raise; more than K succeed), not by import error. E9 fails because the step does not exist (name it in the test so the failure is an assertion on `STEPS`, not an ImportError).
Mutation plan (each mutant one edit; the test in brackets kills it): M1 run check removed from the store [N1, H1]; M2 open holds not summed [N1, E5]; M3 expired holds not summed [E5]; M4 `<=` to `<` at the cap [E1, E2]; M5 order of reasons changed [E7]; M6 `run_id` None treated as an error [E3]; M7 alert raised twice [H7]; M8 alert raised for `kill_switch` [N4 negative case in E7]; M9 `limit_wall` reads only the day counter [E9]; M10 cap value put in the alert text [H6]; M11 lock order changed [H2]; M12 old-signature store allowed silently [H4]. Run: `uv run --all-extras --group test python tests/run_cap_mutants.py`, last line "N of N good; problems: []".

## EVIDENCE COMMANDS (raw output under handover/core-b/evidence/P4c/)
- `uv run --all-extras --group test pytest tests/test_run_cap.py tests/test_limit_wall.py tests/contracts/test_store_spend.py tests/contracts/test_t1_reserve_cap.py tests/test_limits_reserve.py tests/test_p7_tick.py tests/test_audit_drain.py` (PostgreSQL cases with `HADAVIN_TEST_PG_DSN` set).
- the fail-before run on the files of the commit before; the mutant script; `ruff check src tests` and `ruff format --check src tests`; the full suite once.

## ROLLBACK
Tag `pre-P4c`. No stored-data change beyond an additive migration if one is granted. Reverting the source restores the after-the-fact check only (agent_loop.py:259-263), which keeps working unchanged. A store with `run_cap` support and a runtime without it is harmless (the argument defaults to None).

## STATED LIMITS
- A cap smaller than one call's worst case (price times tokens, times the client's attempts, ii-meter.md point 7) refuses every call of that run: the agent can never start. Not a bug; the alert tells the operator. A config check that compares `max_run_usd` to the worst case of the agent's route is out (open question 7).
- A call already reserved is not cancelled by a cap or a stop. The cap bounds what is BOOKED, not what a provider bills for a call that overruns its worst case; that overshoot is booked at settle and audited (existing).
- The kill-switch window (ii-meter.md point 9) is unchanged.
- The loud-wall step reads the day and month counters only; it says nothing about a run cap, which is per run and alerted at the moment of the stop.
- No outside channel: delivery of the alert beyond the card hook and the audit sink is whatever the operator wired to them.

## WHAT STAYS OUT
A new config key or a change to `max_run_usd` or to `config_hash`; a run cap in the in-memory `Budget` (its one total cap stays); changing `GUARD_STOP_REASONS` or the K6 catch counts; a new alert channel, vendor client, webhook, e-mail or chat code; a new card type; a price or cap value in any alert; a table of alerts or a "last alerted" column; repeat or escalation alerts; a check that a cap is larger than a call's worst case; reading prices from a vendor; the gate wrapper and the five charge sites (F-store and core-c); README, SECURITY (no new guarantee sentence until this lands); any change to stop state, roles or grants; applying a migration to a lasting database; live model calls and spend.

## OPEN QUESTIONS with recommended answers
1. ii-meter.md is FINAL with six reasons (ORDER 014): may it be reopened for a seventh, `run_cap`? Recommended YES; core-c's allowlist then takes seven.
2. Keep the old `run_budget` stop at agent_loop.py:259-263 as the fast path and in `GUARD_STOP_REASONS`, and make the new `run_cap` a limits reason outside that set? Recommended YES (K6 numbers do not move).
3. Reason order kill_switch, run_cap, daily_budget, monthly_budget? Recommended YES.
4. No run cap in the in-memory `Budget`? Recommended YES: it has one total cap per invocation and no run budget.
5. Reuse the abstain card for the alert (no new card type)? Recommended YES for this round.
6. A `run_id` with no run row: count the run cost as 0 and sum the holds? Recommended YES (consistent with F-store decision 2: a missing run row moves only the counters).
7. A load-time warning when `max_run_usd` is below the route's worst case? Recommended NO this round.
8. Migration: is an index on the run id of the reservation table wanted? Lead decides and gives the number; core-b does not pick.

## Size (estimate, UNVERIFIED until built)
About 70 source lines (store check about 30 across two stores, limits 10, runtime 20, tick 12), about 400 test lines, 1 mutant file, 1 interface text edit, 1 changelog entry.

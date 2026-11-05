# P0e memo 2: money base (plan-v3 section 8)

Date 2026-11-05. Author: S0 research-and-test agent. Status: DRAFT for `egm:egm-review-loop` (not yet reviewed).
Raw output: `egm\hadavin-sdk\core-complete\p0e\money\evidence-A.txt`, `-B.txt`, `-C.txt`, `-D.txt` (each ends with or contains the probe source).
Refs read: A = core `origin/pr/48` (8986cb5), B = core `origin/main` (ce70eb5) `demos/ask-your-data/askdata/meter.py`, C = core `origin/pr/49` (cd62212), D = Intake `b6592b9` `src/intake/budget.py` plus its caller `model.py`.
Probes ran in throwaway worktrees under `_local\scratch\wt\s0\money-A..D`. Every gate was exercised by running code, not only read.

## Answer first

1. **The winner by the rule is D, Intake `budget.py`.** It is the only candidate that passes all five gates. A and B fail gate 1 (they use `Decimal` USD, not integers) and gate 2 (missing usage settles at zero, or the meter has no usage idea). A, B and C fail gate 4. C is a different thing: approval holds, with no settle.
2. **The plan says the owner is told when the winner is not PR #48. It is not. The owner must be told.**
3. **The rule itself is stricter than the bible.** Plan gate 1 says "integers only". Bible R214 says "integer micro-dollars per 1 million tokens (or `Decimal`)". By R214 alone, A's `Decimal` would pass gate 1. A still fails gates 2 and 4, so the outcome does not change, but the review should confirm the stricter plan wording is intended (I think integers are better; see gap 2).
4. **Second conflict.** The plan's scored item is "round up per token class then summing". R214 says "round UP once per call". D does the R214 version (one ceiling over the sum). Neither under-counts; they differ by up to 1 micro-USD per extra class. The lead must pick one and fix the other text.

## Gate table (evidence file and test name given for each cell)

| Gate | A: PR #48 `llm/metered.py` + `limits.py` | B: askdata `meter.py` | C: PR #49 `store/reservations.py` | D: Intake `budget.py` (+ `model.py` caller) |
|---|---|---|---|---|
| 1 Integers only | **FAIL.** `lim.reserve("a", 5)` raised "reservation must be a finite, non-negative Decimal"; only `Decimal` is accepted (evidence-A, G1) | **FAIL.** Money is a decimal string in JSON ("5.0001") and `Decimal` arithmetic (evidence-B, G1) | **PASS, with a note.** `amount` must be a positive int; 1.5, 0 and -5 refused. Note: pydantic turned `True` into 1 before `validate` saw it (evidence-C, G1) | **PASS.** `reservation.micro` is `int`; sqlite columns are `integer`; float, string and bool usage are treated as garbage and settle at reserved (evidence-D, G1) |
| 2 Missing usage settles at the reserved worst case | **FAIL.** A reply with no usage (cost 0) settled at 0: booked total stayed 0 although the worst case was 0.001557 (evidence-A, G2) | **FAIL (no usage idea).** `settle(reserved, actual)` takes an amount; `settle(1, 0)` left 0 booked (evidence-B, G2) | **FAIL (not a spend meter).** Only `reserve` and `release_reservation`; no usage, no actual cost (evidence-C, G2) | **PASS.** `settle(res, None)` returned the reserved 12250; ledger row `settled_at_reserved`. Zero, negative and garbage usage do the same (evidence-D, G2; D's own test has 14 garbage-usage cases) |
| 3 Settle is idempotent | **PASS.** Second settle raises `ValueError`; total stays 0.1 (evidence-A, G3) | **FAIL.** Settle has no reservation id. Two reserves of 1, then the same `settle(1, 0.1)` twice, left 0.2 booked: the second settle consumed the other call's reservation (evidence-B, G3) | **PASS, for holds.** Same key and content again returns None and holds one row; second `release` returns 0; same key, other amount gives `KEY_CONFLICT` (evidence-C, G3) | **PASS, with a note.** Second settle raises `Refused(ledger_inconsistent)`; total stays 60, one row. It refuses; it does not return the first result (evidence-D, G3) |
| 4 Release in a `finally` / context manager | **FAIL.** A `KeyError` raised inside the model call (not a `ProviderError`) left 0.001557 booked: no settle, no release. It fails safe (money stays held) but the gate asks for a release path (evidence-A, G4) | **FAIL.** No release or context-manager path in the module (evidence-B, G4) | **FAIL.** No helper; the caller must call `release_reservation` (evidence-C, G4) | **PASS in the caller, not in the module.** `KeyboardInterrupt` inside `send` still produced a `settled_at_reserved` row: the `finally` in `GuardedModel.call` (model.py line 285) works. `budget.py` itself has no context manager (evidence-D, G4) |
| 5 Atomic for a single process | **PASS.** 40 threads, cap 1.00, each 0.3: 3 granted, 37 refused, 0.9 booked (evidence-A, G5) | **PASS.** 40 threads: 8 granted, 8 booked of 8.00 room (evidence-B, G5) | **PASS, for holds.** 40 threads: 3 granted, 900 held under cap 1000 (evidence-C, G5) | **PASS.** 20 threads: 2 granted, 2 rows. Also 8 separate processes x 6 attempts on SQLite: 9 granted, 900,090 reserved under the 1,000,000 cap (evidence-D, G5) |
| **Result** | out (gates 1, 2, 4) | out (gates 1, 2, 3, 4) | out (gates 2, 4; not a spend meter) | **survives (all five)** |

## Scored items (D is the only survivor, so this is a profile, not a contest)

| Item | D result | Evidence |
|---|---|---|
| Expiry sweep | **Yes.** `settle_orphans`: an open reservation older than 600 s (never below 2x call deadline + 5) settles at reserved. Probe: after 700 s, 1 swept | evidence-D, S expiry |
| Monotonic clock for clock-back refusal | **Partial.** Refuses a clock more than 1 day behind the ledger's last entry (2-day set-back refused); a 1-hour set-back is accepted. It reads wall `time.time()`, never `time.monotonic()`. A has no clock-back check; B uses monotonic only for the lock timeout | evidence-D, S clock; evidence-A and B, S |
| Round up per token class, then sum | **No: once per call.** In=1, out=1 at 333333 each costs 1 micro-USD (one ceiling over the sum); per-class would be 2. Matches R214, not the plan wording | evidence-D, S rounding |
| Spend and business money as separate types | **No.** Everything is `int` micro-USD of spend; no business-money type | evidence-D, S types |
| Parity with Intake `budget.py` on shared fixtures | **Not applicable to D (it is the reference).** A and B were not run against D's fixtures: NOT-TESTED, not needed since they are out | n/a |

Tie-break (fewer files, then one durable backend) is not needed: one survivor. For the record D is one 753-line module plus its caller, one durable backend (SQLite file). A spans three files with Postgres or memory; B is one file with a JSON file.

## What the losers have that D lacks (keep when P4b builds)

- From A: the billing contract for provider errors (`cost_to_settle`: release when nothing was sent or all refused, book at cost when billed, keep the worst case when unknown, fallback marks); tenant-injective counter keys; per-day, per-month and per-run caps; kill switch inside the same atomic step; a separate maintenance identity for pruning.
- From B: the reserve that stays unspent inside the owner's total, typed-in external spend with a staleness refusal.
- From C: integer holds with `KEY_CONFLICT` idempotency by key, scoped by tenant; useful for business money (see "Refunds").

## Gap list for the winner = the P4b ticket

D passes the five gates, but it is an Intake module, not a core kind. P4b must build:

1. **Lift out of Intake.** D is welded to `Settings`, the owner's sentence file, `prices.json`, `Refused` codes and `doc_sha`/`body_sha`. Core needs a neutral `reserve(key, worst_micro, cap_id)` and `settle(res, usage)` with those policies passed in. Intake-specific parts (owner sentence, circuit breaker, genesis marker) stay in the Intake repo.
2. **One counter shared with `src/hadavin_sdk/limits.py` (plan P4b item a).** Today there are two counters: `limits.py` counts `Decimal` USD per agent per day with daily, monthly and per-run caps; D counts one integer project total. Move `limits.py` to integer micro-USD (a non-revertible semantic change under plan section 10: it needs the "old code reading new data fails loudly" test) and put D's total, A's daily/monthly/run caps and the kill switch behind one reserve step. Hot-file order stays P3a, P4d, P4a, P4b.
3. **Cross-process atomicity on Postgres, 8 processes (plan P4b item b).** D has this only on SQLite (`BEGIN IMMEDIATE`; my 8-process probe held). Postgres needs one atomic statement or `SELECT ... FOR UPDATE`; A's Postgres store already does it for `Decimal` and is the starting SQL. Keep SQLite as the second durable backend. Test: 8 processes against Postgres, total reserved never above the cap.
4. **Context manager.** Add `with meter.reserve(...) as r:` that settles in `finally` (at reserved unless usage was recorded). Today the `finally` lives in Intake's `GuardedModel`, so every other caller must remember it; A and B show what happens when they do not.
5. **Idempotent settle.** A second settle with the same reservation id should return the first result, or the raise should be written down as the contract. A lost-acknowledgement retry is the case A's docstring warns about; D is safe only because it refuses.
6. **Monotonic reservation age.** Use `time.monotonic()` (or the database clock) for orphan age; keep wall time only for the clock-back refusal. A forward wall-clock jump can sweep a live reservation early today (D's 2x-deadline floor limits but does not remove this).
7. **Sweep under least privilege.** On Postgres the orphan sweep runs as its own maintenance identity (update-only, no delete), with a negative test that the runtime role cannot run it.
8. **Rounding rule.** Pick once-per-call (R214, D) or per-class-then-sum (plan). With P4a's five-class usage, per-class costs at most 1 extra micro-USD per class and is safe. Test R214's "10,000 tiny calls never below the exact Decimal total" on the integer ledger; fix the other text.
9. **Separate types.** Distinct `SpendMicro` and business-money types (with currency or unit) so a refund amount can never be added to a model-spend counter (R171).
10. **Port A's billing contract.** D settles every error at the reserved worst case: safe, but it over-counts a call that was refused or never sent.
11. **Do not regress what D already has:** garbage usage settles at reserved, settle above reserved halts, stale or future prices refuse, a refusal writes nothing, the cap tested at exactly the limit and one micro over.

## Refunds: both outcomes of "is refunds the first client"

- **No (lead default).** P3b does not bring PR #49's reservations. Nothing in the meter changes. P4b proceeds from D.
- **Yes.** PR #49 `reservations.py` still must **not** become the meter's base: it fails gates 2 and 4 and has no settle. Use it only for what it is: integer holds on business money while a person approves a refund (`Reservation`, `ReservationLimits`, migration `0005_reservations.sql`, `reserve`, `release_reservation`, `prune_reservations`). Add to it: a typed currency unit kept apart from spend (gap 9), a context-manager release tied to the approval outcome, and strict integer validation so `True` cannot become 1. The plan row 11 wording "decides whether PR #49 reservations become the meter's durable backend" should become "decides whether the hold table ships beside the meter".

## Bible rules read (numbers from `bible\RULES.md`)

- **R214** (line 485): reserve the worst case atomically before the call, reconcile with real `usage`; caps per request, per run and per client per day; integer micro-dollars "(or `Decimal`)", never floats; round UP once per call; test at the limit (allowed) and one micro over (refused); 10,000 tiny calls never below the exact Decimal total; cap day in a named zone (UTC default).
- **R215** (487): fail loudly at the wall (message, log, alert). D refuses with a code; the alert is not in `budget.py`.
- **R216** (489): atomic shared budget counter behind a budget-store kind, Postgres default; Redis or DynamoDB as alternatives. D (SQLite) is the outline for the second backend.
- **R110** (249): per-run token and cost budget beside the step limit; write-action retries idempotent or approval-gated. A has a per-run cap; D has none.
- **R335** (767): hard spend limit per task for long-horizon agents; the meter must support it (A's `max_run_usd`).
- **R211-R213, R278-R292:** model routing, cache and tier choice. They govern which model is called, not the meter.
- **R171** (389): money compared as typed integer minor units; supports gap 9.

## What I could not test (plainly)

- **Postgres with 8 processes:** no Postgres was run. A's Postgres store and the plan's 8-process requirement are untested by me. D's cross-process proof is SQLite only.
- **A and B across processes:** only single-process threads were run. They are out on other gates anyway.
- **Parity on shared fixtures:** not run (D is the reference; the others are out).
- **Live model calls:** none. D's `usage` handling was tested with fake values only. D's own docstring says thinking-token accounting is "NOT CHECKED here".
- **C on Postgres:** its Postgres `reserve` was read, not run.
- **Bool handling in A and B:** not probed.
- The probe tests are throwaway and were not added to any repo.

## Existing D suite (`tests/test_budget.py`: 49 test functions, 89 cases)

Run through `heavy_slot.py --slot-range 3-4` on b6592b9: **89 passed in 8.18 s** (tail saved at the end of `money\evidence-D.txt`). It is Intake's own suite, so it shows D keeps its own promises; it is not an independent check.

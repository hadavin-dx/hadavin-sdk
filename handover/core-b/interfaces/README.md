# INTERFACES published by core-b (SPINE) for core-a and core-c
VERSION 2.3 (06:14 UTC: answers to core-a request 003, see requests/003.answer.md: numbered invariants below; 'closed' means status not open, an expired row can be purged; first settle of an expired row sets settled_usd = max(actual, reserved); a zero amount at the cap is refused; caps and older_than_s are validated from fix round 1 on. The store code is built: commit 8db9c29. 2.2 was 05:56 UTC: section 2 now points to ii-meter.md as the one contract text; invariants are 1 to 13, mutants 20; an expired row settled lower is still claimed and its real cost goes to the run, only the counters stay. 2.1 was 05:44 UTC; 2.0 was 2026-11-20 05:32 UTC). Changes in 2.1 after the F-store ticket review (tickets/F-store-review-1.md): settle_spend returns (row, applied); the settled cost is also added to the run's cost; an expired row is always claimed by its first settle and its counters only move upward; an unknown reservation id raises NotFound from BOTH meters; contract point 9 reworded. The gate's own calls (reserve, settle) are unchanged. SUPERSEDES version 1 (published 05:29 UTC, withdrawn 5 minutes later). If you read version 1: the context-manager API (payer.hold, Hold.record, SpendMicro, six store methods) is GONE. Version 2 is the lead's smaller shape from inputs/draft-ticket-F-store-with-INTERFACE-ii.md, which the lead ruled as the interface (ORDERS.md, lead note 05:30Z). core-b accepts it (DECISIONS.md) because it is about 225 source lines against a 6,681-line branch for the same guarantee.
State: BUILT on cloud/core-b (commit 8db9c29 and fix rounds 1 to 3); reviewed in two ticket rounds and one hostile re-read of the code (tickets/F-store-review-1.md, F-store-review-2.md, F-store-hostile-review-1.md); tests: 471 passed on PostgreSQL 16 in core-b's container, mutants 31 of 31 and 26 of 26; core-a's 187 contract and T1 tests: 183 passed, 4 expected failures. The run that counts is the lead's on PostgreSQL 17 (not run by core-b).
- ii_meter.py + section 2 below: interface (ii), what the model gate wrapper calls. THIS is what core-c codes against.
- i_store_spend.py + section 1 below: interface (i), the four store methods behind it. Only core-b and the test writers use it.
The .py files are signature files (Protocols, no logic), not importable package code; the real code lands in src/hadavin_sdk in step F.
Change requests: handover/<your-name>/requests/<n>-interface.md with the reason; core-b answers in DECISIONS.md and bumps the version here.
Receipts and work items: NO store method is offered (the lead's draft ticket D needs no table; step H is cut unless a review proves a gap).

## 1. Interface (i): store methods for spend reservations
Plain words: a reservation is money set aside for one model call before the call. The store books it on the agent's day and month counters in one database transaction and refuses when a counter would pass its cap. After the call the real cost replaces it. A reservation nobody closed (the process died) is marked expired by a sweep and stays booked at the full amount.
| method | does | errors |
|---|---|---|
| reserve_spend(reservation_id, agent_id, day, usd, *, day_cap, month_cap, run_id=None) -> None | books usd on day and month, or books nothing | SpendCapExceeded(which = "day" or "month", day checked first); StaleState (id exists); ValueError (amount not a finite Decimal >= 0; reservation id not a str of 1 to 200 characters from A-Z a-z 0-9 . _ : -; agent_id or run_id not a str of 1 to 200 characters without control characters; cap not a finite Decimal >= 0 with exponent -12 to 9) |
| settle_spend(reservation_id, actual_usd, *, agent_id) -> tuple[SpendReservation, bool] | first call closes the row (open or expired), moves day and month by actual minus reserved on the row's own day (an expired row only upward) and adds the actual amount to the run's cost when the row has a run; later calls return the stored row with False and change nothing; agent_id is required: a reservation of another agent is NotFound (ORDER 020 m2; no agent-less path since I1) | NotFound; ValueError (amount as above; reservation id breaks the same rule, checked before the lookup) |
| expire_spend_reservations(older_than_s) -> int | open rows older than that (database clock) become expired; counters do not move | |
| purge_spend_reservations(before) -> int | deletes closed rows only (purge role) | |
Invariants (the same numbers as in tickets/F-store.md):
1. Atomic reserve: for N concurrent reserves of an amount w above zero against cap c from separate connections, starting at 0 with no settle in between, exactly floor(c / w) succeed and the counter never passes c through reserves.
2. All or nothing: a refused or failed reserve leaves no reservation row and no counter change; a failed settle leaves the row and the counters unchanged.
3. Idempotent settle: for one id the counters move at most once (from open), or at most once upward (from expired); a later settle returns the stored row with False.
4. Crash rule: an open reservation older than the expiry age becomes expired with settled_usd = reserved_usd; after expiry the booked amount never goes down.
5. Day and month move together in one transaction, day before month.
6. Midnight rule: the day is the UTC date at reserve time, stored in the row; settle and expire act on that stored day and its month.
7. Overshoot: a settle above the reserved amount is booked in full with no cap check.
8. Fail closed: any exception from the store or the stop-state read inside Limits.reserve becomes SpendRefused("limits_unavailable"); no error path returns an id.
9. Amounts are exactly Decimal, finite, 0 <= x < 10**9, at most 12 decimal places; nothing is rounded; caps are a finite Decimal >= 0 with the same exponent window (-12 to 9) and no other upper bound (from fix round 1 on; fix round 3 added the window). `agent_id` and `run_id` are strs of 1 to 200 characters without control characters. `expire_spend_reservations` takes an age 0 to 10**7 s; `purge_spend_reservations` a timezone-aware datetime (ValueError otherwise).
10. Expiry uses the database clock only.
11. Stated limit: the runtime database login can UPDATE its own counters; the memory store guarantees nothing across processes.
12. Purge deletes rows that are not open (settled or expired) and older than the bound; never an open row.
13. For a run whose reservations were all settled, runs.cost_usd equals the sum of the real amounts settled.
Stated limits: no run cap inside the store; no read method for a reservation; a settle after the purge of its row raises NotFound and the worst case stays booked.
Table: spend_reservations (migration 0007). Grants: runtime SELECT, INSERT, UPDATE; purge DELETE plus SELECT on status and closed_at; portal and reset none.

## 2. Interface (ii): the Meter the gate calls
The ONLY text and the ONLY numbering of the contract is interfaces/ii-meter.md (ten points, final after the review and the lead's ORDER 010). The list that stood here until version 2.1 is withdrawn because its numbers differed from that file.
```python
rid = meter.reserve(agent_id, worst_usd, run_id=run_id)   # raises: do NOT call the model
reply = inner.chat(...)
meter.settle(rid, reply.cost_usd)                          # returns the overshoot, 0 when none
```
Two implementers, one shape: Limits (store-backed, for the runtime, the judge and the shadow-card judge) and k1b Budget (in memory with a lock, for the eval and replay command lines; it does not read the stop state). The gate takes the meter as a constructor argument and must not test which one it got.

## 3. Tests other sessions may write now (new files only; different agent than the builder)
- tests/contracts/test_meter.py: the ten points of ii-meter.md against both implementers (file owner: the F-install test writer, since the Budget meter lands with F-install) with a fake inner client that counts calls; hostile amounts (negative, NaN, Infinity, float, bool); settle twice with different amounts; settle after expiry (lower: the row is settled and the run gets the real cost, the day and month counters do not move; higher: the counters rise to the real cost); reserve raising every listed reason.
- tests/contracts/test_t1_reserve_cap.py (PostgreSQL only, skips without HADAVIN_TEST_PG_DSN): 50 PostgresStore objects, one per thread, 50 distinct pg_backend_pid(); cap 3.00 and worst 1.00 gives exactly 3 granted and 47 SpendCapExceeded; control case with check-then-add_spend admits more than 3.
- Store contract additions, crash cases C1 to C5, midnight cases, per-role negative tests and the 20 mutants: listed in tickets/F-store.md.

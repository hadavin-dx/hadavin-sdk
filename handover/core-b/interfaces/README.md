# INTERFACES published by core-b (SPINE) for core-a and core-c
VERSION 2.2 (05:56 UTC: section 2 now points to ii-meter.md as the one contract text; invariants are 1 to 13, mutants 20; an expired row settled lower is still claimed and its real cost goes to the run, only the counters stay. 2.1 was 05:44 UTC; 2.0 was 2026-11-20 05:32 UTC). Changes in 2.1 after the F-store ticket review (tickets/F-store-review-1.md): settle_spend returns (row, applied); the settled cost is also added to the run's cost; an expired row is always claimed by its first settle and its counters only move upward; an unknown reservation id raises NotFound from BOTH meters; contract point 9 reworded. The gate's own calls (reserve, settle) are unchanged. SUPERSEDES version 1 (published 05:29 UTC, withdrawn 5 minutes later). If you read version 1: the context-manager API (payer.hold, Hold.record, SpendMicro, six store methods) is GONE. Version 2 is the lead's smaller shape from inputs/draft-ticket-F-store-with-INTERFACE-ii.md, which the lead ruled as the interface (ORDERS.md, lead note 05:30Z). core-b accepts it (DECISIONS.md) because it is about 225 source lines against a 6,681-line branch for the same guarantee.
State: PUBLISHED. NOT reviewed yet (one EGM round comes with ticket F-store). NOT run: no code for it exists yet.
- ii_meter.py + section 2 below: interface (ii), what the model gate wrapper calls. THIS is what core-c codes against.
- i_store_spend.py + section 1 below: interface (i), the four store methods behind it. Only core-b and the test writers use it.
The .py files are signature files (Protocols, no logic), not importable package code; the real code lands in src/hadavin_sdk in step F.
Change requests: handover/<your-name>/requests/<n>-interface.md with the reason; core-b answers in DECISIONS.md and bumps the version here.
Receipts and work items: NO store method is offered (the lead's draft ticket D needs no table; step H is cut unless a review proves a gap).

## 1. Interface (i): store methods for spend reservations
Plain words: a reservation is money set aside for one model call before the call. The store books it on the agent's day and month counters in one database transaction and refuses when a counter would pass its cap. After the call the real cost replaces it. A reservation nobody closed (the process died) is marked expired by a sweep and stays booked at the full amount.
| method | does | errors |
|---|---|---|
| reserve_spend(reservation_id, agent_id, day, usd, *, day_cap, month_cap, run_id=None) -> None | books usd on day and month, or books nothing | SpendCapExceeded(which = "day" or "month", day checked first); StaleState (id exists); ValueError (amount not a finite Decimal >= 0) |
| settle_spend(reservation_id, actual_usd) -> tuple[SpendReservation, bool] | first call closes the row (open or expired), moves day and month by actual minus reserved on the row's own day (an expired row only upward) and adds the actual amount to the run's cost when the row has a run; later calls return the stored row with False and change nothing | NotFound; ValueError |
| expire_spend_reservations(older_than_s) -> int | open rows older than that (database clock) become expired; counters do not move | |
| purge_spend_reservations(before) -> int | deletes closed rows only (purge role) | |
Invariants (numbered in the F-store ticket, 1 to 13): atomic reserve under N separate connections (exactly floor(cap / amount) succeed); all or nothing; idempotent settle; crash rule (worst case stays booked); day then month in one transaction; the UTC day is fixed at reserve time; overshoot booked in full; amounts are finite Decimals >= 0, nothing rounded; expiry by database clock; purge deletes closed rows only. Stated limits: the runtime database login can still UPDATE its own counters; the memory store guarantees nothing across processes; no run cap inside the store.
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

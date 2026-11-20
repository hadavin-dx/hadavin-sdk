# INTERFACES published by core-b (SPINE) for core-a and core-c
VERSION 2 (2026-11-20 05:32 UTC). SUPERSEDES version 1 (published 05:29 UTC, withdrawn 5 minutes later). If you read version 1: the context-manager API (payer.hold, Hold.record, SpendMicro, six store methods) is GONE. Version 2 is the lead's smaller shape from inputs/draft-ticket-F-store-with-INTERFACE-ii.md, which the lead ruled as the interface (ORDERS.md, lead note 05:30Z). core-b accepts it (DECISIONS.md) because it is about 225 source lines against a 6,681-line branch for the same guarantee.
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
| settle_spend(reservation_id, actual_usd) -> SpendReservation | first call closes the row and moves day and month by actual minus reserved, on the row's own day; later calls return the stored row unchanged; an expired row moves only upward | NotFound; ValueError |
| expire_spend_reservations(older_than_s) -> int | open rows older than that (database clock) become expired; counters do not move | |
| purge_spend_reservations(before) -> int | deletes closed rows only (purge role) | |
Invariants (numbered in the F-store ticket, 1 to 12): atomic reserve under N separate connections (exactly floor(cap / amount) succeed); all or nothing; idempotent settle; crash rule (worst case stays booked); day then month in one transaction; the UTC day is fixed at reserve time; overshoot booked in full; amounts are finite Decimals >= 0, nothing rounded; expiry by database clock; purge deletes closed rows only. Stated limits: the runtime database login can still UPDATE its own counters; the memory store guarantees nothing across processes; no run cap inside the store.
Table: spend_reservations (migration 0007). Grants: runtime SELECT, INSERT, UPDATE; purge DELETE plus SELECT on status and closed_at; portal and reset none.

## 2. Interface (ii): the Meter the gate calls
```python
rid = meter.reserve(agent_id, worst_usd, run_id=run_id)   # raises: do NOT call the model
reply = inner.chat(...)
meter.settle(rid, reply.cost_usd)                          # returns the overshoot, 0 when none
```
Contract (the gate must follow all ten):
1. reserve returns a reservation id only after the worst case is booked. ANY exception from reserve means no model call. SpendRefused.reason is the audit error code: kill_switch, daily_budget, monthly_budget, limits_unavailable or bad_amount. An unknown agent is a KeyError (still no call).
2. settle returns the overshoot: max(0, actual minus reserved). It may be called any number of times; the first call wins.
3. Real cost known, including a request that was refused before sending and cost nothing: call settle(rid, reply.cost_usd) or settle(rid, Decimal(0)).
4. Real cost unknown (timeout, abandoned thread, crash): do NOT settle. The worst case stays booked and the sweep closes the row after 3600 seconds.
5. If settle raises (store down after the call), return the reply anyway. The worst case stays booked. Never retry reserve.
6. One reserve covers the whole chat call, including the client's own internal retries.
7. The gate adds no second booking: nothing calls Limits.charge for a call that went through reserve (core-b deletes the five charge sites in the install change).
8. A stop set between the stop-state read and the booking lets that one call through; it takes effect at the next reserve.
9. run_id is stored for investigation only; no run cap is enforced here.
10. worst_usd is the GATE's job and must cover everything sent: system prompt, messages, tool schemas, documents, at the input price (at most one token per byte), plus route.max_tokens at the output price, times the client's max_attempts. If it covers less, overshoot becomes the normal path and the cap is no longer exact. core-b offers a shared helper for this in the install ticket (in src/hadavin_sdk/llm/common.py: worst_case_usd(route, system, messages, *, tools, documents, requests) -> Decimal); until it exists, core-c may write the formula in the wrapper and core-b will fold it.
Two implementers, one shape: Limits (store-backed, for the runtime, the judge and the shadow-card judge) and k1b Budget (in memory with a lock, for the eval and replay command lines; it does not read the stop state). The gate takes the meter as a constructor argument and must not test which one it got.

## 3. Tests other sessions may write now (new files only; different agent than the builder)
- tests/contracts/test_meter.py: contract points 1 to 9 against both implementers with a fake inner client that counts calls; hostile amounts (negative, NaN, Infinity, float, bool); settle twice with different amounts; settle after expiry (lower changes nothing, higher raises); reserve raising every listed reason.
- tests/contracts/test_t1_reserve_cap.py (PostgreSQL only, skips without HADAVIN_TEST_PG_DSN): 50 PostgresStore objects, one per thread, 50 distinct pg_backend_pid(); cap 3.00 and worst 1.00 gives exactly 3 granted and 47 SpendCapExceeded; control case with check-then-add_spend admits more than 3.
- Store contract additions, crash cases C1 to C5, midnight cases, per-role negative tests and the 19 mutants: listed in tickets/F-store.md.

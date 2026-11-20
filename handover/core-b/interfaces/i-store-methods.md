# INTERFACE (i): store methods for spend reservations (version 1)
Owner and builder: core-b. Contract tests: written by a different agent than the builder (core-a or core-c, see "Contract tests to write").

## Plain words
A reservation is money set aside for ONE model call before the call is made. The store books the set-aside amount on the same three counters it already has (the agent's day total, the agent's month total, the run's cost), inside one database transaction, and refuses when a counter would pass its cap. After the call the reservation is settled at the real cost, or released (given back) when the call was never sent. A reservation nobody closed (the process died) is later marked expired by a sweep; it stays booked at the full set-aside amount, so the cap can never be passed by a crash.

## Source (reuse, not new design)
The six methods, the row model, the migration and both implementations (memory, PostgreSQL) already exist on branch core/P4d-a2 (PR 75, head a8abba0): src/hadavin_sdk/store/protocol.py lines 35-69 and 301-338, models.py 351-366, store/migrations/0006_spend_reservations.sql, store/postgres.py, store/memory.py. Step F takes them as they are; the only planned differences are: the migration file is renumbered 0007_spend_reservations.sql (plan-v4-final B1: 0006 is the stop state), and the stop-state read inside reserve_spend follows step B's ON rule. Full facts with line numbers: handover/core-b/notes/heads-money.md sections 3.1 to 3.7.

## Methods (exact signatures in store_spend_protocol.py)
| method | what it does | errors |
|---|---|---|
| reserve_spend(reservation_id, agent_id, day, amount_usd, *, day_cap, month_cap, run_id=None, run_cap, meta=None) -> SpendOutcome | books amount_usd on day, month and (with run_id) run counters in one step; refuses at a cap | SpendCapExceeded (which = "run", "day" or "month", first failing in that order); KillSwitchOn; ValueError (bad amount, day, id, or counter past MAX_COUNTER_USD); ReservationConflict (same id, other content); StaleState (id already closed); NotFound (unknown run_id) |
| settle_spend(reservation_id, actual_usd) -> SpendOutcome | closes an open or expired reservation at the real cost; the real cost may be higher than the reserved amount and is then booked in full | ValueError; NotFound |
| release_spend(reservation_id) -> SpendOutcome | closes an open or expired reservation and gives the whole amount back | CounterDamaged (a counter is lower than the amount, nothing changed); NotFound |
| get_spend_reservation(reservation_id) -> SpendReservation | one row | NotFound |
| list_open_reservations(agent_id=None, run_id=None, limit=100) -> list[SpendReservation] | open rows, oldest first | |
| sweep_spend_reservations(older_than_s, *, limit=100) -> list[SpendReservation] | open rows older than older_than_s (30 to 10**7 seconds, by the database clock) become expired; NO counter moves | ValueError |

## INVARIANTS (numbered; each gets a contract test)
1. Atomic cap: for any number of concurrent reserve_spend calls on separate connections, the sum booked on a counter never passes its cap; a refused call books nothing on any counter.
2. One id, one effect: reserve, settle and release with the same reservation_id change the books once; a repeat returns the stored row with applied=False.
3. Same id with different content is ReservationConflict and changes nothing.
4. Counters always hold settled plus held amounts, so spend_totals and Limits.blocked see open reservations.
5. Status moves only open -> settled, released or expired, and expired -> settled or released (enforced by a database trigger on PostgreSQL).
6. An expired reservation stays booked at the reserved amount until it is settled or released once.
7. settle above the reserved amount books the real cost in full (money already spent is never hidden).
8. Amounts are exact Decimals: reserve and settle accept at most 6 decimals; no float, no bool, no NaN, no negative, no zero reservation.
9. A stop state that reads ON (or cannot be read) refuses every new reservation. Known limit, stated: a stop that commits during a reserve does not stop that one reserve.
10. No row of spend_reservations is ever deleted by the runtime role (grant: SELECT, INSERT, UPDATE; no DELETE).
11. A custom store without the six methods is refused at start by name (missing_methods).
12. The memory store offers the same methods and errors for tests and the demo stage; it guarantees nothing across processes.

## What other sessions may rely on
- core-c (gate wrapper): does NOT call these methods. It calls interface (ii).
- core-a (door): needs none of these.
- Test writers: the two store kinds are reached through the existing contract suite (tests/contracts/test_store.py, tests/contracts/kinds/store_postgres.py; PostgreSQL tests skip without HADAVIN_TEST_PG_DSN).

## Contract tests to write (different agent than the builder; new files only)
Branch core/P4d-a2 already carries tests/contracts/test_store_reserve.py and test_store_reserve_pg.py (8 threads over 2 connections, 12 connections, 8 processes). Still missing, to be written against this interface:
- T1: 50 SEPARATE PostgreSQL connections reserve against one cap at once; assert invariant 1 exactly (sum booked <= cap, number of successes = floor(cap / amount), every loser got SpendCapExceeded and booked nothing).
- Same T1 with a run cap, and with day rollover at UTC midnight.
- Hostile amounts: "NaN", "Infinity", negative, zero, 7 decimals, float, bool, 10**15 + 1.
- Hostile ids: empty, 201 characters, NUL, newline, SQL text.
- Replay: reserve, settle, settle again, release after settle (StaleState or stored result as stated above).
- Sweep: a row 29 s old is kept, 31 s old expires; counters unchanged; a second sweep finds nothing; two sweeps at once expire each row once.
- Grants: the runtime role cannot DELETE or TRUNCATE spend_reservations; purge and portal roles have no right on it.
- Mutants a test must kill: cap check removed from one counter; settle books reserved instead of actual; release without lowering a counter; sweep lowers a counter; replay books twice.

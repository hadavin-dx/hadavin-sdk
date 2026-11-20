# review-code-F-store-2 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

RESULT REVIEW, step F (spend reserve and settle), worktree cloud-core-b. I only read code and tests; I ran nothing, no Postgres, no pytest. Every "held" below is by reading.

COUNTS: Blocker 0, Major 1, Minor 6.

MAJOR

M1. The operator command to release expired holds under the reset identity does not exist.
- Lead decision (ORDERS.md:154, item 4) asks for it. It is absent from src: no function, CLI entry or store method.
- The reset role holds no right on spend_reservations (migrate.py:56). Z5 is "ON HOLD" (handover/core-b/tickets/F-install.md:32, ESCALATIONS E6).
- The builder's reason is real: a release lowers a booking after expiry, which contradicts invariant 4.
- Failure scenario: the sweep marks a crashed run's hold expired. It stays booked at the worst case on the day and month counters, and no tool frees it. An agent can sit at its cap for the rest of the day or month with no sanctioned fix except hand SQL by a superuser.
- Needed: the lead rules on E6. Either build it as an audited, intent-first command that lowers only expired rows of a named day and moves both counters in one transaction, with grants and negative tests, or record in the plan that holds are never released.
- Until then the item is open, not done.

MINOR

m1. postgres.py:636-666 and limits.py:150-153. The kill-switch read and the booking are not atomic.
- A stop committed between the two lets one more reserve through.
- Accept it and state it in the docs.

m2. postgres.py:683-698. settle_spend takes only the reservation id and does not check the agent.
- Any holder of an id can settle it, for example with 0.
- Ids are uuid4, so they cannot be guessed. The store has no tenant column.
- Tenant isolation here is per-agent counters only. If tenants share a store, add an agent_id check to settle.

m3. tick.py:263-267 and protocol.py:144,158. A stuck age above 10**7 s, or infinite, makes expire_spend_reservations raise ValueError or OverflowError.
- That fails the expire step on every tick, so holds never expire.
- The money stays booked, which is the safe direction, but open rows pile up. Clamp the age.

m4. postgres.py:741 and the purge. After a purge a late or duplicate settle raises NotFound, where before it returned the first result.
- This is safe for the booking. The gate must treat NotFound as "no change".
- The purge has no index on closed_at, so it scans the table.

m5. limits.py:48-69. The in-memory Budget does not validate `limit`, and `charge()` skips check_spend_amount.
- A NaN limit makes reserve raise InvalidOperation. That still means no call, but it is not SpendRefused.
- Budget allows a zero reserve at exactly the cap. Postgres refuses it, because `usd < cap` is strict. The two meters disagree at the edge.

m6. test_t1_reserve_cap.py:33 and test_spend_reservations_pg.py:46. All the PG tests skip when HADAVIN_TEST_PG_DSN is unset.
- The module docstring states that nothing is skipped when it is set, and the skipif reads that way.
- The importorskip("psycopg") at line 24 would still skip silently with the DSN set but psycopg absent. The lead must confirm in the CI log that the tests ran, with a count.

HELD BY READING (not re-reported as findings)

- **Exact money:** every amount and cap goes through check_spend_amount / check_spend_cap (protocol.py:111-141). Floats, ints, bool, NaN, Inf, sNaN, negatives, more than 12 places and 10^9 or more are refused before any SQL. Limits maps them to bad_amount.
- **Fail closed:** every store failure in Limits.reserve becomes limits_unavailable. Only an unknown agent is a KeyError. No path returns an id without a booking.
- **Reasons:** the sixth reason usd_cap exists only in Budget and is listed in the SpendRefused docstring. The other five are kill_switch, daily_budget, monthly_budget, limits_unavailable and bad_amount.
- **Reserve:** the insert, seed, day UPDATE and month UPDATE run in one transaction. The cap check is in the WHERE clause. Day is always before month, so I see no lock-order cycle with add_spend or settle.
- **Settle claim (_CLAIM, postgres.py:674-681):** a FOR UPDATE CTE reads the prior status. CTEs with row locks are not inlined, so there is no misread race with expire or a second settle.
  - First call wins. A second call gets the stored row and `applied=False`.
  - After expiry the booking is GREATEST(actual, reserved) and never goes down.
  - The counters move by `settled - reserved`, on the row's own day and month.
  - An overshoot is audited once, only when applied. An audit failure never raises.
- **Expiry:** uses the database clock. The age is max(3600, longest stuck age), rounded up (tick.py:263-267). The counters do not move. Negative and non-integer ages are refused.
- **Migration 0007:** the CHECKs bind status to settled_usd and closed_at, and an expired row must equal its reserved amount. There are no sequences. The purge role can only delete closed rows.
- **Stated limit:** the runtime role can UPDATE the counters and the reservation rows directly, so a compromised runtime could lower a hold.
- **Memory store:** it mirrors the PG rules under one lock.
- **Tests that exist:** test_t1_reserve_cap.py builds 50 stores of the runtime login and asserts 50 distinct pg_backend_pid values.
  - A 51st connection reads the totals.
  - Exactly 3 of 50 are granted at cap 3 with worst 1.
  - There is an old-pattern control, a repeatable-read variant, and the month cap across two days.
  - It asserts that a refused caller left no row.
  - test_spend_reservations_pg.py covers C1-C5, 8-connection settle, settle racing expire, per-role grants and hostile checks.
  - They can fail on a broken cap or settle.

NOT CHECKED

- Nothing was executed. That includes the 50-connection test, the settle-versus-expire timing and the grant tests, which need PostgreSQL 16.
- The mutant script tests/reserve_mutants.py. I did not confirm its last run exits 0, and I did not review the evidence file in detail.
- Whether the "settle 0 only for errors marked refused-before-response" rule holds.
  - It lives in the gate (core-c model_gate) and in llm/retry.py (ORDER 013).
  - Limits.settle accepts any amount. The rule is not enforced at this layer.
- Whether an unknown route is priced at the largest worst case, and the production-config test. That is F-install.
- Reply.cost_usd defaulting to None and the retry cost summing (ORDERS item 152-153).
- The sha256 of 0007 in migrations_released.json.
- migrate.py grant guard behaviour on 0007 beyond line 56. test_store_spend*.py, test_limits_reserve.py, the CHANGELOG and docs.
- The plan-v4-final step F text. A grep for "usd_cap" and "refused-before-response" in plan-v*.md found nothing, so I used ORDERS.md and the ticket instead.
- agent_loop.py. Reserve and settle are not yet called from any model call site, and the old charge sites remain.

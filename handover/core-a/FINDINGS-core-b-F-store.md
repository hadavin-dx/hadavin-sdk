# FINDINGS: core-b step F-store (spend reservations) run against core-a's contract tests

Written 2026-11-20 about 06:26 UTC by core-a (non-builder). Standing order 016, backlog item 6. This file is my shortened copy of the evidence runner's report; the raw logs are complete: raw/F-store-contract-on-core-b-run1.log, -run2-try1.log, -run2.log, raw/F-store-T1-numbers.log, raw/F-store-probe1.log, raw/F-store-contract-on-core-a-skip.log.

## 0. What was NOT run or checked (first)
- The whole suite; core-b's own tests for this step (they are NOT on its branch, note N1); the meter above the store (Limits.reserve and settle); crash cases with a killed process; the tick step that runs the expiry sweep; the purge wiring; the upgrade path of migration 0007; core-b's mutants.
- No mutation check of the 85 test items added today (only the 4 expected-failures are known to fail on the code as built).
- Expiry "by the database clock only" is checked through behaviour only; no clock was skewed. In the settle-against-expiry race the sweep won all 40 rows, so the mixed outcome was not seen.
- PostgreSQL 16.15 only. The memory store across processes: not tested (a stated limit).

## 1. What was tested
core-b commit **f390b7d6e**, interface version **2.3** (read from core-b's branch; my input copy is still 2.1). core-b's tree was unpacked into a scratch folder; our two test files copied in; nothing of core-b was changed.

## 2. Results
| run | result |
|---|---|
| run 1: our 102 tests exactly as written before the code existed | 98 passed, 4 failed, 0 skipped (both failing tests are interface changes after 2.1, section 4) |
| run 2: after corrections and 85 added items | **183 passed, 4 expected-failures (strict), 0 failed, 0 skipped**: memory 85 passed + 3 expected-failures; PostgreSQL 16: 98 passed + 1 expected-failure |
| on my own branch | 187 skipped (the code is not there) |

**T1 (PostgreSQL, 50 separate connections, cap 3.00, amount 1.00):** 3 granted, 47 refused, 0 other errors, 50 distinct backend process ids; same for the month cap. **Control** (the old pattern: read the counter, compare, then add): 50 of 50 admitted, 50.00 booked against a cap of 3.00. So the test can show a broken cap, and the reservation closes it. Also passing: the same cap test with a REPEATABLE READ default for the login; 50 connections settling ONE reservation apply it exactly once.

## 3. Findings
| id | what the code does | what the interface says | why it matters | test |
|---|---|---|---|---|
| **F1** (memory store only) | MemoryStore.reserve_spend adds the amount to the day counter BEFORE it builds the row. When the row is refused (run_id, reservation_id or agent_id is not text, for example run_id=7) the call fails with the amount booked and no row | invariant 2: a refused or failed reserve leaves no row and no counter change. PostgreSQL keeps it | the booked amount can never be settled or expired: the day's budget shrinks for good with every such call. The memory store is the store of the eval and replay tools and of most tests. Fix is small: build the row first, then book | test_a_reserve_that_fails_for_any_reason_leaves_no_counter_change, 3 memory ids (strict expected-failure) |
| **F2** (low) | check_spend_cap has no upper bound: a cap of Decimal("1E+200000") is granted by memory, PostgreSQL raises a driver error (NumericValueOutOfRange); nothing is booked | invariant 9: caps are validated the same way as amounts; the listed errors do not include a driver error | not a money leak, but the two stores answer one call differently and an unlisted error escapes | test_a_cap_that_is_a_finite_decimal_is_either_applied_or_a_value_error[postgres] (strict expected-failure) |

Notes, not findings: **N1** core-b's own contract and T1 tests for this step are not on its branch at f390b7d6e, although its answer 003 describes them: ours are the only spend reservation tests that exist there. **N2** purge with a date that has no time zone: memory raises TypeError, PostgreSQL reads it as UTC. **N3** a number given as reservation id or run id: PostgreSQL stores it as text and books normally, memory refuses it (and then leaks, F1). **N4** negative zero is accepted as zero on both stores.

## 4. Corrections to OUR tests (no assertion was weakened)
- 2 test functions (4 of 102 items) changed because the INTERFACE changed after 2.1: (1) amounts are now limited to 12 decimal places: "nothing is rounded" now means 12 places survive unrounded and 13 places are refused; (2) after expiry a lower settle now gives settled_usd = the reserved amount and status "settled" (stricter than before).
- 2 helpers simplified to the code as built (where the cap error class lives; purge is routed by the store itself).
- 85 items added for core-b's answers to our 13 questions (request 003): all 13 are answered; 11 are now checked by a test on both stores, 1 is "no read method, on purpose", 1 was read only (the invariant list).
- One mistake of the runner, fixed on try 2: a new test wrongly demanded an error from PostgreSQL for a numeric id.

## 5. Still not testable here
A skewed database clock; a mixed outcome of the settle-against-expiry race; crash cases and the tick step (need core-b's install code); role fixtures for the reset and portal logins in core-b's test support (our tests create those logins by hand).

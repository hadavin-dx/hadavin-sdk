# FINDINGS: core-b's meter (Limits on the store, in-memory Budget), contract tests by core-a

Written 2026-11-20 by the findings writer of core-a. Test file: tests/contracts/test_meter.py (core-a, 1041 lines).

## What was NOT run or checked (read first)
- The whole test suite of core-b: not run. Only our one file ran, on a scratch copy of core-b's tree.
- Planted bugs were put into the memory store and the Budget only. NOT into the PostgreSQL store (SQL not edited), so for that store the test file's catching power is unmeasured; the PostgreSQL cases themselves ran and passed.
- The Budget has no month cap, no stop state and no store: cases for those exist only for Limits.
- No model call, no network. Concurrency cases ran once each (threads, 16 callers); no repeated-run flake check.
- core-b's own meter tests were only listed and grepped, not run.
- The checkout (our branch) skips the whole file (core-b meter not on cloud/core-a): 262 skipped. So nothing here proves anything on our branch.

## What we ran against
- core-b commit d0cac9693 (origin/cloud/core-b, 2026-11-20 06:37 UTC). Scratch folder .../scratchpad/coreb-meter2 (import confirmed from the folder).
- Interface version: handover/core-b/interfaces/README.md VERSION 2.3 (section 2 points to ii-meter.md).
- PostgreSQL 16 on port 55433.

## Results (last line of each run)
| Run | Tree | Result |
|---|---|---|
| raw/meter-contract-on-core-b.log (earlier head, 7f8481795 area) | core-b old | 193 passed, 65 skipped, 4 xfailed |
| raw/meter-contract-on-core-b-run2.log | core-b d0cac9693 | 259 passed, 3 xfailed |
| raw/meter-contract-on-core-b-run3-final-test.log (after our 1 correction) | core-b d0cac9693 | 259 passed, 3 xfailed |
| our checkout | cloud/core-a | 262 skipped (expected) |

Per implementer on d0cac9693 (from run2): Limits on the memory store: all pass except the 3 M1 cases (strict xfail). Limits on PostgreSQL: all pass. Budget: all pass, including the 65 cases that were skipped before.

## What changed since the first run
- The 65 skips are GONE: core-b built reserve/settle/forfeit on the in-memory Budget (src/hadavin_sdk/limits.py). Those cases ran for the first time and all passed.
- The xfail "NOT BUILT N1 (no finding)" is gone for the same reason. Our correction: its conditional marker was turned into a skip-if-not-built (assertion kept, nothing weakened).
- M1 is NOT fixed. Still the only open finding.

## Findings
| id | implementer | what the code does | what the interface or ticket says | why it matters | test id |
|---|---|---|---|---|---|
| M1 | Limits on the memory store (MemoryStore.reserve_spend, src/hadavin_sdk/store/memory.py: counters are written at the line `self._spend[(agent_id, day)] = booked + usd`, the SpendReservation row is built after it) | A reserve whose run_id is not text (int, float, tuple) is refused with `limits_unavailable`, but the worst case stays booked on the day and month counters. No reservation row exists, so nothing can settle or expire it. | interfaces/README.md section 1 invariant 2 "All or nothing: a refused or failed reserve leaves no reservation row and no counter change"; Limits.reserve docstring "no path returns an id without a booking" and ii-meter.md (refused means nothing booked). | Money is lost from the cap for good (until the day ends) for a refused call. Needs a caller that passes a wrong run_id type; a bug in a caller would drain the day budget a little per call. Same class as store finding F1 of our store run. The PostgreSQL store does not have it (case passes). | tests/contracts/test_meter.py::test_a_reserve_that_is_refused_for_any_reason_books_nothing[limits-memory-int], [limits-memory-float], [limits-memory-tuple] (strict xfail, reason "FINDING M1") |
Fix hint: build the SpendReservation (or validate run_id) before changing `self._spend`.

## Skip reasons
- On core-b d0cac9693: none inside the meter file. (Earlier run: 65 skips, all "k1b Budget has no reserve/settle on this tree: the in-memory meter arrives with step F-install"; resolved.)
- On our checkout: whole file skipped with "core-b meter not on this branch yet" (Limits has no reserve here).

## xfail list of the first run, with decision
| xfail | reason | now |
|---|---|---|
| test_both_implementers_have_the_meter_shape[budget] | NOT BUILT N1 (no finding): Budget without reserve/settle | FIXED by core-b; marker removed (kept as skip-if-not-built) |
| test_a_reserve_that_is_refused_for_any_reason_books_nothing[limits-memory-int / float / tuple] | FINDING M1 | still a finding |

## Planted bugs (raw/meter-contract-planted-bugs.log; scratch copy only, restored after each; md5 of the two files checked equal to core-b's)
| Planted bug | Tests failed | Caught by (examples) |
|---|---|---|
| P1 settle applies twice (memory store and Budget) | 23 | test_settle_twice_the_first_call_wins, test_the_settled_cost_is_added_to_the_run_exactly_once, test_threads_settling_one_reservation_on_the_memory_store_apply_it_once, the shared-table cases |
| P2 a refused reserve still books (memory store and Budget) | 27 | test_a_reserve_past_the_cap_is_refused_with_the_cap_reason_and_books_nothing, test_settle_with_zero_frees_the_whole_reservation, thread grant counts |
| P3 overshoot clipped to zero (memory store and Budget) | 30 | test_settle_returns_the_overshoot_and_books_the_real_cost, test_a_settle_after_the_sweep_can_only_raise_the_booked_amount, test_twelve_decimal_places_are_booked_unrounded |
| P4 stop state ignored (Limits) | 16 | test_a_stop_set_before_reserve_refuses_with_kill_switch_and_books_nothing (memory and postgres), the between-read-and-booking case, the limits_unavailable cases for get_kill_switch |
| P5 month cap not checked (memory store) | 3 | test_the_month_cap_refuses_with_monthly_budget_and_books_nothing, test_a_cap_of_zero_refuses_every_call[...monthly_budget], test_the_month_cap_holds_across_the_days_of_a_month_and_a_new_month_is_free |
All five were caught (at least 3 tests each). The P5 count is low (3): month-cap logic is covered by few tests on the memory store; the PostgreSQL month cap is not mutated here.

## Does core-b have its own meter tests, and where do we overlap
Yes: tests/test_limits_reserve.py (28 tests, Limits on the memory store: refusal reasons, hostile amounts, settle, last microsecond of a day), tests/contracts/test_t1_reserve_cap.py (7), tests/demo_askdata/test_meter.py (13; the demo meter with OverBudget, a different object), tests/reserve_mutants.py (mutants of the store step). grep finds no core-b test that names Budget(...).reserve or forfeit (only tests/demo_askdata/test_ledger.py builds a Budget); not read in depth. Overlap: Limits on the memory store (refusals, settle, hostile amounts). New in ours: PostgreSQL through Limits, threads and connections, concurrent settles, stop set between read and booking, closed connection, tick step, the shared scenario table across all implementers, and every Budget case.

## Our corrections to our own test file
1. Removed the stale conditional "NOT BUILT N1" xfail (Budget is built now); replaced by skipif(not built). No assertion changed.
2. ruff check and ruff format: clean.

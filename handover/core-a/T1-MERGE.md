# T1 merge: tests/contracts/test_t1_reserve_cap.py

Decision (lead): core-b's file is the base; core-a's and core-c's extra cases are ported into it.
Result file: worktree /home/user/wt/t1, branch wip/core-a-t1-merge, `tests/contracts/test_t1_reserve_cap.py` (not committed).

## Case lists
- core-b (7): cap_3_and_worst_1_grants_exactly_3_of_50 (+3 settles at 0.10, 2 more granted), cap_2_50_grants_exactly_2,
  month_cap_binds_when_lower, month_cap_across_two_days, fifty_agents_one_caller_each, control_old_check_then_add,
  role_default_repeatable_read (+8 settles of one id: one applies).
- core-a (11 collected): fifty_stores_are_fifty_backends, cap_of_three [day, month], control, repeatable_read,
  fifty_settle_one_applies_once, settles_racing_expiry_sweep, runtime_may_not_delete, purge_role,
  portal_may_not_read, reset_may_not_read.
- core-c (core-a's cases + 14 own): 51st_connection_reads_granted_sum, floor(cap/worst) x5, two_agents,
  month_cap_two_days, fifty_settle_first_wins, settle_above_reserve, settles_below_reserve_free_room, settle_at_zero,
  expired_stay_booked, fifty_sweeps, settle_after_expiry, settle_racing_sweep.

## Disposition
DUPLICATE (not ported; same invariant exists in core-b's file): fifty_stores_are_fifty_backends (`_callers` asserts
distinct pids), cap_of_three day and month (`test_t1_cap_3...`, `..month_cap_binds...`), control, repeatable_read,
51st_connection_reads_granted_sum (`_t1`; its one-day-row/one-month-row count is folded into the floor case),
month_cap_two_days, settles_below_reserve_free_room (b settles three at 0.10 and gets exactly 2 more).

PORTED (13 functions, 18 collected cases; each marked "from core-a T1" / "from core-c T1"):
- floor(cap/worst) x5 params (3.50/1, 0.07/0.01, 1.00/0.30, 0.99/1 -> 0, 50/1 -> 50) [core-c]
- two agents on the same 50 connections, 3 each [core-c]
- 50 settle one reservation, 50 different amounts: one applies, all get the same row, counters and run cost = winner [core-a, core-c]
- settle above the reserve books the actual amount past the cap [core-c]
- settle at zero gives everything back [core-c]
- expired stay booked and keep the cap shut [core-c]
- 50 sweeps expire each row once [core-c]
- settle after expiry never lowers the counters [core-c]
- 40 settles racing 10 sweeps: counters equal the rows, run cost 40 x 0.25 [core-a]
- one row, 25 settles racing 25 sweeps: booked = 0.25 or 1.00 [core-c]
- runtime role may not delete / purge [core-a]; purge role only via the function [core-a]
- portal and reset roles may not read (2 params) [core-a]

NOT PORTABLE AS WRITTEN (adapted, never loosened):
- core-a's "runtime holds SELECT, INSERT, UPDATE" and "purge holds DELETE + SELECT on status, closed_at" are stale on
  core-b (migration 0011: no login has any right on spend_reservations; the money functions are the only way). The
  ported cases assert the STRONGER fact (every direct statement refused, purge still works through
  `purge_spend_reservations`, runtime gets InsufficientPrivilege on it). Overlaps tests/test_money_step4_grants.py.
- core-a's reset-role case skipped itself ("no reset_role"); core-b's World has it, so it now runs.
- API adaptations: `settle_spend(..., agent_id=)`; PG ignores the caps passed to `reserve_spend` (tests/conftest.py
  seeds `hadavin_caps`); logins from `World`; threads via core-b's `_together`.

## Counts (HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55433/postgres, -n 2)
- before (core-b alone): 7 passed; without DSN 7 skipped
- after: 25 passed; without DSN 25 skipped. ruff check and format clean.
- mutation sanity (scratch plugin, no src edit): sweep made a no-op -> `expired_reservations_stay_booked` and
  `fifty_sweeps_at_once` FAIL; settle always reporting applied=True -> `fifty_connections_settle_one..first_wins` FAILS.

## Text for core-b and core-c
core-b: "Copy tests/contracts/test_t1_reserve_cap.py from branch wip/core-a-t1-merge as-is (it is your file plus 18
cases from core-a/core-c; your 7 cases are unchanged). 25 pass on PG, 25 skip without the DSN."
core-c: "Drop your variant: in the integration delete tests/contracts/test_t1_reserve_cap_core_a.py and
tests/contracts/test_t1_reserve_cap_core_c.py and take the merged tests/contracts/test_t1_reserve_cap.py; every case
of yours is either ported (marked 'from core-c T1') or a duplicate listed above."

## review round 1 fixes (fresh reviewer rev-t1, then builder t1-fix; branch wip/core-a-t1-merge now at the head below)

File changed: tests/contracts/test_t1_reserve_cap.py only. 25 -> 26 cases (one added), all green with the PG16 DSN; 26 skipped without it.

- MAJOR: the portal and reset refusal case lost core-a's positive read. A new helper `_may_not_touch_reservations` now runs a read each login is meant to make BEFORE the refusals (portal: `runs`; reset: `kill_switch`; runtime: `spend`; purge: `SELECT run_id, state, updated_at FROM runs`). Mutation: `REVOKE USAGE ON SCHEMA` from the login makes the test fail on that positive read (the relation is then not found), not on a refusal.
- Statement kinds: the helper refuses all five kinds (SELECT, INSERT, UPDATE, DELETE, TRUNCATE) for runtime, purge, portal and reset, plus the extra column/`*` selects, and asserts `w.rights(role).get("spend_reservations") is None` for all four.
- Purge: adds an expired-and-unsettled row (kept), a settled row newer than the cutoff (kept) and the open row (kept); purge_spend_reservations deletes only `status='settled' AND closed_at < p_before` (0011). Old rows are aged by the owner so the rule, not the clock, keeps the expired one.
- core-b duplicates strengthened (names kept): month cap over two days (each day's counter == that day's grants, 3 rows); settles below the reserve (5 rows, open ids == new grants, settled_usd 0.10 x 3, new rows open); control (day == month == WORST * admitted).
- New case: settle at exactly the reserved amount, counters stay 3.00, a reserve that raises still raises, 50 refused.
- Races: the interleaving cannot be asserted deterministically, so the docstrings now state that either order is accepted and that no completion-order assertion was added (it would be flaky).
- Mutation proof: month counter read +0.25 (scratch monkeypatch) turns red the strengthened control (`day == month`), two-days, cap-3 and exact-settle cases.

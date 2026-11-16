# PR75 (P4d-a2) round 2: b / i mutants at the final head a8abba0
Builder bP75, 2026-11-09. Raw files: `handover/evidence/PR75/48dcdb8-a8abba0/`. Tool: `mutate75.py` there (one planted mutant at a time in /home/user/build/WT-75, killer selection run with `-x`, file restored in `finally`; `git status` empty before, in the middle and after the chain: status-before/mid/after.txt).

## Environment
- PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), own cluster on 127.0.0.1:56175, started with pgstart.sh pr75x, stopped with pgstop.sh pr75x. CI runs 17.10: NOT run on 17 here.
- `HADAVIN_REQUIRE_PG=1` and `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56175/postgres` were set for the affected run, the full run and every mutant.
- Python 3.13 venv /home/user/build/venv-pr75-313. The mutant run and the full run were at 48dcdb8; a8abba0 only adds one test (`test_the_sweep_skips_a_row_that_another_transaction_holds`), run alone and with its whole file (38 passed) and its mutant re-run.

## Result: 35 of 35 killed, 0 survivors (the one survivor of the first pass, the sweep without SKIP LOCKED, got a test and is now killed)
| mutant | result | killed by |
|---|---|---|
| b15 lock order inverted (run last), vii-a+vii-b+vii-c | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_vii_a_a_reserve_stopped_at_the_run_row_has_not_touched_the_counter_rows |
| b15-vii-b only | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_vii_b_a_reserve_stopped_at_the_day_row_already_holds_the_run_row |
| b15-vii-a only | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_vii_a_a_reserve_stopped_at_the_run_row_has_not_touched_the_counter_rows |
| b15-settle/release order inverted (vii-c) | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_vii_c_a_settle_stopped_at_the_run_row_holds_only_its_reservation_row |
| b11c release/settle guard dropped (counter may go negative) | KILLED | tests/contracts/test_store_reserve.py::test_r1_to_r4_a_release_with_a_damaged_counter_changes_nothing_and_works_after_repair[postgres-run-open] |
| b11d missing/damaged counter on close not an error | KILLED | tests/contracts/test_store_reserve.py::test_a_damaged_counter_refuses_a_lowering_and_leaves_the_row_as_it_was[postgres] |
| b28b ceiling applied to a settle's excess | KILLED | tests/contracts/test_store_reserve.py::test_e3_after_a_settle_past_the_ceiling_only_lowering_writes_still_work[postgres-run] |
| b28c per-call excess bound restored (max(reserved,1)) | KILLED | tests/contracts/test_store_reserve.py::test_e1_e2_a_settle_above_the_reserved_amount_books_the_full_excess_on_all_three_counters[postgres-0.5-5.0-open] |
| b17 kill-switch read takes FOR SHARE | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_reserve_settle_and_release_work_on_a_login_with_select_only_on_the_kill_switch |
| b18c deadline check removed from _exec | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_t4_a_reserve_that_waits_at_two_rows_runs_out_of_budget_before_the_month_statement |
| b13 kill switch not checked (postgres) | KILLED | tests/contracts/test_store_reserve.py::test_the_kill_switch_refuses_a_new_reserve_and_a_replay_but_not_settle_or_release[postgres] |
| b13m kill switch not checked (memory) | KILLED | tests/contracts/test_store_reserve.py::test_the_kill_switch_refuses_a_new_reserve_and_a_replay_but_not_settle_or_release[memory] |
| b16 sweep age uses the Python clock | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_the_sweep_and_the_day_bound_follow_the_database_clock_not_the_python_clock[clock-ahead] |
| b16b sweep without ORDER BY | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_the_sweep_takes_the_oldest_first_and_breaks_ties_by_id |
| b16c sweep result not sorted (RETURNING order) | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_the_sweep_takes_the_oldest_first_and_breaks_ties_by_id |
| b22 day bound from the Python clock | KILLED | tests/contracts/test_store_reserve_proofs_pg.py::test_the_sweep_and_the_day_bound_follow_the_database_clock_not_the_python_clock[clock-ahead] |
| M5 purge unbatched | KILLED | tests/contracts/test_store_writes_pg.py::test_M5_the_statements_are_batches_of_the_configured_size |
| r2-c meta text not scanned (old: memory accepts NUL/surrogate) | KILLED | tests/contracts/test_store_reserve.py::test_meta_text_is_refused_the_same_way_on_both_stores[memory-nul] |
| r2-a reserve reads self._kill.on directly (old: no single helper) | KILLED | tests/contracts/test_memory_lone_caller.py::test_reserve_and_get_kill_switch_read_the_switch_through_the_one_helper |
| r2-e memory counters move before the row is built (old) | KILLED | tests/contracts/test_memory_lone_caller.py::test_a_failure_while_building_the_row_leaves_no_counter_moved |
| r2-d price_cost catches InvalidOperation only (old) | KILLED | tests/contracts/test_cost_rounding.py::test_price_cost_translates_every_decimal_error_to_value_error |
| r2-d2 fake model prices inline, not through price_cost (old) | KILLED | tests/contracts/test_cost_rounding.py::test_the_fake_model_prices_through_price_cost_and_refuses_a_bad_price |
| r2-e trigger lets open->settled carry expired_at (old) | KILLED | tests/contracts/test_store_reserve_pg.py::test_open_to_settled_or_released_keeps_expired_at_null[settled] |
| r2-e sweep claims rows without status guard / skip locked removed | KILLED (re-run after adding a test) | tests/contracts/test_store_reserve_proofs_pg.py::test_the_sweep_skips_a_row_that_another_transaction_holds |
| i10a no rounding | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10b ROUND_DOWN | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10c ROUND_HALF_UP | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10d ROUND_HALF_EVEN | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10e ROUND_HALF_DOWN | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10f ROUND_UP then always add one unit | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10g quantize at 7 decimals | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10g2 quantize at 9 decimals | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10h tiny nonzero cost rounds to zero | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a7] |
| i10i ROUND_05UP | KILLED | tests/contracts/test_cost_rounding.py::test_reply_rounds_the_cost_up[a1] |
| i10j value passes the context before quantize | KILLED | tests/contracts/test_cost_rounding.py::test_helper_keeps_the_last_digit_of_a_29_digit_value |

## b15, test vii-b: FAIL on the mutant, PASS on the real code
Mutant b15: `for which, table, query, key, cap in steps:` becomes `... in sorted(steps, key=lambda s: s[0] == 'run'):` (run counter last). Output on the mutant (`raw-b15-vii-b.txt`, tail):
```
_298e9c31eedc'"
make = <function make.<locals>.build at 0x7feacf9c7b00>
admin = <psycopg.Connection [IDLE] (host=127.0.0.1 port=56175 database=postgres) at 0x7feacf9f82b0>

    def test_vii_b_a_reserve_stopped_at_the_day_row_already_holds_the_run_row(dsn, make, admin):
        _, day, run = _seeded(make)
        store = make()
        drv.execute(
            admin,
            "SELECT 1 FROM spend WHERE agent_id = %s AND day = %s FOR NO KEY UPDATE",
            (AGENT, day),
        )
        thread, result = _start(lambda: _reserve(store, "vii-b", "1", run=run, day=day))
        found = _wait_for_head(dsn, HEAD_DAY)
        assert found is not None, "the reserve never waited at its spend UPDATE"
        assert re.match(HEAD_DAY, found[2])
        run_locked = _probe_fails(
            dsn, "SELECT 1 FROM runs WHERE run_id = %s FOR NO KEY UPDATE NOWAIT", (run.run_id,)
        )
        admin.rollback()
        thread.join(30)
>       assert (
            run_locked is True
        )  # an inverted order (day first) would leave the run row free: that is mutant b15
E       assert False is True

tests/contracts/test_store_reserve_proofs_pg.py:491: AssertionError
=========================== short test summary info ============================
FAILED tests/contracts/test_store_reserve_proofs_pg.py::test_vii_b_a_reserve_stopped_at_the_day_row_already_holds_the_run_row
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 36 deselected in 0.48s

```
Real code, same command line selection (`pytest tests/contracts/test_store_reserve_proofs_pg.py -v -k vii_b`):
```
tests/contracts/test_store_reserve_proofs_pg.py::test_vii_b_a_reserve_stopped_at_the_day_row_already_holds_the_run_row PASSED [100%]
1 passed, 37 deselected in 0.32s
```

## Not run (stated plainly)
- The a1 harness mutants (a1-1 to a1-6 of the ticket): NOT run in this batch; my 60 minute box was spent mostly waiting for a free heavy slot (the chain was queued at 09:12 UTC and started at 09:26 UTC). They are not impossible; they need a rerun.
- Postgres 17.10 (the CI image).
- The 26 deselected tests: all are marked `perf` (`pytest --collect-only -m perf` gives 26, `-m live` gives 0; list by file in deselected-by-file.txt). CI runs them in their own step; not run here.

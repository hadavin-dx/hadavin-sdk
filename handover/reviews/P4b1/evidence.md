# P4b1-a evidence (builder record only; reviewers judge)

Head: see the report. Branch core/P4b1, rebased onto origin/core/P4d-a2 at 7a84408 (its test-only commit landed after the
build started at c31f336; the rebase was done before the final suite runs). Builder: Sonnet. Nothing here is a verdict.

## 0. What failed, what is blocked, what was NOT run (read this first)

BLOCKED (exact missing names; nothing was invented in src):
- `hadavin_sdk.store.protocol.StoreBusy` and the write wrapper (P4d-a2-ii not built). `Meter._is_busy` looks the name up
  at call time (`getattr(store_protocol, "StoreBusy", None)`), so it starts working when P4d-a2-ii lands. Rows that need
  it use a TEST-LOCAL stand-in class bound to that name by monkeypatch, so they prove only the meter's mapping and retry
  logic and say NOTHING about the real class: T1.8 (busy store), T1.9 (reserve busy, settle/release busy), T1.13 (one
  release after StoreBusy), T1.23 (busy once then success; busy every time = exactly 3 settle calls). Mutants M33a and M33b
  (retry count) are killed by the stand-in only. Not re-run against a real StoreBusy: BLOCKED.
- All of P4b1-b (`llm/metered.py`, `MeteredLLM`, `worst_case_micro`, the usage adapter, T7 and the -b rows): blocked on
  P4a-1/P4a-2 names that do not exist in this base (`request_bound`, `REQUESTS_PER_CHAT`, `UsageMissing`/`UnpricedUsage`,
  `PROMPT_BYTES_PER_TOKEN`, `CHARGE_FALLBACK_ATTEMPTS`, `MAX_USAGE_TOKENS_PER_CLASS`, `Reply.unknown_attempts`). Not started.
  Parity rows P7 (usage adapter part), P9 and P14 and the T4.4 scan of `llm/metered.py` are the -b halves: BLOCKED.
  P7 is covered here only for `record(None)`.
- T3 against Intake's own test file: NOT run. The promotion-input copy has no `config/policy.json`, so `tests/test_budget.py`
  cannot be collected (rc=2). Only the pure functions were compared (section 6). The memo-2 figure of 89 passed was not reproduced.

SLIPS / things to look at:
- First mutation run was INVALID: my harness pointed at a wrong test path and counted "no tests ran" as killed (73 false kills).
  Found by reading the first-failure column, fixed (baseline must pass; a kill needs pytest rc 1 and "failed"), whole run redone.
- That honest run found 2 real survivors: M39b (a negative numerator smaller than the denominator returned 0 instead of an
  error) and M9 (an exception raised inside the exit code could replace the body outcome). Both fixed with new tests (section 5).
- One deviation from the frozen T4.2 allow-list: `collections` (for `collections.abc.Callable`/`Iterator`, annotations only)
  is added to the allowed stdlib modules. The ticket list lacked it but meter.py needs it; the alternative was a deprecated
  `typing.Callable` with a suppression. Logged for the lead.
- Mutation run ran on the pre-rebase commits; the rebase added only 30 test lines of P4d (two contract files). Mutants were
  not re-run after the rebase (full suite was).
- M18, M23, M14, M17, M25: M14/M17/M25 are CUT in the ticket. M18 (the settle never consults the kill switch, so there is
  nothing to mutate in the meter) and M23 (`Limits.blocked` is unchanged P4d-side code) have no mutation here.
- First full suite (before the rebase) had 1 failure, `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`
  (no server on the default local socket). It fails identically on the unchanged base (base-dblink.txt) and passed in the
  later runs, so it depends on the machine, not on this change.
- Python 3.12 and 3.13 both ran with a real Postgres (HADAVIN_REQUIRE_PG=1). No `uv` was used: venvs prepared by the lead.
- NOT run: ruff/bandit on `demos/` (this base has no such use in the commands I ran: I ran `ruff check src tests`,
  `ruff format --check src tests`, `bandit -q -r src -ll`); the perf and live marker split (the full run had no marker filter,
  nothing is live: fake store, fake model, no network); the 2-hour-class soak; a real second Postgres kind; CI, CodeQL,
  SonarCloud, CodeRabbit (not available here; lead to watch the PR).

## 1. Rows built and their status

| Row group | File | Tests | Status |
|---|---|---|---|
| T1.1-T1.7 money types | tests/test_money_types.py | 44 | pass |
| T1.8-T1.32 meter against a scripted store | tests/test_meter_unit.py | 100 (6 use the StoreBusy stand-in) | pass; StoreBusy rows BLOCKED (stand-in) |
| T2.1-T2.15 meter + Limits one counter | tests/contracts/test_meter_limits.py | 32 = 16 x memory, postgres | pass |
| T3 parity P1-P3, P5, P6, P8, P10-P13 (+P4 = T5.1, P7 record(None) only) | tests/test_meter_parity.py | 19 | pass; P7/P9/P14 -b halves BLOCKED |
| T4.1-T4.4 import hygiene, literal scan | tests/test_meter_no_db_import.py | 18 | pass (llm/metered.py scan: -b, BLOCKED) |
| T5.1-T5.5 processes (spawn, Postgres, runtime role) | tests/test_meter_processes.py | 5 | pass (T5.1 and T5.2 are one test; T5.4 has 2 variants) |
| T6.1-T6.8 contract rows | tests/contracts/test_meter.py | 16 = 8 x 2 | pass |

T5.1 numbers: 8 spawned workers x 6 attempts of 50,000 micro-dollars against a cap of 1.000000 USD: exactly 20 granted,
28 refused, counter = 1.000000 before the settles and 0.500000 after each settled at half. The T5 file did not trip the
lock-in guard (it imports no driver; `tests/test_lockin_guard.py` passes), so no allow-list change was needed.

## 2. Suites (gate = pytest exit code)

- Python 3.12: `HADAVIN_REQUIRE_PG=1 HADAVIN_TEST_PG_DSN=<local postgres, database p4b1> PYTHONPATH=src heavy.sh venv312/python -m pytest -q -rs`
  result: 10590 passed, 1 skipped, rc=0 (suite312.log). Skip: tests/contracts/test_llm.py:95 (a Stubber reason, not mine).
- Python 3.13 (same command, venv313): 10590 passed, 1 skipped, rc=0 (suite313-final.log), run on the final rebased head.
- ruff check src tests: All checks passed. ruff format --check src tests: 290 files already formatted. bandit -q -r src -ll: rc=0 (lint.txt).

## 3. Fail-before (BN-6)

`git worktree add <dir> ce70eb5`, only tests/contracts/test_meter_limits.py copied, hadavin_sdk resolved INSIDE the worktree
(printed path under the worktree, resolve rc=0), then `pytest tests/contracts/test_meter_limits.py -k check_then_spend`:

```
before/src/hadavin_sdk/__init__.py
resolve rc=0
FF                                                                       [100%]
=================================== FAILURES ===================================
___________________ test_t2_8_check_then_spend_race[memory] ____________________
store = <hadavin_sdk.store.memory.MemoryStore object at 0x7f10dd9486e0>
    def test_t2_8_check_then_spend_race(store):
        limits = make_limits(store, daily="1.00")
        granted = _race(limits)
        total = store.spend_totals("ag", datetime.now(UTC).date())[0]
>       assert total <= D("1.00"), f"day total {total} passed the 1.00 cap"
E       AssertionError: day total 3.20 passed the 1.00 cap
E       assert Decimal('3.20') <= Decimal('1.00')
E        +  where Decimal('1.00') = D('1.00')
tests/contracts/test_meter_limits.py:267: AssertionError
__________________ test_t2_8_check_then_spend_race[postgres] ___________________
store = <tests.contracts.kinds.store_postgres._SplitStore object at 0x7f10de0a3cb0>
    def test_t2_8_check_then_spend_race(store):
        limits = make_limits(store, daily="1.00")
        granted = _race(limits)
        total = store.spend_totals("ag", datetime.now(UTC).date())[0]
>       assert total <= D("1.00"), f"day total {total} passed the 1.00 cap"
E       AssertionError: day total 3.20 passed the 1.00 cap
E       assert Decimal('3.20') <= Decimal('1.00')
E        +  where Decimal('1.00') = D('1.00')
tests/contracts/test_meter_limits.py:267: AssertionError
=========================== short test summary info ============================
FAILED tests/contracts/test_meter_limits.py::test_t2_8_check_then_spend_race[memory]
FAILED tests/contracts/test_meter_limits.py::test_t2_8_check_then_spend_race[postgres]
2 failed, 30 deselected in 0.80s
pytest rc=1
```

The total 3.20 equals the ticket's measured value. Never run against the new tree. The worktree was removed afterwards.
T1, T3-T6 and the other T2 rows are new features: "new feature; killed by mutants" (section 5). T2.11a is a regression pin that
already passes on ce70eb5 (killed by M29).

## 4. Rung table (ladder v2: 1 no-code, 2 core modules, 3 existing free tools, 4 free libraries, 5 own code)

| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| money.py SpendMicro, BusinessMoney | whole micro-dollars, exact, round up once, no mixing | 4 (a money library) | UNVERIFIED (no doc fetched) | a spend type that refuses int/float/Decimal/business money | KEEP-CODE |
| Meter.reserve/settle/release, release and error tables | reserve before the call, idempotent settle, fail closed | 2/3 (a client LLM gateway key budget) | ticket BN-33 table: lead gateway check 2026-11-06 did not show our guarantees | reserve and settle per run; a replay returns the first result | KEEP-CODE |
| Meter.hold, exit settle, overshoot signal | settle on every exit incl. KeyboardInterrupt | 5 only | ticket | a `finally` around the model call | KEEP-CODE |
| Limits.caps / Limits.hold | caps from the registry; one lazy Meter | 1/2 (registry already holds caps) | registry.py AgentRecord | about 70 lines of glue | KEEP-CODE (the glue) |
| spend_day, orphan_age_s | UTC budget day, orphan age floor | 5 | ticket | the one day expression shared with Limits | KEEP-CODE |

(The ticket's BN-33 table numbers its rungs 1 studio code .. 7 our code; the verdicts are the same.)

## 5. Mutants (M1-M57 live set; every id applied one at a time, tree restored, `git status` empty before and after)

Harness: mutate.py (this folder); baseline must pass first; a mutant is KILLED only on pytest rc 1 with failures. Tests used:
the seven files above, memory kinds only (`-k "not postgres"`); Postgres rows run in the full suite.
Result on the final run: 78 applied, 78 KILLED, 0 SURVIVED, 0 invalid, 0 not applied. Fixes made because of survivors:
M39b -> added (-1, 1_000_000) and (-5, 7) to the T1.5 refusal list; M9 -> new test
`test_t1_22_a_bug_inside_the_exit_never_replaces_the_body_outcome`.
M33a/M33b depend on the StoreBusy stand-in (BLOCKED for the real class). Ids with several variants: M1a/b, M3a/b, M4a/b, M5a-c,
M7a/b, M8a/b, M10a (= M42a), M42b, M13a/b, M15a-d, M16a-c, M32a-c, M36a/b, M38a/b, M39a/b, M40a/b, M43a/b, M44a/b, M46a/b,
M51a/b, M55a, M57a/b. Not mutated: M14, M17, M25 (CUT), M18, M23 (see section 0).

| id | result | first failing test / note |
|---|---|---|
| M1a | KILLED | FAILED tests/test_money_types.py::test_t1_5_ceil_cost_rounds_up_once - assert...  |
| M1b | KILLED | FAILED tests/test_money_types.py::test_t1_5_ceil_cost_rounds_up_once - assert...  |
| M2 | KILLED | FAILED tests/test_money_types.py::test_t1_3_from_usd_has_the_same_verdict_as_check_usd[0.0000001]  |
| M3a | KILLED | FAILED tests/test_money_types.py::test_t1_1_constructor_refuses_everything_but_an_exact_in_range_int[True]  |
| M3b | KILLED | FAILED tests/test_money_types.py::test_t1_6_operators - Failed: DID NOT RAISE...  |
| M4a | KILLED | FAILED tests/test_money_types.py::test_t1_7_business_money - Failed: DID NOT ...  |
| M4b | KILLED | FAILED tests/test_money_types.py::test_t1_7_business_money - AssertionError: ...  |
| M5a | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M5b | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M5c | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M6 | KILLED | FAILED tests/test_meter_unit.py::test_t1_9_reserve_busy_and_overbudget_rows  |
| M7a | KILLED | FAILED tests/test_meter_unit.py::test_t1_12_lost_acknowledgement_releases_exactly_once  |
| M7b | KILLED | FAILED tests/test_meter_unit.py::test_t1_12_lost_acknowledgement_releases_exactly_once  |
| M8a | KILLED | FAILED tests/test_meter_unit.py::test_t1_21_settles_when_the_body_raises[RuntimeError]  |
| M8b | KILLED | FAILED tests/test_meter_unit.py::test_t1_21_settles_when_the_body_raises[KeyboardInterrupt]  |
| M10a | KILLED | FAILED tests/test_meter_unit.py::test_t1_16_second_settle_returns_the_first_result (= M42a) |
| M42b | KILLED | FAILED tests/test_meter_unit.py::test_t1_16_second_settle_returns_the_first_result  |
| M11a | KILLED | FAILED tests/test_meter_unit.py::test_t1_19_record_and_release_rules - Failed... (record and settle) |
| M12 | KILLED | FAILED tests/test_meter_unit.py::test_t1_19_record_and_release_rules - Assert...  |
| M13a | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_overshoot_signal[True-True] - ass...  |
| M13b | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_overshoot_signal[True-True] - ass...  |
| M15a | KILLED | FAILED tests/test_meter_unit.py::test_t1_26_age_follows_the_injected_monotonic_clock  |
| M15b | KILLED | FAILED tests/test_meter_unit.py::test_t1_26_orphan_age[298-601] - assert 600 ...  |
| M15c | KILLED | FAILED tests/test_meter_unit.py::test_t1_26_orphan_age[1-600] - assert 7 == 600  |
| M15d | KILLED | FAILED tests/test_meter_unit.py::test_t1_26_default_hold_and_range - Failed: ...  |
| M16a | KILLED | FAILED tests/test_meter_unit.py::test_t1_28_clock_none_resolves_models_now_at_call_time  |
| M16b | KILLED | FAILED tests/test_meter_unit.py::test_t1_30_the_cap_day_is_utc_at_midnight_under_a_non_utc_zone  |
| M16c | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_6_charge_blocked_and_hold_read_the_same_day_at_midnight[memory] (limits binding replaced by models.now) |
| M19 | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M20 | KILLED | FAILED tests/test_meter_unit.py::test_t1_28_a_store_with_missing_methods_is_refused  |
| M22 | KILLED | FAILED tests/test_meter_unit.py::test_t1_29_the_meter_has_no_sweep_prune_or_delete_name  |
| M24 | KILLED | FAILED tests/test_meter_unit.py::test_t1_8_busy_store_never_reaches_the_model_call  |
| M26 | KILLED | FAILED tests/test_meter_unit.py::test_t1_14_arguments - Failed: DID NOT RAISE...  |
| M27 | KILLED | ERROR    hadavin_sdk.meter:meter.py:423 settle failed: reservation rsv-7bf0bdddc17544e39317abe894e0d060 kept open, planned 9 micro-dollars,   |
| M28 | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_a_raising_callback_is_logged_by_class_and_does_not_escape  |
| M46a | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_a_raising_callback_is_logged_by_class_and_does_not_escape  |
| M30 | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M31 | KILLED | FAILED tests/test_meter_unit.py::test_t1_11_reason_table - AssertionError: as...  |
| M32a | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M32b | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M32c | KILLED | FAILED tests/test_meter_unit.py::test_t1_10_overbudget_numbers_for_run_day_and_month  |
| M33a | KILLED | ERROR    hadavin_sdk.meter:meter.py:423 settle failed: reservation rsv-052b9173832d4c69a272799cdfe0c78c kept open, planned 30 micro-dollars, (STAND-IN) |
| M33b | KILLED | ERROR    hadavin_sdk.meter:meter.py:423 settle failed: reservation rsv-b441d6ac19474766885952d3b4e45626 kept open, planned 30 micro-dollars, (STAND-IN) |
| M33c | KILLED | FAILED tests/test_meter_unit.py::test_t1_19_record_and_release_rules - Assert...  |
| M34 | KILLED | FAILED tests/test_meter_unit.py::test_t1_22_the_bodys_exception_wins_over_a_failing_exit  |
| M35 | KILLED | ERROR    hadavin_sdk.meter:meter.py:423 settle failed: reservation rsv-a55accc43c1648f89edcfcc1b359f6dd kept open, planned 10 micro-dollars,  |
| M36a | KILLED | FAILED tests/test_meter_unit.py::test_t1_12_interrupts_release_and_re_raise_unchanged[KeyboardInterrupt]  |
| M36b | KILLED | FAILED tests/test_meter_unit.py::test_t1_12_interrupts_release_and_re_raise_unchanged[KeyboardInterrupt]  |
| M37 | KILLED | FAILED tests/test_money_types.py::test_t1_6_operators - Failed: DID NOT RAISE...  |
| M38a | KILLED | FAILED tests/test_money_types.py::test_t1_1_constructor_refuses_everything_but_an_exact_in_range_int[1000000000000000001]  |
| M38b | KILLED | FAILED tests/test_money_types.py::test_t1_2_bound_is_exact - ValueError: micr...  |
| M39a | KILLED | FAILED tests/test_money_types.py::test_t1_5_ceil_cost_rounds_up_once - ZeroDi...  |
| M39b | KILLED | FAILED tests/test_money_types.py::test_t1_5_ceil_cost_rounds_up_once - Failed...  |
| M40a | KILLED | FAILED tests/test_money_types.py::test_t1_7_business_money - Failed: DID NOT ...  |
| M40b | KILLED | FAILED tests/test_money_types.py::test_t1_7_business_money - Failed: DID NOT ...  |
| M41 | KILLED | FAILED tests/test_meter_unit.py::test_t1_19_record_and_release_rules - Assert...  |
| M43a | KILLED | FAILED tests/test_meter_unit.py::test_t1_13_no_release_when_the_store_answered[<lambda>5]  |
| M43b | KILLED | FAILED tests/test_meter_unit.py::test_t1_13_no_release_when_the_store_answered[<lambda>2]  |
| M44a | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_9_caps_from_the_registry_rounded_down[memory]  |
| M44b | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_9_caps_from_the_registry_rounded_down[memory]  |
| M45 | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_11b_charge_with_spend_micro_books_the_same_row_and_business_money_is_refused[memory]  |
| M47 | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_10_eight_threads_on_first_use_build_one_meter[memory]  |
| M48 | KILLED | FAILED tests/test_meter_unit.py::test_t1_9_reserve_error_table[<lambda>-counter_damaged]  |
| M49 | KILLED | FAILED tests/test_meter_unit.py::test_t1_9_reserve_error_table[<lambda>-unknown_run]  |
| M50 | KILLED | FAILED tests/test_meter_unit.py::test_t1_9_reserve_error_table[<lambda>-conflict0]  |
| M51a | KILLED | ERROR    hadavin_sdk.meter:meter.py:424 settle failed: reservation rsv-557fce66b51e4c08a50e146f5e79f077 kept open, planned 30 micro-dollars,  |
| M51b | KILLED | FAILED tests/test_meter_unit.py::test_t1_16_second_settle_returns_the_first_result  |
| M52 | KILLED | FAILED tests/test_meter_no_db_import.py::test_t4_4_no_numeric_literal_but_0_1_minus1[money.py]  |
| M53 | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_overshoot_signal[False-True] - As...  |
| M54 | KILLED | FAILED tests/test_meter_unit.py::test_t1_17_release_after_settle_and_settle_after_release  |
| M55a | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_overshoot_signal[True-False] - as...  |
| M21 | KILLED | FAILED tests/test_meter_no_db_import.py::test_t4_1_a_clean_interpreter_imports_the_meter_without_a_database_library  |
| M46b | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_12_a_settle_above_the_reservation_books_the_full_actual_once[memory] (callbacks read once) |
| M56 | KILLED | FAILED tests/test_meter_unit.py::test_t1_20_overshoot_signal[True-True] - Ass... (standalone settle calls on_overshoot) |
| M57a | KILLED | FAILED tests/test_meter_unit.py::test_t1_31_an_old_hold_writes_exactly_one_line_at_exit (over-age line at the limit) |
| M57b | KILLED | FAILED tests/test_meter_unit.py::test_t1_31_an_old_hold_writes_exactly_one_line_at_exit (over-age line dropped) |
| M9 | KILLED | FAILED tests/test_meter_unit.py::test_t1_22_a_bug_inside_the_exit_never_replaces_the_body_outcome (exit failure replaces the body's exception) |
| M29 | KILLED | FAILED tests/contracts/test_meter_limits.py::test_t2_1_a_hold_after_a_charge_is_refused_by_the_daily_cap[memory] (Limits.charge stops booking) |


## 6. Parity with Intake (BN-7)

```
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s
rc=2
INTAKE worst_case read     : 6620 (expect 6620)
INTAKE worst_case fallback : 26480 (expect 26480)
INTAKE ceil rows: 1 38
NOTE: the throwaway copy of intake-a12 does not hold its policy.json, so tests/test_budget.py cannot be collected there
(rc=2 above). Per the ticket this falls back to the pure functions only (worst_case printed above). The Intake test
file itself was therefore NOT run; the 89-passed figure of memo-2 was NOT reproduced by this build.
```
Core side of the same arithmetic: `SpendMicro.ceil_cost(333_334)` = 1 and `ceil_cost(38_000_000)` = 38 (test P8 passes).

## 7. Other

- Import hygiene (T4.1): a clean interpreter importing hadavin_sdk.meter, money and limits has none of psycopg, sqlite3, boto3 in sys.modules (test T4.1 passes).
- Pushed content check: no home path, no model id and no build-folder name in the diff (grep of the added lines, empty).
- Constants: 8 new names in defaults.py (METER_MAX_HOLD_S, METER_MAX_HOLD_LIMIT_S, METER_ORPHAN_AGE_S, METER_ORPHAN_FACTOR,
  METER_ORPHAN_MARGIN_S, METER_SETTLE_RETRIES, MICRO_DECIMALS, MICRO_PER_USD) plus the assert that ties the last two.
- Database p4b1 on the shared local cluster is dropped at the end; the cluster itself was not touched.

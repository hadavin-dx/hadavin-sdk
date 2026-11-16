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

| test (all its parameter cases) | fa3f8c1b + head test file: pass / fail | first line of each distinct failure | origin/main + head test file: pass / fail | first line of each distinct failure |
|---|---|---|---|---|
| test_a_linear_cost_passes_at_any_speed | 10 / 0 | - | 0 / 10 | x10 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_an_n_log_n_cost_passes_at_any_speed | 8 / 0 | - | 0 / 8 | x8 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_a_quadratic_cost_is_flagged_at_any_speed | 12 / 0 | - | 0 / 12 | x12 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_the_smallest_exponent_a_gap_flags | 0 / 3 | x3 `AttributeError: module 'tests.fixtures.timing' has no attribute 'smallest_exponent_flagged'` | 0 / 3 | x3 `AttributeError: module 'tests.fixtures.timing' has no attribute 'smallest_exponent_flagged'` |
| test_the_limit_is_three_times_the_size_ratio | 1 / 0 | - | 1 / 0 | - |
| test_a_fast_small_run_is_not_raised_to_a_floor | 1 / 0 | - | 0 / 1 | x1 `AssertionError: a 1 ms small run was raised to a floor` |
| test_a_small_run_that_is_not_a_time_is_refused_not_passed | 5 / 0 | - | 0 / 5 | x5 `Failed: DID NOT RAISE ValueError` |
| test_a_big_run_that_is_not_a_time_is_refused_not_passed | 0 / 5 | x5 `Failed: DID NOT RAISE ValueError` | 0 / 5 | x5 `Failed: DID NOT RAISE ValueError` |
| test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work | 0 / 6 | x4 `AttributeError: module 'tests.fixtures.timing' has no attribute 'smallest_exponent_flagged'`; x2 `Failed: DID NOT RAISE ValueError` | 0 / 6 | x5 `Failed: DID NOT RAISE ValueError`; x1 `ZeroDivisionError: division by zero` |
| test_a_gap_of_exactly_four_is_the_smallest_allowed | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'check_sizes'` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'check_sizes'` |
| test_an_empty_unit_is_refused_before_any_work | 0 / 1 | x1 `ZeroDivisionError: integer division or modulo by zero` | 0 / 1 | x1 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_a_call_too_fast_to_time_is_refused_not_passed | 1 / 0 | - | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'MAX_CALLS'` |
| test_one_call_is_measured_to_its_true_time | 0 / 5 | x5 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call_each'. Did you mean: 'seconds_per_call'?` | 0 / 5 | x5 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_a_fast_call_is_batched_to_the_batch_length_and_repeated_five_times | 0 / 1 | x1 `AssertionError: the five repeats that count have the same number of calls` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_a_pause_while_the_batch_is_sized_cannot_shorten_the_batches_that_count | 0 / 1 | x1 `AssertionError: a pause while the batch was sized left the batches too short` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_a_slow_call_is_run_once_to_size_the_batch_and_once_in_each_of_five_repeats | 0 / 1 | x1 `AssertionError: one sizing call and five repeats` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_the_two_sizes_take_turns | 0 / 1 | x1 `AssertionError: each size is sized once first` | 0 / 1 | x1 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_a_coarse_clock_cannot_turn_a_fast_call_into_zero | 2 / 0 | - | 0 / 2 | x2 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_a_pause_in_four_of_five_batches_changes_nothing | 1 / 2 | x2 `AssertionError: linear, with pauses` | 0 / 3 | x3 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_a_slow_spell_over_several_batches_in_a_row_changes_nothing | 2 / 6 | x6 `AssertionError: quadratic, with a slow spell` | 0 / 8 | x8 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_the_collector_is_off_while_the_clock_runs_and_back_on_after | 0 / 1 | x1 `AssertionError: one sizing call and five repeats` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'seconds_per_call'` |
| test_the_clock_is_processor_time_except_on_windows | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'CLOCK'` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'CLOCK'` |
| test_the_work_gets_the_unit_repeated_to_exactly_the_two_sizes | 1 / 0 | - | 0 / 1 | x1 `TypeError: is_superlinear() got an unexpected keyword argument 'clock'` |
| test_a_sweep_names_each_slow_case_and_each_case_it_could_not_time | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'problems'` | 0 / 1 | x1 `AttributeError: module 'tests.fixtures.timing' has no attribute 'MAX_CALLS'` |
total fa3f8c1: pass 44 fail 36
total main: pass 1 fail 79

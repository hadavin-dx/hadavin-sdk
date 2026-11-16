Step 1 and 2 tallies (per test: pass/fail counts, seconds)
```
== s1-head
start 2026-11-11T16:07:39Z load 3.50 7.67 9.16 5/206 22264
middle(run 30) 2026-11-11T16:09:08Z load 4.70 6.98 8.78 6/218 24663
end 2026-11-11T16:10:34Z load 3.79 6.19 8.34 6/216 27666
DONE
runs: 60 exit codes: {'0': 60}
process wall seconds: min 2.55 median 2.83 max 3.88
test_the_timing_harness_flags_a_quadratic_stand_in: {'passed': 60} test seconds min 1.195 median 1.291 max 2.443
test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[linear]: {'passed': 60} test seconds min 0.310 median 0.392 max 0.740
test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[n-log-n]: {'passed': 60} test seconds min 0.289 median 0.320 max 0.728
test_the_timing_harness_flags_a_quadratic_stand_in_that_is_fast_on_the_small_input: {'passed': 60} test seconds min 0.300 median 0.366 max 0.703
distinct failures: 0
== s1-main
start 2026-11-11T16:10:34Z load 3.79 6.19 8.34 5/216 27671
middle(run 15) 2026-11-11T16:10:47Z load 4.22 6.16 8.30 3/218 28083
end 2026-11-11T16:11:02Z load 4.03 6.02 8.22 6/207 29163
DONE
runs: 30 exit codes: {'0': 11, '1': 19}
process wall seconds: min 0.85 median 0.94 max 1.15
test_the_timing_harness_flags_a_quadratic_stand_in: {'passed': 11, 'failure': 19} test seconds min 0.532 median 0.566 max 0.698
distinct failures: 1
  x19 test_the_timing_harness_flags_a_quadratic_stand_in: E       AssertionError: a quadratic function must be flagged
== s2
start 2026-11-11T16:11:02Z load 4.03 6.02 8.22 5/207 29167
middle(run 10) 2026-11-11T16:11:13Z load 4.33 6.02 8.19 6/203 29507
end 2026-11-11T16:11:26Z load 4.40 5.95 8.14 6/207 30426
DONE
runs: 20 exit codes: {'0': 20}
process wall seconds: min 1.07 median 1.20 max 1.47
test_a_linear_cost_passes_at_any_speed[1e-09-gap4]: {'passed': 20} test seconds min 0.025 median 0.027 max 0.037
test_a_linear_cost_passes_at_any_speed[1e-09-gap16]: {'passed': 20} test seconds min 0.021 median 0.023 max 0.050
test_a_linear_cost_passes_at_any_speed[1e-08-gap4]: {'passed': 20} test seconds min 0.003 median 0.003 max 0.006
test_a_linear_cost_passes_at_any_speed[1e-08-gap16]: {'passed': 20} test seconds min 0.002 median 0.003 max 0.004
test_a_linear_cost_passes_at_any_speed[1e-07-gap4]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.001
test_a_linear_cost_passes_at_any_speed[1e-07-gap16]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.001
test_a_linear_cost_passes_at_any_speed[1e-05-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_linear_cost_passes_at_any_speed[1e-05-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_linear_cost_passes_at_any_speed[0.001-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_linear_cost_passes_at_any_speed[0.001-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_an_n_log_n_cost_passes_at_any_speed[1e-10-gap4]: {'passed': 20} test seconds min 0.023 median 0.026 max 0.043
test_an_n_log_n_cost_passes_at_any_speed[1e-10-gap16]: {'passed': 20} test seconds min 0.020 median 0.022 max 0.036
test_an_n_log_n_cost_passes_at_any_speed[1e-09-gap4]: {'passed': 20} test seconds min 0.003 median 0.003 max 0.005
test_an_n_log_n_cost_passes_at_any_speed[1e-09-gap16]: {'passed': 20} test seconds min 0.002 median 0.003 max 0.005
test_an_n_log_n_cost_passes_at_any_speed[1e-07-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_an_n_log_n_cost_passes_at_any_speed[1e-07-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_an_n_log_n_cost_passes_at_any_speed[1e-05-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_an_n_log_n_cost_passes_at_any_speed[1e-05-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-11-gap4]: {'passed': 20} test seconds min 0.002 median 0.003 max 0.007
test_a_quadratic_cost_is_flagged_at_any_speed[1e-11-gap16]: {'passed': 20} test seconds min 0.002 median 0.003 max 0.004
test_a_quadratic_cost_is_flagged_at_any_speed[1e-10-gap4]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-10-gap16]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_a_quadratic_cost_is_flagged_at_any_speed[1e-09-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-09-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-07-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-07-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-06-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-06-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.003
test_a_quadratic_cost_is_flagged_at_any_speed[1e-05-gap4]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_quadratic_cost_is_flagged_at_any_speed[1e-05-gap16]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_the_smallest_exponent_a_gap_flags[gap4]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_the_smallest_exponent_a_gap_flags[gap8]: {'passed': 20} test seconds min 0.002 median 0.002 max 0.004
test_the_smallest_exponent_a_gap_flags[gap16]: {'passed': 20} test seconds min 0.003 median 0.004 max 0.006
test_the_limit_is_three_times_the_size_ratio: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_fast_small_run_is_not_raised_to_a_floor: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_small_run_that_is_not_a_time_is_refused_not_passed[0.0]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_small_run_that_is_not_a_time_is_refused_not_passed[-0.001]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_small_run_that_is_not_a_time_is_refused_not_passed[nan]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_small_run_that_is_not_a_time_is_refused_not_passed[inf]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_small_run_that_is_not_a_time_is_refused_not_passed[-inf]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_big_run_that_is_not_a_time_is_refused_not_passed[0.0]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_big_run_that_is_not_a_time_is_refused_not_passed[-0.001]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_big_run_that_is_not_a_time_is_refused_not_passed[nan]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_big_run_that_is_not_a_time_is_refused_not_passed[inf]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_big_run_that_is_not_a_time_is_refused_not_passed[-inf]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[swapped]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[equal]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[negative]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[zero]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[just-under-4x]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work[2x]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_gap_of_exactly_four_is_the_smallest_allowed: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_an_empty_unit_is_refused_before_any_work: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_call_too_fast_to_time_is_refused_not_passed: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_one_call_is_measured_to_its_true_time[1e-09]: {'passed': 20} test seconds min 0.045 median 0.048 max 0.071
test_one_call_is_measured_to_its_true_time[1e-08]: {'passed': 20} test seconds min 0.005 median 0.006 max 0.013
test_one_call_is_measured_to_its_true_time[1e-07]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_one_call_is_measured_to_its_true_time[1e-05]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_one_call_is_measured_to_its_true_time[0.001]: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_a_fast_call_is_batched_to_the_batch_length_and_repeated_five_times: {'passed': 20} test seconds min 0.020 median 0.022 max 0.041
test_a_pause_while_the_batch_is_sized_cannot_shorten_the_batches_that_count: {'passed': 20} test seconds min 0.016 median 0.019 max 0.033
test_a_slow_call_is_run_once_to_size_the_batch_and_once_in_each_of_five_repeats: {'passed': 20} test seconds min 0.000 median 0.000 max 0.001
test_the_two_sizes_take_turns: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_coarse_clock_cannot_turn_a_fast_call_into_zero[0.001]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.001
test_a_coarse_clock_cannot_turn_a_fast_call_into_zero[0.005]: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_a_pause_in_four_of_five_batches_changes_nothing[0.007]: {'passed': 20} test seconds min 0.049 median 0.053 max 0.105
test_a_pause_in_four_of_five_batches_changes_nothing[0.5]: {'passed': 20} test seconds min 0.081 median 0.086 max 0.169
test_a_pause_in_four_of_five_batches_changes_nothing[30.0]: {'passed': 20} test seconds min 0.082 median 0.086 max 0.154
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[0.5-2]: {'passed': 20} test seconds min 0.035 median 0.037 max 0.055
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[0.5-3]: {'passed': 20} test seconds min 0.035 median 0.041 max 0.054
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[0.5-4]: {'passed': 20} test seconds min 0.035 median 0.038 max 0.045
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[0.5-5]: {'passed': 20} test seconds min 0.034 median 0.038 max 0.056
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[30.0-2]: {'passed': 20} test seconds min 0.035 median 0.037 max 0.050
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[30.0-3]: {'passed': 20} test seconds min 0.035 median 0.037 max 0.052
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[30.0-4]: {'passed': 20} test seconds min 0.035 median 0.037 max 0.070
test_a_slow_spell_over_several_batches_in_a_row_changes_nothing[30.0-5]: {'passed': 20} test seconds min 0.035 median 0.037 max 0.068
test_the_collector_is_off_while_the_clock_runs_and_back_on_after: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_the_clock_is_processor_time_except_on_windows: {'passed': 20} test seconds min 0.001 median 0.001 max 0.002
test_the_work_gets_the_unit_repeated_to_exactly_the_two_sizes: {'passed': 20} test seconds min 0.000 median 0.000 max 0.000
test_a_sweep_names_each_slow_case_and_each_case_it_could_not_time: {'passed': 20} test seconds min 0.002 median 0.002 max 0.006
distinct failures: 0
```
Step 4 (under 8 busy loops): per run 'number, exit code, seconds, load before, start second'
```
queued 2026-11-11T16:13:03Z load 4.00 5.33 7.70 5/180 2664
slot-got 2026-11-11T16:13:03Z load 4.00 5.33 7.70 4/183 2670
burners  2671 2672 2673 2674 2675 2676 2677 2678
runs-done 2026-11-11T16:16:38Z load 12.99 9.56 8.93 12/202 8925 busy-loops-alive: 8
stopped 2026-11-11T16:16:38Z load 12.99 9.56 8.93 3/186 8930 busy-loops-alive: 0
heavy-rc=0 finished 2026-11-11T16:16:38Z load 12.99 9.56 8.93 5/183 8935
1 0 5.068003979 load-before: 4.56 5.43 7.71 14/199 started-at-sec: 0
2 0 13.676410169 load-before: 5.24 5.55 7.74 13/197 started-at-sec: 5
3 0 24.867690503 load-before: 6.96 5.92 7.83 13/195 started-at-sec: 19
4 0 14.322650288 load-before: 10.06 6.74 8.05 12/194 started-at-sec: 44
5 0 25.708808164 load-before: 10.72 7.05 8.13 15/215 started-at-sec: 58
6 0 27.475648541 load-before: 11.93 7.63 8.29 16/224 started-at-sec: 84
7 0 15.266593442 load-before: 12.56 8.19 8.46 14/212 started-at-sec: 111
8 0 11.065747806 load-before: 13.05 8.51 8.56 13/218 started-at-sec: 127
9 0 14.429862145 load-before: 12.97 8.64 8.60 12/211 started-at-sec: 138
10 0 8.703467022 load-before: 12.91 8.84 8.67 26/219 started-at-sec: 152
11 0 9.423918485 load-before: 12.92 8.91 8.69 12/208 started-at-sec: 161
12 0 13.977407316 load-before: 12.93 9.04 8.74 13/209 started-at-sec: 170
13 0 12.955549744 load-before: 13.10 9.27 8.82 13/208 started-at-sec: 185
14 0 12.033493247 load-before: 13.07 9.45 8.89 13/211 started-at-sec: 197
runs: 14 exit codes: {'0': 14}
process wall seconds: min 5.07 median 13.98 max 27.48
test_the_timing_harness_flags_a_quadratic_stand_in: {'passed': 14} test seconds min 2.840 median 7.015 max 14.621
test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[linear]: {'passed': 14} test seconds min 0.329 median 2.138 max 3.203
test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[n-log-n]: {'passed': 14} test seconds min 0.306 median 1.615 max 4.543
test_the_timing_harness_flags_a_quadratic_stand_in_that_is_fast_on_the_small_input: {'passed': 14} test seconds min 0.373 median 1.834 max 4.142
distinct failures: 0
```

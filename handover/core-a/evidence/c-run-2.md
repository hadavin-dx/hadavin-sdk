# c-run-2 (perf run, core-c head)

Command: cd /tmp/ca-c-run && uptime && (time uv run --all-extras --group test pytest -q -n 0 -m perf -p no:cacheprovider --durations=15 tests/test_redact_fold_budget.py tests/test_k5_perf.py tests/test_textnorm_perf.py tests/test_textnorm_round2.py tests/test_redact_finder_cap.py tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py -rfE > /tmp/ca-c-run2.log 2>&1)
SHA: 9072e701faa8fcdc94a256fd0a6c03eb2b008621
Load: start 0.60 (1-min; no wait needed), end 1.80 (1-min), max sampled 1.95 (15 s `uptime` samples, 14 samples: 0.55 0.65 0.80 0.84 0.95 1.12 1.38 1.52 1.63 1.64 1.79 1.84 1.94 1.95). Load was below 2 throughout, but rose during the run (the run itself is single-process CPU-bound).
Wall: real 3m29.363s (user 3m25.8s sys 2.0s); pytest reported 208.76s.

## Last 5 lines verbatim
```
5.10s call     tests/test_k5_perf.py::test_redact_untrusted_end_to_end_is_not_super_linear_with_views[fullwidth]
5.01s call     tests/test_textnorm_perf.py::test_scan_needles_and_the_script_views_of_a_text_at_the_cap_are_built_in_linear_time
4.83s call     tests/test_textnorm_round2.py::test_perf_the_chunked_read_at_its_ceiling_is_not_flagged_and_stays_within_the_bound[ascii]
4.49s call     tests/test_k5_perf.py::test_redact_untrusted_end_to_end_is_not_super_linear_with_views[zero-width]
39 passed, 462 deselected in 208.76s (0:03:28)
```

## Counts
39 passed, 0 failed, 0 errors, 462 deselected.
Failing ids: none.

## --durations=15 verbatim
```
============================= slowest 15 durations =============================
40.13s call     tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse
28.80s call     tests/test_k5_perf.py::test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated
13.59s call     tests/test_redact_settle_loop.py::test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit[scaled-curl -u ]
11.78s call     tests/test_textnorm_round2.py::test_perf_the_chunked_read_at_its_ceiling_is_not_flagged_and_stays_within_the_bound[cyrillic]
10.82s call     tests/test_redact_fold_budget.py::test_align_1_the_per_character_class_agrees_with_the_fold_for_every_code_point
8.59s call     tests/test_redact_settle_loop.py::test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit[scaled-password=]
8.01s call     tests/test_redact_settle_loop.py::test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit[None-curl -u ]
7.82s call     tests/test_textnorm_perf.py::test_scan_views_of_a_text_at_the_cap_is_built_in_linear_time
6.71s call     tests/test_redact_fold_budget.py::test_130k_short_non_ascii_lines_cost_a_small_multiple_of_ascii_lines
6.68s call     tests/test_textnorm_perf.py::test_the_one_inserted_letter_match_is_linear_for_a_text_built_to_defeat_it
5.31s call     tests/test_redact_settle_loop.py::test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit[None-password=]
5.10s call     tests/test_k5_perf.py::test_redact_untrusted_end_to_end_is_not_super_linear_with_views[fullwidth]
5.01s call     tests/test_textnorm_perf.py::test_scan_needles_and_the_script_views_of_a_text_at_the_cap_are_built_in_linear_time
4.83s call     tests/test_textnorm_round2.py::test_perf_the_chunked_read_at_its_ceiling_is_not_flagged_and_stays_within_the_bound[ascii]
4.49s call     tests/test_k5_perf.py::test_redact_untrusted_end_to_end_is_not_super_linear_with_views[zero-width]
```

## Called out
- tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse: 40.13s (passed)
- test_redact_finder_cap.py::test_t10_e14_shape_is_refused and ::test_t11_the_real_constant: both ran and passed (marked perf), but neither appears in the top-15 list (smallest listed is 4.49s), so their individual timings were not reported; each is below 4.49s.

## Against expectations
- all pass: matches
- hostile_1 passes: matches (passes); expected zwsp shape ~3 s: differs: observed 40.13s for the whole test (per-shape timing not recorded; load 0.55-1.95 during run)
- T10 about 4.4 s / T11 about 3.1 s: differs: observed not in durations list, so each < 4.49s; exact values not available from this log

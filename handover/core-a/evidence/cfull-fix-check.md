# cfull-fix-check (facts only)
- core-c sha: fc4af41a723df097e1adc8030fda13cad373a2e7 (origin/cloud/core-c, detached, /home/user/wt/cfull). Not 9aeedc22f.
- Python: 3.13.12 (uv run --python 3.13), 3.12.3 (/usr/bin/python3.12). Box: 4 cores. Setup `uv sync --all-extras --group test` ok.
- Command (each run, one process): uv run --python $PY --all-extras --group test pytest -q -n 0 -p no:cacheprovider --no-header -rfE --durations=10
  tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse
  tests/test_textnorm_mixed_script_micro.py::test_a_code_point_newer_than_unicode_15_1_0_counts_as_neutral
  tests/test_redact_glued_rest.py::test_glued_patterns_are_linear   (12 params)
  tests/test_redact_settle_loop.py::test_the_work_of_the_scan_is_bounded_a_hostile_text_is_refused_not_walked_to_the_end
- Load: started 0.04 (no wait needed). Uptime before/after (1-min load): 
  py3.13 r1 0.04 -> 1.43 ; py3.12 r1 1.43 -> 1.12 ; py3.13 r2 1.12 -> 1.02 ; py3.13 r3 1.02 -> 1.00
  (r2/r3 started at load ~1.0-1.1, the 1-min average left over from the preceding single-process run; no wait inserted.)
- Counts: every run = 17 passed, 0 failed, 0 errors. py3.13 r1 96.88s, r2 91.49s, r3 94.13s; py3.12 r1 106.58s.
- Failing ids: none in any run.

## Per id, per python (pass/fail)
| id | py3.13 r1/r2/r3 | py3.12 r1 |
|---|---|---|
| fold_budget::test_hostile_1 | pass/pass/pass | pass |
| textnorm_mixed_script_micro::...newer_than_unicode_15_1_0... | pass/pass/pass | pass (py3.12.3 ran it; no skip/fail) |
| glued_linear[dots-redact] | pass x3 | pass |
| glued_linear[dots-redact_text] | pass x3 | pass |
| glued_linear[hex and dashes-redact] | pass x3 | pass |
| glued_linear[hex and dashes-redact_text] | pass x3 | pass |
| (other 8 glued params) | pass x3 | pass |
| settle_loop::...refused_not_walked_to_the_end | pass x3 | pass |

## --durations (pytest "call" seconds; the tests' own 3.0 s limit is on the in-test measured time, pytest call time is the whole test)
| id | 3.13 r1 | 3.13 r2 | 3.13 r3 | 3.12 r1 |
|---|---|---|---|---|
| fold_budget::test_hostile_1 | 40.50 | 38.92 | 40.83 | 41.98 |
| settle_loop::...not_walked_to_the_end | 11.12 | 10.80 | 10.93 | 12.39 |
| glued[dots-redact_text] | 4.34 | 3.82 | 3.92 | 4.55 |
| glued[dots-redact] | 4.06 | 3.62 | 3.64 | 4.28 |
| glued[hex and dashes-redact] | 3.73 | 3.65 | 3.74 | 5.25 |
| glued[hex and dashes-redact_text] | 3.70 | 3.73 | 3.75 | 4.63 |
| glued[digits and spaces-redact] | 4.32 | 3.46 | 3.37 | 4.19 |
| glued[digits and spaces-redact_text] | 3.86 | 3.50 | 3.16 | 4.14 |
| glued[underscore digits-redact] | 3.40 | 3.26 | 3.38 | 3.69 |
| glued[underscore digits-redact_text] | 3.40 | (not in top10) | 3.59 | 3.91 |
The in-test measured values vs 3.0 s are not printed on pass; all asserts passed.

Raw logs: /home/user/hadavin-sdk/handover/core-a/raw/cfull-py313-r1.log, -r2, -r3, cfull-py312-r1.log, cfull-py3.13-version.log, cfull-py3.12-version.log, cfull-uptime-r2/r3.log

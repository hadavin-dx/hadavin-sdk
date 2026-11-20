# evidence-mutants-19-run6 (facts only)
Tree: lead-mut19e (core-a 83281657b + G33d anchor edit). WSL Ubuntu, CPython 3.13.12 (also system 3.12.3 for step 3). Exit codes from script files.
Copy-only change: `PENDING = {"G33d"}` -> `PENDING = set()` in tests/test_mutants_anchors.py (WSL copy only).
1. tests/test_mutants_anchors.py: `121 passed`. Baseline `endpoint_mutants.py G33d`: EXIT=0, 0 Traceback, `1 killed, 0 crash-accepted (), 0 known survivors`, `1 of 1 run are as expected; problems: []`.
2. FULL script (12:59:33-13:07:51 UTC, 8 min 18 s): EXIT=0, 0 Traceback.
   `117 killed, 3 crash-accepted (G20j, G31, G32e), 0 known survivors`
   `120 of 120 run are as expected; problems: []`. Mutants not as expected: none. Mutant total 120.
   New ones that ran, all `ok KILLED`: G8c, G15e, G36c, G36d, G36e, G36f (send_error one write), G36i (header cap does not count the request line), G36j (header cap 64 bytes too generous).
3. Three files test_t5_wsgiref + T13 + T14: 3.13.12 `105 passed in 10.91s`; 3.12.3 `105 passed in 11.28s`.
   Whole tests/triggers:
   - with --noconftest (runner style; no database): both interpreters `3 failed, 969 passed, 244 skipped, 135 errors` (errors = tests needing conftest fixtures, e.g. test_t5_cases, test_worker main test; failure names not captured).
   - with conftest, no database env: 3.13.12 `3 failed, 1036 passed, 312 skipped (4:58)`; 3.12.3 `3 failed, 1036 passed, 312 skipped (4:57)`. Failed on both: tests/triggers/test_t5_strict_switch.py::test_r41_a_skip_that_names_the_dsn_variable_is_failed_under_the_switch, ::test_r41_without_the_switch_the_same_skips_stay_skips, ::test_r42_an_unknown_value_stops_the_session_at_start. Cause not examined (they start child pytest runs; my run used `-c <empty ini> --rootdir`).
Cleanup: no container; WSL copy, venv312 and logs removed; no processes left.
Files: evidence-mutants-19-run6.md, raw/run6-mutants.log, raw/run6-pytest-runs.log

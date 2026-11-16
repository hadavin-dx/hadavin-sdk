# PR89 db0d9eb round 18, egm:egm-codebase-details (Sonnet 5.5), read-only. No Blocker/Major by reading; 4 Minor + 1 nit (unverified by lead).
m1 fixture/collection-error fix only in runner (_row via read_junit), not at shared judge path; mutation.py docstring contract (first_failure_junit then judge) still gives a false KILLED for a harness copying mutation.py alone. Fix: update contract text or add judge_report helper.
m2 tools/mutation_runner.py:1048-1052/1003-1014 JUNIT_REFUSED=(ValueError,SyntaxError); OSError (PermissionError) from _junit_text uncaught in _row (baseline path catches it) -> whole run crashes mid-way; no test.
m3 line 1080 "NO FAILING TEST NAMED" for every ERROR with empty id (rc 3/4/-9/missing xml); line 1077 sets first_lines "" entries contrary to docstring.
m4 line 1205-1206 failed baseline RuntimeError has no exit code/first line (unreachable DB indistinguishable) -> include _run_end(base_rc) + masked first line.
n5 line 942 stray "(``canary``)".
Checked OK by reading: judge empty-id order, _first_failure ordering, _plugin_module identity, KMP head/tail, marked bookkeeping, masking covers all caller paths, lock fd close-on-exec, new conftest autouse fixture (no writer of HADAVIN_TEST_PG_DSN found).
Not checked: any run, sha256 pins, most of tests, CI, Windows.

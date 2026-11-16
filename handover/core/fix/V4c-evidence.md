# V4c evidence (runner, no judging). Collector: 3995 tests in 97 files (tests/test_docs_match_tools.py docs check passes against it).
| run | tree | head sha | files | passed | failed | skipped | wall | hang |
| 1 old-REQ1 | tree-V4c-old + new test file | 61ded9e (patched, uncommitted) | test_docs_match_tools.py | 11 | 2 | 0 | 4.4s | no |
| 2 new-noREQ | tree-V4c | 76b375f | same | 13 | 0 | 0 | 4.7s | no |
| 3 new-REQ1 | tree-V4c | 76b375f | same | 13 | 0 | 0 | 4.7s | no |
| 4 new-REQ1-20files | tree-V4c | 76b375f | 20 files of doc-readers.txt (includes test_hygiene.py) | 1560 | 0 | 33 | 265s | no |
Run 1 failures: test_the_page_states_the_number_of_tests_and_files_that_the_collector_counts (E: docs/tests.md says 3993, collector counts 3995); test_every_page_about_a_repeated_request_says_it_can_start_a_follow_up_that_is_due (E: AssertionError: README.md).
Skips in run 4: playwright missing (3), no gitleaks (5+), ntpath.isreserved needs 3.13 (1), root can read no-permission file (1), others.
Ruff (pyproject, line-length 120) on the test file: check rc 0, format --check rc 0. Combined patch added lines >100 cols: 90 (>120: 42, none in .py).
Mutants: see mutants-table.txt (7 asked + MH extra). Apply check: git apply --check + apply on fresh tree-EV copy rc 0; diff -rq vs tree-V4c: no differences.
Files not run: all other tests (full suite not run; 77 of 97 files). Commands: see logs.

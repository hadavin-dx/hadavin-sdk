# Runner C: core-touches-3.patch alone on main 61ded9e (tree-C: 3 src files modified + new tests/test_core_key_readers.py)
Started 09:45Z, finished about 10:20Z. No hang. Checked paths: tree-C python path is under tree-C (printed).

## Full suite (serial, split in 5 file groups because one run would pass the 25 min limit; 90 of 90 test files run, nothing left out)
Run 1 (single full run) was ABORTED by me at about 7% after 4 min (rc=143, log 61ded9e-patchC-run1-ABORTED.log / run1.log): too slow with other runners on the machine; replaced by the 5 groups.
| run | head | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|
| g00 (grp-00, 19 files) | 61ded9e+patchC | 816 | 1 | 0 | 0 | 270 s | no |
| g01 (grp-01, 18 files) | same | 495 | 0 | 28 | 0 | 107 s | no |
| g02 (grp-02, 19 files) | same | 1028 | 1 | 69 | 0 | 377 s | no |
| g03 (grp-03, 18 files) | same | 598 | 0 | 86 | 0 | 378 s | no |
| g04 (grp-04, 16 files) | same | 480 | 0 | 15 | 0 | 80 s | no |
| TOTAL | | 3417 | 2 | 198 | 0 | ~1212 s | no |
Skips: 198 in total; the split between browser tests and other skips was not counted per reason (not run: counting skip reasons).

## Failures (both caused by my private TMPDIR inside the tree, not by the patch)
1. tests/test_demo_folder_guard.py::test_a_missing_demo_folder_skips_when_allowed_and_stops_the_run_in_ci : ModuleNotFoundError: No module named 'support' (conftest in a sub-pytest started from tmp_path under tree-C/.tmp-run).
2. tests/test_no_placeholders.py::test_no_placeholder_text_ships : "files that could not be read as text ... .tmp-run/pytest-of-unknown/..." (the test scans the repo folder and finds my TMPDIR files).
Rerun of those 2 files (log 61ded9e-patchC-rerun-2fails-tmpoutside.log) with TMPDIR outside the tree and .tmp-run removed: 3 passed (the first attempt with TMPDIR outside but .tmp-run still present failed test 2 again, same cause). So: the brief's instruction "TMPDIR=T/.tmp-run" makes these 2 tests fail on any tree; not tested on unpatched main (tree-B is another runner's).

## Patch's own new tests on unpatched main (fresh clone of dpld-main at 61ded9e, only tests/test_core_key_readers.py copied; log 61ded9e-C0-newtests.log, per test 61ded9e-C0-per-test.txt)
Result: 7 failed, 5 passed in 2.97 s. The patch adds one test file only (git status: tests/test_core_key_readers.py untracked, nothing else changed).
| test (tests/test_core_key_readers.py::) | fails before (on main) |
|---|---|
| test_hubspot_accept_and_refuse_are_identical_to_the_old_rule_on_1512_key_files | no (passes: expected, equality with old rule) |
| test_smtp_accept_and_refuse_are_identical_to_the_old_rule_on_1512_key_files | no (passes: same) |
| test_live_accept_and_refuse_equal_the_old_rule_except_a_key_of_more_than_one_line | YES |
| test_the_reason_text_of_every_refused_key_file_is_the_new_fixed_text[hubspot] | YES |
| ...[smtp] | YES |
| ...[live] | YES |
| test_no_message_holds_the_key_text_the_file_name_or_the_folder[hubspot] | no (passes) |
| ...[smtp] | no (passes) |
| ...[live] | no (passes) |
| test_the_live_reader_refuses_a_key_of_more_than_one_line_that_is_long_enough | YES |
| test_each_reader_has_three_different_texts_for_empty_short_and_odd_characters | YES |
| test_the_set_of_texts_is_closed_every_message_is_one_of_a_few_fixed_texts | YES |
Same 7 failed / 5 passed as src-v6/evidence-q4h-fail-before.txt states. Note: the 5 passing tests (3 "no message holds the key text" cases plus 2 "identical to old rule") pass on old code, so they do not prove the fix; they are regression guards.

## Differential (src-v6/core-differential-q4h.py, run old tree = main+new test file, new tree = tree-C; log 61ded9e-core-differential.log)
hubspot: 1512 files; both accept 366; both refuse 1146 (text changed 848); only old 0; only new 0
smtp: 1512; both accept 448; both refuse 1064 (text changed 766); only old 0; only new 0
live: 1512; both accept 582; both refuse 833 (text changed 677); only OLD accepts 97; only NEW accepts 0
RESULT: no difference outside the allowed ones. Identical to evidence-q4h-core-differential.txt.

## Not run / uncertain
Windows; ruff/mypy/bandit/gitleaks (excluded by brief); the 2 failing tests were not run on unpatched main to prove they fail there too; skip reasons not broken down; the browser tests skipped (count within the 198).
Commands: see chain.sh (per group), plus the pytest and differential commands in this file. Scratch tree-C0 and tmp folders removed; .tmp-run removed from tree-C; tree-C itself left as patched. No process of mine is running (0).

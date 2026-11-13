# T2 survivor triage (K6, K10, C9) - tree-T2, main 61ded9e + patch 1 + patch 2

Run window 11:30Z-11:45Z (container clock). Product tests only.

## What failed / is uncertain (first)
- My FIRST draft of the new test file failed an existing test: `tests/test_take_script_refusals.py::
  test_every_keep_self_test_in_the_suite_uses_its_own_temp_folder` reads EVERY .py under tests/ and
  reported my sample sources (they contain the two flags) as a run that leaves a folder. Fixed in
  the same piece of work: the made-up sources now live in the module docstring (the scan skips
  docstrings). Logs of the failing draft: `run-base-*-WITH-FIRST-DRAFT-leak-fail.log`. The final file
  passes the whole file (143 passed, `run2-base-fullfile.log`). Note for the lead: this is a
  trap for any future test that holds such samples in a .py file.
- Not checked: whole suite (only test_take_script_refusals.py and the new file); other mutants;
  ruff/format (not asked; line length checked by awk: 0 lines over 100).
- Equivalence of C9 is by reading, not by a test run (no mutant run of C9 done).

## Table
| mutant | verdict | reason | test name | killed on mutant | passes on unmutated |
|---|---|---|---|---|---|
| K6 fold: format dropped | REAL GAP (single mutant survived the existing 143 tests; see "overlap") | tests/keep_scan.py:105-109 is the only reader of a `.format` call whose argument order differs from piece order; glue (:130-132) cannot read `"{1}{0}".format("keep","--")` | test_a_flag_that_only_the_format_fold_can_read_is_found | yes: `run3-K6-new-tests.log` (1 failed, 1 passed) | yes: `run3-unmutated-new-tests.log` (2 passed) |
| K10 placeholders not stripped | REAL GAP | tests/keep_scan.py:131 is the only place that removes `{}` before gluing; `["--dry-fakes","--","{}","keep"]` has no BinOp/Call/f-string for the fold (:81-112) and no piece alone holds a flag | test_a_flag_split_by_a_format_field_is_found_by_the_glued_pieces | yes: `run3-K10-new-tests.log` (1 failed, 1 passed) | yes: `run3-unmutated-new-tests.log` |
| C9 live empty/multi order swapped | EQUIVALENT | src/lead_desk/live_claude.py:422-428: `key` is `read_text().strip()` (:423). After strip an empty key contains no "\n"/"\r", so the multi-line check (:428) never fires on an empty key; a key with a line break is non-empty, so the empty check never fires on it. Each input takes the same branch and gets the same message in either order. The two later checks (:430, :432) are unchanged. | none needed | not run | n/a |

Both K6 and K10 killed together by the new tests: `run3-K6K10-new-tests.log` (2 failed).

## (c) Pair K6+K10 and overlap
| run | selection | result | log |
|---|---|---|---|
| unmutated, with new file | -k "scan or keep or sample" | 73 passed, 70 deselected | run3-base-selection.log |
| K6+K10 together | same | 2 failed, 71 passed: sample cases "flags built by format" and "format with its own fixture" (test_the_scan_judges_every_sample_source) | run2-K6K10-selection.log |
| unmutated, whole file (with new file present) | all | 143 passed in 182 s | run2-base-fullfile.log |
| K6+K10 together | whole file | 2 failed, 141 passed (same two ids) | run2-K6K10-fullfile.log |

So the PAIR is KILLED (killed by the existing sample cases, pair only). Singly each survived the old
tests because the two readers overlap: where the format pieces are in source order, glue and fold
find the same text. That is defence in depth, not equivalence: each single mutant changes behaviour
(the scan misses a leaking self-test) on a sample only that reader finds, shown by my two samples
(each passes unmutated and fails on exactly its own mutant, and the other mutant does not fail it:
K6 run fails only the fold test, K10 run fails only the glue test). So a real test gap existed
for each single mutant; it is now closed by survivor-tests-T2.patch.

## Files
- Patch: out/T2/survivor-tests-T2.patch (new file tests/survivor_tests_T2.py only, 0 lines over 100)
- Copy: out/T2/survivor_tests_T2.py; plant/restore script: out/T2/plant.py (replaces text once,
  restores bytes in `finally`, prints sha; keep_scan.py hash after every run 15fec8c4cf36 = original)
- Raw logs: run*-*.log in out/T2/ (run1/run-K*: first draft; run2: second; run3: final draft)
- Tree status at end: 29 entries at start + tests/survivor_tests_T2.py = 30 (I removed my private
  .tmp-run folder, which the brief's TMPDIR points inside the tree, after the runs).

## Commands run
python plant.py <tree> [K6] [K10] -- venv312/bin/python -m pytest -q -p no:cacheprovider -rfs <files>
(TMPDIR=tree/.tmp-run, PYTHONPATH=tree/src; package path printed: under tree-T2). No unshare needed.
Counts at end: no process of mine left running.

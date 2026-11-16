# Survivor triage of the real-run v6 chain (8 survivors), CORE cloud session

Base: demo main 61ded9e + patch 1 + patch 2. Made-up data. Builders T1, T2, T3 triaged (builder claims, code read by me where noted); an independent evidence runner (EV) re-ran the proofs. Patch of new tests: ../survivor-tests-v1.patch (sha256 94cf2fc5..., NOT applied to any repo).

## What is uncertain or not done (first)
- C9, P2, P4, P10 are EQUIVALENT by reading the code only; no test can kill an equivalent mutant, and the runs only show that they survive. I read the P2, P4 and P10 code lines myself; C9 I did not re-read.
- The cause of "R20 survived here, killed in the demo" is an inference (supported by NOTES-v6.md and a builder simulation), not a re-run of the pre-P3 tree.
- Runner EV used the temp folder inside the tree for runs 2-5 (its brief named two places; these runs are tiny and none scans the repo folder); run 6 used a folder outside the tree. Not a problem for the numbers, but stated.
- Not run: full suite, linters, the K6+K10 pair on the old tree, Windows. The patch's new tests were run only on the patched tree.

## Verdict table
| mutant | verdict | why | test (in survivor-tests-v1.patch unless noted) | killed on mutant (runner EV) | passes unmutated (runner EV) |
|---|---|---|---|---|---|
| R20 config unreadable old | REAL GAP | the `except OSError` arm (run_real_check.py about line 1134) is reached only when the read itself fails; `confine_anywhere` (line 746) turns a missing file or folder into a ValueError first; no test made the read fail | tests/test_survivor_r20_config_read.py::test_a_config_file_whose_read_fails_is_refused_with_one_fixed_line | yes: 1 failed, 2 passed (`assert 'refused: FileNotFoundError\n' == 'refused: --c...not be read\n'`) | yes (3 passed) |
| K6 fold: format dropped | REAL GAP (overlap with the glue) | tests/keep_scan.py fold is the only reader of a .format call whose arguments are not in piece order | tests/test_survivor_keep_scan.py::test_a_flag_that_only_the_format_fold_can_read_is_found | yes: 1 failed, 2 passed | yes |
| K10 placeholders not stripped | REAL GAP (overlap with the fold) | the glue line is the only place that removes `{}` before gluing | tests/test_survivor_keep_scan.py::test_a_flag_split_by_a_format_field_is_found_by_the_glued_pieces | yes: 1 failed, 2 passed | yes |
| K6+K10 together | killed | by two existing sample cases (builder T2: selection 2 failed 71 passed; whole file 2 failed 141 passed); the two new tests also both fail (runner: 2 failed, 1 passed) | existing cases `flags built by format`, `format with its own fixture`; new tests above | yes | |
| N20 result-is-a-folder check off | covered in the full suite, not a gap | existing test_take_script_refusals.py::test_a_result_path_that_cannot_hold_a_file_is_refused_before_the_question[a-folder] kills it (builder T1: full file 1 failed, 142 passed); it survives only in test_real_run_v6.py + test_core_key_readers.py | none needed | yes (builder T1) | |
| C9 live empty and multi order swapped | EQUIVALENT | live_claude.py about lines 423-428: the key is stripped; an empty key has no line break; a key with a line break is not empty; same branch and message in either order | none needed | n/a | n/a |
| P2 hubspot: absent falls back to the vendor | EQUIVALENT | the refusal at crm_hubspot.py line 183 comes first, so `env.get(X) or VENDOR` can only return env[X] | none needed | n/a | n/a |
| P4 live: absent falls back to the provider | EQUIVALENT | same shape: config.py line 206 refuses first | none needed | n/a | n/a |
| P10 refusal swallowed | EQUIVALENT | the mutant puts `pass` before the `raise`; the raise still runs (its name says "disabled", the code does not) | none needed | n/a | n/a |

## Existing tests still pass with the new files present (runner EV, unmutated, patch applied)
test_take_script_refusals.py 143 passed (155 s, includes the self-test that scans tests/ for samples that leave a folder behind); test_real_check_dry.py 71 passed (269 s); test_real_run_v6.py 74 passed; test_core_key_readers.py 12 passed. Collection: 3982 tests, the 3 new ones collected by default. New files: 0 lines over 100 columns. Mutated files restored byte for byte (sha256 equal to before).

## Cause of the R20 difference
The demo's first pass ran before the sonar-p3-final patch: `load_env` read the file directly, so a missing "nope.env" went through the OSError arm and R20's text broke the one-line form: killed. After the patch the same case is a ValueError, so the OSError arm lost its only test. Builder simulation: R20 plus `config = path` in place of the confine line: 1 failed; the simulation alone: 1 passed. The test count (133 vs 143) is not the cause.

## Lesson for later tests
Samples that hold the two flags inside a .py file under tests/ trip the existing self-test; put such samples in a module docstring (the scan skips it).

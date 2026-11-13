# E1 RESULTS (raw; no judging). Run 12:42-13:20Z. Head 61ded9e in both trees.

## Trees (git status recorded: git-status-E1.txt, git-status-E1b.txt)
- tree-E1: patched (31 entries before my runs). tree-E1b: NOT clean main as briefed: 7 modified tests (test_clock_steps, test_crm_hubspot, test_env_numbers, test_ledger_amounts, test_live_claude, test_path_confinement, test_real_check_dry) + 6 untracked test files (test_core_key_readers, test_desk_address_required, test_real_run_v6, test_start_prompt_hardening, test_take_script_refusals, keep_scan*) = patched TESTS on UNPATCHED src. Not cleaned. My runs added an untracked .tmp-run in each tree (+1 entry).
- Package path printed (pkgpaths.txt): both under their own tree/src.

## (1) B2 baseline command, tree-E1: unshare -n lo_up.py pytest tests/test_take_script_refusals.py -k "scan or keep or sample"
Result: rc=1 did NOT return in 21 of 21 runs. Every run: 73 passed, 70 deselected. First failing test id: none. First error line: none.
| mode | run | rc | wall |
|---|---|---|---|
| solo | 1 | 0 | 61s |
| solo | 2 | 0 | 68s |
| solo | 3 | 0 | 76s |
| solo | 4 | 0 | 63s |
| solo | 5 | 0 | 55s |
| shared | 1a | 0 | 101s |
| shared | 1b | 0 | 101s |
| shared | 2a | 0 | 60s |
| shared | 2b | 0 | 65s |
| shared | 3a | 0 | 65s |
| shared | 3b | 0 | 66s |
| shared | 4b | 0 | 59s |
| shared | 4a | 0 | 60s |
| shared | 5a | 0 | 73s |
| shared | 5b | 0 | 77s |
| sep | 1b | 0 | 135s |
| sep | 1a | 0 | 137s |
| sep | 2a | 0 | 82s |
| sep | 2b | 0 | 84s |
| sep | 3b | 0 | 97s |
| sep | 3a | 0 | 100s |

Wall by mode: solo 55-76 s; shared TMPDIR pair 59-101 s; separate TMPDIR pair 82-137 s (other agents' pytest were running on the 4 cores the whole time; 4 pytest processes seen before I started).
Logs: run-61ded9e-<mode>-<run>[a|b].log (a/b = the two concurrent processes). Shared pairs used the same TMPDIR, e.g. RR/tmp-E1/shared-1.

## (2) Two known failures, plain unshare -n + lo_up-q4g.py
| tree | TMPDIR | test | result | first error line |
|---|---|---|---|---|
| tree-E1b | inside | both tests | no_placeholder PASS; demo_folder_guard FAIL | E       AssertionError: ImportError while loading conftest '/home/user/build/rr6/tree-E1b/.tmp-run/pytest-of-unknown/pytest-0/test_a_missing_demo_folder_ski0/a/conftest.py'. |
| tree-E1b | outside | both tests | both PASS | none |
| tree-E1 | inside | both tests | no_placeholder PASS; demo_folder_guard FAIL | E       AssertionError: ImportError while loading conftest '/home/user/build/rr6/tree-E1/.tmp-run/pytest-of-unknown/pytest-0/test_a_missing_demo_folder_ski0/a/conftest.py'. |
| tree-E1 | outside | both tests | both PASS | none |

Detail for the failing cases: tests/test_demo_folder_guard.py:40 assert (4 == 0); inner pytest in the temp folder ends rc 4 with
"ImportError while loading conftest '<TMPDIR>/pytest-of-unknown/pytest-0/test_a_missing_demo_folder_ski0/a/conftest.py' ... conftest.py:33: from support import Rig, ... ModuleNotFoundError: No module named 'support'".
test_no_placeholders::test_no_placeholder_text_ships PASSED in all 4 runs (it did not fail with the inside TMPDIR; only the demo-folder-guard test did). Raw: t2-61ded9e-*.log.

## Not run / uncertain
Not run: anything other than the above (no full suite, no other test files). Cause of the earlier B2 rc=1 is not reproduced; the original log was overwritten, so not explained. I did not test why the inside-TMPDIR case fails beyond the printed error.
## Commands
one.sh, pair.sh, pairs.sh, solo.sh, t2.sh in this folder (exact command lines). 

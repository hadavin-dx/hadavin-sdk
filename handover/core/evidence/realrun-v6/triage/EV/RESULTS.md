# EV2 results (raw logs in this folder; I record, I do not judge)
Tree: /home/user/build/rr6/tree-EV2, base 61ded9e + patch1 + patch2 (29 entries) + survivor-tests-v1.patch (sha256 94cf2fc5..., verified). Start 11:45Z, end ~11:53Z.
Failures during the work: none unexpected. Not run: full suite, other test files, ruff/mypy/bandit. Deviation: brief names TMPDIR RR/tmp-EV in one line and T/.tmp-run in another; runs 2-5 used T/.tmp-run (removed afterwards), run 6 used RR/tmp-EV.

| run | what | passed | failed | skipped | wall | failing test ids, first error line |
|---|---|---|---|---|---|---|
| 1 | git apply --check + git apply, rc=0; status count 29 -> 31 (2 new untracked files) | - | - | - | - | - |
| 2 | unmutated, both new files (run2-unmutated-new-files.log) | 3 | 0 | 0 | 0.34s | none |
| 3 | collect-only tests/ (run3-collect.log): 3982 collected; test_survivor lines 3 (r20: 1, keep_scan: 2) | - | - | - | 5.7s | - |
| 4 | R20 planted (run-mutant-R20.log) | 2 | 1 | 0 | 0.10s | test_survivor_r20_config_read.py::test_a_config_file_whose_read_fails_is_refused_with_one_fixed_line: AssertionError: assert 'refused: FileNotFoundError\n' == 'refused: --c...not be read\n' |
| 5a | K6 planted | 2 | 1 | 0 | 0.14s | test_survivor_keep_scan.py::test_a_flag_that_only_the_format_fold_can_read_is_found: assert ([], 0) == (['test_a'], 1) |
| 5b | K10 planted | 2 | 1 | 0 | 0.13s | test_survivor_keep_scan.py::test_a_flag_split_by_a_format_field_is_found_by_the_glued_pieces: assert ([], 0) == (['test_a'], 1) |
| 5c | K6+K10 planted | 1 | 2 | 0 | 0.11s | both keep_scan tests above fail; r20 test passes |
| 6a | unmutated test_take_script_refusals.py (unshare -n + lo_up-q4g.py) | 143 | 0 | 0 | 155s | none |
| 6b | test_real_check_dry.py | 71 | 0 | 0 | 269s | none |
| 6c | test_real_run_v6.py | 74 | 0 | 0 | 0.5s | none |
| 6d | test_core_key_readers.py | 12 | 0 | 0 | 4s | none |
| 7 | lines over 100 columns in the two new files | over100: 0 | | | | |

Each mutant: planter /home/user/build/rr6/out/EV/plant.py (asserts old text occurs once, restores bytes, compares hash: all printed True).
Step 8: sha256 before/after equal for scripts/run_real_check.py (3f6abc7b...) and tests/keep_scan.py (15fec8c4...). Patch left APPLIED. Final git status --porcelain: 31 entries (final-status.txt). Mutated mutant logs and hashes-before.txt in this folder. .tmp-run removed. No processes of mine left running.
Commands: git apply, plant.py <names> <log> (runs pytest -q -p no:cacheprovider -rfs on the two new files), pytest -rA, pytest --collect-only -q tests/, unshare -n lo_up-q4g.py pytest per file, awk length>100.

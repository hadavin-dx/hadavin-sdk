# C6 flakiness (tree-C6 head 61ded9e + patches + survivor-tests-v1). Run 2026-11-13 12:32-13:05Z.
Command per run (separate process): cd tree-C6; TMPDIR=<dir outside tree> PYTHONPATH=tree-C6/src unshare -n venv312/bin/python src-v6/drivers/lo_up-q4g.py venv312/bin/python -m pytest -q -p no:cacheprovider -rfs <files>
Package path printed: tree-C6/src/lead_desk/__init__.py (under tree).
| file | runs | passes | fails | distinct failing ids | wall min/max (s) |
|---|---|---|---|---|---|
| tests/test_real_run_v6.py (74 tests) | 20 | 20 | 0 | none | 0.9 / 1.3 |
| tests/test_take_script_refusals.py (143) | 20 | 20 | 0 | none | 101.7 / 231.0 |
| tests/test_core_key_readers.py (12) | 20 | 20 | 0 | none | 3.9 / 43.2 |
| tests/test_start_prompt_hardening.py (129) | 20 | 20 | 0 | none | 1.4 / 2.1 |
| guard+no_placeholders, TMPDIR OUTSIDE tree (3) | 20 | 20 | 0 | none | 1.1 / 1.8 |
| guard+no_placeholders, TMPDIR INSIDE tree (3) | 20 | 0 | 20 | tests/test_demo_folder_guard.py::test_a_missing_demo_folder_skips_when_allowed_and_stops_the_run_in_ci (1 id; 1 failed, 2 passed every run) | 0.8 / 1.1 |
In-tree failure first error line: "ImportError while loading conftest .../tree-C6/.tmp-in/.../a/conftest.py: conftest.py:35 from support import ...: ModuleNotFoundError: No module named 'support'" (child pytest finds the repo conftest above its tmp dir; run is deterministic 20/20).
Deviations / uncertainty: (1) brief expected 2 known in-tree failures; I saw 1 (test_no_placeholders passed in-tree every time). (2) take_test run 1 was alone (195 s); runs 2-20 ran in 2 parallel lanes plus the small-file lane, so wall times include CPU contention (core max 43 s is contention). Concurrency also adds stress, no timing assumptions were checked beyond pass/fail. (3) No file had a flaky fail, so no extra 20 runs were triggered; the in-tree fail is deterministic, no extra 20 run done. (4) My first sequential chain was killed (my own pkill) after take_1; take_2 partial run discarded (log deleted). (5) In-tree TMPDIR created tree-C6/.tmp-in (removed afterwards); tree-C6 git status shows only the patch's modified files plus untracked patch files unchanged by me.
Not run: any other test file, full suite, Windows. Logs: out/C6/<label>.log (label = file group + run number, head 61ded9e), summary.txt = one line per run.
Processes at end: 0 of mine running.

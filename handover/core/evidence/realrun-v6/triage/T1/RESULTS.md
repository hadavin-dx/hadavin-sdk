# T1 survivor triage: R20 and N20 (tree-T1 = main 61ded9e + patch 1 + patch 2)

Uncertain or not done (first): the Windows case, the full suite and the three-patch chain were not run. R20 is a
real gap only in the current code; in the demo's first pass it was killed because the code was different (cause
below, shown by a simulation, not by running the old code itself). N20 is NOT a gap in the full suite.

| mutant | verdict | reason | test name | killed on mutant | passes on unmutated |
|---|---|---|---|---|---|
| R20 config unreadable | REAL GAP | `main` has `except OSError` at scripts/run_real_check.py:1134-1136 (print fixed text). `load_env` (:738-762) first calls `confine_anywhere` (:746), which turns a missing file or a folder into `PathRefused` (a `ValueError`, "no such file", "names a folder"), so the OSError arm is reachable only when the read itself fails (permission, disk error). No existing test makes the read fail (as root permission cannot fail either); the "nope.env" case in `test_every_refusal_before_the_question_has_the_same_form` only reaches the ValueError arm. | `tests/survivor_tests_T1.py::test_a_config_file_whose_read_fails_is_refused_with_one_fixed_line` | yes: run-R20-newtest-mutant.log (1 failed), also run-R20-x-refusals-plus-newtest.log (`-x`: 143 passed, then the new test fails) | yes: run-newtest-unmutated.log (1 passed) |
| N20 dir test off | NOT A GAP in the full file (not equivalent) | `if out.is_dir()` at :841 is the only check that refuses a folder: with it off, `is_special_file` (:843), the parent test (:846) and the same-file loop all pass for a folder, so the check returns None and the start question is reached. Killed by the existing `test_take_script_refusals.py::test_a_result_path_that_cannot_hold_a_file_is_refused_before_the_question[a-folder-...]` (the "a-folder" case, line 533 of that file). | existing, no new test | yes: run-N20-refusals-full.log (1 failed, 142 passed, 3m13s); run-N20-refusals-k.log (-k: 1 failed, 2 passed) | n/a (existing test; unmutated full file: 143 passed in run-R20-full.log, which also had R20 planted, see below) |

N20 survives in `tests/test_real_run_v6.py` + `tests/test_core_key_readers.py`: run-N20-v6-and-keyreaders.log = 86 passed
(demo: 85 passed). So the demo note "killed by R2 in the other file" is right (R2 = "folder test off" = the same
change as N20 in the other file's mutant list).

## (d) Why R20 survived in B2's run but was killed in the demo first pass
Same mutant text (RR/src-v6/drivers/mutants/muts-r.json: R20 replaces the print on `OSError` in
scripts/run_real_check.py; identical to what I planted). Runs on tree-T1:
* run-R20-full.log: full `tests/test_take_script_refusals.py` with R20 planted: 143 passed, nothing fails (survives; B2 is confirmed).
  With `-x` the result is the same (nothing to stop on); run-R20-x-refusals-plus-newtest.log shows 143 passed, then only my new test fails.
* Demo first pass (evidence-q4h-mutants.txt line 49): 133 tests, 1 failed. Cause (strong evidence, one inference):
  the first pass ran on the code BEFORE sonar-p3-final. There `load_env` read the file directly, so the "nope.env"
  (missing file) case in `test_every_refusal_before_the_question_has_the_same_form` raised FileNotFoundError and went
  through the OSError arm; the mutant printed "refused: FileNotFoundError", which breaks that test's one-line form
  (regex and "Error" check in `_one_refusal`). The final patch (NOTES-v6.md section 7) rebased onto sonar-p3-final, which puts
  `config = confine_anywhere(path, what="--config")` first (:746) so a missing file is now a ValueError and the
  OSError arm lost its only test. 133 vs 143 tests: the file grew by 10 tests; not the cause.
* Simulation proving this (not the old code itself): I planted R20 together with `config = path` instead of the
  `confine_anywhere` line (pre-P3 behaviour): run-R20-simprep3-k.log = 1 failed
  (`test_every_refusal_before_the_question_has_the_same_form`); the simulation alone: run-simprep3-only-k.log = 1 passed.
  So with the old read path the old test kills R20; with the current path it does not.
* Not checked: the actual first-pass tree was not available, so the inference "the first pass had no confine_anywhere"
  rests on NOTES-v6.md section 7 and this simulation.

## Files
* RR/out/T1/survivor_tests_T1.py (new test, 1 function, lines at most 100 columns) and RR/out/T1/survivor-tests-T1.patch
  (new file tests/survivor_tests_T1.py; `git apply --check` passes on tree-A1). The test patches `Path.read_text` to raise
  PermissionError for the config file only, then asserts the whole output is the one fixed line, with no file name, "Error" or "denied". The start
  question is mocked to fail if asked. Suggest merging it into tests/test_take_script_refusals.py instead of a new file if the owner prefers.
* Raw logs: all run-*.log in RR/out/T1/. Scripts: run.sh (unshare -n + lo_up-q4g.py + pytest, TMPDIR=tree-T1/.tmp-run), plant.py (plants, runs, restores).
* Mutated file restored: `cmp` against the saved copies equal (both after each run: "restored True"); `git status --porcelain` of tree-T1 = 29 entries (same as start); the new test file and .tmp-run were removed from the tree after the runs (the patch file is the deliverable).

## Commands run
`plant.py R20|N20|SIMPREP3+R20|SIMPREP3 <log> <pytest args>` with the pytest args in each log's header; plus tiny probes
(load_env on a missing path and on a folder: both PathRefused). No ruff, mypy, bandit or scans. Never answered a prompt; every
run under plain `unshare -n` with lo up; start question mocked or never reached with input mocked.
Test files not run: everything except tests/test_take_script_refusals.py, tests/test_real_run_v6.py, tests/test_core_key_readers.py and the new test.
Processes at the end: none of mine running (2 pytest processes exist on the machine; they are not mine: other agents' trees).

# evidence-cmut: whole-file mutation runs of cloud/core-c

Head: ef5773ac400ea6e156e8439938f823c0b60b1372 (origin/cloud/core-c, "board 2026-11-20T12:24:50Z"). core-c named 7c31dbc97; the head had moved, this is the head.
Worktree (kept, Windows): C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\lead-cmut
Run: WSL Ubuntu, copy of the tree (no .git) at ~/cmut, `uv sync --python 3.13 --all-extras --group test` EXIT=0 (raw/setup.log). Runners have no parallel option; one at a time, each as `uv run python tests/<name>_mutants.py`, driver raw/run.sh. Raw logs in raw\.
Machine load: other agents' pytest runs shared the WSL box (load average 13-15 on 12 cores during and after the runs). Not mine.

| File | EXIT | Duration | SUMMARY line (verbatim) |
|---|---|---|---|
| textnorm_mutants.py | 0 | 843s | 256 of 256 good; problems: [] |
| gate_mutants.py | 1 | 238s | 104 of 105 good; problems: ["R15 the sweep is not given the call's deadline (design M2)"] |
| redact_mutants.py | 1 | 21s (rerun 69s) | no SUMMARY: RuntimeError: the unmutated copy does not pass its tests |
| g8_mutants.py | 0 | 150s | 35 of 35 good; problems: [] |
| p1d_a_mutants.py | 1 | 559s | no SUMMARY line (prints tuples); 51 mutants, 48 KILLED, 3 not good (below) |
| stage_mutants.py | 0 | 136s | 37 of 37 good; problems: [] |
| migration_numbers_mutants.py | 0 | 116s | 37 of 37 good; problems: [] |
| mutation_runner_mutants.py | 0 | 238s | 62 of 62 good; problems: [] |

## Problem mutants (verbatim)
- gate: `BAD SURVIVED     R15 the sweep is not given the call's deadline (design M2)  []` (first line empty)
- p1d_a: `('A3d', <Verdict.ERROR: 'ERROR'>, 'SNIPPET NOT FOUND', False)`
- p1d_a: `('A43', <Verdict.SURVIVED: 'SURVIVED'>, '', False)`
- p1d_a: `('A15', <Verdict.SURVIVED: 'SURVIVED'>, '', False)`
- redact: baseline (unmutated) FAILED, so no mutant was run (raw/redact.log, raw/redact-rerun.log, same error twice).
  Direct run of the 8 test files (raw/redact-baseline.log): `1 failed, 78 passed, 4 xfailed in 59.21s` (with -x): tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse, `AssertionError: fdfa` (the shape "fdfa" was refused (InputTooLarge/TooDeep) but only "e-acute lines" and "devanagari lines" may be refused). Same failure alone (raw/redact-isolated.log, 6.29s). The test text says a refusal happens "on a machine slower than the test machine", and the load was 13+ on 12 cores, so a load cause is possible but NOT shown; no run on an idle machine was made.
- No SURVIVED/WRONG_REASON/ERROR/BAD lines in textnorm, g8, stage, migration_numbers, mutation_runner. Counts: textnorm 256 (not split into 244/12 by the runner output), gate 105, g8 35.

## Baselines
Unmutated baseline failed for redact only. All other runners completed their baseline.

## Not run
Redact mutants (0 of 94 expected ran). No idle-machine rerun of redact. No pytest full suite.

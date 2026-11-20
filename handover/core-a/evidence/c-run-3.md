# c-run-3 evidence (facts only, no diagnosis)

core-c sha: 9072e701f (`git -C /tmp/ca-c-run rev-parse --short HEAD`), worktree /tmp/ca-c-run, nproc=4.
Commands (strictly sequential, via /tmp/ca-c-run3-driver.sh, one nohup background driver):
`cd /tmp/ca-c-run && uv run --all-extras --group test python tests/<script>.py > /tmp/ca-c-run3-<script>.log 2>&1`
Scripts in order: redact_mutants, gate_mutants, stage_mutants, textnorm_mutants, g8_mutants, e14_mutants, b64_mutants, p1d_a_mutants.
Logs: raw/c-run-3-<script>_mutants.log; start/end/exit/load per script: raw/c-run-3-meta.txt.
Note: a concurrent full test suite (3 workers) was running in the same worktree per the task, so load is non-zero.

| script | expected | observed | verdict | exit | wall | load1 start -> end |
|---|---|---|---|---|---|---|
| redact_mutants | 117 of 117 good; problems: [] | `117 of 117 good; problems: []` | matches | 0 | 408s | 1.40 -> 2.58 |
| gate_mutants | 104 of 105 good (R15 survives) | no summary; traceback `RuntimeError: the unmutated copy does not pass its tests` (tools/mutation_runner.py:527, raised from tests/gate_mutants.py:457); no mutant ran | differs: observed baseline-failure RuntimeError, no R8/R15 result, so R8 survival is not recorded (unknown) | 1 | 6s | 2.58 -> 2.42 |
| stage_mutants | 37 of 37 | `37 of 37 good; problems: []` | matches | 0 | 76s | 2.42 -> 4.03 |
| textnorm_mutants | 256 mutants, all good | `256 of 256 good; problems: []` | matches | 0 | 592s | 4.03 -> 1.54 |
| g8_mutants | 35 of 35 | `35 of 35 good; problems: []` | matches | 0 | 74s | 1.54 -> 1.25 |
| e14_mutants | 8 of 8 | `8 of 8 good; problems: []` | matches | 0 | 17s | 1.25 -> 1.20 |
| b64_mutants | all good | no summary; traceback `RuntimeError: the unmutated copy does not pass its tests` (tests/b64_mutants.py:401 -> mutation_runner.py:527); no mutant ran | differs: observed baseline-failure RuntimeError | 1 | 3s | 1.20 -> 1.18 |
| p1d_a_mutants | record count | 51 mutant result lines: 48 KILLED, 2 SURVIVED, 1 ERROR; no summary line; process exit 1 | recorded | 1 | 215s | 1.18 -> 1.07 |

## Survivors / failures (full list)
- gate_mutants: none listed (run did not reach mutants). R15 and R8 not observed.
- b64_mutants: none listed (run did not reach mutants).
- p1d_a_mutants:
  - `('A43', <Verdict.SURVIVED: 'SURVIVED'>, '', False)` (log line 18)
  - `('A15', <Verdict.SURVIVED: 'SURVIVED'>, '', False)` (log line 39)
  - `('A3d', <Verdict.ERROR: 'ERROR'>, 'SNIPPET NOT FOUND', False)` (log line 9)
- redact, stage, textnorm, g8, e14: no survivors, no failures.

Other: every log begins with the uv warning `UV_NATIVE_TLS ... deprecated`.

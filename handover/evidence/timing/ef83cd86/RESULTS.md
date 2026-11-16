# Evidence: timing, head ef83cd86e63f07bb4bb7f32a6c7f8e4ef459d1a7 (branch wip/cloud-timing-fix2)
EVIDENCE RUNNER: results recorded, nothing judged, nothing fixed. Raw logs: /home/user/build/evidence-raw/timing-ef83cd86/. Worktree clean at the head (git status 0 lines). Times UTC (IST = +5:30).

## Failed or not run first
- Nothing failed on the new head in items run. On origin/main (2a8c2aac) the flaky test failed 2 of 5 runs (below).
- Not run: ci.yml's py3.12 job and the vault service tests (no Vault here; no Python 3.12 run). The full run used my own Postgres 16 started as OS user postgres (port 56733), not CI's Postgres 17.
- ci.yml names no mutant runner except `tests/stage_mutants.py`; the timing mutant list (`tests/migration_numbers_mutants.py`) was run once as the brief asked.
- The probe script (probe.py) is mine and is a rough probe; my first probe run timed out (too many repeats) and was rerun smaller; my first "quadratic" stand-in was not quadratic (constant outer cap, my error) and was replaced.
- Busy loops: mine only (4 per stress run). Contention loops pids 19891-19894 ran 21:21:28 to 21:46:50 (stopped by the script right after busy run 6; the lead asked at 21:43). Probe loops ran 21:56:54-22:01:35 (first, killed at timeout) and 22:01:40-22:02:54 (second); all stopped, `pgrep` shows 0 left.

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| diff list | git diff --name-only origin/main...HEAD | 0 | 19 files (01-diff-names.txt) |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check ... | 0 | 318 files already formatted |
| bandit | bandit -q -r src demos tools -ll | 0 | only two "nosec encountered (B102)" warnings |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| stage mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| gitleaks origin/main..HEAD | gitleaks git --log-opts origin/main..HEAD | 0 | no leaks found |
| full pytest (heavy.sh) | pytest -p no:cacheprovider -q -m "not live and not perf" -rs | 0 | 10624 passed, 1 skipped, 42 deselected in 255.62s |
| timing mutants | tests/migration_numbers_mutants.py via heavy.sh | 0 | 65 of 65 good; problems: [] (by name prefix: timing 30, lexer 17, fix1 11, o100 7; 6 are reported as CRASH, the runner counts them good; the brief expected 32 timing ones, the name prefix gives 30, I did not reconcile the 2) |
| perf-marked (42 tests) alone x3 | pytest -m perf, three-lock flock | 0,0,0 | 42 passed in 149 s / 145 s / 144 s |
| perf-marked beside 4 busy loops x6 | same, loops pids 19891-19894 | 0,0,0,0,0,0 | 42 passed each: 274 s, 271 s, 244 s, 276 s, 243 s, 200 s. Failures: none, no Untimeable text anywhere |
| timing files alone x3 | pytest tests/test_timing_fixture.py tests/test_runmap_partial_escape.py | 0,0,0 | 169 passed in 9.8 s each |
| flaky quadratic stand-in, head x5 (three-lock flock) | pytest ...::test_the_timing_harness_flags_a_quadratic_stand_in | 0 x5 | 1 passed (1.3 s each) |
| same, origin/main 2a8c2aac x5 | same, main worktree src | 1,1,0,0,0 | 2 failed, 3 passed (0.6 s each) |
| fail-before | the 2 changed test files of head copied onto 2f94c2b2 src | 1 | 13 failed, 156 passed; all 13 new tests failed on old code (4 pause params, two_pauses, pause_on_every_try, not_armed_by_agreeing_wall_clock, off_when_clock_not_processor_time, 4 hand_built_growth params, resize_times_only_changed) |
| own probe (probe.py), 4 busy loops | tiny calls 40 times + 15 small loops; sleep; child process; zero-time Growth | 0 | tiny 40 ok, small loop 15 ok, 0 Untimeable; sleep refused, child process refused, 3 zero-time Growth refused; a real quadratic (200 to 1600 chars) flagged True (63.5x vs limit 24), a linear one False |

## Previous head 2f94c2b2 for comparison
Perf beside 4 busy loops: 1 failed of 27 and 3 failed of 27 (Untimeable on tiny calls). On the new head: 0 failed of 42 in 6 runs. The perf-marked set grew 27 to 42 (the real-clock tests are now marked perf).

## Not covered
Windows (guard off there, tests skipped by the head's own skipif; not run here). Item 7 against origin/main as a whole (only the since-2f94c2b2 changed test files were used for fail-before, as the brief asked).

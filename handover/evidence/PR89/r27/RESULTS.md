# PR89 round 27: builder evidence (builder r27, NOT an independent evidence run)

Code head tested: `6690bb5f` (parent `916c71ea`). This evidence folder is added in the next commit; no file outside `handover/` changes in it. Written by the builder: an independent evidence runner and the reviewers still have to confirm it.

## What failed, what is uncertain, what was not run (first)
- Nothing failed at the tested head. One earlier full pytest run (not the final one) showed 1 failure, `test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run` with `SystemExit: 143`: I had sent SIGTERM to that pytest process myself to stop it, so that failure is mine, not a defect. The final full run is `pytest-summary.txt`.
- Not run: Windows, macOS, semgrep, zizmor, trivy, pip-audit, pytest on a real 3.12 interpreter (the suite ran on 3.13.18), perf tests, the timing test alone (not touched by this package).
- The mypy figure is now 14 errors, not 13: my new function `_narrowable` calls `os.getuid` once more (a fifth place). I measured it with mypy 2.4.1 added for the run only (`uv run --with mypy==2.4.1`), not added to the lock: the repo test on both `--python-version` flags (`mypy-test.log`, 2 passed) and mypy under a real 3.12.3 interpreter (`mypy312-real-interpreter.log`: 14 errors, 13 `attr-defined` and 1 `import-not-found`).
- Not proven by a mutant: the three conditions inside `_narrowable` (regular file, own user, one name) are covered only through the second-name case; the owner case cannot be run as a non-root user and not as root without a second user's file (the same limit as before).
- The FIFO test uses a 5 second wait in a thread; on a machine that is very slow the wait is a limit, not a measurement.

## Results
| item | command | exit | result |
|---|---|---|---|
| mutant list as a user who is not root | `runuser -u nobody -- env TMPDIR=<own folder> <venv>/bin/python tests/mutation_runner_mutants.py` through `heavy.sh` (`nobody-id.txt`: uid 65534; the worktree and the venv are world readable, the temp folder is owned by nobody) | 0 | 329 of 329 good; problems: [] (`mutants-nonroot.log`) |
| mutant list as root | same command, no `runuser` | 0 | 329 of 329 good; problems: [] (`mutants-root.log`) |
| the bug of round 26, shown | the round 26 tests and runner (`916c71ea`), one mutant "folders between", as nobody | 1 | 0 of 1 good: `WRONG_REASON`, first line `PermissionError: [Errno 13]` without the expected fragment (`round26-code-nonroot-one-mutant.log`) |
| full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` through `heavy.sh`, own Postgres 16 (port 56941), cloud variables unset | 0 | 10832 passed, 3 skipped (Stubber, 2 mypy cases), 28 deselected |
| stage_mutants | `python tests/stage_mutants.py` through `heavy.sh` | 0 | 37 of 37 good; problems: [] |
| ruff, format, bandit, scan_repo | see `gates.txt` | 0 | all clean |
| gitleaks | `git --log-opts=origin/main..HEAD` and `dir .` | 0 | no leaks |
| fail-before | new and changed tests on the old source | | 4 failed, 9 passed, 2 skipped; each pass explained in `FAILBEFORE-TABLE.md` (Issue 10) |

New mutants (2): "a file with a second name is narrowed before it is checked", "a named pipe under the name of a made file blocks the open": both `KILLED` as root and as nobody. Re-pointed because their text moved (2): "a private file is not put back to 0600", "os.fchmod is used again". The count is 329 (327 + 2).

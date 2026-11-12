# PR89 round 28: builder notes (base head cc1f6228)

Author's own record, not a review. Changed: texts of the mutant-list header, CHANGELOG, one docstring, one new test. `tools/mutation_runner.py` is NOT changed.

## Not checked / not run (first)
- Timing test `test_the_timing_harness_flags_a_quadratic_stand_in` is a known flake: not touched, not run separately. Perf run, Windows, macOS, mypy (not in the lock), non-root mutant run: not run by me in this round (the round 27 independent run did the last two).
- The first full pytest run was cut by MY OWN `timeout 590` (it sent SIGTERM; one test of the signal handling failed with signum 15). That log is kept as `pytest-run1-killed-by-my-timeout.log` outside the repo; it is not a result of the head. The run below is the repeat, with no timeout of mine.

## Fixes
| Item | What changed |
|---|---|
| R27-1 Major | Header bullet rewritten: the killer of "a link out of the tree is accepted" never skips (junction on Windows, `_symlink_or_skip` skips only on Windows with error 1314 where `_dir_link` does not call it). It is in the body-skip list only because the reader follows the helper without looking at the system. CHANGELOG round 27 text corrected, round 28 entry added. New test `test_the_folder_link_killer_never_skips_and_the_header_says_so`. |
| R27-2 | The names "the descriptor of the lock folder leaks" and "a JUnit symbolic link is followed" removed from the first prose list; they stay in the third list only. |
| R27-3, N3 | mypy test docstring: 13 POSIX-only names + 1 import error = 14. Header: round 26 re-pointed 7 (list of 7, verified by diffing the mutant list from 77d12521~1 to 916c71ea), round 27 paragraph (2 added, 2 re-pointed, tests without a mutant). |
| N1 | CHANGELOG: the non-root (user nobody, 329 of 329) and mypy 2.4.1 (3.12 and 3.13, throwaway environment, 14 errors) figures come from the independent run at head cc1f6228, not from a repo test. I did not change the runner docstring (its hash is pinned). |
| N2 | Declined as decided; recorded in the CHANGELOG. Nothing changed. |

## The 3 tests that passed on the old code: one line each
No new mutant: a mutant rewrites a text inside the runner copy, and none of the three guards the runner. Each was instead shown to fail on a planted fault (raw: `plant-*.txt`).
1. `test_that_ci_does_not_run_the_mypy_count_is_true_of_the_workflow_and_the_lock_file`: control test, reads the CI workflow and `uv.lock` as they stand, so it is true before and after. Plant D (a comment naming mypy appended to the workflow) makes it fail; file restored.
2. `test_every_decorator_is_read_even_after_a_true_mark_and_an_unreadable_one_raises`: tests the skip reader inside `tests/test_mutation_runner_meta.py`, which is test code and was already the new reader in the fail-before run, so the old runner code could not fail it. Plant C: the new test appended to the round 26 copy of the meta file (old reader) fails (`plant-C.txt`).
3. `test_the_header_names_the_killers_that_drop_a_case_by_the_system_name_and_both_lists_are_checked`: guards the header text, which is test code, not the runner. Plant B (one name deleted from the OS-branch list) fails it (`plant-B.txt`); header restored.
New test of this round, same reasoning: plant A (header says "although it skips") fails it (`plant-A.txt`).

## Gate results at the final head (exit codes and last lines)
- ruff check: exit 0, "All checks passed!"; ruff format --check: exit 0, "319 files already formatted" (one file was reformatted first by `ruff format`, my new test line)
- bandit -ll: exit 0, only the two existing nosec B102 warnings; scan_repo: exit 0, no output; stage_mutants: exit 0, "37 of 37 good; problems: []" (`gates.txt`)
- mutant list via heavy.sh, as root (not as nobody this round): exit 0, "329 of 329 good; problems: []" (`mutants-result.txt`)
- full pytest `-m "not live and not perf"` via heavy.sh, once at the final head, own Postgres 16 with PGHOST and PGPORT in the server environment: exit 0, "10833 passed, 3 skipped, 28 deselected in 353.26s" (the 3 skips: the Stubber one and the 2 mypy ones, mypy is not in the lock)
- gitleaks: see report (run before the push)

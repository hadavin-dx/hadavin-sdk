# PR85 (A17) independent evidence, head bd33cc9ec4b86c220ca84505cc13a22d693377db (origin/core/P5b2 matched)
Worktree /home/user/build/IND-P5b2, PYTHONPATH=<worktree>/src, hadavin_sdk path verified in the worktree for 3.12 and 3.13.
| # | Command | Exit | Result (raw tail) |
|---|---|---|---|
| 1a | ruff check | 0 | All checks passed! |
| 1b | ruff format --check | 0 | 362 files already formatted |
| 1c | bandit -ll -r src | 0 | High 0, Medium 0, Low 7 (not shown by -ll) |
| 2 | tools/gen_config_error_sites.py --check | 0 | rows=203 LITERAL=42 OPERATOR=134 FOREIGN=27 blank=0 locked=19 |
| 3a | full pytest 3.12 (heavy.sh) | 0 | 11476 passed, 455 skipped, 33 deselected, 86 xfailed in 679.41s |
| 3b | full pytest 3.13 (heavy.sh) | 0 | 11476 passed, 455 skipped, 33 deselected, 86 xfailed in 468.92s |
| 4 | tests/config_error_sites_mutants.py (3.12) | 0 | summary: KILLED=46 of 46; git status clean afterwards |
| 5 | default-plugins rerun | not run | pytest-randomly and xdist absent from both venvs (only pytest) |
Failing tests: none. Not run: Postgres suites; step 5 (plugins absent). Raw logs in this folder.

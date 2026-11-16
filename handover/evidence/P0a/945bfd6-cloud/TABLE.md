# Evidence, PR71 core/P0a, head 945bfd6d21ddc7361b80d1976b159764ec195edd (cloud, 2026-11-10)

EVIDENCE RUNNER: raw results only, no judgement. Worktree /home/user/build/EV-P71-945bfd6/wt (detached, HEAD printed first in every log). Not pushed. Python 3.12 and 3.13.18, venvs outside the worktree.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| pytest -v tests/test_no_pglast_in_runtime.py | 3.12 | 0 | 29 passed | pglast-test-312.log |
| pytest -v tests/test_no_pglast_in_runtime.py | 3.13 | 0 | 29 passed | pglast-test-313.log |
| ruff check | 3.12 / 3.13 | 0 / 0 | "All checks passed!" | ruff-check-312.log, ruff-check-313.log |
| ruff format --check | 3.12 / 3.13 | 0 / 0 | 311 files already formatted | ruff-format-312.log, ruff-format-313.log |
| bandit -q -r src demos tools -ll (venv bandit if present, else uvx) | 3.12 / 3.13 | 0 / 0 | no findings printed; WARNING lines only (nosec B102 src/hadavin_sdk/tools.py:389, "bytes is not a test name") | bandit-312.log, bandit-313.log |
| OLD implementation (151d3e1 code above test_repository_ships_no_pglast + new MUTANTS and test function), temp file deleted; copy kept as spliced-old-impl.py | 3.12 | 1 | 29 collected: 6 failed, 23 passed. Failed: vendored macOS binary; cyclic include-group has no name; cyclic pair still finds pglast; nested .venv import is skipped; nested node_modules vendored is skipped; nested .venv alone is not a scanned file | oldimpl-312.log |
| same | 3.13 | 1 | identical: 6 failed, 23 passed (same six) | oldimpl-313.log |
| new test in a second detached checkout at 945bfd6 with untracked src/.venv/lib/x.py, tools/.venv/lib/y.py (each `import pglast`) and demos/node_modules/pglast/__init__.py + _p.so | 3.12 | 0 | 29 passed (all tests incl. test_repository_ships_no_pglast) | nested-312.log |
| same | 3.13 | 0 | 29 passed | nested-313.log, nested-status.log |
| contrast: OLD 151d3e1 file's test_repository_ships_no_pglast in that same nested checkout | 3.13 | 1 | 1 failed, 20 deselected | nested-old-313.log |
| full suite: pytest -q -rA --tb=short -m "not live and not perf", through /home/user/build/heavy.sh, own Postgres 16 on port 56071 | 3.13 only | 0 | junit: 10113 tests, 0 failures, 0 errors, 1 skipped; pytest line "10112 passed, 1 skipped, 26 deselected in 313.38s" | full-313.log, full-313.xml |

## Not run / notes
- /home/user/build/qsubmit.sh and qrun.sh do not exist on this machine (only heavy.sh, evid.sh, pgstart.sh). I used heavy.sh (the legacy blocking slot wrapper) started in the background with nohup, and read the log. Queue directories absent.
- Full suite ran on Python 3.13 only (brief said once); not on 3.12. No mutation script (scripts/mutation_check.py) run.
- Nested checkout: git status there listed only demos/node_modules/ as untracked; src/.venv and tools/.venv are ignored by the repo's gitignore (nested-status.log). The 1 skipped test in the full suite: reason not inspected.
- Nested checkout is a second worktree, removed after the run. The old-implementation temp test file was deleted from the worktree (git status of wt clean, HEAD 945bfd6).
- Bandit was run from the venv or uvx as the script decided; the scan paths src demos tools are as the brief said.
- Full-suite log contains many ERROR log lines from tests that exercise error paths; rc and junit counts are as above.

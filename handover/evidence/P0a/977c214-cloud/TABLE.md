# Raw run table, PR71 core/P0a head 977c214fd0c78284249e03c7f914ec0eb090487d (cloud, 2026-11-10)
Records only; no judgement. Every log starts with a HEAD line. Env: PG variables unset. Venvs outside the worktree.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| pytest -v tests/test_no_pglast_in_runtime.py | 3.12 | 0 | 39 passed | pglast-test-312.log |
| pytest -v tests/test_no_pglast_in_runtime.py | 3.13 | 0 | 39 passed | pglast-test-313.log |
| ruff check | 3.12 | 0 | "All checks passed!" | ruff-check-312.log |
| ruff check | 3.13 | 0 | "All checks passed!" | ruff-check-313.log |
| ruff format --check | 3.12 | 0 | 311 files already formatted | ruff-format-312.log |
| ruff format --check | 3.13 | 0 | 311 files already formatted | ruff-format-313.log |
| bandit -q -r src demos tools -ll | 3.12 | 0 | no issue lines; 3 tool warnings (nosec B102 at tools.py:389) | bandit-312.log |
| bandit -q -r src demos tools -ll | 3.13 | 0 | same | bandit-313.log |
| awk 'length>100' tests/test_no_pglast_in_runtime.py | n/a | 0 | 0 lines over 100 | awk-100.log |
| new tests spliced onto 945bfd6 helpers (spliced-old-impl.py, temp file deleted) | 3.12 | 1 | 9 failed, 30 passed | oldimpl-312.log |
| same | 3.13 | 1 | 9 failed, 30 passed | oldimpl-313.log |
| checkout A: untracked top-level .venv (with import pglast + pglast package folder), src/.venv, tools/.venv, demos/node_modules (pglast folder + _p.so) | 3.12 | 0 | 39 passed | checkoutA-312.log (status: checkout-A-status.log) |
| same | 3.13 | 0 | 39 passed | checkoutA-313.log |
| checkout B: A plus src/pkg/.venv/lib/z.py with import pglast (one level deeper) | 3.12 | 1 | 1 failed (test_repository_ships_no_pglast, lists "src: pkg/.v... imports pglast"), 38 passed | checkoutB-312.log (status: checkout-B-status.log) |
| same | 3.13 | 1 | same | checkoutB-313.log |
| full suite via heavy-slot queue | - | not run | all 3 slots busy (flock probe 18:52 UTC), qsubmit.sh does not exist in /home/user/build | - |

Tests failing on the 945bfd6 implementation (both Pythons): test_guard_catches[nested .venv import is scanned], [nested node_modules vendored is scanned], [nested .venv under tools is scanned], [unparsable python file], [unparsable stub file], [null byte in python file], [upper-case binary suffix], test_unreadable_directory_raises, test_missing_tree_raises.
Note: the guard implementation lives inside the test file, so "old implementation" = 945bfd6 helper functions plus 977c214 cases.

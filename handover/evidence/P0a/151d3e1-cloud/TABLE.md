# Evidence, PR71 core/P0a, head 151d3e1de43c217f5eca7485cd4695c4c3188351 (cloud, 2026-11-10)

EVIDENCE RUNNER: raw results only, no judgement. Worktree: /home/user/build/EV-P71-151d3e1/wt (detached). Each log prints HEAD first. Not pushed.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| uv sync --all-extras --group test | 3.13.18 | 0 | n/a | sync.log |
| uv run --all-extras --group test pytest -v tests/test_no_pglast_in_runtime.py | 3.13.18 | 0 | 21 collected, 21 passed, 0 failed (1 test_repository_ships_no_pglast + 20 test_guard_catches[...] mutant cases) | pytest.log, pytest-raw.log, pytest.xml |
| uv run --all-extras --group test ruff check | 3.13.18 | 0 | "All checks passed!" | ruff-check.log |
| uv run --all-extras --group test ruff format --check | 3.13.18 | 0 | 311 files already formatted | ruff-format.log |
| uvx --python 3.13 bandit -q -r src demos tools -ll | 3.13.18 | 0 | no issues printed; only [manager]/[tester] WARNING lines (nosec in src/hadavin_sdk/tools.py:389 with no failed test, comment notes) | bandit.log |
| git ls-tree origin/main (demos, tools, *.py/*.pyi) | n/a | 0 | demos 28 (24 askdata, 1 data, 3 db), tools 3; origin/main 2a8c2aa | lstree-py.log |
| violations() on synthetic tree with src/.venv/lib/a.py and demos/node_modules/pkg/b.py, each "import pglast" | 3.13.18 | 0 | output: ['src: .venv/lib/a.py imports pglast', 'demos: node_modules/pkg/b.py imports pglast'] | nested-scan.log |

## Answers
- Mutants: the brief said 19, the file has 20 parametrized cases in test_guard_catches (MUTANTS dict); count verified by grep of the pytest log (20 lines). All 20 reported PASSED. The 21st test is test_repository_ships_no_pglast. Difference 19 vs 20 not explained by me; the lead should check the brief's number.
- demos/ and tools/ on origin/main hold .py files: yes (demos 28, tools 3). No .pyi files in the list (the grep matched .py or .pyi; the listed ones are .py by name, see lstree-py.log directory counts).
- Nested .venv / node_modules: the scan uses rglob("*") with no exclusion, so it does pick them up. Shown by nested-scan.log. Consequence is the test would also read any untracked .venv or node_modules under src, demos or tools in a local checkout; origin/main tracks none (git ls-tree count 0).

## Not run / notes
- Full suite not run (not asked; no heavy slot used).
- Mutation script scripts/mutation_check.py not run; "mutants" here means the file's own parametrized cases.
- bandit is not in the test group, so it ran through uvx (as evid.sh does); the scan paths src demos tools are my choice, not stated in the brief.
- Slip: my nested-scan command created a stray .venv in the worktree (uv default, UV_PROJECT_ENVIRONMENT was not exported in that call); I removed it, `git status` of the worktree is clean, HEAD unchanged.
- Python 3.12 not run.
- Processes: all my commands finished; no process of mine left running. Other agents' pytest processes were visible and left alone.

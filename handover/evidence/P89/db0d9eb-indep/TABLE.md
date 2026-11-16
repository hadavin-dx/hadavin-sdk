# PR89 independent evidence, head db0d9eb49f16b0873d8c7453a2ff5728a923f6c0 (tree 08fa8e824d9bc5c210c9c9359ed374b348f14ebb)
Evidence runner: records only, no judgement. Worktree /home/user/build/WT-P89i (git status clean after the mutant run).
| # | command | exit | counts | log |
|---|---|---|---|---|
| 1 | uv sync --locked --all-extras --group test (3.12, 3.13; no --no-build) | 0, 0 | - | 01-uvsync-312.log, 01-uvsync-313.log |
| 2 | ruff check src tests demos tools | 0 | All checks passed | 02-ruff-check.log |
| 3 | ruff format --check src tests demos tools | 0 | 318 files formatted | 03-ruff-format.log |
| 4 | uvx bandit -ll -r src demos tools (venv has no bandit: exit 127 first, 04a) | 0 | High 0, Medium 0, Low 18 | 04-bandit.log |
| 5 | python tools/scan_repo.py | 0 | empty output | 05-scan-repo.log |
| 6a | pytest -q -m "not live and not perf" -rs, Python 3.12 | 0 | 10619 passed, 1 skipped, 28 deselected, 377.79s | 06-pytest-312.log/.xml |
| 6b | same, Python 3.13 | 0 | 10619 passed, 1 skipped, 28 deselected, 367.86s | 06-pytest-313.log/.xml |
| 7 | uv run --no-sync python tests/mutation_runner_mutants.py (alone, heavy.sh, 3.13 venv) | 0 | 217 of 217 good; problems: [] | 07-mutants.log |
| 8 | hostile/hostile.py (my own script; 22 cases) | 0 | 22 OK, 0 non-OK; 2000-char special + 1000-dot line 0.12 s; 1000-dot line 0.006 s | 08-hostile.log |
| 9 | gitleaks detect --no-git --source out folder | 1 | 8 hits: 06-pytest-312.xml 4, 06-pytest-313.xml 4, no other file (contents not inspected or printed) | 09-gitleaks.log |
Skip in both suites: tests/contracts/test_llm.py:95. Not run: Windows, 3.14, --no-build sync, live tests.

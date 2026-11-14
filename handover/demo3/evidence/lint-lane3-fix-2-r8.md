# Lint on fix-2 r8 tree b19-tree (tree 812a97a), run 06:5xZ by lane3 (lead order 06:50Z)
Venv: /home/user/work/lint-venv, Python 3.13, hash-locked from requirements-dev.txt: ruff 0.17.4, mypy 2.4.1, bandit 1.9.4. Run on a clean copy of the index (no caches in the tree). Raw logs: raw/ copies of /home/user/work/lint-logs/b19-*.log.
| Command | rc | Result |
|---|---|---|
| ruff check . | 1 | F401 `sys` unused: tests/test_one_key_file_rule_and_path_walk.py:13 (1 error) |
| ruff format --check . | 1 | 2 files would be reformatted: tests/test_docs_claims_lane3.py (14 hunks), tests/test_one_key_file_rule_r7.py |
| mypy --platform linux | 0 | no issues, 28 files |
| mypy --platform win32 | 0 | no issues |
| bandit -ll -r src tools scripts -c pyproject.toml | 0 | clean |
| ruff check --select E501 . | 0 | All checks passed: the 13 over-120 base lines are confirmed fine by ruff itself |
The builder's hand scan for unused imports missed `sys` (its AST scan was wrong). The builder's belief "ruff format not run" was right to worry: 2 files fail.

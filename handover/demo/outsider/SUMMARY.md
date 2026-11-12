# Outsider test summary (in progress)
Clone of branch initial-code, head 43110e7. python3.12 exists at /usr/bin/python3.12 (3.12.3), used as docs ask. No guessing needed so far.
Done: clone, venv + pip --require-hashes (8.6s OK), ruff check/format, mypy linux/win32, bandit, check_schema, tests/test_hygiene.py (9 passed, 1 skipped: no gitleaks). 
Running: full pytest without Playwright (single process: requirements-dev.txt has no xdist).

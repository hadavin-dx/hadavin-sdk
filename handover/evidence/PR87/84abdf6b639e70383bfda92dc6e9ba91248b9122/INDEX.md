# PR 87 evidence index (EVIDENCE RUNNER: raw output only, no judgement)
Head 84abdf6b639e70383bfda92dc6e9ba91248b9122, base 0dabf1f. Postgres port 56087.

| file | command | exit code | last line |
|---|---|---|---|
| ruff-check.txt | ruff check src tests demos (py3.13) | 0 | exit=0 |
| ruff-format.txt | ruff format --check src tests demos | 0 | exit=0 |
| bandit.txt | bandit -q -r src demos tools -ll | 0 | exit=0 |
| full-312.txt | pytest -q -rA --tb=short --junitxml (not live, not perf), py312 | 1 | SUMMARY tests=10424 failed=2 errors=0 skipped=1 passed=10421 pytest_exit=1 |
| full-313.txt | pytest -q -rA --tb=short --junitxml (not live, not perf), py313 | 1 | SUMMARY tests=10424 failed=1 errors=0 skipped=1 passed=10422 pytest_exit=1 |
| failbefore.txt | head tests/test_peel_run_id.py vs base 0dabf1f src (PYTHONPATH=src, worktree FB87) | 1 | exit=1 |
| passafter.txt | tests/test_peel_run_id.py at head | 0 | exit=0 |

Test summary lines: full-312.txt '2 failed, 10421 passed, 1 skipped, 28 deselected'; full-313.txt see SUMMARY above. failbefore: 25 failed, 1 passed in 19.72s. passafter: 26 passed.

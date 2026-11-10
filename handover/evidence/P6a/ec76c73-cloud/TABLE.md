# EVIDENCE RUNNER table: core/P6a head ec76c73900fafcec7fc2715fbc29cf565aaa95ee (every log prints HEAD first)
Worktree /home/user/build/EV-P6a-ec76c73/wt (detached). Cloud env vars unset in every command. No judgement here.

| # | Command | Python | Result | Exit | Log |
|---|---|---|---|---|---|
| 1a | ruff check src tests demos tools | uv default | All checks passed | 0 | 1a-ruff-check.log |
| 1b | ruff format --check src tests demos tools | uv default | 318 files already formatted | 0 | 1b-ruff-format.log |
| 1c | bandit -ll (first try, plain `uv run bandit`) | - | FAILED TO RUN: bandit not installed in the test group | 2 | 1c-bandit.log |
| 1c2 | uv run --with bandit bandit -q -r src demos tools -ll | uv default | no issue reported (only [manager]/[tester] WARNING lines about comments / a nosec at src/hadavin_sdk/tools.py:389 with no finding) | 0 | 1c2-bandit-with.log |
| 1d | python tools/scan_repo.py | uv default | no output | 0 | 1d-scan-repo.log |
| 2a | pytest -m "not live and not perf" (own PG16 cluster, 127.0.0.1:5432) | 3.12 | 10500 passed, 1 skipped, 28 deselected (302.73s) | 0 | 2a-full-py312.log |
| 2b | same | 3.13 | 10500 passed, 1 skipped, 28 deselected (271.17s) | 0 | 2b-full-py313.log |
| 2b attempts 1 and 2 | same | 3.13 | STOPPED SILENTLY mid-run (at 92% and at 11%), no summary line, log still ends "exit=0"; cause not found (not an OOM per free -m; other sessions share this machine's slots). Not counted; the rerun above is the result | (0 logged) | 2b-full-py313-attempt1-truncated.log, 2b-full-py313-attempt2-truncated.log |
| 3 | pytest -m perf (alone) | 3.13 | 28 passed, 10501 deselected (59.15s) | 0 | 3-perf-py313.log |
| 4a | pytest tests/test_client_profile.py tests/test_stage_names.py | 3.12 | 200 passed | 0 | 4a-profile-py312.log |
| 4b | same | 3.13 | 200 passed | 0 | 4b-profile-py313.log |
| 5 | python tools/client_profile_mutants.py (alone) | 3.13 | TOTAL mutants 90 planted 90 KILLED by the named test 90 (named 90, no named killer 0) killed only by another test 0 SURVIVED 0 other problems 0 (188s); final git status '' | 0 | 5-mutants.log |
| 5 attempts 1 and 2 | same | 3.13 | attempt 1: refused to start (my shell had PG* and HADAVIN_TEST_PG_DSN set, runner refuses them); attempt 2: stopped silently after the "head" line, exit 0 logged, no mutants run. Not counted | 3 / 0 | 5-mutants-attempt1-refused-pgenv.log, 5-mutants-attempt2-silent-stop.log |
| 5b | git status --short in worktree after the run | - | empty | 0 | 5-git-status-after-mutants.txt |
| 6 | python tests/stage_mutants.py | uv default | 37 of 37 good; problems: [] | 0 | 6-stage-mutants.log |
| 7 | Fail-before: base 0dabf1fa7a2ed58e14b8bca13be1141ac59f9c71 (merge-base origin/main ec76c73) + the two test files copied | 3.12 | collection ERROR in both files: ImportError cannot import name 'edit_config' from tests.k5_support (the helper is added by the PR). 2 errors, 0 tests ran | 0 logged (pipe to tail) | 7-failbefore-py3.12.log |
| 7 | same | 3.13 | same: 2 collection errors, 0 tests ran | 0 logged (pipe to tail) | 7-failbefore-py3.13.log |
| 7b | supplementary (not in brief): base + the two test files + tests/k5_support.py | 3.13 | 84 failed, 116 passed (tail shows FAILED rows in test_client_profile.py and test_stage_names.py) | - | 7b-failbefore-with-k5_support-py3.13.log |

Not run: nothing from the brief was skipped. Pytest runs with a Postgres cluster used throwaway clusters ec76-* (removed, none running). Perf and mutants ran with no other job of mine alongside, but other sessions' jobs share the machine (unmeasured).
Note: the 7 logs end "exit=0" because the pytest output was piped to tail inside bash -c; the real pytest status is the result line.

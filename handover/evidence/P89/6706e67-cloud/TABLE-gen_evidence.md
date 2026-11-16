# A2-PR89 head 6706e6728483b67e549101b1680111a4c2b89471 (evidence table written by gen_evidence; raw output only, no verdict)

Worktree /home/user/build/EV-P89-6706e67/wt; HEAD checked = 6706e6728483b67e549101b1680111a4c2b89471; tracked files changed before the run: no. ticket file NOT found.
HADAVIN_TEST_PG_DSN set: yes; HADAVIN_TEST_VAULT_ADDR set: no. Cloud variables removed (AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_*).
Import path per python: 3.13 -> /home/user/build/EV-P89-6706e67/wt/src/hadavin_sdk/__init__.py; 3.12 -> /home/user/build/EV-P89-6706e67/wt/src/hadavin_sdk/__init__.py
Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.

Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):
- none

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed! [0s] | ruff-check.txt |
| ruff format --check src tests demos tools | 3.13 | 0 | 318 files already formatted [0s] | ruff-format.txt |
| bandit -q -r src demos tools -ll | 3.13 | 0 | no issue lines (bandit run as `uvx --python /usr/local/bin/python3.13 bandit`) [2s] | bandit.txt |
| python tools/scan_repo.py (hygiene cell) | 3.13 | 0 | no hits [0s] | hygiene.txt |
| pytest -q -m "not live and not perf" -rs | 3.13 | 0 | 10518 passed, 13 skipped, 28 deselected [300s] | full-3.13.txt |
| pytest -q -m "not live and not perf" -rs | 3.12 | 0 | 10518 passed, 13 skipped, 28 deselected [331s] | full-3.12.txt |
| pytest -q -m perf -rs | 3.13 | 0 | 28 passed, 10531 deselected [68s] | perf-3.13.txt |
| pytest -q -m perf -rs | 3.12 | 0 | 28 passed, 10531 deselected [68s] | perf-3.12.txt |
| python tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good; problems: [] [36s] | stage-mutants.txt |
| python tests/mutation_runner_mutants.py (new head) | 3.13 | 0 |  [100s] | python-tests-mutation_runner_mutants-py-new-head.txt |
| python tests/mutation_runner_mutants.py (new head) | 3.12 | 0 |  [111s] | python-tests-mutation_runner_mutants-py-new-head.txt |
| scan of these evidence logs with the PATTERNS of tools/scan_repo.py | - | 0 | no hits | hygiene-logs.txt |

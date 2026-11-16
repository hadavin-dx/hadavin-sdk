# P6a head 0ae044b25a3113244777cd078fc9a784647af924 (evidence table written by gen_evidence; raw output only, no verdict)

Worktree <snapshot>; HEAD checked = 0ae044b25a3113244777cd078fc9a784647af924; tracked files changed before the run: no. ticket read: tickets/P6a.md (483 lines, sha256 c0193ce389d5).
HADAVIN_TEST_PG_DSN set: yes; HADAVIN_TEST_VAULT_ADDR set: no. Cloud variables removed (AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_*).
Import path per python: 3.13 -> <snapshot>/src/hadavin_sdk/__init__.py; 3.12 -> <snapshot>/src/hadavin_sdk/__init__.py
Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.

Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):
- none

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| pytest -q -m perf -rs | 3.13 | 0 | 28 passed, 10514 deselected [62s] | perf-3.13.txt |
| pytest -q -m perf -rs | 3.12 | 0 | 28 passed, 10514 deselected [66s] | perf-3.12.txt |
| scan of these evidence logs with the PATTERNS of tools/scan_repo.py | - | 0 | no hits | hygiene-logs.txt |

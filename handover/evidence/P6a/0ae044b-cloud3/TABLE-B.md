# P6a head 0ae044b25a3113244777cd078fc9a784647af924 (evidence table written by gen_evidence; raw output only, no verdict)

Worktree <snapshot>; HEAD checked = 0ae044b25a3113244777cd078fc9a784647af924; tracked files changed before the run: no. ticket read: tickets/P6a.md (483 lines, sha256 c0193ce389d5).
HADAVIN_TEST_PG_DSN set: yes; HADAVIN_TEST_VAULT_ADDR set: no. Cloud variables removed (AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_*).
Import path per python: 3.12 -> <snapshot>/src/hadavin_sdk/__init__.py
Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.

Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):
- none

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| pytest -q -m "not live and not perf" -rs | 3.12 | 0 | 10513 passed, 1 skipped, 28 deselected [323s] | full-3.12.txt |
| pytest tests/test_client_profile.py -q -rA | 3.12 | 0 | 67 passed [3s] | p6a1-client-profile-3.12.txt |
| pytest tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py -q -rA | 3.12 | 0 | 11 passed [2s] | p6a1-pg-3.12.txt |
| scan of these evidence logs with the PATTERNS of tools/scan_repo.py | - | 0 | no hits | hygiene-logs.txt |

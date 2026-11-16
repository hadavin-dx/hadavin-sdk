# P3a-2 head 2b0941b7092e09a209c9808dcc8aab20b109869f (evidence table written by gen_evidence; raw output only, no verdict)

Worktree /home/user/build/recon/p3a2/wt; HEAD checked = 2b0941b7092e09a209c9808dcc8aab20b109869f; tracked files changed before the run: no. ticket read: tickets/P3a.md (286 lines, sha256 fb8bdf2ab728).
HADAVIN_TEST_PG_DSN set: yes; HADAVIN_TEST_VAULT_ADDR set: no. Cloud variables removed (AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_*).
Import path per python: 3.13 -> /home/user/build/recon/p3a2/wt/src/hadavin_sdk/__init__.py; 3.12 -> /home/user/build/recon/p3a2/wt/src/hadavin_sdk/__init__.py
Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.

Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):
- none

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed! [0s] | ruff-check.txt |
| python tools/scan_repo.py (hygiene cell) | 3.13 | 0 | no hits [0s] | hygiene.txt |
| python tests/migration_numbers_mutants.py (P3a-1) | 3.13 | 0 | 40 of 40 good; problems: [] [26s] | p3a1-mutants.txt |
| p3a2_mutants.py (P3a-2, 66 mutants; plants into the tree, runs last) | 3.13 | 0 | 66 of 66 killed [106s] | p3a2-mutants.txt |
| scan of these evidence logs with the PATTERNS of tools/scan_repo.py | - | 0 | no hits | hygiene-logs.txt |

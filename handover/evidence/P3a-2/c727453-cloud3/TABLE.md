# P3a-2 head c727453a1cad96f72cc78ff1a13fe4b792957d3b (evidence table written by gen_evidence; raw output only, no verdict)

Worktree /home/user/build/EV-P73-c727453/wt; HEAD checked = c727453a1cad96f72cc78ff1a13fe4b792957d3b; tracked files changed before the run: no. ticket read: tickets/P3a.md (286 lines, sha256 fb8bdf2ab728).
HADAVIN_TEST_PG_DSN set: yes; HADAVIN_TEST_VAULT_ADDR set: no. Cloud variables removed (AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_*).
Import path per python: 3.13 -> /home/user/build/EV-P73-c727453/wt/src/hadavin_sdk/__init__.py; 3.12 -> /home/user/build/EV-P73-c727453/wt/src/hadavin_sdk/__init__.py
Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.

Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):
- p3a2-mutants: inner rc 1; 55 of 66 killed [98s]; log p3a2-mutants.txt

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed! [0s] | ruff-check.txt |
| ruff format --check src tests demos tools | 3.13 | 0 | 324 files already formatted [0s] | ruff-format.txt |
| bandit -q -r src demos tools -ll | 3.13 | 0 | no issue lines (bandit run as `uvx bandit`) [2s] | bandit.txt |
| python tools/scan_repo.py (hygiene cell) | 3.13 | 0 | no hits [0s] | hygiene.txt |
| pytest -q -m "not live and not perf" -rs | 3.13 | 0 | 10672 passed, 1 skipped, 28 deselected [310s] | full-3.13.txt |
| pytest -q -m "not live and not perf" -rs | 3.12 | 0 | 10672 passed, 1 skipped, 28 deselected [345s] | full-3.12.txt |
| pytest -q -m perf -rs | 3.13 | 0 | 28 passed, 10673 deselected [67s] | perf-3.13.txt |
| pytest -q -m perf -rs | 3.12 | 0 | 28 passed, 10673 deselected [67s] | perf-3.12.txt |
| python tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good; problems: [] [36s] | stage-mutants.txt |
| pytest tests/test_migration_*.py -q -rA | 3.13 | 0 | 484 passed [20s] | p3a-migration-tests-3.13.txt |
| pytest tests/test_migration_*.py -q -rA | 3.12 | 0 | 484 passed [52s] | p3a-migration-tests-3.12.txt |
| python tests/migration_numbers_mutants.py (P3a-1) | 3.13 | 0 | 40 of 40 good; problems: [] [29s] | p3a1-mutants.txt |
| p3a2_mutants.py (P3a-2, 66 mutants; plants into the tree, runs last) | 3.13 | 1 | 55 of 66 killed [98s] | p3a2-mutants.txt |
| scan of these evidence logs with the PATTERNS of tools/scan_repo.py | - | 0 | no hits | hygiene-logs.txt |

## Added rows (run by the evidence runner after the table above was written; same head, same Postgres 16 cluster on port 56010, own venv)

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| python tests/migrate_mutants.py (checked in at this head; plants in a COPY; 89 mutants) | 3.13 | python rc 1 (log ends exit=0 because that is the wrapper's rc of the driver script) | 87 of 89 killed; SURVIVED: M88, R4; ERROR: none | migrate-mutants-checked-in.txt |

Notes for the reviewer (facts, no verdict):
- handover/tools/p3a2_mutants.py holds 66 mutants and was written against head 2b0941b. At c727453 it planted 55 of them, all 55 killed, 0 survived, and 11 could not be planted because their `old` text is no longer in the source exactly once (M61, M64, M66, M67, M88, M88b, M89, M101, MM1, N10, P9; reported ERROR, not killed). Its working tree was clean after the run.
- The branch itself checks in tests/migrate_mutants.py (89 mutants, added in c727453). Its result is the added row above: 87 killed, M88 and R4 survived (the killer test passed with the mutant planted). Survivors are not analysed here.
- Not run: fail-before, hand probes, Postgres 17, CI, semgrep, zizmor, pip-audit, gitleaks, pytest -m live. Postgres 16 server (CI uses 17).
- qsubmit.sh and qrun.sh do not exist in /home/user/build; the runs used heavy.sh (one slot per script). Postgres: one server per run, port 56010, UTF8 cluster, stopped after each run.

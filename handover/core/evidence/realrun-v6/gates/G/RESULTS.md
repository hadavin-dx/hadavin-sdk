# Runner G results (head 6e40f3c, branch local-patched, tree-G; base main 61ded9e)
Versions vs requirements-dev.txt: ruff 0.17.4 (lock 0.17.4), mypy 2.4.1 compiled (lock 2.4.1), bandit 1.9.4 (lock 1.9.4), gitleaks 8.30.1 (workflow 8.30.1). All match.
| run | command | head sha | exit | result | wall | notes |
|---|---|---|---|---|---|---|
| 1 | gitleaks dir . --config .gitleaks.toml --redact --no-banner --ignore-gitleaks-allow | 6e40f3c | 0 | no leaks found | 1s | run first, as in workflow |
| 2 | gitleaks git . (same flags) | 6e40f3c | 0 | no leaks found, 2 commits scanned | 2s | |
| 3 | ruff check . | 6e40f3c | 0 | All checks passed | 0s | |
| 4 | ruff format --check . | 6e40f3c | 0 | 166 files already formatted | 0s | |
| 5 | mypy --platform linux | 6e40f3c | 0 | no issues, 30 source files | 3s | |
| 6 | mypy --platform win32 | 6e40f3c | 0 | no issues, 30 source files | 2s | |
| 7 | bandit -ll -r src tools scripts -c pyproject.toml | 6e40f3c | 0 | see below | 2s | |
| 8 | python scripts/check_schema.py (extra, in workflow) | 6e40f3c | 0 | RESULT ALL PASS | 0s | |
| 9 | git grep literal scan minus exceptions.txt (extra, in workflow) | 6e40f3c | n/a | 0 lines left | - | out/G/literals-left.txt (empty) |
| 10 | canary guard grep (extra, in workflow) | 6e40f3c | 0 | test_hygiene_scan_public present | - | |
Findings table: none for ruff, mypy, gitleaks. Bandit: run metrics show 9 issues by severity Low (below the -ll threshold), 0 Medium, 0 High, exit 0; the 9 Low items are not listed as issues at the -ll level (the log has 0 "Issue:" blocks).
Failures: none. Cloud-image-only differences: none seen.
Not run: the same tools on the tree BEFORE the survivor patch (skipped, not cheap without worktree/stash); pytest (not my task); Windows runner; pip install of requirements-dev (venv312 already has locked versions).
Files edited in tree: none (git status clean). Raw logs: out/G/6e40f3c-*.log

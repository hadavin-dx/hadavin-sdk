# Gates, batch 15 (code head 3ad1cc45; logs in `logs/`, each with its own `head:` line)

| Gate | Result | Log |
|---|---|---|
| ruff check, ruff format --check on src tests demos tools | exit 0, exit 0 | static-final.log |
| bandit -ll | exit 0 | static-final.log |
| scan_repo.py, policy_page.py --check | exit 0, exit 0 | static-final.log |
| stage_mutants.py | 37 of 37 good, exit 0 | stage.log |
| policy_mutants.py real clock | 350 of 350 good, exit 0 | pm-real.log |
| policy_mutants.py --day 2026-12-11 | 350 of 350 good, exit 0 | pm-2026-12-11.log |
| policy_mutants.py --day 2026-12-12 | 349 of 349 good (B12 not run that day by design), exit 0 | pm-2026-12-12.log |
| policy_mutants.py --day 2026-12-13 | 349 of 349 good (B12 not run that day by design), exit 0 | pm-2026-12-13.log |
| notes_lines_check --auto a50d5b2e --head HEAD | exit 0 | notes-check.log |
| full pytest -m "not live and not perf" (own Postgres 16) | 11000 passed, 13 skipped, 28 deselected, rc 0 | full-pytest.log |
| three renewal plants, HADAVIN_POLICY_FULL_RENEWAL_RUN=1 | 3 passed, rc 0 | plants-final.log |
| gitleaks origin/main..HEAD | exit 0 | gitleaks.log (earlier head; re-run before each push) |
| fail-before on a50d5b2e | 13 of 17 fail for the named reason, 4 pass for the stated reason | fail-before-a50d5b2e.log |

Not run: 12 Vault-server tests (no server, IMPOSSIBLE-NOW); perf and live tests (excluded by the brief); the CI notes step on GitHub.

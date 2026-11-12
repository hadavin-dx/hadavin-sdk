# Gates, batch 16 (code head 43be04de; logs in `logs/`, each with its own `head:` line)

| Gate | Result | Log |
|---|---|---|
| ruff check, ruff format --check on src tests demos tools | exit 0, exit 0 | static-final.log |
| bandit -ll | exit 0 | static-final.log |
| scan_repo.py, policy_page.py --check | exit 0, exit 0 | static-final.log |
| stage_mutants.py | 37 of 37 good, exit 0 | stage.log |
| policy_mutants.py real clock | 375 of 375 good, exit 0 | pm-real.log |
| policy_mutants.py --day 2026-12-11 | 375 of 375 good, exit 0 | pm-2026-12-11.log |
| policy_mutants.py --day 2026-12-12 | 374 of 374 good (B12 not run that day by design), exit 0 | pm-2026-12-12.log |
| policy_mutants.py --day 2026-12-13 | 374 of 374 good (B12 not run that day by design), exit 0 | pm-2026-12-13.log |
| policy_mutants.py B16 (the 25 mutants of this batch) | 25 of 25 good, exit 0 | mutants-b16.log |
| policy_mutants.py B15 | 26 of 26 good, exit 0 | mutants-b15.log |
| mutation_runner_mutants.py (65, three new) | 65 of 65 good, exit 0 | mutants-runner.log |
| notes_lines_check --auto origin/main --head HEAD (PR base, as `ci.yml:111`) | exit 0 | notes-check.log (names the commit it ran on) |
| full pytest -m "not live and not perf" (own Postgres 16) | 11017 passed, 13 skipped, 28 deselected, rc 0 | full-pytest.log |
| three renewal plants, HADAVIN_POLICY_FULL_RENEWAL_RUN=1 | 3 passed, rc 0 (42m33s) | plants-final.log |
| gitleaks, last commit | exit 0 | gitleaks.log (names the commit it ran on) |
| fail-before on ccb63021 | 12 of 20 fail for the named reason, 8 pass for the stated reason | fail-before-ccb63021.log |

Not run: the 12 Vault-server tests (no Vault server here), `-m perf`, `-m live`. The code head is 43be04de; later commits add only files under `handover/` (notes and logs).
The first full pytest at 44f42c64 failed one test (the CHANGELOG re-copy list held the old runner sha); fixed in 9e85e2a2; its log was replaced by the run at 43be04de.

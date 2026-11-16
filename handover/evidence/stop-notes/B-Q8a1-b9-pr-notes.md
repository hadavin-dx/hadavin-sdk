# Q8a-1 builder b9 notes (round 8 fix batch), branch core/q8a-1-b9, base 18741c8c, head f0febfb6

Pushed to wip/cloud-q8a1-b9 (new branch, fast-forward only).

## Evidence at the final head (rc from the tool itself)
- full pytest (own Postgres 16, not live/perf): 11041 passed, 1 skipped, rc 0 (a first run found 3 failures, all fixed: two env-secret test expectations in tests/test_p4_secrets.py, one run with the server missing PGHOST)
- tests/stage_mutants.py: 175 of 175 good, rc 0
- ruff check, ruff format --check: clean; bandit -ll (src demos tools): rc 0; tools/scan_repo.py rc 0; gitleaks dir (pycache removed): rc 0
- fail-before: 31 new/changed tests fail on 18741c8c src

## Findings
Issues 1-11 fixed. Extra sibling found by grep: executor.resolve quoted a contract's function reference (fixed, test, mutant M19o). tests/test_p4_secrets.py also needed new expectations.

## Not done / not checked
- R-numbers were not looked up in the bible. EGM review and drift report are for the lead.
- The CHANGELOG decision (default hide, wording "known spellings") is in CHANGELOG.md; questions-for-lead.md not edited.

# checkpoint (UTC 16:08)
- merged origin/main (head fdf4ceb before my commits); own venvs ...-P4d-o101-313/312, own PG16 on 55433 (pgdata under evidence).
- ITEM 1 PROVEN: plain CI command, no file arg, planted defects: 10227 passed, exit 0, no check output (blocker-proof-before.txt). Control with file arg fires.
- code done (uncommitted): pytest_configure state, selected-only, xdist first, connect_role/pg_schema/execute fixes, money baseline pins, nested no-file-arg tests.
- finding for a2-i: add_cost non-finite and sNaN differ memory vs postgres.
- TODO: CHANGELOG, fail-before, mutants script, blocker-proof-after, full suites 3.13 + 3.12, lint, bandit, PR body, push.
- 17:04 DONE: pushed 92dbb1e ff; PR 66 body updated, ready; all logs at 92dbb1e.

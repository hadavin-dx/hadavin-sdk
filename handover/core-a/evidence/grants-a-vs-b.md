# grants-a-vs-b evidence

## SHAs
- core-b (origin/cloud/core-b, current): fa21e8fbb3711250f4ff71d5cdbf96debb8271fa
- A (origin/wip/cloud-core-c/grants): b55d21865bd2aca839533aebc28e2143c8eac1c7
- B (origin/wip/core-a-for-grant-tests): 3ffb442f1c6da977bc67bce26ef914b412c77cb4
- PostgreSQL: 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) at 127.0.0.1:55433

## Commands
- git fetch -q origin cloud/core-b cloud/core-c wip/cloud-core-c/grants wip/core-a-for-grant-tests
- git worktree add --detach /home/user/wt/grant-run origin/cloud/core-b; uv sync --all-extras --group test
- Step 1: tests/test_grants_negative_roles.py does not exist in core-b tree -> skipped.
- Helpers: the test imports tests.test_k3_pilot_env and tests.contracts.kinds.store_postgres; both already exist in core-b; no helper files copied, no src copied. (A-branch diff vs core-c touches tests/conftest.py, test_grants_negative_0007.py, test_money_step4_grants.py; none copied.)
- Per version (file = git show <branch>:tests/test_grants_negative_roles.py copied into worktree tests/):
  - with DSN: HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55433/postgres uv run --all-extras --group test pytest -q -n 2 -rfE --no-header -p no:cacheprovider tests/test_grants_negative_roles.py
  - without DSN: same with env -u HADAVIN_TEST_PG_DSN

## Results
| version | DSN | result |
|---|---|---|
| A | set | 85 passed in 21.55s |
| A | unset | 46 passed, 39 skipped in 22.44s |
| B | set | 88 passed in 20.36s |
| B | unset | 48 passed, 40 skipped in 0.99s |

Failing ids: none in any run (no FAILED/ERROR lines).
(Branch commit message of A claims 117 passed vs core-b head 133803834; observed here vs fa21e8fbb: 85.)

## Diff A vs B
- diff -u A B | wc -l: 536
- test function count (top-level `def test_`): A 50, B 53
- present in A, not in B: (none)
- present in B, not in A:
  - test_case2_the_release_identity_holds_exactly_the_reviewed_cells
  - test_pg_the_money_functions_are_definer_functions_only_the_named_roles_run
  - test_the_runtime_role_writes_no_money_table_and_books_through_functions

## Logs
handover/core-a/raw/grants-{A,B}-{dsn,nodsn}.log

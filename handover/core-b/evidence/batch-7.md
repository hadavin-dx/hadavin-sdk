# Batch 7 evidence run (EV4)

Read-only evidence run. No code changed, nothing committed or pushed.

## Source

- Worktree: `/tmp/core-b-wt/EV4` (detached at `origin/cloud/core-b`)
- Head sha: `fb9a4fb42` (short)

## Lint

- `ruff check src tests`: All checks passed.
- `ruff format --check src tests`: 329 files already formatted.

## Test run

Command: `pytest -q -p no:cacheprovider -n 3 -rs tests` with `HADAVIN_TEST_PG_DSN` pointing at the local test PostgreSQL on port 55439.

Result: **2 failed, 12816 passed, 6 skipped, 0 errors** (501.46s).

### Failing tests

1. `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`
   - First error line: `psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection`
   - Detail: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory`
   - Assessment: environment issue. The attack SQL `dblink_connect('dbname=postgres')` carries no host, so dblink falls back to the default Unix socket on port 5432, where no server is running here. The test's own DSN uses 127.0.0.1:55439.

2. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
   - First error line: `AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: '<vendor-name>'`
   - Assessment: a tracked file, `handover/BRIEF-PREAMBLE.md`, contains a banned vendor brand string. This is a content issue in the repository, not an environment issue. Not changed in this run.

### Errors

None.

### Skip reasons

- `tests/contracts/test_llm.py:95` (x1): Stubber refuses a malformed Converse shape before the kind sees it
- `tests/contracts/test_store_spend_ids_caps.py:107` (x2): None is the way to say no run
- `tests/test_refused_before_response.py:635` (x1): gate not in this tree
- `tests/test_step_b_e5_maintain.py:138` (x1): MAINTAIN exists from PostgreSQL 17; this server is older
- `tests/test_stop_state_roles.py:1376` (x1): from PostgreSQL 16 CREATEROLE alone cannot grant a role it has no ADMIN option on

## Raw output

Full pytest output is at `/tmp/claude-0/ev4.raw`.

# Batch 8 evidence run (EV5): origin/cloud/core-b

Evidence run only. No code changed, nothing committed or pushed.

## Setup

- Worktree: `/tmp/core-b-wt/EV5` (detached)
- Head sha: `c4f8b666e` (origin/cloud/core-b at fetch time)
- DSN: `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test`
- Command: `uv run --all-extras --group test pytest -q -p no:cacheprovider -n 3 -rs tests`
- Raw output: `/tmp/claude-0/ev5.raw`
- Wall time: 450.48s

## Result

- Passed: 12844
- Failed: 2
- Errors: 0
- Skipped: 7

## Failing tests

1. `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`
   - First error line: `psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection`
   - Detail: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory`
   - Note: the test's shared fixture uses `127.0.0.1:55439`, but this failure connects through the default local socket path, which has no server.

2. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
   - First error line: `AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: '<vendor-name>'`
   - The banned string is redacted in this file.

## Skip reasons

- `tests/contracts/test_llm.py:95` (1): Stubber refuses a malformed Converse shape before the kind sees it
- `tests/contracts/test_store_spend_ids_caps.py:107` (2): None is the way to say no run
- `tests/test_refused_before_response.py:635` (1): gate not in this tree
- `tests/test_step_b_e5_maintain.py:138` (1): MAINTAIN exists from PostgreSQL 17; this server is older
- `tests/test_stop_state_roles.py:1395` (1): from PostgreSQL 16 CREATEROLE alone cannot grant a role it has no ADMIN option on
- `tests/test_stop_state_roles.py:1411` (1): below PostgreSQL 16 only: from 16 the CREATEROLE listing does not exist

## Lint and format

- `ruff check src tests`: All checks passed (exit 0)
- `ruff format --check src tests`: 332 files already formatted (exit 0)

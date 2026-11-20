# Batch 6 evidence run (EV3)

Run against a clean detached worktree of `origin/cloud/core-b` at `/tmp/core-b-wt/EV3`. No code was changed, committed or pushed.

## Head

- `git rev-parse --short HEAD`: `7fba93b37` (commit message: `board 2026-11-20T08:19:41Z`)

## Test run

Command: `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test uv run --all-extras --group test pytest -q -p no:cacheprovider -n 3 -rs tests`

Raw output: `/tmp/claude-0/ev3.raw`

| Passed | Failed | Errors | Skipped |
|---|---|---|---|
| 12662 | 2 | 0 | 4 |

Wall time: 336.09s.

### Failing tests

1. `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`
   - First error line: `psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection`
   - Detail: `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory`
   - Note: the DSN passed in the environment points at `127.0.0.1:55439`, but this error reports a default Unix socket on port 5432. The connection in this test path does not appear to use the DSN.

2. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
   - First error line: `AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: 'Port.io'; handover/core-b/evidence/batch-5.md: 'Port.io'`
   - Two tracked handover files contain the string `Port.io`.

### Skipped tests (4 total)

- `tests/contracts/test_llm.py:95` (1 skip): "Stubber refuses a malformed Converse shape before the kind sees it"
- `tests/contracts/test_store_spend_ids_caps.py:107` (2 skips): "None is the way to say no run"
- `tests/test_refused_before_response.py:635` (1 skip): "gate not in this tree"

## Lint and format

- `ruff check src tests`: passed, "All checks passed!"
- `ruff format --check src tests`: passed, "318 files already formatted"

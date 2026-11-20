# Batch 9 evidence run (EV6)

Scope: evidence only. No code changed, nothing committed or pushed.

## Source

- Branch: origin/cloud/core-b, fetched fresh
- Detached worktree: /tmp/core-b-wt/EV6
- Head sha (short): b32e5d019

## Test run

Command: `pytest -q -p no:cacheprovider -n 3 -rs tests`, with `HADAVIN_TEST_PG_DSN` set to the test server on 127.0.0.1:55439. Run once. Raw output: /tmp/claude-0/ev6.raw

Result: **14 failed, 13089 passed, 13 skipped, 4 xfailed**, 1061.36s (17m41s). Pytest exit code 1.

## Lint

- `ruff check src tests`: All checks passed.
- `ruff format --check src tests`: **1 file would be reformatted**, 348 already formatted.
  - `src/hadavin_sdk/cli.py:630` (the `except ConfigError as exc:` clause, with a trailing comment, would be wrapped in parentheses).

## Failing and erroring tests (14)

Pytest reports these as failures. None are errors. Test ids are the function names with parameters, and the defining file in the worktree.

1. `tests/test_k5_fixes2.py::test_a_database_that_applied_the_old_name_is_refused_and_nothing_is_applied`
   - `AssertionError: Regex pattern did not match. Expected regex: '0005_evidence'`
   - Actual message: `migrations are inconsistent: GRANTS names kill_switch_resets, which no migration creates; GRANTS names kill_switch_watermark, which no migration creates`
2. `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`
   - `psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection`
   - `DETAIL: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory`
3. `tests/contracts/test_store_spend.py::test_purge_removes_closed_rows_only[memory]`
   - `assert 1 == 2` (purge_spend_reservations returned 1, expected 2)
4. `tests/contracts/test_store_spend.py::test_purge_removes_closed_rows_only[postgres]`
   - `psycopg.errors.InsufficientPrivilege: a booked spend amount may only go down through hadavin_release_expired_spend (spend_reservations)`
5. to 11. `tests/contracts/test_store_spend_ids_caps.py::test_a_purge_bound_that_is_not_an_aware_datetime_is_a_value_error_and_deletes_nothing[postgres-naive]`, `[postgres-no_offset]`, `[postgres-date]`, `[postgres-str]`, `[postgres-none]`, `[postgres-float]`, `[postgres-int]` (7 ids)
   - Each: `psycopg.errors.InsufficientPrivilege: a booked spend amount may only go down through hadavin_release_expired_spend (spend_reservations)`
12. `tests/contracts/test_store_spend_ids_caps.py::test_an_aware_purge_bound_deletes_the_closed_rows_before_it[postgres]`
   - Same `InsufficientPrivilege` error as above.
13. `tests/contracts/test_store_spend_ids_caps.py::test_an_aware_purge_bound_in_another_zone_is_accepted[postgres]`
   - Same `InsufficientPrivilege` error as above.
14. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
   - `AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: '<vendor-name>'`

Notes on the groups:
- 9 of the 14 are PostgreSQL trigger `hadavin_money_guard()` rejections on `spend_reservations`, raised by the purge path.
- Failure 1 and failure 14 are content or consistency checks, not database errors.
- Failure 2 is a socket connection failure.

## Skipped tests (13)

- `tests/contracts/test_llm.py:95`: Stubber refuses a malformed Converse shape before the kind sees it
- `tests/contracts/test_store_spend_ids_caps.py:107`: None is the way to say no run
- `tests/test_refused_before_response.py:635`: gate not in this tree
- `tests/test_step_b_e5_maintain.py:138`: MAINTAIN exists from PostgreSQL 17; this server is older
- `tests/test_stop_state_roles.py:1403`: from PostgreSQL 16 CREATEROLE alone cannot grant a role it has no ADMIN option on
- `tests/test_stop_state_roles.py:1419`: below PostgreSQL 16 only: from 16 the CREATEROLE listing does not exist
- `tests/test_stop_state_roles.py:1437`: below PostgreSQL 16 only: from 16 the accepted list has no effect
- `tests/test_stop_state_roles.py:1528`: below PostgreSQL 16 only: from 16 the CREATEROLE listing does not exist
- `tests/test_stop_state_roles.py:1543`: below PostgreSQL 16 only
- `tests/test_stop_state_roles.py:1554`: below PostgreSQL 16 only: from 16 the accepted list has no effect
- `tests/test_stop_state_roles.py:1583`: below PostgreSQL 16 only: from 16 the accepted list has no effect
- `tests/test_stop_state_roles.py:1598`: below PostgreSQL 16 only: from 16 the accepted list has no effect

(Test ids for the skips are the file:line pytest printed. The `test_stop_state_roles` skips are version gates, and the server is older than PostgreSQL 16.)

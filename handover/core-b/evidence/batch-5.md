# Batch 5 evidence: cloud/core-b

Evidence run only. No code changed, nothing committed or pushed.

- Branch: origin/cloud/core-b, detached worktree at /tmp/core-b-wt/EV2
- Head sha: a7e590310
- Raw pytest output: /tmp/claude-0/ev2.raw (outside the repo)
- Command: `pytest -q -p no:cacheprovider -n 3 -rs tests` with `HADAVIN_TEST_PG_DSN` set to the local test server on port 55439. One run only.

## Results

- Pytest: **6 failed, 12632 passed, 4 skipped** in 409.63s. Exit code 1.
- `ruff check src tests`: All checks passed.
- `ruff format --check src tests`: 313 files already formatted.

## Failing tests (6)

1. `tests/contracts/test_store_spend.py::test_the_four_methods_have_the_signatures_of_the_ticket`
   First error: `AssertionError: assert ['self', 'res...', 'agent_id'] == ['self', 'res... 'actual_usd']`. The actual signature has one extra parameter, `agent_id`.

2. `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[...]` (parametrized; the failing parameter id is not shown in the raw output)
   First error: `psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection`. DETAIL: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory. The test uses a `127.0.0.1:55439` DSN, but the connection went to the default Unix socket.

3. `tests/test_p2_postgres.py::test_audit_checkpoints_migration_adds_alg_and_label_and_old_rows_get_defaults`
   First error: `AssertionError: assert ['0004_audit_...xpired_spend'] == ['0004_audit_...reservations']`. Migration `0008_release_expired_spend` is present, but the expected list ends at `0007_spend_reservations`.

4. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
   First error: `vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: '<vendor-name>'`.

5. `tests/test_stop_state_roles.py::test_e7_a_flag_on_before_0006_stays_on_after_the_upgrade`
   First error: `AssertionError: assert ['0006_stop_s...xpired_spend'] == ['0006_stop_s...reservations']`. Migration `0008_release_expired_spend` is present, but the expected list ends at `0007_spend_reservations`. Same cause as item 3.

6. `tests/warden_port/test_audit_chain.py::test_an_outcome_that_cannot_be_appended_waits_in_the_outbox`
   First error: `assert 0 == 1`, where `log.reconcile()` returned 0 and the test expected 1.

## Skipped (4 total)

- `tests/contracts/test_llm.py:95` (1): Stubber refuses a malformed Converse shape before the kind sees it
- `tests/contracts/test_store_spend_ids_caps.py:107` (2): None is the way to say no run
- `tests/test_refused_before_response.py:635` (1): gate not in this tree

## Notes

- Items 3 and 5 share one cause: migration `0008_release_expired_spend` is in the tree, but two migration-order tests still expect the list to end at `0007_spend_reservations`.
- Item 2 looks environmental: the connection went to the Unix socket instead of the TCP DSN.
- Items 1, 4 and 6 are not diagnosed beyond the first error line.

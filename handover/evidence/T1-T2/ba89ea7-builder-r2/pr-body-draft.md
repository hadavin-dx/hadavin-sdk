## What this branch adds
Tests for the money meter (the daily and monthly spend caps) and the spend ledger behind it, on the memory store and the Postgres store, plus mutant scripts that prove each test fails when the code is broken on purpose.

## Read this first
- The 50-caller cap is NOT proven here. The failing proof is in handover/seeds/A21b/ on core/cloud-handover (a later change turns it green). What this branch proves is the cap for one caller at a time.
- This branch changes a shared test helper: a missing HADAVIN_TEST_PG_DSN now FAILS every database test when CI=true (it skipped before in the store contract tests; the ask-your-data demo tests already behaved this way). Both conftests now call one function, tests/pg_dsn.py (need_dsn_or_skip). On a developer machine the tests still skip.
- Pins: tests/contracts/test_t1_meter_cap.py has "pin today" tests recording that Limits.charge books NaN, negative and infinite costs as they are (ledger rows BL-core-a21b-seed-01, BL-core-p4d-r1-adv-A7, BL-core-p4d-r1-adv-C5). The later fix flips them.

## Every pytest step in .github/workflows/ci.yml and where it gets the database address
| Step (ci.yml line of the `run:`) | HADAVIN_TEST_PG_DSN comes from |
|---|---|
| Tests (no live calls), Python 3.13 job: `pytest -q -m "not live and not perf" -rs` (line 92) | step env: postgresql://postgres@localhost:5432/postgres (the job's postgres service) |
| Performance of the redaction patterns: `pytest -q -m perf -rs` (line 100) | step env, same value |
| Tests on Python 3.12: `pytest -q -m "not live and not perf" -rs` (line 153) | step env, same value |
No other step runs pytest. Each of the three exports the DSN, so the new CI failure rule cannot fire there unless the service is down. A green CI run on the pushed head is still needed to confirm this; it has not been seen by the builder.

## Run locally (Postgres 16, 127.0.0.1)
See the evidence folder handover/evidence/T1-T2/ba89ea7-builder-r2/ (not committed). Local Postgres is 16, CI uses 17.

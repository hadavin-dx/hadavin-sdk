# A21a (core/T1-T2-tests @ ba89ea7) round 1, egm-design review (money path, uncapped)

Reviewer: egm:egm-design (fresh, read-only, ran nothing). Saved as received; unverified until fixed and re-checked. Source code (limits.py, store/*.py, conftest store fixture), CI workflow, schema were not in its snapshot.
VERDICT: not mergeable as is. Blockers 1-2, Majors 3-6, then round 2.

## Blockers
1. tests/test_t1_meter_parallel.py (4 tests, lines 33-53) fails the full suite (evidence row 4: 4 failed, exit 1). Fix: move the file to the A21b branch (lead's plan); no xfail or skip. Reword the docstrings in test_t1_meter_cap.py (lines 8-9) and meter_mutants.py (lines 9-11) that say "the parallel ones FAIL on this code" to point to tests/test_t1_meter_parallel.py on branch A21b.
2. The Postgres kill proof is not reproducible from the branch: evidence row 5 ran a postgres_mutants.py (P1-P4) that is not in the diff. Fix: commit tests/postgres_mutants.py (fails when HADAVIN_TEST_PG_DSN is missing; docstring says how to run). P3 is killed by a database CheckViolation (spend_month_month_check) in setup, not by a time-rule assertion (log lines 12-14): rewrite to write a valid value (month number taken from the day number) so an assertion catches it, or label it a schema-constraint kill and add a separate mutant past the constraint.

## Majors
3. T1 cap tested only on MemoryStore (build_limits defaults to MemoryStore, meter_support.py:80-91; cap tests and 50-parallel tests do not use the `store` fixture). Production money uses Postgres. Fix: take `store` in the three sequential cap tests, pass `store=store` to build_limits, move them to tests/contracts/ or add a contracts copy; add a parallel Postgres variant (A21b).
4. The 50-parallel harness cannot pass for a choke-point fix: `admit_check_then_charge` (meter_support.py:94-96) is only `not limits.blocked(AGENT)` and run_parallel then calls limits.charge itself, so a correct reserve/settle fix would double charge (control test patches charge to 0, test_t1_meter_cap.py:75). Fix: make `admit` a (reserve, settle) pair supplied by the caller and have run_parallel call settle only; assert sum of final totals <= cap + W.
5. No negative control for the harness itself once the parallel file moves: add a harness-only test with a stub meter (plain function pair, separate check and charge) asserting run_parallel(...) == CALLERS, proving Schedule forces the worst interleaving.
6. Mutants miss real time-rule bugs: year dropped from month key (`(d.year, d.month)` to `d.month`) survives (windows at most 31 days); add memory mutant (ADD_SPEND_FILTER, SPEND_TOTALS_FILTER) and Postgres twin and a test with charges in 2025-03 and 2026-03 (one year plus 1 minute, and 24 months). No Postgres mutant for a missing agent filter (S3/S5 twins) or for the day/month counter skipped. No test for both budgets over the cap at once (does blocked return both reasons?). No test for negative, NaN or Infinity charge (NaN makes `day >= budget.daily` false so the cap never blocks): parametrize charge(AGENT, Decimal("NaN")), Decimal("-1"), Decimal("Infinity") to raise or leave totals unchanged; if source accepts them it is a finding for A21b.

## Minor
7. Weak kill messages: L5 expects "assert {", L6 and S6 both "read at". Use custom assert messages (L5: msg="reads changed a total" at test_t2_ledger_replay.py:118) and distinct text per mutant.
8. Money as integers rule: all amounts are Decimal USD strings (source Budget is Decimal; state as a known source deviation in the PR). Add a Postgres numeric-scale test (charge Decimal("0.0000001"): not silently rounded to 0, or rejected).
9. Fake clock sound; limits: hadavin_sdk.limits.now is patched so real now() only in the IST test; Limits.stop/reset write audit and are untested; fake clock does not cover the Postgres server NOW()/CURRENT_DATE. Add a one-line comment and a test that a past date is used (no server-time column).
10. Postgres skipped silently in CI (56 skips without DSN). Add a guard in the contracts conftest: if os.environ.get("CI") and no DSN, `pytest.fail` instead of skip; confirm ci.yml exports the DSN.
11. test_t1_meter_cap.py:26 cap 0.50 with cost 1.00: add a case where cost is not W to show the overshoot bound.
12. Evidence hygiene: first logs overwritten by another session (-final used); bandit unpinned via uvx; full suite only 3.13 without DSN; no evidence the shell was clear of cloud variables.

## Isolation (unchecked)
Postgres tests share AGENT and fixed dates; a store fixture that does not truncate spend tables would leak totals. Run the contract file twice on one DSN and in random order; add to evidence.

## Not checked
Source code and conftest store fixture; CI workflow, schema, migrations; Limits.stop/reset; tools/mutation_runner.py; random order, twice-on-one-database, multi-process race; py3.12 mutants.

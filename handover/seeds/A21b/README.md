# A21b seed (from the A21a fix builder, round 1, 2026-11-10)

Plan rows: A21a (T2 tests, branch core/T1-T2-tests) and A21b (T1 own-meter 50-parallel, after A13) in
handover/PARALLEL-PLAN-2026-11-10.md. The four failing 50-parallel tests were removed from the A21a branch (they
fail on the current Meter and a red main is not allowed; no xfail, no skip). They live here instead.

Files
- tests/contracts/test_t1_meter_parallel.py: the 50-parallel tests, ported to the new harness (a caller is a
  (reserve, settle) pair; `run_parallel` calls settle only; every test takes the `store` fixture, so memory and
  postgres; asserts admitted <= floor/ceil(cap/W) and the day total <= cap + W). Fails on the current Meter (50 of 50
  admitted). To use it: put it in tests/contracts/ on the A21b branch (after A21a is merged) and swap
  `check_then_charge(limits)` for the (reserve, settle) pair of the new meter.
- tests/contracts/test_t1_charge_values.py: FINDING, see below. Fails on the current code.
- meter_support.py.after-A21a-r2: the harness as it is on the A21a branch (copy for reference; the branch is the source).
- *.ORIGINAL-ba89ea7.py: the files as they were at ba89ea7 (old harness: `admit` was a check only and `run_parallel`
  charged W itself, so a reserve-style fix would have been charged twice).

Still to do in A21b (not done in A21a)
- postgres with several PROCESSES (the store's own lock is per process); a parallel run on the postgres store is in the
  seed tests through the `store` fixture but all threads share one store object.
- parallel run of the real new Meter once A13 lands; mutants of the reserve step.

FINDING for A21b (found by A21a round 1, probed on both store kinds, source NOT changed in A21a)
The meter accepts charge values that break a cap:
- Decimal("NaN"): stored; `Limits.blocked` then raises decimal.InvalidOperation for the rest of the day and month.
- Decimal("-1"): stored; the day total goes down, so a negative charge buys back a call.
- Decimal("-Infinity"): stored; the totals stay -Infinity, so `blocked` never reports a budget again that day and month.
- Decimal("Infinity"): stored; both budgets read as full (fails closed).
Fix at the choke point: `Limits.charge` rejects a value that is not finite or is below zero before calling the store,
and each store's `add_spend` rejects it too (so a direct caller cannot bypass). Then test_t1_charge_values.py passes.
Also stated, not a bug: money is `Decimal` dollars in the source (`Budget`), not integers; the tests keep that type.

Verified by the A21a builder (scratch copy, 2026-11-10): both seed files fail on the current Meter (16 failures: 8
parallel on memory and postgres, 8 charge-value cases); with a lock-protected reserve-then-no-op-settle pair swapped
into the parallel file, the 8 parallel tests pass on both stores. Log: handover/evidence/T1-T2/ba89ea7-builder-r2/seed-check.log.

(Copied by the cloud session on 2026-11-10 from /home/user/build/A21b-seed so the failing proof of the concurrent-caller race lives in git. Related rows: BL-core-a21b-seed-01, BL-core-p4d-r1-adv-A7 and C5.)

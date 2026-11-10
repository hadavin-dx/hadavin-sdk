# A21a (core/T1-T2-tests @ ba89ea7) round 1, codebase-details review (money path, uncapped)

Reviewer: egm:egm-codebase-details (fresh, read-only, ran nothing). Saved as received; unverified until fixed and re-checked.

## Blocker
- B1 Suppression: tests/test_t1_meter_parallel.py:28, `)  # fmt: skip` on the `from tests.meter_support import (...)` block. CLAUDE.md: no suppressions. Fix: delete it and run `ruff format`; re-run `ruff format --check` at the final head and quote the output (evidence row 1b says only "see log").

## Majors
- M1 tests/contracts/test_store_time_rules.py:30 imports `DAYS31, HOURS25, STARTS, WINDOWS, event_times, oracle` from tests/test_t2_ledger_replay.py: a contract test depends on a sibling test file; the money oracle lives in a test module. Fix: move `oracle`, `event_times`, `STARTS`, `WINDOWS`, `HOURS25`, `DAYS31`, `MINUTES6`, `USD` into tests/meter_support.py, import from there in both files, delete duplicate `USD` at test_store_time_rules.py:32 (optionally move `replay()` too).
- M2 Duplicated test bodies between tests/test_t2_ledger_replay.py and tests/contracts/test_store_time_rules.py (agent isolation, own-agent month total, one-microsecond day, 25h and monthly rollover; the contract copy also checks `add_spend` for the other agent, the memory copy does not). Fix: keep one copy per scenario in the contract file; re-point `only_test` ids in meter_mutants.py (S3, S5, L7 name memory tests; the mutant script runs only test_t1_meter_cap.py and test_t2_ledger_replay.py) or keep memory copies as named killers; decide one way.
- M3 Stale wording: test_t1_meter_cap.py:1-9 says "the parallel ones FAIL on this code (see the lead report)" but holds no parallel test; "lead report" is a private note; test_t1_meter_parallel.py:1-9 same copy-paste; all three files cite "STANDING ORDERS 6d, plan v4" (private). Fix: cap file keeps the "what the code does" paragraph only; parallel file states the failure in-repo (every caller passes `Limits.blocked` before any caller reaches `Limits.charge`; fix is a reserve-before-call step, plan row A13); replace the private cite with handover/PARALLEL-PLAN-2026-11-10.md row A21a/A21b or drop it.

## Minor
- m1 FakeClock (meter_support.py:458) duplicates the small Clock in tests/test_cuj.py:23, test_s6_approvals.py:20; it is a superset (set/advance). Record the reason in its docstring.
- m2 `cast(Registry, SimpleNamespace(...))` in make_limits (meter_support.py:476-480) hides type errors; build a real Registry or say why not.
- m3 `NoAudit` (meter_support.py:438-455) mirrors AuditSink by hand; annotate as AuditSink instead of cast.
- m4 Brittle `expect` strings in meter_mutants.py (L1 "assert 4 == 3", L3, L5, L7); use custom assert messages as the S mutants do.
- m5 No mutant targets postgres-specific upsert counters (store/postgres.py:416-440) or the contract file; check postgres_mutants.py P1-P4 cover them, else add spend/spend_month mutants (reviewer could not read postgres_mutants.py).

## Checked, fine
Real API calls (Limits.charge/blocked, Store.add_spend/spend_totals, `hadavin_sdk.limits.now` patch target, models.now) match src; mutant lines L1-L8, S1, S6 match source lines, filters unique; Postgres skip goes through the existing `store` fixture (pg_schema skips without DSN, one schema per test); no os.environ use in the diff; no hardcoded paths/DSNs/credentials; no dev/staging names; no noqa, type: ignore, nosec.

## Not checked
Nothing run; evidence table not cross-read against raw logs; tools/mutation_runner.py and tests/stage_mutants.py not in the on-disk tree (Mutant signature unconfirmed); ruff on meter_mutants.py (E402) relied on evidence; 3.12 full suite; bandit pinning; whether A13 changes the Limits API.

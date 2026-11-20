# Integration door fix (tests/triggers on core/integration-dryrun)

## Root cause (two test-support gaps, no product bug)
1. Child processes get no caps seeding. core-b's live loop reserves before the model call
   (`Limits.reserve` -> `PostgresStore.reserve_spend`), which reads `hadavin_caps`. core-b seeds it with the
   `_seed_caps_before_reserve` fixture of tests/conftest.py, a monkeypatch that exists only in the pytest process.
   The crash-launcher children never got it: no cap row -> `limits.limits_unavailable` -> NEEDS_PERSON, so the run
   ended in the wrong state (first failure: `'NEEDS_PERSON' != 'NO_ACTION'`, r1-store.get_run-1-before) and the
   crash points after the reserve were never reached ("the child did not end within 30.0 s").
2. The crash tables still described the old loop. The merged loop (src/hadavin_sdk/runtime/agent_loop.py,
   limits.py) no longer calls `add_spend`/`add_cost`; it calls get_kill_switch, `reserve_spend` before `llm.chat`
   and `settle_spend` after (the settle books the run cost). Points `store.add_spend:before` etc. were never hit
   (`assert () == ('store.add_spend:before',)`, child never ends).
The stage/demo refusal, model_gate, own_money_rights_problems and TriggerSettings were NOT involved.

## Diff (tests/triggers only, 3 files, +95/-16)
- crash_launcher.py: `RESERVES = hasattr(Limits, "reserve")`; `install_pg_test_seeding()` applies the same three
  wrappers as conftest (tests/money_caps_seed.py) to PostgresStore inside a child; ImportError -> nothing installed;
  `_store("postgres")` calls it.
- test_t5_crash_matrix.py / _paths.py: child_main calls `install_pg_test_seeding()`; wrapped method lists, the
  HANDLE_STEPS table and the READ/PROPOSE path rows are conditional on RESERVES (reserve: get_kill_switch,
  reserve_spend, llm.chat, settle_spend; else the old add_spend/add_cost rows); point-count assertions follow it
  (20 steps / read 61 / propose 82 points with reserve). No assertion weakened, nothing skipped.

## Counts (HADAVIN_REQUIRE_PG=1, PG16 55433)
- merged tree before: 144 failed (22 + 120 + 2), 1218 passed, 4 skipped.
- merged tree after: the three files 454 passed; whole tests/triggers 1374 passed, 4 skipped, 0 failed.
- core-a head (patch applied in a scratch worktree, RESERVES False): crash_matrix 83 passed; paths + postgres 359 passed.

## What the lead carries into the integration
Apply handover/core-a/pr/door-merged-support.patch (`git apply`; it applies cleanly to core-a head too and to the
merged tree, where it is already applied in worktree /home/user/wt/doorm, branch wip/core-a-door-merged, uncommitted).
Future: if core-b renames the seed helpers in tests/money_caps_seed.py, update `install_pg_test_seeding`.

## Follow-up: money end state per crash point (door-merged-support-2.patch, applies after door-merged-support.patch)
Review found that with RESERVES nothing read the money state. Added (RESERVES mode only; the RESERVES=False matrix is
unchanged): tests/triggers/crash_money.py and per-point STATIC expectations (from the call tables, not from a run):
before `reserve_spend` no row, day total 0; between `reserve_spend:after` and `settle_spend:before` exactly one OPEN
row per call in flight (reserved_usd > 0, day total = sum of the open holds); after `settle_spend` the row is settled
at the real cost (0 with the model doubles), day total = settled costs. After restart + tick + signed retry: a run
with a row is never booked again (its rows are those of the kill; an open hold STAYS open, the documented step-1
limit: it waits for expiry), a run without a row ends with every call reserved and settled; the day total always
equals the rows' sum. Read by plain SQL (spend_reservations, spend) on PostgreSQL, by the store's own dict and
spend_totals on memory. RESERVES is tied to the loop (`check_reserves_wiring`: the loop source calls limits.reserve
and money_caps_seed.py exists, else a clear import-time failure; `test_reserves_is_what_the_loop_really_does`:
one real request makes exactly one reserve_spend call iff RESERVES).

LIMIT: the children's seeding (`install_pg_test_seeding`) widens `max_day_skew` to 100000 days and sets
`min_expiry_age` to 0. The matrix therefore does NOT exercise the real day window or the 3600 s expiry floor and
proves nothing about either; it only proves the door's one-run-row / one-approval / one-hold guarantees.

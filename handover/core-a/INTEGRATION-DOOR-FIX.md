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

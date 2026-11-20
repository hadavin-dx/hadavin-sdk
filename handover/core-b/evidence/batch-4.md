# Batch 4 evidence: cloud/core-b

- Source: origin/cloud/core-b at e125a7bc3 ("board 2026-11-20T07:31:22Z"), detached worktree /tmp/core-b-wt/EV1
- Postgres DSN: postgresql://postgres@127.0.0.1:55439/hadavin_test (credentials: none, trust auth)
- Nothing committed or pushed.
- tests/test_grants_negative_roles.py: ABSENT in this tree (exists only on wip/cloud-core-b/Y-integration). Skipped as instructed. Not run.
- Test set: tests/test_stop_state_roles.py tests/test_spend_reservations_pg.py tests/test_audit_drain.py tests/test_audit_drain_transient.py tests/test_p7_tick.py tests/contracts

## Results

| Run | Command | passed | failed | errors | skipped | exit |
|---|---|---|---|---|---|---|
| 1 (one worker) | pytest -q (serial) | 1302 | 0 | 0 | 3 | 0 |
| 2 (-n 3) | pytest -q -n 3 | 1302 | 0 | 0 | 3 | 0 |

Failing test ids: none. Error lines: none.
Skipped test ids: not captured (no -rs in the command). The 3 skips are the same count in both runs.

Static checks:
- `ruff check src tests`: All checks passed!
- `ruff format --check src tests`: 309 files already formatted

## Notes on run validity

- An earlier attempt of run 1 in the background stopped after about 11% with no summary line. The wrapper reported exit 0, but there was no summary and no EV1 pytest process left. That attempt is not counted; run 1 was rerun in the foreground and that rerun is the one recorded above.
- Other pytest jobs were running against the same PostgreSQL server during this batch, from other worktrees: /tmp/core-b-wt/MUT (mutation runs, `-x` against limits/spend/p7 tests) and a scratchpad copy `ycopy` (`-n 3` on stop_state/spend_reservations, with a patched migrate lock). The task asked for one worker because of shared stop-state role state. I did not stop or touch those jobs. Overlap with the recorded runs is possible, so a clean pass here is not a strict isolation proof.

## Raw tail: run 1 (serial, rerun)
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
............................................s........................... [ 38%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 55%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 71%]
...............................................................s........ [ 77%]
.........s.............................................................. [ 82%]
........................................................................ [ 88%]
........................................................................ [ 93%]
........................................................................ [ 99%]
.........                                                                [100%]
1302 passed, 3 skipped in 557.49s (0:09:17)
EXIT_CODE=0

## Raw tail: run 2 (-n 3)
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
......................................................s................. [ 33%]
........................................................................ [ 38%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 55%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 71%]
......s............................................................s.... [ 77%]
........................................................................ [ 82%]
........................................................................ [ 88%]
........................................................................ [ 93%]
........................................................................ [ 99%]
.........                                                                [100%]
1302 passed, 3 skipped in 175.79s (0:02:55)
EXIT_CODE=0

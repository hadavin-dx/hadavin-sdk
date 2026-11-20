# Flake: test_memory_raise_at_point[propose01-store.create_run-1-before]

Verdict: TEST RACE (the test reads the run too early). The code window is real but benign in production.
Not reproduced in two runs (see Evidence); the verdict comes from reading, and the failure text fits it exactly.

## Interleaving
Path `propose`, crash at store.create_run:before, so after the kill there is no row (row is None).
1. Step (a): the retry POST is accepted (OK); a NEW loop thread starts a fresh run.
2. The test calls `_memory_wait(store, run_id, path.final)` with path.final = WAITING_FOR_APPROVAL. It only
   looks at the row state.
3. agent_loop.py:762 `self._to(run, WAITING_FOR_APPROVAL)` writes the row; the approval request is saved only
   later, inside `self.hooks.request_approval(...)` (line 763). Between the two the row is WAITING with no request.
4. The test thread sees WAITING, `_memory_wait` returns, and `run_tick(...)` (step b) runs at now + TICK_LATER
   (one hour later), so the row counts as old enough for `stuck()`.
5. tick.py `stuck()` orphan rule (lines ~155-175): WAITING_FOR_APPROVAL and no approval in
   {PENDING, APPROVED, REJECTED, EXPIRED} -> NEEDS_PERSON/approval_missing. That is the observed failure:
   got ('NEEDS_PERSON','approval_missing'), expected ('WAITING_FOR_APPROVAL', None).
The loop thread then saves the request, but the row is already NEEDS_PERSON. Needs the loop thread to be
descheduled between line 762 and the request save while the test thread polls (10 ms sleep): load only.

## Why it is not a production bug
The real tick uses the real clock; a run is an orphan only if quiet for more than stuck_after_s (floor 60 s
default). The window is microseconds; the test's fake clock (+1 h) is what makes the window visible. The rule
("a crash between WAITING and saving the request leaves a wait nobody can answer") is by design.
Note (optional hardening, not needed): persisting the request before moving to WAITING would close the window
but changes the crash matrix rows; do not do it for this flake.

## Proposed fix (test only; do not weaken any assertion)
In `_memory_wait` (tests/triggers/test_t5_crash_matrix_paths.py ~880) for the row-None branch, also wait for the
loop to be done, not just the state: wait until the state is reached AND the requests are in their final shape
(`_memory_requests(store)` non-empty for the `propose` path, i.e. `req_state(...)` equals the path's final req),
or better, until the runner is idle (`runner.close()`-style drain / no running loop thread) before `run_tick`.
Same check is worth adding at the second `_memory_wait`-like spots (grep `path.final` waits, e.g. line ~949 and
the sqlite/pg twin of this test around line 800-850) so every `propose`/`approve` id is covered; the 4 reruns
of this id passing is consistent with a low-probability window.

## Evidence
- Failure section: handover/core-a/raw/D-fix9-tests.log lines 25-60 (traceback at test line 958, assertion on `after`).
- Earlier full runs: handover/core-a/raw/D-crash-matrix-paths-pg16.log (346 passed) and D-crash-matrix-pg16.log
  passed the same id (the failure is the only one of this id in handover/core-a/raw).
- Reproduction tries: raw/FLAKE-crash-matrix-paths-1.log (-n 0, only the two propose01 ids matching
  `-k "test_memory_raise_at_point and propose01"`: 2 passed; whole-file run alone was not done, to keep to the
  two allowed runs) and raw/FLAKE-crash-matrix-paths-2.log (crash matrix paths + fuzz_concurrent, -n 3: 355 passed).
- Code: src/hadavin_sdk/runtime/agent_loop.py:759-768, src/hadavin_sdk/runtime/tick.py:154-176,
  tests/triggers/test_t5_crash_matrix_paths.py:469-482 (run_tick, TICK_LATER), 880-889 (_memory_wait), 940-958.

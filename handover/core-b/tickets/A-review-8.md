# A-review-8: fresh review of A10 (E9 verdict, ORDER 023), branch cloud/core-b

Reviewer: fresh (not the builder). Source read-only. Test run once:
`HADAVIN_TEST_PG_DSN=... pytest tests/test_audit_drain_a10.py tests/test_mutants_audit_drain_a10.py` -> 20 passed (0.62 s).

Verdict: NOT CLEAN. One Major (verdict item (d) is not reachable on the real deployment), the rest Minor.

## Major

### M1. Quarantine never happens in production: the failure counter lives in a process that lives one tick
- src/hadavin_sdk/audit/chain.py:267 (`_fail_ticks`, in memory), :554-558 (count and rename at N=3), defaults.py:179.
- How the tick runs: cli.py:123 `tick` = "one pass of the housekeeping steps (run every 30-60 s)"; cli.py:181-182 -> `_tick()` (cli.py:389-415) builds the app, calls `run_tick(app)` (runtime/tick.py:380) once and returns the exit code. There is no loop, no daemon and no `--loop` flag anywhere in src, docs or README (grep `--loop` returns nothing). The ticket text (A10, "needs a long-lived tick process (the usual `tick --loop`)") names a mode that does not exist. A scheduler starts a new process each time, so `ChainAudit` is rebuilt and `_fail_ticks` starts empty: it can only ever reach 1.
- Scenario: one outbox row gets a class 22/23/54000 refusal (for example a body with a NUL or lone surrogate that the chain column refuses). Tick 1, 2, 3, ... 10000: the row is read, refused permanently, `_fail_ticks[row]=1`, process exits, counter lost. The step `audit_drain` raises "1 rows not writable" and `run_tick` exits 1 on every tick for ever; the row is never renamed to `poison:`, `quarantined=` is never logged, the "N poison rows quarantined earlier" state is never reached. Verdict (d) "quarantine after N ticks, visible, counted" is built and tested but dead code on the deployed shape. The ticket admits this ("the safe side") but the lead's verdict asked for the opposite outcome (the step stops failing, the row is parked visibly), so the admission is a deviation, not a satisfaction.
- Does the poison row block newer rows? Not directly: `_drain_item` returns False for a permanent refusal (chain.py:547-559), so the pass continues to the next item, and newer good rows drain in the same pass (verified by reading; test at tests/test_audit_drain_a10.py:158-165 covers it for one instance). The tick step still fails every tick (exit 1), which defeats the "step stops failing" intent and trains operators to ignore the alert. Second-order block: poison rows are never skipped by the SELECT (only the `poison:` prefix is), they sort by ts and each takes one of the `drain_batch` slots (chain.py:499-519). With >= drain_batch (default 500) un-quarantined poison rows older than the good rows, no good row is ever read: a real block, reachable only with that many poison rows, but quarantine is exactly what was meant to prevent it.
- Test gap: every quarantine test reuses ONE `ChainAudit` across `reconcile()` calls (tests/test_audit_drain_a10.py:158-194), which is not how the tick runs. The mutant "drop quarantine" (m3) is killed by the same single-instance test, so the suite is green while production never quarantines.
- Smallest fix, no new table, no migration (runtime has INSERT and DELETE on audit_outbox, not UPDATE):
  1. Preferred (about 6 lines): measure the age from the row's own timestamp. New default `AUDIT_QUARANTINE_AFTER_S` (for example 3 x the tick period = 300 s). In `_drain_item`, for a permanent non-42501 refusal of an outbox row on a tick pass, quarantine when `now - event.ts >= AUDIT_QUARANTINE_AFTER_S` (use the injectable clock; drop `_fail_ticks`). A permanent refusal is deterministic, so waiting buys nothing beyond giving an operator a window; `ts` is at or before the time the row was parked, so the age is an upper bound and is stable across processes. Transient and 42501 rows are untouched as now.
  2. Alternative (persisted count in the id): on each failing tick rename `<id>` to `strike<k>:<id>` by INSERT-then-DELETE, reads accept the `strike` prefixes and strip them before the `event.event_id != row_id` check (chain.py:515), at k = N rename to `poison:`. More code and more writes per tick; only worth it if a count rather than an age is wanted.
  3. Either way add a test that builds a FRESH `ChainAudit` per tick (3 instances, same database) and asserts the row ends as `poison:<id>` and the step stops raising for it; keep the single-instance tests as well. Re-aim mutant m3 at it.
  4. Correct the ticket text and the docstrings (defaults.py:177-179, chain.py:265-266) that name `tick --loop`.

## Minor

### m1. The classifier and the limit are fine, but no guard covers a numeric literal in table.py (item (c))
- backends/table.py:206-208: `Field(default=None, ge=1, le=5000)`. The "no hard-coded values" guard (tests/test_no_hardcoded_values.py) scans string constants (AST) for keys, account ids, ARNs, URLs and hosts only; it cannot see a numeric bound, so nothing would have caught this literal and nothing would catch the next one. The module cannot import `defaults` (the ticket says so), so the real defect is that 1 and 5000 are not named anywhere. Fix: a defaults constant `AUDIT_DRAIN_BATCH_MAX = 5000` plus a one-line test that table.py's `le` equals it (the test file may import both), or a generic test that the bound in `ChainSettings` matches defaults. Not a Major: the value is a validation ceiling, not an environment.
- Is 5000 safe? Against A-hostile-review-2 (20000 rows x 5 KB = 45 s, 106 MB, about 2.25 ms and 5.3 KB per row): 5000 rows is about 11 s and 26 MB at 5 KB bodies, which a tick tolerates; the default 500 is about 1.1 s and 2.6 MB. But the same review notes "a body can be 1 MB": 5000 x 1 MB is about 5 GB in the one in-memory page list (`items`, chain.py:495-518), and the `want`-sized pages are all held at once. At the default (500 x 1 MB = 500 MB worst case) it is already heavy. Not safe as a ceiling unless bodies are bounded elsewhere; suggest a ceiling of 2000 or a byte cap, or confirm the event size cap (if one exists) in the ticket. Rated Minor because the default is 500 and it is an operator opt-in.

### m2. Sleep under `_flush_lock` (item (b)): bounded, acceptable, but not "every append during an outage"
- chain.py:368-370, 401-414. Worst case 0.05 + 0.1 = 0.15 s per flush (two sleeps between three attempts), as stated. In a real outage the append at write_intent/write_outcome fails first (chain.py:315, 328) and `_flush_pending` is only called after a SUCCESSFUL append (chain.py:320-321, 342-343), so an outage does not make every append sleep. The sleep shows up only when appends succeed but the head parked event keeps failing transiently (for example a lock wait or timeout that hits that one event): then every write_intent/write_outcome pays +0.15 s and other threads queue on `_flush_lock` (the pre-drain `_drain_pass` takes the same lock, chain.py:491) for that time. That is bounded and small next to a model call; acceptable. Two tightening options, both optional: skip the backoff when the previous flush already failed within the last second (so one stuck event costs 0.15 s once per second, not per append), or flush from the tick only. No test measures the cumulative cost; the fake sleep tests prove the cap, not the total.
- Never dropped: confirmed. After the last attempt the event stays at `_pending[0]` (chain.py:371-379), is logged with a count, and `reconcile` reports it via `_transient_stuck` / `in_memory` (chain.py:437). Still lost if the process exits first (stated, unchanged, in-memory by design).

### m3. Mutants cover the four items the verdict named but none targets the process-lifetime property
- tests/test_mutants_audit_drain_a10.py (m1 classifier flip, m2 LIMIT dropped, m3 quarantine dropped, m4 backoff cap dropped), tests/audit_drain_a10_mutants.py. Good: each is killed. Missing (add with M1): "counter not shared across instances" (the fresh-process-per-tick mutant), and "42501 counted" / "transient counted" are tested as behaviour but not as mutants.

## Item-by-item against verdict E9 / ORDER 023

- (a) one classifier everywhere: MET. `_is_permanent` (chain.py:100-) is the only classifier; used by `_flush_pending` (:371), `_drain_with_backoff` (:409), `_drain_item` (:547), outbox SELECT handling goes through `_is_outage` only for the quiet path (:427) and fails the step otherwise (:429). Inverted as ordered: only 22, 23, 42501, 54000 (defaults.py:183) permanent; unknown errors transient and reported.
- (b) bounded retries, parked, visible, never dropped: MET (see m2).
- (c) LIMIT from config with a safe default: MET functionally (default 500, `backends.audit.drain_batch`, passed to `ChainAudit`); see m1 for the literal bounds and the 5000 ceiling.
- (d) quarantine after N ticks, visible, counted, never deleted: NOT MET in production (M1). Rename keeps the body (chain.py:568-578), never deletes without an INSERT of the kept copy; visible via the "poison rows quarantined earlier" text; but unreachable with one process per tick.
- Mutants for each: present for the four verdict items (m3 above for the gap).

## Files
- /home/user/hadavin-sdk/src/hadavin_sdk/audit/chain.py
- /home/user/hadavin-sdk/src/hadavin_sdk/backends/table.py
- /home/user/hadavin-sdk/src/hadavin_sdk/defaults.py
- /home/user/hadavin-sdk/src/hadavin_sdk/cli.py
- /home/user/hadavin-sdk/tests/test_audit_drain_a10.py
- /home/user/hadavin-sdk/tests/test_mutants_audit_drain_a10.py

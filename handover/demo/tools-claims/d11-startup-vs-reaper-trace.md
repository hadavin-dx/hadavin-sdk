# out-d11: do the contract start-up and reaper sentences contradict each other?

Studio folder: not present in this container (/studio missing); rules not consulted, no R-numbers cited. EVIDENCE RUNNER: ran and recorded, no lint, no pytest, no network, no file changes in the tree. Tree: /tmp/v8work.

## Short answer
Yes, in effect. The two sentences describe two different start-up modes and each omits the other. Neither is wholly wrong. Sentence B (the "counts a try" one) is FALSE for the reaper-on path that production uses and TRUE only for the reaper-off path. Sentence A is TRUE.

Line numbers: the brief says 307 and 316; in this tree the sentences are contract.md:312 (A) and contract.md:321 (B). Lines 307/316 are other bullets.

## What decides it (code)
- src/lead_desk/desk.py:580-618 `Desk.startup()`. Step (3) at desk.py:612-616: `if not self._background:` it selects every `state='pending'` row (no backoff test, no `auto_attempts` test) and calls `run_followup(lead_id)`.
- `self._background` is set True at desk.py:635 inside `start_background()` (desk.py:621-637) and reset at desk.py:644 by `stop_background()`.
- src/lead_desk/server.py:1195-1196: production order is `desk.start_background()` then `desk.startup()`, so production is always reaper-on.
- desk.py:1782-1804 `run_followup` -> desk.py:1806-1820 `_run_followup` -> desk.py:1910+ `_claim(None, lead_id, ("pending",))`. The claim SQL is `_CLAIM_SQL[("pending",)]` at desk.py:190-194: `UPDATE ... SET state='sending', auto_attempts=auto_attempts+1 ... WHERE lead_id=? AND state='pending'`. No backoff check anywhere on this path.
- The backoff check exists only in two other places: `Desk.reap_once` due-filter, desk.py:737-744 (`updated_at + wait_before_drive(tries, last_error) <= now`), and `Desk._pending_and_due`, desk.py:1417-1431 (client replays only). `wait_before_drive` is gate.py:78-87 (2 s if auto_attempts==0, else `backoff_after`: 1, 2, 4, 8 s; 5 s for no_descriptors; model-busy value for busy errors).
- gate.py itself has no start-up logic; it only supplies the constants.

## Sentence A: contract.md:312
Sentence: "With `start_background()` called first, start-up does not drive pending follow-ups (the reaper does), so serving starts at once."
Path: desk.py:614 `if not self._background` (False when the reaper was started first) so desk.py:615-616 is skipped.
Trace, row pending, auto_attempts=1, backoff (1 s after try 1) not over, reaper on:
1. `startup()` step (2) `_requeue_sending` only touches `state='sending'` rows; the pending row is untouched.
2. Step (3) skipped. auto_attempts stays 1. No try counted.
3. Reaper thread waits for `_started` (set desk.py:611), then `reap_once`: row is `pending`, `updated_at+1 <= now` false, so not in `due`; not driven.
4. A later pass, once `updated_at+1 <= now`, drives it: claim makes auto_attempts 2.
Verdict: TRUE. Small precision gap: "the reaper does" drive them only when due (fresh rows after 2 s, retries after their backoff), not at once. Suggested wording: "start-up does not drive pending follow-ups; the reaper drives each one when it is due (a new row after 2 s, a retried row after its backoff), so serving starts at once."

## Sentence B: contract.md:321
Sentence: "Start-up counts a try for a row whose backoff has not passed."
Path: desk.py:612-616 -> run_followup -> `_claim` -> `_CLAIM_SQL` desk.py:190-194 (auto_attempts+1, no time test).
Trace, same row (pending, auto_attempts=1, backoff not over):
- Reaper OFF (`start_background()` never called, or already stopped): step (3) selects the row, `run_followup` claims it at once: state `sending`, auto_attempts 1 -> 2, backoff ignored, the drive runs (a send may happen right away). So the sentence is TRUE here. It also ignores the longer 5 s no_descriptors / busy backoffs.
- Reaper ON (the production order, server.py:1195-1196): step (3) skipped, nothing counted until the reaper finds the row due, and then the backoff has passed. So the sentence is FALSE here.
Verdict: PARTLY (true only when no reaper was started first; false for the normal server).
Why it reads as a contradiction: A says start-up does not drive (reaper on); B says start-up counts a try for a not-due row (reaper off). B does not say which mode, and it sits in a bullet about socket timeouts, where it looks unconditional.
Exact replacement: "Start-up without a reaper (`start_background()` not called first) drives every pending follow-up at once and counts one try for each, even a row whose backoff has not passed. With the reaper started first, start-up drives nothing and counts no try; the reaper drives a row only when its backoff has passed." Also move it out of the socket-timeout bullet.

Possible code-level note (not changed, no edits allowed): the reaper-off start-up path ignores backoff, whereas replays (`_pending_and_due`) and the reaper honor it. That is a behaviour difference, not only a wording one; the owner or lead should say whether it is wanted (a restart without a reaper then spends a try on every pending row). Not tested or run by me.

## Tests
Grepped tests/ for start-up, backoff, auto_attempts, background, drive.
- Covers sentence A (partly): tests/test_desk_http_edge_cases.py:449 `test_startup_50_pending` (reaper first, startup returns under the limit, reaper then sends all 50; it would fail if start-up drove them synchronously, since the sender takes about 15 s); tests/test_server_main_reaper.py:77 `test_main_runs_reaper_while_serving` (order start_background then startup, `_background` True); tests/test_server_main_reaper.py `test_main_reaper_sends_and_frees_lock`. None puts a row with auto_attempts>=1 and a live backoff through start-up, so none checks "no try counted".
- Sentence B: I found NO test that asserts it, for either mode. tests/test_desk_edge_cases.py (startup calls at 386-927) and tests/test_crash_points.py have no assertion on auto_attempts after startup (only test_desk_edge_cases.py:502, a person's Retry). So no test would fail if B were wrong, in either direction. tests/test_model_stamp_and_reaper.py:347 checks the reaper does not re-drive a no_descriptors row at once (backoff honored by the reaper), which supports the reaper-on half of the trace.
- Missing tests, to add if the wording is kept: (1) reaper off, pending row auto_attempts=1 with updated_at=now, `startup()`, assert auto_attempts==2; (2) reaper on, same row, `startup()` then `reap_once()` before the backoff passes, assert auto_attempts==1 and outbox count 0, then advance the clock and assert 2.

## Not checked
No test was run (brief forbids it); the traces are from reading the code only. Did not read all of contract.md beyond lines 295-321 and the grep hits; other sentences about start-up (contract.md:87-88, 287, 300-301) were seen in grep only, though 88 and 287 are consistent with the code read ("start-up sweep claims only pending"). Studio rules and handoff not consulted (folder absent). Head SHA: tree is not a git checkout I inspected (not checked).
Files written: /tmp/work/d/out-d11.md only.

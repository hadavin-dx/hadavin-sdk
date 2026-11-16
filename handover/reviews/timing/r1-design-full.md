<!-- full hand-back report of sub-agent aed6d80b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Review round 1, head 2f94c2b2, non-security path. I read only the snapshot. I did not run anything, so every probability below is reasoned from the code and the CHANGELOG's own numbers. I read CHANGELOG.md lines 1-335 of 420 and did not read the last 85 lines.

VERDICT: the design mostly removes the flake and keeps a quadratic regression visible. Two points keep it from a clean pass:
- The new wait guard can itself raise a false `Untimeable` under load.
- The sentinel-character runmap test has no sensitivity control.

Nothing here is a Blocker.

What I checked and found sound:
- **Clock choice.** `process_time` off win32 with the fastest-of-5 alternating batches is a defensible fix. The CHANGELOG's own table shows linear 14.6-16.8, n log n 17-25 and quadratic 212-256 against a limit of 48, so there is a wide margin. The Windows fallback to wall time is stated honestly, with its residual 5.3x blind spot.
- **Thresholds.** `PER_SIZE=3` at gap 16 flags exponents above 1.40, and a pure quadratic clears the limit by 5.3x. Gaps under 8 are refused and the exact-limit boundary is pinned. A quadratic cost that is a small share of the small run passes, but that is documented and tested, not hidden.
- **Bounded loops.** `MAX_ROUNDS=60` and `MAX_CALLS` are enforced in both sizing loops (`timing.py:204-211`, `212-225`), and `_more_calls` has an overflow guard.

FINDINGS

1. **Major: the wait guard can raise a false `Untimeable` on tiny batches under load (`timing.py:172-181`, `84-87`).**
   - The guard fires when wall time is at least 5 ms and more than 50 times the batch's CPU time. It is applied to every batch, including the first sizing batches of n=1, 2, 4 and so on. Those take microseconds of CPU, so 50 times that is a few hundred microseconds.
   - Scenario: a fast function (about 60 µs per call, e.g. `sum(map(ord, text))`) runs its n=1 batch. The scheduler preempts the process for one 5-10 ms slice. That gives wall 8 ms against CPU 60 µs, a ratio of about 130, and the test raises "mostly waits" although nothing waited.
   - The CHANGELOG itself measures wall at 0.68-1.07 s against 0.10 s CPU (7-10x) on loaded machines, so 5-10 ms preemptions are routine there.
   - Exposure is concentrated in fast functions timed at small inputs, since 50 times a few hundred µs is only ~15 ms of wall. The 16 KiB sweep cases take milliseconds per call, so they are far less exposed.
   - Exposed tests: `test_timing_fixture.py:526` (`test_ordinary_computing_is_not_taken_for_waiting`) and any quick `problems` case.
   - The suite's "60 of 60" passes (CHANGELOG line 281) were taken at the previous head and under load of about 4, so they do not rule this out.
   - Fix: judge waiting on the accumulated wall and CPU of the batches that reached `MIN_BATCH_S`, or only on batches with `took >= MIN_BATCH_S`. Alternatively raise `WAIT_MIN_S` to at least the batch length. Note also that a genuinely sleeping function is still caught at its first big batch.

2. **Major: real-clock tests sit in the unmarked default suite, contradicting the docstring (`test_timing_fixture.py:1-2, 497-535`).**
   - The docstring says "The tests that use the rule with the real clock are marked `perf`". I saw no `perf` marker anywhere in the file.
   - `test_work_that_sleeps_is_refused...`, `test_work_done_in_a_child_process...` and `test_ordinary_computing_is_not_taken_for_waiting` use the real clock and real wall time.
   - Failure scenario: the default (non-perf) CI step on a loaded runner runs them. They depend on the wall-versus-CPU ratio from finding 1. The child-process test uses `ProcessPoolExecutor` with fork from a possibly multi-threaded pytest process. That can emit a fork DeprecationWarning on Python 3.12 and later, which fails under `-W error`.
   - Fix: add the `perf` marker, or make them deterministic with a fake wall clock injected into `_batch_timer`.

3. **Major (conditional on a Windows CI leg): the guard tests cannot pass on Windows (`timing.py:200`, `test_timing_fixture.py:497-523`).**
   - `pick_clock("win32")` gives `perf_counter`, and `wall` is also `perf_counter`. Wall equals CPU there, so the guard never fires.
   - `test_work_that_sleeps...` and the child-process test expect `Untimeable("mostly waits")` and will fail on Windows.
   - The CHANGELOG says Windows was not run, but it never says these two tests are Windows-incompatible. Skip them on win32 and state that in the CHANGELOG. If there is no Windows leg, say so.

4. **Minor/Major: the sentinel runmap test has no sensitivity control (`test_runmap_partial_escape.py:121-131`).**
   - The test measures only the new function on `"x" + run + "y"`. The comment claims the old pattern gave a ratio of about 64, but nothing in the test proves this harness flags the old regex.
   - `_OLD` is already in the file as an oracle.
   - Failure scenario: a refactor reintroduces a quadratic `%C3` scan that happens to be linear on the shapes tested, such as `&`, `&#` and `\u` where the old regex was never shown to be quadratic. The test would pass, with no evidence it can fail.
   - Fix: add a control that runs `growth(lambda run: _old("x"+run+"y", 0), "%C3", 1_500, 12_000)` and asserts `flagged`.
   - Only `%C3` and `%C3%A` have documented quadratic history, so the other five units are probably vacuous. Say so, or drop them.
   - The sentinels themselves are right: with `y` after the run, the `$` anchor forces a rescan from each start.

5. **Minor: the hostile-input ceilings use CPU time but are coarse (`test_runmap_partial_escape.py:116, 142, 166`).**
   - `< 60.0` is documented as generous, and the old regex took 65 s only at 40k groups. For the 600k-character inputs a quadratic regression would take hours, so it is caught.
   - A mildly super-linear regression, for example n^1.3, would pass `< 60` and `< 2.0`. Only the perf-marked ratio test would catch it, and that test is skipped if the perf step is not run.
   - `test_a_run_the_old_pattern_took_seconds_on_is_instant` (< 2.0 s for 15k groups) is the only one with a tight bound. It is unmarked, so it runs in the default suite, and 2.0 s of CPU is generous against milliseconds.

6. **Minor: stale or unsupported claims in the CHANGELOG.**
   - Line 28 still says perf tests are blocking "because the check is a ratio, so a noisy runner moves both runs alike". The entry at lines 258-282 shows that was false for wall time, and the changelog now contradicts itself.
   - Line 281's pass counts ("60 of 60", "14 of 14") are explicitly for "the previous head", not 2f94c2b. Re-run them at the head being merged, or say "not re-measured".
   - "100 tests", "28 mutants (7 added last round)" and "61 of 61 good, 139 s" are unverifiable from the snapshot. The mutant runner is `tests/migration_numbers_mutants.py` and I did not run it.
   - A 335-line "Unreleased" block now holds a test-only entry about 300 lines deep. It belongs in a dev-only section so it does not bury user-facing upgrade steps.

7. **Minor: other design caveats the docstring and CHANGELOG already admit.**
   - `process_time` counts other threads in the process. `tools` uses worker threads for timeouts, so a timed function that spawns a thread or a stuck abandoned worker inflates the reading.
   - Memoised functions are timed only on the cached path.
   - The garbage collector is off while timing.
   - These are acceptable, because they are stated and apply to single-threaded pure functions.

Files read (all under /home/user/build/snap/timing-2f94c2b2/):
- tests/fixtures/timing.py
- tests/test_timing_fixture.py
- tests/test_runmap_partial_escape.py
- tests/test_k5_perf.py
- CHANGELOG.md (lines 1-335)

Greps only, no full read:
- tests/migration_numbers_mutants.py
- the other timing-assertion files (`test_k5_layers.py`, `test_k5_fixes2.py`, `test_k5_fixes6.py`, `test_migration_numbers_guards.py`, `test_g4_parity.py`, `warden_port/test_redaction_review2.py`)

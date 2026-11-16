<!-- full hand-back report of sub-agent a122c19a, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Review round 1, head 2f94c2b2 (non-security path), mode REVIEW. I read every file in the snapshot: tests/fixtures/timing.py, tests/test_timing_fixture.py, CHANGELOG.md lines 1-335 (all timing text is in that range), and the changed sibling tests. For the missed-sibling check I read the older checkout in /home/user/hadavin-sdk. I had no way to run code, so the flake risks below are reasoned from the code, not reproduced.

Verified as accurate:
- The arithmetic: 1.53/1.40 exponents, 2.7x/5.3x clearance, the 15% quadratic part and its 2.5x size at the big end, the 43.5x blind spot, the n log n comments (10.4x and 22.4x), and the gap-64 value of 1.26.
- The "100 tests" count in test_timing_fixture.py: I counted 100.
- `process_time` semantics: it is the CPU time of all threads in the process, excludes children and sleeping, and moves in 15.6 ms steps on Windows. `timeit -p`, the GC-off behaviour and the `Timer.autorange` 0.2 s figure are also correct.
- `Growth`: overriding `__str__` and adding properties on a `NamedTuple` is legal. `ratio` cannot divide by zero when built through `growth()`, because `seconds_per_call_each` only returns values of at least MIN_BATCH_S/n.
- `add_note` is fine, since pyproject says requires-python >=3.12.
- `pick_clock`: the logic is correct.
- The seven CLOCK ceiling tests in the snapshot do pure CPU work (no threads, sleeps or subprocesses), so switching them to CPU time is sound.

## Major

**M1. The wait guard can raise `Untimeable` on a single preempted small batch.** (timing.py:172-181, constants at 84-87; sizing loop at 203-211)

The guard fires when `waited >= 5 ms and waited > 50 * took`. It is evaluated on every batch, including the sizing batches that start at 1 call. For a fast function (a regex scan of a 16 KiB text, `sum(map(ord, ...))`) one call costs tens of microseconds. So the first few sizing batches have `took` of 0.01 to 0.2 ms, and the threshold 50*took is under 10 ms.

Failure scenario: on a loaded or VM-stolen runner (the changelog itself measures at load 8 to 13 on 4 processors), a scheduler preemption or steal of 5 ms or more lands inside one of these tiny batches. The batch raises `Untimeable("... mostly waits ...")`.
- A real, linear function is then reported as unmeasurable.
- In `problems()` (timing.py:261-262) it becomes a "could not be timed" line, so the 216-case sweep in test_k5_perf.py:83 and the migration-lexer sweep fail.
- `test_ordinary_computing_is_not_taken_for_waiting` (test_timing_fixture.py:526-528, 100 µs of work) is exposed to the same flake.

This is the opposite of the harness's own principle: a pause should be absorbed by "fastest of 5", but this guard turns one pause into an error before the min logic runs.

The stress evidence in the changelog (60/60 and 14/14) covers only the four stand-in tests, not the sweep or any sizing-phase run, and the table at CHANGELOG:269-279 does not include the guard.

Fix: apply the guard only to batches that reached MIN_BATCH_S, or to the fastest batch, or to the aggregate over the repeats. A pause of 1 s or more would still not trip a 20 ms batch (threshold about 1 s), but sleep/child detection would be unchanged. Alternatively raise WAIT_MIN_S well above scheduler slices (for example 0.25 s). The sleep test (20 ms sleeps) would need adjusting, and the child test (0.4 s of burn) would be fine.

## Minor

**m1. The guard is keyed on "clock is None", not on "the real processor-time clock".** (timing.py:200)
- On Windows (CLOCK is `perf_counter`) the guard is armed but can never fire, so sleeping or child work is wall-timed and not refused.
- With `monkeypatch.setattr(timing, "CLOCK", model.clock)` and no `clock=` argument (test_timing_fixture.py:381-389), the guard compares real wall time against made-up seconds.
- The docstring at timing.py:38 ("with the real processor-time clock") is correct. The changelog at CHANGELOG:262 ("with the real clock ... refused at once") reads as unconditional and overstates for Windows. Say "off Windows".

**m2. Changelog heading overstates coverage.** (CHANGELOG:267: "searched 2026-11-11: every `time.perf_counter` next to an assertion")
- The search was literally for `perf_counter`.
- Wall-time CPU-bound ceilings that use `time.monotonic` are still there (paths from the older checkout; they are not in the snapshot, so they were presumably untouched at head).
  - /home/user/hadavin-sdk/tests/test_migrate_regex_linear.py:25-27. This is `< 1.0` s on 60k-character inputs and is `perf`-marked. It has the same wall-clock flake class as the original defect and is the most likely miss.
  - /home/user/hadavin-sdk/tests/test_k5_round5.py:252-255 (`< 20` s, pure `prepare_output`).
  - /home/user/hadavin-sdk/tests/test_s4_llm_guard.py:218-220 (`< 5` s, `clean()`).
  - /home/user/hadavin-sdk/tests/demo_askdata/test_validate_fuzz.py:90-104 (`< 120` s).
- Intentional wall-clock tests that should stay: test_k5_review.py:321-324 (hang abandoned at the deadline), test_pgsource_layers.py:134-146 (pg_sleep watchdog), test_k5_classes.py:488-498 (subprocess).
- test_k5_round10.py:128-135 and warden_port/test_redaction_bank.py:357-362 call `time.process_time` directly. That is fine on Linux but bypasses the new Windows rule (`timing.CLOCK`); the changelog does not mention them.
- Either extend the sweep to `monotonic` or reword the heading.

**m3. Redundant comment.** (test_runmap_partial_escape.py:116-118) The "busy runner" comment on the 60 s bound is stale now that the clock is CPU time. This is cosmetic.

**m4. Sibling ceilings can no longer catch a regression that sleeps or blocks.**
- The seven ceilings in CHANGELOG:267 (`timing.CLOCK` is `process_time` off Windows) now ignore time spent blocked, so a sleep, retry-backoff or I/O wait regression would not trip them.
- None of the touched tests do such work today.
- Worth one sentence in the changelog or in a comment, since the changelog sells "another program cannot push them over" only.

**m5. Direct `Growth` construction.** (timing.py:148, 158-162)
- `Growth(0, ...).ratio` or `str()` raises `ZeroDivisionError`, and NaN times print without refusal.
- This is only reachable by hand-built instances, as in test_timing_fixture.py:434, which uses valid values.
- Fine as is. Optionally make `ratio` go through `_check_time`.

**m6. Unmeasured claim.** CHANGELOG:259 and CHANGELOG:281 ("failed 19 of 30", "60 of 60 runs") rest on runs I could not reproduce. The changelog says the measurement script is not kept in the repository, so a reader cannot check these numbers.

## No finding

Untimeable handling is consistent. `Untimeable` subclasses `ValueError`, and `problems()` catches it before the generic `except Exception`, so the case's own `ValueError` is kept unchanged and gets a note (test_timing_fixture.py:459-465 pins this). `add_note` on a re-raised exception keeps its type. The `Untimeable` paths for NaN, inf, negative and zero clocks all terminate (`_more_calls` multiplies by 10, MAX_CALLS and MAX_ROUNDS bound the loops).

<!-- full hand-back report of sub-agent a6bff613, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 1, core/fix-timing-harness-flake @ fa3f8c1b. Mode: REVIEW. Read-only; nothing was executed.

## Verdict
Not ready. The design direction is right (ratio rule kept, floor removed, batching with `timeit`, loud refusal), and I found no call site that became weaker. But there is no evidence for any "passes" claim, and the fix's central statistical claim is not supported by anything in the snapshot.

Evidence file: `/home/user/hadavin-sdk/handover/evidence/timing-harness/fa3f8c1/RESULTS.md` is NOT present (the directory `timing-harness` does not exist). Every "passes", "16 fails in 30 runs", "about 50 s", "7 of 7 good" below is unproven.

## Findings (failures first)

### B1. Blocker: no evidence at all; the purpose of the branch (flake gone) is unproven
- Scope: whole change; `CHANGELOG.md:258` ("its own check no longer fails by chance", "16 fails in 30 runs", "about 50 s where it took 15 s", "seven planted faults ... each caught").
- Nothing shows the new tests pass, that they fail on the old code (required by `class-level-fixes.md`), that the 7 mutants are killed, or that the flake rate changed.
- Fix: EVIDENCE RUNNER saves raw output for: (a) `pytest -m perf` repeated at least 200 times idle and at least 200 times under CPU contention (for example a competing busy loop per core), with fail counts per test; (b) the same count on main for the flaky test; (c) the new tests run against main's `timing.py`; (d) `tests/migration_numbers_mutants.py timing`; (e) wall time of the perf step before and after.

### M1. Major: the decision is not shown to be statistically sound; min-of-3 consecutive 20 ms batches only protects against short, independent interruptions
- Scope: `tests/fixtures/timing.py:32` (`MIN_BATCH_S, REPEATS = 0.02, 3`), `:57`, `:78-80`.
- All batches at the small size run first, then all at the big size (`:78-80`), so a disturbance that starts between them is not cancelled. For a fast call the three counted small batches span about 70 ms in total.
- Missed quadratic scenario: `test_the_timing_harness_flags_a_quadratic_stand_in` has true ratio about 256 against a limit of 48. A stall covering all three small batches (about 70 ms: a container CPU-quota throttle period is 100 ms, a noisy shared runner) that inflates the small time 5.3x makes it pass as "linear". In the k5 harness test (`tests/test_k5_perf.py:56`, 64x against 24x) 2.7x is enough; in the sweep (16x against 12x) 1.33x is enough.
- False alarm scenario: `_n_log_n` (true ratio about 20, limit 48) fails if all three big batches (about 80 ms) run 2.4x slower than the best small batch; linear needs 3x. A neighbour arriving after the small measurement does that.
- `timeit` itself uses 0.2 s in `autorange` and 5 repeats by default; 20 ms and 3 are ten and nearly two times lower, with no measurement justifying them.
- The made-up clock test `test_other_programs_taking_the_machine_in_two_of_three_batches_change_nothing` (`tests/test_timing_fixture.py:139-148`) only covers the favourable case (one clean batch per size always exists).
- Fix: interleave (small batch, big batch, repeated) and take each size's minimum; raise repeats to 5; choose the batch length from the B1 measurements; state in the docstring which disturbance length the rule does not survive.

### M2. Major: the redaction sweep runs at a 4x size gap, where the rule is barely able to see a quadratic, and the test that proves the harness uses a different gap
- Scope: `tests/test_k5_perf.py:23` (`SMALL, BIG = 64 KiB, 256 KiB`), `:61-68`; proof test `:52-57` uses 4 KiB and 32 KiB (8x); e2e `:97` uses 4x. Sizes are unchanged from main, so this is not a regression, but it is the answer to "inputs large enough to show quadratic behaviour".
- With `PER_SIZE = 3` and g = 4 the rule flags only growth above 12x, that is an exponent above 1.79 (g = 8: 1.53; g = 16: 1.40). For cost `b*n + a*n*n` it misses whenever the quadratic part is at most half the linear part at 64 KiB; such a pattern is 3x slower than linear at 256 KiB and passes. A pure quadratic clears the limit by only 1.33x (see M1).
- Nothing proves a quadratic is flagged at the sweep's own sizes.
- Fix: run the quadratic/bounded pair at `SMALL, BIG` exactly as the sweep does (or sweep at 8x or 16x, for example 16 KiB to 256 KiB as the lexer test does), and state the smallest exponent the configuration can flag.

### M3. Major: the constants that carry the fix are not pinned by any deterministic test, and the mutant list has no mutant for them
- Scope: `tests/migration_numbers_mutants.py:321-383`; `tests/test_timing_fixture.py:68-71, 109-119, 128-136`.
- `MIN_BATCH_S 0.02 -> 0.002` survives every made-up clock test by my trace: the tests compare against `timing.MIN_BATCH_S` itself (`:118-119`), and the coarse-clock tolerance `rel=tick / timing.MIN_BATCH_S` (`:134`) gets looser as the constant shrinks.
- `PER_SIZE 3.0 -> anything from about 1.1 to 3.99` survives: the model clock tests only use g = 4 with ratios 4 and 16, and `test_the_limit_is_a_ratio_of_the_two_sizes` restates the formula with `timing.PER_SIZE`. Only the extremes 1000 and 0.001 are planted. There is no deterministic n log n model (`Model.power` is an integer), so "n log n passes" rests on a real-clock test only.
- Missing mutants: batch floor value; ratio constant near the boundary (1.2 and 3.99 or 4.0); `min -> median` (the pause test would kill it by inspection, but it is not planted); `REPEATS -> 1`; the sizes check `if not 0 < small < big`; replacing `timeit` by a hand loop with the collector on.
- Fix: add those mutants; add a deterministic n log n model and a model at g = 16; pin the constants with literal expectations (for example a 1 microsecond call must be batched to at least 20,000 calls).

### m4. Minor: `t_big` is never validated, so a not-a-number big time is passed as "linear"
- Scope: `tests/fixtures/timing.py:44-45`. `grows_faster_than_size(0.01, float("nan"), 1000, 4000)` returns False; a zero or negative `t_big` also returns False. Not reachable through `seconds_per_call` (it returns at least 0.02/calls, or inf), but the function is public and the docstring promises refusal.
- Fix: apply the same finite-and-positive check to `t_big`; add the test.

### m5. Minor: no minimum growth factor is enforced
- Scope: `tests/fixtures/timing.py:39`. For `big/small <= 3` a pure quadratic can never be flagged (g*g <= 3*g), yet `is_superlinear(fn, "a", 1000, 2000)` answers "linear". The docstring says "with g of 4 or more" but the code accepts 1.001.
- Fix: refuse `big < 4 * small` (or the factor chosen in M2) with `ValueError`.

### m6. Minor: sizes and unit are validated only after both measurements
- Scope: `tests/fixtures/timing.py:78-81`. `small=0` times the empty string (possibly up to 3.3 million calls) before the `ValueError`; an empty `unit` gives `ZeroDivisionError`, not the documented refusal.
- Fix: validate sizes and `len(unit) > 0` first.

### m7. Minor: the "too fast to time" refusal cannot trigger with the real clock, and loop overhead is not removed
- Scope: `tests/fixtures/timing.py:32, 60-63`. The threshold is 20 ns per call (20 ms / 1,000,000), below the cost of an empty call through `functools.partial` in the `timeit` loop. A near-instant call is therefore timed as loop overhead and reported "linear". This is correct for a constant cost, but the refusal is only reachable with an injected clock, and the CHANGELOG presents it as a live protection.
- Fix: say so in the docstring, or refuse when the per-call time is within a small multiple of a measured empty-call baseline.

### m8. Minor: a refusal inside the sweep does not say which pattern
- Scope: `tests/test_k5_perf.py:62-67`, `tests/test_migration_numbers.py:811-816`. A `ValueError` aborts the list comprehension (good: refused, not passed) but the message names neither pattern nor unit, and patterns already found slow are lost.
- Fix: catch, re-raise with `(name, unit)`.

### m9. Minor: collector off changes what is measured
- Scope: `tests/fixtures/timing.py:52-54`. Main timed with the garbage collector on; now it is off for the whole batch. Any collector-driven growth in the lexer or redaction (many container objects) is no longer seen. Not stated in the CHANGELOG.
- Fix: state it; or add one collector-on comparison for the two real callers in the evidence run.

### m10. Minor: weak or duplicated assertions in `tests/test_timing_fixture.py`
- `:128-136`: the last two assertions ignore the `tick` parameter (they hard-code 0.001), so they run twice identically; `assert got > 0` is implied by the next line; tolerance for the 15.6 ms tick is 78%.
- `:65` and `:93`: `not hasattr(timing, "MIN_SMALL_S")` / `"FLOOR_S"` check a name, not behaviour (mutant 3 uses the literal 0.004 and is caught only by lines 63-64).
- `:28-34`: `Model.clock` assumes exactly two clock reads per batch, which ties the tests to `timeit`'s internals.
- `:151-160`: about 6.3 million Python calls in the ordinary (non-perf) suite, roughly 1 to 3 s by my estimate; unmeasured.
- `:165`: fails if the suite is ever run with the collector disabled.
- Mutant 5 expects the text `assert 0.0501` (`migration_numbers_mutants.py:363`): it depends on how the float prints (0.05 + 0.0001 accumulated on the model clock); unproven without a run.

### m11. Minor: re-run policy left in a file this change edits, against the claim
- Scope: `tests/test_k5_perf.py:73-74` ("a red run is repeated once by hand ... one red is noise"). Unchanged text, but it is a retry-until-green policy and contradicts "no longer fails by chance". Also `:51` says "16x vs a 12x limit" for a test that uses 8x text (64x against 24x).
- Fix: delete the policy once B1 shows the e2e tests are stable, or keep it and withdraw the claim for e2e.

### m12. Minor: CHANGELOG inaccuracies (`CHANGELOG.md:258`)
- "It used to take one clock reading of the small call": main's callers took the median of three single-call readings (`_cpu`, `_e2e`, `_median_time` in the diff).
- "both now really compare 216 and 18 fast cases": 18 = 2 functions x 9 units is right; 216 cannot be checked here; and "fast" implies all were under the 4 ms floor, while `tests/test_k5_perf.py:10` records 19 ms at 64 KiB for one pattern (already above the floor on main).
- "seven planted faults" listed under "New checks": 5 are new, 2 are retargeted old ones, 1 old mutant was removed.
- Command given as `python ...`; the script's own header says `uv run python ...` (`migration_numbers_mutants.py:11`).
- No time bound is stated for the perf step; only "about 50 s" for the sweep. The mutant script header still says "under a minute" (`:8`) with 5 more mutants.
- Not mentioned: the fixture's signature changed (`measure` returning seconds became the work itself), and the collector is now off.

## What I checked and found sound
- (1) `timeit.Timer(partial(fn, text), timer=clock).timeit`: collector off during the batch and restored; batch growth terminates (NaN, negative or stuck clock end in the `MAX_CALLS` refusal; inf small time is refused by `time_limit`; inf big time is flagged). The docstring's quotes of `timeit` are accurate. Cache effects between 16 KiB and 256 KiB push towards false alarm, not towards a miss, and are far below 3x.
- (2) Call sites, before and after: `test_lexer_is_linear` (same 9 units, 16 KiB/256 KiB, same assertion); sweep (same `PATTERNS x _units`, same sizes, same assertion, every pattern still iterated); e2e (same 5 units, same sizes); k5 harness test unchanged. None weaker. `_e2e` now has its `import` inside the timed call (negligible after the first call). `time`/`statistics` imports removed correctly.
- (3) Stand-ins: `_linear` is n/64 fixed-width counts (linear); `_n_log_n` is 15 and 19 passes (16 x 19/15 = 20.3x, comment correct); `_quadratic` reads n*n/128 characters (about 250x at 16x, still above 150x at 4 KiB even with per-step overhead). Each test can fail. On main's harness the new tests fail by `TypeError` (None compared in `max`), not by assertion; the floor regression itself is carried by mutant 3.
- (5) Each of the 7 `old` strings occurs exactly once in the new `timing.py` (lines 31, 31, 41, 37, 57, 58, 60); the replacement for mutant 7 is validly indented; parameter ids `1e-11`, `1e-09`, `0.0`, `0.05` match pytest's float ids; each killer fails under its mutant by my trace.

## Not checked
- Nothing was run: no test, mutant, timing or lint result is confirmed.
- `tools/mutation_runner.py` (what "fails first" and `only_test` mean), `test_every_mutant_still_applies_to_the_source`, CI workflow (perf step, timeouts, whether `perf` is deselected in the unit step), `pyproject` markers: outside the snapshot.
- Other users of `timing.is_superlinear`, `time_limit` or `MIN_SMALL_S` elsewhere in the repository, and sibling hand-rolled timing code (only the 30 s ceiling test at `tests/test_k5_perf.py:101-116` was seen).
- `hadavin_sdk.guard.redact.PATTERNS` (the count 216, keyword units), and whether `redact_untrusted`, `lex` or `refused_statements` memoise on the text or return a lazy result; repeated calls on the same text would then time the cached path (main had the same exposure).
- The rest of `tests/test_migration_numbers.py` beyond lines 790-868 and the import block.

Files: `/home/user/build/snap/flaky-fa3f8c1/DIFF.patch`, `/home/user/build/snap/flaky-fa3f8c1/tests/fixtures/timing.py`, `/home/user/build/snap/flaky-fa3f8c1/MAIN/tests/fixtures/timing.py`, `/home/user/build/snap/flaky-fa3f8c1/tests/test_timing_fixture.py`, `/home/user/build/snap/flaky-fa3f8c1/tests/test_k5_perf.py`, `/home/user/build/snap/flaky-fa3f8c1/tests/test_migration_numbers.py`, `/home/user/build/snap/flaky-fa3f8c1/tests/migration_numbers_mutants.py`, `/home/user/build/snap/flaky-fa3f8c1/CHANGELOG.md`. Standards read: `/home/user/hadavin-sdk/CLAUDE.md`, `/home/user/hadavin-sdk/.claude/rules/class-level-fixes.md`, `/home/user/hadavin-sdk/.claude/rules/verify-tests-and-evals.md`, `/home/user/hadavin-sdk/.claude/rules/fix-dont-defer-be-honest.md`, `/root/.claude/plugins/cache/egm/egm/0.1.1/agents/codebase_details.md`.

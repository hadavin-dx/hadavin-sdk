Status: resolved

# Goldfish Annotated Review Report (round 1, timing harness fix, ORDER 267, normal path)

**Target:** `/home/user/build/snap/timing-a3c94be5/DIFF.patch` (full), head a3c94be5
**Inputs:** design r1 (3 Major, minors, nits), codebase r1 (1 Major, 3 Minor, nit). The two Majors about Windows CPU ticks are one finding (codebase Major = design Major 2). Independent runner a50fa730 not yet reported; not waited for.
**Handoff:** accepted fixes 9 (3 Major + 5 Minor groups + 1 evidence demand); contested 0; escalated 0; declined 2 (nits: `_is_superlinear` pass-through, `_cpu` list comprehension: both fixed by the same edit, listed as hygiene in the brief, not separate findings); remaining unaddressed 0.

## Round verdict and stop rule
Not clean: 3 unsettled Majors. Normal path: one fix batch, then round 2 must have 0 Blocker and 0 Major; after round 2 only Blockers and Majors get another pass; minors are fixed in the same push without a new review and listed in the ledger. The independent evidence must run on the FINAL head (the runner now running at a3c94be5 is stale for the fix; its 30x old-vs-new contrast stays useful as the baseline).

## Decision (the choke point): ONE estimator in tests/fixtures/timing.py, two changes
1. **Measure a block, not a single call** (fixes design Major 1 floor problem and Major 2 tick problem together). New `block_seconds(fn, text, min_block=0.05)`: call `fn(text)` k times in one timed block, doubling k from 1 until the block takes at least `min_block` (50 ms), then return `elapsed / k`. Tick quantisation (15.6 ms on Windows) is at most about 30 percent of one block, and the result no longer depends on a small run being above a floor by luck. The clock is chosen once by `time.get_clock_info("process_time").resolution <= 1e-4` (CPU time, immune to a busy neighbour) else `time.perf_counter` (fine-grained, with best-of-N for noise); one sentence in the docstring says which and why, replacing the stale "Windows" text in test_k5_perf.py. Keep best-of-N over interleaved sizes and `REPEATS`; lower REPEATS to 5 (block timing already averages inside the block) and state the measured seconds.
2. **Stand-in with a real gap** (design Major 1): `quadratic_stand_in` is sized by the block rule so the small run needs no floor luck; assert in the test that the MEASURED per-call small time is at least 4 x `MIN_SMALL_S` (floor margin) and that the big/small ratio is at least 2x the limit ratio (`PER_SIZE * big/small`): the gap becomes a pinned assertion, not a docstring claim. Use size factor 16 (as the old test, gap about 5x) with a cheaper step so the 16x run stays under about 2 s; CPU seconds of the test stated from the runner's measure, not estimated.

## FIX BRIEF (one small builder; resume from branch wip/cloud-timing-flake head a3c94be5)
Files: `tests/fixtures/timing.py`, `tests/test_k5_perf.py`, `tests/test_migration_numbers.py`, `tests/test_timing_fixture.py`, CHANGELOG entry only if the repo logs test-harness changes (check; else none).
Changes:
- `block_seconds` and the clock choice as above; `cpu_seconds` removed or kept as the single-call primitive used only by `block_seconds`; all callers (test_migration_numbers.py, test_k5_perf.py) call the one estimator. `is_superlinear` signature unchanged except `measure` now returns seconds per call.
- Fresh text per repeat (same length, a different seed character) so a cache or memoisation in `mn.lex`, `refused_statements` or `redact_untrusted` cannot make runs 2 to N free (design 6); plus one test that a cached function (an `lru_cache` wrapper around the quadratic stand-in) is still flagged, because the text differs each run.
- `busy_cpus`: count `len(os.sched_getaffinity(0))` where present else `os.cpu_count()`, cap at 4; readiness handshake with a `multiprocessing.Event` per worker (set after the child's first loop pass) before measuring, with a 10 s timeout that FAILS the test (never passes vacuously); `terminate()` only workers whose `start()` succeeded (`is_alive()`); `kill()` fallback after `join(timeout=10)`; all in `finally`.
- Docs: test_k5_perf.py lines 3-9, 53, 73-76 rewritten to the new rule (no "wall seconds", no "median of three", no re-run policy that contradicts the code); remove the pass-through `_is_superlinear` wrapper; replace the list comprehension in `_cpu` with a counting loop.
- CI time: state the measured seconds of the whole perf group (`pytest -m perf` alone) in the PR body and in the docstring (replace "about 0.4 s"); keep the group under about 30 s on the runner; if the sweep and five end-to-end shapes exceed that with REPEATS 5, cut REPEATS for those callers only and say so.
- Confirm in the evidence that `tests/migration_numbers_mutants.py` still matches its strings and that `mutation_manifest.json` does not pin the changed files (reviewer could not read them); if it does, regenerate the hashes.
Tests (each must FAIL on a3c94be5 where marked, and on old main for the first):
1. a real quadratic is flagged and a linear cost passes with `busy_cpus` running (marked perf); 30 of 30 each under the builder's busy loop (evidence).
2. no-clock estimator tests with a fake clock and fake calls: a small run below the floor (patched so one call takes 1.5 ms) is still flagged for the quadratic stand-in (fast-CPU simulation: design Major 1); a clock that ticks at 15.6 ms (fake clock with that resolution) does NOT flag a linear cost and DOES flag a quadratic one (Windows simulation: Major 2). Both fail on a3c94be5.
3. the margin assertions (small per-call time >= 4 x floor; measured ratio >= 2 x limit ratio).
4. a test that a started-event timeout fails the load test instead of passing (fake process that never signals).
Mutants (run by hand on a throwaway copy, record outputs): `best_of` -> median must be killed by the inflated-small-sample test; PER_SIZE loosened (quadratic passes) must be killed by the flag test; drop the block loop (single call) must be killed by the tick-simulation test; drop `fresh text per repeat` must be killed by the lru_cache test; `busy_cpus` handshake removed must be killed by the never-signals test.
Fail-before: new tests 2 and 4 fail on a3c94be5; test 1 fails on old main at least once in 30 busy runs is not required (the old 2 of 30 stays the baseline).
Gates once at the final head: affected tests while iterating; ONE full suite (`-m "not live and not perf"`), the perf group alone in a slot, ruff check and format --check, bandit -ll, gitleaks, check-no-handover-files.sh. Push once to wip/cloud-timing-flake, no force.

## Evidence the final head needs (independent runner, fresh)
(a) 30 of 30 busy-load runs of the flag test and of the pass test; (b) the five hand mutants killed; (c) the fast-CPU and 15.6 ms tick simulations pass; (d) the full suite and the perf group alone with measured seconds; (e) the old test failing 2 of 30 stays as the baseline (old-busy-30.log).

## Findings (all PROPOSE FIX)
| Finding | Decision | Where |
|---|---|---|
| design 1 stand-in gap not wider, small run near floor | PROPOSE FIX | block timing, size factor 16, margin assertions |
| design 2 = codebase Major, Windows tick | PROPOSE FIX | block timing with clock choice, tick simulation test |
| design 3 claims not demonstrated | PROPOSE FIX | evidence list above, five mutants |
| design 4 CI time claim, repeats | PROPOSE FIX | state measured seconds, REPEATS 5 |
| design 5 / codebase busy_cpus | PROPOSE FIX | handshake, sched_getaffinity, kill, started-only terminate |
| design 6 caching | PROPOSE FIX | fresh text per repeat + lru_cache test |
| design 7 / codebase stale docs | PROPOSE FIX | rewrite |
| design 8 / codebase nits | PROPOSE FIX (hygiene) | remove wrapper, counting loop |
| codebase mutants manifest unknown | PROPOSE FIX | confirm strings and manifest in evidence |
No CONTEST, no ESCALATE: each finding cites lines in the snapshot.

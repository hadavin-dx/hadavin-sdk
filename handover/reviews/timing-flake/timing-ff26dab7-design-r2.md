# timing-ff26dab7-design-r2: timing harness fix (ORDER 267), head ff26dab7, round 2, persona design

Source: hand-back of agent a588a2a23b4e1df9f, saved by the lead (condensed). Static read only, nothing run; every number is the builder's claim. 0 Blocker, 1 Major, 6 Minor, 3 Nits. Snapshot /home/user/build/snap/timing-ff26dab7.

## Major
- **M1** Margin assertion `t_small >= 4 * MIN_SMALL_S` (test_timing_fixture.py:321 flag test, :330 pass test; floor timing.py:24) needs a small run of 4 ms; the stand-in small run is 6.4 ms (1.6x headroom), so a CPU about 1.6x faster fails the margin although the harness flags correctly: false red. Linear pass test small run (256 KiB sum(ord)) est 9-12 ms (estimate), margin 2-3x. Fix: assert `>= MIN_SMALL_S` (or 2x), or calibrate sizes.

## Minor
- m1 REPEATS cut to 2-3 (test_k5_perf.py:42,:101; test_migration_numbers.py:816) weakens noise absorption on the wall-clock path (Windows); state trade-off in docstring or keep 3 for the sweep.
- m2 Perf group 70.9 s vs 30 s goal; check CI perf step timeout; put figure in docstring and PR body.
- m3 Fast-CPU simulation (test_timing_fixture.py:183-193) passes on old 4 ms floor only by float equality (96 ms vs limit 96 ms, check is `>`); use 2.5 ms small run or add a floor hand mutant.
- m4 Weak fail-before (block_seconds missing on old code); never-signals test only proven by the handshake mutant; record five hand-mutant outputs; say new mutants are hand runs.
- m5 CPU clock chosen from self-reported resolution (timing.py:42): a kernel reporting 1 ns but accounting per 4-10 ms tick could give 40-100% error on 10 ms blocks.
- m6 `_variant` changes only the last 4 chars (timing.py:55-61): prefix or chunk caches still hit; note limit.

## Nits
Test name `..flagged_at_any_speed` overstates (floor hides below ~1e-9). test_k5_perf.py:5 docstring over 120 chars. `_FRESH` comment 26^4 fine.

## Deviations answered
MIN_SMALL_S 4 to 1 ms acceptable (side effect M1); block 10 ms fine clock / 50 ms coarse sound; stand-in ratio fine; cache check passed.

## Not checked
No timings reproduced; DIFF/DELTA not read whole; manifest hash pinning; CI perf timeout; lint gates; Windows/macOS reasoned only; xdist.

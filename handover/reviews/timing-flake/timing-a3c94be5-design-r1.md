# timing-a3c94be5-design-r1: timing harness fix (ORDER 267), head a3c94be5, round 1, persona design

Source: hand-back of the design reviewer (agent ae8af7e0), saved by the lead (condensed). Normal path (max 2 rounds). Text only; nothing run. Snapshot `/home/user/build/snap/timing-a3c94be5`. 0 Blocker, 3 Major, 3 Minor-level groups, nits. Direction right (best of 7, CPU time, interleaved sizes, no-clock estimator test; no caller keeps a wall-clock median).

## Major
1. The "wider gap" is not wider (tests/fixtures/timing.py:55-59, test_migration_numbers.py:822-824). Old test 16x size: quadratic about 256x vs limit 48x (gap ~5.3x); new 8x: 64x vs 24x (gap ~2.7x). Real gain only that the small run is now above the 4 ms floor; "about 6 ms" is one machine. Below the floor the limit stays 24 x 4 ms = 96 ms while big = 64 x small; at a 1.5 ms small run big = 96 ms and is not flagged (the CI failure moved to fast CPUs). Fix: size the stand-in so the small run is >= 20 ms, or adapt the step, or assert the measured small time exceeds MIN_SMALL_S by a margin; consider a larger size factor with a cheaper step.
2. CPU time on Windows (tests/test_k5_perf.py:3-6, timing.py:27-32): the file's own docstring records process_time ticking at 15.6 ms on Windows reading 0 for a small run; min of 7 picks the luckiest tick; a 10-14 ms run reads 0, floors to 4 ms, limit 48 ms, a linear 56 ms big run is a false positive. Fix: process_time_ns/thread_time_ns where fine-grained, or loop inside one timed block to >= 50 ms; else state the perf suite is Linux-only as a decision.
3. Claims not demonstrated (NOTES.md): 30x busy-load of the new tests, planted-quadratic 30x, both hand mutants, full suite, perf group alone all not run. Also no check that test_the_fastest_run_ignores_one_inflated_small_sample fails when best_of becomes a median.

## Minor
4. CI-time claim wrong: docstring "about 0.4 s", measured 2.65 s alone, 4.5 s under load; repeats 3 to 7 for every perf caller (sweep and five end-to-end shapes about 2.3x; end-to-end about 7 s at 256 KiB); CI cost of `-m perf` unmeasured.
5. busy_cpus fixture (test_timing_fixture.py:81-101): spawn returns before the child imports (no readiness handshake: the measured loop may run unloaded, tests may pass vacuously; 4.5 vs 2.65 s suggests partial load); `terminate()` on a never-started process masks the real error; `join(timeout=10)` without `kill()`; `os.cpu_count()` ignores affinity and cgroups (64 interpreters on a big runner): use `os.sched_getaffinity(0)` and a started-event handshake.
6. Possible false negative through caching in the code under test (same text run 7 times, minimum counts; memoisation in mn.lex, refused_statements, redact_untrusted would hide a quadratic first call): check no cache, or fresh text per repeat.
7. Stale docs in test_k5_perf.py:3-9, 74-76, 53 (wall seconds, median of three, 64/256 KiB, 16x vs 12x, wall-clock re-run policy).

## Nit
8. `_is_superlinear` pass-through wrapper; `_cpu` list comprehension allocation; load-test sizes unexplained; `_spin` no sleep (intended).

## Not checked
Nothing executed; flake rate under load unknown; code under test not inspected for caching; Python version, `str.count` speed, Windows ticks, CI wall time of the perf group, CI config, xdist; test_migration_numbers.py seen only through the diff.

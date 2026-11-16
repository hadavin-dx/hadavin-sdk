# timing-a3c94be5-codebase-r1: timing harness fix, head a3c94be5, round 1, persona codebase details

Source: hand-back of the codebase reviewer (agent a782aaa6), saved by the lead (condensed). Normal path. Text only; nothing run. Snapshot `/home/user/build/snap/timing-a3c94be5`. 0 Blocker, 1 Major, 3 Minor, nits.

## Major
- process_time brings back the Windows-resolution problem that tests/test_k5_perf.py:4-5 documents (tick 15.6 ms, small run read 0; numbers measured on a Windows laptop). tests/fixtures/timing.py:27-32 `cpu_seconds`, used at test_k5_perf.py:31-32 and :88-91. Best-of-7 reads 0, floors to 4 ms, limit 3 x 4 x 4 = 48 ms vs a big run of a multiple of 15.6 ms (62.4 ms for BANKCODE's 75 ms at 256 KiB): a linear pattern flagged; the 4 KiB quadratic stand-in at test_k5_perf.py:58 is sub-resolution. Linux CI unaffected. Fix: thread_time or perf_counter with min-of-N, or a clock per platform, or state Linux-only; and say why the Windows concern no longer applies.

## Minor
- Stale prose in test_k5_perf.py:3-7 ("wall seconds, median of three") and :73-76 (RE-RUN POLICY "wall clock ... noisy") contradict the code (CPU time, best of 7).
- busy_cpus (test_timing_fixture.py:205-220): `terminate()` on a never-started process masks the original error and leaves earlier workers; `join(timeout=10)` without `kill()`; `os.cpu_count()` ignores cgroups/affinity (use `len(os.sched_getaffinity(0))`); spawn start-up overlaps the first measurements (harmless for min-of-7); 3 runnable on 2 cores (never run 30x under load).
- k5 sweep runtime unverified: repeats 3 to 7 gives about 2.3x timed work; NOTES "perf tests (4) passed alone: 10.6 s" cannot be reconciled with the sweep and the 5 e2e cases; CI perf step (ci.yml:94, `pytest -q -m perf`) is blocking.

## Nit
`_is_superlinear` wrapper (test_k5_perf.py:35-36) is a pure pass-through; `time` import kept for the wall-clock ceiling test (intentional).

## Clean
`_median_time` has no other user; ruff F401 clean; `is_superlinear` signature backward compatible; PER_SIZE/MIN_SMALL_S line unchanged (a string-rewriting mutant still matches; line numbers shift by 2); test names unchanged; perf marker registered (pyproject.toml:87-90); stand-in arithmetic (8x, limit 24x, ~64x) machine-independent; process_time counts all threads, excludes children (a worker subprocess would read near zero); runtime about 2.7 s.

## Not checked
tests/migration_numbers_mutants.py and mutation_manifest.json (not in the snapshot; confirm the manifest does not hash-pin timing.py or these test files); nothing run; 30x load runs, planted quadratic, full suite, perf alone, hand mutants not done; no fail-before evidence; 2-core CI behaviour.

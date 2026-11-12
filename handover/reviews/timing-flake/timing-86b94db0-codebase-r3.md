# timing-86b94db0-codebase-r3: timing-flake batch 3, head 86b94db0, round 3 (Majors-only check)

Source: hand-back of the codebase reviewer (agent ace95a975), saved by the lead (condensed). Normal path, round 3: only Blockers and Majors count. Static read of snapshot `/home/user/build/snap/timing-86b94db0`; nothing run. Result: 0 Blocker, 0 Major introduced by batch 3.

## Round 2 Majors
- Margin assertion: FIXED (tests/test_timing_fixture.py:375, :384 now `>= timing.MIN_SMALL_S`; ratio asserts keep the pin).
- E731: batch 3 lambdas removed. One older line remains, `tests/test_migration_numbers.py:849` (`strip = lambda ...`), not in the diff. Lead check: `ruff check --select E731` on the snapshot file reports it (1 error); the same line is on origin/main (line 857). One `def` fixes it; the independent runner's ruff result decides whether CI counts it.
- Perf group figure: acceptable; the 58 s figure is not in any file of the snapshot (timing.py says "the figure is in the notes of the change"). Put it in the notes and the PR body.

## New false-red or false-green paths
None found: fast-CPU test (quadratic 40 ms vs 30 ms limit, linear passes; floor mutant o267 dies), PER_SIZE mutant killer [1e-07] sound, 4 KiB / 64 KiB stand-in (256x vs 48x limit), `_cpus_to_load` tests, fresh-text test all sound.

## Minor
- test_timing_fixture.py:371 "well above the floor" reads oddly next to :372-374; reword.
- test_timing_fixture.py:1-3 two true sentences easy to misread; reword.

## Not checked
Any timing, the 58 s figure, main's lint state, the CI perf timeout, CHANGELOG placement, Windows.

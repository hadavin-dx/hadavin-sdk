# timing-ff26dab7-codebase-r2: timing harness fix (ORDER 267), head ff26dab7, round 2, persona codebase details

Source: hand-back of agent a7bc5fa7735bff474, saved by the lead (condensed). Static only, nothing run. 0 Blocker, 3 Major, 6 Minor.

## Major
- **M1** E731 lambda assigned to a name in tests/test_timing_fixture.py lines 188, 200-201 (ruff default E7 set; round-1 ruff did not cover these added lines). Use def.
- **M2** `t_small >= 4 * MIN_SMALL_S` (test_timing_fixture.py:321, :330) has margin about 1.5x on the quadratic stand-in (6 ms vs 4 ms); a CPU 1.5x faster fails deterministically. Pin at 2x or enlarge small size. (Same as design M1.)
- **M3** The perf group target of 30 s is not met (70.9 s measured). Disclose in NOTES and PR body; do not repeat "about 30 s". Obvious cost: the 128 KiB quadratic stand-in measured three times (test_migration_numbers.py:823, test_timing_fixture.py:315, k5/e2e); share a measurement or shrink. CI job timeout 30 min so not a CI risk.

## Minor
m1 migration_numbers_mutants.py:335 killer pin `[1e-09]` rests on a float tie (limit about 4e-6 vs t_big 4e-6); pin 1e-07 or comment. m2 stale docs: test_timing_fixture.py:1-2 "no clock" false for the two real-process tests; timing.py:15-16 coarse-clock claim describes only the fake-clock tests; "CPU seconds" wording wrong on Windows (wall clock); test_k5_perf.py:55 "(8x vs a 24x limit)" misleading. m3 busy_cpus failure is a setup ERROR (wording); kill fallback untested. m4 weak tests: busy-worker count test passes for any implementation; measure_sizes fresh-text per repeat not pinned; `_variant` uniqueness only length for short texts; byte cap counts characters. m5 CHANGELOG has no entry for the harness change (one line). m6 platform shape fine (2-core CI ok; Windows wall clock best-of-2 weak).

## Checked correct
block_seconds loop and caps; clock choice; fresh text; busy workers count, handshake, stop; four of five hand mutants killed by the named tests (same-text mutant killed by cache hits assertion, not the flag assertion); mutant table strings unique and updated; imports and perf marks right.

## Not checked
Any execution; mutation_manifest.json pinning; tools/mutation_runner.py pinned comparison; head pyproject, ci.yml, CHANGELOG; other callers of is_superlinear; the lexer source.

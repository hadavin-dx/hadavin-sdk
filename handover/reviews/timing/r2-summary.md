Status: resolved (round 2, head ef83cd86, no Blocker, no Major)
Design review (a2014f61) and codebase review (aeb1977a) both found no Blocker and no Major. Nits (all PROPOSE FIX in one push, no new review per the round cap):
- N1/N2: reword the comments at test_timing_fixture.py:532-537 and :628-637 (only calls_paused=1 hits a tiny batch; the big text stands because its paused batch looks long enough).
- N3: optional test for the second-loop MAX_ROUNDS raise; a mutant for WAIT_FACTOR / WAIT_MIN_S.
- Siblings: confirm tests/test_scan_repo.py:182-184 (monotonic() < 20 around _scan) is not a CPU-bound wall ceiling; name the other raw wall-clock tests (test_k5_classes.py:488-498) in the timing.py docstring.
- Changelog stress counts ("6 of 6", "1 skipped") are unverifiable from the snapshot: evidence runner a027c17f must re-measure; explain the skip.
Not run by reviewers: nothing executed; the 32 timing mutants and the stress runs need the evidence runner.

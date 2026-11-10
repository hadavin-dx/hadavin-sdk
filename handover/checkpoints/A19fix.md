# A19fix checkpoint 1 (2026-11-10 ~17:20 UTC)
done: G1 tests written and shown failing on 7f24178 (29 failed; file handover/checkpoints/A19fix-G1-fail-on-7f24178.txt; old tree had only the two constants stubbed); G1 code (commonwords limits, check_id), G5 (fold_name calls canonical, is_stage_name to tests/fixtures, scan reads STAGE_WORDS), G6 fixture, G3 src rows removed. 320 tests pass in the two files.
next: G3 pins (row count, no src rows, stale), G2 (docstring trigger, T14 fixture walk), G4, G7, mutants file, full suite.
blockers: none. commit SHA: none yet.

checkpoint 2: G1/G2/G3/G5/G6 done, mutants 43 (42 then T6b fixed). next G4, G7, full run
checkpoint 3: committed 85e0801 (G1-G7); mutants 78/78 good; full suite started via heavy.sh log /tmp/claude-0/a19/full.log (waits for a slot)

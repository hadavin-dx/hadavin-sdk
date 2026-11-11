# timing-nits checkpoint 1 (builder, worktree /home/user/build/B-timing-nits, branch core/timing-nits from ef83cd86)
Time: started about 22:05 UTC; this note about 22:20 UTC (IST +5:30).
Done: N1/N2 comments reworded (traced the real batches first); 3 new tests (second-loop MAX_ROUNDS raise, wall 3x cpu is not waiting, pause under 5 ms floor); 4 new mutants (second-loop raise, WAIT_FACTOR 5000 and 2, WAIT_MIN_S 0); runner now prints the first failing line for CRASH rows.
Next: wait for the 4 new mutants, then 10-mutant sample, docstring naming raw wall-clock tests, test_scan_repo justification (measured 0.09 s against a 20 s ceiling), CHANGELOG counts, gates, gitleaks, one full suite, push.
Blockers: none. Note: local core/fix-timing-harness-flake is at a8c269c8 and origin/core/fix-timing-harness-flake at 2f94c2b2; ef83cd86 is on wip/cloud-timing-fix2 and is a fast-forward child of 2f94c2b2, so I push HEAD:core/fix-timing-harness-flake.
sha: not committed yet

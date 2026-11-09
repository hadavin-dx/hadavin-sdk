Checkpoint 1 (06:11Z): head 203451264e72. Done: items 3,5,7,8,9 raw files. Running detached via heavy.sh: item 1 (py3.12), item 2 (py3.13) suites. Next: item 4 perf alone, item 6 mutants (28 changed/new first, then full 226), SUMMARY.md. Blockers: none. Note: bandit is in uv group scan, not test.

Checkpoint 2: first suite runs (3.12, 3.13) exited 0 but printed NO summary line (files kept as *-run1-no-summary-line.txt); reran both with --junitxml for counts, queued in heavy.sh behind other sessions' jobs (PR74, PR66, PR75 hold all 3 slots). The 28 changed/new mutants queued the same way (two earlier attempts exited 1 with no output: see below, cause unknown). Not yet run: item 4 perf (must run alone), item 6 full 226 list.

Checkpoint 3 (06:36Z): 3.13 rerun (junit) running; 3.12 rerun, perf, 28-mutant run still queued behind other sessions' jobs in heavy.sh. Items 3,5,7,8,9 complete.

Checkpoint 4 (06:53Z): 3.13 suite done (junit: 11337 tests, 0 fail, 0 error, 455 skipped). Perf done (16 passed). 28 changed/new mutants done: 27 good, 1 BAD (WRONG_REASON). 3.12 rerun still queued behind other sessions. Full 226 mutant run NOT started (slots).

Final (07:05Z): stopped at 60 min. See SUMMARY.md.

# Q8a-1 b6 checkpoint, 22:20 UTC

Done: all 5 issues implemented (commit 4aa15efd), p1b key-name test adapted and crash mutants built directly (2ea1171f). Full suite at 2ea1171f: 10807 passed, 1 skipped (full2.log). Earlier dblink failure was my Postgres server lacking PGHOST/PGPORT in its environment; restarted with them.
Mutants: first run 99 of 110 good; 11 bad M16 mutants (wrong expect text, one snippet split across lines, one survivor M16e, two param ids). Fixed in uncommitted stage_mutants.py; M16 re-run is running through heavy.sh (mut-M16.log/.rc).
Next: read M16 result, commit, gitleaks, push fast-forward to core/q8a-1-live-override-refusals, stop my Postgres, final report.
Blockers: heavy slots queued (other agents); the 60-minute box is already exceeded because of the queue.

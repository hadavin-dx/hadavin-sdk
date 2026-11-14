# checkpoint B16 (fix-5 r7), 05:15Z (started 05:05Z)
Done: tree /home/user/work/b16-tree (worktree of the clone at f3c39cf8 + claims series + r6 patch; no origin/n8n-evidence-rerun ref). Tests first: raw/b16-fails-before.log (114 failed on the r6 scripts and port helpers). Then: reset.sh and reset.ps1 rewritten in three passes; port blocks (new tests/port_blocks.py, start 20000, two halves); direct binds routed; README. Targeted runs green so far (reset_scripts 66 passed).
Next: finish targeted run, mutation run (script in scratch), pwsh attempt (distro package manager only), xdist run in a scratch venv, ONE full run no earlier than 05:30Z or load < 3.
Blockers: none yet. Lead orders applied: bash minimum named once (README); script text names mapfile -d.

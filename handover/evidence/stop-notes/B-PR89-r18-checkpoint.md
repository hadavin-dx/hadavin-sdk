# B-PR89 round 18 checkpoint (13:31 UTC start)
- 14:03 UTC: plan changed by lead (D-002 REVISED): k-gram pass removed; output projection (_shown_line/_shown_id) + address check on _address_fields with throwaway_hosts; no marker, no boolean override.
- Done: runner (projection, address check, lock dir 0700, minors), mutation.py judge_report, tests (fuzz, address, projection, lock dir, judge_report), 7 new mutants (224), CHANGELOG, docstring.
- Next: proof run on db0d9eb, full gates (pytest with Postgres 56030, ruff, bandit, gitleaks), pins, commits, push.
- No commit yet. Worktree /home/user/build/B-PR89, venv /home/user/build/venv-pr89b.

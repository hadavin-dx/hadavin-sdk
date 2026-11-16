# Q8b checkpoint (builder stopped on the lead's order, 16:19 UTC / 21:49 IST, 2026-11-11)
## Commit
be53718ccbf5e2038cc18c87d334577e7b11ace8, ONE commit on origin/main 2a8c2aac, branch core/q8b-partial-mask-and-card-redaction.
Pushed as a new ref (gitleaks exit 0 before the push). No pull request. Worktree /home/user/build/B-Q8b is clean.
## Done (all on be53718c unless said)
- The five source files, three new test files, tests/q8b_mutants.py (26 mutants), two existing guard tests, CI step, CHANGELOG.
- Full suite ONCE with own Postgres 16.15: 10670 passed, 1 skipped, 28 deselected, 16 xfailed, pytest exit code 0 (B-Q8b-full.log).
- tests/q8b_mutants.py 26 of 26 good, exit 0 (B-Q8b-q8b-mutants.log); tests/stage_mutants.py 37 of 37, exit 0 (B-Q8b-stage-mutants.log).
- ruff check, ruff format --check, bandit -ll, tools/scan_repo.py, gitleaks: exit 0 (B-Q8b-ruff.log, -bandit.log, -scan.log, -gitleaks.log).
- Fail-before on a clean origin/main worktree (/home/user/build/B-Q8b-base, tests laid over): 112 failed, 104 passed, 14 xfailed
  (B-Q8b-fail-before.txt, -groups.txt, -first-lines.txt, B-Q8b-pass-on-main.txt).
- Appendix scripts re-run on 46fdcfb2 (before two later source changes: mention rewrite on the whole line, Secret data that is not a map): /home/user/build/B-Q8b-appendix/.
- PR notes draft: /home/user/build/B-Q8b-pr-notes.md.
## Next (for the agent that resumes)
1. CI performance step (`pytest -q -m perf -rs` with HADAVIN_TEST_PG_DSN): NOT finished; I stopped it after about 40 seconds on the lead's order (B-Q8b-perf.log ends with exit code 143 = stopped, not a test result). Run it alone.
2. Re-run the appendix scripts on be53718c (the two later source changes are not in the saved outputs).
3. Add the Q8b built-beyond items to the PR notes if the lead wants them worded differently; then the lead's evidence runner and egm reviewers.
4. After PR77 merges: rebase and re-run everything the ticket's "Merge order" paragraph lists.
## Blockers
None.
## Running jobs
None. My Postgres (data /home/user/build/pg-q8b, port 56160) is stopped; the port is free. Start it again with pg_ctl as the postgres user (see the report) or make a new cluster.
Left on disk on purpose: worktree /home/user/build/B-Q8b-base (origin/main with the new tests laid over, 5 changed files, for the fail-before proof), venv /home/user/build/venv-q8b, scripts q8b-env.sh, q8b-run-full.sh, q8b-run-mutants.sh.

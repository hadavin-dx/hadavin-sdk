EVIDENCE RUNNER final handback, Q8a-1, head 3f3d4b6cf9d182adc3ceaae31cd3a0663e7299d5. PARTIAL: fail-before has no result, the flaky-test runs were not made, and RESULTS.md was not written.

Done on the exact head (HEAD confirmed, tree clean). Raw logs in /home/user/build/evidence-raw/q8a1-3f3d4b6c/:
- Full pytest, once, via heavy.sh with own Postgres 16.15: `pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, rc 0, "10774 passed, 1 skipped, 28 deselected in 287.04s". XML: 10775 tests, 0 failures, 0 errors, 1 skipped (tests/contracts/test_llm.py:95).
- Stage mutants (clean separate worktree): 92 of 92 good, problems [], rc 0.
- ruff check and ruff format --check over src tests demos tools: rc 0. bandit -ll: rc 0. scan_repo.py: rc 0. gitleaks origin/main..HEAD: rc 0, no leaks. Added suppression lines in the diff: 0. 19 changed files.
- My own hostile probes on config and registry error text (68 rows): marker absent from text and traceback in 61; 1 row accepted (golden_dir outside the folder loads without error); 7 rows show the marker (five as an unknown key name: top-level, backend setting, systems entry, agent entry, action file; two as a value: unknown model_route name and unknown scope name in the registry cross-check). Tick probes: replace() on a context in pilot and prod gives the new message; STEPS is read once per run_tick; duplicate and missing built-in steps refused. CHANGELOG greps for review items 2, 4, 6, 8, 9 found the expected text; item 8 figures are quoted from ecd5dba1, not re-measured.

Not done:
- Fail-before (item 7): run 1 aborted at collection because tests/test_q8a_live_overrides.py imports `VaultConnection`, which origin/main (2a8c2aac) lacks (rc 2, no tests ran; fb-run1-collection-error.log). The relaunch with --continue-on-collection-errors was still queued at my last check; fb.rc did not exist. No failed or passed counts.
- Flaky timing test 3x head and 3x main: not run. Perf step and vault suite: not run (ticket names no perf item; no Vault address).
- RESULTS.md and its gitleaks check: not written; I changed nothing in handover/.

Setup: `uv sync --no-build` fails (editable root), plain locked sync used. My Postgres is on 127.0.0.1:56947 (moved from 56731 because agent q8c1 planned that port). Leftovers of mine to clean after fb.sh ends: that Postgres (data in /home/user/build/EV-q8a1-3f3d4b6c/pgroot, stop as user postgres) and worktrees wt, wt-mut, wt-fb under /home/user/build/EV-q8a1-3f3d4b6c. I fixed nothing and touched no other agent's process.
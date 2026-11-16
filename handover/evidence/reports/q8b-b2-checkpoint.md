# Q8b batch 2 checkpoint 2 (2026-11-11 ~21:58Z)
Done: issues 1-7, 9-12 in code and tests (tests/test_q8b_batch2.py, 19 tests; 15 fail on bcb2bfec, 4 pass there by design); mutants 52 of 52 good (M22 dropped: redundant now); ruff, format, bandit clean; Q8b+k5+k1b tests 7269 passed (before last test edits).
Next: full suite (queued in heavy.sh slot, log /home/user/build/evidence-raw/q8b-b2/full.log), perf step, final report.
Blockers: gitleaks is not installed here (not run). n1 (record-walk key names dbpass etc.) not fixed: needs lead decision (over-masks bypass/compass/oauth).
Commit: see push below.

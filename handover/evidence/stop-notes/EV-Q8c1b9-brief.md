# Q8c-1 batch 9 EVIDENCE brief (round 9 evidence). Read EV-BRIEF-COMMON.md first, then this.
Tag Q8c1b9, pkg Q8c-1, head c6bd7108d3843f9d22f5344966af8e9783969251 on origin/wip/cloud-q8c1-b9 (git fetch origin wip/cloud-q8c1-b9). Previous head 208a47d5 (batch 8). Snapshot (names only): /home/user/build/snap/q8c1b9-c6bd7108/ (FILES.txt, DELTA-FILES.txt, DIFF.patch vs main, DELTA.patch = 208a47d5..c6bd7108). Results: handover/evidence/Q8c-1/c6bd7108/RESULTS.md (also this 8-char folder name).
Spec: handover/tickets/Q8c-least-privilege-policy-per-kind.md (section 6.4 must-fail-on-main). Task list that was fixed: handover/reviews/Q8c-1/goldfish_review_report-r8.md (Issues 1-7; Issue 8 is the IMPOSSIBLE-NOW Vault CI gate). Previous evidence: handover/evidence/Q8c-1/208a47d5/RESULTS.md. Do NOT read the builder's NOTES.md for judgment; you may read it only to find the claimed commands.
Extra items beyond the common list:
(a) tests/policy_mutants.py (the package's mutant runner) on the real clock, with `--day 2026-12-11` and with `--day 2026-12-12`: record "N of N good", any weak/WRONG_REASON line, the `probe ok` line, and diff the per-mutant lines of the three runs.
(b) python tools/policy_page.py --check (real clock) and python tests/stage_mutants.py.
(c) Fail-before: copy only the changed/new test files of DELTA-FILES.txt into a clean detached worktree of 208a47d5 and run them; record counts and per-test failures. Then the overlay on origin/main for ticket 6.4 (F1, F2; F3 = Vault engine, record not run).
(d) Your own probe of Issue 1: plant a renewed review_by in a copy of the dated lists (earliest and a mixed pair) and read the generated page text and docs/declared-permissions.md; grep the whole repo (src tests tools docs CHANGELOG.md) for the literal review day text and list every place it still appears as text.
(e) Issue 6: show the fixed day reaches the child pytest (run one mutant by hand with the env var and print what the tool sees).
(f) The known flake test_the_timing_harness_flags_a_quadratic_stand_in only if it appears in the full suite; do not rerun it otherwise.
Full pytest: -m "not live and not perf" with HADAVIN_TEST_PG_DSN set, own Postgres 16 with PGHOST/PGPORT in the SERVER environment (the builder's one failure was the dblink test from a missing PGHOST; record yours).
Report what failed or was not run FIRST.

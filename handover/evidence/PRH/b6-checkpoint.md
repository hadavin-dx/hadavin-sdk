# PR H batch 6 checkpoint (builder)

Started 2026-11-12 02:21 UTC (07:51 IST). Worktree /home/user/build/B-PRH-b6, branch core/prh-b6 from origin/wip/cloud-prh-b5 (3db0d34d).

## 02:40 UTC (08:10 IST), about 20 minutes in
Done and committed locally (aab1fc5a, not pushed):
- H1 (per-copy counts), H2 (never returns the text as written), H3 (spaced character reading), d3, d11 in code.
- New tests `test_b6_*` in tests/test_prh_tools.py (27 tests); 20 of the first 24 fail on 3db0d34d code; the seeded mix test fails on old code too.
- Mutants 72-79 added, 58 and 59 re-pointed (their old text moved), floor 55 -> 79, pass count pinned at 14 (was 13: the character reading is now a pair).
- Gates run so far: ruff check, ruff format --check, bandit -ll, scan_repo, stage_mutants 37/37: all exit 0.
Next: full pytest through heavy.sh (queued behind other agents), prh_mutants.py in B-PRH-b6-mut, cost compare, NOTES.md, ticket errata, push.
Blockers: none. Heavy slots all busy at 02:40 UTC.

## Checkpoint 03:43 UTC (stopped by the lead, past 75 min)
Done: H1 per-copy counts, H2 no `return raw`, H3 spaced character reading, d3/d11, errata 8.7, mutants 72-81, floor 81, worst pass count 14. Full pytest 12962 passed at 8d5f41d8.
Next: final mutant run at the head (42 may still survive), cost compare, full pytest at final head.
Blockers: heavy slots were busy (queue waits of 15+ minutes).

## Checkpoint 04:04 UTC (resumed 03:44, 45-minute box)
Done: 81 of 81 mutants good at 931d7396 (rc=0; mutant 42 is killed by the hex-in-capitals test). Next: cost compare (queued), then full pytest at the final head, then light gates and push. Blockers: heavy slots (waited about 18 minutes for the mutant run).

## Final 04:12 UTC: all gates green at 931d7396 (see b6/NOTES.md). Nothing left.

# Citation check, REVIEW.md round 35 additions (checker, read-only)
FAILURES / CAVEATS FIRST
1. "952 commits after b4cce5b": `git rev-list --count b4cce5b..HEAD` now gives 955 (HEAD 842055e25). The 3 extra commits are WIP commits made after round 35 was written; 952 was likely right then. Treat as stale, not wrong; re-run at freeze.
2. "the lane's run on b4cce5b had 2 failed + 9404 passed + 455 skipped = 9861": the sum is right (heavy-test-lane/SUMMARY.md:21), but that row is "with the 3 patches" (the patched tree), not plain b4cce5b. Baseline b4cce5b is 2 + 9389 + 455 = 9846. Wording imprecision.
3. "52 test files changed": 52 files under tests/ changed (22 added, 30 modified); only 40 have a test_ name. Count 52 is right as "files under tests/", not as "test files".
4. 10553 (2 + 10551) cannot be verified: pytest is not installed here; no run done. 692-item difference stays unverified (the review says so itself).
Everything else checked: OK.

# E9 evidence: lane3-fix-6 round 2 (EVIDENCE RUNNER, no judgement)

Base commit: f3c39cf89ec989f032ea48a23cfd824b88da9c68 (detached worktree /home/user/work/e9-tree, from /home/user/work/src). Tree head sha after apply: unchanged f3c39cf8 (nothing committed; changes staged with `git add -A`: 8 paths).
Note: /home/user/work/src itself is at 61ded9eb, not f3c39cf8; the worktree was made at the requested commit.

## Patch sha256
- lane3-fix-6-r2.patch  30e05c0c956161f619f9b1333341e3cb57988d3516109744460d85c01aa2259f
- lane3-fix-6b.patch    0f8e2f2e641f90fc143423ea08282d652f0cb09a4762ab7921600ddd66e29cac
- lane3-fix-6-r2-for-stack.patch  983b3eaf0f77ec4c1a2cb955cac89d1262f37c0382b5ec4d1af9b1c42f6bbade
- claims-stack-on-f3c39cf8.patch  7138e884333d4bd0f9d377873fe05aae5f1dfce275758952d2b6e4f05d89194c

## Apply checks (raw)
- Plain base: `git apply --check lane3-fix-6-r2.patch` rc=0; applied r2 rc=0; applied 6b rc=0 with warning: `lane3-fix-6b.patch:65: new blank line at EOF.` / `warning: 1 line adds whitespace errors.`
- Stack (separate scratch worktree at f3c39cf8, since removed): claims-stack-on-f3c39cf8.patch check rc=0 and applied; lane3-fix-6-r2-for-stack.patch check rc=0 and applied; lane3-fix-6b.patch check on that stack rc=0.
- Extra: plain lane3-fix-6-r2.patch on the stack base fails: `error: patch failed: README.md:129`, `error: README.md: patch does not apply`, `error: patch failed: contract.md:65` (expected; use the for-stack variant).
- Stack tree was only apply-checked; no tests run on it.

## Full pytest (plain base + r2 + 6b)
Command: `TMPDIR=/home/user/work/priv/e9/tmp timeout 3000 /home/user/work/final-venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=/home/user/work/priv/e9/tmp/bt` (serial, cwd e9-tree).
Result: `3693 passed, 200 skipped in 1196.01s (0:19:56)`; EXIT_CODE=0; WALL_SECONDS=1197. Failures: none. Log: evidence/raw/e9-fix-6-r2-full.log
CPU idle (vmstat id): start 90%, end 48% (other agents running; machine not loaded at start).
Environment caveat: the shell had AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE and ANTHROPIC_BASE_URL set (sandbox proxy variables); I did not unset them, so the "no cloud configuration" condition was NOT met. Values not printed.

## Skips by reason (from -rs; 16 SKIPPED lines, total 200)
- Browser (playwright not installed): 166 (22 test_mode_safety, 28 test_portal_browser, 113 test_portal_lead_pages, plus 3 more in the same reason group)
- gitleaks missing: 24 (test_gitleaks_exceptions) + 5 + 1 = 30 (incl. 2 in test_gitleaks_semgrep_lock, 1 in test_hygiene; hygiene gitleaks scan therefore did NOT run)
- "singles": no skip reason mentioning singles found; one skip is "measurement run: set LEAD_DESK_LOAD_N" (1)
- Other: 1 Windows-only (test_stall_eviction:526), 1 root can read no-permission file, 1 ntpath.isreserved needs Python 3.13.
- 241/72 numbers: not measurable; the log (quiet -q mode) holds no such counts, and the totals here are 3693 passed / 200 skipped.

## Not run
Hygiene gitleaks scan, all playwright browser tests, load-measurement test, full suite on the stack tree.

## Cleanup
e9-tree worktree left in place (not removed) so the staged tree can be inspected; remove with `git -C /home/user/work/src worktree remove --force /home/user/work/e9-tree`. Scratch e9-stack removed. Progress notes: evidence/raw/e9-progress.txt.

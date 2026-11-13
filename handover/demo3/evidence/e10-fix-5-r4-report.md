# E10 evidence: lane3-fix-5 round 4 (EVIDENCE RUNNER, no judgement)
Base: f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree /home/user/work/e10-tree, detached, removed at end). Nothing committed.
Note: the clone /home/user/work/src itself is at 61ded9e (main); the base commit exists there and was used as asked.
Patch: lane3-fix-5-r4.patch sha256 97a01910c3a79ab13aa858f79e2f89433aa06891b3a274d45d108423e7a9f4e2
## 1. Apply on plain base
git apply rc=0. Staged: M scripts/reset.sh, M tests/conftest.py, M tests/support.py, A tests/test_reset_ps_width.py, M tests/test_reset_scripts.py.
## 2. Stack apply check (base + claims-stack-on-f3c39cf8 + lane3-fix-3-r5 + lane3-fix-1-rN + lane3-fix-5-r4), raw/e10-stack-apply.txt
- with lane3-fix-1-r4: all four git apply rc=0
- with lane3-fix-1-r5 (exists): all four git apply rc=0
(apply only; no tests run on the stacks)
## 3. Full serial pytest, plain patched tree
Command: TMPDIR=/home/user/work/priv/e10-tmp python(final-venv) -m pytest -q -rs -p no:cacheprovider --basetemp /home/user/work/priv/e10-tmp/bt (no xdist, timeout 3000)
Result: 3734 passed, 200 skipped, 0 failed. EXIT_CODE=0. Wall 1253 s (pytest 1252.34 s). Log: raw/e10-fix-5-r4-full.log
Skips seen in tail: playwright not installed (portal tests), LEAD_DESK_LOAD_N measurement run, Windows-only reset test; full list in the log (-rs).
Idle CPU (vmstat, 3 samples): start 64/64/63 %, end 64/63/56 % (other processes on the machine were using about 35 %; not a quiet machine). Files raw/e10-vmstat-start.txt, e10-vmstat-end.txt.
## 4. xdist proof (q1-xdist-venv, -n 4, tests/test_reset_ps_width.py tests/test_reset_scripts.py), 20 runs after serial finished
20 of 20 runs rc=0, each "96 passed" (16-19 s). No failures, so no tracebacks. Counts: raw/e10-xdist.txt, per-run logs raw/e10-xd-N.log.
## Not run
Tests on the stacked trees (step 2 was apply-only); no mutation run; no lint/bandit; playwright tests skipped (module absent); Windows-only tests skipped.
Progress notes: raw/e10-progress.txt

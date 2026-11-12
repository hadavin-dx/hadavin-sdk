# EVIDENCE RUNNER results: PR H batch 10, head 9de76195 (in progress, written progressively)
Runner records only; nothing here is a verdict. Raw logs: /home/user/build/evidence-raw/PRHb10-9de76195/ (outside the repo).
Start 14:20 UTC (19:50 IST). Head verified: `git rev-parse HEAD` = 9de76195728ce1f81058c605fa2fce9cf8b0f3e8 in my own worktree, tree clean; origin/wip/cloud-prh-b10 tip is the same.

## NOT RUN YET / waiting (updated below as they finish)
- (1) tests/prh_mutants.py as root and as nobody: queued in heavy.sh since 14:21 UTC (3 slots held by other agents).
- (2) full pytest, (3) stage_mutants, (4) perf and perf --compare-main: queued behind (1).

# EVIDENCE RUNNER results: PR H batch 10, head 9de76195 (in progress, written progressively)
Runner records only; nothing here is a verdict. Raw logs: /home/user/build/evidence-raw/PRHb10-9de76195/ (outside the repo).
Start 14:20 UTC (19:50 IST). Head verified: `git rev-parse HEAD` = 9de76195728ce1f81058c605fa2fce9cf8b0f3e8 in my own worktree, tree clean; origin/wip/cloud-prh-b10 tip is the same.

## NOT RUN YET / waiting (updated below as they finish)
- (1) tests/prh_mutants.py as root and as nobody: queued in heavy.sh since 14:21 UTC (3 slots held by other agents).
- (2) full pytest, (3) stage_mutants, (4) perf and perf --compare-main: queued behind (1).

## Done so far (14:45 UTC)
- (1) prh_mutants as root: "156 of 156 good; problems: []", exit 0 (14:30-14:36 UTC, alone in my own slot use). As nobody (uid 65534, git-archive copy, env -i): "156 of 156 good; problems: []", exit 0. No survivors. (Numbers go to 160 but 156 mutants run; the runner's own count is 156.)
- (2) full pytest -m "not live and not perf" -rs on my own Postgres 16.15: "13210 passed, 1 skipped, 63 deselected in 568.60s", exit 0 (0 failed; the builder's dblink failure did not occur here; I did not look into why). Skip: tests/contracts/test_llm.py:95 Stubber refuses a malformed Converse shape.
- (3) stage_mutants: "37 of 37 good; problems: []", exit 0.

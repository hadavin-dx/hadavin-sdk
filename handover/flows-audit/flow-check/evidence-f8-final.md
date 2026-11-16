# Evidence F8 final (raw output only, no judgement)

Head at start: 2229ce16619d316ae00998e4bac2b0035cda41a1 (tracked RUNBOOK.md was already modified, uncommitted, before I started).
Head at end: 6f62aab13235014d308fd430df6e31bd592abf2e (two "board" commits by another session landed during my runs; changed files listed below, none under flow-check/).
  handover/flows-audit/RUNBOOK.md
  handover/flows-audit/STATUS-BOARD.md
  handover/flows-audit/reviews-of-core-patches/REVIEW.md
  handover/flows-audit/reviews/round-12z-findings.md

## Failures
None. All commands below exited 0.

## Notes
- Bandit -ll exit 0; it lists 1 Low-severity issue (below the -ll threshold).
- The F8 README gives no build recipe for the patched copy; I used the steps of flow-check/run_all.sh (copy committed flows, git apply F-002 then F-008, run build_mainframe.py with MF_REAL=1, MF_V4=1, MF_TRIES=2, MF_TMO_MS=10000). Patched dir: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8/work/g/real
- run_all.sh printed: committed pin reviewer line NOT confirmed by the lead.
- git status --short on flow-check: 0 lines after all runs; no tracked file changed by the runs; nothing restored.

| command | rc | key output line |
|---|---|---|
| build patched copy (git apply F-002, F-008; build_mainframe.py real) | 0 | apply rc=0 twice; gen rc=0; 4 flow files |
| bash flow-check/test_take_check.sh <patched> <fresh> | 0 | test_take_check: 68 of 68 cases as expected, 0 not as expected |
| RUN_ALL_RAW=<fresh> bash flow-check/run_all.sh <fresh> | 0 | run_all exit status (real-v5 default runs + self-test): 0 |
| ruff check . | 0 | All checks passed! |
| ruff format --check flow-check | 0 | 46 files already formatted |
| bandit -ll -r flow-check | 0 | Medium 0, High 0, Low 1 (total issues by severity) |
| python3 -I tools/check_secrets.py | 0 | PASS 0 hits in 1781 files |
| python3 -I tools/check_refs.py | 0 | PASS 5146 references |
| python3 -I tools/check_counts.py | 0 | PASS 52 files / 655 nodes |
| git status --short flow-check | 0 | (empty) |

Raw logs: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8 (1-test_take_check.log, 2-run_all.log, 3a/3b/3c, 4-*.log, raw-run-all/)

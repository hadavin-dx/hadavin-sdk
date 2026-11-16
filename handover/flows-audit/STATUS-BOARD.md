UPDATED_UTC: 2026-11-16T18:58:58Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.42 load of 4 cores, mem 1/15 GB, RAM 1131/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify fixers; batch r46/r39 fixers when readers report
PUSHED_UTC: 2026-11-16T18:58:58Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback + recovery audit | done | 100 | F6-AUDIT.md, F6B-AUDIT.md | n8n facts unverified; F6b SQL untested |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | state | produced so far |
|---|---|---|---|---|---|---|---|
| a7b88145 | fixer | sonnet | F8 r12 fixes (flow-check) | 18:29Z | 18:58Z (past; check next beat, stop only after note) | running | not yet |
| ad482d95 | fixer | sonnet | patch-copies r20 fixer (README, DEAD-MAN-CHECK; uncapped) | 18:51Z | about 19:10Z | running | not yet |
| a7223517 | fixer | sonnet | FINDINGS/LEDGER r28 fixer | 18:53Z | about 19:12Z | running | not yet |
| ac0729f0 | reviewer comprehension | sonnet | REVIEW.md r45 stranger read | 18:55Z | about 19:08Z | running | not yet |
| a318107e | fixer | sonnet | Q31 r32 fixer (16 Majors) | 18:56Z | about 19:15Z | running | not yet |
| ae2acecf | fixer | sonnet | RW/CT r41 fixer | 18:57Z | about 19:15Z | running | not yet |
| a28bc565 | reviewer comprehension | sonnet | TAKE-CHECKLIST 81-477 read | 18:58Z | about 19:08Z | running | not yet |
| a03960d5 | reviewer comprehension | sonnet | RUNBOOK unread ranges + FIX-PLAN 168-257 read | 18:58Z | about 19:08Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify each fixer on hand-back with own commands (counts, checkers, ruff)
2 REVIEW.md r46 fixer after stranger reader ac0729f0 reports (batch with review-design-r45)
3 plan-files r39 fixer after both new readers report (batch with plan-files-reader-r39)
4 F8 r12: two uncapped reviewers + evidence runner once fixer hands back
5 drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

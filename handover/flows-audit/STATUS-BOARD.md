UPDATED_UTC: 2026-11-16T19:08:43Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.86 load of 4 cores, mem 1/15 GB, RAM 1264/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify fixers on hand-back
PUSHED_UTC: 2026-11-16T19:08:43Z

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
| a7b88145 | fixer | sonnet | F8 r12 fixes (flow-check) | 18:29Z | 19:30Z (note asked) | running | not yet |
| adcf1b56 | fixer | sonnet | REVIEW.md r46 fixer (uncapped) | 19:00Z | about 19:30Z | running | not yet |
| a144d2ea | fixer | sonnet | plan-files r39 fixer (RUNBOOK, TAKE-CHECKLIST, FIX-PLAN) | 19:03Z | about 19:40Z | running | not yet |
| a098e73b | fixer | sonnet | RW/CT r42 fixer (5 Majors + 5 regrades) | 19:04Z | about 19:35Z | running | not yet |
| a6934148 | reviewer comprehension | sonnet | patch-copies README r21 read (uncapped) | 19:05Z | about 19:15Z | running | not yet |
| ac0a8a2a | reviewer codebase-details | sonnet | DEAD-MAN-CHECK r21 technical review (uncapped) | 19:05Z | about 19:15Z | running | not yet |
| a0fdd001 | reviewer comprehension | sonnet | FINDINGS/LEDGER r29 read (ten rows) | 19:07Z | about 19:17Z | running | not yet |
| a8fa6049 | reviewer comprehension | sonnet | Q31 r35 read (line 515 onward) | 19:07Z | about 19:17Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify each fixer on hand-back with own commands (counts, checkers, ruff)
2 F8 r12: two uncapped reviewers + evidence runner once fixer hands back
3 fixers for the r21 patch-copies reviews, r29 FINDINGS and r35 Q31 reads when they report
4 REVIEW.md readers for unread ranges 133-332, 408-451, 459-550, 580-884 after r46 fixer
5 drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

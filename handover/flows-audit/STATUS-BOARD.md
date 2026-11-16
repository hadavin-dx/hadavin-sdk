UPDATED_UTC: 2026-11-16T18:30:44Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 0.45 load of 4 cores, mem 1/15 GB, RAM 1061/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: fixers running; verify on hand-back
PUSHED_UTC: 2026-11-16T18:30:44Z

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
| a4932a53 | fixer | sonnet | REVIEW.md r43 fixes | 18:21Z | about 18:45Z | running | not yet |
| ac51c730 | reviewer comprehension | sonnet | RW/CT r37 stranger read (unread ranges) | 18:27Z | about 18:37Z | running | not yet |
| a9a3009c | reviewer comprehension | sonnet | Q31 r30 stranger read (unread items) | 18:28Z | about 18:38Z | running | not yet |
| a0bc57f5 | fixer | sonnet | plan-files r36 fixes | 18:28Z | about 18:45Z | running | not yet |
| a7b88145 | fixer | sonnet | F8 r12 fixes (reader r12 M1-M3) | 18:29Z | about 18:50Z | running | not yet |
| a390dc2b | reviewer comprehension | sonnet | RUNBOOK steps 1-25 read on snapshot | 18:29Z | about 18:40Z | running | not yet |
| ac924c35 | fixer | sonnet | patch-copies r19 fixes | 18:29Z | about 18:50Z | running | not yet |
| a4a20bcd | fixer | sonnet | FINDINGS/LEDGER r24 fixes | 18:30Z | about 18:45Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify and review F8 r12 fixes (two uncapped reviewers)
2 REVIEW.md r39 readers after r43 fixer
3 patch-copies r20 readers after r19 fixer
4 FINDINGS/LEDGER r26 and plan-files r37 readers
5 drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

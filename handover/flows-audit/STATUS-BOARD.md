UPDATED_UTC: 2026-11-16T18:25:58Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.91 load of 4 cores, mem 1/15 GB, RAM 1146/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify fixers, launch readers
PUSHED_UTC: 2026-11-16T18:25:58Z

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
| a55f209a | evidence runner | sonnet | F8 r11 repeat runs, raw output | 18:00Z | about 18:35Z | running | not yet |
| a4932a53 | fixer | sonnet | REVIEW.md r43 fixes | 18:21Z | about 18:45Z | running | not yet |
| ac9fa011 | fixer | sonnet | RW/CT r35 fixes | 18:23Z | about 18:45Z | running | not yet |
| a5925945 | reviewer comprehension | sonnet | patch-copies r19 stranger read | 18:23Z | about 18:33Z | running | not yet |
| a0e57c6b | reviewer codebase-details | sonnet | patch-copies r19 shell read | 18:23Z | about 18:33Z | running | not yet |
| aa2ab9a5 | fixer | sonnet | Q31 r29 fixes (QUESTIONS.md) | 18:24Z | about 18:40Z | running | not yet |
| ac62b71e | reviewer comprehension | sonnet | FINDINGS/LEDGER r25 stranger read | 18:25Z | about 18:33Z | running | not yet |
| aeed0401 | reviewer comprehension | sonnet | plan-files r36 stranger read | 18:25Z | about 18:35Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 F8 fixer after evidence runner (uncapped)
2 REVIEW.md r39 readers after r43 fixer
3 RW/CT r37 readers (unread ranges)
4 Q31 r30 reader (unread items)
5 drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

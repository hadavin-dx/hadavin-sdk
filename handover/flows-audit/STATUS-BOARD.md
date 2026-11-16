UPDATED_UTC: 2026-11-16T17:05:52Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 3.16 load of 4 cores, mem 1/15 GB, RAM 1407/16087 MB, disk 11G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify arriving reports; next: Q31 r21, RW/CT r25, plan-files r30, patch-copies r12, REVIEW.md r37, F8 evidence
PUSHED_UTC: 2026-11-16T17:05:52Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:20Z | running | run_all.sh intermittency work |
| a1e95c64 | patch-copies r12 fixer | sonnet | README/DEAD-MAN-CHECK from 2 reviews (uncapped) | 17:00Z | 17:25Z | running | editing |
| a07fa885 | FINDINGS/LEDGER r15 reader | sonnet | stranger read of unread rows + r14 edits | 17:03Z | 17:13Z | running | reading |
| afc328f8 | Q31 r21 fixer | sonnet | 7 Majors from reader r20 | 17:04Z | 17:25Z | running | editing |
| a4a76fb0 | REVIEW.md r36 design review | sonnet | design review (uncapped) | 17:04Z | 17:15Z | running | reading |
| a7264848 | REVIEW.md r36 stranger read | sonnet | full read incl. lines 559-644 (uncapped) | 17:04Z | 17:15Z | running | reading |
| a772f35a | RW/CT r25 fixer | sonnet | 8 Majors from reader r24 | 17:05Z | 17:25Z | running | editing |
| a0a16684 | plan-files r30 fixer | sonnet | 8 Majors + stray fragment from reader r29 | 17:06Z | 17:25Z | running | editing |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify Q31 r21, launch round 22 reader
2 verify RW/CT r25, launch round 26 reader
3 verify plan-files r30, launch round 31 reader
4 patch-copies r12: verify, citation checker; REVIEW.md r37 fixer after design+reader reports (plus 3 citation caveats)
5 F8 evidence runner after acf8ab59 reports

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

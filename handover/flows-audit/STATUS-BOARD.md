UPDATED_UTC: 2026-11-16T17:54:37Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.89 load of 4 cores, mem 1/15 GB, RAM 1398/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: Q31 fixer after read; REVIEW.md r41 verify; patch-copies r16 verify
PUSHED_UTC: 2026-11-16T17:54:37Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 18:00Z | running | run_all.sh intermittent exit 1, cause unknown; running 2h |
| a0fef7e3 | patch-copies r16 fixer | sonnet | 4 Majors + 8 Nits (uncapped) | 17:46Z | 18:10Z | running | editing README/DEAD-MAN-CHECK |
| a0d9069a | FINDINGS/LEDGER r20 fixer | sonnet | r20/r21a/r21b findings | 17:47Z | 18:15Z | running | editing FINDINGS/LEDGER |
| a37a1cd3 | Q31 r27 stranger read | sonnet | QUESTIONS 420-737 | 17:48Z | 18:00Z | running | reading |
| a4c8e047 | plan-files r34 stranger read | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 17:52Z | 18:05Z | running | reading |
| a0f5ba85 | plan-files r34 shell read | sonnet | command blocks vs take_check.sh | 17:52Z | 18:05Z | running | reading |
| ad3348bd | RW/CT r33 stranger read | sonnet | RUNSHEET-WORDING/CLAIMS-TABLE | 17:52Z | 18:05Z | running | reading |
| a485bdf2 | REVIEW.md r41 fixer | sonnet | r35/r35 design/r35b/citation findings (uncapped) | 17:53Z | 18:20Z | running | editing REVIEW.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Q31 fixer after r27 read (plus NQ-A..NQ-F and plan-files questions)
2. Verify and re-read REVIEW.md after r41 fixer (count_review 28/4/13/11)
3. Verify patch-copies r16 fixer then r17 readers (sha 64fdf315 e7ff677e ca4982eb)
4. F8 r11 report then evidence runner alone
5. Plan-files / RW-CT fixers after r34/r33 reads

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

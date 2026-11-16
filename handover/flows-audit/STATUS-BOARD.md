UPDATED_UTC: 2026-11-16T17:19:27Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 1.71 load of 4 cores, mem 1/15 GB, RAM 1360/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 8 of 8 running; load 1.7 of 4 cores is under the 70-85 percent target because most agents are read-only reviewers; ITEMS_OPEN 30, 70 percent = 7 of 10 verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T17:19:27Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:35Z | running | run_all.sh intermittency work |
| a3f55414 | RW/CT r29 fixer | sonnet | 9 findings from reader r28 | 17:15Z | 17:35Z | running | editing RW/CT |
| aa00a4e5 | FINDINGS/LEDGER r17 reader | sonnet | stranger read of unread rows | 17:15Z | 17:30Z | running | reading |
| a323882c | plan-files r32 fixer | sonnet | 10 Majors from reader r31 + check 13 | 17:16Z | 17:40Z | running | editing RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a635dbef | REVIEW.md r38 design review | sonnet | design review, whole file (uncapped) | 17:17Z | 17:32Z | running | reading |
| a0d0612a | REVIEW.md r38 stranger read | sonnet | full read (uncapped) | 17:17Z | 17:32Z | running | reading |
| a63c2e9d | patch-copies r14 reader | sonnet | stranger read README+DEAD-MAN-CHECK (uncapped) | 17:18Z | 17:30Z | running | reading |
| a6addcb1 | QUESTIONS glossary fixer | sonnet | rows above line 420 to match Q31 | 17:18Z | 17:30Z | running | editing QUESTIONS.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Verify RW/CT r29 fixer report with checkers; then fresh RW/CT reader
2. REVIEW.md r38 design + reader reports: save, one uncapped r39 fixer; then citation checker
3. Glossary fixer report: verify Q31 section unchanged; then Q31 r24 reader
4. Patch-copies r14 and FINDINGS r17 reader reports: save, fixers
5. Plan-files r32 and F8 r11 reports: verify, fresh reviews; evidence runner for F8 alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

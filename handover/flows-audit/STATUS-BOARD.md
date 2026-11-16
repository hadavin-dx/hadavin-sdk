UPDATED_UTC: 2026-11-16T15:27:00Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 9
CAPACITY: 3.93 load of 4 cores, mem 1/15 GB, RAM 1359/16087 MB, disk 13G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T15:27:00Z

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
| a419eeb7 | evidence runner | sonnet | F8 flow-check final-head evidence | 15:10Z | 15:40Z | running | raw logs in flow-check/raw |
| a086c2de | fixer | sonnet | RW/CT round 16 (3 Blockers, 7 Majors, CT majors) | 15:22Z | 15:50Z | running | none yet |
| a140c86b | citation checker | sonnet | REVIEW.md remaining cites and counts | 15:22Z | 15:40Z | running | none yet |
| a651ae66 | fixer | sonnet | Q31 round 8 (9+6 Majors, new item DB_GRANTS) | 15:24Z | 15:50Z | running | none yet |
| a49a0a01 | fixer | sonnet | REVIEW.md round 24 (15 Majors, uncapped) | 15:24Z | 15:55Z | running | none yet |
| adac1573 | reader | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST round 21 | 15:26Z | 15:45Z | running | none yet |
| a0f9a9fa | code reviewer | sonnet | patch-copies code round 5 (uncapped) | 15:26Z | 15:45Z | running | none yet |
| a4c9b876 | reader | sonnet | patch-copies stranger read | 15:26Z | 15:45Z | running | none yet |
| a4707d80 | fixer | sonnet | FINDINGS/LEDGER round 5 (13 Majors) | 15:27Z | 15:55Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 F8 round 11 fixer (after a419eeb): review-f8-r10 M1-M5 and tests F1-F12
2 RW/CT fresh round 10 reader after a086c2d
3 Q31 round 9 reader after a651ae6
4 REVIEW.md round 25 reviewers after a49a0a0
5 FINDINGS/LEDGER round 5 reader after a4707d8

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

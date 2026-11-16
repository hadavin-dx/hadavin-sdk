UPDATED_UTC: 2026-11-16T15:38:30Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.72 load of 4 cores, mem 1/15 GB, RAM 1378/16087 MB, disk 8.4G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 17G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T15:38:30Z

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
| a419eeb7 | F8 evidence runner, final head | sonnet | run flow-check suite alone, save raw output | 15:10Z | 15:50Z | running | raw/* rewritten |
| a686df56 | patch-copies round 5 fixer | sonnet | fix 3 Majors + 7 reader Majors | 15:29Z | 15:50Z | running | none yet |
| a8c5404d | plan-files round 21 fixer | sonnet | fix 22 findings in RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 15:33Z | 16:00Z | running | none yet |
| ad333466 | Q31 round 9 fixer | sonnet | fix 2 Blockers + 11 Majors in QUESTIONS Q31 | 15:35Z | 16:00Z | running | none yet |
| aa0d1f51 | FINDINGS/LEDGER round 6 fixer | sonnet | fix 2 Blockers + 9 Majors | 15:36Z | 16:00Z | running | none yet |
| a056f463 | RW/CT round 10 fixer | sonnet | fix 4 Blockers + 8 Majors | 15:37Z | 16:05Z | running | none yet |
| a548f03c | citation checker REVIEW.md | sonnet | check cites/numbers in REVIEW.md rows | 15:37Z | 15:50Z | running | none yet |
| ad98d89f | REVIEW.md round 25 fixer | sonnet | fix 14 Majors (uncapped) | 15:38Z | 16:05Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 F8 round 11 fixer (after a419eeb): review-f8-r10 M1-M5 and tests F1-F12
2 Fresh plan-files round 22 stranger read (after a8c5404)
3 Patch-copies round 6 code + reader (after a686df5)
4 Q31 round 10 fresh reader (after ad33346)
5 RW/CT round 11 + FINDINGS/LEDGER round 6 fresh readers (after fixers)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

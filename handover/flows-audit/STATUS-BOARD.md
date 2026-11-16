UPDATED_UTC: 2026-11-16T15:33:46Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 9
CAPACITY: 7.87 load of 4 cores, mem 1/15 GB, RAM 1934/16087 MB, disk 11G free of 252G, top3 522M /tmp/tmp.4gOIkjhGSB 586M /tmp/pytest-of-root 15G /tmp/claude-0 , agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T15:33:46Z

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
| a419eeb7 | F8 evidence runner, final head | sonnet | run flow-check suite alone, save raw output | 15:10Z | 15:45Z | running | raw/* rewritten |
| a60b7859 | Q31 round 9 reader | sonnet | lead-readability of QUESTIONS Q31 | 15:29Z | 15:42Z | running | none yet |
| a686df56 | patch-copies round 5 fixer | sonnet | fix 3 Majors + 7 reader Majors | 15:29Z | 15:50Z | running | none yet |
| aa5fa670 | RW/CT round 10 reader | sonnet | stranger read of claims table + run sheet | 15:31Z | 15:43Z | running | none yet |
| a7c0d07e | FINDINGS/LEDGER round 5 reader | sonnet | fresh read of 45 rows | 15:31Z | 15:43Z | running | none yet |
| a222f11b | Q31 items A-E + F-003 patch fixer | sonnet | add 5 items, fix patch sentence | 15:31Z | 15:45Z | running | none yet |
| a8c5404d | plan-files round 21 fixer | sonnet | fix 22 findings (B1,B2,M1-M20) in RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 15:33Z | 16:00Z | running | none yet |
| af02fb4a | REVIEW.md round 25 reader | sonnet | stranger read, uncapped | 15:33Z | 15:45Z | running | none yet |
| a4d3b786 | REVIEW.md round 25 design | sonnet | least-privilege/design review, uncapped | 15:33Z | 15:48Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 F8 round 11 fixer (after a419eeb): review-f8-r10 M1-M5 and tests F1-F12
2 Fresh stranger read of plan files round 22 (after a8c5404 fix)
3 Patch-copies round 6 code + reader (after a686df5)
4 Q31 fix batch if a60b785 finds Blockers/Majors
5 RW/CT batch fixer if aa5fa67 finds Blockers/Majors

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

UPDATED_UTC: 2026-11-16T14:50:34Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.49 load of 4 cores, mem 1/15 GB, RAM 1350/16087 MB, disk 20G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 7.4G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T14:50:34Z

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
| abfcd0a | fixer F8 r9 (uncapped) | sonnet | take_check/run_all fixes, secret hit, second-angle Majors | 13:55Z | 15:30Z | running | WIP raw files |
| a7111608 | fixer patch-copies r2 (uncapped) | sonnet | B1 pass rule, recipe, dead-man hardening | 14:47Z | 15:20Z | running | none yet |
| ad15e024 | fixer plan files r17 | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST 6 Majors | 14:50Z | 15:15Z | running | none yet |
| a612be1f | fixer RW r7 + claims r6 | sonnet | 9 + 14 Majors, counts | 14:50Z | 15:20Z | running | none yet |
| ad4db551 | fixer REVIEW.md r21 (uncapped) | sonnet | 7 Majors design + cite minors | 14:50Z | 15:30Z | running | none yet |
| a0d8ae8e | reader Q31 round 5 | sonnet | Blockers/Majors only | 14:50Z | 15:05Z | running | none yet |
| a3108330 | reader plan files unread parts | sonnet | RUNBOOK 1-62, steps 1-10, FIX-PLAN 1-77, TC 1-138 | 14:51Z | 15:10Z | running | none yet |
| a87611f6 | checker T19-T21 text and R6 awk | sonnet | FINDINGS vs step 18 | 14:51Z | 15:10Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. F8 evidence runner + fresh uncapped review after abfcd0a (check_secrets PASS, run_all exit code)
2. Fresh uncapped patch-copies review after a7111608
3. Round 22 REVIEW.md reviewers if Blockers/Majors remain
4. Independent verification of fixer edits (checkers, claims-count, clock diff)
5. drift-007 refresh and grep of trigger words before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

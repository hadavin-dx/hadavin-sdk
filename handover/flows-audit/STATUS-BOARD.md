UPDATED_UTC: 2026-11-16T14:55:22Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.58 load of 4 cores, mem 1/15 GB, RAM 1340/16087 MB, disk 20G free of 252G, top3 284M /tmp/fresh19 345M /tmp/e7m 7.6G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T14:55:22Z

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
| abfcd0a3 | fixer F8 r9 (uncapped) | sonnet | take_check/run_all fixes, secret hit, second-angle Majors | 13:55Z | 15:30Z | running | WIP raw files |
| a7111608 | fixer patch-copies r2 (uncapped) | sonnet | B1 pass rule, recipe, dead-man hardening | 14:47Z | 15:20Z | running | none yet |
| ad15e024 | fixer plan files r17+r18+T19-T21 | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST/FINDINGS/LEDGER Majors | 14:50Z | 15:25Z | running | none yet |
| a612be1f | fixer RW r7 + claims r6 | sonnet | 9 + 14 Majors, counts | 14:50Z | 15:20Z | running | none yet |
| abd7b921 | fixer Q31 r5 + citation | sonnet | 6 + 3 findings | 14:54Z | 15:20Z | running | none yet |
| a21e04bb | citation checker claims Table 1 | sonnet | rows 1-86 | 14:55Z | 15:15Z | running | none yet |
| a306b770 | reviewer REVIEW.md r22 design (uncapped) | sonnet | new X-6.9, criterion 9, k1b row | 14:56Z | 15:15Z | running | none yet |
| a39c4cb9 | reviewer REVIEW.md r22 studio-head read | sonnet | decisions readable | 14:56Z | 15:15Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. F8 evidence runner + fresh uncapped review after abfcd0a (check_secrets, run_all exit code)
2. Fresh uncapped patch-copies review after a7111608
3. Verify plan-file, RW/claims and Q31 fixer edits with checkers; round 18+ readers
4. REVIEW.md round 23 only if Blockers/Majors remain
5. drift-007 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

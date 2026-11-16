UPDATED_UTC: 2026-11-16T15:05:06Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 9
CAPACITY: 2.72 load of 4 cores, mem 1/15 GB, RAM 1374/16087 MB, disk 17G free of 252G, top3 345M /tmp/e7m 422M /tmp/tmp.SjFcfMab07 9.5G /tmp/claude-0 , agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T15:05:06Z

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
| abfcd0a3 | fixer F8 r9 (uncapped) | sonnet | flow-check fixes, secret-check false positive | 13:55Z | 15:20Z | WORKING | log flow-check/fix-f8-r9.md |
| a9a70bf1 | fixer REVIEW.md r22 (uncapped) | sonnet | REVIEW.md reports r22 | 14:58Z | 15:30Z | WORKING | log fix-review15.md |
| a1089b6e | reader Q31 round 6 (lead read) | sonnet | QUESTIONS.md Q31 | 15:01Z | 15:15Z | WORKING | report pending |
| aa1b7a5d | fixer plan files r19 | sonnet | RUNBOOK, FIX-PLAN, TAKE-CHECKLIST | 15:03Z | 15:30Z | WORKING | log reviews/fix-tcfp14.md |
| a94cd3cf | fixer patch-copies r3 (uncapped) | sonnet | patch-copies README, DEAD-MAN-CHECK | 15:03Z | 15:30Z | WORKING | log fix-patchcopies3.md |
| a4276e8b | reader FINDINGS/LEDGER consistency | sonnet | FINDINGS, LEDGER-ROWS | 15:04Z | 15:15Z | WORKING | report pending |
| abfa80a0 | citation check remaining CLAIMS rows | sonnet | CLAIMS-TABLE | 15:04Z | 15:15Z | WORKING | report pending |
| ab79617b | reader RW round 8 | sonnet | RUNSHEET-WORDING | 15:04Z | 15:15Z | WORKING | report pending |
| a882098d | reader claims round 7 | sonnet | CLAIMS-TABLE | 15:04Z | 15:15Z | WORKING | report pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
F8 evidence runner plus fresh uncapped review after abfcd0a
Fix batch for Q31 round 6 plus items 80/81 wording and item 6 stale sentence
Verify plan-file and patch-copies fixer edits; fresh uncapped patch-copies round 4
REVIEW.md round 23 uncapped reviewers only if Blockers/Majors remain
drift-007 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

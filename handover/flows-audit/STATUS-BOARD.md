UPDATED_UTC: 2026-11-16T14:59:44Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.86 load of 4 cores, mem 1/15 GB, RAM 1108/16087 MB, disk 19G free of 252G, top3 345M /tmp/e7m 422M /tmp/tmp.SjFcfMab07 8.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T14:59:44Z

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
| a612be1f | fixer RW r7 + claims r6 + lane A cites | sonnet | RUNSHEET-WORDING, CLAIMS-TABLE | 14:35Z | 15:20Z | WORKING | log fix-rswording14.md |
| a21312d7 | fixer Q31 items 78+ | sonnet | QUESTIONS.md Q31 new items | 14:50Z | 15:15Z | WORKING | log fix-q31-6.md |
| a9a70bf1 | fixer REVIEW.md r22 (uncapped) | sonnet | REVIEW.md reports r22 | 14:58Z | 15:30Z | WORKING | log fix-review15.md |
| a8befc8f | reader plan files r19 operator | sonnet | FIX-PLAN/RUNBOOK/TAKE-CHECKLIST | 14:52Z | 15:10Z | WORKING | report pending |
| a43d060d | reader plan files r19 consistency | sonnet | same files | 14:52Z | 15:10Z | WORKING | report pending |
| a6d42fe2 | reviewer patch-copies r3 code (uncapped) | sonnet | patch-copies | 15:00Z | 15:15Z | WORKING | report pending |
| afbad58d | reviewer patch-copies r3 reader (uncapped) | sonnet | patch-copies | 15:00Z | 15:15Z | WORKING | report pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
F8 evidence runner plus fresh uncapped review after abfcd0a
Verify plan-file, RW/claims and Q31 fixer edits with own commands
Claims round 7 and RW round 8 readers (Blockers/Majors) after a612be1
REVIEW.md round 23 uncapped reviewers only if Blockers/Majors remain
drift-007 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

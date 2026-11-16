UPDATED_UTC: 2026-11-16T14:33:55Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.79 load of 4 cores, mem 1/15 GB, RAM 1125/16087 MB, disk 23G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 4.4G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: REVIEW.md r20 readers; F8 evidence; CT sync; Q31 items
PUSHED_UTC: 2026-11-16T14:33:55Z

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
| abfcd0a | F8 r9 fixer (uncapped) | sonnet | check_secrets hit in flow-check, tests, --strict docs | 13:55Z | 14:50Z | running | log flow-check/fix-f8-r9.md |
| aadd3a4 | Q31 round 3 lead read | sonnet | index, defaults, counts | 14:30Z | 14:45Z | running | none yet |
| a74dc08 | CITATION CHECKER Q31 | sonnet | Q31 cites to other files | 14:31Z | 14:45Z | running | reviews/citation-r15-q31.md pending |
| ad4b390 | REVIEW.md r20 design review (uncapped) | sonnet | rating rule, decisions, identity table | 14:32Z | 14:50Z | running | none yet |
| a0ac58a | CLAIMS fixer r14 | sonnet | 5 Majors of design-angle read | 14:33Z | 14:50Z | running | log fix-claims14.md |
| a1e940f | patch-copies fixer (uncapped) | sonnet | README, DEAD-MAN-CHECK, A-01, C-01 findings | 14:35Z | 14:55Z | running | log fix-patchcopies1.md |
| a5d690e | RW fixer r12 | sonnet | 9 Majors of RW r5 read | 14:37Z | 14:55Z | running | log fix-rswording12.md |
| aa375d4 | plan files stranger read r16 | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 14:37Z | 14:50Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md round 20 reader + codebase reviews after the design review (uncapped)
2. F8 r9 evidence runner + fresh uncapped review after abfcd0a (run_all.sh rc 1 and check_secrets FAIL still open)
3. Sync CLAIMS-TABLE with RW string changes (SYNC LIST from fix-rswording12.md) after a0ac58a and a5d690e
4. Fix Q31 r3 and r16 plan-file reader findings; QUESTIONS items for 5 BLOCKED inputs of fix-tcfp11 (report files, I24, 4a text time, post-twice branch time, answer-by table)
5. Post-twice script review (waits on lead: Q29-4)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

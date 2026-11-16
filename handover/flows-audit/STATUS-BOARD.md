UPDATED_UTC: 2026-11-16T14:37:43Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.56 load of 4 cores, mem 1/15 GB, RAM 1326/16087 MB, disk 22G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 5.3G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T14:37:43Z

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
| abfcd0a | F8 fixer r9 (uncapped) | sonnet | check_secrets hit, run_all.sh exit 1 | 13:55Z | 14:50Z | running | fix-f8-r9.md in progress |
| a0ac58a | claims fixer r14 + RW sync list | sonnet | 5 round-4 Majors, then sync 4 paste strings | 14:20Z | 14:50Z | running | fix-claims14.md in progress |
| a1e940f | patch-copies fixer (uncapped) | sonnet | B1-B3, M4-M8 | 14:15Z | 14:50Z | running | fix-patchcopies1.md in progress |
| af6612a | Q31 fixer round 3 + new items | sonnet | round-3 Majors, 5 new items, r16 items | 14:20Z | 14:50Z | running | fix-q31-3.md in progress |
| aea5829 | plan files fixer r16 | sonnet | 6 Majors of stranger read r16 | 14:37Z | 15:00Z | running | fix-tcfp12.md in progress |
| ac6c38b | REVIEW.md r20 fixer (uncapped) | sonnet | design r20 M1-M6, reader r20 B1+M2-M7, roles premise | 14:38Z | 15:10Z | running | fix-review13.md in progress |
| a65a6e1 | RW round 6 reader | sonnet | stranger read RUNSHEET-WORDING | 14:39Z | 14:55Z | running | report pending |
| af835e9 | citation checker RW sections 3+ | sonnet | cites in RW rows | 14:39Z | 14:55Z | running | reviews/citation-r17-rw3.md pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Save and fix r6 RW read findings (after a65a6e1)
2. F8 evidence runner on final head plus fresh uncapped review (after abfcd0a)
3. Fresh REVIEW.md round 21 review (after ac6c38b)
4. Fresh Q31 round 4 read, Blockers/Majors (after af6612a)
5. Fresh claims read after sync (after a0ac58a)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

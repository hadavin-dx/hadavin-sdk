UPDATED_UTC: 2026-11-16T16:09:40Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.72 load of 4 cores, mem 1/15 GB, RAM 1353/16087 MB, disk 17G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 7.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: disk 17G free (57%); percent basis: 70 = 7 of 10 items verified by independent check, none closed since 13:59Z, open 30; patch-copies code r8 saved (2 Majors)
PUSHED_UTC: 2026-11-16T16:09:40Z

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
| acf8ab59 | F8 round 11 fixer (uncapped) | sonnet | flow-check fixes | 15:48Z | 16:48Z | running | run_all.sh intermittency work |
| a15c1de2 | plan-files round 22 fixer | sonnet | FIX-PLAN/TAKE-CHECKLIST/RUNBOOK fixes (r15 reader M1-M4) | 15:54Z | 16:54Z | running | edits pending |
| a00c2f81 | patch-copies citation checker | sonnet | cite check README/DEAD-MAN | 16:05Z | 16:35Z | running | none yet |
| a63eb0e0 | Q31 round 13 fixer | sonnet | front page, reader r12 M1-M12, new items | 16:07Z | 17:07Z | running | edits pending |
| aedc0abd | REVIEW.md r28 design reviewer | sonnet | uncapped design review | 16:07Z | 16:27Z | running | none yet |
| a4d708eb | FINDINGS/LEDGER round 9 fixer | sonnet | reader r8 B1-B2/M1-M5 | 16:08Z | 16:38Z | running | edits pending |
| aa300770 | RW/CT round 14 stranger reader | sonnet | confirm round-13 fixes | 16:08Z | 16:28Z | running | none yet |
| a558a4d5 | REVIEW.md r28 stranger reader | sonnet | uncapped reader lane | 16:10Z | 16:30Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 patch-copies: one fixer for stranger r8 + code r8 + citation, then round 9 reviews
2 REVIEW.md r28: one fixer for design+reader+citation lanes
3 Q31 round 13 fixed: verify totals, fresh reader
4 FINDINGS/LEDGER r9 verify (45 rows 5/5/35), fresh reader
5 F8 evidence runner alone after acf8ab5

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

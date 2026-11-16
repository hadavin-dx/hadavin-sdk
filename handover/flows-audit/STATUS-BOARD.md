UPDATED_UTC: 2026-11-16T16:03:53Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.05 load of 4 cores, mem 1/15 GB, RAM 1418/16087 MB, disk 17G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 7.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: free 17G (56%); percent basis: 70 = 7 of 10 items verified by an independent check, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T16:03:53Z

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
| acf8ab59 | F8 fixer r11 | sonnet | run_all.sh intermittency, M1-M5; rename selftest string | 15:20Z | 16:30Z | WORKING | flow-check edits (unverified) |
| a15c1de2 | plan-files fixer r22 | sonnet | awk fix, clock, Q31 renumber | 15:45Z | 16:20Z | WORKING | - |
| ac32136a | REVIEW.md fixer r27 | sonnet | design/reader/citation fixes | 15:56Z | 16:40Z | WORKING | - |
| a1fc616a | RW/CT fixer r13 | sonnet | reader r12 B1-B2, M3-M19 | 15:59Z | 16:30Z | WORKING | - |
| a594abf3 | Q31 stranger reader r12 | sonnet | Blockers/Majors | 16:01Z | 16:15Z | WORKING | - |
| afe4a47b | patch-copies code reviewer r8 | sonnet | uncapped accuracy | 16:03Z | 16:20Z | WORKING | - |
| a4ec6f66 | FINDINGS/LEDGER stranger r8 | sonnet | Blockers/Majors | 16:03Z | 16:15Z | WORKING | - |
| a0dfe647 | patch-copies stranger r8 | sonnet | uncapped | 16:03Z | 16:15Z | WORKING | - |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 Q31 fixer r13: add plain critical-few front page (proposal) after reader a594abf and zoom-out q31-zoomout-r1
2 REVIEW.md round 28 reviewers (reader, design, citation) after ac32136
3 F8 fresh evidence runner alone, then uncapped reviews, after acf8ab5
4 plan-files round 23 stranger read after a15c1de
5 RW/CT round 14 reader after a1fc616

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

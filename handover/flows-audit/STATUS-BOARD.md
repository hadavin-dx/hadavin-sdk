UPDATED_UTC: 2026-11-16T15:58:28Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 1.72 load of 4 cores, mem 1/15 GB, RAM 1375/16087 MB, disk 18G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 7.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: disk freed ~9.4 GB regenerable scratch earlier; free 18G (55%). Percent basis: 70 = 7 of 10 items verified by an independent check; none closed since 13:59Z; open 30.
PUSHED_UTC: 2026-11-16T15:58:28Z

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
| acf8ab59 | F8 fixer r11 | sonnet | run_all.sh intermittency, M1-M5 | 15:20Z | 16:30Z | WORKING | flow-check/run_all.sh edits, expected-counts.pin (unverified) |
| a99ca468 | RW/CT reader r12 | sonnet | stranger read | 15:40Z | 16:10Z | WORKING | - |
| a15c1de2 | plan-files fixer r22 | sonnet | awk fix, clock, Q31 renumber | 15:45Z | 16:20Z | WORKING | - |
| ad3f3fec | patch-copies fixer r7 | sonnet | bandit group, verdict -rfE, contradiction | 15:56Z | 16:25Z | WORKING | - |
| ac32136a | REVIEW.md fixer r27 | sonnet | design/reader/citation fixes | 15:56Z | 16:40Z | WORKING | - |
| a07a9cb4 | Q31 fixer r12 | sonnet | totals 104/96, item 50, readability M1-M6 | 15:58Z | 16:25Z | WORKING | - |
| a64f2d28 | FINDINGS/LEDGER fixer r8 | sonnet | deadlines, runners, terms | 15:58Z | 16:20Z | WORKING | - |
| a36d9924 | drift-007 refresh checker | sonnet | read-only drift-007-r2 | 15:58Z | 16:20Z | WORKING | - |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 Citation fix pass on CLAIMS-TABLE soft rows 51,54 (after RW/CT reader r12)
2 patch-copies round 8 reviews (code + stranger), uncapped, after ad3f3fe
3 REVIEW.md round 28 reviewers (reader, design, citation), after ac32136
4 F8 fresh evidence runner alone, then uncapped reviews, after acf8ab5
5 plan-files round 23 stranger read, after a15c1de

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

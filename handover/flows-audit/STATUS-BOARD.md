UPDATED_UTC: 2026-11-16T16:25:34Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 3.75 load of 4 cores, mem 1/15 GB, RAM 1535/16087 MB, disk 16G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 8.4G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: next5 in /tmp/gen7/next5.txt; disk 16G free 60%; percent basis 70 = 7 of 10 independently verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T16:25:34Z

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
| acf8ab59 | fixer | sonnet | F8 flow-check round 11 (uncapped) | 15:48Z | 16:40Z | running | edits in flow-check/ |
| a18f1c8d | fixer | sonnet | plan files round 24 | 16:18Z | 16:40Z | running | edits in RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a026f1e0 | fixer | sonnet | FINDINGS/LEDGER round 10 | 16:18Z | 16:40Z | running | edits in FINDINGS/LEDGER-ROWS |
| a3917020 | reader | sonnet | RW/CT round 16 stranger read | 16:23Z | 16:35Z | running | findings inline |
| a13847b9 | reader | sonnet | REVIEW.md r30 stranger read (uncapped) | 16:23Z | 16:40Z | running | findings inline |
| a075caf1 | reviewer | sonnet | REVIEW.md r30 design review (uncapped) | 16:23Z | 16:40Z | running | findings inline |
| ad24e61d | reader | sonnet | Q31 round 15 stranger read | 16:25Z | 16:40Z | running | findings inline |
| aae2f4ca | fixer | sonnet | patch-copies round 10 (uncapped) | 16:25Z | 16:45Z | running | edits in patch-copies/ |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 REVIEW.md r30 citation checker; 2 RW/CT round 16 fixer (incl. row (t) cite line 268); 3 F8 evidence runner then reviews; 4 FINDINGS/LEDGER round 10 reader; 5 patch-copies round 10 readers

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

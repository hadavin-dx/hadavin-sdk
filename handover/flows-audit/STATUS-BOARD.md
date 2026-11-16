UPDATED_UTC: 2026-11-16T16:15:28Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.79 load of 4 cores, mem 1/15 GB, RAM 1511/16087 MB, disk 17G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 7.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: disk 17G free (56%); percent basis: 70 = 7 of 10 items verified by independent check, none closed since 13:59Z, open 30; fixers: 4 running, readers/checkers 4
PUSHED_UTC: 2026-11-16T16:15:28Z

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
| adf9bee4 | patch-copies round 9 fixer (uncapped) | sonnet | README/DEAD-MAN from 3 reports | 16:11Z | 16:41Z | running | edits pending |
| a7188515 | RW/CT round 15 fixer | sonnet | 12 Majors of reader r14 | 16:12Z | 16:42Z | running | edits pending |
| af2eac9a | plan-files round 23 stranger reader | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 16:12Z | 16:32Z | running | none yet |
| a81f425a | REVIEW.md round 29 fixer (uncapped) | sonnet | design r28 + reader r28 + citation r28 | 16:13Z | 16:43Z | running | edits pending |
| a52f846c | Q31 round 14 stranger reader | sonnet | QUESTIONS.md Q31 | 16:14Z | 16:34Z | running | none yet |
| a61a8f40 | Q31 citation checker r14 | sonnet | cites/times/counts | 16:15Z | 16:35Z | running | none yet |
| a4d8461a | FINDINGS/LEDGER round 9 reader | sonnet | stranger read of both files | 16:15Z | 16:35Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 patch-copies round 9 fresh uncapped reviews (stranger, code, citation) after adf9bee
2 F8 fresh evidence runner alone plus uncapped reviews after acf8ab5
3 RW/CT round 15 verify then fresh reader
4 REVIEW.md fresh round 29 reader and design after a81f425
5 Q31 fixer for reader r14 plus citation r14; FINDINGS/LEDGER fixer if reader finds Majors

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

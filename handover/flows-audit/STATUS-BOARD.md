UPDATED_UTC: 2026-11-16T19:56:04Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 3.87 load of 4 cores, mem 1/15 GB, RAM 1138/16087 MB, disk 19G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 4.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5
PUSHED_UTC: 2026-11-16T19:56:04Z

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
| a7636841 | F8 fixer r13 (HEAVY only while it runs tests; one at a time) | sonnet | fix F8 review findings | 19:50Z | 20:50Z | running | checkpoint-f8-r13.md |
| a8200900 | FINDINGS/LEDGER r32 fixer | sonnet | fix 28 Majors, cell diff | 19:54Z | 20:34Z | running | none yet |
| a921f079 | patch-copies README 31-329 reader (uncapped) | sonnet | stranger read | 19:54Z | 20:09Z | running | none yet |
| a3210afe | TAKE-CHECKLIST 200-514 reader | sonnet | stranger read | 19:54Z | 20:09Z | running | none yet |
| a03377cd | CLAIMS-TABLE 21-300 reader | sonnet | stranger read | 19:57Z | 20:12Z | running | none yet |
| aaf24a7e | REVIEW.md uncapped fixer r50-r53 | sonnet | fix 5 reader reports | 19:59Z | 20:49Z | running | none yet |
| a4cb7929 | RUNBOOK fixer r50-r54 (guard/wording only) | sonnet | fix 5 reader reports | 19:59Z | 20:49Z | running | none yet |
| a490e77f | FIX-PLAN stranger reader | sonnet | stranger read | 19:59Z | 20:14Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. patch-copies README+DEAD-MAN-CHECK uncapped fixer (after README 31-329 reader)
2. TAKE-CHECKLIST fixer (r56 + 200-514 reader) and CLAIMS-TABLE fixer (r45, r57, 21-300 reader)
3. RUNBOOK 433+ I-table reader (I7-I58 unread) and RUNBOOK 1-220 re-read after fix
4. F8 independent reviewers and evidence runner (heavy; only when load under 6)
5. Fresh reader on new Q31 text (QUESTIONS lines 420-812) and RUNSHEET-WORDING round 2

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

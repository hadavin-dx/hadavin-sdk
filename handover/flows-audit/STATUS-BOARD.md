UPDATED_UTC: 2026-11-16T16:56:14Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.70 load of 4 cores, mem 1/15 GB, RAM 1363/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 8 running (load 5.9 of 4 cores, above target; disk 12G free 72%, memory 8%); BOOT_ID e78580c0 unchanged; verified plan-files r26, RW/CT r21, REVIEW r33, FINDINGS r12, patch-copies r11; percent stays 70 (no independent close since 13:59Z)
PUSHED_UTC: 2026-11-16T16:56:14Z

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
| acf8ab59 | F8 flow-check round 11 fixer (uncapped) | sonnet | fix run_all.sh intermittency and review findings | 15:49Z | about 17:05Z | running | edits in flow-check/ |
| a02fd9cc | plan-files round 27 reader | sonnet | stranger read RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 16:49Z | about 17:03Z | running | pending |
| a9b78c66 | Q31 round 19 fixer | sonnet | fix 14 Majors from reader r18 + plan-files Q31 edits | 16:53Z | about 17:10Z | running | edits in progress |
| ae59e2df | REVIEW.md round 35 fixer (uncapped) | sonnet | fix design r34 (1 Blocker, 8 Majors) + reader r34 (6 Majors) | 16:53Z | about 17:15Z | running | edits in progress |
| af860e6b | patch-copies round 12 reader (uncapped) | sonnet | stranger read README/DEAD-MAN-CHECK | 16:53Z | about 17:08Z | running | pending |
| a7aa6e3a | patch-copies round 12 code review (uncapped) | sonnet | technical review of shell/SQL/cites | 16:53Z | about 17:08Z | running | pending |
| a5ee5a38 | FINDINGS/LEDGER round 13 reader | sonnet | stranger read of unread cells | 16:55Z | about 17:08Z | running | pending |
| a2067e2d | RW/CT round 23 fixer | sonnet | fix 9 Majors + lower items from reader r22 | 16:56Z | about 17:10Z | running | edits in progress |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Plan-files round 27: save reader, launch fixer (also align fix A for F-011 in TAKE-CHECKLIST/FIX-PLAN)
2. Q31 round 19: verify label counts, launch fresh Q31 reader
3. REVIEW.md round 35: verify counts, launch design + reader + citation (uncapped)
4. Patch-copies: save two reviews, launch one fixer, then citation checker
5. F8: evidence runner alone, then fresh uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

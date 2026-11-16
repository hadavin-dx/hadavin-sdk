UPDATED_UTC: 2026-11-16T16:51:11Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 5.67 load of 4 cores, mem 1/15 GB, RAM 1445/16087 MB, disk 11G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 7 running (8th slot empty: load about 5 of 4 cores, disk 12G free 70%); verified plan-files r26, RW/CT r21, REVIEW r33, FINDINGS r11; percent stays 70 (no independent close since 13:59Z)
PUSHED_UTC: 2026-11-16T16:51:11Z

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
| a6f19722 | patch-copies round 11 fixer (uncapped) | sonnet | fix 9 Majors README/DEAD-MAN-CHECK + secrets-checker hits | 16:43Z | about 17:10Z | running | edits in progress |
| a26c1f8a | Q31 round 18 reader | sonnet | stranger read of Q31 | 16:45Z | about 17:00Z | running | pending |
| a1c708d3 | REVIEW.md round 34 reader (uncapped) | sonnet | stranger read of REVIEW.md | 16:48Z | about 17:03Z | running | pending (design r34 saved: 1 Blocker, 8 Majors) |
| a02fd9cc | plan-files round 27 reader | sonnet | stranger read RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 16:49Z | about 17:03Z | running | pending |
| a477e500 | FINDINGS/LEDGER round 12 fixer | sonnet | fix 5 Majors from reader r12 | 16:51Z | about 17:05Z | running | edits in progress |
| ab2ca265 | RW/CT round 22 reader | sonnet | stranger read of unread RW/CT parts | 16:51Z | about 17:05Z | running | pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Q31 round 18: save reader, launch Q31 fixer (also apply plan-files NEEDS Q31 EDIT: item 51(c), item 15 time)
2. REVIEW.md round 35 fixer after reader r34 reports (one fixer, design r34 + reader r34)
3. Plan-files round 27: save reader, launch fixer
4. Patch-copies: verify fixer, then reader + code + citation (uncapped); secrets checker must PASS
5. F8: evidence runner alone, then fresh uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

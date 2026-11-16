UPDATED_UTC: 2026-11-16T18:09:55Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 3.96 load of 4 cores, mem 1/15 GB, RAM 1078/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: Q31 edit pass; F8 fixer; verify four fixers
PUSHED_UTC: 2026-11-16T18:09:55Z

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
| aeb2251e | fixer | sonnet | plan-files r34 fixes (RUNBOOK/FIX-PLAN/TAKE-CHECKLIST) | 17:5xZ | about 18:20Z | running | not yet reported |
| a55f209a | evidence runner | sonnet | F8 r11 run_all repeat runs, raw output | 18:00Z | about 18:30Z | running | not yet |
| ab3bac8b | fixer | sonnet | patch-copies r17 fixes (README, DEAD-MAN-CHECK) | 18:02Z | about 18:20Z | running | not yet |
| a2dde29a | reviewer comprehension | sonnet | Q31 r28 stranger read | 18:07Z | about 18:15Z | running | not yet |
| af88197e | fixer | sonnet | REVIEW.md r42 fixes (r36 + r37 reports) | 18:08Z | about 18:30Z | running | not yet |
| a2cb770e | reviewer comprehension | sonnet | FINDINGS/LEDGER r23 stranger read | 18:08Z | about 18:16Z | running | not yet |
| ae4cb7af | fixer | sonnet | RW/CT r34 fixes (r34 + r35 reports) | 18:09Z | about 18:25Z | running | not yet |
| ae32698a | citation checker | sonnet | cites/times in 10 re-edited FINDINGS rows | 18:09Z | about 18:20Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Q31 edit pass (r28 readers + F-011/one-database questions + item 26 path:2) after a2dde29a reports
2. F8 fixer (uncapped) after evidence runner a55f209a: reviewer r12 M1-M3
3. Verify and review plan-files, patch-copies, REVIEW.md, RW/CT fixer outputs
4. drift-007-r3 refresh before FINAL
5. Questions for lead (REVIEW.md:77 move, builder session name, second-send item)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

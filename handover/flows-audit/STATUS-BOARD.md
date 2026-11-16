UPDATED_UTC: 2026-11-16T18:04:42Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.59 load of 4 cores, mem 1/15 GB, RAM 1117/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: REVIEW.md fixer after r37; verify four fixers
PUSHED_UTC: 2026-11-16T18:04:42Z

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
| a97d5beb | fixer | sonnet | Q31 r27 fixes (QUESTIONS.md Q31) | 17:3xZ | about 18:15Z | running | not yet reported |
| aeb2251e | fixer | sonnet | plan-files r34 fixes (RUNBOOK/FIX-PLAN/TAKE-CHECKLIST) | 17:4xZ | about 18:15Z | running | not yet reported |
| a19dc1b1 | fixer | sonnet | FINDINGS/LEDGER r21 fixes | 17:4xZ | about 18:15Z | running | not yet reported |
| a55f209a | evidence runner | sonnet | F8 r11 run_all repeat runs, raw output | 18:00Z | about 18:30Z | running | not yet |
| a30cc924 | reviewer codebase-details | sonnet | F8 r12 result review of flow-check scripts | 18:03Z | about 18:12Z | running | not yet |
| ab3bac8b | fixer | sonnet | patch-copies r17 fixes (README, DEAD-MAN-CHECK) | 18:02Z | about 18:20Z | running | not yet |
| a17ff644 | reviewer comprehension | sonnet | RW/CT r34 stranger read | 18:02Z | about 18:12Z | running | not yet |
| a942d640 | reviewer design | sonnet | REVIEW.md r37 design read | 18:04Z | about 18:15Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md r36/r37 fixer (one fixer, uncapped) after r37 reports
2. Verify and review the fixers now running (Q31, plan-files, FINDINGS/LEDGER, patch-copies)
3. F8 evidence plus reviewer results then fixer
4. drift-007-r3 refresh before FINAL
5. Questions for lead (Q31 gaps: F-011/F-041, REVIEW.md:77 move)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

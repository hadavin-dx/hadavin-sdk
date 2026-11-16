UPDATED_UTC: 2026-11-16T15:50:59Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 1.44 load of 4 cores, mem 1/15 GB, RAM 1371/16087 MB, disk 8.9G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 16G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5; patch-copies r6 fix verified by me: git apply --check rc 0 on C-01, C-01-price-only, A-01 at b4cce5b; checks pass; percent 70 unchanged
PUSHED_UTC: 2026-11-16T15:50:59Z

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
| a0e9ee50 | FINDINGS/LEDGER round 7 fixer | sonnet | clocks, who runs greps, F-002 inputs; ratings unchanged | 15:44Z | 16:10Z | running | none yet |
| ab348158 | plan-files round 22 stranger read | sonnet | fresh operator read RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 15:47Z | 16:05Z | running | none yet |
| acf8ab59 | F8 round 11 fixer | sonnet | run_all.sh intermittent exit 1 (3 of 6 runs), M1-M5, F1-F12 (uncapped) | 15:48Z | 16:30Z | running | none yet |
| a207900c | RW/CT round 12 fixer | sonnet | B1-B4, M1-M5 plus 2 SOFT cites | 15:49Z | 16:15Z | running | none yet |
| a18a4e2d | Q31 round 11 fixer | sonnet | fix 11 Majors + 6 readability Majors, add 4 new items (QUESTIONS.md Q31 only) | 15:49Z | 16:15Z | running | none yet |
| afdcb78f | REVIEW.md round 26 stranger read | sonnet | fresh read of whole REVIEW.md incl. Decisions 26-29 (uncapped) | 15:50Z | 16:10Z | running | none yet |
| abb2c71f | REVIEW.md round 26 design/security review | sonnet | rating rule, least-privilege of proposed fixes, Decisions 26-29 (uncapped) | 15:51Z | 16:10Z | running | none yet |
| a55f3104 | patch-copies round 7 code review | sonnet | accuracy of README verdict script, counts, SQL rights (uncapped) | 15:52Z | 16:12Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 patch-copies round 7 stranger read of README + DEAD-MAN-CHECK (needs a free slot; second angle for ORDER 018)
2 Plan-files round 22 fixer: citation mismatches (TAKE-CHECKLIST:118, RUNBOOK:15, FIX-PLAN Step 12) + r22 stranger findings (waits on ab348158)
3 REVIEW.md round 26 citation checker (free slot)
4 FINDINGS/LEDGER round 7 fresh reader (after a0e9ee50)
5 F8 fresh evidence runner + uncapped reviews (after acf8ab59)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.

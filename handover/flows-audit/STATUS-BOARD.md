UPDATED_UTC: 2026-11-16T11:35:31Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 11
PERCENT: 95
AGENTS_RUNNING: 8
CAPACITY: 0.18 load of 4 cores, mem 0/15 GB, RAM 913/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 1.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
NEXT: 8 lanes running; verify each hand-back with checkers
PUSHED_UTC: 2026-11-16T11:35:31Z

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
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aa10943 | F8 fixer r10 | sonnet | 1 Blocker 7 Majors + ruff format | 11:42 | 12:20 | 50 | running | flow-check/fix-f8-r10.md
| a49155e | lint fixer | sonnet | 53 ruff check errors in my tools | 11:50 | 12:15 | 40 | running | fix-lint.md
| a31d0a4 | owner sheet stranger read | sonnet | comprehension read | 11:50 | 12:00 | 40 | running | (inline)
| a0c7782 | FIX-PLAN citation check | sonnet | cites and counts | 11:50 | 12:05 | 40 | running | (inline)
| a60684e | RW/CT adversarial read | sonnet | design review after Q25 | 11:55 | 12:10 | 30 | running | (inline)
| a4949e3 | TAKE-CHECKLIST fixer r2 | sonnet | 15 Majors of stranger read r2 | 11:56 | 12:10 | 30 | running | fix-checklist3.md
| a7442b7 | RUNBOOK writer | sonnet | merged order with commands, time boxes | 12:00 | 12:20 | 5 | running | fix-runbook.md
| a92c85c | contradiction fixer | sonnet | fix FIX-PLAN/REPORT/QUESTIONS | 12:01 | 12:15 | 5 | running | fix-contra1.md

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

UPDATED_UTC: 2026-11-16T11:31:26Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 9
PERCENT: 95
AGENTS_RUNNING: 3
CAPACITY: 0.73 load of 4 cores, mem 0/15 GB, RAM 878/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 1.8G /tmp/claude-0 , agents 3 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check fails on flow-check/check_flows.py and selftest.py (evidence-r9.md 5b), earlier fixer claimed clean; F8 review r10 found 1 Blocker (pin rewrite self-approves) + 7 Majors; fixer running
NEXT: F8 r10 fix, checklist, RW/CT
PUSHED_UTC: 2026-11-16T11:31:26Z

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
| a6a304a | Q25 run sheet + claims | sonnet | apply Q25 + citation Majors | 11:45 | 12:10 | 70 | running | fix-q25-rw.md
| a79ab5b | TAKE-CHECKLIST fixer | sonnet | fix 15 stranger-read items | 11:36 | 11:50 | 40 | running | fix-checklist2.md
| aa10943 | F8 fixer r10 | sonnet | 1 Blocker 7 Majors from review + ruff format | 11:42 | 12:20 | 5 | running | flow-check/fix-f8-r10.md

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

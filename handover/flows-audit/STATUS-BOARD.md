UPDATED_UTC: 2026-11-16T11:38:16Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 12
PERCENT: 55
AGENTS_RUNNING: 8
CAPACITY: 0.54 load of 4 cores, mem 0/15 GB, RAM 907/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 1.9G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
FAILED: ruff format --check on inputs/plan-wp6-resmoke-v5.md (lead-owned); check_refs unresolved CUT-LIST.md:17 (fixer running); lint fixer changed no_name.out (crash removed)
NEXT: ORDER 030: started RW/CT fixer, owner-steps fixer, FIX-PLAN cite fixer, checklist cite check, refs fixer; ruff check 0, format done for my files
PUSHED_UTC: 2026-11-16T11:38:16Z

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
| aa10943 | F8 fixer r10 | sonnet | flow-check pin/fixes | 11:00 | - | 70 | RUNNING | flow-check/fix-f8-r10.md |
| a7442b7 | RUNBOOK writer | sonnet | RUNBOOK.md | 11:20 | - | 50 | RUNNING | fix-runbook.md |
| a92c85c | contradiction fixer | sonnet | FIX-PLAN/REPORT/QUESTIONS | 11:20 | - | 70 | RUNNING | fix-contra1.md |
| a27d6c9 | RW/CT fixer | sonnet | adversarial B1-M9 | 11:40 | - | 5 | RUNNING | fix-rwct3.md |
| a36a8ea | OWNER-STEPS fixer | sonnet | stranger B1-B6 | 11:40 | - | 5 | RUNNING | fix-ownersteps3.md |
| a6439c6 | FIX-PLAN cite fixer | sonnet | 3 wrong cites | 11:40 | - | 5 | RUNNING | fix-fixplan5.md |
| a488a19 | citation check CHECKLIST | sonnet | TAKE-CHECKLIST cites | 11:41 | - | 5 | RUNNING | inline |
| ae747e0 | check_refs fixer | sonnet | CUT-LIST:17 cite | 11:41 | - | 5 | RUNNING | fix-refs.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

UPDATED_UTC: 2026-11-16T09:14:33Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 8
PERCENT: 70
AGENTS_RUNNING: 9
CAPACITY: 0.39 load of 4 cores, mem 0/15 GB, disk free 29G, agents 9 (light+heavy per list)
INTERRUPTED: none
NEXT: round 2 reviews F3, F1 fixer, F8, F9, heavy lane
PUSHED_UTC: 2026-11-16T09:14:33Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 90 | CLAIMS-TABLE.md | 2 reviews done (4 Blocker 17 Major), fixer running, then round 2 |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 85 | fill_flows/fix-f3-r1.md | 50 tests (fixer); round 2 evidence + 2 reviewers running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 80 | RUNSHEET-WORDING.md | written; naive-reader review running; redo after F1 fix |
| F6 | idle fallback | open | 0 | | not needed while queue has items |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied in F1 fixer and F5 |
| F8 | stronger JSON flow checker | running | 5 | flow-check/REPORT.md | builder started |
| F9 | scene to flow map | running | 5 | SCENE-FLOW-MAP.md | reader started |
| H1 | heavy test lane (baseline, patched) | running | 5 | heavy-test-lane/ | 2 evidence runners |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a13997f1eb4d26724 | EVIDENCE RUNNER F3 r2 | sonnet | tests, e2e, hostile, mutants | 09:16 | 09:30 | 10 | running | fill_flows/evidence-f3-r2.md |
| a4bc9f6927ac9fb69 | egm-design F3 r2 | sonnet | review round 2 | 09:16 | 09:30 | 5 | running | none |
| ae8d39dfab6305959 | egm-codebase F3 r2 | sonnet | review round 2 | 09:16 | 09:30 | 5 | running | none |
| ad7e698a4ee4826f8 | fixer F1 | sonnet | claims table batch | 09:17 | 09:35 | 5 | running | CLAIMS-TABLE.md |
| a85e4c98724541bd8 | builder F8 | sonnet | flow checker | 09:19 | 09:45 | 5 | running | flow-check/ |
| a946353fa00c94e95 | reader F9 | sonnet | scene flow map | 09:19 | 09:35 | 5 | running | SCENE-FLOW-MAP.md |
| aeeeb2c67e3c12c1c | HEAVY runner baseline | sonnet | full sdk suite b4cce5b | 09:19 | 09:45 | 5 | running | heavy-test-lane/evidence-baseline.md |
| ae5edef2fc2781814 | HEAVY runner patched | sonnet | suite with 3 patches | 09:19 | 09:45 | 5 | running | heavy-test-lane/evidence-patched.md |
| abaf92c58b1d1335f | egm-comprehension F5 | sonnet | naive reader review | 09:19 | 09:30 | 5 | running | none |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

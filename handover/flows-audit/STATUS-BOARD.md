UPDATED_UTC: 2026-11-16T09:08:16Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 4
PERCENT: 70
AGENTS_RUNNING: 3
INTERRUPTED: none
NEXT: fixers F3 and F4, claims lane B, then F1 reviewers
PUSHED_UTC: 2026-11-16T09:08:16Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table (lane A done 82 rows, lane B running) | running | 60 | lanes13/claims-A.md | then 2 reviewers |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 70 | fill_flows/resolve-f3-r1.md | 2 reviews: 15 Majors, fixer running; then round 2 |
| F4 | patch apply check | running | 80 | patch-apply/REPORT.md | round 2 found 1 false pass + 5 Majors; final fixer running |
| F5 | run-sheet wording | open | 0 | | after F1 |
| F6 | idle fallback | open | 0 | | only if queue empty |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aa12f4710cd6fb12a | claims lane B (F1) | sonnet | owner steps and docs claims (told FACTS-ALREADY-DONE) | 08:50 | 09:20 | 60 | running | lanes13/claims-B.md |
| a45f158fdb6f5d796 | fixer F3 | sonnet | fix 15 Majors, tests, README | 09:09 | 09:30 | 5 | running | fill_flows/fix-f3-r1.md |
| af7cc71941ed87a0c | fixer F4 | sonnet | stronger checker, final batch | 09:09 | 09:30 | 5 | running | patch-apply/REPORT.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

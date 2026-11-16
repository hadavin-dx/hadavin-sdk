UPDATED_UTC: 2026-11-16T09:10:33Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 4
PERCENT: 75
AGENTS_RUNNING: 5
INTERRUPTED: none
NEXT: F1 reviews, F3 and F4 fixers, F5 wording
PUSHED_UTC: 2026-11-16T09:10:33Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 85 | CLAIMS-TABLE.md (312 rows) | 2 reviewers running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 70 | fill_flows/resolve-f3-r1.md | fixer running, then round 2 |
| F4 | patch apply check | running | 80 | patch-apply/REPORT.md | final fixer running |
| F5 | run-sheet wording | running | 10 | RUNSHEET-WORDING.md | started early from the table |
| F6 | idle fallback | open | 0 | | only if queue empty |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a45f158fdb6f5d796 | fixer F3 | sonnet | fix 15 Majors, tests, README | 09:09 | 09:30 | 5 | running | fill_flows/fix-f3-r1.md |
| af7cc71941ed87a0c | fixer F4 | sonnet | stronger checker, final batch | 09:09 | 09:30 | 5 | running | patch-apply/REPORT.md |
| aa845b0544ceeec0d | egm-codebase-details F1 | sonnet | spot-check 25 rows, find missing claims | 09:12 | 09:25 | 5 | running | none |
| a4ea6ce33ec6be4f8 | egm-zoom-out F1 | sonnet | usability for the lead | 09:12 | 09:25 | 5 | running | none |
| a394c8096c96c6a63 | F5 wording | sonnet | paste-ready safe sentences | 09:11 | 09:30 | 5 | running | RUNSHEET-WORDING.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

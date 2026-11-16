UPDATED_UTC: 2026-11-16T09:04:34Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 4
PERCENT: 58
AGENTS_RUNNING: 5
INTERRUPTED: none
NEXT: collect F3 evidence and reviews, F4 fix, F1 lane B; then F1 reviewers and F5
PUSHED_UTC: 2026-11-16T09:04:34Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table (lane A done 82 rows, lane B running) | running | 55 | lanes13/claims-A.md | then 2 reviewers |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes; round 2 not run |
| F3 | fill_flows tool | running | 60 | fill_flows/ | built, 27 tests (builder); evidence + 2 reviewers running |
| F4 | patch apply check | running | 65 | patch-apply/REPORT.md | 2 reviews found Majors; fixer running |
| F5 | run-sheet wording | open | 0 | | after F1 |
| F6 | idle fallback | open | 0 | | only if queue empty |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aa12f4710cd6fb12a | claims lane B (F1) | sonnet | owner steps and docs claims | 08:50 | 09:15 | 60 | running | lanes13/claims-B.md |
| a5c6e309f6c778906 | fixer F4 | sonnet | stronger checker, not-tested section, patch orders | 09:03 | 09:25 | 15 | running | patch-apply/REPORT.md |
| a11c46f220fa89a28 | EVIDENCE RUNNER F3 | sonnet | run fill_flows tests, end-to-end, mutations | 09:04 | 09:25 | 5 | running | fill_flows/evidence-f3.md |
| a519a46e296a0d928 | egm-design F3 | sonnet | review fill_flows design | 09:04 | 09:20 | 5 | running | none |
| a0671d900adfe41ac | egm-codebase-details F3 | sonnet | review fill_flows code | 09:04 | 09:20 | 5 | running | none |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

UPDATED_UTC: 2026-11-16T09:00:41Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 6
PERCENT: 35
AGENTS_RUNNING: 4
INTERRUPTED: none
NEXT: collect F1 lane B and F2 evidence; reviewers on F3 when built; F5 after F1
PUSHED_UTC: 2026-11-16T09:00:41Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table (lane A done 82 rows, lane B running) | running | 50 | lanes13/claims-A.md | then 2 reviewers |
| F2 | core patches cross-review | running | 60 | reviews-of-core-patches/ | 2 reviews saved, evidence running |
| F3 | fill_flows tool | running | 5 | fill_flows/ | builder started 09:00 |
| F4 | patch apply check | running | 5 | patch-apply/REPORT.md | evidence runner started 09:00 |
| F5 | run-sheet wording | open | 0 | | after F1 |
| F6 | idle fallback | open | 0 | | only if queue empty |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a1b2b7ea0b42c07d2 | EVIDENCE RUNNER core patches (F2) | sonnet | pytest, ruff, bandit, before/after, mutation | 08:50 | 09:20 | 45 | running | reviews-of-core-patches/evidence-13.md |
| aa12f4710cd6fb12a | claims lane B (F1) | sonnet | owner steps and docs claims | 08:50 | 09:15 | 60 | running | lanes13/claims-B.md |
| a1ecd3b3a6d04116b | builder F3 | sonnet | fill_flows tool and tests | 09:00 | 09:35 | 5 | running | fill_flows/ |
| a35ae254de4468fcb | EVIDENCE RUNNER F4 | sonnet | apply patches, check flows | 09:00 | 09:25 | 5 | running | patch-apply/REPORT.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

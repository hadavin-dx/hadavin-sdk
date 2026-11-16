UPDATED_UTC: 2026-11-16T08:54:25Z
SESSION: flows-audit
ORDER: 013 (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 4
ITEMS_OPEN: 3
PERCENT: 30
AGENTS_RUNNING: 3
INTERRUPTED: none
NEXT: collect evidence and claims lanes; resolve; assemble CLAIMS-TABLE.md
PUSHED_UTC: 2026-11-16T08:54:25Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| 1 | Q4-Q9 answers into QUESTIONS and FIX-PLAN | done | 100 | QUESTIONS.md, FIX-PLAN.md | |
| 2 | CLAIMS-TABLE.md (2 lanes, then 2 reviewers) | running | 40 | lanes13/claims-A.md, claims-B.md | lanes write now |
| 3 | cross-review of core patches (evidence + 2 reviewers) | running | 50 | reviews-of-core-patches/ | 2 reviews saved, evidence running |
| 4 | FINAL | open | 0 | | after 2 and 3 |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a1b2b7ea0b42c07d2 | EVIDENCE RUNNER core patches | sonnet | pytest, ruff, bandit, before/after, mutation | 08:50 | 09:20 | 30 | running | reviews-of-core-patches/evidence-13.md |
| af029ef6d7b9862bf | egm-codebase-details | sonnet | review core patches | 08:50 | 09:10 | 100 | done (saved) | review-codebase-r1.md |
| a00611c4ffec5962e | egm-design | sonnet | review core patches | 08:50 | 09:10 | 100 | done (saved) | review-design-r1.md |
| a3e8a880362397411 | claims lane A | sonnet | run sheet and statements claims | 08:50 | 09:15 | 40 | running | lanes13/claims-A.md |
| aa12f4710cd6fb12a | claims lane B | sonnet | owner steps and docs claims | 08:50 | 09:15 | 40 | running | lanes13/claims-B.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.

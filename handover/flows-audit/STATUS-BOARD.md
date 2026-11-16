UPDATED_UTC: 2026-11-16T08:31:26Z
SESSION: flows-audit
ORDER: 007 (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 1
PERCENT: 80
AGENTS_RUNNING: 2
INTERRUPTED: none
NEXT: collect two reviews, egm:egm-resolve, fix, FINAL
PUSHED_UTC: 2026-11-16T08:31:26Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| 1 | patch fixes (F-001, F-002, F-004, F-008) | done | 100 | lanes7/evidence-7a.md | not run in n8n |
| 2 | re-rate by one rule, counts table | done | 90 | FINDINGS.md | awaits review |
| 3 | rung tags, BEFORE/AFTER split, CUT-LIST | done | 90 | FIX-PLAN.md | awaits review |
| 4 | verdicts, approvals, T-test, NOT-covered | done | 90 | lanes7/N7-verdicts.md | awaits review |
| 5 | new findings | done | 90 | lanes7/N7-new-findings.md | awaits review |
| 6 | two-reviewer pass, resolve, FINAL | running | 20 | none yet | round 1 of 2 |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a390bf5b8417b9bee | egm-codebase-details | sonnet | checks patches, citations | 08:29 | 08:40 | ? | running | none |
| a577d18e9204efeb3 | egm-zoom-out | sonnet | checks ratings, plan, coverage | 08:29 | 08:40 | ? | running | none |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Q3 in QUESTIONS.md (spend ledger: one exception of two files, or move into Postgres). Not blocking.

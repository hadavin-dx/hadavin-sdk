UPDATED_UTC: 2026-11-16T08:30:31Z
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
PUSHED_UTC: 2026-11-16T08:30:31Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| 1 | patch fixes F-001, F-002, F-004, F-008 | done (static, not run in n8n) | 100 | lanes7/evidence-7a.md, patches/ | F-002 repeat-key behaviour UNVERIFIED until laptop T19 |
| 2 | re-rate by one rule, counts table | done (draft, awaits review) | 90 | FINDINGS.md counts table (46 rows: 8 Blocker, 17 Major, 21 Nit) | F-022, F-025 also demoted by me: flagged |
| 3 | rung tags, BEFORE/AFTER split, CUT-LIST AFTER | done (draft, awaits review) | 90 | FIX-PLAN.md, CUT-LIST.md, FINDINGS 'when' column | |
| 4 | verdicts, approvals, T-test, NOT-covered | done (draft, awaits review) | 90 | lanes7/N7-verdicts.md, FINDINGS F-042, F-043 | |
| 5 | new findings | done (draft, awaits review) | 90 | lanes7/N7-new-findings.md, FINDINGS F-035 to F-046, EXCEPTIONS.md | Q3 for the lead |
| 6 | two-reviewer pass, resolve, FINAL | running (round 1) | 0 | | max 2 rounds |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| acdf03c72e2add6e0 | static reviewer item 5 | sonnet | 7 new findings | 08:20 | 08:26 | 100 | done | lanes7/N7-new-findings.md |
| a1cacfb2ad5a2e005 | static reviewer item 4 | sonnet | verdicts, approvals, T-tests | 08:20 | 08:26 | 100 | done | lanes7/N7-verdicts.md |
| a390bf5b8417b9bee | egm-codebase-details reviewer | sonnet | checks patches and cited facts against source | 08:29 | +10 min | ? | running | none yet |
| a577d18e9204efeb3 | egm-zoom-out reviewer | sonnet | checks rating rule, plan split, coverage of ORDER 007 | 08:29 | +10 min | ? | running | none yet |

## LOST OR INTERRUPTED SINCE THE LAST BOARD
| agent | what it was doing | cause | restarted? new id |
|---|---|---|---|
| none | | | |

## LEAD ACTIONS NEEDED
Q3 in QUESTIONS.md (spend ledger: part of the one exception, or move into Postgres). Not blocking.

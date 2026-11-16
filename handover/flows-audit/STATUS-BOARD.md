UPDATED_UTC: 2026-11-16T08:25:41Z
SESSION: flows-audit
ORDER: 007 (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 6
ITEMS_OPEN: 5
PERCENT: 20
AGENTS_RUNNING: 2
INTERRUPTED: none (first board; boot id recorded, container uptime was about 29 min at 08:19 UTC, so the container started once this session)
NEXT: merge N7-new-findings and N7-verdicts into FINDINGS (items 2, 4, 5), then FIX-PLAN split (item 3), then two-reviewer pass (item 6)
PUSHED_UTC: 2026-11-16T08:25:41Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| 1 | patch fixes F-001, F-002, F-004, F-008 | done (static, not run in n8n) | 100 | lanes7/evidence-7a.md, patches/ | F-002 repeat-key behaviour UNVERIFIED until laptop test |
| 2 | re-rate by one rule, new counts table | todo (script ready) | 10 | /tmp/gen7/rerate.py (untracked) | waits for new finding ids |
| 3 | rung tags, BEFORE/AFTER split, CUT-LIST AFTER | running | 40 | CUT-LIST.md done; FIX-PLAN split todo | |
| 4 | verdicts, approvals finding, T-test, NOT-covered block | running | 15 | lanes7/N7-verdicts.md (agent writing) | |
| 5 | new findings (7 topics) | running | 15 | lanes7/N7-new-findings.md (agent writing) | |
| 6 | two-reviewer pass, resolve, FINAL | todo | 0 | | max 2 rounds |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| acdf03c72e2add6e0 | static reviewer, item 5 | sonnet | 7 new findings | 08:20 | 08:40 | ? | running | none yet |
| a1cacfb2ad5a2e005 | static reviewer, item 4 | sonnet | verdicts, approvals, T-test, NOT-covered | 08:20 | 08:40 | ? | running | none yet |

## LOST OR INTERRUPTED SINCE THE LAST BOARD
| agent | what it was doing | cause | restarted? new id |
|---|---|---|---|
| none | | | |

## LEAD ACTIONS NEEDED
none

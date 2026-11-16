UPDATED_UTC: 2026-11-16T08:33:32Z
SESSION: system-map
ORDER: 011
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 3
ITEMS_OPEN: 3
PERCENT: 5
AGENTS_RUNNING: 0
INTERRUPTED: none
NEXT: write the flow checker, apply 5 patches to scratch copies, run on real-v5 and film-v5
PUSHED_UTC: 2026-11-16T08:33:32Z

## ITEMS
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| 1 | patch and flow-graph check | running | 10 | flowcheck/ | order paths are wrong: the real files are on origin/cloud/flows-audit (n8n-flows-real-v5, n8n-flows-film-v5); inputs copied to flowcheck/in/ |
| 2 | third read of 10 findings | todo | 0 | flowcheck/third-read.md | waits for flows-audit FINAL (board 08:31Z: WORKING, 80%) |
| 3 | FINAL | todo | 0 | | |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
none

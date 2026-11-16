UPDATED_UTC: 2026-11-16T00:00:00Z
SESSION: flows-audit
ORDER: <number of the order you are on>
STATE: WORKING
BOOT_ID: <first 8 characters of: cat /proc/sys/kernel/random/boot_id>
ITEMS_TOTAL: <n>
ITEMS_OPEN: <n>
PERCENT: <0-100, whole backlog>
AGENTS_RUNNING: <n, counted from the real agent list, not assumed>
INTERRUPTED: none
NEXT: <one line: what starts next>
PUSHED_UTC: <time of your last push>

STATE is one of WORKING, WAITING-LEAD (you need an answer: put the question in QUESTIONS.md), BLOCKED (say why), FINAL (every item done).
INTERRUPTED is "none" or a short list: which agent, what it did, why it stopped (container restart, killed, error, timeout, context full), what you did about it.

## ITEMS (every item of the order, in order)
| # | item | state (todo / running / done / blocked) | % | evidence or output file | note |
|---|---|---|---|---|---|

## AGENTS (every agent you started that is not yet closed, plus the ones closed since the last board)
| id | role | model | what it does | started UTC | expected end UTC | % | state (running / done / KILLED / INTERRUPTED / LOST-ON-RESTART) | last output |
|---|---|---|---|---|---|---|---|---|

## LOST OR INTERRUPTED SINCE THE LAST BOARD
| agent | what it was doing | cause | restarted? new id |
|---|---|---|---|

## LEAD ACTIONS NEEDED

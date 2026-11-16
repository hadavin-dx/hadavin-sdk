UPDATED_UTC: NOT-FILLED
SESSION: <name>
ORDER: <number of the order you are on>
STATE: NEW
BOOT_ID: <first 8 characters of: cat /proc/sys/kernel/random/boot_id>
ITEMS_TOTAL: <n>
ITEMS_OPEN: <n>
PERCENT: <0-100, whole backlog>
AGENTS_RUNNING: <n, counted from the real agent list, not assumed>
CAPACITY: <cores busy/total, mem used/total GB, disk free GB, light+heavy agents>
INTERRUPTED: none
FAILED: none
NEXT: <one line: what starts next>
PUSHED_UTC: <time of your last push>

Rules for this file (the lead's tool reads the KEY: value lines, first occurrence wins; write them plain, no bold, no bullets, no backticks):
- UPDATED_UTC is real UTC like 2026-11-16T12:30:00Z. STATE is WORKING, WAITING-LEAD (you need an answer: put the question in QUESTIONS.md), BLOCKED (say why), or FINAL (every item done or deferred by the lead; ITEMS_OPEN must then be 0). Replace every <...> placeholder: a board with placeholders is flagged UNFILLED.
- INTERRUPTED is one line: none, or a short text of which agent stopped, why (container restart, killed, error, timeout, context full) and what you did.
- Overwrite this file every 5 minutes (one file, not a log), commit, pull --rebase, push. Keep it under 3 KB. No secrets.
- If a push fails: retry twice, then set STATE to BLOCKED in the local file and say so in QUESTIONS.md.

## ITEMS (every item of the order, in order; detail and evidence live in REPORT.md, here only the state)
| # | item | state (todo / running / done / blocked / deferred by lead) | % | evidence file | note |
|---|---|---|---|---|---|

## AGENTS (every agent you started that is not closed, plus those closed since the last board)
| id | role | model | what it does | started UTC | expected end UTC | % | state (running / done / KILLED / INTERRUPTED / LOST-ON-RESTART) | last output |
|---|---|---|---|---|---|---|---|---|

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED

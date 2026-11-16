# EXCEPTIONS (store rule: one store, one log place; every exception needs reason, owner, removal trigger; MISSING = nobody wrote it)
| exception | reason (source) | owner | removal trigger | status |
|---|---|---|---|---|
| stage journal (file stage-journal.jsonl) | named by the order as the one allowed exception; reason at PLAN-4-NLITE-FROM-LEAD.md:78 | MISSING | MISSING | OPEN (F-020): the owner names both |
| n8n own SQLite database (holds lead name and e-mail even with saving none, N8N-START.md T7b) | the order says one database = n8n Postgres; n8n here runs on SQLite (N8N-START.md:4) | MISSING | MISSING | OPEN (F-011): switch n8n to Postgres or classify |
| spend ledger and mail/model-call counters (stage_server.py) | test stand-ins | MISSING | MISSING | proposed RETIRED with the stand-ins (lanes/L3-stores.md) |
| desk SQLite behind desk-* doors | retired from the take by the order | n/a | retire the doors (CUT-LIST.md) | OPEN (F-019) |
Not decided here: any of these needs the owner (2b). Nothing in this file changes behaviour.

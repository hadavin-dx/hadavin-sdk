# EXCEPTIONS (store rule: one store, one log place; every exception needs reason, owner, removal trigger; MISSING = nobody wrote it)
| exception | reason (source) | owner | removal trigger | status |
|---|---|---|---|---|
| stage journal (file; named stage.journal in the take scripts and stage-journal.jsonl in the test harness: one name must be chosen, F-020) | named by the order as the one allowed exception; reason at PLAN-4-NLITE-FROM-LEAD.md:78 | MISSING | MISSING | OPEN (F-020): the owner names both |
| n8n own SQLite database (today's default; holds workflows, credentials and run history, N8N-START.md:4 and T7b) | NOT an exception: the lead decided Reading A (ORDER 004): n8n's own state moves into the take's Postgres (DB_TYPE=postgresdb); the SQLite file is only today's state | lead | the re-smoke runs on Postgres (F-011) | OPEN (F-011): fix on the laptop; after it, delete this row |
| spend ledger and mail/model-call counters (stage_server.py, desk SpendLedger) | the stage service writes the ledger during the take, so it is a second record of the model-call fact (lanes/L3-stores.md T2); proposed EXCEPTION (not RETIRED) because the take may call a live model; can be RETIRED only if the take makes no live model call | MISSING | MISSING | OPEN: the owner names both, or confirms no live call (then RETIRED with the stand-ins) |
| desk SQLite behind desk-* doors | retired from the take by the order | n/a | retire the doors (CUT-LIST.md) | OPEN (F-019) |
Not decided here: any of these needs the owner (2b). Nothing in this file changes behaviour.

Definitions: EXCEPTION = a place that may hold the same fact as the one database; it stays only with a written reason, a named owner and a removal trigger. RETIRED = the file or flow is moved out of the take (archived, never deleted). KEEP-ONE = the one database for the take (n8n Postgres, table mf_leads). MISSING = nobody wrote it.
Test-only files proposed RETIRED from the take are listed in lanes/L3-stores.md (CRM, mail and model stand-in files, leads_skip, harness secret files, crash.flag, proxy log, result files).

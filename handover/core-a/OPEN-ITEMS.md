# OPEN-ITEMS of core-a (lookup, 2026-11-20)

Sources: ESCALATIONS.md, DECISIONS.md, requests/ (001-004), QUESTIONS.md, ORDERS.md through ORDER 022. Times are UTC from the files. "No time in file" rows use the file's modification time, marked as such.

## Open

| id | question or need | who must answer | exact missing input | since |
|---|---|---|---|---|
| REQ-001 | Config and wiring for the signed trigger endpoint (Config.triggers, trigger_resolve, registry checks) | core-b | core-b's answer file requests/001.answer.md (ORDER 014 item 3 waits for it) | 2026-11-20 05:41 UTC (draft 3) |
| REQ-002 | README, SECURITY and CHANGELOG sentences for the trigger endpoint | core-b | core-b's accept or reword of each sentence; no answer file exists | 2026-11-20 05:49 UTC (file mtime, no time in file) |
| REQ-003 | 25 questions on INTERFACE (i) v2.1 (C1-C3, G1-G10, P1-P4) | core-b | core-b's answers; C1 decides what purge does with expired rows | 2026-11-20 05:52 UTC (file mtime, no time in file) |
| E5 | Step E crash helper after round 3 of review: grant one more fresh pass? | lead | yes or no on one more fresh pass; Windows run still missing | 2026-11-20 07:09 UTC |
| E6 | Three n8n behaviours: waits over 65 s surviving a restart; Respond then Stop-and-Error; chained Respond node passing its item | lead | one real n8n run that settles all three | 2026-11-20 07:10 UTC |
| REQ-004 | One shared qualified-agents helper in runtime/agent_loop.py | core-b | core-b's helper, or a refusal with reason | 2026-11-20 07:35 UTC (file mtime, no time in file) |
| E7 | triggers/server.py is 316 lines against a ticket promise of about 250 in two modules: keep, vet a library, or drop cap and deadline | lead | choice (a), (b) or (c) from ESCALATIONS E7 | 2026-11-20 08:22 UTC |

## Answered, not open

| id | answer | by |
|---|---|---|
| E1 | 409 writes no audit event, one log line only; worker keeps answering 503 | ORDER 009 |
| E2 | loopback socket test in the batch; own quiet handler if wsgiref leaks | ORDER 009 |
| E3 | accept the duplicate qualification loop; one line in ticket D | ORDER 009 |
| E4 | n8n template finished as an outline marked "not run in n8n" | ORDER 009 |
| Q1-Q10 | all ten questions in QUESTIONS.md | answered by ORDER 022 (item 3) |

## Notes

- DECISIONS.md: 29 rows, the lead verdict column is empty on every row. Not listed: ORDER 002 A.4 says reversible choices do not wait for a verdict. ORDER 005 covers the rows up to 05:21 ("all OK"); ORDER 013 answers the crash-hook row and the back-off row.
- No git command was run. Only this file was written.

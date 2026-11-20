# OPEN-ITEMS of core-a (lookup, 2026-11-20)

Sources: ESCALATIONS.md, DECISIONS.md, requests/ (001-004), QUESTIONS.md, ORDERS.md through ORDER 022. Times are UTC from the files. "No time in file" rows use the file's modification time, marked as such.

## Open

| id | question or need | who must answer | exact missing input | since |
|---|---|---|---|---|
| REQ-001 | Config and wiring for the signed trigger endpoint (Config.triggers, trigger_resolve, registry checks) | core-b | core-b's answer file exists (origin/cloud/core-b f8af6fc02, checked 09:08 UTC); D builds on core-b's answer (ticket D, last section). Open: merge of core-b's code | 2026-11-20 05:41 UTC (draft 3) |
| REQ-002 | README, SECURITY and CHANGELOG sentences for the trigger endpoint | core-b | core-b's answer file exists (002.answer.md); D builds on assumption (ticket D, last section): core-b's rewordings; R-9 HOLD, S-6 DROP. Open: landing change writes README/SECURITY/CHANGELOG; lead decides `max_running` default 4 vs 1 | 2026-11-20 05:49 UTC (file mtime, no time in file) |
| REQ-003 | 25 questions on INTERFACE (i) v2.1 (C1-C3, G1-G10, P1-P4) | core-b | core-b's answer file exists (003.answer.md; C1: purge deletes expired rows). D does not depend on it (ticket D, last section); store contract tests need a read against it | 2026-11-20 05:52 UTC (file mtime, no time in file) |
| REQ-004 | One shared qualified-agents helper in runtime/agent_loop.py | core-b | core-b's answer file exists (004.answer.md, helper in fa184fc65 on origin/cloud/core-b). D builds on assumption (ticket D, last section): worker copy stays until core-b's code is merged here | 2026-11-20 07:35 UTC (file mtime, no time in file) |

## Answered, not open

| id | answer | by |
|---|---|---|
| E1 | 409 writes no audit event, one log line only; worker keeps answering 503 | ORDER 009 |
| E2 | loopback socket test in the batch; own quiet handler if wsgiref leaks | ORDER 009 |
| E3 | accept the duplicate qualification loop; one line in ticket D | ORDER 009 |
| E4 | n8n template finished as an outline marked "not run in n8n" | ORDER 009 |
| E5 | yes, one more fresh pass: done | lead (answer as given to core-a; no file named here) |
| E6 | settled by evidence-n8n-3.md (handover/core-a/inputs/evidence-n8n-3.md) | lead (as told to core-a) |
| E7 | keep the stdlib server (triggers/server.py as it is) | lead |
| Q1-Q10 | all ten questions in QUESTIONS.md | answered by ORDER 022 (item 3) |

## Notes

- DECISIONS.md: 29 rows, the lead verdict column is empty on every row. Not listed: ORDER 002 A.4 says reversible choices do not wait for a verdict. ORDER 005 covers the rows up to 05:21 ("all OK"); ORDER 013 answers the crash-hook row and the back-off row.
- No git command was run. Only this file was written.

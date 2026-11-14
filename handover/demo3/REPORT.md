## HEARTBEAT 161 (13:18Z) - ERROR run 2 (11:05Z flows) same as run 1; GREP finding; the container restarted at about 13:15Z and killed the queue; queue restarted, fixed flows (1ced4e1f) first

| Item | Result at 13:18Z |
|---|---|
| ERROR run 2, 11:05Z flows (je2), n = 2 | SAME AS RUN 1. CRM refuses every call (HTTP 500). Form answered 500. Row stayed processing at attempt 3 for the whole 700 s wait. 0 alerts, 0 mails to intake, 0 CRM rows, 1 model call. Expected failed plus 1 alert: NOT MET, 0 of 2. Phantom noise (66 refused CRM calls, 22 stage requests) did not change a lead count. |
| First run on 1ced4e1f | NOT STARTED yet. See "Restart" below. It is the first job after jg3 (about 13:21Z); ERROR n = 3 takes about 40 min, so the first ERROR answer is about 13:35Z. |
| GREP on the 11:05Z flows (jg1, jg2; n = 2) | FAILED the expectation. n8n log: 0 hits for name, e-mail, key. Exported flow JSON: 0 hits. n8n database file set: name, e-mail and the fake key ARE present, only in database.sqlite-wal (the write-ahead file), not in database.sqlite itself. Postgres row: name 1 hit, e-mail 1 hit (expected, that is the lead row), key 0 hits. |
| Cause of the GREP hit (looked at in jg3's file before the restart) | n8n writes the whole running execution (request headers, body with e-mail, name and the fake key, and the item data) into its execution data table while the run is open, even though all four flows have saveDataSuccessExecution and saveDataErrorExecution set to none. The row is deleted when the run ends, but the deleted pages stay in the -wal file (2 hits for the lead id, 40 for the e-mail domain in jg3). Observed in one file, not yet proven by a second setting (for example n8n's own EXECUTIONS_MODE or secure-delete). Client risk: personal data at rest in n8n's file, unmasked. |
| Restart | The sandbox restarted at about 13:15Z (uptime 2 min at 13:17Z). It killed Postgres, run_b and the harness; jg3 was cut off (its folder removed, rerun). Cause named: container restart, not a test failure. I restarted Postgres (13:17Z), found no leftover n8n, and started run_e.sh: jg3, then the fixed flows (1ced4e1f: ERROR x3, T14, BURST, K3 x3, K6 x3), then the fault repeats. T14 on 8e2b6960 dropped (the newest flows replace it). |
| Earlier results | K1, K2 3/3 done; K3, K6 3/3 unknown; BURST 3/3 pass; faults n = 1 each; ERROR 0/2 as expected. |
| Disk | 4.3G free |

ASK for the lead: forward the GREP finding to the demo: the two items are (1) the request body and the fake key sit in n8n's database file (-wal) during a run although saving is off; (2) the ask is a mask step or a hash before the first node, or a documented n8n setting; tell me which, I will test it.
FAILURES AND RETRIES: container restart 13:15Z killed jg3 (rerun). Nothing else.
NOT DONE / NOT CHECKED (my list, for the lead to decide): all fixed-flow runs; GREP third run; fault repeats; whether a checkpoint or restart removes the hits (not tested); kill/RESULTS.md not written; no comparison with the demo compare table.
WHAT I WOULD DO NEXT (ranked): 1) ERROR x3 on 1ced4e1f; 2) T14, BURST, K3, K6; 3) write RESULTS.md, then compare; 4) test a GREP fix if the demo pushes one.

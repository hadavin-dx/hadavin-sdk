## HEARTBEAT 173 (15:03Z) - F-a/F-b/F-c on the fixed flows 3/3 each: F-c STILL gives unknown + 0 alerts; Fc1 variant and my own v3 alert cases prepared

| Fault on the fixed flows (61e3804b = 1ced4e1f files), n = 3 each | Result |
|---|---|
| F-a (CRM search empty after create) | 3 of 3 done, 1 intake mail, 0 alerts, 1 CRM row, 1 model call. Same as the 11:05Z flows (3 of 3). |
| F-b (SMTP stores the mail, then drops the connection) | 3 of 3 unknown, attempts 1, 1 intake mail, 1 alert naming the lead, 1 CRM row, 1 model call. Same as the 11:05Z flows. |
| F-c (SMTP holds its greeting 40 s on EVERY connection) | 3 of 3 unknown, attempts 1, 0 intake mails, 0 ALERTS, 1 CRM row, 1 model call. STILL NO ALERT on the fixed flows, same as the 11:05Z flows (3 of 3). |
| F-c answers for the demo (written to questions-for-lead.md as Q-20) | (a) pre-greeting hold (the fake waits 40 s before its first line); (b) YES still active for the alert connection (the hold covers every connection); (c) no node error text observed (n8n's log has only start-up lines). Node: the in-run alert node (AlertUnknown in v2): its connection waited and gave up, flow ends quietly. Caution: in my F-c the alert goes through the same slow server, so this is partly my test. |
| Fc1 (hold only the FIRST SMTP connection, so the alert connection answers at once) | running now (3 runs on the fixed flows, then 3 on the 11:05Z flows), result in the next heartbeat. |
| New job: my own v3 alert-loss cases | Plan written and pushed BEFORE any v3 run: kill/PLAN-V3-ALERT.md (cases V3A refuse twice then accept, V3B20 and V3B90 hold then answer, V3C dead 600 s then restored; pass criteria stated). Built: v3 harness (kill/v3.py), fake SMTP switches (alert refuse, alert hold, dead-until), v3 flows from demo commit 6ebb7f62 (4 flow files, read directly; V3-README and the table DDL read, no other demo file). Starts after Fc1, about 15:20Z; about 40 minutes for n = 1 each. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): Fc1 results; all v3 runs; GREP on Postgres-backed n8n; credential needle; RESULTS.md; comparison with the demo table; K1, K2 on the fixed flows.
WHAT I WOULD DO NEXT (ranked): 1) Fc1; 2) v3 cases A, B20, B90, C; 3) repeats of the v3 cases; 4) RESULTS.md and compare.

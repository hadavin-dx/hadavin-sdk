## HEARTBEAT 151 (11:40Z) - kill script RUNNING (not stuck): control run 1 passed on the v2 flows; first kill point next

| Item | State at 11:40Z |
|---|---|
| Flow files tested (v2 top level only, from branch demo/handover at e00f50df) | mf-sub-crm-mail.json, mf-form.json, mf-hook.json, mf-recovery.json, mf_leads.sql (table as pushed, NO label column, NO table patch), DESIGN-A-README.md. Not used: desk-form-door, desk-webhook-door, desk-error-notifier, v1-superseded/. |
| RETRACTED | my HB150 defects F-DDL and F-DDL2 were my own slip: my local copy of mf-form, mf-hook and mf-recovery was the obsolete 10:45Z version (19, 19, 15 nodes; branch v2 has 12, 12, 5). The pushed DDL is fine. All results from runs c1, c1b, c1c (old files, or not published, or webhook not yet registered) are void and not used. |
| Control run 1 (c1d, 1 lead, no kill, v2 files, fresh n8n folder) | PASS: table row done, attempts 1, crm_id crm-1, mail_sent true; counts outside n8n: 1 CRM row, 1 mail to intake, 0 alerts, 1 stage call; the form answered 200 verdict new. |
| Idle test (i1: no lead, 100 s) | running; asks one question: does recovery act on an empty table? In the void run c1c (webhook 404, empty table) the 30-second recovery produced a stage call and a CRM call with lead `None` and an alert mail "lead failed undefined" every 30 s. Not yet reproduced on a clean run, so NOT a finding yet. |
| First kill point | K1 (kill while the stage call is in flight) is the next run, 3 runs per point. |
| Disk | 4.1G free, 90% used (allowance view). Fine; I delete my own temp folders under 2 GB free. |

ASK for the lead: none.
FAILURES AND RETRIES (all named): (1) isolated-vm built for Node 22: rebuilt for 24. (2) n8n listen address :: not available: N8N_LISTEN_ADDRESS=127.0.0.1. (3) task broker port clash: my port 5690. (4) wrong copy of 3 flow files (my slip, above). (5) sub-workflow not published ("Workflow is not active"): now published with the other three. (6) lead sent before the webhook was registered (HTTP 404): the driver now waits until the path answers a GET with "not registered for GET". None is a flake; each has a cause.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K1, K2, K3, K6, F-a, F-b, F-c not run; controls 2 (same lead twice, two at once) and bad e-mail not run; idle result pending; 3 runs per point not done; no comparison with the demo compare table (only after my numbers are saved); WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) read i1; 2) controls: same lead twice, two at once, bad e-mail; 3) K1, K2, K3, K6, three runs each; 4) F-a, F-b, F-c; 5) save numbers, then compare.


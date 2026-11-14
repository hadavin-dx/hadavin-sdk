## HEARTBEAT 154 (12:10Z) - kill script RUNNING: K1 3 of 3 done, K2 1 of 3 done; K3 starts about 12:16Z

| Item | State at 12:10Z (11:05Z flows, journal stage stand-in, one fresh n8n folder per run) |
|---|---|
| K1 kill while stage call in flight, n = 3 runs (j1a, j1b, j1c) | 3 of 3 identical: final done, attempts 2, 1 mail to intake, 1 CRM row, 1 model call (2 stage requests: the second got the stored answer), 0 alerts for the lead. Restart 6.8 to 7.2 s; whole run 208 to 209 s. Matches my plan's prediction (done, 1 CRM, 1 mail). |
| K2 kill after CRM stored the lead, before n8n got the answer, n = 1 run so far (j2a) | done, attempts 2, 1 mail to intake, 1 CRM row (the retried upsert updated the same row, created false), 1 model call, 0 alerts. Matches prediction. 2 more runs to come; n = 1 is not a result yet. |
| K3, K6 (mail steps), F-a, F-b, F-c | not run yet. |
| Idle-recovery noise | changed no per-lead count in any of the 4 runs (4 phantom stage requests, 4 phantom CRM upserts, 5 phantom alert mails per run, each on its own key). Total-per-run counts that ignore the lead id are off by that noise. |
| Disk | 3.5G free, 92% used |

ASK for the lead: none.
FAILURES AND RETRIES: none new since HB153.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K2 runs b and c, K3, K6 (3 runs each), F-a, F-b, F-c, cp2; fixed flows not tested yet; no comparison with the demo compare table (after my numbers are saved); WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish the batch (about 12:50Z); 2) write kill/RESULTS.md with the table and sample sizes; 3) compare; 4) the fixed flows; 5) WINDOWS-RUN-1 additions.


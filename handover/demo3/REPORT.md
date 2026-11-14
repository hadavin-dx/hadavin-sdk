## HEARTBEAT 156 (12:30Z) - kill script RUNNING: K1, K2, K3 done (3 runs each), K6 1 of 3 done; no "K4" exists in my plan

| Item | State at 12:30Z (11:05Z flows, journal stage stand-in, fresh n8n folder per run) |
|---|---|
| K3 kill after mail_sent=true written, before the mail was stored, n = 3 | 3 of 3 the same: final unknown, attempts 2, 0 mails to intake, 1 CRM row, 1 model call, 1 alert naming the lead ("mail outcome unknown", to alerts@example.test); no resend. Recovery restart 6.9 to 7.6 s. |
| K6 kill after the mail was stored, before state done was written, n = 1 (j6a) | unknown, attempts 2, 1 mail to intake, 1 CRM row, 1 model call, 1 alert naming the lead; no second mail. Matches the plan prediction (unknown, 1 mail, 1 alert). Two more runs to come; n = 1 is not a result yet. |
| K4 start (your question) | my plan has K1, K2, K3, K6 only (the lead never defined T1-T3 and T6; ASK in HB148 still stands). There is no K4 or K5; next after K6 is the three fault modes F-a, F-b, F-c, then cp2. |
| K1 and K2, n = 3 each | unchanged: done, 1 mail, 1 CRM row, 1 model call, 0 alerts. |
| Noise | still no per-lead count changed (phantom 4/4/5 per run). |
| Disk | 3.2G free, 92% used |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K6 runs b and c, F-a, F-b, F-c, cp2; fixed flows not tested; no comparison with the demo compare table (after my numbers are saved, about 12:50Z); WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish the batch; 2) write kill/RESULTS.md with all sample sizes; 3) compare with the compare table; 4) fixed flows; 5) WINDOWS-RUN-1 additions.


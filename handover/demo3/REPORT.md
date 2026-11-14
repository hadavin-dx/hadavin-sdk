## HEARTBEAT 155 (12:20Z) - kill script RUNNING: K1 3/3 and K2 3/3 done, K3 1 of 3 done

| Item | State at 12:20Z (11:05Z flows, journal stage stand-in, fresh n8n folder per run) |
|---|---|
| K1 stage call in flight, n = 3 | 3 of 3 the same: done, attempts 2, 1 mail to intake, 1 CRM row, 1 model call, 0 alerts. |
| K2 CRM stored, answer not received, n = 3 | 3 of 3 the same: done, attempts 2, 1 mail to intake, 1 CRM row (second upsert updated the same row), 1 model call, 0 alerts. |
| K3 kill after mail_sent=true written, before the mail was stored, n = 1 (j3a) | final state unknown, attempts 2, 0 mails to intake, 1 CRM row, 1 model call, 1 alert for the lead ("mail outcome unknown for L-j3a", to alerts@example.test); recovery did NOT resend. Row at kill: processing, attempts 1, mail_sent true, crm_id set. Matches plan prediction (unknown, 0 mails, 1 alert). Two more runs to come; n = 1 is not a result yet. |
| K6, F-a, F-b, F-c, cp2 | not run yet. |
| Noise | still no per-lead count changed (phantom 4/4/5 per run). |
| Disk | 3.3G free, 92% used |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K3 runs b and c, K6 (3 runs), F-a, F-b, F-c, cp2; fixed flows not tested; no comparison with the demo compare table (after my numbers are saved); WINDOWS-RUN-1 additions not written. Note for the lead: a lost mail is the K3 outcome by design (one alert, a person decides); I count it as pass only if the demo compare table says the same.
WHAT I WOULD DO NEXT (ranked): 1) finish the batch (about 12:50Z); 2) write kill/RESULTS.md; 3) compare; 4) fixed flows; 5) WINDOWS-RUN-1 additions.


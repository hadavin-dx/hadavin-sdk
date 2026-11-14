## HEARTBEAT 163 (13:33Z) - FIRST RUN ON THE FIXED FLOWS: ERROR run 1 PASSES (failed + 1 alert); ferr2, ferr3 next

| Item (fixed flows, demo commit 61e3804b = same four flow files as 1ced4e1f) | Result at 13:33Z |
|---|---|
| ERROR ferr1, n = 1 of 3 | PASS. CRM refused every call (HTTP 500) from the start. The form answered at once (HTTP 200, verdict "processing", not the old HTTP 500). The row went processing, attempts 1, 2, 3, then state failed, attempts 3, after 478 s (limit asked for: 3 x 120 + 150 = 510 s). Exactly 1 alert mail, subject "[demo] Lead desk: lead failed L-ferr1", to the alerts address. 0 mails to intake. 0 CRM rows. 1 model call (3 stage requests, repeats got the stored answer). 0 lost. Phantom noise: 0 stage, 0 CRM, 0 alerts (the old flows had 22 and 66), so the empty-item noise is gone. |
| Same test on the 11:05Z flows (for the record) | 0 of 2: lead stayed processing, 0 alerts. The change from fail to pass is consistent with the cause named in HB159 (the second recovery branch did not run). Still observed on one flow version pair, n = 1 vs n = 2, no patched copy of the old flow to prove it alone. |
| Queue now | ferr2 (running), ferr3, T14, BURST, K3 x3, K6 x3; then fault repeats. Fixed-flow batch end about 15:15Z. |
| Disk | 4.3G free |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): ferr2, ferr3, T14, BURST, K3, K6 on the fixed flows; fault repeats; kill/RESULTS.md; comparison with the demo compare table; GREP on the new flows (T7b is a demo test; I run it if you ask).
WHAT I WOULD DO NEXT (ranked): 1) ferr2, ferr3; 2) T14, BURST; 3) K3, K6 x3; 4) RESULTS.md then compare; 5) fault repeats.

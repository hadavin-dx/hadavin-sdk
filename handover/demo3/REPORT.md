## HEARTBEAT 166 (13:59Z) - ferr2 PASSES on the fixed flows (2 of 2 ERROR); queue continues, my turn stays open

| Item (fixed flows, demo commit 61e3804b) | Result at 13:59Z |
|---|---|
| ERROR ferr2, n = 2 of 3 | PASS, same as ferr1. CRM refused every call (HTTP 500). Form answered HTTP 200 "processing". Row went to failed, attempts 3, after 452 s (limit 510 s). Exactly 1 alert mail naming L-ferr2, 0 mails to intake, 0 CRM rows, 1 model call, 0 lost. Phantom noise 0 for stage, CRM and alerts. |
| ERROR total on the fixed flows | 2 of 2 pass (ferr1 478 s, ferr2 452 s). On the 11:05Z flows: 0 of 2. |
| Sandbox restarts | ferr2 ran 13:50 to 13:58Z with my turn kept open and was NOT killed (no restart in that time, uptime counted up). This fits the idle-recycle cause (restarts 13:15, 13:40, 13:50Z each after I ended a turn); n = 1 test, not proof. I keep the turn open until the queue is done and write blocks while it runs. |
| Queue | ferr3 running (ends about 14:07Z), then T14, BURST, K3 x3, K6 x3 (about 14:15 to 15:20Z), fixed-flow GREP (fjg1), fault repeats. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): ferr3, T14, BURST, K3, K6 on the fixed flows; fixed-flow GREP; fault repeats; RESULTS.md; compare with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) ferr3; 2) T14, BURST; 3) K3, K6 x3; 4) fjg1; 5) RESULTS.md then compare.

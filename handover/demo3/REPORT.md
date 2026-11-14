## HEARTBEAT 167 (14:09Z) - fixed flows: ERROR 3 of 3 PASS, T14 PASS (n = 1); BURST, K3, K6 running; turn kept open, no restart since 13:50Z

| Item (fixed flows, demo commit 61e3804b = 1ced4e1f flow files) | Result at 14:09Z |
|---|---|
| ERROR, n = 3 | 3 of 3 PASS: ferr1 478 s, ferr2 452 s, ferr3 444 s to state failed (limit 510 s). Each: attempts 3, exactly 1 alert naming the lead, 0 mails to intake, 0 CRM rows, 1 model call, 0 lost. Phantom noise 0. On the 11:05Z flows: 0 of 2. |
| T14 idle 120 s, n = 1 (ft14n) | PASS. Over a 154 s run: 0 stage calls, 0 mails (so 0 alerts and 0 intake mails), 0 CRM calls, 0 phantom lead rows. |
| Queue | BURST (fb1) running now, then K3 x3, K6 x3 (about 14:12 to 15:20Z), fixed-flow GREP, fault repeats. |
| Sandbox | no restart since 13:50Z (uptime counts on) while my turn stays open. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): BURST, K3, K6 on the fixed flows; fixed-flow GREP; fault repeats; RESULTS.md; comparison with the demo table; T14 n = 1 only (as ordered).
WHAT I WOULD DO NEXT (ranked): 1) BURST; 2) K3, K6 x3; 3) fjg1; 4) RESULTS.md then compare; 5) fault repeats.

## HEARTBEAT 169 (14:30Z) - fixed flows (demo commit 61e3804b = 1ced4e1f flow files): ERROR 3/3, T14 1/1, BURST 1/1, K3 3/3, K6 3/3 all done; fixed-flow GREP running

| Test on the fixed flows | n | Result |
|---|---|---|
| ERROR (CRM refuses everything from the start) | 3 | 3 of 3 PASS: state failed after 478, 452, 444 s (limit 510 s); each 1 alert naming the lead, 0 mails to intake, 0 CRM rows, 1 model call, 0 lost. |
| T14 (idle 120 s) | 1 | PASS: 0 stage calls, 0 mails (so 0 alerts, 0 intake mails), 0 CRM calls. |
| BURST (10 same-lead requests at once) | 1 | PASS: 1 CRM row, 1 mail, 1 model call, 1 done row; answers 1 new + 9 "processing, repeat". |
| K3 (killed after mail marked sent, before the mail was stored) | 3 | 3 of 3: lead unknown, attempts 2, 1 alert naming the lead, 0 mails to intake, 1 CRM row, 1 model call, 2 stage requests (the repeat got the stored answer). Restart 6.8 to 6.9 s. |
| K6 (killed after the mail was stored, before state done) | 3 | 3 of 3: lead unknown, attempts 2, 1 alert, 1 mail to intake, 1 CRM row, 1 model call, 2 stage requests. Restart 6.4 to 6.8 s. |
| Phantom noise | all | 0 stage, 0 CRM, 0 alert phantoms in every fixed-flow run; no count changed. |

Compared with the 11:05Z flows (my own runs): K3 3/3 and K6 3/3 give the same counts; BURST same; ERROR changes from 0 of 2 to 3 of 3 (the fix works in my harness). Neither K3 nor K6 end in done: the flows choose "unknown, a person checks" over a possible second mail. That matches the design's stated rule (one mail at most); a K3 lead gets no mail at all until a person acts.
Sandbox: no restart since 13:50Z with my turn open.
Queue now: fixed-flow GREP (fjg1, about 14:32Z), then the fault repeats on the 11:05Z flows (6 runs, about 14:35 to 14:55Z), then RESULTS.md.

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): fixed-flow GREP result; fault repeats (F-a, F-b, F-c n = 1 each so far); K1, K2 and the faults on the fixed flows (not ordered); RESULTS.md; comparison with the demo table; BURST and T14 are n = 1 as ordered.
WHAT I WOULD DO NEXT (ranked): 1) fjg1; 2) fault repeats; 3) RESULTS.md then compare; 4) optional K1, K2 and faults on the fixed flows.

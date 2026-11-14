## HEARTBEAT 168 (14:17Z) - fixed flows: BURST PASS (n = 1); K3 and K6 first runs done (unknown + 1 alert, same as the 11:05Z flows); K3/K6 runs 2 and 3 running

| Item (fixed flows, demo commit 61e3804b = 1ced4e1f flow files) | Result at 14:17Z |
|---|---|
| ERROR, n = 3 | 3 of 3 PASS (HB167). |
| T14, n = 1 | PASS (HB167). |
| BURST, n = 1 (fb1): 10 requests, same lead id, at once, to the production form path | PASS. 1 CRM row, 1 mail to intake, 1 model call, 1 done row (attempts 1). Answers: 1 "new", 9 "processing, repeat". 0 alerts, 0 phantom noise. Same as the 11:05Z flows (3 of 3). |
| K3 (killed after the mail was marked sent, before the mail was stored), n = 1 of 3 (fk3a) | Lead ends unknown, attempts 2, 1 alert naming the lead, 0 mails to intake (the mail was never stored), 1 CRM row, 1 model call. n8n restarted in 6.8 s. Same as the 11:05Z flows (3 of 3 unknown plus alert). |
| K6 (killed after the mail was stored, before state done), n = 1 of 3 (fk6a) | Lead ends unknown, attempts 2, 1 alert, 1 mail to intake, 1 CRM row, 1 model call. Restart 6.6 s. Same as the 11:05Z flows (3 of 3). Note for the lead: the lead had a stored mail but state unknown and an alert: a person must check; no second mail was sent. |
| Phantom noise | 0 in every fixed-flow run so far; no count changed. |
| Sandbox | no restart since 13:50Z with my turn open. |
| Queue | fk3b, fk6b, fk3c, fk6c (about 14:30Z), then fixed-flow GREP (fjg1), then fault repeats. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K3, K6 runs 2 and 3 on the fixed flows; fixed-flow GREP; fault repeats; RESULTS.md; comparison with the demo table; BURST and T14 n = 1.
WHAT I WOULD DO NEXT (ranked): 1) K3, K6 x3; 2) fjg1; 3) RESULTS.md then compare; 4) fault repeats.

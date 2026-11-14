## HEARTBEAT 176 (15:26Z) - v3 cases A and B20 pass (n = 1 each); case C (SMTP dead 10 min) running since 15:22Z, ends about 15:42Z

| v3 flows (demo commit 6ebb7f62, folder n8n-flows-v3), my own cases (plan: kill/PLAN-V3-ALERT.md) | Result at 15:26Z |
|---|---|
| V3A, n = 1: SMTP refuses the first two alert recipients (451), then accepts | PASS. Lead unknown at 0 s, 1 intake mail. Alert tries at 31 s, 121 s (both refused), 242 s (accepted): 1 alert stored at 240 s, alert_sent true, state unknown, 150 s later still 1 alert. 1 CRM row, 1 model call. |
| V3B20, n = 1: SMTP accepts the connection and the first alert recipient, then holds its answer 20 s, then answers normally | PASS. First alert try at 31 s (alert_attempts 1), the mail was stored at 50 s, alert_sent true at about 51 s, state unknown. EXACTLY 1 alert, 1 intake mail, 150 s later still 1 alert. The hold was shorter than the claim window, so no second try started. |
| V3C (dead for 600 s from the moment the lead mail is stored, then restored) | running: started 15:22:47Z, the fake SMTP closes every connection without a greeting until about 15:33Z, then answers; the alert should follow within 300 s; ends about 15:42Z (150 s watch after alert_sent). |
| V3B90 (hold 90 s, longer than the 60 s first claim window) | next after V3C, about 6 minutes. The README expects a possible second alert there; I record the count. |
| Repeats | A, B20, C, B90 repeats are queued (n = 2 or 3 each) if time allows; every number above is n = 1 until then. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): V3C, V3B90 results; repeats; K3, K6, T12, T11 on v3 (not ordered); RESULTS.md; comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) V3C then V3B90; 2) repeats; 3) RESULTS.md and compare.

## HEARTBEAT 175 (15:20Z) - v3 case A (refuse the alert twice) PASSES, n = 1; case B20 running

| v3 flows (demo commit 6ebb7f62, folder n8n-flows-v3, lease 120 s) | Result at 15:20Z |
|---|---|
| V3A, n = 1 (v3a1): the fake SMTP answers 451 to the first two alert recipients, then accepts | PASS. The lead mail was stored once (1 intake mail), the connection was dropped, the lead went unknown (attempts 1) at 0 s. Alert tries: first claim at 31 s (alert_attempts 1, refused), second at 121 s (attempts 2, refused), third at 242 s (attempts 3): the alert mail was stored at 240 s, alert_sent became true, state stayed unknown. Totals: 1 intake mail, EXACTLY 1 alert mail (naming the lead), 1 CRM row, 1 model call. 2 refused alert recipients seen by the fake. I kept watching 150 s after alert_sent turned true: still 1 alert. Time to the alert about 4 minutes, inside the plan's 5 to 6 minute limit. |
| Spacing seen | 31 s, then +90 s, then +121 s: the sweep wakes every 30 s and the claim window grows (so the visible waits are shorter than the README's 120 s and 180 s because the first claim happens before the window starts; I did not check why; I report the times as seen). |
| Not yet | V3B20 (hold 20 s) running now; then V3C (dead 600 s, about 18 min), V3B90, repeats. |
| Harness note (mine) | the timeline log wrote a line for every poll because I compared a list with a tuple; fixed at 15:19Z, only affected the size of the record in v3a1, not any count. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): V3B20, V3B90, V3C; repeats (n = 1 so far for A); K3, K6, T12 on v3 (not ordered); RESULTS.md; comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) V3B20, V3C, V3B90; 2) repeats of A, B, C; 3) RESULTS.md then compare.

## HEARTBEAT 178 (15:43Z) - v3 case C PASS (n = 1); case B90 FAILS the "exactly 1 alert" rule (n = 1): 2 alerts

| v3 flows 6ebb7f62, my own cases (plan: kill/PLAN-V3-ALERT.md) | n | Result |
|---|---|---|
| A: SMTP refuses the alert recipient twice, then accepts | 1 | PASS: 1 alert (at 240 s), alert_sent true, 1 intake mail |
| B20: SMTP holds the alert answer 20 s | 1 | PASS: 1 alert (at 50 s), alert_sent true |
| C: SMTP dead 600 s, then restored | 1 | PASS: 4 refused tries (29, 119, 239, 419 s), 1 alert at 690 s, alert_sent true, 1 intake mail, no second alert in the 150 s watch |
| B90: SMTP holds the alert answer 90 s (longer than the 60 s first claim window) | 1 | FAIL for "exactly 1 alert": 2 alerts, both stored at about 120 s. 1 intake mail, 1 CRM row, alert_sent true, alert_attempts 2. |

Cause of B90 (from the timeline, not yet traced in the node logs): the first claim lasts 60 s (alert_until = now + 60 s x (1 + attempts)). The send was held 90 s, so the claim ran out at about 60 s while send 1 was still waiting. The sweep at about 91 s claimed the row again (attempts 2) and sent alert 2. Both mails arrived at the fake at about 120 s. alert_sent turns true only after a send succeeds, so nothing stops the second claim. The demo README already says a duplicate can happen when a send outlasts the claim window; this run measures it: the owner gets 2 alerts, never 0. Danger direction is the safe one (duplicate, not loss). Fix options for the demo (not tested by me): make the claim window longer than the node timeout (the SMTP node timeout is the number to compare), or set the node timeout below the first claim window.

ASK for the lead: should the demo session decide if 2 alerts in the slow-SMTP case is accepted (then the owner-facing text must say "possible duplicate alert") or fixed? Please forward B90 to them.
FAILURES AND RETRIES: none new. B90 is a named finding with a cause, not a flake.
NOT DONE / NOT CHECKED (my list, for the lead to decide): n = 1 for every case so far (repeats queued: A, C, B20, B90, A, about 40 min); B90 cause not yet traced in the n8n log; K3/K6/T12/T11 on v3 (not ordered); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) repeats, starting with B90 (is the duplicate always there?); 2) trace B90 in the n8n log; 3) RESULTS.md, then compare.

## HEARTBEAT 184 (16:23Z) - v4: all three of your cases pass: B90 n = 2, A n = 2, C n = 1; every run exactly 1 alert

| v4 flows (7709d058), my cases | n | Result | First alert |
|---|---|---|---|
| B90 (hold 90 s) | 2 (3rd running) | exactly 1 alert each, alert_attempts 1, alert_sent true, 1 intake mail | 120 s, 120 s |
| A (refuse twice, then accept) | 2 | exactly 1 alert each, alert_attempts 3, alert_sent true, 1 intake mail, 1 CRM row, no second alert in 150 s | 270 s, 270 s (old v3: 240 and 270 s; not 12 min) |
| C (SMTP dead 600 s, then restored) | 1 (2nd running) | exactly 1 alert, state unknown, 1 intake mail, 1 CRM row, alert_attempts 5, alert_sent true. 4 tries refused while dead (31, 121, 272, 484 s), 5th accepted | 750 s = 150 s after the SMTP came back (v3: 690 s, 90 s after) |
Reading C: the v4 retry spacing is a little longer than v3 (the waits grow to 300 s), so the owner's alert comes about 60 s later than on v3 after a long outage. Not a loss. Spacing, not a defect, for the lead to judge.
v3 for comparison: A n = 2 pass; B20 n = 1 pass; C n = 1 pass (alert at 690 s); B90 n = 3, all with 2 alerts. v3 C repeat is running.

Workers now: 3 parallel lanes (lane 0 v3 C repeat, lane 1 v4 C repeat, lane 2 v4 B90 third run); 0 agents running. Machine load about 1.5 with the lanes.

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): n is 1 to 3 per case; a hold longer than 12 min on v4 (README says a duplicate is still possible; not tested); a failed mark after a sent alert (README says duplicate possible; not tested); n8n stopped while sending; K3/K6/T12/T11 on v4 (not ordered); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) finish the repeats (about 16:40Z); 2) test on v4: hold 13 min (known duplicate) or n8n killed during an alert send (late alert, no loss?), if you want them; 3) RESULTS.md with v3 and v4, then compare.

## HEARTBEAT 183 (16:19Z) - v4: B90 2 of 2 pass, A 1 of 1 pass (first alert at 270 s, not 12 min); v4 C running; v4 A repeat running

| v4 flows (7709d058), my cases | n | Result | First alert |
|---|---|---|---|
| B90 (hold 90 s) | 2 | PASS both: exactly 1 alert, alert_attempts 1, alert_sent true, 1 intake mail | 120 s |
| A (refuse alert recipient twice, then accept) | 1 | PASS: exactly 1 alert, alert_attempts 3, alert_sent true, 1 intake mail, 1 CRM row, no second alert in 150 s | 270 s (v3: 240 s and 270 s). The new AlertBackoff keeps the old 60/120/180 s spacing; no 12 min wait. |
| C (SMTP dead 600 s) | 0 done, run 1 started 16:07Z | running, result about 16:28Z (v3: 690 s) | - |
| A repeat (lane 2) | running since 16:12Z | result about 16:22Z | - |
v3 for comparison: A n = 2 pass, B20 n = 1 pass, C n = 1 pass, B90 n = 3 all with 2 alerts.

Workers now: 3 parallel lanes (lane 0: v3 C repeat, lane 1: v4 C, lane 2: v4 A repeat); 0 agents running.

ASK for the lead: none.
FAILURES AND RETRIES: none new. (Progress-file line for v4 A run 1 is missing because I stopped an old queue loop; the result itself is in results.jsonl.)
NOT DONE / NOT CHECKED (my list, for the lead to decide): v4 C and the repeats; v4 B20 (not planned; v4 B90 covers the hold case); a hold longer than 12 min on v4 (README says a duplicate is still possible; not tested); K3/K6/T12/T11 on v4; RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) v4 C result; 2) v4 A and C repeats; 3) RESULTS.md with v3 and v4, then compare.

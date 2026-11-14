## HEARTBEAT 180 (16:00Z) - v3 B90: 2 alerts in 3 of 3 runs; v4 B90 running now (started 16:00Z)

| v3 flows (6ebb7f62), SMTP holds the alert answer 90 s (B90) | Result |
|---|---|
| Run 1 | 2 alerts, stored at 120 s and 120 s; 1 intake mail, 1 CRM row |
| Run 2 | 2 alerts at 120 s and 120 s; 1 intake mail |
| Run 3 | 2 alerts at 90 s and 120 s; 1 intake mail, 1 CRM row |
So the duplicate is NOT a one-off: n = 3, always 2 alerts, never 0, never 3. Other v3 cases: A n = 2 pass (1 alert each), B20 n = 1 pass, C n = 1 pass.

| v4 flows (demo commit 7709d058, folder n8n-flows-v4), my cases | Status |
|---|---|
| B90 (hold 90 s) | RUNNING, started 16:00Z, result about 16:08Z. Criteria written before the run: exactly 1 alert, alert_attempts 1, alert_sent true, 1 intake mail, still 1 alert 150 s after. |
| A (refuse twice) | next, about 16:20Z. Criterion: first alert near the old 60 to 300 s backoff (v3 gave 240 and 270 s), not 12 min. |
| C (dead 600 s) | after A, about 16:35Z. Criterion: 1 alert after restore. |
| B90 again | after C. The remaining v3 repeats (C, B20, A) come after the v4 runs. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): v4 results; n = 1 per v4 case so far (repeats queued: B90 and later A, C); K3/K6/T12/T11 on v4 (not ordered); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) v4 B90, A, C; 2) v4 repeats; 3) RESULTS.md with v3 and v4, then compare.

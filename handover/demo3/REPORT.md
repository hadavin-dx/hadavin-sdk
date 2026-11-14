## HEARTBEAT 187 (16:41Z) - v4 so far: C 2 of 2, B90 3 of 3, A 2 of 2 pass; K1, K3, K6 pass; KS and B780 running

WORKERS: 3 lanes running (my script processes), 0 language-model agents. Lane 0: K2 next (K1 K3 K6 done). Lane 1: KS (n8n killed while the alert send waits, started 16:38Z, ends about 16:55Z). Lane 2: B780 (hold 780 s, started 16:26Z, ends about 16:55Z). Read RULE-R456; obeying: no side projects, n8n first, parallel.

| v4 flows (7709d058), each n | State | Intake mails | Alerts | CRM rows | Recovery seconds (n8n up again to final state) |
|---|---|---|---|---|---|
| K1 (killed at CRM write), n=1 | done | 1 | 0 | 1 | 144.3 |
| K3 (killed after CRM write), n=1 | unknown | 0 | 1 | 1 | not measured (run started before I added the timer) |
| K6 (killed after mail stored), n=1 | unknown | 1 | 1 | 1 | 144.2 |
| C (SMTP dead 600 s), n=2 | unknown | 1 | exactly 1 (750 s both) | 1 | - |
| B90, n=3 / A, n=2 | unknown | 1 | exactly 1 each | 1 | - |
Recovery seconds: 144 s, NOT comparable with the demo's 59.6 s: the v4 flow folder uses a 120 s lease (stuck-row wait), the demo K1/K2 numbers used 20 s. So V7 (60 s) is not met on these flow files; it is the lease, as designed, not a fault. Ask the demo session which lease the video shows.

ASK for the lead: which lease does the video flow use (20 s or 120 s)? I can rerun K1 and K2 at the video value.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list): K2 result; KS and B780 results; K3 recovery seconds; failed mark after a sent alert; comparison with the demo table; n is 1 for K1, K3, K6.
WHAT I WOULD DO NEXT (ranked): 1) K2, KS, B780; 2) K1, K3, K6 repeats at the video lease; 3) final RESULTS.md, compare, one video line.

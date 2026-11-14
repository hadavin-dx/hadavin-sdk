## HEARTBEAT 194 (17:27Z) - ERROR at lease 45 s 3 of 3 pass; RESULTS.md final and compared with the demo table; all my test runs finished

WORKERS: 0 lanes, 0 agents. STOPPED at 17:27Z: Postgres stopped, 0 run scripts, 0 fakes, 0 n8n processes left (checked with pgrep: count 0). Disk 2.5 GB free. To run more I restart Postgres (one command) and the lanes.

| film-v4, lease 45 s | n | Result |
|---|---|---|
| ERROR (CRM answers 500 to every call) | 3 | state failed, attempts 3, exactly 1 alert naming the lead, 0 mails to intake, 0 CRM rows, in each of 3 (run time about 4 min incl. start-up; 3 x lease + 150 s = 285 s) |
| K1, K2, K3, K6 | 5, 5, 5, 3 | all correct (HB193) |

COMPARISON with the demo table (kill/COMPARE-demo.md, written after my numbers were saved): same end states in K1, K2, K3 (their K3B), K6 (their K3) and ERROR (their T15). Different: the timing. Their lease was 20 s (kill to final median 29.7 s, max 59.6 s); mine at lease 45 s is 60.1 to 61.9 s with almost no spread. I do not know why mine has no spread (guess: my restart always starts the recovery timer at the same moment; not verified). New from me and not in their list: v3 B90 gives 2 alerts (3 of 3), v4 gives 1 (3 of 3); v4 kill during the alert send gives 1 alert 13 min late (2 of 2); v4 hold 780 s and SMTP dead 600 s give 1 alert each.

VIDEO LINE (plain): "About a minute after the crash the lead desk has finished every lead: nothing lost, nothing mailed twice. If the mail server is down or slow, the owner still gets exactly one alert; after a crash during that alert it can take 13 minutes." (n = 18 kill runs, 3 error runs, 2 to 3 per alert case.)

ASK for the lead: none.
FAILURES AND RETRIES: none new since HB192.
NOT DONE / NOT CHECKED (my list): T8, T10, T11, T13, T14 on v4; K3B named case (mapped to my K3); a failed alert mark after a sent alert; the spread difference to the demo timing; GREP on Postgres-backed n8n; a credential needle; paused rounds B21 to B23 (by order).
WHAT I WOULD DO NEXT (ranked): 1) stop processes and report counts; 2) any case you name (T14, T11 on v4 are 5 to 8 min each); 3) idle by order.

## HEARTBEAT 192 (17:19Z) - lease 45 s: K1 5, K2 5, K3 4, K6 2 runs; all correct; RESULTS.md has the new section; one run voided (my slip)

WORKERS: 2 lanes (my script processes): K3 run 5 and K6 run 3 at lease 45 s (end about 17:23Z), 0 language-model agents.

| film-v4, lease 45 s (demo 873a908a) | n | Final state | Intake / alerts / CRM rows | Recovery s (n8n up to final), median / max | Kill to final s, median / max |
|---|---|---|---|---|---|
| K1 | 5 | done | 1 / 0 / 1 | 52.9 / 54.9 | 60.8 / 61.9 |
| K2 | 5 | done | 1 / 0 / 1 | 52.9 / 52.9 | 60.9 / 61.2 |
| K3 | 4 (5th running) | unknown | 0 / 1 / 1 | 53.9 / 54.9 | 61.0 / 61.6 |
| K6 | 2 (3rd running) | unknown | 1 / 1 / 1 | 53.8 / 54.8 | 60.8 / 61.5 |
Lease 120 s (n8n-flows-v4): recovery 144.2 to 144.4 s (K1 2, K2 1, K3 1, K6 2). Table with all rows: kill/RESULTS.md (Part 3).

MY SLIP, named: I started a second script on lane 1 while the first was still running there. The second run's start-up cleared the table of the first (K3 run 2). Result: K3 run 2 reached no final state (void) and the other run failed to start (fakes_not_up). Both are labelled VOID- in results.jsonl and left out of every table; I reran them (K3 run 5 and K6 run 3 now). No product fault.

ASK for the lead: (1) What is T8? My harness has no T8 and I may not read the demo's result files; tell me the case in one line (what is killed or faulted, what is expected) and I run it once at lease 45 s. (2) Same question as before: caption start point, kill or n8n up.
FAILURES AND RETRIES: see the slip above.
NOT DONE / NOT CHECKED (my list): K3 run 5 and K6 run 3 results; T8; failed mark after a sent alert; comparison with the demo table; 15 runs counted: 5 K1, 5 K2, 4 K3 valid, 2 K6 valid.
WHAT I WOULD DO NEXT (ranked): 1) finish K3 and K6; 2) T8 once you define it; 3) compare with the demo table, one video line.

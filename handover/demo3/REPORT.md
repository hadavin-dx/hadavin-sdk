## HEARTBEAT 191 (17:10Z) - lease 45 s (film-v4): recovery 52.9 s from n8n up; 60.1 to 61.9 s from the kill; 11 of 15 runs done, all correct

WORKERS: 2 lanes still running (my script processes: K3 and K2 last runs, about 17:15Z), 0 language-model agents. Lanes 0 and 1 are free.

Flow files: demo folder n8n-flows-film-v4 (demo commit 873a908a), lease 45 s, 2 tries, 10 s timeout. Same harness as the lease-120 runs. "Recovery" = seconds from "n8n is up again" to the lead being in a final state (polled every 2 s, so +-2 s). "Kill to final" = seconds from the kill to the same point (includes my n8n restart time, 7.0 to 8.8 s).

| Point (film-v4, lease 45 s) | n so far | State | Intake mails | Alerts | CRM rows | Recovery s | Kill to final s |
|---|---|---|---|---|---|---|---|
| K1 (killed at CRM write) | 5 | done, attempts 2 | 1 | 0 | 1 | 52.8 to 54.9 (median 52.9) | 60.1 to 61.9 |
| K2 (killed after the mail step) | 4 (5th running) | done, attempts 2 | 1 | 0 | 1 | 52.9 each | 60.4 to 61.2 |
| K3 (killed after CRM write) | 2 (3 more running) | unknown, attempts 2 | 0 | 1 | 1 | 52.8, 52.9 | 60.1, 60.4 |
Reading for the caption: it takes about 53 s from n8n back up (lease 45 s + one 30 s sweep tick, minus where the clock was), and about 61 s from the moment of the kill when my restart takes 7 to 9 s. A 60 s limit counted from the kill is missed by 0.1 to 1.9 s in 9 of 11 runs; counted from n8n up it passes with 7 s to spare. Say which start point the caption uses. Lease 120 s gave 144 s.
Nothing lost, nothing doubled in any run: 1 CRM row each, intake mails 1 (K1, K2) or 0 (K3, with 1 alert).

ASK for the lead: which start point does the caption use (kill or n8n up)? If kill, 60 s is not met on these flow files; a lease of 30 s would meet it (my estimate, not measured).
FAILURES AND RETRIES: none new. Note: my progress lines for these runs print the old flow label "7709d058-v4"; the result rows carry the right label (873a908a-film-v4-lease45).
NOT DONE / NOT CHECKED (my list): K3 n = 5 and K2 n = 5 still finishing; K6 at lease 45 s; failed mark after a sent alert; comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) finish K2, K3; 2) K6 at lease 45 s n = 3 in the free lanes; 3) final RESULTS.md and compare; one video line.

## HEARTBEAT 190 (17:02Z) - lease 45 s runs started on 3 lanes (K1, K2, K3 on film-v4, n = 5, 5, 5 planned); v4 KS 2 of 2: alert at 780 s both

WORKERS: 3 lanes (my script processes), 0 language-model agents. Flow files: demo folder n8n-flows-film-v4 (demo commit 873a908a): I checked the difference to n8n-flows-v4 myself: only the lease (45 s instead of 120 s in the claim SQL of form, hook, recovery), 2 tries instead of 3, and a 10 s instead of 15 s timeout. Lane 1: K1 then K3. Lane 3: K2 then K3. Lane 0: K1 (from the end of the list) then K3. Each result now records recovery seconds (n8n up again to final state) AND kill-to-final seconds. First numbers about 17:10Z, all 15 runs about 17:45Z.

| v4 flows (lease 120 s), results so far | n | Result |
|---|---|---|
| KS (n8n killed while the alert send waits) | 2 | exactly 1 alert each, at 780 s and 780 s (13 min late; not lost) |
| K1 | 2 | done, 1 intake mail, 0 alerts, recovery 144.3 s and 144.3 s |
| K3 | 2 | unknown, 0 intake mails, 1 alert, recovery 144.3 s (first run had no timer) |
| K6 | 2 | unknown, 1 intake mail, 1 alert, recovery 144.2 and 144.4 s |
| K2 | 1 | done, recovery 144.2 s |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list): lease 45 s numbers (running); failed mark after a sent alert; comparison with the demo table; the demo's 60 s V7 limit at lease 45 s: expect about 70 s from n8n up (my guess from 144 s at 120 s, not measured).
WHAT I WOULD DO NEXT (ranked): 1) lease 45 s runs; 2) final RESULTS.md and compare; 3) one video line.

## HEARTBEAT 189 (16:55Z) - v4 KS (n8n killed while the alert send waits): exactly 1 alert, but 13 minutes late; K3, K6 repeats pass

WORKERS: 2 lanes (my script processes), 0 language-model agents. Lane 0: KS run 2 (ends about 17:05Z). Lane 2: K1 repeat. Lane 1 free: nothing left on my video path to start; the final RESULTS.md waits for the last runs.

| v4 flows (7709d058) | n | Result |
|---|---|---|
| KS: hold 90 s, n8n killed 10 s after the alert send began (killed at 40 s, up again at 46 s) | 1 (2nd running) | EXACTLY 1 alert, NOT lost, but it came at 780 s (13 min) after the unknown. State unknown, 1 intake mail, 1 CRM row, alert_attempts 2, alert_sent true. Reason (timeline): the killed send left a 12 min claim on the row; nothing releases it, so the next claim was after 12 min plus a sweep. This is the README's "up to 12 to 13 min late". The owner waits 13 min for the alert in this case. |
| K3 repeat | 2 total | unknown, 0 intake mails, 1 alert, 1 CRM row; recovery 144.3 s |
| K6 repeat | 2 total | unknown, 1 intake mail, 1 alert, 1 CRM row; recovery 144.4 s |
| K1 repeat | running | |
Earlier v4 numbers unchanged: B780 1 alert (720 s), B90 3 of 3 one alert, A 2 of 2, C 2 of 2, K1, K2 pass.

Suggestion for the demo (not tested by me): when n8n starts, clear the alert claims of rows with alert_sent false, so a kill during a send does not cost 12 minutes. n8n node: one extra SQL at start; no code. The lead decides.

ASK for the lead: is a 13 min late alert after an n8n kill acceptable for the video claim? If not, tell the demo session about the start-up clear.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list): KS run 2; K1 repeat; failed mark after a sent alert; comparison with the demo table; lease for the video (open question); n is 1 to 3 per case.
WHAT I WOULD DO NEXT (ranked): 1) finish KS 2 and K1; 2) final RESULTS.md and compare with the demo table; 3) one video line.

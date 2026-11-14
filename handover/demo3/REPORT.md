## HEARTBEAT 188 (16:45Z) - v4: B780 passes (1 alert, no duplicate); K2 passes; KS (kill during send) x2 and K3, K6, K1 repeats running

WORKERS: 3 lanes (my script processes), 0 language-model agents. Lane 0: KS run 2. Lane 1: KS run 1 (ends about 16:55Z). Lane 2: K3, K6, K1 repeats.

| v4 flows (7709d058) | n | Result |
|---|---|---|
| B780 (alert answer held 780 s, longer than the 12 min claim) | 1 | EXACTLY 1 alert, at 720 s; alert_attempts 2; state unknown; 1 intake mail; alert_sent true. No duplicate. Why (my reading, from the timeline, not traced in a log): the mail library gives up after 10 min silence, the send fails, AlertBackoff sets a short retry, the retry is not held. So the duplicate the README fears (send longer than 12 min) did not happen here because the library stops the wait at 10 min. |
| K2 (killed after the mail step) | 1 | done, attempts 2, 1 intake mail, 0 alerts, 1 CRM row, recovery 144.2 s |
| K1, K3, K6 | 1 each | pass (HB187); repeats running |
| B90 3 of 3, A 2 of 2, C 2 of 2 | | exactly 1 alert each |
Recovery seconds on v4 flow files: 144 s in K1, K2, K6 (lease 120 s in this folder). Question open: which lease the video flows use.

ASK for the lead: lease for the video (20 s or 120 s)?
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list): KS results (the kill-during-send case); K3, K6, K1 repeats; B780 n is 1; failed mark after a sent alert; comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) KS x2 results; 2) repeats; 3) final RESULTS.md and compare; one video line.

# Comparison with the demo session's numbers (written AFTER my numbers were saved; their files: K-SERIES-V4.md, V7-NUMBERS-lead-read.md)
Names differ: my K3 (killed when the mail connection opens, mail not delivered) = their K3B. My K6 (killed after the mail was stored) = their K3. Same results: K3B/my K3 1 CRM row, 0 intake mails, 1 alert, unknown; K3/my K6 1 / 1 / 1, unknown. My ERROR (CRM answers 500 to every call) = their T15: failed, 0 CRM rows, 0 mails, 1 alert. My A (alert refused twice) = their AF1: first alert 272 s there, 240 to 270 s here.
| Item | Demo (laptop, v3, lease 20 s) | Mine (cloud, my own harness) | Same? |
|---|---|---|---|
| K1, K2 end state | done, 0 lost, 0 doubled, n = 20 | done, 1 CRM row, 1 intake mail, n = 5 each at lease 45 s (and 1 to 2 at lease 120 s) | yes |
| K3 / K3B and my K6 | unknown, 1 alert, n = 20 each | unknown, 1 alert, n = 5 and 5 (lease 45 s) | yes |
| Kill to final seconds, K1 | 18.0 / 29.65 / 59.6 (min / median / max) | lease 45 s: 60.1 to 61.9, median 60.8; lease 120 s: about 152 | different leases, so no direct match. Spread differs: mine has almost none (60.1 to 61.9). I did not find the reason; my guess: my restart always makes the recovery timer start at the same moment, theirs varies. NOT verified. |
| ERROR / T15 | failed, 1 alert, 3 of 3 | failed, 1 alert, 3 of 3 (lease 45 s) | yes |
| Duplicate alert | B90 never run before; README predicted it | v3: 2 alerts in 3 of 3; v4: 1 alert in 3 of 3 | new from me |
| Kill while the alert send waits (KS) | not in their list | v4: 1 alert, 13 min late, 2 of 2 | new from me |
| Hold 780 s / SMTP dead 600 s | not in their list | v4: 1 alert each (720 s / 750 s) | new from me |
Not compared: T8, T10, T11, T13, T14 on v4 (I did not run them on v4; T14 and burst ran on my fixed flows earlier, see RESULTS.md Part 1).

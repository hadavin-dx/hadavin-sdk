## HEARTBEAT 177 (15:35Z) - v3 case C (SMTP dead 600 s) looks like a PASS so far (n = 1); final 150 s watch still running

| v3 flows 6ebb7f62, case C, n = 1 (read from the run's own event log and the database, not yet the saved result) | Numbers at 15:35Z |
|---|---|
| Lead mail | stored at 0 s, then dropped by the fake: state unknown, attempts 1, mail_sent true |
| Fake SMTP | dead (closes the connection without a greeting) from 0 s to 600 s |
| Alert tries while dead | 4 tries, at 29 s, 119 s, 239 s, 419 s: each refused, alert_attempts counts up, alert_sent stays false |
| Alert after restore | 5th try at about 690 s: accepted, 1 alert stored (to the alerts address), alert_sent true, alert_attempts 5 |
| Spin / extra load | none: 6 SMTP connections in total (1 lead mail, 4 refused, 1 alert), spacing 90 to 180 s |
| Counts (outside n8n, per lead id) | 1 intake mail, exactly 1 alert, 1 CRM row |
| Remaining | the 150 s check that no second alert appears (ends about 15:38Z); then V3B90 |

Note: the alert came about 90 s after the SMTP came back (restore at 600 s, next try at 690 s). Not a loss; the delay is the retry spacing.

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): C final verdict (150 s watch); V3B90; repeats (n = 2 or 3); K3/K6/T12/T11 on v3 (not ordered); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) finish C and B90; 2) repeats; 3) RESULTS.md, then compare.

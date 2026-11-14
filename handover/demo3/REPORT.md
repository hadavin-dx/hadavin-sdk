## HEARTBEAT 174 (15:12Z) - Fc1 3/3 on both flow sets: a held FIRST connection still gives exactly 1 alert; v3 case A (refuse twice) running since 15:11Z

| Item | Result at 15:12Z |
|---|---|
| Fc1 (SMTP holds only the FIRST connection 40 s, so the alert connection answers at once), fixed flows 61e3804b, n = 3 | 3 of 3: state unknown, attempts 1, 0 intake mails (the held lead mail was never stored), exactly 1 alert naming the lead, 1 CRM row, 1 model call. |
| Fc1 on the 11:05Z flows, n = 3 | 3 of 3 the same (unknown, 0 intake mails, 1 alert). |
| What F-c and Fc1 together say | The lost alert in F-c needs the alert path to fail too: when the mail server is slow only for the lead mail, the in-run alert works (6 of 6). When the server is slow for every connection (F-c, 6 of 6 with 0 alerts), nobody is told. That is exactly what v3's retry (alert as state) is meant to fix, so the v3 cases test it. |
| v3 cases (flows from demo commit 6ebb7f62, table with the four alert columns) | V3A (SMTP refuses the first two alert recipients with 451, then accepts) is running: started 15:11Z, expected about 6 minutes (backoff 120 s then 180 s). Then V3B20, V3C (10 min dead), V3B90, then repeats. Results as they land. |
| Sandbox | no restart since 13:50Z with my turn open. |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): V3A to V3C results; repeats; K1, K2 and the rest of the series on v3; RESULTS.md; comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) v3 A, B20, C, B90; 2) repeats; 3) RESULTS.md then compare.

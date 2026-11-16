# Load matrix 3: dpld-fix3-303127b UNPATCHED (Linux, 4 cores, 16 GB). Numbers only.
Same load.py as linux-load-2-baseline; no client retries. Raw: linux-load-3-fix3-raw.txt. Run 10:41-10:42Z (each scenario about 6 s, shared with a builder running tests, so latency is not clean).
| mode | scenario | status codes | 5xx | connection resets/client errors | max latency s | received vs outcomes | lost receipts |
|---|---|---|---|---|---|---|---|
| keyed | same x500 | 499x200, 1x201 | 0 | 0 | 2.31 | 500/500 | 0 |
| keyed | same x1000 | 999x200, 1x201 | 0 | 0 | 4.24 | 1000/1000 | 0 |
| keyed | diff x500 | 500x201 | 0 | 0 | 3.30 | 500/500 | 0 |
| keyed | diff x1000 | 994x201, 6x503 | 6 | 0 | 5.91 | 994/994 | 0 |
| blind | same x500 | 499x200, 1x201 | 0 | 0 | 2.34 | 500/500 | 0 |
| blind | same x1000 | 999x200, 1x201 | 0 | 0 | 3.58 | 1000/1000 | 0 |
| blind | diff x500 | 500x201 | 0 | 0 | 3.72 | 500/500 | 0 |
| blind | diff x1000 | 891x201, 109x503 | 109 | 0 | 7.24 | 911 received, 891 decided | 20 open receipts |
Compared with baseline (aed689a): connection resets are gone in all 8 scenarios (baseline 15 to 274 per scenario). Remaining on this tree: 503 under 1000 DIFFERENT leads (the database lock wait, F9) and, in the blind x1000 run, 20 receipts left open (received 911, decided 891). The final CRM/mail counts of that run: 891 rows, 891 emails, max 1 per lead. Single runs; variance between runs was large in the earlier baseline.

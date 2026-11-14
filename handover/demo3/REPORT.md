## HEARTBEAT 179 (15:52Z) - v3: A passes twice (n = 2), B90 repeat running; v4 probe built (demo commit 7709d058), v4 runs queued right after the v3 B90 repeats

| v3 flows (6ebb7f62), my own cases | n | Result |
|---|---|---|
| A (refuse alert recipient twice, then accept) | 2 | PASS both: exactly 1 alert each, at 240 s and 270 s, alert_sent true, 1 intake mail |
| B20 (hold 20 s) | 1 | PASS: 1 alert at 50 s |
| C (SMTP dead 600 s) | 1 | PASS: 1 alert at 690 s, 4 refused tries before |
| B90 (hold 90 s) | 1 done, 2nd running (v3b90b, started 15:51Z), 3rd queued | run 1: 2 alerts (see HB178). Trace of run 1 from the fake SMTP log: first alert connected at 36 s, held 90 s, finished at 126 s; the second connection began at 126 s (claim 1 ran out at about 96 s, the next sweep re-claimed). Both stored at 126 s. |

Order now (queue script run_n.sh; the lead's order): v3 B90 run 2, v3 B90 run 3, then on v4 (flow files from demo commit 7709d058, folder n8n-flows-v4, table unchanged): B90, A, C, B90 again; then the remaining v3 repeats (C, B20, A) and v4 A, C repeats if time allows. Expected on v4 by the demo README (my criteria, written before running): B90 exactly 1 alert and alert_attempts 1; A first alert still near the old 60 to 300 s backoff (not 12 min); C 1 alert after restore. I will report exact-1-alert counts and the time of the first alert per run. First v4 result about 16:10Z.

ASK for the lead: none.
FAILURES AND RETRIES: none new. (I stopped and restarted my own queue loop twice to reorder; the running test was not touched.)
NOT DONE / NOT CHECKED (my list, for the lead to decide): v4 results; v3 B90 runs 2 and 3; K3/K6/T12/T11 on v3 or v4 (not ordered); the n8n node log gives no alert node lines (execution saving is off, so the trace of B90 comes from the fake SMTP log only); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) v3 B90 repeats, then v4 B90, A, C; 2) RESULTS.md including v3 and v4; 3) compare with the demo table.

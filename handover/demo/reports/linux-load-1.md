# linux-load-1 (ORDER 199) - numbers only, no verdicts
Host: 4 cores, 16086 MB RAM, Linux 6.18, Python 3.12.3. Desk + fakes started as scripts/start_all.sh does (same module commands, own launcher /tmp/dpld-out/load.py, data on /tmp/dpld-out/data = the container disk), keyed and blind outbox, CRM keyed. Own stdlib thread script: one request per thread, start barrier, NO retries (the repo's demo_only/burst.py retries 503 and refused connects, so it would hide them; not used). Raw log: handover/demo/reports/linux-load-1-raw.txt (same content as /tmp/dpld-out/load-raw.txt). Each scenario starts a fresh database. Counts read 3 s after the burst.

## A. Simultaneous submissions (status = what the client saw; received = desk /counts)
| mode | scenario | sent | 201 | 200 | 5xx | client connection resets | desk received | new+dup+review+rejected | lost receipt | CRM rows (per lead max) | emails (per lead max) | max latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keyed | same lead x10 | 10 | 1 | 9 | 0 | 0 | 10 | 10 | 0 | 1 (1) | 1 (1) | 0.06 |
| keyed | same lead x100 | 100 | 1 | 99 | 0 | 0 | 100 | 100 | 0 | 1 (1) | 1 (1) | 1.11 |
| keyed | same lead x500 | 500 | 1 | 352 | 0 | 147 | 353 | 353 | 0 | 1 (1) | 1 (1) | 2.52 |
| keyed | same lead x1000 | 1000 | 1 | 575 | 0 | 424 | 576 | 576 | 0 | 1 (1) | 1 (1) | 2.86 |
| keyed | 100 different leads | 100 | 100 | 0 | 0 | 0 | 100 | 100 | 0 | 100 (1) | 100 (1) | 1.28 |
| blind | same lead x10 | 10 | 1 | 9 | 0 | 0 | 10 | 10 | 0 | 1 (1) | 1 (1) | 0.06 |
| blind | same lead x100 | 100 | 1 | 99 | 0 | 0 | 100 | 100 | 0 | 1 (1) | 1 (1) | 1.12 |
| blind | same lead x500 | 500 | 1 | 249 | 0 | 250 | 250 | 250 | 0 | 1 (1) | 1 (1) | 1.79 |
| blind | same lead x1000 | 1000 | 1 | 469 | 0 | 530 | 470 | 470 | 0 | 1 (1) | 1 (1) | 2.50 |
| blind | 100 different leads | 100 | 100 | 0 | 0 | 0 | 100 | 100 | 0 | 100 (1) | 100 (1) | 1.22 |

Important for reading the table: at 500 and 1000 simultaneous requests, 29% to 53% of the connections were reset by the server side BEFORE a request was read (ConnectionResetError at the client); those requests have no receipt, so "lost receipt = 0" counts only requests the desk saw. The reviewer's reading (unrun) is the listen queue of 64 in constants.py (LISTEN_QUEUE) with a thread per request; I did not confirm the cause (no ss/netstat or kernel counter was captured). A client that does not retry loses those submissions; the burst script's refused-connect retry exists for this. 1000 different leads was not run (the order asked for 100 different).

## B. kill -9 of the desk mid-burst, 10 times (5 keyed + 5 blind), 200 different leads per round
Method: 200 threads fire at once, each retries on connection error/503 up to 60 times with 0.25 s sleep (a client that retries the SAME request id); about 0.4 s after the start the desk gets SIGKILL, 0.5 s later it is restarted on the same database (start-up sweep runs). Counts read 5 s after the last client finished.
| mode | rounds | acked 2xx of 200 | 5xx | CRM rows (max per lead) | emails (max per lead) | retries by clients (per round) | lost receipt | open receipts | pending follow-ups |
|---|---|---|---|---|---|---|---|---|---|
| keyed | 5 | 200 each round | 0 | 200 (1) each round | 200 (1) each round | 61, 84, 72, 124, 126 | 0 | 0 | 0 |
| blind | 5 | 200 each round | 0 | 200 (1) each round | rounds 1-4: 200 (1); round 5: 199 (1) | 190, 138, 136, 123, 81 | 0 | 0 | 0 |
Blind round 5 (database kept, inspected afterwards): follow-ups sent=196, unknown=4 (last_error crash_while_sending); CRM 200 rows, emails 199. So 4 follow-ups were left UNKNOWN for a person (the design for blind mode); the desk's /counts does not show them (open=0, pending_followups=0, ok null here). I did not inspect the first four blind rounds' databases (each run starts a fresh one, only the last was left), so I cannot say whether they also had unknown rows; their email counts were 200.

## C. Not run / not measured
- 1000 DIFFERENT leads; 500 different leads; soak; fsync-slowed run; ulimit -n 256 run; busy-wait (503) counts under 150+ different-lead threads (at 100 different leads there were no 5xx).
- py3.13 for the demo; Windows.
- CPU/memory of the desk during bursts was not recorded.

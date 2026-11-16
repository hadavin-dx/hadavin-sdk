# linux-load-2-baseline (ORDER 201 D) - numbers only, no verdicts
Unpatched tree (commit 494244e = aed689a, /tmp/dpld-baseline), same harness as linux-load-1 (own thread script, no client retries, start barrier, fresh database per scenario, counts read 3 s after the burst), 4 cores, 16 GB, Linux 6.18, Python 3.12.3. Run 10:14-10:16Z while 3 agents (builder, test writer, hostile-run) were also using the machine, so CPU was shared; resets differ a lot from run to run (same-lead x500 keyed: 147 resets in linux-load-1, 15 here), so one run is not a rate. Raw log: linux-load-2-baseline-raw.txt.
| mode | scenario | sent | 5xx | client connection resets | desk received | lost receipt | follow-up states | open receipts | CRM rows (max per lead) | emails (max per lead) | max latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| keyed | same x500 | 500 | 0 | 15 | 485 | 0 | {'sent': 1} | 0 | 1 (1) | 1 (1) | 2.62 |
| keyed | same x1000 | 1000 | 0 | 274 | 726 | 0 | {'sent': 1} | 0 | 1 (1) | 1 (1) | 3.22 |
| keyed | diff x500 | 500 | 0 | 40 | 460 | 0 | {'sent': 460} | 0 | 460 (1) | 460 (1) | 2.89 |
| keyed | diff x1000 | 1000 | 0 | 172 | 828 | 0 | {'sent': 828} | 0 | 828 (1) | 828 (1) | 4.63 |
| blind | same x500 | 500 | 0 | 64 | 436 | 0 | {'sent': 1} | 0 | 1 (1) | 1 (1) | 2.40 |
| blind | same x1000 | 1000 | 0 | 145 | 855 | 0 | {'sent': 1} | 0 | 1 (1) | 1 (1) | 2.93 |
| blind | diff x500 | 500 | 0 | 53 | 447 | 0 | {'sent': 447} | 0 | 447 (1) | 447 (1) | 2.94 |
| blind | diff x1000 | 1000 | 0 | 219 | 781 | 0 | {'sent': 781} | 0 | 781 (1) | 781 (1) | 4.29 |

UNKNOWN follow-ups: none in any scenario (states are all 'sent'). Differing from linux-load-1: this table adds 500 and 1000 DIFFERENT leads. Requests that were reset never reached the desk, so they have no receipt and are not counted in "lost receipt"; the number of submissions that got no answer is the resets column (e.g. blind diff x1000: 219 of 1000). Patched-tree rerun waits for the patch and the laptop's listen-backlog change.

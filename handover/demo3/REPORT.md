## HEARTBEAT 181 (16:08Z) - v4 B90 PASSES (n = 1); v4 A, v4 C and v4 B90 repeat now run in 3 parallel lanes plus 1 trace agent

AGENTS AND LANES RIGHT NOW: 4 workers. 3 parallel test lanes (processes of my own script, not language-model agents: each has its own ports, its own database and its own n8n folder) + 1 trace agent (read-only, reading the n8n source and the recovery flow for B90; report file trace-b90-report.md). Lane 0: v4 A (started 16:05Z). Lane 1: v4 C (16:07Z), then v4 C repeat. Lane 2: v4 B90 repeat (16:07Z), then v4 A repeat. After v4 A ends, lane 0 runs the remaining v3 repeats (C, B20, A). Collision check: ports (crm, stage, smtp, n8n and the n8n task broker) are shifted per lane, the database is kill_t, kill_t1, kill_t2 (one table each), run folders are per label; nothing shared. Machine: 4 cores, load 1.5 with 3 lanes. Risk I name: all timing here is in seconds, so a loaded machine could shift times a few seconds; I will compare against the single-lane times.

| v4 flows (demo commit 7709d058), my cases, n = 1 | Result |
|---|---|
| B90 (hold 90 s) | PASS: exactly 1 alert (stored at 120 s), alert_attempts 1, alert_sent true, 1 intake mail, 1 CRM row, no second alert in the 150 s watch. The same case gave 2 alerts in 3 of 3 runs on v3 (alerts at 120+120, 120+120, 90+120 s). |
| A (refuse alert recipient twice) | running (lane 0) |
| C (dead 600 s) | running (lane 1) |
| B90 repeat | running (lane 2) |

Tool note: the lanes need a change in my own harness (ports, database and credential file per lane); single-lane runs (lane 0) are unchanged.

ASK for the lead: none.
FAILURES AND RETRIES: my own slip, named: two of my queue scripts waited on a process name that matched their own command line (would have waited forever); I caught it within 5 minutes and restarted them; no test result was affected.
NOT DONE / NOT CHECKED (my list, for the lead to decide): v4 A, C, B90 repeat results; the trace agent report; K3/K6/T12/T11 on v4 (not ordered); RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) finish the v4 cases and repeats; 2) fold in the trace report; 3) RESULTS.md with v3 and v4, then compare.

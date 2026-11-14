## HEARTBEAT 182 (16:13Z) - v4 B90 passes 2 of 2 (1 alert each); trace agent finished; v4 A and v4 C still running

AGENTS AND LANES NOW: 3 parallel test lanes (my own script processes): lane 0 v4 A, lane 1 v4 C, lane 2 starts v4 A repeat. The trace agent has finished and is closed (0 agents running).

| v4 flows (7709d058), hold 90 s (B90) | Result |
|---|---|
| Run 1 | 1 alert (stored 120 s), alert_attempts 1, alert_sent true, 1 intake mail, no second alert in 150 s |
| Run 2 (run in parallel with 2 other lanes) | 1 alert (120 s), alert_attempts 1, alert_sent true, 1 intake mail, 1 CRM row |
Same case on v3: 2 alerts in 3 of 3 runs. So v4 removes the duplicate in this case, n = 2.

Trace of the v3 duplicate (agent report evidence/trace-b90-report.md; read by me, I have not re-checked every line): name ALERT-CLAIM-SHORTER-THAN-SEND. Claim lasts 60 s, the held send took 90 s, the sweep (every 30 s) claimed the row again while send 1 waited, two sends ran on two connections. The mark (alert_sent = true) is guarded by the claim token, the send is not, so both mails go out. The Send Email node sets no timeout of its own; the library gives connect 2 min, greeting 30 s, socket silence 10 min (so one send can wait up to 10 min, which fits the v4 choice of a 12 min claim). Not verified by the agent or me: the database token rows during B90; why the 96 s sweep tick missed in runs 1 and 2 but hit in run 3 (no tick times in the n8n log); that the held answer was specifically the RCPT answer.

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): v4 A, v4 C results (due about 16:15Z and 16:25Z); repeats (v4 A, v4 C, then v3 C, B20, A); a hold longer than 12 min on v4 (would still give a duplicate by the demo README; not tested); K3/K6/T12/T11 on v4; RESULTS.md and comparison with the demo table.
WHAT I WOULD DO NEXT (ranked): 1) v4 A and C results and repeats; 2) RESULTS.md with v3 and v4; 3) compare with the demo table.

## HEARTBEAT 158 (12:50Z) - kill script RUNNING: BURST 3 of 3 pass; ERROR run 1 at attempt 3 of 3; GREP and T14 (fixed flows) queued

| Item (11:05Z flows unless stated; journal stage stand-in; fresh n8n folder per run) | Result at 12:50Z |
|---|---|
| BURST: 10 requests with the same lead id sent at once to /webhook/mf-form (production path), n = 3 | 3 of 3 identical: 1 CRM row, 1 mail to intake, 1 model call, 1 row done (attempts 1), 0 alerts; of the 10 answers, 1 was verdict new and 9 were repeat (state processing, repeat true). No answer was an error. |
| ERROR (CRM refuses every call with HTTP 500; expected: three tries, then failed + exactly 1 alert naming the lead, 0 other mails), n = 0 finished, run je1 in progress | row at 12:50Z: processing, attempts 3 of 3, waiting for the last lease (about 75 s) and the failed branch; je2 queued. Result in HB159. |
| GREP (planted fake address, name and fake key; look in n8n's database file, logs, exported flow JSON; Postgres table checked apart), n = 0 | queued (3 runs after ERROR). |
| T14 idle 120 s on the FIXED flows (commit 8e2b6960; expect 0 stage calls, 0 alerts, 0 mails), n = 0 | queued (3 runs after GREP). The fixed flows differ from the 11:05Z set in mf-sub-crm-mail (20 nodes, was 19) and mf-recovery (7 nodes, was 5). |
| Table so far (make_results.py, n = number of runs with that exact outcome) | K1 3/3 done 1 mail 1 CRM 1 model call; K2 3/3 same; K3 3/3 unknown, 0 mails, 1 alert; K6 3/3 unknown, 1 mail, 1 alert; Fa 1, Fb 1, Fc 1 (Fc: unknown, 0 alerts delivered, see HB157); BURST 3/3; controls: single, same twice, two at once, bad e-mail all as expected. Fault repeats (n = 3 each) queued after T14. |
| Disk | 2.7G free, 94% used |

ASK for the lead: none.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): ERROR result, GREP, T14, fault repeats; no comparison with the demo compare table (after my numbers are saved); K1-K6 on the fixed flows not planned unless you want them; WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish queues (about 13:45Z); 2) write kill/RESULTS.md; 3) compare with the compare table; 4) optional K1-K6 on the fixed flows; 5) WINDOWS-RUN-1 additions.


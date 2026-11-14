## HEARTBEAT 152 (11:51Z) - kill script RUNNING: controls done, K1 run a in progress; one finding with proof (F-REC-EMPTY)

| Item | State at 11:51Z |
|---|---|
| Controls (v2 top-level files, fresh n8n folder each run) | 1 lead: done, 1 CRM row, 1 mail to intake, 1 stage call, 0 alerts (PASS). Same lead twice: second answer "repeat, done"; still 1 CRM row, 1 mail, 1 stage call (PASS). Bad e-mail: state review, 0 stage calls, 0 CRM rows, 0 mails (PASS). Two leads at once: both done, 1 mail each (PASS on state and mail); the CRM merged them because my test used one e-mail for both (my test-data slip; driver now uses one e-mail per lead; rerun cp2 is queued after the batch). |
| K1 run a (kill while stage call in flight) | in progress: kill landed while the stage call was open (fake logged peer_closed_before_answer), n8n restarted, row is processing attempts 1, lease expired, waiting for recovery. No result yet. |
| FINDING F-REC-EMPTY (proof: runs i1, c1L, k1a) | In n8n 2.46.6 the Postgres node Execute Query returns one item {success:true} when a non-SELECT statement (UPDATE ... RETURNING) matches no row (n8n source: nodes-base Postgres v2 executeQuery.operation.js line 351). So when mf-recovery has nothing to recover, ClaimStuck feeds that item to RunSub, and MarkFailed feeds it to AlertFailed. Every 30 s on an IDLE stack (no lead at all, run i1, 100 s) I see: 1 stage call with lead None, 1 CRM upsert with lead null, 1 alert mail "[demo] Lead desk: lead failed undefined" to alerts@example.test. Per-lead counting hides it because the subject says "undefined"; I report these totals per run as phantom counts. Likely fix for the demo session to judge: an IF "lead_key is not empty" after ClaimStuck and after MarkFailed. |
| Disk | 3.8G free, 91% used |

ASK for the lead: none.
FAILURES AND RETRIES: as HB151, plus: two leads at once shared one e-mail (my test data): fixed in the driver, cp2 queued. Nothing else new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K1 (2 more runs), K2, K3, K6 (3 runs each), F-a, F-b, F-c, controls cp2; idle result for the phantom effect on the count rule is reported separately; no comparison with the demo compare table yet (after my numbers are saved); WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish the batch (run_all.sh, about 18 more runs, expected end about 12:50Z); 2) cp2; 3) save numbers, then compare; 4) WINDOWS-RUN-1 additions.


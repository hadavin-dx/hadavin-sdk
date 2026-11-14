## HEARTBEAT 153 (12:02Z) - kill script RUNNING: K1 runs a and b done, same result; idle-recovery noise changed no lead count so far

| Item | State at 12:02Z |
|---|---|
| Flows under test | the 11:05Z Design A v2 top-level files (commit 59202078; mf-sub-crm-mail, mf-form, mf-hook, mf-recovery, mf_leads.sql), kept as is for the independence record, as you ordered. The fixed flows (pushed 11:56Z) are tested only after my current kill points. |
| K1 (kill while the stage call is in flight), stage stand-in with the README journal | run j1a: kill landed while the stage call was open; n8n restarted in 7.2 s; recovery took the lead after the lease ran out; final state done, attempts 2, 1 mail to intake, 1 CRM row, 1 model call (the repeat request got the stored answer, 2 stage requests), 0 alerts for the lead. Run j1b: same pattern, see table file once all three runs are done. j1c running. |
| Did idle-recovery noise change any count? | NO in every run so far: the phantom events (stage request with lead None, CRM upsert with lead null, alert mail "lead failed undefined") are 4, 4 and 5 per run and stay on their own keys. Caveat I state plainly: the phantom stage request for lead None is one more model call in total (journal key None), and the alerts mailbox gets extra mail, so a count of ALL alerts or ALL model calls per run is off by that noise; the per-lead count (the README rule) is not. analyze.py prints both. |
| Earlier controls (same v2 files) | 1 lead PASS; same lead twice PASS (1/1/1); bad e-mail PASS (review, nothing sent); two at once PASS on state, CRM merged by my shared e-mail (cp2 queued). |
| Disk | 3.6G free, 91% used |

ASK for the lead: none.
FAILURES AND RETRIES: stage fake changed once (named: it answered a repeat request with a fresh call; the README says it keeps a journal; run k1a kept as a recorded variant, j-runs are the real ones). Nothing else new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): K1 run c, K2, K3, K6 (3 runs each), F-a, F-b, F-c, cp2 not yet run; the fixed flows not tested yet (after my kill points, by your order); no comparison with the demo compare table yet; WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish the 11:05Z batch (about 12:40Z); 2) save my numbers (kill/RESULTS.md), then compare; 3) rerun K1-K6 and the faults on the fixed flows; 4) WINDOWS-RUN-1 additions.


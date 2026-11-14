## HEARTBEAT 159 (12:59Z) - kill script RUNNING: ERROR run 1 FAILED the expectation (lead lost, no alert); ERROR run 2, GREP, T14, fault repeats queued

| Item (11:05Z flows; journal stage stand-in; fresh n8n folder per run) | Result at 12:59Z |
|---|---|
| ERROR: the CRM refuses every call (HTTP 500) from the start; expected: 3 tries, then state failed and exactly 1 alert naming the lead, 0 other mails. n = 1 (je1) | NOT AS EXPECTED. The form answered HTTP 500 "Error in workflow" at once. The row went processing attempts 1, 2, 3 (leases 120 s apart) and then STAYED processing for the rest of the 700 s wait (about 4 minutes past the last lease): no failed state, 0 alerts, 0 mails to intake, 1 model call (3 stage requests, the extra two got the stored answer), 0 CRM rows. By the README counting rule this is LOST (no final state in time). |
| Cause (named; observed, not yet proven by a fix) | F-REC-EMPTY again, now with a worse effect. mf-recovery has two branches from the same timer: ClaimStuck then RunSub, and MarkFailed then AlertFailed. Every 30 s the empty claim feeds a phantom item to RunSub; with the CRM refusing, RunSub fails (my fake logged 66 refused upserts for lead null plus 9 for the lead in this run), the run ends in error, and the second branch (MarkFailed) apparently never runs. Evidence: 0 alerts mails in 13 minutes while the row sat at attempts 3 with an expired lease. The fixed flows (8e2b6960) guard the empty item, so ERROR on them (fe1, fe2) is queued to see if failed + 1 alert now happens. |
| n = 1 so far for ERROR | je2 runs next (13 minutes each); the claim above needs both. |
| Earlier results | unchanged: K1, K2 3/3 done; K3, K6 3/3 unknown; BURST 3/3 pass; faults n = 1 each (repeats queued). |
| Disk | 2.6G free, 94% used |

ASK for the lead: none. Forward to the demo session: ERROR on the 11:05Z flows ends with a lead stuck in processing and no alert (see Cause).
FAILURES AND RETRIES: none of mine. (An expectation failed; that is a test result, not a harness failure.)
NOT DONE / NOT CHECKED (my list, for the lead to decide): ERROR run 2 and the two ERROR runs on the fixed flows; GREP; T14; fault repeats; the cause is observed from fake logs and row state, not proven by a patched copy of the flow; no comparison with the demo compare table (after my numbers are saved); WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish queues (about 14:15Z); 2) write kill/RESULTS.md; 3) compare; 4) optional: patched copy of mf-recovery to prove the cause; 5) WINDOWS-RUN-1 additions.


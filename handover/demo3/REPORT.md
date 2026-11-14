## HEARTBEAT 164 (13:41Z) - SECOND SANDBOX RESTART at 13:40Z killed ferr2 (void); queue restarted as a resumable script; answer to the lead's GREP question

| Item | Status at 13:41Z |
|---|---|
| ferr2 and ferr3 | NO RESULT YET. The sandbox restarted again at 13:40Z (uptime 0 min at 13:40:38Z; the first restart was 13:15Z). It killed ferr2 about 7 minutes in (CRM refusals in progress, no result written). Cause named: sandbox restart, 25 minutes after the first; I do not know why it restarts (nothing in my files). ferr2 is rerun from the start (13:41Z, ends about 13:54Z), ferr3 after it. |
| Queue change | run_g.sh is resumable: it starts Postgres if down and skips labels already saved. Order: ferr2, ferr3, T14, BURST, K3 x3, K6 x3 on the fixed flows (61e3804b), then GREP on the fixed flows (as you ordered, label fjg1; after ERROR/T14/BURST/K3/K6 because all runs share the same ports and cannot run at the same time), then the fault repeats on the 11:05Z flows. If it restarts again I restart the same script; I have no way to stop the sandbox restarting. |
| Your question: where is my KEY needle? | In the REQUEST BODY of the form webhook, field api_key. The harness POSTs JSON to /webhook/mf-form with these fields: submission_id (the lead id), email = "zq" + ".canary@example.test", name = "Zelda" + " Quasar-Canary", api_key = "CANARY" + "KEY" + "-" + "7f3a9c2e" (all built from parts in harness.py lines 306-308). It is NOT in a node, a credential or a flow file. It reached n8n's file because n8n stores the whole webhook request (headers and body) in its execution data while the run is open. In the 11:05Z jg3 file I read the stored item: headers, then {submission_id, email, name, api_key}, then the URL and "production". I did not plant a fake SMTP password; the SMTP credential holds the stand-in text "stand-in", which I did not search for. So the two needles differ: mine is a webhook BODY field; if T7b's key is in a node field or a credential, an absent hit there is not a contradiction. Please tell me where T7b plants its key; I can then run mine with the same place. |
| Old-flow GREP n = 3 | unchanged: 3 of 3 hits in database.sqlite-wal for name, e-mail, key. |
| First fixed-flow result so far | ERROR ferr1 passed (HB163). |
| Disk | 4.3G free |

ASK for the lead: where T7b plants the key (node, field, file), and whether it sends the key in the request body.
FAILURES AND RETRIES: ferr2 void (sandbox restart 13:40Z), rerun started 13:41Z. jg3 first attempt void (my stray process, HB162).
NOT DONE / NOT CHECKED (my list, for the lead to decide): everything after ferr1 on the fixed flows; fixed-flow GREP; fault repeats; RESULTS.md; compare.
WHAT I WOULD DO NEXT (ranked): 1) finish the queue, restarting it after each sandbox restart; 2) fjg1; 3) RESULTS.md then compare.

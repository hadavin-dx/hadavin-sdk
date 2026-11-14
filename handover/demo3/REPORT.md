## HEARTBEAT 157 (12:42Z) - kill script RUNNING: K1, K2, K3, K6 done (3 runs each); F-a, F-b, F-c once each; BURST 1 of 3 done; ERROR, GREP, T14 queued

| Item (11:05Z flows, journal stage stand-in, fresh n8n folder per run) | Result at 12:42Z |
|---|---|
| K6 kill after the mail was stored, before state done, n = 3 | 3 of 3 the same: unknown, attempts 2, 1 mail to intake, 1 CRM row, 1 model call, 1 alert naming the lead, no second mail. |
| K1 n = 3 / K2 n = 3 / K3 n = 3 | K1 and K2: done, 1 mail, 1 CRM row, 1 model call, 0 alerts. K3: unknown, 0 mails, 1 CRM row, 1 model call, 1 alert. All 3 of 3 each. |
| F-a (CRM search empty after create), n = 1 | done, 1 mail, 1 CRM row, 1 model call, 0 alerts. These flows never search the CRM (they call the upsert), so this fault has nothing to bite on; recorded as observed. |
| F-b (SMTP accepts the mail then drops the connection), n = 1 | unknown, attempts 1, 1 mail stored, 1 CRM row, 1 model call, 1 alert naming the lead. No resend. |
| F-c (SMTP greeting delayed 40 s, longer than n8n's mail timeout of about 30 s), n = 1 | OBSERVED HOLE: final state unknown, 0 mails stored, 0 alerts delivered (0 mails in the catcher at all for the lead). Timeline: mail connection at 8 s, node gives up at about 38 s, state unknown, the alert connects to the same slow SMTP at 38 s, times out, and the AlertUnknown node swallows the error (continueRegularOutput). The form request itself ran past my 60 s driver limit (the caller saw a timeout). So when the mail channel is the thing that fails, the alert goes through the same channel and is lost; only the table says unknown. |
| cp2 (two leads at once, one e-mail each) | both done, 1 mail each, 1 CRM row each, 1 model call each. (the first control's merge was my shared e-mail, fixed.) |
| BURST: 10 requests, same lead id, at once, production path /webhook/mf-form, n = 1 so far (jb1) | 1 CRM row, 1 mail, 1 model call, 1 row done (attempts 1); answers: 1 verdict new and 9 answered repeat (9 x state processing, repeat true). Two more runs queued. |
| ERROR (CRM refuses every call, expect failed + exactly 1 alert), GREP (planted address, name and fake key), T14 (idle 120 s on the FIXED flows 8e2b6960, 3 runs) | queued: run_b.sh after BURST (about 25 min for ERROR, GREP, then T14 about 8 min). Extra F-a/F-b/F-c runs (n = 3 each) queued after that. |
| Noise | still no per-lead count changed in K runs (4 phantom stage, 4 phantom CRM, 5 phantom alert mails per 3.5-minute run). |
| Disk | 2.8G free, 93% used |

ASK for the lead: none. FYI for the demo session: the F-c hole above (alert shares the failing mail channel).
FAILURES AND RETRIES: none new since HB153 (my driver 60 s limit is not a failure of the flow).
NOT DONE / NOT CHECKED (my list, for the lead to decide): BURST runs 2 and 3, ERROR, GREP, T14 and fault repeats not run yet; no comparison with the demo compare table (after my numbers are saved); all runs on the 11:05Z flows except T14; the fixed flows get K1-K6 only if you want it after T14; WINDOWS-RUN-1 additions not written.
WHAT I WOULD DO NEXT (ranked): 1) finish queues (about 13:40Z); 2) write kill/RESULTS.md with sample sizes; 3) compare with the compare table; 4) optional: K1-K6 on the fixed flows; 5) WINDOWS-RUN-1 additions.


# V7 numbers READ BY THE LEAD from raw files (2026-11-14 16:27Z). Runner abefbabd, laptop, v3 flows commit 6ebb7f62e, lease 20 s, made-up data. Raw: egm\duplicate-proof-lead-desk\addendum6\raw-designA-laptop\V7-v3\<TEST>\<run>\mf_result_<TEST>.json (laptop-local, not pushed). Status of every row: MEASURED by the demo harness on the laptop; independent harness = lane3 (separate file). T10, T11, T13 not yet finished at this time. NOT run on v3: AF2, T12, K4, K5, lease table. v4 flows (alert duplicate fix) are NOT covered by this file: V4-par runner ab612cf8 is running them.
| Test | what was done | n | pass flag | lost | doubled | unknown | per lead: CRM rows / intake mails / alerts / model calls | note |
|---|---|---|---|---|---|---|---|---|
| AF1 | alert-only SMTP refusal (451 x2) | 1 | true | 0 | 0 | 1 | 1 / 1 / 1 / 1 | first alert 272.1 s, no alert at 20 s |
| T8 | model stage refuses/errors/times out incl. recovery retries (3 tries) | 3 | true | 0 | 0 | 0 | 0 / 0 / 1 / 0 | state failed, exactly 1 alert, 0 CRM writes, 0 model calls |
| T15 | CRM answers HTTP 500 from the start | 3 | true | 0 | 0 | 0 | 0 / 0 / 1 / 1 | state failed, alerts [1,1,1], 0 mails, 0 CRM rows, 91+ s to final |
| T14 | idle stack 120 s | - | true | - | - | - | all 0 | 0 stage, model, CRM, SMTP, table rows |
| K3 | n8n killed after the mail was delivered, before the table update | 20 | true | 0 | 0 | 20 | 1 / 1 / 1 / 1 | UNKNOWN counted, 1 alert each, not re-mailed |
| K3B | n8n killed after mail_sent set, mail NOT yet delivered | 20 | true | 0 | 0 | 20 | 1 / 0 / 1 / 1 | UNKNOWN counted, 1 alert each, no intake mail |
| K1 | n8n killed after claim insert, before CRM write | 20 | true | 0 | 0 | 0 | 1 / 1 / 0 / 1 | recovery completed every lead (0 lost, 0 doubled) |
| K2 | n8n killed after CRM write, before the mail step | 20 | true | 0 | 0 | 0 | 1 / 1 / 0 / 1 | recovery completed every lead |
Reading (lead): on v3 the kill series shows 0 lost and 0 doubled in K1, K2, K3, K3B (80 kills), T8/T15 failures end as failed with exactly 1 alert and no mail, no CRM write, no model call (T8), T14 idle = zero traffic. UNKNOWN (K3/K3B) is the doubtful case by design and always raises 1 alert. Known v3 flaw: when the alert send takes longer than the 60 s first claim, 2 alerts are sent (lane3 B90: 3 of 3 runs on v3); v4 fixes it in lane3's runs (B90 n=2 exactly 1 alert) but v4 is not yet in this file. Decision criteria not yet complete: recovery <= 60 s per lead at lease 20 s not read here (see mf_result recovery seconds); lease 45/120 s table not run.

## V7 FINAL (runner abefbabd report, 16:33Z; calendar 15:02-16:32Z, 11 tests, all pass flag true, rc 0; lead re-read raw for K1,K2,K3,K3B,T10,T11 seconds; T13 from the runner report, lead has not re-read its raw file)
| Test | n | lost | doubled | unknown | seconds kill to final min/median/max | note |
|---|---|---|---|---|---|---|
| T10 | 10 | 0 | 0 | 3 (mail delivered in 3) | 16.6 / 29.95 / 41.8 | lease shorter than SMTP hold: safe but unneeded unknown allowed by the runbook |
| T11 | 8 | 0 | 0 | 0 | 6.0 / 6.95 / 8.1 | |
| T13 | 13 | 0 | 0 | 0 | 0.3 / 5.8 / 7.7 | |
| K1 | 20 | 0 | 0 | 0 | 18.0 / 29.65 / 59.6 | criterion 60 s: margin 0.4 s at lease 20 s |
| K2 | 20 | 0 | 0 | 0 | 17.3 / 29.5 / 59.4 | margin 0.6 s |
| K3 | 20 | 0 | 0 | 20 | 28.5 / 29.45 / 30.5 | |
| K3B | 20 | 0 | 0 | 20 | 28.4 / 29.45 / 31.0 | |
| T8 | 3 | 0 | 0 | 0 (3 failed) | 88.4 / 116.9 / 42.5 (refuse/error/timeout) | 1 alert each, SMTP connections = alerts |
| T15 | 3 | 0 | 0 | 0 (3 failed) | 91.2 / 88.3 / 110.1 (limit 210) | 1 alert each, 27 CRM calls refused |
Caveats stated by the runner: result JSON of K1,K2,K3,K3B,T10,T11,T13 has no per-lead alert count (pass logic folds it under "doubled", not separately verified); no process of the runner left running.

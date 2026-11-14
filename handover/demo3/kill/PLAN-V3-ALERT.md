# Plan: my own alert-loss cases for Design A v3 (written 15:03Z, before any v3 run)

Order from the lead: write my own cases for "the owner gets exactly 1 alert for an unknown lead even when the SMTP refuses or hangs at alert time", run them on the demo's v3 flows (demo commit 6ebb7f62; flow folder n8n-flows-v3, lease 120 s; flow files, the table DDL and V3-README read, nothing else of the demo's). I did NOT read the demo's own AF1 code; I know from the README that AF1 is "refuse the first two alert recipients", which is the lead's case (a); my version is written from the lead's wording.

## What I measure (outside n8n, per lead)
Mails to intake (subject has the lead id, recipient intake), alert mails (recipient alerts), state, alert_sent, alert_attempts (from the table), CRM rows, model calls. Times: when the lead went unknown, when each alert mail was stored.

## Common set-up (every case)
Fresh n8n folder, fresh fakes, v3 table columns added (ALTER TABLE ... ADD COLUMN IF NOT EXISTS for the four alert columns, then TRUNCATE). One lead is sent. The lead mail is stored by the fake SMTP and then the connection is dropped (the existing "drop" mode), so n8n sees an error after the mail was stored: the lead goes unknown with exactly 1 mail to intake. From then only the alert path is faulted.

## Cases (fault only on the alert connection unless said)
- V3A: the fake SMTP answers 451 to the RCPT of the first two alert connections (recipient starts with "alerts@"), then accepts. Expect: state stays unknown; 0 alerts until the third try; then exactly 1 alert; alert_sent true; 1 intake mail; still 1 alert 150 s after alert_sent turned true. By the README's backoff (120 s, then 180 s) the third try is about 5 to 6 minutes after unknown.
- V3B20: the fake accepts the connection and the first alert RCPT but holds its answer 20 s (shorter than the first claim window of 60 s), then answers normally. Expect: exactly 1 alert, alert_sent true.
- V3B90: same hold of 90 s (longer than the first claim window of 60 s, shorter than the mail library's own socket timeout, which I have not measured). The README says a second alert can arrive here. Expected by me: exactly 1 alert is NOT guaranteed; I record the count (1 or 2) and whether the first connection stored a mail.
- V3C: the fake SMTP is dead for 600 s starting the moment the lead mail is stored: every new connection is closed at once without a greeting. After 600 s it answers normally. Expect: state unchanged, 0 alerts for 600 s, alert_sent false during that time, then exactly 1 alert within one backoff step (at most 300 s) after restoration, alert_sent true, 1 intake mail, 0 further alerts after another 150 s.

## Pass criterion per case
state unchanged (unknown), intake mails = 1, alert mails = 1 after restoration, alert_sent = true, no second alert within 150 s after alert_sent. V3B90 is recorded, not judged. Sample size: n = 1 per case first (about 40 minutes in all), repeats as time allows; sample sizes named in every report.

## Not covered (named)
Alert node on a hung connection longer than the mail library's own timeout; `failed` state (CRM refuses everything) with a faulted alert; two recovery copies; film and real folders; the lease 45 s film values.

## Added 2026-11-14 (written before running): two extra cases on the v4 flows (demo commit 7709d058)
- B780: the fake SMTP holds the alert answer 780 s (longer than the 12 min claim, and longer than the 10 min socket silence limit read from the mail library). My reading before the run: the library gives up at 600 s, the send fails, AlertBackoff sets a short retry, the retry is not held, so 1 alert. Pass = exactly 1 alert, state unknown, 1 intake mail, alert_sent true, 0 lost. If 2 alerts come, I record it; not a pass.
- KS: the hold is 90 s; 10 s after the hold starts I kill n8n (SIGKILL) and start it again. My reading before the run: the killed send never stored a mail, the claim runs out at 12 min, the sweep re-claims, 1 alert late (about 12 to 13 min). Pass = exactly 1 alert, never 0, state unknown, 1 intake mail. Time of the alert recorded.
Not covered: a failed mark after a sent alert (needs a database fault; not built).

# lane3 kill script: plan and pass criteria (written 2026-11-14 ~11:13Z BEFORE any run)
Independence: written from the six flow JSON files, mf_leads.sql and DESIGN-A-README.md of branch demo/handover (commit 59202078, "Design A v2", lease 120). I did NOT open any demo result file. One disclosed exception: at 11:05Z I read ~40 lines of handover/demo/n8n-kill-between-steps.md (a different test workflow, 5 kill counts). My predictions below are from the README rules, not from those numbers. The stand-ins, driver and counting are my own code.

## What is tested (made-up data, loopback only, no spend, no secrets)
n8n 2.46.6 (npm, fresh user folder per run), Postgres 16 scratch cluster, my own fakes: CRM (upsert, search, create, control), stage (qualify, label by a fixed rule from the lead id, journal, call count), SMTP catcher (store, delay, pre-greeting delay, drop). The six committed flows, lease 120 s as committed (a shorter-lease variant is a separate, labelled run).

## Kill points (my reading; the lead has not defined T1-T3, T6: ASKED in HB148, no answer yet, so these are MY labels K1..K6, mapped later)
- K1 killed while the stage call is in flight (row processing, nothing external done).
- K2 killed after the CRM stored the lead, before the answer reached n8n.
- K3 killed after mail_sent=true was written, before the mail was stored.
- K6 killed after the mail was stored by the catcher, before the state done was written.
- Kill = SIGKILL of the n8n process at the moment a fake reports the event (not a sleep guess). Then restart n8n on the same Postgres and fakes, wait for recovery (up to 5 minutes), then count.
- Fault modes F-a CRM search empty for N s after a create; F-b SMTP accepts then drops the connection; F-c SMTP delay past the node's own timeout (what the node does is recorded as observed).
- Controls first (no kill): one lead, the same lead twice, two different leads at once, an invalid e-mail.

## Counting (outside n8n, from the fakes and the table; per README counting rule)
per lead id: CRM rows, mails (subject "[demo] lead <id>"), stage calls, alerts (mail to the alert address), final state in mf_leads.
FAIL = more than 1 CRM row, mail, stage call or alert for one lead id (doubled); or no final state after 5 minutes (lost); or state done without its CRM row or mail.
PASS = each lead ends done, review, unknown (1 alert) or failed (after 3 tries, 1 alert) with no doubled count.

## My predictions (from the README text, written before running)
K1 done, 1 CRM, 1 mail after recovery. K2 done, 1 CRM (keyed upsert), 1 mail. K3 unknown, 0 mails, 1 alert (mail_sent already true: no resend). K6 unknown, 1 mail, 1 alert. Controls: first call done, repeat call answers the stored state, no second CRM/mail. Invalid e-mail: review, 0 CRM, 0 mail.
Pass or fail is per row; each kill point is run 3 times on fresh stacks; any run that differs from the others is a finding with its own name.

## Not covered (stated now)
queue mode, other n8n versions, Postgres kill, real CRM/SMTP/model, two n8n processes, Windows.

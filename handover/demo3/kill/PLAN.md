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

## Changes made after the plan was pushed (11:54Z, written before the j-runs; honest list)
1. Flow files: the first copy of mf-form, mf-hook and mf-recovery was the obsolete 10:45Z set (my slip); runs c1, c1b, c1c are void. Tested set: v2 top level only (mf-sub-crm-mail, mf-form, mf-hook, mf-recovery, mf_leads.sql as pushed, no table patch).
2. Harness gaps fixed (each with a named cause): sub-workflow must be published; wait until the webhook is registered; one e-mail per lead (the CRM upsert also matches on e-mail).
3. Stage stand-in: my first stage fake answered a repeat request with a fresh call (run k1a, "naive stage": final done, 1 CRM row, 1 mail, 2 stage requests). The README says the real stage keeps a journal (no second model call). The fake now follows the README: requests and model_calls are counted separately; the counting rule uses model_calls. Runs with the journal stage are labelled j*. k1a stays in results.jsonl as a recorded variant and is not part of the final table.
4. New finding found by the idle test (i1): F-REC-EMPTY (see REPORT). It adds phantom totals per run (stage call with lead None, CRM upsert with lead null, alert "lead failed undefined"); they are reported next to the per-lead counts.
5. Predictions in this plan were written from the README; they are compared only after my numbers are saved.

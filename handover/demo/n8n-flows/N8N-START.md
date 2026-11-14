# N8N-START (final text for D-N3). Written by the cloud demo session; the real-node flows are BUILT, NOT RUN.

## Versions (the flows were built and tested against exactly these; nothing is claimed for other versions)
- n8n 2.46.6, pinned (npm install n8n@2.46.6 into an empty folder; check `npm ls n8n`), regular mode (no queue), SQLite inside n8n. Node.js 24.22.x. Postgres 16 for the lead table (separate from n8n's own SQLite).
- n8n 2.47.7 changes execution redaction: NOT checked by me.

## The three environment variables (the only ones the real-node flows read)
```
DESK_URL=<base address of the desk stage, loopback: the cap + model endpoint>
DESK_TIMEOUT_MS=10000
DESK_ALERT_TO=<the alert recipient address>
```
Also needed by n8n itself so that nodes may read them: N8N_BLOCK_ENV_ACCESS_IN_NODE=false (n8n 2.46.6 default blocks $env in nodes). The mail recipient for new leads is a constant inside the SendMail node (replace INTAKE_ADDRESS_PLACEHOLDER), not an environment variable.

## Execution saving: all four settings are REQUIRED
```
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_ON_ERROR=none
EXECUTIONS_DATA_SAVE_ON_PROGRESS=false
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false
```
What each does (names read from the n8n 2.46.6 source, @n8n/config; effect as I understand it, not each measured on its own):
- SAVE_ON_SUCCESS=none: n8n stores no run data (node inputs and outputs, which hold lead name and e-mail) for runs that succeed.
- SAVE_ON_ERROR=none: the same for runs that fail.
- SAVE_ON_PROGRESS=false: n8n does not write run data node by node while a run is going; with this on, content is saved during the run even if the end-of-run setting is none.
- SAVE_MANUAL_EXECUTIONS=false: runs started by hand from the editor are not saved either.
Without them n8n keeps run data. The lane3 grep (as relayed by the lead, n=1, flows without the four settings): lead name, e-mail AND the key were in the write-ahead file. With the four settings queued (lane3, n=3) and in the laptop T7b: see the T7b section; name and e-mail were still found in the write-ahead file there. The settings reduce what is stored; they do not make it zero. Every flow also carries the same values in its own workflow settings (saveDataSuccessExecution none, saveDataErrorExecution none, saveManualExecutions false).

## Webhook
The lead entries are two webhooks (paths mf-form and mf-hook, Respond to Webhook). Bind n8n to loopback only (N8N_LISTEN_ADDRESS=LOOPBACK-ADDR, N8N_HOST=LOOPBACK, port 5678 by default; the demo harness used 5679), so the webhook is reachable from the machine itself only. The recovery flow runs from its own 30 s timer; it must be ACTIVE (n8n logs "not active and cannot be executed" otherwise) and so must the two entry flows.

## Where each secret lives
n8n credentials only: HubSpot private-app token (credential hubspot-app-token), the SMTP password / Gmail app password (mf-mail-smtp), the Postgres password (n8n-publish-pg). They are encrypted at rest by N8N_ENCRYPTION_KEY (keep that key out of git and out of flows). No key is a node parameter, a header text, an environment variable of the flows or part of a flow file. The desk's model key lives in the desk side's own key file, never in n8n.

## What the scan test (T7b) showed
As relayed to me by the lead from the laptop runner (flows commit 1ced4e1f, first version of the test, grep only, 572 files, one machine, made-up data): lead name (3 hits) and e-mail (2 hits) were found ONLY in n8n's write-ahead file (database.sqlite-wal); the planted fake model key and the planted fake SMTP password were in NO file (main database file, log, flow JSON, other files). T7b started its own n8n with the four settings set (code reading of mf.py T7b: it sets the four before its own restart; the first n8n of the run and the setup step ran without them; to be confirmed from the raw file). RAW FILE NAME: PENDING (the raw output is not in my repo yet; until the file is named this is the lead's relayed result, not something I measured). Whether the name and e-mail also sit in the main database file after a checkpoint: the extended T7b (commit 444dcbf6) answers it, result pending. Statement for the page: the lead name and e-mail may stay in n8n's write-ahead file until a checkpoint; keys and passwords did not reach n8n's files in that test. The test did not search the Postgres lead table (it holds the name and e-mail by design).
Earlier finding by lane3 (independent) on the 11:05Z flows: the planted key was found in the write-ahead file there. My flows never pass a key through n8n in either version (no key, header or credential text in any flow); how the key got into n8n on that run is not known to me.

## What the real-node flows were NOT tested against
HubSpot search or write lag, rate limits, property creation, the contacts v1 endpoint on a real account; a real Gmail server (the node has no timeout setting; TLS and app-password handling); and no run of the four real-node files at all (built, not run). The stand-in versions were tested on one machine, with made-up data, no real mailbox, no spend, not independently.
## Not in this file
Per-lease recovery times (no measured table yet; see PAGE-STATEMENTS-DRAFT.md and the laptop lease runs).

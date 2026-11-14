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

## What the scan test (T7b) showed (read this before you tell anyone "no lead data is kept")
Facts as relayed to me by the lead (raw file names NOT given to me yet; I wrote none of these numbers as mine):
- Laptop T7b, first version (flows commit 1ced4e1f, four settings on, grep only, 572 files): lead name 3 hits and e-mail 2 hits, ONLY in the write-ahead file; the planted fake model key and fake SMTP password in no file.
- Laptop V5 T7b (four settings on): name 3 and e-mail 2 in LIVE rows of the execution_data table; fake key, fake SMTP password and the stage key file: none.
- lane3 HB171 (independent): with the four settings the webhook REQUEST BODY (name, e-mail, and a key sent as a body field) is still in the write-ahead file and, after a checkpoint, in execution_data. Cause per lane3, from the n8n source: a run that is not to be saved is only marked deleted and removed later by pruning. lane3 is testing EXECUTIONS_DATA_PRUNE=false; result pending.
What the page may say (conditions: one machine, made-up data, flows 1ced4e1f):
1. Credentials (SMTP password, HubSpot token, Postgres password) and the stage key file never reached n8n's data folder in these scans. They are in n8n credentials (encrypted by N8N_ENCRYPTION_KEY) or in a file n8n does not read.
2. The lead fields (name, e-mail) DO reach n8n's database through the webhook request body, even with the four settings on, until n8n's pruning removes the run. So the four settings reduce what is kept; they do not make n8n keep nothing.
3. Nobody must send a secret in a lead form field: lane3 saw a key sent as a body field in the same place.
Pruning settings (names and defaults read from the n8n 2.46.6 source, @n8n/config; what they do in a run is NOT measured by me): EXECUTIONS_DATA_PRUNE (default true), EXECUTIONS_DATA_MAX_AGE (hours, default 336), EXECUTIONS_DATA_PRUNE_MAX_COUNT (default 10000), EXECUTIONS_DATA_HARD_DELETE_BUFFER (hours, default 1), EXECUTIONS_DATA_PRUNE_HARD_DELETE_INTERVAL (default 15) and EXECUTIONS_DATA_PRUNE_SOFT_DELETE_INTERVAL (default 60). I have no measured time after which the body is gone; the sentence stays "removed by n8n's pruning, age not measured" until lane3's test names the setting and the age. Do not write "deleted after N hours" without that file.
Earlier lane3 finding on the 11:05Z flows (no settings): the planted key was in the write-ahead file. My flows never put a key into n8n; the likely route is a key sent as a body field (matches HB171), not proven.

## What the real-node flows were NOT tested against
HubSpot search or write lag, rate limits, property creation, the contacts v1 endpoint on a real account; a real Gmail server (the node has no timeout setting; TLS and app-password handling); and no run of the four real-node files at all (built, not run). The stand-in versions were tested on one machine, with made-up data, no real mailbox, no spend, not independently.
## Not in this file
Per-lease recovery times (no measured table yet; see PAGE-STATEMENTS-DRAFT.md and the laptop lease runs).

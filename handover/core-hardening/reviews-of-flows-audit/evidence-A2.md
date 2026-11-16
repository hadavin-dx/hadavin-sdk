# Evidence A2: flow dump (raw facts, no judgement)
- target branch/head (as given in brief; the scratchpad copy has no .git directory, so the sha could not be checked from the files): cloud/flows-audit 35235ace26a516d932e73542c235875f390f333d
- date UTC: 2026-11-16 07:58:03
- script: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/a2/dump_a2.py (run as python3 -I)
- sha256 of the 8 files:
  305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de  real-v5/mf-hook.json
  74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8  real-v5/mf-form.json
  03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759  real-v5/mf-recovery.json
  b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36  real-v5/mf-sub-crm-mail.json
  305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de  film-v5/mf-hook.json
  74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8  film-v5/mf-form.json
  42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79  film-v5/mf-recovery.json
  a0215012962e2e22e3923ed9ecb14bae472e0857636b7356f61e87190968918b  film-v5/mf-sub-crm-mail.json

## real-v5/mf-hook.json
workflow name: Lead desk main frame: e-mail-style entry; settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Receive | n8n-nodes-base.webhook | v2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Item | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Valid | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Claim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- Claimed | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- IsProcessing | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SubInput | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyRan | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyReview | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Stored | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- ReplyStored | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- Receive: {"main[0]": ["Item"]}
- Item: {"main[0]": ["Valid"]}
- Valid: {"main[0]": ["Claim"]}
- Claim: {"main[0]": ["Claimed"]}
- Claimed: {"main[0]": ["IsProcessing"], "main[1]": ["Stored"]}
- IsProcessing: {"main[0]": ["SubInput"], "main[1]": ["ReplyReview"]}
- SubInput: {"main[0]": ["RunSub"]}
- RunSub: {"main[0]": ["ReplyRan"]}
- ReplyRan: (no outgoing connections)
- ReplyReview: (no outgoing connections)
- Stored: {"main[0]": ["ReplyStored"]}
- ReplyStored: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Receive: onError=None extra-outputs=none
- Item: onError=None extra-outputs=none
- Valid: onError=None extra-outputs=none
- Claim: onError=None extra-outputs=none
- Claimed: onError=None extra-outputs={"main[1]": ["Stored"]}
- IsProcessing: onError=None extra-outputs={"main[1]": ["ReplyReview"]}
- SubInput: onError=None extra-outputs=none
- RunSub: onError=None extra-outputs=none
- ReplyRan: onError=None extra-outputs=none
- ReplyReview: onError=None extra-outputs=none
- Stored: onError=None extra-outputs=none
- ReplyStored: onError=None extra-outputs=none
### incoming edges per node
- Receive <- []
- Item <- ['Receive:main[0]']
- Valid <- ['Item:main[0]']
- Claim <- ['Valid:main[0]']
- Claimed <- ['Claim:main[0]']
- IsProcessing <- ['Claimed:main[0]']
- SubInput <- ['IsProcessing:main[0]']
- RunSub <- ['SubInput:main[0]']
- ReplyRan <- ['RunSub:main[0]']
- ReplyReview <- ['IsProcessing:main[1]']
- Stored <- ['Claimed:main[1]']
- ReplyStored <- ['Stored:main[0]']
### nodes with no incoming edge: ["Receive"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### Claim (n8n-nodes-base.postgres)
query:
INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
### alert/mail nodes (name contains Alert or Mail)
### credentials per node (names only)
- Claim: {"postgres": "n8n-publish-pg"}
- Stored: {"postgres": "n8n-publish-pg"}
### webhook nodes
- Receive: path=mf-hook httpMethod=POST authentication=(key absent) responseMode=responseNode all-parameters={"httpMethod": "POST", "path": "mf-hook", "responseMode": "responseNode", "options": {}} credentials={}
### environment variable reads ($env. / process.env), by node
- none found
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Claim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- Stored | n8n-nodes-base.postgres | onError=None | error-output edge present: no

## real-v5/mf-form.json
workflow name: Lead desk main frame: form entry; settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Receive | n8n-nodes-base.webhook | v2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Item | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Valid | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Claim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- Claimed | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- IsProcessing | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SubInput | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyRan | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyReview | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Stored | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- ReplyStored | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- Receive: {"main[0]": ["Item"]}
- Item: {"main[0]": ["Valid"]}
- Valid: {"main[0]": ["Claim"]}
- Claim: {"main[0]": ["Claimed"]}
- Claimed: {"main[0]": ["IsProcessing"], "main[1]": ["Stored"]}
- IsProcessing: {"main[0]": ["SubInput"], "main[1]": ["ReplyReview"]}
- SubInput: {"main[0]": ["RunSub"]}
- RunSub: {"main[0]": ["ReplyRan"]}
- ReplyRan: (no outgoing connections)
- ReplyReview: (no outgoing connections)
- Stored: {"main[0]": ["ReplyStored"]}
- ReplyStored: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Receive: onError=None extra-outputs=none
- Item: onError=None extra-outputs=none
- Valid: onError=None extra-outputs=none
- Claim: onError=None extra-outputs=none
- Claimed: onError=None extra-outputs={"main[1]": ["Stored"]}
- IsProcessing: onError=None extra-outputs={"main[1]": ["ReplyReview"]}
- SubInput: onError=None extra-outputs=none
- RunSub: onError=None extra-outputs=none
- ReplyRan: onError=None extra-outputs=none
- ReplyReview: onError=None extra-outputs=none
- Stored: onError=None extra-outputs=none
- ReplyStored: onError=None extra-outputs=none
### incoming edges per node
- Receive <- []
- Item <- ['Receive:main[0]']
- Valid <- ['Item:main[0]']
- Claim <- ['Valid:main[0]']
- Claimed <- ['Claim:main[0]']
- IsProcessing <- ['Claimed:main[0]']
- SubInput <- ['IsProcessing:main[0]']
- RunSub <- ['SubInput:main[0]']
- ReplyRan <- ['RunSub:main[0]']
- ReplyReview <- ['IsProcessing:main[1]']
- Stored <- ['Claimed:main[1]']
- ReplyStored <- ['Stored:main[0]']
### nodes with no incoming edge: ["Receive"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### Claim (n8n-nodes-base.postgres)
query:
INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
### alert/mail nodes (name contains Alert or Mail)
### credentials per node (names only)
- Claim: {"postgres": "n8n-publish-pg"}
- Stored: {"postgres": "n8n-publish-pg"}
### webhook nodes
- Receive: path=mf-form httpMethod=POST authentication=(key absent) responseMode=responseNode all-parameters={"httpMethod": "POST", "path": "mf-form", "responseMode": "responseNode", "options": {}} credentials={}
### environment variable reads ($env. / process.env), by node
- none found
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Claim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- Stored | n8n-nodes-base.postgres | onError=None | error-output edge present: no

## real-v5/mf-recovery.json
workflow name: Lead desk main frame: recovery (every 30 s); settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Every30s | n8n-nodes-base.scheduleTrigger | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ClaimStuck | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- StuckRow | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- MarkFailed | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertClaim | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertRow | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- AlertSend | n8n-nodes-base.emailSend | v2.1 | onError=continueErrorOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- AlertBackoff | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertMark | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
### connections (every output, as stored: type[index] -> targets)
- Every30s: {"main[0]": ["MarkFailed", "ClaimStuck", "AlertClaim"]}
- ClaimStuck: {"main[0]": ["StuckRow"]}
- StuckRow: {"main[0]": ["RunSub"]}
- RunSub: (no outgoing connections)
- MarkFailed: (no outgoing connections)
- AlertClaim: {"main[0]": ["AlertRow"]}
- AlertRow: {"main[0]": ["AlertSend"]}
- AlertSend: {"main[0]": ["AlertMark"], "main[1]": ["AlertBackoff"]}
- AlertBackoff: (no outgoing connections)
- AlertMark: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Every30s: onError=None extra-outputs=none
- ClaimStuck: onError=continueRegularOutput extra-outputs=none
- StuckRow: onError=None extra-outputs=none
- RunSub: onError=continueRegularOutput extra-outputs=none
- MarkFailed: onError=continueRegularOutput extra-outputs=none
- AlertClaim: onError=continueRegularOutput extra-outputs=none
- AlertRow: onError=None extra-outputs=none
- AlertSend: onError=continueErrorOutput extra-outputs={"main[1]": ["AlertBackoff"]}
- AlertBackoff: onError=continueRegularOutput extra-outputs=none
- AlertMark: onError=continueRegularOutput extra-outputs=none
### incoming edges per node
- Every30s <- []
- ClaimStuck <- ['Every30s:main[0]']
- StuckRow <- ['ClaimStuck:main[0]']
- RunSub <- ['StuckRow:main[0]']
- MarkFailed <- ['Every30s:main[0]']
- AlertClaim <- ['Every30s:main[0]']
- AlertRow <- ['AlertClaim:main[0]']
- AlertSend <- ['AlertRow:main[0]']
- AlertBackoff <- ['AlertSend:main[1]']
- AlertMark <- ['AlertSend:main[0]']
### nodes with no incoming edge: ["Every30s"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### ClaimStuck (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;"
}
#### MarkFailed (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;"
}
#### AlertClaim (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertBackoff (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
### alert/mail nodes (name contains Alert or Mail)
#### AlertClaim | n8n-nodes-base.postgres
incoming: ['Every30s:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertRow | n8n-nodes-base.if
incoming: ['AlertClaim:main[0]']
parameters (masked):
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.lead_key }}",
    "operator": {
     "operation": "notEmpty",
     "singleValue": true,
     "type": "string"
    },
    "rightValue": null
   }
  ],
  "options": {
   "caseSensitive": true,
   "leftValue": "",
   "typeValidation": "loose"
  }
 },
 "options": {}
}
#### AlertSend | n8n-nodes-base.emailSend
incoming: ['AlertRow:main[0]']
parameters (masked):
{
 "emailFormat": "text",
 "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
 "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
 "toEmail": "={{ $env.DESK_ALERT_TO }}"
}
#### AlertBackoff | n8n-nodes-base.postgres
incoming: ['AlertSend:main[1]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark | n8n-nodes-base.postgres
incoming: ['AlertSend:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
### credentials per node (names only)
- ClaimStuck: {"postgres": "n8n-publish-pg"}
- MarkFailed: {"postgres": "n8n-publish-pg"}
- AlertClaim: {"postgres": "n8n-publish-pg"}
- AlertSend: {"smtp": "mf-mail-smtp"}
- AlertBackoff: {"postgres": "n8n-publish-pg"}
- AlertMark: {"postgres": "n8n-publish-pg"}
### webhook nodes
### environment variable reads ($env. / process.env), by node
- AlertSend: ['$env.DESK_ALERT_TO']
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- ClaimStuck | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- MarkFailed | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertClaim | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertSend | n8n-nodes-base.emailSend | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["AlertBackoff"]}
- AlertBackoff | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertMark | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no

## real-v5/mf-sub-crm-mail.json
workflow name: Lead desk main frame: CRM + mail (sub-workflow); settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- SubIn | n8n-nodes-base.executeWorkflowTrigger | v1.1 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Qualify | n8n-nodes-base.httpRequest | v4.2 | onError=continueErrorOutput | retryOnFail=True | maxTries=2 | waitBetweenTries=1000 | extra={}
- LabelOk | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- CrmUpsert | n8n-nodes-base.hubspot | v2.2 | onError=continueErrorOutput | retryOnFail=True | maxTries=2 | waitBetweenTries=1000 | extra={}
- SetCrmId | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- CrmIdOk | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OwnsClaim1 | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- MailClaim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MailRowBack | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SendMail | n8n-nodes-base.emailSend | v2.1 | onError=continueErrorOutput | retryOnFail=False | maxTries=None | waitBetweenTries=None | extra={}
- MarkDone | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MarkUnknownA | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MarkUnknownB | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- UnknownNewA | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- UnknownNew | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- DoneOwned | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutDone | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutUnknown | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutStage | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutLost | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- SubIn: {"main[0]": ["Qualify"]}
- Qualify: {"main[0]": ["LabelOk"], "main[1]": ["OutStage"]}
- LabelOk: {"main[0]": ["CrmUpsert"], "main[1]": ["OutStage"]}
- CrmUpsert: {"main[0]": ["SetCrmId"], "main[1]": ["OutStage"]}
- SetCrmId: {"main[0]": ["CrmIdOk"]}
- CrmIdOk: {"main[0]": ["OwnsClaim1"], "main[1]": ["OutStage"]}
- OwnsClaim1: {"main[0]": ["MailClaim"], "main[1]": ["OutLost"]}
- MailClaim: {"main[0]": ["MailRowBack"]}
- MailRowBack: {"main[0]": ["SendMail"], "main[1]": ["MarkUnknownB"]}
- SendMail: {"main[0]": ["MarkDone"], "main[1]": ["MarkUnknownA"]}
- MarkDone: {"main[0]": ["DoneOwned"]}
- MarkUnknownA: {"main[0]": ["UnknownNewA"]}
- MarkUnknownB: {"main[0]": ["UnknownNew"]}
- UnknownNewA: {"main[0]": ["OutUnknown"], "main[1]": ["OutUnknown"]}
- UnknownNew: {"main[0]": ["OutUnknown"], "main[1]": ["OutUnknown"]}
- DoneOwned: {"main[0]": ["OutDone"], "main[1]": ["OutLost"]}
- OutDone: (no outgoing connections)
- OutUnknown: (no outgoing connections)
- OutStage: (no outgoing connections)
- OutLost: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- SubIn: onError=None extra-outputs=none
- Qualify: onError=continueErrorOutput extra-outputs={"main[1]": ["OutStage"]}
- LabelOk: onError=None extra-outputs={"main[1]": ["OutStage"]}
- CrmUpsert: onError=continueErrorOutput extra-outputs={"main[1]": ["OutStage"]}
- SetCrmId: onError=None extra-outputs=none
- CrmIdOk: onError=None extra-outputs={"main[1]": ["OutStage"]}
- OwnsClaim1: onError=None extra-outputs={"main[1]": ["OutLost"]}
- MailClaim: onError=None extra-outputs=none
- MailRowBack: onError=None extra-outputs={"main[1]": ["MarkUnknownB"]}
- SendMail: onError=continueErrorOutput extra-outputs={"main[1]": ["MarkUnknownA"]}
- MarkDone: onError=None extra-outputs=none
- MarkUnknownA: onError=None extra-outputs=none
- MarkUnknownB: onError=None extra-outputs=none
- UnknownNewA: onError=None extra-outputs={"main[1]": ["OutUnknown"]}
- UnknownNew: onError=None extra-outputs={"main[1]": ["OutUnknown"]}
- DoneOwned: onError=None extra-outputs={"main[1]": ["OutLost"]}
- OutDone: onError=None extra-outputs=none
- OutUnknown: onError=None extra-outputs=none
- OutStage: onError=None extra-outputs=none
- OutLost: onError=None extra-outputs=none
### incoming edges per node
- SubIn <- []
- Qualify <- ['SubIn:main[0]']
- LabelOk <- ['Qualify:main[0]']
- CrmUpsert <- ['LabelOk:main[0]']
- SetCrmId <- ['CrmUpsert:main[0]']
- CrmIdOk <- ['SetCrmId:main[0]']
- OwnsClaim1 <- ['CrmIdOk:main[0]']
- MailClaim <- ['OwnsClaim1:main[0]']
- MailRowBack <- ['MailClaim:main[0]']
- SendMail <- ['MailRowBack:main[0]']
- MarkDone <- ['SendMail:main[0]']
- MarkUnknownA <- ['SendMail:main[1]']
- MarkUnknownB <- ['MailRowBack:main[1]']
- UnknownNewA <- ['MarkUnknownA:main[0]']
- UnknownNew <- ['MarkUnknownB:main[0]']
- DoneOwned <- ['MarkDone:main[0]']
- OutDone <- ['DoneOwned:main[0]']
- OutUnknown <- ['UnknownNewA:main[0]', 'UnknownNewA:main[1]', 'UnknownNew:main[0]', 'UnknownNew:main[1]']
- OutStage <- ['Qualify:main[1]', 'LabelOk:main[1]', 'CrmUpsert:main[1]', 'CrmIdOk:main[1]']
- OutLost <- ['OwnsClaim1:main[1]', 'DoneOwned:main[1]']
### nodes with no incoming edge: ["SubIn"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### SetCrmId (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;"
}
#### MailClaim (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MarkDone (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownA (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownB (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;"
}
### alert/mail nodes (name contains Alert or Mail)
#### MailClaim | n8n-nodes-base.postgres
incoming: ['OwnsClaim1:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MailRowBack | n8n-nodes-base.if
incoming: ['MailClaim:main[0]']
parameters (masked):
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.lead_key }}",
    "operator": {
     "operation": "notEmpty",
     "singleValue": true,
     "type": "string"
    },
    "rightValue": null
   }
  ],
  "options": {
   "caseSensitive": true,
   "leftValue": "",
   "typeValidation": "loose"
  }
 },
 "options": {}
}
#### SendMail | n8n-nodes-base.emailSend
incoming: ['MailRowBack:main[0]']
parameters (masked):
{
 "emailFormat": "text",
 "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}",
 "text": "made-up thank-you text",
 "toEmail": "INTAKE_ADDRESS_PLACEHOLDER"
}
### credentials per node (names only)
- CrmUpsert: {"hubspotAppToken": "hubspot-app-token"}
- SetCrmId: {"postgres": "n8n-publish-pg"}
- MailClaim: {"postgres": "n8n-publish-pg"}
- SendMail: {"smtp": "mf-mail-smtp"}
- MarkDone: {"postgres": "n8n-publish-pg"}
- MarkUnknownA: {"postgres": "n8n-publish-pg"}
- MarkUnknownB: {"postgres": "n8n-publish-pg"}
### webhook nodes
### environment variable reads ($env. / process.env), by node
- Qualify: ['$env.DESK_TIMEOUT_MS', '$env.DESK_URL']
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Qualify | n8n-nodes-base.httpRequest | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["OutStage"]}
- SetCrmId | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MailClaim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- SendMail | n8n-nodes-base.emailSend | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["MarkUnknownA"]}
- MarkDone | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MarkUnknownA | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MarkUnknownB | n8n-nodes-base.postgres | onError=None | error-output edge present: no

## film-v5/mf-hook.json
workflow name: Lead desk main frame: e-mail-style entry; settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Receive | n8n-nodes-base.webhook | v2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Item | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Valid | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Claim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- Claimed | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- IsProcessing | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SubInput | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyRan | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyReview | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Stored | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- ReplyStored | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- Receive: {"main[0]": ["Item"]}
- Item: {"main[0]": ["Valid"]}
- Valid: {"main[0]": ["Claim"]}
- Claim: {"main[0]": ["Claimed"]}
- Claimed: {"main[0]": ["IsProcessing"], "main[1]": ["Stored"]}
- IsProcessing: {"main[0]": ["SubInput"], "main[1]": ["ReplyReview"]}
- SubInput: {"main[0]": ["RunSub"]}
- RunSub: {"main[0]": ["ReplyRan"]}
- ReplyRan: (no outgoing connections)
- ReplyReview: (no outgoing connections)
- Stored: {"main[0]": ["ReplyStored"]}
- ReplyStored: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Receive: onError=None extra-outputs=none
- Item: onError=None extra-outputs=none
- Valid: onError=None extra-outputs=none
- Claim: onError=None extra-outputs=none
- Claimed: onError=None extra-outputs={"main[1]": ["Stored"]}
- IsProcessing: onError=None extra-outputs={"main[1]": ["ReplyReview"]}
- SubInput: onError=None extra-outputs=none
- RunSub: onError=None extra-outputs=none
- ReplyRan: onError=None extra-outputs=none
- ReplyReview: onError=None extra-outputs=none
- Stored: onError=None extra-outputs=none
- ReplyStored: onError=None extra-outputs=none
### incoming edges per node
- Receive <- []
- Item <- ['Receive:main[0]']
- Valid <- ['Item:main[0]']
- Claim <- ['Valid:main[0]']
- Claimed <- ['Claim:main[0]']
- IsProcessing <- ['Claimed:main[0]']
- SubInput <- ['IsProcessing:main[0]']
- RunSub <- ['SubInput:main[0]']
- ReplyRan <- ['RunSub:main[0]']
- ReplyReview <- ['IsProcessing:main[1]']
- Stored <- ['Claimed:main[1]']
- ReplyStored <- ['Stored:main[0]']
### nodes with no incoming edge: ["Receive"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### Claim (n8n-nodes-base.postgres)
query:
INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
### alert/mail nodes (name contains Alert or Mail)
### credentials per node (names only)
- Claim: {"postgres": "n8n-publish-pg"}
- Stored: {"postgres": "n8n-publish-pg"}
### webhook nodes
- Receive: path=mf-hook httpMethod=POST authentication=(key absent) responseMode=responseNode all-parameters={"httpMethod": "POST", "path": "mf-hook", "responseMode": "responseNode", "options": {}} credentials={}
### environment variable reads ($env. / process.env), by node
- none found
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Claim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- Stored | n8n-nodes-base.postgres | onError=None | error-output edge present: no

## film-v5/mf-form.json
workflow name: Lead desk main frame: form entry; settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Receive | n8n-nodes-base.webhook | v2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Item | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Valid | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Claim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- Claimed | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- IsProcessing | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SubInput | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyRan | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ReplyReview | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Stored | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- ReplyStored | n8n-nodes-base.respondToWebhook | v1.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- Receive: {"main[0]": ["Item"]}
- Item: {"main[0]": ["Valid"]}
- Valid: {"main[0]": ["Claim"]}
- Claim: {"main[0]": ["Claimed"]}
- Claimed: {"main[0]": ["IsProcessing"], "main[1]": ["Stored"]}
- IsProcessing: {"main[0]": ["SubInput"], "main[1]": ["ReplyReview"]}
- SubInput: {"main[0]": ["RunSub"]}
- RunSub: {"main[0]": ["ReplyRan"]}
- ReplyRan: (no outgoing connections)
- ReplyReview: (no outgoing connections)
- Stored: {"main[0]": ["ReplyStored"]}
- ReplyStored: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Receive: onError=None extra-outputs=none
- Item: onError=None extra-outputs=none
- Valid: onError=None extra-outputs=none
- Claim: onError=None extra-outputs=none
- Claimed: onError=None extra-outputs={"main[1]": ["Stored"]}
- IsProcessing: onError=None extra-outputs={"main[1]": ["ReplyReview"]}
- SubInput: onError=None extra-outputs=none
- RunSub: onError=None extra-outputs=none
- ReplyRan: onError=None extra-outputs=none
- ReplyReview: onError=None extra-outputs=none
- Stored: onError=None extra-outputs=none
- ReplyStored: onError=None extra-outputs=none
### incoming edges per node
- Receive <- []
- Item <- ['Receive:main[0]']
- Valid <- ['Item:main[0]']
- Claim <- ['Valid:main[0]']
- Claimed <- ['Claim:main[0]']
- IsProcessing <- ['Claimed:main[0]']
- SubInput <- ['IsProcessing:main[0]']
- RunSub <- ['SubInput:main[0]']
- ReplyRan <- ['RunSub:main[0]']
- ReplyReview <- ['IsProcessing:main[1]']
- Stored <- ['Claimed:main[1]']
- ReplyStored <- ['Stored:main[0]']
### nodes with no incoming edge: ["Receive"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### Claim (n8n-nodes-base.postgres)
query:
INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
### alert/mail nodes (name contains Alert or Mail)
### credentials per node (names only)
- Claim: {"postgres": "n8n-publish-pg"}
- Stored: {"postgres": "n8n-publish-pg"}
### webhook nodes
- Receive: path=mf-form httpMethod=POST authentication=(key absent) responseMode=responseNode all-parameters={"httpMethod": "POST", "path": "mf-form", "responseMode": "responseNode", "options": {}} credentials={}
### environment variable reads ($env. / process.env), by node
- none found
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Claim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- Stored | n8n-nodes-base.postgres | onError=None | error-output edge present: no

## film-v5/mf-recovery.json
workflow name: Lead desk main frame: recovery (every 30 s); settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- Every30s | n8n-nodes-base.scheduleTrigger | v1.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- ClaimStuck | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- StuckRow | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- RunSub | n8n-nodes-base.executeWorkflow | v1.2 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- MarkFailed | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertClaim | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertRow | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- AlertSend | n8n-nodes-base.emailSend | v2.1 | onError=continueErrorOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- AlertBackoff | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
- AlertMark | n8n-nodes-base.postgres | v2.5 | onError=continueRegularOutput | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": false}
### connections (every output, as stored: type[index] -> targets)
- Every30s: {"main[0]": ["MarkFailed", "ClaimStuck", "AlertClaim"]}
- ClaimStuck: {"main[0]": ["StuckRow"]}
- StuckRow: {"main[0]": ["RunSub"]}
- RunSub: (no outgoing connections)
- MarkFailed: (no outgoing connections)
- AlertClaim: {"main[0]": ["AlertRow"]}
- AlertRow: {"main[0]": ["AlertSend"]}
- AlertSend: {"main[0]": ["AlertMark"], "main[1]": ["AlertBackoff"]}
- AlertBackoff: (no outgoing connections)
- AlertMark: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- Every30s: onError=None extra-outputs=none
- ClaimStuck: onError=continueRegularOutput extra-outputs=none
- StuckRow: onError=None extra-outputs=none
- RunSub: onError=continueRegularOutput extra-outputs=none
- MarkFailed: onError=continueRegularOutput extra-outputs=none
- AlertClaim: onError=continueRegularOutput extra-outputs=none
- AlertRow: onError=None extra-outputs=none
- AlertSend: onError=continueErrorOutput extra-outputs={"main[1]": ["AlertBackoff"]}
- AlertBackoff: onError=continueRegularOutput extra-outputs=none
- AlertMark: onError=continueRegularOutput extra-outputs=none
### incoming edges per node
- Every30s <- []
- ClaimStuck <- ['Every30s:main[0]']
- StuckRow <- ['ClaimStuck:main[0]']
- RunSub <- ['StuckRow:main[0]']
- MarkFailed <- ['Every30s:main[0]']
- AlertClaim <- ['Every30s:main[0]']
- AlertRow <- ['AlertClaim:main[0]']
- AlertSend <- ['AlertRow:main[0]']
- AlertBackoff <- ['AlertSend:main[1]']
- AlertMark <- ['AlertSend:main[0]']
### nodes with no incoming edge: ["Every30s"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### ClaimStuck (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;"
}
#### MarkFailed (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;"
}
#### AlertClaim (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertBackoff (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
### alert/mail nodes (name contains Alert or Mail)
#### AlertClaim | n8n-nodes-base.postgres
incoming: ['Every30s:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertRow | n8n-nodes-base.if
incoming: ['AlertClaim:main[0]']
parameters (masked):
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.lead_key }}",
    "operator": {
     "operation": "notEmpty",
     "singleValue": true,
     "type": "string"
    },
    "rightValue": null
   }
  ],
  "options": {
   "caseSensitive": true,
   "leftValue": "",
   "typeValidation": "loose"
  }
 },
 "options": {}
}
#### AlertSend | n8n-nodes-base.emailSend
incoming: ['AlertRow:main[0]']
parameters (masked):
{
 "emailFormat": "text",
 "fromEmail": "desk@example.test",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
 "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
 "toEmail": "alerts@example.test"
}
#### AlertBackoff | n8n-nodes-base.postgres
incoming: ['AlertSend:main[1]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark | n8n-nodes-base.postgres
incoming: ['AlertSend:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
### credentials per node (names only)
- ClaimStuck: {"postgres": "n8n-publish-pg"}
- MarkFailed: {"postgres": "n8n-publish-pg"}
- AlertClaim: {"postgres": "n8n-publish-pg"}
- AlertSend: {"smtp": "mf-mail-smtp"}
- AlertBackoff: {"postgres": "n8n-publish-pg"}
- AlertMark: {"postgres": "n8n-publish-pg"}
### webhook nodes
### environment variable reads ($env. / process.env), by node
- none found
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- ClaimStuck | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- MarkFailed | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertClaim | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertSend | n8n-nodes-base.emailSend | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["AlertBackoff"]}
- AlertBackoff | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no
- AlertMark | n8n-nodes-base.postgres | onError=continueRegularOutput | error-output edge present: no

## film-v5/mf-sub-crm-mail.json
workflow name: Lead desk main frame: CRM + mail (sub-workflow); settings: {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": false}; top-level keys: ['name', 'nodes', 'connections', 'settings']
### nodes in order (name | type | typeVersion | onError | retryOnFail | maxTries | waitBetweenTries | other top-level keys)
- SubIn | n8n-nodes-base.executeWorkflowTrigger | v1.1 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- Qualify | n8n-nodes-base.httpRequest | v4.2 | onError=continueErrorOutput | retryOnFail=True | maxTries=2 | waitBetweenTries=1000 | extra={}
- LabelOk | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- CrmUpsert | n8n-nodes-base.httpRequest | v4.2 | onError=continueErrorOutput | retryOnFail=True | maxTries=2 | waitBetweenTries=1000 | extra={}
- SetCrmId | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- CrmIdOk | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OwnsClaim1 | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- MailClaim | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MailRowBack | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- SendMail | n8n-nodes-base.emailSend | v2.1 | onError=continueErrorOutput | retryOnFail=False | maxTries=None | waitBetweenTries=None | extra={}
- MarkDone | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MarkUnknownA | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- MarkUnknownB | n8n-nodes-base.postgres | v2.5 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={"alwaysOutputData": true}
- UnknownNewA | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- UnknownNew | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- DoneOwned | n8n-nodes-base.if | v2.2 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutDone | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutUnknown | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutStage | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
- OutLost | n8n-nodes-base.set | v3.4 | onError=None | retryOnFail=None | maxTries=None | waitBetweenTries=None | extra={}
### connections (every output, as stored: type[index] -> targets)
- SubIn: {"main[0]": ["Qualify"]}
- Qualify: {"main[0]": ["LabelOk"], "main[1]": ["OutStage"]}
- LabelOk: {"main[0]": ["CrmUpsert"], "main[1]": ["OutStage"]}
- CrmUpsert: {"main[0]": ["SetCrmId"], "main[1]": ["OutStage"]}
- SetCrmId: {"main[0]": ["CrmIdOk"]}
- CrmIdOk: {"main[0]": ["OwnsClaim1"], "main[1]": ["OutStage"]}
- OwnsClaim1: {"main[0]": ["MailClaim"], "main[1]": ["OutLost"]}
- MailClaim: {"main[0]": ["MailRowBack"]}
- MailRowBack: {"main[0]": ["SendMail"], "main[1]": ["MarkUnknownB"]}
- SendMail: {"main[0]": ["MarkDone"], "main[1]": ["MarkUnknownA"]}
- MarkDone: {"main[0]": ["DoneOwned"]}
- MarkUnknownA: {"main[0]": ["UnknownNewA"]}
- MarkUnknownB: {"main[0]": ["UnknownNew"]}
- UnknownNewA: {"main[0]": ["OutUnknown"], "main[1]": ["OutUnknown"]}
- UnknownNew: {"main[0]": ["OutUnknown"], "main[1]": ["OutUnknown"]}
- DoneOwned: {"main[0]": ["OutDone"], "main[1]": ["OutLost"]}
- OutDone: (no outgoing connections)
- OutUnknown: (no outgoing connections)
- OutStage: (no outgoing connections)
- OutLost: (no outgoing connections)
### error output edges (output index 1 where node onError=continueErrorOutput; and any main[>=1])
- SubIn: onError=None extra-outputs=none
- Qualify: onError=continueErrorOutput extra-outputs={"main[1]": ["OutStage"]}
- LabelOk: onError=None extra-outputs={"main[1]": ["OutStage"]}
- CrmUpsert: onError=continueErrorOutput extra-outputs={"main[1]": ["OutStage"]}
- SetCrmId: onError=None extra-outputs=none
- CrmIdOk: onError=None extra-outputs={"main[1]": ["OutStage"]}
- OwnsClaim1: onError=None extra-outputs={"main[1]": ["OutLost"]}
- MailClaim: onError=None extra-outputs=none
- MailRowBack: onError=None extra-outputs={"main[1]": ["MarkUnknownB"]}
- SendMail: onError=continueErrorOutput extra-outputs={"main[1]": ["MarkUnknownA"]}
- MarkDone: onError=None extra-outputs=none
- MarkUnknownA: onError=None extra-outputs=none
- MarkUnknownB: onError=None extra-outputs=none
- UnknownNewA: onError=None extra-outputs={"main[1]": ["OutUnknown"]}
- UnknownNew: onError=None extra-outputs={"main[1]": ["OutUnknown"]}
- DoneOwned: onError=None extra-outputs={"main[1]": ["OutLost"]}
- OutDone: onError=None extra-outputs=none
- OutUnknown: onError=None extra-outputs=none
- OutStage: onError=None extra-outputs=none
- OutLost: onError=None extra-outputs=none
### incoming edges per node
- SubIn <- []
- Qualify <- ['SubIn:main[0]']
- LabelOk <- ['Qualify:main[0]']
- CrmUpsert <- ['LabelOk:main[0]']
- SetCrmId <- ['CrmUpsert:main[0]']
- CrmIdOk <- ['SetCrmId:main[0]']
- OwnsClaim1 <- ['CrmIdOk:main[0]']
- MailClaim <- ['OwnsClaim1:main[0]']
- MailRowBack <- ['MailClaim:main[0]']
- SendMail <- ['MailRowBack:main[0]']
- MarkDone <- ['SendMail:main[0]']
- MarkUnknownA <- ['SendMail:main[1]']
- MarkUnknownB <- ['MailRowBack:main[1]']
- UnknownNewA <- ['MarkUnknownA:main[0]']
- UnknownNew <- ['MarkUnknownB:main[0]']
- DoneOwned <- ['MarkDone:main[0]']
- OutDone <- ['DoneOwned:main[0]']
- OutUnknown <- ['UnknownNewA:main[0]', 'UnknownNewA:main[1]', 'UnknownNew:main[0]', 'UnknownNew:main[1]']
- OutStage <- ['Qualify:main[1]', 'LabelOk:main[1]', 'CrmUpsert:main[1]', 'CrmIdOk:main[1]']
- OutLost <- ['OwnsClaim1:main[1]', 'DoneOwned:main[1]']
### nodes with no incoming edge: ["SubIn"]
### SQL-bearing nodes (Claim, ClaimStuck, or SQL containing INSERT/UPDATE/ON CONFLICT)
#### SetCrmId (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;"
}
#### MailClaim (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MarkDone (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownA (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownB (n8n-nodes-base.postgres)
query:
UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;"
}
### alert/mail nodes (name contains Alert or Mail)
#### MailClaim | n8n-nodes-base.postgres
incoming: ['OwnsClaim1:main[0]']
parameters (masked):
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MailRowBack | n8n-nodes-base.if
incoming: ['MailClaim:main[0]']
parameters (masked):
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.lead_key }}",
    "operator": {
     "operation": "notEmpty",
     "singleValue": true,
     "type": "string"
    },
    "rightValue": null
   }
  ],
  "options": {
   "caseSensitive": true,
   "leftValue": "",
   "typeValidation": "loose"
  }
 },
 "options": {}
}
#### SendMail | n8n-nodes-base.emailSend
incoming: ['MailRowBack:main[0]']
parameters (masked):
{
 "emailFormat": "text",
 "fromEmail": "desk@example.test",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}",
 "text": "made-up thank-you text",
 "toEmail": "intake@example.test"
}
### credentials per node (names only)
- SetCrmId: {"postgres": "n8n-publish-pg"}
- MailClaim: {"postgres": "n8n-publish-pg"}
- SendMail: {"smtp": "mf-mail-smtp"}
- MarkDone: {"postgres": "n8n-publish-pg"}
- MarkUnknownA: {"postgres": "n8n-publish-pg"}
- MarkUnknownB: {"postgres": "n8n-publish-pg"}
### webhook nodes
### environment variable reads ($env. / process.env), by node
- Qualify: ['$env.MF_STAGE_TIMEOUT_MS', '$env.MF_STAGE_URL']
- CrmUpsert: ['$env.MF_CRM_URL']
### external-service nodes (HTTP / Postgres / mail etc.) and error output edge presence
- Qualify | n8n-nodes-base.httpRequest | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["OutStage"]}
- CrmUpsert | n8n-nodes-base.httpRequest | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["OutStage"]}
- SetCrmId | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MailClaim | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- SendMail | n8n-nodes-base.emailSend | onError=continueErrorOutput | error-output edge present: yes {"main[1]": ["MarkUnknownA"]}
- MarkDone | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MarkUnknownA | n8n-nodes-base.postgres | onError=None | error-output edge present: no
- MarkUnknownB | n8n-nodes-base.postgres | onError=None | error-output edge present: no

# DIFF TABLE real-v5 vs film-v5 (per flow)
## mf-hook.json
node names only in real-v5: []
node names only in film-v5: []
node order real-v5: ['Receive', 'Item', 'Valid', 'Claim', 'Claimed', 'IsProcessing', 'SubInput', 'RunSub', 'ReplyRan', 'ReplyReview', 'Stored', 'ReplyStored']
node order film-v5: ['Receive', 'Item', 'Valid', 'Claim', 'Claimed', 'IsProcessing', 'SubInput', 'RunSub', 'ReplyRan', 'ReplyReview', 'Stored', 'ReplyStored']
- connections identical
- whole-file identical bytes: True

## mf-form.json
node names only in real-v5: []
node names only in film-v5: []
node order real-v5: ['Receive', 'Item', 'Valid', 'Claim', 'Claimed', 'IsProcessing', 'SubInput', 'RunSub', 'ReplyRan', 'ReplyReview', 'Stored', 'ReplyStored']
node order film-v5: ['Receive', 'Item', 'Valid', 'Claim', 'Claimed', 'IsProcessing', 'SubInput', 'RunSub', 'ReplyRan', 'ReplyReview', 'Stored', 'ReplyStored']
- connections identical
- whole-file identical bytes: True

## mf-recovery.json
node names only in real-v5: []
node names only in film-v5: []
node order real-v5: ['Every30s', 'ClaimStuck', 'StuckRow', 'RunSub', 'MarkFailed', 'AlertClaim', 'AlertRow', 'AlertSend', 'AlertBackoff', 'AlertMark']
node order film-v5: ['Every30s', 'ClaimStuck', 'StuckRow', 'RunSub', 'MarkFailed', 'AlertClaim', 'AlertRow', 'AlertSend', 'AlertBackoff', 'AlertMark']
- node AlertSend differs:
    parameters.fromEmail: real-v5="FROM_ADDRESS_PLACEHOLDER" | film-v5="desk@example.test"
    parameters.toEmail: real-v5="={{ $env.DESK_ALERT_TO }}" | film-v5="alerts@example.test"
- connections identical
- whole-file identical bytes: False

## mf-sub-crm-mail.json
node names only in real-v5: []
node names only in film-v5: []
node order real-v5: ['SubIn', 'Qualify', 'LabelOk', 'CrmUpsert', 'SetCrmId', 'CrmIdOk', 'OwnsClaim1', 'MailClaim', 'MailRowBack', 'SendMail', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'UnknownNewA', 'UnknownNew', 'DoneOwned', 'OutDone', 'OutUnknown', 'OutStage', 'OutLost']
node order film-v5: ['SubIn', 'Qualify', 'LabelOk', 'CrmUpsert', 'SetCrmId', 'CrmIdOk', 'OwnsClaim1', 'MailClaim', 'MailRowBack', 'SendMail', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'UnknownNewA', 'UnknownNew', 'DoneOwned', 'OutDone', 'OutUnknown', 'OutStage', 'OutLost']
- node CrmUpsert differs:
    credentials: real-v5={"hubspotAppToken": {"id": "HS_CRED_PLACEHOLDER", "name": "hubspot-app-token"}} | film-v5="<absent>"
    parameters.additionalFields: real-v5={"customPropertiesUi": {"customPropertiesValues": [{"property": "hadavin_lead_id", "value": "={{ $('SubIn').first().json.lead_key }}"}, {"property": "hadavin_label", "value": "={{ $('Qualify').first().json.label }}"}]}} | film-v5="<absent>"
    parameters.authentication: real-v5="appToken" | film-v5="<absent>"
    parameters.contentType: real-v5="<absent>" | film-v5="json"
    parameters.email: real-v5="={{ $('SubIn').first().json.email }}" | film-v5="<absent>"
    parameters.jsonBody: real-v5="<absent>" | film-v5="={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}"
    parameters.method: real-v5="<absent>" | film-v5="POST"
    parameters.operation: real-v5="upsert" | film-v5="<absent>"
    parameters.options: real-v5={} | film-v5={"timeout": 10000}
    parameters.resource: real-v5="contact" | film-v5="<absent>"
    parameters.sendBody: real-v5="<absent>" | film-v5=true
    parameters.specifyBody: real-v5="<absent>" | film-v5="json"
    parameters.url: real-v5="<absent>" | film-v5="={{ $env.MF_CRM_URL }}/upsert"
    type: real-v5="n8n-nodes-base.hubspot" | film-v5="n8n-nodes-base.httpRequest"
    typeVersion: real-v5=2.2 | film-v5=4.2
- node Qualify differs:
    parameters.options: real-v5={"timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"} | film-v5={"timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 10000) }}"}
    parameters.url: real-v5="={{ $env.DESK_URL }}/qualify" | film-v5="={{ $env.MF_STAGE_URL }}/qualify"
- node SendMail differs:
    parameters.fromEmail: real-v5="FROM_ADDRESS_PLACEHOLDER" | film-v5="desk@example.test"
    parameters.toEmail: real-v5="INTAKE_ADDRESS_PLACEHOLDER" | film-v5="intake@example.test"
- connections identical
- whole-file identical bytes: False


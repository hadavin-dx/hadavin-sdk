# Evidence A4
sha: requested 35235ace26a516d932e73542c235875f390f333d; on-disk check: target has no .git directory, so the sha could NOT be verified from disk (None)
date UTC: 2026-11-16 07:58:44
Values that look like credentials are shown as [MASKED]. No judging in this file.

## Part 1a: real-v5 vs film-v5 (left = real-v5, right = film-v5)

### mf-hook.json
| kind | node/connection | field path | real-v5 | film-v5 |
|---|---|---|---|---|
(no differences found by this script)

### mf-form.json
| kind | node/connection | field path | real-v5 | film-v5 |
|---|---|---|---|---|
(no differences found by this script)

### mf-recovery.json
| kind | node/connection | field path | real-v5 | film-v5 |
|---|---|---|---|---|
| CHANGED node | AlertSend | parameters.fromEmail | "FROM_ADDRESS_PLACEHOLDER" | "desk@example.test" |
| CHANGED node | AlertSend | parameters.toEmail | "={{ $env.DESK_ALERT_TO }}" | "alerts@example.test" |

### mf-sub-crm-mail.json
| kind | node/connection | field path | real-v5 | film-v5 |
|---|---|---|---|---|
| CHANGED node | Qualify | parameters.options.timeout | "={{ Number($env.DESK_TIMEOUT_MS \|\| 10000) }}" | "={{ Number($env.MF_STAGE_TIMEOUT_MS \|\| 10000) }}" |
| CHANGED node | Qualify | parameters.url | "={{ $env.DESK_URL }}/qualify" | "={{ $env.MF_STAGE_URL }}/qualify" |
| CHANGED node | CrmUpsert | credentials.hubspotAppToken.id | "HS_CRED_PLACEHOLDER" | <absent> |
| CHANGED node | CrmUpsert | credentials.hubspotAppToken.name | "hubspot-app-token" | <absent> |
| CHANGED node | CrmUpsert | parameters.additionalFields.customPropertiesUi.customPropertiesValues[0].property | "hadavin_lead_id" | <absent> |
| CHANGED node | CrmUpsert | parameters.additionalFields.customPropertiesUi.customPropertiesValues[0].value | "={{ $('SubIn').first().json.lead_key }}" | <absent> |
| CHANGED node | CrmUpsert | parameters.additionalFields.customPropertiesUi.customPropertiesValues[1].property | "hadavin_label" | <absent> |
| CHANGED node | CrmUpsert | parameters.additionalFields.customPropertiesUi.customPropertiesValues[1].value | "={{ $('Qualify').first().json.label }}" | <absent> |
| CHANGED node | CrmUpsert | parameters.authentication | "appToken" | <absent> |
| CHANGED node | CrmUpsert | parameters.contentType | <absent> | "json" |
| CHANGED node | CrmUpsert | parameters.email | "={{ $('SubIn').first().json.email }}" | <absent> |
| CHANGED node | CrmUpsert | parameters.jsonBody | <absent> | "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}" |
| CHANGED node | CrmUpsert | parameters.method | <absent> | "POST" |
| CHANGED node | CrmUpsert | parameters.operation | "upsert" | <absent> |
| CHANGED node | CrmUpsert | parameters.options | {} | <absent> |
| CHANGED node | CrmUpsert | parameters.options.timeout | <absent> | 10000 |
| CHANGED node | CrmUpsert | parameters.resource | "contact" | <absent> |
| CHANGED node | CrmUpsert | parameters.sendBody | <absent> | true |
| CHANGED node | CrmUpsert | parameters.specifyBody | <absent> | "json" |
| CHANGED node | CrmUpsert | parameters.url | <absent> | "={{ $env.MF_CRM_URL }}/upsert" |
| CHANGED node | CrmUpsert | type | "n8n-nodes-base.hubspot" | "n8n-nodes-base.httpRequest" |
| CHANGED node | CrmUpsert | typeVersion | 2.2 | 4.2 |
| CHANGED node | SendMail | parameters.fromEmail | "FROM_ADDRESS_PLACEHOLDER" | "desk@example.test" |
| CHANGED node | SendMail | parameters.toEmail | "INTAKE_ADDRESS_PLACEHOLDER" | "intake@example.test" |

## Part 1b: mf-form vs mf-hook (left = mf-form, right = mf-hook)

### real-v5
| kind | node/connection | field path | mf-form | mf-hook |
|---|---|---|---|---|
| CHANGED node | Receive | parameters.path | "mf-form" | "mf-hook" |
| CHANGED node | Receive | webhookId | "mf-form-wh" | "mf-hook-wh" |
| CHANGED node | Item | parameters.assignments.assignments[0].value | "={{ $json.body.submission_id }}" | "={{ $json.body.message_id }}" |
| CHANGED node | Item | parameters.assignments.assignments[1].value | "={{ $json.body.email }}" | "={{ $json.body.from_email }}" |
| CHANGED node | Item | parameters.assignments.assignments[2].value | "={{ $json.body.name }}" | "={{ $json.body.from_name }}" |
| CHANGED top-level | name |  | "Lead desk main frame: form entry" | "Lead desk main frame: e-mail-style entry" |

### film-v5
| kind | node/connection | field path | mf-form | mf-hook |
|---|---|---|---|---|
| CHANGED node | Receive | parameters.path | "mf-form" | "mf-hook" |
| CHANGED node | Receive | webhookId | "mf-form-wh" | "mf-hook-wh" |
| CHANGED node | Item | parameters.assignments.assignments[0].value | "={{ $json.body.submission_id }}" | "={{ $json.body.message_id }}" |
| CHANGED node | Item | parameters.assignments.assignments[1].value | "={{ $json.body.email }}" | "={{ $json.body.from_email }}" |
| CHANGED node | Item | parameters.assignments.assignments[2].value | "={{ $json.body.name }}" | "={{ $json.body.from_name }}" |
| CHANGED top-level | name |  | "Lead desk main frame: form entry" | "Lead desk main frame: e-mail-style entry" |

## Part 1c: V5-NODE-DIFF.txt first 40 lines
total lines: 15
```
== mf-form.json
== mf-hook.json
== mf-recovery.json
== mf-sub-crm-mail.json
  ADDED node: CrmIdOk
  CHANGED node: CrmUpsert (fields: credentials)
    credentials: {"hubspotAppToken": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "hubspot-app-token"}} -> {"hubspotAppToken": {"id": "HS_CRED_PLACEHOLDER", "name": "hubspot-app-token"}}
  CHANGED node: SetCrmId (fields: parameters)
    replacement: ={{ [$('SubIn').first().json.lead_key, String($json.vid), $('SubIn').first().json.claim_token] }} -> ={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}
  ADDED connection: CrmIdOk [out 0] -> OwnsClaim1
  ADDED connection: CrmIdOk [out 1] -> OutStage
  ADDED connection: SetCrmId [out 0] -> CrmIdOk
  REMOVED connection: SetCrmId [out 0] -> OwnsClaim1
RESULT: ONLY SetCrmId, CrmIdOk (new IF) with its connections (SetCrmId->OwnsClaim1 replaced), and the HubSpot credential id differ

```

## Part 2: item paths extracted from CUT-LIST.md (tokens only, verdicts not copied)
AUDIT-PAGE-STATEMENTS-V4.md, AUDIT-VIDEO-RUNSHEET.md, DESIGN-A-README.md, FILM-README.md, N8N-RERUN-1.md, N8N-START.md, NODE-DIFF-vs-film.txt, ORDERS.md, PAGE-STATEMENTS-DRAFT.md, PAGE-STATEMENTS-V4-DRAFT.md, PAGE-STATEMENTS-V4.md, PLAN-4-NLITE-FROM-LEAD.md, REPORT.md, RUN-ON-LAPTOP.md, V3-README.md, V4-README.md, V5-NODE-DIFF.txt, VIDEO-RUNSHEET.md, build_flows.py, build_mainframe.py, crm_stub.py, desk-error-notifier.json, desk-webhook-door.json, desk_proxy.py, dn1.py, dn1_common.py, mf-form.json, mf-hook.json, mf-recovery.json, mf-sub-crm-mail.json, mf.py, mf_leads.sql, n8n-a-cause-1, n8n-a-cause-1.md, n8n-diag-1, n8n-diag-1.md, n8n-flows, n8n-flows-film, n8n-flows-film-v3, n8n-flows-film-v4, n8n-flows-film-v5, n8n-flows-real, n8n-flows-real-v3, n8n-flows-real-v4, n8n-flows-real-v5, n8n-flows-v3, n8n-flows-v4, n8n-flows/N8N-START, n8n-flows/N8N-START.md, n8n-flows/PAGE-STATEMENTS-DRAFT, n8n-flows/PAGE-STATEMENTS-DRAFT.md, n8n-flows/desk-form-door, n8n-flows/desk-form-door.json, n8n-flows/mf_leads, n8n-flows/mf_leads.sql, n8n-flows/v1-superseded, n8n-kill-between-steps, n8n-kill-between-steps.md, n8n-mainframe/build_mainframe_v1, n8n-mainframe/build_mainframe_v1.py, n8n-mainframe/examples, n8n-mainframe/examples/docker-native-pg-shim.py, n8n-mainframe/mf, n8n-mainframe/mf.py, n8n-owns-vs-desk-owns, n8n-owns-vs-desk-owns.md, n8n-published-numbers, n8n-published-numbers.md, n8n-rerun, n8n-skip-on-conflict, n8n-skip-on-conflict.md, n8n-table-screen, n8n-table-screen-v2, n8n-table-screen-v2/README, n8n-table-screen-v2/README.md, n8n-table-screen/README, n8n-table-screen/README.md, n8n-tests/dn1_common, n8n-tests/dn1_common.py, n8n-tests/results, n8n-tests/run_dn1, n8n-tests/run_dn1.py, n8n-vs-desk-kill-compare, n8n-vs-desk-kill-compare.md, py.txt, sandbox-scratch-logs, stage_server.py

## Part 2a: folder pairs named in the CUT-LIST table (the "n8n-flows -> v3" row and the "n8n-flows-v4 -> real-v5 / film-v5" row: both successors diffed)

### FOLDER PAIR n8n-flows/v1-superseded  vs  n8n-flows
only in n8n-flows/v1-superseded: ['README.txt']
only in n8n-flows: ['DESIGN-A-README.md', 'N8N-START.md', 'PAGE-STATEMENTS-DRAFT.md', 'PAGE-STATEMENTS-V4-DRAFT.md', 'PAGE-STATEMENTS-V4.md', 'desk-error-notifier.json', 'desk-form-door.json', 'desk-webhook-door.json', 'mf-sub-crm-mail.json', 'mf_leads.sql', 'v1-superseded']

### n8n-flows/v1-superseded/mf-form.json  vs  n8n-flows/mf-form.json
- n8n-flows/v1-superseded/mf-form.json: size 12137 sha256 dfde6673f47bc38375d2c97d821bbed023b87aec16f81d40acc0101455a7388e
- n8n-flows/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
diff total lines: 602
```
40a41,68
>       }
>      ]
>     },
>     "options": {}
>    },
>    "name": "Item",
>    "type": "n8n-nodes-base.set",
>    "typeVersion": 3.4,
>    "position": [
>     220,
>     0
>    ]
>   },
>   {
>    "parameters": {
>     "assignments": {
>      "assignments": [
>       {
>        "id": "lead_key",
>        "name": "lead_key",
>        "value": "={{ $json.lead_key }}",
>        "type": "string"
>       },
>       {
>        "id": "email",
>        "name": "email",
>        "value": "={{ $json.email }}",
>        "type": "string"
43,45c71,79
<        "id": "mail_sent",
<        "name": "mail_sent",
<        "value": false,
---
>        "id": "name",
>        "name": "name",
>        "value": "={{ $json.name }}",
>        "type": "string"
>       },
>       {
>        "id": "valid",
>        "name": "valid",
>        "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}",
52c86
<    "name": "Item",
---
>    "name": "Valid",
56c90
<     220,
---
>     440,
63c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name) VALUES ($1,$2,$3) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
65c99
<      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name] }}"
---
>      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
68c102
<    "name": "Insert",
---
>    "name": "Claim",
72c106
<     440,
---
>     660,
107c141
<    "name": "Inserted",
---
>    "name": "Claimed",
111,126d144
<     660,
<     0
<    ]
<   },
<   {
<    "parameters": {
<     "operation": "executeQuery",
<     "query": "SELECT state, label FROM mf_leads WHERE lead_key=$1;",
```

### n8n-flows/v1-superseded/mf-hook.json  vs  n8n-flows/mf-hook.json
- n8n-flows/v1-superseded/mf-hook.json: size 12152 sha256 37e328267905ae6c4a56d56d57236c0ef67f1ba67d4a6baf1f16ddacd1189eb0
- n8n-flows/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
diff total lines: 602
```
40a41,68
>       }
>      ]
>     },
>     "options": {}
>    },
>    "name": "Item",
>    "type": "n8n-nodes-base.set",
>    "typeVersion": 3.4,
>    "position": [
>     220,
>     0
>    ]
>   },
>   {
>    "parameters": {
>     "assignments": {
>      "assignments": [
>       {
>        "id": "lead_key",
>        "name": "lead_key",
>        "value": "={{ $json.lead_key }}",
>        "type": "string"
>       },
>       {
>        "id": "email",
>        "name": "email",
>        "value": "={{ $json.email }}",
>        "type": "string"
43,45c71,79
<        "id": "mail_sent",
<        "name": "mail_sent",
<        "value": false,
---
>        "id": "name",
>        "name": "name",
>        "value": "={{ $json.name }}",
>        "type": "string"
>       },
>       {
>        "id": "valid",
>        "name": "valid",
>        "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}",
52c86
<    "name": "Item",
---
>    "name": "Valid",
56c90
<     220,
---
>     440,
63c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name) VALUES ($1,$2,$3) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
65c99
<      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name] }}"
---
>      "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
68c102
<    "name": "Insert",
---
>    "name": "Claim",
72c106
<     440,
---
>     660,
107c141
<    "name": "Inserted",
---
>    "name": "Claimed",
111,126d144
<     660,
<     0
<    ]
<   },
<   {
<    "parameters": {
<     "operation": "executeQuery",
<     "query": "SELECT state, label FROM mf_leads WHERE lead_key=$1;",
```

### n8n-flows/v1-superseded/mf-recovery.json  vs  n8n-flows/mf-recovery.json
- n8n-flows/v1-superseded/mf-recovery.json: size 9699 sha256 3a33f9942cd90eca1e077e6ae52419021ac8089383e72c38679dd6cf2c6c9d3b
- n8n-flows/mf-recovery.json: size 4850 sha256 0bdd390e5ce9708ecab3e9c0a0149bbc46ab79ce5fc3edc21f5e1fcc1de2baa0
diff total lines: 464
```
26c26
<     "query": "UPDATE mf_leads SET updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','unknown') AND updated_at < now() - interval '20 seconds' ORDER BY created_at LIMIT 20 FOR UPDATE SKIP LOCKED) RETURNING lead_key, email, name, mail_sent, state;",
---
>     "query": "UPDATE mf_leads SET claimed_until=now() + interval '120 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
34c34
<     0
---
>     -100
42,145c42,43
<    "alwaysOutputData": false
<   },
<   {
<    "parameters": {
<     "assignments": {
<      "assignments": [
<       {
<        "id": "lead_key",
<        "name": "lead_key",
<        "value": "={{ $json.lead_key }}",
<        "type": "string"
<       },
<       {
<        "id": "email",
<        "name": "email",
<        "value": "={{ $json.email }}",
<        "type": "string"
<       },
<       {
<        "id": "mail_sent",
<        "name": "mail_sent",
<        "value": "={{ $json.mail_sent }}",
<        "type": "boolean"
<       }
<      ]
<     },
<     "options": {}
<    },
<    "name": "RItem",
<    "type": "n8n-nodes-base.set",
<    "typeVersion": 3.4,
<    "position": [
<     440,
<     0
<    ]
<   },
<   {
<    "parameters": {
<     "method": "POST",
<     "url": "={{ $env.MF_STAGE_URL }}/qualify",
<     "sendBody": true,
<     "contentType": "json",
<     "specifyBody": "json",
<     "jsonBody": "={{ { lead_key: $('RItem').item.json.lead_key, email: $('RItem').item.json.email } }}",
<     "options": {
<      "timeout": 15000
<     }
<    },
<    "name": "RQualify",
<    "type": "n8n-nodes-base.httpRequest",
<    "typeVersion": 4.2,
<    "position": [
<     660,
<     0
<    ],
<    "retryOnFail": true,
<    "maxTries": 3,
<    "waitBetweenTries": 1000
<   },
<   {
<    "parameters": {
<     "operation": "executeQuery",
<     "query": "UPDATE mf_leads SET label=$2, updated_at=now() WHERE lead_key=$1 RETURNING lead_key;",
<     "options": {
<      "queryReplacement": "={{ [$('RItem').item.json.lead_key, $json.label] }}"
<     }
<    },
<    "name": "RSaveLabel",
<    "type": "n8n-nodes-base.postgres",
<    "typeVersion": 2.5,
<    "position": [
```

### FOLDER PAIR n8n-flows  vs  n8n-flows-v3
only in n8n-flows: ['DESIGN-A-README.md', 'N8N-START.md', 'PAGE-STATEMENTS-DRAFT.md', 'PAGE-STATEMENTS-V4-DRAFT.md', 'PAGE-STATEMENTS-V4.md', 'desk-error-notifier.json', 'desk-form-door.json', 'desk-webhook-door.json', 'v1-superseded']
only in n8n-flows-v3: ['V3-README.md']

### n8n-flows/mf-form.json  vs  n8n-flows-v3/mf-form.json
- n8n-flows/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
- n8n-flows-v3/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
diff total lines: 0
```
```

### n8n-flows/mf-hook.json  vs  n8n-flows-v3/mf-hook.json
- n8n-flows/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
- n8n-flows-v3/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
diff total lines: 0
```
```

### n8n-flows/mf-recovery.json  vs  n8n-flows-v3/mf-recovery.json
- n8n-flows/mf-recovery.json: size 4850 sha256 0bdd390e5ce9708ecab3e9c0a0149bbc46ab79ce5fc3edc21f5e1fcc1de2baa0
- n8n-flows-v3/mf-recovery.json: size 6781 sha256 93a6079ce613b95132eeda7899cae67f14a64f08a3976fb6a09cd58cdcb530e6
diff total lines: 109
```
102c102
<     "query": "UPDATE mf_leads SET state='failed', updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
---
>     "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
122a123,144
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
>     "options": {}
>    },
>    "name": "AlertClaim",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     220,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
145c167
<    "name": "FailedRow",
---
>    "name": "AlertRow",
150c172
<     120
---
>     300
157c179
<     "subject": "={{ '[demo] Lead desk: lead failed ' + $json.lead_key }}",
---
>     "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
159c181
<     "text": "={{ 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
---
>     "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
164c186
<    "name": "AlertFailed",
---
>    "name": "AlertSend",
169c191
<     80
---
>     300
176a199,222
>    "onError": "continueErrorOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertMark",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
192a239,243
>      },
>      {
>       "node": "AlertClaim",
```

### n8n-flows/mf-sub-crm-mail.json  vs  n8n-flows-v3/mf-sub-crm-mail.json
- n8n-flows/mf-sub-crm-mail.json: size 14594 sha256 331ce6e678e1d5f55078b943d97e5c7e76cc1744e0f1db0c7dd938ee530d38ca
- n8n-flows-v3/mf-sub-crm-mail.json: size 13751 sha256 7638c09a10a96800d1eb2d76e8b9a78508203864ce9e723a154a4ff01e749826
diff total lines: 47
```
368,393d367
<     "fromEmail": "desk@example.test",
<     "toEmail": "alerts@example.test",
<     "subject": "={{ '[demo] Lead desk: mail outcome unknown for ' + $('SubIn').first().json.lead_key }}",
<     "emailFormat": "text",
<     "text": "={{ 'Lead id ' + $('SubIn').first().json.lead_key + ': the mail may or may not have been sent. A person decides.' }}",
<     "options": {
<      "appendAttribution": false
<     }
<    },
<    "name": "AlertUnknown",
<    "type": "n8n-nodes-base.emailSend",
<    "typeVersion": 2.1,
<    "position": [
<     2200,
<     0
<    ],
<    "credentials": {
<     "smtp": {
<      "id": "SMTP_CREDENTIAL_ID",
<      "name": "mf-mail-smtp"
<     }
<    },
<    "onError": "continueRegularOutput"
<   },
<   {
<    "parameters": {
723c697
<       "node": "AlertUnknown",
---
>       "node": "OutUnknown",
752,758d725
<       "node": "AlertUnknown",
<       "type": "main",
<       "index": 0
<      }
<     ],
<     [
<      {
763,767c730
<     ]
<    ]
<   },
<   "AlertUnknown": {
<    "main": [
---
>     ],
```

### n8n-flows/mf_leads.sql  vs  n8n-flows-v3/mf_leads.sql
- n8n-flows/mf_leads.sql: size 881 sha256 7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee
- n8n-flows-v3/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
diff total lines: 14
```
1c1,2
< -- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
---
> -- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
> -- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
14c15,20
<   updated_at    timestamptz NOT NULL DEFAULT now());
---
>   updated_at    timestamptz NOT NULL DEFAULT now(),
>   -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
>   alert_sent    boolean NOT NULL DEFAULT false,
>   alert_token   text,
>   alert_until   timestamptz,
>   alert_attempts int NOT NULL DEFAULT 0);
```

### FOLDER PAIR n8n-flows-v3  vs  n8n-flows-v4
only in n8n-flows-v3: ['V3-README.md']
only in n8n-flows-v4: ['V4-README.md']

### n8n-flows-v3/mf-form.json  vs  n8n-flows-v4/mf-form.json
- n8n-flows-v3/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
- n8n-flows-v4/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
diff total lines: 0
```
```

### n8n-flows-v3/mf-hook.json  vs  n8n-flows-v4/mf-hook.json
- n8n-flows-v3/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
- n8n-flows-v4/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
diff total lines: 0
```
```

### n8n-flows-v3/mf-recovery.json  vs  n8n-flows-v4/mf-recovery.json
- n8n-flows-v3/mf-recovery.json: size 6781 sha256 93a6079ce613b95132eeda7899cae67f14a64f08a3976fb6a09cd58cdcb530e6
- n8n-flows-v4/mf-recovery.json: size 7531 sha256 12a7ef2c70ef151c376b6ef1bb1ab6d78c21a874fca247c8aaedbfe84c757a30
diff total lines: 37
```
124c124
<     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
---
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
203a204,227
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertBackoff",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     380
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
296a321,327
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "AlertBackoff",
```

### n8n-flows-v3/mf-sub-crm-mail.json  vs  n8n-flows-v4/mf-sub-crm-mail.json
- n8n-flows-v3/mf-sub-crm-mail.json: size 13751 sha256 7638c09a10a96800d1eb2d76e8b9a78508203864ce9e723a154a4ff01e749826
- n8n-flows-v4/mf-sub-crm-mail.json: size 13751 sha256 7638c09a10a96800d1eb2d76e8b9a78508203864ce9e723a154a4ff01e749826
diff total lines: 0
```
```

### n8n-flows-v3/mf_leads.sql  vs  n8n-flows-v4/mf_leads.sql
- n8n-flows-v3/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
- n8n-flows-v4/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
diff total lines: 0
```
```

### FOLDER PAIR n8n-flows-v4  vs  n8n-flows-real-v5
only in n8n-flows-v4: ['V4-README.md', 'mf_leads.sql']
only in n8n-flows-real-v5: ['V5-NODE-DIFF.txt', 'V5-README.md']

### n8n-flows-v4/mf-form.json  vs  n8n-flows-real-v5/mf-form.json
- n8n-flows-v4/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
- n8n-flows-real-v5/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 4
```
97c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
```

### n8n-flows-v4/mf-hook.json  vs  n8n-flows-real-v5/mf-hook.json
- n8n-flows-v4/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
- n8n-flows-real-v5/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 4
```
97c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
```

### n8n-flows-v4/mf-recovery.json  vs  n8n-flows-real-v5/mf-recovery.json
- n8n-flows-v4/mf-recovery.json: size 7531 sha256 12a7ef2c70ef151c376b6ef1bb1ab6d78c21a874fca247c8aaedbfe84c757a30
- n8n-flows-real-v5/mf-recovery.json: size 7543 sha256 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
diff total lines: 10
```
26c26
<     "query": "UPDATE mf_leads SET claimed_until=now() + interval '120 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
---
>     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
177,178c177,178
<     "fromEmail": "desk@example.test",
<     "toEmail": "alerts@example.test",
---
>     "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
>     "toEmail": "={{ $env.DESK_ALERT_TO }}",
```

### n8n-flows-v4/mf-sub-crm-mail.json  vs  n8n-flows-real-v5/mf-sub-crm-mail.json
- n8n-flows-v4/mf-sub-crm-mail.json: size 13751 sha256 7638c09a10a96800d1eb2d76e8b9a78508203864ce9e723a154a4ff01e749826
- n8n-flows-real-v5/mf-sub-crm-mail.json: size 14932 sha256 b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36
diff total lines: 122
```
19c19
<     "url": "={{ $env.MF_STAGE_URL }}/qualify",
---
>     "url": "={{ $env.DESK_URL }}/qualify",
25c25
<      "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 15000) }}"
---
>      "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
36c36
<    "maxTries": 3,
---
>    "maxTries": 2,
74,82c74,92
<     "method": "POST",
<     "url": "={{ $env.MF_CRM_URL }}/upsert",
<     "sendBody": true,
<     "contentType": "json",
<     "specifyBody": "json",
<     "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}",
<     "options": {
<      "timeout": 15000
<     }
---
>     "authentication": "appToken",
>     "resource": "contact",
>     "operation": "upsert",
>     "email": "={{ $('SubIn').first().json.email }}",
>     "additionalFields": {
>      "customPropertiesUi": {
>       "customPropertiesValues": [
>        {
>         "property": "hadavin_lead_id",
>         "value": "={{ $('SubIn').first().json.lead_key }}"
>        },
>        {
>         "property": "hadavin_label",
>         "value": "={{ $('Qualify').first().json.label }}"
>        }
>       ]
>      }
>     },
>     "options": {}
85,86c95,96
<    "type": "n8n-nodes-base.httpRequest",
<    "typeVersion": 4.2,
---
>    "type": "n8n-nodes-base.hubspot",
>    "typeVersion": 2.2,
90a101,106
>    "credentials": {
>     "hubspotAppToken": {
>      "id": "HS_CRED_PLACEHOLDER",
>      "name": "hubspot-app-token"
>     }
>    },
92c108
<    "maxTries": 3,
---
>    "maxTries": 2,
101c117
<      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id), $('SubIn').first().json.claim_token] }}"
---
>      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
129a146,177
>        "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
>        "rightValue": null,
>        "operator": {
>         "type": "boolean",
>         "operation": "true",
>         "singleValue": true
>        }
>       }
>      ],
>      "combinator": "and"
>     },
>     "options": {}
>    },
>    "name": "CrmIdOk",
>    "type": "n8n-nodes-base.if",
>    "typeVersion": 2.2,
```

### FOLDER PAIR n8n-flows-real  vs  n8n-flows-real-v3
only in n8n-flows-real: ['NODE-DIFF-vs-film.txt', 'README.md']
only in n8n-flows-real-v3: []

### n8n-flows-real/mf-form.json  vs  n8n-flows-real-v3/mf-form.json
- n8n-flows-real/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-real-v3/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-real/mf-hook.json  vs  n8n-flows-real-v3/mf-hook.json
- n8n-flows-real/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-real-v3/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-real/mf-recovery.json  vs  n8n-flows-real-v3/mf-recovery.json
- n8n-flows-real/mf-recovery.json: size 4862 sha256 4a5d00d66c8930ed97f75bb86b1d976e23f679b470f2807335b30b547f3c767c
- n8n-flows-real-v3/mf-recovery.json: size 6793 sha256 0cb0dbdb00078ce7d57ca7ecaf2fff6adebe7bec9a7e38ce4010a566d169c0f9
diff total lines: 109
```
102c102
<     "query": "UPDATE mf_leads SET state='failed', updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
---
>     "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
122a123,144
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
>     "options": {}
>    },
>    "name": "AlertClaim",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     220,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
145c167
<    "name": "FailedRow",
---
>    "name": "AlertRow",
150c172
<     120
---
>     300
157c179
<     "subject": "={{ '[demo] Lead desk: lead failed ' + $json.lead_key }}",
---
>     "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
159c181
<     "text": "={{ 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
---
>     "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
164c186
<    "name": "AlertFailed",
---
>    "name": "AlertSend",
169c191
<     80
---
>     300
176a199,222
>    "onError": "continueErrorOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertMark",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
192a239,243
>      },
>      {
>       "node": "AlertClaim",
```

### n8n-flows-real/mf-sub-crm-mail.json  vs  n8n-flows-real-v3/mf-sub-crm-mail.json
- n8n-flows-real/mf-sub-crm-mail.json: size 14891 sha256 11ee4b969b8578f3f24b4ce9146e4e4086b41658eba5d3165a995a243a5432fd
- n8n-flows-real-v3/mf-sub-crm-mail.json: size 14035 sha256 6d03a6ff6f8a341596bb432fda40d4dfd4227e524344cb9f1eb21bbe513cd70a
diff total lines: 47
```
384,409d383
<     "fromEmail": "FROM_ADDRESS_PLACEHOLDER",
<     "toEmail": "={{ $env.DESK_ALERT_TO }}",
<     "subject": "={{ '[demo] Lead desk: mail outcome unknown for ' + $('SubIn').first().json.lead_key }}",
<     "emailFormat": "text",
<     "text": "={{ 'Lead id ' + $('SubIn').first().json.lead_key + ': the mail may or may not have been sent. A person decides.' }}",
<     "options": {
<      "appendAttribution": false
<     }
<    },
<    "name": "AlertUnknown",
<    "type": "n8n-nodes-base.emailSend",
<    "typeVersion": 2.1,
<    "position": [
<     2200,
<     0
<    ],
<    "credentials": {
<     "smtp": {
<      "id": "SMTP_CREDENTIAL_ID",
<      "name": "mf-mail-smtp"
<     }
<    },
<    "onError": "continueRegularOutput"
<   },
<   {
<    "parameters": {
739c713
<       "node": "AlertUnknown",
---
>       "node": "OutUnknown",
768,774d741
<       "node": "AlertUnknown",
<       "type": "main",
<       "index": 0
<      }
<     ],
<     [
<      {
779,783c746
<     ]
<    ]
<   },
<   "AlertUnknown": {
<    "main": [
---
>     ],
```

### FOLDER PAIR n8n-flows-real-v3  vs  n8n-flows-real-v4
only in n8n-flows-real-v3: []
only in n8n-flows-real-v4: []

### n8n-flows-real-v3/mf-form.json  vs  n8n-flows-real-v4/mf-form.json
- n8n-flows-real-v3/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-real-v4/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-real-v3/mf-hook.json  vs  n8n-flows-real-v4/mf-hook.json
- n8n-flows-real-v3/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-real-v4/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-real-v3/mf-recovery.json  vs  n8n-flows-real-v4/mf-recovery.json
- n8n-flows-real-v3/mf-recovery.json: size 6793 sha256 0cb0dbdb00078ce7d57ca7ecaf2fff6adebe7bec9a7e38ce4010a566d169c0f9
- n8n-flows-real-v4/mf-recovery.json: size 7543 sha256 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
diff total lines: 37
```
124c124
<     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
---
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
203a204,227
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertBackoff",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     380
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
296a321,327
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "AlertBackoff",
```

### n8n-flows-real-v3/mf-sub-crm-mail.json  vs  n8n-flows-real-v4/mf-sub-crm-mail.json
- n8n-flows-real-v3/mf-sub-crm-mail.json: size 14035 sha256 6d03a6ff6f8a341596bb432fda40d4dfd4227e524344cb9f1eb21bbe513cd70a
- n8n-flows-real-v4/mf-sub-crm-mail.json: size 14035 sha256 6d03a6ff6f8a341596bb432fda40d4dfd4227e524344cb9f1eb21bbe513cd70a
diff total lines: 0
```
```

### FOLDER PAIR n8n-flows-real-v4  vs  n8n-flows-real-v5
only in n8n-flows-real-v4: []
only in n8n-flows-real-v5: ['V5-NODE-DIFF.txt', 'V5-README.md']

### n8n-flows-real-v4/mf-form.json  vs  n8n-flows-real-v5/mf-form.json
- n8n-flows-real-v4/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-real-v5/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-real-v4/mf-hook.json  vs  n8n-flows-real-v5/mf-hook.json
- n8n-flows-real-v4/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-real-v5/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-real-v4/mf-recovery.json  vs  n8n-flows-real-v5/mf-recovery.json
- n8n-flows-real-v4/mf-recovery.json: size 7543 sha256 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
- n8n-flows-real-v5/mf-recovery.json: size 7543 sha256 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
diff total lines: 0
```
```

### n8n-flows-real-v4/mf-sub-crm-mail.json  vs  n8n-flows-real-v5/mf-sub-crm-mail.json
- n8n-flows-real-v4/mf-sub-crm-mail.json: size 14035 sha256 6d03a6ff6f8a341596bb432fda40d4dfd4227e524344cb9f1eb21bbe513cd70a
- n8n-flows-real-v5/mf-sub-crm-mail.json: size 14932 sha256 b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36
diff total lines: 61
```
103c103
<      "id": "HUBSPOT_CREDENTIAL_ID",
---
>      "id": "HS_CRED_PLACEHOLDER",
117c117
<      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.vid), $('SubIn').first().json.claim_token] }}"
---
>      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
145a146,177
>        "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
>        "rightValue": null,
>        "operator": {
>         "type": "boolean",
>         "operation": "true",
>         "singleValue": true
>        }
>       }
>      ],
>      "combinator": "and"
>     },
>     "options": {}
>    },
>    "name": "CrmIdOk",
>    "type": "n8n-nodes-base.if",
>    "typeVersion": 2.2,
>    "position": [
>     990,
>     60
>    ]
>   },
>   {
>    "parameters": {
>     "conditions": {
>      "options": {
>       "caseSensitive": true,
>       "leftValue": "",
>       "typeValidation": "loose"
>      },
>      "conditions": [
>       {
>        "id": "c1",
596a629,639
>       "node": "CrmIdOk",
>       "type": "main",
>       "index": 0
>      }
>     ]
>    ]
>   },
>   "CrmIdOk": {
>    "main": [
>     [
>      {
597a641,647
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "OutStage",
```

### FOLDER PAIR n8n-flows-film  vs  n8n-flows-film-v3
only in n8n-flows-film: ['FILM-README.md']
only in n8n-flows-film-v3: []

### n8n-flows-film/mf-form.json  vs  n8n-flows-film-v3/mf-form.json
- n8n-flows-film/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-film-v3/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-film/mf-hook.json  vs  n8n-flows-film-v3/mf-hook.json
- n8n-flows-film/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-film-v3/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-film/mf-recovery.json  vs  n8n-flows-film-v3/mf-recovery.json
- n8n-flows-film/mf-recovery.json: size 4849 sha256 e0def5983f70480c26d82516531fc6f1ce2a4e7ca7644d9e45253e7499cd9f2a
- n8n-flows-film-v3/mf-recovery.json: size 6780 sha256 3dff915232ac1348f4e30978ea4694536cedba5f79568a74fd80bbdfd5b1ab3d
diff total lines: 109
```
102c102
<     "query": "UPDATE mf_leads SET state='failed', updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
---
>     "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
122a123,144
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
>     "options": {}
>    },
>    "name": "AlertClaim",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     220,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
145c167
<    "name": "FailedRow",
---
>    "name": "AlertRow",
150c172
<     120
---
>     300
157c179
<     "subject": "={{ '[demo] Lead desk: lead failed ' + $json.lead_key }}",
---
>     "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
159c181
<     "text": "={{ 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
---
>     "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
164c186
<    "name": "AlertFailed",
---
>    "name": "AlertSend",
169c191
<     80
---
>     300
176a199,222
>    "onError": "continueErrorOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
>     "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertMark",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     300
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
192a239,243
>      },
>      {
>       "node": "AlertClaim",
```

### n8n-flows-film/mf-sub-crm-mail.json  vs  n8n-flows-film-v3/mf-sub-crm-mail.json
- n8n-flows-film/mf-sub-crm-mail.json: size 14594 sha256 a664a3bc6d59f946b7d2af30578bc90342ddad0880fa1c2d3a4f130340883d14
- n8n-flows-film-v3/mf-sub-crm-mail.json: size 13751 sha256 897bb520da9130a8a808f87307113d757f498021e8e74dcc3a396ed86469cb1c
diff total lines: 47
```
368,393d367
<     "fromEmail": "desk@example.test",
<     "toEmail": "alerts@example.test",
<     "subject": "={{ '[demo] Lead desk: mail outcome unknown for ' + $('SubIn').first().json.lead_key }}",
<     "emailFormat": "text",
<     "text": "={{ 'Lead id ' + $('SubIn').first().json.lead_key + ': the mail may or may not have been sent. A person decides.' }}",
<     "options": {
<      "appendAttribution": false
<     }
<    },
<    "name": "AlertUnknown",
<    "type": "n8n-nodes-base.emailSend",
<    "typeVersion": 2.1,
<    "position": [
<     2200,
<     0
<    ],
<    "credentials": {
<     "smtp": {
<      "id": "SMTP_CREDENTIAL_ID",
<      "name": "mf-mail-smtp"
<     }
<    },
<    "onError": "continueRegularOutput"
<   },
<   {
<    "parameters": {
723c697
<       "node": "AlertUnknown",
---
>       "node": "OutUnknown",
752,758d725
<       "node": "AlertUnknown",
<       "type": "main",
<       "index": 0
<      }
<     ],
<     [
<      {
763,767c730
<     ]
<    ]
<   },
<   "AlertUnknown": {
<    "main": [
---
>     ],
```

### FOLDER PAIR n8n-flows-film-v3  vs  n8n-flows-film-v4
only in n8n-flows-film-v3: []
only in n8n-flows-film-v4: []

### n8n-flows-film-v3/mf-form.json  vs  n8n-flows-film-v4/mf-form.json
- n8n-flows-film-v3/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-film-v4/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-film-v3/mf-hook.json  vs  n8n-flows-film-v4/mf-hook.json
- n8n-flows-film-v3/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-film-v4/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-film-v3/mf-recovery.json  vs  n8n-flows-film-v4/mf-recovery.json
- n8n-flows-film-v3/mf-recovery.json: size 6780 sha256 3dff915232ac1348f4e30978ea4694536cedba5f79568a74fd80bbdfd5b1ab3d
- n8n-flows-film-v4/mf-recovery.json: size 7530 sha256 42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
diff total lines: 37
```
124c124
<     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * (1 + LEAST(alert_attempts, 4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
---
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
203a204,227
>     "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
>     "options": {
>      "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
>     }
>    },
>    "name": "AlertBackoff",
>    "type": "n8n-nodes-base.postgres",
>    "typeVersion": 2.5,
>    "position": [
>     770,
>     380
>    ],
>    "credentials": {
>     "postgres": {
>      "id": "PG_CREDENTIAL_ID",
>      "name": "n8n-publish-pg"
>     }
>    },
>    "alwaysOutputData": false,
>    "onError": "continueRegularOutput"
>   },
>   {
>    "parameters": {
>     "operation": "executeQuery",
296a321,327
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "AlertBackoff",
```

### n8n-flows-film-v3/mf-sub-crm-mail.json  vs  n8n-flows-film-v4/mf-sub-crm-mail.json
- n8n-flows-film-v3/mf-sub-crm-mail.json: size 13751 sha256 897bb520da9130a8a808f87307113d757f498021e8e74dcc3a396ed86469cb1c
- n8n-flows-film-v4/mf-sub-crm-mail.json: size 13751 sha256 897bb520da9130a8a808f87307113d757f498021e8e74dcc3a396ed86469cb1c
diff total lines: 0
```
```

### FOLDER PAIR n8n-flows-film-v4  vs  n8n-flows-film-v5
only in n8n-flows-film-v4: []
only in n8n-flows-film-v5: ['V5-README.md']

### n8n-flows-film-v4/mf-form.json  vs  n8n-flows-film-v5/mf-form.json
- n8n-flows-film-v4/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- n8n-flows-film-v5/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 0
```
```

### n8n-flows-film-v4/mf-hook.json  vs  n8n-flows-film-v5/mf-hook.json
- n8n-flows-film-v4/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- n8n-flows-film-v5/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 0
```
```

### n8n-flows-film-v4/mf-recovery.json  vs  n8n-flows-film-v5/mf-recovery.json
- n8n-flows-film-v4/mf-recovery.json: size 7530 sha256 42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
- n8n-flows-film-v5/mf-recovery.json: size 7530 sha256 42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
diff total lines: 0
```
```

### n8n-flows-film-v4/mf-sub-crm-mail.json  vs  n8n-flows-film-v5/mf-sub-crm-mail.json
- n8n-flows-film-v4/mf-sub-crm-mail.json: size 13751 sha256 897bb520da9130a8a808f87307113d757f498021e8e74dcc3a396ed86469cb1c
- n8n-flows-film-v5/mf-sub-crm-mail.json: size 14651 sha256 a0215012962e2e22e3923ed9ecb14bae472e0857636b7356f61e87190968918b
diff total lines: 57
```
101c101
<      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id), $('SubIn').first().json.claim_token] }}"
---
>      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
129a130,161
>        "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
>        "rightValue": null,
>        "operator": {
>         "type": "boolean",
>         "operation": "true",
>         "singleValue": true
>        }
>       }
>      ],
>      "combinator": "and"
>     },
>     "options": {}
>    },
>    "name": "CrmIdOk",
>    "type": "n8n-nodes-base.if",
>    "typeVersion": 2.2,
>    "position": [
>     990,
>     60
>    ]
>   },
>   {
>    "parameters": {
>     "conditions": {
>      "options": {
>       "caseSensitive": true,
>       "leftValue": "",
>       "typeValidation": "loose"
>      },
>      "conditions": [
>       {
>        "id": "c1",
580a613,623
>       "node": "CrmIdOk",
>       "type": "main",
>       "index": 0
>      }
>     ]
>    ]
>   },
>   "CrmIdOk": {
>    "main": [
>     [
>      {
581a625,631
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "OutStage",
```

### FOLDER PAIR n8n-table-screen  vs  n8n-table-screen-v2
only in n8n-table-screen: ['mf-table-screen.json']
only in n8n-table-screen-v2: ['mf-table-screen-v2.json', 'preview-dark.png', 'preview-light.png', 'sample-output.html']

### n8n-table-screen/README.md  vs  n8n-table-screen-v2/README.md
- n8n-table-screen/README.md: size 1996 sha256 41ffd14017aec93973ea4f99fc27bf7ef7e5739a609b15574abe6f6fe5d06461
- n8n-table-screen-v2/README.md: size 4474 sha256 f039140f88834e53c677ca9ba6a0459f680cc2f575302a403eb0dfa64d59bb97
diff total lines: 79
```
1c1
< # Lead table screen (doubtful-case scene)
---
> # Lead table screen v2
3c3
< Status: NOT RUN. No n8n or Postgres can start in this sandbox (disk), so this workflow was never executed. Only the JSON structure was checked.
---
> Status: built, sample rendered with node, NOT run in n8n. Version 1 (folder n8n-table-screen) was run live on n8n 2.46.6 and works; v2 keeps its four nodes, node types and versions, and the same placeholder credential id PG_CREDENTIAL_ID (credential name n8n-publish-pg).
5,6c5,10
< ## What it shows
< A browser page with one table of the newest 50 rows of the table mf_leads: lead_key, state, attempts, mail_sent, alert_sent, alert_attempts, updated_at. No name or e-mail columns are read. The page reloads itself every 5 seconds, so a doubtful case (state unknown or failed, then alert_sent turning true) can be watched live.
---
> ## What changed vs v1 (the 5 rehearsal problems)
> 1. State badges with colour and text: done green, unknown amber, failed red, processing grey. The grey badge also covers the other in-progress states from mf_leads.sql (new, review) and any unexpected value, which shows its own text.
> 2. Dark mode: all colours are CSS variables, with a light palette and a real dark palette chosen by prefers-color-scheme.
> 3. Plain words instead of raw cells: mail: sent / mail: sent, confirmation missing (state unknown) / mail: not sent; alert sent / alert waiting (state unknown or failed, not yet sent) / a dash; attempts shown as tries 1. The alert_attempts column is no longer read.
> 4. updated_at shows as HH:MM:SS UTC, no milliseconds, no raw ISO text.
> 5. One title: the tab title and the heading both say Lead table.
8,26c12,51
< ## Nodes (n8n 2.46.6, n8n nodes only, no Code node)
< 1. Receive: Webhook, GET, path demo-table, response mode: Respond to Webhook.
< 2. ReadLeads: Postgres 2.5, one SELECT, credential n8n-publish-pg.
< 3. BuildHtml: Set 3.4, run once, builds the whole HTML string from all rows (one expression, rows are HTML-escaped).
< 4. ReplyHtml: Respond to Webhook 1.4, text with Content-Type text/html.
< 
< ## Import steps
< 1. In n8n choose Workflows, Import from file, pick mf-table-screen.json.
< 2. Open the ReadLeads node and select the Postgres credential n8n-publish-pg (the file holds the placeholder id PG_CREDENTIAL_ID, as in the other flows).
< 3. Make sure the table mf_leads exists (DDL in the n8n-flows-v4 folder, file mf_leads.sql).
< 4. Save and activate the workflow.
< 5. In the browser open the production webhook address of your n8n instance with the path /webhook/demo-table (on the same machine use the LOOPBACK address and the n8n port). For a test run use the path /webhook-test/demo-table after pressing Listen for test event.
< 
< ## Honest limits
< - Never executed; the expression syntax in BuildHtml and the header option of ReplyHtml are unverified against a live n8n.
< - Empty table: the page shows only the header row.
< - Shows at most 50 rows, newest first; no paging, no filter.
< - The page is public to anyone who can reach the webhook; it shows lead_key values, so do not expose it beyond the demo.
< - Auto-refresh is a plain meta tag; it re-runs the query each time.
---
> Also new: summary strip with counts per state above the table, sticky header, centred card, monospace lead_key, tabular numbers, row hover, footer line "refreshes every 5 s; made-up data", larger text for a 1080p recording.
> 
> Unchanged: 5 s auto-refresh (meta tag), every value HTML-escaped, no name or e-mail read. The SELECT reads only lead_key, state, attempts, mail_sent, alert_sent, updated_at.
> 
> ## Nodes (n8n 2.46.6, no Code node)
> 1. Receive: Webhook 2, GET, path demo-table-v2, Respond to Webhook mode.
> 2. ReadLeads: Postgres 2.5, one SELECT, newest 50 rows.
> 3. BuildHtml: Set 3.4, run once, the whole page is built in one expression, as in v1. It uses only arrow functions, map, filter, join and string replace, as v1 did; no template literals and no statements. The expression contains no closing double brace (CSS is written to avoid it), because that would end the n8n expression early.
> 4. ReplyHtml: Respond to Webhook 1.4, text, Content-Type text/html.
> 
> An n8n HTML node was deliberately not used: it was not proven live, whereas the Set-node expression was.
> 
> ## Import steps (UI)
> 1. Workflows, Import from file, choose mf-table-screen-v2.json.
> 2. Open ReadLeads and select the Postgres credential n8n-publish-pg.
> 3. The table mf_leads must exist (DDL in n8n-flows-v4, file mf_leads.sql).
> 4. Save and activate.
> 5. Open the production webhook address of the instance with the path /webhook/demo-table-v2 (same machine: the LOOPBACK address plus the n8n port). For a test run use /webhook-test/demo-table-v2 after pressing Listen for test event.
> 
> ## LAPTOP IMPORT COMMANDS
> UI: steps above.
> 
> CLI (run where n8n is installed):
> 
>     n8n import:workflow --input=mf-table-screen-v2.json
> 
> Then set the credential on ReadLeads in the UI (the file holds only the placeholder id) and activate the workflow in the UI. After a CLI import, restart n8n if the webhook does not answer.
> 
> Coexisting with v1: v2 uses the path demo-table-v2 and v1 uses demo-table, so both can be active together. If you instead change v2 back to the path demo-table, deactivate v1 first, because two active workflows cannot share one webhook path.
> 
> ## Validation done
> - JSON loads with python3; all four connections resolve; node types and versions equal v1.
> - The Set-node expression was extracted and evaluated with node against made-up rows (done, unknown, failed, processing, an unknown state value, a value with angle brackets and an ampersand, a null time, and an empty table). Output saved as sample-output.html.
> - Checks passed: no name or e-mail column, angle brackets escaped, times as HH:MM:SS, no milliseconds, counts correct, empty table shows a "No leads yet" line.
> 
> ## Unverified
> - Never run in n8n: the real expression parser, the Postgres date type as n8n delivers it (the code accepts an ISO string or a date object), and rendering in a real browser (colours, sticky header, dark mode) are not checked.
> - Shows at most 50 rows, newest first; no paging. The page is public to anyone who can reach the webhook; do not expose it beyond the demo.
> 
> Update 17:17Z: an unexpected state now gets a neutral grey badge with its own text, and the summary strip shows an extra box "other state" only when such a row exists (processing counts only the known in-progress states). Re-rendered with node and re-checked in a browser (light and dark previews replaced). Still NOT run in n8n.
```

### FOLDER PAIR n8n-flows-v4  vs  n8n-flows-film-v5
only in n8n-flows-v4: ['V4-README.md', 'mf_leads.sql']
only in n8n-flows-film-v5: ['V5-README.md']

### n8n-flows-v4/mf-form.json  vs  n8n-flows-film-v5/mf-form.json
- n8n-flows-v4/mf-form.json: size 7971 sha256 ee8b9085afc7ded60c639d9390160a33d9ca6db0a00b20d7a5e6688987f67afd
- n8n-flows-film-v5/mf-form.json: size 7970 sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
diff total lines: 4
```
97c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
```

### n8n-flows-v4/mf-hook.json  vs  n8n-flows-film-v5/mf-hook.json
- n8n-flows-v4/mf-hook.json: size 7986 sha256 7210badd6ab73dde8d33d855497f5bb103f096694be10aaa6b70ddf50ff3ada1
- n8n-flows-film-v5/mf-hook.json: size 7985 sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
diff total lines: 4
```
97c97
<     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '120 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
---
>     "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
```

### n8n-flows-v4/mf-recovery.json  vs  n8n-flows-film-v5/mf-recovery.json
- n8n-flows-v4/mf-recovery.json: size 7531 sha256 12a7ef2c70ef151c376b6ef1bb1ab6d78c21a874fca247c8aaedbfe84c757a30
- n8n-flows-film-v5/mf-recovery.json: size 7530 sha256 42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
diff total lines: 4
```
26c26
<     "query": "UPDATE mf_leads SET claimed_until=now() + interval '120 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
---
>     "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
```

### n8n-flows-v4/mf-sub-crm-mail.json  vs  n8n-flows-film-v5/mf-sub-crm-mail.json
- n8n-flows-v4/mf-sub-crm-mail.json: size 13751 sha256 7638c09a10a96800d1eb2d76e8b9a78508203864ce9e723a154a4ff01e749826
- n8n-flows-film-v5/mf-sub-crm-mail.json: size 14651 sha256 a0215012962e2e22e3923ed9ecb14bae472e0857636b7356f61e87190968918b
diff total lines: 73
```
25c25
<      "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 15000) }}"
---
>      "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 10000) }}"
36c36
<    "maxTries": 3,
---
>    "maxTries": 2,
81c81
<      "timeout": 15000
---
>      "timeout": 10000
92c92
<    "maxTries": 3,
---
>    "maxTries": 2,
101c101
<      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id), $('SubIn').first().json.claim_token] }}"
---
>      "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
129a130,161
>        "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
>        "rightValue": null,
>        "operator": {
>         "type": "boolean",
>         "operation": "true",
>         "singleValue": true
>        }
>       }
>      ],
>      "combinator": "and"
>     },
>     "options": {}
>    },
>    "name": "CrmIdOk",
>    "type": "n8n-nodes-base.if",
>    "typeVersion": 2.2,
>    "position": [
>     990,
>     60
>    ]
>   },
>   {
>    "parameters": {
>     "conditions": {
>      "options": {
>       "caseSensitive": true,
>       "leftValue": "",
>       "typeValidation": "loose"
>      },
>      "conditions": [
>       {
>        "id": "c1",
580a613,623
>       "node": "CrmIdOk",
>       "type": "main",
>       "index": 0
>      }
>     ]
>    ]
>   },
>   "CrmIdOk": {
>    "main": [
>     [
>      {
581a625,631
>       "type": "main",
>       "index": 0
>      }
>     ],
>     [
>      {
>       "node": "OutStage",
```

## Part 2b: file pairs named in the document-duplicate and table-definition lines

### n8n-flows/PAGE-STATEMENTS-DRAFT.md  vs  n8n-flows/PAGE-STATEMENTS-V4.md
- n8n-flows/PAGE-STATEMENTS-DRAFT.md: size 8070 sha256 aa7944b526ea90c61a750a20936b53835e1ce3ec2e304dd6526ba8f4240da564
- n8n-flows/PAGE-STATEMENTS-V4.md: size 15689 sha256 031554c115ed36b911622a873cc891c9ec833e89cfccd2505057af3bfbe5abb3
diff total lines: 191
```
1c1
< # Page statements, DRAFT (cloud demo session). Nothing here is a result unless a number is marked "measured, source". Words follow the publish rule: own runs, one machine, made-up data, stack condition stated, nothing independent.
---
> # Page statements V4: alerts and recovery (rewrite of section C for the v4 flows)
3,28c3,161
< ## A. Real-node flows (HubSpot node, SMTP node): what changes against the stand-in flows
< Built (n8n-flows-real-v3), NEVER RUN; this is what it does by reading and what I can and cannot say about it.
< - CRM step: the n8n HubSpot node, operation Create or Update, keyed on the E-MAIL (the node's key for contacts). The stand-in keyed on lead id AND e-mail. Consequence to state: two different lead ids with the same e-mail become ONE contact (the lead id is stored as a contact property, the last one wins); the lead table keeps one row per lead id. The node's returned contact id goes into crm_id as in the stand-in flows. HubSpot's real behaviour (rate limits, a search index that lags after a create) is NOT covered by my stand-in tests; the stand-in has a "search blind for N s" mode only.
< - Mail step: the n8n Send Email (SMTP) node with Retry On Fail OFF and On Error continue (error output). The node has no custom-header option and no timeout setting (n8n 2.46.6, read from the node description), so the lead id travels in the subject after the [demo] tag, and a slow SMTP server is bounded only by the lease. The Gmail app password sits in an n8n SMTP credential only (encrypted at rest by N8N_ENCRYPTION_KEY).
< - Not tested against the real services by me (no real mailbox, no real HubSpot account, no spend). Any sentence about HubSpot or Gmail behaviour needs the lead's own real-account run.
< 
< ## B. Lease for the film take
< - Design value 120 s: longer than the longest normal run, so recovery never takes a lead a live run still holds. Longest run in the flows today: cap stage up to 3 tries of 15 s, CRM up to 3 tries of 15 s, mail a few seconds = about 100 s worst case (a normal run takes a few seconds).
< - A lease shorter than a slow step costs a SAFE but UNNEEDED state unknown (mail_sent already set, a person decides, 1 alert): my T10 finding, nothing doubled.
< - Film take: a shorter lease makes recovery visible on camera. Candidate: 45 s, with the node timeouts and tries lowered so the worst normal run stays under it (for example stage timeout 10 s, 2 tries; CRM 10 s, 2 tries; this must be set in the flows, it is not today).
< - Recovery time to expect (derived, NOT measured): a killed run is picked up by the first recovery tick after its lease ended, so time from kill to the recovery START is between lease minus the time the run already used and lease + 30 s (tick), and the run itself takes a few more seconds. For a lead that can never succeed (T15): 3 x lease + up to 90 s to the failed state and the one alert. With lease 45: about 45 to 75 s to recovery start, about 135 to 225 s to failed.
< - MEASURED so far (my runs, one Linux machine, test lease 20 s, stand-ins): only one T10 SMTP-hold run (recovery took the lead after the lease and marked unknown). No per-lease recovery table exists yet. To get one: laptop runner `--lease 20`, `--lease 45` and `--lease 120` for K1, K2, K3B, K3, K4 (8 per point) and read `seconds_kill_to_final` min/median/max per lease from count_table.py. Until then the film must not quote a recovery time as measured.
< 
< ## C. Alerts and what n8n keeps (v3, updated 15:40Z). Tag legend: RELAYED-PASS = the lead told me the laptop/lane3 raw run printed pass, I have not read the file (laptop-local; the lead pushes a numbers file after V7); NOT RUN = built or written, no run; READ-ONLY = from reading the flows. Conditions for all: one machine, stand-in SMTP/CRM/stage, made-up data, flows commit 6ebb7f62e for the laptop runs; own runs, not independent unless it says lane3.
< 1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow." [READ-ONLY; T8 and T15 (failed leads, 1 alert each): RELAYED-PASS; unknown case via T12 on v3: NOT RUN]
< 2. "If sending the alert fails, the table keeps alert_sent=false and the alert is tried again until it goes out; after the failures ended in the test, exactly one alert arrived, the lead state did not change and no extra mail went to the intake address." [AF1: RELAYED-PASS; first-alert time and attempt count not given to me; independent check: lane3 v3 cases A and B20 RELAYED-PASS, their content not known to me]
< 3. "The alert is not instant: normally within about 30 seconds of the state change (one recovery tick); while the mail server is failing, the retry gaps are 1, 2, 3, 4, then 5 minutes per lead, so an alert can come minutes late." [30 s: READ-ONLY, no timing measured by me; gaps: READ-ONLY from the SQL; AF1 RELAYED-PASS shows a late alert arrived, seconds not given to me]
< 4. "There is no limit on alert retries (alert_attempts is only a counter)." [READ-ONLY design choice; no test asserts a cap is absent]
< 5. "The only alert channel is e-mail through the SAME mail server that sends the lead mail. While that server is down nobody is notified, and there is no second channel (no Slack, no SMS). A person would see the unsent alerts only by looking at the table: state unknown or failed with alert_sent false and alert_attempts rising." [READ-ONLY; dead-SMTP-for-10-minutes case NOT RUN; Slack alert NOT BUILT]
< 6. "How long n8n's Send Email node waits for a silent mail server is NOT measured. From the library code it is up to 2 minutes to connect, 30 seconds for the greeting, 10 minutes of silence after that; the node has no timeout setting." [AF2: NOT RUN; library values READ-ONLY from nodemailer in n8n 2.46.6]
< 7. "On v3 a lead can get TWO alert e-mails: if the mail server holds its answer longer than 60 seconds, the first send is still waiting when the sweep sends again (lane3, v3 flows 6ebb7f62, n=1: answer held 90 s, 2 alerts at about 120 s). Do NOT write "exactly one alert". On v4 the claim is 12 minutes, so a hold up to the transport limit should give one alert; a duplicate is still possible if a send outlasts 12 minutes or the table update fails after a sent alert. A duplicate, never a loss, is the design." [v3 duplicate: lane3 measured, RELAYED, n=1; B90 on v4: NOT RUN; AF1 RELAYED-PASS shows exactly 1 for a refusal fault, not for a hold]
< 8. "A lead that used up its three tries after the mail step started is called unknown, not failed." [READ-ONLY (MarkFailed SQL). V7 K3 and K3B (n=20 each, MEASURED-ON-LAPTOP, lead-read) show unknown after a kill, not this cap branch; T8 and T15 show failed when no mail step started. The cap-after-mail branch itself: NOT RUN]
< 9. "No mail is sent twice for one lead id in the tested faults." [MEASURED-ON-LAPTOP, lead-read: K1, K2, K3, K3B n=20 each, 0 doubled (80 kills, v3, lease 20 s, one machine, made-up data). T10, T11, T13, K4, K5: not in the numbers file; wording must say "in the kill points K1, K2, K3, K3B", not "all faults"]
< 10. "With the four n8n settings (EXECUTIONS_DATA_SAVE_ON_SUCCESS=none, _ON_ERROR=none, _ON_PROGRESS=false, SAVE_MANUAL_EXECUTIONS=false) n8n still keeps the lead's name and e-mail from the incoming request in its own database (webhook request body) until its pruning removes the run. Credentials (SMTP password, HubSpot token, Postgres password) and the stage key file were not found in n8n's data in the scan." [laptop V5 T7b RELAYED-PASS for the numbers (name 3, e-mail 2 in live execution_data rows; no key or password); lane3 HB171 RELAYED (body in the write-ahead file and, after a checkpoint, in execution_data; also a key sent as a body field); the age at which pruning removes it: NOT MEASURED, lane3 EXECUTIONS_DATA_PRUNE=false test pending; the four settings are REQUIRED: without them lane3 (n=1) found name, e-mail AND key]
< 11. "Do not put a secret in a lead form field." [follows from 10; lane3 HB171 RELAYED]
< Sentences I will NOT write until a file says so: any number of seconds for alert or recovery time; "deleted after N hours"; anything about a real mailbox, real HubSpot account or Slack.
---
> Changelog (2026-11-14 audit fixes; statement 19 added after lane3 HB189):
> 1. Fixed: 4, 7, 12, 13, 14, 17 now use the settled numbers (K3 and K3B 1 alert each, v3 B90 n=3, v4 B90 n=3 plus 1 laptop run, lane3 K1 144.3 s at lease 120 s); 12 lost "in my runs" and "would pass".
> 2. Moved to UNBACKED (do not publish until backed): the 30 s alert timing (6), lane3 cases A and C (8), library timeouts (16), the scan claim (18). Statements 1, 2, 3, 5 got small wording fixes.
> 3. Added: two different K3 names, the new tag RELAYED-LEAD, and one recovery rule of thumb (statement 17).
> 
> Written 2026-11-14 by the cloud demo session. Replaces section C of PAGE-STATEMENTS-DRAFT and the v4 additions draft. Nothing in this file was run by the cloud session. Plain words only.
> 
> ## Tag legend
> - MEASURED-ON-LAPTOP: the lead read the raw result files from the laptop runs and relayed the numbers. The cloud session did not open those files. Laptop-local, not pushed. These runs used the v3 flows, lease 20 s, made-up data, one machine, stand-in SMTP, CRM and stage. Written as "in the laptop runs (lead-read)".
> - RELAYED-INDEPENDENT: the lead relayed what the lane3 harness (a separate harness) printed. Raw lane3 reports HB180 and HB186 are named but were not found in the handover tree, so they could not be checked.
> - RELAYED-LEAD: the lead relayed a pass from the laptop V4-par run; the result file was not read.
> - READ-ONLY: read from the flows or the SQL, never run.
> - NOT RUN: no run exists, or none was given to the cloud session.
> - UNBACKED: a statement with no run, no definition or no named file. Do not publish until backed.
> 
> ## Two different K3 tests (never mix them)
> - demo K3 (n8n killed after the mail was delivered): the laptop harness test, statements 4 and 13.
> - lane3 K3 = this page's K3B and lane3 K6 = this page's demo K3 (lead naming, HB194). Statement 20 uses this page's names.
> 
> ## Lane3 report check
> No lane3 report was found under handover/demo3. HB180 and HB186 are absent from the handover tree. The only report file in this checkout is handover/demo/REPORT.md, a different file, not used. Every lane3 number below is a lead relay only.
> 
> ## Hard rules applied
> - No claim "within 60 s" anywhere without the 20 s test lease. The recovery wording is statements 12 and 17.
> - "Exactly one alert" is never said for a hold longer than 720 s (statement 7).
> - The word "fixed" does not appear as a claim, because no named raw file with n has reached the cloud session.
> - v3 gave two alerts in 3 of 3 lane3 B90 runs. v4 gave exactly 1 alert in 3 of 3 lane3 B90 runs, and 1 on the laptop V4-par run.
> 
> ## Statements
> 
> 1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow."
>    Tag: READ-ONLY for the design. Backing runs: v3 runs (statements 2 and 3 area) plus v4 B90 (statement 7).
>    Test: none for the design sentence.
>    Raw file: none.
> 
> 2. "On the v3 flows, a lead that failed before any mail step started ended in state failed with exactly 1 alert, no mail, no CRM write. T8: three failure kinds, one run each. T15: three runs. One machine, made-up data."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
>    Test: T8 (model stage refuses, errors or times out; 0 CRM rows, 0 mails, 0 model calls) and T15 (CRM answers an error from the start; alerts 1, 1, 1; 0 mails; 0 CRM rows; 27 CRM calls refused).
>    Raw file: V7-v3 folder, mf_result_T8.json and mf_result_T15.json, laptop-local.
>    Note: seconds to the final state for T8 by kind: refuse 88.4, error 116.9, timeout 42.5. For T15 (three runs): 91.2, 88.3 and 110.1 (limit 210). Alert timing inside those runs is not stated beyond "1 alert each".
> 
> 3. "The same failure cases (T8, T15) were not run on the v4 flows."
>    Tag: NOT RUN (no v4 result for them was given). Re-check against the laptop V4-par result before publishing, because that runner may have produced v4 numbers since.
>    Test: T8, T15 on v4.
>    Raw file: none.
> 
> 4. "On the v3 flows, in the laptop runs (lead-read), when n8n was killed after the mail step began, every lead ended unknown, none was lost and none was re-mailed, with 1 alert each: 20 of 20 for demo K3 (n8n killed after the mail was delivered) and 20 of 20 for K3B (killed after the mail was marked sent but before it was delivered). Time from kill to final state was 28.5 to 30.5 s and 28.4 to 31.0 s."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
```

### n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md  vs  n8n-flows/PAGE-STATEMENTS-V4.md
- n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md: size 1234 sha256 b25044981bd151f064072320bab0924ef48195f66df85b4e1f96525f24c3a477
- n8n-flows/PAGE-STATEMENTS-V4.md: size 15689 sha256 031554c115ed36b911622a873cc891c9ec833e89cfccd2505057af3bfbe5abb3
diff total lines: 171
```
1,8c1,161
< # Page statements, v4 additions (draft, written 16:25Z). Replaces sentence 7 of section C only when lane3 final numbers exist.
< Tags: RELAYED = the lead told me a raw run printed this, I have not read the file. READ-ONLY = read from the flows. NOT RUN = no run yet.
< V4-1. "On v4 the alert claim window is 720 seconds and a failed alert send backs off 60 seconds times the attempt count (capped at 5)." [READ-ONLY: build_mainframe.py MF_V4=1, folder n8n-flows-v4]
< V4-2. "On v3, holding the alert answer for 90 seconds gave two alert e-mails (lane3, one run)." [RELAYED, lane3 n=1, v3 flows 6ebb7f62; raw file name not given to me]
< V4-3. "On v4 the same hold (B90) gave N alert e-mails in M runs." [NOT RUN by me; fill N and M ONLY from lane3 final raw files, name the file here: ______ ]
< V4-4. "On v4 a duplicate alert is still possible if the mark step fails after a successful send, or if a send outlasts 720 seconds." [READ-ONLY design limit; no test]
< V4-5. "How long the Send Email node waits for a silent server is not measured (AF2 not run)." [NOT RUN: my sandbox has no room to start Postgres; the laptop v4 runner may run AF2]
< Rule: do not print "fixed" until V4-3 has a named raw file with n and the same pass flag B90 prints.
---
> # Page statements V4: alerts and recovery (rewrite of section C for the v4 flows)
> 
> Changelog (2026-11-14 audit fixes; statement 19 added after lane3 HB189):
> 1. Fixed: 4, 7, 12, 13, 14, 17 now use the settled numbers (K3 and K3B 1 alert each, v3 B90 n=3, v4 B90 n=3 plus 1 laptop run, lane3 K1 144.3 s at lease 120 s); 12 lost "in my runs" and "would pass".
> 2. Moved to UNBACKED (do not publish until backed): the 30 s alert timing (6), lane3 cases A and C (8), library timeouts (16), the scan claim (18). Statements 1, 2, 3, 5 got small wording fixes.
> 3. Added: two different K3 names, the new tag RELAYED-LEAD, and one recovery rule of thumb (statement 17).
> 
> Written 2026-11-14 by the cloud demo session. Replaces section C of PAGE-STATEMENTS-DRAFT and the v4 additions draft. Nothing in this file was run by the cloud session. Plain words only.
> 
> ## Tag legend
> - MEASURED-ON-LAPTOP: the lead read the raw result files from the laptop runs and relayed the numbers. The cloud session did not open those files. Laptop-local, not pushed. These runs used the v3 flows, lease 20 s, made-up data, one machine, stand-in SMTP, CRM and stage. Written as "in the laptop runs (lead-read)".
> - RELAYED-INDEPENDENT: the lead relayed what the lane3 harness (a separate harness) printed. Raw lane3 reports HB180 and HB186 are named but were not found in the handover tree, so they could not be checked.
> - RELAYED-LEAD: the lead relayed a pass from the laptop V4-par run; the result file was not read.
> - READ-ONLY: read from the flows or the SQL, never run.
> - NOT RUN: no run exists, or none was given to the cloud session.
> - UNBACKED: a statement with no run, no definition or no named file. Do not publish until backed.
> 
> ## Two different K3 tests (never mix them)
> - demo K3 (n8n killed after the mail was delivered): the laptop harness test, statements 4 and 13.
> - lane3 K3 = this page's K3B and lane3 K6 = this page's demo K3 (lead naming, HB194). Statement 20 uses this page's names.
> 
> ## Lane3 report check
> No lane3 report was found under handover/demo3. HB180 and HB186 are absent from the handover tree. The only report file in this checkout is handover/demo/REPORT.md, a different file, not used. Every lane3 number below is a lead relay only.
> 
> ## Hard rules applied
> - No claim "within 60 s" anywhere without the 20 s test lease. The recovery wording is statements 12 and 17.
> - "Exactly one alert" is never said for a hold longer than 720 s (statement 7).
> - The word "fixed" does not appear as a claim, because no named raw file with n has reached the cloud session.
> - v3 gave two alerts in 3 of 3 lane3 B90 runs. v4 gave exactly 1 alert in 3 of 3 lane3 B90 runs, and 1 on the laptop V4-par run.
> 
> ## Statements
> 
> 1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow."
>    Tag: READ-ONLY for the design. Backing runs: v3 runs (statements 2 and 3 area) plus v4 B90 (statement 7).
>    Test: none for the design sentence.
>    Raw file: none.
> 
> 2. "On the v3 flows, a lead that failed before any mail step started ended in state failed with exactly 1 alert, no mail, no CRM write. T8: three failure kinds, one run each. T15: three runs. One machine, made-up data."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
>    Test: T8 (model stage refuses, errors or times out; 0 CRM rows, 0 mails, 0 model calls) and T15 (CRM answers an error from the start; alerts 1, 1, 1; 0 mails; 0 CRM rows; 27 CRM calls refused).
>    Raw file: V7-v3 folder, mf_result_T8.json and mf_result_T15.json, laptop-local.
>    Note: seconds to the final state for T8 by kind: refuse 88.4, error 116.9, timeout 42.5. For T15 (three runs): 91.2, 88.3 and 110.1 (limit 210). Alert timing inside those runs is not stated beyond "1 alert each".
> 
> 3. "The same failure cases (T8, T15) were not run on the v4 flows."
>    Tag: NOT RUN (no v4 result for them was given). Re-check against the laptop V4-par result before publishing, because that runner may have produced v4 numbers since.
>    Test: T8, T15 on v4.
>    Raw file: none.
> 
> 4. "On the v3 flows, in the laptop runs (lead-read), when n8n was killed after the mail step began, every lead ended unknown, none was lost and none was re-mailed, with 1 alert each: 20 of 20 for demo K3 (n8n killed after the mail was delivered) and 20 of 20 for K3B (killed after the mail was marked sent but before it was delivered). Time from kill to final state was 28.5 to 30.5 s and 28.4 to 31.0 s."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
>    Test: demo K3 (1 intake mail per lead) and K3B (0 intake mails per lead). n=20 each, lease 20 s. Alerts: 1 each, read from the per_lead alerts field. K1 = 0 alerts and K2 = 0 alerts in the same series.
>    Raw file: V7-v3 folder, mf_result_K3.json and mf_result_K3B.json, laptop-local.
> 
> 5. "On the v3 flows, with the alert send alone refused by the mail server, the first alert did not come at once: in one run it arrived at 272.1 s, and there was no alert at 20 s. Do not write 'within 30 seconds' for this fault."
>    Tag: MEASURED-ON-LAPTOP (lead-read), n=1, v3 flows.
>    Test: AF1 (alert-only mail refusal, two refusals). Result: state unknown unchanged, 1 alert, 1 intake mail, 0 lost, 0 doubled.
>    Raw file: V7-v3 folder, mf_result_AF1.json, laptop-local.
> 
> 6. "On the normal path an alert goes out on the next recovery tick; the flow runs that tick every 30 s."
>    Tag: READ-ONLY for the 30 s tick in the flow.
>    Test: none.
>    Raw file: none.
>    UNBACKED (do not publish until backed): any promise such as "within about 30 seconds of the state change". No run timed the normal-path alert. NOT RUN.
> 
> 7. "On v3 a lead got two alert e-mails when the mail server held its answer for 90 seconds, because the first claim lasts 60 seconds: 2 alerts in 3 of 3 lane3 runs (B90, n=3). On v4 the alert claim window is 720 seconds, and the same 90 second hold gave exactly 1 alert in 3 of 3 lane3 runs (B90, n=3, first alert at about 120 s), plus 1 of 1 on the laptop V4-par run (pass). That is two setups. For a hold longer than 720 seconds nothing was run: a second alert is possible and untested."
>    Tag, v3 B90 (HB180): RELAYED-INDEPENDENT. Raw report HB180 not found in handover.
>    Tag, v4 B90 on lane3 (HB186): RELAYED-INDEPENDENT. Raw report HB186 not found in handover.
>    Tag, v4 B90 on the laptop V4-par: RELAYED-LEAD (result file not read).
>    Tag, hold beyond 720 s: NOT RUN.
>    Test: B90 (answer held 90 s), v3 build and v4 build.
```

### n8n-flows/PAGE-STATEMENTS-DRAFT.md  vs  n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md
- n8n-flows/PAGE-STATEMENTS-DRAFT.md: size 8070 sha256 aa7944b526ea90c61a750a20936b53835e1ce3ec2e304dd6526ba8f4240da564
- n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md: size 1234 sha256 b25044981bd151f064072320bab0924ef48195f66df85b4e1f96525f24c3a477
diff total lines: 38
```
1,28c1,8
< # Page statements, DRAFT (cloud demo session). Nothing here is a result unless a number is marked "measured, source". Words follow the publish rule: own runs, one machine, made-up data, stack condition stated, nothing independent.
< 
< ## A. Real-node flows (HubSpot node, SMTP node): what changes against the stand-in flows
< Built (n8n-flows-real-v3), NEVER RUN; this is what it does by reading and what I can and cannot say about it.
< - CRM step: the n8n HubSpot node, operation Create or Update, keyed on the E-MAIL (the node's key for contacts). The stand-in keyed on lead id AND e-mail. Consequence to state: two different lead ids with the same e-mail become ONE contact (the lead id is stored as a contact property, the last one wins); the lead table keeps one row per lead id. The node's returned contact id goes into crm_id as in the stand-in flows. HubSpot's real behaviour (rate limits, a search index that lags after a create) is NOT covered by my stand-in tests; the stand-in has a "search blind for N s" mode only.
< - Mail step: the n8n Send Email (SMTP) node with Retry On Fail OFF and On Error continue (error output). The node has no custom-header option and no timeout setting (n8n 2.46.6, read from the node description), so the lead id travels in the subject after the [demo] tag, and a slow SMTP server is bounded only by the lease. The Gmail app password sits in an n8n SMTP credential only (encrypted at rest by N8N_ENCRYPTION_KEY).
< - Not tested against the real services by me (no real mailbox, no real HubSpot account, no spend). Any sentence about HubSpot or Gmail behaviour needs the lead's own real-account run.
< 
< ## B. Lease for the film take
< - Design value 120 s: longer than the longest normal run, so recovery never takes a lead a live run still holds. Longest run in the flows today: cap stage up to 3 tries of 15 s, CRM up to 3 tries of 15 s, mail a few seconds = about 100 s worst case (a normal run takes a few seconds).
< - A lease shorter than a slow step costs a SAFE but UNNEEDED state unknown (mail_sent already set, a person decides, 1 alert): my T10 finding, nothing doubled.
< - Film take: a shorter lease makes recovery visible on camera. Candidate: 45 s, with the node timeouts and tries lowered so the worst normal run stays under it (for example stage timeout 10 s, 2 tries; CRM 10 s, 2 tries; this must be set in the flows, it is not today).
< - Recovery time to expect (derived, NOT measured): a killed run is picked up by the first recovery tick after its lease ended, so time from kill to the recovery START is between lease minus the time the run already used and lease + 30 s (tick), and the run itself takes a few more seconds. For a lead that can never succeed (T15): 3 x lease + up to 90 s to the failed state and the one alert. With lease 45: about 45 to 75 s to recovery start, about 135 to 225 s to failed.
< - MEASURED so far (my runs, one Linux machine, test lease 20 s, stand-ins): only one T10 SMTP-hold run (recovery took the lead after the lease and marked unknown). No per-lease recovery table exists yet. To get one: laptop runner `--lease 20`, `--lease 45` and `--lease 120` for K1, K2, K3B, K3, K4 (8 per point) and read `seconds_kill_to_final` min/median/max per lease from count_table.py. Until then the film must not quote a recovery time as measured.
< 
< ## C. Alerts and what n8n keeps (v3, updated 15:40Z). Tag legend: RELAYED-PASS = the lead told me the laptop/lane3 raw run printed pass, I have not read the file (laptop-local; the lead pushes a numbers file after V7); NOT RUN = built or written, no run; READ-ONLY = from reading the flows. Conditions for all: one machine, stand-in SMTP/CRM/stage, made-up data, flows commit 6ebb7f62e for the laptop runs; own runs, not independent unless it says lane3.
< 1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow." [READ-ONLY; T8 and T15 (failed leads, 1 alert each): RELAYED-PASS; unknown case via T12 on v3: NOT RUN]
< 2. "If sending the alert fails, the table keeps alert_sent=false and the alert is tried again until it goes out; after the failures ended in the test, exactly one alert arrived, the lead state did not change and no extra mail went to the intake address." [AF1: RELAYED-PASS; first-alert time and attempt count not given to me; independent check: lane3 v3 cases A and B20 RELAYED-PASS, their content not known to me]
< 3. "The alert is not instant: normally within about 30 seconds of the state change (one recovery tick); while the mail server is failing, the retry gaps are 1, 2, 3, 4, then 5 minutes per lead, so an alert can come minutes late." [30 s: READ-ONLY, no timing measured by me; gaps: READ-ONLY from the SQL; AF1 RELAYED-PASS shows a late alert arrived, seconds not given to me]
< 4. "There is no limit on alert retries (alert_attempts is only a counter)." [READ-ONLY design choice; no test asserts a cap is absent]
< 5. "The only alert channel is e-mail through the SAME mail server that sends the lead mail. While that server is down nobody is notified, and there is no second channel (no Slack, no SMS). A person would see the unsent alerts only by looking at the table: state unknown or failed with alert_sent false and alert_attempts rising." [READ-ONLY; dead-SMTP-for-10-minutes case NOT RUN; Slack alert NOT BUILT]
< 6. "How long n8n's Send Email node waits for a silent mail server is NOT measured. From the library code it is up to 2 minutes to connect, 30 seconds for the greeting, 10 minutes of silence after that; the node has no timeout setting." [AF2: NOT RUN; library values READ-ONLY from nodemailer in n8n 2.46.6]
< 7. "On v3 a lead can get TWO alert e-mails: if the mail server holds its answer longer than 60 seconds, the first send is still waiting when the sweep sends again (lane3, v3 flows 6ebb7f62, n=1: answer held 90 s, 2 alerts at about 120 s). Do NOT write "exactly one alert". On v4 the claim is 12 minutes, so a hold up to the transport limit should give one alert; a duplicate is still possible if a send outlasts 12 minutes or the table update fails after a sent alert. A duplicate, never a loss, is the design." [v3 duplicate: lane3 measured, RELAYED, n=1; B90 on v4: NOT RUN; AF1 RELAYED-PASS shows exactly 1 for a refusal fault, not for a hold]
< 8. "A lead that used up its three tries after the mail step started is called unknown, not failed." [READ-ONLY (MarkFailed SQL). V7 K3 and K3B (n=20 each, MEASURED-ON-LAPTOP, lead-read) show unknown after a kill, not this cap branch; T8 and T15 show failed when no mail step started. The cap-after-mail branch itself: NOT RUN]
< 9. "No mail is sent twice for one lead id in the tested faults." [MEASURED-ON-LAPTOP, lead-read: K1, K2, K3, K3B n=20 each, 0 doubled (80 kills, v3, lease 20 s, one machine, made-up data). T10, T11, T13, K4, K5: not in the numbers file; wording must say "in the kill points K1, K2, K3, K3B", not "all faults"]
< 10. "With the four n8n settings (EXECUTIONS_DATA_SAVE_ON_SUCCESS=none, _ON_ERROR=none, _ON_PROGRESS=false, SAVE_MANUAL_EXECUTIONS=false) n8n still keeps the lead's name and e-mail from the incoming request in its own database (webhook request body) until its pruning removes the run. Credentials (SMTP password, HubSpot token, Postgres password) and the stage key file were not found in n8n's data in the scan." [laptop V5 T7b RELAYED-PASS for the numbers (name 3, e-mail 2 in live execution_data rows; no key or password); lane3 HB171 RELAYED (body in the write-ahead file and, after a checkpoint, in execution_data; also a key sent as a body field); the age at which pruning removes it: NOT MEASURED, lane3 EXECUTIONS_DATA_PRUNE=false test pending; the four settings are REQUIRED: without them lane3 (n=1) found name, e-mail AND key]
< 11. "Do not put a secret in a lead form field." [follows from 10; lane3 HB171 RELAYED]
< Sentences I will NOT write until a file says so: any number of seconds for alert or recovery time; "deleted after N hours"; anything about a real mailbox, real HubSpot account or Slack.
---
> # Page statements, v4 additions (draft, written 16:25Z). Replaces sentence 7 of section C only when lane3 final numbers exist.
> Tags: RELAYED = the lead told me a raw run printed this, I have not read the file. READ-ONLY = read from the flows. NOT RUN = no run yet.
> V4-1. "On v4 the alert claim window is 720 seconds and a failed alert send backs off 60 seconds times the attempt count (capped at 5)." [READ-ONLY: build_mainframe.py MF_V4=1, folder n8n-flows-v4]
> V4-2. "On v3, holding the alert answer for 90 seconds gave two alert e-mails (lane3, one run)." [RELAYED, lane3 n=1, v3 flows 6ebb7f62; raw file name not given to me]
> V4-3. "On v4 the same hold (B90) gave N alert e-mails in M runs." [NOT RUN by me; fill N and M ONLY from lane3 final raw files, name the file here: ______ ]
> V4-4. "On v4 a duplicate alert is still possible if the mark step fails after a successful send, or if a send outlasts 720 seconds." [READ-ONLY design limit; no test]
> V4-5. "How long the Send Email node waits for a silent server is not measured (AF2 not run)." [NOT RUN: my sandbox has no room to start Postgres; the laptop v4 runner may run AF2]
> Rule: do not print "fixed" until V4-3 has a named raw file with n and the same pass flag B90 prints.
```

### AUDIT-PAGE-STATEMENTS-V4.md  vs  n8n-flows/PAGE-STATEMENTS-V4.md
- AUDIT-PAGE-STATEMENTS-V4.md: size 10195 sha256 13da7fabe0a1230552c09c005481bcff08acd368bb92feccf95d285803474332
- n8n-flows/PAGE-STATEMENTS-V4.md: size 15689 sha256 031554c115ed36b911622a873cc891c9ec833e89cfccd2505057af3bfbe5abb3
diff total lines: 225
```
1c1
< # Audit of PAGE-STATEMENTS-V4 (read-only, 2026-11-14)
---
> # Page statements V4: alerts and recovery (rewrite of section C for the v4 flows)
3c3,159
< Checked against: the V7 numbers file (with the lead correction of 16:50Z: K3 = 1 alert each, K3B = 1 each, K1 = 0, K2 = 0), the settled facts from the lead, and, for the READ-ONLY statements, the v4 recovery flow and the v4 table SQL (read, not run). I ran nothing.
---
> Changelog (2026-11-14 audit fixes; statement 19 added after lane3 HB189):
> 1. Fixed: 4, 7, 12, 13, 14, 17 now use the settled numbers (K3 and K3B 1 alert each, v3 B90 n=3, v4 B90 n=3 plus 1 laptop run, lane3 K1 144.3 s at lease 120 s); 12 lost "in my runs" and "would pass".
> 2. Moved to UNBACKED (do not publish until backed): the 30 s alert timing (6), lane3 cases A and C (8), library timeouts (16), the scan claim (18). Statements 1, 2, 3, 5 got small wording fixes.
> 3. Added: two different K3 names, the new tag RELAYED-LEAD, and one recovery rule of thumb (statement 17).
> 
> Written 2026-11-14 by the cloud demo session. Replaces section C of PAGE-STATEMENTS-DRAFT and the v4 additions draft. Nothing in this file was run by the cloud session. Plain words only.
> 
> ## Tag legend
> - MEASURED-ON-LAPTOP: the lead read the raw result files from the laptop runs and relayed the numbers. The cloud session did not open those files. Laptop-local, not pushed. These runs used the v3 flows, lease 20 s, made-up data, one machine, stand-in SMTP, CRM and stage. Written as "in the laptop runs (lead-read)".
> - RELAYED-INDEPENDENT: the lead relayed what the lane3 harness (a separate harness) printed. Raw lane3 reports HB180 and HB186 are named but were not found in the handover tree, so they could not be checked.
> - RELAYED-LEAD: the lead relayed a pass from the laptop V4-par run; the result file was not read.
> - READ-ONLY: read from the flows or the SQL, never run.
> - NOT RUN: no run exists, or none was given to the cloud session.
> - UNBACKED: a statement with no run, no definition or no named file. Do not publish until backed.
> 
> ## Two different K3 tests (never mix them)
> - demo K3 (n8n killed after the mail was delivered): the laptop harness test, statements 4 and 13.
> - lane3 K3 = this page's K3B and lane3 K6 = this page's demo K3 (lead naming, HB194). Statement 20 uses this page's names.
> 
> ## Lane3 report check
> No lane3 report was found under handover/demo3. HB180 and HB186 are absent from the handover tree. The only report file in this checkout is handover/demo/REPORT.md, a different file, not used. Every lane3 number below is a lead relay only.
> 
> ## Hard rules applied
> - No claim "within 60 s" anywhere without the 20 s test lease. The recovery wording is statements 12 and 17.
> - "Exactly one alert" is never said for a hold longer than 720 s (statement 7).
> - The word "fixed" does not appear as a claim, because no named raw file with n has reached the cloud session.
> - v3 gave two alerts in 3 of 3 lane3 B90 runs. v4 gave exactly 1 alert in 3 of 3 lane3 B90 runs, and 1 on the laptop V4-par run.
> 
> ## Statements
> 
> 1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow."
>    Tag: READ-ONLY for the design. Backing runs: v3 runs (statements 2 and 3 area) plus v4 B90 (statement 7).
>    Test: none for the design sentence.
>    Raw file: none.
> 
> 2. "On the v3 flows, a lead that failed before any mail step started ended in state failed with exactly 1 alert, no mail, no CRM write. T8: three failure kinds, one run each. T15: three runs. One machine, made-up data."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
>    Test: T8 (model stage refuses, errors or times out; 0 CRM rows, 0 mails, 0 model calls) and T15 (CRM answers an error from the start; alerts 1, 1, 1; 0 mails; 0 CRM rows; 27 CRM calls refused).
>    Raw file: V7-v3 folder, mf_result_T8.json and mf_result_T15.json, laptop-local.
>    Note: seconds to the final state for T8 by kind: refuse 88.4, error 116.9, timeout 42.5. For T15 (three runs): 91.2, 88.3 and 110.1 (limit 210). Alert timing inside those runs is not stated beyond "1 alert each".
> 
> 3. "The same failure cases (T8, T15) were not run on the v4 flows."
>    Tag: NOT RUN (no v4 result for them was given). Re-check against the laptop V4-par result before publishing, because that runner may have produced v4 numbers since.
>    Test: T8, T15 on v4.
>    Raw file: none.
> 
> 4. "On the v3 flows, in the laptop runs (lead-read), when n8n was killed after the mail step began, every lead ended unknown, none was lost and none was re-mailed, with 1 alert each: 20 of 20 for demo K3 (n8n killed after the mail was delivered) and 20 of 20 for K3B (killed after the mail was marked sent but before it was delivered). Time from kill to final state was 28.5 to 30.5 s and 28.4 to 31.0 s."
>    Tag: MEASURED-ON-LAPTOP (lead-read).
>    Test: demo K3 (1 intake mail per lead) and K3B (0 intake mails per lead). n=20 each, lease 20 s. Alerts: 1 each, read from the per_lead alerts field. K1 = 0 alerts and K2 = 0 alerts in the same series.
>    Raw file: V7-v3 folder, mf_result_K3.json and mf_result_K3B.json, laptop-local.
> 
> 5. "On the v3 flows, with the alert send alone refused by the mail server, the first alert did not come at once: in one run it arrived at 272.1 s, and there was no alert at 20 s. Do not write 'within 30 seconds' for this fault."
>    Tag: MEASURED-ON-LAPTOP (lead-read), n=1, v3 flows.
>    Test: AF1 (alert-only mail refusal, two refusals). Result: state unknown unchanged, 1 alert, 1 intake mail, 0 lost, 0 doubled.
>    Raw file: V7-v3 folder, mf_result_AF1.json, laptop-local.
> 
> 6. "On the normal path an alert goes out on the next recovery tick; the flow runs that tick every 30 s."
>    Tag: READ-ONLY for the 30 s tick in the flow.
>    Test: none.
>    Raw file: none.
>    UNBACKED (do not publish until backed): any promise such as "within about 30 seconds of the state change". No run timed the normal-path alert. NOT RUN.
> 
> 7. "On v3 a lead got two alert e-mails when the mail server held its answer for 90 seconds, because the first claim lasts 60 seconds: 2 alerts in 3 of 3 lane3 runs (B90, n=3). On v4 the alert claim window is 720 seconds, and the same 90 second hold gave exactly 1 alert in 3 of 3 lane3 runs (B90, n=3, first alert at about 120 s), plus 1 of 1 on the laptop V4-par run (pass). That is two setups. For a hold longer than 720 seconds nothing was run: a second alert is possible and untested."
>    Tag, v3 B90 (HB180): RELAYED-INDEPENDENT. Raw report HB180 not found in handover.
>    Tag, v4 B90 on lane3 (HB186): RELAYED-INDEPENDENT. Raw report HB186 not found in handover.
>    Tag, v4 B90 on the laptop V4-par: RELAYED-LEAD (result file not read).
>    Tag, hold beyond 720 s: NOT RUN.
>    Test: B90 (answer held 90 s), v3 build and v4 build.
>    Note: "exactly 1 alert" applies to the 90 s hold only.
> 
> 8. UNBACKED (do not publish until backed). Relayed only: in two other lane3 cases the first alert came at about 270 s (case A, n=2) and at about 750 s (case C, n=1).
>    Tag: UNBACKED, RELAYED-INDEPENDENT. Cases A and C have no definition, no flows version and no file. Case C at 750 s is near the 720 s window and could be misread. Do not use for any alert-time sentence.
>    Test: lane3 case A and case C. NOT RUN by the cloud session.
```

### AUDIT-VIDEO-RUNSHEET.md  vs  VIDEO-RUNSHEET.md
- AUDIT-VIDEO-RUNSHEET.md: size 8874 sha256 7b633259ba39d268cfa9b6a014edad95551a2979ff456d651bc4e4f88924b612
- VIDEO-RUNSHEET.md: size 22485 sha256 5eff2ed7d2838f2e3df70f0646ec727d7577c2f8425f748ea513cd10934eed40
diff total lines: 150
```
1c1
< # Audit of the video run sheet (read-only, made-up data, no new measurements)
---
> # Video run sheet: the ONE video (main flow plus the doubtful-case scene)
3,4c3,88
< Inputs read in full: the run sheet and the V7 numbers file (lead-read, with the 16:50Z correction that per_lead rows carry alerts: K3 = 1 each, K3B = 1 each, K1 = 0, K2 = 0).
< Lane3 report HB186: grep over the handover folder found NO file containing it. It is absent, so the v4 claims (B90 n=3, exactly 1 alert at about 120 s, plus 1 on the laptop V4-par) rest on the settled facts given to me, not on a document I could open. The V7 file still says "B90 n=2" for v4; that line is stale against the settled n=3.
---
> Changelog (WP5 update, plan-4 N-lite)
> - Matched to the real take: lease 45 s; real mail service and real CRM service in scenes 1 to 5 (made-up people only); the n8n execution list IS filmed (old "do NOT open" rule removed, and it is not shown as proof of privacy); claim is only "a lead sent twice with the same id is processed once".
> - (SUPERSEDED 17:05Z, lead answer: the "lease plus 25 to 30 s" caption is DROPPED; no recovery number in any caption until lane3 lease-45 runs land, then the caption is the measured median and max at lease 45, whatever they are.) Old text: recovery wording was "about the lease plus 25 to 30 s", an estimate; 45 s is UNMEASURED, so no screen caption carries a measured recovery number. All V7 and lane3 numbers moved to the closing card as labelled history (older flow version v3, stand-ins, 20 s test lease). Doubtful scene (6 to 10) is filmed on the stand-in with the exact caption in scene 7; option B (kill after delivery) dropped.
> - "(sped up)" labels re-checked (scenes 4, 5, 9, 11): the real wait is read from the stopwatch overlay in the take, never predicted. EST total re-done: 355 s core, 380 s with scene 11.
> 
> Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, section 7), N8N-START, DESIGN-A-README, the table screen README, RUN-ON-LAPTOP and PAGE-STATEMENTS-DRAFT. Nothing here is a new result. All people in the take are made up (addresses only on example.test).
> 
> What is real and what is a stand-in in the take
> - Scenes 1 to 4: real mail through the real mail service, real CRM service, the n8n main frame (flows real-v4, v5 changes only the CRM id step), lease 45 s. Made-up people only.
> - Scene 5 (CRM refuses) needs a switch a real CRM does not have: filmed on a stand-in CRM and captioned so (owner confirms, see risk 7).
> - Scenes 6 to 10 (doubtful case): film flows, a stage with a loopback fake model, the SMTP stand-in with .drop = 1, the table screen. Scene 11 on the stand-in too.
> - Numbers: every V7 number was measured on v3 flows, stand-ins, lease 20 s. The take runs other flows at lease 45 s. So those numbers back nothing on screen in scenes 1 to 11 (except the labelled history line in scene 11) and appear only on the closing card, labelled as history.
> 
> How to read the tags
> - EST = my estimate of screen time, not measured.
> - MEASURED-ON-LAPTOP lead-read = a number the lead read from raw files, quoted from V7-NUMBERS-lead-read with row and test name. Raw files are laptop-local; I have not opened them.
> - RELAYED-INDEPENDENT = lane3 figures relayed to me (lane3 v4 K1 144.3 s at lease 120 s, n=1; lane3 B90). Not opened by me.
> - NO NUMBER = no measured row backs a number for this scene, so nothing numeric goes on screen.
> - Sped up: wherever a wait is sped up, the screen shows the words "sped up" and the real wait (read from the stopwatch overlay) next to them.
> - Lease: the take runs at lease 45 s and the screen shows "setting: lease 45 s" in scenes 4, 5 and 9. The 45 s lease is UNMEASURED. Never write "within 60 s" and never "alert within 30 s".
> - Recovery wording: NONE for now (lead 17:05Z dropped the plus 25 to 30 s caption); after lane3 lease-45 runs land: measured median and max at lease 45 with n and the setting on screen. Old text: "about the lease plus 25 to 30 s, an estimate". Source: lane3 v4 K1 144.3 s at lease 120 s (n=1, RELAYED-INDEPENDENT) and the laptop 20 s data, as combined by the lead. Note from my read of V7 FINAL: K1 median 29.65 s and max 59.6 s at lease 20 s are about lease + 10 and lease + 40, so the 25 to 30 figure is the lead's reading, not a row I can point to. At 45 s the estimate is roughly 70 to 75 s: for planning the sped-up cut only, never a caption number.
> - Two different tests are both called K3. Demo K3 = n8n killed after the mail was delivered. Lane3 K3 = killed after the CRM write. Never mix them. Neither backs the stand-in drop in scenes 7 to 9.
> 
> ## The run sheet
> 
> | Scene | What the owner does (made-up data only) | What the viewer sees | Time | Backing number (status) and caption rule | Must NOT be claimed in this scene |
> |---|---|---|---|---|---|
> | 1. Stack at rest | Opens the prepared screen set: the n8n flow list (entry flows and recovery flow switched on, table-screen flow if it exists), the lead table, the CRM list, the intake mailbox view, and the n8n execution list. Types and clicks nothing in the list. Executions older than the take are pruned first; if a leftover execution shows, do not open it. | Panes empty or at rest, the execution list on screen (status and time columns). Caption card: "made-up people, real mail and CRM services". No address on screen except example.test. | 25 s EST | NO NUMBER on screen. History only: V7 FINAL / first table T14 (one idle run, 120 s, v3 on stand-ins): 0 stage, 0 model, 0 CRM, 0 SMTP, 0 table rows. MEASURED-ON-LAPTOP lead-read. It describes the old stand-in stack, not this take. | Any number. That the execution list proves privacy: it does not, the request body stays in n8n data until pruned. A real person's name or address. Opening an execution that is not made-up data. |
> | 2. One lead goes in | Runs the one prepared send note (saved text, owner pastes it) that posts one made-up lead (made-up person on example.test, key L plus 16 hex, the key is the door id) to the form entry on the LOOPBACK address, path mf-form. | Reply with a verdict (new or done). Then: table row state done, mail_sent true; CRM list shows 1 row (real CRM service); intake mailbox shows 1 mail with subject starting "[demo] lead", sender and receiver addresses cropped or hidden. | 40 s EST | NO NUMBER. No measured row covers the normal path on the real services. "A few seconds" only as the owner's live observation. | Any speed claim as a result. That the model call is real if the stage is a stand-in (say which). Any real address on screen. Gmail or HubSpot behaviour beyond what this one take shows (WP6 smoke not yet run). |
> | 3. Same lead sent again | Pastes the same send note again with the same lead key. | The reply gives the stored state, not a new run. CRM list still 1 row, intake still 1 mail. Caption: "a lead sent twice with the same id is processed once". The screen is the evidence. | 25 s EST | NO NUMBER. T13 (n=13, 3 at once plus a database kill, runner report, raw NOT re-read) is not a resend test and is not quoted. K1, K2, K3, K3B are kill tests and do not back this scene. | The same person through two different doors being one lead (NO such claim anywhere). "No duplicates ever" or "in all faults". Any number. |
> | 4. Kill n8n mid-lead, recovery finishes it | Sends a new made-up lead. At the kill point (after the claim row is written, before the CRM write, as K1) stops n8n with the prepared stop note, then restarts it. Screen shows "setting: lease 45 s". Waits with the stopwatch overlay, then cuts or speeds up. | Table row sits in state processing, then goes to done on its own. CRM 1 row, intake 1 mail. Label "sped up" with the real wait from the overlay. Caption: "recovery takes about the lease plus 25 to 30 s (an estimate, not measured at 45 s)". | 60 s EST (real wait: unmeasured at 45 s; planning guess about 70 to 75 s) | NO NUMBER measured for 45 s. Basis of the estimate: lane3 v4 K1 144.3 s at lease 120 s, n=1 (RELAYED-INDEPENDENT) and V7 FINAL K1 (n=20, lost 0, doubled 0, 18.0 / 29.65 / 59.6 s) and K2 (n=20, 17.3 / 29.5 / 59.4 s) at lease 20 s, v3 (MEASURED-ON-LAPTOP lead-read). Those go on the closing card only. | Any measured recovery number for 45 s. "Within 60 s", "within 30 s". "Lease plus 25" as a fact (it is an estimate). That the kill landed at the intended point unless the rehearsal showed it (a person may miss the window; the kill can land after the CRM write, then only the after-CRM outcome is shown). Postgres kill (K5) or model stage kill (K4): not run. |
> | 5. A lead that can never finish (CRM refuses) | Switches the stand-in CRM to refuse every call (prepared note), sends a made-up lead, waits with the stopwatch overlay, then cuts or speeds up. Screen shows "setting: lease 45 s" and "stand-in CRM: a real CRM has no switch to refuse every call". | After a long wait the row reaches state failed. Intake: 0 mails for this lead. CRM: 0 rows. One alert mail arrives. Label "sped up" with the real wait from the overlay. | 45 s EST (real wait: unmeasured at 45 s; the v3 20 s runs took 88 to 110 s, which does not transfer) | NO NUMBER on screen. History: V7 FINAL T15 (n=3, lost 0, doubled 0, 3 failed, 91.2 / 88.3 / 110.1 s, limit 210) and first table T15 (alerts 1,1,1, 0 mails, 0 CRM rows); T8 (n=3: 0 CRM writes, 0 mails, 0 model calls, 1 alert each). All v3, stand-ins, lease 20 s, MEASURED-ON-LAPTOP lead-read. | "Alert within 30 s". "Always exactly one alert": v3 sent 2 on a slow alert send (lane3 B90, 3 of 3, RELAYED-INDEPENDENT) and v4 is only n=3 plus laptop 1. Any wait time as a number. 27 refused CRM calls: do not quote. That a real CRM was made to refuse. |
> | 6. Doubtful case, step 1: the lead goes in | Sends a made-up lead through the film-flows entry (LOOPBACK address, path mf-form) with the mail stand-in already armed (.drop = 1, see step 2). | The request goes in and n8n answers. Intake list still empty. Label on screen: "test scene on stand-ins". | 20 s EST | NO NUMBER (entry READ-ONLY per DOUBTFUL-SCENE). | Anything about a real mailbox or a real form site. That this scene uses the real services. |
> | 7. Doubtful case, step 2: the mail may or may not have gone | Arms the SMTP stand-in with .drop = 1 before the send (it accepts a mail, then drops the connection without saying queued). Says on screen: "stand-in fault". | Caption exactly: "Test scene on a stand-in mail server: a real mailbox has no switch to drop a connection after accepting a mail." Second line allowed: "the mail server took the mail, the answer never came back". No real mailbox shown. | 30 s EST | NO NUMBER. T12 (this fault) was NOT RUN on v3; the earlier v2 T12 runs (5 samples, raw not kept) are not a measured number. K3 and K3B are n8n kills, a different fault, and do not back this scene. | That a real mailbox can do this. That the mail was sent, or that it was not: nobody knows, that is the point. Any count or timing for the drop. Lane3 K3 (killed after the CRM write): a different test, never cite it. |
> | 8. Doubtful case, step 3: the answer says unknown (UNBACKED, fallback) | Fallback: no typing, no reading aloud; voice says only that the outcome is unknown. Shows the reply only if the rehearsal confirmed a reply exists on these flows and shows its wording. | Fallback: caption "outcome unknown, nobody can say whether the mail went". If confirmed in rehearsal: the reply shows outcome unknown, not done. | 10 s EST (fallback) | NO NUMBER. READ-ONLY (OutUnknown node); reply text not re-checked. With the stand-in drop n8n stays up, so a reply is likely (my inference, not checked). | Any reply wording before rehearsal. Mark this scene CUT if no reply exists and the fallback caption adds nothing. |
> | 9. Doubtful case, step 4: one alert, no second mail | Waits with the stopwatch overlay, then cuts or speeds up. Shows "setting: lease 45 s". Opens the alert mail in the stand-in inbox. | Alert mail with subject "[demo] Lead desk: mail outcome unknown for the lead id" and text "the mail may or may not have been sent. A person decides." Intake list shows 1 mail (stand-in took it; confirm in rehearsal, never run on v3), unchanged after the lease passes. Label "sped up" with the real wait. | 40 s EST (real wait unmeasured at 45 s) | NO NUMBER on screen. History: V7 FINAL K3 (28.5 / 29.45 / 30.5 s) and K3B (28.4 / 29.45 / 31.0 s), n=20 each, lost 0, doubled 0, UNKNOWN 20, 1 alert each (16:50Z correction), at lease 20 s. They back the kill variant only, not the drop variant, and not 45 s. | "Alert within 30 s" (any form). "Exactly one alert" as a rule: it held for those kill runs only; AF1 first alert was 272.1 s at the test settings (n=1). Any alert count or second-mail claim for the drop variant: not backed, the rehearsal decides what the screen shows. Slack alert: NOT BUILT. |
> | 10. Doubtful case, step 5: the table row (UNBACKED, fallback) | Fallback (keep it): a plain picture of the rows taken in rehearsal, or a one-time n8n database-node preview selecting only the seven safe columns. The table screen is BUILT, NOT RUN (laptop rehearsal in progress): show it only if it worked first time in rehearsal, and do not say it works until then. | Row: state unknown, mail_sent true, alert_sent true (false while the alert waits). No name or e-mail column. Caption: "the table row is the flow's belief, not proof the mail arrived". | 30 s EST | NO NUMBER. V7 has no alert_sent column, only a per-lead alerts count (K3 and K3B 1 each). State unknown unchanged after the alert: AF1 (n=1), history only. | That the table screen runs. That V7 has an alert_sent column. That this view proves privacy (it does not; the request body stays in n8n data until pruned). |
> | 11. OPTIONAL: the alert mail is refused twice (UNDER REVIEW: audit advises cut) | Arms the alert-only refusal on the stand-in (AF1 fault: answers 451 twice), sends a doubtful lead, then jumps. On screen: "sped up, real wait read from the overlay, test setting". | Row shows unknown with alert_sent false, then true when the alert finally goes out. | 25 s EST | History only, caption allowed: "in one earlier test (n=1, older flow version, test settings) the first alert took 272.1 s". V7 first table AF1 (n=1): first alert 272.1 s, no alert at 20 s, then 1 alert, 0 extra intake mails, state unknown. MEASURED-ON-LAPTOP lead-read. 45 s: unmeasured. | "Alert within 30 s" or any alert time for this take. Calling it a "dead server" (a 451 refusal twice). A claim from one run. A second channel: there is none. |
> | 12. Closing card | No clicks. Voice over one card, six short lines. | Line 1, claim: a lead sent twice with the same id is processed once. Line 2, history (older flow version v3, stand-ins, 20 s test lease): kill series K1, K2, K3, K3B, 80 kills, 0 lost, 0 doubled; 40 of the 80 (K3, K3B) ended UNKNOWN by design, a person decides. Line 3, recovery: about the lease plus 25 to 30 s, an estimate (lane3 v4 K1 144.3 s at lease 120 s, n=1, relayed independent, plus the 20 s laptop data); the take ran at 45 s, which is NOT measured. Line 4, alerts: v3 sent two alerts on a slow alert send (lane3 3 of 3); v4 one (lane3 n=3 plus laptop 1, relayed). Line 5, retention: the request body, with the made-up name and address, stays in n8n data until pruned (age not measured). Line 6, not tested: other mailboxes or CRMs, Slack alert, other leases; one machine, made-up people, own runs. | 30 s EST | V7 first table: K1, K2, K3, K3B, n=20 each, lost 0, doubled 0 (80 kills); K3 and K3B UNKNOWN 20 each. Lane3 v4 K1 144.3 s at lease 120 s (n=1, RELAYED-INDEPENDENT). Lane3 B90: v3 two alerts in 3 of 3; v4 one alert, n=3 plus laptop 1. All labelled as history, none measured at 45 s. | "All faults". "Nothing is kept". "Within 60 s". "Alert within 30 s". The same person through two doors. Anything independent about v3 numbers. Any measured recovery number for 45 s. The execution list or table as proof of privacy. |
> 
> ## Total running time (EST)
> - Core scenes 1 to 10 and 12: 25 + 40 + 25 + 60 + 45 + 20 + 30 + 10 + 40 + 30 + 30 = 355 s, about 5 min 55 s. (Before: 340 s; scene 1 +10 s for the execution list, scene 7 +5 s for the longer caption.)
> - With the optional scene 11: 380 s, about 6 min 20 s.
> - Scene 8 drops out (CUT) if the rehearsal shows no reply and the fallback adds nothing: subtract 10 s.
> - All times are EST. Real waits behind the sped-up scenes (4, 5, 9, 11) are UNMEASURED at 45 s; read them from the stopwatch in the take. The old measured waits (K1 up to 59.6 s, T15 88.3 to 110.1 s, K3 and K3B about 30 s, AF1 272.1 s) were at lease 20 s on v3 and do not transfer.
> 
> ## Risks the owner must see
> 1. The table screen is BUILT, NOT RUN: the laptop rehearsal is in progress; do not say it works. Keep the screenshot fallback: (a) a picture of the rows taken during rehearsal, columns lead id, state, attempts, mail_sent, alert_sent, alert_attempts, updated at only; or (b) a one-time database-node preview in the n8n editor with the same safe columns.
> 2. The 45 s lease has no measurement: recovery, the failed-lead wait and the alert wait on screen are all unmeasured; no caption number for them. The "plus 25 to 30 s" is an estimate whose basis is one lane3 run at 120 s and 20 s laptop data that does not obviously give 25 to 30 (K1 median is about lease + 10, max about lease + 40).
> 3. The execution list is filmed. It shows made-up data only if every execution in it is from made-up leads; prune old ones first. It must not be presented as privacy proof: the request body stays in n8n data until pruned.
> 4. Timing of the hand-made kill in scene 4: it must land after the claim row and before the CRM write. A person may miss; the kill can also land after the CRM write. Rehearse; state only what the take shows.
> 5. Scene 7 to 9 numbers: the drop fault has no measured row (T12 not run on v3), and the intake count (expected 1) and the alert count with the drop are unconfirmed until rehearsal. K3 and K3B do not back them.
> 6. Frame scan: the owner's scan must find no address except example.test. The real receiver and sender mailboxes (throwaway accounts) show addresses in mail panes and headers; crop or hide them, check every frame.
> 7. Scene 5 uses the stand-in CRM (a real CRM cannot be told to refuse). If the owner wants the whole take on real services, scene 5 must be cut. Open question for the owner.
> 8. Which lease is shipped is not settled: real-v4 and v5 use 45 s, DESIGN-A-README says 120 s for its flows folder. The closing card names the take's 45 s and the 120 s lane3 figure separately.
> 9. Real services (scenes 1 to 4) have not been run in the WP6 smoke: HubSpot id field, Gmail timing and subject unchanged are open (plan-4 section 8).
> 10. Step-2 fault for a real mailbox and the Slack alert are NOT BUILT; the take says "stand-in" or cuts.
> 
> ## What must be rehearsed on the laptop before the take
> 1. Import and activate the table screen flow (the rehearsal under way): open it once; confirm seven columns and no name or address column; if it fails, use the fallback picture.
> 2. The prepared send note: one lead through mf-form on the LOOPBACK address on the real flows; check reply wording for done, for the repeat, and for unknown.
> 3. The stand-in drop on the film flows with .drop = 1: run it five times; note intake count (0 or 1), alert count, state, real seconds to alert, and whether a reply comes back (scene 8).
> 4. The hand kill in scene 4: time the stop note, 5 tries, record how often it lands before the CRM write.
> 5. The refuse-every-call switch on the stand-in CRM (scene 5): note the real seconds at lease 45 s.
> 6. The alert-only refusal (scene 11, if kept): confirm the cut and the overlay text.
> 7. Check the screens show the execution list only with made-up data, and no real name, no address except example.test, no key.
> 8. Check no long code string, link or host name is visible in any pane or caption.
> 9. Check the label "setting: lease 45 s" is visible in scenes 4, 5 and 9.
> 10. Run the whole take once with a stopwatch; compare to the EST column and re-total.
> 
> ## Open decisions for the lead
> Full table in AUDIT-VIDEO-RUNSHEET.md (written for the 20 s plan; where it conflicts with this sheet, this sheet follows plan-4).
```

### n8n-flows/mf_leads.sql  vs  n8n-flows-v3/mf_leads.sql
- n8n-flows/mf_leads.sql: size 881 sha256 7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee
- n8n-flows-v3/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
diff total lines: 14
```
1c1,2
< -- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
---
> -- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
> -- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
14c15,20
<   updated_at    timestamptz NOT NULL DEFAULT now());
---
>   updated_at    timestamptz NOT NULL DEFAULT now(),
>   -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
>   alert_sent    boolean NOT NULL DEFAULT false,
>   alert_token   text,
>   alert_until   timestamptz,
>   alert_attempts int NOT NULL DEFAULT 0);
```

### n8n-flows-v3/mf_leads.sql  vs  n8n-flows-v4/mf_leads.sql
- n8n-flows-v3/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
- n8n-flows-v4/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
diff total lines: 0
```
```

### n8n-flows/mf_leads.sql  vs  n8n-flows-v4/mf_leads.sql
- n8n-flows/mf_leads.sql: size 881 sha256 7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee
- n8n-flows-v4/mf_leads.sql: size 1437 sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0
diff total lines: 14
```
1c1,2
< -- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
---
> -- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
> -- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
14c15,20
<   updated_at    timestamptz NOT NULL DEFAULT now());
---
>   updated_at    timestamptz NOT NULL DEFAULT now(),
>   -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
>   alert_sent    boolean NOT NULL DEFAULT false,
>   alert_token   text,
>   alert_until   timestamptz,
>   alert_attempts int NOT NULL DEFAULT 0);
```

### n8n-flows-real-v5/V5-README.md  vs  n8n-flows-film-v5/V5-README.md
- n8n-flows-real-v5/V5-README.md: size 3099 sha256 331c54bed301555f3cb9cf416d4c160a83749ea2abf7698b209337b28079d015
- n8n-flows-film-v5/V5-README.md: size 3099 sha256 331c54bed301555f3cb9cf416d4c160a83749ea2abf7698b209337b28079d015
diff total lines: 0
```
```

## Part 3: referrer table
live documents searched: handover/demo/VIDEO-RUNSHEET.md, handover/flows-audit/README.md, handover/demo/n8n-flows-film-v5/V5-README.md, handover/demo/n8n-flows-real-v5/V5-README.md, handover/demo/RUN-ON-LAPTOP.md
Match rule: item name not preceded or followed by [A-Za-z0-9_-] (so "n8n-flows" does not match "n8n-flows-v3"); for paths also the last path segment is searched.

| item | scope | referrer file:line | line text |
|---|---|---|---|
| AUDIT-PAGE-STATEMENTS-V4.md | live-doc | none found | |
| AUDIT-PAGE-STATEMENTS-V4.md | whole fa/ tree | 7 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| AUDIT-VIDEO-RUNSHEET.md | live-doc | handover/demo/VIDEO-RUNSHEET.md:74 | Full table in AUDIT-VIDEO-RUNSHEET.md (written for the 20 s plan; where it conflicts with this sheet, this sheet follows plan-4). |
| AUDIT-VIDEO-RUNSHEET.md | whole fa/ tree | 9 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| DESIGN-A-README.md | live-doc | handover/demo/RUN-ON-LAPTOP.md:46 | - `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step). |
| DESIGN-A-README.md | whole fa/ tree | 50 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| FILM-README.md | live-doc | none found | |
| FILM-README.md | whole fa/ tree | 9 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| N8N-RERUN-1.md | live-doc | none found | |
| N8N-RERUN-1.md | whole fa/ tree | 97 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| N8N-START.md | live-doc | none found | |
| N8N-START.md | whole fa/ tree | 97 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| NODE-DIFF-vs-film.txt | live-doc | none found | |
| NODE-DIFF-vs-film.txt | whole fa/ tree | 11 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| ORDERS.md | live-doc | handover/flows-audit/README.md:5 | ORDERS.md (lead writes), REPORT.md (you write, newest on top), QUESTIONS.md (you ask). |
| ORDERS.md | whole fa/ tree | 43 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| PAGE-STATEMENTS-DRAFT.md | live-doc | none found | |
| PAGE-STATEMENTS-DRAFT.md | whole fa/ tree | 16 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| PAGE-STATEMENTS-V4-DRAFT.md | live-doc | none found | |
| PAGE-STATEMENTS-V4-DRAFT.md | whole fa/ tree | 13 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| PAGE-STATEMENTS-V4.md | live-doc | none found | |
| PAGE-STATEMENTS-V4.md | whole fa/ tree | 106 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| PLAN-4-NLITE-FROM-LEAD.md | live-doc | none found | |
| PLAN-4-NLITE-FROM-LEAD.md | whole fa/ tree | 61 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| REPORT.md | live-doc | handover/flows-audit/README.md:5 | ORDERS.md (lead writes), REPORT.md (you write, newest on top), QUESTIONS.md (you ask). |
| REPORT.md | whole fa/ tree | 118 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| RUN-ON-LAPTOP.md | live-doc | none found | |
| RUN-ON-LAPTOP.md | whole fa/ tree | 43 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| V3-README.md | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| V3-README.md | whole fa/ tree | 26 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| V4-README.md | live-doc | none found | |
| V4-README.md | whole fa/ tree | 27 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| V5-NODE-DIFF.txt | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:14 | - Node-by-node diff real-v5 against real-v4: see V5-NODE-DIFF.txt (only SetCrmId, CrmIdOk with its connections, the credential id). Film-v5 against film-v4: same, without the credential line. |
| V5-NODE-DIFF.txt | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:14 | - Node-by-node diff real-v5 against real-v4: see V5-NODE-DIFF.txt (only SetCrmId, CrmIdOk with its connections, the credential id). Film-v5 against film-v4: same, without the credential line. |
| V5-NODE-DIFF.txt | whole fa/ tree | 12 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| VIDEO-RUNSHEET.md | live-doc | none found | |
| VIDEO-RUNSHEET.md | whole fa/ tree | 152 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| build_flows.py | live-doc | none found | |
| build_flows.py | whole fa/ tree | 28 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| build_mainframe.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:8 | real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:9 | film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:8 | real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:9 | film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| build_mainframe.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| build_mainframe.py | whole fa/ tree | 95 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| crm_stub.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| crm_stub.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| crm_stub.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:19 | - crm_stub.py: control field upsert_answer on POST /control: "id" (default, the old answer), "vid", "none". Persistent until set back. |
| crm_stub.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| crm_stub.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:19 | - crm_stub.py: control field upsert_answer on POST /control: "id" (default, the old answer), "vid", "none". Persistent until set back. |
| crm_stub.py | whole fa/ tree | 30 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| desk-error-notifier.json | live-doc | none found | |
| desk-error-notifier.json | whole fa/ tree | 31 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| desk-webhook-door.json | live-doc | none found | |
| desk-webhook-door.json | whole fa/ tree | 42 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| desk_proxy.py | live-doc | none found | |
| desk_proxy.py | whole fa/ tree | 11 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| dn1.py | live-doc | none found | |
| dn1.py | whole fa/ tree | 38 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| dn1_common.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:45 | - `n8n-tests/`: `dn1_common.py` (shared helpers, ports, process control, the exact environment the stage gets), `smtp_catcher.py` (mail stand-in), plus the Design B files (not needed here). |
| dn1_common.py | whole fa/ tree | 66 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf-form.json | live-doc | none found | |
| mf-form.json | whole fa/ tree | 529 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf-hook.json | live-doc | none found | |
| mf-hook.json | whole fa/ tree | 477 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf-recovery.json | live-doc | none found | |
| mf-recovery.json | whole fa/ tree | 444 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf-sub-crm-mail.json | live-doc | none found | |
| mf-sub-crm-mail.json | whole fa/ tree | 698 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:47 | - What needs docker: only Postgres, in five places: run_mf.py (`docker ps/pull/run/exec/rm`), mf.py (`docker exec <name> psql ...`, `pg_isready`, and `docker kill` / `docker start` for the Postgres ki |
| mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:54 | ## 7. Counting rule (outside the flow, in mf.py) |
| mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:61 | ## 8. Pass criteria per test (what mf.py writes as PASS; read the `why` line, not only the word) |
| mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| mf.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| mf.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| mf.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| mf.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| mf.py | whole fa/ tree | 157 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| mf_leads.sql | live-doc | handover/demo/RUN-ON-LAPTOP.md:46 | - `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step). |
| mf_leads.sql | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| mf_leads.sql | whole fa/ tree | 137 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-a-cause-1 | live-doc | none found | |
| n8n-a-cause-1 | whole fa/ tree | 21 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-a-cause-1.md | live-doc | none found | |
| n8n-a-cause-1.md | whole fa/ tree | 19 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-diag-1 | live-doc | none found | |
| n8n-diag-1 | whole fa/ tree | 11 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-diag-1.md | live-doc | none found | |
| n8n-diag-1.md | whole fa/ tree | 10 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows | live-doc | handover/demo/RUN-ON-LAPTOP.md:38 | - `--reps` = kills per point (8 first; then 20: rerun with `--reps 20 --tag L20`). `--lease 20` is the TEST lease so recovery fits inside a run; the design lease is 120 s (flows in n8n-flows/ are buil |
| n8n-flows | live-doc | handover/demo/RUN-ON-LAPTOP.md:46 | - `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step). |
| n8n-flows | whole fa/ tree | 471 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-film | live-doc | none found | |
| n8n-flows-film | whole fa/ tree | 134 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-film-v3 | live-doc | none found | |
| n8n-flows-film-v3 | whole fa/ tree | 247 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-film-v4 | live-doc | none found | |
| n8n-flows-film-v4 | whole fa/ tree | 264 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-film-v5 | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:1 | # Flows v5 (WP4: CRM id). BUILT, NOT RUN. Folders: n8n-flows-real-v5 and n8n-flows-film-v5 (v3 and v4 folders untouched). |
| n8n-flows-film-v5 | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:9 | film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 |
| n8n-flows-film-v5 | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:1 | # Flows v5 (WP4: CRM id). BUILT, NOT RUN. Folders: n8n-flows-real-v5 and n8n-flows-film-v5 (v3 and v4 folders untouched). |
| n8n-flows-film-v5 | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:9 | film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 |
| n8n-flows-film-v5 | whole fa/ tree | 316 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-real | live-doc | none found | |
| n8n-flows-real | whole fa/ tree | 120 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-real-v3 | live-doc | none found | |
| n8n-flows-real-v3 | whole fa/ tree | 247 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-real-v4 | live-doc | none found | |
| n8n-flows-real-v4 | whole fa/ tree | 263 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-real-v5 | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:1 | # Flows v5 (WP4: CRM id). BUILT, NOT RUN. Folders: n8n-flows-real-v5 and n8n-flows-film-v5 (v3 and v4 folders untouched). |
| n8n-flows-real-v5 | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:8 | real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER |
| n8n-flows-real-v5 | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:1 | # Flows v5 (WP4: CRM id). BUILT, NOT RUN. Folders: n8n-flows-real-v5 and n8n-flows-film-v5 (v3 and v4 folders untouched). |
| n8n-flows-real-v5 | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:8 | real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER |
| n8n-flows-real-v5 | whole fa/ tree | 797 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-v3 | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| n8n-flows-v3 | whole fa/ tree | 306 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows-v4 | live-doc | none found | |
| n8n-flows-v4 | whole fa/ tree | 340 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/N8N-START | live-doc | handover/demo/VIDEO-RUNSHEET.md:8 | Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, section 7), N8N-START, DESIGN-A-README, the table screen README, RUN-ON-LAPTOP and |
| n8n-flows/N8N-START | whole fa/ tree | 107 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/N8N-START.md | live-doc | none found | |
| n8n-flows/N8N-START.md | whole fa/ tree | 97 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/PAGE-STATEMENTS-DRAFT | live-doc | handover/demo/VIDEO-RUNSHEET.md:8 | Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, section 7), N8N-START, DESIGN-A-README, the table screen README, RUN-ON-LAPTOP and |
| n8n-flows/PAGE-STATEMENTS-DRAFT | whole fa/ tree | 21 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/PAGE-STATEMENTS-DRAFT.md | live-doc | none found | |
| n8n-flows/PAGE-STATEMENTS-DRAFT.md | whole fa/ tree | 16 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/desk-form-door | live-doc | none found | |
| n8n-flows/desk-form-door | whole fa/ tree | 51 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/desk-form-door.json | live-doc | none found | |
| n8n-flows/desk-form-door.json | whole fa/ tree | 49 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/mf_leads | live-doc | handover/demo/RUN-ON-LAPTOP.md:46 | - `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step). |
| n8n-flows/mf_leads | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| n8n-flows/mf_leads | whole fa/ tree | 972 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/mf_leads.sql | live-doc | handover/demo/RUN-ON-LAPTOP.md:46 | - `n8n-flows/`: the flows as pushed, `mf_leads.sql`, `DESIGN-A-README.md` (flow step by step). |
| n8n-flows/mf_leads.sql | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| n8n-flows/mf_leads.sql | whole fa/ tree | 137 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-flows/v1-superseded | live-doc | none found | |
| n8n-flows/v1-superseded | whole fa/ tree | 127 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-kill-between-steps | live-doc | none found | |
| n8n-kill-between-steps | whole fa/ tree | 10 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-kill-between-steps.md | live-doc | none found | |
| n8n-kill-between-steps.md | whole fa/ tree | 10 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/build_mainframe_v1 | live-doc | none found | |
| n8n-mainframe/build_mainframe_v1 | whole fa/ tree | 16 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/build_mainframe_v1.py | live-doc | none found | |
| n8n-mainframe/build_mainframe_v1.py | whole fa/ tree | 16 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/examples | live-doc | handover/demo/RUN-ON-LAPTOP.md:51 | - Native Postgres instead: put a program called `docker` first on PATH that maps the same commands onto a native Postgres 16 on port 55432. My version is `n8n-mainframe/examples/docker-native-pg-shim. |
| n8n-mainframe/examples | whole fa/ tree | 122 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/examples/docker-native-pg-shim.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:51 | - Native Postgres instead: put a program called `docker` first on PATH that maps the same commands onto a native Postgres 16 on port 55432. My version is `n8n-mainframe/examples/docker-native-pg-shim. |
| n8n-mainframe/examples/docker-native-pg-shim.py | whole fa/ tree | 11 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/mf | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| n8n-mainframe/mf | live-doc | handover/demo/RUN-ON-LAPTOP.md:47 | - What needs docker: only Postgres, in five places: run_mf.py (`docker ps/pull/run/exec/rm`), mf.py (`docker exec <name> psql ...`, `pg_isready`, and `docker kill` / `docker start` for the Postgres ki |
| n8n-mainframe/mf | live-doc | handover/demo/RUN-ON-LAPTOP.md:54 | ## 7. Counting rule (outside the flow, in mf.py) |
| n8n-mainframe/mf | live-doc | handover/demo/RUN-ON-LAPTOP.md:61 | ## 8. Pass criteria per test (what mf.py writes as PASS; read the `why` line, not only the word) |
| n8n-mainframe/mf | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| n8n-mainframe/mf | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| n8n-mainframe/mf | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| n8n-mainframe/mf | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| n8n-mainframe/mf | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| n8n-mainframe/mf | whole fa/ tree | 170 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-mainframe/mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| n8n-mainframe/mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:47 | - What needs docker: only Postgres, in five places: run_mf.py (`docker ps/pull/run/exec/rm`), mf.py (`docker exec <name> psql ...`, `pg_isready`, and `docker kill` / `docker start` for the Postgres ki |
| n8n-mainframe/mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:54 | ## 7. Counting rule (outside the flow, in mf.py) |
| n8n-mainframe/mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:61 | ## 8. Pass criteria per test (what mf.py writes as PASS; read the `why` line, not only the word) |
| n8n-mainframe/mf.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:82 | - Flows: n8n-flows-v3 (or film-v3 / real-v3), table n8n-flows-v3/mf_leads.sql; mf.py creates the table itself with the four alert columns. New test AF1 (`--tests AF1`, about 10 minutes at lease 20). s |
| n8n-mainframe/mf.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| n8n-mainframe/mf.py | live-doc | handover/demo/n8n-flows-film-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| n8n-mainframe/mf.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:15 | - py_compile of build_mainframe.py, crm_stub.py, mf.py: ok. |
| n8n-mainframe/mf.py | live-doc | handover/demo/n8n-flows-real-v5/V5-README.md:20 | - mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these |
| n8n-mainframe/mf.py | whole fa/ tree | 157 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-owns-vs-desk-owns | live-doc | none found | |
| n8n-owns-vs-desk-owns | whole fa/ tree | 29 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-owns-vs-desk-owns.md | live-doc | none found | |
| n8n-owns-vs-desk-owns.md | whole fa/ tree | 29 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-published-numbers | live-doc | none found | |
| n8n-published-numbers | whole fa/ tree | 18 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-published-numbers.md | live-doc | none found | |
| n8n-published-numbers.md | whole fa/ tree | 16 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-rerun | live-doc | none found | |
| n8n-rerun | whole fa/ tree | 53 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-skip-on-conflict | live-doc | none found | |
| n8n-skip-on-conflict | whole fa/ tree | 15 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-skip-on-conflict.md | live-doc | none found | |
| n8n-skip-on-conflict.md | whole fa/ tree | 15 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen | live-doc | none found | |
| n8n-table-screen | whole fa/ tree | 54 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen-v2 | live-doc | handover/demo/VIDEO-RUNSHEET.md:88 | - Table screen: v2 is built (n8n-table-screen-v2, preview images in the folder), NOT run in n8n; the laptop agent re-shoots. |
| n8n-table-screen-v2 | whole fa/ tree | 82 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen-v2/README | live-doc | handover/demo/VIDEO-RUNSHEET.md:8 | Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, section 7), N8N-START, DESIGN-A-README, the table screen README, RUN-ON-LAPTOP and |
| n8n-table-screen-v2/README | whole fa/ tree | 1816 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen-v2/README.md | live-doc | none found | |
| n8n-table-screen-v2/README.md | whole fa/ tree | 1054 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen/README | live-doc | handover/demo/VIDEO-RUNSHEET.md:8 | Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, section 7), N8N-START, DESIGN-A-README, the table screen README, RUN-ON-LAPTOP and |
| n8n-table-screen/README | whole fa/ tree | 1816 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-table-screen/README.md | live-doc | none found | |
| n8n-table-screen/README.md | whole fa/ tree | 1054 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-tests/dn1_common | live-doc | handover/demo/RUN-ON-LAPTOP.md:45 | - `n8n-tests/`: `dn1_common.py` (shared helpers, ports, process control, the exact environment the stage gets), `smtp_catcher.py` (mail stand-in), plus the Design B files (not needed here). |
| n8n-tests/dn1_common | whole fa/ tree | 79 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-tests/dn1_common.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:45 | - `n8n-tests/`: `dn1_common.py` (shared helpers, ports, process control, the exact environment the stage gets), `smtp_catcher.py` (mail stand-in), plus the Design B files (not needed here). |
| n8n-tests/dn1_common.py | whole fa/ tree | 66 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-tests/results | live-doc | none found | |
| n8n-tests/results | whole fa/ tree | 619 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-tests/run_dn1 | live-doc | none found | |
| n8n-tests/run_dn1 | whole fa/ tree | 15 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-tests/run_dn1.py | live-doc | none found | |
| n8n-tests/run_dn1.py | whole fa/ tree | 14 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-vs-desk-kill-compare | live-doc | none found | |
| n8n-vs-desk-kill-compare | whole fa/ tree | 14 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| n8n-vs-desk-kill-compare.md | live-doc | none found | |
| n8n-vs-desk-kill-compare.md | whole fa/ tree | 14 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| py.txt | live-doc | none found | |
| py.txt | whole fa/ tree | 13 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| sandbox-scratch-logs | live-doc | none found | |
| sandbox-scratch-logs | whole fa/ tree | 12 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |
| stage_server.py | live-doc | handover/demo/RUN-ON-LAPTOP.md:44 | - `n8n-mainframe/run_chain.py` (this chain runner), `run_mf.py` (orchestrator: Postgres container, fakes, n8n, setup, then mf.py; stops only what it started), `mf.py` (the tests, the counting), `build |
| stage_server.py | whole fa/ tree | 56 hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |

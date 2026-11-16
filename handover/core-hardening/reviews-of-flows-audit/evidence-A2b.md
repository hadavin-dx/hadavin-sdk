# evidence-A2b (raw facts only; nothing rated)

date UTC: 2026-11-16 07:59:34
script path: /home/user/hadavin-sdk/handover/core-hardening/reviews-of-flows-audit/evidence-A2b-script.py
sha256 of the 8 files (read-only target /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/fa):
- real-v5/mf-hook.json: 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- real-v5/mf-form.json: 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- real-v5/mf-recovery.json: 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759
- real-v5/mf-sub-crm-mail.json: b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36
- film-v5/mf-hook.json: 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de
- film-v5/mf-form.json: 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8
- film-v5/mf-recovery.json: 42d853ac8528c2699a3deac54725d6c4c2672258bf048e6fa88deb3783cb4c79
- film-v5/mf-sub-crm-mail.json: a0215012962e2e22e3923ed9ecb14bae472e0857636b7356f61e87190968918b

# real-v5/mf-hook.json  (workflow name: Lead desk main frame: e-mail-style entry)

## (1) Respond-to-Webhook nodes
- ReplyRan | fed by: ['RunSub:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
  }
- ReplyReview | fed by: ['IsProcessing:main[1]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
  }
- ReplyStored | fed by: ['Stored:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
  }
## (2) Code/Function nodes and IF/Switch conditions
#### Claimed (n8n-nodes-base.if) conditions/parameters:
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
#### IsProcessing (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Claim field=query value-line: INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Receive: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Item: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Valid: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Claim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- Claimed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- IsProcessing: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SubInput: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyRan: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyReview: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Stored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- ReplyStored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=ReplyRan field=responseBody: "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
- node=ReplyReview field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
- node=ReplyStored field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
## (8) Webhook nodes
- Receive: path=mf-hook httpMethod=POST authentication=(not set) responseMode=responseNode webhookId=present
  options: {}
  full parameters: {
   "httpMethod": "POST",
   "options": {},
   "path": "mf-hook",
   "responseMode": "responseNode"
  }
## (9) Appendix: full parameters JSON of every node (masked)
#### Receive (n8n-nodes-base.webhook v2)
{
 "httpMethod": "POST",
 "options": {},
 "path": "mf-hook",
 "responseMode": "responseNode"
}
#### Item (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.body.message_id }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.body.from_email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.body.from_name }}"
   }
  ]
 },
 "options": {}
}
#### Valid (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.name }}"
   },
   {
    "id": "valid",
    "name": "valid",
    "type": "boolean",
    "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}"
   }
  ]
 },
 "options": {}
}
#### Claim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
#### Claimed (n8n-nodes-base.if v2.2)
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
#### IsProcessing (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
#### SubInput (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "claim_token",
    "name": "claim_token",
    "type": "string",
    "value": "={{ $json.claim_token }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $('Valid').item.json.email }}"
   }
  ]
 },
 "options": {}
}
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### ReplyRan (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
}
#### ReplyReview (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
}
#### Stored (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
 },
 "query": "SELECT state FROM mf_leads WHERE lead_key=$1;"
}
#### ReplyStored (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
}

# real-v5/mf-form.json  (workflow name: Lead desk main frame: form entry)

## (1) Respond-to-Webhook nodes
- ReplyRan | fed by: ['RunSub:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
  }
- ReplyReview | fed by: ['IsProcessing:main[1]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
  }
- ReplyStored | fed by: ['Stored:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
  }
## (2) Code/Function nodes and IF/Switch conditions
#### Claimed (n8n-nodes-base.if) conditions/parameters:
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
#### IsProcessing (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Claim field=query value-line: INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Receive: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Item: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Valid: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Claim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- Claimed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- IsProcessing: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SubInput: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyRan: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyReview: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Stored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- ReplyStored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=ReplyRan field=responseBody: "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
- node=ReplyReview field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
- node=ReplyStored field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
## (8) Webhook nodes
- Receive: path=mf-form httpMethod=POST authentication=(not set) responseMode=responseNode webhookId=present
  options: {}
  full parameters: {
   "httpMethod": "POST",
   "options": {},
   "path": "mf-form",
   "responseMode": "responseNode"
  }
## (9) Appendix: full parameters JSON of every node (masked)
#### Receive (n8n-nodes-base.webhook v2)
{
 "httpMethod": "POST",
 "options": {},
 "path": "mf-form",
 "responseMode": "responseNode"
}
#### Item (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.body.submission_id }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.body.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.body.name }}"
   }
  ]
 },
 "options": {}
}
#### Valid (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.name }}"
   },
   {
    "id": "valid",
    "name": "valid",
    "type": "boolean",
    "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}"
   }
  ]
 },
 "options": {}
}
#### Claim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
#### Claimed (n8n-nodes-base.if v2.2)
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
#### IsProcessing (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
#### SubInput (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "claim_token",
    "name": "claim_token",
    "type": "string",
    "value": "={{ $json.claim_token }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $('Valid').item.json.email }}"
   }
  ]
 },
 "options": {}
}
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### ReplyRan (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
}
#### ReplyReview (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
}
#### Stored (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
 },
 "query": "SELECT state FROM mf_leads WHERE lead_key=$1;"
}
#### ReplyStored (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
}

# real-v5/mf-recovery.json  (workflow name: Lead desk main frame: recovery (every 30 s))

## (1) Respond-to-Webhook nodes
## (2) Code/Function nodes and IF/Switch conditions
#### StuckRow (n8n-nodes-base.if) conditions/parameters:
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
#### AlertRow (n8n-nodes-base.if) conditions/parameters:
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
## (3) Schedule/cron/interval triggers
- Every30s (n8n-nodes-base.scheduleTrigger): {"rule": {"interval": [{"field": "seconds", "secondsInterval": 30}]}}
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Every30s field=rule.interval[0].field value-line: seconds
- node=Every30s field=rule.interval[0].secondsInterval value-line: 30
- node=ClaimStuck field=query value-line: UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;
- node=AlertClaim field=query value-line: UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;
- node=AlertBackoff field=query value-line: UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Every30s: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ClaimStuck: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- StuckRow: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueRegularOutput
- MarkFailed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertClaim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertRow: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- AlertSend: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- AlertBackoff: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertMark: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=AlertClaim field=operation: 'executeQuery'
- node=AlertClaim field=query: "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
- node=AlertRow field=conditions.options.typeValidation: 'loose'
- node=AlertRow field=conditions.conditions[0].leftValue: '={{ $json.lead_key }}'
- node=AlertRow field=conditions.conditions[0].operator.type: 'string'
- node=AlertRow field=conditions.conditions[0].operator.operation: 'notEmpty'
- node=AlertSend field=fromEmail: 'FROM_ADDRESS_PLACEHOLDER'
- node=AlertSend field=toEmail: '={{ $env.DESK_ALERT_TO }}'
- node=AlertSend field=subject: "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}"
- node=AlertSend field=emailFormat: 'text'
- node=AlertSend field=text: "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}"
- node=AlertBackoff field=operation: 'executeQuery'
- node=AlertBackoff field=query: "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
- node=AlertBackoff field=options.queryReplacement: "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
- node=AlertMark field=operation: 'executeQuery'
- node=AlertMark field=query: 'UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;'
- node=AlertMark field=options.queryReplacement: "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
## (8) Webhook nodes
## (9) Appendix: full parameters JSON of every node (masked)
#### Every30s (n8n-nodes-base.scheduleTrigger v1.2)
{
 "rule": {
  "interval": [
   {
    "field": "seconds",
    "secondsInterval": 30
   }
  ]
 }
}
#### ClaimStuck (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;"
}
#### StuckRow (n8n-nodes-base.if v2.2)
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
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### MarkFailed (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;"
}
#### AlertClaim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertRow (n8n-nodes-base.if v2.2)
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
#### AlertSend (n8n-nodes-base.emailSend v2.1)
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
#### AlertBackoff (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}

# real-v5/mf-sub-crm-mail.json  (workflow name: Lead desk main frame: CRM + mail (sub-workflow))

## (1) Respond-to-Webhook nodes
## (2) Code/Function nodes and IF/Switch conditions
#### LabelOk (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### CrmIdOk (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### OwnsClaim1 (n8n-nodes-base.if) conditions/parameters:
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
#### MailRowBack (n8n-nodes-base.if) conditions/parameters:
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
#### UnknownNewA (n8n-nodes-base.if) conditions/parameters:
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
#### UnknownNew (n8n-nodes-base.if) conditions/parameters:
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
#### DoneOwned (n8n-nodes-base.if) conditions/parameters:
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Qualify field(node-level)=retryOnFail value=True
- node=Qualify field(node-level)=maxTries value=2
- node=Qualify field(node-level)=waitBetweenTries value=1000
- node=CrmUpsert field(node-level)=retryOnFail value=True
- node=CrmUpsert field(node-level)=maxTries value=2
- node=CrmUpsert field(node-level)=waitBetweenTries value=1000
- node=SendMail field(node-level)=retryOnFail value=False
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- SubIn: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Qualify: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- LabelOk: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- CrmUpsert: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- SetCrmId: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- CrmIdOk: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OwnsClaim1: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- MailClaim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MailRowBack: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SendMail: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- MarkDone: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MarkUnknownA: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MarkUnknownB: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- UnknownNewA: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- UnknownNew: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- DoneOwned: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutDone: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutUnknown: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutStage: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutLost: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=Qualify field=specifyBody: 'json'
- node=Qualify field=jsonBody: "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}"
- node=MailClaim field=operation: 'executeQuery'
- node=MailClaim field=query: "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
- node=MailClaim field=options.queryReplacement: "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
- node=MailRowBack field=conditions.options.typeValidation: 'loose'
- node=MailRowBack field=conditions.conditions[0].leftValue: '={{ $json.lead_key }}'
- node=MailRowBack field=conditions.conditions[0].operator.type: 'string'
- node=MailRowBack field=conditions.conditions[0].operator.operation: 'notEmpty'
- node=SendMail field=fromEmail: 'FROM_ADDRESS_PLACEHOLDER'
- node=SendMail field=toEmail: 'INTAKE_ADDRESS_PLACEHOLDER'
- node=SendMail field=subject: "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}"
- node=SendMail field=emailFormat: 'text'
- node=SendMail field=text: 'made-up thank-you text'
## (8) Webhook nodes
## (9) Appendix: full parameters JSON of every node (masked)
#### SubIn (n8n-nodes-base.executeWorkflowTrigger v1.1)
{
 "inputSource": "passthrough"
}
#### Qualify (n8n-nodes-base.httpRequest v4.2)
{
 "contentType": "json",
 "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}",
 "method": "POST",
 "options": {
  "timeout": "={{ Number($env.DESK_TIMEOUT_MS || 10000) }}"
 },
 "sendBody": true,
 "specifyBody": "json",
 "url": "={{ $env.DESK_URL }}/qualify"
}
#### LabelOk (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### CrmUpsert (n8n-nodes-base.hubspot v2.2)
{
 "additionalFields": {
  "customPropertiesUi": {
   "customPropertiesValues": [
    {
     "property": "hadavin_lead_id",
     "value": "={{ $('SubIn').first().json.lead_key }}"
    },
    {
     "property": "hadavin_label",
     "value": "={{ $('Qualify').first().json.label }}"
    }
   ]
  }
 },
 "authentication": "appToken",
 "email": "={{ $('SubIn').first().json.email }}",
 "operation": "upsert",
 "options": {},
 "resource": "contact"
}
#### SetCrmId (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;"
}
#### CrmIdOk (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### OwnsClaim1 (n8n-nodes-base.if v2.2)
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
#### MailClaim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MailRowBack (n8n-nodes-base.if v2.2)
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
#### SendMail (n8n-nodes-base.emailSend v2.1)
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
#### MarkDone (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownA (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownB (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;"
}
#### UnknownNewA (n8n-nodes-base.if v2.2)
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
#### UnknownNew (n8n-nodes-base.if v2.2)
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
#### DoneOwned (n8n-nodes-base.if v2.2)
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
#### OutDone (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "done"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutUnknown (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "unknown"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutStage (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "stage_failed"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutLost (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "lost_claim"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}

# film-v5/mf-hook.json  (workflow name: Lead desk main frame: e-mail-style entry)

## (1) Respond-to-Webhook nodes
- ReplyRan | fed by: ['RunSub:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
  }
- ReplyReview | fed by: ['IsProcessing:main[1]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
  }
- ReplyStored | fed by: ['Stored:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
  }
## (2) Code/Function nodes and IF/Switch conditions
#### Claimed (n8n-nodes-base.if) conditions/parameters:
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
#### IsProcessing (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Claim field=query value-line: INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Receive: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Item: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Valid: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Claim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- Claimed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- IsProcessing: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SubInput: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyRan: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyReview: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Stored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- ReplyStored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=ReplyRan field=responseBody: "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
- node=ReplyReview field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
- node=ReplyStored field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
## (8) Webhook nodes
- Receive: path=mf-hook httpMethod=POST authentication=(not set) responseMode=responseNode webhookId=present
  options: {}
  full parameters: {
   "httpMethod": "POST",
   "options": {},
   "path": "mf-hook",
   "responseMode": "responseNode"
  }
## (9) Appendix: full parameters JSON of every node (masked)
#### Receive (n8n-nodes-base.webhook v2)
{
 "httpMethod": "POST",
 "options": {},
 "path": "mf-hook",
 "responseMode": "responseNode"
}
#### Item (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.body.message_id }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.body.from_email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.body.from_name }}"
   }
  ]
 },
 "options": {}
}
#### Valid (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.name }}"
   },
   {
    "id": "valid",
    "name": "valid",
    "type": "boolean",
    "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}"
   }
  ]
 },
 "options": {}
}
#### Claim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
#### Claimed (n8n-nodes-base.if v2.2)
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
#### IsProcessing (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
#### SubInput (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "claim_token",
    "name": "claim_token",
    "type": "string",
    "value": "={{ $json.claim_token }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $('Valid').item.json.email }}"
   }
  ]
 },
 "options": {}
}
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### ReplyRan (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
}
#### ReplyReview (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
}
#### Stored (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
 },
 "query": "SELECT state FROM mf_leads WHERE lead_key=$1;"
}
#### ReplyStored (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
}

# film-v5/mf-form.json  (workflow name: Lead desk main frame: form entry)

## (1) Respond-to-Webhook nodes
- ReplyRan | fed by: ['RunSub:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
  }
- ReplyReview | fed by: ['IsProcessing:main[1]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
  }
- ReplyStored | fed by: ['Stored:main[0]']
  responseCode: 200
  parameters (masked): {
   "options": {
    "responseCode": 200
   },
   "respondWith": "json",
   "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
  }
## (2) Code/Function nodes and IF/Switch conditions
#### Claimed (n8n-nodes-base.if) conditions/parameters:
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
#### IsProcessing (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Claim field=query value-line: INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Receive: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Item: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Valid: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Claim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- Claimed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- IsProcessing: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SubInput: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyRan: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ReplyReview: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Stored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- ReplyStored: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=ReplyRan field=responseBody: "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
- node=ReplyReview field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
- node=ReplyStored field=responseBody: "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
## (8) Webhook nodes
- Receive: path=mf-form httpMethod=POST authentication=(not set) responseMode=responseNode webhookId=present
  options: {}
  full parameters: {
   "httpMethod": "POST",
   "options": {},
   "path": "mf-form",
   "responseMode": "responseNode"
  }
## (9) Appendix: full parameters JSON of every node (masked)
#### Receive (n8n-nodes-base.webhook v2)
{
 "httpMethod": "POST",
 "options": {},
 "path": "mf-form",
 "responseMode": "responseNode"
}
#### Item (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.body.submission_id }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.body.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.body.name }}"
   }
  ]
 },
 "options": {}
}
#### Valid (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $json.email }}"
   },
   {
    "id": "name",
    "name": "name",
    "type": "string",
    "value": "={{ $json.name }}"
   },
   {
    "id": "valid",
    "name": "valid",
    "type": "boolean",
    "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email) }}"
   }
  ]
 },
 "options": {}
}
#### Claim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
 },
 "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;"
}
#### Claimed (n8n-nodes-base.if v2.2)
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
#### IsProcessing (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ $json.state }}",
    "operator": {
     "operation": "equals",
     "type": "string"
    },
    "rightValue": "processing"
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
#### SubInput (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $json.lead_key }}"
   },
   {
    "id": "claim_token",
    "name": "claim_token",
    "type": "string",
    "value": "={{ $json.claim_token }}"
   },
   {
    "id": "email",
    "name": "email",
    "type": "string",
    "value": "={{ $('Valid').item.json.email }}"
   }
  ]
 },
 "options": {}
}
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### ReplyRan (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}"
}
#### ReplyReview (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}"
}
#### Stored (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
 },
 "query": "SELECT state FROM mf_leads WHERE lead_key=$1;"
}
#### ReplyStored (n8n-nodes-base.respondToWebhook v1.4)
{
 "options": {
  "responseCode": 200
 },
 "respondWith": "json",
 "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}"
}

# film-v5/mf-recovery.json  (workflow name: Lead desk main frame: recovery (every 30 s))

## (1) Respond-to-Webhook nodes
## (2) Code/Function nodes and IF/Switch conditions
#### StuckRow (n8n-nodes-base.if) conditions/parameters:
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
#### AlertRow (n8n-nodes-base.if) conditions/parameters:
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
## (3) Schedule/cron/interval triggers
- Every30s (n8n-nodes-base.scheduleTrigger): {"rule": {"interval": [{"field": "seconds", "secondsInterval": 30}]}}
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Every30s field=rule.interval[0].field value-line: seconds
- node=Every30s field=rule.interval[0].secondsInterval value-line: 30
- node=ClaimStuck field=query value-line: UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;
- node=AlertClaim field=query value-line: UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;
- node=AlertBackoff field=query value-line: UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- Every30s: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- ClaimStuck: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- StuckRow: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- RunSub: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueRegularOutput
- MarkFailed: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertClaim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertRow: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- AlertSend: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- AlertBackoff: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
- AlertMark: disabled=(absent) continueOnFail=(absent) alwaysOutputData=False onError=continueRegularOutput
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=AlertClaim field=operation: 'executeQuery'
- node=AlertClaim field=query: "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
- node=AlertRow field=conditions.options.typeValidation: 'loose'
- node=AlertRow field=conditions.conditions[0].leftValue: '={{ $json.lead_key }}'
- node=AlertRow field=conditions.conditions[0].operator.type: 'string'
- node=AlertRow field=conditions.conditions[0].operator.operation: 'notEmpty'
- node=AlertSend field=fromEmail: '[MASKED]'
- node=AlertSend field=toEmail: '[MASKED]'
- node=AlertSend field=subject: "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}"
- node=AlertSend field=emailFormat: 'text'
- node=AlertSend field=text: "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}"
- node=AlertBackoff field=operation: 'executeQuery'
- node=AlertBackoff field=query: "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
- node=AlertBackoff field=options.queryReplacement: "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
- node=AlertMark field=operation: 'executeQuery'
- node=AlertMark field=query: 'UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;'
- node=AlertMark field=options.queryReplacement: "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
## (8) Webhook nodes
## (9) Appendix: full parameters JSON of every node (masked)
#### Every30s (n8n-nodes-base.scheduleTrigger v1.2)
{
 "rule": {
  "interval": [
   {
    "field": "seconds",
    "secondsInterval": 30
   }
  ]
 }
}
#### ClaimStuck (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;"
}
#### StuckRow (n8n-nodes-base.if v2.2)
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
#### RunSub (n8n-nodes-base.executeWorkflow v1.2)
{
 "mode": "each",
 "options": {
  "waitForSubWorkflow": true
 },
 "source": "database",
 "workflowId": {
  "__rl": true,
  "mode": "id",
  "value": "SUB_WORKFLOW_ID"
 }
}
#### MarkFailed (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;"
}
#### AlertClaim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {},
 "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;"
}
#### AlertRow (n8n-nodes-base.if v2.2)
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
#### AlertSend (n8n-nodes-base.emailSend v2.1)
{
 "emailFormat": "text",
 "fromEmail": "[MASKED]",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
 "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
 "toEmail": "[MASKED]"
}
#### AlertBackoff (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}
#### AlertMark (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
 },
 "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;"
}

# film-v5/mf-sub-crm-mail.json  (workflow name: Lead desk main frame: CRM + mail (sub-workflow))

## (1) Respond-to-Webhook nodes
## (2) Code/Function nodes and IF/Switch conditions
#### LabelOk (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### CrmIdOk (n8n-nodes-base.if) conditions/parameters:
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### OwnsClaim1 (n8n-nodes-base.if) conditions/parameters:
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
#### MailRowBack (n8n-nodes-base.if) conditions/parameters:
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
#### UnknownNewA (n8n-nodes-base.if) conditions/parameters:
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
#### UnknownNew (n8n-nodes-base.if) conditions/parameters:
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
#### DoneOwned (n8n-nodes-base.if) conditions/parameters:
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
## (3) Schedule/cron/interval triggers
(none by node type)
## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)
- node=Qualify field(node-level)=retryOnFail value=True
- node=Qualify field(node-level)=maxTries value=2
- node=Qualify field(node-level)=waitBetweenTries value=1000
- node=CrmUpsert field(node-level)=retryOnFail value=True
- node=CrmUpsert field(node-level)=maxTries value=2
- node=CrmUpsert field(node-level)=waitBetweenTries value=1000
- node=SendMail field(node-level)=retryOnFail value=False
## (5) Workflow settings (full)
{
 "executionOrder": "v1",
 "saveDataErrorExecution": "none",
 "saveDataSuccessExecution": "none",
 "saveManualExecutions": false
}
other top-level keys: ["name", "nodes", "connections", "settings"]
## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node
- SubIn: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- Qualify: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- LabelOk: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- CrmUpsert: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- SetCrmId: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- CrmIdOk: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OwnsClaim1: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- MailClaim: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MailRowBack: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- SendMail: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=continueErrorOutput
- MarkDone: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MarkUnknownA: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- MarkUnknownB: disabled=(absent) continueOnFail=(absent) alwaysOutputData=True onError=(absent)
- UnknownNewA: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- UnknownNew: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- DoneOwned: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutDone: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutUnknown: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutStage: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
- OutLost: disabled=(absent) continueOnFail=(absent) alwaysOutputData=(absent) onError=(absent)
## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)
- node=Qualify field=specifyBody: 'json'
- node=Qualify field=jsonBody: "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}"
- node=CrmUpsert field=specifyBody: 'json'
- node=CrmUpsert field=jsonBody: "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}"
- node=MailClaim field=operation: 'executeQuery'
- node=MailClaim field=query: "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
- node=MailClaim field=options.queryReplacement: "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
- node=MailRowBack field=conditions.options.typeValidation: 'loose'
- node=MailRowBack field=conditions.conditions[0].leftValue: '={{ $json.lead_key }}'
- node=MailRowBack field=conditions.conditions[0].operator.type: 'string'
- node=MailRowBack field=conditions.conditions[0].operator.operation: 'notEmpty'
- node=SendMail field=fromEmail: '[MASKED]'
- node=SendMail field=toEmail: '[MASKED]'
- node=SendMail field=subject: "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}"
- node=SendMail field=emailFormat: 'text'
- node=SendMail field=text: 'made-up thank-you text'
## (8) Webhook nodes
## (9) Appendix: full parameters JSON of every node (masked)
#### SubIn (n8n-nodes-base.executeWorkflowTrigger v1.1)
{
 "inputSource": "passthrough"
}
#### Qualify (n8n-nodes-base.httpRequest v4.2)
{
 "contentType": "json",
 "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}",
 "method": "POST",
 "options": {
  "timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || 10000) }}"
 },
 "sendBody": true,
 "specifyBody": "json",
 "url": "={{ $env.MF_STAGE_URL }}/qualify"
}
#### LabelOk (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### CrmUpsert (n8n-nodes-base.httpRequest v4.2)
{
 "contentType": "json",
 "jsonBody": "={{ { hadavin_lead_id: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}",
 "method": "POST",
 "options": {
  "timeout": 10000
 },
 "sendBody": true,
 "specifyBody": "json",
 "url": "={{ $env.MF_CRM_URL }}/upsert"
}
#### SetCrmId (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;"
}
#### CrmIdOk (n8n-nodes-base.if v2.2)
{
 "conditions": {
  "combinator": "and",
  "conditions": [
   {
    "id": "c1",
    "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
    "operator": {
     "operation": "true",
     "singleValue": true,
     "type": "boolean"
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
#### OwnsClaim1 (n8n-nodes-base.if v2.2)
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
#### MailClaim (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;"
}
#### MailRowBack (n8n-nodes-base.if v2.2)
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
#### SendMail (n8n-nodes-base.emailSend v2.1)
{
 "emailFormat": "text",
 "fromEmail": "[MASKED]",
 "options": {
  "appendAttribution": false
 },
 "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}",
 "text": "made-up thank-you text",
 "toEmail": "[MASKED]"
}
#### MarkDone (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownA (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;"
}
#### MarkUnknownB (n8n-nodes-base.postgres v2.5)
{
 "operation": "executeQuery",
 "options": {
  "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
 },
 "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;"
}
#### UnknownNewA (n8n-nodes-base.if v2.2)
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
#### UnknownNew (n8n-nodes-base.if v2.2)
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
#### DoneOwned (n8n-nodes-base.if v2.2)
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
#### OutDone (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "done"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutUnknown (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "unknown"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutStage (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "stage_failed"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}
#### OutLost (n8n-nodes-base.set v3.4)
{
 "assignments": {
  "assignments": [
   {
    "id": "outcome",
    "name": "outcome",
    "type": "string",
    "value": "lost_claim"
   },
   {
    "id": "lead_key",
    "name": "lead_key",
    "type": "string",
    "value": "={{ $('SubIn').first().json.lead_key }}"
   }
  ]
 },
 "options": {}
}


# Evidence v10 primary (raw)
Branch head: 9b0a38e2f27418e1bd5db37cfb81d14c301d5c7a
Fetched: 2026-11-16T11:15:23Z
sha256 74a823d4bc99d4bed9a9a523cdea8f4be84aa0de8202e06023c22a702f5058a8  handover/demo/n8n-flows-real-v5/mf-form.json  lines=427
sha256 305fbbf51279fae303d72f24d4addc15d549975004b6c303db03ff00636544de  handover/demo/n8n-flows-real-v5/mf-hook.json  lines=427
sha256 03c566bba549524b7bed0e787fdd46c4a01653450ef97691d14f4614357b0759  handover/demo/n8n-flows-real-v5/mf-recovery.json  lines=340
sha256 b3277363ae04b365459d902e5b5be099f1957126e3d48dbe42c47332cf53ff36  handover/demo/n8n-flows-real-v5/mf-sub-crm-mail.json  lines=812
sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0  handover/demo/n8n-flows-v4/mf_leads.sql  lines=20
sha256 91617691d2c6e0e9542df1381ff0c68df80244412a061b21587108c2093f32c0  handover/demo/n8n-flows-v3/mf_leads.sql  lines=20
sha256 7a18c922a1228d0f7517322cf00fd4be282d164cdaad2ce831ad33e7f92aa6ee  handover/demo/n8n-flows/mf_leads.sql  lines=14

=== grep mf-form.json
2: "name": "Lead desk main frame: form entry",
11:   "name": "Receive",
25:       "id": "lead_key",
26:       "name": "lead_key",
32:       "name": "email",
38:       "name": "name",
46:   "name": "Item",
59:       "id": "lead_key",
60:       "name": "lead_key",
61:       "value": "={{ $json.lead_key }}",
66:       "name": "email",
72:       "name": "name",
78:       "name": "valid",
86:   "name": "Valid",
96:    "operation": "executeQuery",
97:    "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
99:     "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
102:   "name": "Claim",
112:     "name": "n8n-publish-pg"
119:    "conditions": {
122:      "leftValue": "",
125:     "conditions": [
128:       "leftValue": "={{ $json.lead_key }}",
129:       "rightValue": null,
132:        "operation": "notEmpty",
141:   "name": "Claimed",
151:    "conditions": {
154:      "leftValue": "",
157:     "conditions": [
160:       "leftValue": "={{ $json.state }}",
161:       "rightValue": "processing",
164:        "operation": "equals"
172:   "name": "IsProcessing",
185:       "id": "lead_key",
186:       "name": "lead_key",
187:       "value": "={{ $json.lead_key }}",
192:       "name": "claim_token",
198:       "name": "email",
206:   "name": "SubInput",
227:   "name": "RunSub",
238:    "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}",
243:   "name": "ReplyRan",
254:    "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}",
259:   "name": "ReplyReview",
269:    "operation": "executeQuery",
270:    "query": "SELECT state FROM mf_leads WHERE lead_key=$1;",
272:     "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
275:   "name": "Stored",
285:     "name": "n8n-publish-pg"
293:    "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}",
298:   "name": "ReplyStored",

=== grep mf-hook.json
2: "name": "Lead desk main frame: e-mail-style entry",
11:   "name": "Receive",
25:       "id": "lead_key",
26:       "name": "lead_key",
32:       "name": "email",
38:       "name": "name",
46:   "name": "Item",
59:       "id": "lead_key",
60:       "name": "lead_key",
61:       "value": "={{ $json.lead_key }}",
66:       "name": "email",
72:       "name": "name",
78:       "name": "valid",
86:   "name": "Valid",
96:    "operation": "executeQuery",
97:    "query": "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '45 seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;",
99:     "queryReplacement": "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}"
102:   "name": "Claim",
112:     "name": "n8n-publish-pg"
119:    "conditions": {
122:      "leftValue": "",
125:     "conditions": [
128:       "leftValue": "={{ $json.lead_key }}",
129:       "rightValue": null,
132:        "operation": "notEmpty",
141:   "name": "Claimed",
151:    "conditions": {
154:      "leftValue": "",
157:     "conditions": [
160:       "leftValue": "={{ $json.state }}",
161:       "rightValue": "processing",
164:        "operation": "equals"
172:   "name": "IsProcessing",
185:       "id": "lead_key",
186:       "name": "lead_key",
187:       "value": "={{ $json.lead_key }}",
192:       "name": "claim_token",
198:       "name": "email",
206:   "name": "SubInput",
227:   "name": "RunSub",
238:    "responseBody": "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: { done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing' } }}",
243:   "name": "ReplyRan",
254:    "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}",
259:   "name": "ReplyReview",
269:    "operation": "executeQuery",
270:    "query": "SELECT state FROM mf_leads WHERE lead_key=$1;",
272:     "queryReplacement": "={{ [$('Valid').item.json.lead_key] }}"
275:   "name": "Stored",
285:     "name": "n8n-publish-pg"
293:    "responseBody": "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}",
298:   "name": "ReplyStored",

=== grep mf-recovery.json
2: "name": "Lead desk main frame: recovery (every 30 s)",
7:     "interval": [
9:       "field": "seconds",
10:       "secondsInterval": 30
15:   "name": "Every30s",
25:    "operation": "executeQuery",
26:    "query": "UPDATE mf_leads SET claimed_until=now() + interval '45 seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, email, claim_token;",
29:   "name": "ClaimStuck",
39:     "name": "n8n-publish-pg"
47:    "conditions": {
50:      "leftValue": "",
53:     "conditions": [
56:       "leftValue": "={{ $json.lead_key }}",
57:       "rightValue": null,
60:        "operation": "notEmpty",
69:   "name": "StuckRow",
90:   "name": "RunSub",
101:    "operation": "executeQuery",
102:    "query": "UPDATE mf_leads SET state=CASE WHEN mail_sent THEN 'unknown' ELSE 'failed' END, updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;",
105:   "name": "MarkFailed",
115:     "name": "n8n-publish-pg"
123:    "operation": "executeQuery",
124:    "query": "UPDATE mf_leads SET alert_until=now() + interval '720 seconds', alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key, state, alert_token;",
127:   "name": "AlertClaim",
137:     "name": "n8n-publish-pg"
145:    "conditions": {
148:      "leftValue": "",
151:     "conditions": [
154:       "leftValue": "={{ $json.lead_key }}",
155:       "rightValue": null,
158:        "operation": "notEmpty",
167:   "name": "AlertRow",
179:    "subject": "={{ $json.state === 'unknown' ? '[demo] Lead desk: mail outcome unknown for ' + $json.lead_key : '[demo] Lead desk: lead failed ' + $json.lead_key }}",
181:    "text": "={{ $json.state === 'unknown' ? 'Lead id ' + $json.lead_key + ': the mail may or may not have been sent. A person decides.' : 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}",
186:   "name": "AlertSend",
196:     "name": "mf-mail-smtp"
203:    "operation": "executeQuery",
204:    "query": "UPDATE mf_leads SET alert_until=now() + interval '60 seconds' * LEAST(alert_attempts, 5) WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
206:     "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
209:   "name": "AlertBackoff",
219:     "name": "n8n-publish-pg"
227:    "operation": "executeQuery",
228:    "query": "UPDATE mf_leads SET alert_sent=true, updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key;",
230:     "queryReplacement": "={{ [$('AlertRow').item.json.lead_key, $('AlertRow').item.json.alert_token] }}"
233:   "name": "AlertMark",
243:     "name": "n8n-publish-pg"
255:      "node": "MarkFailed",

=== grep mf-sub-crm-mail.json
2: "name": "Lead desk main frame: CRM + mail (sub-workflow)",
8:   "name": "SubIn",
23:    "jsonBody": "={{ { lead_key: $('SubIn').first().json.lead_key, email: $('SubIn').first().json.email } }}",
28:   "name": "Qualify",
42:    "conditions": {
45:      "leftValue": "",
48:     "conditions": [
51:       "leftValue": "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}",
52:       "rightValue": null,
55:        "operation": "true",
64:   "name": "LabelOk",
76:    "operation": "upsert",
83:        "value": "={{ $('SubIn').first().json.lead_key }}"
94:   "name": "CrmUpsert",
104:     "name": "hubspot-app-token"
114:    "operation": "executeQuery",
115:    "query": "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;",
117:     "queryReplacement": "={{ [$('SubIn').first().json.lead_key, String($json.id ?? $json.vid ?? ''), $('SubIn').first().json.claim_token] }}"
120:   "name": "SetCrmId",
130:     "name": "n8n-publish-pg"
137:    "conditions": {
140:      "leftValue": "",
143:     "conditions": [
146:       "leftValue": "={{ /^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? '')) }}",
147:       "rightValue": null,
150:        "operation": "true",
159:   "name": "CrmIdOk",
169:    "conditions": {
172:      "leftValue": "",
175:     "conditions": [
178:       "leftValue": "={{ $json.lead_key }}",
179:       "rightValue": null,
182:        "operation": "notEmpty",
191:   "name": "OwnsClaim1",
201:    "operation": "executeQuery",
202:    "query": "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;",
204:     "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
207:   "name": "MailClaim",
217:     "name": "n8n-publish-pg"
224:    "conditions": {
227:      "leftValue": "",
230:     "conditions": [
233:       "leftValue": "={{ $json.lead_key }}",
234:       "rightValue": null,
237:        "operation": "notEmpty",
246:   "name": "MailRowBack",
258:    "subject": "={{ '[demo] lead ' + $('SubIn').first().json.lead_key }}",
265:   "name": "SendMail",
275:     "name": "mf-mail-smtp"
283:    "operation": "executeQuery",
284:    "query": "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;",
286:     "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
289:   "name": "MarkDone",
299:     "name": "n8n-publish-pg"
306:    "operation": "executeQuery",
307:    "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;",
309:     "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
312:   "name": "MarkUnknownA",
322:     "name": "n8n-publish-pg"
329:    "operation": "executeQuery",
330:    "query": "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;",
332:     "queryReplacement": "={{ [$('SubIn').first().json.lead_key, $('SubIn').first().json.claim_token] }}"
335:   "name": "MarkUnknownB",
345:     "name": "n8n-publish-pg"
352:    "conditions": {
355:      "leftValue": "",
358:     "conditions": [
361:       "leftValue": "={{ $json.lead_key }}",
362:       "rightValue": null,
365:        "operation": "notEmpty",
374:   "name": "UnknownNewA",
384:    "conditions": {
387:      "leftValue": "",
390:     "conditions": [
393:       "leftValue": "={{ $json.lead_key }}",
394:       "rightValue": null,
397:        "operation": "notEmpty",
406:   "name": "UnknownNew",
416:    "conditions": {
419:      "leftValue": "",
422:     "conditions": [
425:       "leftValue": "={{ $json.lead_key }}",
426:       "rightValue": null,
429:        "operation": "notEmpty",
438:   "name": "DoneOwned",
452:       "name": "outcome",
457:       "id": "lead_key",
458:       "name": "lead_key",
459:       "value": "={{ $('SubIn').first().json.lead_key }}",
466:   "name": "OutDone",
480:       "name": "outcome",
481:       "value": "unknown",
485:       "id": "lead_key",
486:       "name": "lead_key",
487:       "value": "={{ $('SubIn').first().json.lead_key }}",
494:   "name": "OutUnknown",
508:       "name": "outcome",
509:       "value": "stage_failed",
513:       "id": "lead_key",
514:       "name": "lead_key",
515:       "value": "={{ $('SubIn').first().json.lead_key }}",
522:   "name": "OutStage",
536:       "name": "outcome",
541:       "id": "lead_key",
542:       "name": "lead_key",
543:       "value": "={{ $('SubIn').first().json.lead_key }}",
550:   "name": "OutLost",
694:      "node": "MarkUnknownB",
712:      "node": "MarkUnknownA",
748:  "MarkUnknownA": {
752:      "node": "UnknownNewA",
759:  "UnknownNewA": {
763:      "node": "OutUnknown",
770:      "node": "OutUnknown",
777:  "MarkUnknownB": {
781:      "node": "UnknownNew",
788:  "UnknownNew": {
792:      "node": "OutUnknown",
799:      "node": "OutUnknown",

=== mf_leads.sql v4
     1	-- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
     2	-- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
     3	-- Design A lead table (Postgres). The insert is the claim. Created before the flows run.
     4	CREATE TABLE mf_leads(
     5	  lead_key      text PRIMARY KEY,
     6	  email         text,
     7	  name          text,
     8	  state         text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')),
     9	  claimed_until timestamptz,
    10	  claim_token   text,
    11	  attempts      int  NOT NULL DEFAULT 0,
    12	  crm_id        text,
    13	  mail_sent     boolean NOT NULL DEFAULT false,
    14	  created_at    timestamptz NOT NULL DEFAULT now(),
    15	  updated_at    timestamptz NOT NULL DEFAULT now(),
    16	  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
    17	  alert_sent    boolean NOT NULL DEFAULT false,
    18	  alert_token   text,
    19	  alert_until   timestamptz,
    20	  alert_attempts int NOT NULL DEFAULT 0);

=== mf_leads.sql v3
     1	-- NOTE (v3 table, four alert columns at the end): matches the flows in n8n-flows-v3, n8n-flows-film-v3, n8n-flows-real-v3. The flows in this folder (v2) ignore the extra columns, so this table also runs them.
     2	-- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
     3	-- Design A lead table (Postgres). The insert is the claim. Created before the flows run.
     4	CREATE TABLE mf_leads(
     5	  lead_key      text PRIMARY KEY,
     6	  email         text,
     7	  name          text,
     8	  state         text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')),
     9	  claimed_until timestamptz,
    10	  claim_token   text,
    11	  attempts      int  NOT NULL DEFAULT 0,
    12	  crm_id        text,
    13	  mail_sent     boolean NOT NULL DEFAULT false,
    14	  created_at    timestamptz NOT NULL DEFAULT now(),
    15	  updated_at    timestamptz NOT NULL DEFAULT now(),
    16	  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
    17	  alert_sent    boolean NOT NULL DEFAULT false,
    18	  alert_token   text,
    19	  alert_until   timestamptz,
    20	  alert_attempts int NOT NULL DEFAULT 0);

=== real-v5 dir listing
handover/demo/n8n-flows-real-v5/V5-NODE-DIFF.txt
handover/demo/n8n-flows-real-v5/V5-README.md
handover/demo/n8n-flows-real-v5/mf-form.json
handover/demo/n8n-flows-real-v5/mf-hook.json
handover/demo/n8n-flows-real-v5/mf-recovery.json
handover/demo/n8n-flows-real-v5/mf-sub-crm-mail.json
=== V5-README grep
5:- The generator takes the HubSpot credential id as argv[6] (LEASE is argv[5]). Without argv[6] the old placeholder text stays.
8:real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
9:film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
10:(The v4 folders were reproduced byte for byte by the OLD generator with these same settings; the lease of real-v4 is 45 and it uses 2 tries and 10 s, like film.)
20:- mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these folders), so MF_V4, MF_TRIES, MF_TMO_MS and the lease are passed as environment.

=== mf-form.json Claimed connections and node (raw, lines as in file)
352:   "Claimed": {
353:    "main": [
354:     [
355:      {
356:       "node": "IsProcessing",
357:       "type": "main",
358:       "index": 0
359:      }
360:     ],
361:     [
362:      {
363:       "node": "Stored",
364:       "type": "main",
365:       "index": 0
366:      }
367:     ]
368:    ]
369:   },
370:   "IsProcessing": {
node114+      1	   },
node114+      2	   "alwaysOutputData": true
node114+      3	  },
node114+      4	  {
node114+      5	   "parameters": {
node114+      6	    "conditions": {
node114+      7	     "options": {
node114+      8	      "caseSensitive": true,
node114+      9	      "leftValue": "",
node114+     10	      "typeValidation": "loose"
node114+     11	     },
node114+     12	     "conditions": [
node114+     13	      {
node114+     14	       "id": "c1",
node114+     15	       "leftValue": "={{ $json.lead_key }}",
node114+     16	       "rightValue": null,
node114+     17	       "operator": {
node114+     18	        "type": "string",
node114+     19	        "operation": "notEmpty",
node114+     20	        "singleValue": true
node114+     21	       }
node114+     22	      }
node114+     23	     ],
node114+     24	     "combinator": "and"
node114+     25	    },
node114+     26	    "options": {}
node114+     27	   },
node114+     28	   "name": "Claimed",
node114+     29	   "type": "n8n-nodes-base.if",
node114+     30	   "typeVersion": 2.2,
node114+     31	   "position": [
node114+     32	    880,
=== same Claimed connection in mf-hook.json
352:   "Claimed": {
353:    "main": [
354:     [
355:      {
356:       "node": "IsProcessing",
357:       "type": "main",
358:       "index": 0
359:      }
360:     ],
361:     [
362:      {
363:       "node": "Stored",
364:       "type": "main",
365:       "index": 0
366:      }
367:     ]
368:    ]
369:   },
370:   "IsProcessing": {

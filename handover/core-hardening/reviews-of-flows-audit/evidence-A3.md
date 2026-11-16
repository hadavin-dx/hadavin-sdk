# evidence-A3 (patches applied in a copy)
sha (target as given in the brief; the copy has no .git so it was NOT verified by me): 35235ace26a516d932e73542c235875f390f333d
date UTC: 2026-11-16 07:57 to about 08:05
COPY: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work (cp -r of fa; no previous work dir existed). git init + one baseline commit (b42b99c) made in COPY only so git apply and git diff work.

## Step 1: git apply --check -p1, cwd COPY root, each against the unmodified baseline
-p1 worked for all five (patch headers use a/ b/). Each: exit 0, no output.
- git apply --check -p1 handover/flows-audit/patches/F-001-one-ddl.patch -> exit=0
- git apply --check -p1 handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch -> exit=0
- git apply --check -p1 handover/flows-audit/patches/F-003-runsheet-claims.patch -> exit=0
- git apply --check -p1 handover/flows-audit/patches/F-004-page-statement-17.patch -> exit=0
- git apply --check -p1 handover/flows-audit/patches/F-008-save-runs-for-the-take.patch -> exit=0

## Step 2: git apply -p1 -v in order, cwd COPY root
F-001: Checking patch handover/demo/n8n-flows/mf_leads.sql... / Applied patch handover/demo/n8n-flows/mf_leads.sql cleanly. exit=0
F-002: Checking patch handover/demo/n8n-mainframe/build_mainframe.py... / Applied ... cleanly. exit=0
F-003: Checking patch handover/demo/VIDEO-RUNSHEET.md... / Applied ... cleanly. exit=0
F-004: Checking patch handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md... / Applied ... cleanly. exit=0
F-008: Checking patch handover/demo/n8n-mainframe/build_mainframe.py... / Applied ... cleanly. exit=0

## Step 3: rebuild commands from both V5-README.md files, cwd COPY/handover/demo/n8n-mainframe (run after all five patches; they overwrite the v5 folders inside COPY only)
$ MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
exit=0
$ MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
exit=0
No network, stack or credential needed (generator imports json, sys, os only). mf.py tests not run (per brief). Both README commands were run; nothing UNVERIFIED in this step.

## Step 4: python3 -I comparison, rebuilt (working tree) vs committed v5 (git HEAD). Script: scratchpad/cmp/diff.py. Output verbatim:
```
## n8n-flows-real-v5/mf-form.json nodes old=12 new=15 conns old=11 new=14
 nodes only old: []
 nodes only new: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
 conns only old: [('Valid', 'main', 0, 'Claim', 'main', 0)]
 conns only new: [('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0), ('KeyOk', 'main', 0, 'Claim', 'main', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0), ('Valid', 'main', 0, 'KeyOk', 'main', 0)]
 nodes same name, differing content: ['Valid', 'Claim']
    Valid parameters old= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali new= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ String($json.lead_key || '').trim() }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "s
    Claim onError old= null new= "continueErrorOutput"
 top-level keys differing: ['settings']
## n8n-flows-real-v5/mf-hook.json nodes old=12 new=15 conns old=11 new=14
 nodes only old: []
 nodes only new: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
 conns only old: [('Valid', 'main', 0, 'Claim', 'main', 0)]
 conns only new: [('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0), ('KeyOk', 'main', 0, 'Claim', 'main', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0), ('Valid', 'main', 0, 'KeyOk', 'main', 0)]
 nodes same name, differing content: ['Valid', 'Claim']
    Valid parameters old= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali new= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ String($json.lead_key || '').trim() }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "s
    Claim onError old= null new= "continueErrorOutput"
 top-level keys differing: ['settings']
## n8n-flows-real-v5/mf-recovery.json nodes old=10 new=10 conns old=9 new=9
 nodes only old: []
 nodes only new: []
 conns only old: []
 conns only new: []
 nodes same name, differing content: []
 top-level keys differing: ['settings']
## n8n-flows-real-v5/mf-sub-crm-mail.json nodes old=20 new=20 conns old=26 new=26
 nodes only old: []
 nodes only new: []
 conns only old: []
 conns only new: []
 nodes same name, differing content: []
 top-level keys differing: ['settings']
## n8n-flows-film-v5/mf-form.json nodes old=12 new=15 conns old=11 new=14
 nodes only old: []
 nodes only new: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
 conns only old: [('Valid', 'main', 0, 'Claim', 'main', 0)]
 conns only new: [('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0), ('KeyOk', 'main', 0, 'Claim', 'main', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0), ('Valid', 'main', 0, 'KeyOk', 'main', 0)]
 nodes same name, differing content: ['Valid', 'Claim']
    Valid parameters old= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali new= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ String($json.lead_key || '').trim() }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "s
    Claim onError old= null new= "continueErrorOutput"
 top-level keys differing: ['settings']
## n8n-flows-film-v5/mf-hook.json nodes old=12 new=15 conns old=11 new=14
 nodes only old: []
 nodes only new: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
 conns only old: [('Valid', 'main', 0, 'Claim', 'main', 0)]
 conns only new: [('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0), ('KeyOk', 'main', 0, 'Claim', 'main', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0), ('Valid', 'main', 0, 'KeyOk', 'main', 0)]
 nodes same name, differing content: ['Valid', 'Claim']
    Valid parameters old= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ $json.lead_key }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "string"}, {"id": "vali new= {"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "value": "={{ String($json.lead_key || '').trim() }}", "type": "string"}, {"id": "email", "name": "email", "value": "={{ $json.email }}", "type": "string"}, {"id": "name", "name": "name", "value": "={{ $json.name }}", "type": "s
    Claim onError old= null new= "continueErrorOutput"
 top-level keys differing: ['settings']
## n8n-flows-film-v5/mf-recovery.json nodes old=10 new=10 conns old=9 new=9
 nodes only old: []
 nodes only new: []
 conns only old: []
 conns only new: []
 nodes same name, differing content: []
 top-level keys differing: ['settings']
## n8n-flows-film-v5/mf-sub-crm-mail.json nodes old=20 new=20 conns old=26 new=26
 nodes only old: []
 nodes only new: []
 conns only old: []
 conns only new: []
 nodes same name, differing content: []
 top-level keys differing: ['settings']
exit=0
```

Full-length text of the settings difference (recovery and sub-crm-mail, both folders; identical shape in all 8 files):
```
@@ -334,8 +334,8 @@
  },
  "settings": {
   "executionOrder": "v1",
-  "saveDataSuccessExecution": "none",
-  "saveDataErrorExecution": "none",
+  "saveDataSuccessExecution": "all",
+  "saveDataErrorExecution": "all",
   "saveManualExecutions": false
  }
 }
\ No newline at end of file
```

## Step 5: git diff --stat in COPY (baseline commit vs now: patches + rebuilt JSON)
```
 handover/demo/VIDEO-RUNSHEET.md                    | 22 ++---
 handover/demo/n8n-flows-film-v5/mf-form.json       | 98 +++++++++++++++++++++-
 handover/demo/n8n-flows-film-v5/mf-hook.json       | 98 +++++++++++++++++++++-
 handover/demo/n8n-flows-film-v5/mf-recovery.json   |  4 +-
 .../demo/n8n-flows-film-v5/mf-sub-crm-mail.json    |  4 +-
 handover/demo/n8n-flows-real-v5/mf-form.json       | 98 +++++++++++++++++++++-
 handover/demo/n8n-flows-real-v5/mf-hook.json       | 98 +++++++++++++++++++++-
 handover/demo/n8n-flows-real-v5/mf-recovery.json   |  4 +-
 .../demo/n8n-flows-real-v5/mf-sub-crm-mail.json    |  4 +-
 handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md      | 14 ++--
 handover/demo/n8n-flows/mf_leads.sql               | 10 ++-
 handover/demo/n8n-mainframe/build_mainframe.py     | 13 ++-
 12 files changed, 419 insertions(+), 48 deletions(-)
```

## Generator and SQL diff (patches F-001, F-002, F-008 as applied)
```diff
diff --git a/handover/demo/n8n-flows/mf_leads.sql b/handover/demo/n8n-flows/mf_leads.sql
index 752c64e..d655b3a 100644
--- a/handover/demo/n8n-flows/mf_leads.sql
+++ b/handover/demo/n8n-flows/mf_leads.sql
@@ -1,4 +1,5 @@
--- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
+-- NOTE (current table, four alert columns at the end): matches the flows used in the take (n8n-flows-real-v5, n8n-flows-film-v5) and the older v3 and v4 flows. The flows in this folder (v2) ignore the extra columns, so this table also runs them (until they are archived, CUT-LIST.md). A table that already exists without the alert columns needs: ALTER TABLE mf_leads ADD COLUMN alert_sent boolean NOT NULL DEFAULT false, ADD COLUMN alert_token text, ADD COLUMN alert_until timestamptz, ADD COLUMN alert_attempts int NOT NULL DEFAULT 0;
+-- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
 -- Design A lead table (Postgres). The insert is the claim. Created before the flows run.
 CREATE TABLE mf_leads(
   lead_key      text PRIMARY KEY,
@@ -11,4 +12,9 @@ CREATE TABLE mf_leads(
   crm_id        text,
   mail_sent     boolean NOT NULL DEFAULT false,
   created_at    timestamptz NOT NULL DEFAULT now(),
-  updated_at    timestamptz NOT NULL DEFAULT now());
+  updated_at    timestamptz NOT NULL DEFAULT now(),
+  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x min(attempts, 5) in the v5 flows).
+  alert_sent    boolean NOT NULL DEFAULT false,
+  alert_token   text,
+  alert_until   timestamptz,
+  alert_attempts int NOT NULL DEFAULT 0);
diff --git a/handover/demo/n8n-mainframe/build_mainframe.py b/handover/demo/n8n-mainframe/build_mainframe.py
index 2b59bf9..2943b45 100644
--- a/handover/demo/n8n-mainframe/build_mainframe.py
+++ b/handover/demo/n8n-mainframe/build_mainframe.py
@@ -41,7 +41,8 @@ def link(con, a, b, out=0):
     con.setdefault(a, {"main": []}); m = con[a]["main"]
     while len(m) <= out: m.append([])
     m[out].append({"node": b, "type": "main", "index": 0})
-ST = {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}
+# Owner 2026-11-16 (ORDER 004): runs are saved for the take only (made-up data) and deleted at clean-up (delete the executions and run n8n execution pruning off the take database).
+ST = {"executionOrder": "v1", "saveDataSuccessExecution": "all", "saveDataErrorExecution": "all", "saveManualExecutions": False}
 KEY = "$('SubIn').first().json.lead_key"; TOK = "$('SubIn').first().json.claim_token"
 def sub():
     n = [N("SubIn", "n8n-nodes-base.executeWorkflowTrigger", 1.1, {"inputSource": "passthrough"}, [0, 0]),
@@ -76,11 +77,15 @@ def call_sub(name, pos, **x): return N(name, "n8n-nodes-base.executeWorkflow", 1
 VERDICT = "{ done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing'"
 def main_flow(name, path, wid, ref, em, nm):
     EMV = "/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email)"
+    # Sender contract: 422 rejected = never retry (no lead_key); 503 retry = the store did not confirm, resend with the SAME lead_key (the INSERT is idempotent: ON CONFLICT DO NOTHING).
     n = [N("Receive", "n8n-nodes-base.webhook", 2, {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}}, [0, 0], webhookId=wid),
          setf("Item", {"lead_key": ("={{ $json.body.%s }}" % ref, "string"), "email": ("={{ $json.body.%s }}" % em, "string"), "name": ("={{ $json.body.%s }}" % nm, "string")}, [220, 0]),
-         setf("Valid", {"lead_key": ("={{ $json.lead_key }}", "string"), "email": ("={{ $json.email }}", "string"), "name": ("={{ $json.name }}", "string"), "valid": ("={{ %s }}" % EMV, "boolean")}, [440, 0]),
+         setf("Valid", {"lead_key": ("={{ String($json.lead_key || '').trim() }}", "string"), "email": ("={{ $json.email }}", "string"), "name": ("={{ $json.name }}", "string"), "valid": ("={{ %s }}" % EMV, "boolean")}, [440, 0]),
+         iff("KeyOk", "={{ $json.lead_key }}", "string", "notEmpty", None, [550, 0]),
+         N("ReplyBadKey", "n8n-nodes-base.respondToWebhook", 1.4, {"respondWith": "json", "responseBody": "={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing' } }}", "options": {"responseCode": 422}}, [550, 180]),
+         N("ReplyStoreFail", "n8n-nodes-base.respondToWebhook", 1.4, {"respondWith": "json", "responseBody": "={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}", "options": {"responseCode": 503}}, [880, 180]),
          pg("Claim", "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '%d seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) "
-            "ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;" % LEASE, "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}", [660, 0]),
+            "ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;" % LEASE, "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}", [660, 0], onError="continueErrorOutput"),
          iff("Claimed", "={{ $json.lead_key }}", "string", "notEmpty", None, [880, 0]),
          iff("IsProcessing", "={{ $json.state }}", "string", "equals", "processing", [1100, -100]),
          setf("SubInput", {"lead_key": ("={{ $json.lead_key }}", "string"), "claim_token": ("={{ $json.claim_token }}", "string"), "email": ("={{ $('Valid').item.json.email }}", "string")}, [1320, -160]),
@@ -90,7 +95,7 @@ def main_flow(name, path, wid, ref, em, nm):
          pg("Stored", "SELECT state FROM mf_leads WHERE lead_key=$1;", "={{ [$('Valid').item.json.lead_key] }}", [1100, 240]),
          respond("ReplyStored", "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}", [1320, 240])]
     c = {}
-    link(c, "Receive", "Item"); link(c, "Item", "Valid"); link(c, "Valid", "Claim"); link(c, "Claim", "Claimed"); link(c, "Claimed", "IsProcessing", 0); link(c, "Claimed", "Stored", 1)
+    link(c, "Receive", "Item"); link(c, "Item", "Valid"); link(c, "Valid", "KeyOk"); link(c, "KeyOk", "Claim", 0); link(c, "KeyOk", "ReplyBadKey", 1); link(c, "Claim", "Claimed", 0); link(c, "Claim", "ReplyStoreFail", 1); link(c, "Claimed", "IsProcessing", 0); link(c, "Claimed", "Stored", 1)
     link(c, "IsProcessing", "SubInput", 0); link(c, "IsProcessing", "ReplyReview", 1); link(c, "SubInput", "RunSub"); link(c, "RunSub", "ReplyRan"); link(c, "Stored", "ReplyStored")
     return {"name": name, "nodes": n, "connections": c, "settings": ST}
 def recovery():
```

## Not done / uncertain
- The sha in the first lines is the brief's; the fa folder has no .git, so I could not check it.
- Node-level diff only compared name sets, connection tuples and per-node JSON equality; position or other cosmetic fields appear only if they differ (none listed besides those shown).
- No n8n import or run (no stack).

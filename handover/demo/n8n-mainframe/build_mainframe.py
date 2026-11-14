"""Builds Design A, version 2 (D-N2a): n8n is the main frame. Made-up data, no secret in the output (credentials by NAME and id only). Written from scratch.
Parts: ONE sub-workflow "CRM + mail" (called by the main flow AND by recovery), two main flows (form entry, e-mail-style entry), one recovery flow (lease claim, plus the failed-lead alert).
Lead table (Postgres): lead_key unique, state (new, processing, done, review, unknown, failed), claimed_until, claim_token, attempts, crm_id, mail_sent, created_at, updated_at. The insert IS the claim.
Every write is a conditional update on the claim token; the SMTP node runs only when its conditional update returned a row; retry is OFF on the SMTP node; if the desk stage (cap + model) errors, times out or refuses, NO CRM write and NO mail runs (fail closed).
Settings from n8n's environment: MF_CRM_URL, MF_STAGE_URL. The mail recipient and the alert recipient are CONSTANTS in the nodes (no expression).
  python build_mainframe.py OUT_DIR PG_CRED_ID SMTP_CRED_ID SUB_WORKFLOW_ID [LEASE_SECONDS]      (LEASE_SECONDS: design value 120; the tests use a shorter value and say so)"""
import json, sys, os
OUT, PGID, SMTPID, SUBID = sys.argv[1:5]; LEASE = int(sys.argv[5]) if len(sys.argv) > 5 else 120
TRIES = int(os.environ.get("MF_TRIES", "3")); TMO = int(os.environ.get("MF_TMO_MS", "15000"))   # film variant: MF_TRIES=2 MF_TMO_MS=10000 (defaults = the design flows)
MAIL_TO, ALERT_TO = "intake@example.test", "alerts@example.test"
def N(name, typ, ver, params, pos, **x):
    d = {"parameters": params, "name": name, "type": typ, "typeVersion": ver, "position": pos}; d.update(x); return d
def pg(name, q, repl, pos, always=True, **x):
    o = {"queryReplacement": repl} if repl else {}
    return N(name, "n8n-nodes-base.postgres", 2.5, {"operation": "executeQuery", "query": q, "options": o}, pos, credentials={"postgres": {"id": PGID, "name": "n8n-publish-pg"}}, alwaysOutputData=always, **x)
def http(name, url, body, pos, retry, errout=False):
    d = N(name, "n8n-nodes-base.httpRequest", 4.2, {"method": "POST", "url": url, "sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": body, "options": {"timeout": "={{ Number($env.MF_STAGE_TIMEOUT_MS || %d) }}" % TMO if "MF_STAGE_URL" in url else TMO}}, pos)
    if retry: d.update(retryOnFail=True, maxTries=TRIES, waitBetweenTries=1000)
    if errout: d["onError"] = "continueErrorOutput"
    return d
def iff(name, left, op_type, op, right, pos):
    return N(name, "n8n-nodes-base.if", 2.2, {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"}, "conditions": [
        {"id": "c1", "leftValue": left, "rightValue": right, "operator": {"type": op_type, "operation": op, **({"singleValue": True} if right is None else {})}}], "combinator": "and"}, "options": {}}, pos)
def respond(name, body, pos): return N(name, "n8n-nodes-base.respondToWebhook", 1.4, {"respondWith": "json", "responseBody": body, "options": {"responseCode": 200}}, pos)
def setf(name, fields, pos):
    return N(name, "n8n-nodes-base.set", 3.4, {"assignments": {"assignments": [{"id": k, "name": k, "value": v, "type": t} for k, (v, t) in fields.items()]}, "options": {}}, pos)
def mail(name, to, subj, text, pos, **x):
    return N(name, "n8n-nodes-base.emailSend", 2.1, {"fromEmail": "desk@example.test", "toEmail": to, "subject": subj, "emailFormat": "text", "text": text, "options": {"appendAttribution": False}}, pos,
             credentials={"smtp": {"id": SMTPID, "name": "mf-mail-smtp"}}, **x)
def link(con, a, b, out=0):
    con.setdefault(a, {"main": []}); m = con[a]["main"]
    while len(m) <= out: m.append([])
    m[out].append({"node": b, "type": "main", "index": 0})
ST = {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}
KEY = "$('SubIn').first().json.lead_key"; TOK = "$('SubIn').first().json.claim_token"
def sub():
    n = [N("SubIn", "n8n-nodes-base.executeWorkflowTrigger", 1.1, {"inputSource": "passthrough"}, [0, 0]),
         http("Qualify", "={{ $env.MF_STAGE_URL }}/qualify", "={{ { lead_key: %s, email: $('SubIn').first().json.email } }}" % KEY, [220, 0], True, errout=True),
         iff("LabelOk", "={{ ['hot','warm','cold'].includes($json.label) && !$json.unknown_model }}", "boolean", "true", None, [440, -60]),
         http("CrmUpsert", "={{ $env.MF_CRM_URL }}/upsert", "={{ { hadavin_lead_id: %s, email: $('SubIn').first().json.email, label: $('Qualify').first().json.label } }}" % KEY, [660, -60], True, errout=True),
         pg("SetCrmId", "UPDATE mf_leads SET crm_id=$2, updated_at=now() WHERE lead_key=$1 AND claim_token=$3 AND state='processing' RETURNING lead_key;", "={{ [%s, String($json.id), %s] }}" % (KEY, TOK), [880, -60]),
         iff("OwnsClaim1", "={{ $json.lead_key }}", "string", "notEmpty", None, [1100, -60]),
         pg("MailClaim", "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND mail_sent=false AND state='processing' RETURNING lead_key;", "={{ [%s, %s] }}" % (KEY, TOK), [1320, -60]),
         iff("MailRowBack", "={{ $json.lead_key }}", "string", "notEmpty", None, [1540, -60]),
         mail("SendMail", MAIL_TO, "={{ '[demo] lead ' + %s }}" % KEY, "made-up thank-you text", [1760, -140], retryOnFail=False, onError="continueErrorOutput"),
         pg("MarkDone", "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;", "={{ [%s, %s] }}" % (KEY, TOK), [1980, -200]),
         pg("MarkUnknownA", "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' RETURNING lead_key;", "={{ [%s, %s] }}" % (KEY, TOK), [1980, -60]),
         pg("MarkUnknownB", "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 AND claim_token=$2 AND state='processing' AND mail_sent RETURNING lead_key;", "={{ [%s, %s] }}" % (KEY, TOK), [1760, 100]),
         iff("UnknownNewA", "={{ $json.lead_key }}", "string", "notEmpty", None, [2200, -60]),
         iff("UnknownNew", "={{ $json.lead_key }}", "string", "notEmpty", None, [1980, 100]),
         mail("AlertUnknown", ALERT_TO, "={{ '[demo] Lead desk: mail outcome unknown for ' + %s }}" % KEY, "={{ 'Lead id ' + %s + ': the mail may or may not have been sent. A person decides.' }}" % KEY, [2200, 0], onError="continueRegularOutput"),
         iff("DoneOwned", "={{ $json.lead_key }}", "string", "notEmpty", None, [2200, -260]),
         setf("OutDone", {"outcome": ("done", "string"), "lead_key": ("={{ %s }}" % KEY, "string")}, [2200, -200]),
         setf("OutUnknown", {"outcome": ("unknown", "string"), "lead_key": ("={{ %s }}" % KEY, "string")}, [2420, 0]),
         setf("OutStage", {"outcome": ("stage_failed", "string"), "lead_key": ("={{ %s }}" % KEY, "string")}, [660, 160]),
         setf("OutLost", {"outcome": ("lost_claim", "string"), "lead_key": ("={{ %s }}" % KEY, "string")}, [1320, 160])]
    c = {}
    link(c, "SubIn", "Qualify"); link(c, "Qualify", "LabelOk", 0); link(c, "Qualify", "OutStage", 1)
    link(c, "LabelOk", "CrmUpsert", 0); link(c, "LabelOk", "OutStage", 1); link(c, "CrmUpsert", "SetCrmId", 0); link(c, "CrmUpsert", "OutStage", 1); link(c, "SetCrmId", "OwnsClaim1")
    link(c, "OwnsClaim1", "MailClaim", 0); link(c, "OwnsClaim1", "OutLost", 1); link(c, "MailClaim", "MailRowBack")
    link(c, "MailRowBack", "SendMail", 0); link(c, "MailRowBack", "MarkUnknownB", 1)
    link(c, "SendMail", "MarkDone", 0); link(c, "SendMail", "MarkUnknownA", 1); link(c, "MarkDone", "DoneOwned"); link(c, "DoneOwned", "OutDone", 0); link(c, "DoneOwned", "OutLost", 1)
    link(c, "MarkUnknownA", "UnknownNewA"); link(c, "UnknownNewA", "AlertUnknown", 0); link(c, "UnknownNewA", "OutUnknown", 1); link(c, "MarkUnknownB", "UnknownNew"); link(c, "UnknownNew", "AlertUnknown", 0); link(c, "UnknownNew", "OutUnknown", 1); link(c, "AlertUnknown", "OutUnknown")
    return {"name": "Lead desk main frame: CRM + mail (sub-workflow)", "nodes": n, "connections": c, "settings": ST}
def call_sub(name, pos, **x): return N(name, "n8n-nodes-base.executeWorkflow", 1.2, {"source": "database", "workflowId": {"__rl": True, "value": SUBID, "mode": "id"}, "mode": "each", "options": {"waitForSubWorkflow": True}}, pos, **x)
VERDICT = "{ done: 'new', unknown: 'unknown', stage_failed: 'processing', lost_claim: 'processing' }[$json.outcome] || 'processing'"
def main_flow(name, path, wid, ref, em, nm):
    EMV = "/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.email)"
    n = [N("Receive", "n8n-nodes-base.webhook", 2, {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}}, [0, 0], webhookId=wid),
         setf("Item", {"lead_key": ("={{ $json.body.%s }}" % ref, "string"), "email": ("={{ $json.body.%s }}" % em, "string"), "name": ("={{ $json.body.%s }}" % nm, "string")}, [220, 0]),
         setf("Valid", {"lead_key": ("={{ $json.lead_key }}", "string"), "email": ("={{ $json.email }}", "string"), "name": ("={{ $json.name }}", "string"), "valid": ("={{ %s }}" % EMV, "boolean")}, [440, 0]),
         pg("Claim", "INSERT INTO mf_leads(lead_key,email,name,state,claimed_until,claim_token,attempts) VALUES ($1,$2,$3, CASE WHEN $4::boolean THEN 'processing' ELSE 'review' END, now() + interval '%d seconds', gen_random_uuid()::text, CASE WHEN $4::boolean THEN 1 ELSE 0 END) "
            "ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key, claim_token, state;" % LEASE, "={{ [$json.lead_key, $json.email, $json.name, $json.valid] }}", [660, 0]),
         iff("Claimed", "={{ $json.lead_key }}", "string", "notEmpty", None, [880, 0]),
         iff("IsProcessing", "={{ $json.state }}", "string", "equals", "processing", [1100, -100]),
         setf("SubInput", {"lead_key": ("={{ $json.lead_key }}", "string"), "claim_token": ("={{ $json.claim_token }}", "string"), "email": ("={{ $('Valid').item.json.email }}", "string")}, [1320, -160]),
         call_sub("RunSub", [1540, -160]),
         respond("ReplyRan", "={{ { n8n_error: false, lead_key: $json.lead_key, verdict: %s } }}" % VERDICT, [1760, -160]),
         respond("ReplyReview", "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: 'review' } }}", [1320, 20]),
         pg("Stored", "SELECT state FROM mf_leads WHERE lead_key=$1;", "={{ [$('Valid').item.json.lead_key] }}", [1100, 240]),
         respond("ReplyStored", "={{ { n8n_error: false, lead_key: $('Valid').item.json.lead_key, verdict: ({ done: 'done', processing: 'processing', new: 'processing', review: 'review', unknown: 'unknown', failed: 'failed' })[$json.state] || 'processing', repeat: true } }}", [1320, 240])]
    c = {}
    link(c, "Receive", "Item"); link(c, "Item", "Valid"); link(c, "Valid", "Claim"); link(c, "Claim", "Claimed"); link(c, "Claimed", "IsProcessing", 0); link(c, "Claimed", "Stored", 1)
    link(c, "IsProcessing", "SubInput", 0); link(c, "IsProcessing", "ReplyReview", 1); link(c, "SubInput", "RunSub"); link(c, "RunSub", "ReplyRan"); link(c, "Stored", "ReplyStored")
    return {"name": name, "nodes": n, "connections": c, "settings": ST}
def recovery():
    n = [N("Every30s", "n8n-nodes-base.scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "seconds", "secondsInterval": 30}]}}, [0, 0]),
         pg("ClaimStuck", "UPDATE mf_leads SET claimed_until=now() + interval '%d seconds', claim_token=gen_random_uuid()::text, attempts=attempts+1, updated_at=now() WHERE lead_key IN ("
            "SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts < 3 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) "
            "RETURNING lead_key, email, claim_token;" % LEASE, None, [220, -100], always=False, onError="continueRegularOutput"),
         iff("StuckRow", "={{ $json.lead_key }}", "string", "notEmpty", None, [330, -100]),
         call_sub("RunSub", [550, -160], onError="continueRegularOutput"),
         pg("MarkFailed", "UPDATE mf_leads SET state='failed', updated_at=now() WHERE state NOT IN ('done','review','unknown','failed') AND claimed_until < now() AND attempts >= 3 RETURNING lead_key;", None, [220, 120], always=False, onError="continueRegularOutput"),
         iff("FailedRow", "={{ $json.lead_key }}", "string", "notEmpty", None, [330, 120]),
         mail("AlertFailed", ALERT_TO, "={{ '[demo] Lead desk: lead failed ' + $json.lead_key }}", "={{ 'Lead id ' + $json.lead_key + ' could not be finished after 3 tries. A person decides.' }}", [550, 80], onError="continueRegularOutput")]
    # the Postgres node returns ONE item {success: true} when a non-SELECT statement matches no row (n8n source, Postgres v2 helpers/utils.js): only an item that carries a lead id is work
    c = {}; link(c, "Every30s", "MarkFailed"); link(c, "Every30s", "ClaimStuck"); link(c, "ClaimStuck", "StuckRow"); link(c, "StuckRow", "RunSub", 0); link(c, "MarkFailed", "FailedRow"); link(c, "FailedRow", "AlertFailed", 0)
    return {"name": "Lead desk main frame: recovery (every 30 s)", "nodes": n, "connections": c, "settings": ST}
os.makedirs(OUT, exist_ok=True)
for fn, w in (("mf-sub-crm-mail.json", sub()),
              ("mf-form.json", main_flow("Lead desk main frame: form entry", "mf-form", "mf-form-wh", "submission_id", "email", "name")),
              ("mf-hook.json", main_flow("Lead desk main frame: e-mail-style entry", "mf-hook", "mf-hook-wh", "message_id", "from_email", "from_name")),
              ("mf-recovery.json", recovery())):
    json.dump(w, open(os.path.join(OUT, fn), "w"), indent=1); print("wrote", fn)

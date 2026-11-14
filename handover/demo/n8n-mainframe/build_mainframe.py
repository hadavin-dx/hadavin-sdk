"""Builds the D-N2 flow family (made-up data, no secret in the output; credentials by NAME and id only): the main flow for two entries (form, e-mail-style webhook) and the recovery flow.
Written from scratch. n8n owns: the lead table (Postgres node), CRM search-then-create (HTTP Request node), the mail (SMTP/Send Email node), the reply. The desk is called by ONE node (qualify) for the cap and the model call.
Settings from n8n's environment: MF_CRM_URL, MF_STAGE_URL.   python build_mainframe.py OUT_DIR PG_CRED_ID SMTP_CRED_ID"""
import json, sys, os
OUT, PGID, SMTPID = sys.argv[1], sys.argv[2], sys.argv[3]
def N(name, typ, ver, params, pos, **x):
    d = {"parameters": params, "name": name, "type": typ, "typeVersion": ver, "position": pos}; d.update(x); return d
def pg(name, q, repl, pos, always=True):
    o = {"queryReplacement": repl} if repl else {}
    return N(name, "n8n-nodes-base.postgres", 2.5, {"operation": "executeQuery", "query": q, "options": o}, pos, credentials={"postgres": {"id": PGID, "name": "n8n-publish-pg"}}, alwaysOutputData=always)
def http(name, url, body, pos, retry):
    d = N(name, "n8n-nodes-base.httpRequest", 4.2, {"method": "POST", "url": url, "sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": body, "options": {"timeout": 15000}}, pos)
    if retry: d.update(retryOnFail=True, maxTries=3, waitBetweenTries=1000)
    return d
def iff(name, left, op_type, op, right, pos):
    return N(name, "n8n-nodes-base.if", 2.2, {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"}, "conditions": [
        {"id": "c1", "leftValue": left, "rightValue": right, "operator": {"type": op_type, "operation": op, **({"singleValue": True} if right is None else {})}}], "combinator": "and"}, "options": {}}, pos)
def respond(name, body, pos): return N(name, "n8n-nodes-base.respondToWebhook", 1.4, {"respondWith": "json", "responseBody": body, "options": {"responseCode": 200}}, pos)
def setf(name, fields, pos):
    return N(name, "n8n-nodes-base.set", 3.4, {"assignments": {"assignments": [{"id": k, "name": k, "value": v, "type": t} for k, (v, t) in fields.items()]}, "options": {}}, pos)
def link(con, a, b, out=0):
    con.setdefault(a, {"main": []}); m = con[a]["main"]
    while len(m) <= out: m.append([])
    m[out].append({"node": b, "type": "main", "index": 0})
def steps(p, x0, y0, nodes, con, entry_from, entry_out=0):
    """the shared steps (main flow and recovery use the same): qualify (desk stage) -> save label -> CRM search -> create if none -> state crm_done -> mail gate -> mark mail_sent -> send -> state done.
    returns the name of the last node (state done)."""
    I = lambda f: "$('%sItem').item.json.%s" % (p, f)
    Q = p + "Qualify"
    nodes += [http(Q, "={{ $env.MF_STAGE_URL }}/qualify", "={{ { lead_key: %s, email: %s } }}" % (I("lead_key"), I("email")), [x0, y0], True),
        pg(p + "SaveLabel", "UPDATE mf_leads SET label=$2, updated_at=now() WHERE lead_key=$1 RETURNING lead_key;", "={{ [%s, $json.label] }}" % I("lead_key"), [x0 + 220, y0]),
        http(p + "CrmSearch", "={{ $env.MF_CRM_URL }}/search", "={{ { lead_key: %s } }}" % I("lead_key"), [x0 + 440, y0], True),
        iff(p + "CrmNone", "={{ $json.results.length }}", "number", "equals", 0, [x0 + 660, y0]),
        http(p + "CrmCreate", "={{ $env.MF_CRM_URL }}/create", "={{ { lead_key: %s, email: %s, label: $('%s').item.json.label } }}" % (I("lead_key"), I("email"), Q), [x0 + 880, y0 - 80], False),
        N(p + "CrmExists", "n8n-nodes-base.noOp", 1, {}, [x0 + 880, y0 + 80]),
        pg(p + "SetCrm", "UPDATE mf_leads SET state='crm_done', updated_at=now() WHERE lead_key=$1 RETURNING lead_key;", "={{ [%s] }}" % I("lead_key"), [x0 + 1100, y0]),
        iff(p + "MailAlready", "={{ %s }}" % I("mail_sent"), "boolean", "true", None, [x0 + 1320, y0]),
        pg(p + "MarkUnknown", "UPDATE mf_leads SET state='unknown', updated_at=now() WHERE lead_key=$1 RETURNING lead_key;", "={{ [%s] }}" % I("lead_key"), [x0 + 1540, y0 + 120]),
        pg(p + "MarkMailSent", "UPDATE mf_leads SET mail_sent=true, updated_at=now() WHERE lead_key=$1 RETURNING lead_key;", "={{ [%s] }}" % I("lead_key"), [x0 + 1540, y0 - 60]),
        N(p + "SendMail", "n8n-nodes-base.emailSend", 2.1, {"fromEmail": "desk@example.test", "toEmail": "={{ %s }}" % I("email"), "subject": "={{ 'Thanks, ref ' + %s }}" % I("lead_key"), "emailFormat": "text", "text": "made-up thank-you text",
          "options": {"appendAttribution": False}}, [x0 + 1760, y0 - 60], credentials={"smtp": {"id": SMTPID, "name": "mf-mail-smtp"}}),
        pg(p + "MarkDone", "UPDATE mf_leads SET state='done', updated_at=now() WHERE lead_key=$1 RETURNING lead_key;", "={{ [%s] }}" % I("lead_key"), [x0 + 1980, y0 - 60])]
    link(con, entry_from, Q, entry_out); link(con, Q, p + "SaveLabel"); link(con, p + "SaveLabel", p + "CrmSearch"); link(con, p + "CrmSearch", p + "CrmNone")
    link(con, p + "CrmNone", p + "CrmCreate", 0); link(con, p + "CrmNone", p + "CrmExists", 1); link(con, p + "CrmCreate", p + "SetCrm"); link(con, p + "CrmExists", p + "SetCrm")
    link(con, p + "SetCrm", p + "MailAlready"); link(con, p + "MailAlready", p + "MarkUnknown", 0); link(con, p + "MailAlready", p + "MarkMailSent", 1)
    link(con, p + "MarkMailSent", p + "SendMail"); link(con, p + "SendMail", p + "MarkDone")
    return p + "MarkDone"
ST = {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}
def main_flow(name, path, wid, ref, em, nm):
    nodes = [N("Receive", "n8n-nodes-base.webhook", 2, {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}}, [0, 0], webhookId=wid),
        setf("Item", {"lead_key": ("={{ $json.body.%s }}" % ref, "string"), "email": ("={{ $json.body.%s }}" % em, "string"), "name": ("={{ $json.body.%s }}" % nm, "string"), "mail_sent": (False, "boolean")}, [220, 0]),
        pg("Insert", "INSERT INTO mf_leads(lead_key,email,name) VALUES ($1,$2,$3) ON CONFLICT (lead_key) DO NOTHING RETURNING lead_key;", "={{ [$json.lead_key, $json.email, $json.name] }}", [440, 0]),
        iff("Inserted", "={{ $json.lead_key }}", "string", "notEmpty", None, [660, 0]),
        pg("StoredState", "SELECT state, label FROM mf_leads WHERE lead_key=$1;", "={{ [$('Item').item.json.lead_key] }}", [880, 300]),
        respond("ReplyRepeat", "={{ { n8n_error: false, lead_key: $('Item').item.json.lead_key, state: $json.state, verdict: $json.state === 'done' ? 'new' : ($json.state === 'unknown' ? 'needs_person' : null), repeat: true } }}", [1100, 300])]
    con = {}; link(con, "Receive", "Item"); link(con, "Item", "Insert"); link(con, "Insert", "Inserted")
    link(con, "Inserted", "StoredState", 1)
    last = steps("", 880, -100, nodes, con, "Inserted", 0)
    nodes.append(respond("ReplyDone", "={{ { n8n_error: false, lead_key: $('Item').item.json.lead_key, state: 'done', verdict: 'new', label: $('Qualify').item.json.label, repeat: false } }}", [3000, -160])); link(con, last, "ReplyDone")
    link(con, "StoredState", "ReplyRepeat")
    return {"name": name, "nodes": nodes, "connections": con, "settings": ST}
def recovery():
    nodes = [N("Every30s", "n8n-nodes-base.scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "seconds", "secondsInterval": 30}]}}, [0, 0]),
        pg("ClaimStuck", "UPDATE mf_leads SET updated_at=now() WHERE lead_key IN (SELECT lead_key FROM mf_leads WHERE state NOT IN ('done','unknown') AND updated_at < now() - interval '20 seconds' "
           "ORDER BY created_at LIMIT 20 FOR UPDATE SKIP LOCKED) RETURNING lead_key, email, name, mail_sent, state;", None, [220, 0], always=False),
        setf("RItem", {"lead_key": ("={{ $json.lead_key }}", "string"), "email": ("={{ $json.email }}", "string"), "mail_sent": ("={{ $json.mail_sent }}", "boolean")}, [440, 0])]
    con = {}; link(con, "Every30s", "ClaimStuck"); link(con, "ClaimStuck", "RItem")
    steps("R", 660, 0, nodes, con, "RItem", 0)
    return {"name": "Lead desk main frame: recovery (every 30 s)", "nodes": nodes, "connections": con, "settings": ST}
os.makedirs(OUT, exist_ok=True)
for fn, w in (("mf-form.json", main_flow("Lead desk main frame: form entry", "mf-form", "mf-form-wh", "submission_id", "email", "name")),
              ("mf-hook.json", main_flow("Lead desk main frame: e-mail-style entry", "mf-hook", "mf-hook-wh", "message_id", "from_email", "from_name")),
              ("mf-recovery.json", recovery())):
    json.dump(w, open(os.path.join(OUT, fn), "w"), indent=1); print("wrote", fn)

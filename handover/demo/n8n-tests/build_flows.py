"""Builds the three n8n flows of the door (made-up data, no secret in the output): the form door, the e-mail-style webhook door and the error notifier.
Written from scratch (the repository's own two flow files are not edited: licence). Same field mapping as those two files.
Settings come from n8n's environment (start command in N8N-START.md): DESK_URL (base address of the desk, no path), DESK_TIMEOUT_MS (node timeout), DESK_ALERT_TO (fixed alert recipient).
  python build_flows.py OUT_DIR [ERROR_WORKFLOW_ID]"""
import json, sys, os
OUT = sys.argv[1]; ERR_ID = sys.argv[2] if len(sys.argv) > 2 else ""
def webhook(path, wid):
    return {"parameters": {"httpMethod": "POST", "path": path, "responseMode": "responseNode", "options": {}}, "name": "Receive the submission", "type": "n8n-nodes-base.webhook",
            "typeVersion": 2, "position": [0, 0], "webhookId": wid}
def mapper(source, ref, payload):
    return {"parameters": {"assignments": {"assignments": [
        {"id": "source", "name": "source", "value": source, "type": "string"},
        {"id": "source_ref", "name": "source_ref", "value": "={{ $json.body.%s }}" % ref, "type": "string"},
        {"id": "payload", "name": "payload", "value": "={{ %s }}" % payload, "type": "object"}]}, "options": {}},
        "name": "Map to the desk format", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [220, 0]}
DESK = {"parameters": {"method": "POST", "url": "={{ $env.DESK_URL }}/leads", "sendBody": True, "contentType": "json", "specifyBody": "json",
        "jsonBody": "={{ { source: $json.source, source_ref: $json.source_ref, payload: $json.payload } }}",
        "options": {"timeout": "={{ Number($env.DESK_TIMEOUT_MS) }}", "response": {"response": {"fullResponse": True, "neverError": False}}}},
        "name": "Send to the desk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 0],
        "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 1000, "onError": "continueErrorOutput"}
OK = {"parameters": {"mode": "runOnceForAllItems", "jsCode":
      "const r = $input.first().json; const ref = $('Map to the desk format').first().json.source_ref;\n"
      "let body = r.body; if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }\n"
      "const verdict = body && typeof body === 'object' ? (body.verdict || null) : null;\n"
      "if (!verdict) { return [{json: {n8n_error: true, error: 'desk answer had no verdict', desk_status: r.statusCode, lead_ref: ref}}]; }\n"
      "return [{json: {n8n_error: false, desk_status: r.statusCode, verdict: verdict, desk: body, lead_ref: ref}}];"},
      "name": "Shape the reply", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [660, -100]}
BAD = {"parameters": {"mode": "runOnceForAllItems", "jsCode":
      "const ref = $('Map to the desk format').first().json.source_ref;\n"
      "return [{json: {n8n_error: true, error: 'desk call failed after retries', lead_ref: ref}}];"},
      "name": "Shape the error reply", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [660, 100]}
def respond(name, code, pos):
    return {"parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {"responseCode": code}}, "name": name, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.4, "position": pos}
STOP = {"parameters": {"errorType": "errorMessage", "errorMessage": "={{ 'desk_unreachable lead_id=' + $json.lead_ref }}"}, "name": "Fail the run (fires the error workflow)", "type": "n8n-nodes-base.stopAndError", "typeVersion": 1, "position": [1100, 100]}
def door(name, path, wid, source, ref, payload):
    nodes = [webhook(path, wid), mapper(source, ref, payload), DESK, OK, BAD, respond("Reply 2xx", "={{ $json.n8n_error ? 502 : 200 }}", [880, -100]), respond("Reply error", 502, [880, 100]), STOP]
    con = {"Receive the submission": {"main": [[{"node": "Map to the desk format", "type": "main", "index": 0}]]},
           "Map to the desk format": {"main": [[{"node": "Send to the desk", "type": "main", "index": 0}]]},
           "Send to the desk": {"main": [[{"node": "Shape the reply", "type": "main", "index": 0}], [{"node": "Shape the error reply", "type": "main", "index": 0}]]},
           "Shape the reply": {"main": [[{"node": "Reply 2xx", "type": "main", "index": 0}]]},
           "Shape the error reply": {"main": [[{"node": "Reply error", "type": "main", "index": 0}]]},
           "Reply error": {"main": [[{"node": "Fail the run (fires the error workflow)", "type": "main", "index": 0}]]}}
    st = {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}
    if ERR_ID: st["errorWorkflow"] = ERR_ID
    return {"name": name, "nodes": nodes, "connections": con, "settings": st}
def notifier():
    err = {"parameters": {}, "name": "Error Trigger", "type": "n8n-nodes-base.errorTrigger", "typeVersion": 1, "position": [0, 0]}
    mail = {"parameters": {"fromEmail": "desk-door@example.test", "toEmail": "={{ $env.DESK_ALERT_TO }}", "subject": "Lead desk door: the desk did not answer",
            "emailFormat": "text", "text": "={{ 'The desk did not answer after retries. ' + $json.execution.error.message + '. Execution ' + $json.execution.id + '.' }}",
            "options": {"appendAttribution": False}},
            "name": "Notify", "type": "n8n-nodes-base.emailSend", "typeVersion": 2.1, "position": [220, 0],
            "retryOnFail": True, "maxTries": 3, "waitBetweenTries": 1000, "credentials": {"smtp": {"id": "CREDENTIAL_ID_PLACEHOLDER", "name": "desk-alert-smtp"}}}
    return {"name": "Lead desk door: error notifier", "nodes": [err, mail], "connections": {"Error Trigger": {"main": [[{"node": "Notify", "type": "main", "index": 0}]]}},
            "settings": {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none"}}
FORM = ('{"name": $json.body.name, "email": $json.body.email, "phone": $json.body.phone, "company": $json.body.company, "message": $json.body.message}')
HOOK = ('{"name": $json.body.from_name, "email": $json.body.from_email, "message": $json.body.body}')
os.makedirs(OUT, exist_ok=True)
for fn, w in (("desk-form-door.json", door("Lead Desk door: Web Form Intake", "desk-form", "door-form-wh", "form", "submission_id", FORM)),
              ("desk-webhook-door.json", door("Lead Desk door: Email Intake", "desk-webhook", "door-hook-wh", "webhook", "message_id", HOOK)),
              ("desk-error-notifier.json", notifier())):
    json.dump(w, open(os.path.join(OUT, fn), "w"), indent=1); print("wrote", fn)

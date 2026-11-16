### n8n-flows/desk-error-notifier.json (2 nodes)  workflow='Lead desk door: error notifier' settings={"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none"}
| # | node | type | parameters (masked) | downstream (out,node) | onError | retry/tries/wait | disabled | credential | reachable |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Error Trigger | n8n-nodes-base.errorTrigger v1 | {} | [(0, 'Notify')] | None | None/None/None | None | none | ENTRY |
| 2 | Notify | n8n-nodes-base.emailSend v2.1 | {"fromEmail": "desk-door@example.test", "toEmail": "={{ $env.DESK_ALERT_TO }}", "subject": "Lead desk door: the desk did not answer", "emailFormat": "text", "text": "={{ 'The desk did not answer after retries. ' + $json.execution.error.message + '. Execution ' + $json.execution.id + '.' }}", "options": {"appendAttribution": false}} | none | None | True/3/1000 | None | smtp:desk-alert-smtp | Y |
dangling edges: []; node names unique: True

# E5 term counts (raw; count = lines matching, case-insensitive, grep -c -i -E)
Run in work-new-pristine/handover/flows-audit (these 3 files are not changed by any patch).
## pattern: PG_CREDENTIAL_ID
  FINDINGS.md: 1
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: SMTP_CREDENTIAL_ID
  FINDINGS.md: 1
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: HubSpot credential
  FINDINGS.md: 0
  FIX-PLAN.md: 0
  EXCEPTIONS.md: 0
## pattern: N8N_BLOCK_ENV_ACCESS_IN_NODE
  FINDINGS.md: 3
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: errorWorkflow
  FINDINGS.md: 4
  FIX-PLAN.md: 0
  EXCEPTIONS.md: 0
## pattern: alert flood|alert cap
  FINDINGS.md: 0
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: 422
  FINDINGS.md: 3
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: 503
  FINDINGS.md: 3
  FIX-PLAN.md: 1
  EXCEPTIONS.md: 0
## pattern: empty key|empty lead_key
  FINDINGS.md: 3
  FIX-PLAN.md: 0
  EXCEPTIONS.md: 0
## pattern: timeout
  FINDINGS.md: 3
  FIX-PLAN.md: 0
  EXCEPTIONS.md: 0
## pattern: lead_key. trimmed|"lead_key" trimmed
  FINDINGS.md: 0
  FIX-PLAN.md: 0
  EXCEPTIONS.md: 0

## flow JSON (committed, real-v5 and film-v5, 4 files each). Counts = occurrences (grep -o | wc -l)
n8n-flows-real-v5 PLACEHOLDER: 4
n8n-flows-real-v5 SUB_WORKFLOW_ID: 3
n8n-flows-real-v5 PG_CREDENTIAL_ID: 14
n8n-flows-real-v5 SMTP_CREDENTIAL_ID: 2
n8n-flows-film-v5 PLACEHOLDER: 0
n8n-flows-film-v5 SUB_WORKFLOW_ID: 3
n8n-flows-film-v5 PG_CREDENTIAL_ID: 14
n8n-flows-film-v5 SMTP_CREDENTIAL_ID: 2

## credential key names and errorWorkflow presence
n8n-flows-real-v5/mf-form.json credential type keys: ['postgres'] credentials entries with an id field: 2 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-real-v5/mf-hook.json credential type keys: ['postgres'] credentials entries with an id field: 2 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-real-v5/mf-recovery.json credential type keys: ['postgres', 'smtp'] credentials entries with an id field: 6 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-real-v5/mf-sub-crm-mail.json credential type keys: ['hubspotAppToken', 'postgres', 'smtp'] credentials entries with an id field: 7 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-film-v5/mf-form.json credential type keys: ['postgres'] credentials entries with an id field: 2 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-film-v5/mf-hook.json credential type keys: ['postgres'] credentials entries with an id field: 2 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-film-v5/mf-recovery.json credential type keys: ['postgres', 'smtp'] credentials entries with an id field: 6 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False
n8n-flows-film-v5/mf-sub-crm-mail.json credential type keys: ['postgres', 'smtp'] credentials entries with an id field: 6 | errorWorkflow in settings: False | errorWorkflow anywhere (text): False

# L2a generator check (2026-11-16T07:00:41Z UTC, IST +5:30)

Commands (from handover/demo/n8n-mainframe, PYTHONDONTWRITEBYTECODE=1), both exit 0, wrote 4 files each into handover/flows-audit/tools/scratch/{real-v5,film-v5}:
```
MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../../flows-audit/tools/scratch/real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER   -> rc=0
MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../../flows-audit/tools/scratch/film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45   -> rc=0
```

Check `git status --porcelain handover/demo` after the builds: empty output (no new or changed file in handover/demo).

## diff saved n8n-flows-real-v5/mf-form.json vs rebuilt scratch/real-v5/mf-form.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-real-v5/mf-hook.json vs rebuilt scratch/real-v5/mf-hook.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-real-v5/mf-recovery.json vs rebuilt scratch/real-v5/mf-recovery.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-real-v5/mf-sub-crm-mail.json vs rebuilt scratch/real-v5/mf-sub-crm-mail.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-film-v5/mf-form.json vs rebuilt scratch/film-v5/mf-form.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-film-v5/mf-hook.json vs rebuilt scratch/film-v5/mf-hook.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-film-v5/mf-recovery.json vs rebuilt scratch/film-v5/mf-recovery.json
```
settings equal: True
rc=0
```

## diff saved n8n-flows-film-v5/mf-sub-crm-mail.json vs rebuilt scratch/film-v5/mf-sub-crm-mail.json
```
settings equal: True
rc=0
```


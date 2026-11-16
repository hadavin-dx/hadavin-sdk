# evidence-A3b (baseline and independence; supplement to evidence-A3.md)
date UTC: 2026-11-16 07:59
target (read-only, no .git, head sha as given in the brief, not verified by me): /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/fa (cloud/flows-audit 35235ace26a516d932e73542c235875f390f333d)
Generator environment: env -i PATH=/usr/bin:/bin HOME=/nonexistent plus the MF_* variables of each README line; python /usr/bin/python3; cwd = <copy>/handover/demo/n8n-mainframe (the folder the V5-README says: 'run in the n8n-mainframe folder').
Each fresh copy: cp -r of fa, then git init + one commit 'baseline' inside the copy only.

## Step 1: BASELINE (work-base, no patch)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-base/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-base/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### Baseline rebuilt vs committed v5 JSON in fa (all 8 files)
### baseline vs committed: 0 difference row(s)
(no differences found by this comparison)

## Step 2: PRISTINE per patch (each on its own fresh copy)

### F-001 in /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f001
-- apply F-001 in work-f001
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f001) git apply -p1 -v handover/flows-audit/patches/F-001-one-ddl.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-flows/mf_leads.sql...
Applied patch handover/demo/n8n-flows/mf_leads.sql cleanly.
(no rebuild requested for this patch)

### F-002 in /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f002
-- apply F-002 in work-f002
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f002) git apply -p1 -v handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
rebuild after F-002 only:
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f002/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f002/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### F-002 rebuild vs BASELINE rebuild: 40 difference row(s)
1. n8n-flows-real-v5/mf-form.json | node only in F-002-rebuild | KeyOk
2. n8n-flows-real-v5/mf-form.json | node only in F-002-rebuild | ReplyBadKey
3. n8n-flows-real-v5/mf-form.json | node only in F-002-rebuild | ReplyStoreFail
4. n8n-flows-real-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
5. n8n-flows-real-v5/mf-form.json | connection only in F-002-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
6. n8n-flows-real-v5/mf-form.json | connection only in F-002-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
7. n8n-flows-real-v5/mf-form.json | connection only in F-002-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
8. n8n-flows-real-v5/mf-form.json | connection only in F-002-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
9. n8n-flows-real-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || F-002-rebuild="continueErrorOutput"
10. n8n-flows-real-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || F-002-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
11. n8n-flows-real-v5/mf-hook.json | node only in F-002-rebuild | KeyOk
12. n8n-flows-real-v5/mf-hook.json | node only in F-002-rebuild | ReplyBadKey
13. n8n-flows-real-v5/mf-hook.json | node only in F-002-rebuild | ReplyStoreFail
14. n8n-flows-real-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
15. n8n-flows-real-v5/mf-hook.json | connection only in F-002-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
16. n8n-flows-real-v5/mf-hook.json | connection only in F-002-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
17. n8n-flows-real-v5/mf-hook.json | connection only in F-002-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
18. n8n-flows-real-v5/mf-hook.json | connection only in F-002-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
19. n8n-flows-real-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || F-002-rebuild="continueErrorOutput"
20. n8n-flows-real-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || F-002-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
21. n8n-flows-film-v5/mf-form.json | node only in F-002-rebuild | KeyOk
22. n8n-flows-film-v5/mf-form.json | node only in F-002-rebuild | ReplyBadKey
23. n8n-flows-film-v5/mf-form.json | node only in F-002-rebuild | ReplyStoreFail
24. n8n-flows-film-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
25. n8n-flows-film-v5/mf-form.json | connection only in F-002-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
26. n8n-flows-film-v5/mf-form.json | connection only in F-002-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
27. n8n-flows-film-v5/mf-form.json | connection only in F-002-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
28. n8n-flows-film-v5/mf-form.json | connection only in F-002-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
29. n8n-flows-film-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || F-002-rebuild="continueErrorOutput"
30. n8n-flows-film-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || F-002-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
31. n8n-flows-film-v5/mf-hook.json | node only in F-002-rebuild | KeyOk
32. n8n-flows-film-v5/mf-hook.json | node only in F-002-rebuild | ReplyBadKey
33. n8n-flows-film-v5/mf-hook.json | node only in F-002-rebuild | ReplyStoreFail
34. n8n-flows-film-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
35. n8n-flows-film-v5/mf-hook.json | connection only in F-002-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
36. n8n-flows-film-v5/mf-hook.json | connection only in F-002-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
37. n8n-flows-film-v5/mf-hook.json | connection only in F-002-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
38. n8n-flows-film-v5/mf-hook.json | connection only in F-002-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
39. n8n-flows-film-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || F-002-rebuild="continueErrorOutput"
40. n8n-flows-film-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || F-002-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@

### F-003 in /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f003
-- apply F-003 in work-f003
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f003) git apply -p1 -v handover/flows-audit/patches/F-003-runsheet-claims.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/VIDEO-RUNSHEET.md...
Applied patch handover/demo/VIDEO-RUNSHEET.md cleanly.
(no rebuild requested for this patch)

### F-004 in /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f004
-- apply F-004 in work-f004
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f004) git apply -p1 -v handover/flows-audit/patches/F-004-page-statement-17.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md...
Applied patch handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md cleanly.
(no rebuild requested for this patch)

### F-008 in /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f008
-- apply F-008 in work-f008
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f008) git apply -p1 -v handover/flows-audit/patches/F-008-save-runs-for-the-take.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
rebuild after F-008 only:
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f008/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-f008/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### F-008 rebuild vs BASELINE rebuild: 16 difference row(s)
1. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
2. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
3. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
4. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
5. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
6. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
7. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
8. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
9. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
10. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
11. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
12. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
13. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
14. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
15. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || F-008-rebuild="all"
16. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || F-008-rebuild="all"

## Step 3: PAIRS (reverse order: F-008 alone, then F-002 on top)
-- apply F-008 in work-pair-f008-f002
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f008-f002) git apply -p1 -v handover/flows-audit/patches/F-008-save-runs-for-the-take.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
-- apply F-002 in work-pair-f008-f002
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f008-f002) git apply -p1 -v handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Hunk #1 succeeded at 77 (offset 1 line).
Hunk #2 succeeded at 95 (offset 1 line).
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f008-f002/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f008-f002/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### pair F-008 then F-002 vs BASELINE rebuild: 56 difference row(s)
1. n8n-flows-real-v5/mf-form.json | node only in pair-rebuild | KeyOk
2. n8n-flows-real-v5/mf-form.json | node only in pair-rebuild | ReplyBadKey
3. n8n-flows-real-v5/mf-form.json | node only in pair-rebuild | ReplyStoreFail
4. n8n-flows-real-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
5. n8n-flows-real-v5/mf-form.json | connection only in pair-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
6. n8n-flows-real-v5/mf-form.json | connection only in pair-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
7. n8n-flows-real-v5/mf-form.json | connection only in pair-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
8. n8n-flows-real-v5/mf-form.json | connection only in pair-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
9. n8n-flows-real-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || pair-rebuild="continueErrorOutput"
10. n8n-flows-real-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
11. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
12. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
13. n8n-flows-real-v5/mf-hook.json | node only in pair-rebuild | KeyOk
14. n8n-flows-real-v5/mf-hook.json | node only in pair-rebuild | ReplyBadKey
15. n8n-flows-real-v5/mf-hook.json | node only in pair-rebuild | ReplyStoreFail
16. n8n-flows-real-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
17. n8n-flows-real-v5/mf-hook.json | connection only in pair-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
18. n8n-flows-real-v5/mf-hook.json | connection only in pair-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
19. n8n-flows-real-v5/mf-hook.json | connection only in pair-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
20. n8n-flows-real-v5/mf-hook.json | connection only in pair-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
21. n8n-flows-real-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || pair-rebuild="continueErrorOutput"
22. n8n-flows-real-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
23. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
24. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
25. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
26. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
27. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
28. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
29. n8n-flows-film-v5/mf-form.json | node only in pair-rebuild | KeyOk
30. n8n-flows-film-v5/mf-form.json | node only in pair-rebuild | ReplyBadKey
31. n8n-flows-film-v5/mf-form.json | node only in pair-rebuild | ReplyStoreFail
32. n8n-flows-film-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
33. n8n-flows-film-v5/mf-form.json | connection only in pair-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
34. n8n-flows-film-v5/mf-form.json | connection only in pair-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
35. n8n-flows-film-v5/mf-form.json | connection only in pair-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
36. n8n-flows-film-v5/mf-form.json | connection only in pair-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
37. n8n-flows-film-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || pair-rebuild="continueErrorOutput"
38. n8n-flows-film-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
39. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
40. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
41. n8n-flows-film-v5/mf-hook.json | node only in pair-rebuild | KeyOk
42. n8n-flows-film-v5/mf-hook.json | node only in pair-rebuild | ReplyBadKey
43. n8n-flows-film-v5/mf-hook.json | node only in pair-rebuild | ReplyStoreFail
44. n8n-flows-film-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
45. n8n-flows-film-v5/mf-hook.json | connection only in pair-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
46. n8n-flows-film-v5/mf-hook.json | connection only in pair-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
47. n8n-flows-film-v5/mf-hook.json | connection only in pair-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
48. n8n-flows-film-v5/mf-hook.json | connection only in pair-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
49. n8n-flows-film-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || pair-rebuild="continueErrorOutput"
50. n8n-flows-film-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
51. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
52. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
53. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
54. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"
55. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-rebuild="all"
56. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-rebuild="all"

### same pair in forward order (F-002 then F-008), extra, for contrast
-- apply F-002 in work-pair-f002-f008
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f002-f008) git apply -p1 -v handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
-- apply F-008 in work-pair-f002-f008
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f002-f008) git apply -p1 -v handover/flows-audit/patches/F-008-save-runs-for-the-take.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f002-f008/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-pair-f002-f008/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### pair F-002 then F-008 vs BASELINE rebuild: 56 difference row(s)
1. n8n-flows-real-v5/mf-form.json | node only in pair-fwd-rebuild | KeyOk
2. n8n-flows-real-v5/mf-form.json | node only in pair-fwd-rebuild | ReplyBadKey
3. n8n-flows-real-v5/mf-form.json | node only in pair-fwd-rebuild | ReplyStoreFail
4. n8n-flows-real-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
5. n8n-flows-real-v5/mf-form.json | connection only in pair-fwd-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
6. n8n-flows-real-v5/mf-form.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
7. n8n-flows-real-v5/mf-form.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
8. n8n-flows-real-v5/mf-form.json | connection only in pair-fwd-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
9. n8n-flows-real-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || pair-fwd-rebuild="continueErrorOutput"
10. n8n-flows-real-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-fwd-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
11. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
12. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
13. n8n-flows-real-v5/mf-hook.json | node only in pair-fwd-rebuild | KeyOk
14. n8n-flows-real-v5/mf-hook.json | node only in pair-fwd-rebuild | ReplyBadKey
15. n8n-flows-real-v5/mf-hook.json | node only in pair-fwd-rebuild | ReplyStoreFail
16. n8n-flows-real-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
17. n8n-flows-real-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
18. n8n-flows-real-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
19. n8n-flows-real-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
20. n8n-flows-real-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
21. n8n-flows-real-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || pair-fwd-rebuild="continueErrorOutput"
22. n8n-flows-real-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-fwd-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
23. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
24. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
25. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
26. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
27. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
28. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
29. n8n-flows-film-v5/mf-form.json | node only in pair-fwd-rebuild | KeyOk
30. n8n-flows-film-v5/mf-form.json | node only in pair-fwd-rebuild | ReplyBadKey
31. n8n-flows-film-v5/mf-form.json | node only in pair-fwd-rebuild | ReplyStoreFail
32. n8n-flows-film-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
33. n8n-flows-film-v5/mf-form.json | connection only in pair-fwd-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
34. n8n-flows-film-v5/mf-form.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
35. n8n-flows-film-v5/mf-form.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
36. n8n-flows-film-v5/mf-form.json | connection only in pair-fwd-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
37. n8n-flows-film-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || pair-fwd-rebuild="continueErrorOutput"
38. n8n-flows-film-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-fwd-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
39. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
40. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
41. n8n-flows-film-v5/mf-hook.json | node only in pair-fwd-rebuild | KeyOk
42. n8n-flows-film-v5/mf-hook.json | node only in pair-fwd-rebuild | ReplyBadKey
43. n8n-flows-film-v5/mf-hook.json | node only in pair-fwd-rebuild | ReplyStoreFail
44. n8n-flows-film-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
45. n8n-flows-film-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
46. n8n-flows-film-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
47. n8n-flows-film-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
48. n8n-flows-film-v5/mf-hook.json | connection only in pair-fwd-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
49. n8n-flows-film-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || pair-fwd-rebuild="continueErrorOutput"
50. n8n-flows-film-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || pair-fwd-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
51. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
52. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
53. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
54. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
55. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"
56. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || pair-fwd-rebuild="all"

## Step 4: CUMULATIVE (F-001, F-002, F-003, F-004, F-008)
-- apply F-001 in work-cum
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum) git apply -p1 -v handover/flows-audit/patches/F-001-one-ddl.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-flows/mf_leads.sql...
Applied patch handover/demo/n8n-flows/mf_leads.sql cleanly.
-- apply F-002 in work-cum
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum) git apply -p1 -v handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
-- apply F-003 in work-cum
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum) git apply -p1 -v handover/flows-audit/patches/F-003-runsheet-claims.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/VIDEO-RUNSHEET.md...
Applied patch handover/demo/VIDEO-RUNSHEET.md cleanly.
-- apply F-004 in work-cum
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum) git apply -p1 -v handover/flows-audit/patches/F-004-page-statement-17.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md...
Applied patch handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md cleanly.
-- apply F-008 in work-cum
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum) git apply -p1 -v handover/flows-audit/patches/F-008-save-runs-for-the-take.patch
exit=0
stdout: (empty)
stderr:
Checking patch handover/demo/n8n-mainframe/build_mainframe.py...
Applied patch handover/demo/n8n-mainframe/build_mainframe.py cleanly.
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
$ (cwd=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/work-cum/handover/demo/n8n-mainframe) env -i PATH=/usr/bin:/bin HOME=/nonexistent MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 /usr/bin/python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit=0
stdout:
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json
stderr: (empty)
rebuild exit codes: [0, 0]
### cumulative vs BASELINE rebuild: 56 difference row(s)
1. n8n-flows-real-v5/mf-form.json | node only in cumulative-rebuild | KeyOk
2. n8n-flows-real-v5/mf-form.json | node only in cumulative-rebuild | ReplyBadKey
3. n8n-flows-real-v5/mf-form.json | node only in cumulative-rebuild | ReplyStoreFail
4. n8n-flows-real-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
5. n8n-flows-real-v5/mf-form.json | connection only in cumulative-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
6. n8n-flows-real-v5/mf-form.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
7. n8n-flows-real-v5/mf-form.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
8. n8n-flows-real-v5/mf-form.json | connection only in cumulative-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
9. n8n-flows-real-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || cumulative-rebuild="continueErrorOutput"
10. n8n-flows-real-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || cumulative-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
11. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
12. n8n-flows-real-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
13. n8n-flows-real-v5/mf-hook.json | node only in cumulative-rebuild | KeyOk
14. n8n-flows-real-v5/mf-hook.json | node only in cumulative-rebuild | ReplyBadKey
15. n8n-flows-real-v5/mf-hook.json | node only in cumulative-rebuild | ReplyStoreFail
16. n8n-flows-real-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
17. n8n-flows-real-v5/mf-hook.json | connection only in cumulative-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
18. n8n-flows-real-v5/mf-hook.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
19. n8n-flows-real-v5/mf-hook.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
20. n8n-flows-real-v5/mf-hook.json | connection only in cumulative-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
21. n8n-flows-real-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || cumulative-rebuild="continueErrorOutput"
22. n8n-flows-real-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || cumulative-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
23. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
24. n8n-flows-real-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
25. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
26. n8n-flows-real-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
27. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
28. n8n-flows-real-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
29. n8n-flows-film-v5/mf-form.json | node only in cumulative-rebuild | KeyOk
30. n8n-flows-film-v5/mf-form.json | node only in cumulative-rebuild | ReplyBadKey
31. n8n-flows-film-v5/mf-form.json | node only in cumulative-rebuild | ReplyStoreFail
32. n8n-flows-film-v5/mf-form.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
33. n8n-flows-film-v5/mf-form.json | connection only in cumulative-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
34. n8n-flows-film-v5/mf-form.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
35. n8n-flows-film-v5/mf-form.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
36. n8n-flows-film-v5/mf-form.json | connection only in cumulative-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
37. n8n-flows-film-v5/mf-form.json | node Claim field onError differs | baseline-rebuild=null || cumulative-rebuild="continueErrorOutput"
38. n8n-flows-film-v5/mf-form.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || cumulative-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
39. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
40. n8n-flows-film-v5/mf-form.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
41. n8n-flows-film-v5/mf-hook.json | node only in cumulative-rebuild | KeyOk
42. n8n-flows-film-v5/mf-hook.json | node only in cumulative-rebuild | ReplyBadKey
43. n8n-flows-film-v5/mf-hook.json | node only in cumulative-rebuild | ReplyStoreFail
44. n8n-flows-film-v5/mf-hook.json | connection only in baseline-rebuild | ('Valid', 'main', 0, 'Claim', 'main', 0)
45. n8n-flows-film-v5/mf-hook.json | connection only in cumulative-rebuild | ('Claim', 'main', 1, 'ReplyStoreFail', 'main', 0)
46. n8n-flows-film-v5/mf-hook.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 0, 'Claim', 'main', 0)
47. n8n-flows-film-v5/mf-hook.json | connection only in cumulative-rebuild | ('KeyOk', 'main', 1, 'ReplyBadKey', 'main', 0)
48. n8n-flows-film-v5/mf-hook.json | connection only in cumulative-rebuild | ('Valid', 'main', 0, 'KeyOk', 'main', 0)
49. n8n-flows-film-v5/mf-hook.json | node Claim field onError differs | baseline-rebuild=null || cumulative-rebuild="continueErrorOutput"
50. n8n-flows-film-v5/mf-hook.json | node Valid field parameters differs | baseline-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ $json.lead_key }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test($json.em || cumulative-rebuild={"assignments": {"assignments": [{"id": "lead_key", "name": "lead_key", "type": "string", "value": "={{ String($json.lead_key || '').trim() }}"}, {"id": "email", "name": "email", "type": "string", "value": "={{ $json.email }}"}, {"id": "name", "name": "name", "type": "string", "value": "={{ $json.name }}"}, {"id": "valid", "name": "valid", "type": "boolean", "value": "={{ /^[^@\\s]+@[^@\\s]+\\.[^@
51. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
52. n8n-flows-film-v5/mf-hook.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
53. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
54. n8n-flows-film-v5/mf-recovery.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
55. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataErrorExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"
56. n8n-flows-film-v5/mf-sub-crm-mail.json | top-level settings.saveDataSuccessExecution differs | baseline-rebuild="none" || cumulative-rebuild="all"

## Step 5: F-001 mf_leads.sql
### git diff of mf_leads.sql in work-f001 (changed lines)
diff --git a/handover/demo/n8n-flows/mf_leads.sql b/handover/demo/n8n-flows/mf_leads.sql
index 752c64e..d655b3a 100644
--- a/handover/demo/n8n-flows/mf_leads.sql
+++ b/handover/demo/n8n-flows/mf_leads.sql
@@ -1 +1,2 @@
--- NOTE: this table matches the CURRENT flows (mf-*.json in this folder, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
+-- NOTE (current table, four alert columns at the end): matches the flows used in the take (n8n-flows-real-v5, n8n-flows-film-v5) and the older v3 and v4 flows. The flows in this folder (v2) ignore the extra columns, so this table also runs them (until they are archived, CUT-LIST.md). A table that already exists without the alert columns needs: ALTER TABLE mf_leads ADD COLUMN alert_sent boolean NOT NULL DEFAULT false, ADD COLUMN alert_token text, ADD COLUMN alert_until timestamptz, ADD COLUMN alert_attempts int NOT NULL DEFAULT 0;
+-- OLDER NOTE: this table matches the flows in this folder (mf-*.json, v2). They store no label column: the label only travels inside the run (stage answer -> CRM). The OLD flows in v1-superseded/ read and write a label column and need the v1 table (same DDL plus: label text); do not mix the two sets.
@@ -14 +15,6 @@ CREATE TABLE mf_leads(
-  updated_at    timestamptz NOT NULL DEFAULT now());
+  updated_at    timestamptz NOT NULL DEFAULT now(),
+  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x min(attempts, 5) in the v5 flows).
+  alert_sent    boolean NOT NULL DEFAULT false,
+  alert_token   text,
+  alert_until   timestamptz,
+  alert_attempts int NOT NULL DEFAULT 0);
### other files in fa mentioning names touched by F-001 (patch only adds columns alert_sent, alert_token, alert_until, alert_attempts and a NOTE; it renames or adds NO constraint or index; the only existing named object in the DDL is the PRIMARY KEY on lead_key, unnamed)
- pattern 'alert_attempts' (grep -rIl under handover/demo and handover/flows-audit): 56 file(s)
    handover/demo/n8n-flows-v4/mf_leads.sql
    handover/demo/n8n-flows-v4/mf-recovery.json
    handover/demo/n8n-flows-v4/V4-README.md
    handover/demo/n8n-flows-film-v5/mf-recovery.json
    handover/demo/n8n-table-screen-v2/README.md
    handover/demo/n8n-flows-real-v4/mf-recovery.json
    handover/demo/n8n-flows/DESIGN-A-README.md
    handover/demo/n8n-flows/N8N-START.md
    handover/demo/n8n-flows/PAGE-STATEMENTS-DRAFT.md
    handover/demo/VIDEO-RUNSHEET.md
    handover/demo/n8n-flows-film-v4/mf-recovery.json
    handover/demo/n8n-flows-v3/V3-README.md
    handover/demo/n8n-flows-v3/mf_leads.sql
    handover/demo/n8n-flows-v3/mf-recovery.json
    handover/demo/AUDIT-PAGE-STATEMENTS-V4.md
    handover/demo/n8n-flows-real-v5/mf-recovery.json
    handover/demo/REPORT.md
    handover/demo/n8n-flows-film-v3/mf-recovery.json
    handover/demo/n8n-table-screen/README.md
    handover/demo/n8n-table-screen/mf-table-screen.json
    handover/demo/n8n-flows-real-v3/mf-recovery.json
    handover/demo/n8n-mainframe/build_mainframe.py
    handover/demo/n8n-mainframe/mf.py
    handover/flows-audit/evidence-2.md
    handover/flows-audit/lanes/L2b-3-plain.header.md
    handover/flows-audit/lanes/L2b-3-plain.findings.md
    handover/flows-audit/lanes/L2b-2-film.header.md
    handover/flows-audit/lanes/L2b-3-plain.md
    handover/flows-audit/lanes/L3-claims.md
    handover/flows-audit/lanes/L1.findings.md
    handover/flows-audit/lanes/L3.findings.md
    handover/flows-audit/lanes/L1.judge.jsonl
    handover/flows-audit/lanes/L1.md
    handover/flows-audit/lanes/L2b-2-film.md
    handover/flows-audit/lanes/L2b-1-real.md
    handover/flows-audit/lanes/L2b-1-real.judge.jsonl
    handover/flows-audit/lanes/L2b-2-film.judge.jsonl
    handover/flows-audit/lanes/L2b-3-plain.judge.jsonl
    handover/flows-audit/FINDINGS.md
    handover/flows-audit/FLOWS-AUDIT.md
    handover/flows-audit/tools/out/diff__n8n-table-screen__mf-table-screen__TO__n8n-table-screen-v2__mf-table-screen-v2.txt
    handover/flows-audit/tools/out/n8n-flows-film-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v3__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-real-v3__mf-recovery__TO__n8n-flows-real-v4__mf-recovery.txt
    handover/flows-audit/tools/out/diff__n8n-table-screen__TO__n8n-table-screen-v2.txt
    handover/flows-audit/tools/out/n8n-flows-film-v4__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-film-v5__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v5__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-v3__mf-recovery__TO__n8n-flows-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-v4__mf-recovery.md
    handover/flows-audit/tools/out/n8n-table-screen__mf-table-screen.md
    handover/flows-audit/tools/out/diff__n8n-flows-film-v3__mf-recovery__TO__n8n-flows-film-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-real-v4__mf-recovery.md
    handover/flows-audit/patches/F-003-runsheet-claims.patch
    handover/flows-audit/patches/F-001-one-ddl.patch
- pattern 'alert_until' (grep -rIl under handover/demo and handover/flows-audit): 46 file(s)
    handover/demo/n8n-flows-v4/mf_leads.sql
    handover/demo/n8n-flows-v4/mf-recovery.json
    handover/demo/n8n-flows-v4/V4-README.md
    handover/demo/n8n-flows-film-v5/mf-recovery.json
    handover/demo/n8n-flows-real-v4/mf-recovery.json
    handover/demo/n8n-flows/DESIGN-A-README.md
    handover/demo/n8n-flows/N8N-START.md
    handover/demo/n8n-flows-film-v4/mf-recovery.json
    handover/demo/n8n-flows-v3/V3-README.md
    handover/demo/n8n-flows-v3/mf_leads.sql
    handover/demo/n8n-flows-v3/mf-recovery.json
    handover/demo/n8n-flows-real-v5/mf-recovery.json
    handover/demo/REPORT.md
    handover/demo/n8n-flows-film-v3/mf-recovery.json
    handover/demo/n8n-flows-real-v3/mf-recovery.json
    handover/demo/n8n-mainframe/build_mainframe.py
    handover/demo/n8n-mainframe/mf.py
    handover/flows-audit/evidence-2.md
    handover/flows-audit/reviews/result-r1-codebase.md
    handover/flows-audit/lanes/L2b-3-plain.header.md
    handover/flows-audit/lanes/L2b-3-plain.findings.md
    handover/flows-audit/lanes/L2b-2-film.header.md
    handover/flows-audit/lanes/L2b-3-plain.md
    handover/flows-audit/lanes/L3-claims.md
    handover/flows-audit/lanes/L1.findings.md
    handover/flows-audit/lanes/L3.findings.md
    handover/flows-audit/lanes/L1.judge.jsonl
    handover/flows-audit/lanes/L1.md
    handover/flows-audit/lanes/L2b-2-film.md
    handover/flows-audit/lanes/L2b-1-real.md
    handover/flows-audit/lanes/L2b-1-real.judge.jsonl
    handover/flows-audit/lanes/L2b-2-film.judge.jsonl
    handover/flows-audit/lanes/L2b-3-plain.judge.jsonl
    handover/flows-audit/FLOWS-AUDIT.md
    handover/flows-audit/tools/out/n8n-flows-film-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v3__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-real-v3__mf-recovery__TO__n8n-flows-real-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-film-v4__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-film-v5__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v5__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-v3__mf-recovery__TO__n8n-flows-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-v4__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-film-v3__mf-recovery__TO__n8n-flows-film-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-real-v4__mf-recovery.md
    handover/flows-audit/patches/F-001-one-ddl.patch
- pattern 'alert_token' (grep -rIl under handover/demo and handover/flows-audit): 44 file(s)
    handover/demo/n8n-flows-v4/mf_leads.sql
    handover/demo/n8n-flows-v4/mf-recovery.json
    handover/demo/n8n-flows-film-v5/mf-recovery.json
    handover/demo/n8n-flows-real-v4/mf-recovery.json
    handover/demo/n8n-flows/DESIGN-A-README.md
    handover/demo/n8n-flows/N8N-START.md
    handover/demo/n8n-flows-film-v4/mf-recovery.json
    handover/demo/n8n-flows-v3/V3-README.md
    handover/demo/n8n-flows-v3/mf_leads.sql
    handover/demo/n8n-flows-v3/mf-recovery.json
    handover/demo/n8n-flows-real-v5/mf-recovery.json
    handover/demo/REPORT.md
    handover/demo/n8n-flows-film-v3/mf-recovery.json
    handover/demo/n8n-flows-real-v3/mf-recovery.json
    handover/demo/n8n-mainframe/build_mainframe.py
    handover/demo/n8n-mainframe/mf.py
    handover/flows-audit/evidence-2.md
    handover/flows-audit/lanes/L2b-3-plain.header.md
    handover/flows-audit/lanes/L2b-3-plain.findings.md
    handover/flows-audit/lanes/L2b-2-film.header.md
    handover/flows-audit/lanes/L2b-3-plain.md
    handover/flows-audit/lanes/L1.findings.md
    handover/flows-audit/lanes/L3.findings.md
    handover/flows-audit/lanes/L1.judge.jsonl
    handover/flows-audit/lanes/L1.md
    handover/flows-audit/lanes/L2b-2-film.md
    handover/flows-audit/lanes/L2b-1-real.findings.md
    handover/flows-audit/lanes/L2b-1-real.md
    handover/flows-audit/lanes/L2b-1-real.judge.jsonl
    handover/flows-audit/lanes/L2b-2-film.judge.jsonl
    handover/flows-audit/lanes/L2b-3-plain.judge.jsonl
    handover/flows-audit/FLOWS-AUDIT.md
    handover/flows-audit/tools/out/n8n-flows-film-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v3__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-real-v3__mf-recovery__TO__n8n-flows-real-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-film-v4__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-film-v5__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v5__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-v3__mf-recovery__TO__n8n-flows-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-v4__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-film-v3__mf-recovery__TO__n8n-flows-film-v4__mf-recovery.txt
    handover/flows-audit/tools/out/n8n-flows-real-v4__mf-recovery.md
    handover/flows-audit/patches/F-001-one-ddl.patch
- pattern 'alert_sent' (grep -rIl under handover/demo and handover/flows-audit): 67 file(s)
    handover/demo/n8n-flows-v4/mf_leads.sql
    handover/demo/n8n-flows-v4/mf-recovery.json
    handover/demo/n8n-flows-v4/V4-README.md
    handover/demo/n8n-flows-film-v5/mf-recovery.json
    handover/demo/n8n-table-screen-v2/mf-table-screen-v2.json
    handover/demo/n8n-table-screen-v2/README.md
    handover/demo/n8n-flows-real-v4/mf-recovery.json
    handover/demo/n8n-flows/DESIGN-A-README.md
    handover/demo/n8n-flows/N8N-START.md
    handover/demo/n8n-flows/PAGE-STATEMENTS-DRAFT.md
    handover/demo/VIDEO-RUNSHEET.md
    handover/demo/PLAN-4-NLITE-FROM-LEAD.md
    handover/demo/n8n-flows-film-v4/mf-recovery.json
    handover/demo/n8n-flows-v3/V3-README.md
    handover/demo/n8n-flows-v3/mf_leads.sql
    handover/demo/n8n-flows-v3/mf-recovery.json
    handover/demo/n8n-flows-real-v5/mf-recovery.json
    handover/demo/DOUBTFUL-SCENE.md
    handover/demo/AUDIT-VIDEO-RUNSHEET.md
    handover/demo/REPORT.md
    handover/demo/n8n-flows-film-v3/mf-recovery.json
    handover/demo/n8n-table-screen/README.md
    handover/demo/n8n-table-screen/mf-table-screen.json
    handover/demo/n8n-flows-real-v3/mf-recovery.json
    handover/demo/n8n-mainframe/build_mainframe.py
    handover/demo/n8n-mainframe/mf.py
    handover/flows-audit/evidence-2.md
    handover/flows-audit/FIX-PLAN.md
    handover/flows-audit/lanes/L2b-3-plain.header.md
    handover/flows-audit/lanes/L2b-3-plain.findings.md
    handover/flows-audit/lanes/L2b-2-film.header.md
    handover/flows-audit/lanes/L2a.findings.md
    handover/flows-audit/lanes/L2b-3-plain.md
    handover/flows-audit/lanes/L3-stores.md
    handover/flows-audit/lanes/L3-claims.md
    handover/flows-audit/lanes/L1.findings.md
    handover/flows-audit/lanes/L2a.judge.jsonl
    handover/flows-audit/lanes/L3.findings.md
    handover/flows-audit/lanes/L1.judge.jsonl
    handover/flows-audit/lanes/L1.md
    handover/flows-audit/lanes/L2b-2-film.findings.md
    handover/flows-audit/lanes/L2b-2-film.md
    handover/flows-audit/lanes/L2a.md
    handover/flows-audit/lanes/L2b-1-real.findings.md
    handover/flows-audit/lanes/L2b-1-real.md
    handover/flows-audit/lanes/L2b-1-real.judge.jsonl
    handover/flows-audit/lanes/L2b-2-film.judge.jsonl
    handover/flows-audit/lanes/L2b-3-plain.judge.jsonl
    handover/flows-audit/FINDINGS.md
    handover/flows-audit/FLOWS-AUDIT.md
    handover/flows-audit/tools/out/diff__n8n-table-screen__mf-table-screen__TO__n8n-table-screen-v2__mf-table-screen-v2.txt
    handover/flows-audit/tools/out/n8n-flows-film-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v3__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-real-v3__mf-recovery__TO__n8n-flows-real-v4__mf-recovery.txt
    handover/flows-audit/tools/out/diff__n8n-table-screen__TO__n8n-table-screen-v2.txt
    handover/flows-audit/tools/out/n8n-flows-film-v4__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-film-v5__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-v3__mf-recovery.md
    handover/flows-audit/tools/out/n8n-flows-real-v5__mf-recovery.md
    handover/flows-audit/tools/out/diff__n8n-flows-v3__mf-recovery__TO__n8n-flows-v4__mf-recovery.txt
    ... 7 more
- pattern 'mf_leads_pkey' (grep -rIl under handover/demo and handover/flows-audit): 0 file(s)
- pattern 'CREATE INDEX' (grep -rIl under handover/demo and handover/flows-audit): 0 file(s)
- pattern 'CONSTRAINT' (grep -rIl under handover/demo and handover/flows-audit): 0 file(s)
### mf_leads.sql in fa: lines with CREATE/INDEX/CONSTRAINT/UNIQUE/PRIMARY
3:CREATE TABLE mf_leads(
4:  lead_key      text PRIMARY KEY,

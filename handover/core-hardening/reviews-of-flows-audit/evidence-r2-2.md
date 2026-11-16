# E2 rebuild and compare (raw)
Note: F-003 (VIDEO-RUNSHEET.md absent from tree) does not apply, so the 'full apply' copy has F-001,F-002,F-004,F-008 only. The generator is changed by F-002 and F-008.
Script: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/r2-check.py (run: python3 -I r2-check.py <r2 dir>). Heuristic: trigger = node type containing 'trigger' or ending '.webhook' (respondToWebhook is NOT a trigger).

## rebuild commands (run in work-new/handover/demo/n8n-mainframe, output to temp dirs; commands copied from the two V5-README.md files)
MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 -I build_mainframe.py $S/r2/rebuilt-real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER  -> exit 0, 4 files written
MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 -I build_mainframe.py $S/r2/rebuilt-film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45  -> exit 0, 4 files written
## extra: same commands with the UNPATCHED generator (new/), byte compare with committed JSON
byte-identical real mf-form
byte-identical real mf-hook
byte-identical real mf-recovery
byte-identical real mf-sub-crm-mail
byte-identical film mf-form
byte-identical film mf-hook
byte-identical film mf-recovery
byte-identical film mf-sub-crm-mail
## byte compare committed vs rebuilt with PATCHED generator
DIFFERENT real mf-form
DIFFERENT real mf-hook
byte-identical real mf-recovery
DIFFERENT real mf-sub-crm-mail
DIFFERENT film mf-form
DIFFERENT film mf-hook
byte-identical film mf-recovery
DIFFERENT film mf-sub-crm-mail

## r2-check.py output verbatim
=== BASELINE (a)(c)(e) on committed JSON, no patch ===
real-v5/mf-form.json json.load=OK
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
real-v5/mf-hook.json json.load=OK
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
real-v5/mf-recovery.json json.load=OK
  [committed] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
real-v5/mf-sub-crm-mail.json json.load=OK
  [committed] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True
film-v5/mf-form.json json.load=OK
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
film-v5/mf-hook.json json.load=OK
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
film-v5/mf-recovery.json json.load=OK
  [committed] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
film-v5/mf-sub-crm-mail.json json.load=OK
  [committed] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True

=== COMMITTED vs REBUILT (patched generator, all patches except F-003 which does not apply) ===
--- real-v5/mf-form.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
  [rebuilt  ] nodes=15 connections=14 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Claim:idx1_wired=True
  (b) nodes added in rebuilt: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail'] ; removed: []
  (d) connection count committed=11 rebuilt=14 ; edges only in committed=[('Valid', 'main', 0, 'Claim', 0)] ; only in rebuilt=[('Claim', 'main', 1, 'ReplyStoreFail', 0), ('KeyOk', 'main', 0, 'Claim', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 0), ('Valid', 'main', 0, 'KeyOk', 0)]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: ['Valid', 'Claim']
--- real-v5/mf-hook.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
  [rebuilt  ] nodes=15 connections=14 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Claim:idx1_wired=True
  (b) nodes added in rebuilt: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail'] ; removed: []
  (d) connection count committed=11 rebuilt=14 ; edges only in committed=[('Valid', 'main', 0, 'Claim', 0)] ; only in rebuilt=[('Claim', 'main', 1, 'ReplyStoreFail', 0), ('KeyOk', 'main', 0, 'Claim', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 0), ('Valid', 'main', 0, 'KeyOk', 0)]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: ['Valid', 'Claim']
--- real-v5/mf-recovery.json  (a) committed load=OK  rebuilt load=OK  byte-identical=True
  [committed] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
  [rebuilt  ] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
  (b) nodes added in rebuilt: [] ; removed: []
  (d) connection count committed=9 rebuilt=9 ; edges only in committed=[] ; only in rebuilt=[]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}  keys_changed=[]
  nodes present in both whose JSON differs: []
--- real-v5/mf-sub-crm-mail.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True
  [rebuilt  ] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True
  (b) nodes added in rebuilt: [] ; removed: []
  (d) connection count committed=26 rebuilt=26 ; edges only in committed=[] ; only in rebuilt=[]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: []
--- film-v5/mf-form.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
  [rebuilt  ] nodes=15 connections=14 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Claim:idx1_wired=True
  (b) nodes added in rebuilt: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail'] ; removed: []
  (d) connection count committed=11 rebuilt=14 ; edges only in committed=[('Valid', 'main', 0, 'Claim', 0)] ; only in rebuilt=[('Claim', 'main', 1, 'ReplyStoreFail', 0), ('KeyOk', 'main', 0, 'Claim', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 0), ('Valid', 'main', 0, 'KeyOk', 0)]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: ['Valid', 'Claim']
--- film-v5/mf-hook.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=12 connections=11 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: none
  [rebuilt  ] nodes=15 connections=14 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Claim:idx1_wired=True
  (b) nodes added in rebuilt: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail'] ; removed: []
  (d) connection count committed=11 rebuilt=14 ; edges only in committed=[('Valid', 'main', 0, 'Claim', 0)] ; only in rebuilt=[('Claim', 'main', 1, 'ReplyStoreFail', 0), ('KeyOk', 'main', 0, 'Claim', 0), ('KeyOk', 'main', 1, 'ReplyBadKey', 0), ('Valid', 'main', 0, 'KeyOk', 0)]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: ['Valid', 'Claim']
--- film-v5/mf-recovery.json  (a) committed load=OK  rebuilt load=OK  byte-identical=True
  [committed] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
  [rebuilt  ] nodes=10 connections=9 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: AlertSend:idx1_wired=True
  (b) nodes added in rebuilt: [] ; removed: []
  (d) connection count committed=9 rebuilt=9 ; edges only in committed=[] ; only in rebuilt=[]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}  keys_changed=[]
  nodes present in both whose JSON differs: []
--- film-v5/mf-sub-crm-mail.json  (a) committed load=OK  rebuilt load=OK  byte-identical=False
  [committed] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [committed] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [committed] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True
  [rebuilt  ] nodes=20 connections=26 dup_names=[] bad_source_keys=[] bad_targets=[]
  [rebuilt  ] isolated_non_trigger(no in, no out)=[] ; non_trigger_without_incoming=[] ; trigger_without_outgoing=[]
  [rebuilt  ] onError=continueErrorOutput nodes: Qualify:idx1_wired=True, CrmUpsert:idx1_wired=True, SendMail:idx1_wired=True
  (b) nodes added in rebuilt: [] ; removed: []
  (d) connection count committed=26 rebuilt=26 ; edges only in committed=[] ; only in rebuilt=[]
  (f) settings committed={"executionOrder": "v1", "saveDataErrorExecution": "none", "saveDataSuccessExecution": "none", "saveManualExecutions": false}
  (f) settings rebuilt  ={"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all", "saveManualExecutions": false}  keys_changed=['saveDataErrorExecution', 'saveDataSuccessExecution']
  nodes present in both whose JSON differs: []

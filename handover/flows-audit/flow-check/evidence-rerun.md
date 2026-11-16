# Evidence rerun (EVIDENCE RUNNER, raw output, no judgement)
Written: Mon Nov 16 09:21:37 UTC 2026
Scratch copy: /tmp/evr1 (fill_flows, flow-check, patch-apply, patches, demo n8n-flows*, n8n-mainframe, VIDEO-RUNSHEET.md). AWS_* unset. Each command under timeout 240.
Note: the first two commands in this file are in run order; the first selftest attempt failed with FileNotFoundError (/tmp/evr1/fc/g/real did not exist yet, run_all.sh had not run); that failed output was not saved. The old checker run WITHOUT --baseline exits 1 (2 FAIL per pristine dir, IF nodes StuckRow/AlertRow lack output 1); with --baseline as run_all.sh uses, exit 0.

### $ timeout 240 python3 -I -m unittest
Mon Nov 16 09:21:14 UTC 2026
....................................................................
----------------------------------------------------------------------
Ran 68 tests in 5.988s

OK
EXIT=0
### $ timeout 240 python3 -I selftest.py ../../demo/n8n-flows-real-v5 /tmp/evr1/fc/g/real
Mon Nov 16 09:21:21 UTC 2026
control_unmutated                              exit=0 expected 0   as expected
control_sticky_note_present_and_unlinked       exit=0 expected 0   as expected
control_aws_example_key_allowed                exit=0 expected 0   as expected
control_self_reference_is_warn_only            exit=0 expected 0   as expected
orphan_reply                                   exit=1 expected 1   named_line_present=True as expected
cycle_only                                     exit=1 expected 1   named_line_present=True as expected
dangling                                       exit=1 expected 1   named_line_present=True as expected
duplicate_name                                 exit=1 expected 1   named_line_present=True as expected
name_case_dup                                  exit=1 expected 1   named_line_present=True as expected
duplicate_id                                   exit=1 expected 1   named_line_present=True as expected
trigger_has_input                              exit=1 expected 1   named_line_present=True as expected
no_trigger                                     exit=1 expected 1   named_line_present=True as expected
if_one_branch                                  exit=1 expected 1   named_line_present=True as expected
switch_gap                                     exit=1 expected 1   named_line_present=True as expected
errout_unwired                                 exit=1 expected 1   named_line_present=True as expected
bad_onerror_value                              exit=1 expected 1   named_line_present=True as expected
bad_maxtries                                   exit=1 expected 1   named_line_present=True as expected
bad_retry_type                                 exit=1 expected 1   named_line_present=True as expected
bad_alwaysoutput_type                          exit=1 expected 1   named_line_present=True as expected
bad_ref                                        exit=1 expected 1   named_line_present=True as expected
bad_items_ref                                  exit=1 expected 1   named_line_present=True as expected
bad_node_dot_ref                               exit=1 expected 1   named_line_present=True as expected
secret_sk                                      exit=1 expected 1   named_line_present=True as expected
secret_aws                                     exit=1 expected 1   named_line_present=True as expected
secret_under_key                               exit=1 expected 1   named_line_present=True as expected
cred_block_missing                             exit=1 expected 1   named_line_present=True as expected
cred_name_empty                                exit=1 expected 1   named_line_present=True as expected
cred_id_missing                                exit=1 expected 1   named_line_present=True as expected
webhook_path_no_reply                          exit=1 expected 1   named_line_present=True as expected
webhook_dead_branch                            exit=1 expected 1   named_line_present=True as expected
webhook_no_reply_node                          exit=1 expected 1   named_line_present=True as expected
sticky_only_file                               exit=1 expected 1   named_line_present=True as expected
missing_position                               exit=1 expected 1   named_line_present=True as expected
count_wrong                                    exit=1 expected 1   named_line_present=True as expected
duplicate_webhook_path                         exit=1 expected 1   named_line_present=True as expected
parse_fail                                     exit=1 expected 1   named_line_present=True as expected
missing_file                                   exit=1 expected 1   named_line_present=True as expected
webhook_auth_required                          exit=1 expected 1   named_line_present=True as expected
Traceback (most recent call last):
  File "/tmp/evr1/handover/flows-audit/flow-check/selftest.py", line 115, in <module>
    sys.exit(main())
             ~~~~^^
  File "/tmp/evr1/handover/flows-audit/flow-check/selftest.py", line 111, in main
    d = make(name, mut, work, PATCHED); rc, out = run(pcmd(d), name, None); good = rc == want and text in out
  File "/tmp/evr1/handover/flows-audit/flow-check/selftest.py", line 88, in make
    d = "%s/%s" % (work, name); shutil.copytree(src, d)
                                ~~~~~~~~~~~~~~~^^^^^^^^
  File "/usr/local/lib/python3.13/shutil.py", line 591, in copytree
    with os.scandir(src) as itr:
         ~~~~~~~~~~^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/evr1/fc/g/real'
EXIT=1
### $ timeout 240 bash run_all.sh /tmp/evr1/fc
Mon Nov 16 09:21:27 UTC 2026
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
pristine process done
patched process done
RESULT: 0 FAIL, 12 WARN
exit=0
RESULT: 0 FAIL, 12 WARN
exit=0
RESULT: 0 FAIL, 14 WARN
exit=0
RESULT: 0 FAIL, 14 WARN
exit=0
EXIT=0
### $ timeout 240 python3 -I selftest.py ../../demo/n8n-flows-real-v5 /tmp/evr1/fc/g/real
Mon Nov 16 09:21:27 UTC 2026
control_unmutated                              exit=0 expected 0   as expected
control_sticky_note_present_and_unlinked       exit=0 expected 0   as expected
control_aws_example_key_allowed                exit=0 expected 0   as expected
control_self_reference_is_warn_only            exit=0 expected 0   as expected
orphan_reply                                   exit=1 expected 1   named_line_present=True as expected
cycle_only                                     exit=1 expected 1   named_line_present=True as expected
dangling                                       exit=1 expected 1   named_line_present=True as expected
duplicate_name                                 exit=1 expected 1   named_line_present=True as expected
name_case_dup                                  exit=1 expected 1   named_line_present=True as expected
duplicate_id                                   exit=1 expected 1   named_line_present=True as expected
trigger_has_input                              exit=1 expected 1   named_line_present=True as expected
no_trigger                                     exit=1 expected 1   named_line_present=True as expected
if_one_branch                                  exit=1 expected 1   named_line_present=True as expected
switch_gap                                     exit=1 expected 1   named_line_present=True as expected
errout_unwired                                 exit=1 expected 1   named_line_present=True as expected
bad_onerror_value                              exit=1 expected 1   named_line_present=True as expected
bad_maxtries                                   exit=1 expected 1   named_line_present=True as expected
bad_retry_type                                 exit=1 expected 1   named_line_present=True as expected
bad_alwaysoutput_type                          exit=1 expected 1   named_line_present=True as expected
bad_ref                                        exit=1 expected 1   named_line_present=True as expected
bad_items_ref                                  exit=1 expected 1   named_line_present=True as expected
bad_node_dot_ref                               exit=1 expected 1   named_line_present=True as expected
secret_sk                                      exit=1 expected 1   named_line_present=True as expected
secret_aws                                     exit=1 expected 1   named_line_present=True as expected
secret_under_key                               exit=1 expected 1   named_line_present=True as expected
cred_block_missing                             exit=1 expected 1   named_line_present=True as expected
cred_name_empty                                exit=1 expected 1   named_line_present=True as expected
cred_id_missing                                exit=1 expected 1   named_line_present=True as expected
webhook_path_no_reply                          exit=1 expected 1   named_line_present=True as expected
webhook_dead_branch                            exit=1 expected 1   named_line_present=True as expected
webhook_no_reply_node                          exit=1 expected 1   named_line_present=True as expected
sticky_only_file                               exit=1 expected 1   named_line_present=True as expected
missing_position                               exit=1 expected 1   named_line_present=True as expected
count_wrong                                    exit=1 expected 1   named_line_present=True as expected
duplicate_webhook_path                         exit=1 expected 1   named_line_present=True as expected
parse_fail                                     exit=1 expected 1   named_line_present=True as expected
missing_file                                   exit=1 expected 1   named_line_present=True as expected
webhook_auth_required                          exit=1 expected 1   named_line_present=True as expected
patched_control                                exit=0 expected 0   named_line_present=True as expected
patched_wrong_code                             exit=1 expected 1   named_line_present=True as expected
patched_failreply_cut                          exit=1 expected 1   named_line_present=True as expected
patched_errlink_cut                            exit=1 expected 1   named_line_present=True as expected
patched_badkey_reply_cut                       exit=1 expected 1   named_line_present=True as expected
SELFTEST: 43 as expected, 0 not as expected (34 negative cases + 4 controls on pristine, 4 negatives + 1 control on patched)
EXIT=0
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/handover/demo/n8n-flows-real-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info
Mon Nov 16 09:21:29 UTC 2026
### /tmp/evr1/handover/demo/n8n-flows-real-v5
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
FAIL /tmp/evr1/handover/demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1]
FAIL /tmp/evr1/handover/demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1]
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none
RESULT: 2 FAIL, 0 WARN
EXIT=1
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/handover/demo/n8n-flows-film-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info
Mon Nov 16 09:21:29 UTC 2026
### /tmp/evr1/handover/demo/n8n-flows-film-v5
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
FAIL /tmp/evr1/handover/demo/n8n-flows-film-v5/mf-recovery.json IF node StuckRow lacks output(s) [1]
FAIL /tmp/evr1/handover/demo/n8n-flows-film-v5/mf-recovery.json IF node AlertRow lacks output(s) [1]
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none
RESULT: 2 FAIL, 0 WARN
EXIT=1
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/fc/g/real /tmp/evr1/fc/g/film --expect mf-form.json=15:14 --expect mf-hook.json=15:14 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --patch-checks F002,F008 --quiet-info
Mon Nov 16 09:21:29 UTC 2026
### /tmp/evr1/fc/g/real
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/real/mf-form.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/real/mf-hook.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
FAIL /tmp/evr1/fc/g/real/mf-recovery.json IF node StuckRow lacks output(s) [1]
FAIL /tmp/evr1/fc/g/real/mf-recovery.json IF node AlertRow lacks output(s) [1]
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all
### /tmp/evr1/fc/g/film
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/film/mf-form.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/film/mf-hook.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
FAIL /tmp/evr1/fc/g/film/mf-recovery.json IF node StuckRow lacks output(s) [1]
FAIL /tmp/evr1/fc/g/film/mf-recovery.json IF node AlertRow lacks output(s) [1]
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all
RESULT: 4 FAIL, 4 WARN
EXIT=1
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/handover/demo/n8n-flows-real-v5 --baseline /tmp/evr1/handover/demo/n8n-flows-real-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info
Mon Nov 16 09:21:33 UTC 2026
### /tmp/evr1/handover/demo/n8n-flows-real-v5
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
WARN /tmp/evr1/handover/demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same)
WARN /tmp/evr1/handover/demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none
RESULT: 0 FAIL, 2 WARN
EXIT=0
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/handover/demo/n8n-flows-film-v5 --baseline /tmp/evr1/handover/demo/n8n-flows-film-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info
Mon Nov 16 09:21:33 UTC 2026
### /tmp/evr1/handover/demo/n8n-flows-film-v5
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none
WARN /tmp/evr1/handover/demo/n8n-flows-film-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same)
WARN /tmp/evr1/handover/demo/n8n-flows-film-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none
RESULT: 0 FAIL, 2 WARN
EXIT=0
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/fc/g/real --baseline /tmp/evr1/handover/demo/n8n-flows-real-v5 --expect mf-form.json=15:14 --expect mf-hook.json=15:14 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --patch-checks F002,F008 --quiet-info
Mon Nov 16 09:21:33 UTC 2026
### /tmp/evr1/fc/g/real
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/real/mf-form.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/real/mf-hook.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN /tmp/evr1/fc/g/real/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same)
WARN /tmp/evr1/fc/g/real/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all
RESULT: 0 FAIL, 4 WARN
EXIT=0
### $ timeout 240 python3 -I check_flows.py /tmp/evr1/fc/g/film --baseline /tmp/evr1/handover/demo/n8n-flows-film-v5 --expect mf-form.json=15:14 --expect mf-hook.json=15:14 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --patch-checks F002,F008 --quiet-info
Mon Nov 16 09:21:33 UTC 2026
### /tmp/evr1/fc/g/film
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/film/mf-form.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/evr1/fc/g/film/mf-hook.json F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 letters, digits, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').item.json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN /tmp/evr1/fc/g/film/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same)
WARN /tmp/evr1/fc/g/film/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all
RESULT: 0 FAIL, 4 WARN
EXIT=0

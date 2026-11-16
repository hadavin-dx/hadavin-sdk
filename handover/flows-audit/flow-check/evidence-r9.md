# evidence-r9 (EVIDENCE RUNNER, run only, no judgement). Date 2026-11-16. Work copy: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/ev (repo untouched except this file).

Note: a first copy dir (scratchpad/ev-f8r9) was deleted by something else mid-run; everything was re-run from scratch in ev-f8r9-run2; only that run is recorded.

## raw: out/1.txt
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 6 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 23 WARN
Known open problems: 17
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
[pristine-strict]
######## pristine-strict real
RESULT: 4 FAIL, 19 WARN
Known open problems: 13
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 18 WARN
Known open problems: 12
exit=1
[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)
RESULT: 2 FAIL, 23 WARN
exit=1
==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ====
[pristine-film]
######## pristine film
RESULT: 0 FAIL, 21 WARN
Known open problems: 15
exit=0
[patched-film]
######## patched film
RESULT: 0 FAIL, 20 WARN
Known open problems: 14
exit=0
[pristine-strict-film]
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 673 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
rc=0
```

## raw: out/2.txt
```
control_unmutated@real-mf-form.json (exit 0, no FAIL, closing block)     as expected
control_unmutated@real-mf-hook.json (exit 0, no FAIL, closing block)     as expected
control_unmutated@real-mf-recovery.json (exit 0, no FAIL, closing block) as expected
control_unmutated@real-mf-sub-crm-mail.json (exit 0, no FAIL, closing block) as expected
control_sticky_note_present_and_unlinked@real-mf-form.json (exit 0, no FAIL) as expected
control_aws_example_key_allowed@real-mf-form.json (exit 0, no FAIL)      as expected
control_pass_through_key_is_not_a_secret@real-mf-form.json (exit 0, no FAIL) as expected
control_env_reference_is_not_a_secret@real-mf-form.json (exit 0, no FAIL) as expected
control_filter_with_one_output@real-mf-form.json (exit 0, no FAIL)       as expected
control_webhook_auth_with_credentials@real-mf-form.json (exit 0, no FAIL) as expected
control_sticky_note_text_may_quote_a_node_name@real-mf-form.json (exit 0, no FAIL) as expected
control_credential_names_as_expected@real-mf-form.json (exit 0, no FAIL) as expected
control_webhook_auth_jwt_with_credentials@real-mf-form.json (exit 0, no FAIL) as expected
control_real_ids_pass_when_ids_are_required@real-mf-form.json (exit 0, no FAIL) as expected
control_closing_block_sums_lead_decisions (webhook without auth counted) as expected
control_known_problems_are_listed (REPLY GAP and no authentication counted) as expected
orphan_node@real-mf-form.json (FAIL, exit 1)                             as expected
orphan_node@real-mf-hook.json (FAIL, exit 1)                             as expected
orphan_node@real-mf-recovery.json (FAIL, exit 1)                         as expected
orphan_node@real-mf-sub-crm-mail.json (FAIL, exit 1)                     as expected
cycle_only@real-mf-form.json (FAIL, exit 1)                              as expected
cycle_only@real-mf-hook.json (FAIL, exit 1)                              as expected
cycle_only@real-mf-recovery.json (FAIL, exit 1)                          as expected
cycle_only@real-mf-sub-crm-mail.json (FAIL, exit 1)                      as expected
dangling@real-mf-form.json (FAIL, exit 1)                                as expected
dangling@real-mf-hook.json (FAIL, exit 1)                                as expected
dangling@real-mf-recovery.json (FAIL, exit 1)                            as expected
dangling@real-mf-sub-crm-mail.json (FAIL, exit 1)                        as expected
duplicate_name@real-mf-form.json (FAIL, exit 1)                          as expected
duplicate_name@real-mf-hook.json (FAIL, exit 1)                          as expected
duplicate_name@real-mf-recovery.json (FAIL, exit 1)                      as expected
duplicate_name@real-mf-sub-crm-mail.json (FAIL, exit 1)                  as expected
name_case_dup@real-mf-form.json (FAIL, exit 1)                           as expected
name_case_dup@real-mf-hook.json (FAIL, exit 1)                           as expected
name_case_dup@real-mf-recovery.json (FAIL, exit 1)                       as expected
name_case_dup@real-mf-sub-crm-mail.json (FAIL, exit 1)                   as expected
duplicate_id@real-mf-form.json (FAIL, exit 1)                            as expected
duplicate_id@real-mf-hook.json (FAIL, exit 1)                            as expected
duplicate_id@real-mf-recovery.json (FAIL, exit 1)                        as expected
duplicate_id@real-mf-sub-crm-mail.json (FAIL, exit 1)                    as expected
trigger_has_input@real-mf-form.json (FAIL, exit 1)                       as expected
trigger_has_input@real-mf-hook.json (FAIL, exit 1)                       as expected
trigger_has_input@real-mf-recovery.json (FAIL, exit 1)                   as expected
trigger_has_input@real-mf-sub-crm-mail.json (FAIL, exit 1)               as expected
sticky_with_link@real-mf-form.json (FAIL, exit 1)                        as expected
sticky_with_link@real-mf-hook.json (FAIL, exit 1)                        as expected
sticky_with_link@real-mf-recovery.json (FAIL, exit 1)                    as expected
sticky_with_link@real-mf-sub-crm-mail.json (FAIL, exit 1)                as expected
secret_sk@real-mf-form.json (FAIL, exit 1)                               as expected
secret_sk@real-mf-hook.json (FAIL, exit 1)                               as expected
secret_sk@real-mf-recovery.json (FAIL, exit 1)                           as expected
secret_sk@real-mf-sub-crm-mail.json (FAIL, exit 1)                       as expected
secret_aws@real-mf-form.json (FAIL, exit 1)                              as expected
secret_aws@real-mf-hook.json (FAIL, exit 1)                              as expected
secret_aws@real-mf-recovery.json (FAIL, exit 1)                          as expected
secret_aws@real-mf-sub-crm-mail.json (FAIL, exit 1)                      as expected
secret_github@real-mf-form.json (FAIL, exit 1)                           as expected
secret_github@real-mf-hook.json (FAIL, exit 1)                           as expected
secret_github@real-mf-recovery.json (FAIL, exit 1)                       as expected
secret_github@real-mf-sub-crm-mail.json (FAIL, exit 1)                   as expected
secret_slack@real-mf-form.json (FAIL, exit 1)                            as expected
secret_slack@real-mf-hook.json (FAIL, exit 1)                            as expected
secret_slack@real-mf-recovery.json (FAIL, exit 1)                        as expected
secret_slack@real-mf-sub-crm-mail.json (FAIL, exit 1)                    as expected
secret_private_key@real-mf-form.json (FAIL, exit 1)                      as expected
secret_private_key@real-mf-hook.json (FAIL, exit 1)                      as expected
secret_private_key@real-mf-recovery.json (FAIL, exit 1)                  as expected
secret_private_key@real-mf-sub-crm-mail.json (FAIL, exit 1)              as expected
secret_jwt@real-mf-form.json (FAIL, exit 1)                              as expected
secret_jwt@real-mf-hook.json (FAIL, exit 1)                              as expected
secret_jwt@real-mf-recovery.json (FAIL, exit 1)                          as expected
secret_jwt@real-mf-sub-crm-mail.json (FAIL, exit 1)                      as expected
secret_url_password@real-mf-form.json (FAIL, exit 1)                     as expected
secret_url_password@real-mf-hook.json (FAIL, exit 1)                     as expected
secret_url_password@real-mf-recovery.json (FAIL, exit 1)                 as expected
secret_url_password@real-mf-sub-crm-mail.json (FAIL, exit 1)             as expected
secret_bearer@real-mf-form.json (FAIL, exit 1)                           as expected
secret_bearer@real-mf-hook.json (FAIL, exit 1)                           as expected
secret_bearer@real-mf-recovery.json (FAIL, exit 1)                       as expected
secret_bearer@real-mf-sub-crm-mail.json (FAIL, exit 1)                   as expected
secret_under_key@real-mf-form.json (FAIL, exit 1)                        as expected
secret_under_key@real-mf-hook.json (FAIL, exit 1)                        as expected
secret_under_key@real-mf-recovery.json (FAIL, exit 1)                    as expected
secret_under_key@real-mf-sub-crm-mail.json (FAIL, exit 1)                as expected
secret_under_key_all_caps@real-mf-form.json (FAIL, exit 1)               as expected
secret_under_key_all_caps@real-mf-hook.json (FAIL, exit 1)               as expected
secret_under_key_all_caps@real-mf-recovery.json (FAIL, exit 1)           as expected
secret_under_key_all_caps@real-mf-sub-crm-mail.json (FAIL, exit 1)       as expected
secret_in_sticky_note@real-mf-form.json (FAIL, exit 1)                   as expected
secret_in_sticky_note@real-mf-hook.json (FAIL, exit 1)                   as expected
secret_in_sticky_note@real-mf-recovery.json (FAIL, exit 1)               as expected
secret_in_sticky_note@real-mf-sub-crm-mail.json (FAIL, exit 1)           as expected
secret_top_level_value@real-mf-form.json (FAIL, exit 1)                  as expected
secret_top_level_value@real-mf-hook.json (FAIL, exit 1)                  as expected
secret_top_level_value@real-mf-recovery.json (FAIL, exit 1)              as expected
secret_top_level_value@real-mf-sub-crm-mail.json (FAIL, exit 1)          as expected
secret_top_level_key@real-mf-form.json (FAIL, exit 1)                    as expected
secret_top_level_key@real-mf-hook.json (FAIL, exit 1)                    as expected
secret_top_level_key@real-mf-recovery.json (FAIL, exit 1)                as expected
secret_top_level_key@real-mf-sub-crm-mail.json (FAIL, exit 1)            as expected
cred_block_missing@real-mf-form.json (FAIL, exit 1)                      as expected
cred_block_missing@real-mf-hook.json (FAIL, exit 1)                      as expected
cred_block_missing@real-mf-recovery.json (FAIL, exit 1)                  as expected
cred_block_missing@real-mf-sub-crm-mail.json (FAIL, exit 1)              as expected
cred_name_empty@real-mf-form.json (FAIL, exit 1)                         as expected
cred_name_empty@real-mf-hook.json (FAIL, exit 1)                         as expected
cred_name_empty@real-mf-recovery.json (FAIL, exit 1)                     as expected
cred_name_empty@real-mf-sub-crm-mail.json (FAIL, exit 1)                 as expected
cred_id_missing@real-mf-form.json (FAIL, exit 1)                         as expected
cred_id_missing@real-mf-hook.json (FAIL, exit 1)                         as expected
cred_id_missing@real-mf-recovery.json (FAIL, exit 1)                     as expected
cred_id_missing@real-mf-sub-crm-mail.json (FAIL, exit 1)                 as expected
httprequest_auth_no_credentials@real-mf-form.json (FAIL, exit 1)         as expected
httprequest_auth_no_credentials@real-mf-hook.json (FAIL, exit 1)         as expected
httprequest_auth_no_credentials@real-mf-recovery.json (FAIL, exit 1)     as expected
httprequest_auth_no_credentials@real-mf-sub-crm-mail.json (FAIL, exit 1) as expected
missing_position@real-mf-form.json (FAIL, exit 1)                        as expected
missing_position@real-mf-hook.json (FAIL, exit 1)                        as expected
missing_position@real-mf-recovery.json (FAIL, exit 1)                    as expected
missing_position@real-mf-sub-crm-mail.json (FAIL, exit 1)                as expected
missing_typeversion@real-mf-form.json (FAIL, exit 1)                     as expected
missing_typeversion@real-mf-hook.json (FAIL, exit 1)                     as expected
missing_typeversion@real-mf-recovery.json (FAIL, exit 1)                 as expected
missing_typeversion@real-mf-sub-crm-mail.json (FAIL, exit 1)             as expected
no_trigger@real-mf-form.json (FAIL, exit 1)                              as expected
no_trigger@real-mf-hook.json (FAIL, exit 1)                              as expected
no_trigger@real-mf-recovery.json (FAIL, exit 1)                          as expected
no_trigger@real-mf-sub-crm-mail.json (FAIL, exit 1)                      as expected
bad_retry_type@real-mf-form.json (FAIL, exit 1)                          as expected
bad_retry_type@real-mf-hook.json (FAIL, exit 1)                          as expected
bad_retry_type@real-mf-recovery.json (FAIL, exit 1)                      as expected
bad_retry_type@real-mf-sub-crm-mail.json (FAIL, exit 1)                  as expected
bad_alwaysoutput_type@real-mf-form.json (FAIL, exit 1)                   as expected
bad_alwaysoutput_type@real-mf-hook.json (FAIL, exit 1)                   as expected
bad_alwaysoutput_type@real-mf-recovery.json (FAIL, exit 1)               as expected
bad_alwaysoutput_type@real-mf-sub-crm-mail.json (FAIL, exit 1)           as expected
bad_ref@real-mf-form.json (FAIL, exit 1)                                 as expected
bad_ref@real-mf-hook.json (FAIL, exit 1)                                 as expected
bad_ref@real-mf-recovery.json (FAIL, exit 1)                             as expected
bad_ref@real-mf-sub-crm-mail.json (FAIL, exit 1)                         as expected
bad_items_ref@real-mf-form.json (FAIL, exit 1)                           as expected
bad_items_ref@real-mf-hook.json (FAIL, exit 1)                           as expected
bad_items_ref@real-mf-recovery.json (FAIL, exit 1)                       as expected
bad_items_ref@real-mf-sub-crm-mail.json (FAIL, exit 1)                   as expected
bad_node_dot_ref@real-mf-form.json (FAIL, exit 1)                        as expected
bad_node_dot_ref@real-mf-hook.json (FAIL, exit 1)                        as expected
bad_node_dot_ref@real-mf-recovery.json (FAIL, exit 1)                    as expected
bad_node_dot_ref@real-mf-sub-crm-mail.json (FAIL, exit 1)                as expected
shape_connection_not_object@real-mf-form.json (FAIL, exit 1)             as expected
shape_connection_not_object@real-mf-hook.json (FAIL, exit 1)             as expected
```

## raw: out/3.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
WARN demo/n8n-flows-real-v5/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started wi
WARN demo/n8n-flows-real-v5/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started wi
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run st
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    mf-form.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-hook.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-sub-crm-mail.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - demo/n8n-flows-real-v5/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  - WARN mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test wo
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### demo/n8n-flows-real-v5
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [demo/n8n-flows-real-v5/mf-form.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN demo/n8n-flows-real-v5/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN demo/n8n-flows-real-v5/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [demo/n8n-flows-real-v5/mf-hook.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN demo/n8n-flows-real-v5/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN demo/n8n-flows-real-v5/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; ClaimStuck credential postgres id PG_CREDENTIAL_ID; MarkFailed credential p
WARN demo/n8n-flows-real-v5/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN demo/n8n-flows-real-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN demo/n8n-flows-real-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery claim)
WARN demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_CREDENTIAL_ID; MarkUnknownB credential postgres id PG_CREDENTIAL_ID; SendMai
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
WARN demo/n8n-flows-real-v5/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node StuckRow output(s) [1]
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - demo/n8n-flows-real-v5/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - demo/n8n-flows-real-v5/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
Known open problems: 17
  - demo/n8n-flows-real-v5/mf-form.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-form.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - demo/n8n-flows-real-v5/mf-form.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-form.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
  - demo/n8n-flows-real-v5/mf-hook.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-hook.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - demo/n8n-flows-real-v5/mf-hook.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-hook.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
  - demo/n8n-flows-real-v5/mf-recovery.json: node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-recovery.json: 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; ClaimStuck credential postgres id PG_CREDENTIAL_ID; MarkFailed credential p
  - demo/n8n-flows-real-v5/mf-recovery.json: 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - demo/n8n-flows-real-v5/mf-recovery.json: IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_CREDENTIAL_ID; MarkUnknownB credential postgres id PG_CREDENTIAL_ID; SendMai
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json: this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to see what happened
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); who calls a web address, whether the flow is
Passing this check does NOT mean the flows are ready to film.
Open items counted: checker known open problems 17 + psql gate 1 + problems of this script 4 (entry flows without the key check: 2, counted inside the problems).
FINAL: take_check exit status 4. RESULT: 0 FAIL, 23 WARN. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 22. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```

## raw: out/4-base.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fi
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 22 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
WARN set equals the pinned set (22 lines in take-warns.pin): no new and no vanished WARN.
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID; 
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recov
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG_C
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 22 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/work/g/real/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
Known open problems: 16
```

## raw: out/4-warn-new.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  + WARN mf-sub-crm-mail.json node MarkDone sets maxTries/waitBetweenTries but retryOnFail is not true (ignored by n8n)
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_I
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no re
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkDone sets maxTries/waitBetweenTries but retryOnFail is not true (ignored by n8n)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id P
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/warn-new/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
```

## raw: out/4-form-count.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=16 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 3 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  + WARN mf-form.json node ExtraNode reads $('Valid') which is not upstream of it (it may not have run)
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count
FAIL /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json orphan nodes (no incoming link, not a trigger) ['ExtraNode']
FAIL /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json unreachable from any trigger ['ExtraNode']
FAIL /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node count 16 != expected 15
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node ExtraNode reads $('Valid') which is not upstream of it (it may not have run)
mf-form.json nodes=16 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no 
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 3 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-count/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
```

## raw: out/4-form-oddword.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=off saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    mf-form.json: saveDataSuccessExecution='off' saveDataErrorExecution='all' saveManualExecutions=True
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 22 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
WARN set equals the pinned set (22 lines in take-warns.pin): no new and no vanished WARN.
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=off saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTI
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes n
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres 
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 22 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/form-oddword/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
```

## raw: out/4-saveoff.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution'] are off ('none' or false): n8n keeps no run lis
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it 
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    mf-sub-crm-mail.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=True
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  + WARN mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept eith
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-form.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-form.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-form.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-form.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-form.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-form.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json] webhook Receive: 5 respondToWebhook node(s) reachable ['ReplyBadKey', 'ReplyRan', 'ReplyReview', 'ReplyStoreFail', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=15 connections=14 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
  [mf-hook.json] Claim alwaysOutputData=False onError='continueErrorOutput'
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  [mf-hook.json] KeyOk IF condition: [{"id": "c1", "leftValue": "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}", "rightValue": null, "operator": {"type": "boolean", "operation": "true", "singleValue": true}}]
  [mf-hook.json] ReplyBadKey status=422 body=={{ { n8n_error: false, lead_key: '', verdict: 'rejected', reason: 'lead_key missing or not valid (1 to 64 characters from A-Z, a-z, 0-9, - or _)' } }}
  [mf-hook.json] ReplyStoreFail status=503 body=={{ { n8n_error: true, lead_key: $('Valid').first().json.lead_key, verdict: 'retry', reason: 'store not confirmed; resend with the same lead_key is safe' } }}
  [mf-hook.json] Valid lead_key assignment: ["={{ String($json.lead_key || '') }}"]
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_ID
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no rec
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id PG
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person cannot open a past run to s
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/saveoff/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
```

## raw: out/4-f008-only.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (i
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 20 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  - WARN mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDENTIAL_
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no r
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgres id 
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=all saveDataError=all saveManual=True
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 20 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
SQL columns compared with the --ddl file: 14 query string(s) read.
SQL WARNS: column WARNs=0 table WARNs=0 postgres steps with no query text (not compared)=0
Known open problems: 14
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-form.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json: webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json: webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/f008-only/mf-hook.json: 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
```

## raw: out/4-nokey-unpatched.txt
```
=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ===
=== READ THIS BLOCK BEFORE ANYTHING ELSE ===
--- (1) The lead table and the column check ---
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows).
Query strings read: 14. Column WARNs: 0. Table WARNs: 0. Postgres steps with no query text (not compared): 0.
GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out.
--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or fals
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or fals
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none'
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purp
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4.
    mf-form.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-hook.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
    mf-sub-crm-mail.json: saveDataSuccessExecution='none' saveDataErrorExecution='none' saveManualExecutions=False
--- (3) Values that must be filled in before import: mail addresses and credential ids ---
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4.
--- (5) Open decisions and environment variables ---
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
STEPS THAT READ ENVIRONMENT VARIABLES (2):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend: $env.DESK_ALERT_TO
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node Qualify: $env.DESK_TIMEOUT_MS, $env.DESK_URL
If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked.
--- (6) Checker result and the WARN baseline ---
RESULT: 0 FAIL, 23 WARN. WARN lines that rest on an n8n rule nobody verified: 2.
!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4.
  - WARN mf-form.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-form.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  - WARN mf-hook.json patch F-002 (Claim step: alwaysOutputData/onError) is UNPROVEN until a test run in n8n shows a repeated lead key still gets its answer
  - WARN mf-hook.json webhook Receive: REPLY GAP: if ['RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' 
  + WARN mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  + WARN mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test wo
=== end of top block; full checker output follows ===
# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line. 3 = the checker itself broke or could not write a file.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# WARN-LEAD-DECISION = an open decision for the lead or owner (no password on a web address, $env reads). Exit stays 0, so exit 0 does NOT mean authentication was checked.
# Rules that come from memory of n8n (tag 'n8n rule UNVERIFIED') are WARN only; --fail-unverified makes them FAIL.
# A credential id that is still a placeholder is always a WARN (use --require-real-credential-ids to make it a FAIL).
# The numbers for THIS run (open decisions, known open problems, accepted IF branches) are printed in the closing block: 'OPEN LEAD DECISIONS' and 'Known open problems'.
# =============================================================================
### /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person can
mf-form.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)
  [/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json] webhook Receive: 3 respondToWebhook node(s) reachable ['ReplyRan', 'ReplyReview', 'ReplyStored']; paths without a reply: none
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json 3 id(s) are still placeholders and must be replaced in n8n before import: Claim credential postgres id PG_CREDENTIAL_ID; RunSub sub-workflow id SUB_WORKFLOW_ID; Stored credential postgres id PG_CREDENTIAL_ID [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a person can
mf-hook.json nodes=12 connections=11 triggers=['Receive'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): Claim postgres n8n-publish-pg PG_CREDENTIAL_ID; Stored postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json 7 id(s) are still placeholders and must be replaced in n8n before import: AlertBackoff credential postgres id PG_CREDENTIAL_ID; AlertClaim credential postgres id PG_CREDENTIAL_ID; AlertMark credential postgres id PG_CREDENTIAL_ID; AlertSend credential smtp id SMTP_CREDE
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json 1 value(s) in node settings are still placeholders; these must be filled before import: AlertSend fromEmail: FROM_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff', 'AlertClaim', 'AlertMark', 'ClaimStuck', 'MarkFailed', 'RunSub']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video make
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json IF node StuckRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json IF node AlertRow lacks output(s) [1] (accepted by a recorded decision, --accept-if; an item that would leave by the missing output stops there silently, so a database failure that ends here vanishes with no alert) (project rule: every IF branch leads somewhere)
mf-recovery.json nodes=10 connections=9 triggers=['Every30s'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): ClaimStuck postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkFailed postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertSend smtp mf-mail-smtp SMTP_CREDENTIAL_ID; AlertBackoff postgres n8n-publish-pg PG_CREDENTIAL_ID; AlertMark postgres n8n-publish-pg PG_CREDENTIAL_ID
WARN-LEAD-DECISION /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: n8n rule UNVERIFIED) this node stops working [run with --block-env-access to make it a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json 7 id(s) are still placeholders and must be replaced in n8n before import: CrmUpsert credential hubspotAppToken id HS_CRED_PLACEHOLDER; MailClaim credential postgres id PG_CREDENTIAL_ID; MarkDone credential postgres id PG_CREDENTIAL_ID; MarkUnknownA credential postgr
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: FROM_ADDRESS_PLACEHOLDER; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credential-ids to make this a FAIL]
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendMail', 'SetCrmId']
WARN /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json this flow's run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] are off ('none' or false): n8n keeps no run list for those runs (saveManualExecutions off = a run started with 'Test workflow' is not kept either), so a pe
mf-sub-crm-mail.json nodes=20 connections=26 triggers=['SubIn'] saveDataSuccess=none saveDataError=none saveManual=False
  credentials (node, kind, name, id): CrmUpsert hubspotAppToken hubspot-app-token HS_CRED_PLACEHOLDER; SetCrmId postgres n8n-publish-pg PG_CREDENTIAL_ID; MailClaim postgres n8n-publish-pg PG_CREDENTIAL_ID; SendMail smtp mf-mail-smtp SMTP_CREDENTIAL_ID; MarkDone postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownA postgres n8n-publish-pg PG_CREDENTIAL_ID; MarkUnknownB postgres n8n-publish-pg PG_C
RESULT: 0 FAIL, 23 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json: IF node StuckRow output(s) [1]
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json: IF node AlertRow output(s) [1]
Run-saving left off by a recorded decision (--accept-no-save), recovery flow not part of the take (decision 4): 1
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json: ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions']
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
CREDENTIAL IDS STILL PLACEHOLDERS (20): these must be replaced in n8n before import (the id that n8n gives each credential and each sub-workflow):
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-form.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node Claim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-hook.json node Stored credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node ClaimStuck credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node RunSub sub-workflow id: SUB_WORKFLOW_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node MarkFailed credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertSend credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertBackoff credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-recovery.json node AlertMark credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node CrmUpsert credential hubspotAppToken id: HS_CRED_PLACEHOLDER
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SetCrmId credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MailClaim credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node SendMail credential smtp id: SMTP_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkDone credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkUnknownA credential postgres id: PG_CREDENTIAL_ID
  - /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-run2/plant/nokey-unpatched/mf-sub-crm-mail.json node MarkUnknownB credential postgres id: PG_CREDENTIAL_ID
STEPS THAT READ ENVIRONMENT VARIABLES (2):
```

## raw: out/5a.txt
```
All checks passed!
```

## raw: out/5b.txt
```
unformatted: File would be reformatted
    --> check_flows.py:77:18
     |
76   |
     - FILES_DEFAULT = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
77   + FILES_DEFAULT = [
78   +     "mf-form.json",
79   +     "mf-hook.json",
80   +     "mf-recovery.json",
81   +     "mf-sub-crm-mail.json",
82   + ]
83   | TRIGGER_EXACT = {
--------------------------------------------------------------------------------
137  | # every way a malformed (but parsable) flow file can make the checker's own code raise: reported as a FAIL, never a Traceback
     - READ_ERRORS = (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError)
138  + READ_ERRORS = (
139  +     OSError,
140  +     ValueError,
141  +     TypeError,
142  +     KeyError,
143  +     IndexError,
144  +     AttributeError,
145  +     RecursionError,
146  + )
147  | # every ordinary Python error class (no blind "except Exception"); anything outside this list (for example KeyboardInterrupt) is not a checker fault
--------------------------------------------------------------------------------
207  |     if ACCEPTED_IF:
     -         print(f"IF branches accepted by a recorded decision (--accept-if): {len(ACCEPTED_IF)}")
208  +         print(
209  +             f"IF branches accepted by a recorded decision (--accept-if): {len(ACCEPTED_IF)}"
210  +         )
211  |         for k in ACCEPTED_IF:
--------------------------------------------------------------------------------
350  | PH_WORD = re.compile(
     -     r"[A-Za-z0-9_]*(?:" + "|".join(re.escape(x) for x in PLACEHOLDERS) + r")[A-Za-z0-9_]*"
351  +     r"[A-Za-z0-9_]*(?:"
352  +     + "|".join(re.escape(x) for x in PLACEHOLDERS)
353  +     + r")[A-Za-z0-9_]*"
354  | )
--------------------------------------------------------------------------------
491  |     except (OSError, ValueError, RecursionError) as e:
     -         fail(tag, f"parse failure {type(e).__name__}: the file is unreadable or not valid JSON")
492  +         fail(
493  +             tag,
494  +             f"parse failure {type(e).__name__}: the file is unreadable or not valid JSON",
495  +         )
496  |         return None
--------------------------------------------------------------------------------
535  |             isinstance(n, dict)
     -             and n.get("type") in ("n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger")
536  +             and n.get("type")
537  +             in ("n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger")
538  |             and "webhookId" in n
--------------------------------------------------------------------------------
585  | }  # n8n form trigger: only none or basicAuth (n8n rule UNVERIFIED: from memory of n8n)
     - CRED_TYPES = ("postgres", "emailSend", "hubspot")  # these always need an attached credential
586  + CRED_TYPES = (
587  +     "postgres",
588  +     "emailSend",
589  +     "hubspot",
590  + )  # these always need an attached credential
591  | # secret shapes are built from parts so this file holds no secret-looking literal (the one allowed literal is the AWS example key)
--------------------------------------------------------------------------------
595  |     ("sk- style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
     -     ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
596  +     (
597  +         "GitHub token",
598  +         re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
599  +     ),
600  |     ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
--------------------------------------------------------------------------------
632  |     if not blocks or not all(
     -         re.match(r"\s*\$(env|credentials|secrets|vars|json|node|\(|items)", b) for b in blocks
633  +         re.match(r"\s*\$(env|credentials|secrets|vars|json|node|\(|items)", b)
634  +         for b in blocks
635  |     ):
--------------------------------------------------------------------------------
673  |             and not value_is_safe(v)
     -             and str(k).lower() not in ("authentication", "genericauthtype", "nodecredentialtype")
674  +             and str(k).lower()
675  +             not in ("authentication", "genericauthtype", "nodecredentialtype")
676  |         ):
--------------------------------------------------------------------------------
745  |     if not resp:
     -         fail(tag, "webhook {} (responseNode): no respondToWebhook reachable".format(n["name"]))
746  +         fail(
747  +             tag,
748  +             "webhook {} (responseNode): no respondToWebhook reachable".format(
749  +                 n["name"]
750  +             ),
751  +         )
752  |     risky = sorted(
--------------------------------------------------------------------------------
783  |         if not isinstance(outs, dict) or any(
     -             not isinstance(l, list) or any(l2 is not None and not isinstance(l2, list) for l2 in l)
784  +             not isinstance(l, list)
785  +             or any(l2 is not None and not isinstance(l2, list) for l2 in l)
786  |             for l in outs.values()
787  |         ):
     -             fail(tag, f"connections of {src!r} are not {{type: [[{{node,type,index}}]]}}")
788  +             fail(
789  +                 tag, f"connections of {src!r} are not {{type: [[{{node,type,index}}]]}}"
790  +             )
791  |             continue
--------------------------------------------------------------------------------
844  |             and len(pos) == 2
     -             and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in pos)
845  +             and all(
846  +                 isinstance(v, (int, float)) and not isinstance(v, bool) for v in pos
847  +             )
848  |         ):
--------------------------------------------------------------------------------
861  |         if "retryOnFail" in n and not isinstance(n["retryOnFail"], bool):
     -             fail(tag, "node {} retryOnFail={!r} is not a boolean".format(nm, n["retryOnFail"]))
862  +             fail(
863  +                 tag,
864  +                 "node {} retryOnFail={!r} is not a boolean".format(
865  +                     nm, n["retryOnFail"]
866  +                 ),
867  +             )
868  |         if n.get("retryOnFail"):
--------------------------------------------------------------------------------
887  |                 tag,
     -                 "node {} alwaysOutputData={!r} is not a boolean".format(nm, n["alwaysOutputData"]),
888  +                 "node {} alwaysOutputData={!r} is not a boolean".format(
889  +                     nm, n["alwaysOutputData"]
890  +                 ),
891  |             )
     -         if n.get("alwaysOutputData") is True and n.get("onError") == "continueErrorOutput":
892  +         if (
893  +             n.get("alwaysOutputData") is True
894  +             and n.get("onError") == "continueErrorOutput"
895  +         ):
896  |             fail(
--------------------------------------------------------------------------------
917  |             short == "httpRequest"
     -             and (n.get("parameters") or {}).get("authentication") not in (None, "none", "")
918  +             and (n.get("parameters") or {}).get("authentication")
919  +             not in (None, "none", "")
920  |         )
--------------------------------------------------------------------------------
928  |                     tag,
     -                     "node {} credential {!r} has no id (name {!r})".format(nm, k, v.get("name")),
929  +                     "node {} credential {!r} has no id (name {!r})".format(
930  +                         nm, k, v.get("name")
931  +                     ),
932  |                 )
--------------------------------------------------------------------------------
948  |                 "node {} ({}) credential kind(s) {} do not include the expected kind {}".format(
     -                     nm, short, sorted(cr), " or ".join(repr(k) for k in CRED_KIND[short])
```

## raw: out/5c.txt
```
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 11:31:01.082607+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 4256
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 1
		High: 0
Files skipped (0):
```

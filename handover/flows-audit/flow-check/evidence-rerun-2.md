# evidence-rerun-2 (EVIDENCE RUNNER, raw, no judgement)

## Counts
run_all.sh rc=0; selftest: 368 as expected, 0 not as expected, 20 skipped
Pristine: default rc=0 (0 FAIL,14 WARN each real/film); --block-env-access rc=1 (2 FAIL,12 WARN); --require-webhook-auth rc=1 (2 FAIL,12 WARN)

## SURVIVED list
none (9 mutants run, 9 killed)

## Mutants (selftest result against mutated checker)
M1_drop_conn_dangling: KILLED  SELFTEST: 363 as expected, 5 not as expected, 20 skipped (not applicable)
M2_drop_continueErrorOutput_target: KILLED  SELFTEST: 361 as expected, 7 not as expected, 20 skipped (not applicable)
M3_drop_alwaysOutput_warn: KILLED  SELFTEST: 363 as expected, 5 not as expected, 20 skipped (not applicable)
M4_drop_env_scan: KILLED  SELFTEST: 358 as expected, 10 not as expected, 20 skipped (not applicable)
M5_drop_cred_name: KILLED  SELFTEST: 363 as expected, 5 not as expected, 20 skipped (not applicable)
M6_exit_always_0: KILLED  SELFTEST: 83 as expected, 285 not as expected, 20 skipped (not applicable)
M7_malformed_json_passes: KILLED  SELFTEST: 363 as expected, 5 not as expected, 20 skipped (not applicable)
M8_disabled_respond_as_enabled: KILLED  SELFTEST: 365 as expected, 3 not as expected, 20 skipped (not applicable)
M9_skip_file_silently: KILLED  SELFTEST: 300 as expected, 68 not as expected, 20 skipped (not applicable)

## run_all.sh output
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 15 s
---- summary (default mode must be exit 0; strict mode shows what the owner's two open decisions would do) ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 14 WARN
Known open problems: 6
exit=0
######## pristine film
RESULT: 0 FAIL, 14 WARN
Known open problems: 6
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 16 WARN
Known open problems: 8
exit=0
######## patched film
RESULT: 0 FAIL, 16 WARN
Known open problems: 8
exit=0
[pristine-strict]
######## pristine-strict real
RESULT: 4 FAIL, 10 WARN
Known open problems: 2
exit=1
######## pristine-strict film
RESULT: 4 FAIL, 10 WARN
Known open problems: 2
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 12 WARN
Known open problems: 4
exit=1
######## patched-strict film
RESULT: 4 FAIL, 12 WARN
Known open problems: 4
exit=1
[selftest exit=0] SELFTEST: 368 as expected, 0 not as expected, 20 skipped (not applicable)
run_all exit status: 0
rc=0

## Pristine mode runs (FAIL/WARN lines, truncated 160 chars)
#### real []
rc=0
WARN ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n set
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access in
WARN ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 0 FAIL, 14 WARN
#### film []
rc=0
WARN ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node Qualify reads $env.MF_STAGE_TIMEOUT_MS, $env.MF_STAGE_URL; if the take blocks environment-variable a
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node CrmUpsert reads $env.MF_CRM_URL; if the take blocks environment-variable access inside nodes (n8n se
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 0 FAIL, 14 WARN
#### real [--block-env-access]
rc=1
WARN ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
FAIL ../../demo/n8n-flows-real-v5/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n set
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
FAIL ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access in
WARN ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 2 FAIL, 12 WARN
#### film [--block-env-access]
rc=1
WARN ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post) [open web address: the owner decide
WARN ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
FAIL ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node Qualify reads $env.MF_STAGE_TIMEOUT_MS, $env.MF_STAGE_URL; if the take blocks environment-variable a
FAIL ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node CrmUpsert reads $env.MF_CRM_URL; if the take blocks environment-variable access inside nodes (n8n se
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 2 FAIL, 12 WARN
#### real [--require-webhook-auth]
rc=1
FAIL ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post)
WARN ../../demo/n8n-flows-real-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
FAIL ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post)
WARN ../../demo/n8n-flows-real-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-real-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json node AlertSend reads $env.DESK_ALERT_TO; if the take blocks environment-variable access inside nodes (n8n set
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-real-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access in
WARN ../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 2 FAIL, 12 WARN
#### film [--require-webhook-auth]
rc=1
FAIL ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive has no authentication (anyone who knows the address can post)
WARN ../../demo/n8n-flows-film-v5/mf-form.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-form.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
FAIL ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive has no authentication (anyone who knows the address can post)
WARN ../../demo/n8n-flows-film-v5/mf-hook.json webhook Receive: REPLY GAP: if ['Claim', 'RunSub', 'Stored'] fails the run stops and the caller gets no answer (e
WARN ../../demo/n8n-flows-film-v5/mf-hook.json external-call nodes without retryOnFail: ['Claim', 'RunSub', 'Stored']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes without retryOnFail: ['AlertBackoff', 'AlertClaim', 'AlertMark', 'AlertSend', 'ClaimStuck
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): ['AlertBackoff
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json write node AlertSend has upstream external call(s) that continue on error: ['AlertClaim']
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node StuckRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-film-v5/mf-recovery.json IF node AlertRow lacks output(s) [1] (baseline already lacks the same) (project rule: every IF branch leads s
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node Qualify reads $env.MF_STAGE_TIMEOUT_MS, $env.MF_STAGE_URL; if the take blocks environment-variable a
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json node CrmUpsert reads $env.MF_CRM_URL; if the take blocks environment-variable access inside nodes (n8n se
WARN ../../demo/n8n-flows-film-v5/mf-sub-crm-mail.json external-call nodes without retryOnFail: ['MailClaim', 'MarkDone', 'MarkUnknownA', 'MarkUnknownB', 'SendM
RESULT: 2 FAIL, 12 WARN

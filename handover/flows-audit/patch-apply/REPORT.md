Mon Nov 16 09:01:17 UTC 2026

# F4 patch-apply evidence (raw, no judgement)
Scratch: /tmp/pa13 (work = all patches in check_patches.sh order; base = unpatched; p-<name> = one patch alone). Checker: check_flows.py (stdlib, read-only).

## Commands
- mk copy of handover/demo/{n8n-flows/*.json,mf_leads.sql,PAGE-STATEMENTS-V4.md,VIDEO-RUNSHEET.md,n8n-mainframe/build_mainframe.py}; cd copy; git apply --check PATCH; git apply PATCH
- real: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py OUT PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
- film: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py OUT PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
- python3 -I check_flows.py DIR

## Apply and generator exit codes
```
## Baseline generator (unpatched)
gen real rc=0
gen film rc=0
## Combined, order of check_patches.sh
F-001-one-ddl check=0 apply=0
F-002-take-key-check-and-claim-error-path check=0 apply=0
F-003-runsheet-claims check=0 apply=0
F-004-page-statement-17 check=0 apply=0
F-008-save-runs-for-the-take check=0 apply=0
gen real rc=0
gen film rc=0
## Each alone
F-001-one-ddl check=0 apply=0
F-002-take-key-check-and-claim-error-path check=0 apply=0
gen real rc=0
gen film rc=0
F-003-runsheet-claims check=0 apply=0
F-004-page-statement-17 check=0 apply=0
F-008-save-runs-for-the-take check=0 apply=0
gen real rc=0
gen film rc=0
```

## Checker output and comparisons
```
### base/real
gen/base/real |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### base/film
gen/base/film |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/base/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### all/real
gen/all/real |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/real |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/all/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### all/film
gen/all/film |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/film |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/all/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/all/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### F-002-take-key-check-and-claim-error-path/real
gen/F-002-take-key-check-and-claim-error-path/real |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### F-002-take-key-check-and-claim-error-path/film
gen/F-002-take-key-check-and-claim-error-path/film |mf-form.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-hook.json parse=ok nodes=15 dup_names=[] connections=14 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-002-take-key-check-and-claim-error-path/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### F-008-save-runs-for-the-take/real
gen/F-008-save-runs-for-the-take/real |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/real |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/real |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-008-save-runs-for-the-take/real |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### F-008-save-runs-for-the-take/film
gen/F-008-save-runs-for-the-take/film |mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/film |mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
gen/F-008-save-runs-for-the-take/film |mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
gen/F-008-save-runs-for-the-take/film |mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=all saveDataError=all
### saved real-v5
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-real-v5 | file=mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### saved film-v5
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-form.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-hook.json parse=ok nodes=12 dup_names=[] connections=11 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-recovery.json parse=ok nodes=10 dup_names=[] connections=9 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
/home/user/hadavin-sdk/handover/demo/n8n-flows-film-v5 | file=mf-sub-crm-mail.json parse=ok nodes=20 dup_names=[] connections=26 dangling=[] orphans=[] saveDataSuccess=none saveDataError=none
### diff base vs saved
real/mf-form identical
real/mf-hook identical
real/mf-recovery identical
real/mf-sub-crm-mail identical
film/mf-form identical
film/mf-hook identical
film/mf-recovery identical
film/mf-sub-crm-mail identical
### diff base vs all (lines)
200
200
### patched generator diffs
-- all/real
diff -r gen/base/real/mf-form.json gen/all/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/all/real/mf-hook.json
diff -r gen/base/real/mf-sub-crm-mail.json gen/all/real/mf-sub-crm-mail.json
-- all/film
diff -r gen/base/film/mf-form.json gen/all/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/all/film/mf-hook.json
diff -r gen/base/film/mf-sub-crm-mail.json gen/all/film/mf-sub-crm-mail.json
-- F-002-take-key-check-and-claim-error-path/real
diff -r gen/base/real/mf-form.json gen/F-002-take-key-check-and-claim-error-path/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/F-002-take-key-check-and-claim-error-path/real/mf-hook.json
-- F-002-take-key-check-and-claim-error-path/film
diff -r gen/base/film/mf-form.json gen/F-002-take-key-check-and-claim-error-path/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/F-002-take-key-check-and-claim-error-path/film/mf-hook.json
-- F-008-save-runs-for-the-take/real
diff -r gen/base/real/mf-form.json gen/F-008-save-runs-for-the-take/real/mf-form.json
diff -r gen/base/real/mf-hook.json gen/F-008-save-runs-for-the-take/real/mf-hook.json
diff -r gen/base/real/mf-sub-crm-mail.json gen/F-008-save-runs-for-the-take/real/mf-sub-crm-mail.json
-- F-008-save-runs-for-the-take/film
diff -r gen/base/film/mf-form.json gen/F-008-save-runs-for-the-take/film/mf-form.json
diff -r gen/base/film/mf-hook.json gen/F-008-save-runs-for-the-take/film/mf-hook.json
diff -r gen/base/film/mf-sub-crm-mail.json gen/F-008-save-runs-for-the-take/film/mf-sub-crm-mail.json
```

## Extra checks (raw results)
- F-002 (all and alone, real and film): KeyOk, ReplyBadKey, ReplyStoreFail exist in mf-form and mf-hook. Links: Valid->KeyOk; KeyOk out0->Claim, out1->ReplyBadKey; Claim out0->Claimed, out1->ReplyStoreFail. Nodes 12 -> 15, connections 11 -> 14. mf-recovery and mf-sub-crm-mail byte-identical to baseline.
- F-008 (all and alone): saveDataSuccessExecution and saveDataErrorExecution = all in mf-form, mf-hook, mf-sub-crm-mail; mf-recovery = none, and equals the saved real-v5 recovery as parsed JSON. Node and connection counts unchanged (12/12/10/20).
- Unpatched generator output is byte-identical (cmp) to saved real-v5 and film-v5 for all 4 files each (8 of 8). No difference.
- F-001: CREATE TABLE text in patched mf_leads.sql contains alert_sent, alert_token, alert_until, alert_attempts (lines 14-17 of the table block).
- F-003, F-004, F-001, build_mainframe.py: 0 conflict markers, strict UTF-8 read ok, no .orig/.rej files; patched build_mainframe.py py_compile ok.
- Orphan rule in checker: node never targeted by a connection and whose type does not contain "trigger" or "webhook".

# Evidence Q18 (EVIDENCE RUNNER: raw output, no judgement)

## Version note
Run 2026-11-16 (UTC). Repo HEAD: dd25464db3aba12b7be00d2bd35054aee208c842 (git status at start: only untracked handover/flows-audit/reviews/sweep2-one-place.md, not in scope).
Work copy: /tmp/f8ev7 (handover/demo, flows-audit/flow-check, tools, patches); removed at the end. Tools: ruff 0.16.9, bandit 1.9.4, python Python 3.13.18.
sha256 before the runs (source files, and again after all mutants were restored in the copy: identical, checked with diff; source files in the repo also unchanged):
```
ce315643d3405b568beb3fbabe90055a0dc201be9f1b91c49ef243c5e77439a5  flow-check/check_flows.py
503c46b8222a751774dde865d0b4f92b704fcde64723f83de9e73c87275d31de  flow-check/take_check.sh
38c4b4d2aeb10836c947158acc960e5ad3671a04d8bd1b3fe2a016ef6e9b6361  flow-check/run_all.sh
91718d303e16930f57c214e3ddbe161a860877b9fc9809b4cd61bdc7220ac218  flow-check/selftest.py
c38a03bb214b4212bbfbe9955655dd4d2e834e70fd224cd80dd84d84eda8aff4  patches/F-008-save-runs-for-the-take.patch
```
sha256 after restore (copy):
```
ce315643d3405b568beb3fbabe90055a0dc201be9f1b91c49ef243c5e77439a5  flow-check/check_flows.py
503c46b8222a751774dde865d0b4f92b704fcde64723f83de9e73c87275d31de  flow-check/take_check.sh
38c4b4d2aeb10836c947158acc960e5ad3671a04d8bd1b3fe2a016ef6e9b6361  flow-check/run_all.sh
91718d303e16930f57c214e3ddbe161a860877b9fc9809b4cd61bdc7220ac218  flow-check/selftest.py
c38a03bb214b4212bbfbe9955655dd4d2e834e70fd224cd80dd84d84eda8aff4  patches/F-008-save-runs-for-the-take.patch
```

## (1) bash run_all.sh   (rc in file: rc=0)
```
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 7 s
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
[selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

real	0m8.815s
user	0m7.140s
sys	0m1.782s
```

## (2) sh tools/check_patches.sh (from the copy root)
```
PASS 4 patches
rc=0
```

## (3) lint on flow-check
ruff check .
```
All checks passed!
rc=0
```
ruff format --check check_flows.py selftest.py  (rc=1: FAILS, 2 files would be reformatted; whole-folder run says 2 files would be reformatted, 29 already formatted)
```

2 files would be reformatted
rc=1
--- full diff list in the whole-folder run:
unformatted: File would be reformatted
    --> check_flows.py:77:18
unformatted: File would be reformatted
    --> selftest.py:105:17
```
bandit -ll -r check_flows.py selftest.py (rc=0)
```

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 4151
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
rc=0
```
bandit -ll -r . (whole folder): rc=0
grep -c 'noqa|nosec|type: ignore':
```
check_flows.py: 0
selftest.py: 0
```

## (4) take_check.sh scenarios (exit code and lines ACCEPTED / INFO / !!! / FINAL; full output of each kept in the run, lines cut at 330 chars)
### unpatched
```
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
ACCEPTED: recovery flow not part of the take (decision 4): demo/n8n-flows-real-v5/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery c
FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 21. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```
### patched
```
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/patched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; th
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/patched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery 
FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 15. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=0
```
### form-save-manual-false
```
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/formoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; th
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/formoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery 
FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```
### recovery-accept-removed
```
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```
### sub-saving-off
```
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/subsaveoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails;
!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/subsaveoff/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recove
FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```
### change-me-mail
```
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/changeme/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; t
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/changeme/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery
FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 15. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=0
```
### table-missing
```
!!! THE TABLE FILE IS MISSING: demo/n8n-flows-v4/mf_leads.sql was not found, so the column names in the SQL steps were NOT checked. On the older table the alert steps fail on every run and no alert is sent. This script exits 4.
INFO: mf-form.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-hook.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
INFO: mf-sub-crm-mail.json run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up.
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/patched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; th
ACCEPTED: recovery flow not part of the take (decision 4): /tmp/f8ev7/w/sc/patched/mf-recovery.json keeps run-saving settings ['saveDataSuccessExecution', 'saveDataErrorExecution', 'saveManualExecutions'] off on purpose (it fires every 30 s, so saved runs would pile up with lead keys and e-mails; the one video makes no recovery 
FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
rc=4
```
### change-me-mail: placeholder lines
```
19:  - /tmp/f8ev7/w/sc/changeme/mf-sub-crm-mail.json node SendMail setting 'fromEmail': CHANGE_ME
93:WARN /tmp/f8ev7/w/sc/changeme/mf-sub-crm-mail.json 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: CHANGE_ME; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-credent
107:  - /tmp/f8ev7/w/sc/changeme/mf-sub-crm-mail.json node SendMail setting 'fromEmail': CHANGE_ME
149:  - /tmp/f8ev7/w/sc/changeme/mf-sub-crm-mail.json: 2 value(s) in node settings are still placeholders; these must be filled before import: SendMail fromEmail: CHANGE_ME; SendMail toEmail: INTAKE_ADDRESS_PLACEHOLDER [run with --require-real-creden
```
Scenario notes: recovery-accept-removed = a copy of take_check.sh with the line '--accept-no-save mf-recovery.json' deleted, run on the patched copy. form-save-manual-false = patched copy with mf-form.json settings.saveManualExecutions=false. sub-saving-off = sub-workflow success/error saving none and manual false. table-missing = TAKE_CHECK_DDL pointing to a file that does not exist.

## (5) 12 mutants (applied in the copy, run_all.sh each, restored). Killed = run_all exit status not 0.
```
M1 check_flows.py | schedule-only rule removed | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=1] SELFTEST: 657 as expected, 2 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 1
M2 check_flows.py | blanket accept: any --accept-no-save name excuses every flow | run_all rc=0 | SURVIVED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 0
M3 check_flows.py | accept matched by prefix mf- instead of exact file name | run_all rc=0 | SURVIVED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 0
M4 check_flows.py | idle-accept WARN loop removed | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=1] SELFTEST: 657 as expected, 2 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: [take_check recovery-accept-idle: want exit 4 and 'accept-no-save --accept-no-save mf-recovery.json excused nothing', got exit 0] // run_all exit status (real-v5 default runs + self-test): 1
M5 take_check.sh | take names mf-form.json instead of mf-recovery.json in --accept-no-save | run_all rc=1 | KILLED
   
M6 check_flows.py | F008 check expects saveManualExecutions True also for recovery | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=1] SELFTEST: 639 as expected, 20 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 1
M7 check_flows.py | F008 check of saveManualExecutions disabled | run_all rc=0 | SURVIVED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 0
M8 check_flows.py | saveManualExecutions False no longer counted as saving off | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=1] SELFTEST: 657 as expected, 2 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 1
M9 check_flows.py | F008 check expects 'all' also for recovery | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=1] SELFTEST: 639 as expected, 20 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 1
M10 take_check.sh | idle accept WARN no longer makes exit 4 | run_all rc=0 | SURVIVED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 0
M11 take_check.sh | exit 4 for PROBLEMS removed | run_all rc=1 | KILLED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: [take_check unpatched-run-saving: want exit 4 and 'A FLOW THAT THE TAKE USES HAS RUN SAVING OFF', got exit 0] [take_check form-run-saving-off: want exit 4 and 'mf-form.json this flow's run-saving settings', got exit 0] [take_check sub-run-saving-off: want exit 4 and 'mf-sub-crm-mail.json this flow's run-saving settings', got exit 0] [t
M12 take_check.sh | FINAL line always prints exit status 0 | run_all rc=0 | SURVIVED
   [pristine] // [patched] // [selftest exit=0] SELFTEST: 659 as expected, 0 not as expected, 62 skipped (not applicable) // [take_check.sh exit=0] missing lines: none // run_all exit status (real-v5 default runs + self-test): 0
```
M5 detail: run_all.sh aborted with: run_all.sh: line 76: TCMISS: unbound variable (rc=1), i.e. killed by a crash of run_all.sh, not by a clean check line.
M10 detail: the idle-accept WARN text contains the words 'run-saving settings', so the first grep alternative still matches; the removed alternative changes no outcome on these inputs.
Survivors: M2 (blanket accept), M3 (prefix match), M7 (F008 saveManualExecutions check off), M10, M12 (FINAL line prints 0 always).

# Evidence f8-r12 runner 2 (raw output, no judgement)
head sha: ad2e41fe5
scratch folder (mktemp): /tmp/tmp.3whPERNHWd
start UTC: 2026-11-16T19:10:30Z
## 1 bash -n
bash -n repeat_run_all.sh rc=0
bash -n run_all.sh rc=0
bash -n take_check.sh rc=0
bash -n test_run_all_raw.sh rc=0
bash -n test_run_all_stop.sh rc=0
bash -n test_take_check.sh rc=0

## 2-test_run_all_stop
command: timeout 900 bash test_run_all_stop.sh
start UTC: 19:10:30  end UTC: 19:10:40  rc=0
```
ok   A-sigterm: the self-test of the run is running (waited up to 150 s)
ok   A-sigterm: the run ended within 40 s of SIGTERM
ok   A-sigterm: exit status 143 (got 143)
ok   A-sigterm: no process of the run is left (checkers, self-test, take script, nested runs)
ok   A-sigterm: the run says it was interrupted
ok   A-sigterm: the raw output of the interrupted run is kept and named (/tmp/trs.BG2b8h/tmp-A-sigterm/fc8raw.3H4OeT)
ok   A-sigterm: the work folder the run made itself is removed from TMPDIR (found: fc8raw.3H4OeT )
ok   B-sigint: the self-test of the run is running (waited up to 150 s)
ok   B-sigint: the run ended within 40 s of SIGINT
ok   B-sigint: exit status 130 (got 130)
ok   B-sigint: no process of the run is left (checkers, self-test, take script, nested runs)
ok   B-sigint: the run says it was interrupted
ok   B-sigint: the raw output of the interrupted run is kept and named (/tmp/trs.BG2b8h/tmp-B-sigint/fc8raw.TrgYnM)
ok   B-sigint: a work folder given on the command line is NOT removed
ok   C-sighup: the self-test of the run is running (waited up to 150 s)
ok   C-sighup: the run ended within 40 s of SIGHUP
ok   C-sighup: exit status 129 (got 129)
ok   C-sighup: no process of the run is left (checkers, self-test, take script, nested runs)
ok   C-sighup: the run says it was interrupted
ok   C-sighup: the raw output of the interrupted run is kept and named (/tmp/trs.BG2b8h/tmp-C-sighup/fc8raw.miYM7y)
ok   C-sighup: a work folder given on the command line is NOT removed
ok   D-limit: the stand-in self-test (sleeps 10 minutes) is running
ok   D-limit: it is stopped by the 3-second limit (within 25 s) while the run goes on
ok   D-limit: the run itself is still going (the limit stopped the step, not the run)
ok   D-limit: no process of the run is left after SIGTERM
test_run_all_stop: 25 of 25 cases as expected, 0 not as expected
```

## 3-test_run_all_raw
command: timeout 1500 bash test_run_all_raw.sh
start UTC: 19:10:40  end UTC: 19:22:36  rc=1
```
ok   run exits 0 while another process truncates every file of its raw folder (got exit 0)
ok   no 'summary line missing' text in the run output
ok   the untouched sentinel file in the raw folder is unchanged
ok   the raw folder holds exactly the same file names as before the run (before: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt | after: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt )
FAIL phase 2: a passing run with --refresh exits 0 (got exit 1)
ok   phase 2: the run's own raw folder is named in its output (--keep) (/tmp/fc8raw.tKTZty)
FAIL phase 2: all 40 raw files of the run are in raw/ byte for byte (40 differ)
FAIL phase 2: refresh-manifest.txt lists exactly the files of this run with their sha256 (not the older file)
ok   phase 2: the file of an older run is left alone and no temporary file stays
FAIL phase 2: the run says that raw/ was refreshed and prints exit status 0
ok   phase 3: a failing run exits 1 (got exit 1)
ok   phase 3: a failing run with --refresh publishes nothing (raw/ holds: older-run-only.txt )
ok   phase 3: the run says raw/ was NOT refreshed and prints exit status 1
test_run_all_raw: 9 of 13 cases as expected, 4 not as expected
last lines of the run outputs:
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
raw/ was NOT refreshed: this run did not pass (its raw files are kept in /tmp/fc8raw.tKTZty)
raw output of this run is kept in: /tmp/fc8raw.tKTZty   (it is not removed later by this script; delete it with rm -rf when it is no longer needed)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
raw/ was NOT refreshed: this run did not pass (its raw files are kept in /tmp/fc8raw.cLT138)
raw output of this run is kept in: /tmp/fc8raw.cLT138   (it is not removed later by this script; delete it with rm -rf when it is no longer needed)
```

## 4-test_take_check
command: timeout 900 bash test_take_check.sh
start UTC: 19:22:36  end UTC: 19:22:36  rc=2
```
script under test: /home/user/hadavin-sdk/handover/flows-audit/flow-check/take_check.sh
usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]
```

## 5-run_all
command: timeout 1800 bash run_all.sh
start UTC: 19:22:36  end UTC: 19:27:14  rc=0
```
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
[selftest exit=0] SELFTEST: 725 as expected, 0 not as expected, 62 skipped (not applicable)
COUNTS match expected-counts.pin: self-test 725 as expected / 0 not / 62 skipped; take suite 574 of 574 cases
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
tracked raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw was NOT changed (pass --refresh to publish this run's raw files)
```

## 5b git status/diff of raw
```
---diff stat
```
old mirror files: check_flows.py expected-counts.pin run_all.sh selftest.py take-warns.pin take_check.sh test_run_all_raw.sh test_run_all_stop.sh test_take_check.sh 

## 6a-OLD-test_run_all_stop
command: timeout 900 bash test_run_all_stop.sh
start UTC: 19:27:14  end UTC: 19:35:04  rc=1
```
ok   A-sigterm: no process of the run is left (checkers, self-test, take script, nested runs)
FAIL A-sigterm: the run says it was interrupted
ok   A-sigterm: the raw output of the interrupted run is kept and named (/tmp/trs.ExUugC/tmp-A-sigterm/fc8raw.Z6DNID)
ok   A-sigterm: the work folder the run made itself is removed from TMPDIR (found: fc8raw.5iNWda fc8raw.9ig2V6 fc8raw.AorXrB fc8raw.DvOnXq fc8raw.Z6DNID )
ok   B-sigint: the self-test of the run is running (waited up to 150 s)
FAIL B-sigint: the run ended within 40 s of SIGINT
FAIL B-sigint: exit status 130 (got 1)
ok   B-sigint: no process of the run is left (checkers, self-test, take script, nested runs)
FAIL B-sigint: the run says it was interrupted
ok   B-sigint: the raw output of the interrupted run is kept and named (/tmp/trs.ExUugC/tmp-B-sigint/fc8raw.Yb7GII)
ok   B-sigint: a work folder given on the command line is NOT removed
ok   C-sighup: the self-test of the run is running (waited up to 150 s)
ok   C-sighup: the run ended within 40 s of SIGHUP
ok   C-sighup: exit status 129 (got 129)
FAIL C-sighup: no process of the run is left (checkers, self-test, take script, nested runs)
FAIL C-sighup: the run says it was interrupted
ok   C-sighup: the raw output of the interrupted run is kept and named (/tmp/trs.ExUugC/tmp-C-sighup/fc8raw.ciHwAU)
ok   C-sighup: a work folder given on the command line is NOT removed
ok   D-limit: the stand-in self-test (sleeps 10 minutes) is running
FAIL D-limit: it is stopped by the 3-second limit (within 25 s) while the run goes on
ok   D-limit: the run itself is still going (the limit stopped the step, not the run)
FAIL D-limit: no process of the run is left after SIGTERM
test_run_all_stop: 16 of 25 cases as expected, 9 not as expected
last lines of the outputs:
[/tmp/trs.ExUugC/out-A-sigterm.txt]
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
raw output of this run is kept in: /tmp/trs.ExUugC/tmp-A-sigterm/fc8raw.Z6DNID
[/tmp/trs.ExUugC/out-B-sigint.txt]
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
tracked raw folder /tmp/trs.ExUugC/raw-B-sigint was NOT changed (pass --refresh to publish this run's raw files)
raw output of this run is kept in: /tmp/trs.ExUugC/tmp-B-sigint/fc8raw.Yb7GII
[/tmp/trs.ExUugC/out-C-sighup.txt]
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
raw output of this run is kept in: /tmp/trs.ExUugC/tmp-C-sighup/fc8raw.ciHwAU
[/tmp/trs.ExUugC/out-D-limit.txt]
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
raw output of this run is kept in: /tmp/trs.ExUugC/tmp-D-limit/fc8raw.2SJqM1
```

## 6b-OLD-test_run_all_raw
command: timeout 900 bash test_run_all_raw.sh
start UTC: 19:35:04  end UTC: 19:46:28  rc=1
```
FAIL run exits 0 while another process truncates every file of its raw folder (got exit 1)
ok   no 'summary line missing' text in the run output
ok   the untouched sentinel file in the raw folder is unchanged
ok   the raw folder holds exactly the same file names as before the run (before: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt | after: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt )
last lines of the run output (phase 1):
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
tracked raw folder /tmp/tra.bglQdd/rawfolder was NOT changed (pass --refresh to publish this run's raw files)
raw output of this run is kept in: /tmp/fc8raw.otwcX1
FAIL phase 2: a passing run with --refresh exits 0 (got exit 1)
ok   phase 2: the run's own raw folder is named in its output (--keep) (/tmp/fc8raw.Y7NPCi)
ok   phase 2: all 40 raw files of the run are in raw/ byte for byte (0 differ)
FAIL phase 2: refresh-manifest.txt lists exactly the files of this run with their sha256 (not the older file)
ok   phase 2: the file of an older run is left alone and no temporary file stays
FAIL phase 2: the run says that raw/ was refreshed and prints exit status 0
ok   phase 3: a failing run exits 1 (got exit 1)
FAIL phase 3: a failing run with --refresh publishes nothing (raw/ holds: apply.log diff-film.txt diff-real.txt gen-film.log gen-real.log nested-take-failure-b.txt nested-take-failure-c.txt nested-take-failure-d.txt nested-take-failure.txt older-run-only.txt patched-film.txt patched-flows-list.txt patched-strict-film.txt patched-strict.txt patched.txt pristine-film.txt pristine-no-baseline.txt pristine-strict-film.txt pristine-strict.txt pristine.txt selftest-new.txt take-check-bad-ddl.txt take-check-disabled-send.txt take-check-exit3.txt take-check-form-run-saving-odd-word.txt take-check-form-run-saving-off.txt take-check-hook-run-saving-block-empty.txt take-check-key-check-absent-is-exit-4.txt take-check-keyok-gone.txt take-check-new-warn-changes-the-pin.txt take-check-no-table-file.txt take-check-old-table.txt take-check-recovery-accept-idle.txt take-check-sub-run-saving-key-missing.txt take-check-sub-run-saving-off.txt take-check-unpatched-run-saving.txt take-check-warn-pin-file-missing.txt take-check-zero-queries.txt take-check.txt test-take-check.txt timing.txt )
FAIL phase 3: the run says raw/ was NOT refreshed and prints exit status 1
test_run_all_raw: 7 of 13 cases as expected, 6 not as expected
last lines of the run outputs:
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
raw files refreshed in /tmp/tra.bglQdd/m2/handover/flows-audit/flow-check/raw: 40 (run exit status 1)
raw output of this run is kept in: /tmp/fc8raw.Y7NPCi
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
raw files refreshed in /tmp/tra.bglQdd/m3/handover/flows-audit/flow-check/raw: 40 (run exit status 1)
raw output of this run is kept in: /tmp/fc8raw.wh0AUS
```

## 7
```
--- git status --short
 M ../FINDINGS.md
 M ../LEDGER-ROWS.md
 M evidence-f8-r12-runner2.md
```
elapsed s: 2158
end UTC: 2026-11-16T19:46:28Z

# Evidence f8-r13 fixer (raw output, final head of this fixer; nothing committed)
Scratch folder of the driver: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad. Each command's stdout+stderr went to a log; rc taken from the command itself (no pipe). UTC 2026-11-16.

## bash test_run_all_stop.sh
start UTC 20:13:32  end UTC 20:16:17  rc=0
```
ok   C-sighup: the run ended within 40 s of SIGHUP
ok   C-sighup: exit status 129 (got 129)
ok   C-sighup: no process of the run is left (checkers, self-test, take script, nested runs)
ok   C-sighup: no process of the run's own session is left (found by session id, not by command line)
ok   C-sighup: the run says it was interrupted
ok   C-sighup: the raw output of the interrupted run is kept and named (/tmp/trs.fNiSG4/tmp-C-sighup/fc8raw.CcmWz0)
ok   C-sighup: a work folder given on the command line is NOT removed
ok   E-sigterm-checkers: a checker run of the run is running (waited up to 400 s)
ok   E-sigterm-checkers: the run ended within 40 s of SIGTERM
ok   E-sigterm-checkers: exit status 143 (got 143)
ok   E-sigterm-checkers: no process of the run is left (checkers, self-test, take script, nested runs)
ok   E-sigterm-checkers: no process of the run's own session is left (found by session id, not by command line)
ok   E-sigterm-checkers: the run says it was interrupted
ok   E-sigterm-checkers: the raw output of the interrupted run is kept and named (/tmp/trs.fNiSG4/tmp-E-sigterm-checkers/fc8raw.GFLt4G)
ok   E-sigterm-checkers: a work folder given on the command line is NOT removed
ok   F-sigint-suite: the take test suite of the run is running (waited up to 400 s)
ok   F-sigint-suite: the run ended within 40 s of SIGINT
ok   F-sigint-suite: exit status 130 (got 130)
ok   F-sigint-suite: no process of the run is left (checkers, self-test, take script, nested runs)
ok   F-sigint-suite: no process of the run's own session is left (found by session id, not by command line)
ok   F-sigint-suite: the run says it was interrupted
ok   F-sigint-suite: the raw output of the interrupted run is kept and named (/tmp/trs.fNiSG4/tmp-F-sigint-suite/fc8raw.S99Pqv)
ok   F-sigint-suite: a work folder given on the command line is NOT removed
ok   G-sighup-nested: the nested test runs of the run is running (waited up to 400 s)
ok   G-sighup-nested: the run ended within 40 s of SIGHUP
ok   G-sighup-nested: exit status 129 (got 129)
ok   G-sighup-nested: no process of the run is left (checkers, self-test, take script, nested runs)
ok   G-sighup-nested: no process of the run's own session is left (found by session id, not by command line)
ok   G-sighup-nested: the run says it was interrupted
ok   G-sighup-nested: the raw output of the interrupted run is kept and named (/tmp/trs.fNiSG4/tmp-G-sighup-nested/fc8raw.nrZgX6)
ok   G-sighup-nested: a work folder given on the command line is NOT removed
ok   H-double-sigterm: the patched flows for selftest.py were built (set-up)
ok   H-double-sigterm: selftest.py given two SIGTERM in a row exits 143 and leaves no work folder, 5 tries (0 went wrong)
ok   D-limit: the stand-in self-test (sleeps 10 minutes) is running
ok   D-limit: it is stopped by the 3-second limit (within 25 s) while the run goes on
ok   D-limit: the run itself is still going (the limit stopped the step, not the run)
ok   D-limit: exit status 143 after the stop (got 143), not 0
ok   D-limit: no process of the run is left after SIGTERM
ok   D-limit: no process of the run's own session is left (by session id)
test_run_all_stop: 56 of 56 cases as expected, 0 not as expected
```

## bash test_run_all_raw.sh
start UTC 20:16:17  end UTC 20:27:59  rc=0
```
ok   run exits 0 while another process truncates every file of its raw folder (got exit 0)
ok   no 'summary line missing' text in the run output
ok   the untouched sentinel file in the raw folder is unchanged
ok   the raw folder holds exactly the same file names as before the run (before: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt | after: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt )
ok   phase 2: a passing run with --refresh exits 0 (got exit 0)
ok   phase 2: the run's own raw folder is named in its output (--keep) (/tmp/fc8raw.1sSZUZ)
ok   phase 2: all 40 raw files of the run are in raw/ byte for byte (0 differ)
ok   phase 2: refresh-manifest.txt lists exactly the files of this run with their sha256 (not the older file)
ok   phase 2: the file of an older run is left alone and no temporary file stays
ok   phase 2: the run says that raw/ was refreshed and prints exit status 0
ok   phase 3: a failing run exits 1 (got exit 1)
ok   phase 3: a failing run with --refresh publishes nothing (raw/ holds: older-run-only.txt )
ok   phase 3: the run failed for the planted reason only (COUNT DRIFT on the pinned self-test count, take check clean), says raw/ was NOT refreshed and prints exit status 1
test_run_all_raw: 13 of 13 cases as expected, 0 not as expected
```

## bash run_all.sh
start UTC 20:27:59  end UTC 20:32:45  rc=0
```
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
COUNTS match expected-counts.pin: self-test 725 as expected / 0 not / 62 skipped; take suite 592 of 592 cases
[take_check.sh exit=5] missing lines: none
[checker result lines] each of the five real-v5 files has exactly one RESULT line that agrees with its exit status
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'ses
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
tracked raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw was NOT changed (pass --refresh to publish this run's raw files)
```

## format and guard checks (from handover/flows-audit)
```
ruff format --check . : 65 files already formatted
python3 -I tools/check_refs.py rc=0 : PASS 5190 references
python3 -I tools/check_names.py rc=0 : PASS 655 rows
python3 -I tools/check_secrets.py rc=0 : PASS 0 hits in 3015 files
python3 -I tools/check_counts.py rc=0 : PASS 52 files / 655 nodes
```

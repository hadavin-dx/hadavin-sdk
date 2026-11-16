# evidence-f8-r13-runner (raw, no judgement)

## (1) git rev-parse / status
start/end UTC: 2026-11-16T20:33:56Z ; rc=0 ; load before: load average 2.68 4.93 4.55
```
449ccacd5
3
```
(HEAD seen after run 3: 72505e5c8; tracked changes differ between checks, other sessions are editing the repo)

## (2) bash run_all.sh
start UTC: 2026-11-16T20:33:59Z ; end UTC: 2026-11-16T20:38:19Z ; rc: 0 ; load before: load average: 2.71, 4.90, 4.54 ; stray processes after: 0
last 15 lines:
```
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
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
tracked raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw was NOT changed (pass --refresh to publish this run's raw files)
```

## (3) bash test_run_all_stop.sh
start UTC: 2026-11-16T20:38:23Z ; end UTC: 2026-11-16T20:41:04Z ; rc: 0 ; load before: load average: 5.72, 4.75, 4.48 ; stray processes after: 0
last 15 lines:
```
ok   G-sighup-nested: exit status 129 (got 129)
ok   G-sighup-nested: no process of the run is left (checkers, self-test, take script, nested runs)
ok   G-sighup-nested: no process of the run's own session is left (found by session id, not by command line)
ok   G-sighup-nested: the run says it was interrupted
ok   G-sighup-nested: the raw output of the interrupted run is kept and named (/tmp/trs.wgrDdL/tmp-G-sighup-nested/fc8raw.O0Ijqs)
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

## git status --short after run 2
```
 M ../reviews-of-core-patches/patch-copies/README.md
?? ../reviews/fix-runbook67.md
```
## after run 3
```
 M ../RUNSHEET-WORDING.md
?? ../reviews/fix-rw42.md
```
Raw logs: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8-r13/

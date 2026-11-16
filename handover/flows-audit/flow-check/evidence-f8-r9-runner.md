# Evidence f8-r9 (EVIDENCE RUNNER; raw output, no judgement)
Head: d527d4263   written 2026-11-16T15:46:54Z   cwd flow-check   host-run alone (ps before/after each run: no run_all/take_check/selftest process outside the script's own nested copies)
Note: run_all.sh itself rewrites tracked files under flow-check/raw/ (git status shows raw/nested-take-failure*.txt, raw/timing.txt modified). I edited no other file.
Full raw logs: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/run1.log run2.log run3.log runs.log (strict) and /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8r9-15208/{run-extra,run4,run5,ttc,ruff-fmt,ruff-chk,secrets,bashn}.log

## (1) run_all.sh run 1  start/end UTC: 2026-11-16T15:09:56Z 2026-11-16T15:14:40Z  exit=1
```
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST summary line missing in raw/selftest-new.txt
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## (1) run_all.sh run 2  start/end UTC: 2026-11-16T15:14:44Z 2026-11-16T15:19:01Z  exit=1
```
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST summary line missing in raw/selftest-new.txt
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## (1) run_all.sh run 3  start/end UTC: 2026-11-16T15:19:01Z 2026-11-16T15:24:03Z  exit=0
```
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## (2) run_all.sh --strict  UTC: 2026-11-16T15:24:09Z 2026-11-16T15:28:28Z  exit=1
```
######## pristine-strict film
RESULT: 8 FAIL, 13 WARN
Known open problems: 7
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 8 FAIL, 12 WARN
Known open problems: 6
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 6 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'session'), so a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## extra run A (run_all.sh <new work dir>, not asked for)  exit=1
```
######## pristine-strict film
RESULT: 8 FAIL, 13 WARN
Known open problems: 7
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 8 FAIL, 12 WARN
Known open problems: 6
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 6 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'ses
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## extra run B (plain run_all.sh, with ps sampler every 8 s)  exit=0
```
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
## extra run C (run_all.sh <new work dir>)  exit=0
```
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
run_all exit status (real-v5 default runs + self-test): 0
```
## (3) bash test_take_check.sh <patched real folder from run A> <new scratch>  UTC: 2026-11-16T15:35:00Z 2026-11-16T15:36:45Z  exit=0
```
ok   f8-r9: a file changed in the ORIGINAL folder while the checker read the private copy is still caught at the end (exit 4) (got exit 4)
ok   f8-r9 M1(second angle): a mail field filled with a made-up bad value is reported by name only: the value is absent from stdout, stderr and the written pin (planted: 0, exit 4)
test_take_check: 496 of 496 cases as expected, 0 not as expected
lines starting FAIL: 0
```
## (4) ruff
```
ruff format --check . exit=0: 56 files already formatted
ruff check . exit=0: All checks passed!
```
## (5) python3 -I tools/check_secrets.py (from flow-check/..)  exit=0
```
PASS 0 hits in 2027 files
```
## (6) bash -n
```
bash -n run_all.sh rc=0
bash -n take_check.sh rc=0
bash -n test_take_check.sh rc=0
```
## ps samples during extra run B
```
     17  bash /home/user/hadavin-sdk/handover/flows-audit/flow-check/run_all.sh /tmp/fc8.Hx0LYZ/tc/nested-work
     17  bash /home/user/hadavin-sdk/handover/flows-audit/flow-check/run_all.sh /tmp/fc8.Hx0LYZ/tc/nested-work-b
     17  bash /home/user/hadavin-sdk/handover/flows-audit/flow-check/run_all.sh /tmp/fc8.Hx0LYZ/tc/nested-work-c
     17  bash /home/user/hadavin-sdk/handover/flows-audit/flow-check/run_all.sh /tmp/fc8.Hx0LYZ/tc/nested-work-d
     34  bash run_all.sh
     34  timeout 1200 bash run_all.sh
```

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

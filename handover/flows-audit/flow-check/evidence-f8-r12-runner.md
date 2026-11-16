# Evidence f8 r12 (runner, no verdict)
Scratch folder (raw outputs): /tmp/tmp.s4mISj1LRO (kept; not removed). Window 18:00-18:27 UTC (23:30-23:57 IST). Commands run from flow-check/ unless noted.

## Exit codes (from log.txt)
rc=0 run1
rc=0 run2
rc=0 run3
rc=0 testraw
rc=0 repeat2
rc=2 hostile_FC_CK
rc=2 hostile_TTD
rc=0 ruff
rc=0 secrets

## Odd things
- Other agents ran at the same time on this machine. git status before showed 2 modified files (CLAIMS-TABLE.md, RUNSHEET-WORDING.md); after showed none, because commits 822369b0f (18:26:11) and 4d7925921 (18:27:34) landed during my window. Not made by this runner.
- Load before: load average: 1.23, 3.26, 3.88; after: load average: 5.59, 4.67, 4.25
- take_check.sh line reads exit=5 in every run with 'missing lines: none'; run_all exit status line is 0.
- Each run took about 4.3 min; the repeat test (2 runs) and test_run_all_raw ran sequentially, after run3.

## run_all.sh runs 1,2,3 (stdout summary lines, identical in all three)
[selftest exit=0] SELFTEST: 725 as expected, 0 not as expected, 62 skipped (not applicable)
COUNTS match expected-counts.pin: self-test 725 as expected / 0 not / 62 skipped; take suite 555 of 555 cases
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
Only line that differs between the three runs (clock times removed): the "checker runs wall time / self-test wall time" line (0 s/7 s, 1 s/7 s, 0 s/9 s).

## test_run_all_raw.sh (exit 0)
ok   the raw folder holds exactly the same file names as before the run (before: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt | after: apply.log gen-real.log selftest-new.txt sentinel.txt take-check.txt )
test_run_all_raw: 4 of 4 cases as expected, 0 not as expected

## repeat_run_all.sh 2 (exit 0)
run 1: exit 0, 23 summary lines
run 2: exit 0, 23 summary lines
repeat_run_all: 2 runs, 0 problems

## raw/ md5 before vs after: diff empty (identical), 56 files

## ruff format --check . (flows-audit): exit 0: 931 files already formatted
## python3 -I tools/check_secrets.py: exit 0: PASS 0 hits in 2805 files

## Hostile inputs
FC_CK=1: exit 2. First line: REFUSED: FC_CK is set. It is a test hook of selftest.py / test_take_check.sh and would change what this script checks; u
TEST_TAKE_DEV=1: exit 2. First line: REFUSED: TEST_TAKE_DEV is set. It is a test hook of selftest.py / test_take_check.sh and would change what this script c

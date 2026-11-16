# Lane C (tests and evidence) review of round 37, head ec992c2 vs r36 ad010b7 (egm-implementation-readiness a5eb7f9a; saved by the lead, condensed; read-only, ran nothing)

Verdict: no Blocker, 2 Major, 6 Minor X, Y notes. Mutant evidence honest, fail-before real, earlier X-1..X-8 mostly closed. Two claims do not hold: head-1 test has no mutant behind it; uncapped scan ran on 3bc7b42, not ec992c2.

## Holds
76 mutants + 1 control (k1-24, s1-14 + s16-18, n1-14, r1-21; s15 never existed); control 67 tests passed; all 76 rc=1, no -x, diff printed before each pytest output; control selector = union of all selectors; all 76 failure blocks belong to the mutated line (weak but real: s16 killed by different group-write message, s8 by the test's own `assert A != B` precondition at 2823, s4 by "n8n.pid is a folder" message, k20-k22 wording pins). First pass 3bc7b42 survivors r16, r21 fixed and whole set rerun at ec992c2 (final log shows fixed assertions). Fail-before 7 failed 184 passed 2 skipped, reasons match. 2 skips (575, 584) Windows-only, legitimate. Three WSL runs 641 passed 2 skipped (third under 12 busy loops). Scan counts r33 118 vs r37 117, only diff `5.15.167.4` gone and a wrapped-path entry.

## X
- X-1 MAJOR: head-1 test `test_r37_head_1_line_one_arrives_and_line_two_fails_the_rest_goes_to_stderr` has no mutant (report C-Y5 cites k1, k2, r2: none match; "head_1" in no selector or log). C-X4 mapping "s10-s14, n14" selects the probe-signal test, not `_holder_and_closed_pipe_run`; ready-marker and `_wait_holding` edits have no mutant (only the 100-run loop). Fix: head-1 selector + control entry + mutant making `_say` ignore `_dead` / send line 2 to stdout; correct the C-X4 mapping or add a mutant removing the marker wait (10+5).
- X-2 MAJOR: gate evidence at a different head: scan ran on "r37 3bc7b42"; ec992c2 edited tests/test_n8n_drive.py (r16 `_env_skip` try/except, r21 pins) = new strings and `except` lines; scan37.sh clones the tip at run time, HEAD line not saved; last offender in scan-uncapped-r37.txt is line 2957. Fix: rerun scan37.sh at ec992c2, save `== dir HEAD` lines, diff lists with line numbers stripped (5+5).
- X-3 Minor: head provenance asserted not recorded (logs' first line is a typed string; loop log's git rev-parse says ad010b7 because the WSL clone is r36 with three files overlaid); sha-wsl-vs-worktree.log has 3 hashes, no head, no timestamp, other files read by tests not covered. Fix: sha256sum before and after the mutant run in the same log, compared with git hash-object of the worktree (5+5).
- X-4 Minor: report line 54 "real-n8n test skipped" contradicts logs (exactly 2 skips 575 and 584, no real-n8n skip; neither switch set). Fix: run `-rA -k r23_real` once or state which (2+3).
- X-5 Minor: A-Y-e "fd 1 redirected BEFORE `_dead = True`" claimed covered by k1; k1 removes the dup2 entirely; no mutant swaps order, no test can see Ctrl-C between the lines. Say "not testable" or add a swap mutant (3+3).
- X-6 Minor: n14 identical to s10 (same TERM-trap deletion, same selector): 75 distinct mutants not 76. Say so or give n14 another mutation (1+1).
- X-7 Minor: 100x load loop covers only two r36 tests; new ready-marker/gate tests (`one_broken_pipe[plain]`, `head_1`) not in it; 0 of 100 bounds rate near 3%; INTERNALERROR "not reproduced" claim (WSL r37 13 failed 438 passed, WSL r33 same, Windows r37 13 failed 437 passed 1 skipped) has no log in b37-logs. Fix: loop the two new tests 100x under load, save the five-file run logs (10+5).
- X-8 Minor: wsl-run-1.log is at head c2af71f (640 passed), not ec992c2, unreferenced: move to superseded (1+1).

## Y
Y-1 `_start_setup` ancestor-skip rule has no mutant (disclosed; too-strict only causes skips, skips = 2). Y-2 s8 killed by text precondition; wording pins deliberate. Y-3 removed-switch-name test scans scripts/ and tests/*.py only (not workflows, runbook). Y-4 r5 selector `held` broad, kill on lslocks assertion. Y-5 scan list compares r33 not r36 (fine for gate). Y-6 REAL/TOOLS switches never set in final WSL runs; meta-tests cover them in a subprocess.

## Not checked
Ran no test, mutant or scan; did not read the rest of the 19000-line test file beyond diff and log references; no lint.yml, runbook, Git Bash, py3.8, non-reaping PID 1; same-files check beyond three sha256 values; whether new r37 lines add scan hits beyond line 2957 (X-2); no _local.

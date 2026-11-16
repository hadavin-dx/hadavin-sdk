# Evidence r10c (EVIDENCE RUNNER: raw results, no judgement)
Date (UTC): 2026-11-16 12:05:33. Run as uid 0 (root). Scratch: /tmp/r10c-ev (patched flows dir made by run_all.sh: /tmp/r10c-ev/w1/g/real; README names no fixed patched path, run_all.sh builds it under its WORKDIR/g/real).

## 1. Start state
- git status --short . (flow-check): '?? fix-f8-r10c.md' only. git clean -n .: 'Would remove fix-f8-r10c.md' and 'Would remove handover/' (flow-check/handover/, pre-existing untracked dir, not mine).
- At the end fix-f8-r10c.md no longer showed as untracked (I did not touch it; someone else changed it). flows-audit also shows '?? reviews/stranger-owner-steps-r7.md' (not mine).

## 2. run_all.sh twice (fresh WORKDIR each: /tmp/r10c-ev/w1, w2)
- run 1: exit 0, 57 s
- run 2: exit 0, 57 s
- Exit code stable (0 and 0). Note: the order of the last 15 lines differs a little between runs (parallel output: selftest line vs take_check line order).

### run 1 last 15 lines
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
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```
### run 2 last 15 lines
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
[selftest exit=0] args_unknown_option (exit 2)                                             as expected
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```

## 3. test_take_check.sh /tmp/r10c-ev/w1/g/real /tmp/r10c-ev/ttc3
exit and time: rc=0 secs=14
```
ok   Q5: a checker that exits 137 is shown as 137 and the take exits 3 (got exit 3)
ok   Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit 3)
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 44 of 44 cases as expected, 0 not as expected
```

## 4. Lint and security (from handover/flows-audit)
- ruff check . : exit 0 (All checks passed!), <1 s
- ruff format --check . : exit 1, <1 s. Output: 'unformatted: File would be reformatted --> inputs/plan-wp6-resmoke-v5.md:193:1' (a python snippet inside a .md file); '1 file would be reformatted, 467 files already formatted'. No file under flow-check or tools is named.
- bandit -ll -r flow-check tools : exit 1, 1 s. Summary tail printed 'Low: 48 / Medium: 1 / High: 5' (the tail does not say if that block is severity or confidence); Severity-High findings seen: B602 x2 in tools/scratch; Severity-Medium: B608 several in tools/scratch; findings are in tools/scratch/** (B602 shell=True in tools/scratch/run_evidence.py:7 and run_evidence2.py:7; B608 in tools/scratch/007/work/*/handover/demo/n8n-mainframe/build_mainframe.py). bandit -ll -r flow-check alone: 'No issues identified', exit 0.
```
7	    p=subprocess.run(cmd,shell=shell,capture_output=True,text=True,executable="/bin/bash")
8	    return p.returncode,(p.stdout+p.stderr)

--------------------------------------------------

Code scanned:
	Total lines of code: 7552
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 4
		Medium: 48
		High: 2
	Total issues (by confidence):
		Undefined: 0
		Low: 48
		Medium: 1
		High: 5
Files skipped (0):
```

## 5. Bare 'bash take_check.sh --flows <patched dir>'
exit 4, 1 s. Reason line: '!!! pin not yet confirmed by the lead: the reviewed-by line ... names a session or says the lead still has to confirm'. RESULT: 0 FAIL, 22 WARN. OVERRIDES: none. sha256 combined 989f5529...e5e666.
```
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (for example whether a repeated lead key still gets its answer, and whether a failed step reaches the failure line: only a test run in n8n can show it); whether the SQL inside the postgres nodes is correct (only the column names are compared, and only with --ddl); who calls a web address, whether the flow is active, and test versus production web address; expression syntax beyond node names; secrets in a s
Passing this check does NOT mean the flows are ready to film.
Open items counted: checker known open problems 16 + psql gate 1 + problems of this script 1 (entry flows without the key check: 0, counted inside the problems).
FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b1551395602ab1ac50d2a6625aecb007757dc42f968980e5e666. RESULT: 0 FAIL, 22 WARN. 22 pinned WARN lines stand for known defects that are not fixed. OVERRIDES: none. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 18. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming.
```

## 6. Hostile inputs (exit codes; times 0-1 s each)
```
empty rc=1 secs=0
missing rc=1 secs=1
unread rc=4 secs=0
nonexist rc=1 secs=1
extrawarn_pin_test1 rc=4 secs=0
extrawarn_pin_notest rc=4 secs=1
testflag_exported rc=4 secs=0
testflag_bare_committed rc=4 secs=0
```
Details (first '!!!' lines in raw logs /tmp/r10c-ev/hostile/*.log):
- empty flows dir: exit 1 (checker FAIL path; also prints 0 query strings and run saving off lines).
- missing mf-hook.json: exit 1 (checker cannot read a listed flow).
- non-existent flows dir: exit 1.
- unreadable file (chmod 000 on mf-recovery.json): exit 4, NOT a read failure, because the session runs as root (uid 0) and root reads it anyway. This case was NOT really tested as non-readable. Only reason lines: pin unconfirmed, WARN set unchanged.
- pin with an extra WARN line appended, TAKE_CHECK_TEST=1 + TAKE_CHECK_WARN_PIN: exit 4; reason lines include 'THE PIN FILE DOES NOT MATCH ITS OWN SHA-256' (caught by the hash, so the WARN-set difference path was not reached by this input). Same without the test flag: exit 4, same message (override ignored or flagged; OVERRIDES line not inspected in detail).
- TAKE_CHECK_TEST=1 exported by caller, bare take on patched dir: exit 4 (pin unconfirmed; OVERRIDES: none).
- TAKE_CHECK_TEST=1 exported, bare take on committed unpatched folder: exit 4 (run saving off, key check absent).

## Restore
- git checkout -- flow-check/raw flow-check/selftest-output run; git status --short . afterwards shows no change inside flow-check (git clean -n . still lists only the pre-existing handover/).
- I created only files under /tmp/r10c-ev (left in place, includes w1, w2 work copies and logs). Pre-existing /tmp/fc8* folders are not mine and were not touched. Nothing committed. No values from fill_flows printed.

## Not checked
- Real non-root unreadable-file case; a pin with an extra WARN line and a recomputed valid sha256; full output of run_all.sh beyond the last 15 lines (raw copies: /tmp/r10c-ev/run1.log, run2.log).

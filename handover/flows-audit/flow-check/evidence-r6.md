# evidence-r6 (EVIDENCE RUNNER, raw, no judging)
copy: /tmp/f8ev6 (removed at end). date 2026-11-16T10:51:52Z

## (1) bash run_all.sh

```
cd /tmp/f8ev6/handover/flows-audit/flow-check; bash run_all.sh > runall.out 2>&1; rc written separately
rc=0
--- full run_all output (stdout) ---
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 6 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 24 WARN
Known open problems: 18
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 26 WARN
Known open problems: 20
exit=0
[pristine-strict]
######## pristine-strict real
RESULT: 4 FAIL, 20 WARN
Known open problems: 14
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 22 WARN
Known open problems: 16
exit=1
[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)
RESULT: 2 FAIL, 23 WARN
exit=1
==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ====
[pristine-film]
######## pristine film
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
[patched-film]
######## patched film
RESULT: 0 FAIL, 24 WARN
Known open problems: 18
exit=0
[pristine-strict-film]
######## pristine-strict film
RESULT: 4 FAIL, 18 WARN
Known open problems: 12
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 20 WARN
Known open problems: 14
exit=1
[selftest exit=0] SELFTEST: 652 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=0] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```

Second run of run_all.sh with an explicit new WORKDIR (to keep the patched flows for scenario copies): rc=0 (see /tmp/f8ev6, removed).
After the mutant pass and restore: post-restore run_all rc=0. Mutated files byte-identical to saved copies (cmp): yes.

## (2) take_check.sh scenarios
Copy layout: /tmp/f8ev6/handover/{demo/..., flows-audit/{flow-check,patches}} (take_check.sh does cd $HERE/../..). Scenario inputs via the script's own env hooks TAKE_CHECK_FLOWS / TAKE_CHECK_DDL (no option exists for --ddl or --accept-if, so those two used a sed-edited copy of take_check.sh or a direct checker call). rc is printed by the shell from the command itself (no pipe).
```
--- scenarios on committed real-v5 base (take as the lead runs it = 'committed') ---
### committed rc=0
    FINAL: FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 21. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### filled rc=0
    FINAL: FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 15. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### patched-base rc=1
    FINAL: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 19. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### no-table-file rc=4
    FINAL: FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 23. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### old-table rc=4
    FINAL: FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 25. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### zero-queries rc=4
    FINAL: FINAL: take_check exit status 4. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 37. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### savedata-all rc=0
    FINAL: FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 21. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### keyok-removed rc=1
    FINAL: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 18. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### change-me rc=0
    FINAL: FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 16. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### nonutf8-flow rc=1
    FINAL: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 17. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming.
### nonutf8-ddl rc=2
    FINAL: FINAL: take_check exit status 2. exit 0 would have meant: no definite fault in the files; NOTHING ran in n8n. The checker gave no verdict; open items: unknown.

--- re-runs with --expect 15:14 for mf-form/mf-hook (sed copy of take_check.sh), because the patched base has 15 nodes ---
### patched-expect15 rc=0 :: FINAL: take_check exit status 0. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 19. (1 = fault
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
### keyok-removed-expect15 rc=1 :: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 18. (1 = fault
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check present (F-002 applied)
mf-hook.json: key check present (F-002 applied)
### keyok-renamed-expect15 rc=1 :: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 19. (1 = fault
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially)
mf-hook.json: key check present (F-002 applied)
### accept-if-nomatch rc=1 :: FINAL: take_check exit status 1. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: 21. (1 = fault
--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---
mf-form.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially)
mf-hook.json: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially)

--- --accept-if matching nothing, checker called directly (real-v5, take's flags minus the other accepts) ---
direct rc=1
WARN accept-if --accept-if mf-recovery.json=NoSuchNode matched nothing: no IF node of that name in that file lacks exactly the recorded output(s), so this decision excuses nothing (file or node name wrong, or the gap is gone)
```

Notes on what the scenarios were (facts, not judgement):
- filled = committed real-v5 with PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID, HS_CRED_PLACEHOLDER, FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER replaced by made-up values (from@example.test, intake@example.test). rc 0, open items 15 (was 21).
- patched-base = flows generated by run_all (F-002 + F-008 applied, 15 nodes in form/hook); the take's fixed --expect 12:11 makes it rc 1 (node count FAIL). With 15:14 it is rc 0.
- zero-queries: every postgres step's 'query' setting removed.
- savedata-all: first 'saveDataSuccessExecution: none' in mf-form.json changed to 'all'. take_check rc 0; its section (2) prints saveDataSuccess=all for mf-form.json; no WARN 'run-saving settings' line matched the take's grep (checked by grepping the output: only the nodes= line contains it).
- keyok-removed: KeyOk node deleted from the patched mf-form.json, connections key KeyOk deleted, but 'Valid' still points to it. With take's 12:11 it is rc 1 for count reasons; with 15:14 rc 1 from dangling target / orphan FAIL lines; section (4) still prints 'key check present' for mf-form.json because the text "KeyOk" still occurs in the connection from Valid. A second copy with the name changed to KeyOkX prints 'key check ABSENT'.
- change-me: made-up 'CHANGE_ME' in SendMail fromEmail on the filled copy. rc 0; the checker WARN 'still placeholders' and the take's section (3) both list it.
- nonutf8-flow: mf-hook.json replaced by bytes ff fe 7b 62 61 64 80: checker FAIL 'parse failure UnicodeDecodeError', take rc 1.
- nonutf8-ddl: DDL file with bytes ff fe 80 then CREATE TABLE: checker 'usage error: --ddl file cannot be read', take rc 2, FINAL line reads 'The checker gave no verdict; open items: unknown.'
- accept-if matching nothing: take rc 1 (the second IF gap is no longer excused so a FAIL appears); checker prints 'WARN accept-if ... matched nothing'.
Expected codes per README table: checker 0/1/2/3; take adds 4 for table missing, 0 queries, column/table WARN, step with no query text. (Recorded, not judged.)

## (3) lint (in the copy, 2 .py files: check_flows.py, selftest.py)
```
ruff with DEFAULT config (copy outside the repo, so the repo pyproject is not found):
All checks passed!
ruff check rc=0
unformatted: File would be reformatted
unformatted: File would be reformatted
2 files would be reformatted
ruff format rc=1
ruff check rc=0
unformatted: File would be reformatted
unformatted: File would be reformatted
ruff format rc=1
	No issues identified.
	Total lines of code: 4030
		Low: 1
		Medium: 0
		High: 0
		Low: 0
		Medium: 1
		High: 0
bandit rc=0
--- ruff with the repo's pyproject (--config /home/user/hadavin-sdk/pyproject.toml: line-length 100, extra rules B DTZ I S TID UP) ---
All checks passed!
ruff check(repo cfg) rc=0
2 files already formatted
ruff format(repo cfg) rc=0
--- grep -c 'noqa|nosec|type: ignore' ---
check_flows.py: 0
selftest.py: 0
```
bandit -ll -r: 'No issues identified' at -ll; its metrics show Low: 1 (below the -ll threshold; not listed at -ll).

## (4) Ten (plus one extra) mutants; each: apply, bash run_all.sh in the copy, record rc, restore. KILLED = run_all rc != 0.
```
M1 KILLED rc=1 file=take_check.sh change='escalation to exit 4 removed'
    [take_check.sh exit=0] missing lines: [take_check no-table-file: want exit 4 and 'THE TABLE FILE IS MISSING', got exit 0] [take_check old-table: want exit 4 and 'A COLUMN OR TABLE IS MISSING', got exit 0] [take_check zero-queries: want exit 4 and '0 QUERY STRI
M2 KILLED rc=1 file=take_check.sh change='missing-table path no longer records a problem'
    [take_check.sh exit=0] missing lines: [take_check no-table-file: want exit 4 and 'THE TABLE FILE IS MISSING', got exit 0]
M3 KILLED rc=1 file=take_check.sh change='zero-queries test never true'
    [take_check.sh exit=0] missing lines: [take_check zero-queries: want exit 4 and '0 QUERY STRINGS WERE READ', got exit 4]
M4 KILLED rc=1 file=take_check.sh change='FINAL prefix dropped on the normal last line'
    [take_check.sh exit=0] missing lines: [FINAL: take_check exit status]
M5 SURVIVED rc=0 file=take_check.sh change='checker exits 2/3 no longer short-circuited'
    [take_check.sh exit=0] missing lines: none
M6 KILLED rc=1 file=take_check.sh change='column WARN count ignored'
    [take_check.sh exit=0] missing lines: [take_check old-table: want exit 4 and 'A COLUMN OR TABLE IS MISSING', got exit 0]
M7 KILLED rc=1 file=take_check.sh change='final exit always 0'
    [take_check.sh exit=0] missing lines: [take_check no-table-file: want exit 4 and 'THE TABLE FILE IS MISSING', got exit 0] [take_check old-table: want exit 4 and 'A COLUMN OR TABLE IS MISSING', got exit 0] [take_check zero-queries: want exit 4 and '0 QUERY STRI
M8 KILLED rc=1 file=take_check.sh change='missing-table branch never taken'
    [take_check.sh exit=0] missing lines: [take_check no-table-file: want exit 4 and 'THE TABLE FILE IS MISSING', got exit 4]
M9 KILLED rc=1 file=take_check.sh change='missing table file still passed to checker'
    [take_check.sh exit=0] missing lines: [take_check no-table-file: want exit 4 and 'THE TABLE FILE IS MISSING', got exit 2]
M10 KILLED rc=1 file=check_flows.py change="checker's loud zero-queries line removed"
    [take_check.sh exit=0] missing lines: none
M11 KILLED rc=1 file=check_flows.py change='query-count line reworded (take_check parses it)'
    [take_check.sh exit=4] missing lines: [a !!! line: the take script found a table or column problem]
```
Mutants M1-M9 on take_check.sh, M10-M11 on check_flows.py (M11 is the extra). Which test killed M10 was not traced (run_all's take_check lines were all present; the non-zero rc came from another step, probably selftest.py or a checker run). M5 SURVIVED: no test in run_all.sh makes the checker exit 2 or 3 through take_check.sh with a checker-level fault under the default env (the lead's no-verdict branch is unexercised by run_all.sh; my nonutf8-ddl scenario above does exercise it by hand and gave rc 2).

## What I could not run / did not do
- Nothing was run in n8n or against a real database (script is static).
- No broad mutation pass over the rest of check_flows.py (out of scope per brief).
- bandit/ruff run in a /tmp copy; the original tree was not linted in place.
- Source files in the repo were not edited; only this evidence file was written. /tmp/f8ev6 removed after saving.

## Version note (added at the end)
The copy was taken at about 10:50 UTC. At the end of the run the originals take_check.sh and run_all.sh had a newer modification time (10:55 UTC, after a repository commit at 10:55:08) and show uncommitted changes in git. This evidence therefore describes the files as they were at about 10:50 UTC, not the files as they stand now. The copy was deleted, so a re-run against the new files is needed. I did not edit those two files.

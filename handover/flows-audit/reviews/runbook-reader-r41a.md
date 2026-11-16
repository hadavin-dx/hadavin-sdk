# RUNBOOK round 41 stranger read, lines 1-215 (agent aaae312a, egm-comprehension), Blockers/Majors only, non-security
Saved by flows-audit, condensed. Reviewer words unverified; static. NOT read: RUNBOOK 216-end (step rows, sections 6-10, Block R text), all other files. 0 Blockers, 7 Majors. UTC/IST pairs checked correct (+5:30); sums at 73 and 208 hold (04:00+269 = 08:29; 06:51, 06:21).
M1 Line 192 STEPLOG wrapper `{ C1; C2; } >> "$STEPLOG" 2>&1; echo "exit $?"` masks a failed C1 (used for steps 1,2,3,4,4a,4b,6,9,10,13,14); lines 190 and 204 same flaw for multi-command COMMAND. Fix: join with && or print exit after each.
M2 Line 83 vs 73, 208, 182: FINAL_SHA has no stated step/time ("appended once by Block R3"); step 1 and stepjudge need it; nobody named to run Block R3 before step 1. Fix: add step 0 "run Block R3, pass line sha-evidence-written"; add FINAL_SHA to the eight-name bootstrap check (line 166) or say it is step 1's guard.
M3 Line 66 two contradictory rules for gate with check (e) NOT CHECKED ("passed with (e) NOT CHECKED" vs "NOT CHECKED is not a pass"). Fix: one rule (PASS-WITH-(e)-NOT-CHECKED only before the owner's scope answer; take-day gate treats it as FAIL).
M4 Line 94 vs 80-84: SHA_PIN2 used but not defined; "four shas" count omits it; lines 14, 82 say restore pin 2 from $SHA_PIN. Fix: define SHA_PIN2; "restore pin 2" = ${SHA_PIN2:-$SHA_PIN}.
M5 Line 3 "newest fix round 38" stale vs "round 41" edits at 94, 202; no changelog for 39-41 in section 1.
M6 Lines 29, 121, 170: three due times for the named WARN reader (04:26Z I36; Tue 03:30Z Q31 item 48; TAKE-CHECKLIST about 08:00Z). Fix: one time in the roles table (line 46), point to it.
M7 Line 192 log lists omit step 17 and steps 27-30 (steps 5,7,8,11,12,15,16,18-26 are own-log). Fix: add them to one list.
Not Major: 194 vs 198 on whether KEY/KEYS are typed per call; 198 says KEY is the one per-run name but KEYS has a skeleton line too (135); line 183 does not reset FNMISS on re-source.

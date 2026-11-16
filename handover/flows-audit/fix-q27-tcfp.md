# fix-q27-tcfp (fixer, round 2 of 2 for TAKE-CHECKLIST.md and FIX-PLAN.md; applies reviews/crossread-q27-stale-r1.md, Q27 to Q30 of ORDERS.md)
Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-tcfp/ (both files). Nothing committed. Nothing run in n8n.

## Failures and doubts first
- My first two edit passes failed on wrong anchors (nothing was written then; each script writes only at the end); fixed the anchors and re-ran. No partial writes.
- Not checked: the other files that still use older wording (OWNER-STEPS-q16-rows.md older lines, take_check.sh, DECISIONS, VIDEO-RUNSHEET): not our files; listed as lead fixes.
- The failure line for T19/T20 forbids the unpatched fallback (Q29-3). Whether the F-002-row fallback patch (new sha, new re-pin) is allowed is NOT answered; marked "lead decides", not invented.
- Not answered anywhere and left as "lead fills in": interval between the mailbox count and the recount (Q29-2), exact clock times for owner items Step D, S9-2, S9-3, F-011/F-041 downgrade evidence.
- The proposed caption sentence "...gave one e-mail message in the intake mailbox." is MY wording, marked "lead confirms" (Q28-1 only gives the phrase).
- I did not cite the lead's wrong time stamps (Q30 correction); I removed my citations of the 14:35Z/13:05Z stamps.
- inputs/DECISIONS-2026-11-16.md was not found at handover/inputs (path unchecked elsewhere); I did not rely on it, only on Q27 item 8.

## Applied (claim checked against ORDERS.md lines 155-171 first)
B1 Tuesday GO = take-path code only; F-002 and T19-T21 not in it; F-011/F-041 fixed or downgraded with evidence before Tue 14:00Z else automatic NO-GO; ledger_check command named (TC schedule row 3; FP item 2, 8, 8b, two-paths section).
B2 Owner list rewritten (TC Words box, new check 11, FP GO section): y/challenge/end on camera, Step D, S9-2, S9-3, post; no Step A.
B3 F-011 no longer "not done before video"; F-041 got plan item 8b.
M1 T19-T21 moved to the Wed practice run, at its end (about 07:00Z), F-002 open at 07:30Z = NO-GO (TC row 3b; FP item 2, step 10).
M2 "decision 4" -> decision 1 explained; take_check.sh still prints "decision 4"; the lead edits it (not our file); TC check 1 and FP step 4 keep the script's current text until then and change in the same commit (lead fix 5).
M3 NO-GO latest re-pin Mon 23 Nov 07:00Z; slip until Mon 23 Nov 12:00Z (TC, FP b7, step 12).
M4 guard = flock lock file, round 23, owner decided; "owner decision pending" removed (TC Words, risk paragraph, Still open; FP).
M5 scripts on take branches (706b34d, rounds 23/24); n8n_api.py and post-twice UNKNOWN, lead provides or writes at re-pin; n8n_drive.py lead provides at re-pin, existence UNVERIFIED (Q30).
M6 HubSpot search owner-yes marked superseded by Q25-1 (TC row 4, 10).
M7 roles: lead records (Playwright), owner edits and posts, lead never edits.
M8 re-smoke about 1 h, done about 09:30Z (TC, FP header and two paths).
M9 owner on-camera steps added (check 11, FP).
M10 practice run Wed vs short re-smoke Tue stated as two runs (Words box).
M11 FP open points replaced by answered / UNVERIFIED notes.
Nits: ORDERS line range updated; Q27-8 cited from ORDERS; Q27-7 rule added between rehearsal and take.
Q28/Q29 added: caption phrase; post-wait mailbox count and mf_leads row in frame; private addresses listed for owner; positive control (TC 5b, FP step 10c); mailbox recount in counts proof; T19/T20 fail = NO-GO; post-twice script and run_real_check_n8n.py on a branch for read-only review plus egm reviewer; Step A stays removed.
Q30 applied: practice run from about 06:00Z, F-002 test at its end; F-031/F-007 not in Tuesday GO but applied and re-read by Wed 06:00Z, Blocker until applied (these two keep their rating in FINDINGS; not our file).

## Tool output (run from handover/flows-audit)
$ python3 tools/check_refs.py   -> exit 0, last line: PASS 5147 references
$ python3 -I tools/check_secrets.py -> exit 0, last line: PASS 0 hits in 1719 files
Sizes: FIX-PLAN.md 47115 -> 54080 bytes.

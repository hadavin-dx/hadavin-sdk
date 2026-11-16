# FINDINGS.md pass-line readiness review, round 10 (agent a38c8f85; reviewer words unverified)
Saved by flows-audit, condensed. Static; nothing ran. Rows F-001, F-013 and FINDINGS L121-154 were not read by the reviewer.
Blockers
B1. "prints nothing" grep pass lines pass falsely when a variable is unset or the folder is wrong (F-037 L113, F-029 L117, F-007 part 1 L111, F-041(a) L118): `cd ""` succeeds; grep on empty var lists nothing. Fix: add a guard (test -d; count of 4 mf-*.json) and a positive control that must list files (TAKE-CHECKLIST check 3 L245 has one); say $REPO/$FILLED/$EXPORT/$LOG/$PGCONN are LEAD FILLS with needed-by time; F-041(a) name the owner sheet and closing-card file.
B2. T21 method inconsistent: FINDINGS/LEDGER say NOLOGIN + pg_terminate_backend; TAKE-CHECKLIST L246 (3b), FIX-PLAN L70, RUNBOOK L107 still say revoke CONNECT; RUNBOOK L28 says runner restores grant. Replace with pointer to F-002 "T21 METHOD". (TAKE-CHECKLIST/FIX-PLAN are ab77681's files; RUNBOOK is ae01e2f's: relay.)
Majors
M1. F-008 pass (L114) passes on count alone (8 lines before and after). Use grep -c '"all"' = 2 per flow (6) and '"none"' on mf-recovery.json = 2. Also "decision 4" literal vs TAKE-CHECKLIST check 1 allowing "decision 1".
M2. F-007 (L111): PAGE-STATEMENTS-V4.md L150, L153 and REPORT.md:49 still say "killed after the mail left"; say whether edited out. Part 2 grep -c with two files prints path:1. Part 2b grep -A8 depends on table length. "(this page)" wording in runsheet.
M3. F-003 part 1 no exit-code echo (add `; echo "exit $?"`); pass only an absence check; name positive greps for new captions.
M4. F-031: sentence may sit in the "not for this video" section; require line in scenes 1-4 or card. Part 2 `in (keys)` prints 0 when keys wrong: add control; SELECT-only login has no connection variable (use $PGCONN_SELECT_ONLY).
M5. F-011 downgrade evidence (b) cannot pass: EXCEPTIONS.md L5 says NOT an exception, names "lead", no trigger/review wording; give instruction to rewrite the row with owner, trigger, review date on one line. F-041 downgrade (a) same unset-variable issue.
M6. F-018: DESK_ALERT_TO check has no command; HubSpot contact count menu path and id-probe time have no needed-by time; F-018 (Major) vs F-037 (Blocker) ordering may be asked.
M7. T19 N=10 s PROVISIONAL vs TAKE-CHECKLIST L246 "under 10 s (fixed test bound)": contradiction; fix wording.
Nits
N1 FINDINGS L31 cites RUNBOOK:99; should be L122 and L100. N2 pipes in table cells (F-007 2b, F-028, F-011(b), F-041). N3 F-028 give one command extracting N. N4 F-003 "Blocker if it ships; Major while draft" double rating text. N5 $PGADMIN needs PGPASSWORD/.pgpass.
Reviewer confirmed: counts table matches 12 rows read; patch files exist; cites checked true for VIDEO-RUNSHEET:90, PAGE-STATEMENTS:150/153, REPORT:49, TAKE-CHECKLIST check 13 at L257.

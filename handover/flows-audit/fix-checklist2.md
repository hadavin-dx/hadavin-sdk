# fix-checklist2 log (TAKE-CHECKLIST.md, round 2), 2026-11-16
Failures and gaps first:
- Nothing was run; every command in the checklist is written, not tested. take_check.sh and the greps were read, not executed.
- I did not re-read ORDERS.md lines 109-120 or the rest of FIX-PLAN/OWNER-STEPS beyond the lines needed; old file:line cites were dropped (reviewer item 14: unverifiable) and replaced by plain words plus answer ids.
- The pass-line counts (2 key check, 3 run saving ON, 1 ACCEPTED line) come from reading take_check.sh; not run. After export-back the WARN set changes, so exit 4 until a new pin is written: stated, not run.
- Q25 item 13 says a README line near 240 is stale; the file has 5 lines, I could not find it; listed as "not re-read".
- Q22 said 2 minutes, Q25 item 12 later says 3: used 3.
- Step A: "stays or not" left to the lead (Q25-7 says Step D only, Step A if kept).
Fixed (reviewer items): 1 words box (lead / test lead / lead ID); 2 no TAKE_CHECK_FORM_EXPECT, absolute path, LOG defined, folder stated; 3 Q26 schedule UTC+IST, stale blocked items removed, only open ones kept; 4 psql gate (four alert_* columns, v4 table file), take mode, HubSpot read-only, cleanup OFF, $env=0; 5 scene 4 (own clock, 3 min, takeover line only if rehearsal showed it); 6 Step D one message per contact, "not found" not a failure; 7 pass lines with countable greps (row 2 explained); 8 psql connection/login "lead fills in", stray rows how to clear; 9 scoped caption, no closing-card numbers; 10 words box defines take, retake, rehearsal, practice run, re-pin, Step D, Row 4; 11 partly (sha written once at re-pin; patch/regenerate commands not in this tree, left to lead); 12 IST added; 13 stale line 69 warned; 15 order of rows and $env check.
Not checked: scripts' real arguments, psql column names of the table, take-day rows T1-T14 wording vs. my table beyond a read, the one-page length when rendered.
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-chk2/TAKE-CHECKLIST.md

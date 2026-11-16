# RUNBOOK lines 220-370 stranger read r67 (agent a452d028, egm-comprehension), non-security
Saved by flows-audit, condensed. Reviewer words unverified; static. NOT read: lines 1-4, 26, 39-219, everything after 370 except rows I33 (477), I44 (488), I10/I35 (454/479); other files and scripts. 2 Blockers, 15 Majors. Section 6 sums rechecked correct.
B1 Step 15 (257; RC4 360; step 6 247) cannot pass: needs all by-reading boxes ticked except RC11, but RC4 reads run_real_check_n8n.py due Tue 09:00Z. Fix: add RC4 to exceptions or move its reading before.
B2 Step 26 (279; pass-words.sh 308-309) pass line cannot be produced: post_counts_ok reads $POSTLOG.counts/.mail/.mail2; nothing in step 26 sets them. Fix: name the command writing them with a NEW POSTLOG, print a word each.
M3 Step 6 (247) vs I33 row (15, 477): 04:54Z vs 09:00Z copy; two files then three; pass cell omits start-syntax-ok, syntax ok, control exit 0, grep exit 1.
M4 Re-smoke length: table 16 default 60 min vs step 16.9 (258) 74 min, ends 09:43Z (15:13 IST) past 09:30Z.
M5 Rehearsal 1: table 18 says 07:40 vs step 21/section 6 07:44, first send 07:48; table times lack Z.
M6 Missing from decision table: I44 recovery on/off (due Tue 06:39Z), hook-leg question (267, 08:29Z), moving 45 min writing to W-Tue (341, Mon 21:00Z).
M7 WARN reader time 4b 04:26Z vs 04:50Z after 4a wait; step 13 "again" with no time (07:14Z, 335).
M8 Step 14 (256) (d)(e)(f) by reading, no printed word; I34/I35 no owner/time.
M9 Steps 21, 23 (274, 276): no printed pass word; rule d/e undefined; scene-4 wording differs.
M10 No check of owner's edited video before post (281-283); steps 28/30 depend on I27 without time.
M11 Step 27 (280): pass words "LEAD FILLS".
M12 Step 17 (259): no saved GO/NO-GO line; 10 min too short.
M13 Step 9 (250): missing credentials "lead decides" no time/outcome.
M14 Step 18 (267) 60 min vs 64 min with fourth gate.
M15 Step 8 (249): DB_SETUP/DB_GRANTS pass only exit 0; no failure action.
M16 Step 4 (243): fail cell has no failure action.
M17 BLOCKED-by cells give only I-numbers without owner or HH:MMZ (IST); times live in section 10.

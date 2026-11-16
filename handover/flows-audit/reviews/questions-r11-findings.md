# QUESTIONS.md round 11 fresh readiness review (agent a9a2002d; reviewer words unverified)
Counts and ORDERS cites reported correct (33 L rows, 28 Q31 items, 27 open, item 20 answered; ORDERS lines 110-177 cites). Not checked by reviewer: FINDINGS, RUNBOOK, OWNER-STEPS quotes; History section (L437-485).
Major
1 Item 10 two answer-by times: L42 and L80 say 07:00Z; table L389, item 10 L413, GATE L50 say 06:15Z; items 18, 26 depend on item 10 and are due 07:00Z. Fix L42/L80 to 06:15Z (item 11 stays 07:00Z).
2 Rows L4, L7, L14 (L60, 63, 70) still plan fill "Wed 18 Nov about 05:30Z" = dropped option 3 (glossary L161, item 8 L411); default is option 1 (Tuesday after re-pin). L7 argument only valid for dropped option. Fix rows or say time depends on item 8.
3 05:54Z deadline for HubSpot scopes ask (L22 L78, item 27 L434) has no source in the file; default fill is after re-pin ~08:00Z. State source or reconcile.
4 Items needing other files without saying so: 17 (L420), 18 (L421, F-011/F-041 evidence lines not quoted), 21 (L424), 23 (L426), 2 (rows V17/V18 undefined), 24 (L427-431), 26 (L433: six OPEN ledger rows not listed), L16 (L72), L18 (L74), L26 (L82). Quote the lines inline or mark "needs FINDINGS/RUNBOOK open".
5 Item 15 default (L418) points at nothing: say plainly what happens if nobody is named (NO-GO for the pin; take cannot run).
6 Item 25 default (L432) uses "the planned wait" which the file says is UNVERIFIED: name the value or say there is none and the lead picks.
7 Item 10 (L413) no default for WHO ACTS (GATE says NO-GO; say so; row L24 says actor NOT NAMED). Item 17 (L420) unclear whether silence means F-031 stays Blocker (lead L171 item 2) or Nit; state it; item 19 depends on it.
8 07:00Z cluster heavy (items 2, 5, 8, 11, 12, 14(c,d), 16, 18, 21, 23, 26, 28); item 8 (delete message 1b ~09:30Z) depends on item 5's count of 3 contacts, both due 07:00Z: put item 5 at 06:55Z or say 8 follows 5.
Nit
1 item 8 sub-points mislabelled (first, which day, third, (e)): label (a)-(e). 2 ORDER 030 cited "line 149" is the heading; text is L150. 3 item 6 "5 h 34 min" measured from chain end 12:55Z not take start 11:55Z; say which. 4 plain-word gaps: SQLite, SMTP, $env, ruff, ruff format, T-08 step 0.
EXTRA from the TAKE-CHECKLIST fixer (ab77681, unverified): F-008 literal "(decision 4)" in take_check.sh/check_flows.py/FINDINGS/LEDGER conflicts with ORDERS Q27 item 8 wording "decision 1": add as a Q31 item (answer: keep "decision 4" in all three files, or change all in one commit). Also HubSpot-scopes timing: ORDERS Q27 item 2 says Wed 07:00Z but credential is used Tue 05:54Z / 08:29Z; and F-018 flag (counts or out) needs a lead decision.

# Citation check r13: CLAIMS-TABLE.md Table 2 (rows 41-77, 80-84)
HEAD at start 650b5f7c716e836520b02ac12a19b489f3365c9f; at end 26099aa6a93e3e92f003643de1dcad70b72bea14 (changed during the run by another process; I committed nothing).
Counts (42 rows): primary cite MATCH 42 of 42, quoted "current words" word for word in file 42 of 42. Secondary cites: SOFT MISMATCH 2 (rows 51, 54), CANNOT-CHECK 4 rows (80-84 desk-repo cites). MISMATCH 0.
ORDERS.md: no Table 2 cite names it; nothing to attribute.
Not used as evidence: any fix-*.md.

SOFT MISMATCH
- Row 54 (B-093): note says OWNER-STEPS-realrun-v3.md step 18 "now describes" end.flag. Step 18 (inputs/OWNER-STEPS-realrun-v3.md:102-103) is "The film pause: type `end`"; the file never says end.flag (grep: no hit). PLAN-4:46 does name it: "waits for the typed word `end` or an `end.flag`", but not who writes it. DELETE of the "Not found" line is only half supported.
- Row 51 (B-045/B-046): why-cell says AGENT-SCOPE-DO-AND-DONT.md lines 14-16 treat qualify_stage.py as existing. Lines 14-16 never name qualify_stage.py or stage_server.py (grep of whole file: 0 hits). DECISION-one-store.md:9 does: "`stage.journal` file in the take folder (qualify_stage.py)". No qualify_stage.py anywhere under handover (find): that part holds.

CANNOT-CHECK (desk repository not in this checkout; only mutation-test scratch copies exist under scratchpad, not authoritative)
- Row 80: docs/settings.md:120.
- Row 81: run_real_check.py:903.
- Row 82: imap_count.py (X-Send-Key, no subject mode).
- Row 83: run_real_check.py:920 and the function list.
- Row 84: imap_count.py constant, smtp_provider.py:73.
The quoted current-words of rows 80-84 (FAILED-TAKE-NOTE:6, :12; PLAN-4:42, :45, :66) all match word for word.

MATCH (file seen, text at cited line)
41 PAGE-STATEMENTS-V4.md:44 (handover/demo/n8n-flows) "3. "The same failure cases (T8, T15) were not run on the v4 flows.""
42 :130 "Total: 18 statements."
43 n8n-owns-vs-desk-owns.md:4 (demo) "n8n owns (stated by the lead): intake, field mapping, the ten-at-once trigger, alerts, ..." (bold markup stripped in quote)
44 AGENT-SCOPE:6 (flows-audit/inputs) "alert on failure (capped at 3, no lead data in the alert)"
45 AGENT-SCOPE:7 "MUST NOT: process the same lead key twice"
46 PLAN-4:37 "one contact per lead" (table cell)
47 PLAN-4:38 cells "Mail send | one mail per lead | 1 Send Email behind MailClaim"
48 PLAN-4:43 quote ok; WATCH-CHECKLIST:10 "reads and archives contacts"; FAILED-TAKE-NOTE:9 "the run archives only the contacts"
49 PLAN-4:57 full sentence present
50 PLAN-4:78; 51 :79 "All model calls run under ONE in-process lock (single flight)."; 52 :122 (V5-README:17 "T17, T18, M1 and K1 on v5 have NOT been run." both v5 copies identical); 53 :195
54 FAILED:16 "Not found anywhere." (PLAN-4:46 end.flag ok, see soft)
55 FAILED:17; PLAN-4:114 and :154 name --retire-check; OWNER-STEPS step 22 (line 119) describes it
56 FAILED:19; PLAN-4:137 "ends 2026-11-23 23:59 IST" (US$189 window cap)
57 RUN-ON-LAPTOP:38; 58 :56
59 N8N-START.md:30 (demo/n8n-flows)
60-69 DESIGN-A-README.md (demo/n8n-flows) :15 (rows 60,61,62a,63), :32 (62b "1 alert"), :16 (64), :17 (65), :20 (66), :28 (67), :40 (68), :42 (69): all quotes verbatim
70-71 V5-README.md:4 (real-v5 and film-v5 identical)
72 n8n-published-numbers.md:3 (why-cell "12 of 20, 2 of 5, 12 of 12" supported at :14)
73 :4 (PUB:30 says NO MATCHING ROW: yes); 74 :5 (PUB:20 b 0 of 13; PUB:31 README says 0 of 15: yes); 75 :6; 76 :21; 77 :22

# c6v design and honesty review, round 4 (egm-design, condensed copy of the inline report), 2026-11-16
Target: REPORT-c6v.md (884 lines) and c6v-CHANGES.md. Read-only, nothing run. Verdict: do NOT type the answer line yet. 1 blocker, 4 majors, 7 minors. c6u design M2-M5 mostly closed; M1 (G12 hold) only partly closed though the report says fully.

## BLOCKER
- B1 Box step 2 (line 9) answer line names c6u ("c6u apply all defaults to REPORT-c6u.md ...") but the report is c6v (104 rows; builder writes c6v-APPLIED-ROWS.md, line 220). Typed as printed it points the builder at the superseded report. Only the time is flagged EXAMPLE. Same text in c6t, c6u, c6v; class 1 and 4 checks missed it. Fix: name c6v and add a verifier check that the report name equals the file name.

## MAJOR
- M1 Box line 22 says release note v18 lines 8, 33, 149, 150 equal the newest note; lines 65, 170 and CHANGES item 5 say lines 8 and 149 DIFFER (line 66 repeats "equal"). v18: line 33 (G12) and 150 unchanged; line 8 no longer lists G12; line 149 has no "unless approved in writing" wording. Box line 19 and L-POST (line 264) still say the note bars lease sentences unless approved in writing (true of v14 only). Fix line 22; say in the box that the G12 reasoning rests on v14 line 149, which v18 dropped.
- M2 G12 hold claimed on 11 rows (lines 170, 264, 684, CHANGES 15); rows 1 and 19 carry none. Row 1 keeps "setting: lease 45 s" with no hold while row 17 holds the same label. Row 19 says "the 45 s lease setting is allowed". Reason cells of rows 15, 17, 19 stale. Line 684 says "eight carve-out rows" but lists 11. This is c6u design M1 again; class 1 must-exist list misses rows 1 and 19. Row 8 item 12 not read.
- M3 Rows 11, 13, 14, 96 contradict under "apply all defaults": row 11 writes card 40 s, 90 words, about 190 s; rows 13/14 write all four lines; row 96 sets the card Time cell (line 41) to 35 s assuming line 1 cut (defaults do not cut it). Run sheet would say 40 s on line 44 and 35 s on line 41.
- M4 Card line 4 and the label "lease" ship by default ("other lease settings") against v18 line 150 ("nothing about a lease"); L-POST admits viewers are never told what lease means. Lines 852 and 692 defer the card wording to L-CARD, which only asks whether the card stays: a deferral to a question that does not exist. Fix: add the question (default: drop "other lease settings" from line 4 until G12) or change the default.
- M5 (honesty, lower) Verifier claims exceed support: CHANGES 16 "any count or version quoted twice is equal" vs line 685 "every count of 30 or more" (below 30 not covered; "eight/11" slipped through). Box 2478 words (22 under 2,500) excludes heading; part 2 (lines 57-62, about 700 words) not counted, effective read-first about 3,200. "267 changed copies, 0 wrong" is the builder's word; not verified.

## MINOR
m1 First rehearsal after TASKS (5)-(9) at lines 93, 300 vs (5)-(10) at 224; G12 is TASK (10). m2 Line 66 says v30/v14 written 17:22:10Z; lines 71, 182 say v30-v33 written 18:46:25Z (identical mtimes for four versions suggest bulk touch); staleness test uses mtime only, no content hash; not said. m3 L-SHEET default example (line 273) says "v30A", box says v34A. m4 Stale labels "RECHECKED AGAIN IN c6t" (71), "[done in c6u]/[done in c6t]" (875-877); "[done in c6v] row 96" (873) says done while nothing is applied: use "written". m5 Line 870 says no sub-agent or background process; CHANGES item 7 admits six full runs (cap 3), not repeated. m6 L-CARDLEN option (b) 74 words, 29.6 s vs 30 s budget: 0.4 s margin, no stopwatch. m7 Default "none" for the lease sentence reverses Q22(c) for the video (ORD:230 over ORD:186); say so plainly.

## Held (checked, true)
Row counts 57+38+3+6 = 104, wave 1 = 95, 37 viewer rows of 5a; card arithmetic (11,35,22,22 = 90 words, 36.0 s; option (b) 74 words, 29.6 s); about 25 UTC/IST pairs and weekdays correct; ORDERS cites resolve; newest sheet v34 and note v18 true at read time; G12 kept open, not read as a decision.

## c6u findings
M1 PARTLY OPEN (M2 above); M2 closed for recounted counts (new stale: "eight", line 22, "v30A"); M3 closed; M4 closed on text (new conflict M3); M5 closed (C-1/C-1b UNVERIFIED); m1 row text unread; m2 now conflicts with row 11; m3 rows 97-104 unread; m4 L-APP2 still unchecked ([needs-lead]); naive M7 deferred to a non-existent question (M4). Earlier reviews c6p-c6t not read.

## Not checked
Rows other than 1, 2, 5, 11, 15, 17, 19, 73, 74, 93, 94, 96; row 8 item 12; sections 1, 4, 6, 8 (below c6u block); scripts and outputs in evidence-c6v*; the 2478 count; old text vs real files (UNVERIFIED); real mtimes; whether any OPEN item has been answered.

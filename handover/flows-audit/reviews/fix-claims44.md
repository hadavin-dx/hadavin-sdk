# fix-claims44: fixer report, CLAIMS-TABLE.md lines 1-300, round 2 of 2 (non-security)
Edited only CLAIMS-TABLE.md. RUNSHEET-WORDING.md, RUNBOOK.md, QUESTIONS.md untouched. Nothing committed.
Not verified: reviewer claims about RW lines were checked only where cited; RW text of rows B-130 and A-005/A-084 read via grep, not in full; the pasted strings were not changed (pair/paste checks pass).

## Commands (after edits)
- python3 claims-count.py CLAIMS-TABLE.md -> verdicts UNSUPPORTED 9, OVERSTATED 107, SUPPORTED 80, RELAYED-ONLY 57, UNTRACED 77, total 330; lanes A 100, B 226, X 4; to-do rows 87; offenders 0; ids 330 unique 330.
- check_rw_ct_pairs.py -> "found word for word in CT: 144; not found in CT: 0".
- check_runsheet_paste.py -> RESULT: PASS. check_refs PASS 5193; check_names PASS 655; check_secrets PASS 0 hits; check_counts PASS 52 files / 655 nodes. ruff format --check . -> 1042 files already formatted.

## Findings
- B1 FIXED. My own script (ids of every to-do row incl. sub-rows, minus 330) gives: rowless 233 = 80 SUPPORTED + 56 RELAYED-ONLY + 64 UNTRACED + 33 OVERSTATED; with a row 97 = 74 OVERSTATED + 9 UNSUPPORTED + 13 UNTRACED + 1 RELAYED-ONLY (A-050). Sums match file totals. The reader was right (a part cannot exceed the whole). Line 116 rewritten (one set, old regrade history removed, "twenty-five" -> "thirty-three", the ten round-43 ids added, B-126/B-140 removed from NO PASTE list); lines 120/121 "64" -> 57; line 218 "41" -> 34; Part 7 table 62/41/50 -> 60/34/59 (sum 230).
- B2 FIXED, one item needs the lead. B-130 now OVERSTATED everywhere (line 161 said UNSUPPORTED); B-126 UNTRACED and B-140 RELAYED-ONLY already matched the lane rows. A-099 UNTRACED kept; UNTRACED defined once (line 15: nothing in this checkout can prove or disprove it, incl. "does not exist yet"). Row 3: line 180 said "planning-only figure of about 61 s"; row 3 writes no figure; line 180 corrected. LEAD CONFIRMS: B-130 grade OVERSTATED vs RELAYED-ONLY (new WL-16; B-130 row note).
- M3 FIXED. One definition set in the "Verdict words" bullet; glossary verdict bullet, "Words used" bullet and Legend item 1 now point to it; OVERSTATED = partly true (file supports part), no longer a catch-all.
- M4 FIXED. Owner list = Step D, typed answers, S9-2, S9-3, plus the crop/blur/cover decision (Q28 item 2; RW line 18 says the same) added at lines 12, 142, 148; line 147 now matches line 12 on contact count.
- M5 FIXED. Row 79 has no CRM clause (row 79 "needs" says so since fix-rwct21); lines 61 and 131 no longer list it under P4a.
- M6 FIXED. Row 39 stays LIVE (tag rule: "a check must be read first") with a note that there is no edit step; line 241 "adds a few words" corrected. Not regraded to OUT (would change 22/65 everywhere); say if you want OUT.
- M7 FIXED. Work order item 3 now lists the live deletes 19b and row 25.
- M8 FIXED. CT, X-5a/X-5b/X-6a-c defined (line 16); forward pointer for lead/Table 1/lane table (line 3); "list C" -> WL-14; "CT bullet D2" -> "bullet D2"; Q-A/Q-B pointer; D3 in WL-7; "burst" explained at line 69 (variant a was already explained).
- M9 FIXED. PASTE table row says proposed, not approved; WL-1 no longer under BLOCKED; WL-5..WL-13 grouped by their own kind (DEFAULT / BLOCKED WL-10 / DECIDED WL-11); kinds sentence extended; WL-8 "Missing input: none".
- M10 FIXED. Line 91 now gives the re-pin date rule (Mon 23 Nov 07:00 UTC = 12:30 IST latest, NO-GO path).
- M11 FIXED. The OUT-with-exception form of rows 13 and 18 is defined in the OUT tag bullet (one status OUT, live rule carried by sub-row 7b); row 13 column names aligned with row 7b.
- M12 FIXED. Item 11 now cites "Q22 item 1" and "Q22 item 4" instead of (1) then (4).
- M13 FIXED. Line 143 now says no tick is set in any done cell (grep: 0 ticked).
- Reader's "UTC/IST pairs correct" and lane counts: not re-verified beyond the script outputs above.

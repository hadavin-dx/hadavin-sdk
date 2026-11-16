# fix-claims59: fixer report for CLAIMS-TABLE.md (reads r57 lines 600-1052, r59 lines 1-300)
Fixer, non-security path beyond round 2 (Blockers and Majors only). Edited only CLAIMS-TABLE.md. No grade word and no total changed. Lines 301-599 were NOT read by any reader and were not assumed clean.
Output of `python3 claims-count.py CLAIMS-TABLE.md` after the edits: verdicts OVERSTATED 110, SUPPORTED 78, RELAYED-ONLY 57, UNTRACED 79, UNSUPPORTED 6, total 330; lanes A 100, B 226, X 4; to-do rows 87; offenders 0; ids 330 unique 330.
Arithmetic: 78+57+6+110+79 = 330; lane A 18+23+50+2+7 = 100; lane B and X 60+34+60+4+72 = 230 = 226+4; traced = 330-79 = 251; 110+6 = 116, minus 35 = 81.

## Fixed
- r59 M1: "253 were traced" -> 251 (Count by script).
- r59 M2: "the 83 claims" -> 81.
- r59 M3: "77 claims are UNTRACED" -> 79, and "77 UNTRACED" -> 79 (the 77 in the round-43 history is a past total and stays).
- r59 M4: "the 12 added on purpose" -> 14 (matches the 14 listed under Count).
- r59 M6: item 1 of "Order of work" now says D2 and D3 are open, both with defaults.
- r59 M7: needs cells of rows 2 and 5 now name the owner's crop/blur/cover decision (Q28 item 2); row 19 names D2. Row 39 already named P4a (nit, no change).
- r59 M8: row 36 note now says which cell to paste today (the "other branch" cell, X-5b; X-5a is HELD for P4b).
- r59 M9: new block "Where the files are" at the top (RUNSHEET-WORDING.md first, then QUESTIONS.md, ORDERS.md, inputs, VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md).
- r59 M10: new block "Five lines first" at the top; the "(read first)" tags of the precedence rule and of "Start here" reworded so nothing else claims to be first.
- r59 nits: change-marker sentence now says only LIVE rows and the OUT row 25 carry a marker (row 19's live delete is sub-row 19b, LIVE); "Rows 13, 18 and 21"; A-099/A-100/A-101 vs RW rows reconciled (A-016f screen and A-016h card, A-016b voice, A-016g for A-101; RW row list checked). The "front part" nit (lines 17 and 269) was not changed: the meaning is clear from the glossary and no better label exists without rewriting two long cells (not a Blocker or Major).
- r57 M10: line 692 now carries the "and no part of it is shown true" rule and points to "Verdict words".
- r57 M9 (wording only): B-219 verdict cell and safe wording now name clauses by their words, not numbers, and no longer call the last clause supported; B-086 wording now says flow files set saving to none (as the regrade bullet says).
- r57 minors: B-027 and B-203 verdict cells say "(real-v5 flows only ...)" after SUPPORTED; Part 7 title no longer says "round 44"; Part 4 sentence points to the verdict cells.

## REGRADE PROPOSAL (lead confirms; in the new block RG-1 to RG-9, nothing applied)
r57 M1 (RG-1), M2 (RG-2), M3 (RG-3), M4 (RG-4), M5 (RG-5), M6 (RG-6), M7 and r59 M5 (RG-7, B-130), M8 (RG-8), M9 B-220 (RG-9). Each line gives the total change; all nine with first options give 81 / 56 / 4 / 109 / 80 = 330.

## Not fixed, why
- Lines 301-599 unread by any reader; needs a reader.
- X-3 evidence: RG-1 asks the lead to check X-3 because its cell was not shown by the reader to name a supported part.
- "Wrong grade words" are the lead's call by the hard rule.
- r57 M5 "B-114 same file": B-114 is OVERSTATED (row count disagrees with source), so only the four RELAYED-ONLY ids are proposed.

## Checks (last lines)
claims-count: total 330 as above. check_rw_ct_pairs: found word for word in CT 144, "not found in CT: 0". check_runsheet_paste: RESULT: PASS. check_refs: PASS 5190 references. check_names: PASS 655 rows. check_secrets: PASS 0 hits in 2959 files. check_counts: PASS 52 files / 655 nodes. ruff format --check: 1084 files already formatted.

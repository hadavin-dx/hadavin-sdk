# Claims table round 9: facts and paste-consistency review (agent a40062c)
Saved by flows-audit, condensed. Reviewer words are unverified until checked. RUNSHEET-WORDING.md (RW) wins where it differs from CLAIMS-TABLE.md. Reviewer did not open the cited sources under handover/demo/; it compared two files only. Not checked: per-row claim counts, verdict correctness, RW rows A-050c, A-052, N-3, rows 20-31, 34, 35, 37-77 replace cells outside the changed list (except 30, 48), lane text of A-023 and A-088.

## Blockers (replace or other-branch text differs from RW)
1. Row 32 (B-213): says "mail", "0 or 1 mail", "the owner deletes"; RW says "e-mail message", "the studio owner". Row 32 appends "This is a statement by the lead ... lead verifies at re-pin", which RW B-213 excludes. Status PROPOSED here, HELD in RW.
2. Row 33 (B-215): same appended lead sentence (RW says it is not part of the string). Other-branch cell "The take script may remove some of the made-up contacts or may leave them; ..." appears in no RW row. PROPOSED vs HELD.
3. Row 33b (B-215b): same two defects; invented other-branch text. PROPOSED vs HELD.
4. Row 36 (X-5b): other-branch says "(SQLite)"; RW says "Today n8n keeps its own records and the lead table is in Postgres." and that P4b decides SQLite.
5. Row 84 (B-038): replace cell wording differs from RW ("The mail subject made by the flow starts with [demo] lead. The constant SUBJECT_TOKEN_PREFIX does not exist yet ...").
6. Row 48 (B-067, B-091): same appended lead sentence; "the owner deletes" vs "the studio owner"; PROPOSED vs HELD.
7. Row 19: exact match to RW. No finding.

## Majors
8. Row 15 (B-032, B-056): replace cell matches neither RW B-056 ("recovery wording: no time or estimate is quoted; the recording shows no timer") nor B-032; [CHANGES: caption or card line deleted] beside non-empty replace text.
9. Row 7 (A-012): "intake mailbox shows 1 mail" vs RW "1 e-mail message".
10. Row 8 (A-016a): "one lead record is sent twice" vs RW "one lead ID is sent twice".
11. Row 79 (B-219): wording differs from RW B-219 (comma after "real services", "In this recording").
12. Status words table and line 3 use CUT and PROPOSED as live words; RW has only PASTE, DELETE, HELD, NO PASTE, SUPERSEDED and says older words are not used. B-067, B-091, B-213, B-215, B-215b listed PROPOSED, RW has HELD. Same in "Live rows" (lines ~340, 344-348) and notes of rows 14, 15, 32, 33, 48.
13. "Live rows" line ~341 says rows 2 (A-005) and 5 (A-084) are PASTE; RW has HELD. A-087c and A-087d are SUPERSEDED in RW, PASTE here (row 3).
14. Line 33 "Read from RUNSHEET-WORDING.md lines 24, 35 and 48" does not resolve (24 = review definition, 35 = heading, 48 = blank).

## Checks that passed
All WL-1..WL-15 exist; named sections exist; counts agree (Table 1 52 lines, 45 rows after removing 7 sub-rows; Table 2 42 rows; 87 total; 22 live + 65 out; lane A 97 + lane B 230; 327 ids). No INSTRUCTION text in replace or other-branch cells. No clear [CHANGES] marker contradiction except row 15.

## Also from the earlier r5 reader part 2 (still to fix, Majors only)
Rows 51, 52, 58, 62, 63, 66, 69, 74, 80, Table 2 vs lane strings (see claims-r8-reader-part2.md).

# fix-claims8: CLAIMS-TABLE.md round 8 fixes (2026-11-16)
Made-up data only. Nothing run in n8n, a CRM or a mail server. Nothing committed. Original saved at /tmp/bak-claims8.md and at the scratchpad (bak-claims8.md). Only CLAIMS-TABLE.md and this log were edited. Not verified by anyone but me; no reviewer has read the result.
Inputs: reviews/claims-r8-reader-findings.md (M1 to M10 and the "could not follow" list) and reviews/claims-r8-facts-findings.md (it landed during the work; its Majors are fixed too, except M4).

## Reader findings
- M1 (INSTRUCTION rule) -> one rule in "Start here" item 6: the cells "replace with" and "other branch" hold only pasteable text, DELETE or "-"; every order moves to the note and starts with INSTRUCTION:. Applied to rows 6, 10, 11, 15, 16, 17, 23, 35, 36, 39, 48, 85, 86, 87 (cells cleaned) and to the lowercase "Instruction(s), not part of the new text" of rows 2 and 7. Row 79: "The post says only:" is part of the file sentence RUNSHEET-WORDING.md B-219 replaces (stated in the rule and the note), not an order.
- M2 (rows 16, 17) -> replace cell is DELETE (old card line 5 or 6, live); the notes-only text is in the note under "NOTES-ONLY TEXT".
- M3 (re-smoke) -> P4b is a listing of the n8n data folder and needs no re-smoke; whether a loopback re-smoke (trial run) happens is BLOCKED: lead decides (WL-10, default: does not happen, the take does not wait). Row 86 no longer says "re-smoke gate".
- M4 (status words) -> new table "Status words" (PASTE, PROPOSED, HELD, CUT, NO PASTE, FILE EDIT) with one gate order read from RUNSHEET-WORDING.md lines 24, 35, 48: check or decision, then re-pin check (PROPOSED rows), then APPROVED last. Rows 32, 33, 33b, 48 are PROPOSED.
- M5 (live tags) -> [LIVE] redefined; every LIVE row (and rows 19, 25 which carry a live delete) has a change marker after its tag: [CHANGES: caption or card words / spoken line / caption or card line deleted / filming only, no words / file only, viewer sees nothing / post text]. No new column (claims-count.py wants 11 cells). Row 78 stays OUT; its approval (WL-12) is for the later rewrite.
- M6 (rows 19, 25) -> markers name the live deletes (R:90 A-023a; P:120 A-073b); overlap of R:90 with row 22 stated in rows 19, 22 note and Start here item 7.
- M7 (Q-F, Q-H, B1) -> Q-F and Q-H defined in the labels list; new item WL-13 (Q-F, default no card; the scene 3 caption does not wait for it); WL-6 lists A-050a, A-050b, A-051a, A-051b; item 8 of Start here says "are to be deleted ... the lead confirms (WL-6)". Row 8b "needs" names Q-F only for the card line.
- M8 (the list) -> one label per item, WL-1 to WL-15 (old A1 to A5, B1 to B7, C, D mapped in the list's intro; QUESTIONS.md Q31 item 39 still uses the old labels and was not edited). Four BLOCKED items (WL-1 to WL-4); the mailbox names (old A5, has a default) moved to the DEFAULT group (WL-5). All 18 citations updated. Line 3 now says the list stands above "Start here".
- M9 (letter collisions) -> list letters are gone (WL-n); one line in "Words with two meanings" keeps D1 to D3, decision N, Step D, lane A, A-nnn, queue item C4 apart.
- M10 ("claim row") -> the n8n reservation is "reservation row" everywhere outside quoted plan sentences; "to-do row", "lane row", "lead-table row" defined; the one place that said "no claim row of its own" now says "to-do row".
- Could not follow: "17:05Z" sentence rewritten (line 73; line 140 already clear); "for each message the lead sends" rewritten as two messages, each listing leftover contacts, and the owner deletes the listed contacts. NOT CONFIRMED: no file says whether one contact or several per message; the lead confirms. Row 7b and the other "no claim id (see the row: ...)" verdict lines now name their one reason each. "Check person": grep finds no such phrase in the current file.
- Nits fixed: line 109 now lists rows 1, 4, 7, 39, 79 for P4a; row 6 note says "may keep a copy"; rows 25, 25b, 25c "needs" no longer say D1 is open for the screen; sub-row list at Table 1 intro includes 7b and 8b. Not changed: "relayed runs of about 61 s" (line 108; reads as the file says).

## Facts findings
- M1 (row 19, "2 runs") -> row 19 replace cell, note, and lane rows A-023 and A-088 now use RUNSHEET-WORDING.md A-023b / A-075 / A-088 strings (number of runs not confirmed). Checker check_rw_ct_pairs.py: unmatched strings 61 -> 57 (A-023b, A-075, A-088, X-5a now found).
- M2 (row 36) -> replace = X-5a, other branch = X-5b, note names their statuses (X-5a HELD waits P4b; X-5b PASTE default); "Live rows" section updated.
- M3 (row 84) -> why-cell says "Not in the desk repository copy (verdict UNTRACED)"; quote artifacts flow"s, desk"s fixed.
- M4 (RUNSHEET-WORDING.md:19 count line) -> NOT touched: another fixer owns that file.
- M5 (rows 32, 33, 33b) -> notes no longer call the last sentence a lead-only remark; it is inside the string; row 32 replace cell is the full RUNSHEET-WORDING.md B-213 string; rows 33 and 33b got the last sentence.
- Nits not done: B-168 "272 s", B-201 "0 of 15" vs "0 of 13", B-214/B-215 id on row 33d (not checked).

## Checks run
- python3 claims-count.py CLAIMS-TABLE.md -> UNSUPPORTED 27, OVERSTATED 62, SUPPORTED 119, UNTRACED 49, RELAYED-ONLY 70, total 327; lanes A 97, B 226, X 4; to-do rows 87; offenders 0; ids 327 unique 327.
- python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> RESULT: PASS.
- python3 tools/check_refs.py -> PASS 5167 references.
- ruff format --check . -> 597 files already formatted.
- Not run: ruff check, check_secrets.py (earlier round: 2 hits in files I do not own).
Not checked: whole-file reread after the edits; the lane tables (437+) beyond the cells named; table-row rendering in a viewer.

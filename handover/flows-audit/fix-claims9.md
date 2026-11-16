# fix-claims9 log (fixer for CLAIMS-TABLE.md, round 9)
Edited only CLAIMS-TABLE.md. Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/CLAIMS-TABLE.bak. Nothing committed. RUNSHEET-WORDING.md (RW) was only read; every string was read live from it at edit time (after the change by fixer ac1d614: B-195, B-197, B-214 HELD).

## What I did, by finding
- Blockers 1-3, 6 (rows 32, 33, 33b, 48): replace cells now equal the RW strings (B-213, B-215, B-215b, B-067 and B-091 with "studio owner", "e-mail message", "Gmail label"). The lead sentence "This is a statement by the lead ..." is removed from all four. Status PROPOSED replaced by HELD. RW has NO other-branch string for B-215 and B-215b, so the invented other-branch cells of rows 33 and 33b are now "-" and the notes say so (nothing invented). Row 48 replace cell is "B-067: ... ; B-091: ..." (ids as labels only).
- Blocker 4 (row 36): replace cell = RW X-5a, other-branch cell = RW X-5b ("Today n8n keeps its own records and the lead table is in Postgres."); the "(SQLite)" text is gone; the cell [5] now says SQLite is only what the files say and P4b has not run.
- Blocker 5 (row 84, B-038) and all other mismatching replace cells: synced to RW word for word (rows 4, 7, 8, 10-13, 15, 18, 20, 23, 24, 25c, 26, 29, 31, 34, 37, 38, 40, 43-47, 49-52, 58-67, 69-72, 74, 79-84). Rows with several RW strings hold "id: string ; id: string".
- Major 8 (row 15): replace cell = B-032 and B-056 strings; marker changed to [CHANGES: card line deleted; file only for PLAN-4-NLITE-FROM-LEAD.md]. PLAN-4-NLITE-FROM-LEAD.md:194: RW has no string for it. I wrote none. It is stated in the row note as HELD and needs a new RW row (OPEN, needs the lead or the RW owner).
- Majors 9-11 (rows 7, 8, 79): synced (A-012 "e-mail message", A-016a "lead ID", B-219 wording).
- Major 12: Status words table rewritten (PASTE, DELETE, HELD, NO PASTE, SUPERSEDED; PROPOSED and CUT removed; FILE EDIT kept as a non-status kind), line 3, "Live rows" section and the notes of rows 14, 15, 32, 33, 48 now use only those words and the live RW statuses. "CUT by decision 1" became "Decided out by decision 1".
- Major 13: Live rows line now reads statuses from RW (A-005, A-084 HELD; A-087c, A-087d SUPERSEDED).
- Major 14: line-33 pointer now names the RW section "Status words (defined once ...)" and its "0b. Rows that wait, and what happens by default", with today's line numbers.
- Part 2 reader findings: rows 51 (B-046: DELETE now in the cell, the verdict cell says UNTRACED only), 52 (cell = B-054; verdict cell says UNSUPPORTED first, T1 half second and not counted), 58 (cell and why-cell now say review counts as lost), 62 (B-150a, b, c), 63, 66, 69 ("one case reported by another test session"), 74, 80 ("studio owner", note that the sentence is about the old desk script and who types y is BLOCKED, WL-1): all cells are RW text only, no orders or notes. Table 2 notes now start with "RW status: id STATUS". A Table 2 intro sentence says RW alone counts and the lane strings are older. The "Paste string ... row X" strings in 67 lane rows were synced to RW. Added a definition line for journal file, claim token and review. Typos repository"s fixed. Rows 54-56 "stale; now ..." cells now say where it is described.
- Nits: B-168 "272 s" (done via RW), B-201 lane cell now says kill rows "0 of 15" (variant b: "0 of 13" valid rows, PUB:20), row 33d now cites B-215 (RW covers the :95 notice in B-215; B-214 is :103), 33c note names RW B-214 HELD.

## Not done, with reason
- 18 RW paste strings have no row in CLAIMS-TABLE.md at all (V-11, V-57, N-2, N-4c, N-5a, N-6, N-9, N-10, N-11b, P-155, B-003a, B-003d, X-6a, X-6b, X-6c, S5-a, S5-b, S5-voice). They are RW-only rows (section 7 and notes) or lane-only claim ids without a Table row; adding Table rows would change row counts (87), so I did not. Next step: the lead decides whether CLAIMS-TABLE needs rows for them.
- Rows 78, 85, 86, 87 have no RW row; their text is untouched (the lead's text from OWNER-STEPS-q16-rows.md or the lead's wording answer).
- Not checked: whether every replace cell of rows 1-3, 5, 6, 9, 14, 16, 17, 19, 21, 22, 25, 25b, 27, 28, 30, 35, 39 equals RW (the compare script found no mismatch for them).

## Raw output
Before (round start): check_rw_ct_pairs: paste strings in RW: 136 | found word for word in CT: 70 | not found: 66.
After:
$ python3 claims-count.py CLAIMS-TABLE.md
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 49, 'RELAYED-ONLY': 70} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
$ python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
section '1': 51 rows
section '2': 19 rows
section '3': 71 rows
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
$ python3 tools/check_refs.py
PASS 5166 references
$ python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
paste strings in RW: 136 | found word for word in CT: 118
not found in CT: 18
  RW line 205 V-11 / PASTE / APPROVED: ____: flows real-v5 (compared with real-v4, real-v5 changes the CRM id step 
  RW line 230 N-5a / HELD / APPROVED: ____: n8n lets another run take over a lead that stopped only after a waitin
  RW line 232 N-6 / PASTE / APPROVED: ____: A CRM is the program where a company keeps its customer contacts.
  RW line 233 N-9 / HELD / APPROVED: ____: the real wait is read from the rehearsal, never predicted; no phone is
  RW line 234 N-10 / HELD / APPROVED: ____: wherever a wait is sped up, the screen shows the words sped up; the re
  RW line 236 N-11b / HELD / APPROVED: ____: Waits for the takeover with no timer on screen, then cuts or speeds up
Verdict counts unchanged (327: 119/70/62/27/49). tools/check_secrets.py reports 1 hit in flow-check/evidence-f8-r8.md:55 (a file I did not touch; not checked further).

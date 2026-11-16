# fix-f1-r8: claims table round 8 (fixer; static text edits, made-up data only; nothing reviewed yet)
Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/c8/ (CLAIMS-TABLE.md, RUNSHEET-WORDING.md as before the edits). Files edited: CLAIMS-TABLE.md, RUNSHEET-WORDING.md, this file. Rows 85-87 kept.

## What is uncertain or not done (first)
- The take scripts (run_real_check_n8n.py, n8n_drive.py) are not in this repository. Everything about what the take does is the lead's statement (Q13, ORDERS.md 10:23Z), not seen by us. Every paste string now says so.
- B-214 (what the take script does at a wrong or closed answer at the film pause) has NO wording. Row 33 used to say "a wrong or closed answer at the pause just ends the pause": Q13 does not say that, so I removed it. B-214 now gets only the HELD, DO NOT QUOTE marker (RW section 0b rule) until the re-pin check. Same for the notice fragment at :95.
- A change in how I resolved row 48: the old "note only: add (...)" for B-017 is gone; B-017 is no wording change in both files (CT verdict SUPPORTED, as a description of the old desk harness). The rows B-067 and B-091 carry the full text.
- No review of these edits. Archive: whether a removed contact can be restored: no file says (UNKNOWN); the desk code comment says "delete into the recycle bin".
- Added open question Q-H to RW section 4 (date and hour of the re-pin; default: no take before the lead writes the re-pin check is done). I did not invent a date.

## M2 (read myself: inputs/OWNER-STEPS-realrun-v3.md lines 103, 104, 112; no v4 of that file exists in this checkout)
:112 (step 20) says delete leftover contacts the lead counted: agrees with decision 2. :104 says two things: "closing the window or Ctrl-C early still archives" (out of date for the take) and "leftover contacts are deleted by you in the HubSpot UI, the lead gives the count" (agrees). TRUE reading: :104 and :112 agree only on who deletes leftovers; :104 as a whole disagrees with decision 2, so RW B-215b was right to rewrite it and CT row 33 ("do not disagree") was wrong. Row 33 now says so.

## Majors
- M1: RW B-214 was NO PASTE with the archive clauses left standing; now HELD marker in both files (CT row 33 and lane row B-214 say the same).
- M2: above. B-215b now named in CT row 33 (ids column, replace-with, note) and in the B-215 lane cell; it has no lane row of its own (claims-count and the checker would not count it).
- M3: row 48 now agrees with Q13 (no "removes from HubSpot after P4c"). Why it stays OUT OF THIS VIDEO and is consistent: none of the three files is filmed, shown or spoken; text is the same as RW B-067/B-091 (which RW lists as FILE EDIT, applied in step 0c.2). B-017 verdict: RW now says SUPPORTED (as CT), NO PASTE.
- M4: RW B-213 paste now ends with the contacts-after-the-take sentences; CT lane row B-213 and to-do row 32 carry the same tail.
- M5: row 33 replace cell no longer starts with a parenthesis; pasted strings are in double quotes behind bare labels such as [:103 first sentence, B-215] (CT rule L17: bare labels are notes). The caveat sentence is in every paste string, not only in a note.
- M6: RW P4c now scopes the ban to "the take's script" and allows a sentence about the old desk harness (as CT L125).
- M7/M8: words added in both files (CT Quick words, RW 0-words and Words and ids): "the lead" = the coordinator; "lead record / lead ID / the made-up person" for the made-up person; re-pin = the lead re-points the demo to the new core commit and checks the take files before the filming (a step of the lead, date unknown, Q-H); archive; harness; claim bridge line (CT claim = a sentence of a file; RW claim = the n8n reservation).
- M9 / counts (from the scripts, rc 0 both):
  - claims-count.py: SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNSUPPORTED 29, UNTRACED 51, total 327; lanes A 97, B 226 plus X 4 = 230; to-do rows 87; offenders 0; 327 unique ids.
  - 83 (CT) vs 80 (RW checker): the checker reads only A and B ids; CT counts the X rows too (X-1 UNSUPPORTED, X-2 OVERSTATED, X-4 UNSUPPORTED): 83 - 3 = 80. 51 vs 50: X-3 is UNTRACED: 51 - 1 = 50. Both numbers now explained in CT "Count" and RW section 6.
  - "14 added on purpose" was wrong: 12 ids (A-012, A-019, A-036, A-050, B-017, B-024, B-045, B-046, B-051, B-078, B-214, B-215), checked by script against the 95 claim ids in the to-do tables (83 flagged + 12 = 95). Fixed in CT line 53.
  - Rows: Table 1 has 45 rows (20 LIVE, of which 7 LIVE TEXT ONLY; 25 OUT), Table 2 has 42 (all OUT): 87 rows, 20 live, 67 out. Old text said 42/42, 17 live and "84 to-do rows": fixed to 45/42, 20, 87. Five rows carry no claim id (36, 78, 85, 86, 87), so 82 rows carry the 95 claims.
- check_runsheet_paste.py: rc 0, PASS (157 rows; 80 flagged, none without a row; 50 UNTRACED, 43 without a row by design). First run after my edit failed (apostrophe in "lead's statement", "NO PASTE (HELD)"); fixed to "This is a statement by the lead; ..." and "NO PASTE".

## Required sentences (verbatim, by grep)
"The old desk harness still deletes; the take does not." and "lead verifies at re-pin" are in the paste string of B-067, B-091, B-213, B-215, B-215b (RW) and B-067, B-091, B-213, B-215 (CT lane rows), CT rows 32, 33, 48. The caveat "This is a statement by the lead; the take scripts are not in this repository, and lead verifies at re-pin." is in each.

## Nits
N1 (B-215b comma variant) fixed; N2 (archive vs delete) fixed in the words; N3 fixed by the bridge; N7 harness defined. Not done: N4, N6 (n8n-flows/ oldest vs v4: not touched), N8.

## Commands
python3 claims-count.py CLAIMS-TABLE.md: rc 0. python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: rc 0 (PASS). Raw logs in the scratchpad c8 folder (cc2.txt, chk3.txt).

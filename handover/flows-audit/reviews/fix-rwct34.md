# fix-rwct34: fixes to RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)

Inputs: reviews/rw-ct-reader-r34.md (M1-M4), rw-ct-reader-r35.md (M1-M12), fix-rwct33.md. Reviewer words were checked against the file text before each change.
EGM was NOT run by me (no Skill access here); the lead runs the result review. Nothing was committed. RUNBOOK.md and QUESTIONS.md were not touched.

## Not done / uncertain (first)
- The exact phrase "reported by another test session; we have not seen its raw files" is NOT yet at every relayed number. About 8 places in RW and 22 in CT are left; most are quoted old sentences, DELETE rows or source notes. CT lane cells near lines 536, 587, 739, 741, 793, 905 and cell 269 could still take it. Not fixed.
- Lead-owned, not fixable here: which window shows each reply and when (new input row (w)); who speaks, captures and arranges windows (row (o)); the send command, send note and scene 4 timing.
- I did not open the raw rerun files in handover/demo/n8n-rerun/ (found on disk). HubSpot id vs vid stays UNVERIFIED.
- Nothing was run against n8n, Postgres or HubSpot (project is static).

## Done
- COLUMNS CROPPED added to A-016 rows, CT A-099/A-100 and input row (m).
- A-016a made a spoken-and-removed row everywhere; line 3 corrected; step 15 paragraph added.
- Frame instructions added in steps 11 and 12a; new UNANSWERED input row (w).
- Relayed numbers: exact phrase added where listed in the plan (see "Not done" for the rest).
- Unobserved-behaviour PASTE strings carry "built to work this way; read in the flow files, not observed"; HELD voice strings carry "read from the flow, not yet run"; lead-sourced ones say "the lead states that".
- CT B-195 cell equals the RW text.
- B-197: the README says 0 of 15; the 1 of 15 is the lead's own list. Old notes ("raw files not in checkout") were wrong and were corrected. Marked HELD with the open point.
- B-017 is UNTRACED in RW and CT.
- Six desk-repo rows annotated.
- Counts re-run: 330 claims; SUPPORTED 89, RELAYED-ONLY 64, OVERSTATED 84, UNSUPPORTED 15, UNTRACED 78 (66 without an RW row, X-3 included; the checker counts A and B ids only: 77 and 65). RW rows 199, paste strings 144.
- D2 defined once; Q-A points to Q28 item 4; "Open items that stop filming" list added under 0c with named defaults; B-045 cell, HELD voice strings and A-083 total row (new A-083b) fixed.
- Slip of mine: the first pass changed only one of three CT places for A-057; I restored the copies and redid it. Pair check now 144 of 144.

## Checks (run from handover/flows-audit)
- claims-count.py: total 330, offenders 0, ids unique.
- check_rw_ct_pairs.py: 144 found, 0 missing.
- check_runsheet_paste.py: RESULT: PASS (199 rows).
- check_refs PASS 5182; check_names PASS 655; check_secrets PASS 0 hits; check_counts PASS 52 files / 655 nodes.
- ruff format --check .: 920 files already formatted.

# fix-rswording14 (FIXER, 2026-11-16, static, nothing run, nothing committed)
Edited only RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT). Backups in the session scratchpad.
Inputs: reviews/rw-r7-reader.md, reviews/claims-r6-reader.md, reviews/citation-claims-t1-r1.md, and two extra coordinator lists (A-036, A-010, A-045, A-007, A-012, A-026, A-020).

## Checker output after the fix (run from flows-audit)
- check_rw_ct_pairs.py: 140 of 140 found, not found 0.
- check_runsheet_paste.py: 191 rows (55/19/72/45), 93 flagged ids all with a row, RESULT: PASS. 60 UNTRACED A/B ids, 50 without a row (allowed).
- check_refs.py: PASS 5168 references.
- claims-count.py: SUPPORTED 105, RELAYED-ONLY 68, OVERSTATED 80, UNSUPPORTED 16, UNTRACED 61 = 330; offenders 0. Lane A 21/24/38/6/11; lane B+X 84/44/42/10/50.

## Grade changes (CT)
- UNTRACED: A-037, B-079, B-121, A-025, A-032 (earlier), B-183, B-189 (desk repo absent).
- OVERSTATED: A-003, B-155, B-107, A-096, A-017, A-051, B-032, B-056, A-073, A-007, A-010, A-045, A-021, A-077, A-030, A-036.
- Markers: A-089 second-verdict marker, B-060 and B-053 text-only labels, A-012 and A-026 inner verdict words removed from the first phrase, B-003 wording.
## New RW rows: A-003 (SUPERSEDED by N-2), A-096, B-155 (PASTE), B-107 (HELD, later video), N-12 (HELD, pane label), A-045 (SUPERSEDED by A-010b).
## RW fixes by finding
Q31 item numbers (76 a-e, 73 c, 77, 39 c); counts (one total); A-016a/A-016d order; A-021 "that lead"; wait lower bound (longer than 75 s plus rehearsal margin); N-12 label row; DELETE rows wait for re-pin; B-045/B-046 rule when qs_01 passes; B-016/B-019 cell mapping (audit proposal); A-019a "three"; A-083 count by combination (18/19/20); N-11a deletes only the real-wait words; N-5a "second copy of the same flow" (RW and CT); step 3 "write down"; rehearsal 07:30Z = 13:00 IST (ORDERS.md line 171).
## CT citation fixes
Row 19 cites R:90 (R:82 same meaning, other words); rows 23b and 23c now quote what P:150 and P:153 really say, with the lead-in sentence cited only at R:90; A-020 cites R:33 only; Table 1 rows 8b and 31 no longer state verdicts.
## Not checked / honest gaps
- Not fixed: A-010, A-010b, A-010c comma splice (not re-read); reviewer item "A-042 UNSUPPORTED for a plan step" (below Major) not touched.
- B-016/B-019 cell mapping is an audit proposal, not read against the PLAN-4 table.
- Source lines of the citation checker's rows 85-87 not opened. A-007/A-010/A-045 grades are my reading, not run.
- QUESTIONS.md and ORDERS.md (lead-owned) may still carry old counts; not edited.

# Fix log, round 4 (last), queue item F1

Not done or not checked (read first)
- Nothing was run (static work). "Checked in text" means read, not run.
- Not fixed: the reader nits on pronoun drift (I / we / the agent), on the completeness of the list at line 94, on the several meanings of "take", and on the order of the Round 1 / Round 2 note paragraphs in lane A and lane B (cosmetic; left as is, no meaning lost).
- Not read: review-codebase-1.md (finding F-01) is not in this checkout; AGENT-SCOPE-DO-AND-DONT.md:20 cites it. B-214 and B-215 stay UNTRACED.
- Not re-checked by me: every other cite in the table. Only the cites the reviewers raised were read again.
- The labels "coordinator confirms" are still open: D1, D2, the K mapping (A-022), the row 78 wording.

Checked against the real files (reviewers right)
- Rows 13/18 were crossed. VIDEO-RUNSHEET.md:39 says "seven safe columns" (row 18); :50 lists seven columns with alert_attempts (row 13). Swapped; row 13 also names :39 second sentence, :62, :88.
- OWNER-STEPS-realrun-v3.md:103 says the script archives; :104 and :112 say the owner deletes leftovers in HubSpot. Row 33 now cites :103 against :104/:112.
- B-108 cite is RUN-ON-LAPTOP.md:82 (was :81). B-196 reason reworded ("file's own results table says NO MATCHING ROW").
- Row 36 cites DECISION-one-store.md line 8 only; :26 already calls it an aim, :14 does not.
- Row 15 now includes PLAN-4-NLITE-FROM-LEAD.md:194.

Changes (by finding)
- 'lead' for the coordinator replaced by 'coordinator' in audit cells; quotes and file names keep the old word; glossary says so.
- Glossary: mail_sent (set before the mail is sent), flow sets v2 to v5 and lease seconds, lane A, P-checks, F-nnn vs F-01, D1-D3, T17, T19, M1, `id`/`vid`, RELAYED-INDEPENDENT, RELAYED-LEAD, UNBACKED, stack, harness, burst, doubtful case.
- Money-risk warning (paid model call) added to Start here; Q7 sentence added as row 78 (Table 1, after row 40; proposed wording for the coordinator to approve).
- 11 SUPPORTED claims marked "text-only, needs run" (A-002, A-011, A-012, A-013, A-018, A-024, A-029, A-034, A-043, A-071, B-051); note beside the 114 added.
- 'verified' changed to 'checked in text' / 'not checked'; 'the coordinator still has to confirm both'.
- Column description (legend 4) fixed.
- Verdict reasons fixed without changing verdicts: rows 52 (B-054), 34 (B-183), A-097/13, 72-77, 10, 7, 39; K-label note added to A-022, A-085, A-086, rows 25, 27, 28.
- Row 3 and A-087: one figure "about 61 s" instead of "60 to 62 s".

Counts after the edits (claims-count.py)
- SUPPORTED 114, RELAYED-ONLY 69, OVERSTATED 49, UNSUPPORTED 25, UNTRACED 70; total 327 (lane A 97, lane B 226 plus X 4 = 230); to-do rows 78; offenders 0; ids 327 unique. No verdict changed, so no count block changed except the to-do rows (77 to 78, 40 to 41 before the take).
- Nothing committed.

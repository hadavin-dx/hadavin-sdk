# c6u design review, round 1 (egm-design, condensed copy of the inline report), 2026-11-16T18:26:57Z
Target REPORT-c6u.md (96 rows). 0 blockers, 5 majors, 6 minors. Do not run "apply all defaults" until M1-M4 are fixed. Read all 850 lines; ran nothing.
## Failures first
- M1 Rows 1, 2, 5, 15, 17, 19, 30, 34, 14 write "the 45 s lease setting is allowed" as settled text while the box holds the same lease words (label "setting: lease 45 s", card line 4 "other lease settings") under G12; release note v14 line 149 bars lease sentences without written approval. Add the G12 hold to row 8 item 12 or reword the carve-outs to "allowed only after G12".
- M2 Stale text in sections 0, 5a, 9: line 844 "ROW 95 IS ADDED" with vague wording and wrong counts (95/37/86 vs 96/38/87); line 833 names v30 and v14 (box says v32, v16); line 837 "for c6t"; line 380 "36 rows" (should be 38); lines 69/76 "89 of 94", "94 edits". Verifier (221 checks) caught none.
- M3 "Newest sheet" stale again: steps-edits now holds OWNER-SHEET-v33-SOURCE, build-v33.py and LEAD-RELEASE-NOTE-v17-SOURCE. Re-run the check last; make the box row conditional.
- M4 Row 96 old text "30 s EST" occurs 3 times in its file; breaks the "occurs once" apply rule. Anchor to something unique on line 41.
- M5 The apply target tree is never named; no tree copy shipped so C-1/C-1b cannot be re-run; C-1 shows DONE without "on scratchpad copy; UNVERIFIED against real files".
- m1 row 76 "relayed" tag missing, same cell as row 39. m2 row 96 Time cell says 40 s but the default card is 79 words (35 s). m3 stale run-sheet leftovers (rehearsal items 3,5,6; risks items 7,8) left unfixed: not an allowed exception, add rows. m4 L-APP2 (E-52) not in this report; confirm other track carries it. m5 box about 2,400 words, still dense. m6 verifier exits 1 on c6t/c6s/c6r reports.
## Held
96 = 49+38+3+6; card arithmetic; about 20 UTC/IST pairs; weekdays; lane3 numbers; ORDERS cites; lease sentence stays out of the public post.
## Not checked
No script run; old texts not checked against real files; evidence-c6u-independent not read.

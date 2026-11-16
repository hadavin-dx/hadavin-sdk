# c6r changes: every finding of the c6q reviews and the independent evidence, mapped to its fix or to the exact lead question

Date: 2026-11-16 (UTC; IST = UTC + 5:30). Builder: build-only sub-agent. Nothing is applied, committed or pushed. REPORT-c6r.md is built by evidence-c6r/build_c6r.py from REPORT-c6p.md (read only) plus the c6q and c6r patches. REPORT-c6q.md and REPORT-c6p.md were not edited.

## FAILURES AND GAPS FIRST (what is not done or not verified)

1. NOT VERIFIED: the rows were checked against a copy of the source files in the build session's scratchpad folder, not against the repository. Equality of the copy with the real files is unverified. In the repository only inputs/DECISION-one-store.md can be read; the files of 89 of the 94 rows cannot (the verifier recounts this). The builder who applies the rows must first confirm that each old text still occurs once in the real file.
2. NOT DONE (two reviews ask for opposite things): the box is 3,490 words, longer than the c6p box (about 3,030) and longer than c6q (about 2,780), because the naive review asked for a what-to-type block and for every internal word to be explained. Lead question: move the second list of words into section 1?
3. NOT DONE: section 0 still starts with history before the how-to; the words EGM and KEY (four meanings) are not defined in the box (naive minors). Moving text between sections is the lead's decision.
4. NOT DONE: the card row's own Time cell on run sheet line 41 (30 s EST) is edited by no row; an edit would need a text that contains a table border. Lead question: change it to 40 s EST by hand when row 11 is applied.
5. OPEN, not mine to close: gate G12 (approval of the lease wording), Q27 meaning and the delete-path criterion (ORD:232, OWNER-OPEN), L-SAVEERR owner confirmation, who adds the 45-second sentence to the owner sheet and release note, which owner sheet is final (v29 A and B were last written 16:46:37 UTC = 22:16:37 IST; the check time of this build is the one printed in REPORT-c6r.md and the verifier fails if a v29 file changes after it).
6. NOT RUN: n8n, any flow, the harness, any stopwatch run. The seconds are estimates (words / 150 x 60).
7. If scene 3 and card line 1 are cut (G12 not approved), the run sheet totals fall; row 11 does not cover that case (lead question in section 9).

## Map

| Finding | Fix | Where |
|---|---|---|
| Design M-A | gate: card line 1 and scene 3 caption not filmed before 'lease wording approved' with UTC and IST; repeat more than 45 s after the first send is mandatory when the plain statement is on the card or caption | row 8 item 12; section 3e; verify 'M-A' |
| Design M-B | card line 2 says 'it sends an alert'; 'one alert' only for stand-in tests (rows 14, 74 and the box) | rows 14, 74; verify 'one alert' |
| Design M-C | Q27 reading labelled as the report's assumption, OWNER-OPEN (ORD:232); does not block Wed 18 Nov; L-DEL says what is still open | box, row 8 item 11, section 9 |
| Design M-D | key reaches the scan by a pattern file in memory or standard input, never a command line, never on disk; hit means cancel or replace the key and treat runs as compromised; item 16 repeats the real-key search | row 6 items 15, 16; verify 'M-D' |
| Design M-E | failed-run saving split off: new question L-SAVEERR (default No); rows 53, 55, 62, 64, 66, 68 wait; row 92 sets saveDataErrorExecution none; counts: ready 49, defaults 36, check 3, waiting 6, wave 1 = 85 | box, section 3, 3b, 3c; verify C-4a (all rows and defaults only) |
| Design M-F | one construction in the length table | box table; verify |
| Design minors | row 11 viewer cell; rounds text reworded (QUESTIONS.md line 24 quoted); report voice removed from rows 40, 48, 49 and row 6 item 14; 'expected' and pruning wording in rows 14, 44, 50, 52; made-up domain and marker check in row 6 item 12; run length for the latest start 18:04 UTC = 23:34 IST in row 8 | rows 6, 8, 11, 14, 40, 44, 48, 49, 50, 52 |
| Naive M1 | 'take' = filmed run; 'the recovery flow claims the contact again' replaces 'takes over' everywhere | box, rows 13, 21 and prose; verify |
| Naive M2 | one construction | box table |
| Naive M3 | row 11 viewer cell now states the change (30 s to 40 s card, about 180 s to about 190 s) | row 11 |
| Naive M4 | three stop-rule entries added (real-key scan items 15 and 16, lease wording approval, made-up domain and marker) | section 3e |
| Naive M5, M6 | claim table, take database, C-3 to C-9, G12, K3B, cut number, money stop explained; WHAT TO TYPE block on top | box |
| Naive minors | '72 edits' to 94; verify-c6p to verify-c6r; 'items 11 to 14' to 11 to 16; section 2 one run to two runs (n=2); build_mainframe.py added to the short-name table (BMF); 'if L-POST stays yes' not found in the c6r text (no change needed) | sections 0, 1, 2 and row 8 |
| Independent evidence, 8 missed mutations | weekday check (all pairs), no lease sentence on row 21, case-insensitive 'The lease question', count statements ('apply on the default', wave 1 rows), stale '58 s' in the box, '(within 45 seconds)' in rows 13, 14, 21; each has a negative control (E1 to E8) | verify-c6r.py; neg_controls_c6r.py |
| Independent evidence, stale v29 line | sheet check rerun (static-checks.sh); report and verifier state the three real v29 files and their real written times; the verifier fails if one is newer than the stated check time | box L-SHEET, section 0 |
| Coordinator 1 | source-copy statement | section 0 |
| Coordinator 4 | IST next to the 22:10 example in the box (checked) | box |

## Evidence files

evidence-c6r/verify-c6r.py and verify-c6r-output.txt (SUMMARY line gives the check count), evidence-c6r/neg_controls_c6r.py and neg-output.txt (78 copies: one unchanged control that must pass, 77 changed copies that must fail), evidence-c6r/static-checks.sh and its output.

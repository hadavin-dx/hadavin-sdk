# c6s-CHANGES.md: every finding of the c6r reviews and its fix (builder round 4)

FAILURES AND GAPS FIRST (what c6s does not do or has not proven)
- Nothing in the edit table has been applied; n8n, the flows and the harness were NOT run; no live call, no spend, no commit.
- The 94 rows were checked against the scratchpad copy of the source files (only 5 of 94 rows can be read in the repository); equality of that copy with the real files is UNVERIFIED.
- The EGM review steps (reviewers, evidence runner) are the studio lead's; verify-c6s.py is the builder's own check: it proves text matches what I wrote and that listed slips are gone, not that a statement is true.
- The leak scan program (check C-6) does not exist; the real-key scan has never run. Needs a builder the studio lead names, a second reader and a fake-key test.
- Card line 2 is backed only by stand-in tests; gated in c6s on a loopback re-smoke alert mail (needs-lead, needs n8n).
- Gate G12 (lease wording) is OPEN with the studio lead (release note v14, LRN14:33 and LRN14:8, does not close it). Cut case and the plan-versus-owner conflict on PLAN:125 are open with the studio lead (needs-lead).
- The box is 3,4xx words by the verifier's count: shorter than c6r only by a few words, because the stranger-reader review asked for more explanation (steps, G12, Q27, the C-9 circle). Not reduced further without dropping what the review asked for; the studio lead decides.
- Seconds in the card tables are estimates; the owner sheets v30 were still being written at the check time (the verifier fails if one changes after it).

MAP: finding id -> fix (where it is in REPORT-c6s.md)
| Id | Fix | Where | Check in verify-c6s.py |
|---|---|---|---|
| F1 | failed-run saving defaults to none; C-4a, C-11 and the C-4 row list rewritten; PLAN:125 overridden on that one point (owner's words cover successful runs only) | L-SAVE, box, glossary, section 7 (C-4, C-4a, C-11), section 9 | F1 checks (6) |
| F2 | card line 2 gated on an alert mail seen in the loopback re-smoke on the edited flows (UTC, IST, a name); stop-rule row added; row 14 reason | row 8 item 12, section 3e, box, row 14 | F2 checks (2) |
| F3 | scan after every rehearsal with real accounts and after the take BEFORE deletion; scanner read by a second person and tested with a fake key; counts only; in place or a deleted-and-counted dump; swap point | row 6 items 15, 16, reason; section 3e; C-6 | F3 checks (7) |
| F4 | sheet check rerun over v19 and later (v30 exists; static-checks.sh); newest version and release note named; verifier fails on a newer sheet than the check time and on a higher version; v14 cited, G12 still open; wider reading of G12 labelled own assumption | box, section 0, section 3, C-10c, section 9, short names (LRN14) | F4 checks (5) |
| m1 | approval must cite the crash-then-repeat-during-recovery case (1 row, 1 mail) | row 8 item 12 | m1 |
| m2 | 'expected to be true until C-9 part 2' | row 13 reason | m2 |
| m3 | cut-case totals once (box CUT CASE) and a two-line Time-cell replacement (old '30 s EST', new '40 s EST' / '35 s EST'); a lead action in the box and in L-CARDLEN; pointers elsewhere | box, row 11 reason, section 9 | m3 |
| m4 | box example time later than the check time, with IST | box answer line | m4 |
| M1 to M8 and naive minors | box rewritten: roles first, does-not-do list before the answer line, order of reviewer names explained, one OWNER ONLY rule (L-SHEET, L-SAVEERR, separate lines), Q27 (a)(b)(c) and G12 explained, 'you' for the studio lead, numbered steps for rows 23, 58, 59, the G12 approval and the 45-second sentence (you or a named builder), the C-9 part 2 circle, EGM/KEY/FINAL/RUN/CHECK/ROW defined; section 0 history moved to section 1b; words take/claim/alert fixed; stale names fixed (c6s, items 11 to 16, L-SAVEERR in the glossary, the two different 36s, row 11 in 5a) | box, sections 0, 1, 1b, 3, 5a, 8, 9 | naive checks (13) |
| Independent evidence (2 of 123 failed; glob missed v30) | static-checks.sh globs v19 and later and lists v31+ | evidence-c6s/static-checks.sh | F4 |

Evidence files: evidence-c6s/verify-c6s-output.txt, neg-output.txt (negative controls), static-checks-output.txt, build_c6s.py.

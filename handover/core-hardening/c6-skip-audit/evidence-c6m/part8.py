P("## 8. Coverage: finding -> fix -> where (every item of the two c6l reviews)")
P("")
P("| Review item | Fix | Where / check |")
P("|---|---|---|")
COV = [
    ("Design B1: gate (row 8, row 6 item 12) built on the wrong script, contradicts Q23, never cites Q22 to Q34, calls the conflict new, unsatisfiable 0-hit rule", "Rows %d and %d re-issued against Q19 item 1, Q23 and Q27; both scripts named and the video's script named; the decisions-file 0-hit requirement dropped; archive-after-error no longer stated as behaviour; 'new' removed; L-DEL default is what Q23 says with the UNVERIFIED part labelled; Q22, Q23, Q25, Q27, Q21.1 cited where they answer" % (n("rs59"), n("rs71")), "Sections 0, 3 (L-DEL, L-LEASE), 6; check C-10b, C-10d redefined; verify-c6m.py: no 'archive or delete' pipe text, rows say run_real_check_n8n.py"),
    ("Design M1: unconfirmed defaults attributed to decisions (rows 1, 3, 5, 31)", "Rows reworded: a default is called a default of the named question; only decision 1 is cited for the cut number", "verify-c6m.py scan 'decided' next to L- defaults; table 3b"),
    ("Design M2: L-CARD is a multi-decision question", "Split into L-CARD, L-CARDCUT, L-CARDTEXT; row 14 reason fixed; each card row depends only on what it changes (section 3 and 3b)", "Table 3b"),
    ("Design M3: rows 36 and 39 are corrections tied to L-PAGE", "Rows %s no longer wait for L-PAGE (corrections apply whatever you answer); row %d split from the rest" % (ids(["pg149a", "pg154"]), n("pg148")), "Table 3b"),
    ("Design M4: row 17 tied to L-ROUND although removing the old caption is independent; is the 'sped up' label a timing number?", "Row 17 split; the live stopwatch and 'sped up, real wait N s' label are named as this run's own clock, not a timing number (Words, L-APPROX)", "Words; section 3"),
    ("Design M5: saved runs have no gate (C-4, C-6 not on the run sheet; no owner)", "Row %d item 14: the take is blocked until two lines (import check passed, leak scan for saved runs passed), each with a UTC and IST time and a name, are written; the studio lead owns it and names the builder" % n("rs71"), "Section 3d; checks C-4, C-6"),
    ("Design M6: wrong-word slips 'studio lead's made-up name', 'studio lead table'", "The replacement rule was fixed and rows rewritten; verify-c6m.py greps for 'studio lead' followed by made-up, table or name", "verify-c6m-output.txt"),
    ("Design m1 (rows 21, 23 tied to C-4)", "Dependencies set per row by the DEP table in build_c6m.py", "Table 3b"),
    ("Design m2 (rows 42, 45, 47 say 'not for the web page')", "Wording 'see statement 20' without saying whether it is for the page", "Rows %s" % ids(["pg105", "pg120a", "pg120b", "pg139"])),
    ("Design m3 (statement 20 names voided runs, not the overlap)", "Row %d names the overlap: 5 kept runs overlap the voided K3B window; whether it disturbed them was not checked" % n("pg149a"), "Section 0 (18 runs); void-check-output.txt"),
    ("Design m4 (dates exist)", "Take target Wed 18 Nov, money stop Mon 23 Nov 18:29 UTC = 23:59 IST, cancel by 18:19 UTC = 23:49 IST, post Wed 25 Nov 15:00 UTC = 20:30 IST, first rehearsal after the loopback re-smoke", "Words; section 3d"),
    ("Design m5 (row 22 refers to a leak-scan section only row 49 creates; row 1 L-KILL (b) keeps 'unmeasured')", "Row 22 text no longer relies on the other section; the unmeasured wording is fixed by the Words entry", "Reading"),
    ("Design m6 (verify scanned page files only for 60.1 to 61.9; 'never deletes' hits not acted on)", "verify-c6m.py scans the new text of every row for the figure and for the 'never deletes' phrases", "verify-c6m-output.txt"),
    ("Naive B1: undefined labels before the decision; no action list", "Action box first (section 'Start here'): every L- label with plain meaning, default, who answers; the reply line; exact limits; Words block", "Top of the report"),
    ("Naive M1: 'lead' two meanings; 'studio lead's made-up name'", "Studio lead / owner / contact record fixed in new texts; Words block; verify scan", "verify-c6m-output.txt"),
    ("Naive M2: owner versus studio lead, how to reach the owner", "Words: the owner is reached through the studio lead; L-SAVE answered by the studio lead", "Words; section 3"),
    ("Naive M3, M4, M5: take, line, sheet, claim", "Words block: take, take script, rehearsal; line N, card line, notice line; run sheet, owner sheet; the word claim not used", "Words"),
    ("Naive M6: apply-all-defaults limits, builder and reviewer, answer format, unreviewed edits, how to reverse, 3b unreadable", "Box: exact reply line, what is and is not applied, unreviewed texts named, reversing; table 3b gets a plain heading", "Top; sections 3b, 3c"),
    ("Naive M7: voided and kept runs unexplained", "Words (kept run, voided run); section 0 gives who and why as far as the file says, and the overlap", "Section 0"),
    ("Naive M8: no dates; times without IST; n= undefined; 'no number on screen' versus 'setting: lease 45 s'", "Dates in UTC and IST; n = number of runs; the setting label is not a timing number", "Words; section 2"),
    ("Naive M9: section 5 hard to read; review codes undecoded", "New column 'What the viewer sees'; glossary decodes review item names; the second reading aid is the apply-order sentence in section 1", "Section 5; glossary"),
    ("Naive m1, m3, m8: n8n, HubSpot, CRM, EGM, import, execution list, short names, developer paths", "Words and glossary; the paths are glossed in section 0", "Words; section 4"),
    ("Naive m2: delete / archive senses", "Words: DELETE, ARCHIVE, CLEARING; section 6", "Words"),
    ("Naive m4: L-ROUND clashes with review round", "Renamed L-APPROX", "Section 3"),
    ("Naive m5: 'unknown with one alert' good or bad news", "Section 0: it is the intended safe end", "Section 0"),
    ("Naive m6: C-9 FAIL cell is an allowance", "C-9 FAIL cell says 'fail; the studio lead may only write index not seen, accepted'", "Section 7"),
    ("Naive m7: eight flow rows share one long reason", "Flow-file rows keep one shared reason sentence, repeated text shortened", "Section 5"),
    ("Slip of c6l: cited a static-checks section C-10c that did not exist", "Section added and output regenerated; newest sheet v26-SOURCE included", "Section 0; static-checks-output.txt"),
]
for a, b, c in COV:
    P("| %s | %s | %s |" % (a, b, c))
P("")

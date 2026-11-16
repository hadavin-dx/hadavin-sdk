# Section patches for REPORT-c6n.md. Executed by build_c6n.py with names: sub, rows, cnt, fl, D in scope. Every patch asserts exactly one match.
import re


def replace_line(text, startswith, newline):
    ls = text.split("\n")
    idx = [i for i, l in enumerate(ls) if l.startswith(startswith)]
    assert len(idx) == 1, (startswith, len(idx))
    ls[idx[0]] = newline
    return "\n".join(ls)


def insert_after_line(text, startswith, newlines):
    ls = text.split("\n")
    idx = [i for i, l in enumerate(ls) if l.startswith(startswith)]
    assert len(idx) == 1, (startswith, len(idx))
    ls[idx[0] + 1:idx[0] + 1] = newlines
    return "\n".join(ls)


def spoken_words():
    ws = []
    for k in (13, 14):
        for q in re.findall(r'spoken: "([^"]*)"', rows[k]["new"]):
            ws.append(len(q.split()))
    return ws


def patch_sections(text):
    # global renames of evidence names (this version's files)
    text = text.replace("evidence-c6m/", "evidence-c6n/").replace("verify-c6m-output.txt", "verify-c6n-output.txt").replace("verify-c6m.py", "verify-c6n.py")
    W = spoken_words()
    total_w = sum(W)
    secs = round(total_w / 2.5)  # 150 words a minute = 2.5 words a second
    # ------------------------------------------------------------ section 0
    text = replace_line(text, "- THE LAST REPORT (REPORT-c6l.md) FAILED TWO INDEPENDENT REVIEWS",
        "- THE LAST REPORT (REPORT-c6m.md) FAILED TWO INDEPENDENT REVIEWS (review-c6m-naive.md: 1 blocker, 8 majors, 9 minors; review-c6m-design.md: 2 majors and 7 minors; its first lines say '1 major' but it lists two, and this report fixes both). "
        "This report fixes every item of both (section 8: finding, fix, check). THIS REPORT HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them).")
    text = insert_after_line(text, "- A SLIP OF REPORT-c6l.md THAT I FOUND AND CORRECT HERE", [
        "- SLIPS OF REPORT-c6m.md THAT I CORRECT HERE (my own, found by the two c6m reviews): (1) the 45-second check was measured from the first reply of scene 2, but the lease starts when the first send arrives (the claim row is written then, JF:97), so a repeat 42 s after the reply could be 48 s after the send; rows 6, 13 and 21 now count from the first send and ask for under 30 s; "
        "(2) the closing text said the take has 'two stores' although the stage journal file is a further record (Q21.3); no viewer-facing sentence on the number of stores is proposed any more; (3) 'lead' meant a contact and the studio lead; (4) two gate lists were mixed up; (5) the action box used terms before they were explained; (6) a phrase count was labelled 'key read-only' but counts any mention of read-only; (7) rows 40 and 48 cited a file that is on another branch.",
        "- SPOKEN LENGTH OF THE CLOSING CARD, NOT TESTED (new in this version; the new texts of rows 13 and 14 caused it): the four spoken card lines hold %d words (%s; counted by evidence-c6n/verify-c6n.py); at about 150 words a minute that is about %d seconds of speech, and the run sheet gives the closing card 30 s (row 11 adds up with 30 s). "
        "The run sheet says 'voice over one card', and no file says whether all lines are read aloud or shown as text. The stopwatch run (rehearsal list item 10) shows the true length; if it is over 30 s, shorten card lines 3 and 4 or give the card more time and re-total row 11. I did not change the card time, because no file gives the owner's speaking speed." % (total_w, " + ".join(str(x) for x in W), secs),
    ])
    text = sub(text, "phrase counts per sheet (never deletes / read, create and change only / does not delete / key read-only)",
               "phrase counts per sheet (never deletes / read, create and change only / does not delete / any mention of read-only or read only, which can be about something other than the HubSpot key)")
    text = sub(text, "C-10b, C-10c (second part) and the second part of C-9", "C-10b, C-10c part 2 (the sheet the owner reads, after L-SHEET) and the second part of C-9")
    text = sub(text, "the new texts hold no internal label and no wrong-word slip.", "the new texts hold no internal label, no wrong-word slip and no bare 'lead' for a contact; each sentence of the new run-sheet gates names who stops.")
    text = sub(text, "so 5 of the 18 kept runs ran at the same time as a voided run; whether that disturbed them was not checked.",
               "so 5 of the 18 kept runs ran at the same time as a voided run. I do not say this is harmless: whether it disturbed them was not checked, so the range 60.1 to 61.9 s carries that caveat (needs-lead, section 9).")
    text = sub(text, "the reason for each is the one in the row (error text, or never reached a final state).",
               "the reason for each is the one in the row (error text, or never reached a final state). A run that never reached a final state (VOID-fl45k3b) has no crash-to-final time, so leaving it out cannot change the range 60.1 to 61.9 s; but a crash run that never finished could also be a real failure that the figures leave out, and no file says who decided to void it. The figures therefore must not be read as 'every crash run recovered' (the 8 runs that ended 'unknown with one alert' are a different, intended end, explained below). Needs-lead: ask the lane3 session why (section 9). Page statement 20 (row 39) discloses both voided runs.")
    text = sub(text, "are different measurements of the same 18 kept runs:", "are different measurements of the same 18 kept runs (the voided runs VOID-fl45k3b and VOID-fl45k6c are not counted):")
    text = sub(text, "'each of 18 runs' without the 2 voided runs (c6k)", "'each of 18 runs' without naming the 2 voided runs VOID-fl45k3b and VOID-fl45k6c (c6k)")
    # ------------------------------------------------------------ section 1
    text = sub(text, "the row numbers are the same as in REPORT-c6l.md.", "the row numbers are the same as in REPORT-c6l.md and REPORT-c6m.md.")
    text = sub(text, "'ready' = no open question and no open check.", "'ready' = no open question and no open check (the text can be applied; it does not mean that the gate the text adds has passed).")
    # ------------------------------------------------------------ section 2
    text = sub(text, "before the recovery flow may take it again. Not a measurement |", "before the recovery flow may take it again. Not a measurement; the video says it as a setting |")
    text = sub(text, "The setting label (lease 45 s) and the live stopwatch are not timing numbers (Words). The kill-to-final and from-n8n-up figures are for the 18 KEPT runs only; the two voided runs are described in section 0.",
               "The setting label (lease 45 s) and the live stopwatch are not timing numbers (Words). The kill-to-final and from-n8n-up figures are for the 18 KEPT runs only; the two voided runs, VOID-fl45k3b and VOID-fl45k6c, are described in section 0.")
    # ------------------------------------------------------------ section 3
    text = sub(text, "May the closing card and the scene 3 caption say: 'We say this only when the second send comes within 45 seconds of the first. The 45 seconds is a setting: for that long the system keeps a contact record for the run that took it first.'?",
               "May the closing card and the scene 3 caption say: 'We say this only when the second send comes within 45 seconds of the first send. The 45 seconds is a setting called the lease: for that long the system keeps that contact reserved for the run that took it first.'?")
    text = sub(text, "(a) is used because decision 8 (DEC:9) allows no extra test run with real accounts, K3B and K3 were never run on the real-v5 flows, and the old K3B sentence is false as written.",
               "(a) is used because K3B and K3 were never run on the real-v5 flows (no result exists for the flows of the take) and the old K3B sentence is false as written. (Decision 8, DEC:9, only replaces the real-account smoke test by the loopback re-smoke; it is not the reason.)")
    text = replace_line(text, "| L-ONEDB | studio lead | Ratify or veto",
        "| L-ONEDB | studio lead | May any text a viewer sees say how many databases or stores n8n and the take use, before the loopback re-smoke has shown which database n8n uses (check C-8)? Facts: n8n has its own database; our claim table is in a Postgres database; the stage also writes a journal file (Q21.3 at ORD:152 calls it the one stated exception of decision 10). So 'two stores' is not true and is not used. After C-8 passes, the only wording allowed is the studio lead's own: 'one Postgres server, two databases' (Q21.3). | No: no viewer-facing text says anything about the number of databases or stores until C-8 passes. The target wording of decision 10 goes into DECISION-one-store.md marked as a target (rows 72, 71, 70). No row of wave 1 depends on this question; rows 58 and 59 wait for C-8 only. | No | If yes: the studio lead gives the sentence (it must not say 'one store' or 'two stores') and a builder adds a row. | none |")
    text = sub(text, "OWNER ONLY (the studio lead asks him; the studio lead may answer if the owner agrees)", "OWNER ONLY (the studio lead asks him; if the owner agrees, the studio lead may answer for him)")
    text = sub(text, "Until then the sheet says 'lead verifies at re-pin'.", "Until then the run sheet says 'UNVERIFIED' and that the studio lead verifies at the re-pin (the order's own words: 'lead verifies at re-pin').")
    text = sub(text, "the studio lead says so and a builder re-issues rows 8 and 6. | none (rows 8 and 6 are written to the answer) |", "the studio lead says so and a builder re-issues row 8. | none (row 8 is written to the answer) |")
    text = sub(text, "Rows it does not apply (they wait for a check): 23, 58, 59.", "Rows 6 and 8 are in the ready rows: their text can be applied now, but the gates they add stay closed until the studio lead writes the lines they ask for (Words: READY). Rows it does not apply (they wait for a check): 23, 58, 59.")
    text = sub(text, "(item 14 of the rehearsal list, row 6)", "(item 14 of the REHEARSAL LIST on the run sheet, row 6)")
    text = sub(text, "no hour for any rehearsal step is written in any file I read.", "no hour for any rehearsal step is written in any file I read; the studio lead chooses the hours and writes each as UTC and IST (example: 2026-11-17 09:00 UTC = 14:30 IST). Scenes 5 to 11 (L-CUT): no edit; the studio lead decides later whether a later video uses them.")
    # 3e: stop rules
    STOP = [
        "3e. STOP RULES for every gate this report puts on the run sheet (who stops, who is told, may the take go on). 'Studio lead' and 'owner' are the two roles of Words. Whoever sees a failure first says stop; only the studio lead decides what happens next.",
        "",
        "| Check (where on the run sheet) | Passes when | If it fails: who stops | Who is told | May the take go on? |",
        "|---|---|---|---|---|",
        "| Active flows (rehearsal list item 11) | only workflows imported from n8n-flows-real-v5 are active | studio lead | the studio lead writes the result in the handoff note | No, not until the list is right |",
        "| Owner sheet (rehearsal list item 12) | the sheet says the owner deletes leftovers by hand and does not state the key's scope unless the owner confirmed it | studio lead | the owner, if the sheet needs his fact | No rehearsal with real accounts and no take until corrected |",
        "| Repeat-send timing (rehearsal list item 13) | gap from first send to repeat send under 30 s; CRM 1 row; test mailbox 1 mail | the person who sees it; the studio lead decides | the owner, if the take is affected | In a rehearsal: redo scene 3. In the take: stop; the studio lead decides whether to film again (a second take needs the owner's spend limit to cover it: the studio lead computes the retake count, Q21.4) |",
        "| Saved-runs gate (rehearsal list item 14: import check C-4 and leak scan C-6) | both lines are written with UTC and IST time and a name | studio lead | the owner (the take is delayed) | No: no take and no rehearsal with real accounts |",
        "| Contact deletion (risks list item 11) | the four lines are written and the search shows no archive or delete call | studio lead | the owner, if a line is found | No, until the studio lead and the owner have decided in writing |",
        "| Repeat-send rule seen (risks list item 12) | the table rule on the contact id is seen in the take's own database | studio lead | the owner, before 'index not seen, accepted' is written | Only without scene 3 and card line 1, unless the studio lead writes 'index not seen, accepted' with UTC and IST time before the take |",
        "| Execution list before scene 1 and scene 2 (row 23, check C-5) | every row is later than the take start time; no rehearsal data | studio lead | nobody, if it passes the second time | Only after the check passes again |",
        "",
    ]
    text = sub(text, "\n## 4. Plain-word glossary", "\n" + "\n".join(STOP) + "\n## 4. Plain-word glossary")
    # ------------------------------------------------------------ section 4
    text = sub(text, "The files call the studio lead 'the lead'. | H6:53 |", "The files call the studio lead 'the lead'. They are two roles; no file says whether one human fills both. | H6:53 |")
    text = sub(text, "so that it cannot be mixed up with the studio lead. 'Lead id' and 'lead key'", "so that it cannot be mixed up with the studio lead. The one exact decision sentence 'a lead sent twice with the same id is processed once' keeps the word 'lead'; there it means a contact. 'Lead id' and 'lead key'")
    text = sub(text, "the studio lead's session note (the handoff folder of the studio) where facts such as the list of active workflows are written down; not in this repository.",
               "the studio lead's session note (the file handoff\\SESSION-HANDOFF.md in the studio folder) where facts such as the list of active workflows are written down; not in this repository.")
    NEW_GLOSS = [
        "| re-pin, at the final head | the moment the studio lead puts together the final version of the take files and reads them again. The developer rule on core modules uses 're-pin' for moving every demo to the newest shared code; the orders use 'at re-pin' and 'at the final head' for this moment, and the audit cannot see when it is. | ORD:132, ORD:191 |",
        "| risks list, rehearsal list | two numbered lists of the run sheet: 'Risks the owner must see' (line 59 is its item 10; row 8 adds items 11 and 12) and 'What must be rehearsed on the laptop before the take' (line 71 is its item 10; row 6 adds items 11 to 14). | RS:59, RS:71 |",
        "| hiding a run, automatic removal (pruning) | hiding = removing a row from the execution list on the screen; automatic removal = n8n erasing old runs by itself. Whether hiding also erases the data is not verified. The files use 'clean-up' for several of these things; this report does not. | NS:42 |",
        "| ready | a row whose new text can be applied now; the gate the text adds may still be closed. | section 1 |",
    ]
    text = insert_after_line(text, "| handoff |", NEW_GLOSS)
    text = sub(text, "| c6b to c6m | successive versions of this audit report; c6m (this file) supersedes c6l;", "| c6b to c6n | successive versions of this audit report; c6n (this file) supersedes c6m;")
    # ------------------------------------------------------------ section 5 reading aids
    AIDS = [
        "5a. WHAT CHANGES FOR A PERSON WATCHING THE VIDEO OR READING THE PAGE (the 12 rows that change something a viewer sees; the full table follows):",
        "",
        "| Row | Where | What a viewer sees now | What a viewer sees after the row |",
        "|---|---|---|---|",
        "| 1 | scene 4 | a caption with a test result and a sentence about crash tests | no test result in seconds and no crash-test words; the stopwatch and 'setting: lease 45 s' stay |",
        "| 12 | closing card | six spoken lines | four spoken lines |",
        "| 13 | closing card, line 1 | 'a lead sent twice with the same id is processed once' | the same sentence plus: only when the second send comes within 45 seconds of the first send (the lease) |",
        "| 14 | closing card, lines 2 to 4 | old history numbers, a recovery estimate, a retention line, a not-tested line | what an alert is and no statement about how fast it arrives; what n8n may keep; what was not tested |",
        "| 15 | closing card | numbers of older tests as history | none of them |",
        "| 17 | scene 4 caption row | 'recovery takes about the lease plus 25 to 30 s' | no test result in seconds; stopwatch and lease label stay |",
        "| 21 | scene 3 caption | one caption line | a second caption line with the 45-second sentence |",
        "| 22 | scene 2 | nothing | a rule for the owner: never put a key, password or token in a form field |",
        "| 24 | scene 1 | an empty execution list | the list shows the recovery flow's run every 30 seconds |",
        "| 33 | web page, scene 4 wording | the cut number and 'about a minute' | no caption wording |",
        "| 41 | web page, statement 20 | the range 60.1 to 61.9 s | marked not for the web page |",
        "| 43 | web page, statement 19 | the 13-minute alert delay | marked not for the web page |",
        "",
        "5b. THE CLOSING CARD, BEFORE AND AFTER (the old file numbers six lines, the new card four; rows 4, 12 to 15 and 20):",
        "",
        "| Old line (file now) | What it says | New line (after rows 12 to 15) |",
        "|---|---|---|",
        "| 1 | the repeat-send statement | card line 1 (row 13) |",
        "| 2 | history: 80 kills, 40 ended unknown | cut (rows 14, 15) |",
        "| 3 | recovery about the lease plus 25 to 30 s | cut (rows 14, 15) |",
        "| 4 | alerts: two or one | card line 2: what an alert is, no statement about its speed (row 14) |",
        "| 5 | retention: what n8n keeps | card line 3 (row 14; row 4 renumbers the pointer 'line 5' to 'line 3') |",
        "| 6 | not tested | card line 4 (row 14) |",
        "",
    ]
    text = sub(text, "\n\n| ID | Status | Target file", "\n\n" + "\n".join(AIDS) + "\n| ID | Status | Target file")
    # ------------------------------------------------------------ section 6
    text = sub(text, "THE GATE (row 8, item 11 of the rehearsal list on the run sheet):", "THE GATE (row 8, item 11 of the RISKS LIST on the run sheet):")
    text = sub(text, "row 8 item 11 says so", "row 8, risks list item 11, says so")
    # ------------------------------------------------------------ section 7
    text = sub(text, "| Row 6 item 14; NOT RUN |", "| Row 6, rehearsal list item 14; NOT RUN |")
    text = sub(text, "(gate, run sheet item 12)", "(gate, risks list item 12)")
    text = sub(text, "part 2: no such rule seen; FAIL: the studio lead may only write 'index not seen, accepted' on the run sheet, with UTC and IST time and name, as an allowance, not a pass; or the statement is not filmed; the studio lead writes 'index not seen, accepted' on the run sheet (ORD:151) or the statement is not filmed",
               "part 2: no such rule seen. FAIL means: scene 3 and card line 1 are not filmed, unless the studio lead writes 'index not seen, accepted' on the run sheet (risks list item 12; ORD:151) with UTC and IST time and his name, before the take and after telling the owner; that is an allowance, not a pass")
    # ------------------------------------------------------------ section 8 (replaced)
    s8 = text.index("## 8. Coverage")
    e8 = text.index("## 9. Not covered here")
    NEW8 = [
        "## 8. Coverage: finding -> fix -> where (every item of the two c6m reviews; the coverage of the c6l reviews is in REPORT-c6m.md section 8 and its fixes are still in force)",
        "",
        "| Review item | Fix | Where / check |",
        "|---|---|---|",
        "| Naive B1: the box used terms before they were explained (n8n, scene numbers, K3B and K3, the take, run sheet, rehearsal list, item numbers, wave 1, lane3, alert delay, Q21.2, re-smoke plan, 're-pin') | A seven-point plain preface before the table; the table cells are plain sentences; 're-pin' is defined in the preface and Words and glossary | Box; Words; glossary |",
        "| Naive M1: the answer line was not typeable (time label, IST, names, no example) | One exact line to copy, with UTC and IST, an explained list of names and a worked 'except' example | Box, 'How to answer' |",
        "| Naive M2: 'apply all defaults' hides consequences | Three lists: it does / it does not / you still have to (saving of every run, the unreviewed 45-second sentence, the checks, the builder and reviewers) | Box |",
        "| Naive M3: two gate lists collide; item numbers ambiguous; the contact-deletion check twice | The lists are named RISKS LIST (line 59) and REHEARSAL LIST (line 71); every item number says its list; the contact-deletion search exists only in row 8, and row 6 item 12 holds only the owner-sheet check | Words; rows 6, 8; glossary |",
        "| Naive M4: 'lead' with two meanings (rows 11, 13, 21, 22, 24, 37, 47) | In new texts and prose 'contact' and 'studio lead'; the one exact decision sentence keeps 'lead' and is explained | Rows 9, 11, 13, 21, 22, 24, 37, 41, 48, 49, 50, 54, 59; check script scan 'bare lead' |",
        "| Naive M5: 'alert' and 'lease' unexplained for a viewer; 'take' in a fourth sense | Row 14 line 2 says what an alert is; rows 13 and 21 say 'a setting called the lease' and 'keeps that contact reserved'; the plain sense of 'take' (a run took a contact) is written as 'reserved for the run that took it first' | Rows 13, 14, 21 |",
        "| Naive M6: the rule 'no timing number' contradicts the spoken 45 seconds | One sentence in Words: the video says no test result in seconds and does say the 45-second setting; rows 1 and 17 say 'no test result in seconds' | Words; rows 1, 17 |",
        "| Naive M7: rows 6 and 8 'ready' but depend on an unanswered question; no earliest date | READY defined (text can be applied; gate stays closed); 'You still have to' list; 'Earliest realistic date' says the audit cannot give one and what it depends on | Box; Words |",
        "| Naive M8: stop and continue rules ambiguous (row 6 item 13, row 23, gate 12 free exit, blank owner) | Section 3e: for each gate, who stops, who is told, may the take go on; gate 12 says who may accept, when and what happens otherwise; the gate owner is named in item 14; row 23 says the studio lead stops filming | Section 3e; rows 6, 8, 23 |",
        "| Naive m1: times without IST or without a time | UTC and IST in rows 6 and 23 and in 3d; example format given | Rows 6, 23; 3d; Words |",
        "| Naive m2: 'clean-up' with several meanings | Words: hiding a run, automatic removal (pruning); 'clean-up' only inside quoted file text | Words; rows 14, 23, 44, 50 |",
        "| Naive m3: box and section 3 disagree (L-SHEET; L-ONEDB changes nothing) | Same words in both for L-SHEET; L-ONEDB says no row of wave 1 depends on it | Box; section 3 |",
        "| Naive m4: section 5 unreadable | Section 5a lists the 12 rows a viewer sees in a short table | Section 5a |",
        "| Naive m5: row 1 new text is a note to the filmer, not a caption | The new text begins 'Scene 4 filming note (a note for the person filming; it is not a caption)' | Row 1 |",
        "| Naive m6: C-10c 'done on sheets' versus 'NOT RUN'; 'all 8 flow files'; L-CUT missing from 3d | C-10c part 2 named as the not-run part; row 62 says that only the 4 real-v5 files are edited; rows 63 to 69 share a short reason; L-CUT added to 3d | Section 0; rows 62 to 69; 3d |",
        "| Naive m7: three numberings of the card | Section 5b: old line, new line table | Section 5b |",
        "| Naive m8: developer words in the box | No setting names in the box; 'your answers of 2026-11-16 (Q21.2, Q22)'; 'the owner's choice of 2026-11-16' | Box |",
        "| Naive m9: are owner and studio lead two people? | Words: two roles, different jobs; no file says whether one human fills both | Words; glossary |",
        "| Naive 'could not follow': overlap with a voided run; why a 338.7 s run was voided; 'unique index seen'; 'the handoff' | Section 0 says the overlap is unchecked and not harmless, that a never-finished run could be a hidden failure and that nobody can say who voided it (needs-lead: ask lane3); gate 12 says how the index is seen (psql \\d mf_leads); the handoff is handoff\\SESSION-HANDOFF.md in the studio folder | Section 0; row 8; glossary; section 9 |",
        "| Design M1: 45 s measured from the first reply, not the first send | Rows 6 (item 13), 13, 21: counted from the first send, under 30 s (15 s margin), scene 2 must be shortened or the first send made late in it; source JF:97 | Rows 6, 13, 21; section 3e |",
        "| Design M2: 'two stores' is false (the stage journal is a third record) | L-ONEDB rewritten: no viewer-facing sentence on the number of stores until C-8 passes; then only 'one Postgres server, two databases' (Q21.3); rows 58 and 59 no longer wait for L-ONEDB | Section 3; rows 58, 59; table 3b |",
        "| Design m3: retention sentence assumes automatic removal is on (NS:42 says it was still being tested) | Rows 14 and 44: 'may stay'; we did not measure how long or whether the removal ever happens | Rows 14, 44 |",
        "| Design m4: rows 3 and 4 not tied to L-CARDTEXT and L-CARDCUT | Ties added; counts of table 3b regenerated and rechecked | Rows 3, 4; table 3b |",
        "| Design m5: contact-deletion check written twice | Kept only in row 8; row 6 item 12 holds the owner-sheet check and points to it | Rows 6, 8 |",
        "| Design m6: 'stale according to that answer' is the report's inference | Row 8: 'probably stale ... he confirms at the re-pin' | Row 8 |",
        "| Design m7: L-KILL default cites decision 8 as the cause | The default cites the missing flow results; decision 8 is named only as not the reason | Section 3, L-KILL |",
        "| Design m8: '18 runs' without both voided labels (report lines 52, 54, 113, 449) | Both labels named on those lines; the check script reads every line with '18 runs' | Section 0; section 2; verify-c6n-output.txt |",
        "| Design m9: C-10c box wording; 'lead verifies at re-pin' only in prose; rows 40 and 48 cite a file on another branch; row 6 item 14 depends on L-SAVE | C-10c says 'any mention of read-only'; rows 6 and 8 say 'the studio lead verifies at the re-pin'; rows 40 and 48 name the branch cloud/core-hardening; item 14 applies only if the flow files are edited (delete it otherwise) | Section 0; rows 6, 8, 40, 48 |",
        "",
    ]
    text = text[:s8] + "\n".join(NEW8) + "\n" + text[e8:]
    # ------------------------------------------------------------ section 9 additions
    text = sub(text, "- [needs-lead] Not reviewed: this report was written and checked by me alone;",
               "- [needs-lead] Ask the lane3 session why VOID-fl45k3b (338.7 s, never reached a final state) and VOID-fl45k6c (stand-in services not up) were voided, and whether the 5 kept runs that overlapped VOID-fl45k3b were disturbed. Next step: the studio lead asks lane3 for its raw notes; until then statement 20 (row 39) discloses both voided runs and the overlap.\n"
               "- [needs-lead] Spoken length of the closing card (section 0): the stopwatch run (rehearsal list item 10) decides whether the card text is shortened or the card time raised.\n"
               "- [needs-lead] Not reviewed: this report was written and checked by me alone;")
    return text

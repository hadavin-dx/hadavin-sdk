# Section patches for REPORT-c6o.md. Executed by build_c6o.py with names: sub, rows, cnt, fl, D, ready, onlyq, withc, nofilm, NROWS in scope.
# Every patch asserts exactly one match (sub) or an exact line start (replace_line).
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


def delete_line(text, startswith):
    ls = text.split("\n")
    idx = [i for i, l in enumerate(ls) if l.startswith(startswith)]
    assert len(idx) == 1, (startswith, len(idx))
    del ls[idx[0]]
    return "\n".join(ls)


def card_words():
    # spoken words of the closing card as the rows now stand (row 13 holds only the plain statement; the lease sentence is open)
    ws = []
    for k in (13, 14):
        for q in re.findall(r'spoken: "([^"]*)"', rows[k]["new"]):
            ws.append(len(q.split()))
    return ws


# Option (a) of L-CARDLEN: the cut spoken text (each line plain words; counted below)
CUT = [
    "A lead sent twice with the same id is processed once.",
    "When the system cannot tell whether a contact was fully handled, it sends one alert asking a person to look.",
    "The made-up name and e-mail address sent to n8n may stay in n8n's own database; we did not measure for how long.",
    "Not tested: other mailboxes, other CRMs, chat alerts, other lease settings. One machine, made-up people, our own runs.",
]


def patch_sections(text):
    # ---- names of this version's files
    text = text.replace("run sheet line 59", "run sheet line 49").replace("run sheet line 71", "run sheet line 61")
    text = text.replace("the independent review of 11:00 UTC found no", "the independent review of 11:00 UTC (16:30 IST) found no").replace("was still being edited at 15:05 UTC;", "was still being edited at 15:05 UTC = 20:35 IST;")
    text = text.replace("evidence-c6n/", "evidence-c6o/").replace("verify-c6n-output.txt", "verify-c6o-output.txt").replace("verify-c6n.py", "verify-c6o.py")
    text = text.replace("REPORT-c6n.md", "REPORT-c6o.md").replace("box_c6n.md", "box_c6o.md")
    text = sub(text, "# REPORT-c6n: video audit fix pass, supersedes REPORT-c6m.md (2026-11-16, UTC; IST = UTC + 5:30)",
               "# REPORT-c6o: video audit fix pass, supersedes REPORT-c6n.md (2026-11-16, UTC; IST = UTC + 5:30)")
    W = card_words()
    CW = [len(c.split()) for c in CUT]
    # ------------------------------------------------------------------ box
    n_ready, n_onlyq, n_withc, n_nofilm = len(ready), len(onlyq), len(withc), len(nofilm)
    n_wave1 = n_ready + n_onlyq
    text = sub(text, "The edit table (section 5) holds 72 proposed text changes. Each has its old text, its new text and what a person watching the video sees. 35 are 'ready' (the text can be applied now), 34 wait for your answer to a question, and 3 wait for a check that needs n8n running.",
               "The edit table (section 5) holds %d proposed text changes. Each has its old text, its new text and what a person watching the video sees. %d are 'ready' (the text can be applied now), %d apply on the default of a question you have not answered, %d wait for a check that needs n8n running, and %d (rows %s) are NOT FILMABLE: they wait for your answer to L-LEASE and have no default." % (NROWS, n_ready, n_onlyq, n_withc, n_nofilm, fl(nofilm)))
    text = sub(text, "Seven things you need before you read the table", "Words used before the explanations below (one meaning each): GATE = a step on the run sheet that blocks the take until a named person has written a result on the run sheet; it is a stop sign, not a check that runs by itself. RE-PIN = the moment when the studio lead puts together the final version of the take files and reads them again. MONEY STOP = Mon 23 Nov 2026 18:29 UTC = 23:59 IST, after which the paid model key must not be used; the owner cancels the key by 18:19 UTC = 23:49 IST. THE POST = the post about the video that is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (the studio lead's answer Q21.1). CLAIM = the table row that says 'this contact is being handled' (the claim row, or claim table); the files also use 'claim' for a sentence in the video, which this report calls a STATEMENT. TAKE = the one filmed run of the video. EST COLUMN = the column of the run sheet that gives the planned seconds of each scene.\n\nSeven things you need before you read the table")
    # questions table in the box: L-LEASE row and the two new questions
    lease_old = [l for l in text.split("\n") if l.startswith("| L-LEASE | Say on the closing card and in the scene 3 caption")]
    assert len(lease_old) == 1
    text = replace_line(text, "| L-LEASE | Say on the closing card and in the scene 3 caption",
        "| L-LEASE | WHICH honest sentence about the 45-second setting is spoken on the closing card and in the scene 3 caption? Reading 1 (the one in ORDERS.md Q21.2): a second send is processed once only within the lease. Reading 2 (what the flow files show, section 3): a second send is refused at ANY time while its row exists; the lease only decides when the recovery flow may take over a contact that is not finished. Answer 1, 2 or none. | NO DEFAULT. Rows 13 and 21 are NOT FILMABLE until you answer. | studio lead |")
    text = insert_after_line(text, "| L-CARDTEXT | Use the new spoken card lines 2 to 4", [
        "| L-CARDLEN | The four spoken card lines hold %d words (about %d s at 150 words a minute) but the run sheet budgets the card 30 s. Which way: (a) cut the spoken text to about %d words (the cut text is in section 3: total of the video about 180 s), or (b) keep the text and give the card about 60 s (total about 210 s)? | (a) cut. Row 11 writes no total for the card either way: its time is 'EST not measured' until the stopwatch run. | studio lead |" % (sum(W), round(sum(W) / 2.5), sum(CW)),
        "| L-SCENES | Restructure scenes 2 and 3 so that the repeat send comes straight after the first reply and the evidence (CRM list 1 row, mailbox 1 mail) is shown once, at the end of scene 3? Effect: scene 2 about 25 s instead of 40 s and scene 3 about 40 s instead of 25 s (scenes 2 and 3 still add to 65 s; these seconds are estimates, not measured); the gap between the two sends falls from about 40 s or more to about 15 s. | No, the scenes stay as they are. | studio lead |"])
    text = sub(text, "| L-KILL | Say anything in scene 4 about the two crash tests K3B and K3? | No. | studio lead |", "| L-KILL | Say anything in scene 4 about the two crash tests K3B and K3? | No. | studio lead |")
    # apply all defaults: the three lists
    text = sub(text, "and four new blocking checks on the run sheet; no reviewer has read these new texts yet.",
               "and six new blocking steps on the run sheet (rehearsal list items 11 to 16 and risks list items 11 and 12 add up to eight items; the six that block are the active-flows list, the owner-sheet check, the repeat-send check, the saved-runs gate, the contact-deletion gate and the repeat-send rule gate; items 15 and 16 are the second leak scan and the after-the-take deletion); no reviewer has read these new texts yet. NOTE: it does NOT put the lease sentence on the card or the caption (L-LEASE has no default). WHO SETS n8n's two saving values: apply-all-defaults edits only the notes file N8N-START.md (rows 55 and 56) and the four flow files plus their generator (rows 62 to 69 and 92); it does not change any running n8n. The studio lead (or the builder he names) sets EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=all in the environment that starts n8n, and the flow-file settings apply when the files are imported; which of the two wins is not verified (the import check C-4 shows it). The exposure is the same as today's for the request body (n8n already keeps it for any run it saves); 'all' adds the data every step passes on. The real new risk is a secret typed into a form field (row 22).")
    text = sub(text, "(1) the named builder applies wave 1, 69 rows (section 3c lists them), to 9 files, by text, in table order, and writes the list of applied row numbers to a file next to this report.",
               "(1) the named builder applies wave 1, %d rows (section 3c lists them), to 10 files (the 9 files of c6n and the flow generator build_mainframe.py), by text, in table order, and writes the list of applied row numbers to the file c6o-APPLIED-ROWS.md next to this report." % n_wave1)
    text = sub(text, "- IT DOES NOT: apply the 3 rows that wait for a check (23, 58, 59);", "- IT DOES NOT: apply the 3 rows that wait for a check (23, 58, 59); apply the %d NOT FILMABLE rows (%s) until you answer L-LEASE; decide L-CARDLEN or L-SCENES (the defaults keep the scenes and cut the card text only if L-CARDLEN default (a) is applied by a builder from the cut text in section 3);" % (n_nofilm, fl(nofilm)))
    text = sub(text, "the 69 rows that need no check (35 ready rows and 34 rows that wait only for a question). Wave 2 is the 3 rows that wait for a check.", "the %d rows that need no check (%d ready rows and %d rows that wait only for a question). Wave 2 is the %d rows that wait for a check. %d more rows are NOT FILMABLE until L-LEASE is answered." % (n_wave1, n_ready, n_onlyq, n_withc, n_nofilm))
    text = sub(text, "The builder is the agent that applies the 69 rows.", "The builder is the agent that applies the %d wave 1 rows." % n_wave1)
    text = sub(text, "`## ANSWER (lead, 2026-11-16T16:40Z = 22:10 IST): c6n apply all defaults to REPORT-c6o.md; builder: builder-1; reviewers: egm-design, egm-comprehension`",
               "`## ANSWER (lead, 2026-11-16T16:40:00Z = 22:10:00 IST): c6o apply all defaults to REPORT-c6o.md; builder: builder-1; reviewers: egm-design, egm-comprehension; L-LEASE: (write 1, 2 or none: this line has no default for it)`")
    text = sub(text, "Replace the time with the real time (type date -u +%FT%TZ for UTC; IST = UTC + 5:30)", "Replace the time with the real time: type date -u +%FT%TZ, which prints UTC with seconds (for example 2026-11-16T16:40:00Z), and add 5 hours 30 minutes by hand for IST (22:10:00)")
    text = sub(text, "To change one default, add after the names: `; except L-KILL: b`", "REPLY FORM FOR EVERY QUESTION (what you may write after 'except', one form each): L-CARD yes or no; L-CARDCUT yes or no; L-CARDTEXT yes or no; L-CARDLEN a or b; L-LEASE 1, 2 or none (the only question without a default: write it every time); L-KILL a or b; L-APPROX yes or no; L-SAVE yes or no; L-PAGE yes or no; L-ONEDB yes or no; L-SCENES yes or no; L-DEL no reply needed; L-CUT yes or no; L-SHEET cannot be put on this line (only the owner knows; write it as a separate line in ORDERS.md: `## ANSWER (owner via lead, time): L-SHEET v25A`). To change one default, add after the names: `; except L-KILL: b`")
    text = sub(text, "EARLIEST REALISTIC DATE: the audit cannot give one.", "EARLIEST REALISTIC DATE: the audit cannot give one, and it corrects the c6n sentence that listed only some steps: the steps are the answer line, the builder applying the rows, the two reviewers reading the changed files, the loopback re-smoke, the import check C-4, the leak scan (a program that still has to be written), the re-pin and the reading of the take script, asking the owner two facts (L-SHEET, the key scope), the first rehearsal, and the stopwatch run (rehearsal list item 10).")
    # ------------------------------------------------------------------ section 0
    text = replace_line(text, "- THE LAST REPORT (REPORT-c6m.md) FAILED TWO INDEPENDENT REVIEWS",
        "- THE LAST REPORT (REPORT-c6n.md) FAILED INDEPENDENT REVIEW AND AN INDEPENDENT CHECK: review-c6n-design.md (8 majors, 7 minors), review-c6n-naive.md (1 blocker, 11 majors, minors) and evidence-c6n-independent/00-SUMMARY.md (its check script never failed whatever it found: the faults '60.1 to 61.9' wrong, the split of the kept runs wrong and a single IST change were not detected; the closing card text needs about 58 s against a 30 s budget). This report (c6o) fixes every item, or labels it [needs-lead], [needs-owner] or [impossible-now] in section 9 with the exact question (section 8: finding, fix, where). THIS REPORT HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them).")
    text = insert_after_line(text, "- THE LAST REPORT (REPORT-c6n.md) FAILED INDEPENDENT REVIEW", [
        "- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE (my own, found by the c6n reviews): (1) THE REPEAT-SEND SENTENCE WAS NOT SUPPORTED: rows 13 and 21 said a second send counts as processed once only within 45 s, while the flows show something else (row 13 gives the reading: the contact table's primary key on the contact id refuses a second row at any gap; the 45 s lease only decides when the recovery flow may take over a contact that is not finished: mf-recovery.json line 26). The studio lead's own reading in ORDERS.md Q21.2 ('no takeover after expiry') does not match that file line. Rows 13 and 21 are now NOT FILMABLE until L-LEASE is answered, and the exit 'index not seen, accepted' is removed from risks list item 12. (2) Row 11 wrote a total of 180 s that its own reason said was probably false; it now says 'EST not measured' for the card (L-CARDLEN gives two ways to make the total true). (3) My check script printed results and never failed; the new script evidence-c6o/verify-c6o.py ends with a non-zero exit code on any failed check, and its 17 negative controls are rerun with raw output (section 7). (4) I wrote 'index not seen, accepted' as an allowed exit in c6n; it is gone. (5) The c6n box said four new blocking checks; the rows add six blocking steps and two more items (box).",
        "- ONE PIECE OF EVIDENCE I COULD NOT RECONCILE: the independent summary says '17 negative controls', and its folder holds 18 changed copies plus one unchanged control copy (V0). I report both numbers and rerun all of them (section 7).",
        "- SPOKEN LENGTH OF THE CLOSING CARD, STILL NOT TESTED: with the rows as they stand the spoken card text holds %d words (counted by evidence-c6o/verify-c6o.py) before the lease sentence; the c6n card held 144 words (about 58 s at 150 words a minute) against the 30 s budget. L-CARDLEN gives two ways (section 3); no stopwatch run exists." % sum(W)])
    # old c6n 'spoken length' bullet replaced by the line above
    text = delete_line(text, "- SPOKEN LENGTH OF THE CLOSING CARD, NOT TESTED (new in this version;")
    ls0 = [l for l in text.split("\n") if l.startswith("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.")]
    assert len(ls0) == 1
    text = replace_line(text, "- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.", "- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every row says NOT APPLIED. Of the %d rows (rows 1 to 72 keep the numbers of REPORT-c6n.md; rows 73 and up are new in c6o, and rows 1, 33 and 39 were split): %d are 'ready' (no open question and no open check; rows %s); %d apply on the default of a question you have not answered (section 3); %d wait for a check that needs n8n (rows %s); %d are NOT FILMABLE until you answer L-LEASE (rows %s). The counts per question are made by a script and checked by a second script that fails on any difference (section 3, table 3b; section 7)." % (NROWS, n_ready, fl(ready), n_onlyq, n_withc, fl(withc), n_nofilm, fl(nofilm)))
    # ------------------------------------------------------------------ section 1 ids
    text = sub(text, "the row numbers are the same as in REPORT-c6l.md and REPORT-c6m.md.", "the row numbers 1 to 72 are the same as in REPORT-c6l.md, REPORT-c6m.md and REPORT-c6n.md; rows 73 and up are new in c6o; the table lists the rows file by file, the lowest line first within a file's group REVERSED (highest line first) so that the lines of the file do not move while the rows are applied.")
    # ------------------------------------------------------------------ section 3: questions
    text = replace_line(text, "| L-LEASE | studio lead (his answers Q21.2",
        "| L-LEASE | studio lead (his answers Q21.2 at ORD:151 and Q22 at ORD:186 ask for an honest sentence on the lease; they do not say which) | Which sentence about the 45-second setting may the closing card and the scene 3 caption carry? READING 1 (ORD:151: 'a gap longer than the lease is not claimed', the c6n text): 'We say this only when the second send comes within 45 seconds of the first send.' The flow files do NOT show that: a second send with the same id is refused at any time (primary key on the contact id, MF:45 and mf_leads.sql line 5; the row is written with ON CONFLICT DO NOTHING, mf-form.json line 97; the repeat is answered from the stored row, mf-form.json lines 270 and 298). READING 2 (what the flow files show; the sentence still needs the rehearsal to show the repeat reply): 'The 45 seconds is a setting called the lease: it decides only when the recovery flow may take over a contact that is not finished; a second send of the same contact is refused at any time.' OR none: no lease sentence at all (the plain statement only). Also settle: ORD:151 says 'no takeover after expiry'; mf-recovery.json line 26 (ClaimStuck: claim time passed, state not done, review, unknown or failed, fewer than 3 attempts) DOES take a contact over after expiry. | NO DEFAULT. Rows 13 and 21 are NOT FILMABLE until the studio lead writes 1, 2 or none. | No | 1: the rows are re-issued with the reading 1 sentence AND a check that the repeat send after 45 s is refused (not run: needs the take's database), and risks list item 12 stays. 2 or none: the rows are re-issued with the chosen sentence. | %s |" % fl(cnt["L-LEASE"]))
    text = insert_after_line(text, "| L-LEASE | studio lead (his answers Q21.2", [
        "| L-CARDLEN | studio lead | Closing card length. The spoken text with the lease sentence open holds %d words now (the c6n text with the lease sentence held 144, about 58 s at 150 words a minute); the run sheet gives the card 30 s. OPTION (a): cut the spoken text to %d words (about %d s): line 1 '%s'; line 2 '%s'; line 3 '%s'; line 4 '%s' (the lease sentence, when answered, adds its own words; with reading 2 about 25 more). OPTION (b): keep the text and budget the card about 60 s: the video then adds to 25 + 40 + 25 + 60 + 60 = 210 s. | (a), applied by the builder as an extra step only after you write 'L-CARDLEN: a'; without an answer rows 11, 13, 14 keep the c6n card text and say 'EST not measured'. | No | (b): row 11 is re-issued with 60 s and total 210 s; rows 13 and 14 stay. | 11, 13, 14, 86 |" % (sum(W), sum(CW), round(sum(CW) / 2.5), CUT[0], CUT[1], CUT[2], CUT[3]),
        "| L-SCENES | studio lead | Restructure scenes 2 and 3: first send and reply in scene 2 (about 25 s), the repeat send straight after it, then the evidence (CRM list 1 row, mailbox 1 mail) shown once in scene 3 (about 40 s instead of showing it twice)? Scenes 2 and 3 still add to 65 s (estimates, not measured). The gap between the two sends falls from about 40 s or more to about 15 s. Why it is asked: rehearsal list item 13 (c6n) could not be followed with the 40 s of scene 2 (c6n naive review M4). | No: the scenes stay; item 13 only writes the gap down. | No | Yes: the studio lead names a builder who re-issues the rows of scenes 2 and 3 on the run sheet (lines 31 and 32; this report does not contain them). | none (rows to be issued) |"])
    # 3c
    text = replace_line(text, "3c. 'APPLY ALL DEFAULTS': what it does is in the box at the top.",
        "3c. 'APPLY ALL DEFAULTS': what it does is in the box at the top. Rows it applies: the %d ready rows (%s) and the %d rows that wait only for a question (%s), %d rows in all, in the files VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, N8N-START.md, mf.py, mf-form.json, mf-hook.json, mf-recovery.json, mf-sub-crm-mail.json, DECISION-one-store.md and build_mainframe.py. Rows 6 and 8 are in the ready rows: their text can be applied now, but the gates they add stay closed until the studio lead writes the lines they ask for (Words: READY). Rows it does not apply: 23, 58, 59 (wait for a check) and %s (NOT FILMABLE until L-LEASE). What changes in content: the closing card gets four spoken lines WITHOUT the lease sentence; scene 4 has no kill-case words and no rounded timing wording; the take saves every run (flow-file rows, the generator, saving notes); statements 19 and 20 are marked not for the web page; DECISION-one-store.md gets the target wording marked as a target." % (n_ready, fl(ready), n_onlyq, fl(onlyq), n_wave1, fl(nofilm)))
    # 3e: repeat-send rule gate
    text = replace_line(text, "| Repeat-send rule seen (risks list item 12)",
        "| Repeat-send rule seen (risks list item 12) | the table rule on the contact id is seen in the take's own database AND L-LEASE is answered | studio lead | the owner, if scene 3 is cut | Only without scene 3 and card line 1. There is no exit 'index not seen, accepted' any more (c6n naive review B1) |")
    text = replace_line(text, "| Repeat-send timing (rehearsal list item 13)",
        "| Repeat-send check (rehearsal list item 13) | both clock times and the repeat reply are written; the repeat reply says the repeat flag is true; CRM 1 row; test mailbox 1 mail | the person who sees it; the studio lead decides | the owner, if the take is affected | In a rehearsal: redo scene 3 (or choose L-SCENES). In the take: stop; the studio lead decides whether to film again (a second take needs the owner's spend limit to cover it: the studio lead computes the retake count, Q21.4) |")
    # ------------------------------------------------------------------ section 7 checks
    text = replace_line(text, "| C-9 | The repeat-send statement is backed",
        "| C-9 | The repeat-send statement is backed by a unique rule on the claim table (gate, risks list item 12) | part 1 me (static); part 2 studio lead | part 1: a primary key or unique index on the contact id in the test program and an ON CONFLICT insert in the entry flows; part 2: the same rule seen in the take's own table (psql \\d mf_leads) | part 2: no such rule seen. FAIL means: scene 3 and card line 1 are NOT filmed. There is no allowance (the c6n exit 'index not seen, accepted' is removed) | part 1 DONE (static) PASS: MF:45, n8n-flows-v4/mf_leads.sql line 5 and ON CONFLICT in mf-form.json line 97 (evidence-c6o/static-checks-output.txt); part 2 NOT RUN; missing input: the take's database after the re-smoke (needs-lead) |")
    text = replace_line(text, "| C-10b | Take script:",
        "| C-10b | Take script at the final version: read EVERY line that sends a request to the customer list (HubSpot), with line number, method and path, and answer Q27 (a), (b), (c) with line numbers (ORDERS.md Q27; (a) go marker before spending, (b) end-date refusal, (c) key cancelled mid-run and the exit code); the searches for the words archive and delete are additional, not enough alone; also the old desk test program and the probe script named, not used by the take | studio lead at the re-pin (ORDERS.md Q23 and Q27) | the take script sends no request that deletes or archives; (b) is shown | any other call, or (b) not shown: STOP (no take on or after Mon 23 Nov 2026) | NOT RUN, UNVERIFIED; missing input: the script is not in the checked files (needs-lead) |")
    # ------------------------------------------------------------------ section 9
    text = delete_line(text, "- [needs-lead] Run sheet lines 30 and 52 still say 'the request body stays in n8n data until pruned'")
    text = sub(text, "- [needs-lead] Not reviewed: this report was written and checked by me alone;", "- [needs-lead] L-LEASE (two readings, section 3), L-CARDLEN (two options), L-SCENES (restructure of scenes 2 and 3): each needs the studio lead's answer; rows 13 and 21 are NOT FILMABLE until L-LEASE is answered.\n- [needs-lead] Run the generator-versus-JSON comparison of row 92 after the builder applies rows 62 to 69 and 92: I did not run it (the audited tree is read only and the generator needs its arguments from the V5 README).\n- [needs-owner] What the owner's HubSpot key may do (Q20 item 3): UNVERIFIED, no text says 'read-only' or 'cannot archive' until he confirms.\n- [impossible-now] Whether the unique rule on the contact id exists in the take's own database: only the loopback re-smoke can show it (C-9 part 2).\n- [needs-lead] Not reviewed: this report was written and checked by me alone;")
    text = sub(text, "## 8. Coverage: finding -> fix -> where (every item of the two c6m reviews;", "## 8. Coverage: finding -> fix -> where (first the c6n reviews, the table directly below; then every item of the two c6m reviews;")
    cov = [
        "",
        "COVERAGE OF THE c6n REVIEWS (review-c6n-design.md, review-c6n-naive.md, evidence-c6n-independent/00-SUMMARY.md):",
        "",
        "| Review item | Fix | Where / check |",
        "|---|---|---|",
        "| Naive B1 (repeat-send sentence has two justifications; 'index not seen, accepted') | rows 13 and 21 carry only the plain statement and are NOT FILMABLE until L-LEASE; the flow reading is in row 13; the exit is removed | rows 13, 21, 8 (item 12), C-9, section 3 L-LEASE, 3e |",
        "| Design M1, naive M3 (row 11 known-false total) | row 11 gives 150 s for scenes 1 to 4 and 'EST not measured' for the card; two options with numbers | row 11, L-CARDLEN |",
        "| Design M2 (scenes 2 and 3 restructure) | question L-SCENES with the effect on the 40 s and 25 s budgets | section 3 |",
        "| Design M3, naive M1 (sped up label, RS:32, 45 s carve-out) | label added to rows 1 and 17; carve-out in rows 2, 5, 15, 19, 30, 34; RS:32 rows 93 and 94 | rows 1, 2, 5, 15, 17, 19, 30, 34, 93, 94 |",
        "| Design M4 (L-CARDTEXT ties; splits; 3b; builder notes and blank) | rows 15, 20, 29, 31 tied; rows 1, 33, 39 split (1/73/74, 33/75, 39/76); 3b recomputed; blank and builder text removed from row 6 | rows 1, 6, 15, 20, 29, 31, 33, 39, 73 to 76, table 3b |",
        "| Design M5, naive M5 (row 8, C-10b, Q23, Q27, key scope, made-up contacts) | rewritten; (a), (b), (c); every request line to be read; key scope UNVERIFIED | rows 8, C-10b |",
        "| Design M6 (n=2) | rows 47, 77, 78, 79, 80 | RES:85 |",
        "| Design M7 (residual lines) | rows 81 to 91; the words 'two stores' and 'three stores' are not used | rows 81 to 91 |",
        "| Design M8 (second leak scan, after-take deletion, generator rule) | rows 6 (items 15, 16), 92, 62 to 69 | rows 6, 62 to 69, 92 |",
        "| Naive M2 to M11 and minors (glossary, six checks, apply-all-defaults, reply line, reply forms, earliest date, run-sheet line numbers) | box rewritten; glossary words added at the top of the box; the run-sheet headings are at lines 49 and 61 (the c6n report wrongly gave 59 and 71, which are item 10 of each list) | box, section 1 |",
        "| Independent summary (check script never fails; 60.1 to 61.9, the split of the kept runs and one IST change undetected; 58 s card) | evidence-c6o/verify-c6o.py exits non-zero on any failed check and has the new checks; the 17 (18 plus control) negative controls rerun; card in L-CARDLEN | section 7, evidence-c6o/neg-output.txt |",
        "",
    ]
    ls = text.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith("## 8. Coverage")][0]
    ls[i + 1:i + 1] = cov
    text = "\n".join(ls)
    gl_rows = [
        "| L-CARDLEN, L-SCENES | the two new questions of c6o (section 3): the length of the closing card, and the restructure of scenes 2 and 3 | c6n design review M1, M2 |",
        "| gate | a step on the run sheet that blocks the take until a named person has written a result with the time in UTC and IST; a stop sign written on the sheet, not a program | c6n naive review minors |",
        "| NOT FILMABLE | status of a row whose text may not be filmed or applied until the studio lead has answered a question that has no default (rows 13 and 21, question L-LEASE) | c6n naive review B1 |",
        "| money stop, the post, re-pin, claim, take | defined in the first paragraph of the box at the top of this report | c6n naive review minors |",
    ]
    text = insert_after_line(text, "| L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE, L-KILL", gl_rows)
    # ------------------------------------------------------------------ section 3 rows-tied column
    tied = {t: (fl(cnt[t]) if t in cnt else "none") for t in ["L-CARD", "L-CARDCUT", "L-CARDTEXT", "L-LEASE", "L-CARDLEN", "L-KILL", "L-APPROX", "L-SAVE", "L-PAGE", "L-ONEDB"]}
    s3 = text.index("## 3. Questions")
    e3 = text.index("3b. Count of rows per question")
    sec3 = text[s3:e3].split("\n")
    for i, l in enumerate(sec3):
        m = re.match(r"^\| (L-[A-Z]+)( \(was [^)]*\))? \|", l)
        if m and m.group(1) in tied and len(l.split(" | ")) >= 7:
            cells = l.rstrip(" |").split(" | ")
            cells[-1] = tied[m.group(1)]
            sec3[i] = " | ".join(cells) + " |"
    text = text[:s3] + "\n".join(sec3) + text[e3:]
    return text

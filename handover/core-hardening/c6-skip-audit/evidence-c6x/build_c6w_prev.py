"""Builds ../REPORT-c6w.md from ../REPORT-c6v.md (read only, never changed). Every patch asserts its match count; a miss stops the build.
Usage: python3 -B -I build_c6w.py   (run_all.sh runs static-checks, this file, the verifier, the negative controls and the scan in that order).
Box counting rule (as in c6v): the words of the start box are counted from the first line AFTER its heading to the line before the heading of part 2."""
import re, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE) + "/"
E = HERE + "/"
FAILS = []
OLDCT = "2026-11-16T19:04:44Z"


def sub(t, old, new, c=1):
    n = t.count(old)
    if (c is not None and n != c) or (c is None and n == 0):
        FAILS.append("expected %s match(es), found %d: %r" % (c, n, old[:120]))
        return t
    return t.replace(old, new)


def rsub(t, pat, new, c=1, flags=re.S):
    ms = list(re.finditer(pat, t, flags))
    if len(ms) != c:
        FAILS.append("regex expected %d match(es), found %d: %r" % (c, len(ms), pat[:100]))
        return t
    return re.sub(pat, lambda m: new, t, flags=flags)


def row_idx(L, k):
    c = [i for i, l in enumerate(L) if l.startswith("| %d | NOT APPLIED" % k)]
    assert len(c) == 1, k
    return c[0]


def edit_row_text(t, k, old, new, c=1):
    L = t.split("\n")
    i = row_idx(L, k)
    n = L[i].count(old)
    if n != c:
        FAILS.append("row %d: expected %d match(es), found %d: %r" % (k, c, n, old[:100]))
        return t
    L[i] = L[i].replace(old, new)
    return "\n".join(L)


def build(words):
    t = open(D + "REPORT-c6v.md", encoding="utf-8").read()
    # ---- 0. file-name tokens of the current report move to c6w; narrative 'c6v' stays (it is history). The proof file name verify-c6v-on-c6u.txt stays.
    t = t.replace("the line-by-line mapping is in c6v-CHANGES.md", "@@V-MAP@@")
    t = re.sub(r"\b(REPORT-|evidence-|verify-|verify_|scan_|neg_new_|neg_controls_|ctime_|census-)c6v(?!-on-c6u)", r"\1c6w", t)
    t = t.replace("c6v-APPLIED-ROWS.md", "c6w-APPLIED-ROWS.md").replace("c6v-CHANGES.md", "c6w-CHANGES.md").replace("@@V-MAP@@", "the line-by-line mapping is in c6v-CHANGES.md")
    # the c6v failure bullet is history now: its own file names stay c6v
    t = sub(t, "- FAILURES FIRST IN c6v (my own, still open when I wrote this): (1) no EGM reviewer has read REPORT-c6w.md or the new checks",
            "- FAILURES FIRST IN c6v (history; c6v FAILED INDEPENDENT REVIEW, see section 8; its own list as I wrote it then): (1) no EGM reviewer had read REPORT-c6v.md or the new checks")
    t = sub(t, "(3b) While I worked, another session wrote a newer release note (v18) and owner sheet. Against v14, release note lines 33 and 150 are the same;", "(3b) While I worked, another session wrote a newer release note (v18) and owner sheet. Against v14, release note lines 33 and 150 are the same (lines 8 and 149 differ);")
    # ---- 1. check time: the c6v time is replaced by the time of the last static-checks run
    ct = re.search(r"check time \(UTC\): (\S+)", open(E + "static-checks-output.txt", encoding="utf-8").read()).group(1)
    dt = datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ")
    ist = lambda x: (x + datetime.timedelta(hours=5, minutes=30))
    old_dt = datetime.datetime.strptime(OLDCT, "%Y-%m-%dT%H:%M:%SZ")
    t = t.replace(OLDCT + " = " + ist(old_dt).strftime("%H:%M:%S") + " IST", ct + " = " + ist(dt).strftime("%H:%M:%S") + " IST")
    t = t.replace(old_dt.strftime("%H:%M:%S") + " UTC = " + ist(old_dt).strftime("%H:%M:%S") + " IST", dt.strftime("%H:%M:%S") + " UTC = " + ist(dt).strftime("%H:%M:%S") + " IST")
    t = t.replace(OLDCT, ct)
    sys.path.insert(0, E)
    import ctime_c6w
    oe1, oi1, oe2, oi2 = ctime_c6w.example_times(OLDCT)
    ne1, ni1, ne2, ni2 = ctime_c6w.example_times(ct)
    t = sub(t, "%s = %s IST" % (oe1, oi1), "%s = %s IST" % (ne1, ni1), 1)
    t = sub(t, "%s = %s IST" % (oe2, oi2), "%s = %s IST" % (ne2, ni2), None)

    # ---- 2. title, answer line (design B1, naive B1)
    t = sub(t, "# REPORT-c6w: video audit fix pass, supersedes REPORT-c6u.md (", "# REPORT-c6w: video audit fix pass, round 5 of the edit-row report, supersedes REPORT-c6v.md (", 1)
    t = sub(t, ": c6u apply all defaults to REPORT-c6u.md; builder: builder-A;", ": c6w apply all defaults to REPORT-c6w.md; builder: builder-A;", 1)
    t = sub(t, "The names are labels no program reads; the reviewers are review agents (EGM = the studio's review method), not people; the ORDER of the two reviewer names matters: B checks facts and risk, C reads as a stranger.",
            "The line must name this report: the word before 'apply all defaults' is c6w and the file is REPORT-c6w.md (the check script compares both with the file name). The names after 'builder' and 'reviewers' are labels no program reads; the reviewers are review agents (EGM = the studio's review method), not people; reviewer-B checks facts and risk, reviewer-C reads as a stranger.", 1)

    # ---- 3. box step 1 shorter, one meaning, no undefined label (design B1/M5, naive M2, M9, m1)
    s1 = ("1. WHAT THE LINE OF STEP 2 DOES. A builder applies the 95 rows of WAVE 1 (defined below) to the demo files, by text, in table order. Where: the builder works in a checkout of branch cloud/flows-audit, folder handover/, which holds 90 of the 95 rows' files; 5 rows edit inputs/DECISION-one-store.md, which exists only on branch cloud/core-hardening (rows 70, 71, 72, 90, 91). The builder writes the list of applied rows to c6w-APPLIED-ROWS.md on branch cloud/core-hardening (folder handover/core-hardening/c6-skip-audit/), and each branch gets its own commit. "
          "The old texts were checked only against a copy in a scratchpad folder (shipped in evidence-c6w/tree/); that the copy equals the real files is UNVERIFIED (99 of the 104 rows name files that branch cloud/core-hardening lacks), so the builder first confirms that each old text occurs once in the real file and stops at any row where it does not.\n"
          "WHAT THE LINE DOES NOT DO: it answers none of the five OPEN items; does not approve G12; runs no check; spends nothing; imports nothing into n8n; does not start the filmed run; writes no card line about the owner's HubSpot key (its scope is unconfirmed); puts no sentence about the 45-second setting into any document; leaves unapplied the 3 rows that wait for a check and the 6 that wait for the owner.")
    t = rsub(t, r"1\. What the line in step 2 does NOT do:.*?\n(?=2\. Add this ONE line)", s1 + "\n", 1)
    t = sub(t, "The G12 approval goes on the run sheet gate (risks list item 12, row 8) with UTC and IST time.", "The G12 approval is ONE line in ORDERS.md (form in the WORDS list, item G12), written only after the loopback re-smoke of TASK (5) has put its results on the run sheet.", 1)

    # ---- 4. defaults leave the card whole; no hand cut in the defaults (design M3, naive M4)
    t = sub(t, "The video is NOT yet filmable. Without G12 the builder cuts them BY HAND when you tell him (section 1c) and sets the card's Time cell to match (row 96).",
            "The video is NOT yet filmable. The defaults cut nothing by hand: rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and row 96 sets the card's Time cell to the same 40 s; the gate, not a row, keeps card line 1 and the caption off the film until G12 is approved (shorter cases: Table B in section 1c; each of them would need a hand edit and a further round).", 1)
    t = sub(t, "the builder cuts them BY HAND", "the builder cuts them BY HAND", 0) if False else t
    t = sub(t, "(row 96 edits it, tied to L-CARDLEN, so the hand edit is gone for the defaults)", "(row 96 edits it, tied to L-CARDLEN, so the hand edit is gone for the defaults)", 0) if False else t

    # ---- 5. G12: one form, one place, one order (design M1, naive B2, M1)
    g12_old = rsub(t, r"- GATE = a run sheet step that blocks the take until a named person writes a result on it\. G12 = YOUR gate.*?\n(?=- TABLE RULE ON THE CONTACT ID)", "@@G12@@\n", 1)
    g12_new = ("- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 = YOUR approval, the row of release note v14 line 33 (LRN14:33): '| G12 | Claims: the one sentence, the ban list of section 5 decided (the lease sentence is out of the public post, lead answer Q22c) | sentence in writing | sentence missing |'. "
               "It is OPEN: I do not approve it, and I do not read release note v18 as an approval. It holds every lease word a viewer would see: 'processed once' beside a crash scene (this report's own reading; LREP:80 says only 'approval of the lease sentence'), the label 'setting: lease 45 s' and the words 'other lease settings' on card line 4 (a viewer hears 'lease' with no explanation). "
               "WHY: your release note v14 line 149 (item 11) bars lease and recovery sentences from the post and the video 'unless approved in writing'; release note v18 dropped those words from line 149, so they are a v14 cite only; v18 keeps line 33 (G12) and line 150 (no sentence about a lease), so the hold rests on those two lines and is this report's reading. "
               "THE ONE FORM, THE ONE PLACE: to approve, write on its own line in ORDERS.md `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`. Nothing else approves G12 and nothing is written on the run sheet for it. "
               "THE ORDER: first the loopback re-smoke of TASK (5) runs these three checks with stand-ins and writes each result with UTC and IST under risks list item 12: (1) the table rule seen in the re-smoke database; (2) a repeat send more than 45 seconds after the first, reply flag true; (3) a crash followed by a repeat while the recovery flow is working, 1 row and 1 mail counted. Then, and only then, you write the G12 line (TASK (10)), dated after those three results. "
               "If you do not approve G12, say so in the answer line by the questions L-CARDLEASE and L-LEASE; the take then cannot show those words (section 1c has the two other answers).")
    t = t.replace("@@G12@@", g12_new)

    # ---- 6. LRN14 cite (design M1, naive M1)
    t = sub(t, "(its lines 8, 33, 149, 150 equal the newest note)", "(its lines 33 and 150 equal the newest note, v18; its lines 8 and 149 differ from v18, section 0)", 1)
    t = sub(t, "release note v18 has lines 8, 33, 149 and 150 equal to v14 (the check script compares the whole lines), so every LRN14 cite stays valid;",
            "release note v18 has lines 33 and 150 equal to v14 (the check script compares the whole lines) and lines 8 and 149 different, so LRN14:8 and LRN14:149 are v14 cites only;", 1)
    t = sub(t, "(LRN14:149, item 11)", "(LRN14:149, item 11; words in v14 only)", None)
    t = sub(t, "LRN14:149, item 11 (any sentence", "LRN14:149, item 11, words in v14 only (any sentence", 1)
    t = sub(t, "(item 11 of your release note bars lease words from the video unless approved in writing;", "(item 11 of your release note v14 bars lease words from the video unless approved in writing; v18 dropped those words;", 1)
    t = sub(t, "the line now says that the 45 s lease setting and the stopwatch are allowed, so it does not contradict", "the line now says that the stopwatch is allowed and the 45 s lease setting only after G12 is approved, so it does not contradict", None)
    # the v14 versus newest statement in 1c (the lines compare list)
    t = sub(t, "the c6s check script mtimes", "the c6s check script mtimes", 0) if False else t

    # ---- 7. rows carrying the lease label hold G12 (design M2, naive M5)
    t = edit_row_text(t, 1, 'and the label "setting: lease 45 s" (a setting, not a result).', 'and the label "setting: lease 45 s" (a setting, not a result; on screen only after G12 is approved).')
    t = edit_row_text(t, 1, "the live stopwatch, the label 'sped up, real wait' and the label 'setting: lease 45 s' stay.", "the live stopwatch and the label 'sped up, real wait' stay; the label 'setting: lease 45 s' stays only after G12 is approved.")
    t = edit_row_text(t, 19, "(the 45 s lease setting is allowed; nothing is measured on the flows of this take)", "(the 45 s lease setting is allowed only after G12 is approved: it is a setting, not a result; nothing is measured on the flows of this take)")

    # ---- 8. the card words: one default, one question (design M4, naive M7)
    lq = "| L-CARDLEASE | Card line 4 says 'other lease settings' and no viewer is told what a lease is (release note v18 line 150 says nothing about a lease). Keep the three words 'other lease settings', held under G12, or drop them (a builder re-issues row 14 and the lengths: line 4 of 19 words, the card 87 words, about 34.8 s)? | Keep, held under G12. If you do not mean to approve G12, answer 'drop' (needs a further round). |"
    t = sub(t, "| L-POST | Does 'public post'", lq + "\n| L-POST | Does 'public post'", 1)
    lq3 = ("| L-CARDLEASE (new in c6w) | studio lead | Card line 4 (row 14) says 'other lease settings'. Keep these three words, held under G12 (they are filmed only after your written G12 line), or drop them? Facts: no viewer is told what a lease is; release note v18 line 150 says nothing about a lease; a card line 4 without them is the same line minus those three words (the card then holds 87 words, about 34.8 s, budget 40 s). | Keep, held under G12. | No | If drop: a builder re-issues row 14 and the card lengths (a further round); the words 'other lease settings' are then in no row. | 14 |")
    t = sub(t, "| L-KILL (was Q2) | studio lead |", lq3 + "\n| L-KILL (was Q2) | studio lead |", 1)
    t = sub(t, "The card wording ('lead' versus 'contact', 'other lease settings') is decided in L-CARD", "The card wording ('lead' versus 'contact', 'other lease settings') is decided in L-CARD", 0) if False else t

    # ---- 9. every non-default answer needs a further round (naive M7)
    t = sub(t, "TO ANSWER: add after the names in step 2 one 'except' per label,",
            "EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND: the builder cannot apply it from this text; a builder re-issues the rows it touches and a reviewer reads them again before they are applied. L-LEASE 1 or 2 counts only if L-POST is 'no' and G12 is approved; with L-POST 'yes' (the default) it is ignored and 'none' applies. "
            "TO ANSWER: add after the names in step 2 one 'except' per label,", 1)
    t = sub(t, "Answer forms: L-CARD, L-CARDCUT, L-CARDTEXT, L-POST,", "Answer forms: L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEASE keep or drop, L-POST,", 1)

    # ---- 10. TASKS and the first rehearsal: one list (design m1, naive B2, M8)
    t = sub(t, "(5) you run the loopback re-smoke and provoke an alert mail (crash test K3), then a builder applies rows 58 and 59;",
            "(5) you run the loopback re-smoke, which runs and writes the three G12 checks (table rule seen; a repeat send more than 45 seconds after the first; a crash followed by a repeat) and provokes an alert mail (crash test K3), then a builder applies rows 58 and 59;", 1)
    t = sub(t, "- TASK (10) you approve G12 in writing. TASK (11) the first rehearsal. TASK (12) the take.",
            "- TASK (10) you write the ONE G12 line in ORDERS.md (form in the WORDS list), dated after the results of TASK (5). TASK (11) the first rehearsal, only when the ONE LIST is complete: TASKS (1) to (6) and (8) to (10) are done and written (TASK (7) happens after the take; TASK (9) is done when you have answered it, yes or no). TASK (12) the take.", 1)
    t = sub(t, "after TASKS (5) to (9) of the list in the box are done and written (the loopback re-smoke has passed, the two lines of rehearsal list item 14 are written, the five entries of risks list item 11 are written, the owner has been asked about the sheet and the key)",
            "when the ONE LIST of the box is complete (TASKS (1) to (6) and (8) to (10) are done and written: the import check and the loopback re-smoke have passed, the leak scan is written and tested, the owner has been asked about the sheet, the key and failed runs, TASK (9) is answered and the G12 line is written; TASK (7), the five entries of risks list item 11 and the two lines of rehearsal list item 14, is written at the re-pin and is NOT part of this list)", 1)
    t = sub(t, "the first rehearsal comes after TASKS (5) to (9) of the box list)", "the first rehearsal comes when the ONE LIST of the box is complete: TASKS (1) to (6) and (8) to (10))", 1)
    t = sub(t, "TASK (11) hold the first rehearsal (after TASKS (5) to (10) are written);", "TASK (11) hold the first rehearsal (when the ONE LIST is complete: TASKS (1) to (6) and (8) to (10) done and written; TASK (7) comes after the take; TASK (9) is done when answered);", 1)
    t = sub(t, "set saving of successful runs to all and of failed runs to none in the environment that starts n8n;",
            "set saving of successful runs to all and of failed runs to none in the environment that starts n8n; in the same re-smoke run the three G12 checks and write each result with date and time in UTC and IST under risks list item 12: the table rule seen in the re-smoke database; one contact sent a second time more than 45 seconds after the first, with the repeat flag true; a crash followed by a repeat while the recovery flow is working, with 1 row and 1 mail counted;", 1)
    t = sub(t, "TASK (10) approve the lease wording (G12): write 'lease wording approved' under risks list item 12 with the date and time in UTC and IST and three pieces of evidence (the table rule seen in the re-smoke database; a repeat sent more than 45 seconds after the first send, flag true; a crash followed by a repeat during the recovery, 1 row and 1 mail counted);",
            "TASK (10) approve G12: write the ONE line of the WORDS list in ORDERS.md with the date and time in UTC and IST, dated after the three results of TASK (5) (nothing is written on the run sheet for G12);", 1)

    # ---- 11. row 8 item 12 and the gate row: no 'lease wording approved'; approval = the ORDERS.md line (naive B2)
    t = sub(t, "Whenever card line 1 or the scene 3 caption carries the plain statement that a second send is processed once (it does under the default), one rehearsal repeat sent more than 45 seconds after the first send is also written here,",
            "Whenever card line 1 or the scene 3 caption carries the plain statement that a second send is processed once (it does under the default), one repeat sent more than 45 seconds after the first send, run in the loopback re-smoke, is also written here,", 1)
    t = sub(t, "APPROVAL: card line 1 and the scene 3 caption are not filmed until the studio lead has written here 'lease wording approved' with the date and time in UTC and IST; this is his own decision",
            "APPROVAL: card line 1 and the scene 3 caption are not filmed until the studio's order file carries the studio lead's G12 line (its form is in the report's WORDS list; he writes it there, not here), dated after the three results below; this is his own decision", 1)
    t = sub(t, "The approval must cite, in writing with the date and time in UTC and IST: (1) the table rule seen in the re-smoke database; (2) the repeat sent more than 45 seconds after the first send, with the repeat flag true; (3) one rehearsal case in which the first run crashes",
            "The three results are written here, each with the date and time in UTC and IST, before the G12 line: (1) the table rule seen in the re-smoke database; (2) the repeat sent more than 45 seconds after the first send, with the repeat flag true; (3) one loopback re-smoke case in which the first run crashes", 1)
    t = sub(t, "| Lease wording approval (risks list item 12) | the studio lead has written 'lease wording approved' with the date and time in UTC and IST, and the repeat sent more than 45 seconds after the first send is written with its reply showing the repeat flag true |",
            "| G12 approval (risks list item 12) | ORDERS.md carries the studio lead's G12 line, dated after the three results written under risks list item 12 (the table rule seen; the repeat sent more than 45 seconds after the first send with its reply showing the repeat flag true; the crash followed by a repeat, 1 row and 1 mail) |", 1)
    t = sub(t, "until he writes 'lease wording approved' with UTC and IST, and a repeat sent more than 45 seconds after the first send is then mandatory;", "until he writes the G12 line with UTC and IST, and a repeat sent more than 45 seconds after the first send is then mandatory;", 1)
    return t, ct


def extra(t, ct):
    # ---- stale labels (naive m3, design m4)
    t = sub(t, "THE NEWEST OWNER SHEET, RECHECKED AGAIN IN c6t:", "THE NEWEST OWNER SHEET AT THE CHECK TIME:", 1)
    t = sub(t, "c6u (this file) supersedes c6t, which superseded c6s, c6r, c6q, c6p and c6o;", "c6w (this file) supersedes c6v, which superseded c6u, c6t, c6s, c6r, c6q, c6p and c6o;", 1)
    t = sub(t, "The c6t box states its real count in its second paragraph and verify-c6w.py recounts it.", "The box states its real count in its second paragraph and verify-c6w.py recounts it.", 1)
    t = sub(t, "The c6s box held about 3,488 words", "(history) The c6s box held about 3,488 words", 1)
    t = re.sub(r"\[done in (c6[a-z])\]", r"[written in \1, not applied]", t)
    t = rsub(t, r"\(10\) NOT FIXED, c6t design review m5:.*?so that the row count stays at 96\.", "(10) FIXED IN c6v: rows 97 to 104 mark the stale leftovers (rehearsal items 3, 5 and 6, risks items 7 and 8); the row count is 104.", 1)
    return t


def extra2(t, ct, words, p2words):
    # ---- card: one default state (design M3, naive M4): row 96 sets 40 s EST like row 11
    L = t.split("\n")
    i = row_idx(L, 96)
    assert L[i].count("`own runs. \\| 35 s EST`") == 1, "row 96 new cell"
    L[i] = L[i].replace("`own runs. \\| 35 s EST`", "`own runs. \\| 40 s EST`")
    t = "\n".join(L)
    t = rsub(t, r"the new cell is 35 s EST, the budget of the state the defaults leave:.*?Other cut cases: Table B\.",
             "the new cell is 40 s EST, the same budget as row 11 (the card the defaults write: 90 words, about 36 s). THE DEFAULTS CUT NOTHING BY HAND: if G12 stays open the gate keeps card line 1 and the scene 3 caption off the film, and the shorter card of Table B (79 words, 31.6 s) fits inside the 40 s. Any shorter case of Table B needs a hand edit of the cell and a further round.", 1)
    t = sub(t, "new in c6u; text and anchor changed in c6v |", "new in c6u; text and anchor changed in c6v; new cell changed from 35 s to 40 s in c6w |", 1)
    t = rsub(t, r"Row 11 writes the defaults, not the cut case; you apply the cut case by hand\. The card's Time cell on run sheet line 41 \(row 96\):.*?the other cut cases: Table B\.",
             "Row 11 writes the defaults, not the cut case; a cut case needs a hand edit and a further round. The card's Time cell on run sheet line 41 (row 96): old cell text (with the words before it): own runs. | 30 s EST. New cell text: 40 s EST, the same as the budget in row 11 (90 words). The defaults cut nothing by hand: with G12 open the gate keeps card line 1 and the scene 3 caption off the film, and the card read without line 1 (79 words, 31.6 s) fits inside the 40 s. The other rows of Table B are NOT the defaults.", 1)
    t = sub(t, "(74 words with the plain line 1, about 29.6 s, budget 30 s, total about 180 s)", "(74 words with the plain line 1, about 29.6 s, budget 30 s, total about 180 s; the margin is 0.4 s and no stopwatch run exists, so (b) may run over)", 1)
    t = sub(t, "NONE (the default): card line 1 is the plain statement", "THE DEFAULT REVERSES YOUR ANSWER Q22 (c) (ORD:186) FOR THE VIDEO: it follows your later answer ORD:230, which is newer; say so if you meant otherwise. NONE (the default): card line 1 is the plain statement", 1)
    # ---- L-SHEET: two names (naive M6, design m3)
    t = sub(t, "Sheet A and sheet B are two renderings of one checklist (the heading of each file says which; the owner's numbers message must name the same letter); answer with one version and letter, for example v34A.",
            "The two files of one version, OWNER-SHEET-vN-A.md and OWNER-SHEET-vN-B.md, are RENDERING A and RENDERING B of one checklist (the heading of each file says which; the owner's numbers message must name the same rendering). KEY ROUTE A and KEY ROUTE B are something else: the two ways of handling the older key (ORD:226 to ORD:228). Answer with one version and one rendering, for example 'v34 rendering A'.", 1)
    t = sub(t, "with the two routes A and B for the older key and marked blanks", "with the two KEY ROUTES A and B for the older key and marked blanks", 1)
    t = sub(t, "Name the one sheet that is final (for example 'v30A'); if the studio lead renders a later version, name that one.", "Name the one sheet that is final (for example 'v34 rendering A'); if the studio lead renders a later version, name that one.", 2)
    # ---- written-times statement (design m2)
    t = sub(t, "(v30 A and B and release note v14 at 17:22:10 UTC = 22:52:10 IST, then", "(at that time v30 A and B and release note v14 showed 17:22:10 UTC = 22:52:10 IST; they now show 18:46:25 UTC like v31 to v33 and release notes v14 to v17, so one bulk write touched them together; then", 1)
    t = sub(t, "'Newest' can change at any minute:", "The identical written time 18:46:25 UTC of v30 to v33 and of release notes v14 to v17 shows a bulk write, not an edit of each file; the check compares written times only and no content hash, so it sees that a file was rewritten but not what changed. 'Newest' can change at any minute:", 1)
    # ---- who read what; honest verifier claims (naive M3, design M5)
    t = sub(t, "- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.", "- WHO HAS READ WHAT. This report c6w: no reviewer yet. The changed files do not exist (nothing is applied). Reviews that read earlier versions of this report: review-c6v-design.md and review-c6v-naive.md read REPORT-c6v.md only; the independent evidence runner of c6v (evidence-c6v-independent/) ran scripts and read nothing else. TASK (3) of the box, the two reviewers after wave 1, reads the CHANGED FILES with the old and new text of each row; it does not judge the statements of this report, so under the defaults nobody else reads those statements: order a review of this report before you type the answer line, or accept that its statements are the builder's.\n- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.", 1)
    t = sub(t, "- FAILURES FIRST IN c6v (history;", C6W_FAIL + "- FAILURES FIRST IN c6v (history;", 1)
    t = sub(t, "- THE 18 RUNS ARE 18 KEPT RUNS.", "- HOW MUCH IS PROVEN BY WHOM: the counts of changed copies in neg-output.txt (for example 'N changed copies, 0 wrong') are my own run of my own scripts; nobody else has rerun them, and a check that passes proves that the text equals what I wrote, not that it is true.\n- THE 18 RUNS ARE 18 KEPT RUNS.", 1)
    t = sub(t, "I started no sub-agent and no background process.", "I started no sub-agent; I ran the full pipeline run_all.sh %s time(s) (cap 2; heavy-slot order), details in c6w-CHANGES.md." % NRUNS, 1)
    # ---- labels defined once (naive m1, m2, M9)
    lab = ("- LABELS OF THE CHECKS AND OF EARLIER REVIEWS (each defined once): CLASS 1 TO 7 = the kinds of check the scripts verify-c6w*.py add on top of the per-row checks: class 1 a safe-default phrase is unchanged in every place it is quoted; class 2 every count or version quoted twice is equal; class 4 every quoted copy of a card line equals the line in rows 13 and 14; class 5 the sentence 'no row edits the owner sheet or release note' stands in the box and in 1c; class 6 a short old text occurs once in the whole file; class 7 (new in c6w) the defects of the c6v reviews: the answer line names this report, one form of G12, the lease label carries the G12 hold on every row, one card state, every label used is defined, one branch statement, two names for sheet A and B, a CHANGES row per finding (class 3 was never used). "
           "W- = the name of a changed copy of this report in evidence-c6w/neg-output.txt that one check must reject. G19 = the clean-start gate of release note v16 line 39. L-APP2 = a question of the owner-sheet track that I did not check (section 9). N1, N2, N5 and F-022 in section 6 = finding numbers of earlier reviews of the demo files, kept as pointers. QUESTIONS.md = the older question file of this folder; mf_leads.sql = the SQL file of the stand-in contact table. RELEASE NOTE VERSIONS: v12 = LRN (older), v14 = LRN14, v18 = the newest; v16 is cited once (G19).\n")
    t = sub(t, "- TWO ROLES. STUDIO LEAD", lab + "- TWO ROLES. STUDIO LEAD", 1)
    # coverage table: the eleven carve-out rows
    t = sub(t, "the eight carve-out rows now say 'the 45 s lease setting is allowed only after G12 is approved'", "the eleven carve-out rows (1, 2, 5, 15, 17, 19, 30, 34, 83, 93, 94) now say 'the 45 s lease setting is allowed only after G12 is approved' (c6w added the hold to rows 1 and 19 and fixed the stale reason cells)", 1)
    t = sub(t, "| rows 1, 2, 5, 15, 17, 19, 30, 34, 83, 93, 94 |", "| rows 1, 2, 5, 15, 17, 19, 30, 34, 83, 93, 94; checked for every row that carries the label (class 7) |", 1)
    t = sub(t, "class 2 check: every count of 30 or more and every owner-sheet version quoted twice is equal", "class 2 check: every count of 30 or more and every owner-sheet version quoted twice is equal; class 7 adds: every count word before 'carve-out rows' or 'rows' equals the rows it lists", 1)
    t = sub(t, "COVERAGE OF THE c6u REVIEWS (", C6V_COV + "COVERAGE OF THE c6u REVIEWS (", 1)
    # section 9: new entries
    t = sub(t, "## 9. Not covered here (each with the label and the exact next step)\n", "## 9. Not covered here (each with the label and the exact next step)\n" + C6W_S9, 1)
    return t


def extra3(t):
    """box trims (naive M9): history and detail leave the box; G12 WHY and ORDER move to section 1c-I; no label before the WORDS list that is not defined there"""
    def line_replace(t, start, new):
        L = t.split("\n")
        cut = [i for i, l in enumerate(L) if l.startswith("## Start here, part 2")][0]
        idx = [i for i, l in enumerate(L[:cut]) if l.startswith(start)]
        if len(idx) != 1:
            FAILS.append("line_replace: %d match(es) for %r" % (len(idx), start[:60]))
            return t
        L[idx[0]] = new
        return "\n".join(L)
    t = rsub(t, r"Five items are OPEN and 'apply all defaults' answers none: the two OWNER ONLY questions of the table; G12 \(yours\); the meaning of Q27 \(a\), \(b\), \(c\) and the delete-path check \(the owner's, ORD:232\)\.",
             "Five items are OPEN and 'apply all defaults' answers none: the two OWNER ONLY questions of the table; G12 (yours); two owner items about the take script (section 1c).", 1)
    t = line_replace(t, "6. WHAT THE DEFAULTS LEAVE:", "6. WHAT THE DEFAULTS LEAVE: G12 OPEN, so card line 1 and the scene 3 caption cannot be filmed; card line 2 waits for an alert mail seen in the loopback re-smoke. The video is NOT yet filmable. The defaults cut nothing by hand: rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and row 96 sets the card's Time cell to the same 40 s; a gate, not a row, keeps card line 1 and the caption off the film until G12 is approved (shorter cases: Table B, section 1c; each needs a hand edit and a further round).")
    t = line_replace(t, "- CONTACT = one made-up sales contact", "- CONTACT = one made-up sales contact (the files call it a 'lead'; card line 1 says 'lead', your decided sentence, lines 2 to 4 say 'contact'). HUBSPOT = the customer-record system (a CRM) where the take writes its contacts. KEY = a secret code that lets a program use an account (the owner's HubSpot key; a second, separate probe key). SEND = one submission of a contact; SAME ID = every send carries the same contact id. n8n = the tool that runs the flows. STAND-IN = a fake service. LOOPBACK RE-SMOKE = a short test of the whole setup on this computer only, with stand-ins.")
    t = line_replace(t, "- TAKE = the one filmed run;", "- TAKE = the one filmed run; REHEARSAL = a practice run. RUN SHEET = VIDEO-RUNSHEET.md: scenes 1 to 4 (1 the stack at rest, 2 one contact goes in, 3 the same contact is sent again, 4 n8n is switched off mid-contact and recovery finishes it) and a closing card (scenes 5 to 11 of an older plan are listed, not filmed); RISKS LIST and REHEARSAL LIST = two numbered lists in it. RE-PIN = putting together and reading the final take files. PUBLIC POST = the post that goes out with the video (your ruling: section 1c).")
    t = line_replace(t, "- GATE = a run sheet step", "- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 = YOUR approval, the row of release note v14 line 33 (LRN14:33): '| G12 | Claims: the one sentence, the ban list of section 5 decided (the lease sentence is out of the public post, lead answer Q22c) | sentence in writing | sentence missing |'. It is OPEN: I do not approve it, and I do not read release note v18 as an approval. It holds every lease word a viewer would see: 'processed once' beside a crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' on card line 4. THE ONE FORM, THE ONE PLACE: write on its own line in ORDERS.md `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`, and only after the loopback re-smoke of TASK (5) has written its three G12 results on the run sheet. Why it is open and in what order: section 1c-I.")
    t = line_replace(t, "- TIMES are UTC with IST", "- TIMES are UTC with IST (UTC + 5:30). CITES (all under handover/core-hardening/): ORD:150 = line 150 of ORDERS.md; LRN14 = steps-edits/LEAD-RELEASE-NOTE-v14.md (its lines 33 and 150 equal the newest note, v18; its lines 8 and 149 differ, section 0); LREP = REPORT.md; PLAN = inputs/plan-wp6-resmoke-v5.md; ONE = inputs/DECISION-one-store.md; DEC = inputs/DECISIONS-2026-11-16.md (section 1 lists every file). THE CUT NUMBER = the 60.1 to 61.9 s recovery time of 18 stand-in crash runs that your decision 1 removes. Q27 = your answer in ORDERS.md about reading the take script. More words (MONEY STOP, FINAL, RUN, CHECK): section 1c.")
    t = rsub(t, r"The newest rendered version at the check time is v34 \(file names and written times: section 1c\)\. \| OPEN \(OWNER ONLY\)", "The newest rendered version at the check time is v34 (section 1c). | OPEN (OWNER ONLY)", 1)
    t = rsub(t, r"The two files of one version, OWNER-SHEET-vN-A\.md and OWNER-SHEET-vN-B\.md, are RENDERING A and RENDERING B of one checklist \(the heading of each file says which; the owner's numbers message must name the same rendering\)\. KEY ROUTE A and KEY ROUTE B are something else: the two ways of handling the older key \(ORD:226 to ORD:228\)\. Answer with one version and one rendering, for example 'v34 rendering A'\. The newest rendered version at the check time is v34 \(section 1c\)\. \| OPEN",
             "Answer with one version and one rendering, for example 'v34 rendering A' (RENDERING A and B = the two files OWNER-SHEET-vN-A.md and -B.md of one checklist; KEY ROUTE A and B are something else, the two ways of handling the older key; section 3). The newest version at the check time is v34. | OPEN", 1)
    t = line_replace(t, "EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND:", "EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND: the builder cannot apply it from this text; a builder re-issues the rows it touches and a reviewer reads them again. L-LEASE 1 or 2 counts only if L-POST is 'no' and G12 is approved; with L-POST 'yes' (the default) it is ignored. TO ANSWER: add after the names in step 2 one 'except' per label, for example `; except L-KILL: b; except L-APPROX: yes`. The two OPEN (OWNER ONLY) questions are two separate lines, each after you have asked the owner (form: section 1c). Answer forms: L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEASE (keep or drop), L-POST, L-APPROX, L-SAVE, L-PAGE, L-ONEDB, L-CUT yes or no; L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply.")
    t = line_replace(t, "- TASKS (1) to (8) in short", "- TASKS (1) to (8) in short (a builder applies rows 23, 58 and 59 as in step 1 and adds the row numbers to c6w-APPLIED-ROWS.md): (1) you write the answer line; (2) the builder applies wave 1; (3) two reviewers read the CHANGED FILES (not this report); (4) you import the edited flows into n8n and run C-4, then a builder applies row 23; (5) you run the loopback re-smoke, which also runs and writes the three G12 checks (table rule seen; a repeat send more than 45 seconds after the first; a crash followed by a repeat) and provokes an alert mail (crash test K3), then a builder applies rows 58 and 59; (6) a builder writes the leak scan C-6 and a second person tests it with a fake key; it runs after every rehearsal with real accounts and after the take, BEFORE any deletion; (7) at the re-pin you read the take script; (8) you ask the owner L-SHEET, the scope of his HubSpot key and L-SAVEERR. Long form: section 1c-F.")
    t = line_replace(t, "DATES. No file gives a duration", "DATES. No file gives a duration for TASKS (4) to (6), so I cannot say whether Wed 18 Nov 2026 (ORD:150, not fixed) can be reached; ask the builder for hours per task first. No take is planned on Mon 23 Nov (ORD:229). The post is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).")
    # section 1c-I carries what left the box
    i_txt = ("\n1c-I. G12: WHY IT IS OPEN, THE ORDER, THE OTHER ANSWERS. WHY: your release note v14 line 149 (item 11) bars lease and recovery sentences from the post and the video 'unless approved in writing'; release note v18 dropped those words from line 149, so they are a v14 cite only; v18 keeps line 33 (G12) and line 150 (no sentence about a lease), so the hold rests on those two lines and is this report's reading (that 'processed once' beside a crash scene is G12's subject is also this report's reading; LREP:80 says only 'approval of the lease sentence'). "
             "THE ORDER (not circular): (a) the loopback re-smoke of TASK (5) runs three checks with stand-ins and writes each result with UTC and IST under risks list item 12: (1) the table rule seen in the re-smoke database; (2) a repeat send more than 45 seconds after the first, reply flag true; (3) a crash followed by a repeat while the recovery flow is working, 1 row and 1 mail counted; (b) then you write the G12 line (TASK (10)), dated after those results; (c) then the first rehearsal (TASK (11)); the ONE LIST before it is TASKS (1) to (6) and (8) to (10). "
             "IF YOU DO NOT MEAN TO APPROVE G12: answer L-CARDLEASE 'drop' and L-LEASE 'none' now; the take then shows none of the held words (a further round). The two other answers to G12 (not approved; or closed already by line 33) are in the list of open items of section 9.\n")
    t = sub(t, "\n1c-H. THE SAVING PLAN LINE.", i_txt + "\n1c-H. THE SAVING PLAN LINE.", 1)
    return t


def extra2b(t, words, p2words):
    t = rsub(t, r"This box holds \d+ words \(counted without this heading line\); detail moved out of it, nothing deleted, is in section 1c\.",
             "This box holds %d words, counted without its heading line; part 2 under it (the exact card words, about %d words) is not counted, so reading both takes about %d words." % (words, p2words, words + p2words), 1)
    return t


def extra3b(t):
    def line_replace(t, start, new):
        L = t.split("\n")
        cut = [i for i, l in enumerate(L) if l.startswith("## Start here, part 2")][0]
        idx = [i for i, l in enumerate(L[:cut]) if l.startswith(start)]
        if len(idx) != 1:
            FAILS.append("line_replace: %d match(es) for %r" % (len(idx), start[:60]))
        
        L[idx[0]] = new
        L[idx[0]] = new
        return "\n".join(L)
    t = rsub(t, r" The deletion question is ANSWERED \(no, never\)\. This box holds ", " The deletion question is ANSWERED (no, never). This box holds ", 1)
    t = line_replace(t, "1. WHAT THE LINE OF STEP 2 DOES.", "1. WHAT THE LINE OF STEP 2 DOES. A builder applies the 95 rows of WAVE 1 (defined below) to the demo files, by text, in table order, on branch cloud/flows-audit (folder handover/; it holds the files of 90 rows). 5 rows (70, 71, 72, 90, 91) edit inputs/DECISION-one-store.md, which exists only on branch cloud/core-hardening; the builder writes the applied row numbers to c6w-APPLIED-ROWS.md there (folder handover/core-hardening/c6-skip-audit/), one commit per branch. The old texts were checked only against a scratchpad copy (shipped in evidence-c6w/tree/); equality with the real files is UNVERIFIED, so the builder first confirms that each old text occurs once in the real file and stops at any row where it does not.")
    t = line_replace(t, "2. Add this ONE line at the end", "2. Add this ONE line at the end of handover/core-hardening/ORDERS.md; the time is an EXAMPLE (real UTC: `date -u +%FT%TZ`, IST: `TZ=Asia/Kolkata date +%FT%T`). The word before 'apply all defaults' must be c6w and the file REPORT-c6w.md (the check script compares them with the file name). The names are labels no program reads; the reviewers are review agents (EGM = the studio's review method), not people: reviewer-B checks facts and risk, reviewer-C reads as a stranger.")
    t = line_replace(t, "WHAT 'APPLY ALL DEFAULTS' DOES", "WHAT 'APPLY ALL DEFAULTS' DOES (full text in section 1c): wave 1 only (step 1). It changes no running n8n; rows 23, 58, 59 and the 6 of L-SAVEERR are NOT applied; no row edits the owner sheet or release note.")
    t = rsub(t, r"\| L-CARDLEASE \| Card line 4 says 'other lease settings'.*?\n", "| L-CARDLEASE | Card line 4 says 'other lease settings'; no viewer is told what a lease is. Keep those three words, held under G12, or drop them (a builder re-issues row 14; the card then holds 87 words, about 34.8 s)? | Keep, held under G12. |\n", 1)
    t = rsub(t, r"- TASK \(9\), A QUESTION TO YOU: none of .*?\n", "- TASK (9), A QUESTION TO YOU: none of OWNER-SHEET-v34-A.md, OWNER-SHEET-v34-B.md and LEAD-RELEASE-NOTE-v18.md carries the 45-second limit sentence; your release note strikes it from the public post (LRN14:150). Do you want it added to the one final owner sheet and the release note? Yes: you or a builder you name adds it (no row does). No: no document carries it.\n", 1)
    t = line_replace(t, "- GATE = a run sheet step", "- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 = YOUR approval, the row of release note v14 line 33 (LRN14:33, 'sentence in writing'). It is OPEN: I do not approve it, and I do not read release note v18 as an approval. It holds every lease word a viewer would see: 'processed once' beside a crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' on card line 4. THE ONE FORM, THE ONE PLACE: write on its own line in ORDERS.md `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`, only after the loopback re-smoke of TASK (5) has written its three G12 results on the run sheet. Why it is open, and the order: section 1c-I.")
    # second trim pass
    t = rsub(t, r"Every question below has ONE status: ANSWERED BY DEFAULT \(you may change it\), ANSWERED \(by you\) or OPEN\. ", "Every question has ONE status: ANSWERED BY DEFAULT (you may change it), ANSWERED or OPEN. ", 1)
    t = rsub(t, r"This box holds (\d+) words, counted without its heading line; part 2 under it \(the exact card words, about", "This box holds \\1 words, counted without its heading line; part 2 under it (the exact card words, about", 0) if False else t
    t = line_replace(t, "6. WHAT THE DEFAULTS LEAVE:", "6. WHAT THE DEFAULTS LEAVE: G12 OPEN, so card line 1 and the scene 3 caption cannot be filmed, and card line 2 waits for an alert mail seen in the loopback re-smoke: the video is NOT yet filmable. The defaults cut nothing by hand: rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s), row 96 sets the card's Time cell to the same 40 s, and a gate keeps the held lines off the film (shorter cases: Table B, section 1c; each a hand edit and a further round).")
    t = sub(t, " DEC = inputs/DECISIONS-2026-11-16.md (section 1 lists every file). THE CUT NUMBER", " DEC = inputs/DECISIONS-2026-11-16.md. THE CUT NUMBER", 1)
    t = rsub(t, r"scenes 1 to 4 \(1 the stack at rest, 2 one contact goes in, 3 the same contact is sent again, 4 n8n is switched off mid-contact and recovery finishes it\) and a closing card \(scenes 5 to 11 of an older plan are listed, not filmed\); RISKS LIST", "scenes 1 to 4 (3 = the same contact is sent again, 4 = n8n is switched off mid-contact) and a closing card (scenes 5 to 11 of an older plan are listed, not filmed); RISKS LIST", 1)
    t = rsub(t, r" ALERT = a warning mail the system is built to send when it cannot tell what happened to a contact \(the stand-in tests showed one; the take's flows were not run\)\.", " ALERT = a warning mail the system is built to send when it cannot tell what happened to a contact (shown only in stand-in tests).", 1)
    t = rsub(t, r"The two OPEN \(OWNER ONLY\) questions are two separate lines, each after you have asked the owner \(form: section 1c\)\. ", "The two OWNER ONLY questions go on two separate lines (form: section 1c). ", 1)
    t = rsub(t, r"the builder cannot apply it from this text; a builder re-issues the rows it touches and a reviewer reads them again\. ", "a builder re-issues the rows it touches and a reviewer reads them again. ", 1)
    t = rsub(t, r"\(a builder applies rows 23, 58 and 59 as in step 1 and adds the row numbers to c6w-APPLIED-ROWS\.md\): ", "(a builder applies rows 23, 58, 59 and lists them in c6w-APPLIED-ROWS.md): ", 1)
    t = rsub(t, r"\(5\) you run the loopback re-smoke, which also runs and writes the three G12 checks \(table rule seen; a repeat send more than 45 seconds after the first; a crash followed by a repeat\) and provokes", "(5) you run the loopback re-smoke, which also runs and writes the three G12 checks (section 1c-I) and provokes", 1)
    t = rsub(t, r" Answer with one version and one rendering, for example 'v34 rendering A' \(RENDERING A and B = the two files OWNER-SHEET-vN-A\.md and -B\.md of one checklist; KEY ROUTE A and B are something else, the two ways of handling the older key; section 3\)\.", " Answer with one version and one rendering, for example 'v34 rendering A' (RENDERING A and B = the A file and the B file of one checklist; not the KEY ROUTES A and B, section 3).", 1)
    t = rsub(t, r"The old texts were checked only against a scratchpad copy \(shipped in evidence-c6w/tree/\); equality with the real files is UNVERIFIED, so the builder first confirms that each old text occurs once in the real file and stops at any row where it does not\.", "The old texts were checked only against a scratchpad copy (evidence-c6w/tree/): equality with the real files is UNVERIFIED, so the builder confirms each old text occurs once in the real file first and stops at any row where it does not.", 1)
    t = rsub(t, r"the label 'setting: lease 45 s' and the words 'other lease settings' on card line 4\. THE ONE FORM", "the label 'setting: lease 45 s' and the words 'other lease settings'. THE ONE FORM", 1)

    # third trim pass
    t = rsub(t, r"\(a builder applies rows 23, 58, 59 and lists them in c6w-APPLIED-ROWS\.md\): \(1\) you write the answer line; \(2\) the builder applies wave 1; \(3\) two reviewers read the CHANGED FILES \(not this report\); \(4\) you import the edited flows into n8n and run C-4, then a builder applies row 23; \(5\) you run the loopback re-smoke, which also runs and writes the three G12 checks \(section 1c-I\) and provokes an alert mail \(crash test K3\), then a builder applies rows 58 and 59; \(6\) a builder writes the leak scan C-6 and a second person tests it with a fake key; it runs after every rehearsal with real accounts and after the take, BEFORE any deletion; \(7\) at the re-pin you read the take script; \(8\) you ask the owner L-SHEET, the scope of his HubSpot key and L-SAVEERR\.",
             "(a builder applies rows 23, 58, 59 and lists them in c6w-APPLIED-ROWS.md): (1) you write the answer line; (2) the builder applies wave 1; (3) two reviewers read the CHANGED FILES (not this report); (4) you import the edited flows into n8n and run C-4, then a builder applies row 23; (5) you run the loopback re-smoke (it also writes the three G12 checks, section 1c-I, and provokes an alert mail, crash test K3), then a builder applies rows 58 and 59; (6) a builder writes the leak scan C-6, a second person tests it with a fake key; it runs after every rehearsal with real accounts and after the take, BEFORE any deletion; (7) at the re-pin you read the take script; (8) you ask the owner L-SHEET, his HubSpot key scope and L-SAVEERR.", 1)
    t = rsub(t, r" KEY = a secret code that lets a program use an account \(the owner's HubSpot key; a second, separate probe key\)\.", " KEY = a secret code that lets a program use an account.", 1)
    t = rsub(t, r"Five items are OPEN and 'apply all defaults' answers none: the two OWNER ONLY questions of the table; G12 \(yours\); two owner items about the take script \(section 1c\)\. ", "Five items are OPEN and 'apply all defaults' answers none: the two OWNER ONLY questions; G12 (yours); two owner items about the take script (section 1c). ", 1)


    # fourth trim pass
    t = rsub(t, r"Your line starts the builder\. The G12 approval is ONE line in ORDERS\.md \(form in the WORDS list, item G12\), written only after the loopback re-smoke of TASK \(5\) has put its results on the run sheet\.", "Your line starts the builder.", 1)
    t = rsub(t, r"Answer forms: L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEASE \(keep or drop\), L-POST, L-APPROX, L-SAVE, L-PAGE, L-ONEDB, L-CUT yes or no; L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply\.", "Answer forms: yes or no, except L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply; L-CARDLEASE keep or drop.", 1)
    t = rsub(t, r"The defaults cut nothing by hand: rows 11 to 14 write the whole card \(90 words, about 36 s, budget 40 s\), row 96 sets the card's Time cell to the same 40 s, and a gate keeps the held lines off the film \(shorter cases: Table B, section 1c; each a hand edit and a further round\)\.", "Rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and its Time cell on the run sheet is set to 40 s; a gate keeps the held lines off the film (shorter cases: Table B, section 1c; each needs a hand edit and a further round).", 1)
    t = rsub(t, r"\(a builder applies rows 23, 58, 59 and lists them in c6w-APPLIED-ROWS\.md\): \(1\)", ": (1)", 1)

    # fifth trim pass
    t = rsub(t, r"\(TASK \(7\) happens after the take; TASK \(9\) is done when you have answered it, yes or no\)", "(TASK (7) comes after the take; TASK (9) is done once answered)", 1)
    t = rsub(t, r" so I cannot say whether Wed 18 Nov 2026 \(ORD:150, not fixed\) can be reached; ask the builder for hours per task first\.", " so whether Wed 18 Nov 2026 (ORD:150, not fixed) can be reached is unknown; ask the builder for hours per task.", 1)
    t = rsub(t, r"spends nothing; imports nothing into n8n; does not start the filmed run; writes no card line", "spends nothing; imports nothing into n8n; writes no card line", 1)
    t = rsub(t, r" \(the files call it a 'lead'; card line 1 says 'lead', your decided sentence, lines 2 to 4 say 'contact'\)", " (the files say 'lead'; card line 1 keeps your decided word 'lead', lines 2 to 4 say 'contact')", 1)
    t = rsub(t, r" THE CUT NUMBER = the 60\.1 to 61\.9 s recovery time of 18 stand-in crash runs that your decision 1 removes\.", " THE CUT NUMBER = the 60.1 to 61.9 s recovery time of 18 stand-in runs, removed by your decision 1.", 1)

    # sixth trim pass
    _k = t.index("## Start here, part 2")
    _h, _tl = t[:_k], t[_k:]
    _h = _h.replace(" It changes no running n8n; rows 23, 58, 59 and the 6 of L-SAVEERR are NOT applied; no row edits the owner sheet or release note.", " No row edits the owner sheet or release note.", 1)
    t = _h + _tl
    t = rsub(t, r" More words \(MONEY STOP, FINAL, RUN, CHECK\): section 1c\.", "", 1)

    t = rsub(t, r" \(shorter cases: Table B, section 1c; each needs a hand edit and a further round\)", " (shorter cases: Table B, section 1c; each needs a hand edit)", 1)
    t = rsub(t, r"; ask the builder for hours per task\.", "; ask the builder.", 1)

    t = sub(t, "| 14 | NOT APPLIED; on the default of L-CARD, L-CARDCUT, L-CARDLEN, L-CARDTEXT |", "| 14 | NOT APPLIED; on the default of L-CARD, L-CARDCUT, L-CARDLEASE, L-CARDLEN, L-CARDTEXT |", 1)
    t = sub(t, "a second person tests it with a fake key", "a second person (someone who did not write the scan) tests it with a fake key", 1)

    t = sub(t, "| L-CARDLEN | 11, 13, 14, 86, 96 | 5 | 0 (none) | 5 (11, 13, 14, 86, 96) |", "| L-CARDLEASE | 14 | 1 | 0 (none) | 1 (14) |\n| L-CARDLEN | 11, 13, 14, 86, 96 | 5 | 0 (none) | 5 (11, 13, 14, 86, 96) |", 1)

    t = t.replace("The identical written time 18:46:25 UTC of v30", "The identical written time 18:46:25 UTC = 00:16:25 IST of v30")

    # seventh trim pass: the WHAT TO TYPE block must fit one screen (under 2,400 characters)
    _k = t.index("## Start here, part 2")
    _h, _tl = t[:_k], t[_k:]
    for _a, _b in (("in short : (1)", "in short: (1)"),
                   (" (capital-letter words and labels here are explained in the lists below and in section 1c):", " (capitalised words are explained in the lists below and in section 1c):"),
                   (" (defined below) to the demo files", " to the demo files"),
                   (" there (folder handover/core-hardening/c6-skip-audit/), one commit per branch.", " there, one commit per branch."),
                   (" (its scope is unconfirmed);", ";"),
                   (" The names are labels no program reads; the reviewers are review agents", " The reviewers are review agents"),
                   ("5. Only the owner lines go in besides. Your line starts the builder.", "5. Your line starts the builder."),
                   (" (shorter cases: Table B, section 1c; each needs a hand edit).", " (shorter cases: Table B, section 1c)."),
                   (" (the check script compares them with the file name)", " (a script compares them with the file name)")):
        assert _h.count(_a) == 1, _a
        _h = _h.replace(_a, _b)
    t = _h + _tl

    t = sub(t, "| 1 | run sheet, line 90 | Scene 4 shows no test result in seconds; the live stopwatch, the label 'sped up, real wait' and the label 'setting: lease 45 s' stay. |", "| 1 | run sheet, line 90 | Scene 4 shows no test result in seconds; the live stopwatch and the label 'sped up, real wait' stay; the label 'setting: lease 45 s' stays only after G12 is approved. |", 1)

    t = sub(t, "RELEASE NOTE VERSIONS: v12 = LRN (older), v14 = LRN14, v18 = the newest; v16 is cited once (G19).", "RELEASE NOTE VERSIONS: v12 = LRN (older), v14 = LRN14, v18 = the newest; v16 is cited once (G19). STEP = one numbered line of WHAT TO TYPE; CHECK = a test by a script of this folder or a run in n8n (C-1 to C-11, section 7); KEY = a secret code (word list in the box); PRIMARY KEY = the database rule that allows one row per contact id; 'lead' is used only inside quotes and file names, otherwise 'contact'.", 1)
    t = sub(t, "5a. WHAT CHANGES", "READING THE REASON CELLS: in the full table the reason cell after its first stop is history of earlier versions; rows 39 and 76 are two edits of two different lines that show the same viewer text.\n5a. WHAT CHANGES", 1)
    _k = t.index("## Start here, part 2")
    _h, _tl = t[:_k], t[_k:]
    assert _h.count("reached only through you.") == 1
    _h = _h.replace("reached only through you.", "reached only through you; if you are also the owner, the two roles stay separate.", 1)
    t = _h + _tl

    t = sub(t, "only the take's own 45 s lease setting may be named.`", "only the take's own 45 s lease setting may be named, and only after G12 is approved.`", 1)
    t = sub(t, "1, 2, 5, 15, 17, 19, 30, 34, 83, 93 and 94", "1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93 and 94", 2)

    t = sub(t, "(40 words; it REPLACES sentence 1; not to be spoken as fact before check C-9 part 2). | none.", "(40 words; it REPLACES sentence 1; not to be spoken as fact before check C-9 part 2). 1 and 2 also need the G12 approval first. | none.", 1)
    t = t.replace("two names for sheet A and B", "two names for the A file and the B file of one owner sheet")
    # real written times of the newest sheet and release note (read from the files; the c6v text carried older times)
    import os as _os, datetime as _dt, re as _re_, glob as _gl_
    _st = _os.environ.get("C6V_STEPS") or _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "steps-edits")
    def _wt(n):
        d = _dt.datetime.fromtimestamp(_os.path.getmtime(_os.path.join(_st, n)), _dt.timezone.utc)
        return d.strftime("%H:%M:%S"), (d + _dt.timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
    t = t.replace("v34 A, B and SOURCE and release note v18 at 18:56:55 UTC = 00:26:55 IST", "v34 A, B and release note v18 again at 19:14:05 UTC = 00:44:05 IST")
    for _old, _fn in (("18:56:54 UTC = 00:26:54 IST", "OWNER-SHEET-v34-A.md"), ("18:56:55 UTC = 00:26:55 IST", "LEAD-RELEASE-NOTE-v18.md")):
        _u, _i = _wt(_fn)
        t = t.replace(_old, "%s UTC = %s IST" % (_u, _i))
    # files written after the freeze: named with their real written time and compared by this script with the file of the previous version
    import filecmp as _fc
    _live = _os.environ.get("C6V_STEPS_LIVE")
    _frz = _os.environ.get("C6V_FREEZE", "2026-11-16T19:30:00Z")
    if _live and _os.path.isdir(_live):
        _fdt = _dt.datetime.strptime(_frz, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc).timestamp()
        _late = sorted(n for n in _os.listdir(_live) if _re_.match(r"(OWNER-SHEET|LEAD-RELEASE-NOTE)-v\d+", n) and n.endswith(".md") and _os.path.getmtime(_os.path.join(_live, n)) > _fdt)
        _parts = []
        for n in _late:
            _u, _i = (lambda d: (d.strftime("%H:%M:%S"), (d + _dt.timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")))(_dt.datetime.fromtimestamp(_os.path.getmtime(_os.path.join(_live, n)), _dt.timezone.utc))
            m = _re_.match(r"(OWNER-SHEET|LEAD-RELEASE-NOTE)-v(\d+)(.*)\.md$", n)
            prev = "%s-v%d%s.md" % (m.group(1), int(m.group(2)) - 1, m.group(3))
            pp = _os.path.join(_live, prev)
            if "SOURCE" in n:
                how = "a draft that was not compared"
            elif not _os.path.exists(pp):
                how = "no file of the previous version to compare"
            elif m.group(1) == "LEAD-RELEASE-NOTE":
                how = "byte-identical to %s" % prev if _fc.cmp(pp, _os.path.join(_live, n), shallow=False) else "DIFFERENT from %s" % prev
            else:
                a_ = open(pp, encoding="utf-8").read().replace("v%d" % (int(m.group(2)) - 1), "v%d" % int(m.group(2)))
                how = "equal to %s after the version number is changed" % prev if a_ == open(_os.path.join(_live, n), encoding="utf-8").read() else "DIFFERENT from %s beyond the version number" % prev
            _parts.append("%s was written %s UTC = %s IST; %s" % (n, _u, _i, how))
        if _parts:
            _fin_r = max(int(_re_.search(r"-v(\d+)", f).group(1)) for f in _gl_.glob(_st + "/LEAD-RELEASE-NOTE-v*.md") if "SOURCE" not in f)
            _txt = " FILES WRITTEN AFTER THE FREEZE (%s = 01:00:00 IST on 2026-11-17, the time up to which this report reads the files): %s. This report names the newest version before the freeze and reads none of these; if the lead finishes a later version, the version numbers named here need a new check." % (_frz, "; ".join(_parts))
            t = sub(t, "NEWEST RELEASE NOTE NAMED: v%d." % _fin_r, "NEWEST RELEASE NOTE NAMED: v%d.%s" % (_fin_r, _txt), 1)
    return t


NRUNS = "2"
FINDINGS = [
    # (id, finding, fix, check name in verify_c6w_part4.py)
    ("design B1", "answer line names c6u and REPORT-c6u.md", "the answer line names c6w and REPORT-c6w.md; the typed line says so in step 2", "D-B1 answer line names this report"),
    ("design M1", "box line 22 says release note lines 8, 33, 149, 150 equal v18; other lines say 8 and 149 differ; G12 reasoning rests on v14:149", "line 22 and the 1c text say 33 and 150 equal, 8 and 149 differ; every cite of item 11 says 'words in v14 only'; the G12 word gives its WHY", "D-M1 one statement about release note lines"),
    ("design M2", "G12 hold missing on rows 1 and 19; stale reason cells; 'eight' versus 11 rows", "rows 1 and 19 carry the hold; the reason cells say the stopwatch is allowed and the lease setting only after G12; 'the eleven carve-out rows'", "D-M2 every row with the lease label holds G12; count words equal listed rows"),
    ("design M3", "rows 11 to 14 and row 96 contradict (40 s and 90 words versus 35 s)", "row 96 sets 40 s like row 11; the defaults cut nothing by hand; Table B cases are not defaults", "D-M3 one card state in rows 11, 13, 14, 96"),
    ("design M4", "card line 4 and 'lease' ship by default; card wording deferred to a question that does not exist", "new question L-CARDLEASE (default keep, held under G12) in the box and in section 3", "D-M4 every question label used exists in the box table"),
    ("design M5", "verifier claims exceed what is checked; box count excludes part 2; '267 copies' is my word", "the box states its count and part 2 separately; HOW MUCH IS PROVEN BY WHOM says the counts are my own run; class 7 checks count words", "D-M5 box count honest; count words equal rows"),
    ("design m1", "first rehearsal list differs (5)-(9) versus (5)-(10)", "ONE LIST in the box, 1c, 3d and section 0", "D-m1 one list before the first rehearsal"),
    ("design m2", "v30 to v33 written-time statements conflict; mtime only", "section 0 states the bulk write and that no content hash is used", "D-m2 written-time statement"),
    ("design m3", "example 'v30A' versus v34A", "'v34 rendering A' everywhere", "D-m3 no 'v30A'"),
    ("design m4", "stale labels c6t and 'done in' while nothing is applied", "labels replaced by 'written in c6x, not applied'", "D-m4 no stale label"),
    ("design m5", "'no sub-agent' versus six full runs", "the sentence names the number of runs of run_all.sh and the cap", "D-m5 run count named"),
    ("design m6", "option (b) of L-CARDLEN has a 0.4 s margin", "margin stated; (b) may run over until a stopwatch run", "D-m6 margin stated"),
    ("design m7", "default none reverses Q22 (c) for the video", "L-LEASE row says plainly that the default follows ORD:230 and reverses ORD:186", "D-m7 reversal stated"),
    ("naive B1", "same as design B1", "same fix", "D-B1 answer line names this report"),
    ("naive B2", "G12 has two forms and a circular order; re-smoke cases not placed", "ONE form (the ORDERS.md line), results written first under risks list item 12, the three cases run in the loopback re-smoke (TASK (5)), the line is TASK (10)", "N-B2 one G12 form, no 'lease wording approved' outside history"),
    ("naive M1", "same as design M1", "same fix", "D-M1 one statement about release note lines"),
    ("naive M2", "one builder, two branches; which branch holds what", "box step 1 names both branches, the 90 plus 5 rows and where c6w-APPLIED-ROWS.md and the commits go", "N-M2 branch statement equals the table"),
    ("naive M3", "reviewing described two ways", "section 0 WHO HAS READ WHAT", "N-M3 who-read-what bullet"),
    ("naive M4", "same as design M3", "same fix", "D-M3 one card state in rows 11, 13, 14, 96"),
    ("naive M5", "row 1 lacks the hold", "same as design M2", "D-M2 every row with the lease label holds G12"),
    ("naive M6", "sheet A/B has two meanings", "RENDERING A/B (two files) and KEY ROUTE A/B (two ways for the older key)", "N-M6 no 'sheet A', both names present"),
    ("naive M7", "non-default answers have no warning; L-LEASE ignored under L-POST yes; card wording deferral", "paragraph EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND; L-CARDLEASE", "N-M7 further-round paragraph"),
    ("naive M8", "first-rehearsal precondition differs; TASK (9) is a question", "ONE LIST; TASK (9) done when answered", "D-m1 one list before the first rehearsal"),
    ("naive M9", "box about 2,500 words, step 1 a run-on, labels before explanation", "box shorter, step 1 in two parts, no undefined label before the WORDS list", "N-M9 no undefined label before the WORDS list; box words stated equal counted"),
    ("naive m1", "words with two meanings (step, line, check, key, lead)", "LABELS bullet defines STEP, CHECK, KEY, PRIMARY KEY, lead", "N-m1 labels bullet"),
    ("naive m2", "undefined labels (L-APP2, G19, N1, classes, W-, release note versions)", "LABELS bullet defines each", "N-m2 labels bullet defines them"),
    ("naive m3", "stale text (c6u this file, c6t box, NOT FIXED count 96)", "replaced", "D-m4 no stale label"),
    ("naive m4", "37 viewer rows versus 38 default rows", "one sentence says they are different sets", "N-m4 sets named"),
    ("naive m5", "rows 39 and 76 same viewer text; reason cells long history", "sentence in section 5: the reason cell after the first stop is history; rows 39 and 76 are two edits of two lines", "N-m5 history sentence"),
    ("naive m6", "reviewer-name order wording", "reviewer-B and reviewer-C roles said", "D-B1 answer line names this report"),
    ("naive m7", "'the lead' reader versus roles", "box: if you are also the owner the roles stay separate", "N-m7 roles sentence"),
    ("naive m8", "section 3e item numbers", "see section 9: stated, not renumbered", "N-m8 listed in section 9"),
    ("naive m9", "counts to reconcile (seven stop steps, ten gate rows, six)", "one sentence in section 9 names the three sets and what each counts", "N-m9 listed in section 9"),
]

C6W_FAIL = ("- FAILURES FIRST IN c6w (my own, still open when I wrote this): (1) no EGM reviewer has read REPORT-c6w.md or the new checks (class 7); every statement here is a builder statement until the studio lead's reviewers have read it. "
    "(2) C-1 and C-1b are DONE on the scratchpad copy only: UNVERIFIED against the real files (99 of the 104 rows name files that branch cloud/core-hardening lacks; the files are shipped in evidence-c6w/tree/). "
    "(3) The independent evidence runner of c6v (agent a6e53326d3376c7d1) was still running when I wrote this; its findings are not in this report unless the studio lead relayed them: see c6w-CHANGES.md. "
    "(4) G12 is still OPEN: I did not read release note v18 (which dropped 'unless approved in writing' from line 149) as a decision. "
    "(5) Every answer other than the default needs a further round: I did not write the re-issued rows for L-CARDLEN b, L-LEASE 1 or 2, L-KILL b, L-APPROX yes, L-PAGE yes, L-POST no, L-CARD no, L-CARDLEASE drop or L-SAVEERR yes (they depend on answers nobody has given). "
    "(6) Sections 1, 4, 6 and 8 (below the c6u block) and rows 19 to 95 apart from the ones named in this section were changed only where a finding named them; the c6v reviewers did not read all of them either. "
    "(7) Nothing is applied; no n8n, flow, harness or stopwatch run; no spend; no commit.\n")

C6V_COV = ("COVERAGE OF THE c6v REVIEWS (review-c6v-design.md, review-c6v-naive.md; the line-by-line mapping is in c6w-CHANGES.md; the checks are in verify_c6w_part4.py and, for the old classes, in verify-c6w.py, verify_c6w_part2.py and verify_c6w_part3.py):\n\n"
    "| Finding | Finding in short | Fix | Check |\n|---|---|---|---|\n"
    + "".join("| %s | %s | %s | %s |\n" % f for f in FINDINGS) + "\n")

C6W_S9 = ("- [needs-lead] Section 3e (naive m8): two rows are pinned to rehearsal list item 12 and three to risks list item 12, and row 8 puts three results under one item number. Not renumbered in c6w because renumbering would change old texts that no reviewer has read. Next step: the reviewers decide whether to renumber.\n"
    "- [needs-lead] Counts to reconcile (naive m9): the builder's stop steps (section 1c, seven), the gate rows of section 3e (ten) and the list of six in section 1c-F count different things (steps that stop a builder; gates on the run sheet; steps of the first-rehearsal list). They are not equal on purpose; a reviewer should confirm that each list is complete.\n"
    "- [needs-lead] Rows 39 and 76 carry the same viewer text on run sheet line 149: they are two edits (two different old texts), not one.\n")


if __name__ == "__main__":
    words = 2300
    t = None
    for _ in range(5):
        FAILS.clear()
        t, ct = build(words)
        t = extra(t, ct)
        p2 = t[t.index("## Start here, part 2"):t.index("## 0. Failures")]
        p2w = len(p2.split())
        t = extra2(t, ct, words, p2w)
        t = extra3(t)
        t = extra3b(t)
        t = extra2b(t, words, p2w)
        body = t[t.index("## Start here: what"):t.index("## Start here, part 2")]
        n = len(body.split("\n", 1)[1].split())
        if n == words:
            break
        words = n
    print("box words (counted without the heading line): stated %d, counted %d; part 2 %d" % (words, n, p2w))
    if FAILS:
        print("BUILD FAILED:")
        for f in FAILS:
            print("  " + f)
        sys.exit(1)
    open(D + "REPORT-c6w.md", "w", encoding="utf-8").write(t if t.endswith("\n") else t + "\n")
    print("wrote REPORT-c6w.md (%d lines)" % len(t.split("\n")))

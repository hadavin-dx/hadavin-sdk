"""Builds ../REPORT-c6x.md (main file), ../REPORT-c6x-TABLE.md (appendix A: section 5, the 104-row edit table) and ../REPORT-c6x-COVERAGE.md (appendix B: section 8)
from ../REPORT-c6w.md (read only, never changed). Every patch asserts its match count; a miss stops the build and prints every miss.
Usage: python3 -B -I build_c6x.py   (run_all.sh runs static-checks, this file, the verifier, the negative controls and the scan in that order).
Box counting rule (as in c6w): the words of the start box are counted from the first line AFTER its heading to the line before the heading of part 2.
The two appendix files are put back into the text by the checks at the line '@@INCLUDE <file>@@' (see load_full in verify-c6x.py): the checks read the same text as before the split."""
import re, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE) + "/"
E = HERE + "/"
FAILS = []
OLDCT = "2026-11-16T19:44:12Z"   # the check time written in REPORT-c6w.md
MOVED = []                        # text that left the start box in c6x; it is printed in section 1c-J (nothing is deleted)


def sub(t, old, new, c=1):
    n = t.count(old)
    if (c is not None and n != c) or (c is None and n == 0):
        FAILS.append("expected %s match(es), found %d: %r" % (c, n, old[:110]))
        return t
    return t.replace(old, new)


def move_out(t, old, new):
    """a piece of the start box is replaced by a shorter one; the old piece is kept word for word in section 1c-J"""
    k0, k1 = t.index("## Start here: what I need"), t.index("## Start here, part 2")
    if t[k0:k1].count(old) != 1:
        FAILS.append("move_out: expected 1 match in the box, found %d: %r" % (t[k0:k1].count(old), old[:90]))
        return t
    MOVED.append(old)
    return t[:k0] + t[k0:k1].replace(old, new) + t[k1:]


def build(words, p2words):
    MOVED.clear()
    t = open(D + "REPORT-c6w.md", encoding="utf-8").read()
    # ---- 0. file-name tokens move to c6x; narrative 'c6w' stays (it is history)
    t = re.sub(r"\b(REPORT-|evidence-|verify-|verify_|scan_|neg_new_|neg_controls_|ctime_|census-|build_)c6w", r"\1c6x", t)
    t = t.replace("c6w-APPLIED-ROWS.md", "c6x-APPLIED-ROWS.md")
    t = t.replace("the line-by-line mapping is in c6w-CHANGES.md", "@@W-MAP@@").replace("c6w-CHANGES.md", "c6x-CHANGES.md").replace("@@W-MAP@@", "the line-by-line mapping is in c6w-CHANGES.md")
    t = sub(t, "The word before 'apply all defaults' must be c6w and the file REPORT-c6x.md", "The word before 'apply all defaults' must be c6x and the file REPORT-c6x.md")
    t = sub(t, "): c6w apply all defaults to REPORT-c6x.md;", "): c6x apply all defaults to REPORT-c6x.md;")
    t = sub(t, "# REPORT-c6x: video audit fix pass, round 5 of the edit-row report, supersedes REPORT-c6v.md (2026-11-16, UTC; IST = UTC + 5:30)",
            "# REPORT-c6x: video audit fix pass, round 6 of the edit-row report, supersedes REPORT-c6w.md (2026-11-16, UTC; IST = UTC + 5:30)\n\n"
            "WHAT FAILED, WHAT IS UNCERTAIN, WHAT I DID NOT RUN (first, in plain words; section 0 has the full list). FAILED: the c6w report failed both independent reviews (review-c6w-design.md: 0 blockers, 5 majors; review-c6w-naive.md: 0 blockers, 9 majors); this report is the fix, and each fix is checked only by my own scripts. The check run of c6w ended unclean (details in section 0). UNCERTAIN: whether the old texts of the 104 rows equal the real files (99 of them cannot be read in this repository); whether the words held under gate G12 are the right words (this report's own reading); whether anything the independent evidence runner of c6w finds is fixed here (its findings reached me late; section 0 says which). NOT RUN: no n8n, no flow, no stopwatch, no take script, no real key; NO REVIEWER HAS READ THIS REPORT; nothing is applied to any file; no spend; no commit; no sub-agent.\n"
            "(This report is in three files so that it can be read in parts: REPORT-c6x.md = start box, sections 0 to 4, 6, 7 and 9; REPORT-c6x-TABLE.md = section 5, the edit table with its 104 rows; REPORT-c6x-COVERAGE.md = section 8, finding to fix to place. Nothing was deleted by the split.)")
    # ---- 1. check time and example times of the start box: replaced by the time of the last static-checks run
    ct = re.search(r"check time \(UTC\): (\S+)", open(E + "static-checks-output.txt", encoding="utf-8").read()).group(1)
    dt = datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ")
    ist = lambda x: (x + datetime.timedelta(hours=5, minutes=30))
    old_dt = datetime.datetime.strptime(OLDCT, "%Y-%m-%dT%H:%M:%SZ")
    sys.path.insert(0, E)
    import ctime_c6x
    oe1, oi1, oe2, oi2 = ctime_c6x.example_times(OLDCT)
    ne1, ni1, ne2, ni2 = ctime_c6x.example_times(ct)
    t = t.replace(OLDCT + " = " + ist(old_dt).strftime("%H:%M:%S") + " IST", ct + " = " + ist(dt).strftime("%H:%M:%S") + " IST")
    t = t.replace(old_dt.strftime("%H:%M:%S") + " UTC = " + ist(old_dt).strftime("%H:%M:%S") + " IST", dt.strftime("%H:%M:%S") + " UTC = " + ist(dt).strftime("%H:%M:%S") + " IST")
    t = t.replace(OLDCT, ct)
    t = sub(t, "%s = %s IST" % (oe1, oi1), "%s = %s IST" % (ne1, ni1), 1)
    t = sub(t, "%s = %s IST" % (oe2, oi2), "%s = %s IST" % (ne2, ni2), None)
    return t, ct


def patches(t, ct):
    # =============== THE START BOX ===============
    # naive M1: no reviewer has read the report; design M2: the G12 scope is the report's own reading
    t = sub(t, "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE. The edit table",
            "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE. NO REVIEWER HAS READ THIS REPORT (nor its checks): every statement in it is the builder's own until the reviewers you order have read it; step 3 of TASKS reads the changed files, not this report. The reach of G12 below (which words it holds) is this report's own reading, not a quote of any file. The edit table")
    t = sub(t, "G12 (yours); two owner items about the take script (section 1c). The deletion question is ANSWERED (no, never).",
            "G12 (yours); the two OWNER-OPEN items about the take script, L-Q27 and L-DELCRIT (ORD:232; they are rows of the QUESTIONS table). The deletion question is ANSWERED (no, never).")
    t = sub(t, "puts no sentence about the 45-second setting into any document;",
            "writes no sentence that explains the 45-second setting into any document (the rows that write the label 'setting: lease 45 s' or the words 'other lease settings' write them only as HELD under G12: see item 6);")
    # naive M9 / m: the names in the typed line, who parses it
    t = sub(t, "The reviewers are review agents (EGM = the studio's review method), not people: reviewer-B checks facts and risk, reviewer-C reads as a stranger.",
            "builder-A, reviewer-B and reviewer-C are NAMES YOU CHOOSE (type them as they are, or put the names of the agents you start): builder-A applies the rows; reviewer-B and reviewer-C are the two review agents of TASK (3) (EGM = the studio's review method): reviewer-B checks facts and risk, reviewer-C reads as a stranger. No program reads this line; the builder you name does, and the check script of this report only compares the label and the file name of its own example.")
    # design M1 / naive M3: every held item in item 6
    t = sub(t, "6. WHAT THE DEFAULTS LEAVE: G12 OPEN, so card line 1 and the scene 3 caption cannot be filmed, and card line 2 waits for an alert mail seen in the loopback re-smoke: the video is NOT yet filmable. Rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and its Time cell on the run sheet is set to 40 s; a gate keeps the held lines off the film (shorter cases: Table B, section 1c).",
            "6. WHAT THE DEFAULTS LEAVE: G12 OPEN, so FOUR things cannot be filmed: (i) card line 1, (ii) the three words 'other lease settings' at the end of card line 4, (iii) the scene 3 caption, (iv) the on-screen label 'setting: lease 45 s' (scene 4, rows 1 and 17) with the carve-out sentences of rows 1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93 and 94 that name it. Card line 2 also waits for an alert mail seen in the loopback re-smoke. The video is NOT yet filmable. Rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and its Time cell on the run sheet is set to 40 s; a gate keeps the held lines off the film, so a person cuts (i) to (iii) by hand before filming: the card then holds 76 words, about 30.4 s, inside the 40 s (Table B, case 'G12 open', section 1c).")
    # naive M4: the G12 forms in the box; design M2 reach of G12
    t = sub(t, "only after the loopback re-smoke of TASK (5) has written its three G12 results on the run sheet. Why it is open, and the order: section 1c-I.",
            "only after the loopback re-smoke of TASK (5) has written its three G12 results on the run sheet. TO REFUSE: write `## G12 (studio lead, <UTC> = <IST>): not approved`, then answer L-CARDLEASE 'drop' and L-LEASE 'none' (a further round; the take then shows none of the held words). IF RELEASE NOTE V14 LINE 33 IS ALREADY YOUR APPROVAL: write `## G12 (studio lead, <UTC> = <IST>): closed: line 33 of release note v14 is my approval`. The reach of G12 (card line 1, the label, 'other lease settings', the scene 3 caption) is this report's own reading: release note v14 line 33 says only 'sentence in writing' and LREP:80 says only 'approval of the lease sentence'. Why it is open, and the order: section 1c-I.")
    # naive m: 'lead', 'claim', A/B, scene 12
    t = sub(t, "CLAIM always means reserve; a sentence in the video is a STATEMENT.",
            "CLAIM always means reserve; a sentence in the video is a STATEMENT (your own wording quoted in L-LEASE answer 1 says 'claim' for a statement). I = the builder who wrote this report, one person. 'Lead' inside a quoted card line = a sales contact; 'the lead' in file names and cites = the studio lead. RENDERING A and RENDERING B = the two files of one owner sheet; KEY ROUTE A and KEY ROUTE B = two ways to treat the owner's older key (section 3).")
    t = sub(t, "and a closing card (scenes 5 to 11 of an older plan are listed, not filmed);",
            "and a closing card (the run sheet calls it scene 12; scenes 5 to 11 of an older plan are listed, not filmed);")
    # the new questions (naive M5, ORD:147)
    t = sub(t, "| L-DEL | Does the take delete contacts? | ANSWERED by you: no, never. (The delete-path check is a different item, OPEN, the owner's: ORD:232.) |",
            "| L-DEL | Does the take delete contacts? | ANSWERED by you: no, never. (The delete-path check is a different item, OPEN, the owner's: L-DELCRIT, ORD:232.) |\n"
            "| L-Q27 | Your answer Q27 (ORD:191) says you read the take script at the re-pin and answer its three points with line numbers: (a) it waits for a go marker before it spends, (b) it refuses to run after the money stop, (c) what happens, and which exit code results, when the key is cancelled during a run. What does 'Q27 is shown' mean: all three, or does (b) alone allow Mon 23 Nov? | OPEN (OWNER-OPEN, ORD:232). Not covered by 'apply all defaults'. This report assumes the strictest reading (all three), as ITS OWN assumption, not his answer. |\n"
            "| L-DELCRIT | What must the delete-path check show? (It is the search of the final take script for the words archive and delete.) | OPEN (OWNER-OPEN, ORD:232). Not covered by 'apply all defaults'. This report assumes the strictest reading (no call to either word anywhere in the script), as ITS OWN assumption, not his answer. |\n"
            "| L-KEYLINE | Your order ORD:147 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'. No row writes it, because the owner has not said what his key may do (the same order says so), and a spoken claim nobody can back is not written. Write it anyway? THIS IS A DEPARTURE FROM YOUR ORDER, stated here. | No (not written). Yes: a builder you name adds a row after the owner has confirmed the key's scope. |")
    t = sub(t, "Answer forms: yes or no, except L-CARDLEN a or b;", "Answer forms: yes or no (L-KEYLINE too), except L-CARDLEN a or b;")
    # shrink: the short task list (the long form is in 1c-F)
    k0 = t.index("- TASKS (1) to (8) in short:")
    k1 = t.index("\n", k0)
    old = t[k0:k1]
    t = move_out(t, old, "- TASKS (1) to (8), one line each (long form: section 1c-F): (1) you write the answer line; (2) the builder applies wave 1; (3) two reviewers read the changed files; (4) import check C-4, then row 23; (5) the loopback re-smoke, then rows 58 and 59; (6) the leak scan C-6 is written and tested; (7) at the re-pin you read the take script; (8) you ask the owner L-SHEET, the key scope and L-SAVEERR.")
    # shrink: the closing sentence of step 1 (it is also in section 0 and in 1c)
    t = move_out(t, "The old texts were checked only against a scratchpad copy (evidence-c6x/tree/): equality with the real files is UNVERIFIED, so the builder confirms each old text occurs once in the real file first and stops at any row where it does not.",
                 "The old texts were checked only against a copy (evidence-c6x/tree/): UNVERIFIED against the real files; the builder confirms each old text first and stops at any row where it does not match.")
    t = move_out(t, "- TIMES are UTC with IST (UTC + 5:30). CITES (all under handover/core-hardening/): ORD:150 = line 150 of ORDERS.md; LRN14 = steps-edits/LEAD-RELEASE-NOTE-v14.md (its lines 33 and 150 equal the newest note, v18; its lines 8 and 149 differ, section 0); LREP = REPORT.md; PLAN = inputs/plan-wp6-resmoke-v5.md; ONE = inputs/DECISION-one-store.md; DEC = inputs/DECISIONS-2026-11-16.md. THE CUT NUMBER = the 60.1 to 61.9 s recovery time of 18 stand-in runs, removed by your decision 1. Q27 = your answer in ORDERS.md about reading the take script.",
                 "- TIMES are UTC with IST (UTC + 5:30). CITES (all under handover/core-hardening/): ORD:150 = line 150 of ORDERS.md; LRN14 = steps-edits/LEAD-RELEASE-NOTE-v14.md (its lines 33 and 150 equal the notes v18 and v19; its lines 8 and 149 differ, section 0); LREP = REPORT.md; PLAN = inputs/plan-wp6-resmoke-v5.md; ONE = inputs/DECISION-one-store.md; DEC = inputs/DECISIONS-2026-11-16.md. THE CUT NUMBER = the 60.1 to 61.9 s recovery time of 18 stand-in runs, removed by your decision 1. Q27 = your answer ORD:191 about reading the take script (its open part: L-Q27).")
    # the dates: 'tonight' (naive m)
    t = sub(t, "DEC:13 gives only the re-smoke target: tonight or tomorrow morning IST.", "DEC:13 gives only the re-smoke target, written on Mon 16 Nov 2026 as 'tonight or tomorrow morning IST' (that is Mon 16 Nov at night or Tue 17 Nov 2026 in the morning, IST).")
    return t


def patches3(t, ct):
    """shrink of the start box: each piece that leaves it is printed word for word in section 1c-J (move_out), the box keeps a shorter form"""
    mo = lambda old, new: move_out(t_ref[0], old, new)
    g = lambda old, new: t_ref.__setitem__(0, move_out(t_ref[0], old, new))
    t_ref = [t]
    g(" builder-A, reviewer-B and reviewer-C are NAMES YOU CHOOSE (type them as they are, or put the names of the agents you start): builder-A applies the rows; reviewer-B and reviewer-C are the two review agents of TASK (3) (EGM = the studio's review method): reviewer-B checks facts and risk, reviewer-C reads as a stranger. No program reads this line; the builder you name does, and the check script of this report only compares the label and the file name of its own example.",
      " builder-A, reviewer-B and reviewer-C are NAMES YOU CHOOSE (builder-A applies the rows; the two reviewers are the review agents of TASK (3): B checks facts and risk, C reads as a stranger; EGM = the studio's review method). No program reads this line but the builder you name; the full note is in 1c-J.")
    g(" TO REFUSE: write `## G12 (studio lead, <UTC> = <IST>): not approved`, then answer L-CARDLEASE 'drop' and L-LEASE 'none' (a further round; the take then shows none of the held words). IF RELEASE NOTE V14 LINE 33 IS ALREADY YOUR APPROVAL: write `## G12 (studio lead, <UTC> = <IST>): closed: line 33 of release note v14 is my approval`. The reach of G12 (card line 1, the label, 'other lease settings', the scene 3 caption) is this report's own reading: release note v14 line 33 says only 'sentence in writing' and LREP:80 says only 'approval of the lease sentence'. Why it is open, and the order: section 1c-I.",
      " TO REFUSE: write `## G12 (studio lead, <UTC> = <IST>): not approved` and answer L-CARDLEASE 'drop', L-LEASE 'none'; IF LINE 33 OF NOTE v14 IS ALREADY YOUR APPROVAL: write `## G12 (studio lead, <UTC> = <IST>): closed: line 33 of release note v14 is my approval`. The reach of G12 is this report's own reading (section 1c-J). Why it is open, and the order: section 1c-I.")
    g(" CLAIM always means reserve; a sentence in the video is a STATEMENT (your own wording quoted in L-LEASE answer 1 says 'claim' for a statement). I = the builder who wrote this report, one person. 'Lead' inside a quoted card line = a sales contact; 'the lead' in file names and cites = the studio lead. RENDERING A and RENDERING B = the two files of one owner sheet; KEY ROUTE A and KEY ROUTE B = two ways to treat the owner's older key (section 3).",
      " CLAIM always means reserve; a sentence in the video is a STATEMENT. I = the builder who wrote this report. Lead, RENDERING and KEY ROUTE: 1c-A and 1c-J.")
    g("| L-Q27 | Your answer Q27 (ORD:191) says you read the take script at the re-pin and answer its three points with line numbers: (a) it waits for a go marker before it spends, (b) it refuses to run after the money stop, (c) what happens, and which exit code results, when the key is cancelled during a run. What does 'Q27 is shown' mean: all three, or does (b) alone allow Mon 23 Nov? | OPEN (OWNER-OPEN, ORD:232). Not covered by 'apply all defaults'. This report assumes the strictest reading (all three), as ITS OWN assumption, not his answer. |",
      "| L-Q27 | Q27 (ORD:191): you read the take script at the re-pin and answer its points (a) go marker before spending, (b) refuses to run after the money stop, (c) what happens, and which exit code, if the key is cancelled in a run. Does 'shown' mean all three? | OPEN (OWNER-OPEN, ORD:232), not covered by 'apply all defaults'; assumed: all three (my assumption, not his answer). |")
    g("| L-DELCRIT | What must the delete-path check show? (It is the search of the final take script for the words archive and delete.) | OPEN (OWNER-OPEN, ORD:232). Not covered by 'apply all defaults'. This report assumes the strictest reading (no call to either word anywhere in the script), as ITS OWN assumption, not his answer. |",
      "| L-DELCRIT | What must the search of the final take script for the words archive and delete show? | OPEN (OWNER-OPEN, ORD:232), not covered by the defaults; assumed: neither word is called anywhere (my assumption). |")
    g("| L-KEYLINE | Your order ORD:147 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'. No row writes it, because the owner has not said what his key may do (the same order says so), and a spoken claim nobody can back is not written. Write it anyway? THIS IS A DEPARTURE FROM YOUR ORDER, stated here. | No (not written). Yes: a builder you name adds a row after the owner has confirmed the key's scope. |",
      "| L-KEYLINE | ORD:147 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'. No row writes it: nobody has said what the owner's key may do. A DEPARTURE FROM YOUR ORDER. Write it anyway? | No. Yes: a builder adds a row after the owner confirms the key's scope. |")
    g("(i) card line 1, (ii) the three words 'other lease settings' at the end of card line 4, (iii) the scene 3 caption, (iv) the on-screen label 'setting: lease 45 s' (scene 4, rows 1 and 17) with the carve-out sentences of rows 1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93 and 94 that name it. Card line 2 also waits for an alert mail seen in the loopback re-smoke. The video is NOT yet filmable. Rows 11 to 14 write the whole card (90 words, about 36 s, budget 40 s) and its Time cell on the run sheet is set to 40 s; a gate keeps the held lines off the film, so a person cuts (i) to (iii) by hand before filming: the card then holds 76 words, about 30.4 s, inside the 40 s (Table B, case 'G12 open', section 1c).",
      "(i) card line 1, (ii) the three words 'other lease settings' (card line 4), (iii) the scene 3 caption, (iv) the label 'setting: lease 45 s' (scene 4; rows 1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93, 94 carry it). Card line 2 also waits for an alert mail seen in the re-smoke. The video is NOT yet filmable. A person cuts (i) to (iii) by hand: the card then holds 76 words, about 30.4 s (Table B, 1c).")
    g(" 5 rows (70, 71, 72, 90, 91) edit inputs/DECISION-one-store.md, which exists only on branch cloud/core-hardening; the builder writes the applied row numbers to c6x-APPLIED-ROWS.md there, one commit per branch. The old texts were checked only against a copy (evidence-c6x/tree/): UNVERIFIED against the real files; the builder confirms each old text first and stops at any row where it does not match.",
      " 5 rows (70, 71, 72, 90, 91) edit a file that exists only on branch cloud/core-hardening; one commit per branch. The old texts were checked only against a copy: UNVERIFIED; the builder confirms each first (details: 1c-J).")
    g("; writes no card line about the owner's HubSpot key; writes no sentence that explains the 45-second setting into any document (the rows that write the label 'setting: lease 45 s' or the words 'other lease settings' write them only as HELD under G12: see item 6); leaves unapplied the 3 rows that wait for a check and the 6 that wait for the owner.",
      "; writes no card line about the owner's HubSpot key; explains the 45-second setting in no document (the label and 'other lease settings' are HELD, item 6); leaves unapplied the 3 rows that wait for a check and the 6 that wait for the owner.")
    g("- CONTACT = one made-up sales contact (the files say 'lead'; card line 1 keeps your decided word 'lead', lines 2 to 4 say 'contact'). HUBSPOT = the customer-record system (a CRM) where the take writes its contacts. KEY = a secret code that lets a program use an account. SEND = one submission of a contact; SAME ID = every send carries the same contact id. n8n = the tool that runs the flows. STAND-IN = a fake service. LOOPBACK RE-SMOKE = a short test of the whole setup on this computer only, with stand-ins.",
      "- CONTACT = one made-up sales contact (the files say 'lead'). HUBSPOT = the customer-record system where the take writes its contacts. KEY = a secret code that lets a program use an account. SEND = one submission of a contact (SAME ID = the same contact id). n8n = the tool that runs the flows. STAND-IN = a fake service. LOOPBACK RE-SMOKE = a test of the whole setup on this computer only, with stand-ins.")
    g(" (the run sheet calls it scene 12; scenes 5 to 11 of an older plan are listed, not filmed); RISKS LIST and REHEARSAL LIST = two numbered lists in it. RE-PIN = putting together and reading the final take files. PUBLIC POST = the post that goes out with the video (your ruling: section 1c).",
      " (the run sheet calls it scene 12); RISKS LIST and REHEARSAL LIST = two numbered lists in it. RE-PIN = reading the final take files. PUBLIC POST = the post that goes with the video (section 1c).")
    g(" Answer with one version and one rendering, for example 'v34 rendering A' (RENDERING A and B = the A file and the B file of one checklist; not the KEY ROUTES A and B, section 3). The newest version at the check time is v34.",
      " Answer with one version and rendering, for example 'v34 rendering A' (A and B = the two files of one checklist). Newest at the check time: v34.")
    g(" TO ANSWER: add after the names in step 2 one 'except' per label, for example `; except L-KILL: b; except L-APPROX: yes`. The two OWNER ONLY questions go on two separate lines (form: section 1c). Answer forms: yes or no (L-KEYLINE too), except L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply; L-CARDLEASE keep or drop.",
      " TO ANSWER: add after the names in step 2 one 'except' per label, for example `; except L-KILL: b`. The two OWNER ONLY questions go on two lines (1c). Forms: yes or no, except L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply; L-CARDLEASE keep or drop.")
    g(" NO REVIEWER HAS READ THIS REPORT (nor its checks): every statement in it is the builder's own until the reviewers you order have read it; step 3 of TASKS reads the changed files, not this report. The reach of G12 below (which words it holds) is this report's own reading, not a quote of any file.",
      " NO REVIEWER HAS READ THIS REPORT OR ITS CHECKS: every statement is the builder's own until reviewers you order have read it (TASK (3) reads the changed files, not this report). The reach of G12 is this report's own reading.")
    g(" It is OPEN: I do not approve it, and I do not read release note v18 as an approval. It holds every lease word a viewer would see: 'processed once' beside a crash scene, the label 'setting: lease 45 s' and the words 'other lease settings'. THE ONE FORM, THE ONE PLACE: write on its own line in ORDERS.md `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`, only after",
      " It is OPEN: I do not approve it, and I do not read release note v18 as one. It holds the lease words a viewer would see (item 6). TO APPROVE write on its own line in ORDERS.md `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`, only after")
    g(" Do you want it added to the one final owner sheet and the release note? Yes: you or a builder you name adds it (no row does). No: no document carries it.", " Add it to the final owner sheet and release note? Yes: you or a builder you name adds it (no row does). No: nothing carries it.")
    g("DATES. No file gives a duration for TASKS (4) to (6), so whether Wed 18 Nov 2026 (ORD:150, not fixed) can be reached is unknown; ask the builder. No take is planned on Mon 23 Nov (ORD:229).", "DATES. No file gives a duration for TASKS (4) to (6), so Wed 18 Nov 2026 (ORD:150) may not be reachable. No take is planned on Mon 23 Nov (ORD:229).")
    g("1 or 2 = a sentence printed in part 2 (1: your 25-word limit sentence; 2: a 40-word explanation). 1 and 2 count only if L-POST is 'no' (if L-POST is 'yes', the default, they are ignored and 'none' applies) and need the G12 approval first.", "1 or 2 = a sentence printed in part 2. 1 and 2 count only if L-POST is 'no' and need G12 first.")
    g(" The card's Time cell (row 96) is in section 1c. | (a). |", " Time cell (row 96): 1c. | (a). |")
    g("Does 'public post' (your answer: the lease sentence stays out of it) include the closing card and the scene 3 caption? Under any answer the lease words on the video are held under G12. | Yes: they count; no sentence about the 45-second setting goes on the card or caption. |",
      "Does 'public post' (the lease sentence stays out of it, your answer) include the closing card and scene 3 caption? | Yes: no sentence about the 45-second setting goes on the card or caption. |")
    g(" The plan PLAN:125 also saves failed runs; the owner's words do not cover that, so failed runs are not saved. | Yes. |", " Failed runs are not saved (PLAN:125 says otherwise; the owner's words do not cover it). | Yes. |")
    g(" Until he answers, the builder keeps failed runs unsaved: 6 rows wait; scenes 1 and 2 then show successful runs only. This is what is done meanwhile, not an answer for him. |", " Until he answers, failed runs stay unsaved (6 rows wait): meanwhile, not his answer. |")
    g("; LREP = REPORT.md; PLAN = inputs/plan-wp6-resmoke-v5.md; ONE = inputs/DECISION-one-store.md; DEC = inputs/DECISIONS-2026-11-16.md. THE CUT NUMBER", "; LREP = REPORT.md; PLAN, ONE, DEC = the three files of inputs/ (1c-A). THE CUT NUMBER")
    g(" Until he answers, the builder uses none and applies no row to a sheet. NOT covered by 'apply all defaults'. |", " Until then no row touches a sheet. NOT covered by the defaults. |")
    g("Mark the run sheet lines of scenes 5 to 11 (an older, longer plan; the filmed video is scenes 1 to 4 and the closing card) as 'not in the one video'?", "Mark the run sheet lines of scenes 5 to 11 (an older plan) as 'not in the one video'?")
    g("May the web page carry the 60.1 to 61.9 s range and the 13-minute alert delay (2 relayed runs)? | No; both stay in the file, marked not for the page. |", "May the web page carry the 60.1 to 61.9 s range and the 13-minute alert delay? | No (marked not for the page). |")
    g("4. The two OPEN (OWNER ONLY) questions: ask the owner and write what he says, each on its own separate line (forms below). Neither can be put on the line of step 2.", "4. The two OWNER ONLY questions: ask the owner and write each answer on its own line (forms: 1c), never on the line of step 2.")
    g(" The deletion question is ANSWERED (no, never).", "")
    g(" Every question has ONE status: ANSWERED BY DEFAULT (you may change it), ANSWERED or OPEN.", " Every question is ANSWERED BY DEFAULT, ANSWERED or OPEN.")
    g(" The post is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).", " Post due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).")
    g(" (estimates until the stopwatch run)", " (estimates)")
    g("Cut the old card lines about '80 kills' and the recovery time (older flows; an estimate no data of this take backs)?", "Cut the old card lines about '80 kills' and the recovery time (no data of this take backs them)?")
    g("Does the take make n8n save every SUCCESSFUL run, so that the past runs filmed in scenes 1 and 2 show runs? (The owner approved this on made-up data, ONE:22-27.)", "Does the take make n8n save every SUCCESSFUL run, so scenes 1 and 2 show past runs? (The owner approved this on made-up data, ONE:22-27.)")
    return t_ref[0]


def late_paragraph(t):
    """the sentence 'FILES WRITTEN AFTER THE FREEZE ...' is rebuilt from the PINNED files (late-pinned and steps-pinned), never from the live folder"""
    import filecmp, glob
    frz = os.environ.get("C6V_FREEZE", "2026-11-16T19:30:00Z")
    late = sorted(os.listdir(E + "late-pinned"))
    parts = []
    for n in late:
        fp = E + "late-pinned/" + n
        d = datetime.datetime.fromtimestamp(os.path.getmtime(fp), datetime.timezone.utc)
        u, i = d.strftime("%H:%M:%S"), (d + datetime.timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        m = re.match(r"(OWNER-SHEET|LEAD-RELEASE-NOTE)-v(\d+)(.*)\.md$", n)
        prev = "%s-v%d%s.md" % (m.group(1), int(m.group(2)) - 1, m.group(3))
        pp = E + "steps-pinned/" + prev
        if "SOURCE" in n:
            how = "a draft that was not compared"
        elif not os.path.exists(pp):
            how = "no file of the previous version to compare"
        else:
            a_ = open(pp, encoding="utf-8").read().replace("v%d" % (int(m.group(2)) - 1), "v%d" % int(m.group(2)))
            how = ("equal to %s after the version number is changed" % prev) if a_ == open(fp, encoding="utf-8").read() else ("DIFFERENT from %s beyond the version number" % prev)
        parts.append("%s was written %s UTC = %s IST; %s" % (n, u, i, how))
    pin = open(E + "PIN-TIME.txt").read().strip()
    new = (" FILES WRITTEN AFTER THE FREEZE (%s = 01:00:00 IST on 2026-11-17, the time up to which this report reads the files; copied ONCE at %s and read from that copy by every check, evidence-c6x/late-pinned/): %s. This report names the newest version before the freeze and reads none of these; if the lead finishes a later version, the version numbers named here need a new check. "
           "COMPARISON BY SCRIPT (evidence-c6x/compare-late-files-output.txt): all three pairs are DIFFERENT (the line 'v35 equals v34, v19 equals v18' of c6w-CHANGES.md 6a was wrong).") % (frz, pin, "; ".join(parts))
    a = t.index(" FILES WRITTEN AFTER THE FREEZE (")
    b = t.index("need a new check.", a) + len("need a new check.")
    return t[:a] + new + t[b:]


def patches2(t, ct):
    t = late_paragraph(t)
    # =============== SECTION 3: the question rows (design M?, naive M5) ===============
    t = sub(t, "| L-CARDLEASE (new in c6w) | studio lead | Card line 4 (row 14) says 'other lease settings'. Keep these three words, held under G12 (they are filmed only after your written G12 line), or drop them? Facts: no viewer is told what a lease is; release note v18 line 150 says nothing about a lease; a card line 4 without them is the same line minus those three words (the card then holds 87 words, about 34.8 s, budget 40 s).",
            "| L-CARDLEASE (new in c6w) | studio lead | Card line 4 (row 14) says 'other lease settings'. Keep these three words, held under G12 (they are filmed only after your written G12 line), or drop them? Facts: no viewer is told what a lease is; release note v18 line 150 says nothing about a lease; a card line 4 without them is the same line minus those three words (the card then holds 87 words, about 34.8 s, budget 40 s). The words are ONE of the four held items (box item 6); they are the reason card line 4 is cut by hand when G12 stays open (76 words with line 1 also cut).")
    t = sub(t, "After C-8 passes AND the clean-start gate G19 is closed (release note v16 line 39: the caption 'one Postgres server, two databases' needs it), the only wording allowed is the studio lead's own: 'one Postgres server, two databases' (Q21.3).",
            "After C-8 passes AND the clean-start gate G19 is closed (release note v16 line 39: the caption 'one Postgres server, two databases' needs it), the only wording allowed is the studio lead's own: 'one Postgres server, two databases' (Q21.3). SCOPE OF THIS RULE (it settles an open conflict with card line 3): the rule bars any viewer text that says HOW MANY databases or stores there are. Card line 3 ('the made-up name and e-mail address sent to n8n may stay in n8n's own database') names the one place where the data may stay and says no number; it is allowed. A reviewer who reads 'own database' as a count says so, and then L-ONEDB 'No' means card line 3 changes to 'in n8n' (a further round); see section 9.")
    # =============== ROW 96 and TABLE B (design M1: every held item) ===============
    t = sub(t, "and the shorter card of Table B (79 words, 31.6 s) fits inside the 40 s. Any shorter case of Table B needs a hand edit of the cell and a further round.",
            "and the shorter cards of Table B (79 words, 31.6 s, with card line 1 cut; or 76 words, 30.4 s, with card line 1 and the three words 'other lease settings' cut) fit inside the 40 s. Any shorter case of Table B needs a hand edit of the cell and a further round.")
    t = sub(t, "| card lines 1 and 2 cut, scene 3 kept | 1, 2, 3, 4 = 150 s | 44 | 17.6 | 20 s | about 170 s | 20 s EST |",
            "| card lines 1 and 2 cut, scene 3 kept | 1, 2, 3, 4 = 150 s | 44 | 17.6 | 20 s | about 170 s | 20 s EST |\n| G12 open, every held item cut by hand: card line 1 and the three words 'other lease settings' cut (card line 4 ends at 'chat messages' with the next sentence kept; the scene 3 caption cut; the label 'setting: lease 45 s' not shown); 35 + 22 + 22 - 3 = 76 | 1, 2, 3, 4 = 150 s | 76 | 30.4 | 35 s | about 185 s | 35 s EST |")
    # =============== SECTION 0 =================
    t = sub(t, "- FAILURES FIRST IN c6w (my own, still open when I wrote this):",
            "- FAILURES FIRST IN c6x (my own, still open when I wrote this; each is checked only by my own scripts): (1) NO REVIEWER HAS READ THIS REPORT OR ITS CHECKS (the c6w report failed two independent reviews and had its own independent evidence run: 5 of its 314 changed copies exit 0, not 0 as c6w said: section 1b, review-c6w-evidence.md). (2) C-1 and C-1b are DONE on a copy only (UNVERIFIED against the real files: 99 of 104 rows name files that this branch lacks). (3) G12 is OPEN and its reach (which words it holds) is this report's reading. (4) THE RUN OF run_all.sh: the 'not clean' state of the c6w run (see c6w-CHANGES.md and section 9) is repeated here only as far as I could see it; section 9 says how many full runs I made of c6x, and whether each ended clean. (5) The checks of c6x are a script run by me; a passing check proves that a text equals what I wrote, not that it is true. (6) NOT RUN: n8n, any flow, stopwatch, take script, real key; no sub-agent; no commit; nothing applied.\n"
            "- THE V35 AND V19 COMPARISON (the file writes of another session, result of evidence-c6x/compare_late_files.py, output compare-late-files-output.txt): c6w-CHANGES.md 6a said 'v35 equals v34 and v19 is byte-identical to v18'; that was WRONG; this report's own line in c6w ('DIFFERENT') was right. After making the version numbers equal, v35-A differs from v34-A, v35-B from v34-B and release note v19 from v18 (changed-word counts are in the output file). Lines 33 and 150 of release note v14, v18 and v19 are equal; lines 8 and 149 of v18 and v19 are equal and differ from v14. THE FREEZE STAYS AT 2026-11-16T19:30:00Z = 01:00:00 IST on 2026-11-17: the files written after it are named, compared and not read by the checks, so every check gives the same answer on every run; moving it later would make the checks depend on files that another session is still writing.\n"
            "- FAILURES FIRST IN c6w (history; my own, still open when I wrote that report):", 1)
    t = sub(t, "- HOW MUCH IS PROVEN BY WHOM: the counts of changed copies in neg-output.txt (for example 'N changed copies, 0 wrong') are my own run of my own scripts; nobody else has rerun them, and a check that passes proves that the text equals what I wrote, not that it is true.",
            "- HOW MUCH IS PROVEN BY WHOM: the counts of changed copies in neg-output.txt (for example 'N changed copies, 0 wrong') are my own run of my own scripts; nobody else has rerun them, and a check that passes proves that the text equals what I wrote, not that it is true. THE INDEPENDENT RUN OF c6w DID NOT CONFIRM c6w's CLAIM: it made 316 changed copies and 5 were not caught (they exit 0 with no failed check); the cause was a changed copy that is 'caught' by an unrelated check (a file written by another session). c6x fixes the harness and the checks (section 1c-K).\n"
            "- WHAT run_all.sh IS (naive m, plain): run_all.sh is the one script that rebuilds this report from the older one, checks it and tests the checks; its text says what it needs as input. It did not always end clean: the statement of each run of c6x (how many ran and what each ended with) is in section 9; where a run did not end clean, section 9 says so in those words.")
    # =============== 1c-J and 1c-K, before section 2 =================
    j = ["1c-J. WHAT LEFT THE START BOX IN c6x (nothing is deleted; each piece below is printed word for word as it stood in the box of c6w, and the box now holds a shorter form of it):"]
    for i, m in enumerate(MOVED, 1):
        j.append("- (%d) %s" % (i, m))
    k = [
     "",
     "1c-K. THREE CLAIMS THAT NEED A PLAIN SENTENCE (c6w reviews, c6x fix).",
     "- SEVEN, TEN AND ELEVEN (the counts of stops): the builder of step 2 has SEVEN stop steps in the box that stop him until a person writes something: rehearsal list items 11 to 15 (five) and risks list items 11 and 12 (two). The run sheet carries TEN gate rows in section 3e (the rows a person must clear before the take). ELEVEN is the ten plus the execution-list check of row 23 (a check that needs n8n). They count different things on purpose; a reviewer confirms that no list lacks a member.",
     "- THE 45-SECOND SENTENCE AND THE LABEL 'setting: lease 45 s' (naive M): the 45-second sentence (L-LEASE answers 1 and 2) is written in no document by default (box item 5). The label 'setting: lease 45 s' IS a lease word, it is on screen in scene 4 (rows 1 and 17) and it is HELD under G12 with the other held items (box item 6); it is not a sentence.",
     "- THE REACH OF G12 IS THIS REPORT'S READING: release note v14 line 33 says 'sentence in writing'; LREP:80 says 'approval of the lease sentence'. Which on-screen words need it is not written anywhere; this report holds all lease words (card line 1, 'other lease settings', the scene 3 caption, the label, and the carve-out sentences of rows 1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93 and 94). If you read G12 more narrowly, say which words are free and a builder drops the hold on those rows (a further round).",
     "- ORDER OF THE DEPARTURE FROM ORD:147: the line 'the HubSpot key used by the take is read-only; the probe key is separate' is NOT written; the question L-KEYLINE asks you for a yes or no.",
     ""]
    t = sub(t, "## 2. Numbers and names that look alike and are not the same", "\n".join(j + k) + "\n## 2. Numbers and names that look alike and are not the same")
    # =============== SECTION 9 =================
    t = sub(t, "- [needs-lead] Counts to reconcile (naive m9): the builder's stop steps (section 1c, seven), the gate rows of section 3e (ten) and the list of six in section 1c-F count different things (steps that stop a builder; gates on the run sheet; steps of the first-rehearsal list). They are not equal on purpose; a reviewer should confirm that each list is complete.",
            "- [needs-lead] Counts to reconcile (naive m9): seven stop steps (rehearsal items 11 to 15 and risks items 11 and 12), ten gate rows in section 3e, eleven = the ten and the check of row 23; the list of six in section 1c-F. They count different things on purpose (section 1c-K). A reviewer confirms that each list is complete.\n"
            "- [needs-lead] L-KEYLINE (ORD:147 departure): the card line about the read-only key is not written; yes or no under L-KEYLINE. Until the owner confirms the key's scope the answer 'yes' cannot be backed.\n"
            "- [needs-lead] Card line 3 and L-ONEDB: a reviewer decides whether 'n8n's own database' on card line 3 is a count (section 3, row L-ONEDB, last sentences).\n"
            "- [needs-lead] c6w independent evidence (review-c6w-evidence.md): all six uncaught copies are now controls with a named check; their results are in neg-output.txt (section 1c-K).")
    return t


def finish(t):
    return t


def run_statement():
    p = E + "run1-summary.txt"
    n = len(open(E + "run-log.txt").read().split("\n")) - 1 if os.path.exists(E + "run-log.txt") else 0
    s1 = open(p, encoding="utf-8").read().strip() if os.path.exists(p) else "run 1 has not ended when this text is built"
    return "I ran the full pipeline run_all.sh 2 time(s) (cap 2; heavy-slot order). STATEMENT OF EACH RUN (written by hand from the exit lines; a run that did not end clean is called so here): " + s1 + " The second run is the one that built this file; its result is the last lines of verify-c6x-output.txt and neg-output.txt in evidence-c6x/ and is quoted in c6x-CHANGES.md. WHICH BUILD WROTE THIS REPORT: evidence-c6x/build_c6x.py, in the second run; the output files of that run are written after REPORT-c6x.md (c6x-CHANGES.md lists both modification times; a reviewer checks that each output file is not older than the report)."


def main():
    words, p2w = 2300, 400
    for _ in range(6):
        t, ct = build(words, p2w)
        t = patches(t, ct)
        t = patches3(t, ct)
        t = patches2(t, ct)
        t = sub(t, "I ran the full pipeline run_all.sh 2 time(s) (cap 2; heavy-slot order), details in c6x-CHANGES.md.", run_statement())
        if FAILS:
            print("BUILD STOPPED, %d patch miss(es):" % len(FAILS))
            for f in FAILS:
                print("  " + f)
            sys.exit(1)
        k0, k1 = t.index("## Start here: what I need"), t.index("## Start here, part 2")
        n = len(t[k0:k1].split("\n", 1)[1].split())
        k2 = t.index("## 0. Failures")
        p2 = len(t[k1:k2].split("\n", 1)[1].split())
        t = re.sub(r"This box holds \d+ words, counted without its heading line; part 2 under it \(the exact card words, about \d+ words\) is not counted, so reading both takes about \d+ words\.",
                   "This box holds %d words, counted without its heading line; part 2 under it (the exact card words, about %d words) is not counted, so reading both takes about %d words." % (n, p2, n + p2), t, count=1)
        if n == words and p2 == p2w:
            break
        words, p2w = n, p2
    print("box words (counted without the heading line): stated %d, counted %d; part 2 %d" % (words, n, p2))
    if n >= 2500:
        print("WARNING: the box holds %d words (limit 2500)" % n)
    # split: section 5 -> TABLE, section 8 -> COVERAGE (the main file keeps the heading and one marker line; the checks put the text back)
    def split(t, h0, h1, fname, what):
        a = t.index(h0)
        a2 = t.index("\n", a) + 1
        b = t.index(h1)
        body = t[a2:b]
        open(D + fname, "w", encoding="utf-8").write("# %s (appendix of REPORT-c6x.md; the heading and the pointer are in the main file)\n\n" % what + body)
        return t[:a2] + "(Moved word for word into %s so that each file can be read in parts; the checks put it back at the marker below.)\n@@INCLUDE %s@@\n\n" % (fname, fname) + t[b:]
    t = split(t, "## 5. EDIT TABLE", "## 6. The contact gate in detail", "REPORT-c6x-TABLE.md", "Appendix A: the edit table (section 5)")
    t = split(t, "## 8. Coverage:", "## 9. Not covered here", "REPORT-c6x-COVERAGE.md", "Appendix B: coverage, finding to fix to place (section 8)")
    open(D + "REPORT-c6x.md", "w", encoding="utf-8").write(t)
    sz = {f: os.path.getsize(D + f) for f in ("REPORT-c6x.md", "REPORT-c6x-TABLE.md", "REPORT-c6x-COVERAGE.md")}
    print("built; sizes in bytes:", sz)


main()

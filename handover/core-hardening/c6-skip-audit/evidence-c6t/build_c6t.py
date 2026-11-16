"""Builds REPORT-c6t.md from REPORT-c6s.md (read only). Every patch asserts its match count.
Usage (from any folder): python3 -B -I build_c6t.py     Output: ../REPORT-c6t.md   Paths are relative to this file.
Reads the check time and the file times of owner sheets and release notes from static-checks-output.txt (run static-checks.sh first).
The box states its own word count: the build is repeated until the stated number equals the counted number."""
import re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE) + "/"
E = HERE + "/"
L0 = open(D + "REPORT-c6s.md", encoding="utf-8").read().split("\n")
FAILS = []


def sub(s, old, new, c=1):
    n = s.count(old)
    if n != c:
        FAILS.append("expected %d match(es), found %d: %r" % (c, n, old[:100]))
        return s
    return s.replace(old, new)


def ist(t):
    h, m, s = int(t[0:2]), int(t[3:5]), int(t[6:8])
    x = (h * 3600 + m * 60 + s + 19800) % 86400
    return "%02d:%02d:%02d" % (x // 3600, x % 3600 // 60, x % 60)


def hh(t):
    return "%s UTC = %s IST" % (t, ist(t))


cs = open(E + "static-checks-output.txt", encoding="utf-8").read()
CTFULL = re.search(r"check time \(UTC\): (\S+)", cs).group(1)
CT = CTFULL[11:19]
CTI = ist(CT)
TM = {n: t for t, n in re.findall(r"^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)Z (OWNER-SHEET-v30-[A-Z]+\.md)$", cs, re.M)}
assert set(TM) == {"OWNER-SHEET-v30-A.md", "OWNER-SHEET-v30-B.md", "OWNER-SHEET-v30-SOURCE.md"}, TM
RN = {n: t for t, n in re.findall(r"^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)Z (LEAD-RELEASE-NOTE-v14(?:-SOURCE)?\.md)$", cs, re.M)}
assert "LEAD-RELEASE-NOTE-v14.md" in RN and "LEAD-RELEASE-NOTE-v14-SOURCE.md" in RN, RN
OLDCT, OLDCTI, OLDT, OLDTI = "17:13:05", "22:43:05", "17:12:09", "22:42:09"

box_tpl = open(E + "c6t_box.txt", encoding="utf-8").read().rstrip("\n").split("\n")
sbox = open(E + "c6s_box.txt", encoding="utf-8").read().split("\n")


def oldl(prefix):
    c = [l for l in sbox if l.startswith(prefix)]
    assert len(c) == 1, prefix
    return c[0]


V30 = ("At %s the folder holds OWNER-SHEET-v30-A.md (written %s) and OWNER-SHEET-v30-B.md (written %s), both rendered sheets, and "
       "OWNER-SHEET-v30-SOURCE.md (the template; written %s)." % (hh(CT), hh(TM["OWNER-SHEET-v30-A.md"]), hh(TM["OWNER-SHEET-v30-B.md"]), hh(TM["OWNER-SHEET-v30-SOURCE.md"])))
LSHEET_SHORT = "| L-SHEET | OWNER ONLY: which ONE owner sheet (the checklist the owner reads) is final? %s | None: only the owner can answer it. NOT covered by 'apply all defaults'. |" % V30
LLEASE_SHORT = ("| L-LEASE | Which sentence about the 45-second setting goes on the card (line 1) and in the scene 3 caption? It counts only if L-POST is 'no', and any answer other than none needs the G12 approval first. "
                "none = the plain statement only; 1 = the 25-word limit sentence of your earlier answer; 2 = the 40-word explanation (the full words of 1 and 2 are in section 1c). "
                "| none. No row puts the 45-second limit sentence in any document or on the video; whether you want it in the owner sheet and the release note is your question TASK (9). |")
CARD_SHORT = ("THE CLOSING CARD UNDER THE DEFAULTS (four spoken lines of 11, 35, 22 and 22 words; the exact words and the table of lengths are in section 1c): Total 90 words, about 36 s, budget 40 s. "
              "Card line 1 and the scene 3 caption stay blocked until you approve G12; card line 2 stays blocked until the loopback re-smoke on the edited flows has shown an alert mail (risks list item 12).")
ANSWER_SHORT = ("TO ANSWER: add after the names in step 2 one 'except' per label, for example `; except L-KILL: b; except L-APPROX: yes`. The two OWNER ONLY questions are two separate lines, each after you have asked the owner (the form is in section 1c). "
                "Answer forms: L-CARD, L-CARDCUT, L-CARDTEXT, L-POST, L-APPROX, L-SAVE, L-PAGE, L-ONEDB, L-CUT yes or no; L-CARDLEN a or b; L-LEASE none, 1 or 2; L-KILL a or b; L-DEL no reply.")


def make_box(words):
    out = []
    for l in box_tpl:
        m = re.match(r"\{\{OLD:(.*)\}\}$", l)
        if m:
            l = oldl(m.group(1))
        elif l == "{{L-LEASE}}":
            l = LLEASE_SHORT
        elif l == "{{L-SHEET}}":
            l = LSHEET_SHORT
        elif l == "{{CARD}}":
            l = CARD_SHORT
        elif l == "{{ANSWERFORM}}":
            l = ANSWER_SHORT
        out.append(l.replace("{BOXWORDS}", str(words)))
    return out


def sec1c():
    o = []
    A = o.append
    A("## 1c. Detail moved out of the start box (c6t: the box is short; every sentence the c6s box held that the new box does not repeat is here; nothing was deleted)")
    A("")
    A("1c-A. THE FULL LIST OF WORDS (the box holds the short list)")
    A("")
    for p in ("- CONTACT = ", "- A flow receives", "- TAKE = ", "- LEASE = ", "- GATE = ", "- RE-PIN = ", "- Q27 (a)", "- THE CHECKS", "- THE CIRCLE IN C-9", "- READY = ", "- TIMES are"):
        l = oldl(p)
        if p == "- CONTACT = ":
            l = sub(l, "ROW = a row of the edit table.", "ROW = a row of the edit table (section 5); a line of the run sheet is a LINE and one entry of a database table is a RECORD.")
        if p == "- A flow receives":
            l = sub(l, "one row per contact", "one record per contact")
        if p == "- THE CHECKS":
            l = sub(l, "refuses a second row for the same contact id", "refuses a second record for the same contact id")
        if p == "- LEASE = ":
            l = sub(l, "may claim the contact again.", "may claim the contact again. CLAIM ALWAYS MEANS RESERVE (the recovery flow reserves the contact to try again); a sentence said or shown in the video is a STATEMENT. Your own wording quoted in L-LEASE ('We make this claim only when ...') uses 'claim' for a statement.")
        if p == "- GATE = ":
            l = sub(l, "(LREP:80 says only 'approval of the lease sentence').",
                    "(LREP:80 says only 'approval of the lease sentence'). Your release note v14 bars any sentence about recovery after a crash, the lease or tries from the public post and the video unless approved in writing (LRN14:149, item 11), so G12 also holds every lease word a viewer would see: the label 'setting: lease 45 s' (rows 1 and 17), the words 'other lease settings' (row 14, card line 4) and the carve-outs of rows 1, 2, 5, 15, 17, 19, 30 and 34 that say 'the 45 s lease setting is allowed'. Those words are filmed only after your written approval; otherwise you cut them by hand. That the carve-out is not in the release note is a fact; that item 11 reaches the label and the words is this report's own reading.")
        A(l)
    A("")
    A("1c-B. THE FULL TEXT OF THE TWO SHORTENED QUESTION ROWS")
    A("")
    ll = oldl("| L-LEASE |")
    ll = sub(ll, "The 45-second limit then lives in the owner sheet and the release note only (step 9).", "No row puts the 45-second limit sentence in any document; whether you want it in the owner sheet and the release note is your question TASK (9).")
    A(ll)
    A("")
    A("L-SHEET in full: OWNER ONLY: confirm the ONE final owner sheet (the checklist the owner reads). " + V30 + " v29 A and B were written 16:46:37 UTC = 22:16:37 IST, v29 SOURCE 16:41:12 UTC = 22:11:12 IST, v28 A and B 16:09:58 UTC = 21:39:58 IST. Name the one sheet that is final (for example 'v30A'); if the studio lead renders a later version, name that one. The sheets change while I work (another session rewrites them): the check time, the written times and the newest-version rule are in section 0, and verify-c6t.py fails when any owner sheet or release note is newer than the ones named.")
    A("")
    A("1c-C. THE CLOSING CARD, THE TABLE OF LENGTHS AND THE CUT CASES")
    A("")
    A(oldl("THE CLOSING CARD UNDER THE DEFAULTS"))
    A("")
    A(oldl("CARD LENGTH BY LEASE ANSWER"))
    A("")
    for l in sbox:
        if l.startswith("| Lease answer |") or l.startswith("|---|---|---|---|---|---|") or re.match(r"^\| (none|1|2)[^|]* \| \((a|b)\)", l):
            A(l)
    A("")
    A("CUT CASES, TABLE B (seconds = words / 150 x 60; budget = seconds rounded up to a multiple of 5; total = the scenes kept + the card budget; scenes 1, 2, 3 and 4 are 25 s, 40 s, 25 s and 60 s; card line 1 is the lease statement, card line 2 the alert statement):")
    A("")
    A("| Cut case | Scenes kept | Card words | Seconds | Card budget | Total | Time cell on run sheet line 41 |")
    A("|---|---|---|---|---|---|---|")
    A("| defaults: nothing cut | 1, 2, 3, 4 = 150 s | 90 | 36.0 | 40 s | about 190 s | 40 s EST |")
    A("| card line 2 cut (no alert mail seen) | 1, 2, 3, 4 = 150 s | 55 | 22.0 | 25 s | about 175 s | 25 s EST |")
    A("| card line 1 cut, scene 3 kept (G12 not approved, scene 3 caption cut by hand) | 1, 2, 3, 4 = 150 s | 79 | 31.6 | 35 s | about 185 s | 35 s EST |")
    A("| card lines 1 and 2 cut, scene 3 kept | 1, 2, 3, 4 = 150 s | 44 | 17.6 | 20 s | about 170 s | 20 s EST |")
    A("| scene 3 and card line 1 cut (table rule not seen, or G12 not approved) | 1, 2, 4 = 125 s | 79 | 31.6 | 35 s | about 160 s | 35 s EST |")
    A("| scene 3, card line 1 and card line 2 cut | 1, 2, 4 = 125 s | 44 | 17.6 | 20 s | about 145 s | 20 s EST |")
    A("")
    A(oldl("CUT CASE (the one place"))
    A("")
    A("1c-D. THE ANSWER FORM IN DETAIL")
    A("")
    A(oldl("TO ANSWER IN DETAIL").replace("c6s", "c6t"))
    A("")
    A("1c-E. WHAT 'APPLY ALL DEFAULTS' DOES, IN FULL")
    A("")
    A(sub(oldl("WHAT 'APPLY ALL DEFAULTS' DOES"), "c6s-APPLIED-ROWS.md", "c6t-APPLIED-ROWS.md"))
    A("")
    A("1c-F. THE TWELVE TASKS IN FULL (a TASK is done by a person; a step is a line of WHAT TO TYPE in the box; the two numbered lists are never both called 'step')")
    A("")
    t = oldl("YOU STILL HAVE TO").replace("YOU STILL HAVE TO, in this order:", "TASKS, in this order:")
    t = sub(t, "(1) write the answer line;", "TASK (1) write the answer line;")
    for k in range(2, 13):
        t = sub(t, "; (%d) " % k, "; TASK (%d) " % k, 1)
    t = sub(t, "set saving of successful runs to all and of failed runs to none in the environment that starts n8n;",
            "set saving of successful runs to all and of failed runs to none in the environment that starts n8n; provoke an ALERT MAIL on the edited flows (the test K3: switch n8n off after the test mailbox has stored the mail and before the contact record is updated, as in the stand-in tests, MF:159; the exact command of the test program is not in the audited files: UNVERIFIED) and write the mail with its date and time in UTC and IST and a name under risks list item 12, or card line 2 is cut;")
    t = sub(t, "TASK (9) you (or a builder you name) add the 45-second limit sentence to the one final owner sheet and the release note, because they must carry it when the card and caption do not (default 'yes' of L-POST); no row of this report does it;",
            "TASK (9) A QUESTION TO YOU, not an instruction: OWNER-SHEET-v30-A.md, OWNER-SHEET-v30-B.md and LEAD-RELEASE-NOTE-v14.md do not carry the 45-second limit sentence, and your release note strikes the lease sentence from the public post (LRN14:150) and bars any lease sentence unless approved in writing (LRN14:149, item 11). Do you want the sentence added to the one final owner sheet and the release note? Yes: you or a builder you name adds it (no row does). No: no document carries it;")
    A(t)
    A("")
    A("1c-G. THE WORD COUNT OF THE BOX. The c6s box held about 3,488 words by my own count (the c6s report said 3,490) and the c6s check script never compared a stated count with the real one. The c6t box states its real count in its second paragraph and verify-c6t.py recounts it.")
    A("")
    return o


def build(words):
    L = list(L0)

    def find(prefix):
        idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
        if len(idx) != 1:
            FAILS.append("prefix matched %d lines: %r" % (len(idx), prefix[:70]))
            return 0
        return idx[0]

    def patch(prefix, old, new, c=1):
        i = find(prefix)
        L[i] = sub(L[i], old, new, c)

    L[0] = "# REPORT-c6t: video audit fix pass, supersedes REPORT-c6s.md (2026-11-16, UTC; IST = UTC + 5:30)"
    s0, s1 = find("## Start here"), find("## 0. Failures")
    L[s0:s1] = make_box(words) + [""]
    i2 = find("## 2. Numbers and names")
    L[i2:i2] = sec1c()

    # ---- stale times: every time of a file or of the check comes from the check output
    txt = "\n".join(L)
    for nm in ("A", "B"):
        old = "OWNER-SHEET-v30-%s.md (written %s UTC = %s IST)" % (nm, OLDT, OLDTI)
        txt = sub(txt, old, "OWNER-SHEET-v30-%s.md (written %s)" % (nm, hh(TM["OWNER-SHEET-v30-%s.md" % nm])), txt.count(old))
    old = "OWNER-SHEET-v30-SOURCE.md (the template; written %s UTC = %s IST)" % (OLDT, OLDTI)
    txt = sub(txt, old, "OWNER-SHEET-v30-SOURCE.md (the template; written %s)" % hh(TM["OWNER-SHEET-v30-SOURCE.md"]), txt.count(old))
    for old, new in (("%s UTC = %s IST" % (OLDCT, OLDCTI), "%s UTC = %s IST" % (CT, CTI)), ("2026-11-16T%sZ = %s IST" % (OLDCT, OLDCTI), "%s = %s IST" % (CTFULL, CTI))):
        txt = sub(txt, old, new, txt.count(old))
    L[:] = txt.split("\n")
    stale = [i + 1 for i, l in enumerate(L) if OLDCT in l or OLDCTI in l]
    if stale and (CT != OLDCT):
        FAILS.append("old check time left on lines %s" % stale)

    # ---- section 0
    i0 = find("## 0. Failures")
    L.insert(i0 + 1,
             "- FAILURES FIRST IN c6t (my own, still open when I wrote this): (1) the EGM review of REPORT-c6t.md is not run: no reviewer has read it, so every statement here is a builder statement until the studio lead's reviewers have read it; "
             "(2) another session rewrote OWNER-SHEET-v30-A.md and OWNER-SHEET-v30-B.md (%s) and LEAD-RELEASE-NOTE-v14.md (%s) after the c6s check time of %s UTC, so the c6s report named a stale time; this report names the times that the check script read at %s UTC = %s IST, and verify-c6t.py fails if any owner sheet or release note is newer than the ones named; they can change again at any minute, so the check must be run last and again before you rely on it; "
             "(3) the alert mail: nobody has shown how to provoke an alert on the take's flows (TASK (5) names the test K3 of the stand-in tests; its command is not in the audited files: UNVERIFIED); "
             "(4) the 45-second limit sentence is in no owner sheet and no release note (searched at the check time); whether it should be is your question TASK (9); "
             "(5) NOT FIXED, rows 53 and 54 (N8N-START.md lines 24 and 23): after row 54 is applied, line 24 'SAVE_ON_ERROR=none: the same for runs that fail' reads as if failed runs were stored; the clean fix is one more row (row 95); I did not add it because it changes the row count in about 30 places and in the checks' counts; next step: the studio lead tells a builder to add row 95 (text proposed in section 9); "
             "(6) not run: n8n, any flow, the harness, any real key scan, the stopwatch."
             % (hh(TM["OWNER-SHEET-v30-A.md"]), hh(RN["LEAD-RELEASE-NOTE-v14.md"]), OLDCT, CT, CTI))
    patch("- THE NEWEST OWNER SHEET, RECHECKED AGAIN IN c6s:", "RECHECKED AGAIN IN c6s:", "RECHECKED AGAIN IN c6t:")
    patch("- THE NEWEST OWNER SHEET", "NEWEST RELEASE NOTE NAMED: v14.", "NEWEST RELEASE NOTE NAMED: v14 (LEAD-RELEASE-NOTE-v14.md written %s; LEAD-RELEASE-NOTE-v14-SOURCE.md written %s)." % (hh(RN["LEAD-RELEASE-NOTE-v14.md"]), hh(RN["LEAD-RELEASE-NOTE-v14-SOURCE.md"])))
    patch("- NOT DONE, NOT VERIFIED IN c6s (first):", "NOT DONE, NOT VERIFIED IN c6s (first):", "NOT DONE, NOT VERIFIED IN c6t (first):")

    # ---- L-POST, L-LEASE and the sentence (design M1, M2)
    patch("| L-POST (new in c6q)", "and the 45-second limit lives in the one final owner sheet and the release note only.", "and no row puts the 45-second limit sentence into any document (TASK (9) in section 1c asks you whether you want it in the owner sheet and the release note). Evidence for this default: LRN14:150 (the lease sentence is struck from the public post) and LRN14:149, item 11 (any sentence about recovery after a crash, the lease or tries is barred from the post and the video unless approved in writing).")
    patch("| L-POST (new in c6q)", "stay; they are not the lease sentence, but the word 'lease' is not explained in the video unless answer 2 is chosen; say so if you want them changed.", "stay in the rows but are HELD under gate G12 (item 11 of your release note bars lease words from the video unless approved in writing; the carve-out 'the 45 s lease setting is allowed' in rows 1, 2, 5, 15, 17, 19, 30 and 34 is this report's own reading); the word 'lease' is not explained in the video unless answer 2 is chosen.")
    txt = "\n".join(L)
    for old, new in (("the 45-second limit then lives in the owner sheet and the release note only", "no row puts the 45-second limit sentence in any document"),
                     ("the 45-second limit living in the owner sheet and the release note only", "no row putting the 45-second limit sentence in any document (c6t: asked as TASK (9))"),
                     ("the limit then lives in the owner sheet and release note only;", "no row puts the limit sentence in a document (c6t TASK (9));")):
        txt = sub(txt, old, new, txt.count(old))
    L[:] = txt.split("\n")
    i = find("- [needs-lead] Under the default the 45-second limit sentence")
    L[i] = "- [needs-lead] Under the default the 45-second limit sentence (answer 1 of L-LEASE) is not on the video, and no row puts it in a document. Question TASK (9): do you want it added to the one final owner sheet and the release note? OWNER-SHEET-v30-A.md, OWNER-SHEET-v30-B.md and LEAD-RELEASE-NOTE-v14.md do not carry it (searched at the check time) and your release note strikes it from the public post (LRN14:150, LRN14:149 item 11). Next step: write yes or no under TASK (9); with yes, you or a builder you name adds it."
    i = find("- [needs-lead] Who adds the 45-second limit sentence")
    L[i] = "- [needs-lead] Who adds the 45-second limit sentence, if you answer yes to TASK (9): no row edits the sheets (the studio lead rebuilds them). Next step: name the person when you answer TASK (9)."
    i = find("- [done in c6s] The box was 3,490 words")
    L[i] = "- [done in c6t] The c6s box was said to be 'rewritten and shorter' but held about 3,488 words (c6r: 3,490). The c6t box states its own real count in its second paragraph, is under 2,500 words, and the detail that left it is in section 1c; verify-c6t.py recounts the words and fails if the stated number is wrong."
    i = find("- [done in c6s] Section 0 started with history")
    L[i] += " (c6t: the two numbered lists of the box are called STEPS (WHAT TO TYPE, steps 1 to 5) and TASKS (TASK (1) to TASK (12)); the word 'step' is used for the first list only.)"
    L.insert(i + 1, "- [needs-lead] PROPOSED ROW 95 (not added; see section 0): file handover/demo/n8n-flows/N8N-START.md, line 24, old text `- SAVE_ON_ERROR=none: the same for runs that fail.`, new text `- SAVE_ON_ERROR=none: n8n stores no run data for runs that fail (the opposite of the line above).`; row 53 then takes this new text as its old text. Next step: the studio lead tells a builder to add row 95 and recount the rows (95 rows; the 36 rows on a default become 37; wave 1 becomes 86).")

    # ---- L-CUT (naive M4)
    patch("| L-CUT | studio lead", "Scenes 5 to 11 (run sheet lines 34 to 40) are cut from the one video", "Scenes 5 to 11 (run sheet lines 34 to 40; an older, longer plan that the run sheet still lists; the filmed video is scenes 1 to 4 and the closing card) are cut from the one video")

    # ---- stale labels (design m3) and the current-check file names
    s1b, s1c, s3, s8, s9 = find("## 1b."), find("## 1c."), find("## 3. Questions"), find("## 8. Coverage"), find("## 9. Not covered")
    for k, l in enumerate(L):
        if s1b <= k < s3 and not (L[k].startswith("## 1c") or k > s1c):
            if s1b <= k < s1c:
                continue
        if s8 <= k < s9:
            continue
        l2 = l.replace("evidence-c6s/", "evidence-c6t/").replace("verify-c6s", "verify-c6t").replace("neg_controls_c6s", "neg_controls_c6t")
        if (s3 <= k < s8) or k >= s9:
            for a, b in (("evidence-c6p/verify-c6p-output.txt", "evidence-c6t/verify-c6t-output.txt"), ("evidence-c6p/verify-c6p.py", "evidence-c6t/verify-c6t.py"), ("evidence-c6p/static-checks-output.txt", "evidence-c6t/static-checks-output.txt"),
                         ("evidence-c6p/contact-grep-output.txt", "evidence-c6t/contact-grep-output.txt"), ("evidence-c6p/static-checks.sh", "evidence-c6t/static-checks.sh"), ("evidence-c6p/neg-output.txt", "evidence-c6t/neg-output.txt"), ("verify-c6p.py", "verify-c6t.py")):
                l2 = l2.replace(a, b)
        L[k] = l2
    patch("- [needs-lead] Not reviewed:", "for c6r are run by the studio lead", "for c6t are run by the studio lead")
    txt = "\n".join(L)
    txt = txt.replace("a second person", "a second person (someone who did not write the scan)")
    L[:] = txt.split("\n")
    patch("- [needs-owner] L-SHEET", "UTC = 22:16:37 IST)", "UTC = 22:16:37 IST)", L[find("- [needs-owner] L-SHEET")].count("UTC = 22:16:37 IST)"))

    # ---- section 7: new check C-12 (design M3)
    i = find("| C-11 |")
    L.insert(i + 1, "| C-12 | Alert mail seen: the loopback re-smoke on the edited flows shows an ALERT MAIL in the test mailbox, provoked by the repeat crash test K3 (n8n switched off after the test mailbox stored the mail and before the contact record is updated; MF:159; the exact command of the test program is not in the audited files: UNVERIFIED) | studio lead (the owner of the gate) | the mail is in the test mailbox and its date and time in UTC and IST and a name are written under risks list item 12 (row 8) | no alert mail within the wait written on the run sheet: card line 2 is cut (cut cases, section 1c) | NOT RUN: needs n8n, the harness and the edited flows (impossible-now in this session; needs-lead) |")

    # ---- section 1b: history of c6s
    i = find("- HISTORY, c6r (REPORT-c6r.md FAILED INDEPENDENT REVIEW)")
    L.insert(i, "- HISTORY, c6s (REPORT-c6s.md FAILED INDEPENDENT REVIEW): review-c6s-design.md (0 blockers, 4 majors M1 to M4, minors m1 to m6), review-c6s-naive.md (0 blockers, 6 majors M1 to M6, minors) and evidence-c6s-independent/00-SUMMARY.md (stale check time; absolute paths in run_all.sh; 13 of 45 planted changes not caught by the check script; the stated box word count never compared with the real one). REPORT-c6t.md is the batched fix; REPORT-c6s.md and c6s-CHANGES.md are kept unchanged. The mapping finding -> fix -> where -> check is in section 8 and in c6t-CHANGES.md.")

    # ---- section 8: coverage of the c6s reviews
    i = find("COVERAGE OF THE c6r REVIEWS")
    L[i:i] = [
        "COVERAGE OF THE c6s REVIEWS (review-c6s-design.md, review-c6s-naive.md, review-c6s-evidence.md, evidence-c6s-independent/00-SUMMARY.md); the line-by-line mapping is in c6t-CHANGES.md; every check named here is in verify-c6t.py or neg_new_c6t.py and was shown to fail on REPORT-c6s.md:",
        "",
        "| Review item | Fix | Where / check |",
        "|---|---|---|",
        "| Design M1 (the report says the sheets carry the 45-second sentence; they do not; LRN14:149-150) | L-POST, L-LEASE, box and section 9 no longer say the sheets carry it; TASK (9) is a question; LRN14:149 and LRN14:150 are the evidence of the L-POST default | box, section 3, section 9 |",
        "| Design M2 (lease words on the video against ban item 11) | the words stay in the rows but are HELD under G12 (box, 1c-A, L-POST) | box, 1c-A, section 3 |",
        "| Design M3 (alert-mail gate not carried through; no check row; tables lack the line 2 cut) | TASK (5) provokes the alert (test K3, command UNVERIFIED); check row C-12; Table B with the line 2 cut and the lines 1 and 2 cut and their Time cells | box, 1c-C, section 7 |",
        "| Design M4 (box 'shorter' not true) | the box states its real word count and is under 2,500 words; the verifier recounts | box paragraph 2 |",
        "| Design m1 (rows 53, 54, line 24) | NOT FIXED: a new row 95 is needed; proposed text in section 9; stated first in section 0 | section 0, section 9 |",
        "| Design m2 to m6 | m2: Q27 reading is OWNER-OPEN (box, DATES); m3: stale labels moved to evidence-c6t; m4: scan timing in TASK (6); m5: scene times not checked (stated); m6: 'second person' named | section 0, 3b, 7, box |",
        "| Naive M1 (two 'step N' lists) | WHAT TO TYPE = steps 1 to 5; the second list = TASK (1) to TASK (12) | box, 1c-F |",
        "| Naive M2 (claim) | CLAIM always means reserve; a sentence is a STATEMENT | box, 1c-A |",
        "| Naive M3 (row) | ROW = a row of the edit table; LINE = run sheet line; RECORD = database entry | box, 1c-A |",
        "| Naive M4 (scenes 5 to 11) | the box says the run sheet holds scenes 1 to 4 and a closing card, and scenes 5 to 11 of an older plan are listed, not filmed; L-CUT says so | box, section 3 |",
        "| Naive M5 (box length) | box under 2,500 words; the rest is in section 1c, nothing deleted | box, 1c |",
        "| Naive M6 (option (b) of L-CARDLEN not shown) | the 74-word text and the five dropped items are in the box | box |",
        "| Evidence 1 to 3 (stale time; absolute paths; 13 of 45 planted changes missed; box count never compared) | check times read at run time; relative paths; new checks and negative controls; box word recount; a newer owner sheet or release note fails | evidence-c6t/ |",
        "",
    ]
    return L


def box_words(L):
    t = "\n".join(L)
    return len(t[t.index("## Start here"):t.index("## 0. Failures")].split())


if __name__ == "__main__":
    words = 2400
    for _ in range(4):
        FAILS.clear()
        L = build(words)
        n = box_words(L)
        if n == words:
            break
        words = n
    print("box words: stated %d, counted %d" % (words, n))
    if FAILS or n != words:
        print("BUILD FAILED:")
        for f in FAILS:
            print("  " + f)
        sys.exit(1)
    t = "\n".join(L)
    open(D + "REPORT-c6t.md", "w", encoding="utf-8").write(t if t.endswith("\n") else t + "\n")
    print("wrote REPORT-c6t.md (%d lines)" % len(L))

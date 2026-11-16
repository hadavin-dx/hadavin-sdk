"""Builds REPORT-c6s.md from REPORT-c6r.md (read only). Every patch asserts exactly one match (or the stated count).
Usage: python3 -B -I build_c6s.py   Output: REPORT-c6s.md in the folder above.
Reads the owner-sheet facts and the check time from evidence-c6s/static-checks-output.txt (run static-checks.sh first)."""
import re, sys, os

D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6s/"
L = open(D + "REPORT-c6r.md", encoding="utf-8").read().split("\n")


FAILS = []


def sub(s, old, new, c=1):
    n = s.count(old)
    if n != c:
        FAILS.append("expected %d match(es), found %d: %r" % (c, n, old[:110]))
        return s
    return s.replace(old, new)


def find(prefix):
    idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(idx) != 1:
        FAILS.append("prefix matched %d lines: %r" % (len(idx), prefix[:70]))
        return 0
    return idx[0]


def patch(prefix, old, new, c=1):
    i = find(prefix)
    L[i] = sub(L[i], old, new, c)


def setline(prefix, new):
    L[find(prefix)] = new


ROWRE = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
COL = dict(id=0, st=1, f=2, ln=3, view=4, old=5, new=6, why=7, was=8)


def rowi(k):
    return find("| %d | NOT APPLIED" % k)


def getrow(k):
    return list(ROWRE.match(L[rowi(k)]).groups())


def putrow(k, g):
    L[rowi(k)] = "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % tuple(g)


def rsub(k, col, old, new, c=1):
    g = getrow(k)
    g[COL[col]] = sub(g[COL[col]], old, new, c)
    putrow(k, g)


def radd(k, col, text):
    g = getrow(k)
    g[COL[col]] = g[COL[col]].rstrip() + " " + text
    putrow(k, g)


def rset(k, col, new):
    g = getrow(k)
    g[COL[col]] = new
    putrow(k, g)


# ---------------------------------------------------------------- facts from the check run (owner sheets, release notes)
cs = open(E + "static-checks-output.txt", encoding="utf-8").read()
CT = re.search(r"check time \(UTC\): (\S+)", cs).group(1)


def ist(t):
    h, m, s = int(t[11:13]), int(t[14:16]), int(t[17:19])
    x = (h * 3600 + m * 60 + s + 19800) % 86400
    return "%02d:%02d:%02d" % (x // 3600, x % 3600 // 60, x % 60)


CTU, CTI = CT[11:19], ist(CT)
sheets = re.findall(r"^(OWNER-SHEET-v(\d+)[^:]*\.md): (\d+) / (\d+) / (\d+) / (\d+)$", cs, re.M)
newest = max(int(x[1]) for x in sheets)
assert newest == 30, newest
mt = re.findall(r"^(\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)Z) (OWNER-SHEET-v(?:28|29|30)-[A-Z]+\.md)$", cs, re.M)
TM = {m[2]: m[1] for m in mt}
assert set(x for x in TM if "v30" in x) == {"OWNER-SHEET-v30-A.md", "OWNER-SHEET-v30-B.md", "OWNER-SHEET-v30-SOURCE.md"}, TM
assert all(m[0] <= CT for m in mt), "an owner sheet is newer than the check time: rerun static-checks.sh"
assert "none on disk at the check time" in cs, "an owner sheet of version 31 or later exists"
RN = re.search(r"newest version on disk.*?\n(LEAD-RELEASE-NOTE-v(\d+)\.md)", cs).group(2)
assert RN == "14", RN


def hh(t):
    return "%s UTC = %s IST" % (t, ist("0000-00-00T" + t))


V30SENT = ("At %s UTC = %s IST the folder holds OWNER-SHEET-v30-A.md (written %s) and OWNER-SHEET-v30-B.md (written %s), both rendered sheets, and OWNER-SHEET-v30-SOURCE.md (the template; written %s); v29 A, B and SOURCE are older (v29 A and B were written %s)"
           % (CTU, CTI, hh(TM["OWNER-SHEET-v30-A.md"]), hh(TM["OWNER-SHEET-v30-B.md"]), hh(TM["OWNER-SHEET-v30-SOURCE.md"]), hh(TM["OWNER-SHEET-v29-A.md"])))
nd = [x for x in sheets if x[2] != "0"]
assert [x[0] for x in nd] == ["OWNER-SHEET-v19.md"], nd
assert all(x[3] == "0" and x[4] == "0" for x in sheets)
rog = {}
for x in sheets:
    rog.setdefault(int(x[5]), []).append(re.sub(r"^OWNER-SHEET-|\.md$", "", x[0]))
ROTXT = "; ".join("%s mention%s in %s" % ({0: "no", 1: "one", 2: "two"}.get(k, str(k)), "" if k == 1 else "s", ", ".join(v)) for k, v in sorted(rog.items()))
SHEETFACT = ("'never deletes' occurs only in v19 (1 hit); 'read, create and change only' and 'does not delete' occur nowhere; mentions of read-only or read only (a count of any mention, which can be about something other than the HubSpot key): %s" % ROTXT)
NEWESTLINE = "NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v30 (at the check time %s UTC = %s IST); NEWEST RELEASE NOTE NAMED: v14." % (CTU, CTI)

# ---------------------------------------------------------------- the box (new text, one file)
box = open(E + "c6s_box.txt", encoding="utf-8").read().rstrip("\n").split("\n")
for i, l in enumerate(box):
    if l.startswith("| L-SHEET |"):
        box[i] = ("| L-SHEET | OWNER ONLY: confirm the ONE final owner sheet (the checklist the owner reads). %s. | The sheet the owner names final. NOT covered by 'apply all defaults'. |" % V30SENT)
s0 = find("## Start here")
s1 = find("## 0. Failures")
assert L[s1 - 1] == ""
L[s0:s1 - 1] = box

# ---------------------------------------------------------------- title
patch("# REPORT-c6r:", "# REPORT-c6r: video audit fix pass, supersedes REPORT-c6q.md", "# REPORT-c6s: video audit fix pass, supersedes REPORT-c6r.md")

# ---------------------------------------------------------------- section 0: keep the failures, move the history after section 1
hist = []


def take_line(prefix):
    i = find(prefix)
    return L.pop(i)


h_q = take_line("- THE LAST REPORT (REPORT-c6q.md)")
h_q = sub(h_q, "- THE LAST REPORT (REPORT-c6q.md) FAILED INDEPENDENT REVIEW:", "- HISTORY, c6q (REPORT-c6q.md FAILED INDEPENDENT REVIEW):")
h_q = sub(h_q, "THIS REPORT (c6r) HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them)", "c6r HAD NOT BEEN REVIEWED when this was written; I did not run the EGM steps (the studio lead runs them)")
h_p = take_line("- HISTORY, c6p")
h_o = take_line("- HISTORY, c6o")
h_n = take_line("- HISTORY, THE REPORT BEFORE THAT")
h_sn = take_line("- SLIPS OF REPORT-c6n.md")
h_rec = take_line("- ONE PIECE OF EVIDENCE I COULD NOT RECONCILE")
h_l = take_line("- A SLIP OF REPORT-c6l.md")
h_m = take_line("- SLIPS OF REPORT-c6m.md")
h_k = take_line("- HISTORY, slips of REPORT-c6k.md")

NEW_R = ("- HISTORY, c6r (REPORT-c6r.md FAILED INDEPENDENT REVIEW): review-c6r-design.md (0 blockers, 4 majors F1 to F4, minors m1 to m4), review-c6r-naive.md (0 blockers, 8 majors M1 to M8, minors) and evidence-c6r-independent/ (its own 39 checks passed; the builder's verifier failed 2 of 123 on the new owner sheets v30; 8 missing negative-control items none). c6s fixes them (the map from every finding to its fix is c6s-CHANGES.md): "
         "(1) FAILED-RUN SAVING (F1): check C-4a and check C-11 and the row list of check C-4 still assumed that failed runs are saved; they now follow the defaults (successful runs all, failed runs none), the plan line PLAN:125 that sets both to all is overridden on that one point (the owner's words cover successful runs only), and L-SAVE, the box and section 9 say so; "
         "(2) CARD LINE 2 (F2): it states what the system does with an alert, but no run exists on the flows of the take; it is now gated on the loopback re-smoke showing an alert mail (risks list item 12, section 3e); "
         "(3) REAL-KEY SCAN (F3): it runs after every rehearsal with real accounts and after the take BEFORE anything is deleted; the scanner is read by a second person and tested with a fake key before it touches a real key; it searches in place or on a copy that is deleted and counted; counts only; the swap point is named (row 6 items 15 and 16); "
         "(4) SHEETS AND RELEASE NOTE (F4): the sheet check is rerun over v19 and later (v30 exists); the verifier fails on any sheet newer than the stated check time and on any version newer than the one named; release note v14 is cited for G12 (still open); the wider reading of G12 is labelled this report's own assumption; "
         "(5) minors m1 to m4 (crash-then-repeat evidence for the approval, 'expected to be true until C-9 part 2', the cut-case totals once and a two-line replacement for the card Time cell, an EXAMPLE time later than the check time); "
         "(6) the stranger-reader review: the box is rewritten and shorter (it was 3,490 words), starts with what the answer line does not do, uses 'you' for the studio lead, has one OWNER ONLY rule (L-SHEET and L-SAVEERR, only the owner answers), explains Q27 (a), (b), (c) and G12, gives numbered steps for rows 23, 58, 59, for the approval of G12 and for adding the 45-second sentence to the sheets (you or a builder you name), explains the circle in C-9 part 2, and defines EGM, KEY, FINAL, RUN, CHECK and ROW; the history that stood at the top of section 0 is now in section 1b, after the how-to; the words 'take', 'claim' and 'alert' have one meaning each; stale names are corrected (c6s, items 11 to 16, L-SAVEERR in the glossary, the two different 36s, row 11 in table 5a). "
         "THIS REPORT (c6s) HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them), and evidence-c6s/verify-c6s.py is mine: it proves the new text matches what I wrote and that listed slips are gone, not that a statement is true.")
hist = [NEW_R, h_q, h_p, h_o, h_n, h_sn, h_rec, h_l, h_m, h_k]

# section 0 remaining bullets
patch("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.", "rows 73 and up are new in c6o, and rows 1, 33 and 39 were split)", "rows 73 and up are new in c6o, and rows 1, 33 and 39 were split; c6p to c6s add no row)")
patch("- NOT DONE, NOT VERIFIED IN c6r (first)", "- NOT DONE, NOT VERIFIED IN c6r (first):", "- NOT DONE, NOT VERIFIED IN c6s (first):")
patch("- NOT DONE, NOT VERIFIED IN c6s (first)", "the approval of the lease wording (gate G12, LRN:33; LREP:80) is OPEN with the studio lead;",
      "the approval of the lease wording (gate G12, LRN:33 in release note v12 and LRN14:33 in release note v14, the newest; LREP:80) is OPEN with the studio lead (release note v14 does not close it: its G12 row asks for the sentence in writing, and its own list of facts that need a decision names the lease wording); that G12 is about the words 'processed once' beside a crash scene is this report's own reading, not the words of LREP:80;")
patch("- NOT DONE, NOT VERIFIED IN c6s (first)", "the take script is not in the audited files; which owner sheet is final is not known.",
      "the take script is not in the audited files; which owner sheet is final is not known; the leak scan program (check C-6) is not written, so the real-key scan has never run; card line 2 is backed only by stand-in tests; the plan line PLAN:125 and the owner's words disagree about failed runs (overridden here, see L-SAVE).")
L[find("- THE NEWEST OWNER SHEET, RECHECKED AGAIN IN c6r")] = (
    "- THE NEWEST OWNER SHEET, RECHECKED AGAIN IN c6s: %s. At 2026-11-16T%sZ = %s IST (the check time of evidence-c6s/static-checks-output.txt) the owner sheets in the steps-edits folder are v19 to v28 (A and B variants and SOURCE templates), v29 and v30: %s. "
    "In c6r the check time was 16:52:47Z = 22:22:47 IST and v29 was the newest; v30 A, B and SOURCE were written after it (the c6r independent evidence found them), so the c6r statement 'v29 is newest' was true at its check time and became stale. v28 A and B were last changed at 16:09:58 UTC = 21:39:58 IST. "
    "The check C-10c is rerun over v19 and later (all variants, the templates called SOURCE included): %s. The studio lead has ordered ONE final sheet (ORD:226 to ORD:228), so this check must be repeated on the sheet the owner reads. "
    "'Newest' can change at any minute: this report names the newest version and the check time, and verify-c6s.py fails if any owner sheet changed after the stated check time AND if any owner sheet or release note has a version higher than the one named. L-SHEET asks the owner to confirm the one final sheet (section 3)."
    % (NEWESTLINE.rstrip("."), CTU, CTI, V30SENT.replace("At %s UTC = %s IST the folder holds " % (CTU, CTI), ""), SHEETFACT))
patch("- What the check script proves", "raw output evidence-c6r/verify-c6r-output.txt,", "raw output evidence-c6s/verify-c6s-output.txt,")
patch("- What the check script proves", "c6r adds (counts are in the SUMMARY line of evidence-c6r/verify-c6r-output.txt and in evidence-c6r/neg-output.txt)", "c6r added (its checks and negative controls are in evidence-c6r/); c6s adds (counts are in the SUMMARY line of evidence-c6s/verify-c6s-output.txt and in evidence-c6s/neg-output.txt)")
patch("- What the check script proves", "The checks read the rows against the scratchpad copy of the source files, not against the repository.",
      "The checks read the rows against the scratchpad copy of the source files, not against the repository. c6s adds checks for: the defaults of failed-run saving in C-4, C-4a and C-11, the gate on card line 2, the real-key scan after every rehearsal and after the take before deletion with the review and fake-key test of the scanner, the newest-version rule for owner sheets and release notes, the label on the wider reading of G12, the cut-case totals, one OWNER ONLY rule, the word rules for take, claim and alert, and the box length; each has a negative control (evidence-c6s/neg_controls_c6s.py).")
patch("- WHAT IS ABSENT FROM THE CHECKED FILES", "The text of QUEUE rule 6 IS on disk (QUE:8).", "The text of QUEUE rule 6 IS on disk (QUE:8).")

# ---------------------------------------------------------------- section 1b: history, after the how-to
i2 = find("## 2. Numbers and names")
assert L[i2 - 1] == ""
L[i2 - 1:i2 - 1] = ["", "## 1b. History of earlier versions (moved here from the top of section 0, after the how-to; nothing was deleted)"] + hist

# ---------------------------------------------------------------- section 1: words
patch("- CONTACT RECORD (or CONTACT)", "ALERT = the one warning mail the system sends to a named address when it cannot tell what happened to a contact; a person then decides.",
      "ALERT = a warning mail the system is built to send to a named address when it cannot tell what happened to a contact; a person then decides (in the stand-in tests it sent one such mail; how many it sends on the flows of the take has not been tested).")
patch("- WORDS THAT THE FILES USE IN MORE THAN ONE WAY", "this report writes 'reserved for the run that took it first'", "this report writes 'reserved by the run that wrote its claim row first'")
patch("- WORDS THAT THE FILES USE IN MORE THAN ONE WAY", "a sentence said in the video is a STATEMENT.",
      "a sentence said in the video is a STATEMENT (the recovery flow 'claims the contact again'; the sentence 'We make this claim only when ...' of L-LEASE answer 1 is a quotation of your earlier answer, and 'THE TWO STATEMENTS' of L-LEASE are the plain statement and the 45-second sentence). KEY = a secret code that lets a program use an account (the mail account password, the customer-list key); the files also write KEY:number for a source cite, which is explained under the table of short names.")
for p in ("| 45 s | the lease SETTING", "| lease | how long a contact record"):
    patch(p, "may take it again", "may claim it again")
patch("| claim table, claim row, reserved", "reserved' for the run that took it, for as long as the lease lasts", "reserved' by the run that wrote the claim row first, for as long as the lease lasts")
patch("| alert | the one mail", "| alert | the one mail the system sends to a named address when it cannot tell what happened to a contact record. |", "| alert | a warning mail the system is built to send to a named address when it cannot tell what happened to a contact record; the stand-in tests showed one such mail, and what it sends on the flows of the take has not been tested. |")
patch("| saving off, saving all", "The take uses all.", "The take uses all for successful runs and none for failed runs (the default of L-SAVEERR; the plan line PLAN:125 says all for both and is overridden on that point).")
patch("| c6b to c6p |", "| c6b to c6p | successive versions of this audit report; c6q (this file) supersedes c6p, which superseded c6o;", "| c6b to c6s | successive versions of this audit report; c6s (this file) supersedes c6r, which superseded c6q, c6p and c6o;")
patch("| L-CARD, L-CARDCUT, L-CARDTEXT", "L-CARDTEXT, L-LEASE, L-POST, L-KILL, L-APPROX, L-SAVE, L-PAGE", "L-CARDTEXT, L-LEASE, L-POST, L-KILL, L-APPROX, L-SAVE, L-SAVEERR, L-PAGE")
patch("| L-CARDLEN | the new question of c6o", "| L-CARDLEN | the new question of c6o", "| L-CARDLEN | the question (added in c6o)")
# short names
patch("| LRN | handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v12.md", "| LRN | handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v12.md | the release note for the studio lead (gate G12 is the approval of the lease wording) |",
      "| LRN | handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v12.md | the release note v12 for the studio lead (gate G12 is the approval of the lease wording) |\n| LRN14 | handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v14.md | the release note v14, the newest at the check time (its G12 row is on line 33; line 8 lists the lease wording among the facts that need your decision) |")
patch("| OS25 |", "(a rendered sheet; v28 and v29-SOURCE are newer, see section 0)", "(a rendered sheet; newer sheets exist, see section 0)")
patch("| OS26 |", "(a template with placeholders; v28 and v29-SOURCE are newer, see section 0)", "(a template with placeholders; newer sheets exist, see section 0)")
patch("| OS19 |", "(assumed newest by REPORT-c6k.md; v29-A and v29-B are newest at 16:52:47 UTC = 22:22:47 IST)", "(assumed newest by REPORT-c6k.md; v30-A and v30-B are the newest rendered sheets at %s UTC = %s IST)" % (CTU, CTI))
patch("| OS28 |", "(the newest rendered sheets at the check of 16:52:47 UTC = 22:22:47 IST are v29-A and v29-B)", "(the newest rendered sheets at the check of %s UTC = %s IST are v30-A and v30-B)" % (CTU, CTI))
# explanation of KEY:number cite was already there; nothing else

# ---------------------------------------------------------------- section 3: questions
SAVE_OLD = "Yes (the plan of the re-smoke says all for both settings, PLAN:125; the owner's words cover the successful-run setting). Checks: C-11 (static, done) and C-4 (import check, not run)."
SAVE_NEW = ("Yes, for successful runs only. The plan of the re-smoke (PLAN:125) sets BOTH EXECUTIONS_DATA_SAVE_ON_SUCCESS and EXECUTIONS_DATA_SAVE_ON_ERROR to all and cites the owner; the owner's words (ONE:22-27, DECISION-one-store.md lines 16 and 27) cover successful runs only, so on that one point the plan is OVERRIDDEN: the studio lead sets EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=none in the environment that starts n8n, and the saving of failed runs waits for L-SAVEERR (OWNER ONLY). "
            "Checks: C-11 (the plan conflict, static, done: the plan says all for both, so the override is needed) and C-4 (import check, not run).")
patch("| L-SAVE | studio lead", SAVE_OLD, SAVE_NEW)
patch("| L-SAVEERR | studio lead, with the owner's confirmation", "| L-SAVEERR | studio lead, with the owner's confirmation (the owner's words cover successful runs only; saving FAILED runs is a separate setting the owner has not been asked about, c6q design review M-E)",
      "| L-SAVEERR | OWNER ONLY (the studio lead asks him and writes down his answer; the studio lead does not answer for him) (the owner's words cover successful runs only; saving FAILED runs is a separate setting the owner has not been asked about, c6q design review M-E)")
patch("| L-SHEET (was Q10)", "OWNER ONLY (the studio lead asks him; if the owner agrees, the studio lead may answer for him)", "OWNER ONLY (the studio lead asks him and writes down his answer; the studio lead does not answer for him)")
patch("| L-SHEET (was Q10)", "At 16:52:47 UTC = 22:22:47 IST the folder holds OWNER-SHEET-v29-A.md (written 16:46:37 UTC = 22:16:37 IST) and OWNER-SHEET-v29-B.md (written 16:46:37 UTC = 22:16:37 IST), both rendered sheets, and OWNER-SHEET-v29-SOURCE.md (the template; written 16:41:12 UTC = 22:11:12 IST); v28 A and B were last changed at 16:09:58 UTC = 21:39:58 IST. Name the one sheet that is final (for example 'v29A'); if the studio lead renders a later version, name that one.",
      V30SENT + "; v28 A and B were last changed at 16:09:58 UTC = 21:39:58 IST. Name the one sheet that is final (for example 'v30A'); if the studio lead renders a later version, name that one.")
patch("| L-SHEET (was Q10)", "has been run on v19 to v29 (all variants", "has been run on v19 to v30 (all variants")
patch("Who answers: STUDIO LEAD", "OWNER ONLY = only the owner knows the fact or holds the permission on his own accounts; the studio lead asks him.",
      "OWNER ONLY = only the owner knows the fact or holds the permission on his own accounts; the studio lead asks him and writes down his answer, and never answers for him. Two questions are OWNER ONLY: L-SHEET and L-SAVEERR.")
patch("| L-LEASE | studio lead", "THE TWO CLAIMS", "THE TWO STATEMENTS")
patch("| L-LEASE | studio lead", "so the unlimited claim is tested", "so the statement without a time limit is tested")
# who runs steps text of 3d
patch("| Repeat-send check (rehearsal list item 13)", "or the studio lead takes the 45-second limit out of the card and caption", "or the studio lead removes the 45-second limit from the card and caption")
# stop rules
patch("| Real-key scan (rehearsal list items 15 and 16)", "scans before the take, after the take and after deletion |",
      "scans after EVERY rehearsal with real accounts, after the take BEFORE anything is deleted, and again after deletion; the scanner is first read by a second person and tested with a fake key; it prints counts only, and searches n8n's own database in place or on a copy that is deleted and counted |")
ix = find("| Real-key scan (rehearsal list items 15 and 16)")
L.insert(ix + 1, "| Card line 2, the alert sentence (risks list item 12) | the loopback re-smoke on the edited flows has shown an alert mail in the test mailbox, and the studio lead has written the date and time in UTC and IST, his name and that the alert mail was seen | studio lead | the owner, if card line 2 is cut | No for card line 2 only: it is cut and lines 3 and 4 stay |")

for _i, _l in enumerate(L):
    if "or takes the 45-second limit out of the card and the caption" in _l:
        L[_i] = _l.replace("or takes the 45-second limit out of the card and the caption", "or removes the 45-second limit from the card and the caption")
# ---------------------------------------------------------------- 5a and rows
patch("5a. WHAT CHANGES FOR A PERSON", "the 36 rows of the run sheet and the page statements whose 'What the viewer sees' is not 'Nothing'", "the 37 rows of the run sheet and the page statements whose 'What the viewer sees' is not 'Nothing'; this group of 37 is a different group from the 36 rows that apply on the default of a question")
# row 11
R11VIEW = "The run sheet's total for the one video changes to 150 s for scenes 1 to 4 plus an estimated 40 s for the closing card (about 190 s in all, not measured; the run sheet had 30 s for the card, about 180 s in all). No viewer text changes."
g = getrow(11)
assert g[COL["view"]].startswith("Nothing on screen; the run sheet's total")
g[COL["view"]] = R11VIEW
putrow(11, g)
i4 = find("| 4 | run sheet, line 80 |")
L.insert(i4 + 1, "| 11 | run sheet, line 44 | %s |" % R11VIEW)
radd(11, "why", "c6s changes (c6r design review m3; c6r naive review M6): the cut-case totals are given once, in the box (CUT CASE); the card's own Time cell on run sheet line 41 is a hand edit with a two-line replacement in the box (L-CARDLEN: old cell text 30 s EST, new cell text 40 s EST under the defaults, 35 s EST in the cut case); this row now appears in table 5a (its viewer cell no longer starts with 'Nothing').")
# row 13
rsub(13, "why", "so the plain statement is true for a second send;", "so the plain statement is expected to be true for a second send until C-9 part 2 has shown the table rule in the take's own database (the facts rest on files that are not in the repository);")
# row 14
radd(14, "why", "c6s changes (c6r design review F2): card line 2 states what the system does with an alert, but no run exists on the flows of the take (the plan excludes alert paths beyond three scenes, and the stand-in tests showed one alert mail); it is gated: it is not filmed until the loopback re-smoke on the edited flows has shown an alert mail (risks list item 12, row 8), and if none is seen line 2 is cut and lines 3 and 4 stay.")
# row 6
R6_15_OLD = "15. SECOND LEAK SCAN. After the first rehearsal with real accounts, the studio lead runs a second leak scan"
R6_15_NEW = "15. SECOND LEAK SCAN. After EVERY rehearsal with real accounts (the first, and again after each later one), the studio lead runs a second leak scan"
rsub(6, "new", R6_15_OLD, R6_15_NEW)
rsub(6, "new", "The first scan runs on fake services and fake keys only; this second scan is the only one that can show whether a real key or a real mail password reached a saved run.",
     "The first scan runs on fake services and fake keys only; this second scan, repeated after each rehearsal, and the scan after the take (item 16) are the only ones that can show whether a real key or a real mail password reached a saved run. "
     "THE SCANNER: the scanner (the leak scan program) is read by a second person and tested with a fake key before it touches a real key: the fake key is built from parts and planted in a stand-in store, the test shows that the scanner counts it (count 1) and counts 0 on a clean store. The scanner prints counts only: no file holds the key or any matched line, and the key is not in the list of running programs and not in the shell history. The second person writes under this item that the scanner was read and tested, with the date and time in UTC and IST and a name; until then the scanner is not used on a real key. "
     "WHERE IT SEARCHES: it searches n8n's own database in place (the search runs inside the database and returns counts), or on a dump of that database (a copy of the whole database written to a file) that is deleted right after the scan; the deletion of the dump is checked by counting the dump files that remain (the count must be 0), because a dump holds the saved runs and is as sensitive as the database. "
     "SWAP POINT: a pattern file kept in memory can still be written to the swap area of this computer (disk space the system uses when memory is full); so the pattern is handed over through standard input where the scanner allows it, and if a pattern file is used the studio lead writes under this item whether swap is off or encrypted on this computer; if he cannot show either, only standard input is used.")
R6_16_OLD = "16. AFTER THE TAKE. The same day, the studio lead deletes every saved run"
R6_16_NEW = ("16. AFTER THE TAKE. First, BEFORE anything is deleted (the saved runs of the take are still there), the studio lead runs the real-key scan of item 15 on all its stores, writes the hit counts and the time in UTC and IST under this item, and a hit for a real key value means the same as in item 15: cancel or replace the key and treat the runs as compromised. "
             "Then, the same day, the studio lead deletes every saved run")
rsub(6, "new", R6_16_OLD, R6_16_NEW)
rsub(6, "new", "So he then runs the leak scan's check of n8n's own database a third time, writes", "So he then runs the leak scan's check of n8n's own database once more after the deletion, writes")
rsub(6, "new", "This third scan also searches for the real key values, in the same way as in item 15", "This scan after the deletion also searches for the real key values, in the same way as in item 15")
rsub(6, "why", "this row adds items 11 to 14 to the REHEARSAL LIST", "this row adds items 11 to 16 to the REHEARSAL LIST")
radd(6, "why", "c6s changes (c6r design review F3): item 15 is repeated after EVERY rehearsal with real accounts (before: only after the first); item 16 scans BEFORE anything is deleted (before: only after the deletion, so a key leaked during the take could be erased unseen) and again after it; new sentences name the scanner review and the fake-key test before it touches a real key, counts only with no file holding the key or matched lines, search in place or on a dump that is deleted and counted, and the swap point (a pattern file in memory can reach swap; standard input is preferred).")
# row 8 item 12
R8_ANCH = " There is no exit: if the rule is not seen, scene 3 and card line 1 are cut and the take goes on without them."
rsub(8, "new", R8_ANCH,
     " The approval must cite, in writing with the date and time in UTC and IST: (1) the table rule seen in the re-smoke database; (2) the repeat sent more than 45 seconds after the first send, with the repeat flag true; (3) one rehearsal case in which the first run crashes (as in scene 4) and the same contact is sent again while the recovery flow is still working on it, with the CRM list and the test mailbox counted afterwards (1 row and 1 mail; if there are more, the words 'processed once' are not approved)."
     " CARD LINE 2 GATE: card line 2 (the sentence that says the system sends an alert) is not filmed until the loopback re-smoke on the edited flows has shown an alert mail in the test mailbox; the studio lead writes here the date and time in UTC and IST, his name and that the alert mail was seen; if no alert mail is seen, card line 2 is cut and lines 3 and 4 stay. The stand-in tests showed one alert mail; that is not a run on the flows of the take."
     + R8_ANCH)
radd(8, "why", "c6s changes (c6r design review F2, F4, m1): item 12 now also gates card line 2 (the alert sentence) on an alert mail seen in the loopback re-smoke on the edited flows, and makes the approval cite three pieces of evidence, the third being the case in which a crash is followed by a repeat during the recovery (m1). Gate G12 is still open in release note v14 (LRN14:33: its row asks for the sentence in writing; LRN14:8 lists the lease wording among the facts that need the studio lead's decision); that G12 is about the words 'processed once' beside a crash scene is this report's own reading (LREP:80 says only 'approval of the lease sentence'). Sources: LRN14:33, LRN14:8, LREP:80")

# ---------------------------------------------------------------- section 7: checks
patch("| C-4 | Import check", "NOT RUN; missing input: running n8n and the rows 63, 62, 65, 64, 67, 66, 69, 68 applied (impossible-now here; needs-lead)",
      "NOT RUN; missing input: running n8n and the rows 63, 65, 67, 69 and 92 applied (the rows 62, 64, 66 and 68 wait for L-SAVEERR, default no, and are not needed by default; impossible-now here; needs-lead)")
L[find("| C-4a |")] = ("| C-4a | After the flow-file rows that apply on the defaults are applied to copies (rows 63, 65, 67, 69; the rows 62, 64, 66, 68 wait for L-SAVEERR and are NOT applied), each of the four real-v5 flow files holds saveDataSuccessExecution all, saveDataErrorExecution none and saveManualExecutions false, once each; with L-SAVEERR answered yes (rows 62, 64, 66, 68 applied too) the failed-run setting reads all | the check script (done by me) | counts all 1, error-all 0, error-none 1, manual-false 1 in each of the 4 files on the defaults | any other count | DONE on copies; result in evidence-c6s/verify-c6s-output.txt |")
L[find("| C-11 |")] = ("| C-11 | L-SAVE check: the owner's words (ONE:22-27; DECISION-one-store.md lines 16 and 27) cover SUCCESSFUL runs only, but the re-smoke plan row PLAN:125 sets both saving settings to all and cites the owner: the plan is overridden on the failed-run setting (static) | me, file read | the plan row is read and the conflict is written down; the studio lead sets EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=none in the environment that starts n8n (the failed-run value becomes all only if the owner answers yes to L-SAVEERR) | the environment that starts n8n holds EXECUTIONS_DATA_SAVE_ON_ERROR=all without the owner's yes | DONE (static): PLAN:125 says all for both, so the override is needed and written (box, L-SAVE, section 9); the runtime proof is C-4 (NOT RUN) and the environment value is set by the studio lead (needs-lead) |")
patch("| C-6 | Leak scan for the take", "NOT RUN; missing inputs: the scan itself (not written; the audit writes no code), a running n8n with stand-ins, and the path of the spend ledger from the take's config (needs-lead)",
      "NOT RUN; missing inputs: the scan itself (not written; the audit writes no code), a second person who reads it and tests it with a fake key before it touches a real key (counts only; no file holds the key or matched lines; the key is not in the list of running programs or the shell history; n8n's own database is searched in place or on a dump that is deleted and counted), a running n8n with stand-ins, and the path of the spend ledger from the take's config (needs-lead)")
patch("| C-10c | The owner sheet the owner reads", "part 1 DONE on the sheets on disk at 2026-11-16T16:52:47Z = 22:22:47 IST (v19 to v29 (all variants, the templates called SOURCE included), evidence-c6r/static-checks-output.txt section C-10c: ", "part 1 DONE on the sheets on disk at 2026-11-16T%sZ = %s IST (v19 to v30 (all variants, the templates called SOURCE included), evidence-c6s/static-checks-output.txt section C-10c: " % (CTU, CTI))
i = find("| C-10c | The owner sheet the owner reads")
a = L[i].index("'never deletes' occurs only in v19")
b = L[i].index("so the check must be repeated on the sheet the studio lead names final")
L[i] = L[i][:a] + SHEETFACT + "); v28 A and B were last changed at 16:09:58 UTC = 21:39:58 IST; " + V30SENT.replace("At %s UTC = %s IST the folder holds " % (CTU, CTI), "the folder holds ") + ", " + L[i][b:]

# ---------------------------------------------------------------- section 8: coverage of the c6r reviews (new block before the c6q block)
cov = [
    "COVERAGE OF THE c6r REVIEWS (review-c6r-design.md, review-c6r-naive.md, review-c6r-evidence.md, evidence-c6r-independent/); the line-by-line mapping is in c6s-CHANGES.md:",
    "",
    "| Review item | Fix | Where / check |",
    "|---|---|---|",
    "| Design F1 (failed-run saving not carried through C-4a, C-11, C-4 row list; PLAN:125) | C-4a and C-11 follow the defaults (successful runs all, failed runs none); PLAN:125 overridden on that point; C-4 row list corrected | L-SAVE, box, sections 7 and 9; checks 'F1' of verify-c6s.py |",
    "| Design F2 (card line 2 states alert behaviour as fact) | gate: card line 2 not filmed until the loopback re-smoke on the edited flows shows an alert mail, with UTC, IST and a name | row 8 item 12, section 3e entry, box; check 'F2' |",
    "| Design F3 (real-key scan holes: only after the first rehearsal; none between the take and deletion; scanner unreviewed; dump; swap) | scan after every rehearsal with real accounts and after the take BEFORE deletion; scanner read by a second person and tested with a fake key; counts only; in place or a dump deleted and counted; swap point named | row 6 items 15 and 16, section 3e, C-6; check 'F3' |",
    "| Design F4 (stale sheets; release note v14; G12 stretched) | sheet check rerun over v19 and later (v30 exists); the verifier fails on a newer sheet than the check time and on a version newer than the named one; release note v14 cited (G12 open); the wider reading of G12 labelled as this report's assumption | box, section 0, section 3, C-10c, section 9; checks 'F4' |",
    "| Design m1 to m4 | crash-then-repeat case in the approval evidence; 'expected to be true until C-9 part 2'; cut-case totals once and a two-line Time cell replacement; EXAMPLE time later than the check time | row 8, row 13, box (L-CARDLEN, CUT CASE, answer line) |",
    "| Naive M1 to M8, minors | box rewritten and shortened; does-not-do list first; reviewer order explained; one OWNER ONLY rule; Q27 and G12 explained; numbered steps; the circle in C-9 part 2 explained; word fixes; stale names; row 11 in 5a; section 0 history moved to 1b | box, sections 0, 1, 1b, 3, 4, 5a |",
    "| Independent evidence (verifier failed 2 of 123 on v30; glob missed v30) | static-checks.sh covers v19 and later; the report names v30 and the check time | evidence-c6s/static-checks.sh |",
    "",
]
ic = find("COVERAGE OF THE c6q REVIEWS")
L[ic:ic] = cov

# ---------------------------------------------------------------- section 9
patch("- [needs-owner or needs-lead] L-SHEET", "[needs-owner or needs-lead] L-SHEET: confirm the ONE final owner sheet.", "[needs-owner] L-SHEET: confirm the ONE final owner sheet.")
i9 = find("- [needs-owner] L-SHEET: confirm the ONE final owner sheet.")
a = L[i9].index("At 16:52:47 UTC")
b = L[i9].index("Next step: name the final sheet")
L[i9] = L[i9][:a] + V30SENT + ". " + L[i9][b:]
L[i9] = sub(L[i9], "they are not used if the owner reads v29", "they are not used if the owner reads v30")
patch("- [needs-lead] Gate G12, the approval of the lease wording", "I do not approve it.",
      "I do not approve it. Release note v14 (LRN14:33, LRN14:8) does not close it. The question reads as 'the words processed once beside a crash scene' because I read it that way: that is this report's own assumption (LREP:80 says only 'approval of the lease sentence'); ask whether you meant something narrower.")
patch("- [needs-lead] Under the default the 45-second limit sentence", "Next step: the studio lead has the one final owner sheet and the release note carry it; no row of this report edits them (the sheet is being rebuilt).",
      "Next step: you, or a builder you name, add it to the one final owner sheet and to the release note (box, step 9); no row of this report edits them.")
patch("- [needs-lead] The card row's own Time cell", "Next step: change it to '40 s EST' when applying row 11, or say that the old cell stays.",
      "Next step (box, L-CARDLEN): change it by hand, old cell text '30 s EST', new cell text '40 s EST' under the defaults ('35 s EST' in the cut case).")
patch("- [needs-lead] The box is about 3,490 words", "- [needs-lead] The box is about 3,490 words: shorter than the c6p box would be impossible with the what-to-type block and the explained words the naive review asked for. Decide whether to move the second list of words into section 1 (the box then drops by about 450 words and the naive M5 explanations leave the box). Not done, because the two reviews ask for opposite things.",
      "- [done in c6s] The box was 3,490 words in c6r; it is rewritten and shorter (its word count is printed by evidence-c6s/verify-c6s-output.txt); the explanations the stranger reader needs stay in the box, the duplicates of section 1 were removed, nothing of the report body was deleted.")
patch("- [needs-lead] Section 0 starts with history before the how-to", "- [needs-lead] Section 0 starts with history before the how-to, and the words 'EGM' and 'KEY' (four meanings) are not defined in the box; fixing both means moving text between sections; the studio lead decides whether it is worth another round.",
      "- [done in c6s] Section 0 started with history before the how-to; the history is now section 1b after the how-to, and the words EGM and KEY are defined in the box.")
patch("- [needs-lead] If scene 3 and card line 1 are cut", "- [needs-lead] If scene 3 and card line 1 are cut (G12 not approved), the run sheet totals (150 s of scenes, 90 spoken words) fall; row 11 does not cover that case. Next step: the studio lead says whether a second set of totals is wanted.",
      "- [needs-lead] If scene 3 and card line 1 are cut (G12 not approved or the table rule not seen), the totals are in the box (CUT CASE, the one place that gives them); row 11 writes the defaults only. Next step: you apply the cut totals by hand, or name a builder who adds a row.")
L.append("- [needs-lead] Failed-run saving, plan conflict: the re-smoke plan row PLAN:125 (an input; not edited here) sets EXECUTIONS_DATA_SAVE_ON_ERROR=all and cites the owner, but the owner's words cover successful runs only (ONE:22-27; DECISION-one-store.md lines 16 and 27). On that one point this report overrides the plan. Next step: you set EXECUTIONS_DATA_SAVE_ON_SUCCESS=all and EXECUTIONS_DATA_SAVE_ON_ERROR=none in the environment that starts n8n, and have the plan row corrected when you next edit the plan; if the owner says yes to L-SAVEERR, the failed-run value becomes all.")
L.append("- [needs-lead] The leak scan program (check C-6) does not exist, so the real-key scan of row 6 items 15 and 16 has never run. Next step: a builder you name writes it; a second person reads it and tests it with a fake key (counts only; no file holds the key or matched lines) before it touches a real key; searching n8n's own database in place or on a dump that is deleted and counted; the swap point is named in row 6 item 15.")
L.append("- [needs-lead] Card line 2 (the alert sentence) is backed only by stand-in tests. Next step: the loopback re-smoke on the edited flows must show an alert mail in the test mailbox, with date and time in UTC and IST and a name, under risks list item 12 (row 8); otherwise card line 2 is cut.")

if FAILS:
    print("\n".join(FAILS)); print(len(FAILS), "FAILED PATCHES"); sys.exit(1)
open(D + "REPORT-c6s.md", "w", encoding="utf-8").write("\n".join(L))
print("built REPORT-c6s.md: %d lines" % len(L))

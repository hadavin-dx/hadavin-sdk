"""Builds ../REPORT-c6v.md from REPORT-c6u-base.md (the c6u build rerun on the live folders by build_base.py; REPORT-c6u.md itself is never touched).
Every patch asserts its match count. Usage: python3 -B -I build_c6v.py   (run_all.sh runs static-checks, build_base.py, this file, the verifier and the negative controls in that order).
Box counting rule (c6v): the words of the start box are counted from the first line AFTER its heading to the line before the heading of part 2; the build repeats until the stated number equals the counted number."""
import re, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE) + "/"
E = HERE + "/"
BASE = open(E + "REPORT-c6u-base.md", encoding="utf-8").read()
FAILS = []
PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")


def sub(t, old, new, c=1):
    n = t.count(old)
    if n != c:
        FAILS.append("expected %d match(es), found %d: %r" % (c, n, old[:110]))
        return t
    return t.replace(old, new)


def row_line(L, k):
    c = [i for i, l in enumerate(L) if l.startswith("| %d | NOT APPLIED" % k)]
    assert len(c) == 1, k
    return c[0]


def edit_row(L, k, field, fn):
    i = row_line(L, k)
    g = list(PAT.match(L[i]).groups())
    ix = dict(st=1, view=4, old=5, new=6, why=7, was=8)[field]
    g[ix] = fn(g[ix])
    L[i] = "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % tuple(g)


def mk_row(i, st, f, ln, view, old, new, why, was="new in c6v"):
    return "| %d | %s | %s | %d | %s | `%s` | `%s` | %s | %s |" % (i, st, f, ln, view, old, new, why, was)


RS = "handover/demo/VIDEO-RUNSHEET.md"
READY = "NOT APPLIED; ready"
NOT_FILMED = "NOT IN THE ONE VIDEO (the one video is scenes 1 to 4 and the closing card; "
WHY_TAIL = " Decided by the studio lead's decision 1 of 2026-11-16 (DEC:2): scenes 5 to 11 are not in the one video. Raised by the c6u design review m3 (stale run-sheet leftovers; not an allowed exception, so rows, not a note). Sources: DEC:2, RS:%d"
# (id, run sheet line, view, old, new, what it says)
NEWROWS = [
    (97, 78, "Nothing on screen (the run sheet's list of open decisions).", "4. Scene 5 on the stand-in CRM or cut (risk 7)?",
     "4. DECIDED: scene 5 is cut (the one video is scenes 1 to 4 and the closing card).", "The open decision 4 asked whether scene 5 stays; decision 1 answers it."),
    (98, 77, "Nothing on screen (the run sheet's list of open decisions).", "3. Keep scene 11 (AF1, n=1) or cut it? Audit recommends cut.",
     "3. DECIDED: scene 11 is cut (the one video is scenes 1 to 4 and the closing card).", "The open decision 3 asked whether scene 11 stays; decision 1 answers it."),
    (99, 67, "Nothing on screen (the run sheet's rehearsal list).", "6. The alert-only refusal (scene 11, if kept): confirm the cut and the overlay text.",
     "6. " + NOT_FILMED + "scene 11 is not filmed): skip this item. (Old text: The alert-only refusal (scene 11, if kept): confirm the cut and the overlay text.)", "Rehearsal item 6 rehearses scene 11."),
    (100, 66, "Nothing on screen (the run sheet's rehearsal list).", "5. The refuse-every-call switch on the stand-in CRM (scene 5): note the real seconds at lease 45 s.",
     "5. " + NOT_FILMED + "scene 5 is not filmed): skip this item. (Old text: The refuse-every-call switch on the stand-in CRM (scene 5): note the real seconds at lease 45 s.)", "Rehearsal item 5 rehearses scene 5."),
    (101, 64, "Nothing on screen (the run sheet's rehearsal list).", "3. The stand-in drop on the film flows with .drop = 1: run it five times; note intake count (0 or 1), alert count, state, real seconds to alert, and whether a reply comes back (scene 8).",
     "3. " + NOT_FILMED + "scene 8 is not filmed): skip this item. (Old text: The stand-in drop on the film flows with .drop = 1: run it five times; note intake count (0 or 1), alert count, state, real seconds to alert, and whether a reply comes back (scene 8).)", "Rehearsal item 3 rehearses scene 8."),
    (102, 57, "Nothing on screen (the run sheet's list of risks).", "8. Which lease is shipped is not settled: real-v4 and v5 use 45 s, DESIGN-A-README says 120 s for its flows folder.",
     "8. DECIDED (the studio lead's answers under 'Update 17:08Z' (22:38 IST) below): the shipped lease is 45 s for the real and film flows; the 120 s of DESIGN-A-README belongs to its own flows folder, not to the take.", "Risks item 8 says the shipped lease is not settled; line 85 of the same file says 'Shipped lease for real and film = 45 s (decided)'. Row 81 edits the second sentence of the same line (an independent part)."),
    (103, 56, "Nothing on screen (the run sheet's list of risks).", "7. Scene 5 uses the stand-in CRM (a real CRM cannot be told to refuse). If the owner wants the whole take on real services, scene 5 must be cut. Open question for the owner.",
     "7. DECIDED: scene 5 is cut (the one video is scenes 1 to 4 and the closing card); no question for the owner remains here.", "Risks item 7 is an open question about scene 5, which decision 1 cuts."),
    (104, 54, "Nothing on screen (the run sheet's list of risks).", "5. Scene 7 to 9 numbers: the drop fault has no measured row",
     "5. " + NOT_FILMED + "scenes 7 to 9 are not filmed): skip this item. (Old text: Scene 7 to 9 numbers: the drop fault has no measured row", "Risks item 5 is about the numbers of scenes 7 to 9."),
]


def build(words):
    t = BASE
    NEWV = int(re.search(r"The newest on disk is v(\d+)", t).group(1))
    # ---- file names and paths of this pass
    t = t.replace("evidence-c6u/", "evidence-c6v/").replace("verify-c6u", "verify-c6v").replace("neg_controls_c6u", "neg_controls_c6v").replace("c6u-APPLIED-ROWS.md", "c6v-APPLIED-ROWS.md")
    t = t.replace("verify-c6t.py", "verify-c6v.py")
    L = t.split("\n")
    L[0] = "# REPORT-c6v: video audit fix pass, supersedes REPORT-c6u.md (2026-11-16, UTC; IST = UTC + 5:30)"
    t = "\n".join(L)

    # ---- M1 (design review): the carve-outs 'the 45 s lease setting is allowed' are held under G12 in every place
    t = t.replace("(the 45 s lease setting is allowed: it is a setting, not a result)", "(the 45 s lease setting is allowed only after G12 is approved: it is a setting, not a result)")
    t = t.replace("(the 45 s lease setting and the stopwatch are allowed)", "(the stopwatch is allowed; the 45 s lease setting is allowed only after G12 is approved)")
    t = t.replace("the carve-outs of rows 1, 2, 5, 15, 17, 19, 30 and 34 that say 'the 45 s lease setting is allowed'", "the carve-outs of rows 1, 2, 5, 15, 17, 19, 30, 34, 83, 93 and 94 that now say 'the 45 s lease setting is allowed only after G12 is approved'")
    t = t.replace("the carve-out 'the 45 s lease setting is allowed' in rows 1, 2, 5, 15, 17, 19, 30 and 34 is this report's own reading", "the carve-out in rows 1, 2, 5, 15, 17, 19, 30, 34, 83, 93 and 94 now reads 'the 45 s lease setting is allowed only after G12 is approved' (c6v design review M1); that item 11 reaches it is this report's own reading")
    t = t.replace("The 45-second lease setting may also be shown or said (it is a setting, not a test result)", "The 45-second lease setting may also be shown or said, only after G12 is approved (it is a setting, not a test result)")

    L = t.split("\n")
    # ---- m1 (design review): row 76 carries the relayed tag
    edit_row(L, 76, "new", lambda s: s.replace(" Final states: 10 runs done", " Final states (relayed from the lane3 session's results, not run for this audit): 10 runs done", 1) if " Final states: 10 runs done" in s else (FAILS.append("row 76 anchor") or s))
    # ---- class 6 (short anchors): row 94 old text 'Any number.' occurs on lines 30 and 32 of the run sheet; the words before it make it unique
    edit_row(L, 94, "old", lambda s: 'in all faults". Any number.')
    edit_row(L, 94, "new", lambda s: 'in all faults". Any test result as a number (the stopwatch is allowed; the 45 s lease setting is allowed only after G12 is approved).')
    edit_row(L, 94, "why", lambda s: s + " c6v (class 6, short anchors): the old text now starts with the words before it, because 'Any number.' alone occurs twice in the file (lines 30 and 32).")
    # ---- M4 + m2: row 96, unique anchor, the Time cell of the state the defaults leave (G12 open: card line 1 cut by hand = 79 words = 35 s)
    edit_row(L, 96, "old", lambda s: "own runs. \\| 30 s EST")
    edit_row(L, 96, "new", lambda s: "own runs. \\| 35 s EST")
    edit_row(L, 96, "view", lambda s: "Nothing on screen (the planned time of the closing card in the run sheet table).")

    def r96why(s):
        a = s.index("The card row's own Time cell")
        return ("The card row's own Time cell on run sheet line 41 said 30 s EST while row 11 sets the card to the budget of the whole card (c6t design review M3). c6v (c6u design review M4, m2): the old text now includes the words before the cell ('own runs. \\| 30 s EST'), because '30 s EST' alone occurs 3 times in the file (lines 36, 39 and 41); the new cell is 35 s EST, the budget of the state the defaults leave: G12 is open, so card line 1 is cut by hand and the card is lines 2 to 4 = 79 words = 31.6 s, budget 35 s (Table B, section 1c; an ESTIMATE until the stopwatch run). "
                "If you approve G12 and the alert mail is seen, the card keeps line 1 (90 words, 36.0 s, budget 40 s): the builder then changes the cell to 40 s EST by hand. Other cut cases: Table B. Sources: RS:41, L-CARDLEN")
    edit_row(L, 96, "why", r96why)
    edit_row(L, 96, "was", lambda s: "new in c6u; text and anchor changed in c6v")
    t = "\n".join(L)
    t = sub(t, "row 96 sets '40 s EST' for the defaults", "row 96 sets '35 s EST', the budget of the card without line 1", 1)
    t = sub(t, "The card's Time cell on run sheet line 41 says '30 s EST'; row 96 changes it to '40 s EST' under (a) and does nothing under (b).",
            "The card's Time cell on run sheet line 41 says '30 s EST'; row 96 changes it to '35 s EST' (the card without line 1, which the defaults leave because G12 is open; '40 s EST' once you approve G12 and line 1 stays) and does nothing under (b).", 1)
    t = sub(t, "The card's Time cell on run sheet line 41 (row 96): Old cell text: 30 s EST. New cell text: 40 s EST (the defaults); 35 s EST when scene 3 and card line 1 are cut (card lines 2 to 4 = 79 words, budget 35 s); the other cut cases: Table B.",
            "The card's Time cell on run sheet line 41 (row 96): old cell text (with the words before it): own runs. | 30 s EST. New cell text: 35 s EST (the state the defaults leave: G12 open, card line 1 cut by hand, card lines 2 to 4 = 79 words, budget 35 s); 40 s EST when you have approved G12 and card line 1 stays (90 words), changed by the builder by hand; the other cut cases: Table B.", 1)
    t = sub(t, "| defaults: nothing cut |", "| nothing cut (G12 approved and the alert mail seen; the defaults leave G12 open) |", 1)
    t = sub(t, "[done in c6u] The card row's own Time cell on run sheet line 41 ('30 s EST') is edited by row 96 under the defaults ('40 s EST'); the cut cases (35 s EST and the values of Table B in section 1c) are hand edits by the builder of step 2 when the studio lead tells him which cut case applies (box, step 6).",
            "[done in c6v] The card row's own Time cell on run sheet line 41 ('30 s EST') is edited by row 96 to '35 s EST', the budget of the card without line 1, which is the state the defaults leave (G12 open); the value 40 s EST (card with line 1, G12 approved) and the other cut cases of Table B in section 1c are hand edits by the builder of step 2 when the studio lead tells him which case applies (box, step 6).", 1)

    # ---- m3 (design review): rows for the stale run-sheet leftovers (ids 97 to 104), inserted in table order (descending line per file)
    L = t.split("\n")
    for (i, ln, view, old, new, why) in NEWROWS:
        r = mk_row(i, READY, RS, ln, view, old, new, why + WHY_TAIL % ln)
        rs_rows = [(j, PAT.match(l)) for j, l in enumerate(L) if PAT.match(l) and PAT.match(l).group(3) == RS]
        after = [j for j, m in rs_rows if int(m.group(4)) >= ln]
        L.insert(max(after) + 1, r)
    t = "\n".join(L)
    NROWS, NREADY, NDEF, NW1 = 104, 57, 38, 95
    NUNREAD = 99
    # counts
    t = sub(t, "holds 96 proposed text changes", "holds %d proposed text changes" % NROWS, 1)
    t = sub(t, "(91 of 96 rows name files this branch does not hold)", "(%d of %d rows name files that branch cloud/core-hardening does not hold)" % (NUNREAD, NROWS), 1)
    t = sub(t, "READY (49: applicable now)", "READY (%d: applicable now)" % NREADY, 1)
    t = sub(t, "WAVE 1 = READY + ON DEFAULT = 87 of the 96 rows", "WAVE 1 = READY + ON DEFAULT = %d of the %d rows" % (NW1, NROWS), 1)
    t = sub(t, "the builder applies the 87 wave 1 rows to 10 files", "the builder applies the %d wave 1 rows to 10 files" % NW1, 1)
    t = sub(t, "(row count 96)", "(row count %d after c6v; 96 in c6u)" % NROWS, 1)
    t = sub(t, "Of the 96 rows (rows 1 to 72 keep the numbers of REPORT-c6n.md; rows 73 to 94 are new in c6o, rows 95 and 96 are new in c6u, and rows 1, 33 and 39 were split; c6p to c6s add no row): 49 are 'ready'",
            "Of the %d rows (rows 1 to 72 keep the numbers of REPORT-c6n.md; rows 73 to 94 are new in c6o, rows 95 and 96 are new in c6u, rows 97 to 104 are new in c6v, and rows 1, 33 and 39 were split; c6p to c6s add no row): %d are 'ready'" % (NROWS, NREADY), 1)
    t = sub(t, "Of the 96 rows, 49 are ready, 38 apply", "Of the %d rows, %d are ready, 38 apply" % (NROWS, NREADY), 1)
    t = sub(t, "87 wave 1 rows, applied first", "%d wave 1 rows, applied first" % NW1, 1)
    t = sub(t, "applies wave 1 (87 rows, section 3 lists them)", "applies wave 1 (%d rows, section 3 lists them)" % NW1, 1)
    t = sub(t, "91 of 96 rows cannot be read in the repository", "%d of %d rows cannot be read in the repository" % (NUNREAD, NROWS), 1)
    t = sub(t, "the 94 edits can be applied", "the %d edits can be applied" % NROWS, 1)
    t = sub(t, "the files of 89 of the 94 rows (the run sheet", "the files of %d of the %d rows (the run sheet" % (NUNREAD, NROWS), 1)
    t = sub(t, "| 49 | ready | none |", "| %d | ready | none |" % NREADY, 1)
    t = sub(t, "| TOTAL | all rows | 96 | ready 49,", "| TOTAL | all rows | %d | ready %d," % (NROWS, NREADY), 1)
    t = sub(t, "Rows it applies: the 49 ready rows", "Rows it applies: the %d ready rows" % NREADY, 1)
    t = sub(t, "), 87 rows in all, in the files", "), %d rows in all, in the files" % NW1, 1)
    t = sub(t, "47, 48, 60, 61, 70, 71, 72, 75, 76, 77, 78, 79, 80, 82, 83, 84, 85, 88, 89, 93, 94", "47, 48, 60, 61, 70, 71, 72, 75, 76, 77, 78, 79, 80, 82, 83, 84, 85, 88, 89, 93, 94, 97, 98, 99, 100, 101, 102, 103, 104", 3)
    # the second wave-1 sentence: the rows it applies, ready first
    # ---- M2/M3 (design and naive): stale text in sections 0, 1b, 5a, 7, 9
    t = sub(t, "this group of 37 is a different group from the 36 rows that apply on the default of a question", "this group is a different group from the 38 rows that apply on the default of a question", 1)
    t = sub(t, "| Design M3 (section 5a stale, page rows missing) | 5a is made from the table (36 rows) |", "| Design M3 (section 5a stale, page rows missing) | 5a is made from the table (the count is in its heading) |", 1)
    t = sub(t, "- [done in c6u] ROW 95 IS ADDED (it was only proposed here before): the old proposal text (not added; see section 0): file handover/demo/n8n-flows/N8N-START.md, line 24, old text `- SAVE_ON_ERROR=none: the same for runs that fail.`, new text `- SAVE_ON_ERROR=none: n8n stores no run data for runs that fail (the opposite of the line above).`; row 53 then takes this new text as its old text. Next step: the studio lead tells a builder to add row 95 and recount the rows (95 rows; the 36 rows on a default become 37; wave 1 becomes 86).",
            "- [done in c6u] Row 95 exists in the table (N8N-START.md line 24, old text `- SAVE_ON_ERROR=none: the same for runs that fail.`, new text `- SAVE_ON_ERROR=none: n8n stores no run data for runs that fail.`); row 53 takes its new text as its old text, so row 95 is applied first. Nothing is left to add.", 1)
    t = sub(t, "OWNER-SHEET-v30-A.md, OWNER-SHEET-v30-B.md and LEAD-RELEASE-NOTE-v14.md do not carry it (searched at the check time)", "the newest rendered owner sheets and release note named in section 0 do not carry it (searched at the check time)", 1)
    t = sub(t, "The EGM review of the changed files, resolve and the drift report for c6t are run by the studio lead.", "The EGM review of the changed files, resolve and the drift report for c6v are run by the studio lead.", 1)
    t = sub(t, "(after steps 5 to 10 are written)", "(after TASKS (5) to (10) are written)", 1)
    t = sub(t, "No file gives a duration for steps 4 to 6, so", "No file gives a duration for TASKS (4) to (6), so", 1)
    t = sub(t, "(box, step 4)", "(box, TASK (4))", 1)
    t = sub(t, "called STEPS (WHAT TO TYPE, steps 1 to 5)", "called STEPS (WHAT TO TYPE, steps 1 to 6)", 1)
    t = t.replace("L-SHEET v30A", "L-SHEET v%dA" % NEWV).replace("(v30A and the times are EXAMPLES)", "(v%dA and the times are EXAMPLES; A and B are the two renderings of the one owner sheet)" % NEWV)
    # ---- naive M6: say what A and B are, in the L-SHEET row of the box
    t = sub(t, "Which ONE owner sheet (the checklist the owner reads) is final? ", "Which ONE owner sheet (the checklist the owner reads) is final? Each version exists as sheet A and sheet B, two renderings of the same checklist: the heading of each file says 'sheet A' or 'sheet B', and the owner's numbers message must name the same letter; answer with one version and letter, for example v%dA. " % NEWV, 1)

    # ---- naive M1: ONE status per open item
    t = sub(t, "Every question below has ONE status: ANSWERED BY DEFAULT (you may change it) or OPEN (OWNER ONLY: only the owner can answer; 'apply all defaults' never answers it); two are OPEN.",
            "Every question below has ONE status: ANSWERED BY DEFAULT (you may change it), ANSWERED (by you) or OPEN. OPEN has two kinds, and 'apply all defaults' answers none of them. OPEN (OWNER ONLY) = only the owner can answer: L-SHEET and L-SAVEERR in the table. OPEN (YOURS or OWNER'S, not a table question): G12 (yours), the meaning of Q27 (a), (b), (c) and the delete-path check (both the owner's, ORD:232). That is five open items in all; L-DEL is ANSWERED (no, never).", 1)
    t = sub(t, "| L-DEL | Does the take delete contacts? ANSWERED by you: no, never. Still open: the delete-path check the owner wants (ORD:232). | As answered. |",
            "| L-DEL | Does the take delete contacts? | ANSWERED by you: no, never. (The delete-path check is a different item, OPEN, the owner's: ORD:232.) |", 1)
    t = sub(t, "| L-CUT | Mark the run sheet lines of scenes 5 to 11", "| L-CUT | Mark the run sheet lines of scenes 5 to 11", 1)
    t = sub(t, "as 'not in the one video'? | No edit. |", "as 'not in the one video'? | No (no edit of the scene table; the rehearsal, risk and open-decision items of those scenes are edited by rows 97 to 104). |", 1)
    t = sub(t, "The two OPEN (OWNER ONLY) questions are two separate lines", "The two OPEN (OWNER ONLY) questions are two separate lines", 1)
    # ---- naive M2: the branch
    t = sub(t, "Old texts were checked only against a scratchpad copy; equality with the real files is UNVERIFIED",
            "WHERE THE BUILDER WORKS: in a checkout of branch cloud/flows-audit, folder handover/ (the files the rows change are on that branch; this report is on branch cloud/core-hardening, which holds only inputs/DECISION-one-store.md of them). Old texts were checked only against a scratchpad copy of those files (shipped in evidence-c6v/tree/, 9 files, byte-equal to a second scratchpad copy of that branch); equality with the real files is UNVERIFIED", 1)
    t = sub(t, "(%d of %d rows name files that branch cloud/core-hardening does not hold): the builder must" % (NUNREAD, NROWS), "(%d of %d rows name files that branch cloud/core-hardening does not hold): before applying a row the builder must" % (NUNREAD, NROWS), 1)
    # ---- naive M4: G12 quoted one way, typed answer forms
    t = sub(t, "(G12 = YOUR gate, release note v14 line 33, LRN14:33; open)", "(G12 = YOUR gate, quoted under WORDS; open)", 1)
    t = sub(t, "- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 holds",
            "- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 is the row of your release note v14, line 33 (LRN14:33): '| G12 | Claims: the one sentence, the ban list of section 5 decided (the lease sentence is out of the public post, lead answer Q22c) | sentence in writing | sentence missing |'. I read it as OPEN: the sentence is not yet in writing; I do not approve it. To CLOSE it, type one of three lines on its own line in ORDERS.md: `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed` or `## G12 (studio lead, <UTC> = <IST>): not approved` or `## G12 (studio lead, <UTC> = <IST>): closed: line 33 of release note v14 is my approval`. G12 holds", 1)
    t = sub(t, "Release note v14 (LRN14:33), your newest, still lists G12", "Release note v14 (LRN14:33; its lines 8, 33, 149 and 150 equal the newest rendered note) still lists G12", 1)
    t = sub(t, "LRN14:33 in release note v14, the newest;", "LRN14:33 in release note v14 (lines 8, 33, 149, 150 equal the newest rendered note);", 1)
    # ---------------- box trims (the box must stay under 2,500 words; the detail is in section 1c) and the naive-review fixes
    def setline(t, prefix, new):
        ls = t.split("\n")
        ix = [i for i, l in enumerate(ls) if l.startswith(prefix)]
        if len(ix) != 1:
            FAILS.append("setline: %d lines start with %r" % (len(ix), prefix[:60]))
            return t
        ls[ix[0]] = new
        return "\n".join(ls)

    t = re.sub(r"This box holds \d+ words; detail moved out of it, nothing deleted, is in section 1c\.", "This box holds %d words (counted without this heading line); detail moved out of it, nothing deleted, is in section 1c." % words, t)
    t = sub(t, "OPEN has two kinds, and 'apply all defaults' answers none of them. OPEN (OWNER ONLY) = only the owner can answer: L-SHEET and L-SAVEERR in the table. OPEN (YOURS or OWNER'S, not a table question): G12 (yours), the meaning of Q27 (a), (b), (c) and the delete-path check (both the owner's, ORD:232). That is five open items in all; L-DEL is ANSWERED (no, never).",
            "Five items are OPEN and 'apply all defaults' answers none: L-SHEET and L-SAVEERR (OWNER ONLY, in the table); G12 (yours); the meaning of Q27 (a), (b), (c) and the delete-path check (the owner's, ORD:232). L-DEL is ANSWERED (no, never).", 1)
    t = setline(t, "1. What the line in step 2 does NOT do:",
                "1. What the line in step 2 does NOT do: it does not answer the five OPEN items; does not approve G12 (WORDS); runs no check, spends nothing, imports nothing into n8n, does not start the filmed run; writes no card line about the owner's HubSpot key (scope unconfirmed); puts no 45-second limit sentence into any document (TASK (9)); leaves unapplied the 3 rows that wait for a check and the 6 that wait for the owner. "
                "WHERE THE BUILDER WORKS: a checkout of branch cloud/flows-audit, folder handover/ (the files the rows change; this report is on branch cloud/core-hardening, which holds only one of them). Old texts were checked only against a scratchpad copy (shipped in evidence-c6v/tree/); equality with the real files is UNVERIFIED (%d of %d rows name files that core-hardening branch lacks): the builder confirms each old text occurs once in the real file BEFORE applying its row, and stops and reports any row where it does not." % (NUNREAD, NROWS))
    t = sub(t, "the reviewers are review agents (EGM), not people", "the reviewers are review agents (EGM = the studio's review method), not people", 1)
    t = sub(t, "- CONTACT = one made-up sales contact (the files call it a 'lead').", "- CONTACT = one made-up sales contact (the files call it a 'lead'; card line 1 says 'lead', your decided sentence, lines 2 to 4 say 'contact': tell the builder if you want one word). HUBSPOT = the customer-record system (a CRM) where the take writes its contacts. KEY = a secret code that lets a program use an account; the HUBSPOT KEY is the owner's key to HubSpot; the PROBE KEY of your answer Q20.3 is a second, separate key (my reading: for look-up tests only).", 1)
    t = sub(t, "RUN SHEET = VIDEO-RUNSHEET.md: scenes 1 to 4 and a closing card", "RUN SHEET = VIDEO-RUNSHEET.md: scenes 1 to 4 (1 the stack at rest, 2 one contact goes in, 3 the same contact is sent again, 4 n8n is switched off mid-contact and recovery finishes it) and a closing card", 1)
    t = setline(t, "- GATE = a run sheet step that blocks the take",
                "- GATE = a run sheet step that blocks the take until a named person writes a result on it. G12 = YOUR gate, the row of your release note v14 line 33 (LRN14:33): '| G12 | Claims: the one sentence, the ban list of section 5 decided (the lease sentence is out of the public post, lead answer Q22c) | sentence in writing | sentence missing |'. It is OPEN: I do not approve it. It holds every lease word a viewer would see: 'processed once' beside a crash scene (this report's own reading; LREP:80 says only 'approval of the lease sentence'), the label 'setting: lease 45 s' and the words 'other lease settings' on card line 4 (a viewer hears 'lease' with no explanation), because your release note bars lease and recovery sentences from the post and the video unless approved in writing (LRN14:149, item 11). "
                "To approve, write on its own line in ORDERS.md: `## G12 (studio lead, <UTC> = <IST>): approved: the words 'processed once' beside the crash scene, the label 'setting: lease 45 s' and the words 'other lease settings' may be filmed`. The two other forms (not approved; closed by line 33) are in section 1c.")
    m = re.search(r"The newest on disk is v%d\. At [^|]*?SOURCE\.md \(the template; written [^)]*\)\." % NEWV, t)
    if not m:
        FAILS.append("L-SHEET short times not found")
    else:
        t = t.replace(m.group(0), "The newest rendered version at the check time is v%d (file names and written times: section 1c, L-SHEET in full; they change while I work, so run evidence-c6v/run_all.sh last)." % NEWV, 1)
    t = sub(t, " The card's Time cell on run sheet line 41 says '30 s EST'; row 96 changes it to '35 s EST' (the card without line 1, which the defaults leave because G12 is open; '40 s EST' once you approve G12 and line 1 stays) and does nothing under (b).", " The card's Time cell (row 96) is in section 1c.", 1)
    t = sub(t, " No row puts the 45-second limit sentence on the card, in the caption, or in any other document; whether you want it in the owner sheet and the release note is your question TASK (9).", " No row puts the 45-second limit sentence anywhere (TASK (9)).", 1)
    t = sub(t, " Under any answer the lease words that stay on the video are held under G12: filmed only after your written approval, otherwise cut by hand.", " Under any answer the lease words on the video are held under G12.", 1)
    t = sub(t, " The plan PLAN:125 also saves failed runs; the owner's words do not cover that, so the plan is overridden on that point: failed runs are not saved.", " The plan PLAN:125 also saves failed runs; the owner's words do not cover that, so failed runs are not saved.", 1)
    t = setline(t, "DATES. No file gives a duration",
                "DATES. No file gives a duration for TASKS (4) to (6), so I cannot say whether Wed 18 Nov 2026 (ORD:150, not fixed) can be reached; ask the builder for hours per task first. No take is planned on Mon 23 Nov (ORD:229); if one is needed, the strictest reading of Q27 (section 1c) applies: MY ASSUMPTION. The post is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).")
    t = sub(t, "- TASKS (1) to (8) in short:", "- TASKS (1) to (8) in short (a builder applies rows 23, 58 and 59 as in step 1 and adds the row numbers to c6v-APPLIED-ROWS.md):", 1)
    t = sub(t, "1c-D. THE ANSWER FORM IN DETAIL\n", "1c-D. THE ANSWER FORM IN DETAIL\n\nG12 FORMS (the approving form is in the box): `## G12 (studio lead, <UTC> = <IST>): not approved` and `## G12 (studio lead, <UTC> = <IST>): closed: line 33 of release note v14 is my approval` (the second means the release note row already is your approval; nothing else changes). Typed forms are examples with your time.\n", 1)
    # second trim pass (c6v): box under 2,500 words
    t = sub(t, " Each version exists as sheet A and sheet B, two renderings of the same checklist: the heading of each file says 'sheet A' or 'sheet B', and the owner's numbers message must name the same letter; answer with one version and letter, for example v%dA." % NEWV, " Sheet A and sheet B are two renderings of one checklist (the heading of each file says which; the owner's numbers message must name the same letter); answer with one version and letter, for example v%dA." % NEWV, 1)
    t = sub(t, " (file names and written times: section 1c, L-SHEET in full; they change while I work, so run evidence-c6v/run_all.sh last).", " (file names and written times: section 1c).", 1)
    t = sub(t, " and sets the card's Time cell to match (row 96 sets '35 s EST', the budget of the card without line 1).", " and sets the card's Time cell to match (row 96).", 1)
    t = sub(t, "CUT CASES (section 1c, Table B): scene 3 and card line 1 cut (G12 not approved) about 160 s; card line 2 cut (no alert mail seen) about 175 s.\n\n", "", 1)
    t = sub(t, " (not the studio's other 're-pin', pointing a demo at a new core version)", "", 1)
    t = sub(t, " Q27 (a), (b), (c), KEY, MONEY STOP, EGM, FINAL, RUN, CHECK: section 1c.", " More words (Q27, MONEY STOP, FINAL, RUN, CHECK): section 1c.", 1)
    t = sub(t, " (no file says whether one human fills both roles)", "", 1)
    t = sub(t, "(1) you write the answer line; (2) the builder applies wave 1; (3) two reviewers read the CHANGED FILES (not this report); (4) you import the edited flows into n8n and run C-4, then a builder applies row 23; (5) you run the loopback re-smoke and provoke an alert mail (crash test K3), then a builder applies rows 58 and 59; (6) a builder writes the leak scan C-6, a second person (someone who did not write the scan) tests it with a fake key, and it runs after every rehearsal with real accounts and after the take, BEFORE any deletion; (7) at the re-pin you read the take script; (8) you ask the owner: L-SHEET, the scope of his HubSpot key, L-SAVEERR. The long form is in section 1c-F.",
            "(1) you write the answer line; (2) the builder applies wave 1; (3) two reviewers read the CHANGED FILES (not this report); (4) you import the edited flows into n8n and run C-4, then a builder applies row 23; (5) you run the loopback re-smoke and provoke an alert mail (crash test K3), then a builder applies rows 58 and 59; (6) a builder writes the leak scan C-6, a second person tests it with a fake key, and it runs after every rehearsal with real accounts and after the take, BEFORE any deletion; (7) at the re-pin you read the take script; (8) you ask the owner L-SHEET, the scope of his HubSpot key and L-SAVEERR. Long form: section 1c-F.", 1)
    t = sub(t, " (no edit of the scene table; the rehearsal, risk and open-decision items of those scenes are edited by rows 97 to 104).", " (rows 97 to 104 fix only stale items).", 1)
    t = sub(t, " (in your earlier answer 1 of the lease question below, 'claim' means statement)", "", 1)
    t = sub(t, " (1: the 25-word limit sentence of your earlier answer; 2: a 40-word explanation)", " (1: your 25-word limit sentence; 2: a 40-word explanation)", 1)
    t = sub(t, " the long form of every task is in section 1c):", " long form: section 1c):", 1)
    t = sub(t, "the 25-word limit sentence of your earlier answer", "the 25-word limit sentence of your earlier answer", 0) if False else t
    t = sub(t, "TO REVERSE A DEFAULT, you name a builder who puts back the old text of the affected rows (every old text is in the table).", "TO REVERSE A DEFAULT, a builder you name puts back the old text of the rows (it is in the table).", 1)
    t = sub(t, "- TASK (9), A QUESTION TO YOU: neither", "- TASK (9), A QUESTION TO YOU: none of", 1)
    t = sub(t, "OWNER-SHEET-v%d-B.md nor LEAD-RELEASE-NOTE-" % NEWV, "OWNER-SHEET-v%d-B.md and LEAD-RELEASE-NOTE-" % NEWV, 1)
    t = sub(t, "carries the 45-second limit sentence, and your release note strikes it", "carries the 45-second limit sentence; your release note strikes it", 1)
    t = sub(t, " C-4 = import check (load the edited flows into n8n, send one made-up contact, look at the past runs).", " C-4 = import check (load the edited flows into n8n; send one made-up contact).", 1)
    t = sub(t, " It changes no running n8n. Rows 23, 58, 59 and the 6 rows of L-SAVEERR are NOT applied; no row edits the owner sheet or the release note.", " It changes no running n8n; rows 23, 58, 59 and the 6 of L-SAVEERR are NOT applied; no row edits the owner sheet or release note.", 2)
    t = sub(t, "(the stand-in tests showed one; the take's flows are not run)", "(the stand-in tests showed one; the take's flows were not run)", 1)
    t = sub(t, " Names after 'builder' and 'reviewers' are labels no program reads;", " The names are labels no program reads;", 1)
    t = sub(t, " (my reading: for look-up tests only)", "", 1)
    t = sub(t, "; this report is on branch cloud/core-hardening, which holds only one of them)", ")", 1)
    t = sub(t, "reading the final take files. PUBLIC POST = your phrase in ORDERS.md ('the lease sentence stays out of the public post').", "reading the final take files. PUBLIC POST = the post that goes out with the video (your ruling is quoted in section 1c).", 1)
    t = sub(t, "L-SHEET and L-SAVEERR (OWNER ONLY, in the table); G12", "the two OWNER ONLY questions of the table; G12", 1)
    t = sub(t, "a builder writes the leak scan C-6, a second person tests it with a fake key", "a builder writes the leak scan C-6, a second person (someone who did not write the scan) tests it with a fake key", 1)
    t = sub(t, "The c6t box states its real count in its second paragraph and verify-c6v.py recounts it.\n", "The c6t box states its real count in its second paragraph and verify-c6v.py recounts it.\n\n1c-H. THE SAVING PLAN LINE. The plan line PLAN:125 sets both n8n saving settings to all and cites the owner; the owner's words cover successful runs only, so on failed runs the plan line is overridden here (failed runs are not saved unless L-SAVEERR is answered yes by the owner).\n", 1)
    t = sub(t, "L-DEL is ANSWERED (no, never).", "The deletion question is ANSWERED (no, never).", 1)
    t = sub(t, "folder handover/ (the files the rows change)", "folder handover/", 1)
    t = sub(t, "and stops and reports any row where it does not.", "and stops at any row where it does not.", 1)
    t = sub(t, "the old text '30 s EST' has no table border and occurs once on that line; row 96 edits it", "the old text 'own runs. \\| 30 s EST' (the words before the cell make it unique; '30 s EST' alone occurs 3 times in the file) occurs once on that line; row 96 edits it", 1)
    t = sub(t, "4. The two OPEN questions: ask", "4. The two OPEN (OWNER ONLY) questions: ask", 1)
    # row 96 edits the rightmost cell of run sheet line 41; rows 12 to 15 consume the text around it, so it must apply first
    _L = t.split("\n")
    _i96 = [k for k, l in enumerate(_L) if l.startswith("| 96 | NOT APPLIED")]
    _i12 = [k for k, l in enumerate(_L) if l.startswith("| 12 | NOT APPLIED")]
    assert len(_i96) == 1 and len(_i12) == 1, "row 96 or row 12 not found"
    _r = _L.pop(_i96[0])
    _L.insert(_L.index([l for l in _L if l.startswith("| 12 | NOT APPLIED")][0]), _r)
    t = "\n".join(_L)
    return t, NEWV


if __name__ == "__main__":
    words = 2400
    t = None
    for _ in range(4):
        FAILS.clear()
        t, NEWV = build(words)
        body = t[t.index("## Start here: what"):t.index("## Start here, part 2")]
        n = len(body.split("\n", 1)[1].split())
        if n == words:
            break
        words = n
    print("box words (counted without the heading line): stated %d, counted %d" % (words, n))
    if FAILS:
        print("BUILD FAILED:")
        for f in FAILS:
            print("  " + f)
        sys.exit(1)
    open(D + "REPORT-c6v.md", "w", encoding="utf-8").write(t if t.endswith("\n") else t + "\n")
    print("wrote REPORT-c6v.md (%d lines)" % len(t.split("\n")))

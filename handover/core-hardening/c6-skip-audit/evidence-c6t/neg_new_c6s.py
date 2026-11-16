# ---- c6s: one changed copy per new rule (each must be caught)
import shutil, glob as _g
def rep_once(a, b):
    assert rep.count(a) >= 1, a[:70]
    return rep.replace(a, b, 1)
def line_sub(prefix, a, b):
    ls = rep.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith(prefix)][0]
    assert a in ls[i], (prefix, a[:60])
    ls[i] = ls[i].replace(a, b, 1)
    return "\n".join(ls)
M["S-F1a-C4a-says-failed-all"] = line_sub("| C-4a |", "error-none 1", "error-none 0")
M["S-F1b-C11-no-override"] = line_sub("| C-11 |", "overridden", "kept")
M["S-F1c-C4-row-list-old"] = line_sub("| C-4 | Import check", "rows 63, 65, 67, 69 and 92", "rows 63, 62, 65, 64, 67, 66, 69, 68")
M["S-F1d-L-SAVE-no-OVERRIDDEN"] = line_sub("| L-SAVE | studio lead", "OVERRIDDEN", "kept")
M["S-F1e-box-no-override"] = rep_once("the plan is overridden on that point", "the plan is kept on that point")
M["S-F1f-glossary-failed-runs"] = rep_once("all for successful runs and none for failed runs", "all for every run")
M["S-F1g-sec9-plan-bullet-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("- [needs-lead] Failed-run saving, plan conflict"))
M["S-F1h-row92-error-all"] = mut_row(rep, 92, "new", lambda s: s.replace('"saveDataErrorExecution": "none"', '"saveDataErrorExecution": "all"', 1))
M["S-F1i-row63-ready-waits"] = mut_row(rep, 63, "st", lambda s: "NOT APPLIED; waits for the answer of L-SAVEERR (default no)")
M["S-F2a-gate-gone-row8"] = mut_row(rep, 8, "new", lambda s: s.replace("CARD LINE 2 GATE", "CARD LINE 2 NOTE"))
M["S-F2b-3e-row-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| Card line 2, the alert sentence"))
M["S-F2c-box-sentence-gone"] = rep_once("card line 2 stays blocked until the loopback re-smoke", "card line 2 is fine")
M["S-F2d-row14-gated-gone"] = mut_row(rep, 14, "why", lambda s: s.replace("it is gated:", "it is free:"))
def i15(a, b):
    return mut_row(rep, 6, "new", lambda s: s.replace(a, b, 1))
M["S-F3a-item15-first-only"] = i15("After EVERY rehearsal with real accounts", "After the first rehearsal with real accounts")
M["S-F3b-scanner-unreviewed"] = i15("is read by a second person and tested with a fake key before it touches a real key", "is run")
M["S-F3c-key-in-file"] = i15("prints counts only: no file holds the key or any matched line", "prints the matched lines")
M["S-F3d-shell-history"] = i15("not in the list of running programs and not in the shell history", "on the command line")
M["S-F3e-dump-kept"] = i15("the count must be 0", "the dump may stay")
M["S-F3f-swap-gone"] = i15("SWAP POINT", "NOTE")
M["S-F3g-item16-after-deletion-only"] = i15("BEFORE anything is deleted", "after anything is deleted")
M["S-F3h-3e-scan-row-old"] = line_sub("| Real-key scan", "after EVERY rehearsal", "after the first rehearsal")
M["S-F3i-C6-no-second-person"] = line_sub("| C-6 |", "a second person who reads it and tests it with a fake key before it touches a real key", "someone")
M["S-F3j-row6-reason-11-to-14"] = mut_row(rep, 6, "why", lambda s: s.replace("items 11 to 16", "items 11 to 14", 1))
M["S-F4a-newest-line-says-v29"] = rep_once("NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v30", "NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v29")
M["S-F4b-release-note-v13-named"] = rep_once("NEWEST RELEASE NOTE NAMED: v14", "NEWEST RELEASE NOTE NAMED: v13")
M["S-F4c-LRN14-cite-gone-from-box"] = rep_once("LRN14:33", "LRN:33")
M["S-F4d-own-reading-label-gone"] = rep_once("that G12 is about 'processed once' beside a crash scene is this report's own reading", "G12 is about processed once")
M["S-F4e-v30-file-unnamed"] = rep_once("OWNER-SHEET-v30-SOURCE.md (the template", "OWNER-SHEET-v30-X.md (the template")
M["S-F4f-v30-time-wrong"] = re.sub(r"(OWNER-SHEET-v30-A\.md \(written )\d\d:\d\d:\d\d", r"\g<1>10:00:00", rep, count=1)
# environment copies of the steps-edits folder: a higher version, a newer release note, a sheet written after the check time
SNAP = os.environ.get("C6T_SNAPSHOT") or (D + "../steps-edits")
def env_variant(name, fn):
    d = tempfile.mkdtemp()
    src = SNAP
    for f in _g.glob(src + "/OWNER-SHEET-v*.md") + _g.glob(src + "/LEAD-RELEASE-NOTE-v*.md"):
        shutil.copy2(f, d)
    fn(d)
    ENV[name] = d
ENV = {}
def _hi_sheet(d): open(d + "/OWNER-SHEET-v31-A.md", "w").write("x")
def _hi_rn(d): open(d + "/LEAD-RELEASE-NOTE-v15.md", "w").write("x")
def _late(d):
    f = d + "/OWNER-SHEET-v30-A.md"
    t = os.path.getmtime(f) + 7200
    os.utime(f, (t, t))
def _missing(d): os.remove(d + "/OWNER-SHEET-v30-B.md")
env_variant("S-F4g-sheet-v31-exists", _hi_sheet)
env_variant("S-F4h-release-note-v15-exists", _hi_rn)
env_variant("S-F4i-v30-sheet-newer-than-check-time", _late)
env_variant("S-F4j-v30-B-file-missing", _missing)
for _n in ENV:
    M[_n] = rep
M["S-m1a-crash-then-repeat-gone"] = mut_row(rep, 8, "new", lambda s: s.replace("while the recovery flow is still working on it", "later", 1))
M["S-m1b-count-gone"] = mut_row(rep, 8, "new", lambda s: s.replace("1 row and 1 mail", "the lists", 1))
M["S-m2-until-C9-gone"] = mut_row(rep, 13, "why", lambda s: s.replace("expected to be true for a second send until C-9 part 2", "true for a second send", 1))
M["S-m3a-cut-totals-again-in-sec9"] = rep + "\n- [needs-lead] Cut case again: scenes 1, 2 and 4 = 25 s + 40 s + 60 s = 125 s.\n"
M["S-m3b-time-cell-gone"] = rep_once("Old cell text: 30 s EST. New cell text: 40 s EST", "Change the cell.")
M["S-m4-example-time-before-check"] = rep_once("2026-11-16T18:00:00Z = 23:30:00 IST", "2026-11-16T16:40:00Z = 22:10:00 IST")
M["S-N1-reviewer-order-gone"] = rep_once("the ORDER of the two reviewer names matters", "the names matter")
M["S-N2-does-not-list-after-answer"] = rep_once("Know first what the line in step 2 does NOT do", "Know first what the line in step 2 leaves out").replace("TO REVERSE A DEFAULT", "TO REVERSE A DEFAULT (it does NOT do much)", 1)
M["S-N3-lead-may-answer-for-him"] = line_sub("| L-SAVEERR | OWNER ONLY (", "OWNER ONLY (the studio lead asks him and writes down his answer; the studio lead does not answer for him)", "OWNER ONLY (the studio lead may answer for him)")
M["S-N3b-sheet-no-owner-only"] = line_sub("| L-SHEET (was Q10)", "OWNER ONLY", "studio lead")
M["S-N4-circle-gone"] = rep_once("THE CIRCLE IN C-9 PART 2", "C-9 PART 2 NOTE")
M["S-N5-take-it-again"] = rep_once("may claim it again", "may take it again")
M["S-N6-alert-fact"] = rep_once("a warning mail the system is built to send to a person", "the one warning mail the system sends to a person")
M["S-N7-title-c6r"] = rep_once("# REPORT-c6s:", "# REPORT-c6r:")
M["S-N8-row11-gone-from-5a"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| 11 | run sheet, line 44"))
M["S-N9-history-back-in-section0"] = rep_once("## 1b. History of earlier versions", "## 1b. Notes").replace("- HISTORY, c6q (REPORT-c6q.md", "- HISTORY, c6q (REPORT-c6q.md", 1).replace("## 0. Failures", "## 0. Failures\n- HISTORY, c6q is back here.", 1)
M["S-N10-EGM-undefined"] = rep_once("EGM = the studio's review method", "EGM is the studio's review method")
M["S-N11-KEY-undefined"] = rep_once("KEY = a secret code", "KEY is a secret code")
M["S-N12-G12-explanation-gone"] = rep_once("G12 = YOUR gate", "G12 = a gate")
M["S-N13-Q27-explanation-gone"] = rep_once("Q27 (a), (b), (c) = your plan's three questions", "Q27 (a), (b), (c) = three questions")
M["S-N14-step9-gone"] = rep_once("(9) you (or a builder you name) add the 45-second limit sentence", "(9) add the 45-second limit sentence")
M["S-N15-step-row23-gone"] = rep_once("a builder applies row 23", "row 23 is applied")
M["S-N16-box-too-long"] = rep[:box_end] + ("filler words here " * 20) + rep[box_end:]
M["S-N17-sec9-stale-box-bullet"] = rep.rstrip("\n") + "\n- [needs-lead] The box is about 3,490 words: not shortened.\n"
M["S-N18-coverage-block-gone"] = rep_once("COVERAGE OF THE c6r REVIEWS", "COVERAGE")
M["S-N19-c6r-name-in-glossary"] = rep_once("c6s (this file) supersedes c6r", "c6q (this file) supersedes c6p")
M["S-N20-SAVEERR-missing-from-glossary"] = rep_once("L-SAVE, L-SAVEERR, L-PAGE", "L-SAVE, L-PAGE")
M["S-N21-gate-used-before-defined"] = rep_once("Every question below has a default", "Every gate question below has a default")

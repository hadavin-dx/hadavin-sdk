# ---- c6t: one changed copy per new rule (each must be caught). rep = REPORT-c6t.md, box = text up to section 0
BOX = rep[:box_end]
def box_sub(a, b):
    assert BOX.count(a) >= 1, a[:70]
    return rep.replace(a, b, 1)
M["T-E1-first-box-number"] = box_sub("Of the 94 rows, 49 are ready", "Of the 94 rows, 48 are ready")
def _allnum(t):
    for a_, b_ in (("Of the 94 rows", "Of the 95 rows"), ("49 are ready", "50 are ready"), ("36 apply on the default", "37 apply on the default"), ("3 wait for a check", "4 wait for a check"), ("6 wait for the owner", "7 wait for the owner"), ("85 wave 1 rows", "86 wave 1 rows")):
        t = t.replace(a_, b_, 1)
    return t
M["T-E2-all-box-numbers"] = _allnum(BOX) + rep[box_end:]
M["T-E3-three-to-four-checks"] = box_sub("3 wait for a check that needs n8n", "4 wait for a check that needs n8n")
M["T-E4-L-CARD-default-no"] = line_sub("| L-CARD | Does the closing card stay", "| Yes. |", "| No. |")
M["T-E5-L-APPROX-default-flipped"] = line_sub("| L-APPROX | May scene 4", "| No. |", "| Yes. |")
M["T-E6-key-end-tied-to-1829"] = rep_once("cancels the paid key by 18:19 UTC = 23:49 IST", "cancels the paid key by 18:29 UTC = 23:59 IST")
M["T-E7-key-shaped-hyphen"] = rep + "\n- test " + "s" + "k-" + "ant-api03-" + "AAAAAAAAAAAAAAAA" + "\n"
M["T-E7b-ghp-key"] = rep + "\n- test " + "gh" + "p_" + "abcdefghij0123456789" + "\n"
M["T-E8-release-note-v14-to-v15"] = rep_once("LRN14:33 in release note v14", "LRN14:33 in release note v15")
M["T-E9-18-kept-to-17"] = rep_once("the 18 kept crash runs", "the 17 kept crash runs")
M["T-E10-L-SHEET-owner-only-gone-box"] = line_sub("| L-SHEET | OWNER ONLY", "OWNER ONLY", "studio lead")
M["T-E10b-L-SAVEERR-owner-only-gone-sec3"] = line_sub("| L-SAVEERR | OWNER ONLY (", "OWNER ONLY (", "studio lead (")
M["T-E11-ORDER-md-wrong-name"] = box_sub("Open handover/core-hardening/ORDERS.md", "Open handover/core-hardening/ORDER.md")
M["T-E12-title-UTC-5-00"] = rep_once("IST = UTC + 5:30", "IST = UTC + 5:00")
M["T-E13-card-words-11-to-12"] = box_sub("four spoken lines of 11, 35, 22 and 22 words", "four spoken lines of 12, 35, 22 and 22 words")
M["T-E14-R-number-in-box"] = box_sub("WHAT TO TYPE (the whole answer", "WHAT TO TYPE (R447; the whole answer")
M["T-E15-stated-count-wrong"] = re.sub(r"This box holds (\d+) words", lambda m: "This box holds %d words" % (int(m.group(1)) + 7), rep, count=1)
M["T-E16-box-too-long"] = rep[:box_end] + ("filler words here " * 20) + rep[box_end:]
M["T-E17-newest-note-time-wrong"] = re.sub(r"(LEAD-RELEASE-NOTE-v15\.md was written )\d\d:\d\d:\d\d", r"\g<1>10:00:00", rep, count=1)
M["T-E18-LRN-short-table-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| LRN14 |"))
M["T-M1-sheets-carry-sentence"] = rep + "\n- The sheets carry the 45-second sentence.\n"
M["T-M1b-task9-instruction"] = rep_once("TASK (9), A QUESTION TO YOU", "TASK (9) add it")
M["T-M2-lease-words-not-held"] = line_sub("| L-POST (new in c6q)", "HELD under gate G12", "left alone")
M["T-M3a-C12-row-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| C-12 |"))
M["T-M3b-no-provocation"] = rep_once("provoke an ALERT MAIL", "look at the mail")
M["T-M3c-TableB-line2-seconds"] = line_sub("| card line 2 cut", "22.0", "23.0")
M["T-M3d-TableB-lines12-row-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| card lines 1 and 2 cut"))
M["T-M4-shorter-no-count"] = rep + "\n- The box is rewritten and shorter.\n"
M["T-N1-task-number-bare"] = rep_once("TASK (1) write the answer line. TASK (2)", "(1) write the answer line. TASK (2)")
M["T-N2-claim-undefined"] = box_sub("CLAIM always means reserve", "CLAIM means something")
M["T-N3-run-sheet-row"] = box_sub("RUN SHEET = VIDEO-RUNSHEET.md", "RUN SHEET = a run sheet row in VIDEO-RUNSHEET.md")
M["T-N4-not-filmed-gone"] = box_sub("listed, not filmed", "listed")
M["T-N6-option-b-gone"] = box_sub("OPTION (b) OF L-CARDLEN, 74 words", "OPTION B")
M["T-m6-second-person-unnamed"] = rep_once("a second person (someone who did not write the scan)", "a second person")
# environment copies: files written after the check time, higher versions, a missing file
def _late_file(fn):
    def f(d):
        p = d + "/" + fn
        t = os.path.getmtime(p) + 7200
        os.utime(p, (t, t))
    return f
env_variant("T-E19-sheet-v31-A-newer", _late_file("OWNER-SHEET-v31-A.md"))
env_variant("T-E19b-sheet-v31-SOURCE-newer", _late_file("OWNER-SHEET-v31-SOURCE.md"))
env_variant("T-E20-release-note-v15-newer", _late_file("LEAD-RELEASE-NOTE-v15.md"))
env_variant("T-E20b-release-note-v15-SOURCE-newer", _late_file("LEAD-RELEASE-NOTE-v15-SOURCE.md"))
env_variant("T-E21-release-note-v16-exists", lambda d: open(d + "/LEAD-RELEASE-NOTE-v16.md", "w").write("x"))
env_variant("T-E22-sheet-v32-exists", lambda d: open(d + "/OWNER-SHEET-v32-A.md", "w").write("x"))
env_variant("T-E23-sheet-v31-B-missing", lambda d: os.remove(d + "/OWNER-SHEET-v31-B.md"))
for _n in ENV:
    if _n.startswith("T-"):
        M[_n] = rep
M["T-E17b-sheet-v31-time-wrong"] = re.sub(r"(OWNER-SHEET-v31-A\.md \(written )\d\d:\d\d:\d\d", r"\g<1>10:00:00", rep, count=1)
M["T-E24-EGM-undefined-1c"] = rep_once("EGM = the studio's review method", "EGM is the studio's review method")
M["T-E25-assumption-label-gone-box"] = box_sub("MY ASSUMPTION", "THE RULE")
M["T-E26-own-reading-gone-box"] = box_sub("this report's own reading", "a fact")

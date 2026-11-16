# ---- c6u: one changed copy per new rule (each must be caught). rep = REPORT-c6u.md, box = text up to section 0
BOX = rep[:box_end]
def box_sub(a, b):
    assert BOX.count(a) >= 1, a[:70]
    return rep.replace(a, b, 1)
M["T-E1-first-box-number"] = box_sub("READY (57:", "READY (56:")
def _allnum(t):
    for a_, b_ in (("READY (49:", "READY (50:"), ("ON DEFAULT (38:", "ON DEFAULT (39:"), ("WAITS FOR A CHECK (3:", "WAITS FOR A CHECK (4:"), ("WAITS FOR THE OWNER (6:", "WAITS FOR THE OWNER (7:"), ("applies the 87 wave 1 rows", "applies the 86 wave 1 rows")):
        t = t.replace(a_, b_, 1)
    return t
M["T-E2-all-box-numbers"] = _allnum(BOX) + rep[box_end:]
M["T-E3-three-to-four-checks"] = box_sub("WAITS FOR A CHECK (3:", "WAITS FOR A CHECK (4:")
M["T-E4-L-CARD-default-no"] = line_sub("| L-CARD | Does the closing card stay", "| Yes. |", "| No. |")
M["T-E5-L-APPROX-default-flipped"] = line_sub("| L-APPROX | May scene 4", "| No. |", "| Yes. |")
M["T-E6-key-end-tied-to-1829"] = rep_once("cancels the paid key by 18:19 UTC = 23:49 IST", "cancels the paid key by 18:29 UTC = 23:59 IST")
M["T-E7-key-shaped-hyphen"] = rep + "\n- test " + "s" + "k-" + "ant-api03-" + "AAAAAAAAAAAAAAAA" + "\n"
M["T-E7b-ghp-key"] = rep + "\n- test " + "gh" + "p_" + "abcdefghij0123456789" + "\n"
M["T-E8-release-note-v14-to-v16"] = rep_once("LRN14:33 in release note v14", "LRN14:33 in release note v16")
M["T-E9-18-kept-to-17"] = rep_once("the 18 kept crash runs", "the 17 kept crash runs")
M["T-E10-L-SHEET-owner-only-gone-box"] = line_sub("| L-SHEET | Which ONE", "OPEN (OWNER ONLY)", "OPEN")
M["T-E10b-L-SAVEERR-owner-only-gone-sec3"] = line_sub("| L-SAVEERR | OWNER ONLY (", "OWNER ONLY (", "studio lead (")
M["T-E11-ORDER-md-wrong-name"] = box_sub("end of handover/core-hardening/ORDERS.md", "end of handover/core-hardening/ORDER.md")
M["T-E12-title-UTC-5-00"] = rep_once("IST = UTC + 5:30", "IST = UTC + 5:00")
M["T-E13-card-words-11-to-12"] = rep_once("line 1 (11 words)", "line 1 (12 words)")
M["T-E14-R-number-in-box"] = box_sub("WHAT TO TYPE (capital-letter", "WHAT TO TYPE (R447; capital-letter")
M["T-E15-stated-count-wrong"] = re.sub(r"This box holds (\d+) words", lambda m: "This box holds %d words" % (int(m.group(1)) + 7), rep, count=1)
M["T-E16-box-too-long"] = rep[:box_end] + ("filler words here " * 20) + rep[box_end:]
M["T-E17-newest-note-time-wrong"] = re.sub(r"(LEAD-RELEASE-NOTE-v\d+\.md was written )\d\d:\d\d:\d\d", r"\g<1>10:00:00", rep, count=1)
M["T-E18-LRN-short-table-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| LRN14 |"))
M["T-M1-sheets-carry-sentence"] = rep + "\n- The sheets carry the 45-second sentence.\n"
M["T-M1b-task9-instruction"] = rep_once("TASK (9), A QUESTION TO YOU", "TASK (9) add it")
M["T-M2-lease-words-not-held"] = line_sub("| L-POST (new in c6q)", "HELD under gate G12", "left alone")
M["T-M3a-C12-row-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| C-12 |"))
M["T-M3b-no-provocation"] = rep_once("provoke an ALERT MAIL", "look at the mail")
M["T-M3c-TableB-line2-seconds"] = line_sub("| card line 2 cut", "22.0", "23.0")
M["T-M3d-TableB-lines12-row-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| card lines 1 and 2 cut"))
M["T-M4-shorter-no-count"] = rep + "\n- The box is rewritten and shorter.\n"
M["T-N1-task-number-bare"] = rep_once("TASKS, in this order: TASK (1) write the answer line;", "TASKS, in this order: (1) write the answer line;")
M["T-N2-claim-undefined"] = box_sub("CLAIM always means reserve", "CLAIM means something")
M["T-N3-run-sheet-row"] = box_sub("RUN SHEET = VIDEO-RUNSHEET.md", "RUN SHEET = a run sheet row in VIDEO-RUNSHEET.md")
M["T-N4-not-filmed-gone"] = box_sub("listed, not filmed", "listed")
M["T-N6-option-b-gone"] = rep_once("OPTION (b) OF L-CARDLEN, 74 words", "OPTION B")
M["T-m6-second-person-unnamed"] = rep_once("a second person (someone who did not write the scan)", "a second person")
# environment copies: files written after the check time, higher versions, a missing file
def _late_file(fn):
    def f(d):
        p = d + "/" + fn
        t = os.path.getmtime(p) + 7200
        os.utime(p, (t, t))
    return f
env_variant("T-E19-sheet-v32-A-newer", _late_file("OWNER-SHEET-v32-A.md"))
env_variant("T-E19b-sheet-v32-SOURCE-newer", _late_file("OWNER-SHEET-v32-SOURCE.md"))
env_variant("T-E20-release-note-v16-newer", _late_file("LEAD-RELEASE-NOTE-v16.md"))
env_variant("T-E20b-release-note-v16-SOURCE-newer", _late_file("LEAD-RELEASE-NOTE-v16-SOURCE.md"))
env_variant("T-E21-release-note-v17-exists", lambda d: open(d + "/LEAD-RELEASE-NOTE-v17.md", "w").write("x"))
env_variant("T-E22-sheet-v33-exists", lambda d: open(d + "/OWNER-SHEET-v33-A.md", "w").write("x"))
env_variant("T-E23-sheet-v32-B-missing", lambda d: os.remove(d + "/OWNER-SHEET-v%s-B.md" % re.search(r"OWNER-SHEET-v(\d+)-A\.md \(written", rep).group(1)))
for _n in ENV:
    if _n.startswith("T-"):
        M[_n] = rep
M["T-E17b-sheet-v32-time-wrong"] = re.sub(r"(OWNER-SHEET-v\d+-A\.md \(written )\d\d:\d\d:\d\d", r"\g<1>10:00:00", rep, count=1)
M["T-E24-EGM-undefined-1c"] = rep_once("EGM = the studio's review method", "EGM is the studio's review method")
M["T-E25-assumption-label-gone-box"] = box_sub("MY ASSUMPTION", "THE RULE")
M["T-E26-own-reading-gone-box"] = box_sub("this report's own reading", "a fact")

# ---- c6u: the 14 changes the c6t verifier missed (c6t independent evidence), each as FIRST copy only and as ALL copies; the check must fail on both
def _fa(tag, a, b):
    assert rep.count(a) >= 2, (tag, a, rep.count(a))
    M["U-" + tag + "-first"] = rep.replace(a, b, 1)
    M["U-" + tag + "-all"] = rep.replace(a, b)
_fa("rows-23-58-59", "23, 58, 59", "23, 58, 60")
_fa("rows-90-91", "90, 91", "90, 92")
_fa("card-words-90", "90 words", "91 words")
_fa("card-seconds-36", "about 36 s", "about 38 s")
_fa("option-b-74-word", "74-word", "144-word")
_fa("budget-40", "budget 40 s", "budget 45 s")
_fa("lease-45-second", "45-second", "55-second")
_fa("wakes-30", "every 30 seconds", "every 20 seconds")
_fa("lrn14-149", "LRN14:149", "LRN14:148")
_fa("ord-150", "ORD:150", "ORD:151")
_fa("runs-18", "18 stand-in crash runs", "17 stand-in crash runs")
_fa("delay-13", "13-minute", "12-minute")
M["U-relayed-2-first"] = rep_once("(2 relayed runs)", "(3 relayed runs)")
M["U-lease-within-45"] = rep.replace("second send comes within 45 seconds", "second send comes within 55 seconds", 1)
M["U-kept-18-first"] = rep.replace("the 18 kept runs", "the 17 kept runs", 1)
# ---- c6u: the rules new in c6u
M["U-row95-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| 95 | NOT APPLIED"))
M["U-row96-gone"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| 96 | NOT APPLIED"))
M["U-row53-chain-broken"] = line_sub("| 53 | NOT APPLIED", "n8n stores no run data for runs that fail.", "n8n stores nothing for runs that fail.")
M["U-row76-audited-sentence-back"] = rep + "\n- the program is not among the audited files.\n"
M["U-box-count-96-to-95"] = box_sub("holds 104 proposed text changes", "holds 103 proposed text changes")
M["U-box-too-long"] = rep[:box_end] + ("filler words here " * 130) + rep[box_end:]
M["U-two-statuses-L-SAVEERR-sec3-default-no"] = rep_once("| OPEN (OWNER ONLY). Until he answers, failed runs stay unsaved", "| No (the lowest-data choice); failed runs stay unsaved")
M["U-B4-unverified-gone"] = box_sub("equality with the real files is UNVERIFIED", "all is fine")
M["U-B5-defaults-leave-gone"] = box_sub("WHAT THE DEFAULTS LEAVE", "NOTE")
M["U-part2-card-words-wrong"] = rep_once("line 2 (35 words)", "line 2 (36 words)")
M["U-L-SHEET-v32-time-missing"] = re.sub(r"(OWNER-SHEET-v\d+-B\.md) \(written [^)]*\)", r"\1", rep, count=1)
M["U-steps-5-to-9-back"] = rep_once("after TASKS (5) to (9) of the list", "after steps 5 to 9 of the list")
M["U-example-time-before-check"] = rep_once(EX1TXT, "2026-11-16T16:40:00Z = 22:10:00 IST")
M["U-row96-old-text-not-once"] = line_sub("| 96 | NOT APPLIED", "`own runs. \\| 30 s EST`", "`own runs. \\| 31 s EST`")
M["U-stale-evidence-c6t-name"] = rep.replace("evidence-c6w/contact-grep-output.txt", "evidence-c6u/contact-grep-output.txt", 1)
M["U-applied-rows-c6t-name"] = rep.replace("c6w-APPLIED-ROWS.md", "c6u-APPLIED-ROWS.md", 1)
M["U-evidence-file-missing"] = rep_once("evidence-c6w/contact-grep-output.txt", "evidence-c6w/no-such-file.txt")

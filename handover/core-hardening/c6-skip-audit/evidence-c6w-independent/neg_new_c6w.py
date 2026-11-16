# ---- c6w: one changed copy per MISSED mutant class of the independent run on c6u (mutations-raw.tsv, mutations-raw-batch2.tsv). rep = REPORT-c6w.md
def _nth(a, b, n):
    """replace the n-th (0-based) occurrence of a by b; None if there are fewer"""
    idx = -1
    for _ in range(n + 1):
        idx = rep.find(a, idx + 1)
        if idx < 0:
            return None
    return rep[:idx] + b + rep[idx + len(a):]
def _all(a, b):
    return rep.replace(a, b) if a in rep else None
# G12 gate: safe default reversed (one copy, and every copy)
for _n in (0, 1, 2):
    M["W-G12-gate-flipped-copy%d" % _n] = _nth("I do not approve it", "I approve it", _n)
M["W-G12-gate-flipped-all"] = _all("I do not approve it", "I approve it")
M["W-G12-OPEN-to-CLOSED"] = _all("G12 OPEN", "G12 CLOSED")
for _n in (0, 2):
    M["W-G12-open-to-closed-copy%d" % _n] = _nth("G12 open", "G12 closed", _n)
M["W-G12-open-is-open-to-approved"] = _nth("G12 is still OPEN", "G12 is approved by default", 0)
M["W-NOTHING-APPLIED-to-EVERYTHING"] = _nth("NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE", "EVERYTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE", 0)
M["W-NOTHING-APPLIED-sentence-deleted"] = _nth("NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE", "", 0)
M["W-take-no-delete-to-has-delete"] = _nth("has NO delete call", "has a delete call", 0)
M["W-no-delete-call-second-copy"] = _nth("no delete call", "a delete call", 1)
M["W-archive-contacts-no-to-yes"] = _nth("archive_contacts 'no'", "archive_contacts 'yes'", 0)
M["W-only-made-up-contacts-to-any"] = _nth("only made-up contacts of this run", "any contacts of any run", 0)
M["W-L-DEL-no-never-to-yes-sometimes-1"] = _nth("no, never", "yes, sometimes", 0)
M["W-L-DEL-no-never-to-yes-sometimes-2"] = _nth("no, never", "yes, sometimes", 1)
_i = rep.index("| L-LEASE | studio lead")
_j = rep.index("\n", _i)
_cells = rep[_i:_j].split(" | ")
_cells[4] = _cells[4].replace("No", "Yes", 1)
M["W-L-LEASE-Confirmed-No-to-Yes"] = rep[:_i] + " | ".join(_cells) + rep[_j:]
for _n in (0, 5, 10, 15, 20, 26):
    M["W-UNVERIFIED-to-VERIFIED-%d" % _n] = _nth("UNVERIFIED", "VERIFIED", _n)
M["W-UNVERIFIED-to-CHECKED"] = _nth("UNVERIFIED", "CHECKED", 3)
M["W-UNVERIFIED-deleted"] = _nth(" UNVERIFIED", "", 7)
M["W-ORD230-quote-deleted-1"] = _nth("lease sentence stays out of the public post", "", 0)
M["W-ORD230-quote-deleted-last"] = _nth("lease sentence stays out of the public post", "", 2)
M["W-filmed-only-after-approval-deleted"] = _nth("Those words are filmed only after your written approval; otherwise you cut them by hand.", "", 0)
M["W-10-files-to-12"] = _nth("to 10 files", "to 12 files", 0)
M["W-twelve-TASKS-to-ten"] = _nth("twelve numbered TASKS", "ten numbered TASKS", 0)
M["W-two-OPEN-to-three-1"] = _nth("two OPEN", "three OPEN", 0)
M["W-wave1-95-to-96-one-place"] = _nth("95 wave 1 rows", "96 wave 1 rows", 0)
M["W-ready-57-to-56-one-place"] = _nth("57 ready", "56 ready", 0)
M["W-rows-104-to-105-one-place"] = _nth("104 rows", "105 rows", 0)
M["W-sheet-version-v33-to-v32-one-place"] = _nth("holds OWNER-SHEET-v"+re.search(r"OWNER-SHEET-v(\d+)-A\.md \(written", rep).group(1), "holds OWNER-SHEET-v0"+re.search(r"OWNER-SHEET-v(\d+)-A\.md \(written", rep).group(1), 0)
M["W-check-time-one-second-off"] = _nth("At 18:29:49 UTC", "At 18:29:50 UTC", 0) if "At 18:29:49 UTC" in rep else _nth("check time", "check time (changed)", 0)
# card line 3 (retention): edit ONE copy
_q3 = "The made-up name and e-mail address sent to n8n may stay in n8n's own database; we did not measure for how long."
M["W-card-line-3-one-copy-edited"] = _nth(_q3, _q3.replace("we did not measure for how long", "it is deleted at once"), 1)
M["W-card-line-3-first-copy-edited"] = _nth(_q3, _q3.replace("may stay", "never stays"), 0)
M["W-card-line-2-one-copy-edited"] = _nth("We make no statement about how quickly an alert mail arrives.", "An alert mail arrives within 30 seconds.", 1)
M["W-card-line-1-one-copy-edited"] = _nth('A lead sent twice with the same id is processed once.', 'A lead sent twice with the same id is never processed twice.', 2)
# pipe in a table cell not escaped (row 96)
M["W-row96-pipe-unescaped"] = _nth("`own runs. \\| 30 s EST`", "`own runs. | 30 s EST`", 0)
M["W-row96-anchor-30-s-EST-only"] = _nth("`own runs. \\| 30 s EST`", "`30 s EST`", 0)
# rows moved: row 96 after row 12 (it then cannot apply on the text row 14 changed)
_L = rep.split("\n")
_a = [k for k, l in enumerate(_L) if l.startswith("| 96 | NOT APPLIED")][0]
_b = [k for k, l in enumerate(_L) if l.startswith("| 15 | NOT APPLIED")][0]
_r = _L.pop(_a); _L.insert(_b + 1, _r)
M["W-row96-after-row15-order"] = "\n".join(_L)
# box over the cap by adding words (the stated count then differs from the real count)
M["W-box-extra-words"] = _nth("## Start here: what I need from you", "## Start here: what I need from you now and also " + "word " * 40, 0)

# ---- c6w class 7: the 7 classes the independent run on c6v missed (one changed copy at EVERY copy), and each defect class of the two c6v reviews restored
_ct8 = _ctn[11:19]
_ctn2 = _ctn[:17] + ("%02d" % ((int(_ctn[17:19]) + 1) % 60)) + "Z"
for _n in range(0, rep.count("at the check time " + _ct8 + " UTC")):
    M["W-C7-check-time-changed-copy%d" % _n] = _nth("at the check time " + _ct8 + " UTC", "at the check time " + _ctn2[11:19] + " UTC", _n)
M["W-C7-check-time-Z-form-changed"] = _nth(_ct8 + "Z = ", _ctn2[11:19] + "Z = ", 0)
for _n in range(0, rep.count("OWNER-SHEET-v34-A.md")):
    M["W-C7-sheet-v34A-to-v33A-copy%d" % _n] = _nth("OWNER-SHEET-v34-A.md", "OWNER-SHEET-v33-A.md", _n)
M["W-C7-Five-to-Four"] = _nth("Five items are OPEN", "Four items are OPEN", 0)
for _n in range(0, rep.count("line 33")):
    M["W-C7-line33-to-34-copy%d" % _n] = _nth("line 33", "line 34", _n)
for _n in range(0, rep.count("LRN14:33")):
    M["W-C7-LRN14-33-to-34-copy%d" % _n] = _nth("LRN14:33", "LRN14:34", _n)
for _n in range(0, rep.count("release note v18")):
    M["W-C7-v18-to-v17-copy%d" % _n] = _nth("release note v18", "release note v17", _n)
for _n in range(0, rep.count("LEAD-RELEASE-NOTE-v18.md")):
    M["W-C7-v18-file-to-v17-copy%d" % _n] = _nth("LEAD-RELEASE-NOTE-v18.md", "LEAD-RELEASE-NOTE-v17.md", _n)
_ll_idx = [k for k, l in enumerate(rep.split("\n")) if l.startswith("| L-LEASE |") and "45-second" in l]
for _n, _k in enumerate(_ll_idx):
    _Ls = rep.split("\n"); _Ls[_k] = _Ls[_k].replace("G12", "xxx"); M["W-C7-L-LEASE-G12-hold-removed-line%d" % _n] = "\n".join(_Ls)
_cb = rep.count("cannot be filmed")
for _n in range(0, _cb):
    M["W-C7-cannot-to-can-copy%d" % _n] = _nth("cannot be filmed", "can be filmed", _n)
# defect classes of the c6v reviews, restored
M["W-C7-answer-line-names-c6v"] = _nth("c6w apply all defaults to REPORT-c6w.md", "c6v apply all defaults to REPORT-c6v.md", 0)
M["W-C7-answer-line-label-only"] = _nth("c6w apply all defaults to REPORT-c6w.md", "c6w apply all defaults to REPORT-c6v.md", 0)
M["W-C7-lines-8-33-149-equal"] = _nth("its lines 8 and 149 differ", "its lines 8, 33, 149 and 150 equal the newest note", 0)
M["W-C7-two-G12-forms"] = _nth("only after the loopback re-smoke of TASK (5)", "only after the loopback re-smoke of TASK (5)", 0) if False else _nth("`## G12 (studio lead, <UTC> = <IST>): approved:", "`## G12 (studio lead, <UTC> = <IST>): lease wording approved:", 0)
M["W-C7-lease-wording-approved-added"] = _nth("a second person", "lease wording approved, a second person", 0)
for _k in (1, 19):
    M["W-C7-row%d-G12-hold-removed" % _k] = mut_row(rep, _k, "view", lambda x: x.replace("G12", "xxx")) if "G12" in PAT.match(L[rowidx(_k)]).group(5) + PAT.match(L[rowidx(_k)]).group(7) + PAT.match(L[rowidx(_k)]).group(8) else None
M["W-C7-row96-back-to-35s"] = mut_row(rep, 96, "new", lambda x: x.replace("40 s EST", "35 s EST"))
M["W-C7-undefined-L-label"] = _nth("L-CARDLEASE", "L-CARDNOPE", 0)
M["W-C7-before-rehearsal-list-5-to-9"] = _nth("TASKS (1) to (6) and (8) to (10)", "TASKS (1) to (6) and (8) to (9)", 1)
M["W-C7-v30A-example"] = _nth("v34 rendering A", "v30A", 0)
M["W-C7-stale-label-c6u-this-file"] = _nth("c6w (this file) supersedes c6v", "c6u (this file) supersedes c6t", 0)
M["W-C7-sheet-A-wording"] = _nth("the A file and the B file of one checklist", "sheet A and sheet B of one checklist", 0)
M["W-C7-further-round-paragraph-deleted"] = _nth("EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND", "ANSWERS", 0)
M["W-C7-branch-statement-90-to-91"] = _nth("it holds the files of 90 rows", "it holds the files of 91 rows", 0)
M["W-C7-box-count-stated-wrong"] = _nth("This box holds ", "This box holds 1", 0)
M["W-C7-roles-sentence-deleted"] = _nth("; if you are also the owner, the two roles stay separate", "", 0)
M["W-C7-labels-bullet-PRIMARY-KEY-deleted"] = _nth("PRIMARY KEY =", "PRIMARY =", 0)
M["W-C7-run-count-deleted"] = _nth("I ran the full pipeline run_all.sh", "I ran the pipeline", 0)
M["W-C7-L-LEASE-reversal-sentence-deleted"] = _nth("THE DEFAULT REVERSES YOUR ANSWER Q22 (c) (ORD:186)", "THE DEFAULT FOLLOWS ORD:230", 0)

M["W-C7-late-file-unnamed"] = _nth("LEAD-RELEASE-NOTE-v19.md was written", "LEAD-RELEASE-NOTE-v19.md was seen", 0)
M["W-C7-late-file-time-deleted"] = _nth("OWNER-SHEET-v35-A.md was written", "OWNER-SHEET-v35-A.md exists", 0)

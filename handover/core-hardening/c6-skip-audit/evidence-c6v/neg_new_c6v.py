# ---- c6v: one changed copy per MISSED mutant class of the independent run on c6u (mutations-raw.tsv, mutations-raw-batch2.tsv). rep = REPORT-c6v.md
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
M["W-G12-open-is-open-to-approved"] = _nth("G12 is open", "G12 is approved by default", 0)
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
M["W-10-files-to-12-second"] = _nth("to 10 files", "to 12 files", 1)
M["W-twelve-TASKS-to-ten"] = _nth("twelve numbered TASKS", "ten numbered TASKS", 0)
M["W-two-OPEN-to-three-1"] = _nth("two OPEN", "three OPEN", 0)
M["W-two-OPEN-to-three-2"] = _nth("two OPEN", "three OPEN", 1)
M["W-wave1-95-to-96-one-place"] = _nth("95 wave 1 rows", "96 wave 1 rows", 0)
M["W-ready-57-to-56-one-place"] = _nth("57 ready", "56 ready", 0)
M["W-rows-104-to-105-one-place"] = _nth("104 rows", "105 rows", 0)
M["W-sheet-version-v33-to-v32-one-place"] = _nth("holds OWNER-SHEET-v33", "holds OWNER-SHEET-v32", 0)
M["W-check-time-one-second-off"] = _nth("At 18:29:49 UTC", "At 18:29:50 UTC", 0) if "At 18:29:49 UTC" in rep else _nth("check time", "check time (changed)", 0)
# card line 3 (retention): edit ONE copy
_q3 = "The made-up name and e-mail address sent to n8n may stay in n8n's own database; we did not measure for how long."
M["W-card-line-3-one-copy-edited"] = _nth(_q3, _q3.replace("we did not measure for how long", "it is deleted at once"), 1)
M["W-card-line-3-first-copy-edited"] = _nth(_q3, _q3.replace("may stay", "never stays"), 0)
M["W-card-line-2-one-copy-edited"] = _nth("We make no statement about how quickly an alert mail arrives.", "An alert mail arrives within 30 seconds.", 1)
M["W-card-line-1-one-copy-edited"] = _nth('A lead sent twice with the same id is processed once.', 'A lead sent twice with the same id is never processed twice.', 2)
# pipe in a table cell not escaped (row 96)
M["W-row96-pipe-unescaped"] = _nth("`own runs. \\| 35 s EST`", "`own runs. | 35 s EST`", 0)
M["W-row96-anchor-30-s-EST-only"] = _nth("`own runs. \\| 30 s EST`", "`30 s EST`", 0)
# rows moved: row 96 after row 12 (it then cannot apply on the text row 14 changed)
_L = rep.split("\n")
_a = [k for k, l in enumerate(_L) if l.startswith("| 96 | NOT APPLIED")][0]
_b = [k for k, l in enumerate(_L) if l.startswith("| 15 | NOT APPLIED")][0]
_r = _L.pop(_a); _L.insert(_b + 1, _r)
M["W-row96-after-row15-order"] = "\n".join(_L)
# box over the cap by adding words (the stated count then differs from the real count)
M["W-box-extra-words"] = _nth("## Start here: what I need from you", "## Start here: what I need from you now and also " + "word " * 40, 0)


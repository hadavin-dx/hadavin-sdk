import re
old = open("report_c6m.py", encoding="utf-8").read().split("\n")
def seg(a, b): return "\n".join(old[a-1:b]) + "\n"
head = seg(1, 57).replace("writes REPORT-c6l.md", "writes REPORT-c6m.md")
new_head = open("new_head.py", encoding="utf-8").read()
sec2 = seg(94, 118)
sec2 = sec2.replace("evidence-c6l", "evidence-c6m")
sec2 += 'P("N = number of runs (so n=2 means 2 runs). The setting label (lease 45 s) and the live stopwatch are not timing numbers (Words). The kill-to-final and from-n8n-up figures are for the 18 KEPT runs only; the two voided runs are described in section 0.")\nP("")\n'
part3 = open("part3.py", encoding="utf-8").read()
gl = seg(155, 210)
gl = gl.replace('("L-CARD, L-KILL, L-ROUND, L-SHEET, L-LEASE, L-DEL, L-SAVE, L-PAGE, L-ONEDB, L-CUT", "the open questions of section 3 (L = question for the studio lead or the owner).", "section 3"),',
  '("L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE, L-KILL, L-APPROX, L-SAVE, L-PAGE, L-ONEDB, L-SHEET, L-DEL, L-CUT", "the questions of section 3 (L = question for the studio lead or the owner); plain meanings are in the box at the top.", "section 3"),')
gl = gl.replace('("c6b to c6l", "successive versions of this audit report; c6l (this file) supersedes c6k;', '("c6b to c6m", "successive versions of this audit report; c6m (this file) supersedes c6l;')
gl = gl.replace('("ORDERS.md answer Q21.2, Q21.3", "numbered answers inside ORDERS.md (the studio lead\'s file): Q21.2 is the statement wording and the lease sentence, Q21.3 the caption for the number of databases.',
  '("ORDERS.md answers Q19 to Q34", "numbered answers inside ORDERS.md (the studio lead\'s file): Q19 item 1 the take program, Q21.1 dates, Q21.2 the statement wording and the lease sentence, Q21.3 the caption for the number of databases, Q22 option (c), Q23 the take never deletes, Q25 cancel-by time, Q27 the studio lead reads the take script at the final version.')
gl = gl.replace('"ORD:151, ORD:152"', '"ORD:150 to ORD:191"')
gl = gl.replace("for t, m, s in G:", '''G += [
    ("n8n, HubSpot, CRM, EGM, import, execution list", "n8n = the workflow tool that runs the flows; HubSpot = the web service that stores the sales contacts (a CRM = customer-record system); EGM = the studio's review method with independent reviewers; import = loading a flow file into n8n; execution list = n8n's screen of past runs.", "Words"),
    ("take script, old desk test program, probe script", "scripts/run_real_check_n8n.py is the take script (the video uses it); scripts/run_real_check.py is the older desk test program (not the take); scripts/hubspot_probe.py tests the HubSpot key. None is in the checked files.", "ORD:%d" % find("ORD", "1. The take program")),
    ("scratchpad/c6/tree/handover, origin/cloud/flows-audit, cloud/core-hardening", "developer paths: a read-only copy of the files of git branch origin/cloud/flows-audit, made in the build session's temporary folder; cloud/core-hardening is the branch this report sits on. Every path in the report is a path inside the repository.", "section 0"),
    ("kept run, voided run, n", "see Words at the top of the report.", "Words"),
]
for t, m, s in G:''')
tbl = '''# ---------------------------------------------------------------- edit table
OLDK = json.load(open(C6 + "/evidence-c6l/edits.json"))
SPLIT = {"rs41b": ["rs41b1", "rs41b2"]}
was = {}
for o in OLDK:
    for nk in SPLIT.get(o["key"], [o["key"]]):
        was.setdefault(nk, []).append("row %d" % o["n"])
P("## 5. EDIT TABLE (every row: NOT APPLIED)")
P("Rows are in apply order (section 1). Paths are paths inside the repository (section 0). 'What the viewer sees' says what a person watching the video or reading the page sees differently. 'Was (c6l)' gives the row number the same edit had in REPORT-c6l.md ('new' = no such row there). Sources use the short names of section 1.")
P("")
P("| ID | Status | Target file (path inside the repository) | Line before any edit | What the viewer sees | Old text (exact) | New text (exact) | Reason and source file:line | Was (c6l) |")
P("|---|---|---|---|---|---|---|---|---|")
for e in EDITS:
    P("| %d | %s | %s | %d | %s | `%s` | `%s` | %s Sources: %s | %s |" % (e["n"], status(e), F[e["fk"]][1], e["line"], e["view"], cell(e["old"]), cell(e["new"]), e["why"], e["src"], "; ".join(was.get(e["key"], ["new"]))))
P("")
P("Row numbers of REPORT-c6l.md mapped to the IDs of this report (every other section uses only the IDs of this report):")
P("")
P("| c6l row (name there) | ID(s) now |")
P("|---|---|")
for o in OLDK:
    P("| %d (%s) | %s |" % (o["n"], o["key"], ids(SPLIT.get(o["key"], [o["key"]]))))
P("")

'''
part6 = open("part6.py", encoding="utf-8").read()
s7 = seg(259, 292)
s7 = s7.replace("evidence-c6l", "evidence-c6m").replace("verify-c6l", "verify-c6m")
# C-10 rows replaced
s7 = re.sub(r'P\("\| C-9 \|.*\n', lambda m: m.group(0).replace("any hit", "any hit"), s7)
s7 = s7.replace("then the studio lead writes 'index not seen, accepted' on the sheet", "FAIL: the studio lead may only write 'index not seen, accepted' on the run sheet, with UTC and IST time and name, as an allowance, not a pass; or the statement is not filmed; the studio lead writes 'index not seen, accepted' on the run sheet")
s7 = re.sub(r'P\("\| C-10b \|.*\n', '''P("| C-10b | Take script: two searches of scripts/run_real_check_n8n.py at the final version, one for the word archive and one for the word delete, output written on the run sheet; also the old desk test program and the probe script named, not used by the take | studio lead at the re-pin (ORDERS.md Q27) | the take script has no archive or delete call, or only (b) own contacts archived and the owner sheet says so | any other call | NOT RUN, UNVERIFIED; missing input: the script is not in the checked files (needs-lead) |")\n''', s7)
s7 = re.sub(r'P\("\| C-10c \|.*\n', '''P("| C-10c | The owner sheet the owner reads: grep -n -i -E 'never deletes|read, create and change only|does not delete' on each sheet | me for the sheets on disk; studio lead for the final sheet | the sheet says the owner deletes leftovers by hand and does not say the HubSpot key is read-only or create-and-change-only unless the owner confirmed it (Q20 item 3) | any other statement of the key's scope | part 1 DONE on the sheets on disk (v19 to v25 and v26-SOURCE, evidence-c6m/static-checks-output.txt section C-10c: v19 1 hit, others 0 for these phrases); v26-SOURCE was still being edited at 15:05 UTC; part 2 NOT RUN; missing input: L-SHEET (needs-owner) |")\n''', s7)
s7 = re.sub(r'P\("\| C-10d \|.*\n', '''P("| C-10d | Decisions file: decision 2 still reads 'the take never deletes' (it is the answer Q23 keeps) | me, file read | decision 2 line present once | line missing or changed | DONE: no 0-hit requirement any more (it was unsatisfiable by construction in REPORT-c6l.md) |")\n''', s7)
s7 += '''P("| C-4 and C-6 as a gate | The run sheet blocks the take until the import check (C-4) and the leak scan for saved runs (C-6) are both written as passed, each with UTC and IST time and a name | studio lead (owner of the gate); a builder he names writes the scan | two lines present before the take | either line missing | Row %d item 14; NOT RUN |" % n("rs71"))
P("")
'''
tail = part6 + seg(259, 259)[:0]
part8 = open("part8.py", encoding="utf-8").read()
part9 = open("part9.py", encoding="utf-8").read()
src = head + new_head + "\n" + sec2 + "\n" + part3 + "\n" + gl + "\n" + tbl + part6 + "\n" + s7 + "\n" + part8 + part9
open("report_c6m.py", "w", encoding="utf-8").write(src)
print("ok", len(src))

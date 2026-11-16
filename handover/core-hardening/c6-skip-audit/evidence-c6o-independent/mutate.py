"""Plants mutations in COPIES of REPORT-c6o.md and runs indep_check.py on each. Fake secrets built from parts. Never edits the report."""
import re, subprocess, sys, os
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6o-independent/"
os.makedirs(E + "mut", exist_ok=True)
rep = open(D + "REPORT-c6o.md", encoding="utf-8").read()
L = rep.split("\n")
def rowline(k): return [i for i, l in enumerate(L) if l.startswith("| %d | NOT APPLIED" % k)][0]
def rep1(t, a, b, nth=0):
    idx = -1
    for _ in range(nth + 1):
        idx = t.index(a, idx + 1)
    return t[:idx] + b + t[idx + len(a):]
M = {}
def row_old_edit(t):
    ls = t.split("\n"); i = rowline(1); ls[i] = ls[i].replace("`Scene 4 caption (FINAL", "`Scene 4 caption (FINAL!", 1); return "\n".join(ls)
M["01-old-text-altered-row1"] = row_old_edit
def line_shift(t):
    ls = t.split("\n"); i = rowline(5); m = re.match(r"^(\| 5 \| [^|]*\| [^|]*\| )(\d+)( \|.*)$", ls[i]); ls[i] = m.group(1) + str(int(m.group(2)) + 1) + m.group(3); return "\n".join(ls)
M["02-row5-line-number-off-by-one"] = line_shift
def del_row(t):
    ls = t.split("\n"); del ls[rowline(50)]; return "\n".join(ls)
M["03-row50-deleted"] = del_row
def dup_id(t):
    ls = t.split("\n"); i = rowline(20); ls[i] = ls[i].replace("| 20 |", "| 19 |", 1); return "\n".join(ls)
M["04-duplicate-id-19"] = dup_id
def status_flip(t):
    ls = t.split("\n"); i = rowline(2); ls[i] = ls[i].replace("NOT APPLIED; ready", "NOT APPLIED; on the default of L-KILL", 1); return "\n".join(ls)
M["05-ready-row2-turned-default"] = status_flip
def nf_ready(t):
    ls = t.split("\n"); i = rowline(13); ls[i] = ls[i].replace("NOT FILMABLE until L-LEASE is answered (no default); also on the default of", "on the default of", 1); return "\n".join(ls)
M["06-NOT-FILMABLE-row13-made-default"] = nf_ready
M["07-IST-pair-one-minute-off"] = lambda t: rep1(t, "18:29 UTC = 23:59 IST", "18:29 UTC = 23:58 IST")
M["08-UTC-changed-IST-kept"] = lambda t: rep1(t, "18:19 UTC = 23:49 IST", "18:09 UTC = 23:49 IST")
M["09-IST-removed-after-UTC"] = lambda t: rep1(t, "15:05 UTC = 20:35 IST", "15:05 UTC")
M["10-weekday-wrong-Mon-to-Tue"] = lambda t: rep1(t, "Mon 23 Nov 2026", "Tue 23 Nov 2026")
M["11-date-wrong-Wed-26-Nov"] = lambda t: rep1(t, "Wed 25 Nov 2026", "Wed 26 Nov 2026")
M["12-60.1-to-61.8-once"] = lambda t: rep1(t, "60.1 to 61.9", "60.1 to 61.8", 7)
M["13-52.8-to-54.8-once"] = lambda t: rep1(t, "52.8 to 54.9", "52.8 to 54.8", 2)
M["14-10-runs-done-to-9"] = lambda t: rep1(t, "10 runs done", "9 runs done")
def drop_void(t):
    ls = t.split("\n")
    for i, l in enumerate(ls):
        if not l.startswith("| ") and re.search(r"\b18 (kept )?(crash )?runs\b", l) and "VOID-fl45k6c" in l and "VOID-fl45k3b" in l:
            ls[i] = l.replace("VOID-fl45k6c", "the other voided run"); return "\n".join(ls)
    raise SystemExit("no line")
M["15-one-void-label-dropped-in-prose"] = drop_void
P = lambda *a: "".join(a)
M["16-fake-aws-key-in-prose"] = lambda t: rep1(t, "## 0. Failures", "## 0. Failures " + P("AK", "IA", "ABCDEFGHIJKLMNOP", "") + "\n#", 0) if False else t.replace("NOTHING IN THIS REPORT HAS BEEN APPLIED", "NOTHING " + P("AK", "IA", "QRSTUVWXYZ", "234567") + " IN THIS REPORT HAS BEEN APPLIED", 1)
M["17-fake-sk-key-in-prose"] = lambda t: t.replace("NOTHING IN THIS REPORT", "NOTHING " + P("s", "k-", "abcdefghij0123456789ABCD") + " IN THIS REPORT", 1)
M["18-fake-ghp-in-new-text"] = lambda t: t.replace("`Scene 4 filming note", "`" + P("gh", "p_", "a1b2c3d4e5f6g7h8i9j0k1l2") + " Scene 4 filming note", 1)
M["19-email-address-in-prose"] = lambda t: t.replace("NOTHING IN THIS REPORT", "NOTHING " + P("someone", "@", "example", ".org") + " IN THIS REPORT", 1)
M["20-prose-row-count-93"] = lambda t: rep1(t, "holds 94 proposed", "holds 93 proposed")
M["21-3b-TOTAL-ready-48"] = lambda t: rep1(t, "ready 49, on defaults only 40", "ready 48, on defaults only 40")
def swap_rows(t):
    ls = t.split("\n"); a, b = rowline(2), rowline(5); ls[a], ls[b] = ls[b], ls[a]; return "\n".join(ls)
M["22-two-rows-swapped-breaks-bottom-up-order"] = swap_rows
def ready_list(t): return rep1(t, "rows 1, 2, 5, 6,", "rows 1, 2, 5,")
M["23-section0-ready-list-drops-6"] = ready_list
def new_ist_drop(t):
    ls = t.split("\n"); i = rowline(6)
    m = re.search(r"\d\d:\d\d UTC = \d\d:\d\d IST", ls[i])
    if not m: raise SystemExit("no pair in row6")
    ls[i] = ls[i].replace(m.group(0), m.group(0).split(" = ")[0], 1); return "\n".join(ls)
M["24-row6-IST-dropped-from-new-text"] = new_ist_drop
M["25-control-unchanged"] = lambda t: t
out = []; wrong = 0
for name, fn in M.items():
    try:
        t2 = fn(rep)
    except Exception as e:
        out.append("%-48s MUTATION NOT APPLIED (%r)" % (name, e)); wrong += 1; continue
    if t2 == rep and "control" not in name:
        out.append("%-48s MUTATION CHANGED NOTHING" % name); wrong += 1; continue
    p = E + "mut/" + name + ".md"
    open(p, "w", encoding="utf-8").write(t2)
    r = subprocess.run([sys.executable, "-B", "-I", E + "indep_check.py", p], capture_output=True, text=True)
    open(E + "mut/" + name + ".out.txt", "w").write(r.stdout[-5000:] + r.stderr[-1000:] + "\nEXIT %d\n" % r.returncode)
    fails = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    exp0 = "control" in name
    ok = (r.returncode == 0) if exp0 else (r.returncode != 0)
    wrong += 0 if ok else 1
    out.append("%-48s exit %d %s %s" % (name, r.returncode, "OK" if ok else "WRONG", (fails[0][:110] if fails else "")))
    os.remove(p)
out.append("SUMMARY: %d copies, %d wrong" % (len(M), wrong))
open(E + "mutation-summary.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))

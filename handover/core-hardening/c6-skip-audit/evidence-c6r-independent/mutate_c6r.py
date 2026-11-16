"""Own mutation runner: makes changed copies of REPORT-c6r.md in a scratch folder (argv[2]), runs indep_c6r.py on each,
records caught (exit non-zero, and which checks failed) or MISSED. Copies are NOT kept in the repo. Fake keys are built from parts."""
import re, subprocess, sys, os
RPT, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
rep = open(RPT, encoding="utf-8").read()
AK = "AK" + "IA" + "QWERTY123456"
SK = "s" + "k-" + "abcdefghij012345"
GH = "gh" + "p_" + "abcdefghij012345"
ROW = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*) \| (handover/\S+) \| (\d+) \| ", re.M)


def rep1(a, b, n=1):
    assert a in rep, a
    return rep.replace(a, b, n)


def row_edit(i, field, fn):
    ls = rep.split("\n")
    for k, l in enumerate(ls):
        m = re.match(r"^\| %d \| NOT APPLIED" % i, l)
        if m:
            if field == "new":
                a = l.index("` | `") + 5
                b = l.index("` | ", a)
                ls[k] = l[:a] + fn(l[a:b]) + l[b:]
            elif field == "old":
                a = l.index(" | `") + 4
                b = l.index("` | `")
                ls[k] = l[:a] + fn(l[a:b]) + l[b:]
            elif field == "st":
                ls[k] = re.sub(r"^(\| %d \| )(NOT APPLIED[^|]*)" % i, lambda mm: mm.group(1) + fn(mm.group(2)), l)
            elif field == "ln":
                ls[k] = re.sub(r"^(\| %d \| NOT APPLIED[^|]*\| handover/\S+ \| )(\d+)" % i, lambda mm: mm.group(1) + fn(mm.group(2)), l)
            elif field == "id":
                ls[k] = re.sub(r"^\| %d \|" % i, "| %s |" % fn(str(i)), l)
            elif field == "file":
                ls[k] = re.sub(r"(NOT APPLIED[^|]*\| )(handover/\S+)", lambda mm: mm.group(1) + fn(mm.group(2)), l, 1)
            elif field == "view":
                a = re.match(r"^\| \d+ \| NOT APPLIED[^|]*\| handover/\S+ \| \d+ \| ", l).end()
                b = l.index(" | `", a)
                ls[k] = l[:a] + fn(l[a:b]) + l[b:]
            return "\n".join(ls)
    raise KeyError(i)


M = {}
M["01-weekday-Wed18-to-Tue"] = rep1("Wed 18 Nov 2026", "Tue 18 Nov 2026")
M["02-weekday-Mon23-to-Tue"] = rep1("Mon 23 Nov 2026", "Tue 23 Nov 2026")
M["03-weekday-Wed25-to-Thu"] = rep1("Wed 25 Nov 2026", "Thu 25 Nov 2026")
M["04-IST-dropped-money-stop"] = rep1("18:29 UTC = 23:59 IST", "18:29 UTC")
M["05-IST-arith-wrong"] = rep1("18:19 UTC = 23:49 IST", "18:19 UTC = 23:19 IST")
M["06-IST-wrong-in-section0"] = rep1("16:52:47 UTC = 22:22:47 IST", "16:52:47 UTC = 22:52:47 IST")
M["07-count-49-ready-to-48"] = rep1("49 are ready", "48 are ready")
M["08-wave1-85-to-84"] = rep1("85 rows (section 3 lists them)", "84 rows (section 3 lists them)")
M["09-TOTAL-line-ready-50"] = rep1("ready 49, on defaults only 36", "ready 50, on defaults only 36")
M["10-defaults-36-to-37"] = rep1("36 apply on the default", "37 apply on the default")
M["11-94-rows-to-93-in-box"] = rep1("holds 94 proposed text changes", "holds 93 proposed text changes")
M["12-status-ready-to-default-row1"] = row_edit(1, "st", lambda s: "NOT APPLIED; on the default of L-SAVE")
M["13-table-row-50-deleted"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| 50 | NOT APPLIED"))
M["14-duplicate-id-50-as-49"] = row_edit(50, "id", lambda s: "49")
M["15-old-text-one-char-row40"] = row_edit(40, "old", lambda s: s[:12] + "X" + s[12:])
M["16-line-number-shifted-row40"] = row_edit(40, "ln", lambda s: str(int(s) + 1))
M["17-lease-sentence-on-caption-row21"] = row_edit(21, "new", lambda s: s + " We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim.")
M["18-lease-sentence-on-row13"] = row_edit(13, "new", lambda s: s + " We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim.")
M["19-stale-58s-in-card-line"] = rep1("90 words, about 36 s, budget 40 s", "90 words, about 58 s, budget 40 s")
M["20-gate-sentence-deleted"] = rep1("blocks the take until a named person has written a result on it", "blocks the take")
M["21-key-on-command-line-row5"] = row_edit(5, "new", lambda s: s + ' curl -H "Authorization: Bearer ' + SK + '" https://example.invalid')
M["22-fake-AKIA-row6"] = row_edit(6, "new", lambda s: s + " " + AK)
M["23-card-seconds-wrong-table"] = rep1("| 90 | 36.0 | 40 s |", "| 90 | 38.0 | 40 s |")
M["24-card-budget-wrong-table"] = rep1("| 90 | 36.0 | 40 s | about 190 s |", "| 90 | 36.0 | 35 s | about 190 s |")
M["25-card-total-wrong-table"] = rep1("| 74 | 29.6 | 30 s | about 180 s |", "| 74 | 29.6 | 30 s | about 190 s |")
M["26-card-line2-word-count"] = rep1("line 2 (35 words)", "line 2 (34 words)")
M["27-prose-90w-about-40s"] = rep1("90 words, which is about 36 s", "90 words, which is about 40 s")
M["28-row-number-in-viewer-cell-row3"] = row_edit(3, "view", lambda s: s + " (see row 14)")
M["29-row-number-in-new-text-row4"] = row_edit(4, "new", lambda s: s + " (see row 14)")
M["30-61.1-in-new-text-row39"] = row_edit(39, "new", lambda s: s.replace("61.9", "61.1")) if "61.9" in re.search(r"^\| 39 \|.*$", rep, re.M).group(0) else rep1("60.1 to 61.9", "60.1 to 61.1")
M["31-ready-list-item-dropped"] = rep1("rows 1, 2, 5, 6, 7, 8, 9, 10, 16", "rows 1, 2, 5, 6, 7, 8, 9, 16")
M["32-waiting-row53-set-ready"] = row_edit(53, "st", lambda s: "NOT APPLIED; ready")
M["33-waiting-6-to-5-in-TOTAL"] = rep1("waiting for the answer of L-SAVEERR 6", "waiting for the answer of L-SAVEERR 5")
M["34-IST-dropped-in-new-text"] = None
M["35-box-wave1-85-to-89"] = rep1("85 rows (section 3 lists them)", "89 rows (section 3 lists them)")
M["36-row40-file-path-swapped"] = row_edit(40, "file", lambda s: "handover/demo/n8n-flows/N8N-START.md")
M["37-two-rows-order-swapped"] = None
M["38-minute-wrong-IST"] = rep1("23:59 IST", "23:58 IST")
M["39-hash-secret-pk-ghp-in-prose"] = rep1("## 1. How to use this report", "## 1. How to use this report\n" + GH)
M["40-closing-card-table-words-wrong"] = rep1("| 1 (45-second limit) | (a) | 115 |", "| 1 (45-second limit) | (a) | 120 |")
# 34: row with UTC time in new text, drop its IST
for r in re.findall(r"^\| (\d+) \| NOT APPLIED", rep, re.M):
    pass
ls = rep.split("\n")
for k, l in enumerate(ls):
    m = re.match(r"^\| (\d+) \| NOT APPLIED", l)
    if m and re.search(r"\d\d:\d\d UTC = \d\d:\d\d IST", l[l.index("` | `"):] if "` | `" in l else ""):
        j = l.index("` | `")
        M["34-IST-dropped-in-new-text"] = "\n".join(ls[:k] + [l[:j] + re.sub(r" = \d\d:\d\d IST", "", l[j:], 1)] + ls[k + 1:])
        break
# 37: swap two adjacent rows of the same file (breaks bottom-up order)
idx = [k for k, l in enumerate(ls) if re.match(r"^\| \d+ \| NOT APPLIED[^|]*\| handover/demo/VIDEO-RUNSHEET.md", l)]
M["37-two-rows-order-swapped"] = None
a, b = None, None
for x, y in zip(idx, idx[1:]):
    if y == x + 1 and re.search(r"\| (\d+) \| ", ls[x]) and ls[x].split(' | ')[3] != ls[y].split(' | ')[3]:
        a, b = x, y
        break
if a is not None:
    l2 = ls[:]
    l2[a], l2[b] = l2[b], l2[a]
    M["37-two-rows-order-swapped"] = "\n".join(l2)
res = []
for name, t in sorted(M.items()):
    if t is None:
        res.append((name, "NOT BUILT", ""))
        continue
    if t == rep:
        res.append((name, "NO-CHANGE", ""))
        continue
    p = os.path.join(OUT, name + ".md")
    open(p, "w", encoding="utf-8").write(t)
    pr = subprocess.run([sys.executable, "-B", "-I", os.path.join(HERE, "indep_c6r.py"), p], capture_output=True, text=True)
    fails = [l.split(" :: ")[0][5:45] for l in pr.stdout.split("\n") if l.startswith("FAIL")]
    res.append((name, "CAUGHT" if pr.returncode != 0 else "MISSED", "; ".join(fails)[:160] + (" EXC:" + pr.stderr.strip().split("\n")[-1][:80] if pr.stderr.strip() else "")))
for r in res:
    print("%-42s %-9s %s" % r)
print("TOTAL %d  CAUGHT %d  MISSED %d  other %d" % (len(res), sum(r[1] == "CAUGHT" for r in res), sum(r[1] == "MISSED" for r in res), sum(r[1] not in ("CAUGHT", "MISSED") for r in res)))

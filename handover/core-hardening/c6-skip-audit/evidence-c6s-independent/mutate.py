"""Plants mutations on COPIES of REPORT-c6s.md (never the original), runs my_check.py and the builder's verify-c6s.py on each, prints a table. The banned string is read at run time from the repo test file and only written into scratch copies. Usage: mutate.py <report> <workdir> <my_check.py> <verify-c6s.py> <steps_dir>"""
import sys, re, os, subprocess, ast
rep, W, MY, VF, STEPS = sys.argv[1:6]
raw = open(rep, encoding="utf-8").read()
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
B = []
for nd in ast.walk(ast.parse(src)):
    if isinstance(nd, ast.Assign) and any(getattr(x, "id", "") == "BANNED" for x in nd.targets): B = list(ast.literal_eval(nd.value))
M = []
def rep1(a, b, name, allocc=False):
    def f(t):
        assert a in t, "anchor missing: " + name
        return t.replace(a, b) if allocc else t.replace(a, b, 1)
    M.append((name, f))
def rowline(k): return lambda t: [l for l in t.split("\n") if l.startswith("| %d | NOT APPLIED" % k)][0]
def del_row(k):
    def f(t):
        l = rowline(k)(t); return t.replace(l + "\n", "", 1)
    return f
def dup_id(a, b):
    def f(t):
        l = rowline(a)(t); return t.replace(l, l.replace("| %d | NOT APPLIED" % a, "| %d | NOT APPLIED" % b, 1), 1)
    return f
rep1("Of the 94 rows", "Of the 93 rows", "01 wrong count: 'Of the 94 rows' -> 93 (line 24 or 71, first)")
rep1("| TOTAL | all rows | 94 |", "| TOTAL | all rows | 95 |", "02 wrong count: TOTAL row 94 -> 95")
rep1("Of the 94 rows, 49 are ready", "Of the 94 rows, 48 are ready", "03 ready 49 -> 48 in box")
rep1("17:13:05 UTC = 22:43:05 IST", "17:13:05 UTC", "04 dropped IST (first pair)")
rep1("17:13:05 UTC = 22:43:05 IST", "17:13:05 UTC = 22:13:05 IST", "05 wrong IST (30 min short)")
rep1("18:29 UTC = 23:59 IST", "18:29 UTC = 23:29 IST", "06 wrong IST on money stop (first)")
rep1("Mon 23 Nov", "Tue 23 Nov", "07 wrong weekday Mon 23 Nov -> Tue (first)")
rep1("Wed 18 Nov", "Thu 18 Nov", "08 wrong weekday Wed 18 Nov -> Thu (first)")
rep1("Wed 25 Nov", "Fri 25 Nov", "09 wrong weekday Wed 25 Nov -> Fri (first)")
rep1("Mon 23 Nov", "Tue 23 Nov", "10 wrong weekday Mon 23 Nov -> Tue (ALL)", True)
rep1("NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v30", "NEWEST OWNER SHEET VERSION NAMED IN THIS REPORT: v26", "11 stale v26 'newest' (section 0)")
rep1("holds OWNER-SHEET-v30-A.md", "holds OWNER-SHEET-v26-A.md", "12 stale v26 in L-SHEET")
M.append(("13 row 50 deleted", del_row(50)))
M.append(("14 duplicate id (row 51 renumbered 50)", dup_id(51, 50)))
M.append(("15 row 94 deleted", del_row(94)))
rep1("3,490", "3,190", "16 box number changed, first '3,490' -> 3,190")
rep1("3,490", "3,190", "17 box number changed, ALL '3,490' -> 3,190", True)
M.append(("18 box paragraph removed (WORDS YOU NEED block of 3 lines)", lambda t: re.sub(r"WORDS YOU NEED.*?\n\n", "", t, count=1, flags=re.S)))
rep1("| L-POST | Your newest answer in ORDERS.md says the lease sentence stays out of the public post. Does 'public post' include the video's closing card and its scene 3 caption? | Yes: they count.", "| L-POST | Your newest answer in ORDERS.md says the lease sentence stays out of the public post. Does 'public post' include the video's closing card and its scene 3 caption? | No: they do not count.", "19 defaults flipped: L-POST Yes -> No (box table)")
rep1("| L-CARD | Does the closing card stay as the last card of the video? | Yes. |", "| L-CARD | Does the closing card stay as the last card of the video? | No. |", "20 defaults flipped: L-CARD Yes -> No")
rep1("'A lead sent twice with the same id is processed once.'", "'A lead sent twice with the same id is processed once. The 45-second lease is a setting.'", "21 lease sentence on card line 1 (first quote)")
rep1("the key must be cancelled by 18:19 UTC = 23:49 IST", "the key must be cancelled by 18:29 UTC = 23:59 IST", "22 key end tied to 18:29 (money stop)")
rep1("line 1 (11 words)", "line 1 (12 words)", "23 card word count 11 -> 12")
rep1("| 90 | 36.0 | 40 s |", "| 90 | 30.0 | 40 s |", "24 card seconds 36.0 -> 30.0")
rep1("| 115 | 46.0 | 50 s |", "| 115 | 46.0 | 45 s |", "25 card budget 50 s -> 45 s")
rep1("| 74 | 29.6 | 30 s | about 180 s |", "| 74 | 29.6 | 30 s | about 185 s |", "26 video total 180 -> 185")
def apply1(t):
    l = rowline(20)(t); return t.replace(l, l.replace("NOT APPLIED", "APPLIED", 1), 1)
M.append(("27 row 20 status says APPLIED", apply1))
def lineno(t):
    l = rowline(1)(t); return t.replace(l, l.replace("| handover/demo/VIDEO-RUNSHEET.md | 90 |", "| handover/demo/VIDEO-RUNSHEET.md | 91 |", 1), 1)
M.append(("28 row 1 stated line 90 -> 91", lineno))
def oldtxt(t):
    l = rowline(5)(t); g = re.findall(r"`(.*?)`", l); o = g[0]
    return t.replace(l, l.replace("`" + o + "`", "`" + o.replace("a", "e", 1) + "`", 1), 1)
M.append(("29 row 5 old text altered by one letter", oldtxt))
M.append(("30 banned string inserted (counts only; value never printed)", lambda t: t.replace("## 1. How to use this report", "## 1. How to use this report\nSee " + B[0] + " here.", 1)))
M.append(("31 internal code R447 added to box", lambda t: t.replace("WHAT TO TYPE", "WHAT TO TYPE (R447)", 1)))
M.append(("32 key-shaped string added (built from parts)", lambda t: t.replace("## 1. How to use this report", "## 1. How to use this report\nkey " + "sk-" + "ant-" + "api03-" + "A" * 40 + "\n", 1)))
rep1("36 apply on the default of a question", "37 apply on the default of a question", "33 36 -> 37 defaults in box")
rep1("3 wait for a check that needs n8n running", "4 wait for a check that needs n8n running", "34 3 -> 4 check rows in box")
rep1("IST = UTC + 5:30", "IST = UTC + 5:00", "35 title says UTC + 5:00")
rep1("v30 (at the check time", "v31 (at the check time", "36 newest sheet claimed v31")
rep1("release note v14", "release note v15", "37 release note v14 -> v15 (first)")
rep1("60.1 to 61.9 s", "60.1 to 69.1 s", "38 range 60.1 to 61.9 -> 69.1 (first)")
rep1("18 kept runs", "17 kept runs", "39 18 kept runs -> 17 (first)")
rep1("2026-11-16T18:00:00Z = 23:30:00 IST", "2026-11-16T18:00:00Z = 23:00:00 IST", "40 answer-line example IST wrong")
M.append(("41 report truncated (last 20 lines cut)", lambda t: "\n".join(t.split("\n")[:-20])))
rep1("OWNER ONLY: confirm the ONE final owner sheet", "confirm the ONE final owner sheet", "42 OWNER ONLY removed from L-SHEET")
rep1("Open handover/core-hardening/ORDERS.md", "Open handover/core-hardening/ORDER.md", "43 box names wrong file ORDER.md")
M.append(("44 pipe removed from row 30 (cell merge)", lambda t: (lambda l: t.replace(l, l.replace(" | ", " ", 1), 1))(rowline(30)(t))))
rep1("17:12:09 UTC = 22:42:09 IST", "17:12:09 UTC = 22:42:09 IST and OWNER-SHEET-v31-A.md", "45 v31 sheet named as existing")
rep1("I do not know", "I know", "46 (control for no-op: anchor optional)") if "I do not know" in raw else None
M.append(("47 no-change control (must PASS both)", lambda t: t))
os.makedirs(W + "/mut", exist_ok=True)
env = dict(os.environ, C6S_STEPS=STEPS)
rows = []
for name, f in M:
    try:
        t = f(raw)
    except AssertionError as e:
        rows.append((name, "ANCHOR-MISSING", "ANCHOR-MISSING")); continue
    p = W + "/mut/%s.md" % name[:2]; open(p, "w", encoding="utf-8").write(t)
    a = subprocess.run([sys.executable, "-B", "-I", MY, p], capture_output=True, text=True)
    b = subprocess.run([sys.executable, "-B", "-I", VF, p], capture_output=True, text=True, env=env)
    fa = [l[5:60] for l in a.stdout.split("\n") if l.startswith("FAIL")]
    fb = [l[5:60] for l in b.stdout.split("\n") if l.startswith("FAIL")]
    rows.append((name, ("CAUGHT %d" % len(fa)) if a.returncode else "MISSED", ("CAUGHT %d" % len(fb)) if b.returncode else "MISSED", fa[:1], fb[:1]))
    os.remove(p)
for r in rows: print(" | ".join(str(x) for x in r))

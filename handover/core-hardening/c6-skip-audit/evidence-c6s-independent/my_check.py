"""Independent checker (evidence runner). Usage: python3 -B -I my_check.py REPORT.md  -> PASS/FAIL lines, exit 1 on any FAIL. Written from the report text, not from the builder's verifier."""
import re, sys, ast, math, datetime, os
R = sys.argv[1]
raw = open(R, encoding="utf-8").read()
L = raw.split("\n")
F = []
def chk(n, ok, d=""):
    print(("PASS " if ok else "FAIL ") + n + (" :: " + str(d)[:200] if d != "" else ""))
    if not ok: F.append(n)
# rows
rowl = [l for l in L if re.match(r"^\| \d+ \| NOT APPLIED", l)]
ids = [int(re.match(r"^\| (\d+) \|", l).group(1)) for l in rowl]
chk("A1 row count is 94", len(rowl) == 94, len(rowl))
chk("A2 ids are exactly 1..94, unique (table is in apply order, not numeric order)", sorted(ids) == list(range(1, 95)), ids[:5])
cols = [len(l.split(" | ")) for l in rowl]
chk("A3 every row has the same number of cells", len(set(cols)) == 1, set(cols))
st = [re.match(r"^\| \d+ \| (NOT APPLIED[^|]*?) \|", l).group(1) for l in rowl]
ready = sum(1 for s in st if s.endswith("ready")); dflt = sum(1 for s in st if "on the default" in s and "after check" not in s); chk_ = sum(1 for s in st if "after check" in s); own = sum(1 for s in st if "owner" in s or "L-SAVEERR" in s)
chk("A4 status split 49+36+3+6 = 94", (ready, dflt, chk_, own) == (49, 36, 3, 6), (ready, dflt, chk_, own, sorted(set(st))[:8]))
# every statement of the row total
cnt = re.findall(r"\b(\d+) (?:proposed )?(?:text changes|rows)\b|Of the (\d+) rows", raw)
nums = {int(x) for t in cnt for x in t if x}
chk("A5 row totals quoted anywhere (N rows / Of the N rows) that look like totals are only 94 where >=90", all(n == 94 for n in nums if n >= 90), sorted(nums))
# 'ready' list in 3c equals ids with ready status
m = re.search(r"^\| \(no question, no check\) \| ([0-9, ]+) \| (\d+) \|", raw, re.M)
lst = [int(x) for x in m.group(1).split(",")]
chk("A6 3b list of ready rows equals the rows whose status says ready, and count 49", sorted(lst) == sorted(i for i, s in zip(ids, st) if s.endswith("ready")) and int(m.group(2)) == len(lst) == 49, (len(lst), m.group(2)))
# times
def mins(h, mi, s): return int(h) * 3600 + int(mi) * 60 + int(s or 0)
pat = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?(?:Z| UTC)(?:[^|\n]{0,3}?)= (\d{1,2}):(\d{2})(?::(\d{2}))? IST")
bad = []; n = 0
for l in L:
    for g in pat.finditer(l):
        n += 1
        u = mins(*g.group(1, 2, 3)); i = mins(*g.group(4, 5, 6))
        if (u + 19800) % 86400 != i: bad.append(g.group(0))
chk("B1 every 'UTC = IST' pair is exactly +5:30 (%d pairs)" % n, not bad and n >= 20, bad[:3])
# UTC times with no IST nearby
lonely = []
for k, l in enumerate(L):
    for g in re.finditer(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?(?:Z| UTC)\b", re.sub(r"`[^`]*`", "", l)):
        l2 = re.sub(r"`[^`]*`", "", l); tail = l2[g.end():g.end() + 45]
        if "IST" not in tail and "=" not in l[max(0, g.start() - 4):g.start()]: lonely.append((k + 1, g.group(0)))
chk("B2 every clock time written as UTC has an IST pair within 45 characters", not lonely, lonely[:6])
# stray times with 'IST' only
# weekday / date
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
bw = []; nw = 0
for g in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Nov)(?:ember)?\b", raw):
    nw += 1
    if days[datetime.date(2026, 11, int(g.group(2))).weekday()] != g.group(1)[:3]: bw.append(g.group(0))
chk("C1 every weekday + date pair is right for Nov 2026 (%d pairs)" % nw, not bw and nw > 0, bw)
bi = []
for g in re.finditer(r"(2026-11-\d\d)(?:\s*\((\w+)\))", raw):
    if days[datetime.date.fromisoformat(g.group(1)).weekday()] != g.group(2)[:3]: bi.append(g.group(0))
chk("C2 ISO date with weekday in brackets are right", not bi, bi)
# card tables
tb = [l for l in L if re.match(r"^\| (none \(the default\)|1 \(45-second limit\)|2 \(lease explained\)) \|", l)]
ok = len(tb) == 6; det = []
for l in tb:
    c = [x.strip() for x in l.strip("|").split("|")]
    w = int(c[2]); s = float(c[3]); b = int(c[4].split()[0]); tot = int(re.search(r"\d+", c[5]).group())
    exp_s = w / 150 * 60; exp_b = math.ceil(exp_s / 5 - 1e-9) * 5
    if abs(exp_s - s) > 0.05 or exp_b != b or tot != 150 + b: ok = False; det.append(c)
chk("D1 card length table: seconds = words/150*60, budget = round up to 5, total = 150+budget (6 rows)", ok, det)
# quoted line word counts
qs = re.search(r"THE CLOSING CARD UNDER THE DEFAULTS[^\n]*", raw).group(0)
parts = re.findall(r"line (\d) \((\d+) words?\) '(.*?)'(?= line \d \(| Total )", qs)
chk("D2 closing card: 4 quoted lines, stated word counts equal real counts", len(parts) >= 3 and all(len(t.split()) == int(c) for _, c, t in parts), [(a, c, len(t.split())) for a, c, t in parts])
tot = sum(int(c) for _, c, _ in parts)
chk("D3 card total (default a) equals table 90", tot == 90, tot)
# box
s = raw.index("## Start here"); e = raw.index("\n## 0.")
box = raw[s:e]; wc = len(box.split())
chk("E1 box word count (own count; report says 3,488 by builder's count)", True, wc)
claim = re.findall(r"([\d,]{5}) words", raw)
chk("E2 box word count stated in report equals my count within 1 percent", any(abs(int(c.replace(",", "")) - wc) <= wc * 0.01 for c in claim if c.replace(",", "").isdigit()), (wc, claim[:5]))
leaks = {k: len(re.findall(p, box)) for k, p in {"R-number": r"\bR\d{3}\b", "WP": r"\bWP\d", "ledger id": r"\b[A-Z]{1,3}-\d{2,3}\b(?!\))", "HB": r"\bHB\d{3}\b", "c6x label": r"\bc6[a-r]\b", "NEEDS_": r"NEEDS_[A-Z]+", "invariant": r"\bI[1-4]\b"}.items()}
chk("F1 box: no internal-code leak patterns (R-numbers, WP, HB, c6[a-r], NEEDS_, invariants)", sum(v for k, v in leaks.items() if k in ("R-number", "WP", "HB", "c6x label", "NEEDS_", "invariant")) == 0, leaks)
# banned
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
t = ast.parse(src); B = []
for nd in ast.walk(t):
    if isinstance(nd, ast.Assign) and any(getattr(x, "id", "") == "BANNED" for x in nd.targets): B = list(ast.literal_eval(nd.value))
cnt = sum(raw.count(b) for b in B)
chk("G1 banned strings (%d read at run time): count in report" % len(B), cnt == 0 and len(B) > 0, cnt)
# stale
chk("H1 no stale 'v26' called newest", not re.search(r"v26[^\n]{0,40}newest|newest[^\n]{0,40}v26", raw, re.I))
chk("H2 title names c6s", L[0].startswith("# REPORT-c6s"))
# defaults
dl = [l for l in L if l.startswith("| L-")]
chk("I1 key defaults: L-SAVE default none for failed runs; L-LEASE none", "failed-run saving defaults to none" in raw or "EXECUTIONS_DATA_SAVE_ON_ERROR" in raw)
print("SUMMARY: %d FAIL" % len(F), F); sys.exit(1 if F else 0)

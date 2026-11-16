"""Independent checker for REPORT-c6p.md. Own code: does not import or read verify-c6p.py.
Usage: python3 -B -I indep_c6p.py REPORT_PATH   (exit 1 on any FAIL; prints PASS/FAIL/INFO per check)
Source copy for rows on handover/demo/*: SRC_TREE env or the scratchpad copy used by the builder's script;
rows on handover/core-hardening/*: the repository checkout."""
import re, sys, os, datetime, collections

H = "/home/user/hadavin-sdk"
T = os.environ.get("SRC_TREE", "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree")
R = sys.argv[1]
text = open(R, encoding="utf-8").read()
L = text.split("\n")
FAILS = []


def chk(n, ok, d=""):
    print(("PASS " if ok else "FAIL ") + n + ((" :: " + str(d)[:500]) if d != "" else ""))
    if not ok:
        FAILS.append(n)


def info(n, d=""):
    print("INFO " + n + " :: " + str(d)[:700])


def src(p):
    base = H if p.startswith("handover/core-hardening/") else T
    return open(base + "/" + p, encoding="utf-8", errors="replace").read()


# ---- parse table (my own splitter: cells split on ' | ', old/new are backtick cells) ----
rows, bad_parse = [], []
for ln, l in enumerate(L, 1):
    if not re.match(r"^\| \d+ \| NOT APPLIED", l):
        continue
    m = re.match(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/\S+) \| (\d+) \| (.*?) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$", l)
    if not m:
        bad_parse.append(ln)
        continue
    i, st, f, n, view, old, new, why, was = m.groups()
    rows.append(dict(i=int(i), st=st, f=f, ln=int(n), view=view, old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), why=why, lno=ln))
chk("A0 every table line parsed (%d rows)" % len(rows), not bad_parse and len(rows) > 0, bad_parse)
chk("A1 ids are exactly 1..94, no duplicate", sorted(r["i"] for r in rows) == list(range(1, 95)), [r["i"] for r in rows if [x["i"] for x in rows].count(r["i"]) > 1])

# ---- old text once on stated line ----
cache = {}
bad = []
for r in rows:
    fl = cache.setdefault(r["f"], src(r["f"]).split("\n"))
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if not r["old"] or seg.count(r["old"]) != 1:
        bad.append((r["i"], seg.count(r["old"]) if r["old"] else "empty"))
chk("B1 old text occurs exactly once on its stated line, in the source copy (94 rows)", not bad, bad)
# also: old text must occur once in the whole file or at least on that line only (informational)
multi = []
for r in rows:
    whole = src(r["f"])
    c = whole.count(r["old"])
    if c != 1:
        multi.append((r["i"], c))
info("B1b rows whose old text occurs more than once in the whole file (the line number decides which)", multi)

# ---- apply in order on in-memory copies ----
tx = {}
ab = []
for r in rows:
    fl = tx.setdefault(r["f"], src(r["f"]).split("\n"))
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if seg.count(r["old"]) != 1:
        ab.append(r["i"])
        continue
    fl[r["ln"] - 1:r["ln"] - 1 + k] = seg.replace(r["old"], r["new"], 1).split("\n")
chk("B2 all 94 rows apply in table order on copies, each old text found on its stated line after the earlier rows", not ab, ab)
last, ob = {}, []
for r in rows:
    if r["f"] in last and r["ln"] > last[r["f"]]:
        ob.append(r["i"])
    last[r["f"]] = r["ln"]
chk("B3 within each file stated lines never rise down the table (bottom-up)", not ob, ob)

# ---- counts ----
def cls(st):
    if "NOT FILMABLE" in st:
        return "nf"
    if "after check" in st:
        return "check"
    if "on the default" in st:
        return "default"
    if st.strip() == "NOT APPLIED; ready":
        return "ready"
    return "other"


C = collections.Counter(cls(r["st"]) for r in rows)
chk("D1 status counts: ready 49, on defaults only 42, wait for a check 3, NOT FILMABLE 0, other 0", (C["ready"], C["default"], C["check"], C["nf"], C["other"]) == (49, 42, 3, 0, 0), dict(C))
ready = sorted(r["i"] for r in rows if cls(r["st"]) == "ready")
deflt = sorted(r["i"] for r in rows if cls(r["st"]) == "default")
chkr = sorted(r["i"] for r in rows if cls(r["st"]) == "check")
chk("D2 rows that wait for a check are 23, 58, 59", chkr == [23, 58, 59], chkr)
wave1 = sorted(ready + deflt)
chk("D3 wave 1 = ready + defaults = 91 rows", len(wave1) == 91, len(wave1))


def nums(s):
    return [int(x) for x in re.findall(r"\d+", s)]


box = "\n".join(L[:59])
bm = re.search(r"## 0\.", text)
boxend = text[:bm.start()].count("\n") if bm else 59
box = "\n".join(L[:boxend])
for name, pat, val in [
    ("box: table holds N rows", r"holds (\d+) proposed text changes", 94),
    ("box: ready", r"(\d+) rows are 'ready'", 49),
    ("box: on defaults", r"(\d+) apply on the default", 42),
    ("box: wait for a check", r"(\d+) wait for a check", 3),
]:
    m = re.findall(pat, box)
    chk("D4 " + name + " = %d" % val, m and all(int(x) == val for x in m), m)
chk("D4 box: wave 1 is 91 rows", len(re.findall(r"\b91 rows\b", box)) >= 1 and not re.findall(r"\b(89|90|92|93) rows\b", box), re.findall(r"\b\d+ rows\b", box)[:12])
chk("D4 box: check rows named as 23, 58, 59", "rows 23, 58, 59" in box)
# section 0
s0 = text[bm.start(): text.index("## 1.")]
m = re.search(r"Of the (\d+) rows .*?: (\d+) are 'ready' \(no open question and no open check; rows ([0-9, ]+)\); (\d+) apply on the default[^;]*; (\d+) wait for a check that needs n8n \(rows ([0-9, ]+)\); none is NOT FILMABLE", s0, re.S)
chk("D5 section 0 counts 94/49/42/3 and none NOT FILMABLE", bool(m) and (m.group(1), m.group(2), m.group(4), m.group(5)) == ("94", "49", "42", "3"), m.groups() if m else None)
chk("D5b section 0 ready list equals the recount", bool(m) and nums(m.group(3)) == ready, m.group(3) if m else None)
chk("D5c section 0 check list equals the recount", bool(m) and nums(m.group(6)) == chkr)
# 3b table
s3b_i = text.index("3b. Count of rows")
s3b = text[s3b_i: text.index("3c. ", s3b_i)]
per = collections.defaultdict(list)
for r in rows:
    st = r["st"]
    for mm in re.finditer(r"after check (C-\d+)", st):
        per[mm.group(1)].append(r["i"])
    d = re.search(r"on the default of ([^;]*)", st)
    if d:
        for q in [x.strip() for x in d.group(1).split(",")]:
            per[q].append(r["i"])
bad3 = []
for line in s3b.split("\n"):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 5 and (cells[0].startswith("L-") or cells[0].startswith("C-")):
        q = cells[0]
        got = nums(cells[1])
        if got != sorted(per.get(q, [])) or int(cells[2]) != len(per.get(q, [])):
            bad3.append((q, got, sorted(per.get(q, []))))
        only = [x for x in per[q] if len(re.findall(r"L-[A-Z]+|C-\d+", next(r for r in rows if r["i"] == x)["st"].replace("NOT APPLIED", ""))) == 1]
        # 'wait only for this' = rows whose status names only this question/check
        claimed = nums(cells[3].split("(", 1)[1]) if "(" in cells[3] and "none" not in cells[3] else []
        if claimed != sorted(only):
            bad3.append((q, "only-col", claimed, sorted(only)))
chk("D6 table 3b: rows tied, how many, 'only this' column all equal my recount from the status words", not bad3, bad3)
chk("D6b table 3b has all 12 questions/checks", sum(1 for l in s3b.split("\n") if re.match(r"^\| (L-|C-)", l)) == len(per) == 12, (len(per), sorted(per)))
tot = re.search(r"\| TOTAL \| all rows \| (\d+) \| ready (\d+), on defaults only (\d+), with a check (\d+), NOT FILMABLE until an answer (\d+)", s3b)
chk("D7 3b TOTAL line = 94/49/42/3/0", bool(tot) and tot.groups() == ("94", "49", "42", "3", "0"), tot.groups() if tot else None)
nq = re.search(r"\| \(no question, no check\) \| ([0-9, ]+) \| (\d+) \|", s3b)
chk("D7b 3b 'no question, no check' row list = ready list", bool(nq) and nums(nq.group(1)) == ready and int(nq.group(2)) == 49)
# section 3 table: rows tied
s3 = text[text.index("## 3. Questions"): s3b_i]
bad3t = []
for line in s3.split("\n"):
    if re.match(r"^\| L-[A-Z]+ ", line):
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        q = cells[0].split(" ")[0]
        last = cells[-1].strip().strip("|").strip()
        got = [] if last.startswith("none") else nums(last)
        exp = sorted(per.get(q, []))
        if got != exp:
            bad3t.append((q, got, exp))
chk("D8 section 3 'rows tied to it' column equals my recount (L-DEL, L-CUT, L-SHEET: none)", not bad3t, bad3t)
# 3c lists
s3c = text[text.index("3c. 'APPLY ALL DEFAULTS'"): text.index("3d. ")]
m3 = re.search(r"the (\d+) ready rows \(([0-9, ]+)\) and the (\d+) rows that wait only for a question \(([0-9, ]+)\), (\d+) rows in all", s3c)
chk("D9 3c: ready list, default list, 91 total equal recount", bool(m3) and nums(m3.group(2)) == ready and nums(m3.group(4)) == deflt and m3.group(5) == "91", m3.group(1, 3, 5) if m3 else None)
# per-file counts in 3c / box
fc = collections.Counter(r["f"] for r in rows)
chk("D10 94 rows over 10 files", sum(fc.values()) == 94 and len(fc) == 10, dict(fc))
w1f = {r["f"] for r in rows if r["i"] in wave1}
chk("D10b wave 1 touches 10 files (box says 10 files)", len(w1f) == 10 and "to 10 files" in box, len(w1f))
info("D11 occurrences of NOT FILMABLE in the report (prose should say zero rows)", [(i + 1, L[i][:110]) for i in range(len(L)) if "NOT FILMABLE" in L[i] and not L[i].startswith("| ") ][:8])
stale = [(i + 1, m.group(0)) for i in range(len(L)) for m in re.finditer(r"\b(?:89 rows|40 rows|apply on the default of a question you have not answered, 40|two rows? (?:are )?NOT FILMABLE|2 NOT FILMABLE)\b", L[i])]
chk("D12 no stale c6o counts (89 rows, 40 rows, 2 NOT FILMABLE)", not stale, stale)

# ---- UTC -> IST ----
oldcells = [r["old"] for r in rows]
def strip_old(l):
    for o in oldcells:
        if o and o in l:
            l = l.replace(o, " ")
    return l
pair = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*UTC|Z)?\s*(?:=|\()\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST")
bp, npair = [], 0
for ln, l in enumerate(L, 1):
    for m in pair.finditer(strip_old(l)):
        npair += 1
        h1, m1, s1, h2, m2, s2 = m.groups()
        if (int(h1) * 60 + int(m1) + 330) % 1440 != (int(h2) * 60 + int(m2)) % 1440 or (s1 or "0") != (s2 or "0"):
            bp.append((ln, m.group(0)))
chk("E1 every 'UTC = IST' pair is +5:30 (%d pairs)" % npair, not bp and npair > 10, bp)
utc = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:UTC|Z)\b|\bT(\d{2}):(\d{2})(?::(\d{2}))?Z")
ist = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST|IST \((\d{1,2}):(\d{2})")
def ists(s):
    o = []
    for m in ist.finditer(s):
        g = m.groups()
        h, mi = (g[0], g[1]) if g[0] is not None else (g[3], g[4])
        o.append((int(h) * 60 + int(mi)) % 1440)
    return o
def utcs(s):
    o = []
    for m in utc.finditer(s):
        g = m.groups()
        h, mi = (g[0], g[1]) if g[0] is not None else (g[3], g[4])
        o.append((int(h) * 60 + int(mi)) % 1440)
    return o
miss, nu = [], 0
for ln, l in enumerate(L, 1):
    l2 = strip_old(l)
    u, i2 = utcs(l2), ists(l2)
    for x in u:
        nu += 1
        if (x + 330) % 1440 not in i2:
            miss.append((ln, "%02d:%02d" % divmod(x, 60)))
chk("E2 every UTC/Z clock time (%d) has its +5:30 IST on the same line" % nu, not miss, miss[:20])
bn = []
for r in rows:
    i2 = ists(r["new"])
    for x in utcs(r["new"]):
        if (x + 330) % 1440 not in i2:
            bn.append((r["i"], "%02d:%02d" % divmod(x, 60)))
chk("E3 every UTC time inside a new text has its IST inside the same new text", not bn, bn)
for u, i_ in [("18:04", "23:34"), ("18:19", "23:49"), ("18:29", "23:59")]:
    chk("E4 %s UTC = %s IST present and correct" % (u, i_), ("%s UTC = %s IST" % (u, i_)) in text and (int(u[:2]) * 60 + int(u[3:]) + 330) % 1440 == int(i_[:2]) * 60 + int(i_[3:]))
chk("E5 no wrong IST for the three money times anywhere", not re.findall(r"18:(?:04|19|29) UTC = (?!23:34|23:49|23:59)\d\d:\d\d IST", text))

# ---- weekdays and dates ----
MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
WD = "Mon Tue Wed Thu Fri Sat Sun".split()
bw, nw = [], 0
for ln, l in enumerate(L, 1):
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?: (\d{4}))?", l):
        nw += 1
        w, d, mo, y = m.groups()
        try:
            a = WD[datetime.date(int(y or 2026), MON[mo], int(d)).weekday()]
        except ValueError:
            bw.append((ln, m.group(0)))
            continue
        if a != w:
            bw.append((ln, m.group(0), a))
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{4})-(\d\d)-(\d\d)", l):
        nw += 1
        w, y, mo, d = m.groups()
        if WD[datetime.date(int(y), int(mo), int(d)).weekday()] != w:
            bw.append((ln, m.group(0)))
chk("F1 weekday+date strings correct for 2026 (%d found)" % nw, not bw and nw >= 5, bw)
yrs = collections.Counter(re.findall(r"\b(20\d\d)-\d\d-\d\d", text))
chk("F2 every ISO date is in 2026", set(yrs) == {"2026"}, dict(yrs))
for d_, w_ in [("2026-11-18", "Wed"), ("2026-11-17", "Tue"), ("2026-11-23", "Mon"), ("2026-11-25", "Wed"), ("2026-11-16", "Mon")]:
    y, mo, d = map(int, d_.split("-"))
    chk("F3 %s is %s" % (d_, w_), WD[datetime.date(y, mo, d).weekday()] == w_)
dd = re.findall(r"(\d{4}-\d\d-\d\d)", text)
bd = []
for x in set(dd):
    try:
        datetime.date.fromisoformat(x)
    except ValueError:
        bd.append(x)
chk("F4 every ISO date is a real calendar date", not bd, bd)

# ---- figures ----
a = re.findall(r"60\.1 to \d+\.\d", text)
chk("G1 every '60.1 to X' is 61.9 (%d)" % len(a), a and set(a) == {"60.1 to 61.9"}, collections.Counter(a))
b = re.findall(r"52\.8 to \d+\.\d", text)
chk("G2 every '52.8 to X' is 54.9 (%d)" % len(b), b and set(b) == {"52.8 to 54.9"}, collections.Counter(b))
chk("G3 no 61.1 or other bound", "61.1" not in text and not re.findall(r"61\.9 to|to 6[2-9]\.\d s", text))
d_ = re.findall(r"(\d+) runs done", text)
u_ = re.findall(r"(\d+) runs unknown", text)
chk("G4 runs done always 10, unknown always 8", d_ and u_ and set(d_) == {"10"} and set(u_) == {"8"}, (collections.Counter(d_), collections.Counter(u_)))
kk = re.findall(r"K1 (\d+), K2 (\d+), K3B (\d+), K3 (\d+)", text)
chk("G5 K1 5 K2 5 K3B 5 K3 3 and sum 18", kk and set(kk) == {("5", "5", "5", "3")} and 5 + 5 + 5 + 3 == 18, collections.Counter(kk))
vb = []
for ln, l in enumerate(L, 1):
    if re.search(r"\b18 (kept |crash )?runs\b", l) and not re.match(r"^\| \d+ \| NOT APPLIED", l) and ("VOID-fl45k3b" not in l or "VOID-fl45k6c" not in l):
        vb.append(ln)
chk("G6 non-table lines with '18 runs' name both voided runs", not vb, vb)
vn = []
for r in rows:
    if re.search(r"\b18 (kept |crash )?runs\b", r["new"]) and ("VOID-fl45k3b" not in r["new"] or "VOID-fl45k6c" not in r["new"]):
        vn.append(r["i"])
info("G7 new texts that say '18 runs' without naming both voided runs (the row's reason cell may name them)", vn)

# ---- card words / seconds ----
def words(s):
    return len(s.split())
def secs(w):
    return w / 150.0 * 60
r13 = next(r for r in rows if r["i"] == 13)["new"]
r14 = next(r for r in rows if r["i"] == 14)["new"]
l1 = re.findall(r'"(.*?)"', r13)
l234 = re.findall(r'"(.*?)"', r14)
wa = [words(x) for x in l1 + l234]
chk("H1 option (a): card lines hold [36, 35, 22, 22] words, total 115 (whitespace split)", wa == [36, 35, 22, 22] and sum(wa) == 115, (wa, sum(wa)))
chk("H2 option (a) seconds at 150 words a minute = 46.0 (rounds to 46)", round(secs(115)) == 46, secs(sum(wa)))
s3t = text[text.index("## 3. Questions"):]
cl = [l for l in s3t.split("\n") if l.startswith("| L-CARDLEN |")][0]
bq = re.findall(r"line (\d) '([^']*(?:'s[^']*)*?)'(?= line \d | \(with)", cl)
bq = re.findall(r"line [1-4] '(.*?)'(?= line [1-4] '| \(with reading)", cl.split("OPTION (b)")[1])
wb = [words(x) for x in bq]
chk("H3 option (b): four lines found, total 87 words", len(bq) == 4 and sum(wb) == 87, (wb, sum(wb)))
chk("H4 option (b) seconds = 34.8, said 'about 35 s'", abs(secs(87) - 34.8) < 0.05 and "about 35 s" in cl, secs(sum(wb)))
chk("H5 totals: 150 + 50 = 200 (a), 150 + 35 = 185 (b); scenes 25+40+25+60 = 150", 25 + 40 + 25 + 60 == 150 and 150 + 50 == 200 and 150 + 35 == 185)
chk("H6 'about 46 s' and '115 words' and 'about 200 s' appear in box, row 11, section 3", all(x in box for x in ["115 words", "about 46 s", "about 200 s"]) and "115 words" in next(r for r in rows if r["i"] == 11)["new"])
bad115 = [(ln, m.group(0)) for ln, l in enumerate(L, 1) for m in re.finditer(r"\b(\d+) words, about (\d+) s\b", l) if (m.group(1), m.group(2)) not in {("115", "46"), ("87", "35"), ("144", "58"), ("103", "41")}]
chk("H7 every 'N words, about M s' pair is consistent with 150 wpm (|M - N/2.5| <= 0.6)", not [x for x in re.findall(r"\b(\d+) words, about (\d+) s\b", text) if abs(int(x[1]) - int(x[0]) / 2.5) > 0.6], re.findall(r"\b(\d+) words, about (\d+) s\b", text))
mm = [m for m in re.finditer(r"(\d+) words\)? ?(?:[:;,]|:)? ?(?:about|is about) (\d+) s", text)]
r1 = re.search(r"sentence '(We make this claim[^']*)' \((\d+) words\)", cl if False else s3t)
if r1:
    chk("H8 reading 1 card sentence word count as stated", words(r1.group(1)) == int(r1.group(2)), (words(r1.group(1)), r1.group(2)))
r2 = re.search(r"2 = '(The 45 seconds is a setting[^']*)'", text)
if r2:
    chk("H9 reading 2 sentence is 40 words (as stated) and about 16 s", words(r2.group(1)) == 40 and round(secs(40)) == 16, (words(r2.group(1)), secs(40)))

# ---- no 'row N' in new run-sheet text; other internal labels ----
rs_new = [r for r in rows if r["f"].endswith("VIDEO-RUNSHEET.md")]
rn = [(r["i"], m.group(0)) for r in rs_new for m in re.finditer(r"\b[Rr]ows? \d+", r["new"])]
chk("I1 no 'row N' or 'rows N' reference inside new run-sheet text (%d run-sheet rows)" % len(rs_new), not rn, rn)
rn2 = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\b[Rr]ows? \d+", r["new"])]
chk("I1b no 'row N' in ANY row's new text (all files)", not rn2, rn2)
lab = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\b(?:L-[A-Z]{3,}|C-\d+[a-z]?|REPORT-c6\w|section \d|c6[a-p]\b|rehearsal list item \d+, row)", r["new"])]
info("I2 internal labels (L-xxx, C-n, REPORT-c6x, 'section n', c6x) inside new texts", lab)
ids_re = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\b(?:ORD|DEC|RS|NS|JF|MF|RCO|RJL|RES|ONE|PLAN|QUE):\d+", r["new"])]
info("I3 source-cite shapes (ORD:150 etc.) inside new texts", ids_re[:12])

# ---- section 5a ----
a5 = text[text.index("5a. WHAT CHANGES"): text.index("5b. THE CLOSING CARD")]
a5rows = {}
for l in a5.split("\n"):
    m = re.match(r"^\| (\d+) \| (run sheet|page statements), line (\d+) \| (.*) \|$", l)
    if m:
        a5rows[int(m.group(1))] = (m.group(2), int(m.group(3)), m.group(4))
exp = {}
for r in rows:
    if (r["f"].endswith("VIDEO-RUNSHEET.md") or r["f"].endswith("PAGE-STATEMENTS-V4.md")) and not r["view"].startswith("Nothing"):
        exp[r["i"]] = ("run sheet" if r["f"].endswith("RUNSHEET.md") else "page statements", r["ln"], r["view"])
chk("J1 5a row set equals rows (run sheet or page statements) whose 'what the viewer sees' is not 'Nothing' (%d)" % len(exp), set(a5rows) == set(exp), (sorted(set(a5rows) ^ set(exp))))
chk("J2 5a each row: file label, line and view text equal the table", all(a5rows.get(i) == v for i, v in exp.items()), [i for i, v in exp.items() if a5rows.get(i) != v])
chk("J3 5a says 36 rows", "the 36 rows" in a5 and len(exp) == 36 and len(a5rows) == 36, (len(exp), len(a5rows)))
fl_rows = sorted(r["i"] for r in rows if "n8n-flows-real-v5" in r["f"] or "build_mainframe" in r["f"] or r["f"].endswith("mf.py") and False)
m = re.search(r"the flow-file rows ([0-9, ]+) change what", a5)
info("J4 5a header names flow-file rows %s; flow-file rows in table (real-v5 json + generator)" % (nums(m.group(1)) if m else None), fl_rows)
chk("J5 5a sorted ascending without duplicates", list(a5rows) == sorted(set(a5rows)), list(a5rows)[:50])

# ---- labels defined before first use (box) ----
bw_ = box.index("WORDS YOU NEED FIRST")
dend = box.index("QUESTIONS (label")
defs = ["CONTACT", "N8N", "TAKE", "REHEARSAL", "RUN SHEET", "STUDIO LEAD", "OWNER", "LEASE", "ALERT", "GATE", "RE-PIN", "READY", "K3B", "TIMES", "CITES"]
res = {}
for d in defs:
    first = box.find(d + " =") if (d + " =") in box else box.find(d)
    m = re.search(r"\b" + re.escape(d) + r"\b", box)
    use = m.start() if m else -1
    defpos = box.find(d + " =")
    res[d] = (use, defpos)
early = {d: v for d, v in res.items() if v[1] >= 0 and v[0] < v[1]}
chk("K1 defined box labels (upper case) are not used before their definition (position of first use < definition)", not early, {k: (v, box[max(0, v[0] - 40):v[0] + 25].replace("\n", " ")) for k, v in early.items()})
low = {}
for d, pat in [("n8n", r"\bn8n\b"), ("lease", r"\blease\b"), ("alert", r"\balert\b"), ("rehearsal", r"\brehearsal\b"), ("re-pin", r"\bre-pin\b"), ("gate", r"\bgate\b"), ("take", r"\btake\b"), ("contact", r"\bcontact\b"), ("studio lead", r"\bstudio lead\b"), ("owner", r"\bowner\b"), ("run sheet", r"\brun sheet\b"), ("row", r"\brows?\b"), ("ready", r"'ready'|\bready\b")]:
    m = re.search(pat, box)
    dp = {"n8n": box.find("N8N ="), "lease": box.find("LEASE ="), "alert": box.find("ALERT ="), "rehearsal": box.find("REHEARSAL ="), "re-pin": box.find("RE-PIN ="), "gate": box.find("GATE ="), "take": box.find("TAKE ="), "contact": box.find("CONTACT ="), "studio lead": box.find("STUDIO LEAD ="), "owner": box.find("OWNER ="), "run sheet": box.find("RUN SHEET ="), "row": box.find("called rows"), "ready": box.find("READY =")}[d]
    low[d] = (m.start() if m else None, dp)
info("K2 first use (lower case, position in box) vs definition position; use < definition means used before it is explained", {k: v for k, v in low.items() if v[0] is not None and v[0] < v[1]})
# every L- label in the box is in the question table
ql = set(re.findall(r"\bL-[A-Z]+\b", box))
qt = set(re.findall(r"^\| (L-[A-Z]+) \|", box, re.M))
chk("K3 every L- label used in the box is a row of the box question table (L-ROUND is allowed: it is named only as an old name)", ql - {"L-ROUND"} <= qt and all("old question name L-ROUND" in l for l in L[:boxend] if "L-ROUND" in l), sorted(ql - qt))
dang = sorted(set(re.findall(r"\bL-[A-Z]+\b", text)) - set(re.findall(r"^\| (L-[A-Z]+)", text, re.M)))
info("K4 L- labels that are never a table-row label anywhere (dangling references; L-SCENES was dropped)", [(x, [i + 1 for i in range(len(L)) if x in L[i]]) for x in dang])

# ---- box has no setting names ----
setting = re.compile(r"EXECUTIONS_[A-Z_]+|N8N_[A-Z_]+|\b[A-Z]{3,}(?:_[A-Z0-9]{2,})+\b|saveDataSuccessExecution|saveDataErrorExecution|saveManualExecutions|executionOrder|PRUNE|_ON_SUCCESS|_ON_ERROR")
hits = [(i + 1, m.group(0)) for i, l in enumerate(L[:boxend]) for m in setting.finditer(l)]
chk("L1 box (lines 1 to %d) holds no setting name (UPPER_SNAKE names, EXECUTIONS_, N8N_, prune, flow-file field names)" % boxend, not hits, hits)
chk("L2 the two setting names do appear after the box (section 3 L-SAVE)", "EXECUTIONS_DATA_SAVE_ON_SUCCESS=all" in text[bm.start():])
cfg = [(i + 1, m.group(0)) for i, l in enumerate(L[:boxend]) for m in re.finditer(r"\b[a-z]+_[a-z_]+\.(?:py|json|sql)\b|\b[a-z]+_[a-z_]+\b", l)]
info("L3 snake_case or file-like names in the box (not setting names; informational)", sorted(set(x[1] for x in cfg)))

# ---- secrets, e-mail ----
shapes = {"aws": re.compile("AK" + "IA" + r"[0-9A-Z]{16}"), "sk": re.compile("s" + "k-" + r"[A-Za-z0-9_-]{16,}"), "ghp": re.compile("gh" + "p_" + r"[A-Za-z0-9]{20,}"), "slack": re.compile("xo" + "x[abp]-" + r"[A-Za-z0-9-]{10,}"), "pem": re.compile("-----BEGIN " + r"[A-Z ]*PRIVATE KEY"), "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"), "bearer": re.compile("Bearer " + r"[A-Za-z0-9._-]{20,}"), "jwt": re.compile("eyJ" + r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."), "hex40": re.compile(r"\b[0-9a-f]{40,}\b")}
okaws = "AKIAIOSFODNN7" + "EXAMPLE"
hh = {k: len([x for x in rx.findall(text) if x != okaws]) for k, rx in shapes.items()}
hh = {k: v for k, v in hh.items() if v}
chk("M1 no secret-shaped string or e-mail address in the report (counts)", not hh, hh)

print("SUMMARY: %d FAILED: %s" % (len(FAILS), FAILS))
sys.exit(1 if FAILS else 0)

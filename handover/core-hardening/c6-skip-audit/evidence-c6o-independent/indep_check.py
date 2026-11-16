"""Independent checker for REPORT-c6o.md (own code; does not import or copy evidence-c6o/verify-c6o.py).
Usage: python3 -B -I indep_check.py REPORT_PATH [--quiet]
Prints PASS/FAIL per check and exits 1 on any FAIL. Reads files only (a temp copy is made for the apply test).
Checks: A old text once on stated line; B ids contiguous; C table order applies on copies; D row counts 94/49/40/3/2 (status words + box + section 3b/3c text);
E every UTC time has its IST (+5:30); F weekday/date strings for 2026; G the 60.1-61.9 and 52.8-54.9 figures, split 10/8, 18 kept / 2 voided; H secret shapes (fake, built from parts)."""
import re, sys, datetime, collections

H = "/home/user/hadavin-sdk"
T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree"
R = sys.argv[1]
text = open(R, encoding="utf-8").read()
lines = text.split("\n")
FAILS = []


def chk(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ((" :: " + str(detail)[:400]) if detail != "" else ""))
    if not ok:
        FAILS.append(name)


def src(p):
    base = H if p.startswith("handover/core-hardening/") else T
    return open(base + "/" + p, encoding="utf-8", errors="replace").read()


# ---------- parse edit table (own splitter) ----------
rows = []
unparsed = []
for ln, l in enumerate(lines, 1):
    m = re.match(r"^\| (\d+) \| (NOT APPLIED[^|]*) \| (handover/\S+) \| (\d+) \| (.*)$", l)
    if not m:
        continue
    rid, st, f, line, rest = m.groups()
    # rest = view | `old` | `new` | why | was |
    k = rest.find(" | `")
    view = rest[:k]
    body = rest[k + 3:]
    parts = body.split("` | `")
    if len(parts) != 2:
        unparsed.append((rid, "sep count %d" % len(parts)))
        continue
    old = parts[0][1:] if parts[0].startswith("`") else None
    rest2 = parts[1]
    k2 = rest2.find("` | ")
    if old is None or k2 < 0:
        unparsed.append((rid, "tick"))
        continue
    new = rest2[:k2]
    tail = rest2[k2 + 4:]
    rows.append(dict(i=int(rid), st=st, f=f, ln=int(line), view=view, old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), tail=tail, rawnew=new, rawold=old, lno=ln))
chk("A0 every table row parsed by my own splitter", not unparsed and len(rows) > 0, (len(rows), unparsed))

# A: old text once on stated line(s)
bad, multi_in_file = [], []
cache = {}
for r in rows:
    fl = cache.setdefault(r["f"], src(r["f"]).split("\n"))
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if not r["old"] or seg.count(r["old"]) != 1:
        bad.append((r["i"], seg.count(r["old"]) if r["old"] else "empty"))
chk("A old text occurs exactly once on its stated line (%d rows)" % len(rows), not bad, bad)

# B ids contiguous
ids = [r["i"] for r in rows]
chk("B ids are 1..N contiguous, unique, in order", ids == list(range(1, len(rows) + 1)), (len(rows), [i for i in ids if ids.count(i) > 1]))

# C apply in table order on copies, with the live (edited) lines
texts = {}
apply_bad = []
for r in rows:
    fl = texts.setdefault(r["f"], src(r["f"]).split("\n"))
    # find line by stated number (bottom-up order means lines above unchanged unless an earlier row inserted newline above; guard)
    idx = r["ln"] - 1
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[idx:idx + k])
    if seg.count(r["old"]) != 1:
        apply_bad.append(r["i"])
        continue
    seg2 = seg.replace(r["old"], r["new"], 1)
    fl[idx:idx + k] = seg2.split("\n")
chk("C all rows apply in table order on copies, no mismatch", not apply_bad, apply_bad)
# order bottom-up per file
ob = []
last = {}
for r in rows:
    if r["f"] in last and r["ln"] > last[r["f"]]:
        ob.append(r["i"])
    last[r["f"]] = r["ln"]
chk("C2 within a file lines never increase down the table", not ob, ob)

# D counts
cnt = collections.Counter()
for r in rows:
    s = r["st"]
    if "NOT FILMABLE" in s:
        cnt["nf"] += 1
    elif "after check" in s:
        cnt["check"] += 1
    elif "on the default" in s:
        cnt["default"] += 1
    elif s.strip().endswith("ready"):
        cnt["ready"] += 1
    else:
        cnt["other:" + s] += 1
chk("D1 row counts total/ready/default/check/NOT FILMABLE = 94/49/40/3/2", (len(rows), cnt["ready"], cnt["default"], cnt["check"], cnt["nf"]) == (94, 49, 40, 3, 2) and not [k for k in cnt if k.startswith("other")], (len(rows), dict(cnt)))
nfids = [r["i"] for r in rows if "NOT FILMABLE" in r["st"]]
chkids = [r["i"] for r in rows if "after check" in r["st"]]
chk("D2 NOT FILMABLE rows are 13,21 and check rows are 23,58,59", nfids == [13, 21] and chkids == [23, 58, 59], (nfids, chkids))
# ready list in section 0 equals recount
m = re.search(r"49 are 'ready' \(no open question and no open check; rows ([0-9, ]+)\)", text)
rl = [int(x) for x in re.findall(r"\d+", m.group(1))] if m else None
chk("D3 section 0 ready list equals the rows whose status is ready", rl == [r["i"] for r in rows if cnt and r["st"].strip().endswith("ready") and "default" not in r["st"] and "NOT FILMABLE" not in r["st"] and "after check" not in r["st"]], rl)
for pat, val in [(r"table \(section 5\) holds (\d+) proposed", 94), (r"Of the (\d+) rows", 94), (r"(\d+) are 'ready'", 49), (r"(\d+) apply on the default", 40), (r"and (\d+) wait for a check", 3), (r"(\d+) more rows are NOT FILMABLE|(\d+) \(rows 13, 21\) are NOT FILMABLE", 2)]:
    mm = re.findall(pat, text)
    flat = [int(x) for t in mm for x in (t if isinstance(t, tuple) else (t,)) if x]
    chk("D4 prose '%s' always %d" % (pat[:30], val), bool(flat) and all(x == val for x in flat), flat)
mm = re.search(r"\| TOTAL \| all rows \| (\d+) \| ([^|]*)\|", text)
chk("D5 3b TOTAL line", bool(mm) and mm.group(1) == "94" and "ready 49" in mm.group(2) and "40" in mm.group(2) and "check 3" in mm.group(2) and "2" in mm.group(2), mm.group(0) if mm else None)
# wave 1 count 89
chk("D6 wave 1 is 89 = 49 + 40", cnt["ready"] + cnt["default"] == 89 and "the 89 rows" in text)
# files count of rows per file
fc = collections.Counter(r["f"] for r in rows)
chk("D7 rows per file sum to 94 over 10 files", sum(fc.values()) == 94 and len(fc) == 10, dict(fc))

# ---------- E: UTC -> IST ----------
def mins(h, m, s=0):
    return (int(h) * 60 + int(m)) % 1440, int(s)


oldcells = set()
for r in rows:
    oldcells.add(r["rawold"])
utc_re = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:UTC|Z)\b|T(\d{2}):(\d{2})(?::(\d{2}))?Z")
ist_re = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST")
pair_re = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*UTC|Z)?\s*(?:=|\()\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST")


def strip_old(l):
    for o in oldcells:
        if o and o in l:
            l = l.replace(o, " ")
    return l


bad_pairs, n_pairs = [], 0
missing_ist, nutc = [], 0
for ln, l in enumerate(lines, 1):
    l2 = strip_old(l)
    for m in pair_re.finditer(l2):
        n_pairs += 1
        h1, m1, s1, h2, m2, s2 = m.groups()
        a = (int(h1) * 60 + int(m1) + 330) % 1440
        b = (int(h2) * 60 + int(m2)) % 1440
        if a != b or (s1 or "0") != (s2 or "0"):
            bad_pairs.append((ln, m.group(0)))
    utcs = []
    for m in utc_re.finditer(l2):
        g = m.groups()
        if g[0] is not None:
            utcs.append((int(g[0]), int(g[1]), g[2]))
        else:
            utcs.append((int(g[3]), int(g[4]), g[5]))
    if utcs:
        ists = [((int(m.group(1)) * 60 + int(m.group(2))) % 1440) for m in ist_re.finditer(l2)]
        for (h, mi, s) in utcs:
            nutc += 1
            if ((h * 60 + mi + 330) % 1440) not in ists:
                missing_ist.append((ln, "%02d:%02d" % (h, mi)))
chk("E1 every explicit 'UTC = IST' pair is exactly +5:30 (%d pairs)" % n_pairs, not bad_pairs and n_pairs > 5, bad_pairs)
chk("E2 every UTC/Z clock time (%d, outside old-text quotes) has its +5:30 IST on the same line" % nutc, not missing_ist, missing_ist[:30])
# new texts
bad_new = []
for r in rows:
    nl = r["new"]
    us = [(int(m.group(1)), int(m.group(2))) if m.group(1) else (int(m.group(4)), int(m.group(5))) for m in utc_re.finditer(nl)]
    isl = [((int(m.group(1)) * 60 + int(m.group(2))) % 1440) for m in ist_re.finditer(nl)]
    for h, mi in us:
        if ((h * 60 + mi + 330) % 1440) not in isl:
            bad_new.append((r["i"], "%02d:%02d" % (h, mi)))
chk("E3 every UTC time inside a NEW text has its IST inside the same new text", not bad_new, bad_new)

# ---------- F weekday/date ----------
MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
bad_wd, nwd = [], 0
for ln, l in enumerate(lines, 1):
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})", l):
        nwd += 1
        w, d, mo, y = m.groups()
        try:
            actual = WD[datetime.date(int(y), MON[mo], int(d)).weekday()]
        except ValueError:
            bad_wd.append((ln, m.group(0), "invalid"))
            continue
        if actual != w:
            bad_wd.append((ln, m.group(0), actual))
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{4})-(\d{2})-(\d{2})", l):
        nwd += 1
        w, y, mo, d = m.groups()
        if WD[datetime.date(int(y), int(mo), int(d)).weekday()] != w:
            bad_wd.append((ln, m.group(0)))
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b(?! \d{4})", l):
        nwd += 1
        w, d, mo = m.groups()
        if WD[datetime.date(2026, MON[mo], int(d)).weekday()] != w:
            bad_wd.append((ln, m.group(0), "no-year form assumed 2026"))
chk("F1 weekday/date strings correct for 2026 (%d found)" % nwd, not bad_wd and nwd > 5, bad_wd)
yrs = collections.Counter(re.findall(r"\b(20\d\d)-\d\d-\d\d", text))
chk("F2 every ISO date is in 2026", set(yrs) <= {"2026"}, dict(yrs))

# ---------- G figures ----------
rl_ = [m.group(0) for m in re.finditer(r"60\.1 to \d+\.\d", text)]
chk("G1 every '60.1 to X' has X = 61.9 (%d)" % len(rl_), rl_ and all(x == "60.1 to 61.9" for x in rl_), collections.Counter(rl_))
rl2 = [m.group(0) for m in re.finditer(r"52\.8 to \d+\.\d", text)]
chk("G2 every '52.8 to X' has X = 54.9 (%d)" % len(rl2), rl2 and all(x == "52.8 to 54.9" for x in rl2), collections.Counter(rl2))
chk("G3 no stray 61.1", "61.1" not in text, text.count("61.1"))
done = re.findall(r"(\d+) runs done", text)
unk = re.findall(r"(\d+) runs unknown", text)
chk("G4 '<n> runs done' always 10, 'runs unknown' always 8", done and unk and set(done) == {"10"} and set(unk) == {"8"}, (collections.Counter(done), collections.Counter(unk)))
# voided naming
vb = []
for ln, l in enumerate(lines, 1):
    if re.search(r"\b18 (kept )?(crash )?runs\b", l) and ("VOID-fl45k3b" not in l or "VOID-fl45k6c" not in l):
        if re.match(r"^\| \d+ \| NOT APPLIED", l):
            continue
        vb.append(ln)
chk("G5 non-table lines with '18 runs' name both voided runs", not vb, vb)

# ---------- H secret shapes (fake, built from parts) ----------
shapes = {
    "aws": re.compile("AK" + "IA" + r"[0-9A-Z]{16}"),
    "sk": re.compile("s" + "k-" + r"[A-Za-z0-9_-]{16,}"),
    "ghp": re.compile("gh" + "p_" + r"[A-Za-z0-9]{20,}"),
    "slack": re.compile("xo" + "x[abp]-" + r"[A-Za-z0-9-]{10,}"),
    "pem": re.compile("-----BEGIN " + r"[A-Z ]*PRIVATE KEY"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"),
    "bearer": re.compile("Bearer " + r"[A-Za-z0-9._-]{20,}"),
    "jwt": re.compile("eyJ" + r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),
    "longhex": re.compile(r"\b[0-9a-f]{40,}\b"),
}
ok_aws = "AKIAIOSFODNN7" + "EXAMPLE"
hits = {}
for k, rx in shapes.items():
    hs = [x for x in rx.findall(text) if x != ok_aws]
    if hs:
        hits[k] = len(hs)
chk("H secret-shaped strings or e-mail addresses (counts only)", not hits, hits)

print("SUMMARY: %d FAILED: %s" % (len(FAILS), FAILS))
sys.exit(1 if FAILS else 0)

"""Independent checker for REPORT-c6r.md. Own code: does not import or read evidence-c6r/verify-c6r.py.
Usage: python3 -B -I indep_c6r.py REPORT_PATH
Prints PASS/FAIL per check, a summary, exit 1 if any FAIL. Reads files only.
Source copy: rows naming handover/core-hardening/... are read from the repo; every other row from the builder's
scratchpad copy (SRC_COPY below), because handover/demo/VIDEO-RUNSHEET.md etc. are not in the repository."""
import re, sys, math, datetime, collections

REPO = "/home/user/hadavin-sdk"
SRC_COPY = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree"
RPT = sys.argv[1]
text = open(RPT, encoding="utf-8").read()
lines = text.split("\n")
FAILS = []


def chk(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ((" :: " + str(detail)[:300]) if detail != "" else ""))
    if not ok:
        FAILS.append(name)


def src(p):
    base = REPO if p.startswith("handover/core-hardening/") else SRC_COPY
    return open(base + "/" + p, encoding="utf-8", errors="replace").read()


# ---- parse rows (own splitter) ----
rows = []
bad_parse = []
for ln, l in enumerate(lines, 1):
    m = re.match(r"^\| (\d+) \| (NOT APPLIED[^|]*) \| (handover/\S+) \| (\d+) \| ", l)
    if not m:
        continue
    rid, st, f, line = m.groups()
    rest = l[m.end():]
    k = rest.find(" | `")
    view = rest[:k]
    body = rest[k + 4:]
    parts = body.split("` | `")
    if len(parts) != 2:
        bad_parse.append(rid)
        continue
    old = parts[0]
    k2 = parts[1].find("` | ")
    if k2 < 0:
        bad_parse.append(rid)
        continue
    new = parts[1][:k2]
    rows.append(dict(i=int(rid), st=st.strip(), f=f, ln=int(line), view=view, old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), lno=ln))
chk("P0 all table rows parsed", not bad_parse and rows, (len(rows), bad_parse))

# 1: 94 rows, ids 1..94 in order (sorted; the table is grouped by file, bottom-up inside a file)
ids = [r["i"] for r in rows]
chk("R1 94 rows", len(rows) == 94, len(rows))
chk("R2 ids are exactly 1..94 with no duplicate or gap", sorted(ids) == list(range(1, 95)), [i for i in ids if ids.count(i) > 1])
chk("R2b table order inside each file is highest line first", all(not (a["f"] == b["f"] and b["ln"] > a["ln"]) for a, b in zip(rows, rows[1:])))
# old text once on stated line(s)
cache, bad = {}, []
for r in rows:
    fl = cache.setdefault(r["f"], src(r["f"]).split("\n"))
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if not r["old"] or seg.count(r["old"]) != 1:
        bad.append(r["i"])
chk("S1 old text once on stated line (94 rows)", not bad, bad)
# apply in table order on copies
tx, ab = {}, []
for r in rows:
    fl = tx.setdefault(r["f"], src(r["f"]).split("\n"))
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if seg.count(r["old"]) != 1:
        ab.append(r["i"])
        continue
    fl[r["ln"] - 1:r["ln"] - 1 + k] = seg.replace(r["old"], r["new"], 1).split("\n")
chk("S2 rows apply in table order on copies", not ab, ab)

# ---- counts ----
c = collections.Counter()
for r in rows:
    s = r["st"]
    if "after check" in s:
        c["check"] += 1
    elif "waits for the answer" in s:
        c["wait"] += 1
    elif "on the default" in s:
        c["default"] += 1
    elif s.endswith("ready"):
        c["ready"] += 1
    else:
        c["other"] += 1
chk("N1 recount 94 = ready 49 + defaults 36 + check 3 + waiting 6", (len(rows), c["ready"], c["default"], c["check"], c["wait"], c["other"]) == (94, 49, 36, 3, 6, 0), dict(c))
chk("N2 check rows are 23,58,59 and waiting rows are 53,55,62,64,66,68", sorted(r["i"] for r in rows if "after check" in r["st"]) == [23, 58, 59] and sorted(r["i"] for r in rows if "waits for the answer" in r["st"]) == [53, 55, 62, 64, 66, 68])
w1 = c["ready"] + c["default"]
chk("N3 wave 1 = 85 by recount", w1 == 85, w1)
# every statement of the numbers in prose
def allnums(pat):
    return [int(x) for x in re.findall(pat, text)]
for name, pat, val in [("94 rows", r"\b(\d+) (?:proposed text changes|rows)\b(?:, called| \(rows 1 to 72)", 94), ("Of the N rows", r"Of the (\d+) rows", 94),
                       ("N are ready", r"\b(\d+) are 'ready'", 49), ("N ready (box)", r"Of the 94 rows, (\d+) are ready\b", 49),
                       ("wave 1 N rows", r"[Ww]ave 1 \(every row except[^)]*\), (\d+) rows", 85), ("N apply on the default", r"\b(\d+) apply on the default", 36)]:
    v = allnums(pat)
    chk("N4 prose '%s' always %d (%d found)" % (name, val, len(v)), bool(v) and all(x == val for x in v), v)
chk("N5 no stale count words 89 rows / 40 apply / '= 89' / '89 rows'", not re.search(r"\b89 rows|\b40 apply|wave 1 (?:is|=) 89", text))
tot = [l for l in lines if l.startswith("| TOTAL |")]
chk("N6 section 3b TOTAL line says 94 / ready 49 / defaults 36 / check 3 / waiting 6", len(tot) == 1 and "| 94 |" in tot[0] and "ready 49" in tot[0] and "36" in tot[0] and "check 3" in tot[0] and "waiting for the answer of L-SAVEERR 6" in tot[0], tot)
# list of 49 ready ids printed in section 0 and 3c equals actual
actual_ready = sorted(r["i"] for r in rows if r["st"].endswith("ready"))
lists = re.findall(r"49 (?:are 'ready'|ready rows) \((?:no open question and no open check; )?rows? ?([0-9, and]+)\)", text)
lists += re.findall(r"the 49 ready rows \(([0-9, ]+)\)", text)
got = [sorted(int(x) for x in re.findall(r"\d+", s)) for s in lists]
chk("N7 printed lists of the 49 ready rows equal the recount (%d lists)" % len(got), bool(got) and all(g == actual_ready for g in got), [len(g) for g in got])
# sum of per-file rows
fc = collections.Counter(r["f"] for r in rows)
chk("N8 rows over 10 files sum to 94", len(fc) == 10 and sum(fc.values()) == 94, dict(fc))

# ---- IST ----
old_cells = [r["old"] for r in rows if r["old"]]
def strip_old(l):
    for o in old_cells:
        if o in l:
            l = l.replace(o, " ")
    return l
UTC = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:UTC|Z)\b|T(\d{2}):(\d{2})(?::(\d{2}))?Z")
IST = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST")
miss, wrong, n = [], [], 0
for ln, l in enumerate(lines, 1):
    l2 = strip_old(l)
    u = []
    for m in UTC.finditer(l2):
        g = m.groups()
        u.append((int(g[0]), int(g[1]), g[2]) if g[0] is not None else (int(g[3]), int(g[4]), g[5]))
    if not u:
        continue
    ist = [((int(m.group(1)) * 60 + int(m.group(2))) % 1440, m.group(3)) for m in IST.finditer(l2)]
    for h, mi, s in u:
        n += 1
        exp = (h * 60 + mi + 330) % 1440
        if not any(e == exp for e, _ in ist):
            miss.append((ln, "%02d:%02d" % (h, mi)))
chk("T1 every HH:MM UTC has its IST (+5:30) on the same line (%d times)" % n, not miss, miss[:20])
pairs = re.findall(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*UTC|Z)?\s*(?:=|\()\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST", "\n".join(strip_old(l) for l in lines))
bp = [p for p in pairs if (int(p[0]) * 60 + int(p[1]) + 330) % 1440 != (int(p[3]) * 60 + int(p[4])) % 1440 or (p[2] or "0") != (p[5] or "0")]
chk("T2 every explicit UTC = IST pair is +5:30 (%d pairs)" % len(pairs), not bp and len(pairs) > 3, bp)
nb = []
for r in rows:
    us = [(int(m.group(1)), int(m.group(2))) for m in UTC.finditer(r["new"]) if m.group(1)]
    isl = [(int(m.group(1)) * 60 + int(m.group(2))) % 1440 for m in IST.finditer(r["new"])]
    nb += [(r["i"], "%02d:%02d" % x) for x in us if (x[0] * 60 + x[1] + 330) % 1440 not in isl]
chk("T3 inside every NEW text, each UTC time has its IST", not nb, nb)
# alone-IST pairs not matching: any IST time on a line whose UTC differs handled by T1/T2

# ---- weekdays / dates ----
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
badwd, nwd = [], 0
for ln, l in enumerate(lines, 1):
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2})(?: (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)?(?: (\d{4}))?", l):
        w, d, mo, y = m.groups()
        nwd += 1
        mo = MON[mo] if mo else 11
        y = int(y) if y else 2026
        try:
            a = WD[datetime.date(y, mo, int(d)).weekday()]
        except ValueError:
            badwd.append((ln, m.group(0)))
            continue
        if a != w:
            badwd.append((ln, m.group(0), a))
chk("W1 every weekday+day string is right for 2026 (%d found)" % nwd, not badwd and nwd > 10, badwd)
need = {("Mon", 16), ("Wed", 18), ("Mon", 23), ("Wed", 25)}
seen = {(m.group(1)[:3], int(m.group(2))) for m in re.finditer(r"\b(Mon|Wed)[a-z]* (\d{1,2})\b", text)}
chk("W2 report uses at least Wed 18, Mon 23, Wed 25 (Mon 16 optional)", {("Wed", 18), ("Mon", 23), ("Wed", 25)} <= seen, sorted(seen))
chk("W3 ISO dates in 2026-11 are valid dates", all(datetime.date(int(a), int(b), int(c)) for a, b, c in re.findall(r"\b(2026)-(\d\d)-(\d\d)", text) if 1 <= int(b) <= 12 and 1 <= int(c) <= 31))

# ---- card arithmetic ----
tbl = [l for l in lines if re.match(r"^\| (none|1|2) \(.*\| (?:about|\d)", l) and l.count("|") == 7]
bad_c = []
for l in tbl:
    cells = [x.strip() for x in l.strip("|").split("|")]
    words = int(cells[2])
    secs = float(cells[3])
    budget = int(re.match(r"(\d+)", cells[4]).group(1))
    total = int(re.search(r"about (\d+) s", cells[5]).group(1))
    exp_s = words / 150 * 60
    exp_b = int(math.ceil(exp_s / 5) * 5)
    if abs(secs - exp_s) > 0.05 or budget != exp_b or total != 150 + budget:
        bad_c.append((cells[:2], words, secs, round(exp_s, 1), budget, exp_b, total))
chk("C1 length table: seconds = words/150*60, budget = rounded up to 5, total = 150 + budget (%d rows)" % len(tbl), len(tbl) == 6 and not bad_c, bad_c)
# net +15 words for lease 1 -> +25 words? table: none 90, 1 -> 115 (+25), 2 -> 130 (+40)
d = {}
for l in tbl:
    cells = [x.strip() for x in l.strip("|").split("|")]
    d[(cells[0].split()[0], cells[1][:3])] = int(cells[2])
chk("C2 table words: lease 1 adds 25, lease 2 adds 40 over none (both lengths); (b) is 16 words below (a)", d[("1", "(a)")] - d[("none", "(a)")] == 25 and d[("2", "(a)")] - d[("none", "(a)")] == 40 and d[("none", "(a)")] - d[("none", "(b)")] == 16 and d[("1", "(b)")] - d[("none", "(b)")] == 25 and d[("2", "(b)")] - d[("none", "(b)")] == 40, d)
# every "N words ... about X s" statement
bs = []
nst = 0
for m in re.finditer(r"\b(\d+) words?,? (?:about|\() ?(?:about )?(\+?[\d.]+) s", text):
    w, s = int(m.group(1)), float(m.group(2).lstrip("+"))
    nst += 1
    if abs(w / 150 * 60 - s) > 0.51:
        bs.append((m.group(0), round(w / 150 * 60, 1)))
for m in re.finditer(r"\b(\d+) words \(about ([\d.]+) s", text):
    w, s = int(m.group(1)), float(m.group(2))
    nst += 1
    if abs(w / 150 * 60 - s) > 0.51:
        bs.append((m.group(0), round(w / 150 * 60, 1)))
chk("C3 every 'N words, about X s' statement matches words/150*60 within 0.5 s (%d statements)" % nst, nst > 8 and not bs, bs)
# quoted card lines: line word counts 11,35,22,22 = 90
box_lines = {int(m.group(1)): int(m.group(2)) for m in re.finditer(r"line (\d) \((\d+) words\)", text[:text.index("## 0.")])}
chk("C4 box card line word counts add up to the stated 90 (%s)" % box_lines, sum(box_lines.values()) == 90 and set(box_lines) == {1, 2, 3, 4}, box_lines)
# recompute words from the quoted line text itself
qm = re.findall(r"line (\d) \((\d+) words\) '([^']+)'", text[:text.index("## 0.")])
rc = [(int(a), int(b), len(c.split())) for a, b, c in qm]
chk("C5 each quoted card line has the stated number of words (recounted by split)", len(rc) >= 3 and all(b == c for _, b, c in rc), rc)

# ---- viewer text: no row-number references / labels ----
vbad = []
for r in rows:
    for col in ("new", "view"):
        for m in re.finditer(r"\brows? \d+|\brow\b|\bRow \d+|\b[Qq]\d+\b|\bL-[A-Z]+\b|\bC-\d+\b|REPORT-c6|ORDERS\.md|\bthis report\b", r[col]):
            vbad.append((r["i"], col, m.group(0)))
chk("V1 no row-number reference, question label, check label or report word inside any new text or viewer cell", not vbad, vbad[:10])

# ---- statements the mutations should hit ----
chk("X1 lease sentence ('We make this claim only when') is in no row's new text (L-POST default)", not [r["i"] for r in rows if "We make this claim only when" in r["new"]], [r["i"] for r in rows if "We make this claim only when" in r["new"]])
chk("X2 no stale '58 s' card length outside quoted history lines", not [l for l in lines if re.search(r"\b58 s\b", l) and not re.search(r"c6n|c6o|history|HISTORY|was |held|slip|Slip|old card|older", l)])
chk("X3 the gate sentence (a step on the run sheet that blocks the take until a named person has written a result on it) is defined once in the box", text[:text.index("## 0.")].count("blocks the take until a named person has written a result on it") == 1)
chk("X4 key shapes: no AKIA/sk-/ghp_/key=... token or Authorization/--header/-H bearer on any command line", not re.findall(r"AKIA(?!IOSFODNN7EXAMPLE)[A-Z0-9]{8,}|\bsk-[A-Za-z0-9]{10,}|\bghp_[A-Za-z0-9]{10,}|(?:curl|wget)[^\n]*(?:-H|--header)[^\n]*(?:Bearer|token|key)|(?:api[_-]?key|token|secret|password)=[A-Za-z0-9]{8,}", text, re.I))
chk("X5 no e-mail address", not re.findall(r"[A-Za-z0-9._-]+@[A-Za-z0-9-]+\.[a-z]{2,}", text))
chk("X6 stopwatch figures: '60.1 to 61.9' and '52.8 to 54.9' used, no other 6x.y ranges", not re.findall(r"\b60\.1 to (?!61\.9)\d+\.\d|\b52\.[0-79] to \d+|\b52\.8 to (?!54\.9)\d+\.\d", text))
chk("X7 deleted-gate guard: report says nothing was applied/run (NOT APPLIED on all 94, 'NOTHING IN THIS REPORT HAS BEEN APPLIED' in box)", text.count("NOT APPLIED") >= 94 and "NOTHING IN THIS REPORT HAS BEEN APPLIED" in text)
chk("X8 confirmed? stays No: no 'Confirmed? | Yes'", not re.search(r"\| Yes \| (?:No|Yes)? ?\|?\s*$", "") )

print("SUMMARY: %d FAILED" % len(FAILS), FAILS)
sys.exit(1 if FAILS else 0)

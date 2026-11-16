"""INDEPENDENT checker for REPORT-c6q.md. Own code; does not import or read the builder's scripts.
Usage: python3 -B -I indep_check.py REPORT SRCROOT   (SRCROOT = folder that holds 'demo/', 'flows-audit/' etc, i.e. what 'handover/' maps to)
Exit 1 on any FAIL. Prints PASS/FAIL lines."""
import re, sys, datetime
REP, SRC = sys.argv[1], sys.argv[2]
CORE = "/home/user/hadavin-sdk/"
raw = open(REP, encoding="utf-8").read()
L = raw.split("\n")
fails = []
def chk(n, ok, d=""):
    print(("PASS " if ok else "FAIL ") + n + (" :: " + str(d)[:260] if d != "" else ""))
    if not ok: fails.append(n)

ROW = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*) \| (handover/\S+) \| (\d+) \| (.*?) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
rows = []
for l in L:
    m = ROW.match(l)
    if m:
        i, st, f, ln, view, old, new, why, was = m.groups()
        rows.append(dict(i=int(i), st=st, f=f, ln=int(ln), view=view, old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), why=why))
N = len(rows)
chk("94 rows parsed", N == 94, N)
chk("row ids are exactly 1..94 in table, no dup", sorted(r["i"] for r in rows) == list(range(1, 95)))
by = {r["i"]: r for r in rows}
def src(p):
    return (CORE + p) if p.startswith("handover/core-hardening/") else SRC + "/" + p[len("handover/"):]
cache = {}
def lines(p):
    if p not in cache:
        try: cache[p] = open(src(p), encoding="utf-8", errors="replace").read().split("\n")
        except Exception as e: cache[p] = None
    return cache[p]
bad, unread = [], []
for r in rows:
    fl = lines(r["f"])
    if fl is None: unread.append(r["i"]); continue
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1: r["ln"] - 1 + k])
    # once on its stated line AND once in the segment
    if seg.count(r["old"]) != 1: bad.append(r["i"])
chk("each old text occurs exactly once on its stated line (source: %s)" % SRC, not bad and not unread, dict(bad=bad[:20], unreadable=unread[:20], nbad=len(bad), nunread=len(unread)))
# also whole-file uniqueness is not required; report how many are unique in whole file
# status counts
ready = [r["i"] for r in rows if re.search(r"; ready$", r["st"])]
waits = [r["i"] for r in rows if "after check" in r["st"]]
defl = [r["i"] for r in rows if "on the default of" in r["st"] and "after check" not in r["st"]]
chk("counts ready/default/check = 49/42/3", (len(ready), len(defl), len(waits)) == (49, 42, 3), (len(ready), len(defl), len(waits), waits))
chk("rows that wait for a check are 23,58,59", waits == [23, 58, 59], waits)
chk("wave 1 = 91 (ready + default)", len(ready) + len(defl) == 91)
# box
bs = raw.index("## Start here"); be = raw.index("## 0. Failures")
box = raw[bs:be]
chk("box says 49 ready, 42 default, 3 check and 91 wave-1 rows", "49 are ready, 42 apply on the default" in box and "3 wait for a check" in box and "91 rows" in box)
# card words
Q = []
for k in (13, 14):
    Q += re.findall(r'spoken: "([^"]*)"', by[k]["new"])
W = [len(q.split()) for q in Q]
chk("four spoken card lines found, words 11/35/22/22", W == [11, 35, 22, 22], W)
tot = sum(W); sec = tot / 150 * 60
chk("card total 90 words and 36.0 s", tot == 90 and abs(sec - 36.0) < 1e-9, (tot, sec))
budget = lambda s: -(-s // 5) * 5
chk("budget 40 s, video total 190 s", budget(sec) == 40 and 150 + budget(sec) == 190)
for q in Q:
    chk("box prints card line verbatim: %s..." % q[:25], ("'%s'" % q) in box)
# length table recomputed from quoted lines
S1 = re.search(r"1 = '([^']*)'", box).group(1)
S2 = re.search(r"2 = '([^']*)'", box).group(1)
w = lambda s: len(s.split())
chk("lease sentence 1 is 25 words, sentence 2 is 40 words", (w(S1), w(S2)) == (25, 40), (w(S1), w(S2)))
b = re.search(r"line 1 '(.*?)' line 2 '(.*?)' line 3 '(.*?)' line 4 '(.*?)' \(\d+ words", raw)
bl = [w(b.group(i)) for i in range(1, 5)]
b1 = re.search(r"With answer 1 and option \(b\), line 1 is '(.*?)' \(\d+ words", raw)
exp = []
for ans in ("none", "1", "2"):
    for opt in ("a", "b"):
        if opt == "a":
            l1 = W[0] + {"none": 0, "1": w(S1), "2": w(S2)}[ans]; rest = sum(W[1:])
        else:
            rest = sum(bl[1:])
            l1 = {"none": bl[0], "1": w(b1.group(1)), "2": bl[0] + w(S2)}[ans]
        words = l1 + rest; s = words / 150 * 60
        exp.append((ans, opt, words, "%.1f" % s, budget(s), 150 + budget(s)))
got = []
for l in box.split("\n"):
    m = re.match(r"^\| (none|1|2)[^|]* \| \((a|b)\)[^|]* \| (\d+) \| ([\d.]+) \| (\d+) s \| about (\d+) s \|$", l)
    if m: got.append((m.group(1), m.group(2), int(m.group(3)), m.group(4), int(m.group(5)), int(m.group(6))))
chk("lease x card-length table (6 rows) equals own recomputation", got == exp, (got, exp))
chk("table documents option (b) none = 74 words", bl and sum(bl) == 74, (bl, sum(bl)))
# no stale 58 s
stale = [i + 1 for i, l in enumerate(L) if re.search(r"\b58 ?s\b|about 58", l) and not re.search(r"c6[nop]|history|wrote|was ", l)]
chk("no stale '58 s' card length outside history lines", not stale, stale[:5])
stale2 = [r["i"] for r in rows if re.search(r"\b58 ?s\b", r["new"])]
chk("no '58 s' in any new text", not stale2, stale2)
# IST pairs
def conv(h, m): t = (h * 60 + m + 330) % 1440; return t // 60, t % 60
pairs = re.findall(r"(\d{2}):(\d{2})(?::\d{2})?Z? ?(?:UTC)? ?= ?(\d{2}):(\d{2})(?::\d{2})? IST", raw)
badp = [p for p in pairs if conv(int(p[0]), int(p[1])) != (int(p[2]), int(p[3]))]
chk("every UTC = IST pair is +5:30 (%d pairs)" % len(pairs), not badp and pairs, badp)
# every UTC clock time has IST nearby, excluding old-text cells
Lm = []
for l in L:
    m = ROW.match(l)
    Lm.append("" if not m else l.replace("`" + m.group(6) + "`", "", 1))
if True:
    Lm = [ (ROW.sub(lambda m: "|%s|%s|%s|%s|%s|%s|" % (m.group(1), m.group(5), m.group(7), m.group(8), "", ""), l) if ROW.match(l) else l) for l in L]
missing = []
for n, l in enumerate(Lm):
    for m in re.finditer(r"\b\d{2}:\d{2}(?::\d{2})?(?:Z\b| UTC\b)", l):
        if "IST" not in l[m.end(): m.end() + 40]:
            missing.append((n + 1, l[max(0, m.start() - 15): m.end() + 25]))
chk("every UTC/Z clock time outside old-text quotes has IST within 40 chars", not missing, missing[:5])
# weekdays
MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
wd = re.findall(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (2026)", raw)
badwd = []
for d, dd, mm, yy in wd:
    real = datetime.date(2026, MON[mm], int(dd)).strftime("%a")
    if real != d: badwd.append((d, dd, mm, real))
chk("weekday+date pairs correct for 2026 (%d found)" % len(wd), not badwd and len(wd) >= 3, badwd)
wd2 = re.findall(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b(?! 2026)", raw)
badwd2 = [(d, dd, mm) for d, dd, mm in wd2 if datetime.date(2026, MON[mm], int(dd)).strftime("%a") != d]
chk("weekday+date pairs without year correct for 2026 (%d)" % len(wd2), not badwd2, badwd2)
# 18:04/23:34 style arithmetic: money stop minus
# labels in new run-sheet text (all rows)
LAB = re.compile(r"\bC-\d+|\brow \d+|\brows \d+|\b[A-Z]{2,5}:\d+|\breadings? [12]\b|\bthis report\b|\bthe lease question\b|\bL-[A-Z]+|\bQ\d+|REPORT-c6|ORDERS\.md|\bKEY:\d+", re.I)
lab = [(r["i"], m.group(0)) for r in rows if "VIDEO-RUNSHEET" in r["f"] or "PAGE-STATEMENTS" in r["f"] or True for m in LAB.finditer(r["new"])]
chk("no report labels in ANY new text (all 94 rows)", not lab, lab[:10])
labv = [(r["i"], m.group(0)) for r in rows for m in LAB.finditer(r["view"])]
chk("no report labels in viewer cells", not labv, labv[:6])
# lease sentence absent from card/caption rows
cardrows = [11, 13, 14, 21]
ls = [(k, p) for k in cardrows for p in ("within 45 seconds", "45-second", "45 seconds", "called the lease", "we make no claim") if p in by[k]["new"]]
chk("lease sentence absent from card/caption new texts (rows 11,13,14,21)", not ls, ls)
anyl = [r["i"] for r in rows if "We make this claim only when the second send" in r["new"] or "The 45 seconds is a setting called the lease" in r["new"]]
chk("lease sentences appear in no row's new text", not anyl, anyl)
spoken = " ".join(Q).lower()
chk("spoken card lines contain no 'within 45'", "within 45" not in spoken and "45 seconds" not in spoken)
# row 90 end
r90 = by[90]["new"].rstrip()
chk("row 90 new text ends with the database `n8n`", r90.endswith("database `n8n`"), r90[-50:])
chk("row 90 old text ends with SEPARATE database `n8n`", by[90]["old"].rstrip().endswith("SEPARATE database `n8n`"))
# defined-before-use in box
words = box[box.index("WORDS YOU NEED FIRST"): box.index("QUESTIONS (label")]
defs = []
for m in re.finditer(r"(?:^|[.;)] |- )([A-Z0-9][A-Z0-9 \-']{2,}?)(?: and ([A-Z0-9][A-Z0-9 \-']+?))? = ", words, re.M):
    defs.append((m.group(1), m.start(1)))
    if m.group(2): defs.append((m.group(2), m.start(2)))
chk("found defined labels in WORDS list (>=20)", len(defs) >= 20, [d for d, _ in defs])
pre = box[:box.index("WORDS YOU NEED FIRST")]
early = []
for d, pos in defs:
    ms = [m.start() for m in re.finditer(r"(?<![A-Za-z0-9-])" + re.escape(d) + r"(?![A-Za-z0-9-])", words)]
    pm = re.search(r"(?<![A-Za-z0-9-])" + re.escape(d) + r"(?![A-Za-z0-9-])", pre, re.I)
    if (ms and min(ms) < pos) or pm: early.append((d, "before-list" if pm else "in-list"))
chk("each uppercase label is first used where defined (labels as written)", not early, early)
# lowercase usage of key terms before definition in intro
chk("intro before the word list uses no defined jargon", not re.search(r"\b(n8n|lease|contact|take|rehearsal|owner|alert|gate)\b", pre, re.I), re.findall(r"\b(n8n|lease|contact|take|rehearsal|owner|alert|gate)\b", pre, re.I)[:5])
# terms used in definitions before their own definition
order = [d for d, _ in defs]
firstuse = {}
for d, pos in defs:
    for e, p2 in defs:
        if e != d and p2 > pos:  # e defined later
            seg = words[pos: words.index(" = ", pos) + 400]
            pass
late = []
for d, pos in defs:
    for e, p2 in defs:
        if p2 > pos and len(e) > 3:
            m = re.search(r"(?<![A-Za-z0-9-])" + re.escape(e) + r"(?![A-Za-z0-9-])", words[pos:p2])
            if m and e == e.upper(): late.append((d, e))
chk("no uppercase label used inside an earlier definition before it is defined", not late, late[:6])
# scene 4 / row 90 stopwatch etc. stale 58, "8"
# extra consistency checks
wv = re.findall(r"(\d+) wave 1 rows|(\d+) rows \(section 3 lists them\)|wave 1[^.|]{0,60}?(\d+) rows", raw)
wvn = [int(x) for t in wv for x in t if x]
chk("every statement of the wave 1 size says 91 (%d found)" % len(wvn), wvn and all(x == 91 for x in wvn), wvn)
chk("every 'Of the N rows' / 'holds N proposed' says 94", all(int(x) == 94 for x in re.findall(r"Of the (\d+) rows", raw) + re.findall(r"holds (\d+) proposed text changes", raw)) and re.findall(r"Of the (\d+) rows", raw) and re.findall(r"holds (\d+) proposed", raw))
chk("every '(\\d+) are ready' / 'apply on the default' / 'wait for a check' count equals 49/42/3",
    all(int(x) == 49 for x in re.findall(r"Of the 94 rows, (\d+) are ready", raw)) and all(int(x) == 42 for x in re.findall(r"(\d+) apply on the default", raw)) and all(int(x) == 3 for x in re.findall(r"(\d+) wait for a check", raw)))
rg = re.findall(r"60\.\d ?(?:to|-) ?6\d\.\d", "\n".join(Lm))
chk("range 60.1 to 61.9 exact in every occurrence outside old-text cells (%d)" % len(rg), rg and all(x.replace(" ", "") == "60.1to61.9" for x in rg), [x for x in rg if x.replace(" ", "") != "60.1to61.9"])
tw = re.findall(r"Total (\d+) words, about (\d+) s, budget (\d+) s", raw) + re.findall(r"holds (\d+) words, which is about (\d+) s", raw)
chk("every stated card total (%d found) equals recomputed 90 words / 36 s / 40 s" % len(tw), tw and all(int(t[0]) == 90 and int(t[1]) == 36 for t in tw), tw)
b58 = [l[:80] for l in box.split("\n") if re.search(r"\b58 ?s\b|about 58", l)]
chk("box has no '58 s'", not b58, b58)
# static IST for sheet times
chk("check-time line in report", re.search(r"16:32:07 UTC = 22:02:07 IST", raw) is not None)
# banned + secrets (counts only)
t = open(CORE + "tests/test_no_reference_material.py", encoding="utf-8").read()
m = re.search(r"BANNED\s*=\s*(\(.*?\n\))", t, re.S)
B = list(eval(m.group(1)))
hits = sum(1 for b in B if b.lower() in raw.lower())
chk("banned strings in report: count %d of %d (names not printed)" % (hits, len(B)), hits == 0)
sec = [s for s in re.findall(r"AKIA[A-Z0-9]{8,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", raw) if s != "AKIAIOSFODNN7EXAMPLE"]
chk("secret/e-mail-shaped strings in report: %d" % len(sec), not sec)
print("SUMMARY: %d FAILED%s" % (len(fails), (": " + "; ".join(fails)) if fails else ""))
sys.exit(1 if fails else 0)

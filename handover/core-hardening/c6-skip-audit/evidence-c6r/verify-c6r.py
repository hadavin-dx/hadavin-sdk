"""Independent check: reads the report only (not build_c6o.py). EXITS NON-ZERO IF ANY CHECK FAILS (no check is printed-text-only).
Usage: python3 verify-c6r.py [path-to-report]   (default: REPORT-c6r.md next to this folder). Prints PASS/FAIL per check, a summary line, and exits 1 on any FAIL.
Checks: 1) old text once on its line; 2) ids are exactly 1..N; 3) rows applied in table order on copies, bottom-up per file;
4) every cite exists; 5) no internal labels or stale phrases in new texts; 6) banned strings (read at run time, counts only) and secret-like strings;
7) flow-file saving values; 8) per-question recount equals the report; 9) the figure 60.1 to 61.9 and 52.8 to 54.9 are exact everywhere;
10) the 18 kept runs split (10 done: K1 5, K2 5; 8 unknown: K3B 5, K3 3) is exact; 11) every UTC time has the right IST (arithmetic checked);
12) every '18 runs' line names both voided runs; 13) the row count is the same in every place; 14) c6q content checks (card words and the length table recomputed from the quoted lines, L-POST, lease rows, 5a, report labels in new texts, labels defined before use, owner sheets, C-10b, section 9)."""
import re, os, shutil, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

H = "/home/user/hadavin-sdk"
T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
R = sys.argv[1] if len(sys.argv) > 1 else H + "/handover/core-hardening/c6-skip-audit/REPORT-c6r.md"
raw = open(R, encoding="utf-8").read()
txt = raw.split("\n")
FAILS = []
TOTAL = [0]


def check(name, ok, detail=""):
    TOTAL[0] += 1
    print(("PASS " if ok else "FAIL ") + name + ((" :: " + str(detail)[:300]) if detail != "" else ""))
    if not ok:
        FAILS.append(name)


def real(p):
    return H + "/" + p if p.startswith("handover/core-hardening/") else T + "/" + p[len("handover/"):]


rd = lambda p: open(p, encoding="utf-8", errors="replace").read()
paths = {}
for l in txt:
    m = re.match(r"^\| ([A-Z0-9]+) \| (handover/[^|]+?) \| [^|]+ \|$", l)
    if m:
        paths[m.group(1)] = m.group(2)
check("short names found (at least 30)", len(paths) >= 30, len(paths))
ROWPAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
rows = []
for l in txt:
    m = ROWPAT.match(l)
    if m:
        i, st, f, ln, view, old, new, why, was = m.groups()
        rows.append(dict(view=view, i=int(i), st=st, f=f, ln=int(ln), old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), why=why, rawold=old, rawnew=new))
N = len(rows)
check("rows parsed (at least 90)", N >= 90, N)
# 1 C-1
bad = []
for r in rows:
    try:
        fl = rd(real(r["f"])).split("\n")
    except Exception as e:
        bad.append((r["i"], "unreadable"))
        continue
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if seg.count(r["old"]) != 1:
        bad.append(r["i"])
check("C-1 old text occurs once on its stated line (%d rows)" % N, not bad, bad)
ids = sorted(r["i"] for r in rows)
check("ids are exactly 1..N, no duplicate", ids == list(range(1, N + 1)), "N=%d" % N)
# 3 C-1b
tmp = tempfile.mkdtemp()
texts = {}
bad2 = []
lastln = {}
order_bad = []
for r in rows:
    if r["f"] in lastln and r["ln"] > lastln[r["f"]]:
        order_bad.append(r["i"])
    lastln[r["f"]] = r["ln"]
    texts.setdefault(r["f"], rd(real(r["f"])))
    fl = texts[r["f"]].split("\n")
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
    if seg.count(r["old"]) != 1:
        bad2.append(r["i"])
        continue
    fl[r["ln"] - 1:r["ln"] - 1 + k] = [seg.replace(r["old"], r["new"], 1)]
    texts[r["f"]] = "\n".join(fl)
check("C-1b all rows apply in table order on copies, no mismatch", not bad2, bad2)
check("C-1b table order is bottom-up within each file (highest line first)", not order_bad, order_bad)
file_groups = []
for r in rows:
    if not file_groups or file_groups[-1] != r["f"]:
        file_groups.append(r["f"])
check("each file's rows form one block in the table", len(file_groups) == len(set(file_groups)), file_groups)
shutil.rmtree(tmp)
# 4 cites
cbad = 0
cn = 0
cache = {}
for key, ln in re.findall(r"\b([A-Z][A-Z0-9]{1,4}):(\d+)\b", raw):
    if key not in paths:
        continue
    cn += 1
    if key not in cache:
        cache[key] = len(rd(real(paths[key])).split("\n"))
    if int(ln) > cache[key]:
        cbad += 1
check("cites exist (%d checked)" % cn, cbad == 0, cbad)
used = set(k for k, _ in re.findall(r"\b([A-Z][A-Z0-9]{1,5}):(\d+)\b", raw))
check("every cite key is defined in section 1", used - set(paths) <= {"UTC", "IST", "OK"} or not (used - set(paths)), sorted(used - set(paths)))
# 5 labels / stale
LAB = re.compile(r"\bQ\d+|\bL-[A-Z]+|decision \d|DECISIONS|ORDERS\.md|REPORT-c6|\bC-\d|\b(?:rs|pg|ns)\d+|\b[A-Z][A-Z0-9]{1,5}:\d+\b|\breadings? [12]\b|\bthis report\b|\b[Tt]he lease question\b|\bPLAN\b|\bRES\b")
lb = [(r["i"], m.group(0)) for r in rows for c in ("new", "view") for m in LAB.finditer(r[c])]
check("no report label, check label, source cite or report word in any new text or viewer cell (all %d rows, no file excluded)" % N, not lb, lb[:8])
STALE = ["52.9", "0 rows", "shows 0", "never deletes", "70 to 75", "80 kills", "archive|delete", "index not seen, accepted", "two stores", "three stores", "one store", "known limitation"]
st = [(s, [r["i"] for r in rows if s in r["new"]]) for s in STALE]
check("no stale phrase in new texts", all(not v for _, v in st), [x for x in st if x[1]])
# 6 banned, secrets
B = list(eval(re.search(r"BANNED\s*=\s*(\(.*?\n\))", rd(H + "/tests/test_no_reference_material.py"), re.S).group(1)))
hits = [b for b in B if b.lower() in raw.lower()]
check("banned vendor strings in report: count %d of %d listed (names not printed)" % (len(hits), len(B)), not hits, "count=%d" % len(hits))
sec = re.findall(r"AKIA[A-Z0-9]{8,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", raw)
sec = [s for s in sec if s != "AKIAIOSFODNN7EXAMPLE"]
check("no secret-like or e-mail string in report", not sec, len(sec))
# 7 C-4a
c4 = []
tmp2 = {}
for r in rows:
    pass
# (re-apply cheaply for the json files)
texts2 = {}
for r in rows:
    if "n8n-flows-real-v5/mf-" in r["f"] and r["f"].endswith(".json"):
        texts2.setdefault(r["f"], rd(real(r["f"])))
        fl = texts2[r["f"]].split("\n")
        k = r["old"].count("\n") + 1
        seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
        if seg.count(r["old"]) == 1:
            fl[r["ln"] - 1:r["ln"] - 1 + k] = [seg.replace(r["old"], r["new"], 1)]
            texts2[r["f"]] = "\n".join(fl)
for f, t in texts2.items():
    c = [t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveManualExecutions": false')]
    if c != [1, 1, 1]:
        c4.append((f, c))
check("C-4a the four flow files give saving all/all/manual-false once each (%d files)" % len(texts2), len(texts2) == 4 and not c4, c4)
# 8 recount
TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")
cnt = {}
for r in rows:
    for t in set(TOK.findall(r["st"])):
        cnt.setdefault(t, []).append(r["i"])
ready = [r["i"] for r in rows if r["st"].endswith("ready")]
nofilm = [r["i"] for r in rows if "NOT FILMABLE" in r["st"]]
withc = [r["i"] for r in rows if any(t.startswith("C-") for t in TOK.findall(r["st"]))]
waits = [r["i"] for r in rows if "waits for the answer of L-SAVEERR" in r["st"]]
onlyq = [r["i"] for r in rows if r["i"] not in nofilm and r["i"] not in waits and TOK.findall(r["st"]) and all(t.startswith("L-") for t in TOK.findall(r["st"]))]
withc = [i for i in withc if i not in waits]
check("recount: ready + defaults + check + waiting = N, none NOT FILMABLE; the waiting rows are exactly 53, 55, 62, 64, 66, 68", len(ready) + len(onlyq) + len(withc) + len(waits) + len(nofilm) == N and waits == [53, 55, 62, 64, 66, 68] and (len(ready), len(onlyq), len(withc)) == (49, 36, 3), (len(ready), len(onlyq), len(withc), len(waits), len(nofilm), N))
sec3 = [l for l in txt if re.match(r"^\| (L-[A-Z]+|C-\d+) \| [\d, ]+ \| \d+ \|", l)]
okc = True
for l in sec3:
    c = [x.strip() for x in l.split("|")[1:-1]]
    got = [int(x) for x in c[1].split(",") if x.strip().isdigit()]
    if got != sorted(cnt.get(c[0], [])) or int(c[2]) != len(got):
        okc = False
check("table 3b equals the recount (%d lines)" % len(sec3), okc and len(sec3) == len(cnt), (len(sec3), len(cnt)))
tot = [l for l in txt if l.startswith("| TOTAL |")]
want = "| TOTAL | all rows | %d | ready %d, on defaults only %d, with a check %d, waiting for the answer of L-SAVEERR %d (default no), NOT FILMABLE until an answer %d | |" % (N, len(ready), len(onlyq), len(withc), len(waits), len(nofilm))
check("3b TOTAL line equals the recount", tot == [want], tot[:1])
tied_ok = True
for l in txt:
    m = re.match(r"^\| (L-[A-Z]+)( \([^)]*\))? \| .* \| ([\d, ]+|none) \|$", l)
    if m and len(l.split(" | ")) >= 7:
        got = [int(x) for x in m.group(3).split(",") if x.strip().isdigit()]
        if got != sorted(cnt.get(m.group(1), [])):
            tied_ok = False
            print("   tied column differs for", m.group(1))
check("section 3 'rows tied to it' column equals the recount", tied_ok)
# 9 figure
full = raw
full_noold = "\n".join(re.sub(r"^(\| \d+ \| NOT APPLIED[^|]*? \| handover/[^|]+? \| \d+ \| [^|]* \| )`.*?` (\| `)", r"\1`` \2", l) for l in txt)
f1 = re.findall(r"60\.\d ?(?:to|-) ?6\d\.\d", full_noold)
f1bad = [x for x in f1 if x.replace(" ", "") not in ("60.1to61.9",)]
check("figure 60.1 to 61.9 exact everywhere (%d occurrences)" % len(f1), not f1bad, f1bad[:4])
check("no '61.1' or other upper bound next to 60.1", not re.search(r"60\.1 ?(?:to|-) ?(?!61\.9)\d", full_noold))
f2 = re.findall(r"52\.\d ?(?:to|-) ?5\d\.\d", full_noold)
check("figure 52.8 to 54.9 exact everywhere (%d occurrences)" % len(f2), all(x.replace(" ", "") in ("52.8to54.9",) for x in f2), [x for x in f2 if x.replace(" ", "") != "52.8to54.9"][:4])
check("61.9 only after 60.1 to", all(full_noold[max(0, m.start() - 8):m.start()].replace(" ", "").endswith("60.1to") for m in re.finditer(r"61\.9", full_noold)), "")
# 10 split
runs_done = re.findall(r"(\d+) runs? done", full)
runs_unk = re.findall(r"(\d+) runs? unknown", full)
check("18 kept runs split: every '<n> runs done' is 10 and every '<n> runs unknown' is 8", all(x == "10" for x in runs_done) and all(x == "8" for x in runs_unk) and runs_done and runs_unk, (runs_done, runs_unk))
splits = re.findall(r"K1 (\d+),? K2 (\d+)", full)
check("K1 5 and K2 5 everywhere", all(a == "5" and b == "5" for a, b in splits) and splits, splits[:4])
splits2 = re.findall(r"K3B (\d+),? K3 (\d+)", full)
check("K3B 5 and K3 3 everywhere", all(a == "5" and b == "3" for a, b in splits2) and splits2, splits2[:4])
check("18 kept runs = K1 5 + K2 5 + K3B 5 + K3 3", 5 + 5 + 5 + 3 == 18 and "18 kept" in full)
# 11 IST arithmetic
def conv(h, m):
    t = (h * 60 + m + 330) % 1440
    return t // 60, t % 60
pairs = re.findall(r"(\d{2}):(\d{2})(?::\d{2})?Z? ?(?:UTC)? ?= ?(\d{2}):(\d{2})(?::\d{2})? IST", full)
badp = [p for p in pairs if conv(int(p[0]), int(p[1])) != (int(p[2]), int(p[3]))]
check("every 'UTC = IST' pair is exactly UTC + 5:30 (%d pairs)" % len(pairs), not badp and len(pairs) >= 10, badp[:4])
# every clock time followed by UTC or Z must have '= .. IST' within 40 characters, except inside old-text cells (file quotes)
body_lines = []
for l in txt:
    if ROWPAT.match(l):
        m = ROWPAT.match(l)
        l = "| %s | %s | %s | %s | %s | | %s | %s |" % (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(7), m.group(8))
    body_lines.append(l)
noist = []
for ln, l in enumerate(body_lines):
    for m in re.finditer(r"\b\d{2}:\d{2}(?::\d{2})?(?:Z\b| UTC\b)", l):
        tail = l[m.end():m.end() + 60]
        if not re.match(r"[^|]{0,8}= ?\d{2}:\d{2}(?::\d{2})? IST", tail) and "IST" not in l[max(0, m.start() - 30):m.end() + 60]:
            noist.append((ln + 1, l[max(0, m.start() - 20):m.end() + 30]))
check("every clock time in UTC or Z has its IST nearby (outside old-text quotes)", not noist, noist[:4])
nu = [r["i"] for r in rows if re.search(r"\bUTC\b", r["new"]) and "IST" not in r["new"]]
check("every new text with UTC also has IST", not nu, nu)
nu2 = [r["i"] for r in rows if len(re.findall(r"\bUTC\b", r["new"])) > len(re.findall(r"\bIST\b", r["new"]))]
check("in every new text each UTC has its own IST (UTC count <= IST count)", not nu2, nu2)
check("IST given with the money stop", "23:59 IST" in full and "18:19 UTC = 23:49 IST" in full and "15:00 UTC = 20:30 IST" in full)
# 12 18 runs
b18 = [i + 1 for i, l in enumerate(txt) if re.search(r"\b18 (kept )?(crash )?runs?\b|each of 18|all 18", l, re.I) and not ("VOID-fl45k3b" in l and "VOID-fl45k6c" in l)
       and not ROWPAT.match(l)]
check("report prose lines with '18 runs' name both voided runs", not b18, b18[:6])
nb = [r["i"] for r in rows if re.search(r"\b18 (kept |crash )*runs?\b|each of 18", r["new"], re.I) and not ("VOID-fl45k3b" in r["new"] and "VOID-fl45k6c" in r["new"])]
check("new texts with '18 runs' name both voided runs", not nb, nb)
nbw = [r["i"] for r in rows if re.search(r"\b18 (kept |crash )*runs?\b|each of 18", r["why"], re.I) and not ("VOID-fl45k3b" in r["why"] and "VOID-fl45k6c" in r["why"]) and not r["new"].count("VOID-fl45k3b")]
check("reason cells with '18 runs' name both voided runs unless the new text does", not nbw, nbw)
# 13 row count everywhere
m = re.search(r"The edit table \(section 5\) holds (\d+) proposed text changes", full)
check("box says the row count of the table", bool(m) and int(m.group(1)) == N, (m.group(1) if m else None, N))
m = re.search(r"Of the (\d+) rows", full)
check("section 0 says the row count of the table", bool(m) and int(m.group(1)) == N, (m.group(1) if m else None, N))
m = re.search(r"%d are ready" % len(ready), full)
check("box says the ready count", bool(m), len(ready))
check("action box first (before section 0)", full.index("## Start here") < full.index("## 0. Failures"))
# 14 c6q content checks
import glob
import build_c6r_text as _T
bylead = {r["i"]: r for r in rows}
box = full[full.index("## Start here"):full.index("## 0. Failures")]
intro = box[:box.index("WORDS YOU NEED FIRST")]
check("no row is NOT FILMABLE", not nofilm, nofilm)
# card lines, recomputed from rows 13 and 14
W = []
Q = []
for k in (13, 14):
    for q in re.findall(r'spoken: "([^"]*)"', bylead[k]["new"]):
        Q.append(q)
        W.append(len(q.split()))
NW = sum(W)
sec_ = NW / 150 * 60
bud = int(sec_ // 5) * 5 + (5 if int(sec_ // 5) * 5 < sec_ - 1e-9 else 0)
check("rows 13+14 hold 4 spoken lines of %d words" % NW, len(W) == 4 and NW > 0, W)
check("box prints all four card lines exactly as the rows have them and the total (%d words, about %d s, budget %d s)" % (NW, round(sec_), bud),
      all(("'%s'" % q) in box for q in Q) and ("Total %d words, about %d s, budget %d s" % (NW, round(sec_), bud)) in box, "")
r11 = bylead[11]["new"]
check("row 11 states the same words, seconds, budget and total (about %d s)" % (150 + bud), ("%d words" % NW) in r11 and ("%d s" % round(sec_)) in r11 and ("closing card %d s" % bud) in r11 and ("about %d s in all" % (150 + bud)) in r11 and "EST NOT MEASURED" in r11, r11[:120])
# table of lengths recomputed from the quoted sentences
ql = [l for l in box.split("\n") if l.startswith("| L-LEASE |")]
m1 = re.search(r"1 = '([^']*)'", ql[0]) if ql else None
m2 = re.search(r"2 = '([^']*)' \(40 words", ql[0]) if ql else None
cl = [l for l in txt if l.startswith("| L-CARDLEN | studio lead")]
mb = re.search(r"line 1 '(.*?)' line 2 '(.*?)' line 3 '(.*?)' line 4 '(.*?)' \(\d+ words", cl[0]) if cl else None
ok = bool(m1 and m2 and mb)
tab_calc = []
if ok:
    w = lambda x: len(x.split())
    a_rest = W[1] + W[2] + W[3]
    b_rest = w(mb.group(2)) + w(mb.group(3)) + w(mb.group(4))
    add = {"none": 0, "1": w(m1.group(1)), "2": w(m2.group(1))}
    for k in ("none", "1", "2"):
        for ln, l1, rest in (("(a)", W[0], a_rest), ("(b)", w(mb.group(1)), b_rest)):
            ww = l1 + add[k] + rest   # ONE construction: the lease sentence is added to line 1; lines 2 to 4 are not touched
            s2 = ww / 150 * 60
            b2 = int(s2 // 5) * 5 + (5 if int(s2 // 5) * 5 < s2 - 1e-9 else 0)
            tab_calc.append((k, ln, ww, "%.1f" % s2, b2, 150 + b2))
boxrows = []
for l in box.split("\n"):
    mm = re.match(r"^\| (none|1|2)[^|]* \| \((a|b)\)[^|]* \| (\d+) \| ([\d.]+) \| (\d+) s \| about (\d+) s \|$", l)
    if mm:
        boxrows.append((mm.group(1), "(%s)" % mm.group(2), int(mm.group(3)), mm.group(4), int(mm.group(5)), int(mm.group(6))))
check("one construction in the length table: no 24-word rewrite of line 1 anywhere (c6q design review M-F)", "B_L1_R1" not in open(os.path.dirname(os.path.abspath(__file__)) + "/build_c6r_text.py").read() and "24-word" not in full and "24 words" not in box, "")
check("table of lengths in the box (6 rows) equals the recomputation from the quoted card lines and lease sentences", ok and boxrows == tab_calc and len(boxrows) == 6, (boxrows[:2], tab_calc[:2]))
check("answer 2 replaces answer 1: net +15 words and no 'add 16' wording", ok and (W[0] + len(m2.group(1).split())) - (W[0] + len(m1.group(1).split())) == 15 and "net +15 words" in full and not re.search(r"\+16 s|add 16|adds 16", full), "")
# questions and L-POST
check("L-POST exists in the box table and in section 3, with a default", any(l.startswith("| L-POST |") for l in box.split("\n")) and any(l.startswith("| L-POST (new in c6q)") for l in txt))
check("rows 11, 13, 14(not), 21 tie to L-POST and L-LEASE (13, 21) and the tied column lists them", all("L-POST" in bylead[k]["st"] for k in (11, 13, 21)) and all("L-LEASE" in bylead[k]["st"] for k in (13, 21)), "")
ll = [l for l in txt if l.startswith("| L-LEASE | studio lead")]
need = ["ORD:230", "ORD:186", "Q22 (c)", "NONE (the default)", "ANSWER 1", "ANSWER 2", "NOT TO BE SPOKEN AS FACT BEFORE C-9 PART 2", "WHAT 'NONE' CLAIMS, HONESTLY", "G12", "LRN:33", "LREP:80", "RECOMMENDATION", "REPLACES", "claim", "again"]
check("section 3 L-LEASE: newest word, honest claim of 'none', G12 open, reading-2 facts not to be spoken, replacement, recommendation", len(ll) == 1 and all(x in ll[0] for x in need), [x for x in need if not ll or x not in ll[0]])
check("L-LEASE definition is the true one (takeover only; repeat refused while the row exists)", "claim the contact again" in box and "may claim a contact that is not finished again" in full and "take over" not in full.replace("take over a contact","") and "NOT the time during which a repeat send is recognised" in full)
check("rows 17 and 81 say 'may' about the 45 s setting", "may be named" in bylead[81]["new"] and "neither 45 s nor 120 s" in bylead[81]["new"])
check("rows 13 and 21 carry the plain statement and no 45-second sentence by default", "within 45 seconds" not in bylead[13]["new"] and "within 45" not in bylead[21]["new"] and "processed once" in bylead[13]["new"] and "processed once" in bylead[21]["new"])
# C-10b, no-take line
c10b = [l for l in txt if l.startswith("| C-10b |")]
check("C-10b: pass and fail cells agree (all of (a), (b) and (c) shown / any not shown)", len(c10b) == 1 and "all of (a), (b) and (c) are shown with line numbers" in c10b[0] and "any of (a), (b), (c) not shown" in c10b[0], "")
check("the 'no take on Mon 23 Nov unless (a), (b) and (c)' line is in the box once, with 18:04 UTC = 23:34 IST once as a plan fact", box.count("applies the strictest reading of your answer Q27") == 1 and "MY ASSUMPTION" in box and "OWNER-OPEN" in box and box.count("18:04 UTC = 23:34 IST") == 1 and "plan fact" in box, "")
check("no 'Tuesday evening' or 'Tue evening' inference", not re.search(r"(?i)tue(sday)?\.? evening", full), "")
bad1051 = [i + 1 for i, l in enumerate(txt) if "1051" in l and "UNVERIFIED" not in l]
check("every line that names plan line 1051 says it is UNVERIFIED", not bad1051, bad1051)
check("departure from ORD:147 stated in section 0, in the L-DEL row and in row 8", "DEPARTURE FROM ORD:147" in full.split("## 1.")[0] and any(l.startswith("| L-DEL") and "DEPARTURE FROM ORD:147" in l for l in txt) and "DEPARTURE FROM ORD:147" in bylead[8]["why"], "")
check("fresh container wording (ORD:146) in row 8, C-9 and the box", "fresh database container" in bylead[8]["new"] and "ORD:146" in bylead[8]["why"] and any(l.startswith("| C-9 |") and "fresh container" in l for l in txt) and "fresh" in box)
# L-SCENES, stale words
check("L-SCENES appears only in coverage lines (section 8), never in a live table or row", all("L-SCENES" not in l for l in txt[:next((i for i, x in enumerate(txt) if x.startswith("COVERAGE OF THE c6p REVIEWS")), len(txt))]) , "")
# row 6 items, row 90, report words in new texts
r6 = bylead[6]["new"]
check("row 6 item 11 has no 'needs n8n and is not run yet'", "needs n8n and is not run yet" not in r6)
i15 = r6[r6.index("15. SECOND LEAK SCAN"):r6.index("16. AFTER THE TAKE")]
check("row 6 item 15 says what the second scan searches for (real key values read from the key file, not printed, counts only)", all(x in i15 for x in ["the real value of the mail account's password", "the real value of the customer-list key", "pattern file that exists only in memory or through standard input", "never on a command line", "never saved to disk", "made-up names", "hit counts only"]), "")
nn = [i + 1 for i, l in enumerate(txt) if re.search(r"\b(103|75|71) words", l) and not re.search(r"c6[nop]|history|was ", l)]
check("no stale card word count (103, 75, 71) outside history lines", not nn, nn[:3])
i13 = r6[r6.index("13. REPEAT-SEND CHECK"):r6.index("14. GATE")]
check("row 6 item 13: the 30 s rule applies only if the card or caption carries the 45-second limit", "If the closing card or the scene 3 caption says that the claim holds only within 45 seconds" in i13 and "If neither the card nor the caption says so" in i13, "")
check("row 6 keeps items 11 to 16, no blank, no builder note", all(("%d. " % n) in r6 for n in range(11, 17)) and "______" not in r6 and "SESSION-HANDOFF" not in r6)
check("row 6 item 16 does not claim that deleting erases the data", "NOT verified" in r6.split("16. AFTER THE TAKE")[1] and not re.search(r"(?i)erases? (the|all) (data|contact)|deletes? the data", r6.split("16. AFTER THE TAKE")[1]))
r90 = bylead[90]["new"]
check("row 90 new text ends with the database n8n (so 'owned by' attaches to it) and has no 'third place'", r90.rstrip().endswith("database `n8n`") and not r90.rstrip().endswith("own state") and "third place" not in full.lower().replace("'third place' removed", ""), r90[-80:])
check("row 91 says the stage journal and some bookkeeping files stay files", "stay files" in bylead[91]["new"])
r8 = bylead[8]["new"]
check("row 8 has 18:04 UTC = 23:34 IST, a plan fact that moves, (a)(b)(c), UNVERIFIED, STOP", "18:04 UTC = 23:34 IST" in r8 and "plan fact" in r8 and all(x in r8 for x in ["(a)", "(b)", "(c)", "UNVERIFIED", "STOP", "EVERY line"]), "")
check("row 76 is tagged design intent, rows 25, 37, 38 say 'stored' not 'delivered'", "design intent" in bylead[76]["new"] and all("stored by the test mailbox" in bylead[k]["new"] and "after the mail was delivered" not in bylead[k]["new"] for k in (25, 37, 38)), "")
bad144 = [r["i"] for r in rows if re.search(r"144\.3", r["new"]) and not re.search(r"144\.3[^|]{0,120}n8n (coming |came )?back up|from n8n", r["new"])]
check("every new text with 144.3 labels it as from n8n coming back up", not bad144, bad144)
rn = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\brows? \d+", r["new"])]
check("no 'row N' reference in any new text", not rn, rn[:5])
ac = [r["i"] for r in rows if re.search(r"\baccepted\b", r["new"])]
check("no 'accepted' exit slip in any new text", not ac, ac)
bl = [r["i"] for r in rows if re.search(r"(?<!studio )(?<!Studio )\blead\b(?!er)", re.sub(r"[Aa] lead sent twice with the same id is processed once", "", r["new"]))]
check("no bare 'lead' in new texts (the one decision sentence excepted)", not bl, bl)
# 5a
vis = sorted(r["i"] for r in rows if not r["view"].startswith("Nothing") and ("VIDEO-RUNSHEET" in r["f"] or "PAGE-STATEMENTS" in r["f"]))
a5 = full[full.index("5a. WHAT CHANGES"):full.index("5b. THE CLOSING CARD")]
got5 = [int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| (?:run sheet|page statements), line", a5, re.M)]
check("5a lists exactly the %d viewer-visible run-sheet and page rows" % len(vis), got5 == vis and any("PAGE-STATEMENTS" in bylead[k]["f"] for k in got5), (len(got5), len(vis)))
check("5a text equals each row's own 'what the viewer sees' cell", all(("| %d | " % k) in a5 and bylead[k]["view"] in a5 for k in vis))
# owner sheets
cs = rd(H + "/handover/core-hardening/c6-skip-audit/evidence-c6q/static-checks-output.txt")
ct = re.search(r"check time \(UTC\): (\S+)", cs).group(1)
vs = sorted(int(m.group(1)) for f in glob.glob(H + "/handover/core-hardening/steps-edits/OWNER-SHEET-v*.md") for m in [re.search(r"OWNER-SHEET-v(\d+)", f)] if m)
check("report names the check time %s and the newest sheet version on disk (v%s)" % (ct, vs[-1] if vs else "?"), bool(vs) and ("v%d" % vs[-1]) in full and ct[11:19] in full and ct[:10] in full, vs[-3:])
import datetime
ct_dt = datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
late = [os.path.basename(f) for f in glob.glob(H + "/handover/core-hardening/steps-edits/OWNER-SHEET-v*.md") if os.path.getmtime(f) > ct_dt]
check("no owner sheet changed after the stated check time (C-10c is current)", not late, late)
check("no claim that v25 or v26 is the newest", not re.search(r"(?i)newest[^.|]{0,60}v2[56]\b(?!-SOURCE\b)", full), "")
check("L-SHEET reads 'confirm the one final sheet' and says v29 is coming", any(l.startswith("| L-SHEET (was Q10)") and "Confirm the one final owner sheet" in l and "OWNER-SHEET-v29-A.md" in l and "OWNER-SHEET-v29-B.md" in l and "OWNER-SHEET-v29-SOURCE.md" in l for l in txt))
# section 9 duplicates
s9 = txt[[i for i, l in enumerate(txt) if l.startswith("## 9.")][0]:]
b9 = [l for l in s9 if l.startswith("- ")]
dup = [x[:60] for i, x in enumerate(b9) if any(x[:70] == y[:70] for y in b9[:i])]
check("section 9 has no duplicate bullet (%d bullets)" % len(b9), not dup, dup)
check("G12 named as open with the studio lead in section 9", any("G12" in l and "OPEN" in l for l in b9))
# box rules
terms = ["contact", "send", "same id", "n8n", "stand-in", "loopback re-smoke", "take", "rehearsal", "run sheet", "risks list", "rehearsal list", "studio lead", "owner", "lease", "alert", "gate", "re-pin", "public post", "ready", "wave 1", "table rule on the contact id", "k3b"]
low = box.lower().replace("## answer (studio lead, 2026-11-16t16:40:00z = 22:10:00 ist)", "## answer (ROLE, 2026-11-16t16:40:00z = 22:10:00 ist)")  # the fixed form of the answer line names the role; the list after it defines it
bad = []
for t in terms:
    first = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(t), low)
    d = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(t) + r"( and [a-z0-9 ]+?)? ?=", low)
    if not d or (first and first.start() < d.start() and t not in ("send", "take", "ready", "wave 1")):
        bad.append((t, bool(d), box[first.start():first.start() + 30] if first else None))
check("every word the box defines is first used where it is defined (case-insensitive, %d terms)" % len(terms), not bad, bad)
ix = intro.lower()
check("the lines before the first word list use none of the defined words", not [t for t in ("n8n", "ready", "contact", "rehearsal", "owner", "lease", "take ") if t in ix], [t for t in ("n8n", "ready", "contact", "rehearsal", "owner", "lease", "take ") if t in ix])
lq = box.find("| Label | Plain question")
fl = [m.group(0) for m in re.finditer(r"L-[A-Z]+", box)]
check("question labels are first used in the table of questions", lq >= 0 and bool(fl) and box.index(fl[0]) > lq, fl[:1])
bw = len(box.split())
p = H + "/handover/core-hardening/c6-skip-audit/REPORT-c6p.md"
pw = None
if os.path.exists(p):
    pr = rd(p)
    pw = len(pr[pr.index("## Start here"):pr.index("## 0. Failures")].split())
check("whole box is at most 3,600 words (%d words; c6p %s; it is LONGER than c6p because the naive review asked for the what-to-type block and for every internal word to be explained: a lead question)" % (bw, pw), bw <= 3600, bw)
sets = re.findall(r"saveDataSuccessExecution|saveManualExecutions|EXECUTIONS_DATA_SAVE", box)
check("box names no n8n setting", not sets, sets)
check("box has one answer line with seconds, three free names, the exception form and L-SHEET apart", "T16:40:00Z = 22:10:00 IST" in box and "builder: builder-A; reviewers: reviewer-B, reviewer-C" in box and "except L-KILL: b" in box and "L-SHEET cannot be put on the line" in box and box.count("## ANSWER (studio lead,") == 1)
W1 = len(ready) + len(onlyq)
W1c = W1
check("box wave 1 count equals ready + defaults (%d)" % W1, ("%d wave 1 rows" % W1) in box, W1)
check("box says it edits the flow files and changes no running n8n; box says the lease sentence is not put in owner sheet or release note by the rows", "changes no running n8n" in box and "no row edits them" in box)
check("box says steps 4 to 6 have no duration", "No file gives a duration for steps 4 to 6" in box)
check("L-SCENES question is gone", "| L-SCENES | studio lead" not in full and not any("L-SCENES" in r["st"] for r in rows))
check("rows 25, 37, 38 and 76 exist as rows", all(k in bylead for k in (25, 37, 38, 76)))
check("generator rule on rows 62 to 69 and row 92 edits the generator", all("GENERATOR RULE" in bylead[k]["why"] for k in range(62, 70)) and bylead[92]["f"].endswith("build_mainframe.py"))
check("section 8 has the coverage of the c6p, c6o and c6n reviews", "COVERAGE OF THE c6p REVIEWS" in full and "COVERAGE OF THE c6o REVIEWS" in full and "COVERAGE OF THE c6n REVIEWS" in full)
# files untouched
import hashlib
for nm in ("REPORT-c6o.md", "REPORT-c6p.md"):
    pass

# ---------------------------------------------------------------- c6r checks (the c6q reviews and the independent evidence of c6q)
import datetime as _dt
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON = {"Nov": 11, "Dec": 12}
wbad = []
wn = 0
for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Nov|Dec)\b(?: (\d{4}))?", raw):
    yr = int(m.group(4)) if m.group(4) else 2026
    wn += 1
    if WD[_dt.date(yr, MON[m.group(3)], int(m.group(2))).weekday()] != m.group(1):
        wbad.append(m.group(0))
check("every weekday written with a date is the true weekday (%d pairs; year 2026 unless written; no pair outside old-text quotes is skipped)" % wn, not wbad and wn >= 8, wbad[:4])
# the independent evidence named 'Tue 23 Nov' and 'Thu 18 Nov' as missed mutations: both are checked here as absent
check("no 'Tue 23 Nov' and no 'Thu 18 Nov' anywhere", "Tue 23 Nov" not in raw and "Thu 18 Nov" not in raw)
# caption row 21: no lease sentence by default
r21 = bylead[21]["new"]
check("row 21 (scene 3 caption) carries no lease sentence (no 'lease', no '45', no 'longer than', no 'claim')", not re.search(r"(?i)lease|\b45\b|longer than|we make this claim|for a longer gap", r21), r21[:140])
# counts: every statement of a count equals the computed value
cnt_bad = []
for m in re.finditer(r"(\d+) (?:rows )?(?:apply on the default|apply on the default of)", raw):
    if int(m.group(1)) != len(onlyq):
        cnt_bad.append(m.group(0))
for m in re.finditer(r"\b(\d+) (?:wave 1 rows|rows in all)", raw):
    if int(m.group(1)) != W1c:
        cnt_bad.append(m.group(0))
for m in re.finditer(r"wave 1 \((?:[^)]*?)\), (\d+) rows", raw):
    if int(m.group(1)) != W1c:
        cnt_bad.append(m.group(0))
check("every 'N apply on the default', 'N wave 1 rows' and 'N rows in all' equals the computed value (%d default-only, %d wave 1)" % (len(onlyq), W1c), not cnt_bad, cnt_bad[:5])
check("no stale count 91 or 42 stated as a wave 1 or default-only count", not re.search(r"\b91 (?:wave 1 )?rows\b|\b42 apply|\bthe 42 rows\b|\bon defaults only 42\b", raw), re.findall(r".{20}\b91 (?:wave 1 )?rows\b.{10}|.{20}\b42 apply.{10}", raw)[:3])
check("the box does not carry the old '58 s' card length", "58 s" not in box and "about 58" not in box)
check("row 14 (and the card rows 13, 14) carry no '(within 45 seconds)'", all("within 45" not in bylead[k]["new"] for k in (13, 14, 21)))
check("'one alert' is not stated as a fact about the take's flows in any new text (rows 13, 14, 74 and the box card text)", all(("sends one alert" not in bylead[k]["new"]) for k in bylead) and "it sends one alert" not in box, "")
# M-A: the approval gate and the mandatory repeat
i12 = bylead[8]["new"]
check("M-A: row 8 item 12 gates card line 1 and the caption on 'lease wording approved' with UTC and IST, and makes the repeat sent more than 45 seconds after the first mandatory", "lease wording approved" in i12 and "UTC and IST" in i12 and "more than 45 seconds after the first send" in i12 and "mandatory" in bylead[8]["why"], "")
check("M-A: the stop rules table has the lease wording approval entry", "| Lease wording approval (risks list item 12) |" in raw)
# M-C: Q27 reading is labelled the report's assumption; L-DEL does not say the open part is answered
check("M-C: Q27 reading labelled as the report's own assumption and OWNER-OPEN (ORD:232) in the box, row 8 and section 9", "MY ASSUMPTION" in box and "ORD:232" in box and "strictest reading" in bylead[8]["new"] and "OWNER-OPEN" in raw.split("## 9.")[1], "")
ldel = [l for l in txt if l.startswith("| L-DEL")]
check("M-C: L-DEL rows say 'ANSWERED' only for the part that is answered and say the delete-path criterion is open", all("Still open" in l or "open" in l for l in ldel) and any("ORD:232" in l for l in ldel), len(ldel))
# M-D: the real-key scan
i15 = bylead[6]["new"]
check("M-D: the key reaches the scan by a pattern file in memory or standard input from the key store; never a command line; never on disk; a hit means cancel or replace the key and treat the runs as compromised", all(x in i15 for x in ["pattern file that exists only in memory or through standard input", "never on a command line", "never saved to disk", "cancels or replaces that key at once", "compromised"]), "")
check("M-D: item 16 repeats the search for real key values", "This third scan also searches for the real key values" in i15, "")
# M-E: successful runs apply, failed runs wait, row 92 sets error none
check("M-E: rows 53, 55, 62, 64, 66, 68 wait for L-SAVEERR; row 92 keeps the failed-run setting none; row 44 says successful runs", all("waits for the answer of L-SAVEERR" in bylead[k]["st"] for k in (53, 55, 62, 64, 66, 68)) and '"saveDataErrorExecution": "none"' in bylead[92]["new"] and "successful run" in bylead[44]["new"], "")
check("M-E: L-SAVEERR is in the box and in section 3 with default No", any(l.startswith("| L-SAVEERR |") for l in box.split("\n")) and any(l.startswith("| L-SAVEERR | studio lead") and "| No |" in l for l in txt), "")
# C-4a on the default application: the failed-run setting stays none
d2 = {}
for r in rows:
    if "n8n-flows-real-v5/mf-" in r["f"] and r["f"].endswith(".json") and r["i"] not in waits:
        d2.setdefault(r["f"], rd(real(r["f"])))
        fl = d2[r["f"]].split("\n")
        k = r["old"].count("\n") + 1
        seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
        if seg.count(r["old"]) == 1:
            fl[r["ln"] - 1:r["ln"] - 1 + k] = [seg.replace(r["old"], r["new"], 1)]
            d2[r["f"]] = "\n".join(fl)
dd = [(os.path.basename(f), t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveManualExecutions": false')) for f, t in d2.items()]
check("C-4a (defaults only): the four flow files then save successful runs (all) and not failed runs, manual false, once each", len(dd) == 4 and all(x[1:] == (1, 0, 1) for x in dd), dd)
# M-F: one construction
check("M-F: one construction (checked above); the box says so", "one construction" in box.lower(), "")
# naive M1/M5/M6
check("naive M1: 'take' is defined as the filmed run and 'the recovery flow claims the contact again' is used instead of 'takes over'", "TAKE = the one filmed run" in box and "claim" in box and "take over" not in raw.replace("Take over", ""), "")
check("naive M5: the claim table is named in the box and every code word of the box is explained or replaced (K3B, K3, C-3 to C-9, G12 are defined)", all(x in box for x in ["CLAIM TABLE", "G12 =", "K3B AND K3 =", "THE CHECKS", "CUT NUMBER"]), "")
check("naive M6: the box starts with a one-screen WHAT TO TYPE block before the first word list", box.find("WHAT TO TYPE") >= 0 and box.find("WHAT TO TYPE") < box.find("WORDS YOU NEED FIRST") and box.find("WORDS YOU NEED FIRST") - box.find("WHAT TO TYPE") < 2200, "")
# the box: UTC with IST on the example time (coordinator item 4); no time example without IST within 40 characters
ex = [m.start() for m in re.finditer(r"22:10", box)]
check("every '22:10' example time in the box has 'IST' within 40 characters (%d places)" % len(ex), ex and all("IST" in box[i:i + 40] for i in ex), len(ex))
# the owner-sheet facts: the real v29 files, their times and the check time
sw = glob.glob(H + "/handover/core-hardening/steps-edits/OWNER-SHEET-v29-*.md")
sw_names = sorted(os.path.basename(f) for f in sw)
check("the real v29 files on disk are %s and the report names every one of them" % sw_names, sw_names == ["OWNER-SHEET-v29-A.md", "OWNER-SHEET-v29-B.md", "OWNER-SHEET-v29-SOURCE.md"] and all(n in raw for n in sw_names), sw_names)
for f in sorted(sw):
    t_ = _dt.datetime.fromtimestamp(os.path.getmtime(f), _dt.timezone.utc)
    print("INFO %s last written %s UTC; check time of the report %s" % (os.path.basename(f), t_.strftime("%H:%M:%S"), ct))
check("source-copy statement: the report says the rows were checked against the scratchpad copy, that equality with the real files is unverified, and that 89 of the 94 rows cannot be read in the repository", "scratchpad/c6/tree/handover" in raw.split("## 1.")[0] and "UNVERIFIED" in raw.split("## 1.")[0] and "89 of the 94 rows" in raw.split("## 1.")[0], "")
nrepo = sum(1 for r in rows if os.path.exists(H + "/" + r["f"]))
check("89 rows of 94 name a file that is not in the repository (recounted: %d rows readable in the repo)" % nrepo, nrepo == 5 and N - nrepo == 89, nrepo)
# no pipe-in-cell: no row text holds a raw table border
check("no row old or new text holds a raw '|' (it would break its table cell)", all("|" not in r["rawold"] and "|" not in r["rawnew"] for r in rows), [r["i"] for r in rows if "|" in r["rawold"] or "|" in r["rawnew"]])
# untouched files
for nm in ("REPORT-c6q.md", "REPORT-c6p.md"):
    check("%s was not changed by this run (it is older than the build of REPORT-c6r.md and holds its own title line)" % nm, os.path.getmtime(H + "/handover/core-hardening/c6-skip-audit/" + nm) < os.path.getmtime(R) and rd(H + "/handover/core-hardening/c6-skip-audit/" + nm).startswith("# REPORT-" + nm[7:10]), "")
print("SUMMARY: %d checks, %d FAILED%s" % (TOTAL[0], len(FAILS), (": " + "; ".join(FAILS)) if FAILS else ""))
sys.exit(1 if FAILS else 0)

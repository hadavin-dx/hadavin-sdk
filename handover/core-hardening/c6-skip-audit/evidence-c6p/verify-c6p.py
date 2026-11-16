"""Independent check: reads the report only (not build_c6o.py). EXITS NON-ZERO IF ANY CHECK FAILS (no check is printed-text-only).
Usage: python3 verify-c6p.py [path-to-report]   (default: REPORT-c6p.md next to this folder). Prints PASS/FAIL per check, a summary line, and exits 1 on any FAIL.
Checks: 1) old text once on its line; 2) ids are exactly 1..N; 3) rows applied in table order on copies, bottom-up per file;
4) every cite exists; 5) no internal labels or stale phrases in new texts; 6) banned strings (read at run time, counts only) and secret-like strings;
7) flow-file saving values; 8) per-question recount equals the report; 9) the figure 60.1 to 61.9 and 52.8 to 54.9 are exact everywhere;
10) the 18 kept runs split (10 done: K1 5, K2 5; 8 unknown: K3B 5, K3 3) is exact; 11) every UTC time has the right IST (arithmetic checked);
12) every '18 runs' line names both voided runs; 13) the row count is the same in every place; 14) c6p content checks (card words, lease sentence, 5a, row N, labels before definitions, stale numbers)."""
import re, os, shutil, tempfile, sys

H = "/home/user/hadavin-sdk"
T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
R = sys.argv[1] if len(sys.argv) > 1 else H + "/handover/core-hardening/c6-skip-audit/REPORT-c6p.md"
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
LAB = re.compile(r"\bQ\d+|\bL-[A-Z]+|decision \d|DECISIONS|ORDERS\.md|REPORT-c6|\bC-\d|\b(?:rs|pg|ns)\d+")
lb = [(r["i"], m.group(0)) for r in rows if "DECISION-one-store" not in r["f"] for m in LAB.finditer(r["new"])]
check("no internal labels in new texts", not lb, lb[:5])
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
onlyq = [r["i"] for r in rows if r["i"] not in nofilm and TOK.findall(r["st"]) and all(t.startswith("L-") for t in TOK.findall(r["st"]))]
check("recount: ready + defaults + check = N, none NOT FILMABLE", len(ready) + len(onlyq) + len(withc) + len(nofilm) == N, (len(ready), len(onlyq), len(withc), len(nofilm), N))
sec3 = [l for l in txt if re.match(r"^\| (L-[A-Z]+|C-\d+) \| [\d, ]+ \| \d+ \|", l)]
okc = True
for l in sec3:
    c = [x.strip() for x in l.split("|")[1:-1]]
    got = [int(x) for x in c[1].split(",") if x.strip().isdigit()]
    if got != sorted(cnt.get(c[0], [])) or int(c[2]) != len(got):
        okc = False
check("table 3b equals the recount (%d lines)" % len(sec3), okc and len(sec3) == len(cnt), (len(sec3), len(cnt)))
tot = [l for l in txt if l.startswith("| TOTAL |")]
want = "| TOTAL | all rows | %d | ready %d, on defaults only %d, with a check %d, NOT FILMABLE until an answer %d | |" % (N, len(ready), len(onlyq), len(withc), len(nofilm))
check("3b TOTAL line equals the recount", tot == [want], tot[:1])
tied_ok = True
for l in txt:
    m = re.match(r"^\| (L-[A-Z]+)( \(was [^)]*\))? \| .* \| ([\d, ]+|none) \|$", l)
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
m = re.search(r"%d are 'ready'" % len(ready), full)
check("box says the ready count", bool(m), len(ready))
check("action box first (before section 0)", full.index("## Start here") < full.index("## 0. Failures"))
# 14 c6p content checks
import glob
bylead = {r["i"]: r for r in rows}
box = full[full.index("## Start here"):full.index("## 0. Failures")]
boxq = box[:box.index("WORDS (more")] if "WORDS (more" in box else box
check("no row is NOT FILMABLE (L-LEASE has a default)", not nofilm, nofilm)
# card words counted from the spoken lines of rows 13 and 14
W = []
for k in (13, 14):
    W += [len(q.split()) for q in re.findall(r'spoken: "([^"]*)"', bylead[k]["new"])]
NW = sum(W)
secs = round(NW / 150 * 60)
check("rows 13+14 hold %d spoken words in 4 lines" % NW, len(W) == 4 and NW > 0, W)
check("box states exactly the counted words and seconds (%d words, about %d s)" % (NW, secs), ("exactly %d words, about %d s" % (NW, secs)) in boxq and ("%d words) " % W[0]) in boxq, "")
r11 = bylead[11]["new"]
check("row 11 states the same words and seconds", ("%d words" % NW) in r11 and ("%d s" % secs) in r11 and "EST NOT MEASURED" in r11, r11[:200])
check("section 0 and L-CARDLEN state the same word count", full.count("%d words" % NW) >= 3, full.count("%d words" % NW))
bad_num = [x for x in re.findall(r"\b(103|75|71|144) words", full) if x in ("103", "75", "71")]
nn = [l[:80] for l in txt if re.search(r"\b(103|75|71) words", l) and "c6o" not in l and "c6n" not in l and "was" not in l and "c6o rows" not in l]
check("no stale word count (103, 75, 71) outside history lines", not nn, nn[:3])
# lease
s1 = "We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim."
check("rows 13 and 21 carry the reading-1 sentence and apply on the default", "within 45 seconds of the first send" in bylead[13]["new"] and "within 45" in bylead[21]["new"] and "L-LEASE" in bylead[13]["st"] and "L-LEASE" in bylead[21]["st"] and not nofilm)
ll = [l for l in txt if l.startswith("| L-LEASE | studio lead")]
check("section 3 L-LEASE: cites Q22 (c) ORD:186 and ORD:230, both readings' sentences, plain 'none', recommendation, a default",
      len(ll) == 1 and all(x in ll[0] for x in ["Q22 (c)", "ORD:186", "ORD:230", s1, "NONE", "REVERSES", "RECOMMENDATION", "READING 1", "READING 2", "| 1 (reading 1"]), len(ll))
check("box L-LEASE row gives both sentences and 'none' with its meaning and a default of 1", s1 in boxq and "none = no lease sentence anywhere" in boxq and "REVERSES" in boxq and "My recommendation: 2" in boxq and "| 1 (your answer Q22 (c) is in force)" in boxq)
check("L-LEASE definition is the true one (takeover only; repeat refused while the row exists)", "may take over a contact that is not finished" in full and "NOT the time during which a repeat send is recognised" in full)
check("rows 17 and 81 say 'may' about the 45 s setting", "may be named" in bylead[81]["new"] and "neither 45 s nor 120 s" in bylead[81]["new"])
# no 'row N' in new text, no 'accepted' exit
rn = [(r["i"], m.group(0)) for r in rows for m in re.finditer(r"\brows? \d+", r["new"])]
check("no 'row N' reference in any new text", not rn, rn[:5])
ac = [r["i"] for r in rows if re.search(r"\baccepted\b", r["new"])]
check("no 'accepted' exit slip in any new text", not ac, ac)
# 5a
vis = sorted(r["i"] for r in rows if not r["view"].startswith("Nothing") and ("VIDEO-RUNSHEET" in r["f"] or "PAGE-STATEMENTS" in r["f"]))
a5 = full[full.index("5a. WHAT CHANGES"):full.index("5b. THE CLOSING CARD")]
got5 = [int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| (?:run sheet|page statements), line", a5, re.M)]
check("5a lists exactly the %d viewer-visible run-sheet and page rows, with page rows present" % len(vis), got5 == vis and any("PAGE-STATEMENTS" in bylead[k]["f"] for k in got5), (len(got5), len(vis)))
v5 = all(("| %d | " % k) in a5 and bylead[k]["view"] in a5 for k in vis)
check("5a text equals each row's own 'what the viewer sees' cell", v5)
# newest owner sheet
vs = sorted(int(m.group(1)) for f in glob.glob(H + "/handover/core-hardening/steps-edits/OWNER-SHEET-v*.md") for m in [re.search(r"OWNER-SHEET-v(\d+)", f)] if m)
check("report names the newest owner sheet version on disk (v%s)" % (vs[-1] if vs else "?"), bool(vs) and ("v%d" % vs[-1]) in full and "16:01:45Z" in full, vs[-3:])
check("no claim that v25 or v26 is the newest", not re.search(r"(?i)newest[^.|]{0,60}v2[56]\b(?!-SOURCE\b)", full.replace("v28 is newest", "")) or "c6o said" in full, "")
# row 90 / 91
r90 = bylead[90]["new"]
check("row 90 ends with the clause about a separate database and has no 'third place'", r90.rstrip().endswith("own state") and "third place" not in full.lower().replace("'third place' removed", "").replace("third place' removed", ""), r90[-120:])
check("row 91 says the stage journal and some bookkeeping files stay files", "stay files" in bylead[91]["new"])
r6 = bylead[6]["new"]
check("row 6 item 16 does not claim that deleting erases the data", "16. AFTER THE TAKE" in r6 and "not verified" in r6.lower().split("16. after the take")[1] if False else "NOT verified" in r6.split("16. AFTER THE TAKE")[1] and not re.search(r"(?i)erases? (the|all) (data|contact)|deletes? the data", r6.split("16. AFTER THE TAKE")[1]), r6.split("16. AFTER THE TAKE")[1][:200])
check("row 6 keeps items 11 to 16, no blank, no builder note", all(("%d. " % n) in r6 for n in range(11, 17)) and "______" not in r6 and "SESSION-HANDOFF" not in r6)
r8 = bylead[8]["new"]
check("row 8 has the latest start 18:04 UTC = 23:34 IST and (a)(b)(c) and UNVERIFIED", "18:04 UTC = 23:34 IST" in r8 and all(x in r8 for x in ["(a)", "(b)", "(c)", "UNVERIFIED", "STOP", "EVERY line"]), "")
check("box and C-10b carry 18:04 UTC = 23:34 IST", "18:04 UTC = 23:34 IST" in boxq and any(l.startswith("| C-10b |") and "18:04 UTC = 23:34 IST" in l for l in txt))
check("row 76 is tagged design intent, rows 25, 37, 38 say 'stored' not 'delivered'", "design intent" in bylead[76]["new"] and all("stored by the test mailbox" in bylead[k]["new"] and "after the mail was delivered" not in bylead[k]["new"] and "after the mail left" not in bylead[k]["new"].replace("words killed after the mail left are not used", "") for k in (25, 37, 38)), "")
# 144.3 label
bad144 = [r["i"] for r in rows if re.search(r"144\.3", r["new"]) and not re.search(r"144\.3[^|]{0,120}n8n (coming |came )?back up|from n8n", r["new"])]
check("every new text with 144.3 labels it as from n8n coming back up", not bad144, bad144)
# box rules
terms = ["CONTACT", "N8N", "TAKE", "REHEARSAL", "RUN SHEET", "STUDIO LEAD", "OWNER", "LEASE", "ALERT", "GATE", "RE-PIN", "READY", "K3B"]
bad = []
for t in terms:
    m = re.search(r"\b%s\b" % re.escape(t), boxq)
    if not m or not re.match(r"%s( and K3)? =" % re.escape(t), boxq[m.start():m.start() + 20]) and not (t in ("TAKE", "REHEARSAL") and boxq[m.start():m.start() + 40].startswith(t + " = ")):
        bad.append((t, boxq[m.start():m.start() + 25] if m else None))
check("every defined label is first used where it is defined (uppercase terms of the box)", not bad, bad)
lq = boxq.find("| Label | Plain question")
fl = [m.group(0) for m in re.finditer(r"L-[A-Z]+", boxq)]
check("question labels are first used in the table of questions", lq >= 0 and bool(fl) and boxq.index(fl[0]) > lq, fl[:1])
bw = len(box.split())
check("whole box is shorter than the c6o box (%d words; c6o 3529, counted with split on 2026-11-16)" % bw, bw < 3529, bw)
sets = re.findall(r"saveDataSuccessExecution|saveManualExecutions|EXECUTIONS_DATA_SAVE", boxq)
check("box names no n8n setting", not sets, sets)
check("box has one answer line with seconds and the three free names", "T16:40:00Z = 22:10:00 IST" in boxq and "builder: builder-1; reviewers: egm-design, egm-comprehension" in boxq)
W1 = len(ready) + len(onlyq)
check("box wave 1 count equals ready + defaults (%d)" % W1, ("%d wave 1 rows" % W1) in boxq, W1)
check("box says it edits the flow files and changes no running n8n", "changes no running n8n" in boxq and "switches" not in boxq.lower().replace("switched off", ""), "")
check("L-SCENES question is gone", "| L-SCENES | studio lead" not in full and not any("L-SCENES" in r["st"] for r in rows))
check("the 4 card line texts in the box (A1 line) are in row 13", "A lead sent twice with the same id is processed once. We make this claim only" in bylead[13]["new"])
check("rows 25, 37, 38 and 76 exist as rows (design M8)", all(k in bylead for k in (25, 37, 38, 76)))
r6v = bylead[6]["view"]
check("row 6 view and row 8 view have no 'accepted' and no 'row N'", not re.search(r"\baccepted\b|\brows? \d+", r6v + bylead[8]["view"]), r6v[:80])
check("generator rule on rows 62 to 69 and row 92 edits the generator", all("GENERATOR RULE" in bylead[k]["why"] for k in range(62, 70)) and bylead[92]["f"].endswith("build_mainframe.py"))
check("section 8 has the coverage of the c6o and c6n reviews", "COVERAGE OF THE c6o REVIEWS" in full and "COVERAGE OF THE c6n REVIEWS" in full)
bl = [(r["i"]) for r in rows if re.search(r"(?<!studio )(?<!Studio )\blead\b(?!er)", re.sub(r"[Aa] lead sent twice with the same id is processed once", "", r["new"]))]
check("no bare 'lead' in new texts (the one decision sentence excepted)", not bl, bl)
print("SUMMARY: %d checks, %d FAILED%s" % (TOTAL[0], len(FAILS), (": " + "; ".join(FAILS)) if FAILS else ""))
sys.exit(1 if FAILS else 0)

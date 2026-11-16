"""Independent check: reads the report only (not build_c6o.py). EXITS NON-ZERO IF ANY CHECK FAILS (no check is printed-text-only).
Usage: python3 -B -I verify-c6t.py [path-to-report]   (default: REPORT-c6t.md next to this folder). Prints PASS/FAIL per check, a summary line, and exits 1 on any FAIL.
Checks: 1) old text once on its line; 2) ids are exactly 1..N; 3) rows applied in table order on copies, bottom-up per file;
4) every cite exists; 5) no internal labels or stale phrases in new texts; 6) banned strings (read at run time, counts only) and secret-like strings;
7) flow-file saving values; 8) per-question recount equals the report; 9) the figure 60.1 to 61.9 and 52.8 to 54.9 are exact everywhere;
10) the 18 kept runs split (10 done: K1 5, K2 5; 8 unknown: K3B 5, K3 3) is exact; 11) every UTC time has the right IST (arithmetic checked);
12) every '18 runs' line names both voided runs; 13) the row count is the same in every place; 14) c6q content checks (card words and the length table recomputed from the quoted lines, L-POST, lease rows, 5a, report labels in new texts, labels defined before use, owner sheets, C-10b, section 9)."""
import re, os, shutil, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

H = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
STEPS = os.environ.get("C6T_STEPS", H + "/handover/core-hardening/steps-edits")  # the negative controls point this at a changed copy
T = os.environ.get("C6T_TREE") or sys.exit("set C6T_TREE to the folder of the copied demo tree (the audited demo files; an input of this check)")
R = sys.argv[1] if len(sys.argv) > 1 else H + "/handover/core-hardening/c6-skip-audit/REPORT-c6t.md"
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
sec = re.findall(r"AKIA[A-Z0-9]{8,}|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9_]{10,}|xox[abprs]-[A-Za-z0-9-]{10,}|pat-[a-z0-9]{2,5}-[0-9a-f-]{20,}|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", raw)
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
# c6s F1: the defaults (rows that wait for L-SAVEERR are NOT applied): success all, error none, manual false
texts3 = {}
for r in rows:
    if "n8n-flows-real-v5/mf-" in r["f"] and r["f"].endswith(".json") and "waits for the answer of L-SAVEERR" not in r["st"]:
        texts3.setdefault(r["f"], rd(real(r["f"])))
        fl = texts3[r["f"]].split("\n")
        k = r["old"].count("\n") + 1
        seg = "\n".join(fl[r["ln"] - 1:r["ln"] - 1 + k])
        if seg.count(r["old"]) == 1:
            fl[r["ln"] - 1:r["ln"] - 1 + k] = [seg.replace(r["old"], r["new"], 1)]
            texts3[r["f"]] = "\n".join(fl)
c4d = []
for f, t in texts3.items():
    c = [t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveDataErrorExecution": "none"'), t.count('"saveManualExecutions": false')]
    if c != [1, 0, 1, 1]:
        c4d.append((f, c))
check("F1 C-4a on the DEFAULT rows the four flow files give success all, failed none, manual false, once each (%d files)" % len(texts3), len(texts3) == 4 and not c4d, c4d)
c4 = []
for f, t in texts2.items():
    c = [t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveManualExecutions": false')]
    if c != [1, 1, 1]:
        c4.append((f, c))
check("F1 C-4a after L-SAVEERR yes (all rows applied) the four flow files give all/all/manual-false once each (%d files)" % len(texts2), len(texts2) == 4 and not c4, c4)
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
# 14.. content checks of c6q, c6r and c6s live in verify_c6t_part2.py; each top-level statement runs on its own, a crash is a FAIL
import ast
_p2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_c6t_part2.py")
_src2 = open(_p2, encoding="utf-8").read()
for _node in ast.parse(_src2).body:
    try:
        exec(compile(ast.Module([_node], []), _p2, "exec"), globals())
    except Exception as _e:
        check("part 2 statement at line %d could not run on this report (%s: %s)" % (_node.lineno, type(_e).__name__, str(_e)[:80]), False)
print("SUMMARY: %d checks, %d FAILED%s" % (TOTAL[0], len(FAILS), (": " + "; ".join(FAILS)) if FAILS else ""))
sys.exit(1 if FAILS else 0)

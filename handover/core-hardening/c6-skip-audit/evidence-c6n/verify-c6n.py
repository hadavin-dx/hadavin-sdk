"""Independent check: reads REPORT-c6n.md only (not build_c6m.py). 1) old text occurs once on its line; 2) apply all rows in table order
to COPIES in a temp dir; 3) every cite KEY:line exists; 4) scan NEW texts for internal labels, stale phrases, banned strings."""
import re, os, shutil, tempfile, sys
H = "/home/user/hadavin-sdk"
T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
R = H + "/handover/core-hardening/c6-skip-audit/REPORT-c6n.md"
txt = open(R, encoding="utf-8").read().split("\n")
def real(p):
    return H + "/" + p if p.startswith("handover/core-hardening/") else T + "/" + p[len("handover/"):]
paths = {}
for l in txt:
    m = re.match(r"^\| ([A-Z0-9]+) \| (handover/[^|]+?) \| [^|]+ \|$", l)
    if m: paths[m.group(1)] = m.group(2)
print("short names", len(paths))
rd = lambda p: open(p, encoding="utf-8", errors="replace").read()
rows = []
for l in txt:
    m = re.match(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$", l)
    if m:
        i, st, f, ln, view, old, new, why, was = m.groups()
        rows.append(dict(i=int(i), st=st, f=f, ln=int(ln), old=old.replace("<br>", "\n"), new=new.replace("<br>", "\n"), why=why))
print("rows parsed", len(rows)); bad = 0
for r in rows:
    fl = rd(real(r["f"])).split("\n"); k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"]-1:r["ln"]-1+k])
    ok = seg.count(r["old"]) == 1
    if not ok: bad += 1; print("C-1 MISMATCH row", r["i"], r["f"], r["ln"])
print("C-1 old text once on its line: %d of %d ok, %d bad" % (len(rows)-bad, len(rows), bad))
ids = [r["i"] for r in rows]; print("ids consecutive from 1:", ids == list(range(1, len(rows)+1)))
# C-1b apply in table order on copies
tmp = tempfile.mkdtemp(); texts = {}; bad2 = 0
for r in rows:
    if r["f"] not in texts: texts[r["f"]] = rd(real(r["f"]))
    t = texts[r["f"]]; fl = t.split("\n")
    # line numbers are pre-edit; table is bottom-up per file so line r["ln"] is still valid
    k = r["old"].count("\n") + 1
    seg = "\n".join(fl[r["ln"]-1:r["ln"]-1+k])
    if seg.count(r["old"]) != 1: bad2 += 1; print("C-1b MISMATCH row", r["i"]); continue
    fl[r["ln"]-1:r["ln"]-1+k] = [seg.replace(r["old"], r["new"])]
    texts[r["f"]] = "\n".join(fl)
for f, t in texts.items():
    p = os.path.join(tmp, f.replace("/", "__")); open(p, "w", encoding="utf-8").write(t)
print("C-1b applied bottom-up in table order: %d rows, %d mismatches, %d files written to %s" % (len(rows), bad2, len(texts), tmp))
# cites
cbad = 0; cn = 0; cache = {}
for key, ln in re.findall(r"\b([A-Z][A-Z0-9]{1,4}):(\d+)\b", "\n".join(txt)):
    if key not in paths: continue
    cn += 1
    if key not in cache: cache[key] = len(rd(real(paths[key])).split("\n"))
    if int(ln) > cache[key]: cbad += 1; print("CITE beyond end of file", key, ln)
print("cites checked %d, beyond end of file %d" % (cn, cbad))
# labels in NEW text (not for DECISION-one-store, which is an internal file)
LAB = re.compile(r"\bQ\d+|\bL-[A-Z]+|decision \d|DECISIONS|ORDERS\.md|REPORT-c6|\bC-\d|\b(?:rs|pg|ns)\d+")
lb = 0
for r in rows:
    if "DECISION-one-store" in r["f"]: continue
    for m in LAB.finditer(r["new"]): lb += 1; print("LABEL in new text row", r["i"], repr(m.group(0)), "|", r["new"][max(0, m.start()-30):m.end()+30].replace("\n", "/"))
print("internal labels in new texts: %d" % lb)
STALE = ["52.9", "0 rows", "shows 0", "never deletes", "70 to 75", "80 kills", "archive|delete", "studio lead's made", "studio lead table"]
for s in STALE:
    hits = [r["i"] for r in rows if s in r["new"]]
    print("stale phrase %r in new texts of rows: %s" % (s, hits or "none"))
import re as _re
B = list(eval(_re.search(r"BANNED\s*=\s*(\(.*?\n\))", open("/home/user/hadavin-sdk/tests/test_no_reference_material.py").read(), _re.S).group(1)))
full = "\n".join(txt)
print("banned strings in report:", [b for b in B if b.lower() in full.lower()] or "none")
sec = re.findall(r"AKIA[A-Z0-9]{8,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", full)
print("secret-like or e-mail strings in report:", sec or "none")
# C-4a: saving settings on the applied copies of the four real-v5 flow files
for f, t in texts.items():
    if "n8n-flows-real-v5/mf-" in f and f.endswith(".json"):
        c = [t.count('"saveDataSuccessExecution": "all"'), t.count('"saveDataErrorExecution": "all"'), t.count('"saveManualExecutions": false')]
        print("C-4a", f.split("/")[-1], c, "PASS" if c == [1, 1, 1] else "FAIL")
# per-question recount from the markdown table
full_rows = [r for r in rows]
tok = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")
cnt = {}
for r in full_rows:
    for t in set(tok.findall(r["st"])): cnt.setdefault(t, []).append(r["i"])
ready = [r["i"] for r in full_rows if not tok.findall(r["st"])]
print("recount ready", len(ready), "of", len(full_rows))
sec3 = [l for l in txt if re.match(r"^\| (L-[A-Z]+|C-\d+) \| [\d, ]+ \| \d+ \|", l)]
okc = True
for l in sec3:
    c = [x.strip() for x in l.split("|")[1:-1]]
    got = [int(x) for x in c[1].split(",") if x.strip().isdigit()]
    if got != sorted(cnt.get(c[0], [])) or int(c[2]) != len(got): okc = False; print("COUNT MISMATCH", c[0])
print("table 3b recount: %d question lines checked, all equal: %s" % (len(sec3), okc and len(sec3) == len(cnt)))
tot = [l for l in txt if l.startswith("| TOTAL |")]
print("TOTAL line:", tot[0] if tot else "MISSING")
# '18' next to run must name both voided runs (same paragraph/line)
b18 = [i+1 for i, l in enumerate(txt) if re.search(r"\b18 (kept )?(crash )?runs?\b|each of 18|all 18", l) and not ("VOID-fl45k3b" in l and "VOID-fl45k6c" in l)]
print("lines with 18 runs and not naming both voided runs (report text):", b18 or "none")
nb = [r["i"] for r in rows if re.search(r"\b18 (kept |crash )*runs?\b|each of 18", r["new"]) and not ("VOID-fl45k3b" in r["new"] and "VOID-fl45k6c" in r["new"])]
print("rows whose new text has 18 without naming both voided runs:", nb or "none")
# figure hold: rows not tied to L-PAGE must not carry 60.1 or 61.9 in new text
fig = [(r["i"], r["st"]) for r in rows if "PAGE-STATEMENTS" in r["f"] and re.search(r"60\.1|61\.9", r["new"]) and "L-PAGE" not in r["st"] and "L-APPROX" not in r["st"]]
print("rows with the 60.1 to 61.9 figure and no L-PAGE hold:", fig or "none")
# word scan in prose (outside quotes of old text): 'the lead' alone and 'claim'
body = "\n".join(l for l in txt if not l.startswith("| ") or "Plain meaning" in l)
print("prose 'the lead' hits:", len(re.findall(r"\bthe lead\b", body)), "| 'claim' hits outside claim table/claim row/claimed:", len(re.findall(r"\bclaims?\b(?! table| row)", body)))
# every short name in a cite exists in section 1; every ALLCAPS label is in the glossary
used = set(k for k, _ in re.findall(r"\b([A-Z][A-Z0-9]{1,5}):(\d+)\b", full))
print("cite keys used but not defined:", sorted(used - set(paths)) or "none")
gl = "\n".join(txt[txt.index("## 4. Plain-word glossary (every short name and label used in this report; term, meaning, where it comes from)"):])
labs = set(re.findall(r"\b(?:L-[A-Z]+|C-\d+[a-d]?)\b", full))
miss = [x for x in sorted(labs) if x not in gl and not (x.startswith("C-") and "C-1 to C-11" in gl) and not (x.startswith("L-") and "L-CARD, L-CARDCUT" in gl) and x != "L-ROUND"]
print("labels missing from glossary:", miss or "none")
shutil.rmtree(tmp)

# extra c6m checks
print("--- c6m extra checks ---")
allnew = "\n".join(r["new"] + "\n" + r["why"] for r in rows)
print("wrong-word slips 'studio lead' + made-up/table/name in new text or reason:", re.findall(r"studio lead(?:'s)? (?:made-up|table|name)", allnew) or "none")
print("pipe-grep text 'archive|delete' anywhere in the report:", full.count("archive|delete"))
print("'new in this report' near contact deletion:", len(re.findall(r"new in this report", full)))
print("rows saying the take script archives as fact:", [r["i"] for r in rows if re.search(r"\btake (script )?archives\b|archives at the end", r["new"])] or "none")
for q in ("Q19", "Q22", "Q23", "Q25", "Q27", "Q21.1"):
    print("report cites", q, ":", full.count(q))
print("action box first (before section 0):", full.index("## Start here") < full.index("## 0. Failures"))
print("every row has a viewer column text:", all(len(re.match(r"^\| %d \|.*" % r["i"], [l for l in txt if l.startswith("| %d | NOT APPLIED" % r["i"])][0]).group(0)) > 0 for r in rows))
print("IST given with the money stop:", "23:59 IST" in full, "| take target:", "Wed 18 Nov" in full)

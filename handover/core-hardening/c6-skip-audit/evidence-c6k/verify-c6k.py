"""Independent check: reads REPORT-c6k.md only (not build_c6k.py). 1) old text occurs once on its line; 2) apply all rows in table order
to COPIES in a temp dir; 3) every cite KEY:line exists; 4) scan NEW texts for internal labels, stale phrases, banned strings."""
import re, os, shutil, tempfile, sys
H = "/home/user/hadavin-sdk"
T = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
R = H + "/handover/core-hardening/c6-skip-audit/REPORT-c6k.md"
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
    m = re.match(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$", l)
    if m:
        i, st, f, ln, old, new, why, was = m.groups()
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
STALE = ["52.9", "0 rows", "shows 0", "never deletes", "70 to 75", "80 kills"]
for s in STALE:
    hits = [r["i"] for r in rows if s in r["new"]]
    print("stale phrase %r in new texts of rows: %s" % (s, hits or "none"))
import re as _re
B = list(eval(_re.search(r"BANNED\s*=\s*(\(.*?\n\))", open("/home/user/hadavin-sdk/tests/test_no_reference_material.py").read(), _re.S).group(1)))
full = "\n".join(txt)
print("banned strings in report:", [b for b in B if b.lower() in full.lower()] or "none")
sec = re.findall(r"AKIA[A-Z0-9]{8,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", full)
print("secret-like or e-mail strings in report:", sec or "none")
shutil.rmtree(tmp)

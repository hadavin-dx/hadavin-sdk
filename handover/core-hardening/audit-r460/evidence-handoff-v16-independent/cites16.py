"""Seeded sample of 60 file:line cites of CORE-PR-HANDOFF-v16.md checked against src/ (and tests/). Heuristic, records only.
HIT = file resolves, range inside file, and an identifier named in backticks just before the cite occurs inside the cited range (+-1 line).
MOVED = file resolves and range exists but the identifier is only elsewhere in the file. MISSING = file not found, range outside file, or identifier nowhere.
RANGE-ONLY = no identifier near the cite, so only file and range were checked."""
import re, random, sys
from pathlib import Path
doc = Path(sys.argv[1]).read_text()
repo = Path(sys.argv[2])
srcroot = repo / "src" / "hadavin_sdk"
pat = re.compile(r"(?<![\w/.-])((?:[A-Za-z_][\w.-]*/)*[A-Za-z_][\w-]*\.(?:py|sql|toml|yml|yaml)):(\d+)(?:-(\d+))?((?:,\s*:\d+(?:-\d+)?)*)")
cites = []
for mo in pat.finditer(doc):
    path, a, b, more = mo.group(1), int(mo.group(2)), mo.group(3), mo.group(4)
    ranges = [(a, int(b) if b else a)]
    for mm in re.finditer(r":(\d+)(?:-(\d+))?", more or ""):
        ranges.append((int(mm.group(1)), int(mm.group(2) or mm.group(1))))
    ctx = doc[max(0, mo.start() - 170):mo.start()]
    for r in ranges:
        cites.append((path, r, ctx, doc.count("\n", 0, mo.start()) + 1))
uniq = {}
for c in cites:
    uniq.setdefault((c[0], c[1]), c)
allc = sorted(uniq.values(), key=lambda c: (c[3], c[0], c[1]))
print(f"INFO cites found: {len(cites)} total, {len(allc)} distinct (path, range)")
rnd = random.Random(16016)
sample = rnd.sample(allc, 60) if len(allc) >= 60 else allc
def resolve(path):
    cand = [repo / path, srcroot / path, repo / "src" / path]
    for c in cand:
        if c.is_file():
            return c, ""
    if "/" not in path:
        hits = list(srcroot.rglob(path)) + [h for h in (repo / "tests").rglob(path)] + list((repo / ".github").rglob(path)) + [h for h in repo.glob("*/" + path)] + [h for h in (repo / "demos").rglob(path)]
        if len(hits) == 1:
            return hits[0], ""
        if len(hits) > 1:
            return hits[0], f"ambiguous({len(hits)})"
    return None, ""
stop = {"self", "None", "True", "False", "src", "hadavin_sdk", "tests"}
out = {"HIT": 0, "MOVED": 0, "MISSING": 0, "RANGE-ONLY": 0}
def snip(f, a, b):
    L = f.read_text(errors="replace").split("\n")
    return " | ".join(x.strip()[:90] for x in L[a - 1:min(b, a + 1)])
for path, (a, b), ctx, line in sample:
    f, note = resolve(path)
    if f is None:
        out["MISSING"] += 1; print(f"MISSING  doc line {line}  {path}:{a}-{b}  (file not found)"); continue
    L = f.read_text(errors="replace").split("\n")
    if a > len(L) or b > len(L):
        out["MISSING"] += 1; print(f"MISSING  doc line {line}  {path}:{a}-{b}  (file has {len(L)} lines)"); continue
    toks = [t for t in re.findall(r"`([^`]{3,60})`", ctx)]
    ids = []
    for t in toks[::-1]:
        for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", t):
            if w not in stop and not w.endswith(("py", "sql")) and w not in ids and ("_" in w or re.search(r"[A-Z]", w)):
                ids.append(w)
    ids = ids[:6]
    if not ids:
        out["RANGE-ONLY"] += 1; print(f"RANGE-ONLY doc line {line}  {path}:{a}-{b} {note}  CODE: {snip(f,a,b)}  CLAIM: ...{ctx[-110:]!r}"); continue
    seg = "\n".join(L[max(0, a - 2):min(len(L), b + 1)])
    inr = [i for i in ids if i in seg]
    if inr:
        out["HIT"] += 1; print(f"HIT      doc line {line}  {path}:{a}-{b} {note} (found {inr[0]})")
    else:
        where = [(i, n + 1) for i in ids for n, l in enumerate(L) if i in l]
        if where:
            out["MOVED"] += 1; print(f"MOVED    doc line {line}  {path}:{a}-{b} {note} ({where[0][0]} is at line {where[0][1]})  CODE: {snip(f,a,b)}  CLAIM: ...{ctx[-110:]!r}")
        else:
            out["MISSING"] += 1; print(f"MISSING  doc line {line}  {path}:{a}-{b} {note} (none of {ids[:3]} in file)  CODE: {snip(f,a,b)}  CLAIM: ...{ctx[-110:]!r}")
print("INFO sample", len(sample), out)


"""Own citation re-check (v15 independent). python3 -B -I cite_sample_indep.py <repo> <audit_dir> <out_prefix>
Extracts file:line cites from CORE-PR-HANDOFF-v15.md and -other-tracks.md with its own regex; seed 20261116; samples 60;
for each: resolve file, range exists?, the range text, anchors (identifier words in backticks on the same doc line,
that are not cites) found inside range / within 3 lines / elsewhere in file / nowhere. Verdict by program:
HIT (an anchor inside the range), NEAR (anchor within 3 lines outside), MOVED (anchor elsewhere in file only), MISSING (file/range absent or no anchor in file)."""
import os, re, random, sys, json
repo, adir, outp = sys.argv[1], sys.argv[2], sys.argv[3]
docs = ["CORE-PR-HANDOFF-v15.md", "CORE-PR-HANDOFF-v15-other-tracks.md"]
CITE = re.compile(r"([\w./-]*[\w-]+\.(?:py|sql|yml|md|sh|toml))((?::\d+(?:-\d+)?(?:\s*,\s*(?=:?\d))?)+)")
NUMS = re.compile(r":?(\d+)(?:-(\d+))?")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
STOP = set("this that with from line lines file true false none self test tests docs which when then else".split())
files = {}
for top in ("src", "tests", "demos", ".github", "handover", "docs", "pyproject.toml"):
    pth = os.path.join(repo, top)
    if os.path.isfile(pth): files[top] = pth; continue
    for d, ds, fs in os.walk(pth):
        ds[:] = [x for x in ds if x not in ("__pycache__", ".git", ".venv")]
        for f in fs:
            p = os.path.join(d, f); files[os.path.relpath(p, repo)] = p
files = {r: p for r, p in files.items() if not r.startswith("handover/core-hardening/audit-r460")}
def resolve(name): return [r for r in files if r == name or r.endswith("/" + name)]
cites = []
for doc in docs:
    for n, line in enumerate(open(os.path.join(adir, doc), encoding="utf-8").read().split("\n"), 1):
        spans = re.findall(r"`([^`]+)`", line); anc = set()
        for s in spans:
            s2 = CITE.sub("", s)
            for w in IDENT.findall(s2):
                if w.lower() not in STOP: anc.add(w)
        for m in CITE.finditer(line):
            for a, b in NUMS.findall(m.group(2)):
                cites.append((doc, n, m.group(1), int(a), int(b) if b else int(a), sorted(anc)))
print("cites extracted by my regex:", len(cites))
rnd = random.Random(20261116); idx = sorted(rnd.sample(range(len(cites)), 60))
cache = {}
def lines_of(rel):
    if rel not in cache: cache[rel] = open(files[rel], encoding="utf-8", errors="replace").read().split("\n")
    return cache[rel]
res = []; cnt = {}
for i in idx:
    doc, n, path, lo, hi, anc = cites[i]; c = resolve(path)
    if not c: v, det, txt = "MISSING", "file not found", ""
    else:
        pref = [r for r in c if r.startswith(("src/", "tests/", "demos/", ".github/"))] or c
        rel = pref[0]; L = lines_of(rel); amb = len(pref) > 1
        if lo > len(L): v, det, txt = "MISSING", f"{rel} has {len(L)} lines", ""
        else:
            inside = "\n".join(L[lo-1:min(hi, len(L))]); near = "\n".join(L[max(0, lo-4):min(len(L), hi+3)]); whole = "\n".join(L)
            ain = [a for a in anc if re.search(r"\b" + re.escape(a) + r"\b", inside)]
            anear = [a for a in anc if re.search(r"\b" + re.escape(a) + r"\b", near)]
            awhole = [a for a in anc if re.search(r"\b" + re.escape(a) + r"\b", whole)]
            if ain: v = "HIT"; det = "anchors inside: " + ",".join(ain[:4])
            elif anear: v = "NEAR"; det = "anchors within 3 lines: " + ",".join(anear[:4])
            elif awhole: v = "MOVED"; det = "anchors only elsewhere in file: " + ",".join(awhole[:4])
            else: v = "NOANCHOR"; det = "no anchor of the doc line occurs in the file (cannot judge by words)"
            if amb: det += f" [AMBIGUOUS name: {len(pref)} files, used {rel}]"
            det = rel + " (" + str(len(L)) + " lines): " + det
            txt = " || ".join(x.strip()[:90] for x in L[lo-1:min(hi, len(L))][:4])
    cnt[v] = cnt.get(v, 0) + 1; res.append((i, doc, n, path, lo, hi, v, det, txt))
print("seed 20261116; sample indexes", idx)
print("counts", json.dumps(cnt, sort_keys=True))
with open(outp + "-sample60.tsv", "w") as f:
    for r in res: f.write("\t".join(map(str, r)) + "\n")

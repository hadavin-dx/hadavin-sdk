"""Independent citation checker (v14). usage: python -I cite_check_indep_v14.py <repo_root> <out_tsv> <doc>...
Own code, not the builder's. Per file:line cite: resolves the file, checks the range exists, then tests the anchors.
Anchors = identifier-like words from backtick spans on the SAME doc line that are not themselves cites AND that occur at
least once in the cited file. STATUS: HIT0 (anchor inside the cited window exactly), HIT2 (only within +-2 lines),
MOVED (anchors exist in the file but none within +-2: reports nearest line and delta), NOANCHOR_IN_FILE (line has
anchors, none occur in this file: cannot judge), NOANCHOR (no anchors on the line), MISSING, AMBIG, RANGE.
Also checks backtick names against the code corpus and path-like names against the file system. Changes nothing."""
import os, re, sys, csv
root, out = sys.argv[1], sys.argv[2]; docs = sys.argv[3:]
TOPS = ("src", "tests", "demos", ".github", "handover")
EXCL = ("handover/core-hardening/audit-r460",)
files = {}
for top in TOPS:
    for d, ds, fs in os.walk(os.path.join(root, top)):
        ds[:] = [x for x in ds if x not in ("__pycache__", ".git", ".venv")]
        for f in fs:
            p = os.path.join(d, f); rel = os.path.relpath(p, root)
            files[rel] = p
code_files = {r: p for r, p in files.items() if not any(r.startswith(e) for e in EXCL)}
cache = {}
def L(p):
    if p not in cache: cache[p] = open(p, encoding="utf-8", errors="replace").read().split("\n")
    return cache[p]
corpus = "\n".join("\n".join(L(p)) for r, p in code_files.items() if r.endswith((".py", ".sql", ".yml", ".yaml", ".toml", ".md", ".sh", ".txt", ".json")))
def resolve(name):
    c = [r for r in code_files if r == name or r.endswith("/" + name)]
    pref = [r for r in c if r.startswith(("src/hadavin_sdk/", "tests/", "demos/", ".github/"))]
    return pref or c
CITE = re.compile(r"([\w./-]*[\w-]+\.(?:py|sql|yml|md|sh|toml))((?::\d+(?:-\d+)?(?:\s*,\s*(?=:?\d))?)+)")
NUMS = re.compile(r":?(\d+)(?:-(\d+))?")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
STOP = set("this that with from line lines file true false none self test tests docs which when then else.".split())
def anchors_of(line):
    spans = re.findall(r"`([^`]+)`", line); a = set()
    for s in spans:
        if CITE.search(s): s = CITE.sub("", s)
        for w in IDENT.findall(s):
            if w.lower() in STOP or w.isdigit(): continue
            a.add(w)
    return a
rows = []; counts = {}
def bump(k): counts[k] = counts.get(k, 0) + 1
for doc in docs:
    for n, line in enumerate(open(doc, encoding="utf-8").read().split("\n"), 1):
        anc = anchors_of(line)
        for m in CITE.finditer(line):
            path, rest = m.group(1), m.group(2)
            if re.match(r"(?:raw|evidence|cites)[\w-]*", path) and False: continue
            cands = resolve(path)
            specs = [(int(a), int(b) if b else int(a)) for a, b in NUMS.findall(rest)]
            for (lo, hi) in specs:
                kind = "range" if hi != lo else "single"
                if not cands:
                    st = "MISSING"; detail = "file not found"
                elif len(cands) > 1 and not any(c == path or c.endswith("/" + path) and c.count("/") == path.count("/") for c in cands[:1]) and len(set(os.path.basename(c) for c in cands)) == 1 and len(cands) > 1:
                    st = "AMBIG"; detail = ",".join(cands[:3])
                else:
                    rel = cands[0]; ls = L(code_files[rel])
                    if hi > len(ls) or lo < 1: st = "RANGE"; detail = f"{rel} has {len(ls)} lines"
                    else:
                        fa = [w for w in anc if re.search(r"\b" + re.escape(w) + r"\b", "\n".join(ls))]
                        win0 = "\n".join(ls[lo - 1:hi]); win2 = "\n".join(ls[max(0, lo - 3):hi + 2])
                        if not anc: st = "NOANCHOR"; detail = rel
                        elif not fa: st = "NOANCHOR_IN_FILE"; detail = rel
                        elif any(re.search(r"\b" + re.escape(w) + r"\b", win0) for w in fa): st = "HIT0"; detail = rel
                        elif any(re.search(r"\b" + re.escape(w) + r"\b", win2) for w in fa): st = "HIT2"; detail = rel
                        else:
                            best = None
                            for i, t in enumerate(ls, 1):
                                if any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in fa):
                                    d = abs(i - (lo + hi) // 2)
                                    if best is None or d < best[0]: best = (d, i)
                            st = "MOVED"; detail = f"{rel} nearest anchor line {best[1]} (delta {best[0]}) anchors={sorted(fa)[:4]}"
                bump(st); rows.append((os.path.basename(doc), n, f"{path}:{lo}" + (f"-{hi}" if hi != lo else ""), kind, st, detail))
with open(out, "w", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["doc", "doc_line", "cite", "kind", "status", "detail"]); w.writerows(rows)
print("cites:", len(rows)); print("status counts:", dict(sorted(counts.items())))
# backtick-name existence
for doc in docs:
    txt = open(doc, encoding="utf-8").read(); miss = {}; pathmiss = {}; tot = 0
    for n, line in enumerate(txt.split("\n"), 1):
        for s in re.findall(r"`([^`\n]+)`", line):
            s0 = s.strip()
            if CITE.search(s0): 
                pm = re.match(r"^([\w./-]+\.(?:py|sql|yml|md|sh|toml))(?::|$)", s0)
                if pm and not resolve(pm.group(1)) and not os.path.exists(os.path.join(os.path.dirname(doc), pm.group(1))): pathmiss.setdefault(pm.group(1), n)
                continue
            core = re.sub(r"\(.*$", "", s0).split("::")[-1]
            if re.fullmatch(r"[A-Za-z_][\w.]*", core) and (("_" in core) or re.search(r"[a-z][A-Z]", core) or s0.endswith("(") or "." in core):
                tot += 1; last = core.split(".")[-1]
                if len(last) >= 4 and not re.search(r"\b" + re.escape(last) + r"\b", corpus): miss.setdefault(core, n)
            elif re.fullmatch(r"[\w./-]+\.(?:py|sql|yml|md|sh|toml|tsv|txt|json)", s0):
                if not resolve(s0) and not os.path.exists(os.path.join(os.path.dirname(doc), s0)) and not os.path.exists(os.path.join(os.path.dirname(doc), "evidence-handoff-v14", s0)):
                    pathmiss.setdefault(s0, n)
    print(f"== {os.path.basename(doc)}: identifier-like backtick names checked {tot}; NOT in code corpus (src,tests,demos,.github,handover minus audit-r460): {len(miss)}; path-like names unresolved: {len(pathmiss)}")
    for k, v in sorted(miss.items(), key=lambda x: x[1]): print(f"  NAME-NOT-IN-CODE line {v}: {k}")
    for k, v in sorted(pathmiss.items(), key=lambda x: x[1]): print(f"  PATH-UNRESOLVED line {v}: {k}")

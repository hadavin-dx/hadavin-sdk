"""Independent citation resolver (own code). usage: python -I ind_cites.py <repo> <doc>...
Cite forms: path.ext:N, :N-M, path.ext:N,:M / ', :M' / ' and :M' continuations (same path),
and bare ':N' later in the same sentence (AMBIGUOUS, tested against nearest preceding path).
Checks: file exists (unique suffix match under src/hadavin_sdk, tests, demos, .github, docs, handover),
range inside file length, range well-formed, anchor (backtick identifiers near the cite) within range +-3 lines."""
import os, re, sys, json
root = sys.argv[1]; docs = sys.argv[2:]
index = {}
for top in ("src", "tests", "demos", ".github", "docs", "handover", "."):
    base = os.path.join(root, top)
    walker = [(base, [], os.listdir(base))] if top == "." else os.walk(base)
    for d, ds, fs in walker:
        if top != ".": ds[:] = [x for x in ds if x not in ("__pycache__", ".git", ".venv", "node_modules")]
        for f in fs:
            p = os.path.join(d, f)
            if os.path.isfile(p): index[os.path.relpath(p, root)] = p
def resolve(name):
    name = name[2:] if name.startswith("./") else name
    ex = [r for r in index if r == name]
    if ex: return ex
    c = [r for r in index if r.endswith("/" + name)]
    pref = [r for r in c if r.split("/")[0] in ("src", "tests", "demos", ".github")]
    c = pref or c
    core = [r for r in c if r.startswith("src/hadavin_sdk/")]
    if len(core) == 1 and "/" not in name: return core
    return c
cache = {}
def lines(rel):
    if rel not in cache:
        cache[rel] = open(index[rel], encoding="utf-8", errors="replace").read().split("\n")
        if cache[rel] and cache[rel][-1] == "": cache[rel].pop()
    return cache[rel]
PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w-]+\.(?:py|sql|yml|yaml|md|toml|sh))")
NUM = r":(\d+)(?:-(\d+))?"
CITE = re.compile(PATH.pattern + r"((?:" + NUM + r")(?:\s*(?:,|and|;)?\s*(?::\d+(?:-\d+)?))*)")
BARE = re.compile(r"(?<![\w/.)-])" + NUM + r"(?![\d:])")
def anchors(seg):
    toks = []
    for span in re.findall(r"`([^`]+)`", seg):
        if re.search(r"\.(py|sql|yml|md)", span) and ":" in span: continue
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", span):
            if not (("_" in t) or re.search(r"[a-z][A-Z]", t) or t.isupper() or t[0].isupper() and len(t) > 5 or (t + "(") in span or ("." + t) in span or (t + ".") in span): continue
            if t not in ("self", "None", "True", "False", "from", "import", "with", "that", "this", "tests", "src"): toks.append(t)
    return toks
rows = []
for doc in docs:
    for ln, line in enumerate(open(doc, encoding="utf-8").read().split("\n"), 1):
        # cites with path
        spans = []
        for m in CITE.finditer(line):
            spans.append((m.start(), m.end(), m.group(1), m.group(2), False))
        covered = [(s, e) for s, e, *_ in spans]
        # bare continuations not covered
        for m in BARE.finditer(line):
            if any(s <= m.start() < e for s, e in covered): continue
            prev = [x for x in spans if x[1] <= m.start()]
            # also include paths without line numbers earlier in line
            pm = [p for p in PATH.finditer(line[:m.start()])]
            if not pm: continue
            last = pm[-1]
            between = line[last.end():m.start()]
            sent_break = bool(re.search(r"[.;)]\s", between)) 
            spans.append((m.start(), m.end(), last.group(1), m.group(0), True))
        spans.sort()
        for idx, (s, e, path, rest, bare) in enumerate(spans):
            prev_end = spans[idx-1][1] if idx else max(0, line.rfind(". ", 0, s) + 1)
            nxt = spans[idx+1][0] if idx + 1 < len(spans) else len(line)
            seg = line[prev_end:s] + " " + line[e:nxt]
            for a, b in [(x[0], x[1]) for x in re.findall(NUM, rest)] and re.findall(r":(\d+)(?:-(\d+))?", rest):
                a = int(a); b = int(b) if b else a
                st = "AMBIGUOUS" if bare else "OK"
                # adjacency: bare ':N' directly after prior cite separator is not ambiguous
                if bare:
                    gap = line[spans[idx-1][1]:s] if idx else "xx"
                    if idx and re.fullmatch(r"\s*(,|;|and|/|,\s*and)?\s*", gap): st = "OK"
                cands = resolve(path)
                if not cands:
                    rows.append((doc, ln, path, a, b, "MISSING-FILE", "", st)); continue
                if len(cands) > 1: st = "AMBIGUOUS"
                res = []
                for c in cands:
                    L = lines(c)
                    if a < 1 or b < a: res.append((c, "RANGE-BAD", len(L)))
                    elif b > len(L): res.append((c, "RANGE-OUT(len=%d)" % len(L), len(L)))
                    else:
                        toks = anchors(seg)
                        lo, hi = max(1, a-3), min(len(L), b+3)
                        win = "\n".join(L[lo-1:hi])
                        if not toks: res.append((c, "RANGE-OK/NO-ANCHOR", len(L)))
                        else:
                            hit = [t for t in toks if t in win]
                            res.append((c, "ANCHOR-OK" if hit else "ANCHOR-MISS[" + ",".join(sorted(set(toks))[:5]) + "]", len(L)))
                good = [x for x in res if not x[1].startswith("RANGE-OUT") and x[1] != "RANGE-BAD"]
                for c, r, n in (good[:1] if good else res[:1]):
                    L = lines(c); txt = " | ".join(x.strip() for x in L[max(0, a-1):min(len(L), b)][:2])[:110]
                    rows.append((doc, ln, c, a, b, r, txt, st if len(cands) == 1 or True else st))
                    if len(cands) > 1: rows[-1] = rows[-1][:7] + ("AMBIGUOUS" if st == "OK" else st,)
out = sys.argv[0]
w = open("cites-table.tsv", "w")
w.write("doc\tdoc_line\tfile\tfrom\tto\tresult\tstatus\tsource_text\n")
for r in rows: w.write("%s\t%d\t%s\t%d\t%d\t%s\t%s\t%s\n" % (os.path.basename(r[0]), r[1], r[2], r[3], r[4], r[5], r[7], r[6]))
w.close()
from collections import Counter
cnt = Counter(); 
for r in rows:
    k = r[5].split("[")[0].split("(")[0]; cnt[(os.path.basename(r[0]), k, r[7])] += 1
for k, v in sorted(cnt.items()): print(v, *k)
print("total", len(rows))

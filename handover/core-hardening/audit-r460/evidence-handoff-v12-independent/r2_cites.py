"""R2 citation checker (own code, written for the v12 independent check). Reads files only; runs no repo code.
usage: python -I r2_cites.py <repo> <outdir> <doc>...
Class A (real code cites): path:N, path:N-M, continuations ", :N", `path` N-M (prose range), "ci.yml line(s) N".
Class B (prose backtick words): every other backtick span, checked as file / symbol / not-a-symbol.
"""
import os, re, sys, subprocess, collections
repo, outdir, docs = sys.argv[1], sys.argv[2], sys.argv[3:]
SKIP = {"__pycache__", ".git", ".venv", "node_modules", ".pytest_cache", ".ruff_cache"}
files = {}
for top in ("src", "tests", "demos", ".github", "docs", "handover", "scripts", "tools"):
    b = os.path.join(repo, top)
    if not os.path.isdir(b):
        continue
    for d, ds, fs in os.walk(b):
        ds[:] = [x for x in ds if x not in SKIP]
        for f in fs:
            p = os.path.join(d, f)
            files[os.path.relpath(p, repo)] = p
for f in os.listdir(repo):
    p = os.path.join(repo, f)
    if os.path.isfile(p):
        files[f] = p
CODE = [r for r in files if r.startswith(("src/", "tests/", "demos/", ".github/")) or "/" not in r]
_t = {}
def text(r):
    if r not in _t:
        try:
            _t[r] = open(files[r], encoding="utf-8", errors="replace").read()
        except Exception:
            _t[r] = ""
    return _t[r]
def lines(r):
    t = text(r).split("\n")
    if t and t[-1] == "":
        t.pop()
    return t
def resolve(name):
    """returns (candidates, how). Doc rule: folder-written name is under src/hadavin_sdk unless tests/ demos/."""
    name = name.lstrip("./") if name.startswith("./") else name
    if name in files:
        return [name], "exact"
    for pre in ("src/hadavin_sdk/", "src/hadavin_sdk/store/migrations/"):
        if pre + name in files:
            return [pre + name], "src-rel"
    c = [r for r in files if r.endswith("/" + name)]
    core = [r for r in c if r.startswith("src/hadavin_sdk/")]
    if len(core) == 1:
        return core, "unique-in-core"
    if len(c) == 1:
        return c, "unique"
    pref = [r for r in c if r.startswith(("tests/", "demos/", ".github/"))]
    if len(c) > 1:
        return c, "multi"
    return [], "none"
EXT = r"(?:py|sql|yml|yaml|md|toml|sh|txt|tsv|cfg|json)"
PATH = r"((?:[\w.\-]+/)*[\w.\-]+\." + EXT + r")"
NUM = r"\d+(?:-\d+)?"
# cite with colon numbers and continuations
C1 = re.compile(PATH + r":(" + NUM + r")((?:\s*(?:,|;|and|/|,\s*and)?\s*:" + NUM + r")*)")
# path in backticks followed by space and prose range(s): `store/migrate.py` 40-100 and 283-345
C2 = re.compile(r"`" + PATH + r"`\s*(?:\(?lines?\s*)?(" + NUM + r"(?:\s*(?:,|and)\s*" + NUM + r")*)(?![\w:./-])")
# ci.yml lines 86-87 / ci.yml line 77
C3 = re.compile(PATH + r"\s*\(?lines?\s+(" + NUM + r"(?:\s*(?:,|and)\s*" + NUM + r")*)")
BARECONT = re.compile(r"(?<![\w/.)\-\d])(?<!\w):(" + NUM + r")(?![\w\d:])")
def rngs(s):
    out = []
    for m in re.finditer(r"(\d+)(?:-(\d+))?", s):
        a = int(m.group(1)); b = int(m.group(2) or a); out.append((a, b))
    return out
STOP = {"self", "None", "True", "False", "from", "import", "with", "that", "this", "tests", "src", "path", "file", "line", "lines", "none", "NaN", "Infinity", "Decimal"}
def idents(seg):
    toks = []
    for span in re.findall(r"`([^`]+)`", seg):
        if re.search(r"\." + EXT + r"(:|$|\b)", span) and re.search(r":\d", span):
            continue
        if " " in span.strip() and not re.search(r"[(_]", span):
            continue
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", span):
            if len(t) < 4 or t in STOP:
                continue
            if ("_" in t) or re.search(r"[a-z][A-Z]", t) or (t.isupper() and len(t) > 3) or (t[0].isupper()) or (t + "(" in span) or ("." + t in span):
                toks.append(t)
    seen = []
    for t in toks:
        if t not in seen:
            seen.append(t)
    return seen
def word_lines(r, tok):
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(tok) + r"(?![A-Za-z0-9_])")
    return [i for i, l in enumerate(lines(r), 1) if pat.search(l)]
rows = []
def add(**k):
    rows.append(k)
for doc in docs:
    dn = os.path.basename(doc)
    for ln, line in enumerate(open(doc, encoding="utf-8").read().split("\n"), 1):
        cites = []  # (start,end,path,[(a,b)],kind)
        for m in C1.finditer(line):
            rs = rngs(":" + m.group(2) + m.group(3))
            rs = rngs(m.group(2)) + rngs(m.group(3))
            cites.append((m.start(), m.end(), m.group(1), rs, "path:N"))
        for m in C2.finditer(line):
            if any(s <= m.start() < e for s, e, *_ in cites):
                continue
            cites.append((m.start(), m.end(), m.group(1), rngs(m.group(2)), "path N-M (prose)"))
        for m in C3.finditer(line):
            if any(s <= m.start() < e for s, e, *_ in cites):
                continue
            cites.append((m.start(), m.end(), m.group(1), rngs(m.group(2)), "path line(s) N"))
        cites.sort()
        # bare :N not part of any cite
        for m in BARECONT.finditer(line):
            if any(s <= m.start() < e for s, e, *_ in cites):
                continue
            prev = [c for c in cites if c[1] <= m.start()]
            pm = [x for x in re.finditer(PATH, line[:m.start()])]
            path = (prev[-1][2] if prev and (not pm or prev[-1][1] >= pm[-1].end()) else (pm[-1].group(1) if pm else None))
            if path:
                cites.append((m.start(), m.end(), path, rngs(m.group(1)), "bare :N (not a continuation)"))
        cites.sort()
        for i, (s, e, path, rs, kind) in enumerate(cites):
            lo = max(line.rfind(". ", 0, s) + 1, line.rfind("| ", 0, s) + 1, cites[i - 1][1] if i else 0)
            hi = cites[i + 1][0] if i + 1 < len(cites) else len(line)
            before = line[lo:s]; after = line[e:hi]
            anch = idents(before) or idents(after)
            cand, how = resolve(path)
            for (a, b) in rs:
                base = dict(doc=dn, line=ln, cite="%s:%d%s" % (path, a, "-%d" % b if b != a else ""), kind=kind, cls="A")
                claim = (before.strip()[-70:] + " ||" + after.strip()[:40]).replace("\t", " ")
                if not cand:
                    add(**base, claim=claim, target=path, actual="file not found in tree", status="MISSING"); continue
                if how == "multi":
                    add(**base, claim=claim, target=path, actual="name matches %d files: %s" % (len(cand), ",".join(cand[:3])), status="AMBIGUOUS"); continue
                r = cand[0]; L = lines(r)
                if a < 1 or b < a or b > len(L):
                    # symbol elsewhere?
                    where = []
                    for t in anch:
                        wl = word_lines(r, t)
                        if wl: where.append((t, wl[0]))
                    if where:
                        add(**base, claim=claim, target=r, actual="range past EOF (len %d); %s at %d" % (len(L), where[0][0], where[0][1]), status="LINE-OFF")
                    else:
                        add(**base, claim=claim, target=r, actual="range past EOF or malformed (file len %d)" % len(L), status="MISSING")
                    continue
                win = "\n".join(L[a - 1:b])
                if not anch:
                    add(**base, claim=claim, target=r, actual="range ok, no anchor: " + " | ".join(x.strip() for x in L[a - 1:b][:1])[:60], status="MATCH", note="range-only"); continue
                hit = [t for t in anch if re.search(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", win)]
                if hit:
                    add(**base, claim=claim, target=r, actual="%s present in %d-%d" % (hit[0], a, b), status="MATCH", note="anchor"); continue
                anyfile = [(t, word_lines(r, t)) for t in anch]
                found = [(t, w) for t, w in anyfile if w]
                if found:
                    t, w = found[0]
                    near = min(w, key=lambda x: min(abs(x - a), abs(x - b)))
                    add(**base, claim=claim, target=r, actual="%s at line %d (cite %d-%d, off by %d)" % (t, near, a, b, near - a if near < a else near - b), status="LINE-OFF"); continue
                # absent in file: symbol absent from tree?
                add(**base, claim=claim, target=r, actual="anchors %s absent from file" % ",".join(anch[:3]), status="MISSING", note="symbol-absent-in-file")
        # Class B: backtick spans not inside a cite
        covered = [(s, e) for s, e, *_ in cites]
        for m in re.finditer(r"`([^`]+)`", line):
            if any(s <= m.start() < e for s, e in covered):
                continue
            sp = m.group(1).strip()
            base = dict(doc=dn, line=ln, cite="`%s`" % sp[:60], kind="backtick", cls="B", claim=line[max(0, m.start() - 40):m.start()].strip().replace("\t", " ")[-40:])
            # file path
            pm = re.fullmatch(PATH, sp)
            if pm:
                c, how = resolve(sp)
                if c and how != "multi":
                    add(**base, target=c[0], actual="file exists", status="MATCH", note="file")
                elif how == "multi":
                    add(**base, target=sp, actual="matches %d files" % len(c), status="AMBIGUOUS", note="file")
                else:
                    add(**base, target=sp, actual="no such file in tree", status="MISSING", note="file")
                continue
            # dir path
            if re.fullmatch(r"[\w.\-/]+/", sp) or (re.fullmatch(r"[\w.\-]+(/[\w.\-]+)+", sp) and not re.search(r"\s", sp)):
                p = sp.rstrip("/")
                ex = any(r.startswith(p + "/") or r.startswith("src/hadavin_sdk/" + p + "/") for r in files) or any(r == p or r == "src/hadavin_sdk/" + p or r.startswith("src/hadavin_sdk/" + p) for r in files)
                add(**base, target=sp, actual="folder/path exists" if ex else "no such path", status="MATCH" if ex else "MISSING", note="folder"); continue
            ids = idents("`" + sp + "`")
            if not ids or (" " in sp and not re.search(r"[(_]|\.\w", sp)):
                add(**base, target="-", actual="not a code symbol (word, value, command or id)", status="AMBIGUOUS", note="not-symbol"); continue
            absent = []; present = []
            for t in ids:
                hits = [r for r in CODE if re.search(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", text(r))]
                (present if hits else absent).append((t, hits[0] if hits else ""))
            if not absent:
                add(**base, target=present[0][1], actual="%d symbol(s) found, e.g. %s" % (len(present), present[0][0]), status="MATCH", note="symbol"); continue
            if present:
                add(**base, target=present[0][1], actual="partly: absent=%s" % ",".join(t for t, _ in absent[:3]), status="MISSING", note="symbol-partial")
            else:
                add(**base, target="-", actual="absent from src/tests/demos/.github: %s" % ",".join(t for t, _ in absent[:3]), status="MISSING", note="symbol")
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "cites-table.tsv"), "w", encoding="utf-8") as w:
    w.write("cited_at\tclass\tkind\tclaim\ttarget\twhat_is_actually_there\tstatus\tnote\n")
    for r in rows:
        w.write("%s:%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (r["doc"], r["line"], r["cls"], r["kind"], (r["cite"] + " :: " + r["claim"])[:150].replace("\t", " "), r["target"], r["actual"][:110], r["status"], r.get("note", "")))
c = collections.Counter((r["cls"], r["status"]) for r in rows)
print(sorted(c.items()))
print("total", len(rows))

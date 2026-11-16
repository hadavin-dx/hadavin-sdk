#!/usr/bin/env python3
"""Independent import-cycle check (written fresh; does not read evidence-handoff-v10/).
Parses every module under src/hadavin_sdk with ast.

Edge kinds per import statement:
  run  = statement executed at import time (module top level, including inside try/if blocks, but NOT inside
         `if TYPE_CHECKING:` and NOT inside a function/class method body)
  type = inside `if TYPE_CHECKING:` at module top level
  late = inside a function body (not import time)

Counting A: explicit import / from-import statements only (target modules named in the statement, `from X import Y`
            goes to X.Y if that is a module, else X).
Counting B: A plus, for every imported module, an edge to each ancestor package (`pkg/__init__`), because Python
            runs the package __init__ first.

Output: strongly connected components (size > 1) for each variant, then the same after adding the planned edges
of section 8.1 of CORE-PR-HANDOFF-v10.md (read by this script from the markdown between the PLANNED-EDGES markers).
"""
import ast, os, re, sys, json
from collections import defaultdict

SRC = "/home/user/hadavin-sdk/src"
DOC = "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v10.md"
PKG = "hadavin_sdk"

mods = {}  # dotted -> path
for d, _, fs in os.walk(os.path.join(SRC, PKG)):
    if "__pycache__" in d:
        continue
    for f in fs:
        if not f.endswith(".py"):
            continue
        p = os.path.join(d, f)
        rel = os.path.relpath(p, SRC)[:-3].split(os.sep)
        if rel[-1] == "__init__":
            rel = rel[:-1]
        mods[".".join(rel)] = p


def resolve_from(cur, node):
    if node.level:
        base = cur.split(".")
        is_pkg = mods[cur].endswith("__init__.py")
        if not is_pkg:
            base = base[:-1]
        base = base[: len(base) - (node.level - 1)]
        mod = ".".join(base + ([node.module] if node.module else []))
    else:
        mod = node.module or ""
    return mod


def edges_of(name):
    tree = ast.parse(open(mods[name], encoding="utf-8").read())
    out = []  # (target, kind)

    def tgt(mod, names):
        res = []
        if not mod.startswith(PKG):
            return res
        for n in names or [None]:
            cand = mod + "." + n if n else None
            if cand and cand in mods:
                res.append(cand)
            elif mod in mods:
                res.append(mod)
        return res

    def walk(body, kind):
        for node in body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    for t in tgt(a.name, None):
                        out.append((t, kind))
            elif isinstance(node, ast.ImportFrom):
                mod = resolve_from(name, node)
                for t in tgt(mod, [a.name for a in node.names]):
                    out.append((t, kind))
            elif isinstance(node, ast.If):
                test = ast.unparse(node.test)
                if "TYPE_CHECKING" in test:
                    walk(node.body, "type")
                    walk(node.orelse, kind)
                else:
                    walk(node.body, kind)
                    walk(node.orelse, kind)
            elif isinstance(node, (ast.Try,)):
                walk(node.body, kind)
                for h in node.handlers:
                    walk(h.body, kind)
                walk(node.orelse, kind)
                walk(node.finalbody, kind)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(node.body, "late")
            elif isinstance(node, ast.ClassDef):
                walk(node.body, kind)
            elif isinstance(node, (ast.With, ast.For, ast.While)):
                walk(node.body, kind)

    walk(tree.body, "run")
    return out


def ancestors(m):
    parts = m.split(".")
    return [".".join(parts[:i]) for i in range(1, len(parts))]


def build(kinds, parents):
    g = defaultdict(set)
    for m in mods:
        for t, k in edges_of(m):
            if k in kinds and t != m:
                g[m].add(t)
                if parents:
                    for a in ancestors(t):
                        if a in mods and a != m:
                            g[m].add(a)
        g.setdefault(m, set())
    return g


def scc(g):
    idx, low, st, on, res, c = {}, {}, [], set(), [], [0]
    sys.setrecursionlimit(10000)

    def sc(v):
        idx[v] = low[v] = c[0]
        c[0] += 1
        st.append(v)
        on.add(v)
        for w in g[v]:
            if w not in idx:
                sc(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                res.append(sorted(comp))

    for v in list(g):
        if v not in idx:
            sc(v)
    return sorted(res, key=len, reverse=True)


# planned edges from the document table
txt = open(DOC, encoding="utf-8").read()
seg = txt.split("<!-- PLANNED-EDGES-BEGIN -->")[1].split("<!-- PLANNED-EDGES-END -->")[0]
planned = []  # (src, dst, kind)
for ln in seg.strip().split("\n")[2:]:
    cells = [x.strip() for x in ln.strip().strip("|").split("|")]
    if len(cells) < 3:
        continue
    srcm = PKG + "." + cells[0]
    for kind, cell in (("run", cells[1]), ("type", cells[2])):
        for t in [x.strip() for x in cell.split(",") if x.strip()]:
            planned.append((srcm, PKG + "." + t, kind))

print("modules:", len(mods))
print("planned edges parsed:", len(planned))
missing = sorted({x for s, d, k in planned for x in (s, d) if x not in mods})
print("planned endpoints that do not exist today (new modules expected):", missing)

report = {}
for label, kinds, parents in [("A-run", {"run"}, False), ("A-run+type", {"run", "type"}, False),
                              ("B-run", {"run"}, True), ("B-run+type", {"run", "type"}, True),
                              ("A-run+type+late", {"run", "type", "late"}, False)]:
    g = build(kinds, parents)
    base = scc(g)
    # add planned edges (kinds counted per variant)
    g2 = {k: set(v) for k, v in g.items()}
    for s, d, k in planned:
        if k in kinds:
            for n in (s, d):
                g2.setdefault(n, set())
            g2[s].add(d)
            if parents:
                for a in ancestors(d):
                    if a in mods and a != s:
                        g2[s].add(a)
    new = scc(g2)
    print(f"\n== {label}: today {len(base)} cycle group(s) of size>1 ; with planned edges {len(new)}")
    for i, comp in enumerate(base):
        print(f"  today[{i}] size {len(comp)}:", ", ".join(x.replace(PKG + '.', '') for x in comp))
    for i, comp in enumerate(new):
        tag = "SAME" if comp in base else "CHANGED/NEW"
        print(f"  planned[{i}] size {len(comp)} {tag}:", ", ".join(x.replace(PKG + '.', '') for x in comp))
    tm = {s for s, d, k in planned} | {d for s, d, k in planned}
    in_new = sorted(x for c in new for x in c if x in tm and not any(x in b for b in base))
    print("  planned-table modules in a cycle group they were NOT in today:", [x.replace(PKG + '.', '') for x in in_new])
    report[label] = dict(today=base, planned=new)
json.dump(report, open("cycles_report.json", "w"), indent=1)

# hypothetical: llm.spend -> config as a type-only edge (v10 section 8.1 text claims this closes a cycle through
# config, registry, deferred, replay_records)
g = build({"run", "type"}, False)
g[PKG + ".llm.spend"] = {PKG + ".models", PKG + ".llm.protocol", PKG + ".config"}
for s, d, k in planned:
    g.setdefault(s, set()).add(d)
print("\n== hypothetical llm.spend -> config (type-only, counting A, run+type), planned edges included")
for comp in scc(g):
    if PKG + ".llm.spend" in comp:
        print("  cycle containing llm.spend:", ", ".join(x.replace(PKG + '.', '') for x in comp))

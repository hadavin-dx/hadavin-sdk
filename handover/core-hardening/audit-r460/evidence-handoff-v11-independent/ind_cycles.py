"""Own import-cycle counter. usage: python -I ind_cycles.py <repo>
Nodes = modules of src/hadavin_sdk (package __init__ = the package name). Edges from ast Import/ImportFrom, relative imports resolved.
Variants: tt = include imports under `if TYPE_CHECKING`; fn = include imports inside functions.
A = explicit imports only. B = A + for every imported module an edge to each ancestor package __init__ (what Python runs).
BG = group by parent package: modules collapse to their package node (strict reading of 'group by parent package')."""
import ast, os, sys, re
root = sys.argv[1]; pkgdir = os.path.join(root, "src", "hadavin_sdk"); TOP = "hadavin_sdk"
mods = {}
for d, ds, fs in os.walk(pkgdir):
    ds[:] = [x for x in ds if x != "__pycache__"]
    for f in fs:
        if not f.endswith(".py"): continue
        rel = os.path.relpath(os.path.join(d, f), pkgdir)[:-3].split(os.sep)
        if rel[-1] == "__init__": rel = rel[:-1]
        mods[".".join([TOP] + rel)] = (os.path.join(d, f), f == "__init__.py")
def collect(name, path, is_pkg):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = []  # (target, in_tt, in_fn)
    def walk(node, tt, fn):
        for ch in ast.iter_child_nodes(node):
            ntt, nfn = tt, fn
            if isinstance(ch, ast.If):
                t = ch.test
                if (isinstance(t, ast.Name) and t.id == "TYPE_CHECKING") or (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING"):
                    for b in ch.body: walk_stmt(b, True, fn)
                    for b in ch.orelse: walk_stmt(b, tt, fn)
                    continue
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)): nfn = True
            walk_stmt(ch, ntt, nfn)
    def walk_stmt(ch, tt, fn):
        if isinstance(ch, ast.Import):
            for a in ch.names: out.append((a.name, tt, fn))
        elif isinstance(ch, ast.ImportFrom):
            if ch.level:
                base = name.split(".") if is_pkg else name.split(".")[:-1]
                base = base[:len(base) - (ch.level - 1)] if ch.level > 1 else base
                modname = ".".join(base + ([ch.module] if ch.module else []))
            else: modname = ch.module or ""
            for a in ch.names:
                cand = modname + "." + a.name
                out.append((cand if cand in mods else modname, tt, fn))
        else:
            if isinstance(ch, ast.If):
                t = ch.test
                if (isinstance(t, ast.Name) and t.id == "TYPE_CHECKING") or (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING"):
                    for b in ch.body: walk_stmt(b, True, fn)
                    for b in ch.orelse: walk_stmt(b, tt, fn)
                    return
            nfn = fn or isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef))
            for c in ast.iter_child_nodes(ch): walk_stmt(c, tt, nfn)
    for ch in tree.body: walk_stmt(ch, False, False)
    return out
raw = {m: collect(m, p, ip) for m, (p, ip) in mods.items()}
def graph(tt, fn, mode, extra=None):
    g = {m: set() for m in mods}
    for m, lst in raw.items():
        for tgt, is_tt, is_fn in lst:
            if (is_tt and not tt) or (is_fn and not fn): continue
            if tgt not in mods: 
                # resolve to nearest existing module prefix
                parts = tgt.split(".")
                while parts and ".".join(parts) not in mods: parts.pop()
                if not parts or parts[0] != TOP: continue
                tgt = ".".join(parts)
            if tgt != m: g[m].add(tgt)
            if mode == "B":
                parts = tgt.split(".")
                for i in range(1, len(parts)):
                    anc = ".".join(parts[:i])
                    if anc in mods and anc != m: g[m].add(anc)
    if extra:
        for m, tgts in extra.items():
            g.setdefault(m, set()); g[m] |= {t for t in tgts if t != m}
    return g
def scc(g):
    idx = {}; low = {}; st = []; on = set(); res = []; c = [0]
    sys.setrecursionlimit(10000)
    def sc(v):
        idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
        for w in g.get(v, ()):
            if w not in idx: sc(w); low[v] = min(low[v], low[w])
            elif w in on: low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v: break
            res.append(sorted(comp))
    for v in g:
        if v not in idx: sc(v)
    return sorted([x for x in res if len(x) > 1], key=lambda x: (-len(x), x))
def short(x): return [m.replace(TOP + ".", "").replace(TOP, "<root>") for m in x]
def group(g):
    pk = lambda m: m if mods[m][1] else (m.rsplit(".", 1)[0])
    h = {}
    for m, ts in g.items():
        h.setdefault(pk(m), set())
        for t in ts:
            if pk(t) != pk(m): h[pk(m)].add(pk(t))
    return h
def rep(title, g, grouped=False):
    comps = scc(g)
    print("%s: sizes=%s" % (title, [len(x) for x in comps]))
    for x in comps[:3]: print("    group(%d): %s" % (len(x), ", ".join(short(x))))
    return comps
print("modules:", len(mods))
for tt in (False, True):
    for fn in (True, False):
        tag = "tt=%s fn=%s" % (tt, fn)
        rep("A  %s" % tag, graph(tt, fn, "A"))
        rep("B  %s" % tag, graph(tt, fn, "B"))
        rep("BG(group by parent package) %s" % tag, group(graph(tt, fn, "A")))
# planned: parse the document table
doc = open(sys.argv[2], encoding="utf-8").read()
tab = doc.split("<!-- PLANNED-EDGES-BEGIN -->")[1].split("<!-- PLANNED-EDGES-END -->")[0]
rt = {}; ty = {}
def fq(n):
    n = n.strip().strip("`")
    return TOP + "." + n if n else None
for row in tab.strip().split("\n")[2:]:
    c = [x.strip() for x in row.strip("|").split("|")]
    rt[fq(c[0])] = [fq(x) for x in c[1].split(",") if x.strip()]
    ty[fq(c[0])] = [fq(x) for x in c[2].split(",") if x.strip()]
newmods = [m for m in list(rt) + [t for v in list(rt.values()) + list(ty.values()) for t in v] if m not in mods]
print("planned modules not in today's tree:", sorted(set(short(newmods))))
for m in set(newmods): mods[m] = ("", False)
def planned(tt, mode, replace):
    g = graph(tt, True, mode)
    for m in set(newmods): g.setdefault(m, set())
    for m in rt:
        add = set(rt[m]) | (set(ty[m]) if tt else set())
        if mode == "B":
            for t in list(add):
                parts = t.split(".")
                for i in range(1, len(parts)):
                    a = ".".join(parts[:i])
                    if a in mods and a != m: add.add(a)
        if replace: g[m] = add - {m}
        else: g[m] |= add - {m}
    return g
for replace in (False, True):
    for tt in (False, True):
        for mode in ("A", "B"):
            g = planned(tt, mode, replace)
            rep("PLANNED %s tt=%s %s" % ("replace-listed-modules" if replace else "today+table", tt, mode), g)
            if mode == "A": rep("PLANNED %s tt=%s BG" % ("replace-listed-modules" if replace else "today+table", tt), group(g))

"""Own import-graph + SCC program (v12 independent). Reads src/hadavin_sdk with ast; runs no repo code. usage: python -I r2_graph.py <src-root>"""
import ast, os, sys
root = sys.argv[1]; pkg = "hadavin_sdk"
mods = {}
for d, ds, fs in os.walk(os.path.join(root, pkg)):
    ds[:] = [x for x in ds if x != "__pycache__"]
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(d, f); rel = os.path.relpath(p, os.path.join(root, pkg))[:-3].split(os.sep)
            name = ".".join(rel[:-1]) if rel[-1] == "__init__" else ".".join(rel)
            mods[name] = (p, rel[-1] == "__init__")
def tgt(name):  # longest existing module prefix
    parts = name.split(".")
    while parts:
        n = ".".join(parts)
        if n in mods: return n
        parts.pop()
    return None
def edges_of(name):
    p, isinit = mods[name]
    tree = ast.parse(open(p, encoding="utf-8").read())
    pk = name if isinit else ".".join(name.split(".")[:-1])
    out = []  # (target, kind) kind: top | func | typing
    def visit(node, ctx):
        for ch in ast.iter_child_nodes(node):
            c = ctx
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)): c = "func" if ctx == "top" else ctx
            if isinstance(ch, ast.If):
                t = ast.unparse(ch.test)
                if "TYPE_CHECKING" in t:
                    for b in ch.body: visit_one(b, "typing")
                    for b in ch.orelse: visit_one(b, ctx)
                    continue
            visit_one(ch, c)
    def visit_one(ch, c):
        if isinstance(ch, ast.Import):
            for a in ch.names:
                if a.name.split(".")[0] == pkg and tgt(a.name[len(pkg)+1:]): out.append((tgt(a.name[len(pkg)+1:]), c))
        elif isinstance(ch, ast.ImportFrom):
            if ch.level:
                base = pk.split(".") if pk else []
                base = base[:len(base) - (ch.level - 1)] if ch.level > 1 else base
                full = ".".join(base + ([ch.module] if ch.module else []))
            else:
                if not ch.module or ch.module.split(".")[0] != pkg: return
                full = ch.module[len(pkg)+1:] if ch.module != pkg else ""
            for a in ch.names:
                cand = (full + "." + a.name).strip(".")
                t = tgt(cand) if (cand in mods or tgt(cand) not in (None, "")) and cand in mods else tgt(full) if full else None
                if cand in mods: t = cand
                if t: out.append((t, c))
        else:
            visit(ch, c)
    visit(tree, "top")
    return out
E = {m: edges_of(m) for m in mods}
def scc(nodes, adj):
    idx = {}; low = {}; st = []; on = set(); res = []; i = [0]
    sys.setrecursionlimit(10000)
    def sc(v):
        idx[v] = low[v] = i[0]; i[0] += 1; st.append(v); on.add(v)
        for w in adj.get(v, ()):
            if w not in idx: sc(w); low[v] = min(low[v], low[w])
            elif w in on: low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v: break
            res.append(sorted(comp))
    for v in nodes:
        if v not in idx: sc(v)
    return [c for c in res if len(c) > 1]
def build(kinds, parents):
    adj = {}
    for m, es in E.items():
        for t, k in es:
            if k in kinds and t != m:
                adj.setdefault(m, set()).add(t)
                if parents:
                    parts = t.split(".")
                    for n in range(1, len(parts)):
                        pp = ".".join(parts[:n])
                        if pp in mods and pp != m: adj.setdefault(m, set()).add(pp)
    return adj
print("modules", len(mods), "edges(top/func/typing)", {k: sum(1 for es in E.values() for t, kk in es if kk == k) for k in ("top", "func", "typing")})
for label, kinds in (("top only", {"top"}), ("top+func", {"top", "func"}), ("top+typing", {"top", "typing"}), ("all (top+func+typing)", {"top", "func", "typing"})):
    for parents in (False, True):
        cs = scc(list(mods), build(kinds, parents))
        print("%-22s counting %s: %d groups, sizes %s" % (label, "B(parents)" if parents else "A(explicit)", len(cs), [len(c) for c in cs]))
        for c in cs: print("    ", c)

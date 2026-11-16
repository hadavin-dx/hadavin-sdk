"""EVIDENCE RUNNER: AST import graph of src/hadavin_sdk. Read-only. usage: python -I import_graph.py <src_root>"""
import ast, os, sys
root = sys.argv[1]; pkg = "hadavin_sdk"
mods = {}
for d, _, fs in os.walk(os.path.join(root, pkg)):
    if "__pycache__" in d: continue
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(d, f); rel = os.path.relpath(p, root)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"): rel = rel[:-9]
            mods[rel] = p
def resolve(name):
    while name:
        if name in mods: return name
        name = name.rpartition(".")[0]
    return None
def edges(mode):
    g = {m: set() for m in mods}
    for m, p in mods.items():
        t = ast.parse(open(p, encoding="utf-8").read())
        is_pkg = p.endswith("__init__.py")
        base = m if is_pkg else m.rpartition(".")[0]
        def visit(node, top):
            for ch in ast.iter_child_nodes(node):
                nested = top and not isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                if isinstance(ch, ast.Import):
                    for a in ch.names:
                        if a.name.startswith(pkg) and (mode == "all" or top): add(m, a.name)
                elif isinstance(ch, ast.ImportFrom):
                    if ch.level:
                        parts = base.split(".")
                        if ch.level > 1: parts = parts[: len(parts) - (ch.level - 1)]
                        b = ".".join(parts) + ("." + ch.module if ch.module else "")
                    else: b = ch.module or ""
                    if b.startswith(pkg) and (mode == "all" or top):
                        add(m, b)
                        for a in ch.names: add(m, b + "." + a.name, only_mod=True)
                if isinstance(ch, ast.If) and "TYPE_CHECKING" in ast.dump(ch.test) and mode == "runtime":
                    for o in ch.orelse: visit(ast.Module(body=[o], type_ignores=[]), top)
                    continue
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)): visit(ch, False)
                elif isinstance(ch, ast.ClassDef): visit(ch, False)
                else: visit(ch, top)
        def add(src, name, only_mod=False):
            if only_mod and name not in mods: return
            r = resolve(name)
            if r and r != src: g[src].add(r)
        visit(t, True)
    return g
def scc(g):
    idx = {}; low = {}; st = []; on = set(); out = []; c = [0]
    sys.setrecursionlimit(10000)
    def sc(v):
        idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
        for w in sorted(g[v]):
            if w not in idx: sc(w); low[v] = min(low[v], low[w])
            elif w in on: low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v: break
            if len(comp) > 1: out.append(sorted(comp))
    for v in sorted(g):
        if v not in idx: sc(v)
    return out
print("modules:", len(mods))
for mode in ("all", "toplevel", "runtime"):
    g = edges(mode)
    print(f"== mode={mode} edges={sum(len(v) for v in g.values())}")
    comps = scc(g)
    print("cycles (strongly connected sets of size>=2):", len(comps))
    for c in comps: print("  ", c, "| contains llm.*:", any(x.startswith("hadavin_sdk.llm") for x in c))
    for a, b in (("hadavin_sdk.llm.common", "hadavin_sdk.llm.gate"), ("hadavin_sdk.llm.retry", "hadavin_sdk.llm.protocol")):
        print("  edge", a, "->", b, b in g.get(a, ()), "| reverse", a in g.get(b, ()))

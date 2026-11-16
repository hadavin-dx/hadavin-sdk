"""Read-only AST import-graph check for hand-off v8 (builder's own check, not the runner's evidence).
usage: python -I import_graph_v8.py <src_root>
1. Builds the real top-level import graph of hadavin_sdk (module-import-time edges only, TYPE_CHECKING bodies
   excluded, function-level imports excluded) and lists today's cycles.
2. Overlays the PLANNED edges of hand-off v8 section 4.2 (new modules llm.spend, llm.gate, llm.metered, llm.build,
   store.amounts and the new imports of existing modules) and lists every cycle that contains a planned module
   or an existing module whose imports change.
3. Overlays the v6 shape (llm.gate imports llm.common) to show the contrast.
Changes nothing; prints only."""
import ast, os, sys

root = sys.argv[1]; pkg = "hadavin_sdk"
mods = {}
for d, _, fs in os.walk(os.path.join(root, pkg)):
    if "__pycache__" in d:
        continue
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(d, f); rel = os.path.relpath(p, root)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"):
                rel = rel[:-9]
            mods[rel] = p

def resolve(name, known):
    while name:
        if name in known:
            return name
        name = name.rpartition(".")[0]
    return None

def toplevel_graph():
    g = {m: set() for m in mods}
    for m, p in mods.items():
        tree = ast.parse(open(p, encoding="utf-8").read())
        is_pkg = p.endswith("__init__.py")
        base = m if is_pkg else m.rpartition(".")[0]
        def walk(body):
            for node in body:
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.startswith(pkg):
                            add(m, a.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        parts = base.split(".")
                        if node.level > 1:
                            parts = parts[: len(parts) - (node.level - 1)]
                        b = ".".join(parts) + ("." + node.module if node.module else "")
                    else:
                        b = node.module or ""
                    if b.startswith(pkg):
                        add(m, b)
                        for a in node.names:
                            if b + "." + a.name in mods:
                                add(m, b + "." + a.name)
                elif isinstance(node, ast.If):
                    if "TYPE_CHECKING" in ast.dump(node.test):
                        walk(node.orelse)
                    else:
                        walk(node.body); walk(node.orelse)
                elif isinstance(node, (ast.Try,)):
                    walk(node.body)
                    for h in node.handlers: walk(h.body)
                    walk(node.orelse); walk(node.finalbody)
        def add(src, name):
            r = resolve(name, mods)
            if r and r != src:
                g[src].add(r)
        walk(tree.body)
    return g

def scc(g):
    idx = {}; low = {}; st = []; on = set(); out = []; c = [0]
    sys.setrecursionlimit(10000)
    def sc(v):
        idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
        for w in sorted(g[v]):
            if w not in idx:
                sc(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                out.append(sorted(comp))
    for v in sorted(g):
        if v not in idx:
            sc(v)
    return out

P = pkg + "."
PLANNED = {  # module -> modules it imports at import time, per v8 section 4.2 table
    "llm.spend": ["models", "llm.protocol"],
    "llm.gate": ["llm.spend", "llm.protocol", "models"],
    "llm.metered": ["llm.gate", "llm.spend", "llm.protocol", "llm.common", "defaults"],
    "llm.build": ["backends.factory", "config", "llm.metered"],
    "store.amounts": [],
    "llm.common": ["llm.gate", "llm.spend", "llm.protocol", "llm.retry", "models"],
    "llm.retry": ["llm.protocol"],
    "limits": ["llm.spend", "llm.gate", "store.protocol", "store.amounts", "config", "models", "registry"],
    "store.postgres": ["store.amounts", "store.protocol"],
    "store.memory": ["store.amounts", "store.protocol"],
    "runtime.agent_loop": ["limits", "llm.spend", "llm.metered", "llm.common", "llm.gate"],
    "app": ["llm.build", "llm.metered", "limits"],
    "guard.injection": ["llm.protocol"],
    "k1b.loop": ["llm.protocol", "llm.gate"],
    "cli": ["llm.build", "llm.gate", "limits"],
}
V6_EXTRA = {"llm.gate": ["llm.common"]}

def overlay(extra, drop_gate_common=False):
    g = toplevel_graph()
    for short, deps in extra.items():
        full = P + short
        g.setdefault(full, set())
        for d in deps:
            g[full].add(P + d); g.setdefault(P + d, set())
    return g

print("modules on disk:", len(mods))
g0 = toplevel_graph()
print("== today (top-level edges): edges=%d" % sum(len(v) for v in g0.values()))
for c in scc(g0):
    print("  cycle:", c)
g1 = overlay(PLANNED)
print("== v8 planned overlay: edges=%d" % sum(len(v) for v in g1.values()))
touch = {P + k for k in PLANNED}
bad = 0
for c in scc(g1):
    hit = sorted(set(c) & touch)
    print("  cycle:", c, "| contains a planned or changed module:", hit)
    if hit and set(c) not in [set(x) for x in scc(g0)]:
        bad += 1
print("  NEW or CHANGED cycles caused by the v8 shape:", bad)
g2 = overlay(PLANNED); g2.setdefault(P + "llm.gate", set()).add(P + "llm.common")
print("== v6 shape (llm.gate imports llm.common):")
for c in scc(g2):
    if any(x.startswith(P + "llm.") for x in c):
        print("  cycle:", c)

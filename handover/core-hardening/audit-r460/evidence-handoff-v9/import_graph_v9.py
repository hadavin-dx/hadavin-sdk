"""Read-only AST import-graph check for hand-off v9 (author's own check, not the runner's evidence).
usage: python -I import_graph_v9.py <src_root> --table <file with PLANNED-EDGES markers> [--diff <other file>]
1. Builds the real import graph of hadavin_sdk twice: (a) run-time edges only (TYPE_CHECKING bodies skipped),
   (b) run-time plus TYPE_CHECKING edges. Function-level imports are not edges. Lists today's cycles for both.
2. Reads the planned-edges table from the file between the lines PLANNED-EDGES-BEGIN and PLANNED-EDGES-END
   (columns: module | run-time imports | type-only imports) and overlays it on both graphs.
3. Reports every cycle that is new, or that contains a planned module and did not exist today.
4. With --diff, extracts the same table from a second file and prints the differences (exit 1 if any).
Changes nothing; prints only. Exit 1 when a new cycle appears or the tables differ."""
import ast, os, re, sys

def table_of(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"PLANNED-EDGES-BEGIN[^\n]*\n(.*?)\n[^\n]*PLANNED-EDGES-END", txt, re.S)
    if not m:
        sys.exit("no PLANNED-EDGES markers in " + path)
    out = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] in ("module",) or set(cells[0]) <= set("-"):
            continue
        rt = [x.strip() for x in cells[1].split(",") if x.strip()]
        tc = [x.strip() for x in cells[2].split(",")] if len(cells) > 2 else []
        out[cells[0]] = (sorted(rt), sorted(x for x in tc if x))
    return out

args = sys.argv[1:]
root = args[0]
table = table_of(args[args.index("--table") + 1])
pkg = "hadavin_sdk"
mods = {}
for d, _, fs in os.walk(os.path.join(root, pkg)):
    if "__pycache__" in d:
        continue
    for f in fs:
        if f.endswith(".py"):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"):
                rel = rel[:-9]
            mods[rel] = p

def resolve(name):
    while name:
        if name in mods:
            return name
        name = name.rpartition(".")[0]
    return None

def graph(with_tc):
    g = {m: set() for m in mods}
    for m, p in mods.items():
        tree = ast.parse(open(p, encoding="utf-8").read())
        base = m if p.endswith("__init__.py") else m.rpartition(".")[0]
        def add(name):
            r = resolve(name)
            if r and r != m:
                g[m].add(r)
        def walk(body):
            for node in body:
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.startswith(pkg):
                            add(a.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        parts = base.split(".")
                        if node.level > 1:
                            parts = parts[: len(parts) - (node.level - 1)]
                        b = ".".join(parts) + ("." + node.module if node.module else "")
                    else:
                        b = node.module or ""
                    if b.startswith(pkg):
                        add(b)
                        for a in node.names:
                            if b + "." + a.name in mods:
                                add(b + "." + a.name)
                elif isinstance(node, ast.If):
                    if "TYPE_CHECKING" in ast.dump(node.test):
                        if with_tc:
                            walk(node.body)
                        walk(node.orelse)
                    else:
                        walk(node.body); walk(node.orelse)
                elif isinstance(node, ast.Try):
                    walk(node.body)
                    for h in node.handlers:
                        walk(h.body)
                    walk(node.orelse); walk(node.finalbody)
        walk(tree.body)
    return g

def scc(g):
    idx, low, st, on, out, c = {}, {}, [], set(), [], [0]
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
def overlay(g0, with_tc):
    g = {k: set(v) for k, v in g0.items()}
    for short, (rt, tc) in table.items():
        full = P + short
        g.setdefault(full, set())
        for d in rt + (tc if with_tc else []):
            g[full].add(P + d); g.setdefault(P + d, set())
    return g

bad = 0
print("modules on disk:", len(mods), "| planned rows:", len(table))
missing = [P + k for k in table if (P + k) not in mods]
print("planned modules not on disk yet (new):", sorted(m[len(P):] for m in missing))
for label, with_tc in (("run-time edges only", False), ("run-time plus TYPE_CHECKING edges", True)):
    g0 = graph(with_tc)
    today = [set(c) for c in scc(g0)]
    print("== today, %s: edges=%d cycles=%d" % (label, sum(len(v) for v in g0.values()), len(today)))
    for c in scc(g0):
        print("  cycle:", c)
    g1 = overlay(g0, with_tc)
    after = scc(g1)
    print("== planned overlay, %s: edges=%d cycles=%d" % (label, sum(len(v) for v in g1.values()), len(after)))
    touch = {P + k for k in table}
    for c in after:
        new = set(c) not in today
        print("  cycle:", c, "| new:", new, "| planned modules in it:", sorted(set(c) & touch))
        if new:
            bad += 1
print("NEW cycles caused by the planned table (both countings):", bad)
if "--diff" in args:
    other = table_of(args[args.index("--diff") + 1])
    diffs = [k for k in sorted(set(table) | set(other)) if table.get(k) != other.get(k)]
    print("== table diff (document vs --diff file): %d differing rows" % len(diffs))
    for k in diffs:
        print("  ", k, "| doc:", table.get(k), "| other:", other.get(k))
    bad += len(diffs)
sys.exit(1 if bad else 0)

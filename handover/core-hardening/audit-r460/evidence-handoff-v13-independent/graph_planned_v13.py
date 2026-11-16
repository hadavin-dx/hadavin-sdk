"""Independent planned-edge merge for hand-off v13 (own code, reads files only).
usage: python -I graph_planned_v13.py <src-root> <doc.md>
Reuses the graph builder of r2_graph_v13.py (everything before its print loop), then ADDS the rows of the
PLANNED-EDGES table (additive merge, the document's own rule) and prints the groups around package llm."""
import sys, re
src = open(__file__.replace("graph_planned_v13.py", "r2_graph_v13.py"), encoding="utf-8").read().split('print("modules"')[0]
sys.argv = [sys.argv[0], sys.argv[1]] + sys.argv[2:]
doc = sys.argv[2]
ns = {"__file__": "x"}
exec(compile(src, "r2_graph_v13", "exec"), ns)
mods, E, scc, build = ns["mods"], ns["E"], ns["scc"], ns["build"]
txt = open(doc, encoding="utf-8").read()
tab = txt.split("<!-- PLANNED-EDGES-BEGIN -->")[1].split("<!-- PLANNED-EDGES-END -->")[0]
rows = []
for l in tab.strip().split("\n")[2:]:
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    mod = c[0].strip("`")
    rt = [x.strip().strip("`") for x in c[1].split(",") if x.strip()]
    ty = [x.strip().strip("`") for x in c[2].split(",") if x.strip()]
    rows.append((mod, rt, ty))
print("planned rows:", len(rows), "new modules (no file today):", [m for m, _, _ in rows if m not in mods])
for label, keep_func in (("additive merge", True),):
    for m, rt, ty in rows:
        mods.setdefault(m, (None, False)); E.setdefault(m, [])
        for t in rt: E[m].append((t, "top")); mods.setdefault(t, (None, False)); E.setdefault(t, [])
        for t in ty: E[m].append((t, "typing")); mods.setdefault(t, (None, False)); E.setdefault(t, [])
for label, kinds in (("top only", {"top"}), ("top+typing (B reading in the doc)", {"top", "typing"}), ("all", {"top", "func", "typing"})):
    for parents in (False, True):
        cs = scc(list(mods), build(kinds, parents))
        print("%-34s %s: sizes %s" % (label, "B(parents)" if parents else "A(explicit)", sorted([len(c) for c in cs], reverse=True)))
        for c in cs: print("    ", len(c), c)

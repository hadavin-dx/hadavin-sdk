import sys, importlib.util, io, contextlib
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    spec=importlib.util.spec_from_file_location('cyc','cycles_v14_from_independent.py'); cyc=importlib.util.module_from_spec(spec); spec.loader.exec_module(cyc)
P=cyc.PKG
def graph(kinds, parents, extra):
    g=cyc.build(kinds,parents)
    g={k:set(v) for k,v in g.items()}
    for s,d,k in extra:
        if k in kinds:
            g.setdefault(s,set()).add(d); g.setdefault(d,set())
            if parents:
                for a in cyc.ancestors(d):
                    if a in cyc.mods and a!=s: g[s].add(a)
    return g
kinds={"run","type"}
base=cyc.scc(graph(kinds,True,[]))
print("today B run+type groups sizes",[len(c) for c in base])
full=cyc.scc(graph(kinds,True,cyc.planned))
print("with all planned:",[len(c) for c in full])
# which single planned edge alone changes the groups?
for e in cyc.planned:
    r=cyc.scc(graph(kinds,True,[e]))
    if sorted(map(len,r))!=sorted(map(len,base)):
        print("single edge changes groups:", e[0].replace(P+'.',''),"->",e[1].replace(P+'.',''),e[2],[len(c) for c in r])
# same, counting A (only explicit) run+type, but with the `from X import Y` => also edge to X (the other reading of A)

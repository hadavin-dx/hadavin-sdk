import sys,pathlib,re,ast
root=pathlib.Path(sys.argv[1]); sys.path[:0]=[str(root/"src"),str(root/"tests"),str(root)]
import conftest
T=root/"tests"
ENV=re.compile(r"\benv\.(rig|fakes|serve)\b")
def why(f,seen=()):
    text=f.read_text(encoding="utf-8"); r=[]
    m=sorted(set(x.group(1) for x in ENV.finditer(text)))
    tree=ast.parse(text)
    dm=set();bound=set();imp=set()
    for n in ast.walk(tree):
        mods=[]
        if isinstance(n,ast.ImportFrom): mods=[n.module or ""]
        elif isinstance(n,ast.Import): mods=[a.name for a in n.names]
        for mm in mods:
            h=mm.split(".")[0]
            if h in("demo_only","edge_case_helpers"): dm.add(h)
            o=T/(h+".py")
            if h.startswith("test_") and o!=f and o.is_file() and conftest._needs_demo(o): imp.add(h)
        nm=[n.id] if isinstance(n,ast.Name) else [n.attr] if isinstance(n,ast.Attribute) else [a.name for a in n.names] if isinstance(n,ast.ImportFrom) else []
        for x in nm:
            if x in ("build_rig","DEMO_LEADFLOW"): bound.add(x)
    if dm: r.append("imports "+"/".join(sorted(dm)))
    if m: r.append("env."+"/".join(m)+" (rig or fakes of the demo)")
    if bound: r.append("uses "+"/".join(sorted(bound)))
    if imp: r.append("imports "+", ".join(sorted(imp))+" (needs the demo)")
    return "; ".join(r)
for f in sorted(T.glob("test_*.py")):
    if conftest._needs_demo(f): print(f"{f.name}\t{why(f)}")

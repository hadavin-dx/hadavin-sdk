# Reads the banned-name list at run time from the repo test; prints counts only.
import ast,sys,pathlib
R=pathlib.Path("/home/user/hadavin-sdk")
t=ast.parse((R/"tests/test_no_reference_material.py").read_text(encoding="utf-8"))
best=[]
for n in ast.walk(t):
    if isinstance(n,(ast.Assign,ast.AnnAssign)) and n.value is not None:
        try: v=ast.literal_eval(n.value)
        except Exception: continue
        if isinstance(v,(list,tuple,set,frozenset)) and v and all(isinstance(x,str) for x in v) and len(v)>len(best): best=list(v)
print("list size:",len(best))
for root in sys.argv[1:]:
    cs=ci=files=0
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file() and ".git/" not in str(p):
            try: s=p.read_text(encoding="utf-8",errors="replace")
            except Exception: continue
            files+=1
            lo=s.lower()
            for w in best:
                cs+=s.count(w); ci+=lo.count(w.lower())
    print(root.split("/")[-1] or root,"files",files,"case-sensitive hits",cs,"case-insens hits",ci)

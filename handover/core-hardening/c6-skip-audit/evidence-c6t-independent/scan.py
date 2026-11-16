import re,os,sys,ast
O=sys.argv[1]
src=open("/home/user/hadavin-sdk/tests/test_no_reference_material.py",encoding="utf-8").read()
tree=ast.parse(src); B=None
for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and any(getattr(t,"id","")=="BANNED" for t in n.targets):
        B=ast.literal_eval(n.value)
B=[b for b in (B if not isinstance(B,dict) else B.keys())]
print("banned list size",len(B))
files=[]
for d,_,fs in os.walk(O):
    for f in fs: files.append(os.path.join(d,f))
tot=0;hit={}
for p in files:
    t=open(p,encoding="utf-8",errors="replace").read().lower()
    for i,b in enumerate(B):
        c=t.count(str(b).lower())
        if c: hit[(p,i)]=c; tot+=c
print("files scanned",len(files),"banned hits total",tot,"files with hits",len({k[0] for k in hit}))
for (p,i),c in list(hit.items())[:10]: print(" ",os.path.relpath(p,O),"banned#",i,c)
pats={"sk-key":r"sk-[A-Za-z0-9_-]{16,}","AKIA":r"AKIA[0-9A-Z]{16}","ghp":r"gh[pousr]_[A-Za-z0-9]{30,}","xox":r"xox[baprs]-[A-Za-z0-9-]{10,}","pat-hubspot":r"pat-[a-z0-9]{2,4}-[0-9a-f-]{20,}","privkey":r"-----BEGIN [A-Z ]*PRIVATE KEY","bearer":r"Bearer [A-Za-z0-9._-]{20,}","long-b64/hex40":r"\b[A-Fa-f0-9]{40,}\b","email":r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}"}
for k,pt in pats.items():
    n=0;fl=set();ex=set()
    for p in files:
        m=re.findall(pt,open(p,encoding="utf-8",errors="replace").read())
        if m: n+=len(m); fl.add(os.path.basename(p))
        for x in m: ex.add(x[:6]+"..." if k!="email" else x.split("@")[1])
    print("secret-like",k,"matches",n,"files",len(fl), sorted(ex)[:4] if k=="email" else "")

import csv, os, re, sys
repo="/home/user/hadavin-sdk"; adir=repo+"/handover/core-hardening/audit-r460"
rows=[r for r in csv.DictReader(open(adir+"/evidence-handoff-v15/cites-v15.tsv"), delimiter="\t") if r["status"]=="MOVED"]
print(len(rows), file=sys.stderr)
files={}
for top in ("src","tests","demos",".github"):
    for d,ds,fs in os.walk(os.path.join(repo,top)):
        ds[:]=[x for x in ds if x not in("__pycache__",)]
        for f in fs: files[os.path.relpath(os.path.join(d,f),repo)]=1
def res(n):
    c=[r for r in files if r==n or r.endswith("/"+n)]; return ([r for r in c if r.startswith("src/hadavin_sdk/") or r.startswith("tests/")] or c)[0]
dl={}
for i,r in enumerate(rows,1):
    doc=r["doc"]; 
    if doc not in dl: dl[doc]=open(adir+"/"+doc,encoding="utf-8").read().split("\n")
    line=dl[doc][int(r["doc_line"])-1]; cite=r["cite"]; path,rng=cite.split(":",1)
    k=line.find(cite); ctx=line[max(0,k-230):k+len(cite)+120].replace("\n"," ")
    rel=res(path); L=open(repo+"/"+rel,encoding="utf-8",errors="replace").read().split("\n")
    lo,_,hi=rng.partition("-"); lo=int(lo); hi=int(hi or lo)
    print(f"### {i} {doc}:{r['doc_line']} {cite} -> {rel}\nDOC: ...{ctx}...")
    for ln in range(max(1,lo),min(len(L),hi)+1):
        if ln-lo<14: print(f"  {ln}: {L[ln-1][:150]}")

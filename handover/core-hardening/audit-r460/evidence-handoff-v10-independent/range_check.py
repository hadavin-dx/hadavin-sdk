#!/usr/bin/env python3
"""For each citation: file exists, a<=b<=file length, and a heuristic content hit:
some identifier-like word from the same doc line (not a file name) occurs in the cited lines."""
import json, re, os
ROOT="/home/user/hadavin-sdk/"
AUD=ROOT+"handover/core-hardening/audit-r460/"
cites=json.load(open("cites.json"))
docl={}
for d in {c["doc"] for c in cites}:
    docl[d]=open(AUD+d,encoding="utf-8").read().split("\n")
cache={}
def lines(p):
    if p not in cache: cache[p]=open(ROOT+p,encoding="utf-8",errors="replace").read().split("\n")
    return cache[p]
STOP=set("with this that from have which they there their these those more than when will into only also does done what each every call calls file files line lines test tests kind kinds code data none true false path text read same used uses used step both then must such other about after before were been once name names list lists case cases count value values rule rules new one two three four five six seven eight nine ten the and for not are but can all any may src hadavin_sdk llm store guard demos".split())
rows=[]
bad=0
for c in cites:
    p=c["path"]; L=lines(p); n=len(L)
    if L and L[-1]=="": n-=1
    okrange = 1<=c["a"]<=c["b"]<=n
    seg="\n".join(L[c["a"]-1:c["b"]]) if okrange else ""
    ctx=docl[c["doc"]][c["line"]-1]
    # words from backticks on the doc line
    words=set()
    for bt in re.findall(r"`([^`]+)`",ctx):
        if re.search(r"\.(py|sql|md|ya?ml|sh)\b",bt) and ":" in bt: 
            bt=re.sub(r"^[\w./-]+\.\w+:?[\d,-]*","",bt)
        for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}",bt):
            if w.lower() not in STOP: words.add(w)
    hit=[w for w in words if w in seg]
    rows.append(dict(c, n=n, okrange=okrange, hits=hit[:5], nwords=len(words)))
    if not okrange: bad+=1
json.dump(rows,open("range_rows.json","w"))
print("cites",len(rows),"out_of_range",bad)
for r in rows:
    if not r["okrange"]: print("OUT",r["doc"],r["line"],r["path"],r["a"],r["b"],"len",r["n"])
nohit=[r for r in rows if r["okrange"] and not r["hits"]]
print("no identifier hit:",len(nohit))

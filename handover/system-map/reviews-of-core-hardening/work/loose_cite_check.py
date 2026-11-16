import re,os,sys
snap="snap"; 
pat=re.compile(r'`?((?:src|demos|tests|docs|handover)/[\w./\-]+\.\w+|[\w\-]+(?:/[\w.\-]+)+\.(?:py|md|sql|toml|json|jsonl|yml|yaml)|[\w\-]+\.(?:py|md|sql|toml))[:`]*:(\d+)(?:-(\d+))?')
idx={}
for r,d,fs in os.walk(snap):
    for f in fs: idx.setdefault(f,[]).append(os.path.join(r,f))
def res(p):
    for pre in ("","src/hadavin_sdk/"):
        q=os.path.join(snap,pre+p)
        if os.path.isfile(q): return q
    c=[x for x in idx.get(os.path.basename(p),[]) if x.endswith(p)]
    return c[0] if len(c)==1 else (c if c else None)
tot=ok=nofile=amb=oor=0; bad=[]
for fn in sys.argv[1:]:
    for n,l in enumerate(open(fn,errors="replace"),1):
        for m in pat.finditer(l):
            tot+=1; p=m.group(1); r=res(p)
            if r is None: nofile+=1; bad.append((fn[-20:],n,p,"NOFILE")); continue
            if isinstance(r,list): amb+=1; continue
            nl=sum(1 for _ in open(r,errors="replace")); ln=int(m.group(3) or m.group(2))
            if ln>nl: oor+=1; bad.append((fn[-20:],n,p+":"+m.group(2),f"OUTOFRANGE {nl}"))
            else: ok+=1
print(tot,ok,nofile,amb,oor)
for b in bad[:60]: print(b)

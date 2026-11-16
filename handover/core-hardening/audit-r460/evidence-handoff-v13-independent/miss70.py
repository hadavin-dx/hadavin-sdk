import pickle,re,sys
B="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/evidence-handoff-v13/cites-table.tsv"
R="/home/user/hadavin-sdk/"
L=open(B,encoding="utf-8").read().split("\n")[1:]
rows=[l.split("\t") for l in L if "ANCHOR-MISS" in l]
print(len(rows))
docs={d:open("docs/"+d,encoding="utf-8").read().split("\n") for d in ("CORE-PR-HANDOFF-v13.md",)}
out=[]
for i,r in enumerate(rows):
    doc,dl,f,a,b,res=r[:6]
    a=int(a);b=int(b)
    try: src=open(R+f,encoding="utf-8",errors="replace").read().split("\n")
    except Exception: src=[]
    txt=" | ".join(x.strip() for x in src[a-1:min(b,a+2)])[:110] if 1<=a<=len(src) else "(past EOF)"
    line=docs[doc][int(dl)-1]
    short=f.split("/")[-1]
    pos=line.find(short+":"+str(a))
    if pos<0: pos=line.find(short)
    claim=line[max(0,pos-110):pos].replace("\n"," ")
    out.append((i,doc,dl,f,a,b,res,claim,txt))
    print("%d|L%s|%s:%d-%d|%s => %s"%(i,dl,f.replace("src/hadavin_sdk/",""),a,b,claim[-80:],txt))
pickle.dump(out,open("miss70.pkl","wb"))

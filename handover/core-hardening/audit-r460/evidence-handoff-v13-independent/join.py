import csv,pickle,re,collections
B="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/evidence-handoff-v13/cites-table.tsv"
b=[r for r in csv.DictReader(open(B),delimiter="\t")]
miss=[r for r in b if r["result"].startswith("ANCHOR-MISS")]
print(len(miss),"builder ANCHOR-MISS rows;", len({(r['doc'],r['doc_line'],r['file'],r['from'],r['to']) for r in miss}),"distinct")
out=pickle.load(open("classA.pkl","rb"))
rows=[r for r in csv.DictReader(open("out1/cites-table.tsv"),delimiter="\t") if r["class"]=="A"]
idx=collections.defaultdict(list)
for i,(o,r) in enumerate(zip(out,rows)):
    doc,ln=o[0].rsplit(":",1)
    path,rng=o[1].rsplit(":",1)
    a,bb=(rng.split("-")+[rng])[:2] if "-" in rng else (rng,rng)
    idx[(doc,ln,o[3],a,bb)].append(i)
res=[]
for r in miss:
    k=(r["doc"],r["doc_line"],r["file"],r["from"],r["to"])
    ids=idx.get(k)
    res.append((r,ids))
    if not ids: print("NO JOIN",k)
pickle.dump(res,open("miss.pkl","wb"))
c=collections.Counter()
for r,ids in res:
    if ids:
        for i in ids: c[rows[i]["note"] or rows[i]["status"]]+=1
print(c)

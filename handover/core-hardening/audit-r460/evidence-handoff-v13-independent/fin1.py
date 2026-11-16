import csv,re,pickle
R="/home/user/hadavin-sdk/"
rows=list(csv.DictReader(open("out1/cites-table.tsv"),delimiter="\t"))
out=[]
for r in rows:
    if r["class"]!="A": continue
    cite=r["claim"].split(" :: ")[0]
    m=re.match(r"(.*):(\d+)(?:-(\d+))?$",cite)
    a,b=int(m.group(2)),int(m.group(3) or m.group(2))
    t=r["target"]
    try:
        L=open(R+t,encoding="utf-8",errors="replace").read().split("\n")
        txt=" | ".join(x.strip() for x in L[a-1:min(b,a+2)])[:200] if 1<=a<=len(L) else "(past EOF len %d)"%len(L)
    except Exception: txt="(unreadable)"
    out.append((r["cited_at"],cite,r["claim"].split(" :: ",1)[1],t,r["status"],r["what_is_actually_there"],txt))
pickle.dump(out,open("classA.pkl","wb"))
for i,o in enumerate(out):
    if o[4]!="MATCH": print(i,o[0],o[1],"||",o[2],"||",o[5],"||",o[6]);print()

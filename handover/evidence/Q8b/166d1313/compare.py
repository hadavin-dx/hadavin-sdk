import json, sys, collections
R="/home/user/build/evidence-raw/Q8bb10-166d1313/"
h=json.load(open(R+"8-probe-wt.json")); o=json.load(open(R+"8-probe-wt-old.json")); m=json.load(open(R+"8-probe-wt-main.json"))
rows=[]
cat=lambda k:k.split("|")[0]
stat=collections.defaultdict(lambda: collections.Counter())
for k in h:
    rh,ro,rm=h[k]["readable"],o[k]["readable"],m[k]["readable"]
    c=cat(k)
    stat[c]["cells"]+=1
    if rh: stat[c]["readable_head"]+=1
    if ro: stat[c]["readable_c36"]+=1
    if rm: stat[c]["readable_main"]+=1
    if rh and not rm: stat[c]["head_readable_main_masked"]+=1
    if rh and rm: stat[c]["head_readable_also_main"]+=1
    if rm and not rh: stat[c]["main_readable_head_masked"]+=1
    if rh and not ro: stat[c]["head_readable_c36_masked"]+=1
    rows.append((k,rh,ro,rm))
for c,s in stat.items(): print(c,dict(s))
with open(R+"8-probe-readable-on-head.tsv","w") as f:
    f.write("cell\thead_readable\tc36_readable\tmain_readable\n")
    for k,rh,ro,rm in rows:
        if rh: f.write(f"{k}\t{rh}\t{ro}\t{rm}\n")
print(sum(1 for r in rows if r[1]),"readable on head")

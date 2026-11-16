import json
ROOT="/home/user/hadavin-sdk/"
rows=json.load(open("range_rows.json"))
seen=set()
for r in rows:
    if r["okrange"] and not r["hits"]:
        k=(r["path"],r["a"],r["b"])
        if k in seen: continue
        seen.add(k)
        L=open(ROOT+r["path"],encoding="utf-8",errors="replace").read().split("\n")
        seg=L[r["a"]-1:r["b"]]
        print(f'## {r["path"].replace("src/hadavin_sdk/","")}:{r["a"]}-{r["b"]}  [{r["doc"][-8:-3]}#{r["line"]}]')
        if len(seg)>6: seg=seg[:3]+["   ..."]+seg[-2:]
        for i,s in enumerate(seg): print("   ",s[:130])

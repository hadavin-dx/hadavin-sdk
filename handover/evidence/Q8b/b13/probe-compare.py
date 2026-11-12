import json,sys,collections
for p in ("probe","probe12","probe_extra"):
    d={n:json.load(open(f"{p}-{n}.json")) for n in ("head","main","old")}
    tot={n:sum(1 for v in d[n].values() if v["readable"]) for n in d}
    hm=[k for k in d["head"] if d["head"][k]["readable"] and not d["main"].get(k,{"readable":True})["readable"]]
    om=[k for k in d["old"] if d["old"][k]["readable"] and not d["main"].get(k,{"readable":True})["readable"]]
    mh=[k for k in d["main"] if d["main"][k]["readable"] and not d["head"][k]["readable"]]
    print(p,"cells",len(d["head"]),"readable head/main/old",tot["head"],tot["main"],tot["old"],"| readable on head & masked on main:",len(hm),"| on old & masked on main:",len(om),"| readable on main & masked on head:",len(mh))
    kinds=collections.Counter(k.split("|")[0]+"|"+(k.split("|")[1] if "|" in k else "") for k in hm)
    json.dump(sorted(hm),open(f"{p}-head-readable-main-masked-cells.json","w"))
    print("   head-only cells by first two parts:",dict(list(kinds.items())[:8]))

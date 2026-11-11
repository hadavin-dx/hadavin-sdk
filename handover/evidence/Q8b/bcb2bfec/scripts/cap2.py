from lib import *
print("## import", path_src())
def mk(p, n): return {f"E{i:04d}": b64(f"zq{p}-{i:05d}-secretvalue") for i in range(n)}
# 3 Secrets of 200 entries: is the budget per Secret or shared?
secs = [{"kind": "Secret", "data": mk(p, 200)} for p in "abc"]
logs = [{"message": f"leak zq{p}-{i:05d}-secretvalue"} for p in "abc" for i in range(200)]
out = walk(secs + logs); t = [js(x) for x in out[3:]]
print("[CAP3 3 Secrets x 200] readable repeats:", sum(1 for k, (p, i) in enumerate([(p, i) for p in "abc" for i in range(200)]) if f"zq{p}-{i:05d}-secretvalue" in t[k]), "of 600")
# 300 values under one credential key (list)
vals = [f"zqlist-{i:05d}-secretvalue" for i in range(300)]
out = walk([{"passwords": vals}, {"message": " ".join(vals)}])
print("[CAP list under credential key, 300 items] readable in log:", sum(1 for v in vals if v in js(out[1])), "; list items readable under key:", sum(1 for v in vals if v in js(out[0])))
# one nested map of 300 under credential key
d = {f"k{i}": f"zqmap-{i:05d}-secretvalue" for i in range(300)}
out = walk([{"credentials": d}, {"message": " ".join(d.values())}])
print("[CAP map under credential key, 300 entries] readable in log:", sum(1 for v in d.values() if v in js(out[1])))
# the budget bypass: entries 257+ held back, same value as an earlier entry under a different key?
data = mk("z", 256); data["LATE"] = data["E0000"]
out = walk([{"kind": "Secret", "data": data}, {"message": "leak zqz-00000-secretvalue"}])
print("[CAP late entry same value as first] readable:", "zqz-00000-secretvalue" in js(out[1]))
# registered entries beyond cap, repeat in a second Secret's own data

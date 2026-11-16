import json, sys, collections
R = sys.argv[1]; name = sys.argv[2]
h = json.load(open(f"{R}/{name}-wt.json")); o = json.load(open(f"{R}/{name}-wt-old.json")); m = json.load(open(f"{R}/{name}-wt-main.json"))
stat = collections.defaultdict(collections.Counter); rows = []
for k in h:
    c = "|".join(k.split("|")[:1]); rh, ro, rm = h[k]["readable"], o[k]["readable"], m[k]["readable"]
    s = stat[c]; s["cells"] += 1
    s["head_readable"] += rh; s["old166_readable"] += ro; s["main_readable"] += rm
    s["head_readable_main_masked"] += (rh and not rm); s["main_readable_head_masked"] += (rm and not rh); s["head_readable_old_masked"] += (rh and not ro)
    if rh: rows.append((k, rh, ro, rm))
for c, s in stat.items(): print(c, dict(s))
with open(f"{R}/{name}-readable-on-head.tsv", "w") as f:
    f.write("cell\thead\told166\tmain\tin\tout\n")
    for k, rh, ro, rm in rows: f.write(f"{k}\t{rh}\t{ro}\t{rm}\t{h[k]['in']!r}\t{h[k]['out']!r}\n")
print(len(rows), "readable on head of", len(h))

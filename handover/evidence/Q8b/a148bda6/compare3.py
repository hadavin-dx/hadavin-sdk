"""Compare probe outputs head / 2153ad85 / main. usage: compare3.py <rawdir> <name> <heldfile>. Writes cell names only to stdout files;
readable input/output text goes to the HELD file outside the repo."""
import json, sys, collections, hashlib
R, name = sys.argv[1], sys.argv[2]
h, o, m = (json.load(open(f"{R}/{name}-{x}.json")) for x in ("wt", "wt-old", "wt-main"))
stat = collections.defaultdict(collections.Counter); hm = []
with open(f"{R}/{name}-held-readable-head-masked-main.txt", "w") as held:
    for k in h:
        c = k.split("|")[0]; rh, ro, rm = h[k]["readable"], o[k]["readable"], m[k]["readable"]
        s = stat[c]; s["cells"] += 1; s["head"] += rh; s["old2153"] += ro; s["main"] += rm
        s["head_and_main_masked_not"] += (rh and not rm); s["head_masked_main_readable"] += (rm and not rh); s["head_readable_old_masked"] += (rh and not ro)
        if rh and not rm:
            hm.append(k); held.write(f"{k}\tIN={h[k]['in']!r}\tOUT={h[k]['out']!r}\n")
for c, s in stat.items():
    print(c, dict(s))
with open(f"{R}/{name}-cells-readable-on-head-masked-on-main.txt", "w") as f:
    for k in hm:
        f.write(f"{k}\t{hashlib.sha256(h[k]['in'].encode()).hexdigest()[:10]}\n")
print("readable on head and masked on main:", len(hm), "of", len(h))

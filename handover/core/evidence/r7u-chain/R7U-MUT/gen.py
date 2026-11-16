import sys, glob, hashlib
sys.path.insert(0, "."); from mutants import M; from kmap import K
rows = {}
for fn in ["res1.tsv", "res2.tsv"]:
    for l in open(fn):
        p = l.rstrip("\n").split("\t"); rows[p[0]] = p
wide = {}
for fn in ["wide1.tsv", "wide2.tsv", "wide2a.tsv"]:
    try:
        for l in open(fn):
            p = l.rstrip("\n").split("\t"); wide[p[0]] = p
    except FileNotFoundError: pass
out = []; surv = []; stats = {"KILLED": 0, "SURVIVED": 0, "CRASH": 0, "NA": 0}
for mid, kind, f, old, new, exp, tests in M:
    r = rows.get(mid)
    if not r: out.append(f"| {mid} | | | {exp} | NOT RUN | |"); continue
    if "NOT-APPLIED" in r[2:3] or len(r) < 4: res = "NOT-APPLIED"; stats["NA"] += 1; loc = r[1]
    else:
        loc = r[1]; v = r[2]
        if v == "KILLED": res = "KILLED by " + r[4].split("::")[-1].rstrip("']")[:90]; stats["KILLED"] += 1
        elif v.startswith("ERR"): res = "CRASH (" + v + ", whole run aborted at start; counts as caught, no single test id)"; stats["CRASH"] += 1
        else:
            w = wide.get(mid)
            wtxt = "wide: not run" if not w else f"wide: {w[1]} {w[2]} {w[3] if w[1]=='KILLED' else w[4][:80]}"
            res = f"SURVIVED narrow ({tests and K[mid][1][:60]}); {wtxt}"; stats["SURVIVED"] += 1; surv.append((mid, loc, old, new, exp, w))
    eq = r[-2] if len(r) > 5 else r[-1]
    out.append(f"| {mid} | {loc} | {kind}: {old.strip()[:50]!r} -> {new.strip()[:50]!r} | {exp} | {res} | {'yes' if 'restored=True' in r[-2:] or 'restored=True' in '\t'.join(r) else 'NO'} |")
open("table.md", "w").write("\n".join(out)); 
with open("survivors.md", "w") as s:
    for mid, loc, old, new, exp, w in surv:
        s.write(f"### {mid} at {loc}\nexpected catcher: {exp}\nOLD:\n```\n{old}\n```\nNEW:\n```\n{new}\n```\nwide: {w}\n\n")
print(stats)

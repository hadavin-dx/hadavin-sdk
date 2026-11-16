import json, subprocess, sys, os
cases = json.load(open("/tmp/hd8i/h/cases-letters.json"))
shell = sys.argv[1]
res = []
for c in cases:
    t, v = c["text"], c["value"]
    if v and v not in t: v = t.split()[-1][-10:]
    r = subprocess.run([shell, "/tmp/hd8i/v8.sh", "--mask"], input=t.encode("utf-8", "replace"), capture_output=True, timeout=120)
    o = r.stdout.decode("utf-8", "replace")
    shown = bool(v) and v in o
    # partial: any 12-char window of value shown
    part = bool(v) and len(v) >= 12 and any(v[i:i+12] in o for i in range(0, len(v)-11, 6))
    res.append((c["id"], r.returncode, "SHOWN" if shown else ("PARTIAL" if part else "hidden"), len(v or ""), len(o)))
    print("%-28s exit=%s %s vlen=%s outlen=%s" % res[-1], flush=True)
print("TOTAL", len(res), "shown", sum(1 for r in res if r[2]=="SHOWN"), "partial", sum(1 for r in res if r[2]=="PARTIAL"), "nonzero-exit", sum(1 for r in res if r[1]!=0))

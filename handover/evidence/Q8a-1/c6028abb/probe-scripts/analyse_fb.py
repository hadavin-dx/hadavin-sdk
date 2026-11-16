import json, sys, xml.etree.ElementTree as ET, re, collections
R="/home/user/build/evidence-raw/Q8a1b11-c6028abb/"
ch=json.load(open(R+"4-changed-tests.json"))
changed={(f.split("/")[-1][:-3], t) for f,l in ch.items() for t in l}
def load(p):
    out=[]
    for tc in ET.parse(p).getroot().iter("testcase"):
        mod=tc.get("classname").split(".")[-1]; name=tc.get("name"); base=name.split("[")[0]
        st="passed"; first=""
        for k in ("failure","error","skipped"):
            e=tc.find(k)
            if e is not None:
                st="failed" if k!="skipped" else "skipped"
                txt=(e.get("message") or "")+"\n"+(e.text or "")
                lines=[l for l in txt.splitlines() if l.strip().startswith(("E ","E  ")) or "Error" in l]
                first=(lines[0].strip() if lines else txt.strip().splitlines()[0] if txt.strip() else "")[:160]
        out.append((mod,base,name,st,first))
    return out
for tag in sys.argv[1:]:
    rows=load(R+f"4-failbefore-{tag}.xml")
    print(f"== overlay on {tag}: total {len(rows)}; failed {sum(r[3]=='failed' for r in rows)}; passed {sum(r[3]=='passed' for r in rows)}")
    per=collections.OrderedDict()
    for mod,base,name,st,first in rows:
        if (mod,base) in changed:
            d=per.setdefault((mod,base),[0,0,""]); d[0 if st=="passed" else 1]+=1
            if st!="passed" and not d[2]: d[2]=first
    for (mod,base),(p,f,first) in per.items():
        print(f"  {'FAIL' if f and not p else ('MIXED' if f else 'pass')} {mod}::{base}  passed={p} failed={f}  {first}")
    # unchanged-name tests that failed (the data tables changed)
    other=[r for r in rows if r[3]=='failed' and (r[0],r[1]) not in changed]
    print("  failed tests NOT in the changed-function set:", len(other), collections.Counter((r[0],r[1]) for r in other).most_common(6))

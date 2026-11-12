import sys, xml.etree.ElementTree as ET, collections
def load(p):
    d={}
    for tc in ET.parse(p).getroot().iter("testcase"):
        k=tc.get("classname")+"::"+tc.get("name")
        d[k]="fail" if (tc.find("failure") is not None or tc.find("error") is not None) else ("skip" if tc.find("skipped") is not None else "pass")
    return d
h=load(sys.argv[1]); o=load(sys.argv[2])
fails=[k for k,v in o.items() if v=="fail"]
print("old failed:",len(fails))
for k in fails: print("  FAIL-ON-OLD",k)
byfile=collections.Counter()
passes=collections.defaultdict(list)
for k,v in o.items():
    if v=="pass":
        base=k.split("[")[0]; passes[base].append(k)
print("tests passing on old, grouped by function (count of rows):")
for b,l in sorted(passes.items()): print("  ",len(l),b)

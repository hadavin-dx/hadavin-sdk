import re, sys
S = r"(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)"
def parse(path):
    d = {}
    for ln in open(path, errors="replace"):
        ln = ln.rstrip("\n")
        m = re.match(r"^\[gw\d+\]\s+\[\s*\d+%\]\s+" + S + r"\s+(tests/.*?)\s*$", ln)
        if m: d[m.group(2)] = m.group(1); continue
        m = re.match(r"^(tests/.*?)\s+" + S + r"\s+\[\s*\d+%\]\s*$", ln)
        if m: d[m.group(1)] = m.group(2)
    return d
a, b = parse(sys.argv[1]), parse(sys.argv[2])
print("ids", len(a), len(b))
oa, ob = sorted(set(a) - set(b)), sorted(set(b) - set(a))
print("only in A:", len(oa), oa[:20]); print("only in B:", len(ob), ob[:20])
diff = {k: (a[k], b[k]) for k in a if k in b and a[k] != b[k]}
print("different outcome:", len(diff))
for k, v in sorted(diff.items()): print(" ", k, v)
from collections import Counter
print("A", dict(Counter(a.values())), "B", dict(Counter(b.values())))

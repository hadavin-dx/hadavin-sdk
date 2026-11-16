"""Reads BANNED at run time from tests/test_no_reference_material.py; prints counts only (never a banned string)."""
import re, sys
H = "/home/user/hadavin-sdk"
src = open(H + "/tests/test_no_reference_material.py", encoding="utf-8").read()
m = re.search(r"BANNED\s*=\s*(\(.*?\n\)|\[.*?\n\])", src, re.S)
B = list(eval(m.group(1)))
print("banned list size:", len(B))
for p in sys.argv[1:]:
    t = open(p, encoding="utf-8", errors="replace").read().lower()
    print("%s: %d of %d banned strings occur (total occurrences %d)" % (p.split("/")[-1], sum(1 for b in B if b.lower() in t), len(B), sum(t.count(b.lower()) for b in B)))

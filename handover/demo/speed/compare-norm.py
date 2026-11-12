"""throwaway: compare.py A.xml B.xml [C.xml...]  -> compares (id, outcome, skip reason / failure type) sets and counts of A vs each other."""
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def load(p):
    out, dup = {}, 0
    for tc in ET.parse(p).getroot().iter("testcase"):
        tid = (f"{tc.get('classname')}::{tc.get('name')}").replace("]@browser]", "]").replace("]@reset]", "]").replace("@browser", "").replace("@reset", "")
        o, d = "passed", ""
        for ch in tc:
            if ch.tag in ("skipped", "failure", "error"):
                o = ch.tag
                d = (ch.get("type") or "") if ch.tag != "skipped" else re.sub(r"'[^']*'", "'P'", ch.get("message") or "")
                if ch.tag == "skipped" and ch.get("type") == "pytest.xfail":
                    o = "xfailed"
        if tid in out:
            dup += 1
        out[tid] = (o, d)
    return out, dup


base, bd = load(sys.argv[1])
print(f"base {sys.argv[1]}: {len(base)} ids, dup {bd}", dict(Counter(v[0] for v in base.values())))
ok = True
for p in sys.argv[2:]:
    cur, cd = load(p)
    only_a, only_b = set(base) - set(cur), set(cur) - set(base)
    diff = [(k, base[k], cur[k]) for k in base if k in cur and base[k] != cur[k]]
    same = not (only_a or only_b or diff or bd != cd)
    ok &= same
    print(f"{p}: {len(cur)} ids, dup {cd}", dict(Counter(v[0] for v in cur.values())), "IDENTICAL" if same else "DIFFERENT")
    for k in sorted(only_a)[:10]:
        print("  only in base:", k)
    for k in sorted(only_b)[:10]:
        print("  only in other:", k)
    for k in diff[:10]:
        print("  changed:", k)
print("RESULT", "ALL IDENTICAL" if ok else "MISMATCH")
sys.exit(0 if ok else 1)

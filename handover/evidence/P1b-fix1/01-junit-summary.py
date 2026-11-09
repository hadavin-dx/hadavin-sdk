import sys, xml.etree.ElementTree as ET, collections
r = ET.parse(sys.argv[1]).getroot(); s = r if r.tag == "testsuite" else r[0]
print({k: s.get(k) for k in ("tests", "failures", "errors", "skipped", "time")})
by = collections.Counter(); rows = []
for tc in s.iter("testcase"):
    sk = tc.find("skipped")
    if sk is not None:
        m = (sk.get("message") or "")[:200]; by[m] += 1; rows.append(f"SKIPPED {tc.get('classname')}::{tc.get('name')} | {m}")
    for tag in ("failure", "error"):
        if tc.find(tag) is not None: rows.append(f"{tag.upper()} {tc.get('classname')}::{tc.get('name')}")
print("skip reasons (count, reason):")
for m, n in by.most_common(): print(f"  {n:4d}  {m}")
print("--- every skipped/failed test id ---"); print("\n".join(rows))

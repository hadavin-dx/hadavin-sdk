import sys, unicodedata
sys.path.insert(0, "src")
from hadavin_sdk.guard import textnorm as t
print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version, [n for n in dir(t) if "identity" in n or n in ("fold","same_person")])
ik = t.identity_key
bad_idem, bad_case = [], []
for cp in range(0x110000):
    if 0xD800 <= cp <= 0xDFFF: continue
    c = chr(cp)
    try:
        a = ik(c)
        if ik(a) != a: bad_idem.append(cp)
        u, l = c.upper(), c.lower()
        if u != l and ik(u) != ik(l): bad_case.append(cp)
    except Exception as e:
        bad_idem.append(("EXC", cp, type(e).__name__)); break
print("not idempotent:", len(bad_idem), [hex(x) if isinstance(x,int) else x for x in bad_idem[:25]])
print("case asymmetric:", len(bad_case), [hex(x) for x in bad_case[:25]])
print("same_person('BØB','bob'):", t.same_person("BØB","bob"), "| ik(Ø)=", repr(ik("Ø")), "ik(ø)=", repr(ik("ø")))

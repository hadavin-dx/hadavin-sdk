import sys, unicodedata
sys.path.insert(0, "src")
from hadavin_sdk.guard import textnorm as t
ik = t.identity_key
print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version)
print("admin+U+0345:", repr(ik("adminͅ")), "admin:", repr(ik("admin")), "same_person:", t.same_person("adminͅ", "admin"))
cats = {"Cc","Cf","Mn","Me","Zl","Zp","Co","Cn"}
bases = ["a","B","i","α","Α","k"]
bad_suffix, bad_prefix = [], []
for cp in range(0x110000):
    if 0xD800 <= cp <= 0xDFFF: continue
    c = chr(cp)
    if unicodedata.category(c) not in cats: continue
    for b in bases:
        if ik(b + c) != ik(b): bad_suffix.append((hex(cp), b)); break
    for b in bases:
        if ik(c + b) != ik(b): bad_prefix.append((hex(cp), b)); break
print("suffix breaks key:", len(bad_suffix), bad_suffix[:12])
print("prefix breaks key:", len(bad_prefix), bad_prefix[:12])

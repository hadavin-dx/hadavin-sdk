import sys, unicodedata
sys.path.insert(0, r"C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\pr63\src")
from hadavin_sdk.guard import textnorm as t
print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version)
cats = {}
for cp in range(0x110000):
    ch = chr(cp)
    c = unicodedata.category(ch)
    if c in ("Mc", "Lm", "Sk"):
        cats.setdefault(c, []).append(ch)
for c, chars in cats.items():
    hide_fold = hide_squeeze = hide_idkey = 0
    sample = []
    for ch in chars:
        s = "pass" + ch + "word"
        fv = t.fold_views(s)
        sv = t.squeeze_views(s)
        ik = t.identity_keys(s)
        a = any("password" in v for v in fv)
        b = any("password" in v for v in sv)
        k = any("password" == v.lstrip("\ue000") or "password" in v for v in ik)
        if not a: hide_fold += 1; sample.append(f"U+{ord(ch):04X}") if len(sample) < 6 else None
        if not b: hide_squeeze += 1
        if not k: hide_idkey += 1
    print(c, "count", len(chars), "| fold_views miss", hide_fold, "| squeeze_views miss", hide_squeeze, "| identity_keys miss", hide_idkey, "| sample", sample)
# visible Devanagari examples
for ch in ("\u093e", "\u093f", "\u0903"):
    s = "pass" + ch + "word"
    print(f"U+{ord(ch):04X}", unicodedata.category(ch), "fold_views", [v for v in t.fold_views(s)][:2], "squeeze_views", [v for v in t.squeeze_views(s)][:2])

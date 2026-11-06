"""Lead probe 3 (round 3 review claims F1 and F2). Prints raw facts only."""
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
from hadavin_sdk.guard import textnorm as tn  # noqa: E402

print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version)
names = [n for n in dir(tn) if not n.startswith("_")]
print("public:", names)

alpha = "α"  # Greek small alpha, a look-alike of Latin a
iota_sub = "ͅ"
hostile = alpha + iota_sub + "dmin"
plain = "admin"
for fn_name in ("identity_key", "fold", "squeeze"):
    fn = getattr(tn, fn_name, None)
    if fn is None:
        continue
    try:
        print(fn_name, "hostile ->", repr(fn(hostile)), "| plain ->", repr(fn(plain)))
    except Exception as exc:  # report, never hide
        print(fn_name, "raised", type(exc).__name__, exc)
sp = getattr(tn, "same_person", None)
if sp:
    print("same_person(hostile, plain) =", sp(hostile, plain))
    print("same_person(alpha+U+0345 omicron variant) =", sp("passwοͅrd", "password"))

# F2: how many look-alike table sources are unassigned (Cn) in this interpreter's Unicode version
import hadavin_sdk.guard._confusables as cf  # noqa: E402

table = None
for n in dir(cf):
    v = getattr(cf, n)
    if isinstance(v, dict) and len(v) > 100:
        table = (n, v)
        break
if table:
    name, d = table
    cn = [k for k in d if isinstance(k, str) and len(k) == 1 and unicodedata.category(k) == "Cn"]
    print("table", name, "entries", len(d), "single-char sources unassigned (Cn) here:", len(cn))
    print("examples:", [f"U+{ord(k):04X}" for k in cn[:8]])
else:
    print("no big dict found in _confusables:", [n for n in dir(cf) if not n.startswith("__")])

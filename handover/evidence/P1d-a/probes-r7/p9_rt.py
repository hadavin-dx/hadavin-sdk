"""P9: classify the round-trip failures. usage: PYTHONPATH=<tree>/src python p9_rt.py"""
import re, collections, sys
sys.argv = ["x", "B"]
exec(open("p9_props.py").read().split("which = ")[0])
PH = re.compile(r"<([A-Z][A-Z0-9]*)_\d+>")
def strip(s): return PH.sub("", s).replace("[.]", ".")
def subseq(a, b):
    it = iter(b); return all(ch in it for ch in a)
xs = gen("TXT-B", B, 2000)
n = 0; kinds = collections.Counter(); newk = collections.Counter(); other = []
for x in xs:
    c = channel.clean(x)
    if len(c) > 2900: continue
    n += 1; s = second(c)
    if s == c: continue
    if subseq(strip(s), strip(c)):
        kinds["more masking only"] += 1
        for k in set(PH.findall(s)) - set(PH.findall(c)): newk[k] += 1
        if "[.]" in c and "." in strip(s) and False: pass
    else:
        kinds["other"] += 1; other.append((x, c, s))
print("texts", n, dict(kinds), "new kinds", dict(newk))
for x, c, s in sorted(other, key=lambda t: len(t[0]))[:3]: print(repr(c), "\n ", repr(s))
# secrets shown on the second pass but masked on the first?
leak = [x for x in xs if SV_B in second(channel.clean(x)) and SV_B not in channel.clean(x)]
print("secret newly shown by the second pass:", len(leak))

import sys
sys.path.insert(0, "/home/user/build/prh-author/scratch")
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
import random; sys.path.insert(0, "/home/user/build/prh-author/main/tests")
import test_k5_round12_fuzz as F
rng = random.Random(F.SEED)
for i in range(791):
    text, parts, strict, tagged, base = F._case(rng)
    pool = [n for n in sorted(F.PRODUCERS) if n in {"clean", "slack"}] if tagged else sorted(F.PRODUCERS)
    rng.sample(pool, 1)
P1, P2 = parts
s0 = text.find("passw")
small = "note " + text[s0:text.find(P2) + len(P2)] + " end"
print("P1 shape:", "".join("a" if c.isalpha() else "9" if c.isdigit() else c for c in P1), "P2 shape:", "".join("a" if c.isalpha() else "9" if c.isdigit() else c for c in P2))
def short(t): return ascii(t.replace(P1, "[PART1]").replace(P2, "[PART2]"))
print("main clean:", short(channel.clean(small)))
import proto
d = P1 + "\x0b" + P2
print("neutralise(decoded):", short(channel._neutralise(d)))
print("strip(decoded)[0]:", short(proto.strip(d)[0]))
print("neutralise(strip(decoded)):", short(channel._neutralise(proto.strip(d)[0])))
print("strip(neutralise(decoded))[0]:", short(proto.strip(channel._neutralise(d))[0]))
orig = runmap._keep_earlier_masks
def kem(view, pairs):
    r = orig(view, pairs)
    if P2 in view: print("  keep_earlier_masks view:", short(view[view.find("passw"):]), "pairs:", [(p, short(x)) for p, x in pairs], "->", short(r[r.find("passw"):]))
    return r
proto.install()
runmap._keep_earlier_masks = kem
print("proto clean:", short(channel.clean(small)))

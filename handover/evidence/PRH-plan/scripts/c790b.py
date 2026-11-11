import sys, random, re
sys.path.insert(0, "/home/user/build/prh-author/scratch"); sys.path.insert(0, "/home/user/build/prh-author/main/tests")
import test_k5_round12_fuzz as F
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
rng = random.Random(F.SEED)
for i in range(791):
    text, parts, strict, tagged, base = F._case(rng)
    pool = [n for n in sorted(F.PRODUCERS) if n in {"clean", "slack"}] if tagged else sorted(F.PRODUCERS)
    rng.sample(pool, 1)
def short(t):
    for k, p in enumerate(parts): t = t.replace(p, f"[PART{k+1}]")
    return t
s = text.find("passw")
small = "note " + text[s:text.find(parts[1]) + len(parts[1])] + " end"
print("small:", ascii(short(small)))
print("main small clean:", ascii(short(channel.clean(small))))
m = channel._seeded(text); print("seeded entries", len(m))
o = channel.clean(text); print("main full: has PART2", parts[1] in o, ascii(short(o[o.find("passw")-5:o.find("passw")+40])))
import proto
proto.install()
print("proto small clean:", ascii(short(channel.clean(small))))
# trace views
orig_both = proto._both
def tr(text_, mapping, neutralise, cache, stats):
    r = orig_both(text_, mapping, neutralise, cache, stats)
    if parts[0] in text_ or "[PART" in short(text_):
        k = text_.find("passw"); print("  _both in:", ascii(short(text_[k:k+60])), "-> out:", ascii(short(r[0][r[0].find("passw"):r[0].find("passw")+50])))
    return r
proto._both = tr
o = channel.clean(text); print("proto full: has PART2", parts[1] in o)
for n in (3, 40, 100, 103, 120):
    junk = " , ".join(f"<IPV4_{k}>" for k in range(1, n + 1))
    t2 = "note " + junk + " , " + text[s:text.find(parts[1]) + len(parts[1])] + " end"
    print(n, "distinct junk placeholders: proto leaks PART2:", parts[1] in channel.clean(t2))

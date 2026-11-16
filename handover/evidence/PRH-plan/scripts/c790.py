"""Diagnose existing fuzz case 790 under the author prototype (made-up data from the seeded generator)."""
import sys, random
sys.path.insert(0, "/home/user/build/prh-author/scratch"); sys.path.insert(0, "/home/user/build/prh-author/main/tests")
import test_k5_round12_fuzz as F
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
rng = random.Random(F.SEED)
for i in range(F.CASES):
    text, parts, strict, tagged, base = F._case(rng)
    frags = F._fragments(parts, base)
    pool = [n for n in sorted(F.PRODUCERS) if n in {"clean", "slack"}] if tagged else sorted(F.PRODUCERS)
    pick = rng.sample(pool, 1)
    if i == 790: break
print("case", i, "strict", strict, "tagged", tagged, "producers", pick + ["clean"])
print("len", len(text), "parts lens", [len(p) for p in parts])
def short(t):
    t = t
    for k, p in enumerate(parts): t = t.replace(p, f"[PART{k+1}]")
    return t
import re
sec = re.search(r"(password|secret|api_key|passwd)\S*", text)
print("text around secret:", ascii(short(text[max(0,text.find(parts[1])-120):text.find(parts[1])+40])))
print("count <IPV4_ junk:", text.count("<IPV4_"), "distinct:", len(set(re.findall(r"<IPV4_\d+>", text))))
out_main = channel.clean(text)
print("MAIN clean: leaked", [f for f in frags if f in out_main][:3])
import proto
mode = sys.argv[1] if len(sys.argv) > 1 else "proto"
if mode == "maxv_big": proto.MAXV = 10**9
proto.install()
out = channel.clean(text)
lk = [f for f in frags if f in out]
print("PROTO(", mode, ") clean: leaked longest", max(lk, key=len)[:12] if lk else None, "n", len(lk))
seg = out[max(0, out.find(parts[1][-6:]) - 150): out.find(parts[1][-6:]) + 30] if lk else ""
print("out around leak:", ascii(short(seg)))
D, S = proto.strip(text)
print("strip changes text:", D != text, "D!=S:", D != S, "removed chars:", sorted({hex(ord(c)) for c in text if c not in D})[:10])

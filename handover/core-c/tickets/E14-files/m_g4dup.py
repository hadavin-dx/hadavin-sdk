import base64, random, sys
from hadavin_sdk.guard import runmap
rng = random.Random(11)
m = runmap.RunMap()
for i in range(6):
    size = rng.randint(30_000, 60_000)
    text = f"blob {i}: {base64.b64encode(rng.randbytes(size * 3 // 4)).decode()} end"
    runmap.redact_untrusted(text, m)
vals = list(m.values())
print("entries", len(m), "sum", sum(map(len, vals)), "set-sum", sum(map(len, set(vals))))
print(sorted((runmap.kind_of(p), len(v)) for p, v in m.items()))
R = sys.modules["hadavin_sdk.guard.redact"]
r = R._Redactor(dict(m)); r._build(); print("rules chars", sum(map(len, r._rules)))

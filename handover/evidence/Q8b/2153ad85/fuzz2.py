"""EVIDENCE RUNNER own fuzz for Q8b batch 11: wrapped and multi-cut headers with made-up secrets, split by shape
(A same line, B indented continuation, C unindented break). usage: fuzz2.py <src> N seed"""
import sys, random, json, collections
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard.redact import redact
N = int(sys.argv[2]); seed = int(sys.argv[3])
AL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SEPS = {"A": [" ", "  ", "\t"], "B": ["\n ", "\n  ", "\r\n\t", "\n\t", "\n    "], "C": ["\n", "\r\n", "\r", "\n\n"]}
SCH = ["Basic", "Token", "ApiKey", "Digest", "Bearer"]
KEYS = ["Authorization", "authorization", "Proxy-Authorization", "X-Api-Key", "token", "secret", "passwd"]
def sec(rnd, n):
    s = "".join(rnd.choice(AL) for _ in range(n))
    if rnd.random() < .3:
        i = rnd.randrange(1, n - 1); s = s[:i] + rnd.choice(".~:-") + s[i + 1:]
    return s
def gram(s, o, k=8):
    return [s[i:i + k] for i in range(len(s) - k + 1) if s[i:i + k] in o]
rnd = random.Random(seed); cnt = collections.Counter(); ex = collections.defaultdict(list)
for i in range(N):
    n = rnd.randint(16, 80); s = sec(rnd, n); k = rnd.randint(2, 5)
    cuts = sorted(rnd.sample(range(4, n - 3), min(k - 1, max(1, n - 8))))
    pieces = [s[a:b] for a, b in zip([0] + cuts, cuts + [n])]
    secs = [p for p in pieces if len(p) >= 8]
    shape = rnd.choice("ABC"); key = rnd.choice(KEYS); sc = rnd.choice(SCH)
    glue = "".join(p + rnd.choice(SEPS[shape]) for p in pieces[:-1]) + pieces[-1]
    t = f"{key}: {sc} {glue}\nnext line ok\n"
    o = redact(t).text
    r = [g for sx in secs for g in gram(sx, o)]
    tag = f"shape{shape}"
    cnt[tag + "_total"] += 1
    if r:
        cnt[tag + "_readable"] += 1
        cnt[f"{tag}|{sc}_readable"] += 1
        if len(ex[tag]) < 3: ex[tag].append({"in": t[:160], "out": o[:160]})
print(json.dumps({"counts": dict(sorted(cnt.items())), "examples": ex}))

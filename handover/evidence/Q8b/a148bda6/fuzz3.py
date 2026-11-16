"""EVIDENCE RUNNER own fuzz for Q8b batch 12: wrapped credential headers with made-up secrets built at run time, any scheme word or none,
0-4 extra first-line words, the break characters of group 4, shapes A (same line), B (indented), C (no indent). usage: fuzz3.py <src> N seed"""
import sys, random, json, collections
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard.redact import redact
N = int(sys.argv[2]); seed = int(sys.argv[3])
AL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BRK = ["\n", "\r\n", "\r", " ", " ", "\x0b", "\x0c", "\x85"]
SEPS = {"A": [" ", "  ", "\t"], "B": [" ", "  ", "\t", "    "], "C": [""]}
SCH = ["Basic", "Token", "ApiKey", "Digest", "Bearer", "NTLM", "Negotiate", "OAuth", "Splunk", "Hawk", "AWS", "Custom-X", ""]
KEYS = ["Authorization", "authorization", "Proxy-Authorization", "X-Api-Key", "token", "secret", "passwd"]
WORDS = ["x", "ok", "foo", "the", "a1", "word"]
def sec(rnd, n):
    s = "".join(rnd.choice(AL) for _ in range(n))
    if rnd.random() < .3:
        i = rnd.randrange(1, n - 1); s = s[:i] + rnd.choice(".~:-") + s[i + 1:]
    return s
def gram(s, o, k=8):
    return [s[i:i + k] for i in range(len(s) - k + 1) if s[i:i + k] in o]
rnd = random.Random(seed); cnt = collections.Counter()
for i in range(N):
    n = rnd.randint(16, 80); s = sec(rnd, n); k = rnd.randint(2, 5)
    cuts = sorted(rnd.sample(range(4, n - 3), min(k - 1, max(1, n - 8))))
    pieces = [s[a:b] for a, b in zip([0] + cuts, cuts + [n])]
    secs = [p for p in pieces if len(p) >= 8]
    shape = rnd.choice("ABC"); key = rnd.choice(KEYS); sc = rnd.choice(SCH)
    extra = " ".join(rnd.choice(WORDS) for _ in range(rnd.randint(0, 4))) if shape != "A" else ""
    if shape == "A":
        glue = "".join(p + rnd.choice(SEPS["A"]) for p in pieces[:-1]) + pieces[-1]
    else:
        b = rnd.choice(BRK)
        first = pieces[0] + ((" " + extra) if extra else "")
        glue = first + "".join(b + rnd.choice(SEPS[shape]) + p for p in pieces[1:])
    t = f"{key}: {(sc + ' ') if sc else ''}{glue}\nnext line ok\n"
    o = redact(t).text
    r = [g for sx in secs for g in gram(sx, o)]
    tag = f"shape{shape}"
    cnt[tag + "_total"] += 1
    if r:
        cnt[tag + "_readable"] += 1
        cnt[f"{tag}|{'scheme=' + sc if sc else 'no-scheme'}_readable"] += 1
print(json.dumps(dict(sorted(cnt.items()))))

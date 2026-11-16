import sys, random, json, collections
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard.redact import redact
N = int(sys.argv[2]); seed = int(sys.argv[3])
AL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SEPS = [" ", "  ", "\t", "\n", "\r\n", "\r", "\n  ", "\r\n\t", "\n\n"]
SCH = ["Basic", "Token", "ApiKey", "Digest", "Bearer"]
KEYS = ["Authorization", "authorization", "Proxy-Authorization", "X-Api-Key", "token", "secret", "passwd"]
def sec(rnd, n, lower=False):
    a = AL[:26] if lower else AL
    s = "".join(rnd.choice(a) for _ in range(n))
    if rnd.random() < .3:
        i = rnd.randrange(1, n - 1); s = s[:i] + rnd.choice(".~:-") + s[i + 1:]
    return s
def gram(s, o, k=8):
    return [s[i:i + k] for i in range(len(s) - k + 1) if s[i:i + k] in o]
rnd = random.Random(seed); cnt = collections.Counter(); ex = []
for i in range(N):
    kind = rnd.choice(["wrap", "multicut", "digest"])
    secs = []
    if kind == "wrap":
        n = rnd.randint(8, 64); s = sec(rnd, n, rnd.random() < .4); secs = [s]
        t = f"{rnd.choice(KEYS)}{rnd.choice([': ', '=', ' : '])}{rnd.choice(SCH)}{rnd.choice(SEPS)}{s}\nnext line ok\n"
    elif kind == "multicut":
        n = rnd.randint(16, 80); s = sec(rnd, n); k = rnd.randint(2, 5)
        cuts = sorted(rnd.sample(range(4, n - 3), min(k - 1, max(1, n - 8))))
        pieces = [s[a:b] for a, b in zip([0] + cuts, cuts + [n])]
        secs = [p for p in pieces if len(p) >= 8]
        glue = "".join(p + rnd.choice(SEPS) for p in pieces[:-1]) + pieces[-1]
        t = f"{rnd.choice(KEYS)}: {rnd.choice(SCH)} {glue}\n"
    else:
        parts = [sec(rnd, rnd.randint(16, 40)) for _ in range(rnd.randint(2, 4))]; secs = parts
        nl = rnd.choice(["\n", "\r\n"]); ind = rnd.choice([" ", "    ", "\t"])
        t = f'Authorization: Digest username="u",{nl}' + "".join(f'{ind}k{j}="{p}",{nl}' for j, p in enumerate(parts)) + f"{ind}qop=auth\n"
    o = redact(t).text
    r = [g for s in secs for g in gram(s, o)]
    cnt[kind + "_total"] += 1
    if r:
        cnt[kind + "_readable"] += 1
        if len(ex) < 5: ex.append({"kind": kind, "in": t[:200], "out": o[:200]})
print(json.dumps({"counts": cnt, "examples_head5": ex}))

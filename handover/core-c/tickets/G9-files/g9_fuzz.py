"""G9 v3 evidence, random search (`PYTHONHASHSEED=0`). argv: tree, n, seed, alphabet mode (abc | mixed), entry (redact | natural | gate).
abc: values of 4-7 letters over `abc`, words of 3-16 (v1's fuzz). mixed: a random 30-character base over [a-zA-Z0-9]; values are
random substrings of it of 8-14 characters; the text is 1-4 random substrings of the base of 8-30 characters (overlaps are frequent and
every piece is secret-shaped). redact: seeded map, R.redact. natural: no map, `password=<value>` lines then the text, R.redact_many.
gate: seeded map, runmap.enforce_map. Oracle: the output read back (every key put back); a stored value of 4+ characters whose
occurrence covers a readable character and part of a placeholder is a leak."""
import importlib, random, re, sys, string
from collections import Counter
tree, N, SEED, MODE, ENTRY = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
sys.path.insert(0, tree + "/src")
R = importlib.import_module("hadavin_sdk.guard.redact")
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
import g9_probe  # noqa: E402

g9_probe.install(R)
from hadavin_sdk.guard import runmap
TOK = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
def leaks(out, mapping, values):
    E, flags, last = [], [], 0
    for m in TOK.finditer(out):
        free = out[last:m.start()]; E.append(free); flags += [0] * len(free)
        v = mapping.get(m.group(), "\0"); E.append(v); flags += [1 if m.group() in mapping else 2] * len(v); last = m.end()
    E.append(out[last:]); flags += [0] * len(out[last:]); e = "".join(E); found = []
    for v in values:
        j = e.find(v)
        while j >= 0:
            f = flags[j:j + len(v)]
            if 0 in f and 1 in f and 2 not in f: found.append(v); break
            j = e.find(v, j + 1)
    return found
rng = random.Random(SEED)
stats, passes, ex = Counter(), Counter(), []
AL = string.ascii_letters + string.digits
for i in range(N):
    if MODE == "abc":
        values = sorted({"".join(rng.choice("abc") for _ in range(rng.randint(4, 7))) for _ in range(rng.randint(2, 5))})
        text = " ".join("".join(rng.choice("abc") for _ in range(rng.randint(3, 16))) for _ in range(rng.randint(1, 4)))
    else:
        base = "".join(rng.choice(AL) for _ in range(30))
        def sub(lo, hi):
            n = rng.randint(lo, hi); s = rng.randint(0, 30 - n); return base[s:s + n]
        values = sorted({sub(8, 14) for _ in range(rng.randint(2, 5))})
        text = " ".join(sub(8, 30) for _ in range(rng.randint(1, 4)))
    mapping = {f"<SECRET_{n + 1}>": v for n, v in enumerate(values)}
    g9_probe.reset()
    try:
        if ENTRY == "redact":
            res = R.redact(text, mapping=dict(mapping)); out, mp = res.text, res.mapping
            if res.restore(out) != text: stats["restore differs"] += 1
            if R.redact(out, mapping=dict(mp)).text != out: stats["second redact changes"] += 1
        elif ENTRY == "natural":
            outs, mp = R.redact_many([f"password={v}" for v in values] + [text]); out = outs[-1]
        else:
            out, mp = runmap.enforce_map(text, dict(mapping)), mapping
    except Exception as exc:
        stats["refused " + type(exc).__name__ + " " + str(exc)] += 1; continue
    passes.update(g9_probe.STATS["passes"])
    lk = leaks(out, mp, [v for v in mp.values() if len(v) >= 4])
    if lk:
        stats["leak"] += 1
        if len(ex) < 2: ex.append((values, text, out))
    else: stats["clean"] += 1
    if any(c not in "<>_" + AL + " =" for c in out): stats["odd char"] += 1
print(tree.rsplit("/", 1)[-1], MODE, ENTRY, dict(stats), "passes per sweep", dict(sorted(passes.items(), key=str)))
for e in ex: print("  example", e)

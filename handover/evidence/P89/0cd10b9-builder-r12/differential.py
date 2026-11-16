"""Differential: the b855a8f masking (all layers) against the round-12 masking (plain find + _fragment_spans) on plain-ASCII secrets and pytest-style lines.
Run: PYTHONPATH=src python differential.py  (from a tree that has src/ and tools/ of round 12; OLD is the b855a8f copy)."""
import importlib.util, os, random, sys
OLD = "/home/user/build/EV-P89-r12-old"
NEW = "/home/user/build/RB89"
def load(name, root):
    sys.path.insert(0, root + "/src")
    spec = importlib.util.spec_from_file_location(name, root + "/tools/mutation_runner.py")
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
old = load("mr_old", OLD); new = load("mr_new", NEW)
rng = random.Random(20261111)
ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
EXTRA = "-_.@!#$%^*()+=,:/?~ "
def pw():
    n = rng.choice([4, 6, 8, 12, 16, 21, 30])
    pool = ALPHA * 3 + (EXTRA if rng.random() < .3 else "") + ("&;" if rng.random() < .1 else "")
    return "".join(rng.choice(pool) for _ in range(n)).strip() or "Zq9xK2mP"
def dsn(p):
    kind = rng.choice(["kv", "kv2", "url", "kvq"])
    if kind == "kv": return "host=db.internal.example.org port=5432 dbname=mutants user=svc password=" + p
    if kind == "kv2": return "user=svc password=" + p + " host=db.internal.example.org dbname=mutants"
    if kind == "url": return "postgresql://svc:" + p.replace("@", "").replace("/", "").replace("?", "").replace("#", "").replace(" ", "x") + "@db.internal.example.org:5432/mutants"
    return "postgresql://svc@db.internal.example.org/mutants?password=" + p.replace("&", "").replace(" ", "x")
def lines(v):
    out = []
    for _ in range(6):
        h, t = rng.choice([(12, 13), rng.randint(1, 30), ]) if False else (12, 13)
        h, t = (12, 13) if rng.random() < .5 else (rng.randint(1, 30), rng.randint(1, 30))
        out.append(f"E   assert '{v[:h]}...{v[-t:]}' == 'other'")
    out.append(f"E   assert '{v}' == 'other'")
    for _ in range(6):
        a = rng.randint(0, len(v)); b = rng.randint(a, len(v))
        piece = v[a:b]; sep = rng.choice(["...", "....", ".....", "... ...", "..."])
        side = rng.random()
        pre = "".join(rng.choice(ALPHA + " =/") for _ in range(rng.randint(0, 6)))
        post = "".join(rng.choice(ALPHA + " =/") for _ in range(rng.randint(0, 6)))
        if side < .4: out.append(f"E   x {pre}{piece}{sep}{post} y")
        elif side < .8: out.append(f"E   x {pre}{sep}{piece}{post} y")
        else: out.append(f"E   x {piece}{sep}{v[a:b][::-1]}{sep}{piece}")
    for _ in range(4):  # quote or other mark right beside the dots (not a plain ``...``)
        h = rng.randint(2, 14); mark = rng.choice(["'", '"', "\\", " "])
        out.append(f"E   assert ['{v[:h]}{mark}...{mark}{v[-h:]}']")
    for _ in range(3):  # a piece of the value NOT beside dots; and dots elsewhere
        a = rng.randint(0, len(v) - 1); b = rng.randint(a + 1, len(v))
        out.append(f"E   see {v[a:b]} and a cut ... elsewhere and {v[a:b]}")
    return out
refused = 0; by_mark = {}; cases = diffs = same = 0; kinds = {}; examples = {}
for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 3000):
    p = pw(); v = dsn(p); os.environ["HADAVIN_TEST_PG_DSN"] = v
    so = old._secret_values(("HADAVIN_TEST_PG_DSN",))
    try: sn = new._secret_values(("HADAVIN_TEST_PG_DSN",))
    except ValueError: refused += 1; continue  # a % that decodes to an odd character: the new rule refuses it (tested elsewhere)
    for ln in lines(v):
        cases += 1
        a, b = old._masked(ln, so), new._masked(ln, sn)
        strip = lambda t: "".join(c for c in t if c not in "'\"\\")  # old also hides the quote marks next to a span: not a difference in what is hidden
        if a == b or strip(a) == strip(b): same += 1; continue
        diffs += 1
        marked_line = "['" in ln and ln.startswith("E   assert [")
        side = "mark-beside-dots" if marked_line else "plain"
        ca, cb = strip(a).replace(old.MASK, "").replace(" ", ""), strip(b).replace(old.MASK, "").replace(" ", "")
        mark = side + ":" + ("old-hides-more" if len(ca) < len(cb) else "new-hides-more" if len(cb) < len(ca) else "other")
        # does the new output leave the secret readable? (a leak check on what new keeps that old hid)
        kinds[mark] = kinds.get(mark, 0) + 1
        examples.setdefault(mark, []).append((v, ln, a, b))
        if marked_line:
            for m in ("'...'", chr(34)+"..."+chr(34), chr(92)+"..."+chr(92), " ... "):
                pass
            used = "quote" if ("'..." in ln or "...'" in ln) else "doublequote" if ln.count(chr(34))>0 else "backslash" if chr(92) in ln else "space"
            by_mark[used] = by_mark.get(used, 0) + 1
print("differing lines by the mark that stands beside the dots:", by_mark)
print("DSNs refused by the new rule (a percent sign that decodes to an odd character):", refused)
print(f"cases={cases} same={same} different={diffs} kinds={kinds}")
for mark, ex in examples.items():
    print("==", mark, "first 6 of", len(ex))
    for v, ln, a, b in ex[:6]:
        print("DSN :", v); print("LINE:", ln); print("OLD :", a); print("NEW :", b); print()

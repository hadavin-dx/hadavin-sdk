"""G9 v3 evidence: the shapes of review round 2 (design B1, M1, M5, M6) on tree argv[1], each through the entry point named.
argv[2:]: shape names (default all). Thread CPU seconds (one run), traced peak (tracemalloc, a second run when asked), passes and units
of the sweep calls (g9_probe). Every credential is made up and built from parts."""

import importlib
import random
import string
import sys
import time
import tracemalloc

tree = sys.argv[1]
sys.path.insert(0, tree + "/src")
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
R = importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk import defaults  # noqa: E402
from hadavin_sdk.guard import runmap  # noqa: E402

import g9_probe  # noqa: E402

g9_probe.install(R)
CAP = defaults.MAX_REDACT_CHARS
rng = random.Random(23)  # noqa: S311
AL = string.ascii_letters + string.digits


def rand(n):
    return "".join(rng.choice(AL) for _ in range(n))


def planted(n_lines, secret_len=130_000):
    """design B1: one long secret T0 found by its key, N short secrets `token=<last 5 of T0>XYZ<i>`, then N lines `<SECRET_1>XYZ<i>`
    (the first secret's placeholder written by the author: a key of the map once T0 is found)."""
    t0 = rand(secret_len)
    rules = [f"token={t0[-5:]}XY{i:05d}" for i in range(n_lines)]
    lines = [f"<SECRET_1>XY{i:05d}" for i in range(n_lines)]
    return "\n".join([f"password={t0}", *rules, *lines])


def comb_map(depth):
    """design M5: a comb of nested SECRET values (P[:i] + 'Z', i = 4..depth): the finder splits it into groups."""
    p = rand(depth)
    return {f"<SECRET_{i}>": p[:i] + "Z" for i in range(4, depth + 1)}, p


def jar_text():
    sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
    import g9_shapes as C

    return C.SHAPES["jar 330x64 + copies to cap"]


def bundle(n, overlap=True):
    """design M6: a redact_many bundle of n strings, each with its own overlapping pair and the overlap."""
    items = []
    for _ in range(n):
        base = rand(20)
        a, b = base[:12], base[6:]
        items.append(f"password={a}\ntoken={b}\nsee {base if overlap else a} end")
    return items


def curl_union():
    a, b = "abcd" + "efgh", "efgh" + "ijkl"
    head = f"password={a}\ntoken={b}\nsee {a}ijkl\n"
    return head + ("curl -u " * (CAP // 8 + 1))[: CAP - len(head)]


def encoded_mentions(n, value_len=67_583):
    """G4 v7 L26's shape with a SECRET stand-in (the kind does not change the cost): `step i see <SECRET_1> now.` x n, the value
    random base64 wrapped at 32."""
    b64 = string.ascii_letters + string.digits + "+/"
    raw = "".join(rng.choice(b64) for _ in range(value_len - value_len // 33))
    v = "\n".join(raw[i : i + 32] for i in range(0, len(raw), 32))
    m = runmap.RunMap({"<SECRET_1>": v})
    return "\n".join(f"step {i} see <SECRET_1> now." for i in range(n)), m


def run(name, fn, trace=False):
    g9_probe.reset()
    if trace:
        tracemalloc.start()
    t = time.thread_time()
    try:
        res = fn()
        what = "ok"
    except Exception as e:  # noqa: BLE001
        res, what = None, f"RAISED {type(e).__name__}({e})"
    took = time.thread_time() - t
    peak = ""
    if trace:
        peak = f" peak_MB={tracemalloc.get_traced_memory()[1] / 1e6:.0f}"
        tracemalloc.stop()
    print(f"{name}: cpu_s={took:.2f}{peak} {what} {g9_probe.summary()}", flush=True)
    return res


def s_planted(n):
    text = planted(n)
    print(f"  planted N={n} len={len(text):,}")
    res = run(f"planted N={n} redact", lambda: R.redact(text), trace=True)
    if res is not None:
        sizes = [len(v) for k, v in res.mapping.items()]
        print(f"  map entries={len(sizes)} map chars={sum(sizes):,} max={max(sizes):,}")


SHAPES = {
    "planted 10": lambda: s_planted(10),
    "planted 40": lambda: s_planted(40),
    "planted 1500": lambda: s_planted(1500),
    "planted 300": lambda: s_planted(300),
    "comb 1700 + jar via redact_text": lambda: (
        lambda cm: run(
            f"comb depth 1700 ({len(cm[0])} values) + jar",
            lambda: runmap.redact_text(jar_text(), runmap.RunMap(cm[0])),
        )
    )(comb_map(1700)),
    "comb 1700 + jar via enforce_map": lambda: (
        lambda cm: run(
            f"comb depth 1700 + jar, enforce_map of its redact_text output",
            lambda: runmap.enforce_map(runmap.redact_text(jar_text(), (m := runmap.RunMap(cm[0]))), m),
        )
    )(comb_map(1700)),
    "bundle 1000": lambda: run("redact_many 1000 strings, one overlap each", lambda: R.redact_many(bundle(1000))),
    "bundle 1000 no overlap": lambda: run("redact_many 1000 strings, no overlap", lambda: R.redact_many(bundle(1000, False))),
    "bundle 3000": lambda: run("redact_many 3000 strings, one overlap each", lambda: R.redact_many(bundle(3000))),
    "bundle 3000 no overlap": lambda: run("redact_many 3000 strings, no overlap", lambda: R.redact_many(bundle(3000, False))),
    "curl union": lambda: run("curl -u at cap with one overlap", lambda: runmap.redact_text(curl_union(), runmap.RunMap())),
    "curl": lambda: run("curl -u at cap", lambda: runmap.redact_text(("curl -u " * (CAP // 8 + 1))[:CAP], runmap.RunMap())),
}
for k in (30, 1000, 1800, 1900, 2000):
    SHAPES[f"mentions {k}"] = (lambda k: lambda: (lambda tm: run(f"65,536-char value mentioned {k} times, enforce_map", lambda: runmap.enforce_map(tm[0], tm[1])))(encoded_mentions(k)))(k)

for name in sys.argv[2:] or list(SHAPES):
    SHAPES[name]()

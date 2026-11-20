import base64, random, resource, textwrap, time, tracemalloc
from hadavin_sdk.guard import runmap
rnd = random.Random(26)
def b64(s): return base64.b64encode(s.encode()).decode()
rmap = runmap.RunMap()
words = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike".split()
rows = []
for i in range(24):
    n = rnd.randint(30_000, 60_000)
    body = "deploy note %d db_password=%s " % (i, "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12)))
    while len(body) < n * 3 // 4:
        body += rnd.choice(words) + " "
    blob = "\n".join(textwrap.wrap(b64(body), 36))
    t0 = time.thread_time()
    out = runmap.redact_text("step %d\n%s\nend" % (i, blob), rmap)
    dt = time.thread_time() - t0
    t1 = time.thread_time()
    runmap.redact_text("a short line %d with nothing" % i, rmap)
    d2 = time.thread_time() - t1
    t2 = time.thread_time()
    try:
        runmap.enforce_map("hello world " + out[:50], rmap)
        enf = time.thread_time() - t2
    except Exception as e:
        enf = "%s(%s)" % (type(e).__name__, e)
    chars = sum(map(len, rmap.values()))
    rows.append((i, len(blob), len(rmap), chars, round(dt, 2), round(d2, 2), enf if isinstance(enf, str) else round(enf, 2), resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))
    print(rows[-1], flush=True)

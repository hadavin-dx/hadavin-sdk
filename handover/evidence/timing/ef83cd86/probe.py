import sys, time, subprocess, collections
sys.path.insert(0, sys.argv[1])
from tests.fixtures import timing as T
out = collections.Counter()
errs = collections.Counter()
# 1 tiny non-waiting calls, many repeats
for i in range(40):
    try:
        g = T.growth(lambda s: len(s) + 1, "ab", 1500, 12000); out["tiny_ok"] += 1
    except T.Untimeable as e:
        out["tiny_Untimeable"] += 1; errs[str(e)[:120]] += 1
for i in range(15):
    try:
        T.growth(lambda s: sum(1 for _ in s[:200]), "ab", 1500, 12000); out["small_loop_ok"] += 1
    except T.Untimeable as e:
        out["small_loop_Untimeable"] += 1; errs[str(e)[:120]] += 1
# 2 sleeping function must raise
for name, fn in (("sleep", lambda s: time.sleep(0.01)), ("child", lambda s: subprocess.run([sys.executable, "-c", "import time;time.sleep(0.05)"]))):
    try:
        T.growth(fn, "ab", 1500, 12000); out[name + "_NOT_refused"] += 1
    except T.Untimeable:
        out[name + "_refused"] += 1
# 3 quadratic still flagged
g = T.growth(lambda s: sum(1 for a in s[:3000] for b in s[:len(s)//4]), "ab", 1500, 12000); out["quad_flagged=%s" % g.flagged] += 1
for a in ((0.0, 1.0), (1.0, 0.0), (float("nan"), 1.0)):
    try: str(T.Growth(a[0], a[1], 1500, 12000)); out["zero_time_NOT_refused"] += 1
    except T.Untimeable: out["zero_time_refused"] += 1
print(dict(out)); print(dict(errs))

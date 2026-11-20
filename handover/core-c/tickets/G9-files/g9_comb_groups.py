"""G9 v3 evidence (design M5): finder groups of a comb map and the units of one read-back of the cookie probe on tree argv[1]."""
import importlib, random, string, sys, time
sys.path.insert(0, sys.argv[1] + "/src"); sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
R = importlib.import_module("hadavin_sdk.guard.redact")
import g9_shapes as C
rng = random.Random(23); p = "".join(rng.choice(string.ascii_letters) for _ in range(int(sys.argv[2])))
m = {f"<SECRET_{i}>": p[:i] + "Z" for i in range(4, len(p) + 1)}
r = R._Redactor(m); r.find(C.cookie(300)); t = time.thread_time(); r.sweep(""); print("build s", round(time.thread_time() - t, 2))
print("depth", len(p), "values", len(m), "finders", len(r._finders), "slow", len(r._slow))
probe = C.fill(C.cookie(300)); out = r._sweep_once(probe, None, [0]) if hasattr(r, "_sweep_once") else None
w = [0]; t = time.thread_time(); r._overlaps(out, None, w); print("read-back units", f"{w[0]:,}", "cpu", round(time.thread_time() - t, 2))

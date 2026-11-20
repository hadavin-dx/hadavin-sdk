"""G9 v3 evidence: the honest worst shapes (cost.py) and H1/H2 (cost2.py) through runmap.redact_text with a fresh RunMap on tree argv[1];
best of 2 thread-CPU runs; passes and the largest unit count of one sweep call (g9_probe). argv[2:]: shape names (default all)."""
import importlib, sys, time
tree = sys.argv[1]
sys.path.insert(0, tree + "/src"); sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
R = importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk.guard import runmap
import g9_probe
g9_probe.install(R)
argv = sys.argv
import g9_shapes as C2  # the shapes (same folder)
for name in argv[2:] or list(C2.SHAPES):
    text = C2.SHAPES[name]; best = None
    for _ in range(2):
        g9_probe.reset(); t0 = time.thread_time()
        try: runmap.redact_text(text, runmap.RunMap()); res = "ok"
        except Exception as e: res = f"RAISED {type(e).__name__}({e})"
        took = time.thread_time() - t0; best = took if best is None else min(best, took)
    print(f"{name}: cpu_s={best:.2f} {res} {g9_probe.summary()}", flush=True)

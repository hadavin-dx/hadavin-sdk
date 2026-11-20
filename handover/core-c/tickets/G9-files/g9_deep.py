"""G9 v3: the anchored check (rules longer than the reach) on tree argv[1]."""
import sys, time
sys.path.insert(0, sys.argv[1] + "/src")
import importlib; R = importlib.import_module("hadavin_sdk.guard.redact"); from hadavin_sdk.guard import runmap
from hadavin_sdk import defaults
def reg(m):
    r = R._Redactor(m); r._may_register = True; return r
base = "".join(f"{n:04x}Qz" for n in range(200)); tail = "TAIL1234"
for d in (100, 200, 0, 1000):
    r = reg({"<SECRET_1>": base, "<SECRET_2>": base[d:] + tail})
    print("deep", 1200 - d, "->", r.sweep(base + tail), len(r.mapping))
# left side: secret ends deep in a long token from the left
r = reg({"<SECRET_1>": base, "<SECRET_2>": "HEAD5678" + base[:1100]})
print("left deep ->", r.sweep("HEAD5678" + base))
# gate
print("gate deep ->", runmap.enforce_map(base + tail, {"<SECRET_1>": base, "<SECRET_2>": base[100:] + tail}))
# two tokens in the run
r = reg({"<SECRET_1>": base[:600], "<SECRET_2>": base[600:], "<SECRET_3>": base[50:] + tail})
print("two-token run ->", r.sweep("<SECRET_1><SECRET_2>" + tail))
# k5 shape
r = R._Redactor({"<HIGHENTROPY_1>": "x" * 262_143}); r.sweep("")
w = [0]; t = time.thread_time(); print("k5", r._overlaps("<HIGHENTROPY_1> ", None, w), w, round(time.thread_time() - t, 3))
# periodic hostile
r = reg({"<SECRET_1>": "x" * 5000}); t = time.thread_time()
try: print(r.sweep("<SECRET_1>" + "x" * 3000 + " end")[:40])
except Exception as e: print("periodic", type(e).__name__, e)
print("periodic cpu", round(time.thread_time() - t, 3))
r = reg({"<SECRET_1>": "x" * 262_143}); t = time.thread_time()
try: print(r.sweep("<SECRET_1>" + "x" * 100_000 + " end")[:40])
except Exception as e: print("periodic 262k", type(e).__name__, e)
print("periodic 262k cpu", round(time.thread_time() - t, 3))
# reach test pin
r = R._Redactor({"<HIGHENTROPY_1>": "x" * 200_000}); r.sweep(""); w=[0]
print(r._overlaps("<HIGHENTROPY_1> ", None, w), w)
w=[0]; print(r._overlaps("<HIGHENTROPY_1> <HIGHENTROPY_1> ", None, w), w)

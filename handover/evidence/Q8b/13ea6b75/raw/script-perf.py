# Q8b perf probe of the new patterns: ratio method of CI's perf step (4x text; limit 12x time; best of three). Raw seconds printed.
import time, sys
from lib import *
print("## import", path_src())
A = "<made-up-value>"
shapes = {
 "long domain run + glued key": lambda n: "bob@" + "d" * n + ".com" + f"password={A}",
 "long host run, no @, + glued key": lambda n: "d" * n + ".com" + f"password={A}",
 "dotted 250-char labels + key": lambda n: ("a@" + "b" * 250 + ".") * (n // 252) + f"password={A}",
 "long run of key word": lambda n: "password" * (n // 8),
 "long run of key=": lambda n: "password=" * (n // 9),
 "long run of key=value pairs": lambda n: "token=x " * (n // 8),
 "long run of spaces after key=": lambda n: f"password={A}" + " " * n + "end",
 "key= then spaces only": lambda n: "password=" + " " * n,
 "key then many words": lambda n: f"password={A} " + "word " * (n // 5),
 "many short addresses": lambda n: "x@y." * (n // 4),
 "Bearer run": lambda n: "Authorization: Bearer " * (n // 22),
 "link then key run": lambda n: "https://example.com/x password: " * (n // 33),
 "tabs and newlines run": lambda n: f"password=" + ("\t\n" * (n // 2)) + "x",
}
paths = {"walk": lambda t: runmap.redact_untrusted(t, runmap.RunMap()), "card": clean}
def best(fn, text, reps=3):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter(); fn(text); ts.append(time.perf_counter() - t0)
    return min(ts)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
print(f"size small={N//4} large={N}; columns: shape | path | t(small) s | t(large) s | ratio | len(text large)")
for name, mk in shapes.items():
    for pn, fn in paths.items():
        try:
            a, b = best(fn, mk(N // 4)), best(fn, mk(N))
            print(f"{name} | {pn} | {a:.4f} | {b:.4f} | {b / max(a, 1e-9):.1f} | {len(mk(N))}", flush=True)
        except Exception as e:
            print(f"{name} | {pn} | EXC {type(e).__name__}: {str(e)[:100]}", flush=True)

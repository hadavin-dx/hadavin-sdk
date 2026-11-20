"""G9 v3 evidence: the design critic's chain (round 1 M2) on tree argv[1]; argv[2] == "pieces": G9 unions register pieces and the written
form (v1's design, `_place_union(..., derived=True)` forced) for the comparison of 9.3. Passes per sweep from g9_probe."""
import importlib, sys, time
sys.path.insert(0, sys.argv[1] + "/src")
R = importlib.import_module("hadavin_sdk.guard.redact")
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
import g9_probe  # noqa: E402

g9_probe.install(R)
if sys.argv[2:] == ["pieces"]:
    _real = R._Redactor._place_union
    R._Redactor._place_union = lambda self, union, kind, derived=True: _real(self, union, kind, True)
from hadavin_sdk.guard import runmap
A = "xY7wV6uT5s" + "R4aB3dE5fG9"      # S1, ends with G9 (21)
S2 = "G9" + "hIjK1mNoPq2R"            # S2 starts with G9 (14); tail hIjK1mNoPq2R (12)
TAIL = "hIjK1mNoPq2R"
def chain(depth):
    """depth locations after L1: L_k = TAIL[:12-k] glued to a secret whose value starts with TAIL[12-k] (so the piece of pass k straddles it)"""
    secrets = [A, S2]
    lines = []
    for k in range(1, depth + 1):
        x = TAIL[12 - k] + ["sT7uVw9z", "wQ4eZ5tY", "kL8mN2bV", "pO3iU7yT", "zX6cV1bN"][k - 1]
        secrets.append(x)
        lines.append("at " + TAIL[: 12 - k] + x + " ;")
    head = ["password=" + s for s in secrets]
    return "\n".join(head + ["see " + A + TAIL + " end"] + lines)
for depth in range(0, 5):
    text = chain(depth)
    for mode in ("redact", "redact_text"):
        g9_probe.reset()
        t0 = time.thread_time()
        try:
            out = R.redact(text).text if mode == "redact" else runmap.redact_text(text, runmap.RunMap())
            res = "ok: " + " | ".join(out.splitlines()[len(text.splitlines()) - depth - 1:])
        except Exception as e:
            res = f"RAISED {type(e).__name__} {e}"
        print(f"depth={depth} {mode}: {g9_probe.summary()} cpu={time.thread_time()-t0:.3f}s {res}")

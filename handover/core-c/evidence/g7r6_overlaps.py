"""G7 fix round 6: the exact reproductions of the two open overlap cases (E10). Run: uv run --all-extras --group test python handover/core-c/evidence/g7r6_overlaps.py"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]
V = "ab" + "9x"

print("-- (a) raw overlap in the literal sweep: F1 = V+ab, F2 = xyz+V, raw copy xyz+V+ab")
r = R._Redactor({"<SECRET_1>": V})
f1 = r._place("BEARER", V + "ab", "<SECRET_1>ab")
f2 = r._place("BEARER", "xyz" + V + "", "xyz<SECRET_1>")
print("F1", f1, "F2", f2, "sweep input", repr("see xyz" + V + "ab end"), "->", repr(r.sweep("see xyz" + V + "ab end")))
p = R._Redactor({"<SECRET_1>": "abcd" + "efgh", "<SECRET_2>": "efgh" + "ijkl"})
print("plain values abcdefgh / efghijkl, input abcdefghijkl ->", repr(p.sweep("abcdefghijkl")))

print("-- (b) overlap completed in a later round: F1 registered, copy swept, F2 registered after")
r = R._Redactor({"<SECRET_1>": V})
f1 = r._place("BEARER", V + "ab", "<SECRET_1>ab")
round2 = r._spelled_sweep("xyz<SECRET_1>ab", None)
f2 = r._place("BEARER", "xyz" + V, "xyz<SECRET_1>")
round3 = r._spelled_sweep(round2, None)
print("round 2 text", repr(round2), "after F2 registered, round 3 text", repr(round3), "F2 =", f2)
print("through the call: not reproduced by a natural input (the second form needs a chain through a later round); the test stands a `find` in for it")

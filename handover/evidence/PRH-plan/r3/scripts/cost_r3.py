"""Cost probe for PR H rev 3 (D3, D4, M5). Runs on main (2a8c2aac) from the clean worktree; standard library only.

Clock: time.process_time (CPU of this process), median of REPEATS, main and each variant interleaved in ONE process
so machine load moves both alike. Sizes: 65,536 and 262,144 characters (the cap). Shapes: exact lines below,
repeated to the size (`fill`). Variants measured:
  main           runmap.redact_untrusted as on main
  rev2-canon     main with canonical's Cf test replaced by the rev-2 per-character `is_ignorable` (frozenset + Cf)
  rev3-canon     main with canonical's Cf filter replaced by ONE compiled character-class removal (rev 3 W2)
  fastpath       the cost of rev 3's added checks on hidden-free text: `_ANY.search` on the text and on undo(text)
Worst case (D4): one `redact()` pass and `_views()` measured on the worst shape; rev-3 bound composed as
  10 passes + 2 x views (stated as an estimate composed from measured parts, not an end-to-end run)."""

from __future__ import annotations

import re
import statistics
import sys
import time
import unicodedata

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
import hidden_ref_oracle as oracle  # noqa: E402  (the r3 reference oracle, for the ignorable set only)

REPEATS = 5
ESC = "\x1b"
CAP = defaults.MAX_REDACT_CHARS
SMALL = 65_536
print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version, "cap", CAP, "budget", defaults.REDACT_BUDGET_S)
print("hadavin_sdk loaded from", sys.modules["hadavin_sdk"].__file__)

SHAPES = {  # name -> one line; hidden-free shapes are the ratio gate (rev 3 section 4.4)
    "S1 plain ASCII log": "2026-11-04T10:00:00Z INFO worker-7 request served status=200 path=/api/v1/items took 12ms\n",
    "S2 tab table": "pod-web-7f9c\tRunning\t3\tnode-a12\tdefault\tcluster-east\n",
    "S3 JSON lines": '{"ts": "2026-11-04T10:00:00Z", "level": "info", "msg": "served", "status": 200, "path": "/api/v1/items", "ms": 12}\n',
    "S4 Hindi": "यह एक साधारण वाक्य है जिसमें कोई गुप्त जानकारी नहीं है।\n",
    "S5 Persian ZWNJ emoji": "این یک جملهٔ ساده است؛ می‌خواهم بگویم \U0001F600❤️ \U0001F468‍\U0001F469‍\U0001F467\n",
    "H1 coloured output": ESC + "[32mPASS" + ESC + "[0m tests/test_items.py::test_list " + ESC + "[1;34m12ms" + ESC + "[0m\n",
    "H2 colour inside a word": "match: req" + ESC + "[1;31muest" + ESC + "[0m_id served in 12ms\n",
    "W worst: Persian + colour inside a word + percent": "می‌خواهم req" + ESC + "[1;31muest" + ESC + "[0m_id 50%25 done\n",
}
HIDDEN_FREE = [k for k in SHAPES if k[0] == "S"]


def fill(u: str, n: int) -> str:
    return (u * (n // len(u) + 1))[:n]


IGN = oracle.derive_ignorable()
_IGN_SET = frozenset(chr(c) for c in IGN)
_ORIG_CANON = runmap.canonical


def _class(points) -> str:
    return "".join(
        (re.escape(chr(a)) if a == b else re.escape(chr(a)) + "-" + re.escape(chr(b))) for a, b in oracle.to_ranges(frozenset(points))
    )


# rev 3: ignorables = the pinned set plus every Cf above U+007F (main's rule) as ONE class
_CF = frozenset(c for c in range(0x80, 0x110000) if unicodedata.category(chr(c)) == "Cf")
_IGN_RE = re.compile("[" + _class(IGN | _CF) + "]")


def canon_rev2(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKC", text) if not (c in _IGN_SET or (c > "\x7f" and unicodedata.category(c) == "Cf"))
    )


def canon_rev3(text: str) -> str:
    return _IGN_RE.sub("", unicodedata.normalize("NFKC", text))


_ANY = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]")


def run_variant(name: str, text: str) -> float:
    runmap.canonical = {"main": _ORIG_CANON, "rev2-canon": canon_rev2, "rev3-canon": canon_rev3}[name]
    a = time.process_time()
    try:
        runmap.redact_untrusted(text, {})
    except runmap.RedactionError as exc:
        print("   raised", type(exc).__name__)
    finally:
        runmap.canonical = _ORIG_CANON
    return time.process_time() - a


def fastpath(text: str) -> float:
    a = time.process_time()
    _ANY.search(text)
    if not text.isascii() or any(c in text for c in "\\%&"):
        _ANY.search(runmap.undo(text))  # rev 3 reuses _views' undo result; timed here in full as an upper bound
    return time.process_time() - a


# equality check: rev3 canonical == main canonical on every shape (hidden-free shapes hold no non-Cf ignorable
# except U+FE0F and ZWJ/ZWNJ in S5, which rev 3 removes on purpose: reported, not asserted)
for k, u in SHAPES.items():
    t = fill(u, 4096)
    print("canon-equal", k, "main==rev3:", _ORIG_CANON(t) == canon_rev3(t), "rev2==rev3:", canon_rev2(t) == canon_rev3(t))

print("shape | chars | main cpu | rev2-canon cpu | rev3-canon cpu | fastpath cpu | rev3 estimate | rev3/main | rev2/main")
results = {}
for k, u in SHAPES.items():
    if k.startswith("W"):
        continue
    for n in (SMALL, CAP):
        text = fill(u, n)
        rows = {v: [] for v in ("main", "rev2-canon", "rev3-canon")}
        fp = []
        for _ in range(REPEATS):
            for v in rows:
                rows[v].append(run_variant(v, text))
            fp.append(fastpath(text))
        med = {v: statistics.median(x) for v, x in rows.items()}
        f = statistics.median(fp)
        est = med["rev3-canon"] + f
        results[(k, n)] = (med, f, est)
        print(f"{k} | {n} | {med['main']:.3f} | {med['rev2-canon']:.3f} | {med['rev3-canon']:.3f} | {f:.4f} | {est:.3f} | {est / med['main']:.2f} | {med['rev2-canon'] / med['main']:.2f}")

# D4 worst case: one pass and the views on the worst shape at the cap
w = fill(SHAPES["W worst: Persian + colour inside a word + percent"], CAP)
p, v = [], []
for _ in range(REPEATS):
    a = time.process_time()
    redact(w, mapping={})
    p.append(time.process_time() - a)
    a = time.process_time()
    runmap._views(w)
    v.append(time.process_time() - a)
tp, tv = statistics.median(p), statistics.median(v)
a = time.process_time()
try:
    runmap.redact_untrusted(w, {})
    res = "finished"
except runmap.RedactionError as exc:
    res = "raised " + type(exc).__name__
tm = time.process_time() - a
print(f"W pass cpu {tp:.3f} | views cpu {tv:.3f} | main end-to-end {tm:.3f} {res}")
for passes, label in ((18, "rev-2 bound (18 passes, 2 views sets)"), (10, "rev-3 bound (10 passes, 1 views set)")):
    sets = 2 if passes == 18 else 1
    est = passes * tp + sets * tv
    largest = int(CAP * min(1.0, defaults.REDACT_BUDGET_S / est))
    print(f"W {label}: estimate {est:.2f} s cpu at the cap; largest size under the 6 s budget about {largest} chars")
print("done")

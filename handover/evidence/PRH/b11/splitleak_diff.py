"""EVIDENCE for PR H batch 11: the per-text set difference of readable texts between trees (cell name and text hash only, no text).
Usage: python splitleak_diff.py <head.jsonl> <main.jsonl> <ea6dbdaf.jsonl> <old.jsonl>  (files written by fuzz_cells.py)."""

import json, sys
from collections import Counter


def load(p):
    return {(r["cell"], r["h"]): r for r in map(json.loads, open(p))}


head, main, ea6, old = (load(p) for p in sys.argv[1:5])
print("unique texts by (cell, hash):", *(len(d) for d in (head, main, ea6, old)))
r = lambda d: {k for k, v in d.items() if v["readable"]}
H, M, E, O = r(head), r(main), r(ea6), r(old)
cells = lambda s: dict(Counter(k[0].split("/")[0] for k in s))
for name, other in (("main", M), ("ea6dbdaf", E), ("5c430b6a (batch 10 head)", O)):
    print(f"readable on head and NOT readable on {name}:", len(H - other), cells(H - other))
    print(f"readable on {name} and NOT readable on head:", len(other - H))
print("readable on head:", len(H), cells(H))
print("readable on main:", len(M))
print(
    "head readable split texts:",
    sum(1 for k in H if k[0].startswith("split")),
    "main readable split texts:",
    sum(1 for k in M if k[0].startswith("split")),
)
print(
    "withheld on head:",
    sum(v["withheld"] for v in head.values()),
    "withheld on main:",
    sum(v["withheld"] for v in main.values()),
    "withheld on old:",
    sum(v["withheld"] for v in old.values()),
)

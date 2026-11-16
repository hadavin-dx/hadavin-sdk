"""Check (a). Run from repo root: python3 handover/flows-audit/tools/check_counts.py
Pass = 52 files / 655 nodes live; equals tools/out/counts.txt; each lane heading '### <path rel. handover/demo> (<n> nodes)' has n table rows = nodes in that json; every one of the 52 files appears in exactly one lane. Exit 0 pass, 1 fail. Lanes absent = prints SKIP-LANES (only counts checked)."""

import glob
import json
import os
import re
import sys


def read_lines(path):
    with open(path) as fh:
        return fh.readlines()


def read_json(path):
    with open(path) as fh:
        return json.load(fh)


R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DEMO = os.path.join(R, "demo")
LANES = os.path.join(R, "flows-audit", "lanes")
files = [
    f
    for f in sorted(glob.glob(DEMO + "/n8n-*/**/*.json", recursive=True))
    if "/n8n-tests/" not in f
]
live = {}
for f in files:
    d = read_json(f)
    if isinstance(d, dict) and "nodes" in d:
        live[os.path.relpath(f, DEMO)] = len(d["nodes"])
bad = []
if (len(live), sum(live.values())) != (52, 655):
    bad.append(f"live totals {len(live)} files / {sum(live.values())} nodes, expected 52 / 655")
rec = {}
for l in read_lines(os.path.join(R, "flows-audit", "tools", "out", "counts.txt")):
    m = re.match(r"(\d+) (\S+)", l)
    if m:
        rec[m.group(2)] = int(m.group(1))
if rec != live:
    bad.append("tools/out/counts.txt differs from live counts")
seen = {}
for lf in sorted(glob.glob(LANES + "/*.md")):
    cur = None
    for l in read_lines(lf):
        m = re.match(r"### (\S+) \((\d+) nodes\)", l)
        if m:
            cur = m.group(1)
            seen.setdefault(cur, 0)
            seen[cur] += 0
            hdr = int(m.group(2))
            rows = 0
            seen[cur] = [hdr, 0, 1 if not isinstance(seen[cur], list) else seen[cur][2] + 1]
            continue
        if cur and re.match(r"\| \d+ \|", l):
            seen[cur][1] += 1
if not glob.glob(LANES + "/*.md"):
    print("SKIP-LANES: no lane files yet")
else:
    for p, n in live.items():
        v = seen.get(p)
        if not v:
            bad.append(f"MISSING in lanes: {p}")
        elif v[2] != 1:
            bad.append(f"{p}: appears {v[2]} times")
        elif v[0] != n or v[1] != n:
            bad.append(f"{p}: json {n}, heading {v[0]}, rows {v[1]}")
print("FAIL " + "; ".join(bad) if bad else f"PASS {len(live)} files / {sum(live.values())} nodes")
sys.exit(1 if bad else 0)

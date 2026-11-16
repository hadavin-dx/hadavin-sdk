"""Check (b). Every lane table row: node exists in its json; the first 10 cells (machine columns) equal the row of the same number in tools/out/<name>.md cell for cell. Run from repo root. Exit 0/1."""

import glob
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DEMO = os.path.join(R, "demo")
OUT = os.path.join(R, "flows-audit", "tools", "out")
cells = lambda l: [c.strip() for c in re.split(r"(?<!\\)\|", l.strip())[1:-1]]
bad = []
rows = 0
for lf in sorted(glob.glob(os.path.join(R, "flows-audit", "lanes", "*.md"))):
    cur = None
    for l in open(lf):
        m = re.match(r"### (\S+) \(\d+ nodes\)", l)
        if m:
            cur = m.group(1)
            names = {n["name"] for n in json.load(open(os.path.join(DEMO, cur)))["nodes"]}
            ref = {
                cells(x)[0]: cells(x)[:10]
                for x in open(os.path.join(OUT, cur.replace("/", "__")[:-5] + ".md"))
                if re.match(r"\| \d+ \|", x)
            }
            continue
        if cur and re.match(r"\| \d+ \|", l):
            c = cells(l)
            rows += 1
            if c[1] not in names:
                bad.append(f"{os.path.basename(lf)} {cur} row {c[0]}: node {c[1]!r} not in json")
            elif c[:10] != ref.get(c[0]):
                bad.append(
                    f"{os.path.basename(lf)} {cur} row {c[0]}: machine columns differ from tools/out"
                )
print(
    "FAIL " + "; ".join(bad[:20]) + (f" ... {len(bad)} total" if len(bad) > 20 else "")
    if bad
    else f"PASS {rows} rows"
)
sys.exit(1 if bad else 0)

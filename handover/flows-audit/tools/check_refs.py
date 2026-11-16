"""Check (c). In FINDINGS.md and lanes/*.md: '<path>.json:<NodeName>' must name a node that exists; '<path>.(md|py|txt|sql|sh):<n>' must be a line <= file length.
Path resolution: relative to handover/demo, then handover/, then repo root; if that fails, by BASENAME anywhere under handover/demo (a ref passes if ANY file with that basename satisfies it; a basename that exists nowhere fails).
A ref '<path>.json:row <n>' passes if n <= node count of that file.
Node names may contain spaces: the text after ':' up to , ; ) | ` or ' and ' / ' vs ' is taken, and the ref passes if a node name of the file is a prefix of it.
Run from repo root: python3 handover/flows-audit/tools/check_refs.py   Exit 0 pass, 1 fail, one PASS or FAIL line."""

import glob
import json
import os
import re
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DEMO = os.path.join(R, "demo")


def read_text(path, **kw):
    with open(path, **kw) as fh:
        return fh.read()


def line_count(path):
    with open(path, errors="replace") as fh:
        return sum(1 for _ in fh)


bases = [DEMO, R, os.path.join(R, "..")]
index = {}
for d, _, fs in os.walk(DEMO):
    for f in fs:
        index.setdefault(f, []).append(os.path.join(d, f))


def find_all(p):
    for b in bases:
        q = os.path.join(b, p)
        if os.path.isfile(q):
            return [q]
    return index.get(os.path.basename(p), [])


nodes_cache = {}


def nodes(q):
    if q not in nodes_cache:
        nodes_cache[q] = {x["name"] for x in json.loads(read_text(q)).get("nodes", [])}
    return nodes_cache[q]


bad = []
n = 0
for f in [os.path.join(R, "flows-audit", "FINDINGS.md")] + sorted(
    glob.glob(os.path.join(R, "flows-audit", "lanes", "*.md"))
):
    if not os.path.exists(f):
        continue
    t = read_text(f, encoding="utf-8")
    for p, rest in re.findall(r"([\w./-]+\.json):([A-Za-z](?:(?! and | vs )[^,;)|`\n])*)", t):
        n += 1
        rest = rest.strip()
        m = re.match(r"row (\d+)", rest)
        if m:
            if not any(1 <= int(m.group(1)) <= len(nodes(q)) for q in find_all(p)):
                bad.append(f"{os.path.basename(f)}: {p}:row {m.group(1)} out of range")
            continue
        if not any(any(rest.startswith(nm) for nm in nodes(q)) for q in find_all(p)):
            bad.append(f"{os.path.basename(f)}: {p}:{rest[:30]}")
    for p, ln in re.findall(r"([\w./-]+\.(?:md|py|txt|sql|sh)):(\d+)", t):
        n += 1
        if not any(int(ln) <= line_count(q) for q in find_all(p)):
            bad.append(f"{os.path.basename(f)}: {p}:{ln}")
print(
    "FAIL unresolved: " + "; ".join(bad[:25]) + (f" ... {len(bad)} total" if len(bad) > 25 else "")
    if bad
    else f"PASS {n} references"
)
sys.exit(1 if bad else 0)

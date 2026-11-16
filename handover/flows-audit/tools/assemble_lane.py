"""Assemble a lane file mechanically so machine columns are never retyped.
Run from repo root:  python3 handover/flows-audit/tools/assemble_lane.py <lane-name> <path-rel-handover/demo.json> [more paths...]
Reads  handover/flows-audit/lanes/<lane>.judge.jsonl   (one JSON object per line):
   {"file": "<path>", "row": <n>, "cells": [13 strings in the section-4 judgement order]}
   {"file": "<path>", "row": <n>, "same_as": "<text put in every judgement cell>"}
 and optional handover/flows-audit/lanes/<lane>.header.md (put first: inputs, absent files, notes).
Writes handover/flows-audit/lanes/<lane>.md = header + skeleton table per file with TODO replaced by the given cells.
Rows without an entry stay TODO; the script prints how many TODO rows remain per file. A cell may not contain a newline; '|' is escaped."""

import contextlib
import io
import json
import os
import re
import sys

import dump_nodes

H = os.path.dirname(os.path.abspath(__file__))
LANES = os.path.join(H, "..", "lanes")
DEMO = os.path.join(H, "..", "..", "demo")
lane, files = sys.argv[1], sys.argv[2:]


def dump(*args, cwd):
    """Run dump_nodes.py in this process (same code, same output) from folder cwd; returns (exit code, stdout)."""
    buf = io.StringIO()
    with contextlib.chdir(cwd), contextlib.redirect_stdout(buf):
        rc = dump_nodes.main(list(args))
    return rc, buf.getvalue()


J = {}
jp = os.path.join(LANES, lane + ".judge.jsonl")
if os.path.exists(jp):
    with open(jp, encoding="utf-8") as fh:
        for n, l in enumerate(fh, 1):
            if not l.strip():
                continue
            o = json.loads(l)
            cells = [o["same_as"]] * 13 if "same_as" in o else o["cells"]
            if len(cells) != 13:
                raise ValueError(f"{jp}:{n} needs exactly 13 cells, has {len(cells)}")
            J[(o["file"], int(o["row"]))] = [
                str(c).replace("\n", " ").replace("|", "\\|") for c in cells
            ]
out = []
hp = os.path.join(LANES, lane + ".header.md")
if os.path.exists(hp):
    with open(hp, encoding="utf-8") as fh:
        out.append(fh.read().rstrip() + "\n")
todo_total = 0
for f in files:
    rc, stdout = dump("skeleton", f, cwd=DEMO)
    if rc != 0:
        raise RuntimeError(f"dump_nodes skeleton {f} failed with exit code {rc}")
    t = stdout.splitlines()
    todo = 0
    for l in t:
        m = re.match(r"\| (\d+) \|", l)
        if m and l.endswith(" TODO |" * 13):
            c = J.get((f, int(m.group(1))))
            if c:
                l = l[: -len(" TODO |" * 13)] + "".join(f" {x} |" for x in c)
            else:
                todo += 1
        out.append(l)
    out.append(f"<!-- {f}: {todo} rows still TODO -->")
    out.append("")
    print(f"{f}: {todo} TODO")
    todo_total += todo
with open(os.path.join(LANES, lane + ".md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("TOTAL TODO", todo_total)

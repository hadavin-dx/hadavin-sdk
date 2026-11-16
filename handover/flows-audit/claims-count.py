"""Recount the claim verdicts in CLAIMS-TABLE.md and check the table columns.

Usage: python3 claims-count.py CLAIMS-TABLE.md
Claim rows start with `| A-nnn |`, `| B-nnn |` or `| X-n |` and must have 7 cells
(8 pipe signs). To-do rows start with `| <number> |` and must have 11 cells.
The verdict is the first phrase of cell 6 (longest phrase first).
Prints: verdict counts, counts per lane, offenders, number of ids and unique ids.
"""

import collections
import re
import sys

VERDICTS = [
    "SUPPORTED ONLY BY RELAYED NUMBER",  # reported as RELAYED-ONLY
    "SUPPORTED",
    "OVERSTATED",
    "UNSUPPORTED",
    "UNTRACED",
]


def count(path):
    verdicts = collections.Counter()
    lanes = collections.Counter()
    offenders = []
    ids = []
    todo_rows = 0
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    in_todo = True  # to-do rows exist only before the lane sections
    for line in lines:
        if line.startswith("# LANE A"):
            in_todo = False
        m = re.match(r"\| (A-\d+|B-\d+|X-\d) \|", line)
        if m:
            cells = line.strip().strip("|").split(" | ")
            if len(cells) != 7 or line.count("|") != 8:
                offenders.append((m.group(1), "cells", len(cells), line.count("|")))
                continue
            for phrase in VERDICTS:
                if cells[5].startswith(phrase):
                    name = "RELAYED-ONLY" if phrase.startswith("SUPPORTED ONLY") else phrase
                    verdicts[name] += 1
                    lanes[m.group(1)[0]] += 1
                    break
            else:
                offenders.append((m.group(1), "no verdict", cells[5][:30]))
            ids.append(m.group(1))
            continue
        if in_todo and re.match(r"\| \d+ \| ", line):
            todo_rows += 1
            cells = line.strip().strip("|").split(" | ")
            if len(cells) != 11:
                offenders.append(("row " + line.split(" | ")[0].strip("| "), "cells", len(cells)))
    return verdicts, lanes, offenders, ids, todo_rows


if __name__ == "__main__":
    v, lane, bad, ids, todo = count(sys.argv[1])
    print("verdicts:", dict(v), "total", sum(v.values()))
    print("lanes (A, B incl. X):", dict(lane))
    print("to-do rows:", todo)
    print("offenders:", len(bad), bad)
    print("ids:", len(ids), "unique:", len(set(ids)))

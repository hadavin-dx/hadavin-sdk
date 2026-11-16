import collections
import re
import sys

DECISION = re.compile(r"(PROPOSE FIX|DECLINE|CONTEST|ESCALATE)")


def decision(row):
    for cell in row[2:4]:
        m = DECISION.match(cell)
        if m:
            return m.group(1)
    raise SystemExit(f"no decision cell in row {row[0]}")


rows = []
with open(sys.argv[1], encoding="utf-8") as fh:
    lines = fh.readlines()
for line in lines:
    if re.match(r"\| [CAGDX]-\d+ \|", line):
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
print("rows", len(rows), [r[0] for r in rows])
print("severity", dict(collections.Counter(r[1] for r in rows)))
print("decision", dict(collections.Counter(decision(r) for r in rows)))

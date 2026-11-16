import collections
import re
import sys

rows = []
with open(sys.argv[1], encoding="utf-8") as fh:
    lines = fh.readlines()
for line in lines:
    if re.match(r"\| [CAGDX]-\d+ \|", line):
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
print("rows", len(rows), [r[0] for r in rows])
print("severity", dict(collections.Counter(r[1] for r in rows)))
print(
    "decision",
    dict(
        collections.Counter(
            re.match(
                r"(PROPOSE FIX|DECLINE|CONTEST|ESCALATE)",
                r[2] if r[2].split()[0] in ("PROPOSE", "DECLINE") else r[3],
            ).group(1)
            for r in rows
        )
    ),
)

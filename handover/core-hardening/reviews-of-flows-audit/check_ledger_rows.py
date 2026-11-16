"""Format check for LEDGER-ROWS.md: 9 pipe-separated fields per data row, enums, unique ids, ISO date."""
import re, sys
STATUS = {"OPEN", "FIXED-UNVERIFIED", "FIXED-VERIFIED", "OWNER-ONLY", "IMPOSSIBLE-NOW"}
SEV = {"Blocker", "Major", "Nit"}
rows, bad, ids = 0, [], set()
for n, line in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    if not line.startswith("RF-"):
        continue
    f = [c.strip() for c in line.rstrip("\n").split("|")]
    rows += 1
    if len(f) != 9:
        bad.append(f"line {n}: {len(f)} fields"); continue
    if f[0] in ids: bad.append(f"line {n}: duplicate id {f[0]}")
    ids.add(f[0])
    if f[2] not in SEV: bad.append(f"line {n}: severity {f[2]!r}")
    if f[5].split()[0] not in STATUS: bad.append(f"line {n}: status {f[5]!r}")
    if not re.match(r"\d{4}-\d{2}-\d{2}", f[8]): bad.append(f"line {n}: date {f[8]!r}")
print(f"rows={rows} problems={len(bad)}")
for b in bad: print(b)
sys.exit(1 if bad or not rows else 0)

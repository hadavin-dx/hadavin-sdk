"""Recount FINDINGS.md rows once: python3 tools/count_findings.py [FINDINGS.md]
Severity = first word of the severity cell (Blocker, Major, Nit); BEFORE = 'when' cell starts with BEFORE, else AFTER.
Prints counts and the BEFORE/AFTER split table; exit 0."""
import re, sys, collections
p = sys.argv[1] if len(sys.argv) > 1 else 'FINDINGS.md'
c = collections.Counter(); ids = []
for l in open(p, encoding='utf-8'):
    m = re.match(r'\| (F-\d+) \| (\w+)[^|]* \| [^|]* \| [^|]* \| (\w+)', l)
    if m:
        ids.append(m.group(1)); c[(m.group(2), 'BEFORE' if m.group(3) == 'BEFORE' else 'AFTER')] += 1
print('rows', len(ids), 'unique', len(set(ids)))
tot = collections.Counter()
for s in ('Blocker', 'Major', 'Nit'):
    b, a = c[(s, 'BEFORE')], c[(s, 'AFTER')]; tot['B'] += b; tot['A'] += a
    print(f'| {s} | {b} | {a} | {a + b} |')
print(f"| all | {tot['B']} | {tot['A']} | {tot['A'] + tot['B']} |")
print('sev', {s: sum(v for (k, w), v in c.items() if k == s) for s in ('Blocker', 'Major', 'Nit')})

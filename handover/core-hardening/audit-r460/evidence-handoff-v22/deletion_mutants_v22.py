"""v22 (v21 evidence): delete each pinned statement or timeout from each held file, and append ADD CONSTRAINT to DB-2; v22 must flag all, v21 shows what it missed."""
import sys, glob, os, re
sys.path.insert(0, '.')
import secdef_guard_v22 as g, allow_v22 as A, secdef_guard_v21 as q, allow_v21 as AQ
tot = caught = missq = 0; bad = []
def run(label, n, m):
    global tot, caught, missq
    tot += 1; p = A.check(g, n, m); caught += bool(p)
    if not p: bad.append(label)
    try: pq = AQ.check(q, n, m)
    except Exception: pq = ['err']
    missq += (not pq); print(("v22 FLAG " if p else "v22 MISS ") + ("v21 flag " if pq else "v21 MISS ") + label)
for f in sorted(glob.glob('held-sql/*.sql')):
    n = os.path.basename(f); t = open(f).read(); lines = t.split(';\n')
    for i, l in enumerate(lines):
        if re.match(r'\s*(--[^\n]*\n\s*)*(ALTER TABLE|COMMENT ON|CREATE (UNIQUE )?INDEX|CREATE TABLE|SET LOCAL)', l, re.I) or 'ADD CONSTRAINT' in l:
            run(f"{n} delete statement {i}: {' '.join(l.split())[:60]!r}", n, ';\n'.join(lines[:i] + lines[i + 1:]))
t = open('held-sql/spend_decrease_log.sql').read()
run("DB-2 appended ADD CONSTRAINT", 'spend_decrease_log.sql', t + "\nALTER TABLE spend ADD CONSTRAINT x_ok CHECK (usd > -1000000);\n")
run("DB-2 lock_timeout line removed", 'spend_decrease_log.sql', re.sub(r"SET LOCAL lock_timeout[^;]*;", "", t))
print(f"deletion mutants {tot}; v22 flags {caught}; v21 misses {missq}; v22 misses {bad}")
sys.exit(1 if bad else 0)

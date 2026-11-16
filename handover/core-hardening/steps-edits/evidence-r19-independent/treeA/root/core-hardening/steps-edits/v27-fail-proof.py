"""v27-fail-proof.py: runs the v27 checks of Part 4 and Part 5 (C105 to C159, one or more per finding of the two v26 reviews) on the BUILT v26 files (read only)
and on the BUILT v27 files. Shows which checks fail on v26 (they must) and that none fails on v27. Lists every check that does NOT fail on v26 (a check that cannot fail on the old files proves nothing).
Usage: python3 v27-fail-proof.py. Exit 0 = every check fails on v26 or is listed as unable to fail there, and none fails on v27."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v27.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 4 (v27)'):]
def run(A, B, NOTE, OPEN):
    fails = []
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, fail=lambda c, m: fails.append(c), F={'okb': '16:00 UTC = 21:30 IST'}, SEC=[])
    exec(head + '\n' + body, ns); return set(fails)
codes = sorted(set(re.findall(r"\b(C1[0-5]\d)\b", body)))
old = run(rd('OWNER-SHEET-v26-A.md'), rd('OWNER-SHEET-v26-B.md'), rd('LEAD-RELEASE-NOTE-v10.md'), rd('v26-OPEN-FOR-LEAD.md'))
new = run(rd('OWNER-SHEET-v27-A.md'), rd('OWNER-SHEET-v27-B.md'), rd('LEAD-RELEASE-NOTE-v11.md'), rd('v27-OPEN-FOR-LEAD.md'))
cannot = [c for c in codes if c not in old]
print('checks in Part 4 and 5: %d' % len(codes)); print('fail on built v26: %d' % len(old & set(codes)))
print('do NOT fail on built v26 (cannot prove a change; reason must be given in v27-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v27: %s' % (sorted(new) or 'none'))
bad = len(new)
print('v27-fail-proof: %d problem(s)' % bad); sys.exit(1 if bad else 0)

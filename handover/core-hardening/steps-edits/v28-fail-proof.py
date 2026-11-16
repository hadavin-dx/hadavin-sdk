"""v28-fail-proof.py: runs the v28 checks of Part 4 and Part 5 (C160 to C170, one or more per class change of the v26/v27 root-cause reading) on the BUILT v27 files (read only)
and on the BUILT v28 files. Shows which checks fail on v27 (they must) and that none fails on v28. Lists every check that does NOT fail on v27 (a check that cannot fail on the old files proves nothing).
Usage: python3 v28-fail-proof.py. Exit 0 = every check fails on v27 or is listed as unable to fail there, and none fails on v28."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v28.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 4 (v28)'):]
def run(A, B, NOTE, OPEN, SD):
    fails = []
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=lambda c, m: fails.append(c), F={'okb': '16:00 UTC = 21:30 IST'}, SEC=[])
    exec(head + '\n' + body, ns); return set(fails)
codes = sorted(set(re.findall(r"\b(C1[67]\d)\b", body)))
va, vb = rd('OWNER-SHEET-v27-A.md'), rd('OWNER-SHEET-v27-B.md')
old = run(va, vb, rd('LEAD-RELEASE-NOTE-v11.md'), rd('v27-OPEN-FOR-LEAD.md'), {'A': va, 'B': vb})
import importlib.util
spec = importlib.util.spec_from_file_location('b28', D + 'build-v28.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
sa, sb = rd('OWNER-SHEET-v28-A.md'), rd('OWNER-SHEET-v28-B.md')
wa = bm.combine(sa, rd('OWNER-CARD-v28-A.md'), rd('OWNER-NUMBERS-v28-A.md'), rd('OWNER-FILM-v28.md')); wb = bm.combine(sb, rd('OWNER-CARD-v28-B.md'), rd('OWNER-NUMBERS-v28-B.md'), rd('OWNER-FILM-v28.md'))
new = run(wa, wb, rd('LEAD-RELEASE-NOTE-v12.md'), rd('v28-OPEN-FOR-LEAD.md'), {'A': sa, 'B': sb})
cannot = [c for c in codes if c not in old]
print('checks in Part 4 and 5: %d' % len(codes)); print('fail on built v27: %d' % len(old & set(codes)))
print('do NOT fail on built v27 (cannot prove a change; reason must be given in v28-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v28: %s' % (sorted(new) or 'none'))
bad = len(new)
print('v28-fail-proof: %d problem(s)' % bad); sys.exit(1 if bad else 0)

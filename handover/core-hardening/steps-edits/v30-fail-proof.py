"""v30-fail-proof.py: runs the v30 checks of Part 4 and Part 5 (C160 to C184, one or more per class change of the v26/v28 root-cause reading) on the BUILT v28 files (read only)
and on the BUILT v30 files. Shows which checks fail on v28 (they must) and that none fails on v30. Lists every check that does NOT fail on v28 (a check that cannot fail on the old files proves nothing).
Usage: python3 v30-fail-proof.py. Exit 0 = every check fails on v28 or is listed as unable to fail there, and none fails on v30."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v30.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 4 (v30)'):]
def run(A, B, NOTE, OPEN, SD, FF=None):
    fails = []
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=lambda c, m: fails.append(c), F=FF or {'okb': '16:00 UTC = 21:30 IST'}, SEC=[])
    exec(head + '\n' + body, ns); return set(fails)
codes = sorted(set(re.findall(r"\b(C1[6-8]\d)\b", body)))
va, vb = rd('OWNER-SHEET-v28-A.md'), rd('OWNER-SHEET-v28-B.md')
wva = '\n'.join(rd(n) for n in ('OWNER-SHEET-v28-A.md', 'OWNER-CARD-v28-A.md', 'OWNER-NUMBERS-v28-A.md', 'OWNER-FILM-v28.md'))   # every v28 owner page together (the most text the old files could offer a check)
wvb = '\n'.join(rd(n) for n in ('OWNER-SHEET-v28-B.md', 'OWNER-CARD-v28-B.md', 'OWNER-NUMBERS-v28-B.md', 'OWNER-FILM-v28.md'))
old = run(wva, wvb, rd('LEAD-RELEASE-NOTE-v12.md'), rd('v28-OPEN-FOR-LEAD.md'), {'A': va, 'B': vb})
import importlib.util
spec = importlib.util.spec_from_file_location('b28', D + 'build-v30.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
sa, sb = rd('OWNER-SHEET-v30-A.md'), rd('OWNER-SHEET-v30-B.md')
wa = bm.combine(sa, rd('OWNER-CARD-v30-A.md')) + '\n' + rd('OWNER-APPENDIX-v30-A.md') + '\n' + rd('OWNER-FILM-PERSON-v30.md'); wb = bm.combine(sb, rd('OWNER-CARD-v30-B.md')) + '\n' + rd('OWNER-APPENDIX-v30-B.md') + '\n' + rd('OWNER-FILM-PERSON-v30.md')
_fn = {}; exec(open(D + 'facts-v30.py', encoding='utf-8').read(), _fn)
new = run(wa, wb, rd('LEAD-RELEASE-NOTE-v14.md'), rd('v30-OPEN-FOR-LEAD.md'), {'A': sa, 'B': sb}, _fn['F'])
cannot = [c for c in codes if c not in old]
print('checks in Part 4 and 5: %d' % len(codes)); print('fail on built v28: %d' % len(old & set(codes)))
print('do NOT fail on built v28 (cannot prove a change; reason must be given in v30-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v30: %s' % (sorted(new) or 'none'))
bad = len(new)
print('v30-fail-proof: %d problem(s)' % bad); sys.exit(1 if bad else 0)

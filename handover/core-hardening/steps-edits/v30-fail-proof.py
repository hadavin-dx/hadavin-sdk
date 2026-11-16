"""v30-fail-proof.py: runs the Part 7 checks of newchecks-v30.py (C185 to C209, one or more per finding of review-v29-security.md, review-v29-naive.md and review-v29-evidence.md)
on the BUILT v29 files (read only) and on the BUILT v30 files. Every check must fail on v29 or be listed as unable to fail there with the reason printed; none may fail on v30.
Usage: python3 -B -I v30-fail-proof.py. Exit 0 = none fails on v30 and every check that does not fail on v29 is listed."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v30.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 7 (v30, round 2)'):]
def run(A, B, NOTE, OPEN, SD, FF, ver):
    fails = {}
    def fl(c, m): fails.setdefault(c, []).append(m)
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=fl, F=FF, SEC=[], PAGEVER=ver)
    exec(head + '\n' + body, ns); return fails
codes = sorted(set(re.findall(r"\b(C(?:18[5-9]|19\d|20\d))\b", body)))
import importlib.util
spec = importlib.util.spec_from_file_location('b30', D + 'build-v30.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
_fn = {}; exec(open(D + 'facts-v30.py', encoding='utf-8').read(), _fn); FF = _fn['F']
def whole(ver, k, note, op):
    return bm.combine(rd('OWNER-SHEET-%s-%s.md' % (ver, k)), rd('OWNER-CARD-%s-%s.md' % (ver, k))) + '\n' + rd('OWNER-APPENDIX-%s-%s.md' % (ver, k)) + '\n' + rd('OWNER-FILM-PERSON-%s.md' % ver)
old = run(whole('v29', 'A', 0, 0), whole('v29', 'B', 0, 0), rd('LEAD-RELEASE-NOTE-v13.md'), rd('v29-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v29-A.md'), 'B': rd('OWNER-SHEET-v29-B.md')}, FF, 'v29')
new = run(whole('v30', 'A', 0, 0), whole('v30', 'B', 0, 0), rd('LEAD-RELEASE-NOTE-v14.md'), rd('v30-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v30-A.md'), 'B': rd('OWNER-SHEET-v30-B.md')}, FF, 'v30')
cannot = [c for c in codes if c not in old]
print('checks in Part 7: %d (%s to %s)' % (len(codes), codes[0], codes[-1])); print('fail on built v29: %d' % len([c for c in codes if c in old]))
for c in sorted(old): print('  v29 fails %s (%d line(s)); first: %s' % (c, len(old[c]), old[c][0][:100]))
print('do NOT fail on built v29 (cannot prove a change; reason in v30-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v30: %s' % (sorted(new) or 'none'))
for c in sorted(new): print('  v30 fails %s: %s' % (c, new[c][0][:100]))
print('v30-fail-proof: %d problem(s)' % len(new)); sys.exit(1 if new else 0)

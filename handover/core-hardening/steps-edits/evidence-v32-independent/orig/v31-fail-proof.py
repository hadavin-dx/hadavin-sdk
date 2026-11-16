"""v31-fail-proof.py: runs the Part 8 checks of newchecks-v31.py (C210 to C227, one or more per finding of review-v30-security.md, review-v30-naive.md and review-v30-evidence.md)
on the BUILT v30 files (read only) and on the BUILT v31 files. Every check must fail on v30 or be listed as unable to fail there with the reason printed; none may fail on v31.
Usage: python3 -B -I v31-fail-proof.py. Exit 0 = none fails on v31 and every check that does not fail on v30 is listed."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v31.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 8 (v31, round 3)'):]
def run(A, B, NOTE, OPEN, SD, FF, ver):
    fails = {}
    def fl(c, m): fails.setdefault(c, []).append(m)
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=fl, F=FF, SEC=[], PAGEVER=ver)
    exec(head + '\n' + body, ns); return fails
codes = sorted(set(re.findall(r"\b(C2(?:1\d|2\d))\b", body)))
import importlib.util
spec = importlib.util.spec_from_file_location('b31', D + 'build-v31.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
_fn = {}; exec(open(D + 'facts-v31.py', encoding='utf-8').read(), _fn); FF = _fn['F']
def whole(ver, k):
    return bm.combine(rd('OWNER-SHEET-%s-%s.md' % (ver, k)), rd('OWNER-CARD-%s-%s.md' % (ver, k))) + '\n' + rd('OWNER-APPENDIX-%s-%s.md' % (ver, k)) + '\n' + rd('OWNER-FILM-PERSON-%s.md' % ver)
old = run(whole('v30', 'A'), whole('v30', 'B'), rd('LEAD-RELEASE-NOTE-v14.md'), rd('v30-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v30-A.md'), 'B': rd('OWNER-SHEET-v30-B.md')}, FF, 'v30')
new = run(whole('v31', 'A'), whole('v31', 'B'), rd('LEAD-RELEASE-NOTE-v15.md'), rd('v31-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v31-A.md'), 'B': rd('OWNER-SHEET-v31-B.md')}, FF, 'v31')
cannot = [c for c in codes if c not in old]
print('checks in Part 8: %d (%s to %s)' % (len(codes), codes[0], codes[-1])); print('fail on built v30: %d' % len([c for c in codes if c in old]))
for c in sorted(old): print('  v30 fails %s (%d line(s)); first: %s' % (c, len(old[c]), old[c][0][:100]))
print('do NOT fail on built v30 (cannot prove a change; reason in v31-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v31: %s' % (sorted(new) or 'none'))
for c in sorted(new): print('  v31 fails %s: %s' % (c, new[c][0][:100]))
print('v31-fail-proof: %d problem(s)' % len(new)); sys.exit(1 if new else 0)

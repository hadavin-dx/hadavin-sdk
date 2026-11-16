"""v33-fail-proof.py: runs the Part 9 checks of newchecks-v33.py (C228 to C262, one or more per finding of review-v31 and review-v32 security, naive and evidence reports)
on the BUILT v32 files (read only) and on the BUILT v33 files. Every check must fail on v32 or be listed as unable to fail there with the reason printed; none may fail on v33.
Usage: python3 -B -I v33-fail-proof.py. Exit 0 = none fails on v33. Prints which checks do not fail on v32."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v33.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 9 (v33'):]
def run(A, B, NOTE, OPEN, SD, FF, ver):
    fails = {}
    def fl(c, m): fails.setdefault(c, []).append(m)
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=fl, F=FF, SEC=[], PAGEVER=ver)
    exec(head + '\nimport os as _os\n' + body, ns); return fails
codes = sorted(set(re.findall(r"\b(C2(?:2[89]|[3-9]\d))\b", body)))
import importlib.util
spec = importlib.util.spec_from_file_location('b32', D + 'build-v33.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
def facts(v):
    d = {}; exec(open(D + 'facts-%s.py' % v, encoding='utf-8').read(), d); return d['F']
def whole(ver, k):
    return bm.combine(rd('OWNER-SHEET-%s-%s.md' % (ver, k)), rd('OWNER-CARD-%s-%s.md' % (ver, k))) + '\n' + rd('OWNER-APPENDIX-%s-%s.md' % (ver, k)) + '\n' + rd('OWNER-FILM-PERSON-%s.md' % ver)
old = run(whole('v32', 'A'), whole('v32', 'B'), rd('LEAD-RELEASE-NOTE-v16.md'), rd('v32-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v32-A.md'), 'B': rd('OWNER-SHEET-v32-B.md')}, facts('v32'), 'v32')
new = run(whole('v33', 'A'), whole('v33', 'B'), rd('LEAD-RELEASE-NOTE-v17.md'), rd('v33-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v33-A.md'), 'B': rd('OWNER-SHEET-v33-B.md')}, facts('v33'), 'v33')
cannot = [c for c in codes if c not in old]
print('checks in Part 9: %d (%s to %s)' % (len(codes), codes[0], codes[-1])); print('fail on built v32: %d' % len([c for c in codes if c in old]))
for c in sorted(old): print('  v32 fails %s (%d line(s)); first: %s' % (c, len(old[c]), old[c][0][:100]))
print('do NOT fail on built v32 (cannot prove a change; reason in v33-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v33: %s' % (sorted(new) or 'none'))
for c in sorted(new): print('  v33 fails %s: %s' % (c, new[c][0][:100]))
print('v33-fail-proof: %d problem(s)' % len(new)); sys.exit(1 if new else 0)

"""v36-fail-proof.py: runs the Part 9 checks of newchecks-v36.py (C228 to C280, one or more per finding of review-v31 to v35 security, naive and evidence reports; C274 to C280 are the round 7 meaning checks)
on the BUILT v35 files (read only) and on the BUILT v36 files. Every check must fail on v35 or be listed as unable to fail there with the reason printed; none may fail on v36.
Usage: python3 -B -I v36-fail-proof.py. Exit 0 = none fails on v36. Prints which checks do not fail on v35."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
src = rd('newchecks-v36.py'); head = src[:src.index('# ---- Part 1')]; body = src[src.index('# ---- Part 9 (v36'):]
def run(A, B, NOTE, OPEN, SD, FF, ver):
    fails = {}
    def fl(c, m): fails.setdefault(c, []).append(m)
    ns = dict(rd=rd, A=A, B=B, NOTE=NOTE, OPEN=OPEN, SHEETS_DISK=SD, D=D, fail=fl, F=FF, SEC=[], PAGEVER=ver)
    exec(head + '\nimport os as _os\n' + body, ns); return fails
codes = sorted(set(re.findall(r"\b(C2(?:2[89]|[3-9]\d))\b", body)))
import importlib.util
spec = importlib.util.spec_from_file_location('b32', D + 'build-v36.py'); bm = importlib.util.module_from_spec(spec); sys.argv = ['x', D]; spec.loader.exec_module(bm)
def facts(v):
    d = {}; exec(open(D + 'facts-%s.py' % v, encoding='utf-8').read(), d); d['F'].setdefault('bs_pair', ' '.join(d['F']['bs'].split()[-5:])); return d['F']
def whole(ver, k):
    return bm.combine(rd('OWNER-SHEET-%s-%s.md' % (ver, k)), rd('OWNER-CARD-%s-%s.md' % (ver, k))) + '\n' + rd('OWNER-APPENDIX-%s-%s.md' % (ver, k)) + '\n' + rd('OWNER-FILM-PERSON-%s.md' % ver)
old = run(whole('v35', 'A'), whole('v35', 'B'), rd('LEAD-RELEASE-NOTE-v19.md'), rd('v35-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v35-A.md'), 'B': rd('OWNER-SHEET-v35-B.md')}, facts('v35'), 'v35')
new = run(whole('v36', 'A'), whole('v36', 'B'), rd('LEAD-RELEASE-NOTE-v20.md'), rd('v36-OPEN-FOR-LEAD.md'), {'A': rd('OWNER-SHEET-v36-A.md'), 'B': rd('OWNER-SHEET-v36-B.md')}, facts('v36'), 'v36')
cannot = [c for c in codes if c not in old]
print('checks in Part 9: %d (%s to %s)' % (len(codes), codes[0], codes[-1])); print('fail on built v35: %d' % len([c for c in codes if c in old]))
for c in sorted(old): print('  v35 fails %s (%d line(s)); first: %s' % (c, len(old[c]), old[c][0][:100]))
print('do NOT fail on built v35 (cannot prove a change; reason in v36-CHANGES.md): %s' % (cannot or 'none'))
print('fail on built v36: %s' % (sorted(new) or 'none'))
for c in sorted(new): print('  v36 fails %s: %s' % (c, new[c][0][:100]))
print('v36-fail-proof: %d problem(s)' % len(new)); sys.exit(1 if new else 0)

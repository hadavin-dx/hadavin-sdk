"""Check (c). In FINDINGS.md and lanes/*.md: '<path>.json:<NodeName>' must name a node that exists (path rel. handover/demo or handover/); '<path>.(md|py|txt|sql|sh):<n>' must be a line <= file length. Run from repo root. Exit 0/1."""
import glob, json, os, re, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); bases = [os.path.join(R, 'demo'), R, os.path.join(R, '..')]
def find(p):
    for b in bases:
        q = os.path.join(b, p)
        if os.path.isfile(q): return q
bad = []; n = 0
for f in [os.path.join(R, 'flows-audit', 'FINDINGS.md')] + sorted(glob.glob(os.path.join(R, 'flows-audit', 'lanes', '*.md'))):
    if not os.path.exists(f): continue
    t = open(f).read()
    for p, node in re.findall(r'([\w./-]+\.json):([A-Za-z][A-Za-z0-9_]*)', t):
        n += 1; q = find(p)
        if not q or node not in {x['name'] for x in json.load(open(q)).get('nodes', [])}: bad.append(f'{os.path.basename(f)}: {p}:{node}')
    for p, ln in re.findall(r'([\w./-]+\.(?:md|py|txt|sql|sh)):(\d+)', t):
        n += 1; q = find(p)
        if not q or int(ln) > sum(1 for _ in open(q, errors='replace')): bad.append(f'{os.path.basename(f)}: {p}:{ln}')
print('FAIL unresolved: ' + '; '.join(bad[:20]) if bad else f'PASS {n} references'); sys.exit(1 if bad else 0)

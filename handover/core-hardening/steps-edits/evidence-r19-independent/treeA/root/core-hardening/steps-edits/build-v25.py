"""Builds every v25 text from its source plus the one facts file (facts-v25.py), so no copy can drift:
  OWNER-SHEET-v25-SOURCE.md  -> OWNER-SHEET-v25-A.md and OWNER-SHEET-v25-B.md (older-key kind A or B; the finished sheets hold no marker)
  LEAD-RELEASE-NOTE-v9-SOURCE.md -> LEAD-RELEASE-NOTE-v9.md ;  v25-OPEN-FOR-LEAD-SOURCE.md -> v25-OPEN-FOR-LEAD.md
Placeholders {{name}} come from facts-v25.py; an unknown placeholder, a marker left over or unbalanced markers stop the build.
Usage: python3 build-v25.py [folder]"""
import os, re, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
ns = {}
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'facts-v25.py'), encoding='utf-8').read(), ns)
FACTS = ns['F']
def fill(s):
    def r(m):
        if m.group(1) not in FACTS: raise SystemExit('unknown placeholder {{%s}}' % m.group(1))
        return FACTS[m.group(1)]
    return re.sub(r'\{\{(\w+)\}\}', r, s)
def variant(s, keep):
    drop = 'B' if keep == 'A' else 'A'
    s = re.sub(r'\[\[%s:.*?\]\]' % drop, '', s, flags=re.S)
    return re.sub(r'\[\[%s:\s?(.*?)\]\]' % keep, r'\1', s, flags=re.S)
def tidy(o):
    o = re.sub(r'[ \t]+\n', '\n', o); o = re.sub(r' {2,}(?=[.,;:)])', '', o); return o.replace('( ', '(')
def build():
    out = {}
    src = open(D + 'OWNER-SHEET-v25-SOURCE.md', encoding='utf-8').read()
    assert src.count('[[') == src.count(']]'), 'unbalanced markers'
    for k in 'AB':
        o = tidy(fill(variant(src, k)))
        assert '[[' not in o and ']]' not in o and '{{' not in o, 'leftover in ' + k
        out['OWNER-SHEET-v25-%s.md' % k] = o
    for s, d in (('LEAD-RELEASE-NOTE-v9-SOURCE.md', 'LEAD-RELEASE-NOTE-v9.md'), ('v25-OPEN-FOR-LEAD-SOURCE.md', 'v25-OPEN-FOR-LEAD.md')):
        if os.path.exists(D + s):
            o = fill(open(D + s, encoding='utf-8').read()); assert '{{' not in o; out[d] = o
    return out
if __name__ == '__main__':
    for n, o in build().items():
        open(D + n, 'w', encoding='utf-8').write(o); print(n, len(o.split()), 'words')

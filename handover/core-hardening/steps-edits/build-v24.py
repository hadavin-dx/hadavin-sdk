"""Builds OWNER-SHEET-v24-A.md and OWNER-SHEET-v24-B.md from the one source OWNER-SHEET-v24-SOURCE.md.
Keeps [[A: ...]] text for A and [[B: ...]] text for B, removes the other kind and all markers. Fails if any marker is left or if a variant is unbalanced.
Usage: python3 build-v24.py [folder]  (default: this folder)"""
import os, re, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
def variant(s, keep):
    drop = 'B' if keep == 'A' else 'A'
    s = re.sub(r'\[\[%s:.*?\]\]' % drop, '', s, flags=re.S)
    return re.sub(r'\[\[%s:(.*?)\]\]' % keep, lambda m: m.group(1).strip(' ') if m.group(1).startswith(' ') else m.group(1), s, flags=re.S)
src = open(D + 'OWNER-SHEET-v24-SOURCE.md', encoding='utf-8').read()
assert src.count('[[') == src.count(']]'), 'unbalanced markers'
for k in 'AB':
    out = variant(src, k)
    out = re.sub(r' +\n', '\n', out)
    out = re.sub(r'  +(?=[.,;:)])', '', out)
    out = out.replace('( ', '(')
    assert '[[' not in out and ']]' not in out, 'marker left in ' + k
    # the sheet title says which kind it is only in the file name, never in the text
    open(D + 'OWNER-SHEET-v24-%s.md' % k, 'w', encoding='utf-8').write(out)
    print(k, len(out.split()), 'words')

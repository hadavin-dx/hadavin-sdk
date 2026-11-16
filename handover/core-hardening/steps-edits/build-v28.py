"""Builds every v28 text from its source plus the one facts file (facts-v28.py), so no copy can drift:
  OWNER-SHEET-v28-SOURCE.md  -> OWNER-SHEET-v28-A.md and OWNER-SHEET-v28-B.md (older-key kind A or B; the finished sheets hold no marker)
  LEAD-RELEASE-NOTE-v12-SOURCE.md -> LEAD-RELEASE-NOTE-v12.md ;  v28-OPEN-FOR-LEAD-SOURCE.md -> v28-OPEN-FOR-LEAD.md
Placeholders {{name}} come from facts-v28.py; an unknown placeholder, a marker left over or unbalanced markers stop the build.
Usage: python3 build-v28.py [folder]"""
import os, re, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
ns = {}
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'facts-v28.py'), encoding='utf-8').read(), ns)
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
POINTER = ("### THE CARD (the separate printed page OWNER-CARD-v28-%s.md)\nPrint that page and keep it beside you. Every step called \"the card\", every danger sign W1 to W9 and the cancel lists L1 to L5 are on that page only; "
           "this sheet does not repeat them. Fill its blanks before you press create of the run key.\n\n")
def split(o):
    """returns (sheet text with the card and film blocks cut out, card text, film text)"""
    c0 = o.index('<<CARD\n'); c1 = o.index('CARD>>\n'); f0 = o.index('<<FILM\n'); f1 = o.index('FILM>>')
XX
def combine(sheet, card, film):
    """the whole text a check reads: the card put back in place, the film page appended"""
    i = sheet.index('### THE CARD'); j = sheet.index('### The rules')
    return sheet[:i] + card.rstrip('\n') + '\n\n' + sheet[j:].rstrip('\n') + '\n\n' + film
def build():
    out = {}
    src = open(D + 'OWNER-SHEET-v28-SOURCE.md', encoding='utf-8').read()
    assert src.count('[[') == src.count(']]'), 'unbalanced markers'
    films = []
    for k in 'AB':
        o = tidy(fill(variant(src, k)))
        assert '[[' not in o and ']]' not in o and '{{' not in o, 'leftover in ' + k
        sheet, card, film = split(o)
        out['OWNER-SHEET-v28-%s.md' % k] = sheet.replace('@@POINTER@@', POINTER % k)
        out['OWNER-CARD-v28-%s.md' % k] = card; films.append(film)
    assert films[0] == films[1], 'the film page differs between A and B'
    out['OWNER-FILM-v28.md'] = films[0]
    for s, d in (('LEAD-RELEASE-NOTE-v12-SOURCE.md', 'LEAD-RELEASE-NOTE-v12.md'), ('v28-OPEN-FOR-LEAD-SOURCE.md', 'v28-OPEN-FOR-LEAD.md')):
        if os.path.exists(D + s):
            o = fill(open(D + s, encoding='utf-8').read())
            if d.startswith('LEAD'): o = o.replace('@@NUMBERS_SAMPLE@@', sample_block(src))
            assert '{{' not in o; out[d] = o
    return out
def sample_block(src):
    """the numbers message sample, generated once from the owner sheet source (the note embeds it, so the two cannot drift)"""
    i = src.index('SAMPLE (made-up values, never real):'); j = src.index('```', src.index('```', i) + 3) + 3
    return tidy(fill(variant(src[i:j], 'A'))) + '\n(sheet B differs only in its older key line: it adds "Older-key time: ' + FACTS['okb'] + ' on the run day" and says the older key is left valid)'
if __name__ == '__main__':
    for n, o in build().items():
        open(D + n, 'w', encoding='utf-8').write(o); print(n, len(o.split()), 'words')

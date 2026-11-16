"""Builds every v30 text from its source plus the one facts file (facts-v30.py), so no copy can drift:
  OWNER-SHEET-v30-SOURCE.md  -> OWNER-SHEET-v30-A.md and OWNER-SHEET-v30-B.md (older-key kind A or B; the finished sheets hold no marker)
  LEAD-RELEASE-NOTE-v14-SOURCE.md -> LEAD-RELEASE-NOTE-v14.md ;  v30-OPEN-FOR-LEAD-SOURCE.md -> v30-OPEN-FOR-LEAD.md
Placeholders {{name}} come from facts-v30.py; an unknown placeholder, a marker left over or unbalanced markers stop the build.
Usage: python3 build-v30.py [folder]"""
import os, re, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
ns = {}
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'facts-v30.py'), encoding='utf-8').read(), ns)
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
def cut(o, name):
    i = o.index('<<%s\n' % name); j = o.index('%s>>\n' % name)
    return o[:i] + o[j + len(name) + 3:], o[i + len(name) + 3:j].strip('\n') + '\n'
def unmark(o, name):
    return o.replace('<<%s\n' % name, '').replace('%s>>\n' % name, '')
def appendix_blocks(o):
    """the long detail leaves the sheet and goes to the appendix in order: whole blocks <<F1 title ... F1>>, and inline cuts (((F5 title:: text ))) that leave the pointer "(appendix 5)"; the sheet keeps its own short text beside each"""
    parts = {}
    def add(n, t, body):
        parts.setdefault(n, [t, []])[1].append(body.strip('\n'))
    def r(m):
        add(m.group(1), m.group(2), m.group(3)); return ''
    o = re.sub(r'<<F(\d+) ([^\n]*)\n(.*?)\nF\1>>\n?', r, o, flags=re.S)
    def r2(m):
        add(m.group(1), m.group(2), m.group(3)); return ' (appendix %s)' % m.group(1) + (' ' if m.group(3).endswith(' ') else '')
    o = re.sub(r' ?\(\(\(F(\d+) ([^\n:]*?):: (.*?)\)\)\)(?!\))', r2, o, flags=re.S)
    return o, [(int(n), v[0], '\n\n'.join(v[1])) for n, v in sorted(parts.items(), key=lambda kv: int(kv[0]))]
POINTER = ("### THE CARD, sheet %s (a separate printed page OWNER-CARD-v30-%s.md)\nPrint that page and keep it beside you. Every step called \"the card\", every danger sign W1 to W9 and the cancel lists L1 to L5 are on that page only; "
           "this sheet does not repeat them. Fill its blanks before you press create of the run key.\n\n")
def split(o, k):
    """returns (sheet text with the card cut out, card page, appendix text, film person page)"""
    o, film = cut(o, 'FILMPERSON')
    o, parts = appendix_blocks(o)
    i = o.index('<<CARD\n'); j = o.index('CARD>>\n')
    card = o[i + 7:j].strip('\n') + '\n'
    o = o[:i] + '@@CARD@@' + o[j + 8:]
    o = unmark(o, 'NUMBERS')
    sheet = o.replace('@@CARD@@', POINTER % (k, k)).rstrip('\n') + '\n\n---\nEnd of sheet %s (OWNER-SHEET-v30-%s.md).\n' % (k, k)
    app = '# Owner appendix v30, sheet %s: the long detail (it binds you the same as the sheet; each part says where the sheet points to it)\n' % k
    for n, t, body in parts: app += '\n## Appendix part %s: %s\n%s\n' % (n, t, body)
    app += '\n---\nEnd of the appendix, sheet %s (OWNER-APPENDIX-v30-%s.md).\n' % (k, k)
    return sheet, card, app, film
def combine(sheet, card):
    """the whole text a check reads: the card page put back in place of its pointer"""
    i = sheet.index('### THE CARD'); j = sheet.index('### The rules')
    return sheet[:i] + card.rstrip('\n') + '\n\n' + sheet[j:]
def build():
    out = {}
    src = open(D + 'OWNER-SHEET-v30-SOURCE.md', encoding='utf-8').read()
    assert src.count('[[') == src.count(']]'), 'unbalanced markers'
    films = []
    for k in 'AB':
        o = tidy(fill(variant(src, k)))
        assert '[[' not in o and ']]' not in o and '{{' not in o, 'leftover in ' + k
        sheet, card, app, film = split(o, k)
        out['OWNER-SHEET-v30-%s.md' % k] = sheet; out['OWNER-CARD-v30-%s.md' % k] = card; out['OWNER-APPENDIX-v30-%s.md' % k] = app; films.append(film)
    assert films[0] == films[1], 'the film person page differs between A and B'
    out['OWNER-FILM-PERSON-v30.md'] = films[0]
    wc = {}
    for k in 'AB':
        w = [len(out[x % k].split()) for x in ('OWNER-SHEET-v30-%s.md', 'OWNER-CARD-v30-%s.md', 'OWNER-APPENDIX-v30-%s.md')] + [len(out['OWNER-FILM-PERSON-v30.md'].split())]
        wc.update({'WC_SHEET_' + k: w[0], 'WC_CARD_' + k: w[1], 'WC_APP_' + k: w[2], 'WC_FILMP_' + k: w[3], 'WC_ALL_' + k: w[0] + w[2] + w[3]})
    for s, d in (('LEAD-RELEASE-NOTE-v14-SOURCE.md', 'LEAD-RELEASE-NOTE-v14.md'), ('v30-OPEN-FOR-LEAD-SOURCE.md', 'v30-OPEN-FOR-LEAD.md')):
        if os.path.exists(D + s):
            o = fill(open(D + s, encoding='utf-8').read())
            if d.startswith('LEAD'): o = o.replace('@@NUMBERS_SAMPLE@@', sample_block(src))
            for kk, vv in wc.items(): o = o.replace('@@%s@@' % kk, '{:,}'.format(vv))
            assert '{{' not in o and '@@WC_' not in o; out[d] = o
    return out
def sample_block(src):
    """the numbers message sample, generated once from the owner sheet source (the note embeds it, so the two cannot drift)"""
    i = src.index('SAMPLE (made-up values, never real):'); j = src.index('```', src.index('```', i) + 3) + 3
    return tidy(fill(variant(src[i:j], 'A'))) + '\n(sheet B differs from sheet A in its sheet letter, its older key line (the older key is left valid until the older-key time) and the older-key steps)'
if __name__ == '__main__':
    for n, o in build().items():
        open(D + n, 'w', encoding='utf-8').write(o); print(n, len(o.split()), 'words')

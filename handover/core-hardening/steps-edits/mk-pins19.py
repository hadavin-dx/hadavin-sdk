# builds r19-pins.txt: the golden list of every sentence of EDITS.md with its number of copies (the one source of truth the checker compares EDITS.md to)
import re, collections, sys
def sentences(t):
    out = []
    for l in t.split('\n'):
        l = l.strip()
        if not l: continue
        out += [s.strip() for s in re.split(r'(?<=[.!?;]) +', l) if s.strip()]
    return out
if __name__ == '__main__':
    c = collections.Counter(sentences(open('EDITS.md', encoding='utf-8').read()))
    with open('r19-pins.txt', 'w', encoding='utf-8') as f:
        for s, n in sorted(c.items()): f.write('%d\t%s\n' % (n, s))
    print('pins', len(c), 'distinct sentences', sum(c.values()), 'total')

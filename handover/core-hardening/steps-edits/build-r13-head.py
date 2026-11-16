"""Round 13 builder: anchored patches of EDITS.md (every old string asserted to occur exactly once).
Reads EDITS.round12.md, writes EDITS.md. No vendor words, no secrets."""
import re, sys
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
T = open(D + 'EDITS.round12.md', encoding='utf-8').read()
errs = []

def sub(old, new, n=1):
    global T
    c = T.count(old)
    if c != n:
        errs.append(f'anchor count {c} (want {n}): {old[:70]!r}'); return
    T = T.replace(old, new)

def row_span(rid):
    i = T.index(f'\n### {rid}: ') + 1
    m = re.compile(r'\n### E-\d\d: |\n## Lines checked and found consistent').search(T, i + 5)
    return i, (m.start() + 1 if m else len(T))

def rsub(rid, old, new, n=1):
    global T
    i, j = row_span(rid)
    seg = T[i:j]
    c = seg.count(old)
    if c != n:
        errs.append(f'{rid}: anchor count {c} (want {n}): {old[:70]!r}'); return
    T = T[:i] + seg.replace(old, new) + T[j:]

def why_add(rid, text):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    idx = [n for n, l in enumerate(lines) if l.startswith('Why:')]
    if len(idx) != 1:
        errs.append(f'{rid}: Why lines {len(idx)}'); return
    lines[idx[0]] = lines[idx[0]].rstrip() + ' ' + text
    T = T[:i] + '\n'.join(lines) + T[j:]

def set_why(rid, text):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    idx = [n for n, l in enumerate(lines) if l.startswith('Why:')]
    if len(idx) != 1:
        errs.append(f'{rid}: Why lines {len(idx)}'); return
    lines[idx[0]] = text
    T = T[:i] + '\n'.join(lines) + T[j:]

def _find_new(lines, nth):
    n_new = -1
    for k, l in enumerate(lines):
        if re.match(r'^NEW[^\n]*:$', l) and k + 1 < len(lines) and lines[k + 1] == '~~~~':
            n_new += 1
            if n_new == nth:
                e = k + 2
                while lines[e] != '~~~~': e += 1
                return k + 2, e
    return None

def set_new(rid, body, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block {nth} not found'); return
    lines[r[0]:r[1]] = body.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

def edit_new(rid, pairs, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block {nth} not found'); return
    body = '\n'.join(lines[r[0]:r[1]])
    for old, new in pairs:
        c = body.count(old)
        if c != 1:
            errs.append(f'{rid} NEW: anchor count {c}: {old[:70]!r}'); return
        body = body.replace(old, new)
    lines[r[0]:r[1]] = body.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

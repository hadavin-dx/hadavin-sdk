# EVIDENCE RUNNER A4 script. Read-only on the target; writes only the evidence file and tree-hits file.
import json, re, os, sys, subprocess, hashlib, datetime, glob
FA = sys.argv[1]; OUT = sys.argv[2]; TREE = sys.argv[3]
D = os.path.join(FA, 'handover/demo')
out = []
def w(s=''): out.append(s)
SENS = re.compile(r'(pass|token|secret|key|credential|authorization|bearer)', re.I)
LONG = re.compile(r'^[A-Za-z0-9_\-/+=]{32,}$')
def mask(path, v):
    s = json.dumps(v, sort_keys=True, ensure_ascii=False)
    last = path.split('.')[-1]
    if SENS.search(last) and not isinstance(v, (dict, list)) and v not in ('', None, True, False):
        return '[MASKED]'
    s = re.sub(r'"([^"]{32,})"', lambda m: '[MASKED]' if LONG.match(m.group(1)) else m.group(0), s)
    return s
def flat(o, p=''):
    r = {}
    if isinstance(o, dict):
        for k, v in o.items(): r.update(flat(v, f'{p}.{k}' if p else k))
        if not o: r[p] = {}
    elif isinstance(o, list):
        for i, v in enumerate(o): r.update(flat(v, f'{p}[{i}]'))
        if not o: r[p] = []
    else: r[p] = o
    return r
def load(path):
    d = json.load(open(path)); return d
def conns(d):
    r = {}
    for src, outs in d.get('connections', {}).items():
        for typ, branches in outs.items():
            for i, br in enumerate(branches):
                r[f'{src}/{typ}[{i}]'] = sorted(f"{c['node']}:{c.get('type')}:{c.get('index')}" for c in (br or []))
    return r
def diff(a, b, la, lb):
    A, B = load(a), load(b)
    na = {n['name']: n for n in A['nodes']}; nb = {n['name']: n for n in B['nodes']}
    rows = [('kind', 'node/connection', 'field path', la, lb)]
    for n in na:
        if n not in nb: rows.append(('REMOVED node', n, '(type %s)' % na[n].get('type'), '-', ''))
    for n in nb:
        if n not in na: rows.append(('ADDED node', n, '(type %s)' % nb[n].get('type'), '', '-'))
    for n in na:
        if n in nb:
            fa, fb = flat(na[n]), flat(nb[n])
            for k in sorted(set(fa) | set(fb)):
                if fa.get(k, '<absent>') != fb.get(k, '<absent>'):
                    va = mask(k, fa[k]) if k in fa else '<absent>'; vb = mask(k, fb[k]) if k in fb else '<absent>'
                    rows.append(('CHANGED node', n, k, va, vb))
    ca, cb = conns(A), conns(B)
    for k in sorted(set(ca) | set(cb)):
        if ca.get(k) != cb.get(k):
            rows.append(('CHANGED connection', k, '', json.dumps(ca.get(k, '<absent>')), json.dumps(cb.get(k, '<absent>'))))
    for k in A:
        if k not in ('nodes', 'connections') and A.get(k) != B.get(k):
            rows.append(('CHANGED top-level', k, '', mask(k, A.get(k)), mask(k, B.get(k))))
    return rows
def table(rows):
    w('| ' + ' | '.join(rows[0]) + ' |'); w('|' + '---|' * len(rows[0]))
    for r in rows[1:]:
        w('| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in r) + ' |')
    if len(rows) == 1: w('(no differences found by this script)')
FL = ['mf-hook', 'mf-form', 'mf-recovery', 'mf-sub-crm-mail']
w('# Evidence A4'); 
head = open(os.path.join(FA, '.git/HEAD')).read().strip() if os.path.exists(os.path.join(FA, '.git/HEAD')) else None
w(f'sha: requested 35235ace26a516d932e73542c235875f390f333d; on-disk check: target has no .git directory, so the sha could NOT be verified from disk ({head})')
w('date UTC: ' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
w('Values that look like credentials are shown as [MASKED]. No judging in this file.')
w('\n## Part 1a: real-v5 vs film-v5 (left = real-v5, right = film-v5)')
for f in FL:
    w(f'\n### {f}.json'); table(diff(f'{D}/n8n-flows-real-v5/{f}.json', f'{D}/n8n-flows-film-v5/{f}.json', 'real-v5', 'film-v5'))
w('\n## Part 1b: mf-form vs mf-hook (left = mf-form, right = mf-hook)')
for v in ('real-v5', 'film-v5'):
    w(f'\n### {v}'); table(diff(f'{D}/n8n-flows-{v}/mf-form.json', f'{D}/n8n-flows-{v}/mf-hook.json', 'mf-form', 'mf-hook'))
w('\n## Part 1c: V5-NODE-DIFF.txt first 40 lines')
p = f'{D}/n8n-flows-real-v5/V5-NODE-DIFF.txt'; L = open(p, encoding='utf-8', errors='replace').read().split('\n')
w(f'total lines: {len(L)}'); w('```')
for l in L[:40]: w(l)
w('```')
# Part 2
cl = open(os.path.join(FA, 'handover/flows-audit/CUT-LIST.md'), encoding='utf-8').read()
toks = set(re.findall(r'[A-Za-z0-9_][\w./-]*\.(?:md|py|txt|sql|json|png|html)\b', cl)) | set(re.findall(r'(?<![\w/-])(?:n8n-[a-z0-9-]+|sandbox-scratch-logs)(?:/[\w-]+)?(?![\w-])', cl))
toks = {t for t in toks if not t.startswith('.')}
items = sorted(toks)
w('\n## Part 2: item paths extracted from CUT-LIST.md (tokens only, verdicts not copied)')
w(', '.join(items))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def filepair(a, b):
    w(f'\n### {os.path.relpath(a, D)}  vs  {os.path.relpath(b, D)}')
    for p in (a, b):
        if os.path.isfile(p): w(f'- {os.path.relpath(p, D)}: size {os.path.getsize(p)} sha256 {sha(p)}')
        else: w(f'- {os.path.relpath(p, D)}: NOT FOUND on disk'); 
    if os.path.isfile(a) and os.path.isfile(b):
        r = subprocess.run(['diff', a, b], capture_output=True, text=True, errors='replace').stdout.split('\n')
        if r and r[-1] == '': r = r[:-1]
        w(f'diff total lines: {len(r)}'); w('```')
        for l in r[:80]: w(mask_line(l))
        w('```')
def mask_line(l):
    return re.sub(r'"([^"]{32,})"', lambda m: '[MASKED]' if LONG.match(m.group(1)) else m.group(0), l)
def folderpair(a, b):
    A, B = os.path.join(D, a), os.path.join(D, b)
    w(f'\n### FOLDER PAIR {a}  vs  {b}')
    fa = sorted(os.listdir(A)) if os.path.isdir(A) else None; fb = sorted(os.listdir(B)) if os.path.isdir(B) else None
    if fa is None or fb is None: w(f'folder missing: {a}={fa is not None} {b}={fb is not None}'); return
    w(f'only in {a}: {sorted(set(fa)-set(fb))}'); w(f'only in {b}: {sorted(set(fb)-set(fa))}')
    for f in sorted(set(fa) & set(fb)):
        if os.path.isfile(os.path.join(A, f)): filepair(os.path.join(A, f), os.path.join(B, f))
pairs = [('n8n-flows/v1-superseded', 'n8n-flows'), ('n8n-flows', 'n8n-flows-v3'), ('n8n-flows-v3', 'n8n-flows-v4'), ('n8n-flows-v4', 'n8n-flows-real-v5'),
         ('n8n-flows-real', 'n8n-flows-real-v3'), ('n8n-flows-real-v3', 'n8n-flows-real-v4'), ('n8n-flows-real-v4', 'n8n-flows-real-v5'),
         ('n8n-flows-film', 'n8n-flows-film-v3'), ('n8n-flows-film-v3', 'n8n-flows-film-v4'), ('n8n-flows-film-v4', 'n8n-flows-film-v5'),
         ('n8n-table-screen', 'n8n-table-screen-v2')]
w('\n## Part 2a: folder pairs named in the CUT-LIST table (the "n8n-flows -> v3" row and the "n8n-flows-v4 -> real-v5 / film-v5" row: both successors diffed)')
for a, b in pairs: folderpair(a, b)
folderpair('n8n-flows-v4', 'n8n-flows-film-v5')
w('\n## Part 2b: file pairs named in the document-duplicate and table-definition lines')
fp = [('n8n-flows/PAGE-STATEMENTS-DRAFT.md', 'n8n-flows/PAGE-STATEMENTS-V4.md'), ('n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md', 'n8n-flows/PAGE-STATEMENTS-V4.md'),
      ('n8n-flows/PAGE-STATEMENTS-DRAFT.md', 'n8n-flows/PAGE-STATEMENTS-V4-DRAFT.md'),
      ('AUDIT-PAGE-STATEMENTS-V4.md', 'n8n-flows/PAGE-STATEMENTS-V4.md'), ('AUDIT-VIDEO-RUNSHEET.md', 'VIDEO-RUNSHEET.md'),
      ('n8n-flows/mf_leads.sql', 'n8n-flows-v3/mf_leads.sql'), ('n8n-flows-v3/mf_leads.sql', 'n8n-flows-v4/mf_leads.sql'), ('n8n-flows/mf_leads.sql', 'n8n-flows-v4/mf_leads.sql'),
      ('n8n-flows-real-v5/V5-README.md', 'n8n-flows-film-v5/V5-README.md')]
for a, b in fp: filepair(os.path.join(D, a), os.path.join(D, b))
# Part 3
w('\n## Part 3: referrer table')
docs = [os.path.join(FA, 'handover/README.md'), os.path.join(FA, 'handover/STATUS.md'), os.path.join(FA, 'handover/STUDIO-RULES.md'), f'{D}/VIDEO-RUNSHEET.md']
docs += sorted(glob.glob(FA + '/handover/*/README.md')) + sorted(glob.glob(FA + '/**/V5-README.md', recursive=True)) + sorted(glob.glob(FA + '/**/RUN-ON-LAPTOP*', recursive=True))
docs = [d for d in dict.fromkeys(docs) if os.path.isfile(d)]
w('live documents searched: ' + ', '.join(os.path.relpath(d, FA) for d in docs))
w('Match rule: item name not preceded or followed by [A-Za-z0-9_-] (so "n8n-flows" does not match "n8n-flows-v3"); for paths also the last path segment is searched.')
allfiles = []
for r, ds, fs in os.walk(FA):
    ds[:] = [x for x in ds if x != '.git']
    for f in fs: allfiles.append(os.path.join(r, f))
def textlines(p):
    try:
        b = open(p, 'rb').read()
        if b'\0' in b[:4096]: return None
        return b.decode('utf-8', 'replace').split('\n')
    except Exception: return None
cache = {}
for p in allfiles:
    t = textlines(p)
    if t is not None: cache[p] = t
tree = []
w('\n| item | scope | referrer file:line | line text |'); w('|---|---|---|---|')
for it in items:
    names = {it}
    if '/' in it: names.add(it.rsplit('/', 1)[1])
    pat = re.compile('(?<![A-Za-z0-9_-])(' + '|'.join(re.escape(n) for n in sorted(names)) + ')(?![A-Za-z0-9_-])')
    live = 0; whole = 0
    for p, t in cache.items():
        for i, l in enumerate(t, 1):
            if pat.search(l):
                rel = os.path.relpath(p, FA); txt = l.strip()[:200].replace('|', '\\|')
                if p in docs: w(f'| {it} | live-doc | {rel}:{i} | {txt} |'); live += 1
                tree.append(f'{it}\t{rel}:{i}\t{l.strip()[:200]}'); whole += 1
    if live == 0: w(f'| {it} | live-doc | none found | |')
    w(f'| {it} | whole fa/ tree | {whole} hit(s) in total (all listed in evidence-A4-tree-hits.tsv) | |')
open(OUT, 'w').write('\n'.join(out) + '\n'); open(TREE, 'w').write('\n'.join(tree) + '\n')

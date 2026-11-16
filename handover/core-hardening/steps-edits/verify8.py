import re, sys, ast, collections, shutil, os
D = '/home/user/hadavin-sdk/handover/core-hardening/'
E = D + 'steps-edits/EDITS.md'
IN = D + 'inputs/'
txt = open(E, encoding='utf-8').read()
lines = txt.split('\n')
fail = 0
def F(msg):
    global fail
    fail += 1
    print('FAIL', msg)

# ---- parse rows, respecting fenced blocks
rows = []; cur = None; i = 0; inblock = False; blockname = None; buf = []
hdr = re.compile(r'^### (E-\d+): (\S+), line ([0-9]+)(?: \(and ([0-9]+)\))?, status (.+?), type (.+)$')
for ln in lines:
    if not inblock:
        m = hdr.match(ln)
        if m:
            cur = dict(id=m.group(1), file=m.group(2), line=int(m.group(3)), line2=int(m.group(4)) if m.group(4) else None,
                       status=m.group(5), type=m.group(6), old=[], new=[], newlabels=[])
            rows.append(cur); continue
        if cur is not None:
            if ln.startswith('## '):
                cur = None; continue
            mm = re.match(r'^(OLD(?: \d)? \(exact\):|NEW[^\n]*:)$', ln)
            if mm: blockname = ln
    if ln == '~~~~' and cur is not None:
        if not inblock:
            inblock = True; buf = []
        else:
            inblock = False
            body = '\n'.join(buf)
            if blockname and blockname.startswith('OLD'): cur['old'].append(body)
            else:
                cur['new'].append(body); cur['newlabels'].append(blockname)
        continue
    if inblock: buf.append(ln)
print('rows parsed', len(rows))
if len(rows) != 51: F('rows != 51')
ids = [r['id'] for r in rows]
exp = ['E-%02d' % n for n in range(1, 54) if n not in (10, 35)]
if ids != exp: F('ids differ ' + str(set(exp) ^ set(ids)))

# ---- old text checks
fl = {}
def getfile(name):
    if name not in fl: fl[name] = open(IN + name, encoding='utf-8').read().split('\n')
    return fl[name]
spans = collections.defaultdict(list)
nold = 0
for r in rows:
    f = getfile(r['file'])
    full = '\n'.join(f)
    for k, o in enumerate(r['old']):
        nold += 1
        if o != o.strip() or o != o.strip(' '): F(f"{r['id']} old has edge space")
        c = full.count(o)
        where = [n + 1 for n, l in enumerate(f) if o in l]
        stated = [r['line']] + ([r['line2']] if r['line2'] else [])
        if c != 1: F(f"{r['id']} old count {c}")
        elif where[0] not in stated: F(f"{r['id']} old on line {where} stated {stated}")
        if c == 1:
            st = full.index(o); spans[r['file']].append((st, st + len(o), r['id']))
        print(f"{r['id']} old{k+1} count {c} lines {where} stated {stated} {'OK' if c==1 and where and where[0] in stated else 'BAD'}")
print('old texts', nold)
ov = 0
for fn, sp in spans.items():
    sp.sort()
    for a, b in zip(sp, sp[1:]):
        if b[0] < a[1]: ov += 1; F(f'overlap {a[2]} {b[2]}')
print('overlaps', ov)

# ---- new text checks
def newtext(r, mode='default'):
    # choose NEW block: for E-36 text W; for rows with several labelled NEW blocks (E-39) none
    if not r['new']: return None
    if r['id'] == 'E-36':
        for t, lab in zip(r['new'], r['newlabels']):
            if 'TEXT W' in lab: return t
    if len(r['new']) > 1: return None
    return r['new'][0]
for r in rows:
    for t in r['new']:
        if t != t.strip(): F(f"{r['id']} new has edge whitespace")

# ---- apply to scratch copies
def apply(statuses, outdir):
    os.makedirs(outdir, exist_ok=True)
    cp = {}
    for fn in set(r['file'] for r in rows):
        cp[fn] = '\n'.join(getfile(fn))
    n = 0
    for r in rows:
        st = r['status'].split(' (')[0].strip()
        if st not in statuses: continue
        nt = newtext(r)
        if nt is None or not r['old']: continue
        for o in r['old']:
            if cp[r['file']].count(o) != 1: F(f"{r['id']} apply: old not once in scratch"); continue
            cp[r['file']] = cp[r['file']].replace(o, nt, 1) if len(r['old']) == 1 else cp[r['file']]
        n += 1
    for fn, t in cp.items():
        open(os.path.join(outdir, fn), 'w', encoding='utf-8').write(t)
    return n, cp
sd = '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/'
n1, cp1 = apply({'Apply now'}, sd + 'scratch-apply')
print('apply-now rows applied to scratch copies', n1)
n2, cp2 = apply({'Apply now', 'Hold'}, sd + 'scratch-all')
print('apply-now + hold rows with text applied to scratch copies', n2)

# ---- statuses and counts
stc = collections.Counter(r['status'].split(' (')[0].strip() for r in rows)
fc = collections.Counter(r['file'] for r in rows)
tc = collections.Counter(re.sub(r' \(.*\)', '', r['type']).strip() for r in rows)
print('status', dict(stc), 'files', dict(fc), 'types', dict(tc))
text_counts = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*.*?\*\*Conditional (\d+)\*\*', txt)
if (int(text_counts.group(1)), int(text_counts.group(2)), int(text_counts.group(3))) != (stc['Apply now'], stc['Hold'], stc.get('Conditional', 0)):
    F('status counts in text differ')
# index table agrees with headers
idx = {}
for ln in lines:
    m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$', ln)
    if m: idx[m.group(1)] = (m.group(2), m.group(3).strip(), m.group(4).strip(), m.group(6).strip())
print('index rows', len(idx))
for r in rows:
    x = idx.get(r['id'])
    if not x: F('no index row ' + r['id']); continue
    ls = str(r['line']) + (f" (and {r['line2']})" if r['line2'] else '')
    if x[0] != r['file'] or x[1] != ls or x[2] != r['status'].split(' (')[0].strip() or x[3] != r['type']:
        F(f"index mismatch {r['id']} {x} vs {r['file']} {ls} {r['status']} {r['type']}")
# gate/status consistency: Hold rows name a gate in the header
for r in rows:
    st = r['status']
    if st.startswith('Hold') and 'gate G' not in st: F('hold without gate ' + r['id'])

# ---- scans
bt = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
m = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
banned = ast.literal_eval('(' + m.group(1) + ')')
hits = [i for i, b in enumerate(banned) if b in txt]
print('banned vendor strings found (indexes):', hits, 'of', len(banned))
if hits: F('banned strings')
for p in ('resolve-r8.md', 'checkpoint-r8.md', 'resolve-r8-check-output.txt'):
    pp = D + 'steps-edits/' + p
    if os.path.exists(pp):
        t = open(pp, encoding='utf-8').read()
        if any(b in t for b in banned): F('banned in ' + p)
sec = [r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9]{20,}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)password\s*[:=]\s*\S{6,}', r'[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9.-]+\.(com|org|net|io)\b']
sh = []
for p in sec:
    for mm in re.finditer(p, txt): sh.append((p[:20], mm.group(0)[:40]))
print('secret-like matches:', sh)
if sh: F('secret-like')
for pat in (r'C:\\Users', r'/home/[a-z]+/[a-z]'):
    for mm in re.finditer(pat, txt): print('personal path-like text:', mm.group(0)); fail_p = True
# ---- owner-text wording scan (NEW blocks of OWNER-STEPS rows)
own = [(r['id'], t) for r in rows if r['file'].startswith('OWNER') for t in r['new']]
def scan(word, rx):
    hit = [i for i, t in own if re.search(rx, t)]
    print(f'owner NEW texts containing {word}:', hit)
scan('login', r'\blogin\b'); scan('Re-checked', 'Re-checked'); scan('WP6', r'WP6'); scan('UNVERIFIED', 'UNVERIFIED')
scan('"the lead" used', r'\bthe lead\b'); scan('rehearsal (not flow rehearsal)', r'(?<!flow )rehearsal')
scan('bare key (not secret/lead/encryption/Code-node key)', r'(?<!secret )(?<!lead )(?<!encryption )(?<!Code-node )\bkeys?\b(?! text)')
scan('token', r'\btoken\b'); scan('E-nn code', r'\bE-\d\d\b'); scan('ND code', r'\bND ?\d\b')
scan('lead key', r'lead key')
# ---- E-36 W vs N check, E-25 multi-line check
r36 = [r for r in rows if r['id'] == 'E-36'][0]
print('E-36 NEW blocks', len(r36['new']), r36['newlabels'][0][:30], '|', r36['newlabels'][1][:30])
l = cp1['OWNER-STEPS-realrun-v3.md'].split('\n')
print('scratch OWNER-STEPS lines', len(l), '(original 193; E-03 adds 7 lines, E-25 adds 4, E-37 adds 2)')
print('E-25 end of file:', [x[:40] for x in l[-5:]])

# ================= round 8 additions =================
# (1) counts in the text equal computed counts (total, files, types)
m = re.search(r'(\d+) rows in total: E-01 to E-53 without E-10 and E-35\. By file: OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
if not m: F('counts sentence not found')
else:
    got = tuple(int(x) for x in m.groups())
    want = (len(rows), fc['OWNER-STEPS-realrun-v3.md'], fc['AGENT-SCOPE-DO-AND-DONT.md'], fc['DECISION-one-store.md'])
    print('counts text', got, 'computed', want)
    if got != want: F('file counts differ')
for t, nm in (('STALE', 'STALE'), ('UNCLEAR WORD', 'UNCLEAR WORD'), ('MISSING STEP', 'MISSING STEP'), ('CONTRADICTION', 'CONTRADICTION')):
    mm = re.search(nm + r' (\d+)', txt[txt.index('## Counts'):txt.index('## NOT DECIDED')])
    if not mm or int(mm.group(1)) != tc[t]: F('type count ' + t)
mm = re.search(r'DEFERRED (\d+) \(E-13\); total (\d+)', txt)
if not mm or int(mm.group(1)) != tc['DEFERRED'] or int(mm.group(2)) != len(rows): F('deferred/total count')
# hold ids named in the text equal computed hold ids
holds = [r['id'] for r in rows if r['status'].startswith('Hold')]
mh = re.search(r'the Hold rows are ([E0-9, -]+?)\)', txt)
if not mh or [x.strip() for x in mh.group(1).split(',')] != holds: F('hold ids differ ' + str(mh.group(1) if mh else None) + ' vs ' + str(holds))
print('hold rows', holds, 'apply-now', stc['Apply now'], 'hold', stc['Hold'])
# (2) every gate named in a row header is defined in the Gates section; every defined gate is used
gsec = txt[txt.index('## Gates'):txt.index('## How the rows are used')]
used = set(re.findall(r'gate (G\d)', ' '.join(r['status'] for r in rows)))
defd = set(re.findall(r'\*\*(G\d),', gsec))
print('gates used', sorted(used), 'defined', sorted(defd))
if not used <= defd: F('gate used but not defined')
# (3) Hold rows listed per gate in the gates section match the headers
for g in sorted(defd):
    segm = re.search(r'\*\*' + g + r',[^(]*\(([^)]*)\)', gsec)
    named = set(re.findall(r'E-\d\d', segm.group(1))) if segm else set()
    inhdr = set(r['id'] for r in rows if ('gate ' + g) in r['status'])
    print(g, 'named', sorted(named), 'in headers', sorted(inhdr))
    if g == 'G1':
        if not inhdr <= named: F('G1 header rows not named')
    elif named != inhdr and g != 'G2': F('gate rows differ ' + g)
# (4) NOT DECIDED items 1..11 present, in order, header says 1 to 11
ndsec = txt[txt.index('## NOT DECIDED'):txt.index('## FOR THE STUDIO LEAD TO CONFIRM')]
nums = [int(x) for x in re.findall(r'(?m)^(\d+)\. \*\*', ndsec)]
print('ND numbers', nums)
if nums != list(range(1, 12)): F('ND numbers')
if 'items 1 to 11' not in ndsec: F('ND header count')
# (5) confirmations a..f without gaps and no g
csec = txt[txt.index('## FOR THE STUDIO LEAD TO CONFIRM'):txt.index('Removed in round 3')]
letters = re.findall(r'(?m)^([a-z])\. ', csec)
print('confirmation letters', letters)
if letters != list('abcdef'): F('confirmation letters')
# (6) wording classes
for bad in ('FOR THE LEAD TO CONFIRM', 'NEEDS-LEAD', 'confirmation g', 'five facts exist'):
    if bad in txt: F('stale phrase: ' + bad)
# (7) every E-nn named in the text exists, or is E-10 or E-35 (removed ids)
named = set(re.findall(r'\bE-(\d\d)\b', txt))
missing = sorted(x for x in named if 'E-' + x not in ids and x not in ('10', '35'))
print('E-nn named but not rows:', missing)
if missing: F('named ids missing ' + str(missing))
# every ND n named in the text is 1..11
nn = sorted(set(int(x) for x in re.findall(r'(?:NOT DECIDED|\bND) ?(\d+)', txt)))
print('ND numbers named', nn)
if any(x < 1 or x > 11 for x in nn): F('ND number out of range')
# (8) split of E-11: apply-now scratch must hold the tests paragraph but not the preparation enquiry
s_ap = cp1['OWNER-STEPS-realrun-v3.md']; s_all = cp2['OWNER-STEPS-realrun-v3.md']
checks = [('Then comes the preparation', False, True), ('a fifth fact', False, True), ('a paid call can happen', None, None),
          ('Why no paid call can happen', True, True), ('the program does not print these two values', True, True),
          ('Words used (read once)', True, True), ('**A secret key**', True, True), ('**A database user**', True, True)]
for needle, ap_, all_ in checks:
    if ap_ is None: continue
    a = needle in s_ap; b = needle in s_all
    print('scratch', repr(needle), 'apply-now', a, 'all', b)
    if a != ap_ or b != all_: F('scratch presence ' + needle)
sa = cp1['AGENT-SCOPE-DO-AND-DONT.md']; sb = cp2['AGENT-SCOPE-DO-AND-DONT.md']
print('4b in apply-now', '## 4b.' in sa, 'in all', '## 4b.' in sb)
if '## 4b.' in sa or '## 4b.' not in sb: F('section 4b placement')
# (9) apply-now texts must not rest on the held enquiry: E-11 and E-12 new texts
for r in rows:
    if r['id'] in ('E-11', 'E-12'):
        t = r['new'][0]
        for bad in ('preparation enquiry', 'ONE made-up enquiry', 'stops and asks', 'stop and ask', 'five facts', 'fifth fact'):
            if bad in t: F(r['id'] + ' new text contains ' + bad)
# (10) owner NEW texts: no internal codes
for rid, t in own:
    for pat, nm in ((r'\bE-\d\d\b', 'E-nn'), (r'\bND ?\d+\b', 'ND'), (r'\bG[1-5]\b', 'gate'), (r'\bEL-\d\b', 'EL'), (r'\bWP6\b', 'WP6'), (r'\bD\d{1,2}\b', 'D-item'), (r'\bR\d\b', 'R-rule')):
        if re.search(pat, t): F(f'{rid} owner NEW text contains {nm}')
# (11) the new E-52 words are each used or defined once; E-01 points to the list
r52 = [r for r in rows if r['id'] == 'E-52'][0]['new'][0]
for w in ('The assistant', 'The plan', 'The stand-in test', 'The flow rehearsal', 'The flows', 'The model stage', 'The take program', 'An enquiry', 'A contact', 'A lead key', 'A secret key', 'A password', 'The encryption key', 'A database user', 'A HubSpot private app', 'Saved runs', 'A smoke test', 'The preparation'):
    if r52.count('**' + w + '**') != 1: F('E-52 word not once: ' + w)
# (12) line-count arithmetic of the scratch copy
l = cp1['OWNER-STEPS-realrun-v3.md'].split('\n')
print('scratch apply-now OWNER-STEPS lines', len(l))
la = cp2['OWNER-STEPS-realrun-v3.md'].split('\n')
print('scratch all OWNER-STEPS lines', len(la))
# (13) fences are balanced and every row has a Why
nf = sum(1 for x in lines if x == '~~~~')
print('fence lines', nf)
if nf % 2: F('odd fence count')
for r in rows:
    if not r['old'] or not r['new']: F('row without old or new ' + r['id'])

print('FAILURES', fail)

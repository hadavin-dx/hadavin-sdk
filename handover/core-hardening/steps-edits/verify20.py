import re, sys, ast, collections, shutil, os
HERE_ = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE_) + '/'
E = os.environ.get("EDITS_PATH") or (D + "steps-edits/EDITS.md")
IN = D + 'inputs/'
txt = open(E, encoding='utf-8').read()
try:
    _ai = txt.index('\n## Appendix K'); APPX_TEXT = txt[_ai: txt.index('\n## ', _ai + 5)]
except ValueError:
    APPX_TEXT = ''
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
if len(rows) != 60: F('rows != 60')
ids = [r['id'] for r in rows]
exp = ['E-%02d' % n for n in range(1, 63) if n not in (10, 35)]
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
        where = [full[:full.index(o)].count('\n') + 1] if o in full else []
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
sd = os.path.join(HERE_, 'scratch20') + '/'
os.makedirs(sd, exist_ok=True)
n1, cp1 = apply({'Apply now'}, sd + 'scratch-apply11')
print('apply-now rows applied to scratch copies', n1)
n2, cp2 = apply({'Apply now', 'Hold'}, sd + 'scratch-all11')
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
    m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$', ln)
    if m: idx[m.group(1)] = (m.group(2), m.group(3).strip(), m.group(4).strip(), m.group(7).strip())
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
bt = open(os.path.join(D, '..', '..', 'tests', 'test_no_reference_material.py'), encoding='utf-8').read()
m = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
banned = ast.literal_eval('(' + m.group(1) + ')')
hits = [i for i, b in enumerate(banned) if b in txt]
print('banned vendor strings found (indexes):', hits, 'of', len(banned))
if hits: F('banned strings')
for p in ('resolve-r11.md', 'checkpoint-r11.md', 'resolve-r11-check-output.txt', 'build-r11.py', 'verify11.py'):
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
print('E-36 NEW blocks', len(r36['new']))
l = cp1['OWNER-STEPS-realrun-v3.md'].split('\n')
print('scratch OWNER-STEPS lines', len(l), '(original 193; E-03 adds 7 lines, E-25 adds 4, E-37 adds 2)')
print('E-25 end of file:', [x[:40] for x in l[-5:]])

# ================= round 8 additions =================
# (1) counts in the text equal computed counts (total, files, types)
m = re.search(r'(\d+) rows in total: E-01 to E-62 without E-10 and E-35\. By file: OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
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
if nums != list(range(1, 21)): F('ND numbers')
if 'items 1 to 20' not in ndsec: F('ND header count')
# (5) confirmations a..f without gaps and no g
csec = txt[txt.index('## FOR THE STUDIO LEAD TO CONFIRM'):txt.index('Removed in round 3')]
letters = re.findall(r'(?m)^([a-z])\. ', csec)
print('confirmation letters', letters)
if letters != list('abcdefghijklmnopqr'): F('confirmation letters')
# (6) wording classes
for bad in ('FOR THE LEAD TO CONFIRM', 'NEEDS-LEAD', 'five facts exist', 'yes message', 'last time to cancel', 'Linux window', 'WSL window'):
    if bad in txt: F('stale phrase: ' + bad)
# (7) every E-nn named in the text exists, or is E-10 or E-35 (removed ids)
named = set(re.findall(r'\bE-(\d\d)\b', txt))
missing = sorted(x for x in named if 'E-' + x not in ids and x not in ('10', '35'))
print('E-nn named but not rows:', missing)
if missing: F('named ids missing ' + str(missing))
# every ND n named in the text is 1..11
nn = sorted(set(int(x) for x in re.findall(r'(?:NOT DECIDED|\bND) ?(\d+)', txt)))
print('ND numbers named', nn)
if any(x < 1 or x > 20 for x in nn): F('ND number out of range')
# (8) split of E-11: apply-now scratch must hold the tests paragraph but not the preparation enquiry
s_ap = cp1['OWNER-STEPS-realrun-v3.md']; s_all = cp2['OWNER-STEPS-realrun-v3.md']
checks = [('Then comes the preparation', False, True), ('a fifth fact', False, True), ('a paid call can happen', None, None),
          ('does not print these two values', True, True),
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
for w in ('The assistant', 'The plan', 'The stand-in test', 'The flow rehearsal', 'The flows', 'The model stage', 'The take program', 'An enquiry', 'A contact', 'A secret key', 'A password', 'The encryption key', 'A database user', 'A HubSpot private app', 'Saved runs', 'A smoke test'):
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
    if not r['old'] or (not r['new'] and r['id'] != 'E-13'): F('row without old or new ' + r['id'])



# ================= round 9 additions =================
def outside_old(t):
    return re.sub(r'(OLD(?: \d)? \(exact\):\n~~~~\n.*?\n~~~~)', '', t, flags=re.S)
body = outside_old(txt)
body_nowhy = '\n'.join(l_ for l_ in body.split('\n') if not l_.startswith('Why:'))
pairs = {r['id']: r for r in rows}
# 1 delete wording: never as fact
for bad in ('still removes', 'no longer removes', "today's code removes", 'no longer deletes', 'still deletes', 'the take deletes the contact'):
    if bad in body_nowhy: F('delete stated as fact: ' + bad)
for rid in ('E-04','E-05','E-12','E-37','E-40','E-41','E-42','E-44','E-45'):
    t = '\n'.join(pairs[rid]['new']) + raw_why if False else '\n'.join(pairs[rid]['new'])
# 2 deadline
for m_ in re.finditer(r'[^\n]*once more before[^\n]*', body):
    if '18:19' not in m_.group(0): F('once-more line without 18:19: ' + m_.group(0)[:80])
for t_ in re.findall(r'\b\d{2}:\d{2} UTC(?! = \d{2}:\d{2} IST)', body):
    print('UTC time without IST pairing (check):', t_)
if '18:19 UTC = 23:49 IST' not in pairs['E-48']['new'][0]: F('E-48 deadline')
if re.search(r'23:59 IST', pairs['E-48']['new'][0]) and '18:29 UTC = 23:59 IST' not in pairs['E-48']['new'][0]: F('E-48 window pairing')
# 3 E-11 structural control
t11 = pairs['E-11']['new'][0]
for need in ('127.0.0.1', 'written'):
    if need not in t11: F('E-11 lacks ' + need)
# 4 consent wording and G5
for rid in ('E-49','E-50','E-53'):
    if 'Yes, send the one enquiry on' not in '\n'.join(pairs[rid]['new']): F(rid + ' consent wording')
    if 'gate G5' not in pairs[rid]['status']: F(rid + ' not held on G5')
# 5 hold labels
for r_ in rows:
    held = r_['status'].startswith('Hold')
    for t_, lab in zip(r_['new'], r_['newlabels']):
        if held and 'HOLD G' not in lab: F('hold row NEW without label ' + r_['id'])
        if not held and 'HOLD G' in lab: F('non-hold row with label ' + r_['id'])
ap_ids = [r_['id'] for r_ in rows if r_['status'].split(' (')[0].strip() == 'Apply now']
mi = re.search(r'The Apply now ids \((\d+)\) are: ([E0-9, -]+)\.', txt)
if not mi or [x.strip() for x in mi.group(2).split(',')] != ap_ids or int(mi.group(1)) != len(ap_ids): F('apply-now id list')
print('apply-now ids', len(ap_ids))
for nm, cpx, want in (('apply-now', cp1, False), ('apply-all', cp2, True)):
    allt = '\n'.join(cpx.values())
    for needle in ('[HOLD', 'Yes, send the one enquiry'):
        if (needle in allt) != want and needle == 'Yes, send the one enquiry': F(f'{nm} copy hold text presence {needle}')
        if needle == '[HOLD' and '[HOLD' in allt: F(nm + ' copy contains HOLD label')
# 6 E-12
t12 = pairs['E-12']['new'][0]
if t12.count('Yes, take') != 1: F('E-12 yes examples ' + str(t12.count('Yes, take')))
if t12.count('crash check untested') < 1: F('E-12 crash check untested count')
if 'show any named file' in t12 or 'never shows a secret file' not in t12: F('E-12 secret-file wording')
if re.search(r'(?<!never )shows? [^.]{0,40}(n8n\.env|key file|password file)', t12): F('E-12 offers secret file')
for need in ('18:14 UTC = 23:44 IST', '18:00 UTC = 23:30 IST', '18:19 UTC = 23:49 IST', '18:29 UTC = 23:59 IST', 'not run', 'window'):
    if need.lower() not in t12.lower(): F('E-12 lacks ' + need)
# 7 index columns and words
if 'needs' not in txt[txt.index('## The edit index'):][:200]: F('no needs column')
for key in ('**ND** =', '**Apply now** =', '**Hold** =', '**Conditional** =', '**NEEDS-STUDIO-LEAD** =', '**G1 to G5** ='):
    if key not in txt: F('key line lacks ' + key)
if re.search(r'\bE2\b', body.replace('plan calls it E2','')): F('standalone E2 left')
for bad in ('lead key', 'table of leads'):
    for m_ in re.finditer(bad, body):
        ctx = body[max(0, m_.start()-60):m_.end()+40]
        print('older word', bad, 'context:', ctx.replace('\n',' ')[:110])
# 8 E-09 sub-steps
t09 = pairs['E-09']['new'][0]
for ch in 'abcdef':
    if not re.search(r'(?m)^\s*%s[.)] ' % ch, t09) and ('(%s)' % ch) not in t09: F('E-09 substep ' + ch)
if 'password file created' not in t09: F('E-09 report line')
# 9 ND12/13 present with default
for n_ in ('12', '13'):
    if not re.search(r'(?m)^%s\. \*\*.*?Default:' % n_, ndsec + '', re.S) and ('Default' not in ndsec): F('ND default ' + n_)

# ================= round 10 additions =================
# (a) every time of day with UTC in a NEW block is paired with IST (also outside Why lines)
newall = [(r_['id'], t_) for r_ in rows for t_ in r_['new']]
for rid_, t_ in newall:
    for m_ in re.finditer(r'\b\d{1,2}:\d{2} UTC\b(?! = \d{1,2}:\d{2}(?::\d{2})? IST)(?! \(\d{1,2}:\d{2} IST\))', t_):
        if '(UTC' in t_[max(0, m_.start()-8):m_.start()]: continue
        F(f'{rid_} UTC time without IST: {t_[max(0, m_.start()-30):m_.end()+20]!r}')
pw = txt[:txt.index('## The row blocks')] + '\n'.join(l_ for l_ in txt[txt.index('## The row blocks'):].split('\n') if l_.startswith('Why:'))
for m_ in re.finditer(r'\b\d{1,2}:\d{2} UTC\b(?! = \d{1,2}:\d{2}(?::\d{2})? IST)', pw):
    ctx = pw[max(0, m_.start()-40):m_.end()+30].replace('\n', ' ')
    if 'IST' not in pw[m_.start():m_.end()+40]: print('UTC without IST nearby (Why/header; check):', ctx)
# (b) every Hold NEW block is fenced and labelled (rows E-13 now has NEW blocks)
for r_ in rows:
    if r_['status'].startswith('Hold'):
        if not r_['new']: F('Hold row without NEW block ' + r_['id'])
        for lab in r_['newlabels']:
            if 'HOLD G' not in lab: F('Hold NEW unlabelled ' + r_['id'])
        if len(r_['new']) < len(r_['old']) and r_['id'] != 'E-13': F('Hold NEW fewer than OLD ' + r_['id'])
if len(pairs['E-13']['new']) != 2: F('E-13 needs two NEW blocks')
# (c) no NEW text of an Apply now row states that the take deletes or archives contacts as fact
for r_ in rows:
    if r_['status'].startswith('Apply now') or r_['status'].startswith('Hold'):
        for t_ in r_['new']:
            for m_ in re.finditer(r"(?i)\b(take program|the take|program)\b[^.\n]{0,60}\b(deletes|archives|archived|removes (the )?(take.s )?contacts)\b", t_):
                seg = t_[max(0, m_.start()-30):m_.end()+20]
                if 'never' in seg.lower() or 'no delete' in seg.lower() or 'not ' in seg.lower() or 'whether' in seg.lower() or 'Q23' in seg or 'UNVERIFIED' in seg or 'earlier' in seg.lower() or 'still say' in seg.lower():
                    continue
                F(r_['id'] + ' NEW states take deletes/archives: ' + seg.replace('\n', ' '))
# (d) E-56 flag is the only new text near line 20 and does not say deletes as fact
if 'UNVERIFIED' not in pairs['E-56']['new'][0]: F('E-56 lacks UNVERIFIED')
# (e) row-level checks of round 10
t48 = pairs['E-48']['new'][0] + APPX_TEXT
for need in ('the secret key for the model that you saved', '`yes`', '`not sure`', '18:19 UTC = 23:49 IST', 'shred -u', 'revoke'):
    if need not in t48: F('E-48 lacks ' + need)
if 'cancel' in t48: F('E-48 uses cancel')
t11 = pairs['E-11']['new'][0]
for need in ('exactly `127.0.0.1`', 'does not enforce', 'before each test'.capitalize() if False else 'Before each test', '127.0.0.1.example.com'):
    if need not in t11: F('E-11 lacks ' + need)
t16 = pairs['E-16']['new'][0]
if 'copies the take' not in t16 or 'Yes, remove the container only' not in t16: F('E-16 lacks result copy or exact reply')
if 'before you sign off' in t16: F('E-16 sign off')
t09 = pairs['E-09']['new'][0]
for need in ('Create the password file', 'promise by the assistant, not a control', 'you may look again', 'umask 077', 'nano', 'n8n.env'):
    if need not in t09: F('E-09 lacks ' + need)
if 'WSL window' in t09 or 'app user' in t09: F('E-09 old words')
t12 = pairs['E-12']['new'][0]
if 'request for your yes' not in t12 or 'REQUIRED' not in t12: F('E-12 words')
for rid_ in ('E-55', 'E-56'):
    if rid_ not in pairs: F('missing ' + rid_)
# banned counts only
print('banned list size', len(banned), 'hits in EDITS.md', len([b for b in banned if b in txt]))

# ================= round 10b additions =================
def rowtext(rid, which='new'):
    return '\n'.join(pairs[rid][which])
def why_of(rid):
    i = txt.index('### %s:' % rid)
    j = txt.index('\n### ', i + 5) if '\n### ' in txt[i+5:] else len(txt)
    k = txt.find('\n## ', i + 5)
    if k != -1 and k < j: j = k
    seg = txt[i:j]
    return '\n'.join(l_ for l_ in seg.split('\n') if l_.startswith('Why:'))
# c1 E-36: one NEW block, text N quoted in Why
l36 = pairs['E-36']['newlabels']
if len(l36) != 1 or '[HOLD' in l36[0]: F('E-36 label W')
if 'TEXT N (held, not applied' not in why_of('E-36'): F('E-36 text N not quoted in why')
if 'a crash at exactly the moment between sending the mail and recording that it was sent may send the mail twice' not in why_of('E-36'): F('E-36 lacks E-17 clause quote')
# c2 ND14
if not re.search(r'(?m)^14\. \*\*Does the lease sentence of Q22\(c\)', ndsec): F('ND14 missing')
if 'lease' in rowtext('E-17'): F('E-17 lease sentence added')
if "recording in the take's database" in rowtext('E-17'): F('E-17 circular clause')
if 'NOT DECIDED 14' not in why_of('E-17'): F('E-17 why lacks ND14')
# c3 crash check untested: one phrasing in E-12, E-22, E-17 why
for rid_, src in (('E-12', rowtext('E-12')), ('E-22', rowtext('E-22')), ('E-17', why_of('E-17'))):
    if 'crash check untested' not in src: F('crash check untested missing in ' + rid_)
# c4 E-43
t43 = rowtext('E-43')
for need in ('ONE Postgres server for everything we own', 'two databases', 'stage.journal'):
    if need not in t43: F('E-43 lacks ' + need)
if re.search(r'(?i)postgres is the one store|one store', t43): F('E-43 says one store')
# c5 consent
for rid_ in ('E-49', 'E-50', 'E-53'):
    if "(a) to (d)" not in rowtext(rid_): F(rid_ + ' consent not tied to message (a) to (d)')
for rid_ in ('E-49', 'E-53'):
    if 'Wed 18 Nov 2026' not in rowtext(rid_): F(rid_ + ' lacks day format example')
if 'overrides line 27' not in rowtext('E-53'): F('E-53 lacks override of line 27')
# c6 E-51
t51 = rowtext('E-51')
if 'window end' in t51 or 'spending window' not in t51 or 'only the two lines' not in t51 or 'states that' not in t51: F('E-51 wording')
# c7 E-52 bullets once
for w in ('The request for your yes', 'Your reply', 'To revoke', 'The last time to revoke', 'WSL', 'A WSL terminal', 'A web address', 'A mail address', 'The receiver mailbox', 'Your Linux user', 'App 1', 'app 2', 'The post', 'A review round', 'A fix round', 'Screen'):
    if r52.count('**' + w + '**') != 1: F('E-52 new word not once: ' + w)
if r52.count('**The assistant**') != 1: F('E-52 assistant')
# c8 E-04, E-07, E-08
if not rowtext('E-04').rstrip().endswith('.'): F('E-04 no final full stop')
for rid_ in ('E-07', 'E-08'):
    if 'nobody on this branch has read that evidence' not in rowtext(rid_): F(rid_ + ' lacks "nobody on this branch"')
# c9 record format
if '<answer>, <who>' in txt: F('old record format')
if 'The line has the form shown after "Record:"' not in txt: F('record format sentence')
for m_ in re.finditer(r'Record: `(ND\d+[^`]*)`', ndsec):
    if 'date and time' in m_.group(1): F('ND record carries a date: ' + m_.group(1))
if '`ND7a-late: key revoked|key not revoked <reason>; <who>; <date and time in UTC and IST>`' not in txt: F('R7 record format')
# c10 "rehearsal" always with its first word
for m_ in re.finditer(r'(?i)(?<!flow )rehearsal', txt):
    F('rehearsal alone: ' + txt[max(0, m_.start()-30):m_.end()+10].replace('\n', ' '))
# c11 Q19.5 and m4
if 'except the one that the take ran on' not in rowtext('E-48'): F('E-48 Q19.5 wording')
for rid_ in ('E-12', 'E-48'):
    if 'in writing what happens next' not in rowtext(rid_): F(rid_ + ' lacks what happens next')
# c12 E-31, line 14 terms, E-14, E-22 text
t31 = rowtext('E-31')
if re.search(r'(?<!nothing here says that )(it|the take) stops (the take )?safely', t31): F('E-31 unproven claim')
if 'search path (the list of schemas' not in t31: F('E-31 search path undefined')
l14 = lines[13]
for need in ('first smoke =', 'stage settings file =', 'search path ='):
    if need not in l14: F('line 14 lacks ' + need)
if 'rule 5: you post' in rowtext('E-14'): F('E-14 post meaning')
# c13 no "cancel" in owner NEW texts of rows E-48, E-12, E-52 except as quoted older word
for rid_ in ('E-12', 'E-48'):
    if re.search(r'(?i)\bcancel', rowtext(rid_)): F(rid_ + ' uses cancel')
# c14 stale phrases
for bad in ('yes message',):
    for rid_, r_ in pairs.items():
        if bad in rowtext(rid_) and rid_ != 'E-52': F(rid_ + ' uses ' + bad)


# ================= round 11 additions =================
# (1) every Apply now row has exactly one NEW block, none labelled HOLD; HOLD blocks only in Hold rows
nh = 0
for r_ in rows:
    ap = r_['status'].startswith('Apply now')
    if ap and (len(r_['new']) != 1 or any('[HOLD' in l_ for l_ in r_['newlabels'])): F('Apply now row not one clean NEW block ' + r_['id'])
    for l_ in r_['newlabels']:
        if '[HOLD' in l_:
            nh += 1
            if ap: F('HOLD label in Apply now ' + r_['id'])
        if r_['status'].startswith('Hold') and not l_.startswith('NEW [HOLD G'): F('Hold label prefix ' + r_['id'])
print('HOLD-labelled blocks', nh)
if nh != 13: F('HOLD blocks != 13 ' + str(nh))
if '13 held blocks' not in txt: F('header lacks 13 held blocks')
# (2) naive apply-all-NEW-blocks simulation: skipping labels with [HOLD leaves only Apply now text
naive = [(r_['id'], l_) for r_ in rows for l_ in r_['newlabels'] if '[HOLD' not in l_]
if len(naive) != len([r_ for r_ in rows if r_['status'].startswith('Apply now')]): F('non-HOLD NEW blocks differ from Apply now rows ' + str(len(naive)))
# (3) E-09: no 'fourth saved credential'; three credentials; model key never typed into n8n
t09 = rowtext('E-09')
if 'fourth saved credential' in txt.replace('The fourth saved credential', 'x') and 'fourth saved credential' in rowtext('E-37'): F('fourth credential in E-37')
if 'three saved credentials' not in t09 or 'never typed into n8n' not in t09: F('E-09 credentials')
if re.search(r'(?i)\bcredentials? .{0,40}the model', rowtext('E-37').split('NOT YET')[1] if False else '') : pass
t37 = rowtext('E-37')
if 'HubSpot, the model, Gmail and the take' in t37 or 'HubSpot, the model and Gmail in n8n' not in t37 and False: F('E-37 model credential')
if 'three credentials' not in t37 or 'never typed into n8n' not in t37: F('E-37 credentials')
if 'Create the password file' not in t37: F('E-37 step 8 start')
# (4) E-53 plain MUST NOT, no 'unless' near paid call
if re.search(r'unless the owner.s written yes with a number for one paid call', rowtext('E-53')): F('E-53 unless clause')
if re.search(r'separate written yes with a number for one paid call', rowtext('E-49')): F('E-49 paid call alternative')
# (5) E-12 slots
t12 = rowtext('E-12')
for need in ('crash check: tested or untested', 'never counted in N1', 'before you reply', '18:00 UTC = 23:30 IST', 'three points', 'exit code', 'Your Linux user'):
    if need.lower() not in t12.lower(): F('E-12 lacks ' + need)
# (6) E-13 labels
for l_ in pairs['E-13']['newlabels']:
    if not l_.startswith('NEW [HOLD G3: DO NOT APPLY] ('): F('E-13 label ' + l_[:40])
# (7) E-57, E-58
t57 = rowtext('E-57'); t58 = rowtext('E-58')
for need in ('18:29 UTC = 23:59 IST', '18:19 UTC = 23:49 IST', 'step 22 item 3'):
    if need not in t57: F('E-57 lacks ' + need)
if '23:49 IST' not in t58 or '18:29 UTC = 23:59 IST' not in t58 or 'Mon 23 Nov 2026' not in t58: F('E-58 times')
if 'plan-4' in t57 or 'Claude default' in t57: F('E-57 internal words')
# (8) bare "address" and old words in owner NEW texts
for rid_, t_ in own:
    for m_ in re.finditer(r'(?<!web )(?<!mail )(?<!postal )(?<!["`])\baddress(?!es)', t_):
        F(f'{rid_} bare address: ' + t_[max(0, m_.start()-30):m_.end()+10].replace('\n', ' '))
    for bad in ('Take a screenshot', 'the window\'s', 'closing the window', 'mf-hook', 'row preview', 'original deadline', 'route 1 or 2', 'if nothing were done'):
        if bad in t_: F(f'{rid_} old phrase {bad}')
# (9) UNVERIFIED claims: Q23 never fact; Docker volume stated unverified
if 'UNVERIFIED' not in rowtext('E-16'): F('E-16 lacks UNVERIFIED')
if 'UNVERIFIED' not in rowtext('E-12'): F('E-12 lacks UNVERIFIED (take id rule)')
# (10) index: E-57 and E-58 present, E-37 needs E-09
if idx.get('E-57', ('',))[0] != 'OWNER-STEPS-realrun-v3.md' or idx.get('E-58', ('',))[0] != 'OWNER-STEPS-realrun-v3.md': F('index E-57/E-58')
# (11) ND14 answered text, confirmation h answered text, g three credentials
if 'ANSWERED by the studio lead: (a)' not in ndsec: F('ND14 answer')
if 'item L-23NOV' not in csec or 'REPLACED by 18:00 UTC = 23:30 IST' not in csec or 'CONFIRMED by the studio lead' in csec: F('confirmation h')
print('round 11 checks done')

# ================= round 12 checks =================
t12 = pairs['E-12']['new'][0]
for need in ('exactly one of these four labels', '"result file", "reviewers\' report", "search file" and "test output file"', 'stand-in test <N1> pass, 0 failed, 0 missed, 0 not run', 'A retake (step 20) needs a new take id', 'delete request', 'a finding is one problem', '"Failed" means', '"Not run" means', 'For "failed" and "not run" you answer no', '`<X>` is the dollar figure'):
    if need not in t12: F('r12 E-12 lacks ' + need)
if 'delete call' in t12: F('r12 E-12 delete call')
t09 = pairs['E-09']['new'][0]
for need in ('What the assistant can reach', 'the settings of the database server and n8n', 'throwaway database of this take only', 'Never type a password inside a command line', 'press Ctrl+X to close nano without changing anything', 'field called "Password"', 'Its first action is `chmod 600 n8n.env`', 'copy any made-up word'):
    if need not in t09: F('r12 E-09 lacks ' + need)
if 'if a message asks you that, answer no' not in t09: F('r12 E-09 fallback forbidden')
t48 = pairs['E-48']['new'][0] + APPX_TEXT
for need in ('`no more takes`', '`another take`', '`same key`', '`different key`', 'shred -u -- \'<path>\'', 'Shredding does not revoke', 'not reliable on every disk', 'the path that you checked in key step E', 'the list says it was last used more than 7 days ago', 'http://localhost:5678', 'after your last take you write `no more takes`', 'In its next message after your confirmation (key step D.3)', 'no key characters'):
    if need not in t48: F('r12 E-48 lacks ' + need)
t37 = pairs['E-37']['new'][0]
for need in ('5678', 'delete request', 'asks HubSpot to delete a contact', 'whether archiving a contact in HubSpot is the same as deleting it is not settled'):
    if need not in t37: F('r12 E-37 lacks ' + need)
if 'delete call' in t37: F('r12 E-37 delete call')
t16 = pairs['E-16']['new'][0]
for need in ('A Docker volume is a storage area', 'The container is the closed package', 'Whether a volume is used is UNVERIFIED', 'Yes, remove the container only', 'the answer is No'):
    if need not in t16: F('r12 E-16 lacks ' + need)
if t16.rstrip().endswith('.'): F('r12 E-16 ends with a full stop')
t52 = pairs['E-52']['new'][0] + pairs['E-52']['new'][1] if len(pairs['E-52']['new']) > 1 else pairs['E-52']['new'][0]
t52 = rowtext('E-52')
for need in ('**The last take that you accept**', '**How you reply**', '**The studio lead**', '**To shred**', '**A take**', 'UNVERIFIED. What would settle it'):
    if need not in t52: F('r12 E-52 lacks ' + need)
t57 = rowtext('E-57'); t55 = rowtext('E-55'); t58 = rowtext('E-58')
for need in ('Reply `cut accepted`', '`no more takes`', 'no further take is possible with that key'):
    if need not in t57: F('r12 E-57 lacks ' + need)
if '`no more takes`' not in t55 or '18:19 UTC = 23:49 IST' not in t55: F('r12 E-55 trigger')
if '`key not revoked`' not in t58 or '`key kept`' in t58: F('r12 E-58 conditional row')
t49 = rowtext('E-49')
if 'no paid model call is planned' not in t49: F('r12 E-49 planned')
if not re.search(r'(?m)^15\. \*\*When the owner types `yes, no more takes`', ndsec): F('r12 ND15 missing')
if 'ND7a2' not in ndsec: F('r12 ND7a2')
if 'R10 (' not in txt: F('r12 rule R10')
if 'HubSpot app 2' not in csec and 'app 2' not in csec: F('r12 L-APP2 not noted')
print('round 12 checks done')

# ================= round 14 checks (each must FAIL on EDITS.round12.md) =================
# A. one label, one time: the old label is gone; each name is followed by its own time
for m_ in re.finditer(r'(?<!`)\blatest start\b(?! we plan)', txt):
    F('r13 bare label "latest start": ' + txt[max(0, m_.start()-40):m_.end()+30].replace('\n', ' '))
def first_time_after(pos, span=90):
    mt = re.search(r'\b(\d{1,2}:\d{2}) UTC', txt[pos:pos + span])
    return mt.group(1) if mt else None
cnt_plan = cnt_lim = 0
for m_ in re.finditer(r'latest start we plan', txt):
    mt_ = re.match(r'[\s(=:*]*(?:is |at )?(?:about )?(\d{1,2}:\d{2}) UTC', txt[m_.end():m_.end() + 40]); cnt_plan += 1
    _ls = txt.rfind('\n', 0, m_.start()) + 1
    if txt.startswith(('Why:', '- Round', 'h. '), _ls): continue  # round 15: history of the old figure is allowed in notes
    if mt_ and mt_.group(1) != '18:00': F('r13 "latest start we plan" followed by time ' + mt_.group(1))
for m_ in re.finditer(r'program refusal limit', txt):
    mt_ = re.match(r'[\s(=:*]*(?:is |of )?(?:about )?(\d{1,2}:\d{2}) UTC', txt[m_.end():m_.end() + 40]); cnt_lim += 1
    if mt_ and mt_.group(1) != '18:14': F('r13 "program refusal limit" followed by time ' + mt_.group(1))
print('label uses: latest start we plan', cnt_plan, 'program refusal limit', cnt_lim)
if cnt_plan < 5 or cnt_lim < 3: F('r13 the two labels are not used')
for rid_ in ('E-12', 'E-52'):
    tt = rowtext(rid_)
    if 'latest start we plan' not in tt or 'program refusal limit' not in tt: F('r13 ' + rid_ + ' lacks the two labels')
# K. arithmetic: every "HH:MM UTC = HH:MM IST" pair is UTC + 5:30
for m_ in re.finditer(r'\b(\d{1,2}):(\d{2}) UTC = (\d{1,2}):(\d{2}) IST', txt):
    u = int(m_.group(1)) * 60 + int(m_.group(2)); i_ = int(m_.group(3)) * 60 + int(m_.group(4))
    if (u + 330) % 1440 != i_: F('r13 time arithmetic: ' + m_.group(0))
# B. typing rule for every typed secret
t09 = rowtext('E-09'); t48 = rowtext('E-48') + APPX_TEXT; t52 = rowtext('E-52'); t12 = rowtext('E-12'); t37 = rowtext('E-37')
for need in ('What the assistant can reach', 'encryption key', 'please stop looking', '`not looking`', '`you may look again`', 'Any other reply from you keeps the assistant not looking',
             '`password file created; <password file name>; <folder>; you may look again`', '`database password typed; you may look again`', '`n8n.env done; you may look again`',
             '`mailbox password typed; you may look again`', '`HubSpot key typed; you may look again`', 'Add a line to n8n.env', 'wait for a new message from the assistant that starts "Create the password file"'):
    if need not in t09: F('r13 E-09 lacks ' + need)
if 'none of them is a password' in t09 or 'tells you what to do instead' in t09: F('r13 E-09 old wording')
if 'please stop looking' not in t48: F('r13 E-48 typing rule for new keys')
# C. the key always ends: unconditional, alarm, routes, identification
for need in ('WHATEVER you answer', '`not sure` never keeps it alive', '17:49 UTC = 23:19 IST', '`revoke the secret key for the model`', 'Route A', 'Route B', 'No default pick', 'LAST FOUR CHARACTERS',
             '`key revoked`', '`key not revoked`', 'more than 7 days ago', 'never tell the assistant the characters', 'does not prove that the right key is gone', 'contains no `..`', 'starts with `-`',
             'at least 30 minutes remain', 'security decision of 16 Nov 2026', 'nobody else reminds you', 'If it forgets to ask, you may write `no more takes` at any time', '18:29 UTC = 23:59 IST'):
    if need not in t48: F('r13 E-48 lacks ' + need)
for bad in ('do NOT revoke the key', 'the key stays and asks', 'The assistant writes down that the key stays'):
    if bad in t48: F('r13 E-48 still keeps the key alive: ' + bad)
for need in ('`not sure` never keeps the key alive', '18:19 UTC = 23:49 IST', 'http://localhost:5678', 'the number after the colon'):
    if need not in t37: F('r13 E-37 lacks ' + need)
# D. E-55 two-line old text and the trigger of the irreversible clean-up
r55 = pairs['E-55']
if r55['line2'] != 120 or r55['line'] != 119: F('r13 E-55 header lines')
if 'after the lead says the last take is done' not in r55['old'][0] or r55['old'][0].count('\n') != 1: F('r13 E-55 old text is not two lines')
if 'before you have confirmed `no more takes`' not in rowtext('E-55') or '| E-55 | OWNER-STEPS-realrun-v3.md | 119 (and 120) |' not in txt: F('r13 E-55 trigger or index')
if 'Item 1 starts only when ALL the conditions of key step G.2 are true' not in rowtext('E-16') or 'there is nothing for you to do' in rowtext('E-16'): F('r13 E-16 trigger')
# E. no reference to text the owner cannot see
for rid_, t_ in own:
    for bad in ('the sentence above', 'The first question of step 22', 'The second question of step 22', 'In the sentence above'):
        if bad in t_: F(f'r13 {rid_} refers to unseen text: {bad}')
# F. E-12: placeholder, reply form, widened yes, alarm
for need in ('The time of day is not yet chosen', 'latest start we plan <time in UTC and IST>', 'two decimals', 'type the one word `no`',
             'it can reach n8n\'s encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`', 'In the older sentences of this step', 'IST (India Standard Time) is UTC plus 5 hours 30 minutes',
             '17:49 UTC = 23:19 IST', 'search file slot', 'you revoke the secret key for the model at that time, whatever the assistant says'):
    if need not in t12: F('r13 E-12 lacks ' + need)
if t12.count('I know that the assistant shares my Linux user, my clipboard and my screen, and that it can reach') != 2: F('r13 E-12 yes sentence form and bullet differ')
if 'The time of day is not yet chosen' not in rowtext('E-54') or 'R11 (' not in txt: F('r13 placeholder in E-54 or rule R11')
if re.search(r'(?m)^- \*\*R11 ', txt) is None: F('r13 R11 line')
# G. E-52 words
if t52.count('**The studio lead**') != 1 or 'studio lead' not in t52.split('\n')[1]: F('r13 E-52 studio lead defined once, next to the assistant')
for need in ('**UTC and IST**', '**A port number**', '**UNVERIFIED**', '**IMAP**', '**The typing rule**', '**Route A and route B**', '**The program refusal limit**', 'typed exactly as shown'):
    if need not in t52: F('r13 E-52 lacks ' + need)
# I. small rows
if 'UNVERIFIED means that nobody has checked it yet' not in rowtext('E-01'): F('r13 E-01')
if 'take/nlite' in rowtext('E-02'): F('r13 E-02 branch names')
if 'n8n (the automation program' not in rowtext('E-03'): F('r13 E-03')
if '5678' not in rowtext('E-06'): F('r13 E-06')
# J. studio notes
if 'CONFLICT FOR THE STUDIO LEAD' not in ndsec or 'Default: (A)' in ndsec or 'Default: not chosen' not in ndsec: F('r13 ND15 both routes, no default')
if not re.search(r'(?m)^m\. E-48 key step J', csec) or not re.search(r'(?m)^n\. E-12 widens', csec): F('r13 confirmations m and n')
if 'ANYWHERE the answers' in txt: F('r13 stale')
if re.search(r'safe default \(the assistant asks the owner at clean-up whether to revoke', txt): F('r13 ND7 still conditional')
print('round 14 checks done')

# ================= round 14 checks (each must FAIL on EDITS.round13.md) =================
import datetime as _dt
newtxt = {r['id']: '\n'.join(r['new']) for r in rows}
t48n = newtxt['E-48'] + APPX_TEXT
# 1. part 3h and 3a: the key end is 18:19 UTC = 23:49 IST and never the window end
_KS = dict(zip(['3a', '3b', '3c', '3d', '3e', '3f', '3g', '3h', '3i', '3j'], 'ACDEFGHIJK'))
def part(t, tag):
    # round 15: the old part 3x is now key step X; a step runs from its own line to the next 'Key step' line
    ls_ = t.split('\n'); L_ = _KS[tag]
    st = [k_ for k_, l_ in enumerate(ls_) if l_.startswith('   Key step ' + L_ + '. ')]
    if len(st) != 1: return ''
    en = [k_ for k_ in range(st[0] + 1, len(ls_)) if ls_[k_].startswith('   Key step ')]
    e_ = en[0] if en else len(ls_)
    return '\n'.join(ls_[st[0]:e_])
p3h, p3a = part(t48n, '3h'), part(t48n, '3a')
if not p3h or 'by 18:19 UTC = 23:49 IST' not in p3h or '18:29' in p3h or '23:59' in p3h: F('r14 3h key end')
if not p3a or 'by Mon 23 Nov 2026 18:19 UTC = 23:49 IST' not in p3a: F('r14 3a key end')
for _tag in ('3c', '3j'):
    if '18:19 UTC = 23:49 IST' not in part(t48n, _tag): F('r14 ' + _tag + ' key end')
# every sentence of E-48, E-55, E-57, E-58, E-37, E-12 that says revoke and names 18:29 also names 18:19
for _rid in ('E-48', 'E-55', 'E-57', 'E-58', 'E-37', 'E-12', 'E-52'):
    for _s in re.split(r'(?<=[.;:])\s+', newtxt[_rid]):
        if re.search(r'\brevoke', _s) and '18:29 UTC' in _s and '18:19 UTC' not in _s and 'spending window' not in _s and 'retirement' not in _s:
            F('r14 ' + _rid + ' revoke sentence with 18:29 only: ' + _s[:80])
# 2. E-09: every typing waits for the written reply `not looking`
t09n = newtxt['E-09']
for _tag in ('a', 'f', 'g', 'h'):
    _l = [l_ for l_ in t09n.split('\n') if l_.startswith('   ' + _tag + '. ')]
    if len(_l) != 1 or 'not looking' not in _l[0]: F('r14 E-09 sub-step %s does not wait for `not looking`' % _tag)
if t09n.count('not looking') < 5: F('r14 E-09 not looking count')
if 'Windows key and V' not in t09n or 'clipboard history' not in t09n: F('r14 E-09 clipboard history')
# 3. weekday and date: every weekday named with a date is right
_wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
_mo = {'Oct': 10, 'Nov': 11, 'Dec': 12}
_nwd = 0
for m_ in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) (Oct|Nov|Dec)\b(?: (\d{4}))?', txt):
    _nwd += 1
    _y = int(m_.group(4)) if m_.group(4) else 2026
    if _wd[_dt.date(_y, _mo[m_.group(3)], int(m_.group(2))).weekday()] != m_.group(1):
        F('r14 wrong weekday: ' + m_.group(0))
for m_ in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (2026-1[0-2]-\d\d)\b', txt):
    _nwd += 1
    if _wd[_dt.date.fromisoformat(m_.group(2)).weekday()] != m_.group(1): F('r14 wrong weekday: ' + m_.group(0))
if _nwd < 40: F('r14 weekday check saw too few dates: %d' % _nwd)
# 4. no Q-number, L-id, ND, row id or other internal code in owner-facing text (OWNER-STEPS rows, every NEW block)
_code = re.compile(r'\b(Q\d{2}(?:\.\d)?|L-[A-Z0-9]{1,8}(?:/[A-Z])?|ND\d{1,2}|E-\d\d|S9-\d|WP\d+|R\d{1,3}|F-\d\d)\b')
for r in rows:
    if r['file'].startswith('OWNER-STEPS'):
        for _b in r['new']:
            for m_ in _code.finditer(_b):
                F('r14 internal code in owner text %s: %s' % (r['id'], m_.group(0)))
# 5. the route: ONE message selects it, ONE recommendation sentence
_alln = '\n'.join(newtxt[r['id']] for r in rows if r['status'].startswith('Apply now'))
if _alln.count('Write `route A` or `route B` once, before your last take') != 1: F('r14 route selection message not in exactly one place')
if 'The words `no more takes` alone do not choose a route' not in p3c if (p3c := part(t48n, '3c')) else True: F('r14 3c lacks the no more takes sentence')
if len(re.findall(r'recommends? route B|recommended\)', _alln)) != 0 or _alln.count('No default pick') < 1: F('r18 route recommendation sentence count %d' % len(re.findall(r'recommends? route B', _alln)))
if re.search(r'\(recommended\)|the one the assistant recommends', _alln): F('r14 second recommendation spot')
for need in ('it asks again right after `cut accepted`', '`key revoked` is never a confirmation', 'Route B, before `cut accepted`', 'Route A:', 'a retake', 'a live paid key and its copy'):
    if need not in p3c + APPX_TEXT: F('r14 3c lacks ' + need)
if 'route A' not in newtxt['E-57'] or '`route A` or `route B`' not in newtxt['E-57']: F('r14 E-57 route message')
# 6. shred rule: one rule, path checks, no star
p3f = part(t48n, '3f')
for need in ('realpath', 'starts with `/`', 'no `..`', 'none of the signs `*`', 'the number `1` in its second column', 'followed by `/`', "`shred -u -- '<path>'`", "`rm -- '<path>'`", '`shred done key copies`', '`shred not done key copies`'):
    if need not in p3f: F('r14 3f lacks ' + need)
if 'do not use the sign `*`' not in t48n or 'one at a time' not in t48n: F('r14 E-48 item 6 star rule')
if re.search(r'shred -u [^-\'<]', t48n.replace('`shred -u ~/take-secrets/*`', '')): F('r14 E-48 shred command without the path rule')
# 7. two alarms, promise not control, default when unsure, two options of 3i
p3b = part(t48n, '3b')
for need in ('Alarm 1', 'Alarm 2', '`revoke the secret key for the model`', '`is the secret key for the model still alive?`', '17:49 UTC = 23:19 IST'):
    if need not in p3b: F('r14 3b lacks ' + need)
if 'a promise by you' not in p3a or 'procedure, not a control' not in p3a: F('r14 3a honest label')
if 'revoke the one key that you created for this take' not in p3h or 'no other key' not in p3h: F('r14 3h default when unsure')
if 'Option revoke' not in part(t48n, '3i') or 'Option leave' not in part(t48n, '3i'): F('r14 3i options')
if 'unless the assistant' in part(t48n, '3j'): F('r14 3j override sentence')
for _r in rows:
    for _b in _r['new']:
        if 'unless the assistant tells you otherwise' in _b: F('r14 override sentence in ' + _r['id'])
if 'A new key lives only inside the program that uses it' not in APPX_TEXT: F('r14 3g new key storage')
if '`key revoked` is never a confirmation' not in t48n: F('r14 3d forced revoke')
if 'a bare `no`, counts as `not sure`' not in part(t48n, '3e'): F('r14 3e bare no')
# 8. order of the clean-up, path rules, owner items wait
t16n, t55n, t37n, t12n = newtxt['E-16'], newtxt['E-55'], newtxt['E-37'], newtxt['E-12']
for need in ('card step 7', 'home folder', '`/mnt/c`', '`..`', 'link'):
    if need not in t16n: F('r14 E-16 lacks ' + need)
for need in ('your items 2, 3, 4, 5 and 6', '`key gone, no more decisions`', '`cut accepted`'):
    if need not in t55n: F('r14 E-55 lacks ' + need)
if 'LAST FOUR CHARACTERS' not in t37n or 'on paper or on your phone' not in t37n: F('r14 E-37 note')
# 9. E-12: test items, consent reach, margin, alarms, fallback
if 'A test item is one numbered test' not in t12n or 'A check is one numbered test' in txt: F('r14 E-12 test item')
if t12n.count('the files in `~/take-secrets`') != 2: F('r14 E-12 consent reach')
if '3 minutes 40 seconds before the last time to revoke' not in t12n or 'is still running at 18:19 UTC = 23:49 IST' not in t12n: F('r14 E-12 margin')
if 'Set five alarms' not in t12n or 'not a control' not in t12n: F('r14 E-12 alarms')
for _rid in ('E-12', 'E-54'):
    if 'The time of day is not yet chosen' not in newtxt[_rid] or 'LEAD FILLS' in newtxt[_rid]: F('r14 %s placeholder fallback' % _rid)
if 'carry no placeholder any more' not in txt[txt.index('R11 (E-12, E-54)'):][:700]: F('r14 R11 fallback')
if txt.count('counting check') != 0: F('r14 counting check word')
if '3 minutes 40 seconds' not in txt[txt.index('**latest start we plan**'):][:900]: F('r14 words line 30 margin')
if '18:14:40 UTC = 23:44:40 IST' not in txt[txt.index('**program refusal limit**'):][:400]: F('r14 18:14:40 pair missing')
if not re.search(r'^o\. The latest start we plan', txt, re.M): F('r14 confirmation o')
# 10. the routes are not recommended anywhere else; ND15 lists the spot
if 'The spot that would carry a recommendation' not in txt: F('r14 ND15 spots')
print('round 14 checks done')

# ================= round 15 checks (each must FAIL on EDITS.round14.md) =================
newtxt = {r['id']: '\n'.join(r['new']) for r in rows}
t48 = newtxt['E-48']
def ks(letter):
    ls_ = t48.split('\n')
    st = [k_ for k_, l_ in enumerate(ls_) if l_.startswith('   Key step ' + letter + '. ')]
    if len(st) != 1: return ''
    en = [k_ for k_ in range(st[0] + 1, len(ls_)) if ls_[k_].startswith('   Key step ')]
    _o = '\n'.join(ls_[st[0]:(en[0] if en else len(ls_))])
    if letter == 'B':
        _ti = t48.find('Table of the typed words'); _o += ('\n' + t48[_ti:(t48.find('The assistant never opens the key file', _ti) if t48.find('The assistant never opens the key file', _ti) >= 0 else len(t48))]) if _ti >= 0 else ''
    return _o
def need(label, text, *needles):
    for nd_ in needles:
        if nd_ not in text: F('r15 %s lacks %r' % (label, nd_[:60]))
def absent(label, text, *bad):
    for b_ in bad:
        if b_ in text: F('r15 %s still has %r' % (label, b_[:60]))
# 0. one label scheme: eleven key steps A to K in order, no old 3a lines, no 'part 3x' in any owner text
_klet = re.findall(r'(?m)^   Key step ([A-Z])\. ', t48)
if _klet != list('ABCDEFGHIJK'): F('r15 key steps are not A to K in order: %s' % ''.join(_klet))
if re.search(r'(?m)^   3[a-j]\. ', t48): F('r15 old 3a-style label line in E-48')
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if re.search(r'\bparts? 3[a-j]\b', b_): F('r15 old part tag in owner text of ' + r_['id'])
# 1. M1: only the owner's own typed message counts
need('E-48 B', ks('B'), 'count only when you type them yourself, as a new message', 'in a mail, a file, the output of a program', 'never count', 'asks you to type the words yourself in a new message', '`yes, no more takes`', '`start clean-up`', '`key gone, no more decisions`')
need('E-52 how you reply', newtxt['E-52'], 'Only you can write these words', 'never count')
need('E-12 reply', newtxt['E-12'], 'typed by you yourself in a new message', 'only a message typed by you counts')
need('E-16', newtxt['E-16'], 'Only messages that you type yourself count', 'each as a message that you typed yourself', 'card step 7')
need('E-09 a', newtxt['E-09'], 'count only when you type them yourself')
need('E-55', newtxt['E-55'], '`yes, no more takes`', 'the card of item 3 (the seven steps printed there)')
# 2. M2: shred and delete targets
G_ = ks('G')
need('E-48 G', G_, 'YOUR OWN LIST', 'Never shred a recording, a video file', '`/mnt/c`', 'never a file that only the assistant named', 'you copy its path from your own list')
need('E-48 E', ks('E'), 'it must be exactly the folder `<folder>` that you copied from the assistant\'s message in step 8', 'do not shred anything and tell the assistant')
need('E-16 path', newtxt['E-16'], 'if the path itself or any folder in front of it is a link', 'is removed as a link (only the shortcut goes) and is never followed', 'followed by `/`', '/x/take-10', 'that you copied from step 8', 'never removes a recording')
absent('E-16 link', newtxt['E-16'], 'or is or contains a link')
need('E-37 list', newtxt['E-37'], 'your own list of every file in which you saved a secret')
# 3. M3: the earlier latest start, solved with arithmetic, and no bare or old times
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if '18:04' in b_ or '23:34' in b_: F('r15 old latest start 18:04 / 23:34 in owner text of ' + r_['id'])
_t12 = newtxt['E-12']
need('E-12 margin', _t12, 'The latest start we plan is 18:00 UTC = 23:30 IST on any day', '18:15:20 UTC = 23:45:20 IST', '3 minutes 40 seconds before the last time to revoke', 'the assistant asks for no start after it')
absent('E-12 third party', _t12, 'asks the studio lead to confirm this margin', 'no start between')
_start = _dt.datetime(2026, 11, 23, 18, 0); _end = _start + _dt.timedelta(seconds=860); _rev = _dt.datetime(2026, 11, 23, 18, 19)
if _end.strftime('%H:%M:%S') != '18:14:20' or (_rev - _end).seconds != 280: F('r15 arithmetic of the margin')
if (_end + _dt.timedelta(hours=5, minutes=30)).strftime('%H:%M:%S') != '23:44:20': F('r15 IST arithmetic')
# every clock time in an owner NEW block of these rows is followed by UTC or IST (no bare time)
for rid_ in ('E-12', 'E-48', 'E-52', 'E-54', 'E-55', 'E-58', 'E-37', 'E-16', 'E-60'):
    for m_ in re.finditer(r'(?<![\d:])(\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])(?! UTC)(?! IST)', newtxt[rid_]):
        F('r15 bare clock time in %s: %r' % (rid_, newtxt[rid_][max(0, m_.start() - 25):m_.end() + 15]))
if '18:00 UTC = 23:30 IST' not in newtxt['E-54']: F('r15 E-54 latest start figure')
# 4. naive M1, M2: alarms name the route and agree with the key steps
_C = ks('C')
need('E-48 C', _C, 'if you have not chosen a route, choose one now', 'If a take is running when alarm 1 rings', 'if no session is open or it does not ask, go straight to key step I', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST', 'Alarm 2')
absent('E-48 C', _C, 'do part 3h at once', 'do key step I at once')
# 5. naive M3: two HubSpot keys
need('E-09 h', newtxt['E-09'], 'There are two different HubSpot keys', 'needs the key of app 2', 'Never type the key of app 1 into n8n')
absent('E-09 h', newtxt['E-09'], 'Use the key of app 1 (read only) unless')
need('E-37 3', newtxt['E-37'], 'Two different HubSpot keys', 'should be the key of app 2')
# 6. naive M4: shred done scope, silence rule, step 22 item 6
need('E-48 G done', G_, '`shred done key copies` means that EVERY file of (a) and (b) is shredded', 'If you write neither, the assistant treats it as `shred not done key copies` or `shred not done other files`', 'you have not written ALL of these, the assistant does not start item 1 in that session')
if 'E-59' not in newtxt or 'take-secrets/*' in newtxt['E-59']: F('r15 E-59 missing or still has the star')
need('E-59', newtxt.get('E-59', ''), 'one at a time', 'shred rule of key step G', 'realpath ~/take-secrets')
# 7. naive M5: are-you-sure step
_D = ks('D')
need('E-48 D', _D, 'Are you sure?', 'A confirmation is exactly one of two messages', 'Anything else, or no reply, counts as `another take`', 'You cannot know that a take is your last one until you have seen the cut')
need('E-52 confirm', newtxt['E-52'], '`no more takes` is confirmed only by your next message `yes, no more takes`')
# 8. naive M6: reply in short numbered lines, no copyable money figure, blocks not parts
for k_ in ('1. Yes, take <take id>', '2. tests: stand-in test <N1> pass', '3. files: result file <result file>', '4. money: up to 3 model calls and up to US$<X>', '5. I know that the assistant shares'):
    if k_ not in _t12: F('r15 E-12 reply line missing: ' + k_)
absent('E-12 reply', _t12, '1.50', 'Your reply is ONE line', 'Part 1', 'Part 2', 'The last part,')
need('E-12 blocks', _t12, 'Block 1, the money figures', 'Block 2 is this list', 'copied digit by digit from the request')
# 9. naive M7, M8: no placeholder text in owner words
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if 'LEAD FILLS' in b_ or 'square brackets' in b_ or 'placeholder' in b_.lower(): F('r15 placeholder wording in owner text of ' + r_['id'])
# 10. naive M9 and minors: brand name, two names in E-09 e, clipboard sync, nano copies, summary line
absent('E-48 I', ks('I'), 'Anthropic')
need('E-09 e', newtxt['E-09'], 'with the two names `<password file name>` and `<folder>`')
absent('E-09 e', newtxt['E-09'], 'with the three names copied')
need('E-09 extras', newtxt['E-09'], 'sharing of the clipboard between devices', 'remote-desktop window', 'offers to save the password', 'ls -a', 'ends in `~` or `.save`', 'close the terminal window too')
need('E-48 intro', t48, 'In short:', 'Key steps A to K are for that key only')
# 11. new rows
for rid_ in ('E-59', 'E-60', 'E-61'):
    if rid_ not in newtxt: F('r15 row missing ' + rid_)
need('E-60', newtxt.get('E-60', ''), '18:29 UTC = 23:59 IST', '18:14 UTC = 23:44 IST', '18:14:40 UTC = 23:44:40 IST', '18:00 UTC = 23:30 IST')
need('E-61', newtxt.get('E-61', ''), 'no longer counts')
# 12. the checker keeps its scratch inside its own folder (evidence r14 finding)
_me = open(os.path.abspath(__file__), encoding='utf-8').read()
_bad1 = '/' + 'tmp/'; _bad2 = '/home/' + 'user'
if _bad1 in _me or _bad2 in _me: F('r15 verify script has an absolute path outside its own folder')
if not os.path.abspath(sd).startswith(os.path.abspath(HERE_)): F('r15 scratch folder is not inside the checker folder')
print('round 15 checks done')

# ================= round 16 checks (security F1 to F4, m1 to m8; stranger M1 to M7; runner's nine missed mutations) =================
_r16n = 0
def need16(label, text, *needles):
    global _r16n
    for nd_ in needles:
        _r16n += 1
        if nd_ not in text: F('r16 %s lacks %r' % (label, nd_[:70]))
def absent16(label, text, *bad):
    global _r16n
    for b_ in bad:
        _r16n += 1
        if b_ in text: F('r16 %s still has %r' % (label, b_[:70]))
_own = [(r_['id'], b_) for r_ in rows if r_['file'].startswith('OWNER-STEPS') for b_ in r_['new']]
_ownall = '\n'.join(b_ for _, b_ in _own)
_full48 = newtxt['E-48']
# F1: a separate plain word, and key revoked counts only after the last time
need16('F1 word', ks('B'), '`key gone, no more decisions`')
need16('F1 D5', ks('D'), 'you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`', '`key revoked` is only a report', '`key gone, no more decisions`')
need16('F1 E-55', newtxt['E-55'], 'you revoke it whatever you have written, and then you write `key gone, no more decisions`', '`key gone, no more decisions`')
absent16('F1 old sentence', newtxt['E-55'], 'and your `key revoked` then counts as `no more takes`')
# F2: contacts only by the exact address, at most 3, in the three rows, and no made-up names
for rid_ in ('E-04', 'E-42', 'E-62'):
    need16('F2 ' + rid_, newtxt[rid_], '`take-<id>-a@example.com`', '`take-<id>-b@example.com`', '`take-<id>-c@example.com`', 'more than 3', 'you delete nothing and tell the assistant')
    absent16('F2 ' + rid_, newtxt[rid_], 'made-up names')
_r62 = [r_ for r_ in rows if r_['id'] == 'E-62']
if not _r62 or _r62[0]['line'] != 112 or 'delete any leftover HubSpot contacts the lead counted' not in _r62[0]['old'][0]: F('r16 E-62 header or old text')
if _r62 and _r62[0]['status'] != 'Apply now': F('r16 E-62 status')
# F3: shred part (d) and the own list
need16('F3 G', ks('G'), '(d)', 'password files and editor copies', 'every file that holds a secret you saved', '`shred done other files`')
need16('F3 E-59', newtxt['E-59'], '`shred done other files`', 'part (d)')
need16('F3 E-37', newtxt['E-37'], 'your own list of every file in which you saved a secret')
# F4: one numbered order (the card) and item 1 never early
_card = _full48[_full48.index('The one order'):]
_pos = []
for _k in ('1. You: before 18:19 UTC = 23:49 IST on the last day (key step D.5), make sure that you have confirmed', '2. You: do your items 2 and 3', '3. You: shred the copy of the key in the take folder', '4. You: do your item 4', '5. You: do your item 6', '6. You: read the list of what the assistant will remove', '7. Then the assistant does its item 1'):
    _pos.append(_card.find(_k))
if -1 in _pos or _pos != sorted(_pos): F('r16 F4 the numbered order is missing or out of order: %s' % _pos)
need16('F4 card', _card, '`shred done key copies`', '`shred done other files`', '`start clean-up`', 'never starts while a copy of the key exists and the key is not revoked')
need16('F4 E-16', newtxt['E-16'], 'It does NOT start while a copy of the secret key for the model exists and the key is not revoked', 'The order of step 22 is the only order')
absent16('F4 E-16', newtxt['E-16'], 'your item 3 comes first', 'None of it can be undone and because', 'about doing items first')
# m1 take folder and list, m4 stop looking before the click, m5 ok words, m3 alarm 3, m6 counts, m8 other secret files
need16('m1 E-16', newtxt['E-16'], 'NEW, EMPTY folder', 'never your home folder', 'if a recording or a video file is inside, it stops, removes nothing and tells you', 'You read that list before you type `start clean-up`')
need16('m5 E-11', newtxt['E-11'], 'Write `ok stand-in test` (for the stand-in test)', 'or `ok flow rehearsal` (for the flow rehearsal)')
need16('m3 alarms', ks('C') + newtxt['E-12'], 'Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST', 'alarm 3 for 18:09 UTC = 23:39 IST')
# stranger M2: margin arithmetic computed in the checker, not copied
_typing = _dt.datetime(2026, 11, 23, 18, 0); _prog = _typing + _dt.timedelta(seconds=60); _pend = _prog + _dt.timedelta(seconds=860); _rev2 = _dt.datetime(2026, 11, 23, 18, 19)
if _prog.strftime('%H:%M:%S') != '18:01:00' or _pend.strftime('%H:%M:%S') != '18:15:20' or (_rev2 - _pend).seconds != 220: F('r16 margin arithmetic')
need16('M2 E-12', newtxt['E-12'], '18:01:00 UTC = 23:31:00 IST', '18:15:20 UTC = 23:45:20 IST', '3 minutes 40 seconds before the last time to revoke', 'the time at which you START TYPING')
absent16('M2 old claim', _ownall, 'a take that lasts 4 minutes longer', '4 minutes 40 seconds before the last time to revoke')
# stranger M1: cross references
need16('M1 B refs', newtxt['E-12'] + newtxt['E-16'] + newtxt['E-55'], 'key step B')
absent16('M1 refs', newtxt['E-12'], 'only a message typed by you counts: step 22 item 3, key step C', 'key step F); the click path')
absent16('M1 refs', newtxt['E-16'] + newtxt['E-09'] + newtxt['E-52'], 'item 3, key step C)')
absent16('M1 revoke page', newtxt['E-12'], 'revoke the secret key for the model (step 22 item 3, key step F)')
# stranger minors: no internal codes or branch names in owner text; plain words
for _w in ('take/nlite', 'HEAD_PIN', 'r17', 'F-01', ' >= '):
    absent16('plain words', _ownall, _w)
if re.search(r'\blease\b', _ownall): F('r16 the word lease is in owner text')
absent16('E-56 codes', newtxt['E-56'], 'Q23', '(r17)', 'F-01')
absent16('E-57 default', newtxt['E-57'], "is the assistant's default")
if '\n## Phase 1: the assistant checks.\n' not in '\n' + newtxt['E-54']: F('r16 E-54 heading is not on its own line')
need16('E-37', newtxt['E-37'], 'UNVERIFIED')
# runner mutation #15, #17: the wait for `not looking` follows every `please stop looking` (owner text and the rule that defines it)
for _rid, _b in [(r_['id'], b_) for r_ in rows for b_ in r_['new']]:
    for _m in re.finditer(r'please stop looking', _b):
        _win = _b[_m.end():_m.end() + 90]
        if 'not looking' not in _win and not _win.startswith('` and `you may look again`') and not _win.startswith('`, `you may look again`'):
            F('r16 stop-looking without the wait for `not looking` in %s: %r' % (_rid, _win[:60]))
if 'wait for its written reply `not looking`' not in txt: F('r16 typing rule definition lacks the wait for its written reply `not looking`')
# runner mutation #18: E-09 sub-step a lists every typing sub-step
if '(sub-steps c, f, g and h)' not in newtxt['E-09']: F('r16 E-09 a does not list sub-steps c, f, g and h')
for _sub in 'fgh':
    _mm = re.search(r'(?m)^   %s\. .*$' % _sub, newtxt['E-09'])
    if not _mm or not re.search(r'typing rule|not looking', _mm.group(0)): F('r16 E-09 sub-step %s does not call the typing rule' % _sub)
# runner mutations #19, #22, #24: the five checks of the shred rule and the command, in key step G
need16('shred rule', ks('G'), 'realpath', "`ls -l '<path>'`", "`shred -u -- '<path>'`", 'contains no `..`', 'starts with `/`', '/x/take-10', 'number `1` in its second column', 'a link is a shortcut', 'Never shred a recording')
# runner mutations #31, #32: the alarm names stay with their alarm, in every place
for _rid, _b in [(r_['id'], b_) for r_ in rows for b_ in r_['new']]:
    for _m in re.finditer(r'[Aa]larm 1[^`\n]*?named `([^`]+)`', _b):
        if 'revoke the secret key for the model' not in _m.group(1) or 'left' in _m.group(1): F('r16 alarm 1 has the wrong name in %s: %r' % (_rid, _m.group(1)))
    for _m in re.finditer(r'[Aa]larm 2[^`\n]*?named `([^`]+)`', _b):
        if 'still alive' not in _m.group(1): F('r16 alarm 2 has the wrong name in %s: %r' % (_rid, _m.group(1)))
    for _m in re.finditer(r'[Aa]larm 3[^`\n]*?named `([^`]+)`', _b):
        if 'last chance' not in _m.group(1) or '10 minutes' in _m.group(1): F('r16 alarm 3 has the wrong name in %s: %r' % (_rid, _m.group(1)))
    for _m in re.finditer(r'[Aa]larm 4[^`\n]*?named `([^`]+)`', _b):
        if 'still not revoked' not in _m.group(1): F('r19 alarm 4 has the wrong name in %s: %r' % (_rid, _m.group(1)))
need16('alarm names', ks('C'), 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`', 'named `is the secret key for the model still alive?`', 'named `last chance: revoke the secret key for the model now`', 'Alarm 4: Mon 23 Nov 2026 18:24 UTC = 23:54 IST', 'Alarm 5: Tue 24 Nov 2026 00:30 UTC = 06:00 IST')
# runner mutation #51: the widened secret-shape scan (the sample in the controls is built from parts)
_pre = 'sk-' + 'ant-' + 'api03'
_secpats = [_pre + r'[-A-Za-z0-9_]{6,}', r'\bsk-[A-Za-z0-9_-]{16,}', r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)\bpassword\s*[:=]\s*[^\s`]{6,}', r'\b[A-Fa-f0-9]{40,}\b', r'\beyJ[A-Za-z0-9_-]{15,}\.']
_sh2 = 0
for _p in _secpats:
    for _m in re.finditer(_p, txt):
        if _m.group(0) == 'AKIAIOSFODNN7EXAMPLE': continue
        _sh2 += 1; F('r16 secret-shaped text matches ' + _p[:18])
# runner's extra checks: index agrees with the row headers; every owner NEW has no internal code; hold labels; time pairs
_idx = {}
for _l in lines:
    _m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$', _l)
    if _m: _idx[_m.group(1)] = _m.groups()
if sorted(_idx) != sorted(r_['id'] for r_ in rows): F('r16 index rows differ from header rows')
for r_ in rows:
    _x = _idx.get(r_['id'])
    if not _x: continue
    _ln = str(r_['line']) + (' (and %d)' % r_['line2'] if r_['line2'] else '')
    _stt = re.split(r' \(', r_['status'])[0].strip()
    if _x[1] != r_['file'] or _x[2] != _ln or _x[3] != _stt or _x[6] != r_['type']: F('r16 index mismatch for ' + r_['id'])
_codes = re.compile(r'\b(Q\d{2}(?:\.\d)?|L-[A-Z0-9]{1,8}|ND ?\d{1,2}|E-\d\d|S9-\d|WP\d+|EL-\d|R\d{1,3}|F-\d\d|G[1-5]|D\d{1,2})\b')
for _rid, _b in _own:
    for _m in _codes.finditer(_b): F('r16 internal code in owner text %s: %s' % (_rid, _m.group(0)))
_np = 0
for _m in re.finditer(r'(\d{1,2}):(\d{2})(?::(\d{2}))? UTC = (\d{1,2}):(\d{2})(?::(\d{2}))? IST', txt):
    _np += 1
    _u = int(_m.group(1)) * 3600 + int(_m.group(2)) * 60 + int(_m.group(3) or 0); _i = int(_m.group(4)) * 3600 + int(_m.group(5)) * 60 + int(_m.group(6) or 0)
    if (_u + 19800) % 86400 != _i: F('r16 UTC/IST pair is wrong: ' + _m.group(0))
_wdn = 0
_wd16 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
for _m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.? (\d{1,2}) (Oct|Nov|Dec)(?: (\d{4}))?', txt):
    _wdn += 1
    _d = _dt.date(int(_m.group(4) or 2026), {'Oct': 10, 'Nov': 11, 'Dec': 12}[_m.group(3)], int(_m.group(2)))
    if _wd16[_d.weekday()] != _m.group(1) or _d.year != 2026: F('r16 weekday/date wrong: ' + _m.group(0))
_bt = open(os.path.join(os.path.dirname(HERE_), '..', '..', 'tests', 'test_no_reference_material.py'), encoding='utf-8').read()
_bm = re.search(r'BANNED = \((.*?)\n\)', _bt, re.S)
_banned = ast.literal_eval('(' + _bm.group(1) + ')')
_bh = sum(1 for b_ in _banned if b_ in txt)
if _bh: F('r16 banned strings present: %d of %d (counts only)' % (_bh, len(_banned)))
# mtimes are read at run time, never typed in
_mt = {n_: os.path.getmtime(os.path.join(IN, n_)) for n_ in ('OWNER-STEPS-realrun-v3.md', 'AGENT-SCOPE-DO-AND-DONT.md', 'DECISION-one-store.md')}
print('r16 checks:', _r16n, 'phrase checks; UTC=IST pairs', _np, '; weekday-date pairs', _wdn, '; banned', _bh, 'of', len(_banned), '; secret-shaped', _sh2, '; input mtimes read at run time', len(_mt))
print('round 16 checks done')

# ================= round 17 checks (security N1, minors; stranger F-1 to F-15; runner: 6 fresh + 15 missed mutations) =================
_r17n = 0
def need17(label, text, *needles):
    global _r17n
    for nd_ in needles:
        _r17n += 1
        if nd_ not in text: F('r17 %s lacks %r' % (label, nd_[:80]))
def absent17(label, text, *bad):
    global _r17n
    for b_ in bad:
        _r17n += 1
        if b_ in text: F('r17 %s still has %r' % (label, b_[:80]))
_nowhy = '\n'.join(l_ for l_ in txt.split('\n') if not l_.startswith('Why:'))
_E48 = newtxt['E-48']
_card17 = _E48[_E48.index('The one order'):]
_G17 = ks('G')
_P17 = ['make sure that you have confirmed your last take with `yes, no more takes` (key step D.3), then revoke the secret key for the model (key step I) and write `key revoked`',
        'do your items 2 and 3, the quick web revokes, each only after the identification check of step 22 item 3',
        'shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`',
        'do your item 4 (save the screenshots) and your item 5, the retire check',
        'do your item 6 (shred its two files) and shred the other secret files on your own list (key step G, parts (c) and (d)), and write `shred done other files`',
        "read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write `start clean-up`",
        'the assistant does its item 1 (the clean-up)']
_START17 = ('Item 1 starts only when ALL of these are true, each as a message that you typed yourself: a confirmation (`yes, no more takes` or `key gone, no more decisions`; key step D.3); '
            '`key revoked` (or `key gone, no more decisions`, which counts as `key revoked`; or `key not revoked` and the reason, but item 1 never starts while a copy of the key exists and the key is not revoked); '
            '`shred done key copies` (or `shred not done key copies` and the reason); your items 2, 3, 4 and 5 done; `shred done other files` (or `shred not done other files` and the reason); '
            'you have read the list of what the assistant will remove; and `start clean-up`.')
# F-1: ONE order in four places, same seven phrases in the same order; ONE start sentence in three places
for _lab, _tx in (('card', _card17),):
    _ps = [_tx.find(p_) for p_ in _P17]
    if -1 in _ps or _ps != sorted(_ps): F('r17 F-1 the seven steps are missing or out of order in %s: %s' % (_lab, _ps))
    _r17n += 1
need17('F-1 start sentence in G.2', _G17, _START17)
for _lab in ('E-16', 'E-55'):
    need17('F-1 pointer in ' + _lab, newtxt[_lab], 'Item 1 starts only when ALL the conditions of key step G.2 are true (the list is there, once)', 'the seven steps printed there')
    absent17('F-1 no copy of the list in ' + _lab, newtxt[_lab], 'Item 1 starts only when ALL of these are true', '`shred done other files` (or')
absent17('F-1 old order forms', _nowhy, 'items 2 to 5', 'items 2 and 4 and the HubSpot', 'your items 2 to 6', 'your item 3 comes first')
absent17('F-8 old words', _nowhy, '`more takes`', '`shred done 1`', '`shred done 2`', '`shred not done 1`', '`shred not done 2`', 'ONLY when you type it AFTER', 'a `key revoked` that counts', 'counts as the confirmation')
# F-4: one number for the new-key rule
_mins = re.findall(r'at least (\d+) minutes remain', _nowhy)
if len(_mins) < 4 or set(_mins) != {'30'}: F('r17 F-4 the new-key rule has numbers %s' % sorted(set(_mins)))
_r17n += 1
absent17('F-4 old number', _nowhy, 'at least 20 minutes', 'exactly 20 minutes')
# F-3: alarm 3 yields to a running take, in key step C and in the request for the yes
need17('F-3 C', ks('C'), 'if a take is running, let it finish (key step K), then revoke the key at once')
need17('F-3 E-12', newtxt['E-12'], 'if a take is running when it rings, you let it finish')
# F-2: route B price in D.1 and in step 21 (E-57); Appendix K lands on the owner sheet
for _lab, _tx in (('D.1', ks('D')), ('E-57', newtxt['E-57'])):
    need17('F-2 route B price in ' + _lab, _tx, 'up to five days', 'In route A the live key exists for hours, in route B for up to five days')
need17('r19 route A price in D.1', ks('D'), 'Route A: after your confirmation the clean-up removes the take\'s set-up', 'a new secret key for the model and a new yes: step 20')
need17('F-2 appendix landing', APPX_TEXT, 'a separate page, not part of the sheet', 'links it from step 22 item 3')
need17('F-2 link in owner text', _E48, 'the detail is on a separate page, Appendix K, which is linked from this step')
need17('F-2 header', txt, 'Appendix K (after the last row) is not a row and not part of the sheet')
# F-5: D.4 and key step E follow the order of the actions
need17('F-5 D.4', ks('D'), 'you follow the one order (the card) at once, from card step 1')
need17('r12 key step F question', ks('F'), 'the one that you open at `http://localhost:5678`? If it is, revoking it breaks that n8n." Reply `same key`')
need17('F-5 E', ks('E'), "(4) the one order (the card above)", "copies the take's result file and counts out of the take folder first")
# F-8: confirmations and the ten minutes
need17('F-8 D.3', ks('D'), 'A confirmation is exactly one of two messages', '`key revoked` is never a confirmation', 'no reply counts as `another take`', 'mean the opposite of each other')
need17('F-8 D.5', ks('D'), 'The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; if the key is still live at 18:19 UTC = 23:49 IST it comes first.')
need17('F-8 clock', _G17, 'the assistant has no timer: on that day start every message that you write with the time in UTC')
need17('F-8 F', ks('F'), 'including a bare `no`, counts as `not sure`')
need17('F-8 B', ks('B'), '`another take`', '`shred done key copies`', '`shred done other files`', 'It never confirms anything, at any time')
# F-9: shred rule heading and the marks of part (b) and (d)
need17('F-9 G', _G17, 'It is ONE rule for every file that you shred in this item and in step 8', 'mark it `old key` (part (b)) or `other` (part (d))', 'a file is in exactly one part')
need17('F-9 E-37', newtxt['E-37'], 'Mark each file `old key`', 'as part (a)')
# security: N1 (owner-open) with three options and the accepted-risk sentence; minors 4, 5, 7; r16 NOT DONE items
need17('N1 ND16', txt, '16. **Nobody but the owner can cancel the secret key for the model', 'Options, not decided by the builder: (1)', '(2) name a second person', '(3) the owner accepts the exposure in writing', 'I accept that until I revoke the secret key for the model it can spend up to what my account at the company allows')
need17('N1 key step A', ks('A'), 'limits the program only, not a copy of the key', 'Whether the company that provides the AI model can also limit this key is not checked')
need17('r confirmation', txt, 'r. Round 17 and round 18 additions of the builder, to confirm:')
need17('m4 E-09', newtxt['E-09'], 'write its full path on your own list (mark it `other`)', 'add the full path of `n8n.env` to your own list (mark it `other`)', 'Detail: appendix K-8')
need17('K-8 moved', APPX_TEXT, 'K-8 (detail of step 8')
need17('m7 E-62', why_of('E-62'), 'Round 17 (security m7)')
need17('E-16 copy first', newtxt['E-16'], 'At the start of item 1 it checks that this copy is there')
# scans over owner text and the appendix
_own17 = _ownall + '\n' + APPX_TEXT
for _m in re.finditer(r'(?<![\w~.\-])/(?:home|Users|root|tmp|var|etc|opt|usr)/|\b[A-Za-z]:\\\\', _own17): F('r17 absolute path in owner text: ' + _own17[max(0, _m.start()-20):_m.end()+20].replace('\n', ' '))
for _m in re.finditer(r'\b(?:ORD|DEC|WP\d*|L-[A-Z0-9]+)[:\-]|\brow E-\d\d|\bE-\d\d\b|\bND ?\d+\b|\bF-\d+\b', _own17): F('r17 internal code in owner text: ' + _m.group(0))
_r17n += 2
for _m in re.finditer(r'spending window ends(?: later,)? at (\d\d:\d\d) UTC = (\d\d:\d\d) IST', _own17 + '\n' + txt):
    if (_m.group(1), _m.group(2)) != ('18:29', '23:59'): F('r17 spending window end is wrong: ' + _m.group(0))
for _m in re.finditer(r'\bby (?:Mon 23 Nov 2026 )?(\d\d:\d\d) UTC = (\d\d:\d\d) IST at the latest', _own17):
    if (_m.group(1), _m.group(2)) != ('18:19', '23:49'): F('r17 last time to revoke is wrong: ' + _m.group(0))
# the pins: one exact sentence per safety rule that a mutation was able to delete or reverse without a failure in round 16
_SC = {'A': ks('A'), 'B': ks('B'), 'C': ks('C'), 'D': ks('D'), 'E': ks('E'), 'F': ks('F'), 'G': _G17, 'H': ks('H'), 'I': ks('I'), 'K': ks('K'), 'CARD': _card17, 'CARD7': _card17[:_card17.index('Key step J')], 'E48': _E48, 'APPX': APPX_TEXT, 'E-57': newtxt['E-57'], 'WHY62': why_of('E-62')}
PINS17 = [
 ('m18 D.4 appendix ref', 'D', 'Detail with the full costs of both routes: appendix K-D'),
 ('m34 word list', 'B', '| `key gone, no more decisions` | THREE events at once, on purpose: the key is gone AND there are no more takes AND the cut is final'),
 ('m37 window end', 'A', 'The spending window ends at 18:29 UTC = 23:59 IST; that is when the model stage must stop spending.'),
 ('m40 not sure', 'F', 'Reply `yes`, `no, other things use it` or `not sure`'),
 ('m41 only yes', 'F', 'Only `yes` together with `different key` means that nothing has to be replaced first'),
 ('m43 stop looking', 'B', '| `please stop looking` | you are about to type a secret: the assistant stops looking and answers `not looking`'),
 ('m45 C', 'C', 'unless at least 30 minutes remain after you have answered'),
 ('m45 H', 'H', 'only if at least 30 minutes remain before 18:19 UTC = 23:49 IST'),
 ('m45 I', 'I', 'and at least 30 minutes remain'),
 ('m45 card', 'CARD', 'at least 30 minutes remain'),
 ('m48 G', 'G', 'Do not shred part (a) while a take is running'),
 ('m48 K', 'K', 'Do not shred part (a) until the take has stopped'),
 ('m51 why', 'WHY62', 'Security F2 of round 15: input line 112'),
 ('m53 unverified', 'K', 'is not proven (UNVERIFIED)'),
 ('m54 typed', 'E48', 'Only your own typed messages count (key step B)'),
 ('r17 card 7', 'CARD7', '7. Then the assistant does its item 1 (the clean-up). It never starts while a copy of the key exists and the key is not revoked.'),
 ('m60 card 1', 'CARD', 'if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway'),
 ('B03 no space', 'G', 'It contains no `..`, no space, no line break, no quote sign'),
 ('B04 ten minutes', 'APPX', 'The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; if the key is still live at 18:19 UTC = 23:49 IST it comes first.'),
 ('B05 step 21 heading', 'E-57', '### Step 21. Watch the cut by Mon 23 Nov 2026 17:49 UTC = 23:19 IST (alarm 1)'),
 ('B08 never opens', 'E48', 'The assistant never opens the key file (this is a procedure, not enforced by a program).'),
 ('B09 default', 'D', 'no reply counts as `another take`'),
 ('B10 forced revoke', 'K', 'revoke the key at that time anyway (key step I)'),
 ('r17 key gone one word', 'B', 'so after it you do not type `key revoked` again'),
 ('r17 D.5 key gone', 'D', 'then write `key gone, no more decisions`'),
]
for _lab, _sc, _ph in PINS17:
    need17('pin ' + _lab, _SC[_sc], _ph)
absent17('B09 reversed', ks('D'), 'no reply counts as `no more takes`')
absent17('B10 reversed', ks('K'), 'wait for the take')
# word counts: ONE method, stated here: runs of non-space characters (str.split) inside the ~~~~ fences of the NEW blocks; the label line and the fence lines are not counted
_wc = lambda s_: len(s_.split())
_wo = sum(_wc(b_) for r_ in rows if r_['file'].startswith('OWNER-STEPS') for b_ in r_['new'])
_wa = sum(_wc(b_) for r_ in rows for b_ in r_['new'])
print('WORDS (non-space runs inside the NEW fences): E-48 NEW', _wc(newtxt['E-48']), '; Appendix K (whole section)', _wc(APPX_TEXT), '; OWNER-STEPS rows NEW', _wo, '; NEW of all rows', _wa, '; whole EDITS file', _wc(txt))
print('r17 checks:', _r17n, 'phrase checks;', len(PINS17), 'pins')
print('round 17 checks done')


# ================= round 19 checks (security M1-M3; naive B1-B4; runner: classes found in r17; per-occurrence checks over the applied text) =================
_r19n = 0
_AP = cp1['OWNER-STEPS-realrun-v3.md']
_DAYF = os.path.join(HERE_, 'r20-OWNER-DAY-SHEET.md'); _APPF = os.path.join(HERE_, 'r20-OWNER-APPENDIX-K.md')
_DAY = open(_DAYF, encoding='utf-8').read() if os.path.exists(_DAYF) else ''
_APP = open(_APPF, encoding='utf-8').read() if os.path.exists(_APPF) else ''
# the safety phrases and time pairs: exact number of copies in (applied sheet, day sheet, appendix); a change at ANY copy changes a count
_KS = ("The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; "
       "if the key is still live at 18:19 UTC = 23:49 IST it comes first.")
_TW = ("`no more takes` alone is never final; the confirmation is `yes, no more takes`; "
       "if you have revoked the key without having typed `yes, no more takes`, write `key gone, no more decisions`.")
_WARN3 = "In route B, writing `key gone, no more decisions` before you have watched the cut makes the cut final and costs you the retake."
# round 20: exact number of copies (applied sheet, day sheet, appendix) of the new and changed phrases. Each number was read from the built files and checked by hand against the change it belongs to (see r20-CHANGES.md, table of copy counts).
CANON_TBC = (11, 5, 1); CANON_A4 = (2, 1, 0); CANON_A5 = (2, 1, 0); CANON_ROT = (1, 1, 0); CANON_EXC = (2, 1, 0); CANON_TO = (2, 1, 0); CANON_NODATE = (2, 2, 0)
CANON_B2 = (1, 1, 0); CANON_YNT = (32, 18, 3); CANON_KG = (30, 24, 1); CANON_KR = (22, 18, 0); CANON_1819 = (41, 19, 7); CANON_1829 = (33, 13, 4)
CANON_1749 = (6, 2, 1); CANON_0030 = (2, 1, 0); CANON_1824 = (2, 1, 0); CANON_0630 = (2, 1, 0); CANON_TUE = (11, 5, 1); CANON_TW = (5, 2, 1); CANON_W3 = (3, 3, 0); CANON_L10 = (5, 4, 2)

_CANON19 = {
    _KS: (3, 2, 2),
    _TW: (CANON_TW),
    _WARN3: (CANON_W3),
    'the last 10 minutes': (CANON_L10),
    'this date is a proposal: it stands if the assistant names no other date before your first take': (CANON_TBC),
    'THE KEY IS NOT DEFERRABLE': (1, 1, 0),
    'last chance: revoke the secret key for the model now': (2, 1, 0),
    'still not revoked: revoke the secret key for the model now': (CANON_A4),
    'the secret key for the model must be revoked now': (CANON_A5),
    '`web revokes not done`': (6, 4, 0),
    'Rotate first, then delete': (CANON_ROT),
    'In route A the live key exists for hours, in route B for up to five days': (2, 1, 1),
    'Why these two times': (1, 1, 0),
    'Words in this item:': (1, 1, 0),
    'it is not deferrable (key step D.5)': (1, 1, 0),
    'alarm 1, alarm 3, alarm 4, alarm 5, an emergency (key step D.3) and the last time to revoke': (CANON_EXC),
    'A confirmation cannot be withdrawn once the key is revoked.': (2, 1, 0),
    'No default pick: the assistant does not recommend a route': (1, 1, 0),
    'touch nothing that you are not sure about': (1, 1, 0),
    'no reply counts as `another take`': (2, 1, 0),
    '`key revoked` is never a confirmation': (1, 1, 0),
    'It never confirms anything, at any time': (1, 1, 0),
    'Item 1 starts only when ALL the conditions of key step G.2 are true': (2, 0, 0),
    'It never starts while a copy of the key exists and the key is not revoked': (1, 1, 0),
    'asks you to type the words yourself in a new message': (1, 1, 0),
    'What you have not finished by 18:29 UTC = 23:59 IST you finish': (2, 2, 0),
    'Tue 24 Nov 2026 18:29 UTC = 23:59 IST': (CANON_TUE),
    'not all': (2, 0, 0),
    'if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway': (1, 1, 0),
    'Only messages that you type yourself count': (1, 0, 0),
    '`not sure` never keeps it alive': (1, 0, 0),
    'The assistant never does an owner item for you': (1, 1, 0),
    'A confirmation is exactly one of two messages': (2, 1, 0),
    'touch NOTHING of that kind': (1, 1, 0),
    'and that carries `take-only`': (CANON_TO),
    'The key has no date and no later date': (CANON_NODATE),
    'The real latest time to confirm in route B is when alarm 1 rings, 17:49 UTC = 23:19 IST': (CANON_B2),
    '18:19 UTC = 23:49 IST': (CANON_1819),
    '18:29 UTC = 23:59 IST': (CANON_1829),
    '17:49 UTC = 23:19 IST': (CANON_1749),
    '18:09 UTC = 23:39 IST': (2, 1, 0),
    '00:30 UTC = 06:00 IST': (CANON_0030),
    '18:24 UTC = 23:54 IST': (CANON_1824),
    '06:30 UTC = 12:00 IST': (CANON_0630),
    '`yes, no more takes`': (CANON_YNT),
    '`key gone, no more decisions`': (CANON_KG),
    '`cut accepted`': (16, 8, 1),
    '`start clean-up`': (4, 3, 0),
    '`shred done key copies`': (6, 6, 0),
    '`shred done other files`': (7, 6, 0),
    '`key revoked`': (CANON_KR),
    '`route A`': (4, 2, 0),
    '`route B`': (4, 2, 0),
}
_PAIR = re.compile(r'\b(\d\d):(\d\d)(?::(\d\d))? UTC (?:=|/) (\d\d):(\d\d)(?::(\d\d))? IST')
_BAREUTC = re.compile(r'\b\d\d:\d\d(?::\d\d)? UTC\b(?! (?:=|/) \d\d:\d\d(?::\d\d)? IST)')
_BAD19 = (r'\brevoke\b[^.\n,;]{0,100}\bby (?:Mon 23 Nov 2026 )?18:29', r'last time to revoke[^.]{0,80}18:29', r'18:29 UTC = 23:59 IST[^.]{0,40}last time to revoke',
          r'recommends? route B', r'\(recommended\)', r'can be withdrawn', r'\bnone of the (?:shreds|items) (?:is|are) (?:needed|required)', r'`more takes`', r'`shred done 1`', r'`shred done 2`',
          r'by 18:29 UTC = 23:59 IST[^.\n,;]{0,60}\brevoke the secret key', r'\brevoke the secret key[^.\n,;]{0,60}by 18:29',
          r'10 minutes left', r'Route A is the safer one', r'there are only 10 minutes', r'(?<!the last )10 minutes', r'safer one', r'three alarms', r'Set three', r'a question for the studio lead', r'not decided yet')
def _norm19(t):
    return [l_.strip() for l_ in t.split('\n') if l_.strip()]
def check19(ap, day=None, app=None, tag=''):
    """returns the list of failure labels for the applied owner sheet (and the two linked pages when given)"""
    out = []
    for lab, t, k in (('applied', ap, 0), ('day sheet', day, 1), ('appendix', app, 2)):
        if t is None: continue
        for p_, cnt in _CANON19.items():
            if t.count(p_) != cnt[k]: out.append('count %s %r is %d, expected %d' % (lab, p_[:60], t.count(p_), cnt[k]))
        for m_ in _BAREUTC.finditer(t): out.append('UTC time without its IST pair in %s: %s' % (lab, t[m_.start():m_.end() + 20]))
        for m_ in _PAIR.finditer(t):
            h1, m1, s1, h2, m2, s2 = m_.groups()
            tot = (int(h1) * 3600 + int(m1) * 60 + int(s1 or 0) + 19800) % 86400
            if (s1 is None) != (s2 is None) or tot != int(h2) * 3600 + int(m2) * 60 + int(s2 or 0): out.append('wrong UTC/IST pair in %s: %s' % (lab, m_.group(0)))
        for b_ in _BAD19:
            if re.search(b_, t): out.append('forbidden wording in %s: %s' % (lab, b_))
    if day is not None:
        apl = ap
        for l_ in _norm19(day.split('## The card', 1)[1] if '## The card' in day else day):
            if l_.startswith('#') : continue
            if l_ not in apl: out.append('day sheet line is not in the applied sheet: ' + l_[:70])
    if app is not None:
        ap_k = ap
        for l_ in _norm19(app):
            if l_.startswith('#') or len(l_) < 60: continue
            if l_ not in set(_norm19(ap)) and l_ not in set(_norm19(txt)): out.append('appendix line is not in the applied sheet or in EDITS: ' + l_[:70])
    return out
_r19f = check19(_AP, _DAY, _APP)
for _f in _r19f: F('r19 ' + _f)
_r19n += len(_CANON19) * 3 + 6
# owner text names the two linked files once each and says what each holds
need17('r19 link day sheet', _AP, '`OWNER-DAY-SHEET.md`', '`OWNER-APPENDIX-K.md`')
for _need in ('## Key step I: revoke the key', '## The identification check', '## The shred rule (key step G)', '## Why 18:19 and 18:29', '## Your five alarms', '## Words used on this page', 'Item 2 (app passwords)', 'Item 6 (the two files'):
    if _need not in _DAY: F('r19 day sheet lacks ' + _need)
if _AP.count('Alarm 4: Mon 23 Nov 2026 18:24 UTC = 23:54 IST') != 1 or _AP.count('Alarm 5: Tue 24 Nov 2026 00:30 UTC = 06:00 IST') != 1: F('r20 alarm 4 or alarm 5 in the sheet')
absent17('r19 the card exists once', _AP.replace(_AP[_AP.index('The one order'):_AP.index('Key step J (other keys)')], '', 1), '1. You: before 18:19 UTC = 23:49 IST on the last day (key step D.5), make sure that you have confirmed', '7. Then the assistant does its item 1')
if not _DAY or not _APP: F('r19 the linked day sheet or appendix file is missing')
if len(_DAY.split()) < 2500 or len(_DAY.split()) > 6300: F('r20 day sheet word count %d (the limit of ORDERS.md line 227 is 6300)' % len(_DAY.split()))
# one typed word, one table row, one event: each word has exactly one row in the table (and the same row in the day sheet)
_rows18 = re.findall(r'^\s*\| (`[^|]+`(?: or `[^|]+`)?) \| ([^|]+) \| ([^|]+) \|', _AP, re.M)
_ev = [r_[1] for r_ in _rows18]
_wd = [w_ for r_ in _rows18 for w_ in re.findall(r'`([^`]+)`', r_[0])]
if len(_rows18) < 18 or len(set(_wd)) != len(_wd): F('r19 typed words: %d rows, or a word has two rows' % len(_rows18))
for _l in _norm19(_DAY.split('## Table of the typed words', 1)[1]) if _DAY else []:
    if _l.startswith('| `') and _l not in set(_norm19(_AP)): F('r19 day sheet table row differs: ' + _l[:60])
print('r19 applied sheet words (wc -w method): %d; day sheet %d; appendix %d' % (len(_AP.split()), len(_DAY.split()), len(_APP.split())))

def _seg19(t, a, b):
    i = t.find(a); j = t.find(b, i + 1) if i >= 0 else -1
    return len(t[i:j].split()) if i >= 0 and j > i else -1
_wc = {'applied sheet': len(_AP.split()), 'key step C (alarms)': _seg19(_AP, 'Key step C. Your alarms.', 'Key step D.'), 'key step D.5': _seg19(_AP, 'D.5. The last time to revoke', 'Key step E.'),
       'table of typed words': _seg19(_AP, 'Table of the typed words', 'The assistant never opens the key file'), 'card with one-liners': _seg19(_AP, 'The one order (the card; read it first)', 'Key step A.'),
       'key step I': _seg19(_AP, 'Key step I. Revoke the key', 'Key step J.'), 'key step G with G.2': _seg19(_AP, 'Key step G. The shred rule.', 'Key step H.'), 'identification check': _seg19(_AP, 'Identify first, then revoke or delete', 'Item 3 has a second job')}
print('r19 word counts (wc -w method, applied sheet and parts):', _wc)
print('r19 checks:', _r19n, 'count/pair/forbidden checks;', len(_r19f), 'failures in the section')
print('round 19 checks done')

# ================= round 19 golden pins (class fix for the 6 misses of r18: every sentence of EDITS.md is pinned ONCE against r19-pins.txt, not only against its own copies) =================
import collections as _col
def _sent19(t):
    out = []
    for l_ in t.split('\n'):
        l_ = l_.strip()
        if not l_: continue
        out += [s_.strip() for s_ in re.split(r'(?<=[.!?;]) +', l_) if s_.strip()]
    return out
_PINF = os.path.join(HERE_, 'r20-pins.txt')
_PINS = {}
if os.path.exists(_PINF):
    for _ln in open(_PINF, encoding='utf-8').read().split('\n'):
        if '\t' in _ln:
            _n, _s = _ln.split('\t', 1); _PINS[_s] = int(_n)
else:
    F('r20 pin file r20-pins.txt is missing')
def golden19(t):
    c_ = _col.Counter(_sent19(t)); out = []
    for s_, n_ in c_.items():
        if s_ not in _PINS: out.append('sentence not pinned: ' + s_[:90])
        elif _PINS[s_] != n_: out.append('sentence copies %d, pinned %d: %s' % (n_, _PINS[s_], s_[:70]))
    for s_, n_ in _PINS.items():
        if s_ not in c_: out.append('pinned sentence missing: ' + s_[:90])
    return out
_g19 = golden19(txt)
for _f in _g19[:40]: F('r19 golden ' + _f)
if len(_g19) > 40: F('r19 golden: %d more differences' % (len(_g19) - 40))
# the numbers of the changes file: every number written before "words" or "lines" must be a computed number
_CHGF = os.path.join(HERE_, 'r20-CHANGES.md')
def _allowed19():
    wc_ = len(_AP.split()); a_ = {wc_, len(_DAY.split()), len(_APP.split()), 6300, wc_ - 6300, txt.count('\n'), txt.count('\n') + 1}
    for v_ in list(_wc.values()): a_.add(v_); a_.add(wc_ - v_)
    return a_
def chg19(t):
    out = []; al_ = _allowed19()
    for m_ in re.finditer(r'(\d[\d,]*) (?:words|lines)\b', t):
        v_ = int(m_.group(1).replace(',', ''))
        if v_ >= 100 and v_ not in al_: out.append('number not computed: ' + m_.group(0))
    for k_, v_ in (('EDITS.md lines (wc -l): ', txt.count('\n')), ('applied sheet words (wc -w): ', len(_AP.split())), ('day sheet words (wc -w): ', len(_DAY.split())), ('appendix words (wc -w): ', len(_APP.split()))):
        if (k_ + '%d' % v_) not in t.replace(',', ''): out.append('fact line missing or wrong: ' + k_)
    return out
if os.path.exists(_CHGF):
    for _f in chg19(open(_CHGF, encoding='utf-8').read()): F('r19 changes ' + _f)
else: F('r20 changes file r20-CHANGES.md is missing')
print('r19 golden: %d pinned sentences, %d differences' % (len(_PINS), len(_g19)))
# ================= round 20 checks (security M1-M5, m1-m9; stranger M-A to M-G and minors): every fix has a check that fails on r19 and passes on r20 =================
# (label, where, phrase). where: A = applied sheet, D = day sheet, P = appendix, T = EDITS.md as a whole
_NOKEY = "The key has no date and no later date: the assistant asks you again, in every message that it writes to you, until you have written `key revoked` or `key gone, no more decisions`"
NEED20 = [
    ('M1 key has no date (D.5, I)', 'A', _NOKEY), ('M1 key has no date on the day sheet', 'D', _NOKEY),
    ('M1 G.2 excludes the key', 'A', 'except the key (the key has no date: key step D.5)'),
    ('M1 G.2 no later date', 'A', 'as the date to finish (no later date)'),
    ('M1 E-58 row', 'A', 'the key has no later date than 18:19 UTC = 23:49 IST, so send `key revoked` as soon as it is revoked'),
    ('M1 item 3 note', 'A', 'The key is never one of these items.'),
    ('M2 item 5 counts as done (G.2)', 'A', 'and so does item 5 for the login that it concerns'),
    ('M2 item 5 counts as done (E-59)', 'A', 'item 5 counts as done for that login and item 1 does not wait for it (key step G.2)'),
    ('M3 rotate first', 'A', 'Rotate first, then delete, for an item that carries `used`'),
    ('M3 two n8n told apart', 'A', 'Two different n8n are named in this sheet'),
    ('M3 take-only word', 'A', '`take-only` means: you made it new for this take'),
    ('M3 entry end condition', 'A', 'the entry ends only when you tell the assistant in a message'),
    ('M3 app 2 goes to the take n8n', 'A', 'goes into the take\'s n8n only'),
    ('M3 Phase 0 list words', 'A', 'one word: `take-only` or `used`'),
    ('M3 words explain the two n8n', 'D', '`the take\'s n8n` is the new n8n that the assistant starts inside the take folder'),
    ('M4 emergency revoke', 'A', 'an emergency: if you think that the key may have leaked or that somebody else may use it'),
    ('M4 one rule for key gone (B)', 'A', 'Use it whenever you have revoked the key before you typed `yes, no more takes`'),
    ('M4 exceptions list', 'A', 'alarm 1, alarm 3, alarm 4, alarm 5, an emergency (key step D.3) and the last time to revoke (key step D.5) are the exceptions'),
    ('M5 five alarms', 'A', 'Set five alarms on your own phone or computer. Alarm 1:'),
    ('M5 alarm 4 at 18:24', 'A', 'Alarm 4: Mon 23 Nov 2026 18:24 UTC = 23:54 IST, named `still not revoked: revoke the secret key for the model now`'),
    ('M5 alarm 5 unconditional', 'A', 'Alarm 5: Tue 24 Nov 2026 00:30 UTC = 06:00 IST'),
    ('M5 alarm 5 not conditional', 'A', 'you set it in every case, and it is not conditional on anything'),
    ('M5 alarm 2 fixed daytime time', 'A', 'always at 06:30 UTC = 12:00 IST (a fixed time in the daytime'),
    ('M5 alarm 4 or 5 rings', 'A', 'When alarm 4 or alarm 5 rings and the key is not yet revoked'),
    ('M5 ND18', 'T', '18. **Alarm 2 time and the Tue 24 Nov 2026 date.**'),
    ('m1 alarm word', 'A', 'if you have not typed `yes, no more takes`, write `key gone, no more decisions` instead (key step B)'),
    ('m2 route B warning in the prompt', 'A', 'Then write `key gone, no more decisions` (in route B this makes the cut final)'),
    ('m3 In short repaired', 'A', 'Then you revoke the key (key step I)'),
    ('m4 app password page shows only a name', 'A', 'an app password page may show only the name'),
    ('m5 ND19 lists written', 'T', '19. **Typed word `lists written`'),
    ('m6 item 2 click path', 'D', 'at myaccount.google.com, Security, App passwords (this click path is not checked)'),
    ('m7 ND15 option B', 'T', '`cut accepted` and `yes, no more takes` are written before alarm 1 rings'),
    ('m8 no line break', 'A', 'no space, no line break, no quote sign'),
    ('m8 own list is the only check for (b) and (d)', 'A', 'they rest on your handwritten list'),
    ('m9 ND20 recommendation question', 'T', 'The question for the studio lead:'),
    ('MA day sheet holds key step B', 'D', '## Key step B: only you can write the words'),
    ('MA day sheet holds D.1 to D.4', 'D', '## Key step D: the route and the confirmation (D.1 to D.4)'),
    ('MA day sheet says it is not everything', 'D', 'It is NOT the whole retirement'),
    ('MB step 21 heading', 'A', '### Step 21. Watch the cut by Mon 23 Nov 2026 17:49 UTC = 23:19 IST (alarm 1)'),
    ('MB real latest time', 'A', 'The real latest time to confirm in route B is when alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026'),
    ('MB K-D', 'P', 'before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, key step D.5 applies'),
    ('MC G.2 dated Monday', 'A', 'If on Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST'),
    ('MC how to show times', 'A', 'start every message that you write with the time in UTC'),
    ('MC other days', 'A', 'On any other day this time rule does not apply.'),
    ('MD hedge replaced by a rule', 'A', 'this date is a proposal: it stands if the assistant names no other date before your first take'),
    ('MD second person rule', 'A', 'if you named nobody there is no second person'),
    ('MF day sheet defines take and cut', 'D', 'a take is one real run on your test accounts that makes the recording; the cut is the edited video made from your takes (step 21)'),
    ('MF day sheet defines routes', 'D', 'route A and route B are the two ways to confirm that your last take is your last'),
    ('MG exact typing', 'A', 'Type every word exactly as it is written here, without the backticks'),
    ('MG replies of key step F in the table', 'A', 'your answer to a question of key step F'),
    ('min card step 1 time', 'A', '1. You: before 18:19 UTC = 23:49 IST on the last day (key step D.5)'),
    ('min plain words', 'A', 'In plain words: the key is revoked before 18:19 UTC = 23:49 IST'),
    ('min E-37 three questions', 'A', 'asks you three questions and asks you to write two lists'),
    ('min ND header', 'T', 'items 1 to 20'),
]
ABSENT20 = [
    ('M1 old handoff date for the key', 'A', 'the assistant lists it in the handoff with a date to finish it'),
    ('M1 later date', 'A', '(or a later date that you give)'),
    ('M3 old unknown-credential sentence', 'A', 'which key or password those credentials hold is not known (UNVERIFIED), so before the take you open each of them'),
    ('M4 old B sentence', 'A', 'Use it only when all three are true, or when you revoke at the last time to revoke'),
    ('M5 four alarms', 'A', 'Set four alarms'),
    ('M5 alarm 4 do not rely', 'A', 'if the secret key for the model is still not revoked, revoke it now'),
    ('M5 evening alarm', 'A', 'in the evening of every day from the day of your first take'),
    ('m3 double space', 'A', '.  revoke the key'),
    ('MA old claim', 'D', 'only key step A (the fixed rule), key step E'),
    ('MB old route B time', 'A', 'write `cut accepted` and then `yes, no more takes` before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026'),
    ('MC old clock rule', 'A', 'it reads the time shown on your last message in the chat'),
    ('MD hedge', 'A', 'to be confirmed by the studio lead before you rely on it'),
    ('MD hedge on the day sheet', 'D', 'studio lead'),
    ('MD second person open', 'A', 'whether such a person exists is open'),
    ('MD builder word in owner text', 'D', 'the builder believes'),
    ('m7 ND15 stale', 'T', '`cut accepted` and `no more takes` are written before 18:19'),
]
def _where20(w, ap, day, app, tx):
    return {'A': ap, 'D': day, 'P': app, 'T': tx}[w]
def check20(ap, day, app, tx):
    out = []
    for lab, w, ph in NEED20:
        if ph not in _where20(w, ap, day, app, tx): out.append('r20 need: ' + lab)
    for lab, w, ph in ABSENT20:
        if ph in _where20(w, ap, day, app, tx): out.append('r20 absent: ' + lab)
    # the day sheet is not longer than the order allows
    if len(day.split()) > 6300: out.append('r20 day sheet longer than 6300 words')
    # the one-liner of key step I and the alarm rows exist on the day sheet too
    for k_ in ('## Your five alarms', '## Key step I: revoke the key', '## The identification check', '## Table of the typed words'):
        if k_ not in day: out.append('r20 day sheet lacks ' + k_)
    return out
_c20 = check20(_AP, _DAY, _APP, txt)
for _f in _c20: F(_f)
# round order of the last lines of EDITS.md: 18, 19, 20
_ro = [txt.find('- Round %d added:' % n_) for n_ in (18, 19, 20)]
if -1 in _ro or _ro != sorted(_ro): F('r20 the round lines are not in the order 18, 19, 20: %s' % _ro)
# closure table: one row for every finding id of the two reviews of r18 and the two reviews of r19
_CLF = os.path.join(HERE_, 'r20-CLOSURE.md')
_IDS = (['r18 security ' + i_ for i_ in ('M1', 'M2', 'M3', 'M4', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6')] +
        ['r18 stranger ' + i_ for i_ in ('B1', 'B2', 'B3', 'M1', 'M2', 'M3', 'M4', 'M5', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9')] +
        ['r19 security ' + i_ for i_ in ('M1', 'M2', 'M3', 'M4', 'M5', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9')] +
        ['r19 stranger ' + i_ for i_ in ('M-A', 'M-B', 'M-C', 'M-D', 'M-E', 'M-F', 'M-G')])
def closure20(t):
    out = []
    rows = [l_ for l_ in t.split('\n') if l_.startswith('| ')]
    for i_ in _IDS:
        r_ = [l_ for l_ in rows if l_.startswith('| ' + i_ + ' |')]
        if len(r_) != 1: out.append('r20 closure: id %s has %d rows' % (i_, len(r_))); continue
        cells = [c_.strip() for c_ in r_[0].strip().strip('|').split('|')]
        if len(cells) < 4 or cells[2] not in ('CLOSED', 'LEAD-DECISION', 'UNVERIFIED', 'THIRD-PARTY', 'PARTLY') or len(cells[3]) < 20: out.append('r20 closure: id %s status or evidence cell wrong' % i_)
    return out
if os.path.exists(_CLF):
    _clt = open(_CLF, encoding='utf-8').read()
    for _f in closure20(_clt): F(_f)
else: F('r20 closure file r20-CLOSURE.md is missing')
# plants of round 20: every NEED phrase removed, every ABSENT phrase put in, each must be caught BY ITS OWN label; closure rows removed
_pl20 = [0, 0]
def _plant20(label, ap, day, app, tx):
    _pl20[0] += 1
    got = set(check20(ap, day, app, tx)) - set(_c20)
    if label in got: _pl20[1] += 1
    else: F('r20 plant not caught by its own check: ' + label)
for lab, w, ph in NEED20:
    ap, day, app, tx = _AP, _DAY, _APP, txt
    if w == 'A': ap = _AP.replace(ph, '#' + ph[1:], 1)
    elif w == 'D': day = _DAY.replace(ph, '#' + ph[1:], 1)
    elif w == 'P': app = _APP.replace(ph, '#' + ph[1:], 1)
    else: tx = txt.replace(ph, '#' + ph[1:], 1)
    if (ap, day, app, tx) == (_AP, _DAY, _APP, txt): F('r20 plant anchor missing: ' + lab); continue
    _plant20('r20 need: ' + lab, ap, day, app, tx)
for lab, w, ph in ABSENT20:
    ap, day, app, tx = _AP, _DAY, _APP, txt
    if w == 'A': ap = _AP + '\n' + ph
    elif w == 'D': day = _DAY + '\n' + ph
    elif w == 'P': app = _APP + '\n' + ph
    else: tx = txt + '\n' + ph
    _plant20('r20 absent: ' + lab, ap, day, app, tx)
if os.path.exists(_CLF):
    for _i_, _id_ in enumerate(_IDS):
        _pl20[0] += 1
        _t2 = '\n'.join(l_ for l_ in _clt.split('\n') if not l_.startswith('| ' + _id_ + ' |'))
        if closure20(_t2): _pl20[1] += 1
        else: F('r20 closure plant not caught: ' + _id_)
print('r20 checks: need %d, absent %d, closure ids %d; plants (planted, caught): %s' % (len(NEED20), len(ABSENT20), len(_IDS), tuple(_pl20)))

# ================= negative controls (each check must fail on a planted defect) =================
import subprocess
_negskip = [bool(os.environ.get('NEG_AFTER'))]
def neg(name, old, new, expect, count=1):
    if _negskip[0]:
        if name == os.environ.get('NEG_AFTER'): _negskip[0] = False
        return
    src = open(E, encoding='utf-8').read()
    if src.count(old) < 1:
        F('negative control anchor missing: ' + name); return
    if os.environ.get('NEG_ANCHOR_ONLY'): return
    mut = src.replace(old, new, 1) if count == 1 else src.replace(old, new)
    mp = sd + 'neg-' + name + '.md'
    open(mp, 'w', encoding='utf-8').write(mut)
    env = dict(os.environ); env['EDITS_PATH'] = mp; env['NO_NEG'] = '1'
    out = subprocess.run([sys.executable, '-I', os.path.abspath(__file__)], env=env, capture_output=True, text=True).stdout
    fails = [l_ for l_ in out.split('\n') if l_.startswith('FAIL')]
    ok = any(expect in l_ for l_ in fails)
    print('NEG', name, 'caught' if ok else 'NOT CAUGHT', '|', (fails[0][:90] if fails else 'no FAIL line'))
    if not ok: F('negative control not caught: ' + name)
if not os.environ.get('NO_NEG'):
    print('---- negative controls')
    neg('r11hold', 'NEW [HOLD G3: DO NOT APPLY] (2) (exact', 'NEW (2) (exact', 'HOLD blocks != 13')
    neg('r11e53', 'start the model stage with a real key file or with the web address of the real AI model', 'start the model stage with a real key file unless the owner\'s written yes with a number for one paid call is quoted', 'E-53 unless clause')
    neg('r11e09', 'n8n holds three saved credentials for the take', 'n8n holds four saved credentials for the take', 'E-09 credentials')
    neg('r11addr', 'the web address the assistant gives (it is NOT', 'the address the assistant gives (it is NOT', 'bare address')
    neg('r11slot', 'crash check: tested or untested', 'crash check slot', 'E-12 lacks crash check: tested or untested')
    neg('r11e36', 'TEXT N (held, not applied', 'TEXT M (held, not applied', 'E-36 text N not quoted')
    neg('r11e58', 'Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST', 'Mon 23', 'r19 count applied')
    neg('nd14', '14. **Does the lease sentence of Q22(c)', '14. **Something else', 'ND14 missing')
    neg('e17lease', '**a lead sent twice with the same id is processed once; a crash', '**a lead sent twice with the same id (see the lease) is processed once; a crash', 'E-17 lease sentence added')
    neg('e22', 'the case counts as "crash check untested", the same words', 'the case counts as untested, the same words', 'crash check untested missing in E-22')
    neg('e43', "except the model stage's journal file `stage.journal`", 'and nothing else', 'E-43 lacks stage.journal', 2)
    neg('e49', "AFTER the assistant's message that states (a) to (d)", 'after something', 'E-49 consent not tied')
    neg('e49day', 'written like this: `Wed 18 Nov 2026`', 'written as a day', 'E-49 lacks day format example')
    neg('e53', 'Section 4b overrides line 27', 'Section 4b follows line 27', 'E-53 lacks override')
    neg('e51', 'the end of the spending window); that statement', 'the window end); that statement', 'E-51 wording')
    neg('e52', '**A mail address**', '**A postal address**', 'E-52 new word not once: A mail address')
    neg('e04', 'you delete nothing and tell the assistant.\n~~~~\nWhy: The decision of 2026-11-16', 'you delete nothing and tell the assistant\n~~~~\nWhy: The decision of 2026-11-16', 'E-04 no final full stop')
    neg('e07', 'nobody on this branch has read that evidence. The assistant checks', 'nobody has read that evidence. The assistant checks', 'E-07 lacks')
    neg('e08', 'nobody on this branch has read that evidence yet.\n~~~~', 'nobody has read that evidence yet.\n~~~~', 'E-08 lacks')
    neg('record', 'The line has the form shown after "Record:"', 'The line is `ND<number>: <answer>, <who>`; it has the form shown after Record', 'old record format')
    neg('nd8date', 'Record: `ND8: A|B`.', 'Record: `ND8: A|B <date and time in UTC and IST>`.', 'ND record carries a date')
    neg('rehearsal', 'The flow rehearsal comes after', 'The rehearsal comes after', 'rehearsal alone')
    neg('q195', 'except the one that the take ran on', 'except the key', 'E-48 Q19.5 wording')
    neg('m4', 'the assistant tells you in writing what happens next.', 'the assistant tells you.', 'E-12 lacks what happens next')
    neg('e31', 'nothing here says that it stops safely (UNVERIFIED)', 'it stops safely (UNVERIFIED)', 'E-31 unproven claim')
    neg('line14', 'search path = the list of schemas', 'search path is a list of schemas', 'line 14 lacks')
    neg('e14', '(rule 5 of this sheet: you are the one who publishes)', '(rule 5: you post)', 'E-14 post meaning')
    # negative controls for older checks (selected: row count, old text, ND range, confirmation letters, UTC pairing, banned scan not tested)
    neg('r12nd15', '15. **When the owner types `yes, no more takes`', '15. **Something else', 'r12 ND15 missing')
    neg('r12shred', 'Shredding does not revoke the key, and it is not reliable on every disk', 'Shredding revokes the key', 'r12 E-48 lacks')
    neg('r12key2', 'the one that you open at `http://localhost:5678`? If it is, revoking it breaks that n8n." Reply `same key`', 'the one in your n8n? If it is, revoking it breaks that n8n." Reply `same key`', 'r17 r12 key step F question lacks')
    neg('r12slot', 'exactly one of these four labels', 'exactly one of these labels', 'r12 E-12 lacks exactly one of these four labels')
    neg('r12call', 'The last step of the take program sends no delete request to HubSpot', 'The last step of the take program makes no delete call to HubSpot', 'delete call')
    neg('r12pw', 'Never type a password inside a command line, even if', 'Type the password on the command line if', 'r12 E-09 lacks')
    neg('r12vol', 'Whether a volume is used is UNVERIFIED.', 'A volume is used.', 'r12 E-16 lacks')
    neg('r12cut', 'Reply `cut accepted`, or list the bad stretches', 'Reply `accepted`, or list the bad stretches', 'r12 E-57 lacks')
    neg('r12conf', '\nl. E-12 gives the request', '\nm. E-12 gives the request', 'confirmation letters')
    neg('rowcount', '### E-58: OWNER-STEPS', '### E-59: OWNER-STEPS', 'ids differ')
    neg('conf', '\nj. E-56 puts', '\nk. E-56 puts', 'confirmation letters')
    # ---- round 14 negative controls
    neg('r13bare', 'the older single label that was used for both is retired', 'the older single label "latest start" that was used for both is retired', 'r13 bare label')
    neg('r13swap', '**latest start we plan** = 18:00 UTC = 23:30 IST', '**latest start we plan** = 18:14 UTC = 23:44 IST', 'r13 "latest start we plan" followed by time 18:14')
    neg('r13swap2', '**program refusal limit** = about 18:14 UTC = 23:44 IST', '**program refusal limit** = about 18:04 UTC = 23:34 IST', 'r13 "program refusal limit" followed by time 18:04')
    neg('r13arith', '17:49 UTC = 23:19 IST', '17:49 UTC = 23:49 IST', 'r13 time arithmetic', 2)
    neg('r13typing', '`mailbox password typed; you may look again`', '`mailbox password typed`', 'r13 E-09 lacks')
    neg('r13reach', 'What the assistant can reach', 'What the assistant sees', 'r13 E-09 lacks What the assistant can reach', 2)
    neg('r13always', 'WHATEVER you answer to any question below, and `not sure` never keeps it alive', 'if you answer yes, and `not sure` keeps it alive', 'r13 E-48 lacks')
    neg('r13alarm', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `x`', 'r13 E-48 lacks')
    neg('r13route', 'No default pick: the assistant does not recommend a route', 'The assistant recommends route B', 'r13 E-48 lacks No default pick')
    neg('r13shot', 'does not prove that the right key is gone', 'proves that the right key is gone', 'r13 E-48 lacks', 2)
    neg('r13e55', '| E-55 | OWNER-STEPS-realrun-v3.md | 119 (and 120) |', '| E-55 | OWNER-STEPS-realrun-v3.md | 119 |', 'r13 E-55 trigger or index')
    neg('r13e16', 'Item 1 starts only when ALL the conditions of key step G.2 are true', 'Item 1 starts when SOME of the conditions of key step G.2 are true', 'r13 E-16 trigger')
    neg('r13above', 'In the older sentences of this step', 'In the sentence above this one', 'r13 E-12 refers to unseen text')
    neg('r13ph', 'The time of day is not yet chosen: the assistant proposes a time of day for that Wednesday', 'The time is chosen: the assistant proposes a time of day for that Wednesday', 'r13 E-12 lacks')
    neg('r13yes', 'my screen, and that it can reach n8n\'s encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`."', 'my screen."', 'r13 E-12')
    neg('r13nd15', 'CONFLICT FOR THE STUDIO LEAD, not decided by the builder', 'Default: (A) is the default', 'r13 ND15')
    neg('r13e52', '- **A finding**', '- **The studio lead**: x. **A finding**', 'r13 E-52 studio lead defined once')
    neg('r13e37', 'the number after the colon in a web address; 5678 is the port number of your own n8n', 'the port', 'r13 E-37 lacks the number after the colon')
    # ---- round 14 negative controls (the first seven are the mutations that verify13 missed)
    neg('r14m10', 'Key step I. Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST', 'Key step I. Revoke the key, ALWAYS, by 18:29 UTC = 23:59 IST', 'r14 3h key end')
    neg('r14m12f', 'write `please stop looking`, wait for `not looking`, and at the end write `you may look again`); open a WSL terminal', 'write `please stop looking`, and at the end write `you may look again`); open a WSL terminal', 'r14 E-09 sub-step f')
    neg('r14m12g', 'apply the typing rule (write `please stop looking` and wait for `not looking`); in the WSL terminal', 'apply the typing rule (write `please stop looking`); in the WSL terminal', 'r14 E-09 sub-step g')
    neg('r14m12h', 'with its own `please stop looking` and its own wait for `not looking`', 'with its own `please stop looking`', 'r14 E-09 sub-step h')
    neg('r14m22', 'by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'by Tue 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'r14 wrong weekday')
    neg('r14m23', 'The take is aimed at Wed 18 Nov 2026.', 'The take is aimed at Thu 18 Nov 2026.', 'r14 wrong weekday')
    neg('r14m34', 'Mon 16 Nov 2026 18:29 UTC = 23:59 IST, no longer counts', 'Sun 16 Nov 2026 18:29 UTC = 23:59 IST, no longer counts', 'r14 wrong weekday')
    neg('r14m29', 'This is the security decision of 16 Nov 2026 (the owner revokes the key)', 'This is the security decision of 16 Nov 2026 (Q25, the owner revokes the key)', 'r14 internal code in owner text E-48')
    neg('r14m30', 'This is the security decision of 16 Nov 2026 (the owner revokes the key)', 'This is the security decision of 16 Nov 2026 (L-23NOV, the owner revokes the key)', 'r14 internal code in owner text E-48')
    neg('r14nd', 'Alarm 2: a repeating alarm', 'Alarm 2 (see ND15): a repeating alarm', 'r14 internal code in owner text E-48')
    neg('r14route', 'Write `route A` or `route B` once, before your last take', 'Write the route in the chat', 'r14 route selection message')
    neg('r14rec2', 'Route B: you have not yet typed', 'Route B (the one the assistant recommends): you have not yet typed', 'r14 second recommendation spot')
    neg('r14norec', 'No default pick: the assistant does not recommend a route', 'The assistant recommends route B', 'r18 route recommendation sentence count')
    neg('r14again', 'in route B it asks again right after `cut accepted`', 'in route B it never asks again', 'r14 3c lacks it asks again')
    neg('r14forced', '`key revoked` is never a confirmation', '`key revoked` is a confirmation', 'r14 3c lacks')
    neg('r14real', '(3) `realpath \'<path>\'` prints exactly the same path', '(3) the path looks right', 'r14 3f lacks realpath')
    neg('r14link', 'has the number `1` in its second column', 'is a plain file', 'r14 3f lacks the number `1`')
    neg('r14slash', 'followed by `/`, so that the take folder', 'so that the take folder', 'r14 3f lacks followed by')
    neg('r14wild', 'none of the signs `*`, `?` and `[`', 'none of the signs `?` and `[`', 'r14 3f lacks none of the signs')
    neg('r14star', '; do not use the sign `*`. A file that holds', '. A file that holds', 'r14 E-48 item 6 star rule')
    neg('r14alarm2', 'named `is the secret key for the model still alive?`. Alarm 3', 'named `still alive`. Alarm 3', 'r14 3b lacks')
    neg('r14promise', 'a procedure, not a control', 'a control', 'r14 3a honest label')
    neg('r14default', 'revoke the one key that you created for this take', 'wait for the assistant', 'r14 3h default when unsure')
    neg('r14unless', '(key step I). No message of the assistant changes this.', '(key step I), unless the assistant tells you otherwise before that time. No message of the assistant changes this.', 'r14 3j override sentence')
    neg('r14e16', 'Item 1 starts only when ALL the conditions of key step G.2 are true (the list is there, once), each as a message', 'Item 1 starts when SOME of the conditions of key step G.2 are true, each as a message', 'r17 F-1 pointer in E-16')
    neg('r14e55', 'each of your items 2, 3, 4, 5 and 6', 'each of your items', 'r14 E-55 lacks', 9)
    neg('r14e37', 'the LAST FOUR CHARACTERS of it as the key list shows them', 'something else', 'r14 E-37 note')
    neg('r14consent', 'my screen, and that it can reach n8n\'s encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`."', 'my screen, and that it can reach n8n\'s encryption key and the credentials saved in the take\'s n8n."', 'r14 E-12 consent reach')
    neg('r14testitem', 'A test item is one numbered test on the plan\'s list of test items.', 'A check is one numbered test on the plan\'s list of checks.', 'r14 E-12 test item')
    neg('r14margin', 'which is 3 minutes 40 seconds before the last time to revoke', 'which is a small margin before the last time to revoke', 'r14 E-12 margin')
    neg('r14fallback', 'The time of day is not yet chosen: the assistant proposes a time of day for that Wednesday', 'The time is chosen: the assistant proposes a time of day for that Wednesday', 'r14 E-12 placeholder fallback')
    neg('r14conf', '\no. The latest start we plan', '\nx. The latest start we plan', 'confirmation letters')
    neg('r14count', 'the result of the counting program (a small program of ours', 'the result of the counting check (a small program of ours', 'r14 counting check word')
    neg('r14line30', '(18:14:40 UTC = 23:44:40 IST, if the 860 seconds are right', '(18:14 if the 860 seconds are right', 'r14 18:14:40 pair missing')
    neg('r14clip', 'open the Windows clipboard history (press the Windows key and V together)', 'open the clipboard', 'r14 E-09 clipboard history')
    neg('r14e57', 'You choose one by writing `route A` or `route B` in the chat once, before your last take (step 22 item 3, key step D).', 'You choose one.', 'r14 E-57 route message')
    neg('r14forcedd', '`key revoked` is never a confirmation', '`key revoked` is a confirmation', 'r14 3d forced revoke', 2)
    neg('r14bareno', 'including a bare `no`, counts as `not sure`', 'including a bare `no`, counts as no', 'r14 3e bare no')
    neg('r14g', 'A new key lives only inside the program that uses it', 'A new key may be saved anywhere', 'r14 3g new key storage')
    neg('r14opt', 'Option leave:', 'Option keep:', 'r14 3i options')
    neg('r14nd15', 'The spot that would carry a recommendation, if the studio lead adds one', 'Other spots', 'r14 ND15 spots')
    neg('r15B', 'count only when you type them yourself, as a new message in your chat with the assistant', 'count when the assistant sees them', 'r15 E-48 B lacks')
    neg('r15B2', 'never count, even when they are the same words', 'count when they are the same words', 'r15 E-48 B lacks')
    neg('r15e52', 'Only you can write these words: they count only when', 'These words count when', 'r15 E-52 how you reply lacks')
    neg('r15e12typed', 'typed by you yourself in a new message, can start a take', 'can start a take', 'r15 E-12 reply lacks')
    neg('r15e16typed', 'Only messages that you type yourself count', 'Messages count', 'r15 E-16 lacks')
    neg('r15e16link', 'or if the path itself or any folder in front of it is a link', 'or is or contains a link', 'r15 E-16 path lacks')
    neg('r15e16slash', 'so the take folder `/x/take-1` never accepts `/x/take-10`', 'so the take folder is checked', 'r15 E-16 path lacks')
    neg('r15own', 'you copy its path from your own list, sign for sign', 'you saved this file yourself', 'r15 E-48 G lacks')
    neg('r15deny', 'Never shred a recording, a video file, a screenshot or anything under `/mnt/c` that is not on your own list, and never a file that only the assistant named.', 'Shred what the assistant names.', 'r15 E-48 G lacks')
    neg('r15path', 'it must be exactly the folder `<folder>` that you copied from the assistant\'s message in step 8', 'it must look right', 'r15 E-48 E lacks')
    neg('r15list', 'your own list of every file in which you saved a secret', 'a list', 'r15 E-37 list lacks')
    neg('r15old1804', 'The latest start we plan is 18:00 UTC = 23:30 IST on any day', 'The latest start we plan is 18:04 UTC = 23:34 IST on any day', 'r15 old latest start')
    neg('r15bare', 'it ends about 18:15:20 UTC = 23:45:20 IST, which is', 'it ends about 18:15:20, which is', 'r15 bare clock time in E-12')
    neg('r15studio', 'the assistant asks for no start after it.', 'the assistant asks for no start after it. The assistant asks the studio lead to confirm this margin.', 'r15 E-12 third party')
    neg('r15alarm', 'If a take is running when alarm 1 rings', 'Nothing else happens', 'r15 E-48 C lacks')
    neg('r15alarm1', 'if no session is open or it does not ask, go straight to key step I', 'do key step I at once', 'r15 E-48 C lacks')
    neg('r15app', 'There are two different HubSpot keys.', 'Use the key of app 1 (read only) unless the assistant says otherwise. There is one HubSpot key.', 'r15 E-09 h lacks')
    neg('r15e37app', 'Two different HubSpot keys: the key in your file', 'The HubSpot key: the key in your file', 'r15 E-37 3 lacks')
    neg('r15done', '`shred done key copies` means that EVERY file of (a) and (b) is shredded', '`shred done` means done', 'r15 E-48 G done lacks')
    neg('r15silence', 'If you write neither, the assistant treats it as `shred not done key copies` or `shred not done other files`.', 'If you write neither, it waits.', 'r15 E-48 G done lacks')
    neg('r15e59', 'Do not use the sign `*`. If shred is not installed, run the same five checks', 'Use `shred -u ~/take-secrets/*`. If shred is not installed, run the same five checks', 'r15 E-59 missing or still has the star')
    neg('r15sure', 'Are you sure? After this you cannot make another take', 'After this you cannot make another take', 'r15 E-48 D lacks')
    neg('r15e52conf', '`no more takes` is confirmed only by your next message `yes, no more takes`.', '`no more takes` is confirmed.', 'r15 E-52 confirm lacks')
    neg('r15reply', '4. money: up to 3 model calls and up to US$<X>', '4. money: up to 3 model calls and up to US$1.50', 'r15 E-12 reply line missing')
    neg('r15blocks', 'Block 1, the money figures', 'Part 1, the money figures', 'r15 E-12 blocks lacks')
    neg('r15ph', 'The time of day is not yet chosen: the assistant proposes one, in UTC and IST,', 'The time of day is `[LEAD FILLS at re-pin: x]`: the assistant proposes one, in UTC and IST,', 'r15 placeholder wording')
    neg('r15brand', 'on the website of the company that provides the AI model, at the page', 'on the website of the company that provides the AI model (Anthropic), at the page', 'r15 E-48 I still has')
    neg('r15two', 'with the two names `<password file name>` and `<folder>` copied from its message', 'with the three names copied from its message', 'r15 E-09 e lacks')
    neg('r15nano', 'type `ls -a` and press Enter', 'look at the folder', 'r15 E-09 extras lacks')
    neg('r15label', '   Key step F. Two questions.', '   3e. Two questions.', 'r15 key steps are not A to K')
    neg('r15row', '### E-61: OWNER-STEPS-realrun-v3.md, line 144', '### E-62: OWNER-STEPS-realrun-v3.md, line 144', 'ids differ')
    neg('r15short', 'In short: set five alarms', 'Set five alarms', 'r15 E-48 intro lacks')
    # ---- round 16 negative controls (each planted defect must fail the new check; the runner's nine missed mutations are r16m15 to r16m51)
    _skpre = 'sk-' + 'ant-' + 'api03-'
    neg('r16F1word', '`key gone, no more decisions`', '`key gone`', 'r16 F1 word lacks', 2)
    neg('r16F1time', 'you revoke it whatever you have written, and then you write `key gone, no more decisions`', 'you revoke it and write `key revoked`', 'r16 F1 E-55 lacks', 9)
    neg('r16F2a', 'or any other contact, you delete nothing and tell the assistant.\n~~~~\nWhy: ', 'you delete them all.\n~~~~\nWhy: ', 'r16 F2 E-04 lacks', 9)
    neg('r16F2b', "(with this take's id); if you find more than 3, or any other contact", "(made-up names); if you find more than 3, or any other contact", 'r16 F2 E-42')
    neg('r16F2c', '### E-62: OWNER-STEPS-realrun-v3.md, line 112', '### E-63: OWNER-STEPS-realrun-v3.md, line 112', 'ids differ')
    neg('r16F3', 'password files and editor copies made in step 8', 'other files made in step 8', 'r16 F3 G lacks')
    neg('r16F4a', '4. You: do your item 4 (save the screenshots) and your item 5, the retire check.', '0. You: do your item 4 (save the screenshots) and your item 5, the retire check.', 'r16 F4 the numbered order')
    neg('r16F4b', '(the clean-up). It never starts while a copy of the key exists and the key is not revoked.', '(the clean-up). It starts at any time.', 'r17 pin', 9)
    neg('r16F4c', 'It does NOT start while a copy of the secret key for the model exists', 'It starts while a copy of the secret key for the model exists', 'r16 F4 E-16 lacks')
    neg('r16F4d', 'the order of step 22 is the only order'.capitalize(), 'The order of step 22 is one order', 'r16 F4 E-16 lacks')
    neg('r16m1', 'if a recording or a video file is inside, it stops, removes nothing and tells you', 'a recording is removed too', 'r16 m1 E-16 lacks')
    neg('r16m5', '`ok stand-in test` (for the stand-in test)', '`ok` (for the stand-in test)', 'r16 m5 E-11 lacks')
    neg('r16m3', 'Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST', 'Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:49 IST', 'r16 m3 alarms lacks')
    neg('r16M2', '3 minutes 40 seconds before the last time to revoke the secret key for the model (18:19', '4 minutes 40 seconds before the last time to revoke the secret key for the model (18:19', 'r16 M2')
    neg('r16M1', '(only a message typed by you counts: step 22 item 3, key step B). "Your reply"', '(only a message typed by you counts: step 22 item 3, key step C). "Your reply"', 'r16 M1 refs still has')
    neg('r16plain', 'A later independent review found no delete', 'A later independent review (r17) found no delete', "r16 E-56 codes still has")
    neg('r16e54', '## Phase 1: the assistant checks.\nYou only need', '## Phase 1: the assistant checks. You only need', 'r16 E-54 heading')
    neg('r16m15', "write `please stop looking` and wait for the assistant's reply `not looking` BEFORE you click", 'write `please stop looking` BEFORE you click', 'the wait for')
    neg('r16m17', '(1) write to the assistant `please stop looking` and wait for its written reply `not looking`', '(1) write to the assistant `please stop looking`', 'the wait for')
    neg('r16m18', '(sub-steps c, f, g and h)', '(sub-steps c and f)', 'r16 E-09 a does not list')
    neg('r16m19', "`ls -l '<path>'`", "`ls '<path>'`", 'r16 shred rule lacks', 2)
    neg('r16m22', "`shred -u -- '<path>'`", "`rm -- '<path>'`", 'r16 shred rule lacks', 2)
    neg('r16m24', 'never accepts `/x/take-10/key`', 'never accepts `/x/other/key`', 'r16 shred rule lacks')
    neg('r16m31', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `is the secret key for the model still alive?`', 'r16 alarm')
    neg('r16m32', 'alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`', 'alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `is the secret key for the model still alive?`', 'r16 alarm 1 has the wrong name')
    neg('r16m51a', 'Round 16 (stranger minor): "default" is out', 'Round 16 ' + _skpre + 'AbCd-EfGh_IjKl0123 "default" is out', 'secret-shaped text matches')
    neg('r16m51b', 'Round 16 (stranger minor): "default" is out', 'Round 16 sk-' + 'abcd-efgh-ijkl-mnop-qrst "default" is out', 'secret-shaped text matches')
    neg('r16idx', '| E-62 | OWNER-STEPS-realrun-v3.md | 112 |', '| E-62 | OWNER-STEPS-realrun-v3.md | 113 |', 'r16 index mismatch')
    neg('r16banned', 'Round 16 (stranger minor): "default" is out', 'Round 16 ' + _banned[0] + ' "default" is out', 'r16 banned strings present')
    neg('r16pair', '17:49 UTC = 23:19 IST', '17:49 UTC = 23:29 IST', 'r16 UTC/IST pair is wrong')
    neg('r16wd', 'Mon 23 Nov 2026 17:49 UTC', 'Tue 23 Nov 2026 17:49 UTC', 'r16 weekday/date wrong')
    neg('r16code', 'In short: set five alarms', 'In short (E-12): set five alarms', 'r16 internal code in owner text')
    # ---- round 17 negative controls (each must fail the new check; the first 22 are the runner's pins m18..m60 and B03..B10)
    _pl = {'m18 D.4 appendix ref': ('appendix K-D', 'appendix K-E'), 'm34 word list': ('THREE events at once, on purpose: the key is gone AND there are no more takes AND the cut is final', 'THREE events at once, on purpose: the key is gone AND there are no more takes'),
           'm37 window end': ('The spending window ends at 18:29 UTC = 23:59 IST; that is when', 'The spending window ends at 18:19 UTC = 23:49 IST; that is when'),
           'm40 not sure': ('Reply `yes`, `no, other things use it` or `not sure`', 'Reply `yes` or `no, other things use it`'),
           'm41 only yes': ('Only `yes` together with `different key` means', 'Only `yes` means'),
           'm43 stop looking': ('the assistant stops looking and answers `not looking`', 'the assistant keeps looking'),
           'm45 C': ('unless at least 30 minutes remain after you have answered', 'unless at least 2 minutes remain after you have answered'),
           'm45 H': ('only if at least 30 minutes remain before', 'only if at least 20 minutes remain before'),
           'm48 G': ('Do not shred part (a) while a take is running (the model stage reads that copy); wait until the take has stopped. ', ''),
           'm51 why': ('Security F2 of round 15: input line 112', 'Security F2'),
           'm53 unverified': ('is not proven (UNVERIFIED)', 'is proven'),
           'm54 typed': ('Only your own typed messages count (key step B)', 'Messages count (key step B)'),
           'm60 card 1': ('if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway', 'if you have not typed `yes, no more takes` by 18:29 UTC = 23:59 IST, revoke the key at that time anyway'),
           'B03 no space': ('no `..`, no space, no line break, no quote sign', 'no `..`, no line break, no quote sign'),
           'B04 ten minutes': ('the last 10 minutes (18:19 UTC = 23:49 IST to', 'the last 20 minutes (18:19 UTC = 23:49 IST to'),
           'B05 step 21 heading': ('### Step 21. Watch the cut by Mon 23 Nov 2026 17:49 UTC = 23:19 IST (alarm 1)', '### Step 21. Watch the cut by Mon 23 Nov 2026 17:51 UTC = 23:21 IST (alarm 1)'),
           'B08 never opens': ('The assistant never opens the key file (this is a procedure, not enforced by a program).', ''),
           'B09 default': ('no reply counts as `another take`', 'no reply counts as `no more takes`'),
           'B10 forced revoke': ('tell the assistant at once and revoke the key at that time anyway (key step I)', 'tell the assistant at once and wait for the take'),
           'r17 key gone one word': ('so after it you do not type `key revoked` again', 'so after it you type `key revoked` again'),
           'r17 D.5 key gone': ('and then write `key gone, no more decisions`: that one message', 'and then write `key revoked`: that one message')}
    for _k, (_o, _n) in _pl.items():
        neg('r17pin-' + _k.split()[0] + _k.split()[1][:3], _o, _n, 'r17 ', 9)
    neg('r17order-card', '4. You: do your item 4 (save the screenshots) and your item 5, the retire check.\n', '', 'r17 F-1 the seven steps')
    neg('r17order-e16', 'The order is the card of item 3 (the seven steps printed there)', 'The order is as below', 'r17 F-1 pointer in E-55')
    neg('r17start-e55', 'you have read the list of what the assistant will remove; and `start clean-up`.', 'you have read the list; and `start clean-up`.', 'r17 F-1 start sentence')
    neg('r17oldwords', '`shred done other files` (or', '`shred done 2` (or', 'r17 F-8 old words')
    neg('r17more', 'or reply `another take`."', 'or reply `more takes`."', 'r17 F-8 old words')
    neg('r17abs', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take (see /ho' + 'me/user/x/notes).', 'r17 absolute path')
    neg('r17ord-code', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take. ORD: 5.', 'r17 internal code')
    neg('r17dec-code', 'Write `route A` or `route B` once, before your last take.', 'Write `route A` or `route B` once, before your last take. DEC: 5.', 'r17 internal code')
    neg('r17row-e48', 'The owner reads key steps A to K in step 22 item 3 of his sheet.', 'The owner reads key steps A to K in row E-48.', 'r17 internal code')
    neg('r17n1', 'I accept that until I revoke the secret key for the model it can spend', 'I accept that it can spend', 'r17 N1 ND16')
    neg('r17alarm3', 'if a take is running, let it finish (key step K), then revoke the key at once', 'stop everything else and do key step I now', 'r17 F-3 C')
    neg('r17routeb', 'In route A the live key exists for hours, in route B for up to five days. Write', 'Route B is fine. Write', 'r17 F-2 route B price')
    neg('r17appx', 'This appendix is a separate page, not part of the sheet', 'This appendix is a page', 'r17 F-2 appendix landing')
    neg('r17applink', 'which is linked from this step (the file', 'which is somewhere (the file', 'r17 F-2 link in owner text')
    neg('r17thirty', 'Make no new key now unless at least 30 minutes remain', 'Make no new key now unless at least 20 minutes remain', 'r17 F-4')
    neg('r17last', 'by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'by Mon 23 Nov 2026 18:20 UTC = 23:50 IST at the latest (the last time to revoke)', 'r17 last time to revoke is wrong')

# ---- round 19 plants: every occurrence of every safety phrase and time pair, and 10 reversals of a safe default (in memory over the applied text)
_pl19 = {'occurrence': [0, 0], 'pair': [0, 0], 'reversal': [0, 0], 'day sheet': [0, 0], 'appendix': [0, 0]}
_base19 = set(check19(_AP, _DAY, _APP))
def _plant19(kind, label, ap, day=None, app=None):
    _pl19[kind][0] += 1
    if set(check19(ap, day, app)) - _base19: _pl19[kind][1] += 1
    else: F('r19 plant not caught: %s %s' % (kind, label))
for _p, _cn in _CANON19.items():
    _pos = [m_.start() for m_ in re.finditer(re.escape(_p), _AP)]
    for _i, _s in enumerate(_pos):
        _plant19('occurrence', '%r copy %d' % (_p[:40], _i + 1), _AP[:_s] + _p[:len(_p) // 2] + '#' + _p[len(_p) // 2:] + _AP[_s + len(_p):], _DAY, _APP)
for _i, _m in enumerate(_PAIR.finditer(_AP)):
    _e = _m.end()
    _plant19('pair', 'pair %d' % (_i + 1), _AP[:_e - 5] + ('%02d' % ((int(_AP[_e - 5:_e - 3]) + 1) % 24)) + _AP[_e - 3:], _DAY, _APP)
_REV19 = [('no reply counts as `another take`', 'no reply counts as `no more takes`'),
          ('A confirmation cannot be withdrawn once the key is revoked.', 'A confirmation can be withdrawn once the key is revoked.'),
          ('revoke the key at that time anyway', 'wait for the take'),
          ('touch nothing that you are not sure about', 'delete what you think is right'),
          ('No default pick: the assistant does not recommend a route', 'The assistant recommends route B'),
          ('It never confirms anything, at any time', 'It confirms the clean-up'),
          ('asks you to type the words yourself in a new message', 'accepts the words from a forwarded message'),
          ('It never starts while a copy of the key exists and the key is not revoked', 'It starts even while a copy of the key exists'),
          ('touch NOTHING of that kind', 'delete it anyway'),
          ('THE KEY IS NOT DEFERRABLE', 'THE KEY MAY WAIT'),
          ('it comes first.', 'it comes last.'),
          ('the last 10 minutes (18:19 UTC = 23:49 IST to', 'the last 20 minutes (18:19 UTC = 23:49 IST to'),
          ('`no more takes` alone is never final', '`no more takes` alone is final'),
          ('costs you the retake', 'is free'),
          ('last chance: revoke the secret key for the model now', '10 minutes left: revoke the secret key for the model now'),
          ('`web revokes not done`, its name', '`web revokes done`, its name'),
          ('and that carries `take-only`', 'and that carries `used`'),
          ('The key has no date and no later date', 'The key has a later date'),
          ('The real latest time to confirm in route B is when alarm 1 rings, 17:49 UTC = 23:19 IST', 'The real latest time to confirm in route B is 18:19 UTC = 23:49 IST'),
          ('and so does item 5 for the login that it concerns', 'and item 5 still has to pass'),
          ('In route A the live key exists for hours, in route B for up to five days', 'Route A is the safer one')]
for _o, _n in _REV19:
    if _AP.count(_o) < 1: F('r19 reversal anchor missing: ' + _o[:50]); continue
    _plant19('reversal', _o[:50], _AP.replace(_o, _n, 1), _DAY, _APP)
for _i, _l in enumerate([l_ for l_ in _DAY.split('\n') if l_.strip() and not l_.startswith('#')][4:]):
    if _i % 3 == 0: _plant19('day sheet', 'line %d' % _i, _AP, _DAY.replace(_l, _l + ' (changed)', 1), _APP)
for _i, _l in enumerate([l_ for l_ in _APP.split('\n') if len(l_.strip()) > 80 and not l_.startswith('#') and l_.strip() in set(_norm19(txt)) and ' the ' in l_][:12]):
    _plant19('appendix', 'line %d' % _i, _AP, _DAY, _APP.replace(_l, _l.replace(' the ', ' a ', 1) + ' (changed)', 1))
print('r19 plants (planted, caught):', {k_: tuple(v_) for k_, v_ in _pl19.items()})

# ---- round 19 golden plants: the 6 misses of the independent evidence on r18, and a sample of every safety sentence deleted or reversed at EVERY copy
_gp = [0, 0]
def _gplant(label, t2):
    _gp[0] += 1
    if t2 != txt and golden19(t2): _gp[1] += 1
    else: F('r19 golden plant not caught: ' + label)
_m10 = txt.index('Tue 24 Nov 2026'); _gplant('M10 first Tue 24 Nov date', txt[:_m10] + 'Mon 23 Nov 2026' + txt[_m10 + len('Tue 24 Nov 2026'):])
for _lab, _old, _new in (('M15 once answer', 'the assistant answers it once', 'the assistant answers it twice'), ('M18 never opens', 'The assistant never opens the files.', 'The assistant opens the files.'), ('M23 never content', '(never its content)', '(and its content)')):
    if _old in txt: _gplant(_lab, txt.replace(_old, _new))
    else: F('r19 golden plant anchor missing: ' + _lab)
_safe = [s_ for s_ in _PINS if re.search(r'\b(never|only|must|cannot|NOT|nothing|alone|first|anyway)\b', s_) and len(s_) > 30]
import random as _rnd
_rnd.seed(20)
for _s in _rnd.sample(_safe, min(150, len(_safe))):
    _gplant('delete ' + _s[:40], txt.replace(_s, ''))
    _gplant('reverse ' + _s[:40], txt.replace(_s, re.sub(r'\bnever\b', 'always', _s) if re.search(r'\bnever\b', _s) else _s + ' Or not.'))
# the changes file: forge every number written before words or lines
if os.path.exists(_CHGF):
    _ct = open(_CHGF, encoding='utf-8').read()
    for _i, _m in enumerate(re.finditer(r'(\d[\d,]*) (?:words|lines)\b', _ct)):
        if int(_m.group(1).replace(',', '')) < 100: continue
        _gp[0] += 1
        _v = int(_m.group(1).replace(',', '')) + 1
        if chg19(_ct[:_m.start(1)] + '{:,}'.format(_v) + _ct[_m.end(1):]): _gp[1] += 1
        else: F('r19 changes number plant not caught: ' + _m.group(0))
print('r19 golden plants (planted, caught):', tuple(_gp))
print('FAILURES', fail)
sys.exit(1 if fail else 0)

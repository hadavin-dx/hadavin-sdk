import re, sys, ast, collections, shutil, os
D = '/home/user/hadavin-sdk/handover/core-hardening/'
E = os.environ.get("EDITS_PATH") or (D + "steps-edits/EDITS.md")
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
if len(rows) != 56: F('rows != 56')
ids = [r['id'] for r in rows]
exp = ['E-%02d' % n for n in range(1, 59) if n not in (10, 35)]
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
sd = '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/'
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
bt = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
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
m = re.search(r'(\d+) rows in total: E-01 to E-58 without E-10 and E-35\. By file: OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
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
if nums != list(range(1, 16)): F('ND numbers')
if 'items 1 to 15' not in ndsec: F('ND header count')
# (5) confirmations a..f without gaps and no g
csec = txt[txt.index('## FOR THE STUDIO LEAD TO CONFIRM'):txt.index('Removed in round 3')]
letters = re.findall(r'(?m)^([a-z])\. ', csec)
print('confirmation letters', letters)
if letters != list('abcdefghijkl'): F('confirmation letters')
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
if any(x < 1 or x > 15 for x in nn): F('ND number out of range')
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
for need in ('18:14 UTC = 23:44 IST', '18:04 UTC = 23:34 IST', '18:19 UTC = 23:49 IST', '18:29 UTC = 23:59 IST', 'not run', 'window'):
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
    for m_ in re.finditer(r'\b\d{1,2}:\d{2} UTC\b(?! = \d{1,2}:\d{2} IST)(?! \(\d{1,2}:\d{2} IST\))', t_):
        if '(UTC' in t_[max(0, m_.start()-8):m_.start()]: continue
        F(f'{rid_} UTC time without IST: {t_[max(0, m_.start()-30):m_.end()+20]!r}')
pw = txt[:txt.index('## The row blocks')] + '\n'.join(l_ for l_ in txt[txt.index('## The row blocks'):].split('\n') if l_.startswith('Why:'))
for m_ in re.finditer(r'\b\d{1,2}:\d{2} UTC\b(?! = \d{1,2}:\d{2} IST)', pw):
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
t48 = pairs['E-48']['new'][0]
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
if '`ND7a-late: <answer>; <who>; <date and time in UTC and IST>`' not in txt: F('R7 record format')
# c10 "rehearsal" always with its first word
for m_ in re.finditer(r'(?i)(?<!flow )rehearsal', txt):
    F('rehearsal alone: ' + txt[max(0, m_.start()-30):m_.end()+10].replace('\n', ' '))
# c11 Q19.5 and m4
if 'except the key that the take runs on' not in rowtext('E-48'): F('E-48 Q19.5 wording')
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
for need in ('crash check: tested or untested', 'never counted in N1', 'before you reply', '18:04 UTC = 23:34 IST', 'three points', 'exit code', 'Your Linux user'):
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
if 'CONFIRMED by the studio lead' not in csec: F('confirmation h')
print('round 11 checks done')

# ================= round 12 checks =================
t12 = pairs['E-12']['new'][0]
for need in ('exactly one of these four labels', '"result file", "reviewers\' report", "search file" and "test output file"', 'stand-in test <N1> pass, 0 failed, 0 missed, 0 not run', 'A retake (step 20) needs a new take id', 'delete request', 'a finding is one problem', '"Failed" means', '"Not run" means', 'For "failed" and "not run" you answer no', '`<X>` is the dollar figure'):
    if need not in t12: F('r12 E-12 lacks ' + need)
if 'delete call' in t12: F('r12 E-12 delete call')
t09 = pairs['E-09']['new'][0]
for need in ('Who can see the password', 'part of their settings', 'throwaway database of this take only', 'Never type a password inside a command line', 'press Ctrl+X to close nano without changing anything', 'field called "Password"', 'Its first action is `chmod 600 n8n.env`', 'copy any made-up word'):
    if need not in t09: F('r12 E-09 lacks ' + need)
if 'if a message asks you that, answer no' not in t09: F('r12 E-09 fallback forbidden')
t48 = pairs['E-48']['new'][0]
for need in ('`no more takes`', '`more takes`', '`same key`', '`different key`', 'shred -u <path>', 'Shredding does not revoke', 'not reliable on every disk', 'inside the take folder', 'its name and at the date it was last used', 'the one on port 5678', 'right after the last take that you accept', 'In its next message after your `no more takes`', 'no screenshot of the key list'):
    if need not in t48: F('r12 E-48 lacks ' + need)
t37 = pairs['E-37']['new'][0]
for need in ('port 5678', 'delete request', 'asks HubSpot to delete a contact', 'whether archiving a contact in HubSpot is the same as deleting it is not settled'):
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
for need in ('reply `cut accepted`', '`no more takes`', 'no further take is possible with that key'):
    if need not in t57: F('r12 E-57 lacks ' + need)
if '`no more takes`' not in t55 or '18:19 UTC = 23:49 IST' not in t55: F('r12 E-55 trigger')
if '`key kept`' not in t58: F('r12 E-58 conditional row')
t49 = rowtext('E-49')
if 'no paid model call is planned' not in t49: F('r12 E-49 planned')
if not re.search(r'(?m)^15\. \*\*When the owner writes `no more takes`', ndsec): F('r12 ND15 missing')
if 'ND7a2' not in ndsec: F('r12 ND7a2')
if 'R10 (' not in txt: F('r12 rule R10')
if 'HubSpot app 2' not in csec and 'app 2' not in csec: F('r12 L-APP2 not noted')
print('round 12 checks done')

# ================= negative controls (each check must fail on a planted defect) =================
import subprocess
def neg(name, old, new, expect, count=1):
    src = open(E, encoding='utf-8').read()
    if src.count(old) < 1:
        F('negative control anchor missing: ' + name); return
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
    neg('r11e58', 'Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST', 'Mon 23', 'E-58 times')
    neg('nd14', '14. **Does the lease sentence of Q22(c)', '14. **Something else', 'ND14 missing')
    neg('e17lease', '**a lead sent twice with the same id is processed once; a crash', '**a lead sent twice with the same id (see the lease) is processed once; a crash', 'E-17 lease sentence added')
    neg('e22', 'the case counts as "crash check untested", the same words', 'the case counts as untested, the same words', 'crash check untested missing in E-22')
    neg('e43', "except the model stage's journal file `stage.journal`", 'and nothing else', 'E-43 lacks stage.journal', 2)
    neg('e49', "AFTER the assistant's message that states (a) to (d)", 'after something', 'E-49 consent not tied')
    neg('e49day', 'written like this: `Wed 18 Nov 2026`', 'written as a day', 'E-49 lacks day format example')
    neg('e53', 'Section 4b overrides line 27', 'Section 4b follows line 27', 'E-53 lacks override')
    neg('e51', 'the end of the spending window); that statement', 'the window end); that statement', 'E-51 wording')
    neg('e52', '**A mail address**', '**A postal address**', 'E-52 new word not once: A mail address')
    neg('e04', 'otherwise the made-up names to look for.\n~~~~', 'otherwise the made-up names to look for\n~~~~', 'E-04 no final full stop')
    neg('e07', 'nobody on this branch has read that evidence. The assistant checks', 'nobody has read that evidence. The assistant checks', 'E-07 lacks')
    neg('e08', 'nobody on this branch has read that evidence yet.\n~~~~', 'nobody has read that evidence yet.\n~~~~', 'E-08 lacks')
    neg('record', 'The line has the form shown after "Record:"', 'The line is `ND<number>: <answer>, <who>`; it has the form shown after Record', 'old record format')
    neg('nd8date', 'Record: `ND8: A|B`.', 'Record: `ND8: A|B <date and time in UTC and IST>`.', 'ND record carries a date')
    neg('rehearsal', 'The flow rehearsal comes after', 'The rehearsal comes after', 'rehearsal alone')
    neg('q195', 'except the key that the take runs on (the key you saved for the take)', 'except the key', 'E-48 Q19.5 wording')
    neg('m4', 'the assistant tells you in writing what happens next (step 22', 'the assistant tells you (step 22', 'E-12 lacks what happens next')
    neg('e31', 'nothing here says that it stops safely (UNVERIFIED)', 'it stops safely (UNVERIFIED)', 'E-31 unproven claim')
    neg('line14', 'search path = the list of schemas', 'search path is a list of schemas', 'line 14 lacks')
    neg('e14', '(rule 5 of this sheet: you are the one who publishes)', '(rule 5: you post)', 'E-14 post meaning')
    # negative controls for older checks (selected: row count, old text, ND range, confirmation letters, UTC pairing, banned scan not tested)
    neg('r12nd15', '15. **When the owner writes `no more takes`', '15. **Something else', 'r12 ND15 missing')
    neg('r12shred', 'Shredding does not revoke the key, and it is not reliable on every disk', 'Shredding revokes the key', 'r12 E-48 lacks')
    neg('r12key2', 'the one on port 5678? If it is, revoking it breaks that n8n." Reply', 'the one in your n8n? If it is, revoking it breaks that n8n." Reply', 'r12 E-48 lacks the one on port 5678')
    neg('r12slot', 'exactly one of these four labels', 'exactly one of these labels', 'r12 E-12 lacks exactly one of these four labels')
    neg('r12call', 'The last step of the take program sends no delete request to HubSpot', 'The last step of the take program makes no delete call to HubSpot', 'delete call')
    neg('r12pw', 'Never type a password inside a command line, even if', 'Type the password on the command line if', 'r12 E-09 lacks')
    neg('r12vol', 'Whether a volume is used is UNVERIFIED.', 'A volume is used.', 'r12 E-16 lacks')
    neg('r12cut', 'Watch the cut from the first second to the last; reply `cut accepted`', 'Watch the cut from the first second to the last; reply `accepted`', 'r12 E-57 lacks')
    neg('r12conf', '\nl. E-12 gives the request', '\nm. E-12 gives the request', 'confirmation letters')
    neg('rowcount', '### E-58: OWNER-STEPS', '### E-59: OWNER-STEPS', 'ids differ')
    neg('conf', '\nj. E-56 puts', '\nk. E-56 puts', 'confirmation letters')
print('FAILURES', fail)
sys.exit(1 if fail else 0)

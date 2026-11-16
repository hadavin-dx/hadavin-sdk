# Independent checker for EDITS.md (evidence runner script; records, does not judge the content).
# usage: python3 -B -I check_r10b.py EDITS_PATH INPUTS_DIR BANNED_SRC [--report]
import re, sys, ast, datetime, collections
edits_path, inputs_dir, banned_src = sys.argv[1:4]
report = '--report' in sys.argv
fails = []
info = []
def F(m): fails.append(m)
def I(m): info.append(m)
txt = open(edits_path, encoding='utf-8').read()
lines = txt.split('\n')

# ---- parse
hdr = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+?), type (.+)$')
fence = [i for i, l in enumerate(lines) if l == '~~~~']
if len(fence) % 2: F('odd number of fences')
rows = []
cur = None
blocks_of_row = {}
hdr_idx = [(i, hdr.match(l)) for i, l in enumerate(lines) if l.startswith('### E-')]
for i, m in hdr_idx:
    if not m: F('malformed row header line %d: %s' % (i + 1, lines[i][:60]))
hdr_idx = [(i, m) for i, m in hdr_idx if m]
for n, (i, m) in enumerate(hdr_idx):
    end = hdr_idx[n + 1][0] if n + 1 < len(hdr_idx) else len(lines)
    r = dict(id=m.group(1), file=m.group(2), line=int(m.group(3)), line2=int(m.group(4)) if m.group(4) else None,
             status=m.group(5), type=m.group(6), olds=[], news=[], hdrline=i + 1)
    j = i + 1
    while j < end:
        if lines[j] == '~~~~':
            k = j + 1
            while k < end and lines[k] != '~~~~': k += 1
            if k >= end: F(r['id'] + ' unclosed fence'); break
            label = lines[j - 1]
            body = '\n'.join(lines[j + 1:k])
            if label.startswith('OLD'): r['olds'].append((label, body))
            elif label.startswith('NEW'): r['news'].append((label, body))
            else: F(r['id'] + ' fence without OLD/NEW label: ' + label[:40])
            j = k + 1
        else: j += 1
    rows.append(r)
ids = [r['id'] for r in rows]
exp = ['E-%02d' % n for n in range(1, 57) if n not in (10, 35)]
I('rows parsed %d' % len(rows))
if len(rows) != 54: F('row count %d != 54' % len(rows))
if len(set(ids)) != len(ids): F('duplicate E-nn ids: ' + str([x for x, c in collections.Counter(ids).items() if c > 1]))
if ids != exp: F('ids not the expected continuous list (E-01..E-56 without E-10, E-35): diff ' + str(sorted(set(exp) ^ set(ids))))
for r in rows:
    if not r['olds']: F(r['id'] + ' has no OLD block')
    if not r['news']: F(r['id'] + ' has no NEW block')

# ---- (1) old texts in inputs
cache = {}
def inp(name):
    if name not in cache:
        try: cache[name] = open(inputs_dir + '/' + name, encoding='utf-8').read()
        except Exception as e:
            cache[name] = None; F('cannot read input ' + name)
    return cache[name]
spans = collections.defaultdict(list)
old_rep = []
for r in rows:
    t = inp(r['file'])
    if t is None: continue
    stated = [r['line']] + ([r['line2']] if r['line2'] else [])
    for lab, o in r['olds']:
        c = t.count(o)
        if c == 0: F('%s OLD missing in %s' % (r['id'], r['file'])); old_rep.append((r['id'], 'MISSING', 0, None)); continue
        if c > 1: F('%s OLD occurs %d times in %s' % (r['id'], c, r['file'])); old_rep.append((r['id'], 'REPEATED', c, None)); continue
        st = t.index(o)
        ln = t.count('\n', 0, st) + 1
        if ln not in stated: F('%s OLD starts on line %d but stated %s' % (r['id'], ln, stated))
        spans[r['file']].append((st, st + len(o), r['id'], lab))
        old_rep.append((r['id'], 'ONCE', 1, ln))
ov = []
for f, sp in spans.items():
    sp.sort()
    for a, b in zip(sp, sp[1:]):
        if b[0] < a[1]: ov.append((a[2], b[2])); F('OLD overlap %s / %s' % (a[2], b[2]))
    # also pairwise (not just neighbours)
    for x in range(len(sp)):
        for y in range(x + 1, len(sp)):
            if sp[y][0] < sp[x][1] and (sp[x][2], sp[y][2]) not in ov and sp[x][2] != sp[y][2] and sp[y][0] >= sp[x][0]:
                F('OLD overlap %s / %s' % (sp[x][2], sp[y][2]))
    # same row with two olds overlapping is also caught above
if report:
    for x in old_rep: print('OLD', *x)
    print('overlaps', ov)

# ---- (2) apply
def is_hold_label(lab): return '[HOLD' in lab
def apply_rows(include_hold):
    cp = {}
    log = []
    for r in rows:
        t = cp.get(r['file']) or inp(r['file'])
        if t is None: continue
        cp[r['file']] = t
        # pair OLD k with NEW k when counts equal, else first OLD with each selected NEW sequentially
        sel = [(lab, b) for lab, b in r['news'] if include_hold or not is_hold_label(lab)]
        if not sel: log.append((r['id'], 'no-block-applied')); continue
        for k, (lab, b) in enumerate(sel):
            o = r['olds'][k][1] if len(r['olds']) == len(r['news']) and len(r['olds']) > 1 else r['olds'][0][1]
            if len(r['olds']) == len(r['news']) and len(r['olds']) > 1:
                o = r['olds'][[x[0] for x in r['news']].index(lab)][1]
            c = cp[r['file']].count(o)
            if c != 1: log.append((r['id'], 'FAILED old count %d at apply time (%s)' % (c, lab[:30]))); continue
            cp[r['file']] = cp[r['file']].replace(o, b, 1)
            log.append((r['id'], 'applied ' + ('HOLD ' if is_hold_label(lab) else '') + lab[:28]))
    return cp, log
cpA, logA = apply_rows(False)
cpB, logB = apply_rows(True)
import os
if os.environ.get('DUMP'):
    for tag, cpx in (('A', cpA), ('B', cpB)):
        os.makedirs(os.environ['DUMP'] + '/' + tag, exist_ok=True)
        for fn_, t_ in cpx.items(): open(os.environ['DUMP'] + '/' + tag + '/' + fn_, 'w', encoding='utf-8').write(t_)
for fn_, t_ in cpA.items():
    if 'DO NOT APPLY' in t_ or '[HOLD' in t_: F('applied non-hold copy of %s contains HOLD text' % fn_)
badA = [x for x in logA if 'FAILED' in x[1]]
for x in badA: F('apply (non-hold) ' + str(x))
holdApplied = [x for x in logB if 'HOLD' in x[1]]
naiveFail = [x for x in logB if 'FAILED' in x[1]]
I('non-hold blocks applied cleanly: %d, failures %d' % (len([x for x in logA if x[1].startswith('applied')]), len(badA)))
I('naive apply-all: HOLD blocks that a script applying every NEW block would apply: %d rows %s; naive failures %d %s' % (len(holdApplied), sorted(set(x[0] for x in holdApplied)), len(naiveFail), [x[0] for x in naiveFail]))
# hold labelling consistency
for r in rows:
    hs = r['status'].startswith('Hold')
    labs = [is_hold_label(l) for l, _ in r['news']]
    if hs and not all(labs): F(r['id'] + ' Hold row has a NEW block without [HOLD label')
    if not hs and all(labs): F(r['id'] + ' non-Hold row has only HOLD blocks')
    if not hs and any(labs) and r['id'] != 'E-36': F(r['id'] + ' non-Hold row carries a [HOLD block (only E-36 is allowed)')
    for l, _ in r['news']:
        if is_hold_label(l):
            g = re.search(r'\[HOLD (G\d|Cb)', l)
            if not g: F(r['id'] + ' HOLD label has no gate')
            elif g.group(1)[0] == 'G' and ('gate ' + g.group(1)) not in r['status'] and r['id'] != 'E-36': F(r['id'] + ' HOLD label gate differs from header: ' + g.group(1))
    if hs and not re.search(r'gate G\d', r['status']): F(r['id'] + ' Hold without gate in header')
# edge whitespace
for r in rows:
    for lab, b in r['olds'] + r['news']:
        if b != b.strip(): F(r['id'] + ' block with edge whitespace')
        if not b: F(r['id'] + ' empty block')
        if '~~~~' in b: F(r['id'] + ' fence inside block')

# ---- (4) counts
stc = collections.Counter(r['status'].split(' (')[0].strip() for r in rows)
I('status counts ' + str(dict(stc)))
if stc['Apply now'] != 42: F('Apply now %d != 42' % stc['Apply now'])
if stc['Hold'] != 12: F('Hold %d != 12' % stc['Hold'])
if sum(stc.values()) != 54: F('status total != 54 (other statuses: %s)' % dict(stc))
if set(stc) - {'Apply now', 'Hold'}: F('unexpected status ' + str(set(stc) - {'Apply now', 'Hold'}))
# text claims
m = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*', txt)
if not m or (int(m.group(1)), int(m.group(2))) != (stc['Apply now'], stc['Hold']): F('Counts sentence differs from computed status counts')
holds = [r['id'] for r in rows if r['status'].startswith('Hold')]
applies = [r['id'] for r in rows if r['status'].startswith('Apply now')]
mh = re.search(r'the Hold rows are ([E0-9, -]+?)\)', txt)
if not mh or [x.strip() for x in mh.group(1).split(',')] != holds: F('Hold id list in Counts differs from headers')
ma = re.search(r'The Apply now ids \(\d+\) are: ([E0-9, -]+?)\. ', txt)
if not ma or [x.strip() for x in ma.group(1).split(',')] != applies: F('Apply now id list in Counts differs from headers')
m = re.search(r'(\d+) rows in total: E-01 to E-56 without E-10 and E-35\. By file: OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
fc = collections.Counter(r['file'] for r in rows)
if not m or tuple(map(int, m.groups())) != (len(rows), fc['OWNER-STEPS-realrun-v3.md'], fc['AGENT-SCOPE-DO-AND-DONT.md'], fc['DECISION-one-store.md']): F('file counts sentence differs: computed %s' % dict(fc))
# NOT DECIDED items
nd_sec = txt[txt.index('## NOT DECIDED'):txt.index('## FOR THE STUDIO LEAD TO CONFIRM')]
nd = [int(x) for x in re.findall(r'^(\d+)\. \*\*', nd_sec, re.M)]
if nd != list(range(1, 15)): F('NOT DECIDED numbers %s not 1..14' % nd)
for mm in re.finditer(r'NOT DECIDED (\d+)|\bND ?(\d+)', txt):
    n = int(mm.group(1) or mm.group(2))
    if not 1 <= n <= 14: F('NOT DECIDED reference out of range: %d' % n)
# confirmation letters
cf = txt[txt.index('## FOR THE STUDIO LEAD TO CONFIRM'):txt.index('## Rules for the studio lead')]
letters = re.findall(r'^([a-z])\. ', cf, re.M)
if ''.join(letters) != 'abcdefghij': F('confirmation letters defined: %s' % ''.join(letters))
used_conf = set(re.findall(r'[Cc]onfirmation ([a-z])\b', txt)) | set(x[1] for x in re.findall(r'\b(C)([a-j])\b(?!\w)', txt))
if not used_conf <= set(letters): F('confirmation letters used but not defined: %s' % sorted(used_conf - set(letters)))
I('confirmation letters defined %s used %s' % (''.join(letters), sorted(used_conf)))
# gates
gs = txt[txt.index('## Gates'):txt.index('## How the rows are used')]
gdef = re.findall(r'^- \*\*(G\d)\b', gs, re.M)
if gdef != ['G1', 'G2', 'G3', 'G4', 'G5']: F('gates defined %s' % gdef)
gused = set(re.findall(r'\b(G\d+)\b', txt))
if not gused <= set(gdef): F('gate letters used but not defined: %s' % sorted(gused - set(gdef)))
hdr_gates = set(re.findall(r'gate (G\d)', ' '.join(r['status'] for r in rows)))
I('gates defined %s; used anywhere %s; in headers %s' % (gdef, sorted(gused), sorted(hdr_gates)))
# per-gate lists in the Gates section vs headers
for g in gdef:
    m = re.search(r'^- \*\*' + g + r',[^(]*\(([^)]*)\)', gs, re.M)
    if not m: continue
    listed = sorted(set(re.findall(r'E-\d+', m.group(1).split(';')[0])))
    actual = sorted(r['id'] for r in rows if ('gate ' + g) in r['status'])
    # G2 rows are Apply now with "after gate G2" text; compare as sets for G1,G3,G4,G5 on holds
    if g != 'G2' and listed != actual: F('gate %s list %s differs from headers %s' % (g, listed, actual))
# E-nn mentions exist
allids = set(re.findall(r'\bE-\d{2}\b', txt))
bad = sorted(x for x in allids if x not in set(ids) and x not in ('E-10', 'E-35'))
if bad: F('E-nn mentioned but not a row: %s' % bad)
inblk = set()
for a, b in zip(fence[0::2], fence[1::2]): inblk.update(range(a, b + 1))
rm_ment = [(n + 1, x) for n, l in enumerate(lines) for x in ('E-10', 'E-35') if re.search(r'\b' + x + r'\b', l)]
I('removed ids E-10/E-35 mentioned at lines %s' % rm_ment)
for n_, x in rm_ment:
    if (n_ - 1) in inblk: F('removed id %s mentioned inside a fenced block at line %d' % (x, n_))
    if lines[n_ - 1].startswith('| ' + x): F('removed id %s has an index row' % x)
# index table
idx = {}
for l in lines:
    m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$', l)
    if m: idx[m.group(1)] = [x.strip() for x in m.groups()]
if sorted(idx) != sorted(ids): F('index table ids differ from rows: %s' % sorted(set(idx) ^ set(ids)))
for r in rows:
    x = idx.get(r['id'])
    if not x: continue
    ls = str(r['line']) + (' (and %d)' % r['line2'] if r['line2'] else '')
    st = r['status'].split(' (')[0].strip()
    if x[1] != r['file'] or x[2] != ls or x[3] != st: F('index row mismatch %s: %s vs %s %s %s' % (r['id'], x[1:4], r['file'], ls, st))
    g = re.search(r'gate (G\d)', r['status'])
    if st == 'Hold' and (not g or x[4] != g.group(1)): F('index gate differs for ' + r['id'])

# ---- (3) times and dates
def hm(s): h, m_ = s.split(':'); return int(h) * 60 + int(m_)
tm = re.compile(r'\b(\d{1,2}:\d{2}) (UTC|IST)\b')
lone = []; pairs = []
for n, l in enumerate(lines, 1):
    toks = [(m.start(), m.group(1), m.group(2)) for m in tm.finditer(l)]
    utc = [t for t in toks if t[2] == 'UTC']; ist = [t for t in toks if t[2] == 'IST']
    used = set()
    for u in utc:
        best = None
        for k, s in enumerate(ist):
            if k in used: continue
            d = abs(s[0] - u[0])
            if d <= 90 and (best is None or d < best[0]): best = (d, k, s)
        if not best: lone.append((n, u[1] + ' UTC')); continue
        used.add(best[1])
        ok = (hm(u[1]) + 330) % 1440 == hm(best[2][1])
        pairs.append((n, u[1], best[2][1], ok))
        if not ok: F('line %d: %s UTC is not %s IST' % (n, u[1], best[2][1]))
    for k, s in enumerate(ist):
        if k not in used: lone.append((n, s[1] + ' IST'))
if lone and any('UTC' in x[1] for x in lone):
    for x in lone:
        if 'UTC' in x[1]: F('lone UTC time with no IST: line %d %s' % x)
I('UTC/IST pairs %d (all consistent: %s); lone times %s' % (len(pairs), all(p[3] for p in pairs), lone))
if report:
    for p in pairs: print('PAIR line %d %s UTC = %s IST %s' % p)
    print('LONE', lone)
# ISO date + time pairs: date part must be same in the pair
for m in re.finditer(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC', txt):
    pass
# weekday/date strings
mon = {m_: i for i, m_ in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
dates = []
for n, l in enumerate(lines, 1):
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?: (\d{4}))?', l):
        y = int(m.group(4) or 2026)
        try: d = datetime.date(y, mon[m.group(3)], int(m.group(2)))
        except ValueError: F('line %d impossible date %s' % (n, m.group(0))); continue
        ok = wd[d.weekday()] == m.group(1)
        dates.append((n, m.group(0), d.isoformat(), wd[d.weekday()], ok))
        if not ok: F('line %d: %s is a %s' % (n, m.group(0), wd[d.weekday()]))
    for m in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', l):
        try: datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: F('line %d impossible ISO date %s' % (n, m.group(0)))
# ISO date near a weekday word
for n, l in enumerate(lines, 1):
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b[^.\n]{0,12}?(\d{4}-\d{2}-\d{2})', l):
        d = datetime.date.fromisoformat(m.group(2))
        if wd[d.weekday()] != m.group(1): F('line %d: %s is a %s' % (n, m.group(2), wd[d.weekday()]))
I('weekday/date strings %d all correct: %s' % (len(dates), all(x[4] for x in dates)))
if report:
    for x in dates: print('DATE line %d %s -> %s %s %s' % x)
# ISO-date UTC/IST pairs: same date in both
for m in re.finditer(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC[^\n]{0,60}?(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) IST', txt):
    a = datetime.datetime.fromisoformat(m.group(1) + 'T' + m.group(2)) + datetime.timedelta(minutes=330)
    b = datetime.datetime.fromisoformat(m.group(3) + 'T' + m.group(4))
    if a != b: F('ISO UTC/IST pair mismatch ' + m.group(0)[:80])

# ---- secrets / banned
bt = open(banned_src, encoding='utf-8').read()
bm = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
banned = ast.literal_eval('(' + bm.group(1) + ')')
bh = sum(1 for b in banned if b in txt)
I('banned strings in EDITS.md: %d of %d' % (bh, len(banned)))
if bh: F('banned vendor string present (%d)' % bh)
secpats = [r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9]{20,}', r'gh[pousr]_[A-Za-z0-9]{20,}', r'xox[abp]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)\bpassword\s*[:=]\s*[^\s`<]{6,}', r'(?i)\b(secret|token|api[_-]?key)\s*[:=]\s*[A-Za-z0-9+/_-]{16,}', r'\b[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9.-]+\.[a-z]{2,}\b', r'\b[0-9]{12}\b(?=.*account)']
for p in secpats:
    for mm in re.finditer(p, txt):
        if mm.group(0) == 'AKIAIOSFODNN7EXAMPLE': continue
        F('secret-shaped string: pattern %s' % p[:25])
# HOLD label present count
nh = sum(1 for r in rows for l, _ in r['news'] if is_hold_label(l))
I('NEW blocks labelled HOLD: %d' % nh)
if nh != 14: F('HOLD-labelled NEW blocks %d != 14' % nh)

if report:
    for x in info: print('INFO', x)
    for x in logB: print('NAIVE', x)
for f in fails: print('FAIL', f)
print('RESULT', 'FAIL %d' % len(fails) if fails else 'OK')
sys.exit(1 if fails else 0)

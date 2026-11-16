#!/usr/bin/env python3
"""Independent checker for EDITS.md (round 11). Written from the brief, not from verify11.py.
usage: check_r11_own.py EDITS_PATH INPUTS_DIR SCRATCH_DIR [--quiet] [--check-sha]
Exit 0 = no FAIL; exit 1 = at least one FAIL. Never edits EDITS_PATH or the inputs."""
import sys, re, os, hashlib, collections, datetime

EDITS, INPUTS, SCR = sys.argv[1], sys.argv[2], sys.argv[3]
QUIET = '--quiet' in sys.argv
EXPECT_SHA = '63a730eb77a4da41282e277477922c64f9e15a1f213b1c0055c3f2c6e3e847be'
CHECK_SHA = '--check-sha' in sys.argv
fails = []
notes = []


def FAIL(m):
    fails.append(m)


def NOTE(m):
    notes.append(m)


raw = open(EDITS, 'rb').read()
txt = raw.decode('utf-8')
lines = txt.split('\n')
if CHECK_SHA and hashlib.sha256(raw).hexdigest() != EXPECT_SHA:
    FAIL('sha256 differs from expected')
if CHECK_SHA and txt.count('\n') != 912:
    FAIL('newline count %d != 912' % txt.count('\n'))

# ---------- parse (line based; fences are lines that are exactly ~~~~)
HDR = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+?), type (.+)$')
rows = []
cur = None
open_at = None
label = None
buf = []
lastnonblank = None
for no, ln in enumerate(lines, 1):
    if open_at is None:
        m = HDR.match(ln)
        if m:
            cur = dict(id=m.group(1), file=m.group(2), line=int(m.group(3)),
                       line2=int(m.group(4)) if m.group(4) else None,
                       status_full=m.group(5), type=m.group(6), hdr_no=no, blocks=[])
            gm = re.match(r'Hold \(gate (G\d)\)$', cur['status_full'])
            cur['gate'] = gm.group(1) if gm else None
            cur['status'] = re.sub(r' \(.*$', '', cur['status_full'])
            if cur['status'] == 'Hold' and not gm:
                FAIL('%s Hold header without (gate Gx)' % m.group(1))
            rows.append(cur)
            lastnonblank = None
            continue
        if ln == '~~~~':
            if cur is None:
                FAIL('fence outside any row at line %d' % no)
            open_at = no
            label = lastnonblank
            buf = []
            continue
        if ln.startswith('## '):
            cur = None
        if ln.strip():
            lastnonblank = ln
    else:
        if ln == '~~~~':
            if cur is not None:
                cur['blocks'].append(dict(label=label or '', body='\n'.join(buf), start=open_at + 1))
            open_at = None
        else:
            buf.append(ln)
if open_at is not None:
    FAIL('unclosed fence opened at line %d' % open_at)

for r in rows:
    r['old'] = [b for b in r['blocks'] if b['label'].startswith('OLD')]
    r['new'] = [b for b in r['blocks'] if b['label'].startswith('NEW')]
    other = [b for b in r['blocks'] if not (b['label'].startswith('OLD') or b['label'].startswith('NEW'))]
    if other:
        FAIL('%s has a block with an unknown label: %r' % (r['id'], other[0]['label'][:40]))
    r['apply'] = r['status'] == 'Apply now'
    r['hold'] = r['status'] == 'Hold'
    if not (r['apply'] or r['hold']):
        FAIL('%s unknown status %r' % (r['id'], r['status']))

# ---------- ids, counts
ids = [r['id'] for r in rows]
expected_ids = ['E-%02d' % n for n in range(1, 59) if n not in (10, 35)]
if len(ids) != len(set(ids)):
    FAIL('duplicate row ids: %s' % [i for i, c in collections.Counter(ids).items() if c > 1])
if ids != expected_ids:
    FAIL('row ids differ from E-01..E-58 without E-10,E-35: missing %s extra %s' % (sorted(set(expected_ids) - set(ids)), sorted(set(ids) - set(expected_ids))))
if len(rows) != 56:
    FAIL('rows %d != 56' % len(rows))
n_apply = sum(r['apply'] for r in rows)
n_hold = sum(r['hold'] for r in rows)
if n_apply != 44:
    FAIL('Apply-now rows %d != 44' % n_apply)
if n_hold != 12:
    FAIL('Hold rows %d != 12' % n_hold)
fc = collections.Counter(r['file'] for r in rows)
byfile = (fc.get('OWNER-STEPS-realrun-v3.md', 0), fc.get('AGENT-SCOPE-DO-AND-DONT.md', 0), fc.get('DECISION-one-store.md', 0))
if byfile != (37, 15, 4) or sum(fc.values()) != 56:
    FAIL('by file %s != (37,15,4)' % (byfile,))

# stated counts in prose (line 45 style)
m = re.search(r'(\d+) rows in total: .*?OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
if not m:
    FAIL('stated row-count sentence not found')
else:
    if tuple(map(int, m.groups())) != (len(rows), byfile[0], byfile[1], byfile[2]):
        FAIL('stated counts %s differ from actual %s' % (m.groups(), (len(rows),) + byfile))
m = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*.*?\*\*Conditional (\d+)\*\*; total (\d+)', txt)
if not m:
    FAIL('stated status-count sentence not found')
else:
    if tuple(map(int, m.groups())) != (n_apply, n_hold, 0, len(rows)):
        FAIL('stated status counts %s differ from actual %s' % (m.groups(), (n_apply, n_hold, 0, len(rows))))
m = re.search(r'The Apply now ids \((\d+)\) are: ([^.]*?)\. Round 11', txt)
if not m:
    FAIL('stated Apply-now id list not found')
else:
    stated = re.findall(r'E-\d+', m.group(2))
    actual = [r['id'] for r in rows if r['apply']]
    if int(m.group(1)) != len(actual) or stated != actual:
        FAIL('stated Apply-now id list differs from rows')
m = re.search(r'\(G1: ([^,]*?(?:, E-[0-9, E-]*?)?), G3: ([^,]*?), G4: ([^,]*?), G5: ([^;)]*?); the Hold rows are ([^)]*?)\)', txt)
if not m:
    FAIL('stated gate/Hold list not found')
else:
    for g, s in zip(('G1', 'G3', 'G4', 'G5'), m.groups()[:4]):
        st = sorted(re.findall(r'E-\d+', s))
        ac = sorted(r['id'] for r in rows if r['hold'] and r['gate'] == g)
        if st != ac:
            FAIL('stated %s Hold list %s differs from rows %s' % (g, st, ac))
    st = sorted(re.findall(r'E-\d+', m.group(5)))
    if st != sorted(r['id'] for r in rows if r['hold']):
        FAIL('stated Hold id list differs from rows')
m = re.search(r'By type: STALE (\d+), UNCLEAR WORD (\d+), MISSING STEP (\d+), CONTRADICTION (\d+).*?DEFERRED (\d+)', txt)
tc = collections.Counter(re.sub(r' \(.*$', '', r['type']).strip() for r in rows)
if not m:
    FAIL('stated type counts not found')
else:
    if tuple(map(int, m.groups())) != (tc['STALE'], tc['UNCLEAR WORD'], tc['MISSING STEP'], tc['CONTRADICTION'], tc['DEFERRED']):
        FAIL('stated type counts %s differ from actual %s' % (m.groups(), dict(tc)))
if '13 held blocks' not in txt:
    FAIL('prose "13 held blocks" missing')

# ---------- inputs
inputs = {}
for r in rows:
    if r['file'] not in inputs:
        p = os.path.join(INPUTS, r['file'])
        if not os.path.exists(p):
            FAIL('input file missing %s' % r['file'])
            inputs[r['file']] = ''
        else:
            inputs[r['file']] = open(p, encoding='utf-8').read()
for fn, want in (('OWNER-STEPS-realrun-v3.md', 193), ('AGENT-SCOPE-DO-AND-DONT.md', 35)):
    if fn in inputs and inputs[fn]:
        have = inputs[fn].count('\n') + (0 if inputs[fn].endswith('\n') else 1)
        if have != want:
            FAIL('input %s has %d lines, text says %d' % (fn, have, want))
if '(193 lines, called OWNER-STEPS' not in txt or '(35 lines, called AGENT-SCOPE' not in txt:
    FAIL('stated input line counts text missing')

# every OLD exactly once at its stated line; overlaps
spans = collections.defaultdict(list)
n_old = 0
for r in rows:
    content = inputs.get(r['file'], '')
    stated_lines = [r['line']] + ([r['line2']] if r['line2'] else [])
    if not r['old']:
        FAIL('%s has no OLD block' % r['id'])
    if r['apply'] and len(r['old']) != 1:
        FAIL('%s (Apply now) has %d OLD blocks' % (r['id'], len(r['old'])))
    if len(r['old']) > 1 and len(r['old']) != len(stated_lines):
        FAIL('%s has %d OLD blocks but %d stated lines' % (r['id'], len(r['old']), len(stated_lines)))
    for k, b in enumerate(r['old']):
        n_old += 1
        o = b['body']
        if o == '':
            FAIL('%s OLD empty' % r['id'])
            continue
        c = content.count(o)
        if c != 1:
            FAIL('%s OLD%d occurs %d times (need 1)' % (r['id'], k + 1, c))
            continue
        pos = content.index(o)
        ln = content.count('\n', 0, pos) + 1
        if len(r['old']) > 1 and len(r['old']) == len(stated_lines):
            if ln != stated_lines[k]:
                FAIL('%s OLD%d at line %d, stated %d' % (r['id'], k + 1, ln, stated_lines[k]))
        elif ln not in stated_lines:
            FAIL('%s OLD at line %d, stated %s' % (r['id'], ln, stated_lines))
        spans[r['file']].append((pos, pos + len(o), r['id']))
for fn, sp in spans.items():
    sp.sort()
    for a, b in zip(sp, sp[1:]):
        if b[0] < a[1]:
            FAIL('OLD overlap in %s: %s and %s' % (fn, a[2], b[2]))
if n_old != 57:
    FAIL('OLD block total %d != 57' % n_old)

# ---------- NEW blocks and HOLD labels
hold_blocks = []
apply_blocks = []
for r in rows:
    if r['apply']:
        if len(r['new']) != 1:
            FAIL('%s (Apply now) has %d NEW blocks (need exactly 1)' % (r['id'], len(r['new'])))
        for b in r['new']:
            apply_blocks.append((r['id'], b))
            L = b['label']
            if 'HOLD' in L.upper() or 'DO NOT APPLY' in L.upper():
                FAIL('%s Apply-now NEW label looks held: %r' % (r['id'], L[:50]))
            if not L.startswith('NEW (exact'):
                FAIL('%s Apply-now NEW label unexpected: %r' % (r['id'], L[:50]))
    if r['hold']:
        if not r['new']:
            FAIL('%s Hold row without NEW block' % r['id'])
        for b in r['new']:
            hold_blocks.append((r['id'], b))
            L = b['label']
            if not L.startswith('NEW [HOLD ' + str(r['gate']) + ': DO NOT APPLY]'):
                FAIL('%s HOLD label does not start with NEW [HOLD %s: DO NOT APPLY]: %r' % (r['id'], r['gate'], L[:60]))
            if 'HOLD' not in L or 'DO NOT APPLY' not in L:
                FAIL('%s HOLD label lacks HOLD / DO NOT APPLY' % r['id'])
if len(hold_blocks) != 13:
    FAIL('HOLD-labelled blocks %d != 13' % len(hold_blocks))
if len(apply_blocks) != 44:
    FAIL('Apply-now NEW blocks %d != 44' % len(apply_blocks))
# simulate two skipping scripts over ALL NEW blocks
allnew = [(r['id'], b) for r in rows for b in r['new']]
pref_kept = [x for x in allnew if not x[1]['label'].startswith('NEW [HOLD')]
cont_kept = [x for x in allnew if 'HOLD' not in x[1]['label']]
hold_ids = set(r['id'] for r in rows if r['hold'])
for name, kept in (('prefix-skipping', pref_kept), ('contains-skipping', cont_kept)):
    leaked = [i for i, b in kept if i in hold_ids]
    if leaked:
        FAIL('%s script would apply held rows: %s' % (name, leaked))
    if len(kept) != 44:
        FAIL('%s script keeps %d NEW blocks (want 44)' % (name, len(kept)))
for r in rows:
    for b in r['blocks']:
        if 'HOLD' in b['label'] and not (r['hold'] and b['label'].startswith('NEW [HOLD')):
            FAIL('%s block label with HOLD outside a Hold row/NEW: %r' % (r['id'], b['label'][:50]))

# ---------- apply in row order on COPIES
os.makedirs(SCR, exist_ok=True)
cp = {fn: t for fn, t in inputs.items()}
for r in rows:
    if not r['apply'] or len(r['new']) != 1 or len(r['old']) != 1:
        continue
    o, n = r['old'][0]['body'], r['new'][0]['body']
    c = cp[r['file']].count(o)
    if c != 1:
        FAIL('apply %s: OLD occurs %d times in the working copy at its turn' % (r['id'], c))
        continue
    cp[r['file']] = cp[r['file']].replace(o, n, 1)
for fn, t in cp.items():
    open(os.path.join(SCR, 'applied-' + fn), 'w', encoding='utf-8').write(t)
for r in rows:
    if r['hold']:
        for b in r['old']:
            if cp[r['file']].count(b['body']) != 1:
                FAIL('after applying, Hold %s OLD occurs %d times' % (r['id'], cp[r['file']].count(b['body'])))
for r in rows:
    if r['apply'] and r['new'] and r['new'][0]['body'] not in cp[r['file']]:
        FAIL('applied NEW of %s later overwritten' % r['id'])

# ---------- index table vs headers
idx = {}
for ln in lines:
    m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$', ln)
    if m:
        if m.group(1) in idx:
            FAIL('duplicate index row %s' % m.group(1))
        idx[m.group(1)] = [g.strip() for g in m.groups()[1:]]
if len(idx) != 56:
    FAIL('index rows %d != 56' % len(idx))
for r in rows:
    x = idx.get(r['id'])
    if not x:
        FAIL('no index row for %s' % r['id'])
        continue
    ls = str(r['line']) + (' (and %d)' % r['line2'] if r['line2'] else '')
    st = 'Apply now' if r['apply'] else 'Hold'
    if (x[0], x[1], x[2], x[5]) != (r['file'], ls, st, r['type']):
        FAIL('index row %s differs from header: %s vs %s' % (r['id'], x, (r['file'], ls, st, r['type'])))
    if r['hold'] and x[3] != r['gate']:
        FAIL('index gate of %s is %r, header gate %s' % (r['id'], x[3], r['gate']))
    if r['hold'] and x[3] == '-':
        FAIL('Hold %s has no gate in the index' % r['id'])
    if r['apply'] and x[3] != '-' and r['id'] not in ('E-07', 'E-08', 'E-56'):
        FAIL('Apply-now %s has a gate %r in the index' % (r['id'], x[3]))
gates_txt = '\n'.join(l for l in lines if l.startswith('- **G'))
for g in ('G1', 'G2', 'G3', 'G4', 'G5'):
    if '- **%s,' % g not in gates_txt:
        FAIL('gate %s not described' % g)
mg = re.search(r'- \*\*G1, [^(]*\(([^)]*)\)', gates_txt)
if mg:
    named = set(re.findall(r'E-\d+', mg.group(1)))
    g1 = set(r['id'] for r in rows if r['hold'] and r['gate'] == 'G1')
    if not g1 <= named:
        FAIL('G1 bullet lacks Hold rows %s' % sorted(g1 - named))


# ---------- time and date checks
def hm(s):
    h, m_ = s.split(':')
    return int(h) * 60 + int(m_)


def fmt(t):
    t %= 1440
    return '%02d:%02d' % (t // 60, t % 60)


n_pairs = 0
for m in re.finditer(r'(\d{1,2}:\d{2}) UTC ?(?:=|\() ?(\d{1,2}:\d{2}) IST', txt):
    n_pairs += 1
    if (hm(m.group(1)) + 330) % 1440 != hm(m.group(2)):
        FAIL('UTC/IST pair wrong: %r (want %s)' % (m.group(0), fmt(hm(m.group(1)) + 330)))
for m in re.finditer(r'(\d{1,2}:\d{2}) IST', txt):
    before = txt[max(0, m.start() - 14):m.start()]
    if not re.search(r'\d{1,2}:\d{2} UTC ?(=|\() ?$', before):
        NOTE('IST time without adjacent UTC twin: ...%s' % txt[max(0, m.start() - 40):m.end()].replace('\n', ' '))
for m in re.finditer(r'(\d{1,2}):(\d{2}) \+ 5:30 = (\d{1,2}):(\d{2})', txt):
    if (hm('%s:%s' % m.group(1, 2)) + 330) % 1440 != hm('%s:%s' % m.group(3, 4)):
        FAIL('arithmetic wrong: %r' % m.group(0))
for m in re.finditer(r'(\d{1,2}:\d{2}) UTC(?! ?(?:=|\())', txt):
    NOTE('UTC time without IST: ...%s' % txt[max(0, m.start() - 30):m.end() + 25].replace('\n', ' '))
WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MON = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
n_wd = 0
for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?: (\d{4}))?', txt):
    n_wd += 1
    yr = int(m.group(4)) if m.group(4) else 2026
    try:
        d = datetime.date(yr, MON[m.group(3)], int(m.group(2)))
    except ValueError:
        FAIL('invalid date %r' % m.group(0))
        continue
    if WD[d.weekday()] != m.group(1):
        FAIL('weekday wrong: %r is a %s' % (m.group(0), WD[d.weekday()]))
    if m.group(4) and m.group(4) != '2026':
        FAIL('year not 2026: %r' % m.group(0))
for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{4})-(\d{2})-(\d{2})', txt):
    n_wd += 1
    try:
        d = datetime.date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        if WD[d.weekday()] != m.group(1):
            FAIL('weekday wrong: %r' % m.group(0))
    except ValueError:
        FAIL('invalid date %r' % m.group(0))
n_iso = 0
for m in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', txt):
    n_iso += 1
    try:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        FAIL('invalid ISO date %r' % m.group(0))
        continue
    if d.year != 2026:
        FAIL('ISO date not in 2026: %s' % m.group(0))
for m in re.finditer(r'\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b', txt):
    if m.group(3) != '2026':
        FAIL('year not 2026: %r' % m.group(0))
    try:
        datetime.date(int(m.group(3)), MON[m.group(2)], int(m.group(1)))
    except ValueError:
        FAIL('invalid date %r' % m.group(0))

# ---------- secret / fake key patterns anywhere in the file
SEC = [r'AKIA[0-9A-Z]{16}', r'ASIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9_-]{20,}', r'ghp_[A-Za-z0-9]{20,}', r'github_pat_[A-Za-z0-9_]{20,}',
       r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'\bpat-[a-z0-9]{2,4}-[0-9a-f-]{30,}',
       r'\b[A-Za-z0-9+/]{40,}={0,2}\b', r'\b[0-9a-f]{40,}\b']
for p in SEC:
    for m in re.finditer(p, txt):
        s = m.group(0)
        if s == 'AKIAIOSFODNN7EXAMPLE' or '/' in s:
            continue
        FAIL('secret-like string (%s...) at line %d' % (s[:6], txt.count('\n', 0, m.start()) + 1))

if not QUIET:
    print('rows', len(rows), 'apply', n_apply, 'hold', n_hold, 'byfile', byfile, 'old blocks', n_old,
          'apply NEW', len(apply_blocks), 'hold blocks', len(hold_blocks), 'index rows', len(idx),
          'utc/ist pairs', n_pairs, 'weekday-date strings', n_wd, 'iso dates', n_iso)
    for n in notes:
        print('NOTE', n)
for f in fails:
    print('FAIL', f)
print('RESULT', 'FAIL (%d)' % len(fails) if fails else 'PASS')
sys.exit(1 if fails else 0)

"""Runner's OWN checker for EDITS.md round 15 (written independently; not derived from chk15.py or verify15.py).
usage: python3 -B -I mychk.py <EDITS.md> <inputs dir> [--info]
Prints one 'FAIL <tag> | detail' line per problem; exit 1 if any."""
import re, sys, ast, os, datetime, collections

edits_path, inputs_dir = sys.argv[1], sys.argv[2]
info = '--info' in sys.argv
txt = open(edits_path, encoding='utf-8').read()
L = txt.split('\n')
fails = []


def F(tag, msg=''):
    fails.append((tag, msg))
    print('FAIL', tag, '|', msg[:160])


# ---------- parse rows (fence aware)
HDR = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+?), type (.+)$')
rows, cur, infence, label, buf = [], None, False, None, []
start = next(i for i, l in enumerate(L) if l.startswith('## The row blocks'))
end = next(i for i, l in enumerate(L) if i > start and l.startswith('## Lines checked and found consistent'))
for i in range(start, end):
    l = L[i]
    if l.strip() == '~~~~':
        if not infence:
            infence, buf = True, []
        else:
            infence = False
            if cur is not None and label is not None:
                (cur['old'] if label.startswith('OLD') else cur['new']).append(('\n'.join(buf), label))
        continue
    if infence:
        buf.append(l)
        continue
    m = HDR.match(l)
    if m:
        cur = dict(id=m.group(1), file=m.group(2), line=int(m.group(3)), line2=int(m.group(4)) if m.group(4) else None,
                   status=m.group(5), type=m.group(6), old=[], new=[], pos=i)
        rows.append(cur)
        label = None
        continue
    if re.match(r'^(OLD|NEW)\b.*:$', l):
        label = l
if infence:
    F('fence', 'unterminated fence in row region')
nfence = sum(1 for i in range(start, end) if L[i].strip() == '~~~~')
if nfence % 2:
    F('fence', 'odd number of fence lines')

# ---------- (a) counts, ids
ids = [r['id'] for r in rows]
exp = ['E-%02d' % n for n in range(1, 62) if n not in (10, 35)]
if len(rows) != 59:
    F('rowcount', f'{len(rows)} rows, need 59')
if len(set(ids)) != len(ids):
    F('dupid', str([k for k, v in collections.Counter(ids).items() if v > 1]))
if ids != exp:
    F('idorder', 'ids not E-01..E-61 minus 10,35 in order: diff ' + str(sorted(set(exp) ^ set(ids))))
st = lambda r: re.split(r' \(', r['status'])[0].strip()
sc = collections.Counter(st(r) for r in rows)
if sc.get('Apply now', 0) != 47 or sc.get('Hold', 0) != 12:
    F('statuscount', str(dict(sc)))
for m in re.finditer(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*', txt):
    if (int(m.group(1)), int(m.group(2))) != (47, 12):
        F('statustext', m.group(0))
for m in re.finditer(r'(\d+) rows in total', txt):
    if int(m.group(1)) != 59:
        F('totaltext', m.group(0))
mm = re.search(r'OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', txt)
fc = collections.Counter(r['file'] for r in rows)
if mm and tuple(map(int, mm.groups())) != (fc['OWNER-STEPS-realrun-v3.md'], fc['AGENT-SCOPE-DO-AND-DONT.md'], fc['DECISION-one-store.md']):
    F('filecounts', f'text {mm.groups()} vs rows {dict(fc)}')

# ---------- (b) index vs headers
idx = {}
for l in L:
    m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$', l)
    if m:
        idx[m.group(1)] = m.groups()
if sorted(idx) != sorted(ids):
    F('indexrows', 'index ids differ from header ids: ' + str(sorted(set(idx) ^ set(ids))))
for r in rows:
    x = idx.get(r['id'])
    if not x:
        continue
    ln = str(r['line']) + (f" (and {r['line2']})" if r['line2'] else '')
    if x[1] != r['file'] or x[2] != ln or x[3] != st(r) or x[6] != r['type']:
        F('indexmismatch', f"{r['id']} index {x[1:]} vs header {r['file']} {ln} {st(r)} {r['type']}")
    gm = re.search(r'gate (G\d)', r['status'])
    if st(r) == 'Hold' and (not gm or x[4] != gm.group(1)):
        F('indexgate', f"{r['id']} index gate {x[4]} vs {r['status']}")

# ---------- (c) OLD text once at stated line
files = {}
for r in rows:
    fn = r['file']
    if fn not in files:
        files[fn] = open(os.path.join(inputs_dir, fn), encoding='utf-8').read()
    full = files[fn]
    stated = {r['line']} | ({r['line2']} if r['line2'] else set())
    if not r['old']:
        F('noold', r['id'])
    for o, lab in r['old']:
        c = full.count(o)
        if c != 1:
            F('oldcount', f"{r['id']} OLD occurs {c}x")
        else:
            ln = full[:full.index(o)].count('\n') + 1
            if ln not in stated:
                F('oldline', f"{r['id']} OLD at line {ln}, stated {sorted(stated)}")

# ---------- (d) hold labels
for r in rows:
    held = st(r) == 'Hold'
    if held and not r['new']:
        F('holdnonew', r['id'])
    for t, lab in r['new']:
        if held and 'HOLD G' not in lab:
            F('holdlabel', f"{r['id']} NEW label lacks HOLD G: {lab[:50]}")
        if not held and 'HOLD' in lab:
            F('applylabel', f"{r['id']} apply row has HOLD label")
    if held and not re.search(r'gate G[1-5]', r['status']):
        F('holdgate', r['id'])

# ---------- (e) times
newall = [(r['id'], r['file'], t) for r in rows for t, _ in r['new']]
PAIR = re.compile(r'(\d{1,2}):(\d{2}) UTC = (\d{1,2}):(\d{2}) IST')
npairs = 0
body = txt  # whole file, pairs are checked everywhere (incl. Why lines)
for m in PAIR.finditer(body):
    npairs += 1
    u = int(m.group(1)) * 60 + int(m.group(2))
    i_ = int(m.group(3)) * 60 + int(m.group(4))
    if (u + 330) % 1440 != i_:
        F('istwrong', m.group(0))
for rid, fn, t in newall:
    for m in re.finditer(r'\b(\d{1,2}):(\d{2}) UTC\b', t):
        tail = t[m.end():m.end() + 30]
        head = t[max(0, m.start() - 12):m.start()]
        if not re.match(r' = \d{1,2}:\d{2}(:\d{2})? IST', tail) and not re.match(r' \(\d{1,2}:\d{2} IST\)', tail) and '(UTC' not in head:
            F('istmissing', f"{rid}: {t[max(0, m.start() - 25):m.end() + 20]!r}")
if re.search(r'18:19 UTC = (23:59|00:)', body) or re.search(r'18:19 UTC = 23:4[0-8]', body):
    F('tie1819', '18:19 UTC tied to a wrong IST time')
if re.search(r'18:29 UTC = 23:4', body):
    F('tie1829', '18:29 UTC tied to 23:4x IST')
for t in ('18:19 UTC = 23:49 IST', '18:29 UTC = 23:59 IST', '18:00 UTC = 23:30 IST', '17:49 UTC = 23:19 IST', '18:14 UTC = 23:44 IST'):
    if t not in body:
        F('missingtime', t + ' absent')
# latest start must be 18:00 everywhere
if re.search(r'18:0[1-9]|18:[1-5]\d UTC = 23:3[1-9] IST|23:34 IST|18:04', ''.join(t for _, _, t in newall)):
    F('oldstart', 'a NEW text has 18:04 / 23:34 or a start later than 18:00 paired with 23:3x')
newjoined = '\n'.join(t for _, _, t in newall)
for m in re.finditer(r'latest start', newjoined):
    seg = newjoined[m.start():m.end() + 160]
    pre = newjoined[max(0, m.start() - 160):m.start()]
    near = re.findall(r'\d{1,2}:\d{2} UTC', seg[:110] + pre[-60:])
    near = [x for x in near if x not in ('18:00 UTC',) and not x.startswith(('18:19', '18:29', '17:49', '18:14'))]
    if near:
        F('lateststart', 'latest start near a different time ' + str(near) + ': ' + seg[:70].replace('\n', ' '))
# bad: any "18:04" anywhere outside OLD and Why? check NEW only above; whole file count for info
# ---------- (f) weekday and date, Nov/Dec 2026
MON = {'Nov': 11, 'Dec': 12, 'Oct': 10}
WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
nwd = 0
for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.? (\d{1,2}) (Oct|Nov|Dec)(?: (\d{4}))?', body):
    nwd += 1
    y = int(m.group(4)) if m.group(4) else 2026
    try:
        d = datetime.date(y, MON[m.group(3)], int(m.group(2)))
    except ValueError:
        F('baddate', m.group(0))
        continue
    if WD[d.weekday()] != m.group(1) or y != 2026:
        F('weekday', f'{m.group(0)} is really {WD[d.weekday()]} {y}')
for m in re.finditer(r'\b(\d{1,2}) (Nov|Dec) 2026 \((Mon|Tue|Wed|Thu|Fri|Sat|Sun)', body):
    d = datetime.date(2026, MON[m.group(2)], int(m.group(1)))
    nwd += 1
    if WD[d.weekday()] != m.group(3):
        F('weekday', m.group(0))

# ---------- (g) owner text codes
own = [(r['id'], t) for r in rows if r['file'].startswith('OWNER') for t, _ in r['new']]
for rid, t in own:
    for pat, nm in ((r'\bE-\d+\b', 'E-code'), (r'\bQ-?\d+\b', 'Q-code'), (r'\bL-\d+\b', 'L-code'), (r'\bR-?\d{1,2}\b', 'R-code'),
                    (r'\bND[- ]?\d+', 'ND-code'), (r'\bEL-\d\b', 'EL-code'), (r'\bWP\d\b', 'WP-code'), (r'\bD\d{1,2}\b', 'D-code')):
        mm = re.search(pat, t)
        if mm:
            F('ownercode', f'{rid} {nm}: {t[max(0, mm.start() - 20):mm.end() + 10]!r}')

# ---------- (h) typing steps wait for "not looking"
for rid, t in [(r['id'], t) for r in rows for t, _ in r['new']]:
    for m in re.finditer(r'please stop looking', t):
        win = t[m.end():m.end() + 70]
        if 'not looking' not in win and not win.startswith('` and `you may look again`'):
            F('notlooking', f'{rid}: stop-looking not followed by the wait for not looking within 70 chars: {win[:70]!r}')
# sub-step a of E-09 must list the sub-steps that type a secret, and f,g,h must call the rule
r09 = next((r for r in rows if r['id'] == 'E-09'), None)
t09 = '\n'.join(t for t, _ in r09['new']) if r09 else ''
if '(sub-steps c, f, g and h)' not in t09:
    F('typingrule_scope', 'E-09 a does not list sub-steps c, f, g and h')
for sub in 'fgh':
    m = re.search(r'(?m)^   %s\. .*$' % sub, t09)
    if not m or not re.search(r'typing rule|not looking', m.group(0)):
        F('typingrule_sub', 'E-09 sub-step %s does not call the typing rule' % sub)
# the three parts of the rule in the one place that defines it
if not re.search(r'wait for its written reply `not looking`', txt):
    F('rule_a', 'typing rule definition lacks wait for its written reply not looking')
if 'write `you may look again`' not in txt:
    F('rule_a', 'typing rule lacks you may look again')

# ---------- (i) shred rules
r48 = next((r for r in rows if r['id'] == 'E-48'), None)
t48 = '\n'.join(t for t, _ in r48['new']) if r48 else ''
need48 = [
    ('realpath', 'realpath'), ('ls -l', "`ls -l '<path>'`"), ('shred -u', '`shred -u`'), ('dotdot rule', 'contains no `..`'),
    ('starts with /', 'starts with `/`'), ('take-10 prefix', '/x/take-10/key'), ('link rule', 'a link is a shortcut'),
    ('second column 1', 'number `1` in its second column'), ('shred done scope', 'EVERY file of (a), (b) and (c)'),
    ('never shred recording', 'Never shred a recording'), ('yes, no more takes', '`yes, no more takes`'),
    ('confirm sentence', 'Only a new message from you with the words `yes, no more takes` confirms it'),
    ('anything else counts more takes', 'Anything else, or no reply, counts as `more takes`'),
    ('whatever you answer', 'WHATEVER you answer'), ('not sure kills', '`not sure` never keeps it alive'),
    ('alarm1 revoke', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`'),
    ('alarm2 alive', 'named `is the secret key for the model still alive?`'),
    ('count only typed', 'count only when you type them yourself'),
    ('key steps A..K', None), ('in short', 'In short:'), ('no cancel', None),
]
for nm, needle in need48:
    if needle is None:
        continue
    if needle not in t48:
        F('e48_' + nm.replace(' ', '_'), 'E-48 NEW lacks ' + needle)
labels = re.findall(r'(?m)^   Key step ([A-Z])\.', t48)
if labels != list('ABCDEFGHIJK'):
    F('keysteps', 'key step letters ' + ''.join(labels))
if re.search(r'\bcancel', t48):
    F('e48_cancel', 'E-48 uses cancel')
if re.search(r'Alarm 2: a repeating alarm', t48) is None:
    F('alarm2', 'Alarm 2 repeating text missing')
# alarm names attach to the right alarm
for rid, fn, t in newall:
    for m in re.finditer(r'[Aa]larm 1[^`\n]*?named `([^`]+)`', t):
        if 'revoke' not in m.group(1):
            F('alarmswap', f'{rid} alarm 1 named {m.group(1)}')
    for m in re.finditer(r'[Aa]larm 2[^`\n]*?named `([^`]+)`', t):
        if 'alive' not in m.group(1):
            F('alarmswap', f'{rid} alarm 2 named {m.group(1)}')
# other shred places: any 'shred -u ~' or wildcard in NEW text
for rid, fn, t in newall:
    if re.search(r'shred -u [^\n]*[~*]', t):
        F('shredwild', f'{rid} shred with ~ or * in NEW text')
r43 = [r for r in rows if r['file'].startswith('OWNER') and 'delete the two secret files' in '\n'.join(t for t, _ in r['new'])]
for r in r43:
    tt = '\n'.join(t for t, _ in r['new'])
    if 'key step G' not in tt or 'Do not use the sign `*`' not in tt:
        F('item6shred', f"{r['id']} take-secrets step lacks key step G or no-star rule")
# no more takes steps elsewhere
for rid in ('E-55', 'E-57'):
    r = next((x for x in rows if x['id'] == rid), None)
    if r is None:
        F('missingrow', rid)

# ---------- (j) banned + secret shapes (counts only)
bt = open(os.path.join(os.path.dirname(os.path.abspath(edits_path)), '..', '..', '..', 'tests', 'test_no_reference_material.py'), encoding='utf-8').read() if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(edits_path)), '..', '..', '..', 'tests', 'test_no_reference_material.py')) else open(os.environ['BANNED_SRC'], encoding='utf-8').read()
bm = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
banned = ast.literal_eval('(' + bm.group(1) + ')')
bh = sum(1 for b in banned if b in txt)
if bh:
    F('banned', f'{bh} of {len(banned)} banned strings present')
pre = 'sk-' + 'ant-' + 'api03'
secs = [pre + r'-?[A-Za-z0-9_-]{8,}', r'\bsk-[A-Za-z0-9]{20,}', r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}',
        r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)\bpassword\s*[:=]\s*[^\s`]{6,}']
sh = 0
for p in secs:
    for m in re.finditer(p, txt):
        if m.group(0) == 'AKIAIOSFODNN7EXAMPLE':
            continue
        sh += 1
        F('secretshape', p[:14] + ' matched')
if '--apply' in sys.argv:
    outdir = sys.argv[sys.argv.index('--apply') + 1]
    os.makedirs(outdir, exist_ok=True)
    cp = {fn: t for fn, t in files.items()}
    matched = total = 0
    per = []
    for r in rows:
        if st(r) != 'Apply now':
            continue
        for k, (o, _) in enumerate(r['old']):
            total += 1
            if cp[r['file']].count(o) == 1:
                matched += 1
                nt = r['new'][min(k, len(r['new']) - 1)][0] if r['new'] else ''
                cp[r['file']] = cp[r['file']].replace(o, nt, 1)
            else:
                per.append(r['id'])
    for fn, t in cp.items():
        open(os.path.join(outdir, fn), 'w', encoding='utf-8').write(t)
    print('APPLY apply-now OLD texts', total, 'matched exactly once', matched, 'unmatched rows', per,
          'resulting lines', {fn: t.count(chr(10)) + 1 for fn, t in cp.items()})
if info:
    print('INFO rows', len(rows), 'apply', sc.get('Apply now'), 'hold', sc.get('Hold'), 'OLD blocks', sum(len(r['old']) for r in rows),
          'NEW blocks', sum(len(r['new']) for r in rows), 'UTC=IST pairs', npairs, 'weekday-date pairs', nwd,
          'banned hits', bh, 'of', len(banned), 'secret-shape hits', sh, 'index rows', len(idx))
print('FAILS', len(fails))
sys.exit(1 if fails else 0)

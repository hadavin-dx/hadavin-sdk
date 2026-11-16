# Independent checker for EDITS.md round 14. Own code; does not import verify14.py. Reads files; writes only stdout.
import re, ast, sys, os, collections, datetime
HERE = '/home/user/hadavin-sdk/handover/core-hardening/'

def parse(txt):
    lines = txt.split('\n'); rows = []; cur = None; inb = False; lab = None; buf = []
    hdr = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+?), type (.+)$')
    for ln in lines:
        if not inb:
            m = hdr.match(ln)
            if m:
                cur = dict(id=m[1], file=m[2], line=int(m[3]), line2=int(m[4]) if m[4] else None, status=m[5], type=m[6], old=[], new=[], labels=[], why=[])
                rows.append(cur); continue
            if ln.startswith('## '): cur = None
            if cur is not None and ln.startswith('Why:'): cur['why'].append(ln)
            if cur is not None and re.match(r'^(OLD|NEW)\b.*:$', ln): lab = ln
        if ln == '~~~~' and cur is not None:
            if not inb: inb = True; buf = []
            else:
                inb = False; b = '\n'.join(buf)
                if lab and lab.startswith('OLD'): cur['old'].append(b)
                else: cur['new'].append(b); cur['labels'].append(lab)
            continue
        if inb: buf.append(ln)
    return rows

def load_banned():
    bt = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
    m = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
    return ast.literal_eval('(' + m.group(1) + ')')

def check(txt, indir=HERE + 'inputs/', info=None, banned=None):
    fails = []
    F = lambda k, m: fails.append((k, m))
    I = info or (lambda *a: None)
    rows = parse(txt)
    st = lambda r: r['status'].split(' (')[0].strip()
    byid = {r['id']: r for r in rows}
    own = [r for r in rows if r['file'].startswith('OWNER')]
    # 1 rows, ids, counts
    exp = ['E-%02d' % n for n in range(1, 59) if n not in (10, 35)]
    ids = [r['id'] for r in rows]
    if len(rows) != 56: F('rowcount', f'{len(rows)} rows, expected 56')
    if len(set(ids)) != len(ids): F('ids-unique', 'duplicate ids ' + str([k for k, v in collections.Counter(ids).items() if v > 1]))
    if ids != exp: F('ids-order', 'ids differ/order: ' + str(sorted(set(exp) ^ set(ids))))
    cs = collections.Counter(st(r) for r in rows)
    m = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*', txt)
    if not m: F('counts', 'header counts not found')
    elif (int(m[1]), int(m[2])) != (cs['Apply now'], cs['Hold']): F('counts', f'header {m[1]}/{m[2]} vs computed {cs["Apply now"]}/{cs["Hold"]}')
    if (cs['Apply now'], cs['Hold']) != (44, 12) or sum(cs.values()) != len(rows) or len(cs) != 2: F('counts', f'computed {dict(cs)} want Apply now 44 Hold 12 only')
    mi = re.search(r'The Apply now ids \((\d+)\) are: ([E0-9, -]+)\.', txt)
    apids = [r['id'] for r in rows if st(r) == 'Apply now']
    if not mi or int(mi[1]) != len(apids) or [x.strip() for x in mi[2].split(',')] != apids: F('counts', 'Apply now id list differs')
    mh = re.search(r'the Hold rows are ([E0-9, -]+?)\)', txt)
    if not mh or [x.strip() for x in mh[1].split(',')] != [r['id'] for r in rows if st(r) == 'Hold']: F('counts', 'Hold id list differs')
    if not re.search(r'\b56 rows in total', txt): F('counts', '"56 rows in total" missing')
    # index table vs headers
    idx = {}
    for ln in txt.split('\n'):
        mm = re.match(r'^\| (E-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|', ln)
        if mm: idx[mm[1]] = [x.strip() for x in mm.groups()[1:]]
    for r in rows:
        x = idx.get(r['id'])
        if not x: F('index', 'no index row for ' + r['id']); continue
        if x[0] != r['file']: F('index', f"{r['id']} index file {x[0]} vs {r['file']}")
    # 2 old text once on stated line
    fcache = {}; nold = 0
    for r in rows:
        full = fcache.setdefault(r['file'], open(indir + r['file'], encoding='utf-8').read())
        for o in r['old']:
            nold += 1
            c = full.count(o)
            if c != 1: F('old', f"{r['id']} old text occurs {c} times in {r['file']}"); continue
            ln = full[:full.index(o)].count('\n') + 1; ln_end = ln + o.count('\n')
            stated = [r['line']] + ([r['line2']] if r['line2'] else [])
            if not any(ln <= s <= ln_end for s in stated): F('old', f"{r['id']} found at line {ln} stated {stated}")
    I('OLD blocks', nold)
    # 3 UTC/IST pairs
    mins = lambda s: int(s.split(':')[0]) * 60 + int(s.split(':')[1])
    pairs = list(re.finditer(r'\b(\d{1,2}:\d{2})(?::\d{2})? UTC (?:=|\() ?(?:about )?(\d{1,2}:\d{2})(?::\d{2})? IST', txt))
    for p in pairs:
        if (mins(p[1]) + 330) % 1440 != mins(p[2]): F('ist', f'{p[1]} UTC paired with {p[2]} IST')
    I('UTC=IST pairs', len(pairs))
    for r in rows:
        for t in r['new']:
            for mm in re.finditer(r'\b\d{1,2}:\d{2}(?::\d{2})? UTC\b(?! (?:=|\() ?(?:about )?\d{1,2}:\d{2})', t):
                F('ist-unpaired', f"{r['id']} NEW UTC time without IST: {t[max(0, mm.start()-30):mm.end()+15]!r}")
            for mm in re.finditer(r'(?<![:\d])(\d{1,2}:\d{2})(?::\d{2})? IST\b', t):
                if not re.search(r'UTC (?:=|\() ?(?:about )?$', t[max(0, mm.start()-20):mm.start()]): F('ist-unpaired', f"{r['id']} NEW IST time without UTC: {t[max(0, mm.start()-25):mm.end()]!r}")
    # 3b bare HH:MM in NEW blocks that is not followed by UTC/IST and is not the IST half of a pair
    for r in rows:
        for t in r['new']:
            for mm in re.finditer(r'(?<![\d:.])(\d{1,2}:\d{2})(?::\d{2})?(?![\d:])(?! (?:UTC|IST))', t):
                pre = t[max(0, mm.start()-12):mm.start()]
                if re.search(r'(?:=|\() ?(?:about )?$', pre): continue
                F('bare-time', f"{r['id']} NEW time without UTC/IST label: {t[max(0, mm.start()-30):mm.end()+20]!r}")
    # 4 weekday/date
    wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']; mo = {'Oct': 10, 'Nov': 11, 'Dec': 12}; nd = 0
    for mm in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Oct|Nov|Dec)[a-z]*(?: (\d{4}))?', txt):
        nd += 1; d = datetime.date(int(mm[4]) if mm[4] else 2026, mo[mm[3]], int(mm[2]))
        if wd[d.weekday()] != mm[1]: F('weekday', f'{mm[0]} is really {wd[d.weekday()]}')
    for mm in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{4})-(\d{2})-(\d{2})', txt):
        nd += 1; d = datetime.date(int(mm[2]), int(mm[3]), int(mm[4]))
        if wd[d.weekday()] != mm[1]: F('weekday', f'{mm[0]} is really {wd[d.weekday()]}')
    I('weekday/date pairs', nd)
    # required dates exist with right weekday
    for s in ('Mon 16 Nov', 'Wed 18 Nov', 'Mon 23 Nov'):
        if s not in txt: F('weekday', 'expected date string missing: ' + s)
    # 5 key end and money stop
    keyend = '18:19 UTC = 23:49 IST'; stop = '18:29 UTC = 23:59 IST'
    for rid in ('E-12', 'E-37', 'E-48', 'E-52', 'E-55', 'E-57', 'E-58'):
        if rid in byid and not any(keyend in t for t in byid[rid]['new']): F('keyend', f'{rid} NEW lacks {keyend}')
    for rid in ('E-12', 'E-48', 'E-55', 'E-58'):
        if rid in byid and not any(stop in t for t in byid[rid]['new']): F('keyend', f'{rid} NEW lacks money stop {stop}')
    for r in rows:
        for t in r['new']:
            for sent in re.split(r'(?<=[.;])\s+|\n', t):
                if re.search(r'(?i)\b(?:revoke|revoked|revoking|last time to revoke)\b', sent) and '18:29 UTC' in sent and keyend not in sent and not re.search(r'(?i)spending window|money stop|stop spending|stops? at|window ends|ends 10 minutes', sent):
                    F('keyend', f"{r['id']} revoke sentence names 18:29 UTC without 18:19: " + sent[:150])
                if re.search(r'(?i)(?:ends? by|last time to revoke|revoke[^.]{0,60}by)\b[^.]{0,40}18:29', sent): F('keyend', f"{r['id']} key end tied to 18:29: " + sent[:150])
    # any 18:19/23:49/18:29/23:59 in NEW blocks not in the proper pair
    for r in rows:
        for t in r['new']:
            for mm in re.finditer(r'18:19|23:49|18:29|23:59', t):
                ctx = t[max(0, mm.start()-12):mm.end()+14]
                if not re.search(r'18:19 UTC = 23:49 IST|18:29 UTC = 23:59 IST|= 23:49 IST|= 23:59 IST|18:19 UTC = 23:49|18:29 UTC = 23:59', t[max(0, mm.start()-12):mm.end()+14]): F('keyend', f"{r['id']} NEW stray key/stop time: " + ctx.replace('\n', ' '))
    # 18:14:40 only with label refusal limit
    for mm in re.finditer(r'18:14:40', txt):
        w = txt[max(0, mm.start()-260):mm.start()]
        if 'program refusal limit' not in w: F('label', '18:14:40 without "program refusal limit" within 260 chars before: ' + w[-80:].replace('\n', ' '))
    for mm in re.finditer(r'(?i)\blatest start\b(?! we plan)', txt): F('label', 'bare "latest start": ' + txt[max(0, mm.start()-30):mm.end()+30].replace('\n', ' '))
    for mm in re.finditer(r'(?i)(?<!program )\brefusal limit', txt): F('label', 'refusal limit without "program": ' + txt[max(0, mm.start()-30):mm.end()+30].replace('\n', ' '))
    for tm, want, other in (('18:04 UTC', 'latest start we plan', 'program refusal limit'), ('18:14 UTC', 'program refusal limit', 'latest start we plan')):
        for mm in re.finditer(re.escape(tm), txt):
            ctx = txt[max(0, mm.start()-60):mm.start()].split('\n')[-1]
            if ctx.rfind(other) > ctx.rfind(want): F('label', f'{tm} follows "{other}" instead of "{want}": ' + ctx[-90:])
    for mm in re.finditer(r'latest start we plan\W{0,6}(?:is |= |of |at )?(?:about )?\W{0,2}(\d{1,2}:\d{2}) UTC', txt):
        if mm[1] != '18:04': F('label', f'latest start we plan paired with {mm[1]}')
    for mm in re.finditer(r'program refusal limit\W{0,6}(?:is |= |of |at )?(?:about )?\W{0,2}(\d{1,2}:\d{2}) UTC', txt):
        if mm[1] != '18:14': F('label', f'program refusal limit paired with {mm[1]}')
    # 6 typing steps wait for 'not looking' (line level)
    for r in own:
        for t in r['new']:
            for line in t.split('\n'):
                for mm in re.finditer(r'[^.\n]*\b(?:type|paste)\b[^.\n]*\b(?:password|secret key|new key|app password)\b[^.\n]*', line, re.I):
                    seg = mm[0]
                    if re.search(r'(?i)never type|do not type|type nothing|not type|answer no|a text that you type|you type yourself|you type the password\)|chmod|^\s*\(?you type', seg): continue
                    if re.match(r'\s+[bcd]\. ', line) and r['id'] == 'E-09': continue
                    if 'not looking' not in line and 'typing rule' not in line: F('typing', f"{r['id']} typing line without not-looking/typing rule: {seg[:110]!r}")
    # typing rule parts in E-09: every sub-step that types a secret: c,f,g,h; f g h must say wait for not looking
    t09 = '\n'.join(byid['E-09']['new']) if 'E-09' in byid else ''
    for sub in ('f', 'g', 'h'):
        mm = re.search(r'(?m)^\s+%s\. .*$' % sub, t09)
        if not mm: F('typing', f'E-09 sub-step {sub} missing'); continue
        if 'not looking' not in mm[0] or 'please stop looking' not in mm[0]: F('typing', f'E-09 sub-step {sub} lacks please stop looking / not looking')
    ma = re.search(r'(?m)^\s+a\. .*$', t09)
    if not ma or 'wait for its written reply `not looking`' not in ma[0] or 'type nothing secret before you have the reply `not looking`' not in ma[0]: F('typing', 'E-09 step a lacks the wait rule')
    t48 = '\n'.join(byid['E-48']['new']) if 'E-48' in byid else ''
    m3g = re.search(r'(?m)^\s+3g\. .*$', t48)
    if not m3g or 'not looking' not in m3g[0] or 'you may look again' not in m3g[0]: F('typing', 'E-48 3g lacks not looking / you may look again')
    ms = re.search(r'(?m)^- \*\*The typing rule\*\*.*$', '\n'.join(byid['E-52']['new'])) if 'E-52' in byid else None
    if not ms or 'not looking' not in ms[0]: F('typing', 'E-52 typing rule line lacks not looking')
    for r in own:
        for t in r['new']:
            if re.search(r'unless the assistant tells you otherwise', t): F('phrase', f"{r['id']} NEW re-adds 'unless the assistant tells you otherwise'")
            if re.search(r'`key kept`', t): F('phrase', f"{r['id']} old phrase `key kept`")
    # 7 key revoked / shred done ordering (E-48)
    i1 = t48.find('When the key is revoked, shred every file'); i2 = t48.find('Until the key is revoked, keep its copies')
    if i1 < 0: F('order', 'E-48 lacks "When the key is revoked, shred every file"')
    if i2 < 0: F('order', 'E-48 lacks "Until the key is revoked, keep its copies"')
    if i1 >= 0 and i2 >= 0 and not i1 < i2: F('order', 'E-48 keep-copies sentence comes before shred-after-revoke sentence')
    if re.search(r'(?i)before the key is revoked, shred|shred[^.]{0,60}before (?:you )?revok', t48): F('order', 'E-48 says shred before revoke')
    if '`key revoked`' in t48 and '`shred done`' in t48:
        if t48.find('3f.') > t48.find('3h.'): F('order', '3f after 3h')
    for r in own:
        for t in r['new']:
            for sent in re.split(r'(?<=[.;])\s+|\n', t):
                if '`shred done`' in sent and re.search(r'(?i)(?:starts?|started|waits?|only after|after)', sent) and not re.search(r'key revoked|key not revoked', sent) and 'write `shred done`' not in sent:
                    F('order', f"{r['id']} sentence names `shred done` as a gate without `key revoked`: " + sent[:140])
    # shred rule
    for need, tag in (('It contains no `..`', 'path has no ..'), ('`realpath', 'realpath'), ('ls -l', 'ls -l check'), ('take folder `/x/take-1`', 'take-1 vs take-10')):
        if need not in t48: F('shred', 'E-48 shred rule lacks ' + tag)
    for r in rows:
        for t in r['new']:
            if re.search(r'shred -u (?:--|<path>|-- )', t) and not re.search(r'no `\.\.`', t): F('shred', f"{r['id']} NEW has shred -u without the no-'..' rule")
    # routes
    for need, tag in (('Route A:', 'route A'), ('Route B:', 'route B'), ('in route B the words `no more takes` count only after `cut accepted`', 'route B condition'), ('does nothing else until you answer', 'route unknown ask'), ('3j.', '3j'), ('WHATEVER you answer', 'WHATEVER')):
        if need not in t48: F('route', 'E-48 lacks ' + tag)
    def need(rid, subs, tag):
        t_ = '\n'.join(byid[rid]['new']) if rid in byid else ''
        for sb in subs:
            if sb not in t_: F('rowcontent', f'{rid} NEW lacks ({tag}): {sb!r}')
    need('E-09', ['please stop looking', 'wait for its written reply `not looking`', 'write `you may look again`'], 'not-looking step')
    need('E-55', ['`no more takes`', keyend, stop], 'trigger and deadlines')
    need('E-16', ['only after you have written `no more takes`'], 'clean-up trigger')
    need('E-57', [keyend, '`cut accepted`'], 'cut step')
    need('E-58', ['`key revoked`', '`key not revoked`', keyend, stop], 'send table')
    # 8 internal codes in owner-facing NEW text
    codes = ((r'\bE-\d\d\b', 'E-nn'), (r'\bND ?\d+[a-z0-9]*\b', 'ND'), (r'\bR\d{1,3}\b', 'R-number'), (r'\bL-[A-Z0-9]+(?:/[A-Z])?\b', 'L-id'), (r'\bL\d\b', 'L-row'), (r'\bQ\d+(?:\.\d+)?(?:\([a-z]\))?\b', 'Q-number'),
             (r'\bD\d{1,2}\b', 'D-item'), (r'\bG[1-5]\b', 'gate'), (r'\bEL-\d\b', 'EL'), (r'\bWP\d\b', 'WP'), (r'\bS9-\d+\b', 'S9'), (r'\bORD:', 'ORD:'), (r'\bORD-\d', 'ORD-n'))
    for r in own:
        for t in r['new']:
            for pat, nm in codes:
                for mm in re.finditer(pat, t): F('codes', f"{r['id']} owner NEW has {nm}: {t[max(0, mm.start()-25):mm.end()+15]!r}")
    # 9 hold labels
    for r in rows:
        held = st(r) == 'Hold'
        for lab in r['labels']:
            if held and 'HOLD G' not in lab: F('hold', f"{r['id']} hold row NEW block without HOLD label")
            if not held and 'HOLD G' in lab: F('hold', f"{r['id']} non-hold row with HOLD label")
    # 10 banned (counts) and secrets
    if banned is None: banned = load_banned()
    hits = sum(1 for b in banned if b in txt)
    I('banned found (count only)', hits, 'of', len(banned))
    if hits: F('banned', f'{hits} banned strings present (not printed)')
    sec = [r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9_-]{20,}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[\'"]?[A-Za-z0-9/+_-]{12,}',
           r'\beyJ[A-Za-z0-9_-]{15,}\.', r'\b[0-9a-f]{40,}\b', r'\bAIza[0-9A-Za-z_-]{30,}', r'[A-Za-z0-9._%+-]+@(?!example\.com\b)[A-Za-z0-9.-]+\.[a-z]{2,}']
    for p in sec:
        for mm in re.finditer(p, txt):
            if mm[0] != 'AKIAIOSFODNN7EXAMPLE': F('secret', f'secret-shaped match /{p[:22]}/ len {len(mm[0])}')
    return fails, rows

if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else HERE + 'steps-edits/EDITS.md'
    f, rows = check(open(p, encoding='utf-8').read(), info=lambda *a: print('INFO', *a))
    print('FAILS', len(f)); print(dict(collections.Counter(k for k, _ in f)))
    for k, m in f: print('FAIL', k, '|', m[:300])

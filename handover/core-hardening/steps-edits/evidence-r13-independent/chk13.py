# Independent checker for EDITS.md round 13. Records only; reads files, writes nothing except stdout.
import re, ast, sys, os, collections, datetime
HERE = '/home/user/hadavin-sdk/handover/core-hardening/'
def parse(txt):
    lines = txt.split('\n'); rows = []; cur = None; inb = False; lab = None; buf = []
    hdr = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+?), type (.+)$')
    for i, ln in enumerate(lines):
        if not inb:
            m = hdr.match(ln)
            if m:
                cur = dict(id=m[1], file=m[2], line=int(m[3]), line2=int(m[4]) if m[4] else None, status=m[5], type=m[6], old=[], new=[], labels=[]); rows.append(cur); continue
            if ln.startswith('## '): cur = None
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
def check(path, indir=HERE + 'inputs/', info=None):
    fails = []
    def F(k, m): fails.append((k, m))
    I = info if info is not None else (lambda *a: None)
    txt = open(path, encoding='utf-8').read(); rows = parse(txt)
    st = lambda r: r['status'].split(' (')[0].strip()
    # 1 rows, ids
    exp = ['E-%02d' % n for n in range(1, 59) if n not in (10, 35)]
    ids = [r['id'] for r in rows]
    if len(rows) != 56: F('rowcount', f'{len(rows)} rows, expected 56')
    if len(set(ids)) != len(ids): F('ids-unique', 'duplicate ids ' + str([k for k, v in collections.Counter(ids).items() if v > 1]))
    if ids != exp: F('ids-order', 'ids differ from E-01..E-58 without E-10,E-35: ' + str(sorted(set(exp) ^ set(ids))) + ('' if sorted(ids) != sorted(exp) else ' (order)'))
    # 2 counts
    cs = collections.Counter(st(r) for r in rows)
    m = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*', txt)
    if not m: F('counts', 'header counts not found')
    else:
        if (int(m[1]), int(m[2])) != (cs['Apply now'], cs['Hold']): F('counts', f'header {m[1]}/{m[2]} vs computed {cs["Apply now"]}/{cs["Hold"]}')
    if cs['Apply now'] != 44 or cs['Hold'] != 12: F('counts', f'computed Apply now {cs["Apply now"]} Hold {cs["Hold"]} (want 44 and 12)')
    mi = re.search(r'The Apply now ids \((\d+)\) are: ([E0-9, -]+)\.', txt)
    apids = [r['id'] for r in rows if st(r) == 'Apply now']
    if not mi or int(mi[1]) != len(apids) or [x.strip() for x in mi[2].split(',')] != apids: F('counts', 'Apply now id list in header differs from rows')
    mh = re.search(r'the Hold rows are ([E0-9, -]+?)\)', txt)
    if not mh or [x.strip() for x in mh[1].split(',')] != [r['id'] for r in rows if st(r) == 'Hold']: F('counts', 'Hold id list in header differs from rows')
    if not re.search(r'\b56 rows in total', txt): F('counts', '"56 rows in total" missing')
    # 3 old text once on stated line
    fcache = {}
    old_fail = []; nold = 0
    for r in rows:
        try:
            full = fcache.setdefault(r['file'], open(indir + r['file'], encoding='utf-8').read())
        except Exception as e:
            F('old', f"{r['id']} input file missing {r['file']}"); continue
        for o in r['old']:
            nold += 1
            c = full.count(o)
            if c != 1: old_fail.append(f"{r['id']} count {c}"); continue
            ln = full[:full.index(o)].count('\n') + 1
            ln_end = ln + o.count('\n')
            stated = [r['line']] + ([r['line2']] if r['line2'] else [])
            if ln not in stated and not any(ln <= s <= ln_end for s in stated): old_fail.append(f"{r['id']} found at line {ln} stated {stated}")
    for x in old_fail: F('old', x)
    I('old texts checked', nold, 'failures', len(old_fail))
    # 4 UTC/IST pairs, whole file
    def mins(s): h, mm = s.split(':'); return int(h) * 60 + int(mm)
    pairs = list(re.finditer(r'\b(\d{1,2}:\d{2}) UTC (?:=|\() ?(?:about )?(\d{1,2}:\d{2}) IST', txt))
    for p in pairs:
        if (mins(p[1]) + 330) % 1440 != mins(p[2]): F('ist', f'{p[1]} UTC paired with {p[2]} IST')
    I('UTC/IST pairs', len(pairs))
    # NEW text: every UTC time must be paired
    for r in rows:
        for t in r['new']:
            for mm in re.finditer(r'\b\d{1,2}:\d{2} UTC\b(?! (?:=|\() ?(?:about )?\d{1,2}:\d{2} IST)', t):
                F('ist-unpaired', f"{r['id']} NEW has UTC time without IST: {t[max(0,mm.start()-30):mm.end()+15]!r}")
        for t in r['new']:
            for mm in re.finditer(r'(?<![:\d])(\d{1,2}:\d{2}) IST\b(?<!= )', t):
                before = t[max(0, mm.start()-20):mm.start()]
                if not re.search(r'UTC (?:=|\() ?(?:about )?$', before): F('ist-unpaired', f"{r['id']} NEW has IST time without UTC: {t[max(0,mm.start()-25):mm.end()]!r}")
    # weekday/date
    wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    mo = {'Nov': 11, 'Dec': 12, 'Oct': 10}
    nd = 0
    for mm in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Oct|Nov|Dec)(?: (\d{4}))?', txt):
        nd += 1; y = int(mm[4]) if mm[4] else 2026
        d = datetime.date(y, mo[mm[3]], int(mm[2]))
        if wd[d.weekday()] != mm[1]: F('weekday', f'{mm[0]} is really {wd[d.weekday()]}')
    for mm in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', txt):
        pass
    I('weekday/date pairs', nd)
    # 5 labels
    for mm in re.finditer(r'(?i)\blatest start\b(?! we plan)', txt): F('label', 'old single label "latest start" without "we plan": ' + txt[max(0, mm.start()-40):mm.end()+30].replace('\n', ' '))
    for mm in re.finditer(r'(?i)(?<!program )\brefusal limit', txt): F('label', 'refusal limit without "program": ' + txt[max(0, mm.start()-40):mm.end()+30].replace('\n', ' '))
    n_plan = n_lim = 0
    for mm in re.finditer(r'latest start we plan\W{0,6}(?:is |= |of |at )?(?:about )?\W{0,2}(\d{1,2}:\d{2}) UTC = (\d{1,2}:\d{2}) IST', txt):
        n_plan += 1
        if (mm[1], mm[2]) != ('18:04', '23:34'): F('label', f'latest start we plan paired with {mm[1]} UTC = {mm[2]} IST')
    for mm in re.finditer(r'program refusal limit\W{0,6}(?:is |= |of |at )?(?:about )?\W{0,2}(\d{1,2}:\d{2}) UTC = (\d{1,2}:\d{2}) IST', txt):
        n_lim += 1
        if (mm[1], mm[2]) != ('18:14', '23:44'): F('label', f'program refusal limit paired with {mm[1]} UTC = {mm[2]} IST')
    I('label+time same-phrase pairs', n_plan, n_lim)
    # reverse: each 18:04 / 18:14 time: the nearest label before it (same paragraph, 120 chars) must be right one
    for tm, want, other in (('18:04 UTC', 'latest start we plan', 'program refusal limit'), ('18:14 UTC', 'program refusal limit', 'latest start we plan')):
        for mm in re.finditer(re.escape(tm), txt):
            ctx = txt[max(0, mm.start()-45):mm.start()].split('\n')[-1]
            a, b = ctx.rfind(want), ctx.rfind(other)
            if b > a: F('label', f'{tm} follows "{other}" not "{want}": ' + ctx[-90:])
    # every NEW block that mentions a UTC time 18:04/18:14 must have the label; rows that use the labels
    for r in rows:
        for t in r['new']:
            if re.search(r'18:04 UTC', t) and 'latest start we plan' not in t: F('label', f"{r['id']} NEW has 18:04 UTC without the label 'latest start we plan'")
            if re.search(r'18:14 UTC', t) and 'program refusal limit' not in t: F('label', f"{r['id']} NEW has 18:14 UTC without the label 'program refusal limit'")
    # 6 key end
    key_rows = [r for r in rows if r['file'].startswith('OWNER') and any(re.search(r'revoke', t) and re.search(r'secret key|model key|key for the model', t) for t in r['new'])]
    I('rows with key revoke text', [r['id'] for r in key_rows])
    for r in key_rows:
        for t in r['new']:
            if re.search(r'revoke', t) and re.search(r'secret key|model key|key for the model', t) and '18:19 UTC = 23:49 IST' not in t and r['id'] in ('E-12', 'E-37', 'E-48', 'E-55', 'E-57', 'E-58'):
                F('keyend', f"{r['id']} NEW mentions key revoke but lacks '18:19 UTC = 23:49 IST'")
    byid = {r['id']: r for r in rows}
    for rid in ('E-12', 'E-37', 'E-48', 'E-55', 'E-57', 'E-58'):
        if rid in byid and not any('18:19 UTC = 23:49 IST' in t for t in byid[rid]['new']): F('keyend', f'{rid} lacks key end 18:19 UTC = 23:49 IST')
    for r in rows:
        for t in r['new']:
            for sent in re.split(r'(?<=[.;:])\s+|\n', t):
                if re.search(r'\b(?:revoke|revoked|revoking)\b[^;]*\b(?:secret )?key\b|\bkey\b[^;]*\b(?:revoke|revoked|ends by)\b', sent) and '18:29 UTC' in sent and '18:19 UTC' not in sent:
                    F('keyend', f"{r['id']} NEW key revoke sentence names 18:29 UTC without 18:19: " + sent[:140])
    # 7 steps that must exist (content checks used by mutations): not-looking step, routes A and B, shred path
    own = [r for r in rows if r['file'].startswith('OWNER')]
    ownnew = '\n'.join(t for r in own for t in r['new'])
    for need, msg in (('not looking', 'not looking step'), ('please stop looking', 'please stop looking reply'), ('you may look again', 'you may look again reply'),
                      ('no more takes', 'no more takes reply'), ('cut accepted', 'route B reply'), ('shred -u', 'shred path'), ('Route A', 'route A'), ('Route B', 'route B')):
        if need not in txt: F('content', 'missing ' + msg)
    t48 = '\n'.join(byid['E-48']['new']) if 'E-48' in byid else ''
    for need, msg in (('Route A:', 'E-48 route A'), ('Route B (recommended):', 'E-48 route B'), ('not looking', 'E-48 not-looking step')):
        if need not in t48 and not (need == 'not looking' and any('not looking' in '\n'.join(byid[x]['new']) for x in ('E-09','E-52') if x in byid)): F('content', 'E-48/E-55/E-57 lack ' + msg)
    # shred must come with the no-.. rule: any NEW block with shred -u must also say the path has no ".." / must not contain ..
    for r in rows:
        for t in r['new']:
            if 'shred -u <path>' in t and not re.search(r'no (?:`\.\.`|"\.\."|\.\.)|\bnot (?:contain|include|have)[^.]{0,30}`?\.\.`?|\.\.[^.\n]{0,40}(?:never|not allowed|refuse|stop)|no `\.\.`', t):
                F('shred', f"{r['id']} NEW block has shred -u without the no-'..' path rule")
    # 8 reply phrases
    phr = collections.defaultdict(list)
    for r in own:
        for t in r['new']:
            for mm in re.finditer(r'`([^`\n]{2,80})`', t):
                p = mm[1]
                if re.search(r'[/\\<>~$=()*]|\.\w{1,5}\b|^\d|--|^-', p) or p.startswith('Yes, ') is False and len(p.split()) > 6: continue
                phr[p].append((r['id'], t[max(0, mm.start()-110):mm.end()+110].replace('\n', ' ')))
    ctxreq = {'cut accepted': r'\bcut\b', 'no more takes': r'take', 'key revoked': r'revoke', 'key not revoked': r'revoke', 'please stop looking': r'look', 'you may look again': r'look', 'not looking': r'look',
              'tested': r'crash check', 'untested': r'crash check', 'same key': r'n8n|key', 'different key': r'key', 'no, other things use it': r'secret key|key', 'end': r'take|pause|script'}
    for p_, lst in phr.items():
        if p_ in ctxreq:
            for rid_, c_ in lst:
                if not re.search(ctxreq[p_], c_): F('phrase', f'{rid_} phrase `{p_}` used without its context word /{ctxreq[p_]}/: {c_[60:200]}')
    # a reply phrase may not be offered for the other route's act: `cut accepted` must never be tied to "no more takes" as its meaning
    for r in own:
        for t in r['new']:
            if re.search(r'`cut accepted`\s+(?:means|is the same as|counts as)[^.]{0,40}no more takes|`no more takes`\s+(?:means|is the same as|counts as)[^.]{0,40}cut accepted', t): F('phrase', f"{r['id']} one phrase defined as the other")
            if re.search(r'`key kept`', t): F('phrase', f"{r['id']} uses old phrase `key kept`")
            if re.search(r'`(?:key revoked|key not revoked)`', t) and re.search(r'`(?:key revoked|key not revoked)`[^.]{0,60}(?:means|counts as)[^.]{0,60}(?:cut|take is over)', t): F('phrase', f"{r['id']} key phrase given a second meaning")
    # reply groups: Reply `a`, `b` or `c`
    grp = collections.defaultdict(set)
    for r in own:
        for t in r['new']:
            for mm in re.finditer(r'[Rr]eply (?:with exactly )?((?:`[^`]+`(?:, | or )?)+)', t):
                g = tuple(re.findall(r'`([^`]+)`', mm[1])); grp[g].add(r['id'])
    I('REPLY GROUPS', {' | '.join(k): sorted(v) for k, v in grp.items()})
    seen = collections.defaultdict(list)
    for g in grp:
        for w in g: seen[w].append(g)
    I('PHRASES', {k: sorted(set(x[0] for x in v)) for k, v in phr.items()})
    # 9 internal codes in owner-facing NEW text
    codes = ((r'\bE-\d\d\b', 'E-nn'), (r'\bND ?\d+[a-z0-9]*\b', 'ND'), (r'\bR\d{1,3}\b', 'R-number'), (r'\bL-[A-Z0-9]+(?:/[A-Z])?\b', 'L-id'), (r'\bL\d\b', 'L-row'), (r'\bQ\d+(?:\.\d+)?(?:\([a-z]\))?\b', 'Q-number'),
             (r'\bD\d{1,2}\b', 'D-item'), (r'\bG[1-5]\b', 'gate'), (r'\bEL-\d\b', 'EL'), (r'\bWP\d\b', 'WP'), (r'\bS9-\d+\b', 'S9'), (r'\bUNVERIFIED\b', 'UNVERIFIED (flag word, info)'))
    for r in own:
        for t in r['new']:
            for pat, nm in codes:
                for mm in re.finditer(pat, t):
                    if nm.startswith('UNVERIFIED'): continue
                    F('codes', f"{r['id']} owner NEW text has {nm}: {t[max(0,mm.start()-25):mm.end()+15]!r}")
    # 10 banned (counts only) and secrets
    banned = load_banned(); hits = sum(1 for b in banned if b in txt)
    I('banned strings found (count only)', hits, 'of', len(banned))
    if hits: F('banned', f'{hits} banned strings present (not printed)')
    sec = [r'AKIA[0-9A-Z]{16}', r'sk-[A-Za-z0-9_-]{20,}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[\'"]?[A-Za-z0-9/+_-]{12,}',
           r'\beyJ[A-Za-z0-9_-]{15,}\.', r'\b[0-9a-f]{40,}\b', r'\bAIza[0-9A-Za-z_-]{30,}', r'\b(?:pat-[a-z0-9]{2,4}-[0-9a-f-]{20,})', r'[A-Za-z0-9._%+-]+@(?!example\.com\b)[A-Za-z0-9.-]+\.[a-z]{2,}']
    for p in sec:
        for mm in re.finditer(p, txt):
            s = mm[0]
            if s == 'AKIAIOSFODNN7EXAMPLE': continue
            F('secret', f'secret-shaped string matches /{p[:25]}/ (len {len(s)})')
    return fails, rows, txt
if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else HERE + 'steps-edits/EDITS.md'
    def info(*a): print('INFO', *a)
    f, rows, txt = check(p, info=info)
    print('FAILS', len(f))
    c = collections.Counter(k for k, _ in f); print(dict(c))
    for k, m in f: print('FAIL', k, '|', m[:300])

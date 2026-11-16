"""Independent checker for owner sheet v30. Does not import check-v30.py, build-v30.py or newchecks-v30.py (it only RUNS build-v30.py as a program in a temp folder).
Usage: python3 -B -I indep30.py <steps-edits folder> [--json]. Reads only; writes only in a temp folder it creates. Prints PASS/FAIL/INFO lines."""
import re, sys, os, ast, hashlib, datetime as dt, tempfile, shutil, subprocess
D = sys.argv[1].rstrip('/') + '/'
OUT = []
def p(kind, code, msg): OUT.append('%s %s %s' % (kind, code, msg))
def rd(n):
    try: return open(D + n, encoding='utf-8').read()
    except Exception as e: p('FAIL', 'I00', 'cannot read %s: %s' % (n, type(e).__name__)); return ''
OW = {k: ['OWNER-SHEET-v30-%s.md' % k, 'OWNER-CARD-v30-%s.md' % k, 'OWNER-APPENDIX-v30-%s.md' % k] for k in 'AB'}
FILM = 'OWNER-FILM-PERSON-v30.md'; LEAD = ['LEAD-RELEASE-NOTE-v14.md', 'v30-OPEN-FOR-LEAD.md']
T = {n: rd(n) for n in sum(OW.values(), []) + [FILM] + LEAD}
OWNERPAGES = [n for n in T if n.startswith('OWNER-')]
# I01 word counts
wc = {n: len(t.split()) for n, t in T.items()}
for n in sorted(wc): p('INFO', 'I01', 'words %s = %d' % (n, wc[n]))
for k in 'AB':
    s, c, a = [wc[n] for n in OW[k]]
    p('INFO', 'I01', 'sheet %s: sheet+appendix+film = %d, sheet+card+appendix+film = %d' % (k, s + a + wc[FILM], s + c + a + wc[FILM]))
    if s > 6300: p('FAIL', 'I01', 'sheet %s %d words > 6300 (limit used by v29 independent check)' % (k, s))
    if s < 4000 or c < 500 or a < 500: p('FAIL', 'I01', 'page suspiciously short for %s' % k)
if wc[FILM] < 100: p('FAIL', 'I01', 'film page too short')
# I02 UTC/IST pairs, whole text, every page
rx_utc = re.compile(r'(?<![\d:])(\d\d):(\d\d)(?::(\d\d))? UTC\b'); rx_pair = re.compile(r' = (\d\d):(\d\d)(?::(\d\d))? IST')
npairs = 0; bad = 0
for n, t in T.items():
    for ln, line in enumerate(t.split('\n'), 1):
        for m in rx_utc.finditer(line):
            q = rx_pair.match(line, m.end())
            if not q: p('FAIL', 'I02', '%s:%d UTC with no IST pair: %r' % (n, ln, line[max(0, m.start() - 8):m.end() + 30])); bad += 1; continue
            npairs += 1
            u = int(m[1]) * 60 + int(m[2]); i = int(q[1]) * 60 + int(q[2])
            if (u + 330) % 1440 != i or (m[3] and q[3] and m[3] != q[3]): p('FAIL', 'I02', '%s:%d wrong IST %s -> %s' % (n, ln, m[0], q[0])); bad += 1
        for m in re.finditer(r'(?<![\d:])(\d\d):(\d\d)(?::\d\d)? IST', line):
            if ('UTC = ' + m[0]) not in line: p('FAIL', 'I02', '%s:%d IST with no UTC partner %s' % (n, ln, m[0])); bad += 1
p('INFO', 'I02', 'pairs checked %d, problems %d' % (npairs, bad))
for u, i in (('18:29', '23:59'), ('18:19', '23:49'), ('18:04', '23:34'), ('18:00', '23:30')):
    if (int(u[:2]) * 60 + int(u[3:]) + 330) % 1440 != int(i[:2]) * 60 + int(i[3:]): p('FAIL', 'I02', 'self test %s' % u)
    ow = {k: sum(T[n].count('%s UTC = %s IST' % (u, i)) for n in OW[k] + [FILM]) for k in 'AB'}
    ld = sum(T[n].count('%s UTC = %s IST' % (u, i)) for n in LEAD)
    if u == '18:29':
        for k in 'AB': p('PASS' if ow[k] else 'FAIL', 'I02', 'sheet %s owner pages hold "%s UTC = %s IST" x%d' % (k, u, i, ow[k]))
    else:
        p('PASS' if (ld or ow['A'] or ow['B']) else 'DEVIATION', 'I02', '"%s UTC = %s IST": owner pages A/B x%d/x%d, lead pages x%d%s' % (u, i, ow['A'], ow['B'], ld, '' if (ld or ow['A'] or ow['B']) else ' (ABSENT from every v30 page)'))
# I03 weekdays
MON = {m: i + 1 for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
nw = 0
for n, t in T.items():
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b(?: (\d{4}))?', t):
        nw += 1
        if dt.date(int(m[4] or 2026), MON[m[3]], int(m[2])).strftime('%a') != m[1]: p('FAIL', 'I03', '%s wrong weekday %r' % (n, m[0]))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b,? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b', t):
        nw += 1
        if dt.date(2026, MON[m[2]], int(m[3])).strftime('%a') != m[1]: p('FAIL', 'I03', '%s wrong weekday %r' % (n, m[0]))
    for m in re.finditer(r'\b(\d{1,2}) Nov (20\d\d)', t):
        if m[2] != '2026': p('FAIL', 'I03', '%s wrong year %r' % (n, m[0]))
p('INFO', 'I03', 'weekday-date mentions checked %d' % nw)
for d, wd in ((16, 'Mon'), (18, 'Wed'), (23, 'Mon'), (25, 'Wed')):
    if dt.date(2026, 11, d).strftime('%a') != wd: p('FAIL', 'I03', 'self test')
    full = '%s %d Nov 2026' % (wd, d)
    for k in 'AB':
        c = sum(T[n].count(full) for n in OW[k] + [FILM]); p('PASS' if c else 'FAIL', 'I03', 'sheet %s owner pages hold "%s" x%d' % (k, full, c))
    for n, t in T.items():
        for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) %d Nov' % d, t):
            if m[1] != wd: p('FAIL', 'I03', '%s: %d Nov named %s' % (n, d, m[1]))
# I04 placeholders
for k in 'AB':
    txt = '\n'.join(T[n] for n in OW[k] + [FILM])
    o = len(re.findall(r'\[OWNER FILLS: [^\]]+\]', txt)); l = len(re.findall(r'\[LEAD FILLS at re-pin: [^\]]+\]', txt))
    p('PASS' if o and l else 'FAIL', 'I04', 'sheet %s owner pages: [OWNER FILLS: ...] x%d, [LEAD FILLS at re-pin: ...] x%d' % (k, o, l))
    # malformed spellings
    for m in re.finditer(r'\[(OWNER|LEAD) FILLS[^\]]*\]', txt):
        if m[0] in ('[OWNER FILLS ...]', '[LEAD FILLS ...]'): continue          # the appendix explains the kinds of brackets with this short form
        if not (m[0].startswith('[OWNER FILLS: ') or m[0].startswith('[LEAD FILLS at re-pin: ')): p('INFO', 'I04', 'sheet %s other bracket text starting FILLS (prose, not a placeholder?): %r' % (k, m[0][:60]))
for n in LEAD:
    t = T[n]; p('INFO', 'I04', '%s: [OWNER FILLS: x%d, [LEAD FILLS at re-pin: x%d, literal spellings with "..." x%d' % (n, t.count('[OWNER FILLS: '), t.count('[LEAD FILLS at re-pin: '), t.count('[OWNER FILLS: ...]') + t.count('[LEAD FILLS at re-pin: ...]')))
# I05 'cancel the older key' in lead pages
for n in LEAD:
    t = T[n]
    for m in re.finditer(r'cancel the older key', t, re.I):
        pre = t[max(0, m.start() - 90):m.start()]; post = t[m.end():m.end() + 60]
        quoted = bool(re.search(r'["`“]\s*$', pre)) or bool(re.search(r'(lead|message)[^.]{0,40}(says?|sends?|tells?|writes?)[^.]{0,30}$', pre, re.I))
        p('FAIL' if quoted else 'INFO', 'I05', '%s: "cancel the older key" %s | ...%s[HIT]%s' % (n, 'LOOKS LIKE LEAD-MESSAGE WORDING' if quoted else 'descriptive mention', pre[-60:].replace('\n', ' '), post[:40].replace('\n', ' ')))
    for m in re.finditer(r'cancel(?:s|ling|led)? (?:your |the |that )?(?:older|old|previous) key', t, re.I):
        if m[0].lower() != 'cancel the older key': p('INFO', 'I05', '%s: variant "%s"' % (n, m[0]))
# I06 appendix pointers resolve
for k in 'AB':
    app = T[OW[k][2]]; parts = {int(m[1]): m.start() for m in re.finditer(r'^## Appendix part (\d+):', app, re.M)}
    bodies = {}
    ks = sorted(parts)
    for i, a in enumerate(ks): bodies[a] = app[parts[a]:parts[ks[i + 1]] if i + 1 < len(ks) else len(app)]
    p('INFO', 'I06', 'sheet %s appendix parts present: %s' % (k, ks))
    if ks != list(range(1, ks[-1] + 1)): p('FAIL', 'I06', 'sheet %s appendix part numbers not 1..n' % k)
    for pn, b in bodies.items():
        if len(b.split()) < 15: p('FAIL', 'I06', 'sheet %s appendix part %d is nearly empty' % (k, pn))
    refs = {}
    for src in OW[k] + [FILM]:
        for m in re.finditer(r'\((?:appendix|see appendix)(?: part)?s? (\d+(?:(?:, | and | to )\d+)*)\)|appendix part (\d+)|appendix (\d+)', T[src]):
            nums = re.findall(r'\d+', m[0]); 
            for x in nums: refs.setdefault((src, int(x)), 0); refs[(src, int(x))] += 1
    bad = [(s, x) for (s, x) in refs if x not in parts]
    for s, x in bad: p('FAIL', 'I06', 'sheet %s: %s points to appendix %d which does not exist' % (k, s, x))
    p('PASS' if not bad else 'FAIL', 'I06', 'sheet %s: %d distinct (page, part) pointers, %d unresolved; total pointer mentions %d' % (k, len(refs), len(bad), sum(refs.values())))
    # film page must not point into appendix (film person reads only film page)
    if re.search(r'appendix', T[FILM], re.I): p('INFO', 'I06', 'film page mentions the word appendix')
    # every part is pointed to by the sheet or card
    used = {x for (s, x) in refs if s != OW[k][2]}
    for pn in parts:
        if pn not in used: p('INFO', 'I06', 'sheet %s appendix part %d is not pointed to from sheet/card/film' % (k, pn))
    # pointers that name a number but the part title keyword check for "Appendix N" with capital in appendix self refs
    for m in re.finditer(r'(?:part|Part) (\d+)', app):
        if int(m[1]) not in parts and 'Appendix part' not in app[max(0, m.start() - 10):m.start()]: pass
# I07 rebuild into temp and compare with disk
tmp = tempfile.mkdtemp(prefix='indep30-')
try:
    for n in ('facts-v30.py', 'build-v30.py', 'OWNER-SHEET-v30-SOURCE.md', 'LEAD-RELEASE-NOTE-v14-SOURCE.md', 'v30-OPEN-FOR-LEAD-SOURCE.md'):
        shutil.copy(D + n, tmp + '/' + n)
    r = subprocess.run([sys.executable, '-B', '-I', tmp + '/build-v30.py', tmp], capture_output=True, text=True, timeout=300)
    p('INFO', 'I07', 'rebuild rc=%d stderr=%r' % (r.returncode, r.stderr[-120:]))
    if r.returncode: p('FAIL', 'I07', 'rebuild stopped')
    gen = [f for f in sorted(os.listdir(tmp)) if f.startswith(('OWNER-', 'LEAD-RELEASE-NOTE-v14.md', 'v30-OPEN-FOR-LEAD.md')) and 'SOURCE' not in f]
    exp = sorted(['OWNER-SHEET-v30-A.md', 'OWNER-SHEET-v30-B.md', 'OWNER-CARD-v30-A.md', 'OWNER-CARD-v30-B.md', 'OWNER-APPENDIX-v30-A.md', 'OWNER-APPENDIX-v30-B.md', FILM] + LEAD)
    if gen != exp: p('FAIL', 'I07', 'rebuilt file set %s differs from expected' % gen)
    for n in exp:
        a = hashlib.sha256(open(tmp + '/' + n, 'rb').read()).hexdigest() if os.path.exists(tmp + '/' + n) else 'MISSING'
        b = hashlib.sha256(open(D + n, 'rb').read()).hexdigest()
        p('PASS' if a == b else 'FAIL', 'I07', '%s rebuilt %s disk %s %s' % (n, a[:12], b[:12], 'equal' if a == b else 'DIFFERENT'))
finally: shutil.rmtree(tmp, ignore_errors=True)
# I08 secrets (patterns built from parts)
S = lambda *a: ''.join(a)
PATS = {
 'anthropic-shape': re.compile(S('sk', '-ant', '-api03', '-', r'[A-Za-z0-9_\-]{8,}')),
 'anthropic-prefix-any': re.compile(S('sk', '-ant', '-')),
 'sk-generic': re.compile(S('sk', '-', r'[A-Za-z0-9]{20,}')),
 'aws-key': re.compile(S('A', 'KIA', r'[0-9A-Z]{16}')),
 'github-token': re.compile(S('gh', r'[pousr]', '_', r'[A-Za-z0-9]{30,}')),
 'slack-token': re.compile(S('xo', r'x[abprs]', '-', r'[A-Za-z0-9-]{10,}')),
 'private-key': re.compile(S('-----BEGIN ', r'[A-Z ]*', 'PRIVATE KEY')),
 'jwt': re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}'),
 'long-hex-or-b64': re.compile(r'(?<![A-Za-z0-9/+_=-])[A-Za-z0-9+/_-]{40,}={0,2}(?![A-Za-z0-9/+_=-])'),
 'email': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
 'bearer': re.compile(r'(?i)bearer\s+[A-Za-z0-9._-]{20,}'),
 'hubspot-pat': re.compile(S('pa', 't-', r'[a-z]{2,4}', r'\d?-[0-9a-f]{8}-[0-9a-f]{4}')),
}
EXAMPLE = S('AKIA', 'IOSFODNN7', 'EXAMPLE')
cnt = {k: 0 for k in PATS}; hits = []
for n, t in T.items():
    for ln, line in enumerate(t.split('\n'), 1):
        for k, rx in PATS.items():
            for m in rx.finditer(line):
                v = m[0]
                if k == 'aws-key' and v == EXAMPLE: continue
                if k == 'email' and re.search(r'@example\.(com|org|net)$', v): continue
                if k == 'long-hex-or-b64' and (re.fullmatch(r'[a-z0-9_-]+', v) and '-' in v or v.count('/') > 0 and '.' in v): pass
                if k == 'email': p('INFO', 'I08', 'email-shaped text %s:%d is a masked example with a three-dot ellipsis? %s' % (n, ln, ('\u2026' in line[max(0, m.start() - 6):m.start()])))
                cnt[k] += 1; hits.append('%s:%d [%s] %s...(len %d)' % (n, ln, k, v[:4] + '*' * 4, len(v)))
for k, v in cnt.items(): p('PASS' if v == 0 else 'FAIL', 'I08', 'secret pattern %s: %d hit(s) outside the allowed example' % (k, v))
for h in hits[:40]: p('INFO', 'I08', 'hit ' + h)
# I09 banned strings (read at run time, counts only)
try:
    tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
    BANNED = None
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in nd.targets): BANNED = [e.value for e in nd.value.elts]
    p('INFO', 'I09', 'BANNED entries read: %d' % len(BANNED))
    tot = 0
    for n, t in T.items():
        c = sum(t.count(b) for b in BANNED)
        tot += c
        if c: p('FAIL', 'I09', '%s: %d banned-string hit(s)' % (n, c))
    # also the other v30 files
    extra = ['v30-CHANGES.md', 'OWNER-SHEET-v30-SOURCE.md', 'LEAD-RELEASE-NOTE-v14-SOURCE.md', 'v30-OPEN-FOR-LEAD-SOURCE.md', 'facts-v30.py', 'check-v30.py', 'build-v30.py', 'newchecks-v30.py', 'mut30.py', 'v30-fail-proof.py', 'pointers-v30.txt']
    for n in extra:
        try: t = open(D + n, encoding='utf-8').read()
        except Exception: p('INFO', 'I09', 'cannot read ' + n); continue
        c = sum(t.count(b) for b in BANNED)
        if c: p('FAIL', 'I09', '%s: %d banned-string hit(s) (not an owner page)' % (n, c))
        tot += c
    p('PASS' if tot == 0 else 'FAIL', 'I09', 'banned-string total hits over %d built + %d other files: %d (counts only; strings not printed)' % (len(T), len(extra), tot))
except Exception as e: p('FAIL', 'I09', 'could not read BANNED: %s' % type(e).__name__)
for l in OUT: print(l)
print('indep30: %d FAIL line(s), %d DEVIATION line(s)' % (sum(1 for l in OUT if l.startswith('FAIL')), sum(1 for l in OUT if l.startswith('DEVIATION'))))
sys.exit(1 if any(l.startswith('FAIL') for l in OUT) else 0)

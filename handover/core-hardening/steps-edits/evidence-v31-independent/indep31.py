"""indep31.py: OWN independent checker for the built v31 pages (does not read or reuse check-v31.py or newchecks-v31.py).
Usage: python3 -B -I indep31.py <folder> [--counts]   Prints one line per finding ('FINDING Ixx text'); exit 1 if any.
Banned strings are read from the repo test at run time; only counts are printed. Secret-shaped samples are built from parts in hostile31.py."""
import os, re, sys, ast, datetime as dt

TESTFILE = '/home/user/hadavin-sdk/tests/test_no_reference_material.py'
OWNER = lambda k: ['OWNER-SHEET-v31-%s.md' % k, 'OWNER-CARD-v31-%s.md' % k, 'OWNER-APPENDIX-v31-%s.md' % k]
FILM = 'OWNER-FILM-PERSON-v31.md'
LEAD = ['LEAD-RELEASE-NOTE-v15.md', 'v31-OPEN-FOR-LEAD.md']
IST = dt.timedelta(hours=5, minutes=30)
CAPS = {'OWNER-SHEET-v31-A.md': 6300, 'OWNER-SHEET-v31-B.md': 6300}


def banned():
    t = ast.parse(open(TESTFILE, encoding='utf-8').read())
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets):
            return [e.value for e in n.value.elts]
    return []


def check(D, verbose=False):
    D = D.rstrip('/') + '/'
    out = []
    def f(code, msg): out.append('FINDING %s %s' % (code, msg))
    def rd(n):
        try: return open(D + n, encoding='utf-8').read()
        except Exception: f('I00', 'cannot read ' + n); return ''
    T = {n: rd(n) for n in OWNER('A') + OWNER('B') + [FILM] + LEAD}
    OWNERPAGES = OWNER('A') + OWNER('B') + [FILM]
    # I01 word counts
    for n, c in CAPS.items():
        w = len(T[n].split())
        if w > c: f('I01', '%s has %d words, cap %d' % (n, w, c))
        if w < c * 0.7: f('I01', '%s only %d words (cut?)' % (n, w))
    for n in OWNERPAGES + LEAD:
        if len(T[n].split()) < 300: f('I01', '%s only %d words (cut?)' % (n, len(T[n].split())))
    # sheet-vs-sheet size sanity: B and A within 15 percent
    for a, b in (('OWNER-SHEET-v31-A.md', 'OWNER-SHEET-v31-B.md'), ('OWNER-CARD-v31-A.md', 'OWNER-CARD-v31-B.md'), ('OWNER-APPENDIX-v31-A.md', 'OWNER-APPENDIX-v31-B.md')):
        wa, wb = len(T[a].split()), len(T[b].split())
        if abs(wa - wb) > 0.15 * max(wa, wb): f('I01', '%s and %s differ by more than 15 percent (%d vs %d)' % (a, b, wa, wb))
    # I02 UTC/IST pairs, seconds included
    PAIR = re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2}))? ?UTC ?(?:=|/|\(|,)? ?(\d{1,2}):(\d{2})(?::(\d{2}))? ?IST')
    allpairs = {}
    for n, t in T.items():
        for m in PAIR.finditer(t):
            h1, m1, s1, h2, m2, s2 = m.groups()
            a = dt.timedelta(hours=int(h1), minutes=int(m1), seconds=int(s1 or 0)) + IST
            b = dt.timedelta(hours=int(h2), minutes=int(m2), seconds=int(s2 or 0))
            if (s1 is None) != (s2 is None): f('I02', '%s: seconds on one side only: %s' % (n, m.group(0)))
            if a.total_seconds() % 86400 != b.total_seconds() % 86400: f('I02', '%s: wrong pair %s' % (n, m.group(0)))
            allpairs.setdefault(n, set()).add('%02d:%02d%s' % (int(h1), int(m1), (':' + s1) if s1 else ''))
        # lone UTC or IST time with no partner
        for m in re.finditer(r'(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))? ?(UTC|IST)\b', t):
            tail = t[m.end():m.end() + 12]; head = t[max(0, m.start() - 16):m.start()]
            if m.group(4) == 'UTC' and not re.match(r'\s?(=|/|\(|,)?\s?\d{1,2}:\d{2}', tail): f('I02', '%s: UTC time without IST partner: %s' % (n, m.group(0)))
            if m.group(4) == 'IST' and not re.search(r'UTC\s?(=|/|\(|,)?\s?$', head): f('I02', '%s: IST time without UTC partner: %s' % (n, m.group(0)))
    need = {'18:29': '23:59', '18:19': '23:49', '18:09': '23:39', '15:00': '20:30'}
    for k in 'AB':
        whole = '\n'.join(T[n] for n in OWNER(k) + [FILM])
        for u, i in need.items():
            if u + ' UTC = ' + i + ' IST' not in whole: f('I02', 'sheet %s owner pages lack the pair %s UTC = %s IST' % (k, u, i))
        if '18:04 UTC = 23:34 IST' not in whole + '\n' + T[LEAD[0]]: f('I02', 'sheet %s: pair 18:04 UTC = 23:34 IST absent' % k)
    if '18:14:40 UTC = 23:44:40 IST' not in '\n'.join(T.values()): f('I02', 'pair with seconds 18:14:40 UTC = 23:44:40 IST absent from all pages')
    # I03 weekday-date pairs
    WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    MON = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    for n, t in T.items():
        for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?: (\d{4}))?', t):
            y = int(m.group(4) or 2026)
            try: d = dt.date(y, MON[m.group(3)], int(m.group(2)))
            except ValueError: f('I03', '%s: impossible date %s' % (n, m.group(0))); continue
            if WD[d.weekday()] != m.group(1): f('I03', '%s: %s is a %s' % (n, m.group(0), WD[d.weekday()]))
        for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (Nov|Oct|Dec)[a-z]* (\d{1,2})\b', t):
            d = dt.date(2026, MON[m.group(2)], int(m.group(3)))
            if WD[d.weekday()] != m.group(1): f('I03', '%s: %s is a %s' % (n, m.group(0), WD[d.weekday()]))
        for m in re.finditer(r'(\d{4})-(\d{2})-(\d{2})(?:T[\d:]+Z)?(?: \((Mon|Tue|Wed|Thu|Fri|Sat|Sun)\))?', t):
            if m.group(4):
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                if WD[d.weekday()] != m.group(4): f('I03', '%s: ISO date %s weekday wrong' % (n, m.group(0)))
    req = ['Mon 16 Nov 2026', 'Wed 18 Nov 2026', 'Sun 22 Nov 2026', 'Mon 23 Nov 2026', 'Wed 25 Nov 2026']
    for k in 'AB':
        whole = '\n'.join(T[n] for n in OWNER(k) + [FILM])
        for r in req:
            if r not in whole: f('I03', 'sheet %s owner pages lack %s' % (k, r))
    # I04 appendix pointers and step pointers resolve
    for k in 'AB':
        app = T['OWNER-APPENDIX-v31-%s.md' % k]
        parts = set(int(x) for x in re.findall(r'^## Appendix part (\d+):', app, re.M))
        if not parts or sorted(parts) != list(range(1, max(parts) + 1)): f('I04', 'appendix %s parts not 1..N in order: %s' % (k, sorted(parts)))
        for n in ('OWNER-SHEET-v31-%s.md' % k, 'OWNER-CARD-v31-%s.md' % k, 'OWNER-APPENDIX-v31-%s.md' % k, FILM):
            for m in re.finditer(r'\(?appendix (\d+)\)?', T[n]):
                if int(m.group(1)) not in parts: f('I04', '%s: pointer to appendix %s, which is not a part' % (n, m.group(1)))
            for m in re.finditer(r'appendix (\d+)((?:(?:, | and | to )\d+)+)', T[n]):
                for x in re.findall(r'\d+', m.group(2)):
                    if int(x) not in parts: f('I04', '%s: pointer to appendix %s, not a part' % (n, x))
        sh = T['OWNER-SHEET-v31-%s.md' % k]
        steps = set(); sec = None
        for line in sh.split('\n'):
            m = re.match(r'## (\d+)\.', line)
            if m: sec = int(m.group(1)); continue
            m = re.match(r'(\d+)\. ', line)
            if m and sec: steps.add('%d.%s' % (sec, m.group(1)))
        for n in ('OWNER-SHEET-v31-%s.md' % k, 'OWNER-CARD-v31-%s.md' % k, 'OWNER-APPENDIX-v31-%s.md' % k):
            for m in re.finditer(r'(?<![\d.$:/-])\b([5-9]\.\d{1,2})\b(?![.:]?\d)', T[n]):
                if m.group(1) not in steps: f('I04', '%s: step pointer %s does not exist in sheet %s' % (n, m.group(1), k))
        for m in re.finditer(r'card step (\d)\b', '\n'.join(T[n] for n in OWNER(k))):
            if not re.search(r'^%s\. ' % m.group(1), T['OWNER-CARD-v31-%s.md' % k], re.M): f('I04', 'card step %s does not exist on card %s' % (m.group(1), k))
        for m in re.finditer(r'\b([WL])(\d)\b', T['OWNER-SHEET-v31-%s.md' % k] + T['OWNER-APPENDIX-v31-%s.md' % k]):
            lim = 9 if m.group(1) == 'W' else 5
            if int(m.group(2)) > lim or int(m.group(2)) < 1: f('I04', 'label %s out of range %s' % (m.group(0), k))
        for lab in ['W%d' % i for i in range(1, 10)] + ['L%d' % i for i in range(1, 6)]:
            if not re.search(r'\b%s\b' % lab, T['OWNER-CARD-v31-%s.md' % k]): f('I04', 'card %s lacks label %s' % (k, lab))
        if 'OWNER-CARD-v31-%s.md' % k not in sh or 'OWNER-APPENDIX-v31-%s.md' % k not in sh and 'OWNER-APPENDIX' not in sh: pass
    # I05 absolute paths
    for n in OWNERPAGES:
        for m in re.finditer(r'(?<![\w.])(/(?:home|tmp|root|Users|var|etc|opt|usr)/[\w./-]+|[A-Za-z]:\\[\w\\.-]+)', T[n]):
            f('I05', '%s: absolute path %s' % (n, m.group(0)[:40]))
    # I06 internal codes in owner pages
    for n in OWNERPAGES:
        for m in re.finditer(r'\bQ\d+\b|\bORD:|\bDEC:|\bC\d{2,3}\b|\bL-\d+[A-Z]+\b|\bG\d{2}\b|\bR\d{3}\b|\bWP\d+|\bM-[A-Z]\d\b', T[n]):
            f('I06', '%s: internal code %s' % (n, m.group(0)))
    # I07 secrets
    pats = [(r'\bsk-[A-Za-z0-9_-]{10,}', 'sk-style key'), (r'AKIA[0-9A-Z]{16}', 'AWS key'), (r'gh[pousr]_[A-Za-z0-9]{20,}', 'github token'), (r'xox[abprs]-[A-Za-z0-9-]{10,}', 'slack token'),
            (r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}', 'JWT'), (r'-----BEGIN [A-Z ]*PRIVATE KEY', 'private key'), (r'(?i)bearer [A-Za-z0-9._~+/-]{20,}', 'bearer'),
            (r'(?<![A-Za-z0-9])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9])', 'long token'), (r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}', 'assignment')]
    for n, t in T.items():
        for p, label in pats:
            for m in re.finditer(p, t):
                if m.group(0) == 'AKIAIOSFODNN7EXAMPLE': continue
                if label == 'long token' and re.fullmatch(r'[a-z-]+', m.group(0)): continue
                f('I07', '%s: %s-shaped text (%d chars)' % (n, label, len(m.group(0))))
    # I08 banned strings: counts only
    bn = banned()
    if not bn: f('I08', 'could not read the banned list')
    for n, t in T.items():
        c = sum(t.lower().count(b.lower()) for b in bn)
        if c: f('I08', '%s: %d banned-string hit(s)' % (n, c))
    # I09 emails
    for n, t in T.items():
        for m in re.finditer(r'[\w.…*+-]+@[\w-]+(?:\.[\w-]+)+', t):
            local = m.group(0).split('@')[0]
            if '…' in local or '*' in local: continue
            f('I09', '%s: email-shaped text %s' % (n, re.sub(r'[A-Za-z0-9]', 'x', m.group(0))[:30]))
    # I10 content anchors (invariants read from the pages, not from check-v31.py)
    for k in 'AB':
        sh = T['OWNER-SHEET-v31-%s.md' % k]; cd = T['OWNER-CARD-v31-%s.md' % k]; ap = T['OWNER-APPENDIX-v31-%s.md' % k]
        whole = sh + cd + ap
        if '168 hours (7 days)' not in sh: f('I10', 'sheet %s lacks the 7-day rule wording "168 hours (7 days)"' % k)
        if 'less than 7 days ago' not in sh: f('I10', 'sheet %s lacks "less than 7 days ago"' % k)
        if 'alarm 3 at the cancel-by time' not in sh: f('I10', 'sheet %s lacks "alarm 3 at the cancel-by time"' % k)
        if 'cancel-by' not in cd: f('I10', 'card %s lacks cancel-by' % k)
        if whole.count('cancel-by') < 8: f('I10', 'sheet %s package has only %d cancel-by mentions' % (k, whole.count('cancel-by')))
        if 'model key cancelled' not in cd: f('I10', 'card %s lacks the word "model key cancelled"' % k)
        if 'cancel failed' not in cd: f('I10', 'card %s lacks "cancel failed"' % k)
        if 'UNVERIFIED' not in sh: f('I10', 'sheet %s lacks UNVERIFIED labels' % k)
        if 'This sheet is %s' % k not in sh and 'sheet %s' % k not in sh: f('I10', 'sheet %s does not name its own letter' % k)
        other = 'B' if k == 'A' else 'A'
        if re.search(r'\bsheet %s\b' % other, cd) and False: pass
        if '[OWNER FILLS' not in whole: f('I10', 'sheet %s lacks [OWNER FILLS placeholders' % k)
        if '[LEAD FILLS' not in whole: f('I10', 'sheet %s lacks [LEAD FILLS placeholders' % k)
        for bad in ('{{', '}}', '[[', ']]', '@@', '<<', '>>'):
            if bad in whole: f('I10', 'sheet %s package holds leftover marker %r' % (k, bad))
    for pl in re.findall(r'\[LEAD FILLS[^\]:]*', '\n'.join(T[n] for n in OWNER('A') + OWNER('B'))):
        if not pl.startswith('[LEAD FILLS at re-pin'): f('I10', 'odd LEAD FILLS spelling: %r' % pl)
    for pl in re.findall(r'\[OWNER FILL[^\]:]*', '\n'.join(T[n] for n in OWNER('A') + OWNER('B'))):
        if not pl.startswith('[OWNER FILLS'): f('I10', 'odd OWNER FILLS spelling: %r' % pl)
    note = T[LEAD[0]]
    if 'Money-safe default if you do not choose: A (warning beside it:' not in note: f('I10', 'lead note lacks the warning beside default A')
    if 'A will probably fail on Wed 18 Nov' not in note: f('I10', 'lead note lacks the "A will probably fail on Wed 18 Nov" warning')
    if re.search(r'(?i)the lead (sends|messages|tells)[^.\n]{0,60}"?cancel the older key', note): f('I10', 'lead page lets a lead message release the older-key cancel')
    for k in 'AB':
        sh = T['OWNER-SHEET-v31-%s.md' % k]
        if 'The lead sends the numbers message for one letter only' not in sh: f('I10', 'sheet %s lacks the one-letter rule' % k)
    # I11 money
    for k in 'AB':
        whole = '\n'.join(T[n] for n in OWNER(k))
        for want in ('0.27', '0.81', '13.21', '14.33', '860 s'):
            if want not in whole: f('I11', 'sheet %s lacks the number %s' % (k, want))
    for n, t in T.items():
        for m in re.finditer(r'\$\s?(\d+\.\d{2})\b|\b(\d+\.\d{2}) (?:US )?(?:dollars|USD)', t):
            v = m.group(1) or m.group(2)
            if v not in ('0.27', '0.81', '13.21', '12.40', '189.00', '0.10', '0.50', '3.00', '15.00', '2.00', '10.00', '4.00', '20.00', '100.00', '5.00', '0.30', '1.50', '27.00') and False: f('I11', '%s: amount %s' % (n, v))
    return out


if __name__ == '__main__':
    res = check(sys.argv[1])
    for l in res: print(l[:230])
    print('indep31: %d finding(s)' % len(res))
    sys.exit(1 if res else 0)

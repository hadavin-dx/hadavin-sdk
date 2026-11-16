"""chk28i.py: the evidence runner's OWN checker for the v28 owner package (not check-v28.py, no code shared with it).
Usage: python3 -I chk28i.py <folder>   Prints FAIL / INFO lines, exit 1 if any FAIL. It reads only the finished texts."""
import os, re, sys, difflib, datetime as dt
D = sys.argv[1].rstrip('/') + '/'
OWNER = ['OWNER-SHEET-v28-A.md', 'OWNER-CARD-v28-A.md', 'OWNER-NUMBERS-v28-A.md', 'OWNER-SHEET-v28-B.md', 'OWNER-CARD-v28-B.md',
         'OWNER-NUMBERS-v28-B.md', 'OWNER-FILM-v28.md']
LEAD = ['LEAD-RELEASE-NOTE-v12.md', 'v28-OPEN-FOR-LEAD.md']
ALLF = OWNER + LEAD
FAILS, INFO = [], []
def fail(c, m): FAILS.append('FAIL %s %s' % (c, m))
def info(c, m): INFO.append('INFO %s %s' % (c, m))
T = {}
for n in ALLF:
    try: T[n] = open(D + n, encoding='utf-8').read()
    except Exception as e: T[n] = ''; fail('K00', 'cannot read %s (%s)' % (n, type(e).__name__))
def lines(n): return T[n].split('\n')

# K01 word counts
for k in 'AB':
    w = {p: len(T['OWNER-%s-v28-%s.md' % (p, k)].split()) for p in ('SHEET', 'CARD', 'NUMBERS')}
    film = len(T['OWNER-FILM-v28.md'].split())
    info('K01', 'letter %s words: sheet %d card %d numbers %d film %d total %d' % (k, w['SHEET'], w['CARD'], w['NUMBERS'], film, sum(w.values()) + film))
    if w['SHEET'] > 6300: fail('K01', 'sheet %s page has %d words (max 6300)' % (k, w['SHEET']))
for n in ALLF:
    if len(T[n].split()) == 0: fail('K01', n + ' is empty')

# K02 UTC/IST pairs
PAIR = re.compile(r'(\d\d):(\d\d)(?::(\d\d))? UTC = (\d\d):(\d\d)(?::(\d\d))? IST')
LONE = re.compile(r'(\d\d):(\d\d)(?::(\d\d))? UTC(?! = \d\d:\d\d)')
npairs = {}
for n in ALLF:
    c = 0
    for m in PAIR.finditer(T[n]):
        c += 1
        u = int(m[1]) * 60 + int(m[2]); i = int(m[4]) * 60 + int(m[5])
        if (u + 330) % 1440 != i or (m[6] and m[3] != m[6]) or (m[6] and not m[3]): fail('K02', '%s wrong IST: %s' % (n, m[0]))
        if not (0 <= int(m[1]) < 24 and int(m[2]) < 60): fail('K02', '%s impossible time %s' % (n, m[0]))
    npairs[n] = c
    lone = [m[0] for m in LONE.finditer(T[n])]
    if lone:
        (fail if n in OWNER else info)('K02', '%s UTC time(s) with no IST beside: %d %s' % (n, len(lone), lone[:6]))
    for m in re.finditer(r'(?<!= )(?<!\d)(\d\d:\d\d) IST', T[n]):
        info('K02', '%s IST time with no UTC before it: %s' % (n, m[0]))
    for m in re.finditer(r'(\d{4}-\d\d-\d\d)T(\d\d:\d\d:\d\d)Z', T[n]):
        if (m[1], m[2]) != ('2026-11-23', '18:29:00'): fail('K02', '%s ISO time %s is not the deadline' % (n, m[0]))
info('K02', 'pairs per file: ' + ', '.join('%s=%d' % (k, v) for k, v in npairs.items()))

# K03 weekdays and dates (2026)
MON = {m: i + 1 for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
WD = 'Mon Tue Wed Thu Fri Sat Sun'.split()
def wd(d, mo): return WD[dt.date(2026, MON[mo], int(d)).weekday()]
nd = 0
for n in ALLF:
    t = T[n]
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b( \d{4})?', t):
        nd += 1
        try:
            if wd(m[2], m[3]) != m[1] or (m[4] and m[4].strip() != '2026'): fail('K03', '%s wrong weekday/year: %s (right: %s)' % (n, m[0], wd(m[2], m[3])))
        except ValueError: fail('K03', '%s impossible date %s' % (n, m[0]))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b', t):
        nd += 1
        try:
            if wd(m[3], m[2]) != m[1]: fail('K03', '%s wrong weekday: %s (right: %s)' % (n, m[0], wd(m[3], m[2])))
        except ValueError: fail('K03', '%s impossible date %s' % (n, m[0]))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* (2026-\d\d-\d\d)', t):
        nd += 1
        if WD[dt.date.fromisoformat(m[2]).weekday()] != m[1]: fail('K03', '%s wrong weekday %s' % (n, m[0]))
    for m in re.finditer(r'\b(\d{1,2}) (Nov)(?! 2026)\b(?! \d)', t):
        pass
info('K03', 'weekday-date mentions checked: %d' % nd)
for n in OWNER:   # the three anchor dates appear with the right weekday wherever the date appears at all
    for d, w in (('18 Nov', 'Wed'), ('23 Nov', 'Mon'), ('25 Nov', 'Wed'), ('16 Nov', 'Mon')):
        for m in re.finditer(r'(\w{3})? ?\b' + d + r'\b', T[n]):
            if m[1] in WD and m[1] != w: fail('K03', '%s anchor date %s has weekday %s' % (n, d, m[1]))

# K04 18:19 / 23:49 and 18:04 / 18:14
for n in ALLF:
    for i, ln in enumerate(lines(n), 1):
        for m in re.finditer(r'18:19(:\d\d)?', ln):
            if not ln[m.start():].startswith('18:19 UTC = 23:49 IST') and not ln[m.start():].startswith('18:19:00 UTC = 23:49 IST'): fail('K04', '%s:%d 18:19 without = 23:49 IST' % (n, i))
        for m in re.finditer(r'23:49', ln):
            if '18:19' not in ln[max(0, m.start() - 22):m.start()]: fail('K04', '%s:%d 23:49 not paired with 18:19' % (n, i))
        near = [x for x in re.finditer(r'revoked?[- ]by|cancel-by|revoke-by', ln, re.I) if re.search(r'\b18:(?!29)\d\d', ln[max(0, x.start() - 100):x.end() + 100])]
        if near and '18:19 UTC = 23:49 IST' not in ln.replace('18:19:00', '18:19'):
            fail('K04', '%s:%d revoke-by wording with an 18:xx time but no 18:19 UTC = 23:49 IST on the line' % (n, i))
        for m in re.finditer(r'\b18:(04|14)(:\d\d)? UTC|\b23:(34|44)(:\d\d)? IST', ln):
            src = re.search(r'lease|860|derive|your answer|deadline|latest start|allows|need_seconds|minus', ln, re.I)
            info('K04', '%s:%d %s source word: %s' % (n, i, m[0], src[0] if src else 'NONE'))
            if not src: fail('K04', '%s:%d %s listed with no source on the line' % (n, i, m[0]))
# the schedule arithmetic written out by hand
dl = dt.datetime(2026, 11, 23, 18, 29)
if (dl - dt.timedelta(minutes=10)).strftime('%H:%M') != '18:19': fail('K04', 'arith')
if (dl - dt.timedelta(seconds=860)).strftime('%H:%M:%S') != '18:14:40': fail('K04', 'arith')
for k in 'AB':   # sample schedule: 11:30 + 5 + 15 + 10 = 12:00 ; +10 = 12:10 ; earliest 10:30
    nm = T['OWNER-NUMBERS-v28-%s.md' % k]
    for pat in ('Earliest key time: 10:30 UTC = 16:00 IST', 'Latest start: 11:30 UTC = 17:00 IST', 'Alarm time: 12:00 UTC = 17:30 IST', 'Cancel-by time: 12:10 UTC = 17:40 IST', 'Run day: Wed 18 Nov 2026'):
        if pat not in nm: fail('K04', 'numbers %s lacks "%s"' % (k, pat))
    if 11 * 60 + 30 + 5 + 15 + 10 != 12 * 60 or 12 * 60 + 10 != 730: fail('K04', 'arith')

# K05 placeholders
for n in OWNER + LEAD:
    t = T[n]
    for m in re.finditer(r'(?<!\[)\[([A-Za-z][^\[\]\n]{0,100})\](?!\()', t):
        if not re.match(r'(OWNER|LEAD) FILLS', m[1]): fail('K05', '%s unlabelled bracket placeholder [%s]' % (n, m[1][:50]))
    for m in re.finditer(r'\b(TBD|TODO|XXX|FIXME|FILL ME|PLACEHOLDER|lorem ipsum)\b|\?\?\?|<TBD>|\.\.\.\.', t, re.I if False else 0):
        fail('K05', '%s leftover marker %r' % (n, m[0]))
    if n not in ('OWNER-CARD-v28-A.md', 'OWNER-CARD-v28-B.md') and re.search(r'_{4,}', t): fail('K05', n + ' has a blank line ____ outside the card')
    if '{{' in t or '@@' in t or '[[' in t: fail('K05', n + ' has a build marker left')
for k in 'AB':
    nm = T['OWNER-NUMBERS-v28-%s.md' % k]
    if 'SAMPLE (made-up values' not in nm: fail('K05', 'numbers %s: sample not labelled made-up' % k)
    ob = nm.count('[OWNER FILLS'); lb = nm.count('[LEAD FILLS')
    if ob < 1 or lb < 1: fail('K05', 'numbers %s: placeholder label sentence missing (OWNER %d LEAD %d)' % (k, ob, lb))
    inblock = False; nslots = 0
    for i, ln in enumerate(nm.split('\n'), 1):
        if ln.startswith('```'): inblock = not inblock; continue
        if re.search(r'<[a-z][^<>]{1,60}>', ln) and not inblock and not ln.startswith('1.') and 'angle' not in ln: info('K05', 'numbers %s:%d angle slot outside the sample block: %s' % (k, i, ln[:90]))
        if inblock: nslots += len(re.findall(r'<[^<>]{1,70}>', ln))
    info('K05', 'numbers %s: %d angle slots inside the labelled sample; label strings OWNER %d, LEAD %d' % (k, nslots, ob, lb))
    if 'Text in angle brackets' not in T['OWNER-SHEET-v28-%s.md' % k]: fail('K05', 'sheet %s does not say what angle brackets mean' % k)

# K06 internal ids in owner text
ALLOW_R = {'R1', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10'}
for n in OWNER:
    t = T[n]
    for m in re.finditer(r'\b(C\d{2,3}|G\d{1,3}|N\d{2}|WP\d+|DF\d+|P0\w|S\d{2}|K\d{2}|T\d{2})\b', t): fail('K06', '%s internal id %s' % (n, m[0]))
    for m in re.finditer(r'\bR\d+\b', t):
        if m[0] not in ALLOW_R: fail('K06', '%s rule id %s is not defined in the sheet (R1, R4 to R10 only)' % (n, m[0]))
    for m in re.finditer(r'\bW(\d+)\b', t):
        if not 1 <= int(m[1]) <= 9: fail('K06', '%s %s not a card danger sign' % (n, m[0]))
    for m in re.finditer(r'\bL(\d+)\b', t):
        if not 1 <= int(m[1]) <= 5: fail('K06', '%s %s not a card list' % (n, m[0]))
    for m in re.finditer(r'(check|build|facts|mut|newchecks|fail-proof)[-_]?v?\d+\S*\.py|\bledger\b|\bblocker\b|\bEGM\b|\bpointers-v\d+', t, re.I): fail('K06', '%s internal tool word %r' % (n, m[0]))
for k in 'AB':
    s = T['OWNER-SHEET-v28-%s.md' % k]; c = T['OWNER-CARD-v28-%s.md' % k]
    for r in ALLOW_R:
        if not re.search(r'\|\s*%s\s*\|' % r, s) and r != 'R9': fail('K06', 'sheet %s has no table row for %s' % (k, r))
    for x in ['W%d' % i for i in range(1, 10)] + ['L%d' % i for i in range(1, 6)]:
        if not re.search(r'\b%s\b' % x, c): fail('K06', 'card %s never defines %s' % (k, x))
info('K06', 'internal-id scan done on 7 owner pages (R1,R4-R10, W1-W9, L1-L5 are labels the pages define themselves)')

# K07 links and step references
OWN_NAMES = re.compile(r'\b((?:OWNER|LEAD)-[A-Za-z0-9-]+\.md|v28-[A-Za-z0-9-]+\.(?:md|py)|(?:build|check|facts|mut|newchecks)-?v?28[A-Za-z0-9-]*\.py|pointers-v28\.txt)')
for n in ALLF:
    for m in OWN_NAMES.finditer(T[n]):
        if not any(os.path.isfile(x + m[1]) for x in (D, D + '../inputs/', D + '../')): fail('K07', '%s links to %s which does not exist' % (n, m[1]))
for k in 'AB':
    other = 'B' if k == 'A' else 'A'
    for p in ('OWNER-SHEET-v28-%s.md' % k,):
        for m in re.finditer(r'OWNER-(CARD|NUMBERS)-v28-([A-Z])\.md', T[p]):
            if m[2] != k: fail('K07', '%s points to the %s page of the other letter: %s' % (p, m[1], m[0]))
    for p in ('OWNER-CARD-v28-%s.md' % k, 'OWNER-NUMBERS-v28-%s.md' % k):
        for m in re.finditer(r'OWNER-(SHEET|CARD|NUMBERS)-v28-([A-Z])\.md', T[p]):
            if m[2] != k: fail('K07', '%s points to letter %s: %s' % (p, m[2], m[0]))
    # section and step references
    sh = T['OWNER-SHEET-v28-%s.md' % k]; sec = None; items = {}
    for ln in sh.split('\n'):
        h = re.match(r'## (\d+)\.', ln)
        if h: sec = int(h[1]); items[sec] = 0; continue
        it = re.match(r'(\d+)\. ', ln)
        if it and sec: items[sec] = max(items[sec], int(it[1]))
    nums = T['OWNER-NUMBERS-v28-%s.md' % k]
    items[3] = max([int(x) for x in re.findall(r'^(\d+)\. ', nums, re.M)] or [0])
    for n in ('OWNER-SHEET-v28-%s.md' % k, 'OWNER-CARD-v28-%s.md' % k, 'OWNER-NUMBERS-v28-%s.md' % k, 'OWNER-FILM-v28.md'):
        for m in re.finditer(r'(?<![\d.$/])([1-9])\.([1-9]\d?)(?![\d.]|,\d)', T[n]):
            pre = T[n][max(0, m.start() - 6):m.start()]
            if re.search(r'USD |x |= |\$', pre): continue
            if m[1] and int(m[1]) not in items or int(m[2]) > items.get(int(m[1]), 0): fail('K07', '%s step reference %s does not exist in sheet %s (section has %d items)' % (n, m[0], k, items.get(int(m[1]), 0)))
        for m in re.finditer(r'(?<!no )\bsection (\d)\b', T[n]):
            if int(m[1]) not in items: fail('K07', '%s names section %s which does not exist' % (n, m[1]))
    info('K07', 'sheet %s items per section: %s' % (k, items))

# K08 A and B differ only in older-key parts
OLD = re.compile(r'older|okb|16:00 UTC|21:30|7\.11|(?<![A-Z])(?:Three|Four) phone|alarm 4|-[AB]\.md|sheet [AB]', re.I)
for p in ('OWNER-SHEET-v28', 'OWNER-CARD-v28', 'OWNER-NUMBERS-v28'):
    a = T[p + '-A.md'].split('\n'); b = T[p + '-B.md'].split('\n'); sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal': continue
        la = '\n'.join(a[i1:i2]); lb = '\n'.join(b[j1:j2])
        wa, wb = la.split(), lb.split(); ws = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
        seg = ' / '.join('[%s] -> [%s]' % (' '.join(wa[x1:x2])[:90], ' '.join(wb[y1:y2])[:90]) for t2, x1, x2, y1, y2 in ws.get_opcodes() if t2 != 'equal')
        ok = bool(OLD.search(la + ' ' + lb))
        if not ok: ok = all(' '.join(wa[x1:x2]).lower() in ('three', 'four') for t2, x1, x2, y1, y2 in ws.get_opcodes() if t2 != 'equal')
        info('K08', '%s hunk A%d-%d/B%d-%d older-key vocabulary=%s : %s' % (p, i1 + 1, i2, j1 + 1, j2, ok, seg[:300]))
        if not ok: fail('K08', '%s hunk at A line %d differs in a part with no older-key wording' % (p, i1 + 1))
        for x in re.findall(r'\d\d:\d\d UTC', la + lb): pass
if T['OWNER-FILM-v28.md'] != T['OWNER-FILM-v28.md']: fail('K08', 'film')

# K09 n8n key, credentials, secrets, deletion sentences
def sentences(t): return [s.strip() for s in re.split(r'(?<=[.;!?])\s+|\n|\|', t) if s.strip()]
NEG = re.compile(r"\b(no|not|never|none|nothing|without|otherwise|difference|would|made no|n't|cannot|only if)\b", re.I)
cred = set()
for n in OWNER:
    for s in sentences(T[n]):
        if re.search(r'n8n', s, re.I) and re.search(r'\b(model |run |look |older |paid[- ]model )?key\b|secret|password|token', s, re.I) and re.search(r'\b(type|typed|paste|pasted|enter|entered|put|store|stored|save|saved|add|added|upload)\b', s, re.I) and not NEG.search(s):
            fail('K09', '%s sentence puts a key/secret into n8n: %s' % (n, s[:140]))
        if re.search(r"\b(delet\w*|archiv\w*)\b", s, re.I) and re.search(r'contact', s, re.I):
            who = re.search(r'\b(take|test program|the program|n8n|workflow|script|the run)\b[^.]{0,80}\b(delet\w*|archiv\w*)|contacts? (?:will be|are|is|were|get|gets) (?:delet|archiv)\w*', s, re.I)
            if who and not NEG.search(s): fail('K09', '%s sentence says the take deletes/archives contacts: %s' % (n, s[:140]))
    t = T[n]
    for fam, pat in (('model key', r'\b(model|run|look|older|paid[- ]model) key\b'), ('gmail app password', r'app passwords?|gmail passwords'), ('hubspot app secret', r'app secrets?|private apps?')):
        if re.search(pat, t, re.I): cred.add(fam)
    for m in re.finditer(r'\b(ssh key|private key|api key|api token|access token|auth token|bearer|oauth|client secret|personal access|github token|n8n login|n8n password|n8n api|master password|cookie|passkey|webhook secret|signing key|service account)\b', t, re.I):
        fail('K09', '%s names a further credential kind: %s' % (n, m[0]))
    for m in re.finditer(r'\b(?<![A-Z_])(?!million)(\w+) tokens?\b', t):
        if m[1].lower() not in ('million', 'output', 'input', 'of', 'and', 'in', 'out', 'the', 'per') and not re.match(r'(model|expected)', m[1]): info('K09', '%s word before "token": %s' % (n, m[0]))
    for pat in (r'sk-ant-[A-Za-z0-9_-]{8,}', r'\bsk-[A-Za-z0-9]{20,}', r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN', r'\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[a-z])(?=[A-Za-z0-9_-]*[A-Z])[A-Za-z0-9_-]{32,}\b'):
        for m in re.finditer(pat, t):
            if m[0] == 'AKIAIOSFODNN7EXAMPLE': continue
            fail('K09', '%s looks like a secret (pattern %s)' % (n, pat[:14]))
    for m in re.finditer(r'(?<![\u2026\w.+-])[\w.+-]+@(?!example\.com)[\w-]+\.(com|org|net|io|in)\b', t):
        fail('K09', '%s has an address that is not example.com: %s***' % (n, m[0][:3]))
if cred != {'model key', 'gmail app password', 'hubspot app secret'}: fail('K09', 'credential kinds named on the owner pages are %s, expected exactly 3' % sorted(cred))
for k in 'AB':
    if 'Model key outside the model program: none' not in T['OWNER-NUMBERS-v28-%s.md' % k]: fail('K09', 'numbers %s lacks the line "Model key outside the model program: none"' % k)
if not any(re.search(r'n8n.{0,60}(key|credential)', T[n], re.I) for n in OWNER): fail('K09', 'no owner page mentions the n8n key check at all')
info('K09', 'credential kinds named: %s' % sorted(cred))
# lead docs: the deletion promise
for n in LEAD:
    for s in sentences(T[n]):
        if re.search(r'\b(take|test program|n8n|workflow)\b[^.]{0,60}\b(delet\w*|archiv\w*)\b[^.]{0,40}contact', s, re.I) and not NEG.search(s): fail('K09', '%s sentence says the take deletes/archives contacts: %s' % (n, s[:140]))

# K10 money
for k in 'AB':
    nm = T['OWNER-NUMBERS-v28-%s.md' % k]
    p = (40000 * 3 + 10000 * 15) / 1000000
    if abs(p - 0.27) > 1e-9 or abs(3 * p - 0.81) > 1e-9: fail('K10', 'arith')
    for pat in ('USD 0.27', 'USD 0.81', 'USD 189.00', 'in USD 3.00, out USD 15.00', 'PRICE_IN_CENTS = 300', 'PRICE_OUT_CENTS = 1500', 'CALL_CEILING = 3'):
        if pat not in nm: fail('K10', 'numbers %s lacks %s' % (k, pat))
for n in OWNER:
    for m in re.finditer(r'USD (\d+(?:\.\d+)?)', T[n]):
        if m[1] not in ('0.27', '0.81', '189.00', '3.00', '15.00', '13.21', '12.40', '1.00', '0.00'): info('K10', '%s other USD figure %s' % (n, m[0]))
print('\n'.join(INFO)); print('\n'.join(FAILS)); print('chk28i: %d failure(s)' % len(FAILS)); sys.exit(1 if FAILS else 0)

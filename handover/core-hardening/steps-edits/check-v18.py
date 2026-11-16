"""v18 form checks: reads text only, runs nothing else. Prints counts, never a banned word.
Proves FORM (ids, counts, order of terms, arithmetic of the invented examples, weekdays); it cannot prove a statement true."""
import ast, re, sys, datetime as dt
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'S': 'OWNER-SHEET-v18.md', 'N': 'LEAD-RELEASE-NOTE-v2.md', 'M': 'v18-MAP.md', 'O': 'v18-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
problems = []
def bad(msg): problems.append(msg); print('PROBLEM:', msg)
def ok(msg): print('ok:', msg)
S, Nn, M, O = T['S'], T['N'], T['M'], T['O']

# 1 counts
n = {k: len(t.splitlines()) for k, t in T.items()}
print('lines:', n)
if not 70 <= n['S'] <= 140: bad('sheet lines %d not in 70..140' % n['S'])
else: ok('sheet lines %d' % n['S'])
heads = re.findall(r'^## ', S, re.M)
print('sheet headings:', len(heads))
if len(heads) != 9: bad('sheet headings %d, expected 9' % len(heads))

# 2 rules defined once, referenced ones exist
defs = re.findall(r'^\| (R\d+) \|', S, re.M)
if defs != ['R%d' % i for i in range(1, 11)]: bad('rule ids defined: %s' % defs)
else: ok('R1..R10 each defined once')
for k, t in T.items():
    for r in set(re.findall(r'\bR(\d+)\b', t)):
        if not 1 <= int(r) <= 10: bad('%s refers to R%s' % (F[k], r))
for i in range(1, 11):
    outside = sum(len(re.findall(r'\bR%d\b' % i, t)) for t in T.values()) - 1
    if outside < 1: bad('R%d never referenced outside its definition' % i)
ok('rule references checked')
# gates
gdefs = re.findall(r'^\| (G\d+) \|', Nn, re.M)
want = ['G%d' % i for i in list(range(1, 16)) + list(range(17, 25))] + ['G16', 'G25', 'G26', 'G27', 'G28', 'G29']
if sorted(gdefs, key=lambda x: int(x[1:])) != ['G%d' % i for i in range(1, 30)] or len(set(gdefs)) != 29: bad('G ids defined: %s' % gdefs)
else: ok('G1..G29 each defined once')
sec = re.split(r'^### 1([abc])\.', Nn, flags=re.M)
parts = {sec[i]: sec[i + 1] for i in range(1, len(sec) - 1, 2)}
def ids(txt): return re.findall(r'^\| (G\d+) \|', txt, re.M)
if set(ids(parts.get('b', ''))) != {'G16', 'G25', 'G26'}: bad('gate group b wrong: %s' % ids(parts.get('b', '')))
if set(ids(parts.get('c', ''))) != {'G27', 'G28', 'G29'}: bad('gate group c wrong: %s' % ids(parts.get('c', '')))
if len(ids(parts.get('a', ''))) != 23 or 'G15' not in ids(parts.get('a', '')) or 'G16' in ids(parts.get('a', '')): bad('gate group a wrong')
ok('gate groups checked') if not any('gate group' in x for x in problems) else None
for k, t in T.items():
    for g in set(re.findall(r'\bG(\d+)\b', t)):
        if not 1 <= int(g) <= 29: bad('%s refers to G%s' % (F[k], g))
for s in set(re.findall(r'section (\d+)', S)):
    if not 1 <= int(s) <= 9: bad('sheet refers to section %s' % s)
nopen = len(re.findall(r'^\| \d+ \|', O, re.M))
for k in ('N', 'M'):
    for o in set(re.findall(r'\bOpen (\d+)\b', T[k])):
        if not 1 <= int(o) <= nopen: bad('%s refers to Open %s (only %d)' % (F[k], o, nopen))
print('open rows:', nopen)

# 3 rule key phrases once, only in the rule table
phr = ['you cancel only', 'secret-looking', 'does not enforce', 'Recording is ON only', 'FREEZE =', 'ONE cancel rule',
       'no closed gate', 'does not print the model settings figures', 'shares your Linux user', 'Hard end, in this order']
rows = [l for l in S.splitlines() if re.match(r'\| R\d+ \|', l)]
for p in phr:
    cnt = sum(t.lower().count(p.lower()) for t in (S, Nn, O))
    inrule = sum(l.lower().count(p.lower()) for l in rows)
    if cnt != 1 or inrule != 1: bad('phrase %r occurs %d times (in rule table %d)' % (p, cnt, inrule))
ok('rule phrases checked') if not any('phrase' in x for x in problems) else None
# window end text once in glossary (+ once in the typed yes line); not in the note
c = S.count('18:29 UTC = 23:59 IST')
if c != 2: bad('window end phrase in sheet %d times, expected 2 (glossary and yes line)' % c)
if Nn.count('18:29 UTC = 23:59 IST') > 1: bad('window end phrase repeated in note')
if S.count('15:00 UTC = 20:30 IST') != 1: bad('post-by time not exactly once in sheet')

# 4 glossary: first use is the bold definition
terms = ['lead', 'numbers message', 'clean-up message', 'run name', 'test people', 'take program', 'model program', 'model key', 'older key',
         'app passwords', 'take settings file', 'model settings file', 'contact id', 'notice', 'challenge', 'printed result', 'film pause',
         'window end', 'latest start', 'alarm time', 'cancel-by time', 'call ceiling', 'run total', 'usage page', 'throwaway accounts',
         'UNVERIFIED', 'WSL', 'n8n', 'take window']
for t in terms:
    m = re.search(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])', S, re.I)
    if not m: bad('term %r never used' % t); continue
    pre = S[max(0, m.start() - 2):m.start()]
    line = S[S.rfind('\n', 0, m.start()) + 1:S.find('\n', m.start())]
    # the word "lead" opens the glossary bullet; 'take window' is defined in the heading of section 7
    if pre != '**' and not (t == 'take window' and line.startswith('## 7.')) and not (t == 'UNVERIFIED' and pre == '**'):
        bad('term %r first used before its definition (line: %s...)' % (t, line[:70]))
ok('glossary order checked') if not any('term' in x for x in problems) else None
# old names must be gone
for old in ['key deadline', 'Key deadline', 'latest start formula', 'old wording', 'Step 0', 'check window', 'closed gate exists but']:
    for k in 'SO':
        if old in T[k]: bad('%s still holds old term %r' % (F[k], old))

# 5 banned words (counts only)
tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
banned = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in node.targets):
        banned = [e.value for e in node.value.elts]
cnt_cs = sum(t.count(b) for t in T.values() for b in banned)
cnt_ci = sum(t.lower().count(b.lower()) for t in T.values() for b in banned)
print('banned words: %d listed, occurrences case-sensitive %d, case-insensitive %d' % (len(banned), cnt_cs, cnt_ci))
if cnt_cs or cnt_ci or not banned: bad('banned words found or list unread')

# 6 word discipline
for k in 'SNO':
    if re.search(r'\bstop\b', T[k]): bad('%s holds bare lowercase "stop"' % F[k])
S_nocode = re.sub(r'`[^`]*`', '', S)
if re.search(r'\brows?\b', S_nocode, re.I): bad('"row" in sheet')
if re.search(r'HubSpot key|probe key|API key', S): bad('other key meaning in sheet')
for k in 'SNO':
    Tk = re.sub(r'`[^`]*`', '', T[k])
    for m in re.finditer(r'(?<![A-Za-z])programs?(?![A-Za-z])', Tk):
        pre = Tk[max(0, m.start() - 6):m.start()].lower()
        if not (pre.endswith('take ') or pre.endswith('model ')):
            bad('%s: bare "program" near %r' % (F[k], Tk[max(0, m.start() - 30):m.start() + 20])); break
    if re.search(r'(?<!take )(?<!model )(?<!Take )(?<!Model )settings file', re.sub(r'`[^`]*`', '', T[k])): bad('%s: bare "settings file"' % F[k])
ok('word checks run')

# 7 arithmetic and dates of the invented examples
def hm(s): h, m = s.split(':')[:2]; return dt.timedelta(hours=int(h), minutes=int(m), seconds=int(s.split(':')[2]) if s.count(':') == 2 else 0)
IST = dt.timedelta(hours=5, minutes=30)
pairs = 0
for k, t in T.items():
    for a, b in re.findall(r'(\d\d:\d\d(?::\d\d)?) UTC = (\d\d:\d\d(?::\d\d)?) IST', t):
        pairs += 1
        if (hm(a) + IST) % dt.timedelta(days=1) != hm(b): bad('%s: %s UTC is not %s IST' % (F[k], a, b))
print('UTC = IST pairs checked:', pairs)
for k, t in T.items():
    for wd, day in re.findall(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) Nov 2026', t):
        if dt.date(2026, 11, int(day)).strftime('%a') != wd: bad('%s: %s %s Nov 2026 weekday wrong' % (F[k], wd, day))
# sample message of the sheet
mm = re.search(r'Latest start: (\d\d:\d\d) UTC.*?Alarm time: (\d\d:\d\d) UTC.*?Cancel-by time: (\d\d:\d\d) UTC', S)
ls, lf, cb = (hm(x) for x in mm.groups())
rl_fp = int(re.search(r'run length (\d+) min \+ film pause (\d+) min = (\d+)', S).group(3))
margin = int(re.search(r'margin (\d+) min', S).group(1))
if lf - ls != dt.timedelta(minutes=rl_fp): bad('sample: alarm time is not latest start + run length + film pause')
if cb - lf != dt.timedelta(minutes=margin): bad('sample: cancel-by time is not alarm time + margin')
if rl_fp != int(re.search(r'run length (\d+) min', S).group(1)) + int(re.search(r'film pause (\d+) min', S).group(1)): bad('sample: sum of run length and film pause')
if cb > hm('18:29'): bad('sample: cancel-by time after window end')
# worked example of the note
we = hm('18:29:00'); B = we - dt.timedelta(seconds=860)
if str(B) != '18:14:40': bad('B is %s' % B)
if f'B = 18:14:40' not in Nn or 'window end - 30 min = 17:59:00' not in Nn: bad('note example text missing')
ex = min(hm('11:30'), B, we - dt.timedelta(minutes=30))
if ex != hm('11:30'): bad('example 1 latest start')
if (ex + dt.timedelta(minutes=20), ex + dt.timedelta(minutes=30)) != (hm('11:50'), hm('12:00')): bad('example 1 alarm and cancel-by')
ex2 = min(hm('18:10'), B, we - dt.timedelta(minutes=30))
if (ex2, ex2 + dt.timedelta(minutes=20), ex2 + dt.timedelta(minutes=30)) != (hm('17:59'), hm('18:19'), hm('18:29')): bad('example 2')
for s in ['LS = 11:30 UTC = 17:00 IST', 'LF = 11:50 UTC = 17:20 IST', 'CB = 12:00 UTC = 17:30 IST', 'LF = 18:19 UTC = 23:49 IST', 'CB = 18:29:00 UTC = 23:59 IST', '17:59:00 UTC = 23:29 IST', '18:14:40 UTC = 23:44:40 IST']:
    if s not in Nn.replace('latest start LS', 'LS').replace('; LS', '; LS'):
        if s not in Nn: bad('note example lacks %r' % s)
from decimal import Decimal as Dc
price = (Dc(40000) * 3 + Dc(10000) * 15) / 1000000
if price != Dc('0.27') or price * 3 != Dc('0.81') or Dc('12.40') + Dc('0.81') != Dc('13.21') or Dc('3.90') - Dc('3.10') != Dc('0.80'): bad('price example arithmetic')
for s in ['0.27', '0.81', '13.21', '40,000 x 3 + 10,000 x 15']:
    if s not in S + Nn: bad('price example text %r missing' % s)
ok('arithmetic, weekdays and UTC/IST pairs checked')

# 8 map completeness
def has(ids_, label):
    for i in ids_:
        if not re.search(r'^\| %s( |\|)' % re.escape(i), M, re.M): bad('map lacks %s' % i)
has(['BR-' + c for c in 'abcdefghijklmnopqrs'] + ['BR-M%d' % i for i in (3, 4, 5, 12, 13, 14)] + ['BR-N%d' % i for i in range(1, 7)], 'BR')
has(['ST-B%d' % i for i in range(1, 8)] + ['ST-M%d' % i for i in range(1, 19)] + ['ST-T%d' % i for i in range(1, 6)] + ['ST-N%d' % i for i in range(1, 16)] + ['ST-Never'], 'ST')
has(['SE-B1', 'SE-B2'] + ['SE-M%d' % i for i in range(1, 13)] + ['SE-N%d' % i for i in range(1, 7)] + ['SE-D'], 'SE')
has(['CO-%d' % i for i in range(1, 23)] + ['CO-drift'], 'CO')
has(['AD-B%d' % i for i in range(1, 5)] + ['AD-M%d' % i for i in range(1, 16)] + ['AD-N1 to N6'], 'AD')
has(['RC-%d' % i for i in range(1, 6)], 'RC')
print('map table rows:', len(re.findall(r'^\| ', M, re.M)))
ok('map checked') if not any('map' in x for x in problems) else None

# 9 required controls and template slots
need = ['run-<run name>', 'phone alarm', 'prepaid', 'auto-reload', '18:29 UTC = 23:59 IST', '15:00 UTC = 20:30 IST', 'UNVERIFIED', 'revoke',
        'contact id', '`n`', 'challenge', '`end`', 'I cancel the older key', 'model key cancelled', 'sha256sum', 'key save failed',
        'record/0-1/', 'recognise', 'If you do nothing', 'minimal', 'Order of the day', 'one take per key', '"go"', 'I decline',
        'cancel the key (R2) first', 'exact addresses ending `@example.com`', 'allowed characters' if False else 'Values the lead sends may hold only']
for p in need:
    if p.lower() not in S.lower(): bad('sheet lacks %r' % p)
for p in ['Expected after the take', 'minutes at "Type y to start"', 'subject start', 'Second take', 'second take', 'need_seconds', 'Take broker port'.lower() if False else 'take broker port',
          'model key file (per-run path)', 'independent reader', 'F-01', 'ss -tlnH', 'credit on the prepaid page']:
    if p.lower() not in Nn.lower(): bad('note lacks %r' % p)
for p in ['5678', '5679', '5690', '5691', '5692', '5693']:
    if p not in Nn: bad('note port list lacks %s' % p)
proposal = re.search(r'proposal (\d{4}) and (\d{4})', Nn)
if not proposal or {proposal.group(1), proposal.group(2)} & {'5678', '5679', '5690', '5691', '5692', '5693'}: bad('port proposal collides')
print('TOTAL PROBLEMS', len(problems))
sys.exit(1 if problems else 0)

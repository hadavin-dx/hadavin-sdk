"""v19 form checks: reads text only, runs nothing else. Prints counts, never a banned word.
Proves FORM (ids, counts, order of terms, arithmetic of the invented examples, weekdays); it cannot prove a statement true."""
import ast, re, sys, datetime as dt
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'S': 'OWNER-SHEET-v19.md', 'N': 'LEAD-RELEASE-NOTE-v3.md', 'M': 'v19-MAP.md', 'O': 'v19-OPEN-FOR-LEAD.md'}
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
if sorted(gdefs, key=lambda x: int(x[1:])) != ['G%d' % i for i in range(1, 33)] or len(set(gdefs)) != 32: bad('G ids defined: %s' % gdefs)
else: ok('G1..G32 each defined once')
sec = re.split(r'^### 1([abc])\.', Nn, flags=re.M)
parts = {sec[i]: sec[i + 1] for i in range(1, len(sec) - 1, 2)}
def ids(txt): return re.findall(r'^\| (G\d+) \|', txt, re.M)
if set(ids(parts.get('b', ''))) != {'G16', 'G25', 'G26', 'G30'}: bad('gate group b wrong: %s' % ids(parts.get('b', '')))
if set(ids(parts.get('c', ''))) != {'G27', 'G28', 'G29'}: bad('gate group c wrong: %s' % ids(parts.get('c', '')))
want_a = {'G%d' % i for i in list(range(1, 16)) + list(range(17, 25)) + [31, 32]}
if set(ids(parts.get('a', ''))) != want_a or len(ids(parts.get('a', ''))) != 25: bad('gate group a wrong')
ok('gate groups checked') if not any('gate group' in x for x in problems) else None
for k, t in T.items():
    for g in set(re.findall(r'\bG(\d+)\b', t)):
        if not 1 <= int(g) <= 32: bad('%s refers to G%s' % (F[k], g))
for s in set(re.findall(r'section (\d+)', S)):
    if not 1 <= int(s) <= 9: bad('sheet refers to section %s' % s)
nopen = len(re.findall(r'^\| \d+ \|', O, re.M))
for k in ('N', 'M'):
    for o in set(re.findall(r'\bOpen (\d+)\b', T[k])):
        if not 1 <= int(o) <= nopen: bad('%s refers to Open %s (only %d)' % (F[k], o, nopen))
print('open rows:', nopen)

# 3 rule key phrases once, only in the rule table
phr = ['you cancel only', 'secret-looking', 'does not enforce', 'Recording is ON only', 'FREEZE =', 'ONE cancel rule',
       'no gate closes before then', 'does not print the model settings figures', 'shares your Linux user', 'Hard end, in this order']
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
terms = ['lead', 'message place', 'numbers message', 'clean-up message', 'second way', 'UNVERIFIED', 'HubSpot', 'contact', 'contact id', 'run name', 'test people',
         'person id', 'take program', 'WSL', 'n8n', 'model program', 'version id', 'fingerprint', 'model key', 'older key', 'key list', 'key file', 'app passwords',
         'take window', 'second window', 'take settings file', 'model settings file', 'notice', 'challenge', 'printed result', 'exit code', 'film pause',
         'window end', 'latest start', 'alarm time', 'cancel-by time', "program's last start", 'call ceiling', 'run total', 'balance', 'highest balance you accept',
         'program limit', 'usage page', 'throwaway accounts']
for t in terms:
    m = re.search(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])', S[S.index('## 1.'):], re.I)
    off = S.index('## 1.')
    if not m: bad('term %r never used' % t); continue
    SS = S[off:]
    pre = SS[max(0, m.start() - 2):m.start()]
    line = SS[SS.rfind('\n', 0, m.start()) + 1:SS.find('\n', m.start())]
    # the word "lead" opens the glossary bullet; 'take window' is defined in the heading of section 7
    if pre != '**':
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
        post = Tk[m.end():m.end() + 8]
        if not (pre.endswith('take ') or pre.endswith('model ') or post.startswith(' limit') or post.startswith("'s last")):
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
sm = re.search(r'minutes at "Type y to start" (\d+) \+ run length (\d+) \+ film pause (\d+) = (\d+); margin (\d+)', S)
y_, rl_, fp_, tot_, margin = (int(x) for x in sm.groups())
if y_ + rl_ + fp_ != tot_: bad('sample: sum of y minutes, run length and film pause')
if lf - ls != dt.timedelta(minutes=tot_): bad('sample: alarm time is not latest start + y minutes + run length + film pause')
if cb - lf != dt.timedelta(minutes=margin): bad('sample: cancel-by time is not alarm time + margin')
if cb > hm('18:29'): bad('sample: cancel-by time after window end')
we = hm('18:29:00'); B = we - dt.timedelta(seconds=860)
if str(B) != '18:14:40': bad('B is %s' % B)
if 'Program\'s last start: 18:14:40 UTC = 23:44:40 IST' not in S: bad('sample lacks program last start')
if ls > B: bad('sample: latest start after the program last start')
if ls > we - dt.timedelta(minutes=tot_ + margin): bad('sample: latest start too late for the window end')
# sample money
bal = Dc_ = None
from decimal import Decimal as Dc
price = (Dc(40000) * 3 + Dc(10000) * 15) / 1000000
if price != Dc('0.27') or price * 3 != Dc('0.81') or Dc('12.40') + Dc('0.81') != Dc('13.21'): bad('price example arithmetic')
mb = re.search(r'Balance on the prepaid page: US\$(\d+)\.00.*?Highest balance[^:]*: US\$(\d+)\s.*?Program limit: US\$([\d.]+) \(money used before ([\d.]+) \+ run total ([\d.]+)\)', S)
if not mb: bad('sample money line missing')
else:
    bal, hi, pl, mu, rt = (Dc(x) for x in mb.groups())
    if not (rt <= bal <= hi): bad('sample: balance %s not between run total and highest balance %s' % (bal, hi))
    if mu + rt != pl or rt != Dc('0.81'): bad('sample: program limit is not money used + run total')
    if pl > Dc('180'): bad('sample: program limit above studio ceiling')
for s_ in ['0.27', '0.81', '13.21', '40,000 x 3 + 10,000 x 15']:
    if s_ not in S + Nn: bad('price example text %r missing' % s_)
# note worked examples
def need_(x):
    if x not in Nn: bad('note example lacks %r' % x)
ex = min(hm('11:30'), B, we - dt.timedelta(minutes=35))
if (ex, ex + dt.timedelta(minutes=25), ex + dt.timedelta(minutes=35)) != (hm('11:30'), hm('11:55'), hm('12:05')): bad('example 1')
ex2 = min(hm('18:10'), B, we - dt.timedelta(minutes=35))
if (ex2, ex2 + dt.timedelta(minutes=25), ex2 + dt.timedelta(minutes=35)) != (hm('17:54'), hm('18:19'), hm('18:29')): bad('example 2')
for x in ['LS = 11:30 UTC = 17:00 IST', 'LF = 11:55 UTC = 17:25 IST', 'CB = 12:05 UTC = 17:35 IST', 'LF = 18:19:00 UTC = 23:49 IST', 'CB = 18:29:00 UTC = 23:59 IST', '17:54:00 UTC = 23:24 IST', '18:14:40 UTC = 23:44:40 IST', 'window end - 35 min = 17:54:00', 'B = 18:14:40']: need_(x)
ok('arithmetic, weekdays and UTC/IST pairs checked')

# 8 map completeness
def has(ids_):
    for i in ids_:
        if not re.search(r'^\| %s( |\|)' % re.escape(i), M, re.M): bad('map lacks %s' % i)
has(['SB%d' % i for i in range(1, 7)] + ['SC-A', 'SC-B', 'SC-C', 'SC-D'] + ['SM%d' % i for i in range(1, 26)] + ['SQ-len'])
has(['XM%d' % i for i in range(1, 9)] + ['XN%d' % i for i in range(1, 9)] + ['EM%d' % i for i in range(1, 6)] + ['K%d' % i for i in range(1, 23)])
print('map table rows:', len(re.findall(r'^\| ', M, re.M)))
ok('map checked') if not any('map' in x for x in problems) else None

# 9 required controls and template slots
need = ['run-<run name>', 'phone alarm', 'prepaid', 'auto-reload', '18:29 UTC = 23:59 IST', '15:00 UTC = 20:30 IST', 'UNVERIFIED', 'revoke',
        'contact id', '`n`', 'challenge', '`end`', 'I cancel the older key', 'model key cancelled', 'sha256sum', 'key save failed',
        'record/0-1/', 'recognise', 'If you do nothing', 'minimal', 'Order of the day', 'one take per key', '"go"', 'I decline',
        'cancel the key (R2) first', 'exact addresses ending `@example.com`', 'letters, digits and `. _ / -`', 'Second way', 'Reading the counts',
        'bash', 'grep "^<setting name>="', 'NOT safe', 'the whole balance', '(a) an address other than', '(f) a browser tab title', 'Recall & snapshots']
for p in need:
    if p.lower() not in S.lower(): bad('sheet lacks %r' % p)
for p in ['Expected after the take', 'minutes at "Type y to start"', 'subject start', 'Second take', 'second take', 'need_seconds', 'take broker port',
          'model key file (per-run path)', 'independent reader', 'F-01', 'ss -tlnH', 'balance on the prepaid page', 'G30', 'G31', 'G32',
          'ORDERS.md line 150', 'a lead sent twice with the same id is processed once', 'FACTS line 3', 'AGENT-SCOPE line 15', 'CORRECTIONS (a)']:
    if p.lower() not in Nn.lower(): bad('note lacks %r' % p)
for p in ['5678', '5679', '5690', '5691', '5692', '5693']:
    if p not in Nn: bad('note port list lacks %s' % p)
proposal = re.search(r'proposal (\d{4}) and (\d{4})', Nn)
if not proposal or {proposal.group(1), proposal.group(2)} & {'5678', '5679', '5690', '5691', '5692', '5693'}: bad('port proposal collides')
for w in ['backstop', 'Backstop', 'Credit', 'credit on', 'head ', ' head', '(good here)', 'closed gate']:
    if w in S: bad('sheet still holds old word %r' % w)
if 'made-up sales contact' in Nn: bad('note still holds the drifted claim wording')
if 'UNVERIFIED: the post-by' in S or 'source of that time UNVERIFIED' in S: bad('post-by still marked UNVERIFIED')
# every command printed in the sheet's backticks that starts a shell command is in R6's list or R10
print('TOTAL PROBLEMS', len(problems))
sys.exit(1 if problems else 0)

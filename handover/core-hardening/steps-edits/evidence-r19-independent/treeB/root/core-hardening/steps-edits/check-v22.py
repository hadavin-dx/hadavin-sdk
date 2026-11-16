"""v22 form checks. Reads text only, runs nothing else. Prints counts, never a banned word.
Proves FORM only (ids, pointers, definitions, arithmetic of the invented examples, set phrases, charset); it cannot prove a statement true.
New in v22 (the two classes the v21 checker missed in the independent mutation test, evidence-v21-independent 06b):
  (1) unlisted set phrase: every quoted phrase in a "send / reply / write to the lead" context must be in the set-phrase list, every listed phrase must be used,
      every phrase uses only the second R8 character set, placeholder spelling is one form;
  (2) changed pointer target: every line of the sheet has its pointer tokens (R-ids, N.M items, card parts and steps, section numbers) compared with a frozen
      pointer map (evidence-v22/pointer-golden-v22.json, regenerate by a human with --print-golden after a deliberate change), plus a unit-keyword table
      that says what each pointed-at rule or step must still contain, plus explicit anchors for the v21 failure F1.
Folder can be overridden with the environment variable V22_DIR (used by the planted-mistake runs)."""
import ast, json, os, re, sys, datetime as dt
from decimal import Decimal as Dc
D = os.environ.get('V22_DIR', '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/')
if not D.endswith('/'): D += '/'
F = {'S': 'OWNER-SHEET-v22.md', 'N': 'LEAD-RELEASE-NOTE-v6.md', 'O': 'v22-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
S, Nn, O = T['S'], T['N'], T['O']
problems = []
def bad(msg): problems.append(msg); print('PROBLEM:', msg)
def ok(msg): print('ok:', msg)
def nocode(t): return re.sub(r'`[^`]*`', '', t)
Slines = S.splitlines()

# ---------- sheet units ----------
def unit_key(line):
    return line[:48]
ptr_re = re.compile(r'\bR\d+\b|(?<![\d.:/-])\b[5-8]\.\d{1,2}\b(?![\d:])|card (?:Part|step) \d|section \d+|Part \d')
def pointers(line):
    return sorted(m.group(0) for m in ptr_re.finditer(nocode(line)))
def golden_now():
    g, seen = {}, {}
    for ln in Slines:
        k = unit_key(ln)
        seen[k] = seen.get(k, 0) + 1
        g['%s#%d' % (k, seen[k])] = pointers(ln)
    return {k: v for k, v in g.items() if v}
if '--print-golden' in sys.argv:
    print(json.dumps(golden_now(), indent=0, sort_keys=True)); sys.exit(0)

# 1 counts
n = {k: len(t.splitlines()) for k, t in T.items()}
v21 = open(D + 'OWNER-SHEET-v21.md', encoding='utf-8').read()
print('lines:', n, ' words v21 -> v22: %d -> %d' % (len(v21.split()), len(S.split())), ' note words v5 -> v6: %d -> %d' % (len(open(D + 'LEAD-RELEASE-NOTE-v5.md', encoding='utf-8').read().split()), len(Nn.split())))
heads = re.findall(r'^## ', S, re.M)
if len(heads) != 9: bad('sheet headings %d, expected 9' % len(heads))
else: ok('9 headings')

# 2 rules, gates, pointers
defs = re.findall(r'^\| (R\d+) \|', S, re.M)
if defs != ['R%d' % i for i in range(1, 11)]: bad('rule ids defined: %s' % defs)
else: ok('R1..R10 each defined once')
for k, t in T.items():
    for r in set(re.findall(r'\bR(\d+)\b', t)):
        if not 1 <= int(r) <= 10: bad('%s refers to R%s' % (F[k], r))
for i in (1, 4, 5, 6, 7, 8, 9, 10):
    outside = sum(len(re.findall(r'\bR%d\b' % i, t)) for t in T.values()) - 1
    if outside < 1: bad('R%d never referenced outside its definition' % i)
# R2 and R3 are pointers to the card: no other place may cite them (the cancel rule is stated once, in the card)
for i in (2, 3):
    c = len(re.findall(r'\bR%d\b' % i, S))
    if c != 1: bad('sheet cites R%d %d times (only its own pointer row may; everything else says "the card")' % (i, c))
r2 = [l for l in Slines if l.startswith('| R2 |')][0]; r3 = [l for l in Slines if l.startswith('| R3 |')][0]
if len(r2.split()) > 40 or len(r3.split()) > 40 or 'card' not in r2 or 'card' not in r3: bad('R2 or R3 row is not a short pointer to the card')
gdefs = re.findall(r'^\| (G\d+) \|', Nn, re.M)
NG = 42
if sorted(gdefs, key=lambda x: int(x[1:])) != ['G%d' % i for i in range(1, NG + 1)] or len(set(gdefs)) != NG: bad('G ids defined: %s' % gdefs)
else: ok('G1..G%d each defined once' % NG)
sec = re.split(r'^### 1([abc])\.', Nn, flags=re.M)
parts = {sec[i]: sec[i + 1] for i in range(1, len(sec) - 1, 2)}
def ids(txt): return re.findall(r'^\| (G\d+) \|', txt, re.M)
if set(ids(parts.get('b', ''))) != {'G16', 'G25', 'G26', 'G30'}: bad('gate group b wrong: %s' % ids(parts.get('b', '')))
if set(ids(parts.get('c', ''))) != {'G27', 'G28', 'G29'}: bad('gate group c wrong')
want_a = {'G%d' % i for i in list(range(1, 16)) + list(range(17, 25)) + list(range(31, 43))}
if set(ids(parts.get('a', ''))) != want_a or len(ids(parts.get('a', ''))) != len(want_a): bad('gate group a wrong: %s' % sorted(set(ids(parts.get('a', ''))) ^ want_a))
else: ok('gate groups a (%d), b (4), c (3) checked' % len(want_a))
if 'G1 to G15, G17 to G24, G31 to G42' not in Nn: bad('statements line does not name the 1a gate range')
for k, t in T.items():
    for g in set(re.findall(r'\bG(\d+)\b', t)):
        if not 1 <= int(g) <= NG: bad('%s refers to G%s' % (F[k], g))
if re.search(r'\bG\d+\b', S): bad('sheet cites a gate id: %s' % sorted(set(re.findall(r'\bG\d+\b', S))))
else: ok('sheet cites no gate id')
for s in set(re.findall(r'section (\d+)', S)):
    if not 1 <= int(s) <= 9: bad('sheet refers to section %s' % s)
opennums = [int(x) for x in re.findall(r'^\| (\d+) \|', O, re.M)]
nopen = len(opennums)
if opennums != list(range(1, nopen + 1)): bad('Open numbers not 1..n in order: %s' % opennums)
for k in 'NO':
    for o in set(re.findall(r'\bOpen (\d+)\b', T[k])):
        if not 1 <= int(o) <= nopen: bad('%s refers to Open %s (only %d)' % (F[k], o, nopen))
print('open rows:', nopen)
# note section 0 items numbered 1..n in order (v21 finding F3)
sec0 = Nn[Nn.index('## 0.'):Nn.index('## 1. Gates')]
nums0 = [int(x) for x in re.findall(r'^(\d+)\. ', sec0, re.M)]
if nums0 != list(range(1, len(nums0) + 1)): bad('note section 0 items not in order: %s' % nums0)
else: ok('note section 0 items 1..%d in order' % len(nums0))
for m in re.finditer(r'Note section 0 item (\d+)', O + Nn):
    if int(m.group(1)) > len(nums0): bad('cites note section 0 item %s (only %d)' % (m.group(1), len(nums0)))
# sheet items per section
items, cur = {}, None
for line in Slines:
    h = re.match(r'## (\d)\.', line)
    if h: cur = int(h.group(1)); items[cur] = 0; continue
    if cur and re.match(r'\d+\. ', line): items[cur] += 1
print('numbered items per sheet section:', {k: v for k, v in items.items() if v})
for k, t in T.items():
    tt = nocode(t)
    for a, b in set(re.findall(r'(?<![\d.:/-])\b([5-8])\.(\d{1,2})\b(?![\d:])', tt)):
        if int(b) < 1 or int(b) > items.get(int(a), 0): bad('%s: pointer %s.%s does not exist (sheet section %s has %d items)' % (F[k], a, b, a, items.get(int(a), 0)))
for m in re.finditer(r'card step (\d+)', S + Nn + O):
    if not 1 <= int(m.group(1)) <= items[2]: bad('card step %s does not exist (%d steps)' % (m.group(1), items[2]))
for m in re.finditer(r'card Parts? (\d)', S + Nn + O):
    if not 1 <= int(m.group(1)) <= 4: bad('card Part %s does not exist' % m.group(1))
for p in ('**Part 1,', '**Part 2,', '**Part 3,', '**Part 4,'):
    if S.count(p) != 1: bad('card %s not exactly once' % p)
ok('item, card and section pointers checked')

# 3 cancel rule stated once (card); trigger list once
card = S[S.index('### The card'):S.index('### The ten rules')]
once = ['Part 2, what you may cancel', 'Cancelling may not be undoable', 'with all filters off', 'N minus K', 'at most 60 seconds', 'try the same page on your phone',
        'nothing else matters until it is', 'No word of the lead resumes', 'No timer of the lead exists', '(e) the latest start passes', 'one lower for each key cancelled',
        'Why two:', 'Key-list check 1, 2, 3', 'the only meaning of "unsure"']
for p in once:
    c = S.count(p)
    if c != 1: bad('phrase %r occurs %d times in the sheet (expected 1)' % (p, c))
for p in once[:11]:
    if p not in card: bad('phrase %r is not inside the card' % p)
for p in ['Part 2, what you may cancel', 'with all filters off', 'N minus K', 'Cancelling may not be undoable']:
    if p in Nn or p in O: bad('note or open list restates the cancel rule phrase %r' % p)
rules_only = ['Hard end', 'Recording is ON only', 'FREEZE = in the take terminal', "does not print the model settings file's figures", 'Only five words in a message', 'are not locks']
rows = [l for l in Slines if re.match(r'\| R\d+ \|', l)]
for p in rules_only:
    cnt = sum(t.lower().count(p.lower()) for t in (S, Nn, O)); inrule = sum(l.lower().count(p.lower()) for l in rows)
    if p == 'Hard end':
        if cnt != 0: bad('old R3 phrase %r still present' % p)
    elif cnt != 1 or inrule != 1: bad('phrase %r occurs %d times (in rule table %d)' % (p, cnt, inrule))
if S.count('18:29 UTC = 23:59 IST') != 2: bad('deadline phrase in sheet not exactly 2 (glossary and yes line)')
if Nn.count('18:29 UTC = 23:59 IST') > 1: bad('deadline phrase repeated in note')
if S.count('15:00 UTC = 20:30 IST') != 1: bad('post-by time not exactly once in sheet')
ok('single-source phrases checked')

# 4 glossary order
terms = ['lead', 'message place', 'numbers message', 'clean-up message', 'other channel', 'report in words', 'UNVERIFIED', 'FREEZE', 'HubSpot', 'contact', 'contact id',
         'run name', 'test people', 'prep contact', 'person id', 'take program', 'WSL', 'n8n', 'model program', 'rehearsal', 'version id', 'fingerprint', 'start line',
         'model key', 'older key', 'key list', 'valid key', 'cancelled word', 'key alive', 'key-list check 1, 2, 3', 'key file', 'app passwords', 'HubSpot app secrets', 'take terminal', 'read terminal',
         'take settings file', 'model settings file', 'notice', 'challenge', 'printed result', 'exit code', 'film pause', 'film cue', 'recording', 'recording off', 'recording box',
         'privacy switches', 'film person', 'editor', 'post checker', 'demo mail', 'deadline', 'latest start', 'alarm time', 'cancel-by time', 'alarm-time alarm', 'cancel-by alarm',
         'silence minutes', 'earliest key time', "program's last start", 'call ceiling', 'spend lock', 'end-date refusal', 'expected total', 'program limit', 'balance', 'prepaid', 'auto-reload',
         'per-key limit', 'tokens', 'ledger total', 'usage page', 'masked account', 'throwaway accounts']
SS = S[S.index('## 1.'):]
G = SS[:SS.index('## 2.')]
G = G[G.index('\n- ') + 1:]  # the intro paragraph may point forward (UNVERIFIED, see below); the terms are checked from the first bullet
for t in terms:
    m = re.search(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z-])', G, re.I if t not in ('UNVERIFIED', 'FREEZE', 'WSL') else 0)
    if not m: bad('term %r never used in the glossary' % t); continue
    if G[max(0, m.start() - 2):m.start()] != '**':
        line = G[G.rfind('\n', 0, m.start()) + 1:G.find('\n', m.start())]
        bad('term %r first used before its definition (line: %s...)' % (t, line[:70]))
for old in ['key deadline', 'Key deadline', 'old wording', 'Step 0', 'check window', 'words you see', 'Backstop', 'backstop', 'Credit', 'take-prep', 'pgrep -af', 'args=', 'separate note you need not read', 'as R6 says', 'Open 1 and 2']:
    for k in 'SO':
        if old in T[k] and not (k == 'O' and old in ('backstop', 'Backstop', 'pgrep -af', 'args=', 'Open 1 and 2', 'as R6 says')): bad('%s still holds old term %r' % (F[k], old))
    if old in ('Open 1 and 2', 'as R6 says') and old in Nn: bad('note still holds %r' % old)

# 5 banned words (counts only)
tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
banned = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in node.targets):
        banned = [e.value for e in node.value.elts]
allfiles = dict(T)
for extra in ('v22-CHANGES.md', 'checkpoint-v22.md', 'check-v22.py', 'evidence-v22/check-v22-raw.txt'):
    try: allfiles[extra] = open(D + extra, encoding='utf-8').read()
    except OSError: pass
cnt_cs = sum(t.count(b) for t in allfiles.values() for b in banned)
cnt_ci = sum(t.lower().count(b.lower()) for t in allfiles.values() for b in banned)
print('banned words: %d listed, occurrences case-sensitive %d, case-insensitive %d (files read: %d)' % (len(banned), cnt_cs, cnt_ci, len(allfiles)))
if cnt_cs or cnt_ci or not banned: bad('banned words found or list unread')

# 6 word discipline
S_nc = nocode(S)
for k in 'SNO':
    if re.search(r'\bstop\b(?!")', re.sub(r'"stop"', '', nocode(T[k]))): bad('%s holds a bare lowercase "stop"' % F[k])
if re.search(r'\brows?\b', S_nc, re.I): bad('"row" in sheet')
if re.search(r'HubSpot key|probe key|API key', S): bad('other key meaning in sheet')
if '$' in S_nc: bad('dollar sign outside code in the sheet')
if 'US$' in S: bad('US$ in sheet')
for k in 'SNO':
    Tk = nocode(T[k])
    for m in re.finditer(r'(?<![A-Za-z])programs?(?![A-Za-z])', Tk):
        pre = Tk[max(0, m.start() - 6):m.start()].lower(); post = Tk[m.end():m.end() + 8]
        if not (pre.endswith('take ') or pre.endswith('model ') or post.startswith(' limit') or post.startswith("'s last")):
            bad('%s: bare "program" near %r' % (F[k], Tk[max(0, m.start() - 30):m.start() + 20])); break
    if re.search(r'(?<!take )(?<!model )(?<!Take )(?<!Model )settings file', Tk): bad('%s: bare "settings file"' % F[k])
if re.search(r'\bthe take\b(?! program| terminal| settings)', S_nc): bad('sheet uses "the take" as a noun')
if re.search(r'take window|second window|Take window', S): bad('sheet still says take window or second window')
if re.search(r'\bunsure\b', S_nc) and not S.count('the only meaning of "unsure"') == 1: bad('unsure rule')
ok('word checks run')

# 7 arithmetic and dates
def hm(s): h, m = s.split(':')[:2]; return dt.timedelta(hours=int(h), minutes=int(m), seconds=int(s.split(':')[2]) if s.count(':') == 2 else 0)
IST = dt.timedelta(hours=5, minutes=30)
pairs = 0
for k, t in T.items():
    for a, b in re.findall(r'(\d\d:\d\d(?::\d\d)?) UTC = (\d\d:\d\d(?::\d\d)?) IST', t):
        pairs += 1
        if (hm(a) + IST) % dt.timedelta(days=1) != hm(b): bad('%s: %s UTC is not %s IST' % (F[k], a, b))
print('UTC = IST pairs checked:', pairs)
wd = 0
for k, t in T.items():
    for w, day in re.findall(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) Nov 2026', t):
        wd += 1
        if dt.date(2026, 11, int(day)).strftime('%a') != w: bad('%s: %s %s Nov 2026 weekday wrong' % (F[k], w, day))
print('weekday mentions checked:', wd)
mm = re.search(r'Latest start: (\d\d:\d\d) UTC.*?Alarm time: (\d\d:\d\d) UTC.*?Cancel-by time: (\d\d:\d\d) UTC', S)
ls, lf, cb = (hm(x) for x in mm.groups())
sm = re.search(r'minutes at "Type y to start" (\d+) \+ run length (\d+) \+ film pause (\d+) = (\d+); margin (\d+)', S)
y_, rl_, fp_, tot_, margin = (int(x) for x in sm.groups())
sl = re.search(r'Minutes at "Type y to start": (\d+)   Run length: (\d+) \(the take program needs at least (\d+) seconds = ([\d.]+) minutes\)   Film pause: (\d+)   Margin: (\d+)', S)
if not sl: bad('separate lines for minutes at y, run length, film pause missing in the sample')
else:
    if (int(sl.group(1)), int(sl.group(2)), int(sl.group(5)), int(sl.group(6))) != (y_, rl_, fp_, margin): bad('separate lines disagree with the sums line')
    if (Dc(sl.group(3)) / 60 * 10).to_integral_value(rounding='ROUND_CEILING') / 10 != Dc(sl.group(4)): bad('need seconds / 60 (rounded up to one decimal) is not the minutes shown')
    if rl_ * 60 < int(sl.group(3)): bad('sample run length %d minutes is below need_seconds %s' % (rl_, sl.group(3)))
Z = 10
if y_ + rl_ + fp_ != tot_: bad('sample: sum of y minutes, run length and film pause')
if lf - ls != dt.timedelta(minutes=tot_): bad('sample: alarm time is not latest start + y minutes + run length + film pause')
if cb - lf != dt.timedelta(minutes=margin): bad('sample: cancel-by time is not alarm time + margin')
we = hm('18:29:00'); B = we - dt.timedelta(seconds=860)
if str(B) != '18:14:40': bad('B is %s' % B)
if "Program's last start: 18:14:40 UTC = 23:44:40 IST" not in S: bad('sample lacks program last start')
if ls > B: bad('sample: latest start after the program last start')
if ls > we - dt.timedelta(minutes=tot_ + margin + Z): bad('sample: latest start too late for the deadline and cancel buffer')
if cb > we - dt.timedelta(minutes=Z): bad('sample: cancel-by time inside the cancel buffer')
lim = we - dt.timedelta(minutes=tot_ + margin + Z)
if '18:29 minus %d minutes = %s UTC' % (tot_ + margin + Z, str(lim)[:-3].rjust(5, '0')) not in S: bad('check 4 worked example text does not match the arithmetic (%s)' % lim)
price = (Dc(40000) * 3 + Dc(10000) * 15) / 1000000
if price != Dc('0.27') or price * 3 != Dc('0.81') or Dc('12.40') + Dc('0.81') != Dc('13.21'): bad('price example arithmetic')
mb = re.search(r'Balance on the prepaid page: USD (\d+)\.00.*?Program limit: USD ([\d.]+) \(ledger total ([\d.]+) \+ expected total ([\d.]+)\)', S)
if not mb: bad('sample money line missing')
else:
    bal, pl, mu, rt = (Dc(x) for x in mb.groups())
    if not (rt <= bal): bad('sample: balance below the expected total')
    if mu + rt != pl or rt != Dc('0.81'): bad('sample: program limit is not ledger total + expected total')
    if pl > Dc('180'): bad('sample: program limit above studio ceiling')
    sv = dict(re.findall(r'(\b[A-Z_]+) = (\d+)', S[S.index('Settings to compare'):S.index('Minutes at "Type y')]))
    if Dc(sv['PRICE_IN_CENTS']) / 100 != 3 or Dc(sv['PRICE_OUT_CENTS']) / 100 != 15 or Dc(sv['PROGRAM_LIMIT_CENTS']) / 100 != pl: bad('sample settings in cents disagree with the sample money')
    if (Dc(sv['TOKENS_IN']) * Dc(sv['PRICE_IN_CENTS']) + Dc(sv['TOKENS_OUT']) * Dc(sv['PRICE_OUT_CENTS'])) / 1000000 / 100 != Dc('0.27'): bad('sample settings do not give 0.27 per call')
    if Dc(sv['CALL_CEILING']) != 3: bad('sample call ceiling setting')
if 'DEADLINE = 2026-11-23T18:29:00Z' not in S: bad('sample deadline setting')
for s_ in ['0.27', '0.81', '13.21', '40,000 x 3 + 10,000 x 15']:
    if s_ not in S + Nn: bad('price example text %r missing' % s_)
ex = min(hm('11:30'), B, we - dt.timedelta(minutes=50))
if (ex, ex + dt.timedelta(minutes=30), ex + dt.timedelta(minutes=40)) != (hm('11:30'), hm('12:00'), hm('12:10')): bad('note example 1')
ex2 = min(hm('18:10'), B, we - dt.timedelta(minutes=50))
if (ex2, ex2 + dt.timedelta(minutes=30), ex2 + dt.timedelta(minutes=40)) != (hm('17:39'), hm('18:09'), hm('18:19')): bad('note example 2')
if we - (ex2 + dt.timedelta(minutes=40)) != dt.timedelta(minutes=Z): bad('example 2: cancel-by is not exactly the buffer before the deadline')
for x in ['LS = 11:30 UTC = 17:00 IST', 'LF = 12:00 UTC = 17:30 IST', 'CB = 12:10 UTC = 17:40 IST', 'LF = 18:09:00 UTC = 23:39 IST', 'CB = 18:19:00 UTC = 23:49 IST',
          '17:39:00 UTC = 23:09 IST', '18:14:40 UTC = 23:44:40 IST', 'deadline - 50 min = 17:39:00', 'B = 18:14:40']:
    if x not in Nn: bad('note example lacks %r' % x)
# sample dates on one day (finding F9): the run day, the ps example and the file time
rd = re.search(r'Run day: (\w{3}) (\d+) Nov 2026', S)
psx = re.search(r'`(\d+) (\w{3}) Nov (\d+) (\d\d:\d\d:\d\d) 2026 python3`', S)
fx = re.search(r'`2026-11-(\d\d) (\d\d:\d\d:\d\d)\.\d+ \+0000`', S)
if not (rd and psx and fx): bad('sample ps or file time example not found')
else:
    if not (psx.group(3) == rd.group(2) == fx.group(1)) or psx.group(2) != rd.group(1): bad('ps/file examples are not on the sample run day')
    if not (hm('11:00') <= hm(fx.group(2)) < hm(psx.group(4)) <= ls): bad('sample file time, process start, earliest key time and latest start not in order')
ok('arithmetic, weekdays, UTC/IST pairs, buffer examples and sample dates checked')

# 8 yes sentence charset, five step words
ym = re.search(r'"(Yes, run <run name>:.*?)"\s+Amounts', S)
if not ym: bad('yes sentence not found')
else:
    y = re.sub(r'<[^>]*>', '5', ym.group(1))
    if re.search(r'[^A-Za-z0-9 .,:=_/@+-]', y): bad('yes sentence charset: %r' % sorted(set(re.findall(r'[^A-Za-z0-9 .,:=_/@+-]', y))))
    if 'USD' not in y or '$' in y or 'does not end the calls' not in y: bad('yes sentence money form or missing clause')
r8 = [l for l in Slines if l.startswith('| R8 |')][0]
for w in ['"go"', '"n8n is off"', '"post"', '"still works"', '"continue"']:
    if w not in r8: bad('R8 lacks step word %s' % w)
if 'Only five words' not in r8: bad('R8 lacks the five-word statement')

# 9 set phrases: class "unlisted set phrase" (v21 mutation M5)
lst = [l for l in Slines if l.startswith('**Set phrases you send')]
if len(lst) != 1: bad('set phrase list not found exactly once')
else:
    norm = lambda s: re.sub(r'<[^>]*>', '<>', s.strip())
    listed = [norm(x) for x in re.findall(r'"([^"]+)"', lst[0])]
    lead_words = {'stop'}
    lead_says = {'go', 'n8n is off', 'post', 'still works', 'continue'}
    fill = lambda s: re.sub(r'<[^>]*>', 'x', s)
    for p in listed:
        if p in lead_words: continue
        if re.search(r'[^A-Za-z0-9 .,:=_/@+<>-]', p): bad('set phrase %r uses a character outside the second R8 set' % p)
    # every sending context uses a listed phrase
    body = '\n'.join(l for l in Slines if not l.startswith('**Set phrases you send') and not l.startswith('```'))
    body = re.sub(r'```.*?```', '', S, flags=re.S).replace(lst[0], '')
    ctx = re.compile(r'(?:\bsend\b|\bsends\b|\bsent\b|\breply\b|\bReply\b|write to the lead|\bwrite\b|\bwrote to the lead\b)[^"\n]{0,50}"([^"]+)"')
    used = set()
    for m in ctx.finditer(nocode(body)):
        ph = norm(m.group(1))
        if ph in lead_says: continue
        if ph not in listed: bad('quoted phrase %r is sent or written but is not in the set-phrase list' % m.group(1))
        else: used.add(ph)
    for ph in listed:
        if ph in lead_words: continue
        pat = '<[^>]*>'.join(re.escape(x) for x in ph.split('<>'))
        if len(re.findall(pat, body)) < 1: bad('listed set phrase %r is not used in any step or rule' % ph)
    # the older-key phrase has one spelling everywhere (finding F6)
    spell = set(norm(m.group(0)) for m in re.finditer(r'I cancel the older key <[^>]*>(?:, nothing else I know uses it)?', S))
    if len(spell) != 1 or not all('nothing else I know uses it' in x for x in spell): bad('older key phrase spelled in more than one form: %s' % spell)
    ok('set phrases: %d listed, %d used in a send context, charset and spelling checked' % (len(listed), len(used)))

# 10 pointers: class "changed pointer target" (v21 mutation M11, finding F1)
UNITKW = {'R1': 'alone', 'R4': 'Money.', 'R5': 'Compare every number', 'R6': 'by hand', 'R7': 'delete only made-up', 'R8': 'The lead\'s messages give values',
          'R9': 'Recording is ON only', 'R10': 'FREEZE = in the take terminal',
          '5.1': 'Run name', '5.3': 'Laptop on the run day', '5.4': 'Receiver Gmail', '5.6': 'Model account pages', '5.7': 'Settings figures', '5.8': 'The yes',
          '6.1': 'Recall', '6.2': 'Two phone alarms', '6.3': 'ls -l', '6.4': 'set -C', '6.5': 'exit 0', '6.6': 'ps -o',
          '7.1': 'Ticks', '7.2': 'sha256sum', '7.3': 'start line', '7.4': 'Compare the notice', '5.2': 'People', '7.6': 'Film pause', '7.8': 'Type `end`', '7.9': 'echo $?', '7.10': 'usage page',
          '8.1': 'date -u', '8.2': 'Contacts', '8.3': 'App passwords', '8.4': 'HubSpot app secrets', '8.5': 'Demo mails', '8.6': 'Retire check', '8.7': 'laptop settings', '8.8': 'finished video'}
def unit_text(i):
    if re.fullmatch(r'R\d+', i): return [l for l in Slines if l.startswith('| %s |' % i)][0]
    a, b = i.split('.'); a = int(a)
    cur_ = None
    for l in Slines:
        h = re.match(r'## (\d)\.', l)
        if h: cur_ = int(h.group(1)); continue
        if cur_ == a and re.match(r'%s\. ' % b, l): return l
    return ''
for i, kw in UNITKW.items():
    if kw not in unit_text(i): bad('pointer target %s no longer contains %r' % (i, kw))
mentioned = set(re.findall(r'\bR(\d+)\b', nocode(S)))
for m in set(re.findall(r'(?<![\d.:/-])\b([5-8]\.\d{1,2})\b(?![\d:])', nocode(S))):
    if m not in UNITKW: bad('sheet points at %s but the unit-keyword table has no entry (add one)' % m)
# explicit anchors for F1 and the card hand-offs
r10 = [l for l in Slines if l.startswith('| R10 |')][0]; r6 = [l for l in Slines if l.startswith('| R6 |')][0]
if 'echo' in r6: bad('R6 mentions echo (the exit code pointer belongs to 7.9)')
if '7.9' not in r10 or 'echo $?' in r10 and 'as R6' in r10: bad('R10 must point to 7.9 for the exit code')
if 'echo $?' not in unit_text('7.9'): bad('7.9 does not hold echo $?')
if 'Go on at 7.9 if you typed `end`; otherwise at 8.1' not in S: bad('card step 6 hand-off pointers changed')
if 'card step 5' not in lst[0] or 'card Part 4' not in lst[0]: bad('set-phrase list does not point at the card')
gold_path = D + 'evidence-v22/pointer-golden-v22.json'
if not os.path.exists(gold_path): gold_path = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/evidence-v22/pointer-golden-v22.json'
try:
    gold = json.load(open(gold_path, encoding='utf-8'))
    now = golden_now()
    diff = [k for k in set(gold) | set(now) if gold.get(k) != now.get(k)]
    for k in sorted(diff)[:8]:
        bad('pointer map changed at %r: frozen %s, now %s' % (k[:48], gold.get(k), now.get(k)))
    if not diff: ok('pointer map equals the frozen map (%d lines carry pointers)' % len(now))
except OSError:
    bad('frozen pointer map not found (create with --print-golden)')

# 11 required controls
need = ['run-<run name>', 'two phone alarms', 'prepaid', 'auto-reload', '15:00 UTC = 20:30 IST', 'revoke', 'contact id', '`n`', 'challenge', '`end`', 'I cancel the older key',
        'model key cancelled', 'sha256sum', 'key save failed', 'record/0-1/', 'recognise', 'If you do nothing', 'Minimal', 'Order of the day', 'One run per key', '"go"', 'I decline',
        'exact mail addresses ending `@example.com`', 'letters, digits and `. _ / -`', 'Other channel', 'Reading the counts', 'bash', 'grep "^<setting name>="', 'NOT safe',
        'the whole balance', '(a) a mail address other than', '(f) a browser tab title', 'Recall & snapshots', 'Key-list check', 'cancel-by alarm', 'Report in words',
        'prep-<run name>@example.com', 'Demo mail', 'minimum think time', 'Spend lock', 'End-date refusal', 'continue', 'comm=', '/mnt/', 'subject starts with the subject start',
        'move it to Trash', 'HubSpot app secrets', 'Cancelled word', 'python3 -I', 'beginning of any used name', 'Worked example: Wed 18 Nov', 'STOP RULE']
for p in need:
    if p.lower() not in S.lower(): bad('sheet lacks %r' % p)
for p in ['Expected after the run', 'minutes at "Type y to start"', 'Second take', 'need_seconds', 'take broker port', 'per-run path', 'independent reader', 'F-01', 'ss -tlnH',
          'ORDERS.md line 150', 'ORDERS.md line 152', 'a lead sent twice with the same id is processed once', 'FACTS line 3', 'AGENT-SCOPE line 15', 'CORRECTIONS (a)', 'cancel buffer',
          'subject start', 'NOT SHOWN', 'ORDER 034 is not shown as met', 'G39', 'G40', 'G41', 'G42', 'no FILE you read', 'line 304']:
    if p.lower() not in Nn.lower(): bad('note lacks %r' % p)
for p in ['5678', '5679', '5690', '5691', '5692', '5693']:
    if p not in Nn: bad('note port list lacks %s' % p)
proposal = re.search(r'proposal (\d{4}) and (\d{4})', Nn)
if not proposal or {proposal.group(1), proposal.group(2)} & {'5678', '5679', '5690', '5691', '5692', '5693'}: bad('port proposal collides')
for p_ in ['highest balance', 'Highest balance', 'worst-case run total', 'Run total', 'Window end', 'window end', 'Go marker', 'second way', 'separate funding', 'differs from the word', 'once, as R6 says']:
    if p_ in S: bad('sheet still holds %r' % p_)
print('TOTAL PROBLEMS', len(problems))
sys.exit(1 if problems else 0)

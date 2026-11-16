"""check-v24.py: rebuilds every generated v24 file from its source and facts-v24.py, compares it with the file on disk,
then checks facts across ALL files. Usage: python3 check-v24.py   (folder: env V24_DIR, default this folder). Exit 0 = no failure.
It reports failures; it never says a file is good beyond the checks it runs."""
import os, re, sys, datetime as dt, subprocess
D = os.environ.get('V24_DIR') or os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
FAILS = []
def fail(code, msg): FAILS.append('%s %s' % (code, msg))
def rd(n): return open(D + n, encoding='utf-8').read()
ns = {}; exec(open(D + 'facts-v24.py', encoding='utf-8').read(), ns); F = ns['F']
bns = {'__name__': 'x'}
import importlib.util
spec = importlib.util.spec_from_file_location('b24', D + 'build-v24.py'); b = importlib.util.module_from_spec(spec)
sys.argv = ['x', D]; spec.loader.exec_module(b)
GEN = b.build()
for n, o in GEN.items():                                   # C01 copies cannot differ from source
    if not os.path.exists(D + n): fail('C01', 'missing ' + n); continue
    if rd(n) != o: fail('C01', n + ' differs from what its source and facts build')
for n in ('OWNER-SHEET-v24-A.md', 'OWNER-SHEET-v24-B.md', 'LEAD-RELEASE-NOTE-v8.md', 'v24-OPEN-FOR-LEAD.md', 'v24-CHANGES.md'):
    if not os.path.exists(D + n): fail('C02', 'file missing: ' + n)
A = rd('OWNER-SHEET-v24-A.md') if os.path.exists(D + 'OWNER-SHEET-v24-A.md') else ''
B = rd('OWNER-SHEET-v24-B.md') if os.path.exists(D + 'OWNER-SHEET-v24-B.md') else ''
ALL = {n: rd(n) for n in ('OWNER-SHEET-v24-A.md', 'OWNER-SHEET-v24-B.md', 'LEAD-RELEASE-NOTE-v8.md', 'v24-OPEN-FOR-LEAD.md', 'v24-CHANGES.md') if os.path.exists(D + n)}
# C03 arithmetic from primitives (independent of facts-v24.py: written out here)
price_c = (40000 * 300 + 10000 * 1500) // 1000000
if price_c != 27: fail('C03', 'price per call is not 27 cents')
if price_c * 3 != 81: fail('C03', 'expected total is not 81 cents')
if 1240 + 81 != 1321: fail('C03', 'limit is not 1321 cents')
if F['price'] != '0.27' or F['total'] != '0.81' or F['limit'] != '13.21' or F['limit_cents'] != '1321': fail('C03', 'facts money differs')
if round(860 / 60, 2) != 14.33 or F['need_min'] != '14.33': fail('C03', '860 s is not 14.33 min')
dl = dt.datetime(2026, 11, 23, 18, 29)
if (dl - dt.timedelta(seconds=860)).strftime('%H:%M:%S') != '18:14:40' or '18:14:40 UTC = 23:44:40 IST' not in F['last']: fail('C03', 'last start pair')
if '18:19 UTC = 23:49 IST' not in F['d23cb'] or '18:29 UTC = 23:59 IST' not in F['dl']: fail('C03', 'deadline pairs')
if F['cap'] != '17:39': fail('C03', 'latest start of 23 Nov is not 17:39')
if 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST' != F['postby']: fail('C03', 'post-by')
if dt.date(2026, 11, 18).strftime('%a') != 'Wed' or dt.date(2026, 11, 23).strftime('%a') != 'Mon' or dt.date(2026, 11, 25).strftime('%a') != 'Wed': fail('C03', 'weekdays')
# C04 every UTC/IST pair and every weekday-date in ALL files
for n, t in ALL.items():
    for m in re.finditer(r'(\d\d):(\d\d)(?::(\d\d))? UTC = (\d\d):(\d\d)(?::(\d\d))? IST', t):
        u = int(m[1]) * 60 + int(m[2]); i = int(m[4]) * 60 + int(m[5])
        if (u + 330) % 1440 != i or (m[3] and m[6] and m[3] != m[6]): fail('C04', n + ' bad pair ' + m[0])
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)( 2026)?', t):
        d = dt.datetime.strptime('%s %s 2026' % (m[2], m[3]), '%d %b %Y')
        if d.strftime('%a') != m[1]: fail('C04', n + ' wrong weekday ' + m[0])
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b', t):
        d = dt.datetime.strptime('%s %s 2026' % (m[3], m[2]), '%d %b %Y')
        if d.strftime('%a') != m[1]: fail('C04', n + ' wrong weekday ' + m[0])
    for m in re.finditer(r'(USD|US\$) ?(\d+\.\d+)', t):
        if m[2] not in ('0.27', '0.81', '13.21', '0.10', '0.50', '2.00', '10.00', '3.00', '15.00', '189.00', '180.00', '12.40', '0.00') and n.startswith('OWNER'): fail('C04', n + ' unexpected amount ' + m[0])
    if re.search(r'\b14\.4\b', t): fail('C04', n + ' says 14.4 (the figure is 14.33)')
# C05 stale references
STALE = [r'card Part 2', r'\bPart 2\b', r're-pin', r'check 5\b', r'sha256', r'\(v2[0-3]\b', r'OWNER-SHEET-v2[0-3]', r'LEAD-RELEASE-NOTE-v[1-7]\b', r'\bR[23] (is|are) kept']
for n, t in ALL.items():
    if n == 'v24-CHANGES.md': continue
    for p in STALE:
        for m in re.finditer(p, t):
            if n.startswith('OWNER') or p not in (r'\(v2[0-3]\b',): fail('C05', '%s stale text %r' % (n, m[0]))
# C06 banned vendor words (list read from the repo guard test; strings never printed)
try:
    import ast
    tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
    words = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in node.targets):
            words = [str(x) for x in ast.literal_eval(node.value)]
    if not words: fail('C06', 'BANNED tuple not found')
    for n, t in ALL.items():
        for w in words:
            if w.lower() in t.lower(): fail('C06', '%s holds a banned word (index %d)' % (n, words.index(w)))
except Exception as e: fail('C06', 'banned list unreadable: %s' % type(e).__name__)
# C07 word counts
for n in ('OWNER-SHEET-v24-A.md', 'OWNER-SHEET-v24-B.md'):
    c = len(ALL.get(n, '').split())
    if c > 6500: fail('C07', '%s has %d words (limit 6500)' % (n, c))
# C08 variant checks and no marker
for n, t in (('A', A), ('B', B)):
    if '[[' in t or ']]' in t or '{{' in t: fail('C08', n + ' has a marker')
if 'I will cancel the older key myself' not in A or 'stays valid during the run and I understand' in A: fail('C08', 'A yes sentence wrong')
if 'stays valid during the run and I understand' not in B or 'I will cancel the older key myself' in B: fail('C08', 'B yes sentence wrong')
if 'cancel the older key <its name>' not in B or 'Without (i) or (ii) the older key stays valid' not in B: fail('C08', 'B older key route missing')
# C09 the cancel rule lives only on the card
for n, t in (('A', A), ('B', B)):
    i = t.find('### THE CARD'); j = t.find('### The rules')
    if i < 0 or j < i: fail('C09', n + ' card boundaries'); continue
    out = t[:i] + t[j:]
    for p in (r'press the cancel button', r'confirmation word', r'reload the page'):
        if re.search(p, out): fail('C09', '%s cancel rule text %r outside the card' % (n, p))
# C10 words used in the card are defined inside the card first
for n, t in (('A', A), ('B', B)):
    i = t.find('**Words on this card'); j = t.find('**Blanks:**')
    k = t.find('**When (any one')
    if i < 0 or j < 0 or k < 0: fail('C10', n + ' card parts'); continue
    for m in re.finditer(r'\*\*([A-Z][A-Za-z -]+)\*\* =', t[i:j]):
        term = m[1].lower(); pos = t.lower().find(term, i)
        if pos != i + m.start() + 2: fail('C10', '%s card term %r used before its definition' % (n, m[1]))
# C11 pointers: every "x.y" step reference exists and points at the right topic
for n, t in (('A', A), ('B', B)):
    steps = {}
    cur = None
    for line in t.split('\n'):
        mh = re.match(r'## (\d)\.', line)
        if mh: cur = mh[1]
        ms = re.match(r'(\d+)\. ', line)
        if (cur or 'x') in '5678' and ms: steps['%s.%s' % (cur, ms[1])] = steps.get('%s.%s' % (cur, ms[1]), '') + line
        elif (cur or 'x') in '5678' and steps and line.strip() and not line.startswith('#'): last = list(steps)[-1]; steps[last] += line
    for m in re.finditer(r'(?<![\d.`$])([5-9])\.(\d{1,2})(?![\d.]*\d)\b', t):
        key = '%s.%s' % (m[1], m[2])
        if m[1] in '5678' and key not in steps and not re.match(r'\d+\.\d\d', t[m.start():m.start() + 6]): fail('C11', '%s pointer to missing step %s' % (n, key))
    BIND = {'5.8': 'The yes', '6.3': 'date -u', '6.5': 'If the line is not', '6.6': 'Key-list check 3', '7.3': 'start line', '7.4': 'challenge', '7.8': 'type `end`',
            '7.9': 'echo $?', '8.1': 'two times', '8.3': 'App passwords', '8.4': 'HubSpot app secrets', '8.5': 'Demo mails', '5.6': 'Key-list check 1', '6.2': 'phone alarms', '6.4': 'paste key, Enter:'}
    for k, w in BIND.items():
        if w not in steps.get(k, ''): fail('C11', '%s step %s lacks its topic %r' % (n, k, w))
    for m in re.finditer(r'\(?(8\.3 and 8\.4) say where', t):
        pass
# C12 set phrases: every phrase told by the sheet is in the list
for n, t in (('A', A), ('B', B)):
    i = t.find('**Set phrases'); lst = t[i:i + 1500]
    for k, v in F.items():
        if k.startswith('ph_') and v not in lst and not (k == 'ph_older' and n == 'B'): fail('C12', '%s set phrase missing from list: %s' % (n, v))
    if n == 'B' and F['ph_older'] in t: fail('C12', 'B holds the older-key phrase')
    for m in re.finditer(r'tell(?:ing)? "([^"]+)"', t):
        if m[1] not in [v for k, v in F.items() if k.startswith('ph_')] and m[1] != 'none': fail('C12', '%s told phrase not in list: %s' % (n, m[1]))
# C13 yes pattern characters
for n, t in (('A', A), ('B', B)):
    m = re.search(r'follows this pattern, each `<\.\.\.>` filled: "(.*?)" \*\*Filled example', t, re.S)
    if not m: fail('C13', n + ' yes pattern not found'); continue
    y = re.sub(r'<[^>]*>', 'x', m[1])
    bad = set(re.sub(r"[A-Za-z0-9 .:,_/=@+\-]", '', y))
    if bad: fail('C13', '%s yes pattern has characters %r' % (n, bad))
    if 'Deadline 2026-11-23' not in y and 'Deadline' not in y: fail('C13', n + ' yes lacks deadline')
# C14 adversarial and stranger invariants
INV = [('C14a', 'the key\'s own one-time display at 6.3 and the paste at 6.4'), ('C14b', 'switch it OFF yourself at once'), ('C14c', 'Three phone alarms'),
       ('C14d', 'Text between backticks is typed without the backticks'), ('C14e', 'only if the window\'s last line is `paste key, Enter:`'),
       ('C14f', '"READ" and "TEST"'), ('C14g', 'ignore a `.used` ending'), ('C14h', 'reverses the order of `end` and the card'), ('C14i', 'minutes of the time `date -u` shows'),
       ('C14j', 'if 7.4 never happened, tell "none"'), ('C14k', 'SAMPLE (made-up values'), ('C14l', 'no key was made'), ('C14m', 'never use rotate'),
       ('C14n', 'set -C; umask 077; read -rs'), ('C14o', 'last-resort step <step>'), ('C14p', 'one line only'), ('C14q', 'weekday, month, day and year must equal the run day'),
       ('C14r', 'balance and auto-reload equal your yes'), ('C14s', 'Never "Select all", never empty Trash'.replace('Never "Select all", never empty Trash', 'Never "Select all", never empty Trash')),
       ('C14t', 'STOP RULE'), ('C14u', 'FREEZE'), ('C14v', 'the card: cancel'.replace('the card: cancel', 'THE CARD'))]
for n, t in (('A', A), ('B', B)):
    for c, s in INV:
        if s not in t: fail(c, '%s lacks %r' % (n, s))
if 'before the earliest' in A and 'wait until the earliest key time has come' not in A: fail('C14w', 'A older key cancel not after earliest key time')
for n, t in (('A', A), ('B', B)):
    if 'sha256' in t.lower(): fail('C14x', n + ' has a checksum line that looks like a secret')
# C15 bash -n on the key-save line (key file filled with a made-up path)
for n, t in (('A', A), ('B', B)):
    m = re.search(r"`(\(\s?set -C; umask 077; read -rs .*?echo \"exit \$\?\")`", t)
    if not m: fail('C15', n + ' key-save line not found'); continue
    line = m[1].replace('<key file>', '/home/x/k')
    r = subprocess.run(['bash', '-n', '-c', line], capture_output=True, text=True)
    if r.returncode: fail('C15', n + ' bash -n: ' + r.stderr[:80])
print('check-v24: %d failure(s)' % len(FAILS))
for f in FAILS: print('FAIL', f)
sys.exit(1 if FAILS else 0)

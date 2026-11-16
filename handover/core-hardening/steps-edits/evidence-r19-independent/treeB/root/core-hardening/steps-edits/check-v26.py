"""check-v26.py: rebuilds every generated v25 file from its source and facts-v26.py, compares it with the file on disk,
then checks facts across ALL files. Usage: python3 check-v26.py   (folder: env V26_DIR, default this folder). Exit 0 = no failure.
It reports failures; it never says a file is good beyond the checks it runs.
C19 compares every pointer with pointers-v26.txt; after a person has read the new pointers: ACCEPT_POINTERS=1 python3 check-v26.py rewrites that list."""
import os, re, sys, datetime as dt, subprocess
D = os.environ.get('V26_DIR') or os.path.dirname(os.path.abspath(__file__))
if not D.endswith('/'): D += '/'
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
FAILS = []
def fail(code, msg): FAILS.append('%s %s' % (code, msg))
def rd(n): return open(D + n, encoding='utf-8').read()
ns = {}; exec(open(D + 'facts-v26.py', encoding='utf-8').read(), ns); F = ns['F']
bns = {'__name__': 'x'}
import importlib.util
spec = importlib.util.spec_from_file_location('b24', D + 'build-v26.py'); b = importlib.util.module_from_spec(spec)
sys.argv = ['x', D]; spec.loader.exec_module(b)
GEN = b.build()
for n, o in GEN.items():                                   # C01 copies cannot differ from source
    if not os.path.exists(D + n): fail('C01', 'missing ' + n); continue
    if rd(n) != o: fail('C01', n + ' differs from what its source and facts build')
for n in ('OWNER-SHEET-v26-A.md', 'OWNER-SHEET-v26-B.md', 'LEAD-RELEASE-NOTE-v10.md', 'v26-OPEN-FOR-LEAD.md', 'v26-CHANGES.md'):
    if not os.path.exists(D + n): fail('C02', 'file missing: ' + n)
A = rd('OWNER-SHEET-v26-A.md') if os.path.exists(D + 'OWNER-SHEET-v26-A.md') else ''
B = rd('OWNER-SHEET-v26-B.md') if os.path.exists(D + 'OWNER-SHEET-v26-B.md') else ''
ALL = {n: rd(n) for n in ('OWNER-SHEET-v26-A.md', 'OWNER-SHEET-v26-B.md', 'LEAD-RELEASE-NOTE-v10.md', 'v26-OPEN-FOR-LEAD.md', 'v26-CHANGES.md') if os.path.exists(D + n)}
# C03 arithmetic from primitives (independent of facts-v26.py: written out here)
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
    if n == 'v26-CHANGES.md': continue
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
for n in ('OWNER-SHEET-v26-A.md', 'OWNER-SHEET-v26-B.md'):
    c = len(ALL.get(n, '').split())
    if c > 6500: fail('C07', '%s has %d words (limit 6500)' % (n, c))
# C08 variant checks and no marker
for n, t in (('A', A), ('B', B)):
    if '[[' in t or ']]' in t or '{{' in t: fail('C08', n + ' has a marker')
if 'I will cancel the older key myself' not in A or 'stays valid during the run and I understand' in A: fail('C08', 'A yes sentence wrong')
if 'stays valid during the run and I understand' not in B or 'I will cancel the older key myself' in B: fail('C08', 'B yes sentence wrong')
if 'cancel the older key <its name>' not in B or '7.11, always, by ' + F['okb'] not in B: fail('C08', 'B older key route missing')
# C09 the cancel rule lives only on the card
for n, t in (('A', A), ('B', B)):
    i = t.find('### THE CARD'); j = t.find('### The rules')
    if i < 0 or j < i: fail('C09', n + ' card boundaries'); continue
    out = t[:i] + t[j:]
    for p in (r'press the cancel button', r'confirmation word', r'reload the page'):
        if re.search(p, out): fail('C09', '%s cancel rule text %r outside the card' % (n, p))
# C10 words used in the card are defined inside the card first
for n, t in (('A', A), ('B', B)):
    i = t.find('**Words on this card'); j = t.find('**Blanks, filled before')
    k = t.find('**When (any one')
    if i < 0 or j < 0 or k < 0: fail('C10', n + ' card parts'); continue
    for m in re.finditer(r'\*\*([A-Z][A-Za-z -]+)\*\* =', t[i:j]):
        term = m[1].lower(); pos = t.lower().find(term, i)
        if pos != i + m.start() + 2: fail('C10', '%s card term %r used before its definition' % (n, m[1]))
        if t[i:t.find("### The rules")].lower().count(term) < 2: fail('C10', '%s card term %r defined but not used again in the card' % (n, m[1]))
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
    if n == 'A' and 'send "%s"' % F['ph_older'] not in t: fail('C12', 'A lacks the older-key send at 6.7')
    for m in re.finditer(r'(?:tell(?:ing)?|[Ss]end) "([^"]+)"', t):
        if m[1] not in [v for k, v in F.items() if k.startswith('ph_')] and m[1] != 'none': fail('C12', '%s told phrase not in list: %s' % (n, m[1]))
# C13 yes pattern characters
for n, t in (('A', A), ('B', B)):
    m = re.search(r'in this pattern: "(.*?)" Amounts have two decimals', t, re.S)
    if not m: fail('C13', n + ' yes pattern not found'); continue
    y = re.sub(r'<[^>]*>', 'x', m[1])
    bad = set(re.sub(r"[A-Za-z0-9 .:,_/=@+\-]", '', y))
    if bad: fail('C13', '%s yes pattern has characters %r' % (n, bad))
    if 'Deadline 2026-11-23' not in y and 'Deadline' not in y: fail('C13', n + ' yes lacks deadline')
# C14 adversarial and stranger invariants
INV = [('C14a', 'the key\'s own one-time display at 6.3 and the paste at 6.4'), ('C14b', 'switch it OFF yourself at once'), ('C14c', 'Three phone alarms'),
       ('C14d', 'Text between backticks is typed without the backticks'), ('C14e', 'only if the window\'s last line is `paste key, Enter:`'),
       ('C14f', '"READ" and "TEST"'), ('C14g', 'A **run name** is 4 to 12 lowercase letters and digits'), ('C14h', 'reverses `end` and the card'), ('C14i', 'minutes of the time `date -u` shows'),
       ('C14j', 'if 7.4 never happened, send "none"'), ('C14k', 'SAMPLE (made-up values'), ('C14l', 'no key was made'), ('C14m', 'never use rotate'),
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

# ---- v25b additions: C16 to C25 (each closes a gap the ported v23 plants M01 to M54 showed) ----
import difflib
NOTE = ALL.get('LEAD-RELEASE-NOTE-v10.md', ''); OPEN = ALL.get('v26-OPEN-FOR-LEAD.md', ''); CHG = ALL.get('v26-CHANGES.md', '')
TEXTS = {'sheetA': A, 'sheetB': B, 'note': NOTE, 'open': OPEN, 'changes': CHG}
# C16 every pointer target exists: Open N has a row, G N has a row, sheet N.M is a step, open rows run 1..n with no gap
open_rows = [int(m[1]) for m in re.finditer(r'^\| (\d+) \|', OPEN, re.M)]
if open_rows != [i for i in range(1, open_rows[-1] + 1) if i != 59]: fail('C16', 'open list rows are not 1..n in order with only the removed row 59 missing (rows are quoted as Open N)')
g_rows = set(m[1] for m in re.finditer(r'^\| (G\d+) \|', NOTE, re.M))
def step_ids(t):
    out = set(); cur = None
    for line in t.split('\n'):
        mh = re.match(r'## (\d)\.', line)
        if mh: cur = mh[1]
        ms = re.match(r'(\d+)\. ', line)
        if cur in ('5', '6', '7', '8') and ms: out.add('%s.%s' % (cur, ms[1]))
    return out
SIDS = step_ids(A) | step_ids(B)
for n, t in TEXTS.items():
    for m in re.finditer(r'\bOpen (\d+)((?:(?:, | and | to )\d+)*)', t):
        for k in [m[1]] + re.findall(r'\d+', m[2]):
            if int(k) not in open_rows: fail('C16', '%s: Open %s does not exist (%d rows)' % (n, k, len(open_rows)))
    for m in re.finditer(r'\bG(\d+)\b', t):
        if 'G' + m[1] not in g_rows: fail('C16', '%s: G%s has no row in the note' % (n, m[1]))
    for m in re.finditer(r'\b[Ss]heet ([5-8]\.\d{1,2})\b', t):
        if m[1] not in SIDS: fail('C16', '%s: sheet %s is not a step' % (n, m[1]))
# C17 values: every statement of a number in any file equals the independent value
EXPECT = [(r'[Pp]rice per call(?: at full size)?:? (?:USD )?(\d+\.\d+)', '0.27'), (r'Expected total:? (?:USD )?(\d+\.\d+)', '0.81'), (r'expected total (?:USD )?(\d+\.\d+)', '0.81'),
          (r'gives (0\.\d+);', '0.27'), (r'TOKENS_OUT = (\d+)', '10000'), (r'TOKENS_IN = (\d+)', '40000'), (r'PRICE_IN_CENTS = (\d+)', '300'), (r'PRICE_OUT_CENTS = (\d+)', '1500'),
          (r'CALL_CEILING = (\d+)', '3'), (r'B submitted (\d+) times', '10'), (r'A submitted (\d+) times', '2'), (r'IST = UTC \+ (\d+:\d+)', '5:30'),
          (r'Program limit:? (?:USD )?(\d+\.\d+)', '13.21'), (r'Ledger total (\d+\.\d+)', '12.40'), (r'balance USD (\d+\.\d+)', '189.00'), (r'\b(14\.\d+) min', '14.33'), (r'(\d+) seconds = (\d+\.\d+)', None)]
for n, t in TEXTS.items():
    for p, v in EXPECT:
        if v is None: continue
        for m in re.finditer(p, t):
            if m[1] != v: fail('C17', '%s: %r says %s, expected %s' % (n, m[0][:50], m[1], v))
    for m in re.finditer(r'\b14\.\d+\b', t):
        if m[0] != '14.33': fail('C17', '%s: figure %s (the only figure is 14.33)' % (n, m[0]))
# C18 independent time literals (not read from facts-v26.py)
LIT = {'ek': '11:00 UTC = 16:30 IST', 'ls': '11:30 UTC = 17:00 IST', 'lf': '12:00 UTC = 17:30 IST', 'cb': '12:10 UTC = 17:40 IST', 'sum': '30', 'y': '5', 'rl': '15', 'fp': '10', 'mg': '10'}
for k, v in LIT.items():
    if F[k] != v: fail('C18', 'fact %s is %r, expected %r' % (k, F[k], v))
if int(F['y']) + int(F['rl']) + int(F['fp']) != int(F['sum']): fail('C18', 'Y + RL + FP is not the sum')
if -(-860 // 60) > int(F['rl']): fail('C18', 'run length below 860 s')
# C19 pointer ledger: every pointer (with the 28 characters before it) must be one a person verified; --accept-pointers rewrites the list
PT = re.compile(r'(?<![\d.$:])(?:\b[5-9]\.\d{1,2}\b(?![.:]?\d)|\bG\d+\b|\bOpen \d+(?:(?:, | and | to )\d+)*|\bsection \d+\b|\bR\d{1,2}\b|\bQ\d+\b|\bcard step \d\b)')
cur_ptr = set()
for n, t in TEXTS.items():
    for m in PT.finditer(t):
        pre = re.sub(r'\s+', ' ', t[max(0, m.start() - 28):m.start()])
        cur_ptr.add('%s|%s|%s' % (n, pre, m[0]))
LEDGER = D + 'pointers-v26.txt'
if os.environ.get('ACCEPT_POINTERS') == '1':
    open(LEDGER, 'w', encoding='utf-8').write('\n'.join(sorted(cur_ptr)) + '\n'); print('pointers-v26.txt rewritten: %d entries (a person must have read each new one)' % len(cur_ptr))
elif not os.path.exists(LEDGER): fail('C19', 'pointers-v26.txt missing')
else:
    ok_ptr = set(open(LEDGER, encoding='utf-8').read().split('\n')) - {''}
    for e in sorted(cur_ptr - ok_ptr): fail('C19', 'pointer not in the verified list: ' + e[:100])
# C20 angle-bracket placeholders in the sheet come from one list
PH_OK = {'<amount or none>', '<call ceiling>', '<date>', '<expected total>', '<in words>', '<its name or none>', '<its name>', '<key file>', "<lead's answer>", '<model settings file>',
         '<name and how>', '<name>', '<number or none>', '<number>', '<page address>', '<path from the message>', '<range>', '<run name>', '<setting name>', '<step>',
         '<test settings file name>', '<the balance you read on the prepaid page>', '<the word you read, it must be off>', '<word seen by the lead>', '<words>', '<copied>', '<place>', '<how>', '<zone>', '<its last-used time, never or none>', '<address>', '<folder path>', '<minutes>', "<the lead's exact sentence>", '<masked address>', '<the cd line>', '<name and how to call>', '<yes or no>'}
for n, t in (('A', A), ('B', B)):
    for m in set(re.findall(r'<[A-Za-z][^<>\n]{0,45}>', t)):
        if m not in PH_OK: fail('C20', '%s: placeholder not in the list: %s' % (n, m))
# C21 set phrase told at the step that owns it; no near-miss of a set phrase anywhere
OWN = {'8.2': 'ph_cd', '8.3': 'ph_apr', '8.4': 'ph_hsr', '8.5': 'ph_dmd', '7.4': 'ph_rs', '6.5': 'ph_ksf'}
for n, t in (('A', A), ('B', B)):
    cur = None; steps = {}; last = None
    for line in t.split('\n'):
        mh = re.match(r'## (\d)\.', line)
        if mh: cur = mh[1]; last = None
        ms = re.match(r'(\d+)\. ', line)
        if cur in ('5', '6', '7', '8') and ms: last = '%s.%s' % (cur, ms[1]); steps[last] = line
        elif last and line.strip() and not line.startswith('#'): steps[last] += ' ' + line
    for k, ph in OWN.items():
        if '"%s"' % F[ph] not in steps.get(k, ''): fail('C21', '%s: step %s does not tell its set phrase %r' % (n, k, F[ph]))
        for k2, v2 in F.items():
            if k2.startswith('ph_') and k2 != ph and k2 not in ('ph_mkc', 'ph_nokey', 'ph_rs', 'ph_cf', 'ph_ksf', 'ph_tp', 'ph_msg') and 'send "%s"' % v2 in steps.get(k, ''): fail('C21', '%s: step %s tells the phrase of another step: %s' % (n, k, v2))
    i = t.find('### THE CARD'); card = t[i:t.find('### The rules')]
    if 'Send exactly: %s. Only now' % F['ph_mkc'] not in card: fail('C21', n + ': card step 5 lacks its exact phrase')
PHS = [v for k, v in F.items() if k.startswith('ph_')]
for n, t in TEXTS.items():
    for q in set(re.findall(r'"([^"\n]{6,70})"', t)):
        for v in PHS:
            r = difflib.SequenceMatcher(None, q.lower(), v.lower()).ratio()
            if q != v and q != re.sub(r'\s*<[^>]*>', '', v) and ' ' in q and r >= 0.8: fail('C21', '%s: quoted words %r look like the set phrase %r but differ' % (n, q, v))
# C22 the cancel rule text lives only on the card: paraphrases outside it, in any file
CAN = [r'(?<![Aa]uto-)\b(reload|reloads|reloaded|refresh|refreshes|refreshed)\b', r'beside each key', r'click Cancel', r'cancelled (state|word) each time', r'press the cancel button', r'confirmation word']
for n, t in (('sheetA', A), ('sheetB', B)):
    i = t.find('### THE CARD'); j = t.find('### The rules'); out = t[:i] + t[j:]
    for p in CAN:
        for m in re.finditer(p, out): fail('C22', '%s: cancel-rule wording %r outside the card' % (n, m[0]))
for n in ('note', 'open'):
    for p in CAN:
        for m in re.finditer(p, TEXTS[n]): fail('C22', '%s: cancel-rule wording %r' % (n, m[0]))
# C23 fixed sentences that must stay (each one is a rule the reviews asked for)
KEEP = ['**STOP RULE.**', 'A key alive: the card first', 'The balance is at least the expected total.', 'If two rules disagree: the card first, then R1, then R10', 'Never "Select all", never empty Trash',
        'letters, digits, single spaces and `. _ / - : = @ + , \'` only', 'A submitted 2 times with the same person id, 1 contact, 1 mail; B submitted 10 times, 1 contact, 1 mail',
        'paper notes "READ" and "TEST"', 'No word of the lead resumes a run whose key was alive', 'a wait never delays the card'.capitalize()]
for n, t in (('A', A), ('B', B)):
    for s_ in KEEP:
        if s_ not in t: fail('C23', '%s lacks the fixed sentence %r' % (n, s_))
for item in ('Windows menu paths', 'the Recall page', 'the paste method', 'the app-password page path', 'the HubSpot private-app page path', 'the Chrome profile menu', 'where the contact id sits'):
    if item not in NOTE: fail('C23', 'note lacks tolerated item: ' + item)
# C24 R8 character list: the yes pattern uses only what R8 allows
mr = re.search(r'single spaces and `([^`]+)` only', A)
if mr:
    allowed = set(mr[1].replace(' ', '')) | set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
    for n, t in (('A', A), ('B', B)):
        m = re.search(r'in this pattern: "(.*?)" Amounts have two decimals', t, re.S)
        if m and set(re.sub(r'<[^>]*>', 'x', m[1])) - allowed: fail('C24', n + ': yes pattern holds a character R8 does not allow')
else: fail('C24', 'R8 character list not found')
# C25 the three window facts of 5.1 and the three alarms agree (set once in the card words and in 6.2)
for n, t in (('A', A), ('B', B)):
    if t.count('one of the three alarms of 6.2') != 1 or 'Three phone alarms' not in t: fail('C25', n + ' alarm count wording')
exec(open(HERE + 'newchecks-v26.py', encoding='utf-8').read())
print('check-v26: %d failure(s)' % len(FAILS))
for f in FAILS: print('FAIL', f)
sys.exit(1 if FAILS else 0)

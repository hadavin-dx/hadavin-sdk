"""v16 checks (extends check-v15.py): reads text only, runs nothing else."""
import re, sys, ast
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'W': 'OWNER-SHEET-v16.md', 'CH': 'v16-CHANGES.md', 'OP': 'v16-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
bad = 0
def fail(msg):
    global bad
    print('FAIL', msg); bad += 1
src = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
banned = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', src, re.S).group(1) + ')')
print('banned strings in test list:', len(banned))
for k, t in T.items():
    n = sum(t.count(b) for b in banned); n2 = len(re.findall(r'\b(PENDING|TBD|TODO)\b', t))
    print(f'{F[k]}: banned={n} PENDING/TBD/TODO={n2} bytes={len(t.encode())} UNVERIFIED={t.count("UNVERIFIED")}')
    if n or n2: fail('banned/placeholder in ' + F[k])
W, CH, OP = T['W'], T['CH'], T['OP']
i2, i3 = W.index('\n# Part 2.'), W.index('\n# Part 3.')
P1, P2, P3 = W[:i2], W[i2:i3], W[i3:]
print('Part 1 bytes', len(P1.encode()), '(v15 sheet 35882) | Part 2', len(P2.encode()), '| Part 3', len(P3.encode()), '| file', len(W.encode()), '(v15 three files 80446)')
# 1 open items
lst = P3.split('## 18. Open items')[1]
nums = [int(x) for x in re.findall(r'\bOI-(\d+)\b (?:\(proposal\) )?[a-z]', lst.split('**Not proven')[0])]
nums = sorted(set(nums))
print('open items in appendix 18:', nums[0], '..', nums[-1], 'count', len(nums))
if nums != list(range(1, len(nums) + 1)): fail('open item list not sequential: %s' % nums)
N = len(nums)
for k, t in T.items():
    for n in set(re.findall(r'\bOI-(\d+)\b', t)):
        if int(n) > N: fail(f'{k}: OI-{n} not in the list')
body = P1 + P2 + P3.split('## 18. Open items')[0]
for n in nums:
    if not re.search(r'\bOI-%d\b' % n, body): fail(f'open item never used outside the list: OI-{n}')
    if not re.search(r'^\| OI-%d \|' % n, OP, re.M): fail(f'OI-{n} missing from v16-OPEN-FOR-LEAD.md')
if re.search(r'\bB\d{1,2}\b', W): fail('old blank name B<n> left in the sheet: %s' % re.findall(r'\bB\d{1,2}\b', W)[:5])
props = sorted(set(int(x) for x in re.findall(r'OI-(\d+) \(proposal\)', lst)))
opp = sorted(int(m.group(1)) for m in re.finditer(r'^\| OI-(\d+) \|.*\| (?:Proposal)', OP, re.M))
print('proposals in sheet list:', props, '| OP rows starting "Proposal":', opp)
if props != opp: fail('proposal labels differ between sheet and OP')
# 2 card lines
rows = [l for l in P2.splitlines() if '________' in l]
print('card lines with an underline:', len(rows))
for l in rows:
    if l.count('________') != 1: fail('card line with several underlines: ' + l[:60])
    if not re.search(r'row \d+|OI-\d+|step A message', l): fail('card underline line without source: ' + l[:60])
if 'no underscore' not in P2.lower(): fail('card complete rule missing')
# 3 forbidden patterns
for pat, why in ((r'run key', 'old'), (r'take key', 'old'), (r'MF_', 'film-v5'), (r'\bQ\d{2}', 'Q-number'), (r'\bQ\d\b', 'Q-number'),
                 (r'[Dd]ecision \d', 'decision number'), (r'\bC\.3\b', 'removed step'), (r'list of runs', 'n8n look'), (r'[Ee]xit code [1-9]\b', 'exit code'),
                 (r'\bcode [1-9]\b', 'exit code'), (r'SKIPPED', 'result word'), (r'run card', 'renamed'), (r'day card(?!\))', 'x') if False else (r'run window', 'renamed'),
                 (r'run folder', 'renamed'), (r'run settings file', 'renamed'), (r'ruling of 2026', 'unsourced'), (r'default decision', 'jargon'),
                 (r'cancel every', 'old I.0 rule'), (r'every key with no', 'old I.0 rule'), (r'\bA reading\b|\bE reading\b', 'renamed reading'),
                 (r'\bdev\b|\bstaging\b', 'stage name'), (r'stage\.env', 'stage word'), (r'180', 'US$180'), (r'\b189\b', 'US$189'), (r'loopback', 'jargon')):
    c = len(re.findall(pat, W))
    if pat == r'loopback': 
        c = len(re.findall(pat, P1 + P2))
    if c: fail(f'forbidden "{pat}" ({why}) x{c}')
for pat in (r'5[- ]minute', r'\b5 minutes\b', r'at most 3', r'\b3 (?:runs|retire)', r'20[- ]minute', r'\b20 minutes\b', r'24[- ]hours?\b', r'24 h\b', r'2[- ]minutes?\b',
            r'two minutes', r'30[- ]minutes?\b', r'15 minutes', r'\b120\b', r'2 seconds', r'\b45\b', r'\b860\b', r'about 14', r'14 minutes', r'exit code 3'):
    c = len(re.findall(pat, W))
    if c: fail(f'invented/unsourced number "{pat}" x{c}')
# 4 hard-coded times
ok_times = {'18:29', '23:59', '15:00', '20:30', '5:30'}
for t_ in set(re.findall(r'(?<![\d.])\d{1,2}:\d{2}(?!\d)', W)):
    if t_ not in ok_times: fail('hard-coded time ' + t_)
for s in ('18:29 UTC = 23:59 IST', '25 Nov 2026 15:00 UTC = 20:30 IST'):
    print(s, W.count(s))
    if W.count(s) < 1: fail('date string missing: ' + s)
# 5 bare "lead"
t = W
for ph in ('a lead sent twice', 'sales lead', 'lead key', '"lead"', "'lead'", 'unfinished lead', 'unfinished test person', 'lead whose', '[demo] lead', 'lead desk', 'lead-status', '"Lead" alone', 'Lead" alone', 'sales contact', 'a lead sent', 'Studio lead', 'studio lead'):
    t = t.replace(ph, '')
c = [t[max(0, m.start() - 25):m.end() + 15].replace('\n', ' ') for m in re.finditer(r'\b[Ll]eads?\b', t)]
if c: fail(f'bare "lead" x{len(c)}: {c[:4]}')
# 6 one place per rule and key rulings
if P1.count('Recording OFF first') != 1 or W.count('Recording OFF first') != 1: fail('Key exposed rule not exactly once')
if re.search(r'nothing can (start or )?spend', P1 + P2): fail('"nothing can spend" claim in Parts 1/2')
if 'three tries' in P1 + P2: fail('lease tries sentence in Parts 1 or 2')
if 'NOT APPROVED' not in P3 or 'candidate' not in P3: fail('lease candidate missing')
if W.count('It is the only source of the latest start') != 1: fail('latest start not defined once')
for pat in ('the only place they are defined', 'Freeze never delays Time'):
    if W.count(pat) != 1: fail('missing once: ' + pat)
stop = P1.split('## The five stop words')[1].split('After any word')[0] if 'After any word' in P1 else P1.split('## The five stop words')[1].split('Once a model key exists')[0]
words = re.findall(r'^\| (\d) \| \*\*([A-Za-z ]+)\*\*', stop, re.M)
print('stop words:', words)
if [w[1] for w in words] != ['Key exposed', 'Emergency cancel', 'Time', 'Freeze', 'Stop'] or [w[0] for w in words] != list('12345'): fail('stop word table wrong')
if 'LOWER order number wins' not in P1: fail('precedence rule missing')
for pat, why in (('named `run-<run name>`', 'key name rule (words)'), ('never cancel', 'unknown key rule'), ('at or before the money stop', 'row 11 limit'),
                 ('step A (first', 'step A order'), ('exactly one result', 'delete method'), ('record, not a control', 'usage page'),
                 ('Decimal', 'price calculator'), ('show token', 'A.5 token click'), ('rule 9', 'people rule'), ('Recording, editing and posting', 'logistics section'),
                 ('informational only', 'ruling (k)'), ('NOT APPROVED', 'lease'), ('imported and activated', 'checksum word'), ('TZ=UTC', 'time zone rule')):
    if pat not in W: fail(f'missing: {why} ({pat})')
# A before B in order table
ot = P3.split('## 6. Order table')[1].split('## 7.')[0]
if ot.index('step A') > ot.index('B, C.1, C.2, D'): fail('order table: step A not before B')
# 7 cross references
for k, t in (('W', W), ('CH', CH), ('OP', OP)):
    for n in re.findall(r'[Aa]ppendix (\d+)', t):
        if not 1 <= int(n) <= 18: fail(f'{k}: bad appendix ref {n}')
secs = sorted(int(x) for x in re.findall(r'^## (\d+)\.', P3, re.M))
if secs != list(range(1, 19)): fail('appendix sections not 1..18: %s' % secs)
rows_a = sorted(int(x) for x in re.findall(r'^\| (\d+) \|', P3.split('## 2. The value list')[1].split('## 3.')[0], re.M))
if rows_a != list(range(1, 24)): fail('value list rows not 1..23')
for n in re.findall(r'\brows? (\d+)', W) + [x for p in re.findall(r'rows (\d+) (?:to|and) (\d+)', W) for x in p]:
    if not 1 <= int(n) <= 23: fail(f'bad row {n}')
for n in re.findall(r'go items? (\d)', W):
    if not 1 <= int(n) <= 9: fail(f'bad go item {n}')
goitems = re.findall(r'^(\d)\. ', P1.split('## The go list')[1].split('## The money rule')[0], re.M)
if goitems != [str(i) for i in range(1, 10)]: fail('go items not 1..9: %s' % goitems)
money = re.findall(r'^(\d)\. ', P1.split('## The money rule')[1].split('## Rules that hold')[0], re.M)
if money != [str(i) for i in range(1, 7)]: fail('money items not 1..6: %s' % money)
for n in re.findall(r'money rule items? (\d)', W):
    if n not in money: fail(f'bad money item {n}')
ban = re.findall(r'(?:^|\s)(\d{1,2})\. ', P3.split('## 7. Post ban')[1].split('Two further')[0])
if sorted(set(int(i) for i in ban)) != list(range(1, 14)): fail('ban list not 1..13')
for n in re.findall(r'\brules? (\d+)', W):
    if not 1 <= int(n) <= 15: fail(f'bad rule ref {n}')
rl = re.findall(r'^(\d+)\. ', P1.split('## Rules that hold in every step')[1].split('## Step 0.')[0], re.M)
print('rules numbered at line start:', rl)
for r_ in set(re.findall(r'\b(A\.0b|A\.[0-6]|0\.[1-6]|C\.[1-2]|I\.[0-7]|F\.[1-5]|E\.[0-4])\b', W)):
    head = {'A.0b', 'A.0', 'A.1', 'A.2', 'A.3', 'A.4', 'A.5', 'A.6', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', 'C.1', 'C.2', 'I.0', 'I.1', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'F.1', 'F.2', 'F.3', 'F.4', 'F.5', 'E.0', 'E.1', 'E.2', 'E.3', 'E.4'}
    if r_ not in head: fail('unresolved step ref ' + r_)
for i in range(1, 6):
    if not re.search(rf'^{i}\. ', P2.split('## F. Film pause')[1], re.M): fail(f'card F item {i} missing')
# 8 findings coverage
ids = (['SE-M%d' % i for i in range(1, 8)] + ['SE-N%d' % i for i in range(1, 9)] + ['ST-B%d' % i for i in range(1, 6)] + ['ST-%d' % i for i in range(6, 18)]
       + ['ST-n%d' % i for i in range(1, 9)] + ['ST-U%d' % i for i in range(1, 8)] + ['ST-G'] + ['CI-%d' % i for i in range(1, 14)] + ['AD-%d' % i for i in range(1, 41)])
missing = [i for i in ids if not re.search(r'^\| %s \|' % re.escape(i), CH, re.M)]
rowsch = re.findall(r'^\| ([A-Z]+-[A-Za-z]*\d*|ST-G) \|', CH, re.M)
print('finding ids expected:', len(ids), 'rows in CHANGES:', len(rowsch), 'missing:', missing)
if missing or len(rowsch) != len(ids): fail('findings without a row or extra rows: %s' % missing)
st = {}
for l in CH.splitlines():
    m = re.match(r'^\| ([A-Z]+-[A-Za-z]*\d*|ST-G) \| (FIXED|BLANK|MOVED|NOT FIXED)', l)
    if m: st[m.group(2)] = st.get(m.group(2), 0) + 1
print('status counts (by first word):', st, 'rows with no status word first:', len(rowsch) - sum(st.values()))
print('card lines still open (lead fills):', len(rows))
print('TOTAL PROBLEMS', bad)
sys.exit(1 if bad else 0)

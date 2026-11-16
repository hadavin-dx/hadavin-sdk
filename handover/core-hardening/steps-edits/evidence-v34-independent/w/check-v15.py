"""v15 checks (extends check-v14.py): banned strings, blank markers, Q-numbers, hard-coded times, dead cross references,
invented-number list, renamed words, one-place rules, finding coverage. Read-only: reads text, runs nothing else."""
import re, sys, ast
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'S': 'OWNER-STEPS-realrun-v15.md', 'C': 'OWNER-DAY-CARD-v15.md', 'A': 'OWNER-STEPS-v15-APPENDIX.md',
     'CH': 'v15-CHANGES.md', 'OP': 'v15-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
OWN = ('S', 'C', 'A')
bad = 0
def fail(msg):
    global bad
    print('FAIL', msg); bad += 1

src = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
m = re.search(r'BANNED = \((.*?)\n\)', src, re.S)
banned = ast.literal_eval('(' + m.group(1) + ')')
print('banned strings in test list:', len(banned))
for k, t in T.items():
    n = sum(t.count(b) for b in banned)
    n2 = len(re.findall(r'\b(PENDING|TBD|TODO)\b', t))
    print(f'{F[k]}: banned={n} PENDING/TBD/TODO={n2} bytes={len(t.encode())} UNVERIFIED={t.count("UNVERIFIED")}')
    if n or n2: fail(f'banned/placeholder in {F[k]}')
S, C, A, CH, OP = (T[k] for k in ('S', 'C', 'A', 'CH', 'OP'))

# 1. blank list B1..Bn in the sheet, sequential, cited on the card or in the sheet
lst = S.split('## The blanks')[1].split('## Words')[0]
nums = [int(x) for x in re.findall(r'\bB(\d+) ', lst)]
print('blank list numbers:', nums[0], '..', nums[-1], 'count', len(nums))
if nums != list(range(1, len(nums) + 1)): fail('blank list not sequential')
N = len(nums)
for k in OWN + ('OP',):
    for n in set(re.findall(r'\bB(\d+)\b', T[k])):
        if int(n) not in nums: fail(f'{k}: blank B{n} not in the list')
body = S.split('## Words')[1] + C + A
for n in nums:
    if not re.search(r'\bB%d\b' % n, body): fail(f'list blank never used outside the list: B{n}')
    if not re.search(r'\bB%d\b' % n, OP): fail(f'blank B{n} missing from v15-OPEN-FOR-LEAD.md')
# marker string must carry a blank number
M = 'THE STUDIO LEAD FILLS THIS IN'
for k in OWN:
    for m_ in re.finditer(M, T[k]):
        if not re.search(r'blank B\d+', T[k][m_.end():m_.end() + 120]): fail(f'{k}: marker without blank number')
# 2. card: every underline row carries a row number, a B number or "step A"; one underline per row
rows = [l for l in C.splitlines() if '________' in l]
print('card rows with an underline:', len(rows))
for l in rows:
    if l.count('________') != 1: fail('card row with several underlines: ' + l[:60])
    if not re.search(r'\| (?:row \d+|B\d+|step A)', l.split('|')[-3] if len(l.split('|')) >= 4 else ''):
        if not re.search(r'row \d+|\bB\d+\b|step A', l): fail('card underline row without row or B number: ' + l[:60])
if 'no underscore' not in C.lower() and 'no underscore' not in S.lower(): fail('half-filled cell rule missing')
for k in ('S', 'C'):
    if 'underscore' not in T[k]: fail(f'{k}: blank-cell rule missing')
# 3. renamed words and removed things (owner files)
for pat, why in ((r'run key', 'old name'), (r'take key', 'old name'), (r'MF_', 'film-v5 setting'), (r'\bQ\d{2}', 'Q-number'),
                 (r'\bQ\d\b', 'Q-number'), (r'[Dd]ecision \d', 'decision number'), (r'\bC\.3\b', 'removed step'),
                 (r'Sign in at the address', 'n8n sign-in'), (r'list of credentials', 'n8n look'), (r'list of runs', 'filmed n8n run list'),
                 (r'13 sends', 'send meaning'), (r'[Ee]xit code [1-9]\b', 'exit code stated'), (r'\bcode [1-9]\b', 'exit code stated'),
                 (r'\(\d\)\s*\d* retire', 'x'), (r'SKIPPED', 'result word'), (r'run card', 'renamed value list'), (r'day card', 'renamed card'),
                 (r'run window', 'renamed program window'), (r'run folder', 'renamed program folder'), (r'run settings file', 'renamed'),
                 (r'index not seen', 'moved to the lead list'), (r'last run is done', 'one phrase: no more runs'),
                 (r'ruling of 2026', 'unsourced ruling'), (r'default decision', 'jargon')):
    for k in OWN:
        c = len(re.findall(pat, T[k]))
        if c: fail(f'{k}: forbidden "{pat}" ({why}) x{c}')
# 4. invented numbers (turn into blanks): none of these may appear in the owner files
for pat in (r'5[- ]minute', r'\b5 minutes\b', r'at most 3', r'\b3 (?:runs|retire)', r'20[- ]minute', r'\b20 minutes\b', r'4 to 12', r'24[- ]hours?\b',
            r'24 h\b', r'2[- ]minutes?\b', r'two minutes', r'30[- ]minutes?\b', r'15 minutes', r'\b120\b', r'2 seconds', r'\b45\b', r'\b860\b',
            r'\{30', r'about 14', r'14 minutes', r'within 60', r'exit code 3'):
    for k in OWN:
        if k == 'A' and pat == r'within 60': continue   # ban list quotes the forbidden claim "within 60 seconds"
        c = len(re.findall(pat, T[k]))
        if c: fail(f'{k}: invented/unsourced number "{pat}" x{c}')
# 5. hard-coded times: only the money stop, the post time, their IST forms and the offset
ok_times = {'18:29', '23:59', '15:00', '20:30', '5:30'}
for k in OWN:
    for t_ in set(re.findall(r'(?<![\d.])\d{1,2}:\d{2}(?!\d)', T[k])):
        if t_ not in ok_times: fail(f'{k}: hard-coded time {t_}')
for s in ('18:29 UTC = 23:59 IST', '25 Nov 2026 15:00 UTC = 20:30 IST'):
    for k in ('S',):
        print(k, s, T[k].count(s))
        if T[k].count(s) < 1: fail('date string missing: ' + s)
# 6. "lead" alone (outside the claim and the quoted definitions) must be "studio lead"
for k in OWN:
    t = T[k]
    for ph in ('a lead sent twice', 'sales lead', 'lead key', '"lead"', "'lead'", 'unfinished lead', 'lead whose', '[demo] lead', 'lead desk', 'lead-status'):
        t = t.replace(ph, '')
    c = [t[max(0, m_.start() - 25):m_.end() + 15].replace('\n', ' ') for m_ in re.finditer(r'(?<!studio )\b[Ll]eads?\b', t)]
    if c: fail(f'{k}: bare "lead" x{len(c)}: {c[:3]}')
# 7. one place per rule
if '| **Key exposed**' in C or 'Which word to use' in C: fail('card redefines the stop words')
for k in ('C', 'A'):
    if 'Recording OFF first' in T[k]: fail(f'{k} repeats the Key exposed definition')
if S.count('Recording OFF first') != 1: fail('Key exposed rule not exactly once in the sheet')
if re.search(r'nothing can (start or )?spend', S + C): fail('"nothing can spend" claim in S or C')
if 'up to three tries' in S + C or 'three tries' in S + C: fail('lease sentence in the owner sheet or card')
if 'NOT APPROVED' not in A or 'up to three tries' not in A: fail('lease candidate missing from appendix 8')
for pat in ('lease length', 'latest start'):
    pass
if A.count('It is the only source of the latest start') != 1: fail('latest start not defined once')
if 'about 14' in A: fail('second latest-start figure')
for pat in ('Freeze never stops F.4, I.0 or 0.6', 'the only place they are defined'):
    if S.count(pat) != 1: fail('missing once: ' + pat)
# 8. cross references
def exists(path_n, k): return k
heads = set(re.findall(r'\*\*(A\.0b|A\.\d|0\.\d|C\.\d|I\.\d|[BD])[ .]', S)) | set(f'I.{i}' for i in range(0, 8)) | {'E', 'E.0', 'F', 'H', 'I', 'J', 'G', 'T'}
heads |= {f'F.{i}' for i in range(1, 6)} | {f'E.{i}' for i in range(1, 5)}
for k in OWN:
    for r_ in set(re.findall(r'\b(A\.0b|A\.[0-6]|0\.[1-6]|C\.[1-3]|I\.[0-7]|F\.[1-5]|E\.[0-4])\b', T[k])):
        if r_ not in heads: fail(f'{k}: unresolved step ref {r_}')
for r_ in re.findall(r'^(E\.0|## E\. |## F\. )', C, re.M): pass
if 'E.0 Before E' not in C: fail('card lacks E.0 heading')
cf = C.split('## F. Film pause')[1]
for i in range(1, 6):
    if not re.search(rf'^{i}\. ', cf, re.M): fail(f'card F item {i} missing')
secs = sorted(int(x) for x in re.findall(r'^## (\d+)\.', A, re.M))
if secs != list(range(1, 19)): fail('appendix sections not 1..18')
for k in OWN + ('CH', 'OP'):
    for n in re.findall(r'[Aa]ppendix (\d+)', T[k]) + (re.findall(r'[Ss]ection (\d+)', T[k]) if k == 'A' else []):
        if int(n) not in secs: fail(f'{k}: bad appendix/section ref {n}')
rows_a = sorted(int(x) for x in re.findall(r'^\| (\d+) \|', A.split('## 3.')[0].split('## 2.')[1], re.M))
if rows_a != list(range(1, 24)): fail('value list rows not 1..23')
for k in OWN:
    for n in re.findall(r'\brows? (\d+)', T[k]) + [x for p in re.findall(r'rows (\d+) (?:to|and) (\d+)', T[k]) for x in p]:
        if not 1 <= int(n) <= 23: fail(f'{k}: bad row {n}')
    for n in re.findall(r'go items? (\d)', T[k]):
        if not 1 <= int(n) <= 9: fail(f'{k}: bad go item {n}')
goitems = re.findall(r'^(\d)\. ', S.split('## The go list')[1].split('## The money rule')[0], re.M)
if goitems != [str(i) for i in range(1, 10)]: fail('go items not 1..9')
money = re.findall(r'^(\d)\. ', S.split('## The money rule')[1].split('## Rules that hold')[0], re.M)
if money != [str(i) for i in range(1, 7)]: fail('money items not 1..6')
for n in re.findall(r'money rule items? (\d)', S + C + A):
    if n not in money: fail(f'bad money item {n}')
ban = re.findall(r'(?:^|\s)(\d{1,2})\. ', A.split('## 8.')[1].split('## 9.')[0].split('Two further')[0])
if sorted(set(int(i) for i in ban)) != list(range(1, 14)): fail('ban list not 1..13')
rl = re.findall(r'\brule (\d+)', S + C + A)
for n in rl:
    if not 1 <= int(n) <= 14: fail(f'bad rule ref {n}')
# 9. finding coverage in v15-CHANGES.md: one row per finding id
ids = (['SE-N%d' % i for i in range(1, 9)] + ['SE-M%d' % i for i in range(3, 8)] + ['SE-n1', 'SE-n2', 'SE-n3'] + ['SE-O%d' % i for i in range(1, 6)] + ['SE-D']
       + ['ST-B'] + ['ST-%d' % i for i in range(1, 18)] + ['ST-n%d' % i for i in range(1, 13)]
       + ['CI-%d' % i for i in range(1, 7)] + ['CI-U%d' % i for i in range(1, 10)]
       + ['AD-%d' % i for i in range(1, 44)] + ['CO-%d' % i for i in range(1, 13)] + ['R2-%d' % i for i in range(1, 9)] + ['R2-F']
       + ['NC-5', 'NC-6', 'NC-7', 'NC-8', 'NC-15', 'NC-19', 'NC-20'] + ['OR-%d' % i for i in range(1, 7)])
missing = [i for i in ids if not re.search(r'^\| %s \|' % re.escape(i), CH, re.M)]
print('finding ids expected:', len(ids), 'rows in CHANGES:', len(re.findall(r'^\| [A-Z0-9-]+[a-z]?\d* \|', CH, re.M)), 'missing:', missing)
if missing: fail('findings without a row: %s' % missing)
# 10. open blanks report (package state)
print('card underline rows still open (lead fills):', len(rows))
print('sheet markers "THE STUDIO LEAD FILLS THIS IN":', S.count(M), '| proposals listed in OPEN:', len(re.findall(r'proposal', OP, re.I)))
for k in OWN: print(F[k], 'bytes', len(T[k].encode()))
print('TOTAL PROBLEMS', bad)
sys.exit(1 if bad else 0)

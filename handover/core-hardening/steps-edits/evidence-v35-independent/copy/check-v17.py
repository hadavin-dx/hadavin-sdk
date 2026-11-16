"""v17 checks: reads text only, runs nothing else. Prints counts, never a banned word."""
import ast, re, sys
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'S': 'OWNER-SHEET-v17.md', 'N': 'LEAD-RELEASE-NOTE-v1.md', 'M': 'v17-MAP.md', 'O': 'v17-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
problems = []
def bad(msg): problems.append(msg); print('PROBLEM:', msg)
def ok(msg): print('ok:', msg)

# 1 counts
n = {k: len(t.splitlines()) for k, t in T.items()}
print('lines:', n)
if not 60 <= n['S'] <= 100: bad('sheet lines %d not in 60..100' % n['S'])
else: ok('sheet lines %d' % n['S'])
heads = re.findall(r'^## ', T['S'], re.M)
print('sheet headings:', len(heads))
if not 6 <= len(heads) <= 9: bad('heading count %d' % len(heads))

# 2 rules defined once, referenced ones exist
S = T['S']
defs = re.findall(r'^\| (R\d+) \|', S, re.M)
if sorted(defs, key=lambda x: int(x[1:])) != ['R%d' % i for i in range(1, 11)] or len(set(defs)) != 10:
    bad('rule ids defined: %s' % defs)
else: ok('R1..R10 each defined once')
for k, t in T.items():
    for r in set(re.findall(r'\bR(\d+)\b', t)):
        if not 1 <= int(r) <= 10: bad('%s refers to R%s which is not defined' % (F[k], r))
for i in range(1, 11):
    outside = sum(len(re.findall(r'\bR%d\b' % i, t)) for t in T.values()) - 1
    if outside < 1: bad('R%d is never referenced outside its definition' % i)
ok('rule references checked')
# G ids
Nn = T['N']
gdefs = re.findall(r'^\| (G\d+) \|', Nn, re.M)
if gdefs != ['G%d' % i for i in range(1, 25)]: bad('G ids defined: %s' % gdefs)
else: ok('G1..G24 each defined once')
for k, t in T.items():
    for g in set(re.findall(r'\bG(\d+)\b', t)):
        if not 1 <= int(g) <= 24: bad('%s refers to G%s' % (F[k], g))
# section refs in sheet
for s in set(re.findall(r'section (\d+)', S)):
    if not 1 <= int(s) <= 8: bad('sheet refers to section %s' % s)
# open item refs
nopen = len(re.findall(r'^\| \d+ \|', T['O'], re.M))
for k in ('N', 'M'):
    for o in set(re.findall(r'\bOpen (\d+)\b', T[k]) + re.findall(r'open item (\d+)', T[k])):
        if not 1 <= int(o) <= nopen: bad('%s refers to Open %s (only %d)' % (F[k], o, nopen))
print('open rows:', nopen)

# 3 rule key phrases appear once, only in the rule table
phr = ['cancel only', 'secret-looking', 'window-end setting', 'does not enforce', 'count equals', 'FREEZE =', 'Recording OFF first',
       'ONE cancel rule', 'Never a tool', 'no closed gate', 'does not print the model settings figures', 'could read the key file']
rows = {l for l in S.splitlines() if re.match(r'\| R\d+ \|', l)}
for p in phr:
    cnt = sum(t.lower().count(p.lower()) for k, t in T.items() if k in 'SNO')
    inrule = sum(l.lower().count(p.lower()) for l in rows)
    if cnt != 1 or inrule != 1:
        # 'no closed gate' also legitimately appears in the lead's ban list
        bad('phrase %r occurs %d times (in rule table %d)' % (p, cnt, inrule))
ok('rule phrases checked') if not any('phrase' in x for x in problems) else None

# 4 glossary: first use is the bold definition
terms = ['lead', 'test people', 'run name', 'take program', 'model program', 'model key', 'app passwords', 'take settings file',
         'model settings file', 'contact id', 'notice', 'challenge', 'printed result', 'film pause', 'window end', 'key deadline',
         'latest start', 'call ceiling', 'run total', 'usage page', 'throwaway accounts', 'UNVERIFIED', 'WSL', 'n8n', 'take window', 'check window']
for t in terms:
    m = re.search(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])', S, re.I)
    if not m: bad('term %r never used' % t); continue
    pre = S[max(0, m.start() - 2):m.start()]
    # 'take window' and 'check window' are defined in a heading parenthesis, accept the section 6 heading
    line = S[S.rfind('\n', 0, m.start()) + 1:S.find('\n', m.start())]
    if pre != '**' and not (t in ('take window', 'check window') and line.startswith('## 6.')):
        bad('term %r first used before its definition (line: %s...)' % (t, line[:60]))
ok('glossary order checked') if not any('term' in x for x in problems) else None

# 5 banned words (counts only)
tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
banned = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in node.targets):
        banned = [e.value for e in node.value.elts]
cnt_cs = sum(t.count(b) for t in T.values() for b in banned)
cnt_ci = sum(t.lower().count(b.lower()) for t in T.values() for b in banned)
print('banned words: %d listed, occurrences case-sensitive %d, case-insensitive %d' % (len(banned), cnt_cs, cnt_ci))
if cnt_cs or cnt_ci: bad('banned words found')

# 6 no bare lowercase stop; no bare program / settings file / row; no "lead" as sales contact outside the claim
for k in 'SNO':
    t = T[k]
    if re.search(r'\bstop\b', t): bad('%s holds bare lowercase "stop"' % F[k])
S_nocode = re.sub(r'`[^`]*`', '', S)
if re.search(r'(?<!take )(?<!model )(?<!Model )(?<!Take )\bprograms?\b', S_nocode): bad('bare "program" in sheet')
if re.search(r'(?<!take )(?<!model )(?<!Take )(?<!Model )settings file', S_nocode, re.I): bad('bare "settings file" in sheet')
if re.search(r'\brows?\b', S_nocode, re.I): bad('"row" in sheet')
# key meaning: 'key file' ok; 'HubSpot key' not in sheet
if re.search(r'HubSpot key|probe key|API key', S): bad('other key meaning in sheet')
for k in 'SNO':
    Tk = re.sub(r'`[^`]*`', '', T[k])
    for m in re.finditer(r'(?<![A-Za-z])program(?![A-Za-z])', Tk):
        pre = Tk[max(0, m.start() - 6):m.start()].lower()
        if not (pre.endswith('take ') or pre.endswith('model ')):
            bad('%s: bare "program" near %r' % (F[k], Tk[max(0, m.start() - 30):m.start() + 20])); break
ok('word checks run')

# 7 map completeness
M = T['M']
secs = re.split(r'^## (\d+)\. ', M, flags=re.M)
sec = {int(secs[i]): secs[i + 1] for i in range(1, len(secs) - 1, 2)}
def has(s, ids, pat):
    for i in ids:
        if not re.search(pat % re.escape(i), sec[s], re.M): bad('map section %d lacks %s' % (s, i))
has(3, ['M-A', 'M-B', 'M-C', 'M-D', 'M-E', 'M-F', 'M-G', 'M-H'] + ['v15 M%d' % i for i in range(1, 8)] + ['n%d' % i for i in range(1, 10)], r'^\| %s[ |]')
has(4, ['M%d' % i for i in range(1, 16)] + ['n%d' % i for i in range(1, 11)] + ['U%d' % i for i in range(1, 8)], r'^\| %s[ |]')
has(5, ['B1', 'B2', 'B3'] + ['M%d' % i for i in range(1, 12)] + ['n%d' % i for i in range(1, 6)] + ['SC%d' % i for i in range(1, 8)], r'^\| %s[ |]')
has(6, [str(i) for i in range(1, 18)], r'^\| %s[ |]')
has(2, ['OI-%d' % i for i in range(1, 39)], r'\| %s \|')
cits = set()
for l in sec[7].splitlines():
    m = re.match(r'\| ([\d, ]+?)(?= [A-Za-z"])', l)
    if m: cits |= {int(x) for x in re.findall(r'\d+', m.group(1))}
if cits != set(range(1, 11)): bad('citation ids %s' % sorted(cits))
for s in ['Step 0', 'A.0 ', 'A.0b', 'A.1', 'A.2', 'A.3', 'A.4', 'A.5', 'A.6', 'I.0', 'I.1', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'F.1', 'F.2', 'F.3', 'F.4', 'F.5', 'E.0', 'C.1', 'C.2', 'Go list 1', 'Go list 9', 'Trial run', 'Stop rules', 'DO THIS FIRST 5'] + ['Appendix %d ' % i for i in range(1, 19)]:
    if s not in sec[1]: bad('map section 1 lacks %r' % s)
maprows = len(re.findall(r'^\| ', M, re.M))
print('map table rows (all, including header and separator rows):', maprows)
ok('map checked') if not any('map' in x for x in problems) else None

# 8 required controls present in the sheet (key phrases)
need = ['run-<run name>', 'Recording', 'phone alarm', 'prepaid', 'auto-reload', '18:29 UTC = 23:59 IST', '15:00 UTC = 20:30 IST', 'UNVERIFIED',
        'before I type y', 'revoke', 'contact id', '`n`', 'challenge', '`end`', 'step 0', 'Step 0']
for p in need:
    if p not in S and p.lower() not in S.lower(): bad('sheet lacks %r' % p)
print('TOTAL PROBLEMS', len(problems))
sys.exit(1 if problems else 0)
